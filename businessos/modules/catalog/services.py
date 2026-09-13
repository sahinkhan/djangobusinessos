from collections.abc import Iterable, Mapping

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from businessos.core.access.policies import validate_business_context
from businessos.core.common.context import BusinessContext
from businessos.core.reference.models import UnitOfMeasure

from .models import (
    Attribute,
    AttributeValue,
    Product,
    ProductCategory,
    ProductVariant,
    VariantAttributeValue,
)


def _in_scope(model, context: BusinessContext, object_id, label: str):
    try:
        return model.objects.get(id=object_id, company_id=context.company_id)
    except model.DoesNotExist as exc:
        raise PermissionDenied(f"The {label} is outside the selected company.") from exc


def _category(context, category_id):
    if category_id in (None, ""):
        return None
    category = _in_scope(ProductCategory, context, category_id, "category")
    if not category.is_active:
        raise ValidationError({"category": "Select an active category."})
    return category


def _uom(uom_id):
    try:
        return UnitOfMeasure.objects.get(id=uom_id, is_active=True)
    except UnitOfMeasure.DoesNotExist as exc:
        raise ValidationError({"default_uom": "Select an active unit of measure."}) from exc


@transaction.atomic
def create_category(
    context: BusinessContext, *, name: str, parent_id=None, is_active: bool = True
) -> ProductCategory:
    validate_business_context(context)
    parent = _category(context, parent_id)
    category = ProductCategory(
        company_id=context.company_id, name=name, parent=parent, is_active=is_active
    )
    category.save()
    return category


def _new_product(
    context,
    *,
    name,
    category_id,
    product_type,
    structure,
    default_uom_id,
    sales_description="",
    purchase_description="",
    is_sellable=True,
    is_purchasable=True,
    is_active=True,
):
    return Product.objects.create(
        company_id=context.company_id,
        name=name,
        category=_category(context, category_id),
        product_type=product_type,
        structure=structure,
        default_uom=_uom(default_uom_id),
        sales_description=sales_description,
        purchase_description=purchase_description,
        is_sellable=is_sellable,
        is_purchasable=is_purchasable,
        is_active=is_active,
    )


@transaction.atomic
def create_simple_product(
    context: BusinessContext,
    *,
    name: str,
    sku: str,
    product_type: str,
    default_uom_id,
    category_id=None,
    sales_description: str = "",
    purchase_description: str = "",
    is_sellable: bool = True,
    is_purchasable: bool = True,
    is_active: bool = True,
) -> Product:
    validate_business_context(context)
    product = _new_product(
        context,
        name=name,
        category_id=category_id,
        product_type=product_type,
        structure=Product.Structure.SIMPLE,
        default_uom_id=default_uom_id,
        sales_description=sales_description,
        purchase_description=purchase_description,
        is_sellable=is_sellable,
        is_purchasable=is_purchasable,
        is_active=is_active,
    )
    ProductVariant.objects.create(
        company_id=context.company_id,
        product=product,
        sku=sku,
        is_default=True,
        is_active=is_active,
    )
    return product


@transaction.atomic
def create_variable_product(
    context: BusinessContext,
    *,
    name: str,
    variants: Iterable[Mapping],
    product_type: str,
    default_uom_id,
    category_id=None,
    sales_description: str = "",
    purchase_description: str = "",
    is_sellable: bool = True,
    is_purchasable: bool = True,
    is_active: bool = True,
) -> Product:
    validate_business_context(context)
    variant_specs = list(variants)
    if not variant_specs:
        raise ValidationError({"variants": "A variable Product requires at least one variant."})
    if sum(bool(spec.get("is_default")) for spec in variant_specs) > 1:
        raise ValidationError({"variants": "A Product can have at most one default variant."})
    product = _new_product(
        context,
        name=name,
        category_id=category_id,
        product_type=product_type,
        structure=Product.Structure.VARIABLE,
        default_uom_id=default_uom_id,
        sales_description=sales_description,
        purchase_description=purchase_description,
        is_sellable=is_sellable,
        is_purchasable=is_purchasable,
        is_active=is_active,
    )
    for spec in variant_specs:
        ProductVariant.objects.create(
            company_id=context.company_id,
            product=product,
            sku=spec["sku"],
            is_default=bool(spec.get("is_default", False)),
            is_active=bool(spec.get("is_active", True)),
        )
    return product


