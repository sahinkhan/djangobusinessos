from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from businessos.core.audit.models import AuditEntry
from businessos.modules.catalog.services import update_product
from businessos.modules.procurement import services as procurement_services
from businessos.modules.procurement.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseReceipt,
    PurchaseReceiptLine,
)
from businessos.modules.procurement.selectors import (
    purchase_order_detail,
    purchase_order_total,
    received_quantity_for_line,
    remaining_quantity_for_line,
)
from businessos.modules.procurement.services import (
    add_purchase_order_line,
    cancel_purchase_order,
    confirm_purchase_order,
    create_purchase_order,
    receive_purchase_order,
    update_purchase_order,
    update_purchase_order_line,
)


@pytest.fixture
def purchase_line(business_context, draft_purchase_order, purchasable_variant):
    return add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=Decimal("5"),
        unit_cost=Decimal("12.3456"),
    )


@pytest.fixture
def confirmed_purchase_order(business_context, draft_purchase_order, purchase_line):
    return confirm_purchase_order(business_context, order_id=draft_purchase_order.id)


def _receipt(context, order, line, quantity="2", key="receipt-1", receipt_date=None):
    return receive_purchase_order(
        context,
        purchase_order_id=order.id,
        receipt_date=receipt_date or date(2026, 9, 14),
        idempotency_key=key,
        lines=[
            {
                "purchase_order_line_id": line.id,
                "quantity_received": Decimal(quantity),
            }
        ],
    )


