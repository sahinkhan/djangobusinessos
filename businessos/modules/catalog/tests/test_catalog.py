import inspect
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection

from businessos.core.access.models import UserCompanyAccess
from businessos.core.common.context import BusinessContext
from businessos.core.modules.manifest import validate_manifest
from businessos.core.modules.services import register_manifest
from businessos.core.organization.models import Company
from businessos.modules.catalog.manifest import MODULE as CATALOG_MANIFEST
from businessos.modules.catalog.models import (
    Product,
    ProductCategory,
    ProductVariant,
    VariantAttributeValue,
)
from businessos.modules.catalog.selectors import (
    active_variants,
    default_variant_for_product,
    products_for_company,
    variant_by_sku,
)
from businessos.modules.catalog.services import (
    assign_variant_attribute_values,
    create_attribute,
    create_attribute_value,
    create_category,
    create_product_variant,
    create_simple_product,
    create_variable_product,
    update_product,
    update_product_variant,
)
from businessos.modules.party.manifest import MODULE as PARTY_MANIFEST
from businessos.modules.party.services import create_party


@pytest.mark.django_db
def test_simple_product_gets_exactly_one_default_variant(business_context, uom):
    product = create_simple_product(
        business_context,
        name="Organic Honey",
        sku=" honey-001 ",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )

    assert product.structure == Product.Structure.SIMPLE
    assert product.variants.count() == 1
    variant = default_variant_for_product(business_context, product_id=product.id)
    assert variant.sku == "HONEY-001"
    assert variant.is_default is True
    assert variant_by_sku(business_context, sku="honey-001") == variant


@pytest.mark.django_db
def test_service_product_has_variant_without_inventory_dependency(business_context, uom):
    product = create_simple_product(
        business_context,
        name="Consulting Hour",
        sku="SERVICE-HOUR",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
        is_purchasable=False,
    )

    assert product.product_type == Product.Type.SERVICE
    assert product.variants.get().is_default is True
    assert "inventory" not in CATALOG_MANIFEST["depends"]


@pytest.mark.django_db
def test_simple_product_rejects_additional_or_non_default_variant(business_context, uom):
    product = create_simple_product(
        business_context,
        name="Simple",
        sku="SIMPLE-1",
        product_type=Product.Type.CONSUMABLE,
        default_uom_id=uom.id,
    )

    with pytest.raises(ValidationError, match="variable Product"):
        create_product_variant(business_context, product_id=product.id, sku="SIMPLE-2")
    variant = product.variants.get()
    variant.is_default = False
    with pytest.raises(ValidationError, match="must be default"):
        variant.save()

    update_product(
        business_context,
        product_id=product.id,
        name="Simple renamed",
        sku="SIMPLE-EDITED",
    )
    variant.refresh_from_db()
    assert variant.sku == "SIMPLE-EDITED"


@pytest.mark.django_db
def test_simple_product_activation_synchronizes_default_variant_without_sku(
    business_context, uom
):
    product = create_simple_product(
        business_context,
        name="Seasonal service",
        sku="SEASONAL-1",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
        is_active=False,
    )
    variant = product.variants.get()
    assert variant.is_active is False

    update_product(business_context, product_id=product.id, is_active=True)

    variant.refresh_from_db()
    assert variant.is_active is True
    assert active_variants(business_context).get(id=variant.id) == variant


@pytest.mark.django_db
def test_variable_product_supports_explicit_variants_and_attributes(business_context, uom):
    product = create_variable_product(
        business_context,
        name="Premium T-Shirt",
        variants=[
            {"sku": "TS-BLK-M", "is_default": True},
            {"sku": "TS-WHT-L"},
        ],
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )
    color = create_attribute(business_context, name="Color")
    size = create_attribute(business_context, name="Size")
    black = create_attribute_value(business_context, attribute_id=color.id, value="Black")
    medium = create_attribute_value(business_context, attribute_id=size.id, value="M")
    variant = product.variants.get(sku="TS-BLK-M")

    assign_variant_attribute_values(
        business_context, variant_id=variant.id, attribute_value_ids=[black.id, medium.id]
    )

    assert product.variants.count() == 2
    assert list(
        variant.attribute_assignments.order_by("attribute__name").values_list(
            "attribute__name", "attribute_value__value"
        )
    ) == [("Color", "Black"), ("Size", "M")]
    second_variant = product.variants.get(sku="TS-WHT-L")
    update_product_variant(
        business_context,
        variant_id=second_variant.id,
        sku="TS-WHT-XL",
        is_default=False,
        is_active=True,
    )
    second_variant.refresh_from_db()
    assert second_variant.sku == "TS-WHT-XL"


@pytest.mark.django_db
def test_contradictory_attribute_values_are_rejected_without_losing_assignments(
    business_context, uom
):
    product = create_variable_product(
        business_context,
        name="Shirt",
        variants=[{"sku": "SHIRT-1"}],
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )
    color = create_attribute(business_context, name="Color")
    black = create_attribute_value(business_context, attribute_id=color.id, value="Black")
    white = create_attribute_value(business_context, attribute_id=color.id, value="White")
    variant = product.variants.get()
    assign_variant_attribute_values(
        business_context, variant_id=variant.id, attribute_value_ids=[black.id]
    )

    with pytest.raises(ValidationError, match="at most one value"):
        assign_variant_attribute_values(
            business_context, variant_id=variant.id, attribute_value_ids=[black.id, white.id]
        )

    assert list(variant.attribute_assignments.values_list("attribute_value_id", flat=True)) == [
        black.id
    ]


