from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from businessos.modules.procurement.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseReceipt,
    PurchaseReceiptLine,
)
from businessos.modules.procurement.services import (
    add_purchase_order_line,
    confirm_purchase_order,
    receive_purchase_order,
)


@pytest.fixture
def line(business_context, draft_purchase_order, purchasable_variant):
    return add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=Decimal("2"),
        unit_cost=Decimal("5"),
    )


@pytest.fixture
def receipt(business_context, draft_purchase_order, line):
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    return receive_purchase_order(
        business_context,
        purchase_order_id=draft_purchase_order.id,
        receipt_date=date(2026, 9, 14),
        idempotency_key="hardening",
        lines=[{"purchase_order_line_id": line.id, "quantity_received": "1"}],
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model", [PurchaseOrder, PurchaseOrderLine, PurchaseReceipt, PurchaseReceiptLine]
)
def test_public_queryset_update_and_delete_are_blocked(model):
    with pytest.raises(ValidationError, match="bulk updates are unsupported"):
        model.objects.all().update(updated_at=None)
    with pytest.raises(ValidationError, match="queryset deletion is unsupported"):
        model.objects.all().delete()


@pytest.mark.django_db
def test_order_and_line_bulk_create_update_upsert_are_blocked(draft_purchase_order, line):
    with pytest.raises(ValidationError, match="bulk creation/upsert"):
        PurchaseOrder.objects.bulk_create([draft_purchase_order])
    with pytest.raises(ValidationError, match="bulk updates"):
        PurchaseOrder.objects.bulk_update([draft_purchase_order], ["notes"])
    with pytest.raises(ValidationError, match="bulk creation/upsert"):
        PurchaseOrder.objects.bulk_create(
            [draft_purchase_order],
            update_conflicts=True,
            update_fields=["notes"],
            unique_fields=["id"],
        )
    with pytest.raises(ValidationError, match="bulk creation/upsert"):
        PurchaseOrderLine.objects.bulk_create([line])
    with pytest.raises(ValidationError, match="bulk updates"):
        PurchaseOrderLine.objects.bulk_update([line], ["quantity"])


@pytest.mark.django_db
def test_receipt_bulk_paths_and_instance_mutation_are_blocked(receipt):
    receipt_line = receipt.lines.get()
    for model, obj, field in [
        (PurchaseReceipt, receipt, "receipt_date"),
        (PurchaseReceiptLine, receipt_line, "quantity_received"),
    ]:
        with pytest.raises(ValidationError, match="bulk creation/upsert"):
            model.objects.bulk_create([obj])
        with pytest.raises(ValidationError, match="bulk updates"):
            model.objects.bulk_update([obj], [field])
        with pytest.raises(ValidationError, match="cannot be deleted"):
            obj.delete()
        if field == "receipt_date":
            obj.receipt_date = date(2026, 9, 15)
        else:
            obj.quantity_received = Decimal("1.5")
        with pytest.raises(ValidationError, match="immutable"):
            obj.save()


@pytest.mark.django_db
def test_private_transition_rejects_unsupported_edge(draft_purchase_order):
    with pytest.raises(ValidationError, match="Unsupported Purchase Order lifecycle"):
        PurchaseOrder.objects.get_queryset()._transition_locked_order(
            order_id=draft_purchase_order.id,
            expected_status=PurchaseOrder.Status.DRAFT,
            target_status=PurchaseOrder.Status.CANCELLED,
            changed_at=draft_purchase_order.updated_at,
        )


@pytest.mark.django_db
def test_private_receipt_insertion_rejects_untrusted_token(receipt):
    clone = PurchaseReceipt(
        company=receipt.company,
        number="PR-UNTRUSTED",
        purchase_order=receipt.purchase_order,
        receipt_date=receipt.receipt_date,
        idempotency_key="untrusted",
        posted_at=receipt.posted_at,
    )
    with pytest.raises(ValidationError, match="Unsupported Purchase Receipt insertion"):
        PurchaseReceipt.objects.get_queryset()._insert_posted_receipt(clone, token=object())
