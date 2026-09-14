from django.db.models import Q

from businessos.core.access.policies import validate_business_context
from businessos.core.common.context import BusinessContext

from .models import Attribute, Product, ProductCategory, ProductVariant


def products_for_company(context: BusinessContext, *, search: str = "", product_type: str = ""):
    validate_business_context(context)
    queryset = (
        Product.objects.select_related("category", "default_uom")
        .prefetch_related("variants")
        .filter(company_id=context.company_id)
    )
    if search.strip():
        queryset = queryset.filter(
            Q(name__icontains=search.strip()) | Q(variants__sku__icontains=search.strip())
        ).distinct()
    if product_type:
        queryset = queryset.filter(product_type=product_type)
    return queryset.order_by("name")


def active_categories(context: BusinessContext):
    validate_business_context(context)
    return ProductCategory.objects.filter(
        company_id=context.company_id, is_active=True
    ).select_related("parent")


def active_variants(context: BusinessContext):
    validate_business_context(context)
    return ProductVariant.objects.filter(
        company_id=context.company_id, is_active=True, product__is_active=True
    ).select_related("product")


def product_detail(context: BusinessContext, *, product_id) -> Product:
    validate_business_context(context)
    return Product.objects.select_related("category", "default_uom").prefetch_related(
        "variants__attribute_assignments__attribute",
        "variants__attribute_assignments__attribute_value",
    ).get(id=product_id, company_id=context.company_id)


def default_variant_for_product(context: BusinessContext, *, product_id) -> ProductVariant:
    validate_business_context(context)
    return ProductVariant.objects.select_related("product").get(
        product_id=product_id, company_id=context.company_id, is_default=True
    )


def variant_by_sku(context: BusinessContext, *, sku: str) -> ProductVariant:
    validate_business_context(context)
    return ProductVariant.objects.select_related("product").get(
        company_id=context.company_id, sku=sku.strip().upper()
    )


def attributes_for_company(context: BusinessContext):
    validate_business_context(context)
    return Attribute.objects.filter(company_id=context.company_id).prefetch_related("values")
