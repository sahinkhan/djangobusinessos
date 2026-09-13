from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection

from businessos.core.access.models import UserCompanyAccess
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.modules.catalog.models import Product, ProductVariant
from businessos.modules.catalog.services import (
    create_simple_product,
    create_variable_product,
    update_product,
)
from businessos.modules.party.models import Party
from businessos.modules.party.services import create_party
from businessos.modules.sales.manifest import MODULE
from businessos.modules.sales.models import SalesOrder, SalesOrderLine
from businessos.modules.sales.selectors import (
    confirmed_sales_orders,
    sales_order_detail,
    sales_order_total,
    sales_orders_for_company,
)
from businessos.modules.sales.services import (
    add_sales_order_line,
    cancel_sales_order,
    confirm_sales_order,
    create_sales_order,
    remove_sales_order_line,
    update_sales_order,
    update_sales_order_line,
)


@pytest.fixture
def customer(business_context):
    return create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Northwind",
        is_customer=True,
    )


@pytest.fixture
def variant(business_context, uom):
    product = create_simple_product(
        business_context,
        name="Consulting",
        sku="CONSULT-001",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
        sales_description="Consulting day",
    )
    return product.variants.get()


@pytest.fixture
def draft_order(business_context, customer, currency):
    return create_sales_order(
        business_context,
        customer_id=customer.id,
        order_date=date(2026, 9, 13),
        currency_id=currency.id,
        notes="Priority customer",
    )


@pytest.mark.django_db
def test_manifest_and_schema_preserve_sales_boundaries():
    assert MODULE == {
        "code": "sales",
        "name": "Sales",
        "version": "0.1.0",
        "depends": ["party", "catalog", "organization", "reference", "access"],
    }
    assert SalesOrderLine._meta.get_field("product_variant").related_model is ProductVariant
    assert not any(field.name == "stock" for field in Product._meta.fields)
    assert {field.name for field in SalesOrder._meta.fields}.isdisjoint(
        {"invoice", "warehouse", "stock_quantity"}
    )


@pytest.mark.django_db
def test_create_order_and_line_snapshot_concrete_variant(
    business_context, draft_order, variant
):
    line = add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=Decimal("2.5000"),
        unit_price=Decimal("120.0000"),
    )

    assert draft_order.number.startswith("SO-")
    assert len(draft_order.number) == 35
    assert line.company_id == draft_order.company_id
    assert line.product_variant == variant
    assert line.sku_snapshot == "CONSULT-001"
    assert line.name_snapshot == "Consulting"
    assert line.description_snapshot == "Consulting day"
    assert line.position == 1


@pytest.mark.django_db
def test_draft_order_header_and_lines_can_be_updated_and_removed(
    business_context, draft_order, variant, customer, currency, uom
):
    line = add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=1,
        unit_price=10,
    )
    update_sales_order(
        business_context,
        order_id=draft_order.id,
        customer_id=customer.id,
        order_date=date(2026, 9, 14),
        currency_id=currency.id,
        notes="Updated",
    )
    replacement = create_simple_product(
        business_context,
        name="Replacement service",
        sku="REPLACE-001",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
        sales_description="Replacement description",
    ).variants.get()
    update_sales_order_line(
        business_context,
        line_id=line.id,
        product_variant_id=replacement.id,
        quantity=3,
        unit_price=12,
        description="Updated snapshot",
    )
    line.refresh_from_db()
    draft_order.refresh_from_db()
    assert draft_order.notes == "Updated"
    assert line.product_variant == replacement
    assert line.sku_snapshot == "REPLACE-001"
    assert line.name_snapshot == "Replacement service"
    assert line.quantity == 3
    assert line.description_snapshot == "Updated snapshot"
    assert line.position == 1

    draft_order.number = "SO-CHANGED"
    with pytest.raises(ValidationError, match="number cannot be changed"):
        draft_order.save()

    remove_sales_order_line(business_context, line_id=line.id)
    assert not SalesOrderLine.objects.filter(id=line.id).exists()