@pytest.mark.django_db
def test_inactive_attribute_rejected_for_new_assignment_without_losing_history(
    business_context, uom
):
    product = create_variable_product(
        business_context,
        name="Archived option product",
        variants=[{"sku": "ARCHIVE-1"}],
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )
    color = create_attribute(business_context, name="Color")
    black = create_attribute_value(business_context, attribute_id=color.id, value="Black")
    variant = product.variants.get()
    assign_variant_attribute_values(
        business_context, variant_id=variant.id, attribute_value_ids=[black.id]
    )
    color.is_active = False
    color.save()

    with pytest.raises(PermissionDenied, match="not active"):
        assign_variant_attribute_values(
            business_context, variant_id=variant.id, attribute_value_ids=[black.id]
        )

    assert list(variant.attribute_assignments.values_list("attribute_value_id", flat=True)) == [
        black.id
    ]


@pytest.mark.django_db(transaction=True)
def test_concurrent_attribute_replacements_finish_as_one_complete_submission(
    business_context, uom
):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock concurrency contract requires PostgreSQL.")
    product = create_variable_product(
        business_context,
        name="Concurrent option product",
        variants=[{"sku": "CONCURRENT-1"}],
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )
    color = create_attribute(business_context, name="Color")
    size = create_attribute(business_context, name="Size")
    black = create_attribute_value(business_context, attribute_id=color.id, value="Black")
    large = create_attribute_value(business_context, attribute_id=size.id, value="L")
    variant = product.variants.get()
    start = Barrier(2)

    def replace(values):
        close_old_connections()
        try:
            start.wait(timeout=5)
            assign_variant_attribute_values(
                business_context, variant_id=variant.id, attribute_value_ids=values
            )
        finally:
            close_old_connections()

    submissions = ([black.id], [large.id])
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(replace, values) for values in submissions]
        for future in futures:
            future.result(timeout=10)

    final_values = set(
        VariantAttributeValue.objects.filter(variant=variant).values_list(
            "attribute_value_id", flat=True
        )
    )
    assert final_values in [set(values) for values in submissions]


@pytest.mark.django_db
def test_database_and_model_allow_at_most_one_default_variant(business_context, uom):
    product = create_variable_product(
        business_context,
        name="Variable",
        variants=[{"sku": "VAR-1", "is_default": True}],
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )

    with pytest.raises(ValidationError):
        create_product_variant(
            business_context, product_id=product.id, sku="VAR-2", is_default=True
        )
    with pytest.raises(ValidationError, match="last variant"):
        product.variants.get().delete()


@pytest.mark.django_db
def test_sku_is_unique_per_company_and_reusable_in_another_company(
    business_context, operator, currency, uom
):
    create_simple_product(
        business_context,
        name="First",
        sku="SHARED-SKU",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )
    with pytest.raises(ValidationError):
        create_simple_product(
            business_context,
            name="Duplicate",
            sku="shared-sku",
            product_type=Product.Type.STOCKABLE,
            default_uom_id=uom.id,
        )

    other_company = Company.objects.create(code="OTHER", name="Other", base_currency=currency)
    other_context = BusinessContext(actor_id=operator.id, company_id=other_company.id)
    UserCompanyAccess.objects.create(user=operator, company=other_company)
    other_product = create_simple_product(
        other_context,
        name="Allowed",
        sku="SHARED-SKU",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )
    assert other_product.variants.get().sku == "SHARED-SKU"


@pytest.mark.django_db
def test_catalog_relationships_and_selectors_are_company_scoped(
    business_context, operator, currency, uom
):
    category = create_category(business_context, name="Company One")
    product = create_simple_product(
        business_context,
        name="Visible",
        sku="VISIBLE-1",
        category_id=category.id,
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )
    other_company = Company.objects.create(code="OTHER", name="Other", base_currency=currency)
    other_context = BusinessContext(actor_id=operator.id, company_id=other_company.id)

    assert list(products_for_company(business_context)) == [product]
    assert list(active_variants(business_context)) == [product.variants.get()]
    with pytest.raises(PermissionDenied, match="access to this company"):
        list(products_for_company(other_context))
    with pytest.raises(PermissionDenied, match="outside the selected company"):
        create_simple_product(
            business_context,
            name="Cross scoped",
            sku="CROSS-1",
            category_id=ProductCategory.objects.create(
                company=other_company, name="Other Category"
            ).id,
            product_type=Product.Type.STOCKABLE,
            default_uom_id=uom.id,
        )


def test_catalog_has_no_authoritative_stock_field():
    forbidden = {"stock", "stock_quantity", "quantity_on_hand", "warehouse_balance"}
    assert forbidden.isdisjoint({field.name for field in Product._meta.get_fields()})
    assert forbidden.isdisjoint({field.name for field in ProductVariant._meta.get_fields()})


@pytest.mark.django_db
def test_manifests_register_and_service_contracts_follow_dependency_rules():
    party = validate_manifest(PARTY_MANIFEST)
    catalog = validate_manifest(CATALOG_MANIFEST)
    party_record = register_manifest(PARTY_MANIFEST)
    catalog_record = register_manifest(CATALOG_MANIFEST)

    assert party.depends == ("identity", "organization", "reference", "access")
    assert catalog.depends == ("reference", "organization", "access")
    assert party_record.dependencies == list(party.depends)
    assert catalog_record.dependencies == list(catalog.depends)
    assert party_record.is_enabled is False
    assert catalog_record.is_enabled is False
    assert "context" in inspect.signature(create_simple_product).parameters
    assert "request" not in inspect.signature(create_simple_product).parameters
    assert "request" not in inspect.signature(create_party).parameters
    assert VariantAttributeValue._meta.get_field("variant").related_model is ProductVariant


def test_core_has_no_reverse_imports_to_phase1_modules():
    core_root = Path(__file__).resolve().parents[3] / "core"
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in core_root.rglob("*.py")
    )

    assert "businessos.modules.party" not in source
    assert "businessos.modules.catalog" not in source