@pytest.mark.django_db
def test_purchase_order_lifecycle_snapshots_totals_and_audit(
    business_context, draft_purchase_order, purchase_line
):
    assert purchase_line.sku_snapshot == "BUY-001"
    assert purchase_line.name_snapshot == "Purchased consulting"
    assert purchase_line.description_snapshot == "Supplier service day"
    assert purchase_order_total(business_context, order_id=draft_purchase_order.id) == Decimal(
        "61.72800000"
    )

    update_purchase_order(business_context, order_id=draft_purchase_order.id, notes="Updated")
    update_purchase_order_line(
        business_context,
        line_id=purchase_line.id,
        product_variant_id=purchase_line.product_variant_id,
        quantity=Decimal("5"),
        unit_cost=Decimal("12.3456"),
        description="Updated snapshot",
    )
    confirmed = confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    retry = confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    assert confirmed.id == retry.id
    assert confirmed.status == PurchaseOrder.Status.CONFIRMED
    assert (
        AuditEntry.objects.filter(
            action="procurement.order.confirmed", object_id=str(confirmed.id)
        ).count()
        == 1
    )

    cancelled = cancel_purchase_order(business_context, order_id=confirmed.id)
    retry = cancel_purchase_order(business_context, order_id=confirmed.id)
    assert retry.id == cancelled.id
    assert cancelled.status == PurchaseOrder.Status.CANCELLED
    assert (
        AuditEntry.objects.filter(
            action="procurement.order.cancelled", object_id=str(confirmed.id)
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_confirmation_requires_line_and_cancelled_cannot_reconfirm(
    business_context, draft_purchase_order, purchase_line
):
    purchase_line.delete()
    with pytest.raises(ValidationError, match="requires at least one line"):
        confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchase_line.product_variant_id,
        quantity=1,
        unit_cost=1,
    )
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    cancel_purchase_order(business_context, order_id=draft_purchase_order.id)
    with pytest.raises(ValidationError, match="cancelled"):
        confirm_purchase_order(business_context, order_id=draft_purchase_order.id)


@pytest.mark.django_db
def test_partial_multiple_receipts_are_derived_and_exact_retry_is_noop(
    business_context, confirmed_purchase_order, purchase_line
):
    first = _receipt(business_context, confirmed_purchase_order, purchase_line)
    retry = _receipt(business_context, confirmed_purchase_order, purchase_line)
    assert retry.id == first.id
    assert PurchaseReceipt.objects.count() == 1
    assert PurchaseReceiptLine.objects.count() == 1
    assert AuditEntry.objects.filter(action="procurement.receipt.posted").count() == 1
    second = _receipt(
        business_context,
        confirmed_purchase_order,
        purchase_line,
        quantity="3",
        key="receipt-2",
    )
    assert second.id != first.id
    assert received_quantity_for_line(
        business_context, purchase_order_line_id=purchase_line.id
    ) == Decimal("5")
    assert remaining_quantity_for_line(
        business_context, purchase_order_line_id=purchase_line.id
    ) == Decimal("0")
    detail = purchase_order_detail(business_context, order_id=confirmed_purchase_order.id)
    assert detail.lines.get().remaining_quantity == 0


@pytest.mark.django_db
def test_receipt_rejects_overreceipt_conflict_precision_and_empty_payload(
    business_context, confirmed_purchase_order, purchase_line
):
    _receipt(business_context, confirmed_purchase_order, purchase_line, quantity="4")
    for quantity, message in [
        ("2", "exceeds"),
        ("0.12345", "four decimal places"),
        ("0", "greater than zero"),
    ]:
        with pytest.raises(ValidationError, match=message):
            _receipt(
                business_context,
                confirmed_purchase_order,
                purchase_line,
                quantity=quantity,
                key=f"bad-{quantity}",
            )
    with pytest.raises(ValidationError, match="requires at least one line"):
        receive_purchase_order(
            business_context,
            purchase_order_id=confirmed_purchase_order.id,
            receipt_date=date(2026, 9, 14),
            idempotency_key="empty",
            lines=[],
        )
    with pytest.raises(ValidationError, match="different Purchase Receipt"):
        _receipt(
            business_context,
            confirmed_purchase_order,
            purchase_line,
            quantity="1",
            key="receipt-1",
        )


@pytest.mark.django_db
def test_iso_date_retry_is_canonical(business_context, confirmed_purchase_order, purchase_line):
    first = _receipt(
        business_context,
        confirmed_purchase_order,
        purchase_line,
        key="date-key",
        receipt_date="2026-09-14",
    )
    retry = _receipt(
        business_context,
        confirmed_purchase_order,
        purchase_line,
        key="date-key",
        receipt_date="2026-09-14",
    )
    assert retry.id == first.id


@pytest.mark.django_db
def test_order_with_receipt_cannot_cancel(
    business_context, confirmed_purchase_order, purchase_line
):
    _receipt(business_context, confirmed_purchase_order, purchase_line)
    with pytest.raises(ValidationError, match="with receipts"):
        cancel_purchase_order(business_context, order_id=confirmed_purchase_order.id)


@pytest.mark.django_db
def test_cross_company_line_and_receipt_composition_fail_closed(
    business_context, confirmed_purchase_order, purchase_line
):
    from businessos.core.organization.models import Company

    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=confirmed_purchase_order.currency,
        country=confirmed_purchase_order.company.country,
        default_language=confirmed_purchase_order.company.default_language,
    )
    purchase_line.company = other
    with pytest.raises(ValidationError):
        purchase_line.save()
    with pytest.raises(PermissionDenied):
        receive_purchase_order(
            business_context,
            purchase_order_id=confirmed_purchase_order.id,
            receipt_date=date(2026, 9, 14),
            idempotency_key="foreign-line",
            lines=[
                {
                    "purchase_order_line_id": "00000000-0000-0000-0000-000000000001",
                    "quantity_received": "1",
                }
            ],
        )