@pytest.mark.django_db
def test_confirmation_requires_line_and_is_atomic_retry_safe(
    business_context, draft_order, variant
):
    with pytest.raises(ValidationError, match="at least one line"):
        confirm_sales_order(business_context, order_id=draft_order.id)
    draft_order.refresh_from_db()
    assert draft_order.status == SalesOrder.Status.DRAFT
    assert draft_order.confirmed_at is None

    add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=2,
        unit_price=25,
    )
    first = confirm_sales_order(business_context, order_id=draft_order.id)
    confirmed_at = first.confirmed_at
    second = confirm_sales_order(business_context, order_id=draft_order.id)

    assert first.status == second.status == SalesOrder.Status.CONFIRMED
    assert second.confirmed_at == confirmed_at
    assert SalesOrder.objects.filter(id=draft_order.id).count() == 1
    assert SalesOrderLine.objects.filter(sales_order=draft_order).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_confirmation_serializes_to_one_transition(
    business_context, draft_order, variant
):
    if connection.vendor != "postgresql":
        pytest.skip("Sales confirmation row-lock contract requires PostgreSQL.")
    add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=1,
        unit_price=10,
    )
    start = Barrier(2)

    def confirm():
        close_old_connections()
        try:
            start.wait(timeout=5)
            return confirm_sales_order(
                business_context, order_id=draft_order.id
            ).confirmed_at
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(confirm), executor.submit(confirm)]
        timestamps = [future.result(timeout=10) for future in futures]

    draft_order.refresh_from_db()
    assert draft_order.status == SalesOrder.Status.CONFIRMED
    assert timestamps == [draft_order.confirmed_at, draft_order.confirmed_at]


@pytest.mark.django_db
def test_confirmation_revalidates_customer_and_variant(
    business_context, draft_order, variant
):
    add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=1,
        unit_price=10,
    )
    update_product(business_context, product_id=variant.product_id, is_sellable=False)

    draft_order.status = SalesOrder.Status.CONFIRMED
    with pytest.raises(ValidationError, match="only change through lifecycle services"):
        draft_order.save()
    draft_order.refresh_from_db()
    assert draft_order.status == SalesOrder.Status.DRAFT

    with pytest.raises(PermissionDenied, match="active sellable"):
        confirm_sales_order(business_context, order_id=draft_order.id)
    draft_order.refresh_from_db()
    assert draft_order.status == SalesOrder.Status.DRAFT


@pytest.mark.django_db
def test_normal_model_save_cannot_bypass_lifecycle_services(
    business_context, draft_order, variant
):
    add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=1,
        unit_price=10,
    )

    draft_order.status = SalesOrder.Status.CONFIRMED
    with pytest.raises(ValidationError, match="only change through lifecycle services"):
        draft_order.save()
    draft_order.refresh_from_db()
    assert draft_order.status == SalesOrder.Status.DRAFT

    confirmed = confirm_sales_order(business_context, order_id=draft_order.id)
    assert confirmed.status == SalesOrder.Status.CONFIRMED

    confirmed.status = SalesOrder.Status.CANCELLED
    with pytest.raises(ValidationError, match="only change through lifecycle services"):
        confirmed.save()
    confirmed.refresh_from_db()
    assert confirmed.status == SalesOrder.Status.CONFIRMED

    cancelled = cancel_sales_order(business_context, order_id=draft_order.id)
    assert cancelled.status == SalesOrder.Status.CANCELLED


@pytest.mark.django_db(transaction=True)
def test_concurrent_line_additions_receive_unique_internal_positions(
    business_context, draft_order, variant
):
    if connection.vendor != "postgresql":
        pytest.skip("Sales line-position row-lock contract requires PostgreSQL.")
    start = Barrier(2)

    def add_line():
        close_old_connections()
        try:
            start.wait(timeout=5)
            return add_sales_order_line(
                business_context,
                order_id=draft_order.id,
                product_variant_id=variant.id,
                quantity=1,
                unit_price=10,
            ).position
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(add_line), executor.submit(add_line)]
        positions = [future.result(timeout=10) for future in futures]

    assert sorted(positions) == [1, 2]
    assert list(
        SalesOrderLine.objects.filter(sales_order=draft_order)
        .order_by("position")
        .values_list("position", flat=True)
    ) == [1, 2]


@pytest.mark.django_db
def test_confirmed_order_and_lines_are_immutable_through_service_and_model(
    business_context, draft_order, variant
):
    line = add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=1,
        unit_price=10,
    )
    confirm_sales_order(business_context, order_id=draft_order.id)

    with pytest.raises(ValidationError, match="Only draft"):
        update_sales_order(business_context, order_id=draft_order.id, notes="No")
    with pytest.raises(ValidationError, match="Only draft"):
        update_sales_order_line(
            business_context,
            line_id=line.id,
            product_variant_id=variant.id,
            quantity=2,
            unit_price=10,
            description="No",
        )
    with pytest.raises(ValidationError, match="Only draft"):
        remove_sales_order_line(business_context, line_id=line.id)

    draft_order.refresh_from_db()
    draft_order.notes = "Direct bypass"
    with pytest.raises(ValidationError, match="immutable"):
        draft_order.save()
    line.refresh_from_db()
    line.quantity = 9
    with pytest.raises(ValidationError, match="only be changed"):
        line.save()
    with pytest.raises(ValidationError, match="only be removed"):
        line.delete()


