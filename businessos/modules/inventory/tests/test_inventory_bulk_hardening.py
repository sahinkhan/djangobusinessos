from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from businessos.modules.inventory.models import StockMovement, StockMovementLine
from businessos.modules.inventory.services import add_stock_movement_line, post_stock_movement


@pytest.fixture
def movement_line(business_context, draft_receipt, stockable_variant, warehouse):
    return add_stock_movement_line(
        business_context,
        movement_id=draft_receipt.id,
        product_variant_id=stockable_variant.id,
        quantity="2",
        destination_warehouse_id=warehouse.id,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("model", [StockMovement, StockMovementLine])
def test_public_queryset_update_and_delete_are_blocked(model):
    with pytest.raises(ValidationError, match="bulk updates are unsupported"):
        model.objects.all().update(updated_at=None)
    with pytest.raises(ValidationError, match="queryset deletion is unsupported"):
        model.objects.all().delete()


@pytest.mark.django_db
def test_bulk_create_update_and_upsert_are_blocked(draft_receipt, movement_line):
    for model, obj, fields in [
        (StockMovement, draft_receipt, ["notes"]),
        (StockMovementLine, movement_line, ["quantity"]),
    ]:
        with pytest.raises(ValidationError, match="bulk creation/upsert"):
            model.objects.bulk_create([obj])
        with pytest.raises(ValidationError, match="bulk updates"):
            model.objects.bulk_update([obj], fields)
        with pytest.raises(ValidationError, match="bulk creation/upsert"):
            model.objects.bulk_create(
                [obj], update_conflicts=True, update_fields=fields, unique_fields=["id"]
            )


@pytest.mark.django_db
def test_instance_paths_cannot_bypass_services(
    business_context, draft_receipt, movement_line
):
    draft_receipt.notes = "Direct"
    with pytest.raises(ValidationError, match="through Inventory services"):
        draft_receipt.save()
    movement_line.quantity = Decimal("9")
    with pytest.raises(ValidationError, match="through Inventory services"):
        movement_line.save()
    with pytest.raises(ValidationError, match="through Inventory services"):
        movement_line.delete()
    post_stock_movement(business_context, movement_id=draft_receipt.id)
    with pytest.raises(ValidationError, match="through Inventory services"):
        draft_receipt.delete()


@pytest.mark.django_db
def test_private_posting_rejects_untrusted_callers(draft_receipt):
    with pytest.raises(ValidationError, match="Unsupported Stock Movement lifecycle"):
        StockMovement.objects.get_queryset()._post_locked_movement(
            movement_id=draft_receipt.id,
            expected_status=StockMovement.Status.DRAFT,
            posted_at=draft_receipt.created_at,
            token=object(),
        )
    draft_receipt.refresh_from_db()
    assert draft_receipt.status == StockMovement.Status.DRAFT