@pytest.mark.django_db
def test_transition_and_receipt_audit_roll_back_atomically(
    business_context, draft_purchase_order, purchase_line, monkeypatch
):
    real_audit = procurement_services.record_audit_entry

    def unavailable(**kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(procurement_services, "record_audit_entry", unavailable)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    draft_purchase_order.refresh_from_db()
    assert draft_purchase_order.status == PurchaseOrder.Status.DRAFT

    monkeypatch.setattr(procurement_services, "record_audit_entry", real_audit)
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    monkeypatch.setattr(procurement_services, "record_audit_entry", unavailable)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        _receipt(business_context, draft_purchase_order, purchase_line)
    assert not PurchaseReceipt.objects.exists()
    assert not PurchaseReceiptLine.objects.exists()


@pytest.mark.django_db
def test_receipt_audit_metadata_and_duplicate_line_rejection(
    business_context, confirmed_purchase_order, purchase_line
):
    with pytest.raises(ValidationError, match="only once"):
        receive_purchase_order(
            business_context,
            purchase_order_id=confirmed_purchase_order.id,
            receipt_date="2026-09-14",
            idempotency_key="duplicate-lines",
            lines=[
                {"purchase_order_line_id": purchase_line.id, "quantity_received": "1"},
                {"purchase_order_line_id": purchase_line.id, "quantity_received": "1"},
            ],
        )
    receipt = _receipt(business_context, confirmed_purchase_order, purchase_line)
    audit = AuditEntry.objects.get(action="procurement.receipt.posted", object_id=str(receipt.id))
    assert audit.actor_id == business_context.actor_id
    assert audit.company_id == business_context.company_id
    assert audit.object_type == "procurement.PurchaseReceipt"
    assert audit.metadata == {
        "number": receipt.number,
        "purchase_order_id": str(confirmed_purchase_order.id),
        "idempotency_key": "receipt-1",
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "final_status", [PurchaseOrder.Status.CONFIRMED, PurchaseOrder.Status.CANCELLED]
)
def test_historical_line_delete_rejects_in_memory_parent_substitution(
    business_context,
    draft_purchase_order,
    purchase_line,
    supplier,
    currency,
    final_status,
):
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    if final_status == PurchaseOrder.Status.CANCELLED:
        cancel_purchase_order(business_context, order_id=draft_purchase_order.id)
    other_draft = create_purchase_order(
        business_context,
        supplier_id=supplier.id,
        order_date=date(2026, 9, 15),
        currency_id=currency.id,
    )
    stale_line = PurchaseOrderLine.objects.get(pk=purchase_line.pk)
    original_total = purchase_order_total(business_context, order_id=draft_purchase_order.id)
    stale_line.purchase_order_id = other_draft.id

    with pytest.raises(ValidationError, match="ownership cannot be reassigned"):
        stale_line.delete()

    assert PurchaseOrderLine.objects.filter(
        pk=purchase_line.pk, purchase_order=draft_purchase_order
    ).exists()
    assert draft_purchase_order.lines.count() == 1
    assert (
        purchase_order_total(business_context, order_id=draft_purchase_order.id) == original_total
    )


@pytest.mark.django_db
def test_partially_received_order_line_delete_rejects_parent_substitution(
    business_context, draft_purchase_order, purchase_line, purchasable_variant, supplier, currency
):
    other_line = add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=Decimal("3"),
        unit_cost=Decimal("4"),
    )
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    _receipt(business_context, draft_purchase_order, purchase_line, quantity="1")
    other_draft = create_purchase_order(
        business_context,
        supplier_id=supplier.id,
        order_date=date(2026, 9, 15),
        currency_id=currency.id,
    )
    stale_line = PurchaseOrderLine.objects.get(pk=other_line.pk)
    original_total = purchase_order_total(business_context, order_id=draft_purchase_order.id)
    stale_line.purchase_order_id = other_draft.id

    with pytest.raises(ValidationError, match="ownership cannot be reassigned"):
        stale_line.delete()

    assert PurchaseOrderLine.objects.filter(
        pk=other_line.pk, purchase_order=draft_purchase_order
    ).exists()
    assert (
        purchase_order_total(business_context, order_id=draft_purchase_order.id) == original_total
    )


@pytest.mark.django_db
def test_draft_line_delete_rejects_in_memory_parent_substitution(
    business_context, draft_purchase_order, purchase_line, supplier, currency
):
    other_draft = create_purchase_order(
        business_context,
        supplier_id=supplier.id,
        order_date=date(2026, 9, 15),
        currency_id=currency.id,
    )
    stale_line = PurchaseOrderLine.objects.get(pk=purchase_line.pk)
    original_total = purchase_order_total(business_context, order_id=draft_purchase_order.id)
    stale_line.purchase_order_id = other_draft.id

    with pytest.raises(ValidationError, match="ownership cannot be reassigned"):
        stale_line.delete()

    assert PurchaseOrderLine.objects.filter(
        pk=purchase_line.pk, purchase_order=draft_purchase_order
    ).exists()
    assert other_draft.lines.count() == 0
    assert (
        purchase_order_total(business_context, order_id=draft_purchase_order.id) == original_total
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "catalog_changes, expected_sku, expected_name",
    [
        ({"sku": "REFRESH-SKU"}, "REFRESH-SKU", "Purchased consulting"),
        ({"name": "Renamed purchase"}, "BUY-001", "Renamed purchase"),
        ({"sku": "REFRESH-BOTH", "name": "Renamed together"}, "REFRESH-BOTH", "Renamed together"),
    ],
    ids=["sku-only", "name-only", "sku-and-name"],
)
def test_snapshot_only_line_refresh_records_one_update_audit(
    business_context,
    draft_purchase_order,
    purchase_line,
    catalog_changes,
    expected_sku,
    expected_name,
):
    before = AuditEntry.objects.filter(
        action="procurement.order.updated", object_id=str(draft_purchase_order.id)
    ).count()
    update_product(
        business_context, product_id=purchase_line.product_variant.product_id, **catalog_changes
    )

    update_purchase_order_line(
        business_context,
        line_id=purchase_line.id,
        product_variant_id=purchase_line.product_variant_id,
        quantity=purchase_line.quantity,
        unit_cost=purchase_line.unit_cost,
        description=purchase_line.description_snapshot,
    )

    purchase_line.refresh_from_db()
    assert purchase_line.sku_snapshot == expected_sku
    assert purchase_line.name_snapshot == expected_name
    assert (
        AuditEntry.objects.filter(
            action="procurement.order.updated", object_id=str(draft_purchase_order.id)
        ).count()
        == before + 1
    )


