from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError

from businessos.modules.sales.models import SalesOrder, SalesOrderLine
from businessos.modules.sales.services import (
    add_sales_order_line,
    cancel_sales_order,
    confirm_sales_order,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("company_id", uuid4()),
        ("number", "SO-BULK-BYPASS"),
        ("customer_id", uuid4()),
        ("order_date", date(2026, 9, 15)),
        ("currency_id", uuid4()),
        ("status", SalesOrder.Status.CONFIRMED),
        ("notes", "Bulk bypass"),
        ("confirmed_at", None),
    ],
)
def test_sales_order_queryset_update_rejects_every_business_field(
    draft_order, field, value
):
    before = SalesOrder.objects.values().get(pk=draft_order.pk)

    with pytest.raises(ValidationError, match="bulk updates are unsupported"):
        SalesOrder.objects.filter(pk=draft_order.pk).update(**{field: value})

    assert SalesOrder.objects.values().get(pk=draft_order.pk) == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("company_id", uuid4()),
        ("number", "SO-BULK-UPDATE"),
        ("customer_id", uuid4()),
        ("order_date", date(2026, 9, 15)),
        ("currency_id", uuid4()),
        ("status", SalesOrder.Status.CONFIRMED),
        ("notes", "Bulk update bypass"),
        ("confirmed_at", None),
    ],
)
def test_sales_order_bulk_update_rejects_every_business_field(
    draft_order, field, value
):
    before = SalesOrder.objects.values().get(pk=draft_order.pk)
    setattr(draft_order, field, value)

    with pytest.raises(ValidationError, match="bulk updates are unsupported"):
        SalesOrder.objects.bulk_update([draft_order], [field])

    assert SalesOrder.objects.values().get(pk=draft_order.pk) == before


@pytest.mark.django_db
def test_sales_order_bulk_create_and_conflict_upsert_are_rejected(draft_order):
    new_order = SalesOrder(
        company_id=draft_order.company_id,
        number="SO-BULK-CREATE",
        customer_id=draft_order.customer_id,
        order_date=draft_order.order_date,
        currency_id=draft_order.currency_id,
    )
    with pytest.raises(ValidationError, match="bulk creation/upsert is unsupported"):
        SalesOrder.objects.bulk_create([new_order])

    upsert = SalesOrder(
        id=draft_order.id,
        company_id=draft_order.company_id,
        number=draft_order.number,
        customer_id=draft_order.customer_id,
        order_date=draft_order.order_date,
        currency_id=draft_order.currency_id,
        notes="Conflict upsert bypass",
    )
    with pytest.raises(ValidationError, match="bulk creation/upsert is unsupported"):
        SalesOrder.objects.bulk_create(
            [upsert],
            update_conflicts=True,
            update_fields=["notes"],
            unique_fields=["id"],
        )

    draft_order.refresh_from_db()
    assert draft_order.notes == "Priority customer"
    assert not SalesOrder.objects.filter(number="SO-BULK-CREATE").exists()


@pytest.fixture
def draft_line(business_context, draft_order, variant):
    return add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=Decimal("1"),
        unit_price=Decimal("10"),
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("company_id", uuid4()),
        ("sales_order_id", uuid4()),
        ("product_variant_id", uuid4()),
        ("sku_snapshot", "BULK-SKU"),
        ("name_snapshot", "Bulk name"),
        ("description_snapshot", "Bulk description"),
        ("quantity", Decimal("2")),
        ("unit_price", Decimal("20")),
        ("position", 99),
    ],
)
def test_sales_line_queryset_update_rejects_every_business_field(
    draft_line, field, value
):
    before = SalesOrderLine.objects.values().get(pk=draft_line.pk)

    with pytest.raises(ValidationError, match="bulk updates are unsupported"):
        SalesOrderLine.objects.filter(pk=draft_line.pk).update(**{field: value})

    assert SalesOrderLine.objects.values().get(pk=draft_line.pk) == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "field,value",
    [
        ("company_id", uuid4()),
        ("sales_order_id", uuid4()),
        ("product_variant_id", uuid4()),
        ("sku_snapshot", "BULK-SKU"),
        ("name_snapshot", "Bulk name"),
        ("description_snapshot", "Bulk description"),
        ("quantity", Decimal("2")),
        ("unit_price", Decimal("20")),
        ("position", 99),
    ],
)
def test_sales_line_bulk_update_rejects_every_business_field(
    draft_line, field, value
):
    before = SalesOrderLine.objects.values().get(pk=draft_line.pk)
    setattr(draft_line, field, value)

    with pytest.raises(ValidationError, match="bulk updates are unsupported"):
        SalesOrderLine.objects.bulk_update([draft_line], [field])

    assert SalesOrderLine.objects.values().get(pk=draft_line.pk) == before


