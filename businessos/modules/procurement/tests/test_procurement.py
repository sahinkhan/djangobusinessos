from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from businessos.core.audit.models import AuditEntry
from businessos.modules.procurement import services as procurement_services
from businessos.modules.procurement.models import (
    PurchaseOrder,
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