@pytest.mark.django_db
def test_true_noop_line_update_does_not_record_audit(
    business_context, draft_purchase_order, purchase_line
):
    before = AuditEntry.objects.filter(
        action="procurement.order.updated", object_id=str(draft_purchase_order.id)
    ).count()
    update_purchase_order_line(
        business_context,
        line_id=purchase_line.id,
        product_variant_id=purchase_line.product_variant_id,
        quantity=purchase_line.quantity,
        unit_cost=purchase_line.unit_cost,
        description=purchase_line.description_snapshot,
    )
    assert (
        AuditEntry.objects.filter(
            action="procurement.order.updated", object_id=str(draft_purchase_order.id)
        ).count()
        == before
    )


@pytest.mark.django_db
def test_snapshot_refresh_rolls_back_when_audit_fails(business_context, purchase_line, monkeypatch):
    original = (
        purchase_line.product_variant_id,
        purchase_line.sku_snapshot,
        purchase_line.name_snapshot,
        purchase_line.description_snapshot,
        purchase_line.quantity,
        purchase_line.unit_cost,
    )
    update_product(
        business_context,
        product_id=purchase_line.product_variant.product_id,
        sku="ROLLBACK-SKU",
        name="Rollback name",
    )
    audit_count = AuditEntry.objects.count()

    def unavailable_audit(**kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(procurement_services, "record_audit_entry", unavailable_audit)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        update_purchase_order_line(
            business_context,
            line_id=purchase_line.id,
            product_variant_id=purchase_line.product_variant_id,
            quantity=purchase_line.quantity,
            unit_cost=purchase_line.unit_cost,
            description=purchase_line.description_snapshot,
        )

    purchase_line.refresh_from_db()
    assert (
        purchase_line.product_variant_id,
        purchase_line.sku_snapshot,
        purchase_line.name_snapshot,
        purchase_line.description_snapshot,
        purchase_line.quantity,
        purchase_line.unit_cost,
    ) == original
    assert AuditEntry.objects.count() == audit_count


@pytest.mark.django_db
@pytest.mark.parametrize("non_finite", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
@pytest.mark.parametrize("field_name", ["quantity", "unit_cost"])
def test_non_finite_line_values_fail_with_validation_error_and_roll_back(
    business_context, purchase_line, non_finite, field_name
):
    original = (purchase_line.quantity, purchase_line.unit_cost)
    audit_count = AuditEntry.objects.count()
    values = {"quantity": purchase_line.quantity, "unit_cost": purchase_line.unit_cost}
    values[field_name] = non_finite

    with pytest.raises(ValidationError) as exc_info:
        update_purchase_order_line(
            business_context,
            line_id=purchase_line.id,
            product_variant_id=purchase_line.product_variant_id,
            description=purchase_line.description_snapshot,
            **values,
        )

    assert field_name in exc_info.value.message_dict
    assert any("finite" in message for message in exc_info.value.message_dict[field_name])
    purchase_line.refresh_from_db()
    assert (purchase_line.quantity, purchase_line.unit_cost) == original
    assert AuditEntry.objects.count() == audit_count