@pytest.mark.django_db
def test_sales_line_bulk_create_and_conflict_upsert_are_rejected(draft_line):
    new_line = SalesOrderLine(
        company_id=draft_line.company_id,
        sales_order_id=draft_line.sales_order_id,
        product_variant_id=draft_line.product_variant_id,
        sku_snapshot="BULK-LINE",
        name_snapshot="Bulk line",
        quantity=Decimal("1"),
        unit_price=Decimal("1"),
        position=2,
    )
    with pytest.raises(ValidationError, match="bulk creation/upsert is unsupported"):
        SalesOrderLine.objects.bulk_create([new_line])

    upsert = SalesOrderLine(
        id=draft_line.id,
        company_id=draft_line.company_id,
        sales_order_id=draft_line.sales_order_id,
        product_variant_id=draft_line.product_variant_id,
        sku_snapshot=draft_line.sku_snapshot,
        name_snapshot=draft_line.name_snapshot,
        description_snapshot=draft_line.description_snapshot,
        quantity=Decimal("99"),
        unit_price=draft_line.unit_price,
        position=draft_line.position,
    )
    with pytest.raises(ValidationError, match="bulk creation/upsert is unsupported"):
        SalesOrderLine.objects.bulk_create(
            [upsert],
            update_conflicts=True,
            update_fields=["quantity"],
            unique_fields=["id"],
        )

    draft_line.refresh_from_db()
    assert draft_line.quantity == Decimal("1")
    assert SalesOrderLine.objects.filter(sales_order_id=draft_line.sales_order_id).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("final_status", [SalesOrder.Status.CONFIRMED, SalesOrder.Status.CANCELLED])
def test_queryset_delete_cannot_remove_confirmed_or_cancelled_history(
    business_context, draft_order, draft_line, final_status
):
    confirm_sales_order(business_context, order_id=draft_order.id)
    if final_status == SalesOrder.Status.CANCELLED:
        cancel_sales_order(business_context, order_id=draft_order.id)

    with pytest.raises(ValidationError, match="queryset deletion is unsupported"):
        SalesOrderLine.objects.filter(pk=draft_line.pk).delete()
    with pytest.raises(ValidationError, match="queryset deletion is unsupported"):
        SalesOrder.objects.filter(pk=draft_order.pk).delete()

    assert SalesOrder.objects.filter(pk=draft_order.pk, status=final_status).exists()
    assert SalesOrderLine.objects.filter(pk=draft_line.pk).exists()


@pytest.mark.django_db
def test_private_transition_path_rejects_arbitrary_lifecycle_edges(draft_order):
    with pytest.raises(ValidationError, match="Unsupported Sales Order lifecycle transition"):
        SalesOrder.objects.get_queryset()._transition_locked_order(
            order_id=draft_order.id,
            expected_status=SalesOrder.Status.DRAFT,
            target_status=SalesOrder.Status.CANCELLED,
            changed_at=draft_order.updated_at,
        )

    draft_order.refresh_from_db()
    assert draft_order.status == SalesOrder.Status.DRAFT