@transaction.atomic
def update_product(context: BusinessContext, *, product_id, **changes) -> Product:
    validate_business_context(context)
    product = _in_scope(Product, context, product_id, "product")
    allowed = {
        "name",
        "sku",
        "category_id",
        "product_type",
        "default_uom_id",
        "sales_description",
        "purchase_description",
        "is_sellable",
        "is_purchasable",
        "is_active",
    }
    unknown = changes.keys() - allowed
    if unknown:
        raise ValidationError(f"Unsupported Product fields: {', '.join(sorted(unknown))}")
    sku = changes.pop("sku", None)
    if sku is not None and product.structure != Product.Structure.SIMPLE:
        raise ValidationError("Update variable Product SKUs through ProductVariant services.")
    if "category_id" in changes:
        changes["category"] = _category(context, changes.pop("category_id"))
    if "default_uom_id" in changes:
        changes["default_uom"] = _uom(changes.pop("default_uom_id"))
    for field_name, value in changes.items():
        setattr(product, field_name, value)
    product.save()
    if sku is not None:
        variant = product.variants.get()
        variant.sku = sku
        variant.is_default = True
        variant.is_active = product.is_active
        variant.save()
    return product


@transaction.atomic
def create_product_variant(
    context: BusinessContext,
    *,
    product_id,
    sku: str,
    is_default: bool = False,
    is_active: bool = True,
) -> ProductVariant:
    validate_business_context(context)
    product = _in_scope(Product, context, product_id, "product")
    if product.structure != Product.Structure.VARIABLE:
        raise ValidationError("Additional variants require a variable Product.")
    variant = ProductVariant(
        company_id=context.company_id,
        product=product,
        sku=sku,
        is_default=is_default,
        is_active=is_active,
    )
    variant.save()
    return variant


@transaction.atomic
def update_product_variant(
    context: BusinessContext,
    *,
    variant_id,
    sku: str,
    is_default: bool,
    is_active: bool,
) -> ProductVariant:
    validate_business_context(context)
    variant = _in_scope(ProductVariant, context, variant_id, "variant")
    variant.sku = sku
    variant.is_default = is_default
    variant.is_active = is_active
    variant.save()
    return variant


@transaction.atomic
def create_attribute(
    context: BusinessContext, *, name: str, is_active: bool = True
) -> Attribute:
    validate_business_context(context)
    attribute = Attribute(company_id=context.company_id, name=name, is_active=is_active)
    attribute.save()
    return attribute


@transaction.atomic
def create_attribute_value(
    context: BusinessContext, *, attribute_id, value: str, is_active: bool = True
) -> AttributeValue:
    validate_business_context(context)
    attribute = _in_scope(Attribute, context, attribute_id, "attribute")
    attribute_value = AttributeValue(
        company_id=context.company_id,
        attribute=attribute,
        value=value,
        is_active=is_active,
    )
    attribute_value.save()
    return attribute_value


@transaction.atomic
def assign_variant_attribute_values(
    context: BusinessContext, *, variant_id, attribute_value_ids: Iterable
) -> ProductVariant:
    validate_business_context(context)
    variant = _in_scope(ProductVariant, context, variant_id, "variant")
    if variant.product.structure != Product.Structure.VARIABLE:
        raise ValidationError("Simple Product variants do not use attribute assignments.")
    requested_ids = set(attribute_value_ids)
    values = list(
        AttributeValue.objects.select_related("attribute").filter(
            id__in=requested_ids, company_id=context.company_id, is_active=True
        )
    )
    if len(values) != len(requested_ids):
        raise PermissionDenied("One or more attribute values are outside the selected company.")
    attribute_ids = [value.attribute_id for value in values]
    if len(attribute_ids) != len(set(attribute_ids)):
        raise ValidationError("Select at most one value for each attribute.")
    variant.attribute_assignments.all().delete()
    for value in values:
        VariantAttributeValue.objects.create(
            company_id=context.company_id,
            variant=variant,
            attribute=value.attribute,
            attribute_value=value,
        )
    return variant