@pytest.mark.django_db
def test_confirmed_order_can_be_cancelled_explicitly_and_retry_is_safe(
    business_context, draft_order, variant, customer, currency
):
    with pytest.raises(ValidationError, match="Only a confirmed"):
        cancel_sales_order(business_context, order_id=draft_order.id)
    add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=1,
        unit_price=10,
    )
    confirmed = confirm_sales_order(business_context, order_id=draft_order.id)
    cancelled = cancel_sales_order(business_context, order_id=draft_order.id)
    repeated = cancel_sales_order(business_context, order_id=draft_order.id)

    assert cancelled.status == repeated.status == SalesOrder.Status.CANCELLED
    assert repeated.confirmed_at == confirmed.confirmed_at
    with pytest.raises(ValidationError, match="cancelled"):
        confirm_sales_order(business_context, order_id=draft_order.id)
    with pytest.raises(ValidationError, match="Only draft"):
        update_sales_order(
            business_context,
            order_id=draft_order.id,
            customer_id=customer.id,
            currency_id=currency.id,
        )


@pytest.mark.django_db
def test_invalid_customer_variant_quantity_and_price_are_rejected(
    business_context, company, currency, uom, draft_order
):
    supplier = create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Supplier only",
        is_supplier=True,
    )
    with pytest.raises(PermissionDenied, match="active customer"):
        create_sales_order(
            business_context,
            customer_id=supplier.id,
            order_date=date.today(),
            currency_id=currency.id,
        )
    product = create_simple_product(
        business_context,
        name="Not for sale",
        sku="NO-SALE",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
        is_sellable=False,
    )
    with pytest.raises(PermissionDenied, match="active sellable"):
        add_sales_order_line(
            business_context,
            order_id=draft_order.id,
            product_variant_id=product.variants.get().id,
            quantity=1,
            unit_price=1,
        )
    sellable = create_variable_product(
        business_context,
        name="Variable service",
        variants=[{"sku": "VAR-1", "is_default": True}],
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
    ).variants.get()
    with pytest.raises(ValidationError, match="greater than zero"):
        add_sales_order_line(
            business_context,
            order_id=draft_order.id,
            product_variant_id=sellable.id,
            quantity=0,
            unit_price=1,
        )
    with pytest.raises(ValidationError, match="cannot be negative"):
        add_sales_order_line(
            business_context,
            order_id=draft_order.id,
            product_variant_id=sellable.id,
            quantity=1,
            unit_price=-1,
        )
    assert not SalesOrderLine.objects.filter(company=company).exists()


@pytest.mark.django_db
def test_cross_company_composition_and_reads_are_rejected(
    business_context, company, currency, uom, customer, draft_order
):
    other_company = Company.objects.create(
        code="OTHER", name="Other Company", base_currency=currency
    )
    other_user = get_user_model().objects.create_user("other-sales@example.com", "password")
    UserCompanyAccess.objects.create(user=other_user, company=other_company)
    other_context = BusinessContext(actor_id=other_user.id, company_id=other_company.id)
    other_customer = create_party(
        other_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Other Customer",
        is_customer=True,
    )
    other_variant = create_simple_product(
        other_context,
        name="Other Service",
        sku="OTHER-1",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
    ).variants.get()

    with pytest.raises(PermissionDenied):
        create_sales_order(
            business_context,
            customer_id=other_customer.id,
            order_date=date.today(),
            currency_id=currency.id,
        )
    with pytest.raises(PermissionDenied):
        add_sales_order_line(
            business_context,
            order_id=draft_order.id,
            product_variant_id=other_variant.id,
            quantity=1,
            unit_price=10,
        )
    with pytest.raises(PermissionDenied):
        update_sales_order(other_context, order_id=draft_order.id, notes="Cross company")
    with pytest.raises(SalesOrder.DoesNotExist):
        sales_order_detail(other_context, order_id=draft_order.id)
    assert list(sales_orders_for_company(other_context)) == []
    assert draft_order.company == company
    assert draft_order.customer == customer


@pytest.mark.django_db
def test_selectors_derive_totals_and_scope_status(
    business_context, draft_order, variant
):
    add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=2,
        unit_price=10,
    )
    add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=Decimal("0.5"),
        unit_price=8,
    )
    assert sales_order_total(business_context, order_id=draft_order.id) == Decimal("24")
    assert list(sales_orders_for_company(business_context, search="north")) == [draft_order]
    assert list(confirmed_sales_orders(business_context)) == []

    confirm_sales_order(business_context, order_id=draft_order.id)
    assert list(confirmed_sales_orders(business_context)) == [draft_order]
