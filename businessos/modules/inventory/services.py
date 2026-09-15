from decimal import Decimal, InvalidOperation
from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from businessos.core.access.policies import require_permission
from businessos.core.audit.services import record_audit_entry
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company, Warehouse
from businessos.modules.catalog.models import Product, ProductVariant

from .manifest import CREATE_MOVEMENTS, POST_MOVEMENTS, UPDATE_MOVEMENTS
from .models import (
    _LINE_MUTATION_TOKEN,
    _MOVEMENT_MUTATION_TOKEN,
    _POSTING_TOKEN,
    StockMovement,
    StockMovementLine,
)


def _lock_company_and_authorize(context: BusinessContext, permission_code: str) -> Company:
    company = (
        Company.objects.select_for_update()
        .filter(id=context.company_id, is_active=True)
        .first()
    )
    if company is None:
        raise PermissionDenied("The selected company does not exist or is inactive.")
    require_permission(context, permission_code)
    return company


def _quantity(value) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({"quantity": "Enter a valid quantity."}) from exc
    if not result.is_finite() or result <= 0:
        raise ValidationError({"quantity": "Quantity must be finite and greater than zero."})
    if result.as_tuple().exponent < -4 or result.adjusted() > 13:
        raise ValidationError(
            {"quantity": "Quantity supports at most 14 whole and 4 decimal digits."}
        )
    return result


def _source(source_module, source_type, source_id):
    module = source_module.strip() if source_module else None
    kind = source_type.strip() if source_type else None
    values = (module, kind, source_id)
    if any(value is not None for value in values) and not all(
        value is not None for value in values
    ):
        raise ValidationError("Source module, type, and ID must be supplied together.")
    return module, kind, source_id


def _variant(context: BusinessContext, variant_id) -> ProductVariant:
    try:
        return ProductVariant.objects.select_related("product", "product__default_uom").get(
            id=variant_id,
            company_id=context.company_id,
            is_active=True,
            product__is_active=True,
            product__product_type__in=[Product.Type.STOCKABLE, Product.Type.CONSUMABLE],
            product__default_uom__is_active=True,
        )
    except ProductVariant.DoesNotExist as exc:
        raise PermissionDenied(
            "Select an active stockable or consumable variant with an active UoM "
            "in the selected company."
        ) from exc


def _warehouse(context: BusinessContext, warehouse_id, field):
    if warehouse_id is None:
        return None
    try:
        return (
            Warehouse.objects.select_related("branch")
            .filter(id=warehouse_id, company_id=context.company_id, is_active=True)
            .filter(Q(branch__isnull=True) | Q(branch__is_active=True))
            .get()
        )
    except Warehouse.DoesNotExist as exc:
        raise PermissionDenied(
            f"Select an active {field.replace('_', ' ')} in the selected company."
        ) from exc


def _validate_route(movement_type, source, destination):
    if movement_type == StockMovement.Type.RECEIPT and (source is not None or destination is None):
        raise ValidationError("A receipt requires only a destination warehouse.")
    if movement_type == StockMovement.Type.ISSUE and (source is None or destination is not None):
        raise ValidationError("An issue requires only a source warehouse.")
    if movement_type == StockMovement.Type.TRANSFER and (source is None or destination is None):
        raise ValidationError("A transfer requires source and destination warehouses.")
    if source is not None and destination is not None and source.id == destination.id:
        raise ValidationError("Source and destination warehouses must differ.")


def _locked_movement(context: BusinessContext, movement_id) -> StockMovement:
    try:
        return StockMovement.objects.select_for_update().get(
            id=movement_id, company_id=context.company_id
        )
    except StockMovement.DoesNotExist as exc:
        raise PermissionDenied("The Stock Movement is outside the selected company.") from exc


def _require_draft(movement: StockMovement):
    if movement.status != StockMovement.Status.DRAFT:
        raise ValidationError("Only draft Stock Movements may be changed.")


def _movement_number() -> str:
    return f"SM-{uuid4().hex.upper()}"


def _record_update(context, movement, **metadata):
    record_audit_entry(
        context=context,
        action="inventory.movement.updated",
        object_type="inventory.StockMovement",
        object_id=movement.id,
        metadata=metadata,
    )


@transaction.atomic
def create_stock_movement(
    context: BusinessContext,
    *,
    movement_type,
    effective_at,
    reference="",
    notes="",
    idempotency_key=None,
    source_module=None,
    source_type=None,
    source_id=None,
) -> StockMovement:
    _lock_company_and_authorize(context, CREATE_MOVEMENTS)
    if not timezone.is_aware(effective_at):
        raise ValidationError({"effective_at": "Enter a timezone-aware effective time."})
    key = idempotency_key.strip() if idempotency_key else None
    if key and StockMovement.objects.filter(
        company_id=context.company_id, idempotency_key=key
    ).exists():
        raise ValidationError({"idempotency_key": "This idempotency key is already in use."})
    source_module, source_type, source_id = _source(source_module, source_type, source_id)
    for _attempt in range(3):
        movement = StockMovement(
            company_id=context.company_id,
            number=_movement_number(),
            movement_type=movement_type,
            effective_at=effective_at,
            reference=reference,
            notes=notes,
            idempotency_key=key,
            source_module=source_module,
            source_type=source_type,
            source_id=source_id,
        )
        try:
            with transaction.atomic():
                movement.save(_inventory_token=_MOVEMENT_MUTATION_TOKEN)
        except IntegrityError as exc:
            if key and StockMovement.objects.filter(
                company_id=context.company_id, idempotency_key=key
            ).exists():
                raise ValidationError(
                    {"idempotency_key": "This idempotency key is already in use."}
                ) from exc
            if StockMovement.objects.filter(
                company_id=context.company_id, number=movement.number
            ).exists():
                continue
            raise
        record_audit_entry(
            context=context,
            action="inventory.movement.created",
            object_type="inventory.StockMovement",
            object_id=movement.id,
            metadata={"number": movement.number, "movement_type": movement.movement_type},
        )
        return movement
    raise ValidationError("A unique Stock Movement number could not be generated.")


@transaction.atomic
def update_stock_movement(context: BusinessContext, *, movement_id, **changes) -> StockMovement:
    _lock_company_and_authorize(context, UPDATE_MOVEMENTS)
    movement = _locked_movement(context, movement_id)
    _require_draft(movement)
    allowed = {"movement_type", "effective_at", "reference", "notes"}
    unknown = changes.keys() - allowed
    if unknown:
        raise ValidationError(f"Unsupported Stock Movement fields: {', '.join(sorted(unknown))}")
    if "effective_at" in changes and not timezone.is_aware(changes["effective_at"]):
        raise ValidationError({"effective_at": "Enter a timezone-aware effective time."})
    if (
        "movement_type" in changes
        and changes["movement_type"] != movement.movement_type
        and movement.lines.exists()
    ):
        raise ValidationError("Movement type cannot change after lines are added.")
    before = {field: getattr(movement, field) for field in allowed}
    for field, value in changes.items():
        setattr(movement, field, value)
    movement.save(_inventory_token=_MOVEMENT_MUTATION_TOKEN)
    changed_fields = sorted(field for field in allowed if before[field] != getattr(movement, field))
    if changed_fields:
        _record_update(context, movement, change="header", fields=changed_fields)
    return movement


def _line_values(
    context,
    movement,
    *,
    product_variant_id,
    quantity,
    source_warehouse_id=None,
    destination_warehouse_id=None,
):
    variant = _variant(context, product_variant_id)
    source = _warehouse(context, source_warehouse_id, "source_warehouse")
    destination = _warehouse(context, destination_warehouse_id, "destination_warehouse")
    _validate_route(movement.movement_type, source, destination)
    return {
        "product_variant": variant,
        "sku_snapshot": variant.sku,
        "product_name_snapshot": variant.product.name,
        "uom": variant.product.default_uom,
        "quantity": _quantity(quantity),
        "source_warehouse": source,
        "destination_warehouse": destination,
    }


@transaction.atomic
def add_stock_movement_line(context: BusinessContext, *, movement_id, **data):
    _lock_company_and_authorize(context, UPDATE_MOVEMENTS)
    movement = _locked_movement(context, movement_id)
    _require_draft(movement)
    line = StockMovementLine(
        company_id=context.company_id,
        movement=movement,
        **_line_values(context, movement, **data),
    )
    line.save(_inventory_token=_LINE_MUTATION_TOKEN)
    _record_update(
        context,
        movement,
        change="line_added",
        line_id=str(line.id),
        product_variant_id=str(line.product_variant_id),
    )
    return line


@transaction.atomic
def update_stock_movement_line(context: BusinessContext, *, movement_id, line_id, **data):
    _lock_company_and_authorize(context, UPDATE_MOVEMENTS)
    movement = _locked_movement(context, movement_id)
    _require_draft(movement)
    try:
        line = StockMovementLine.objects.get(
            id=line_id, movement_id=movement.id, company_id=context.company_id
        )
    except StockMovementLine.DoesNotExist as exc:
        raise PermissionDenied("The Stock Movement Line is outside the selected company.") from exc
    persisted_fields = (
        "product_variant_id",
        "sku_snapshot",
        "product_name_snapshot",
        "uom_id",
        "quantity",
        "source_warehouse_id",
        "destination_warehouse_id",
    )
    before = {name: getattr(line, name) for name in persisted_fields}
    for field, value in _line_values(context, movement, **data).items():
        setattr(line, field, value)
    line.save(_inventory_token=_LINE_MUTATION_TOKEN)
    changed_fields = sorted(
        name for name in persisted_fields if before[name] != getattr(line, name)
    )
    if changed_fields:
        _record_update(
            context,
            movement,
            change="line_updated",
            line_id=str(line.id),
            fields=changed_fields,
        )
    return line


@transaction.atomic
def remove_stock_movement_line(context: BusinessContext, *, movement_id, line_id) -> None:
    _lock_company_and_authorize(context, UPDATE_MOVEMENTS)
    movement = _locked_movement(context, movement_id)
    _require_draft(movement)
    try:
        line = StockMovementLine.objects.get(
            id=line_id, movement_id=movement.id, company_id=context.company_id
        )
    except StockMovementLine.DoesNotExist as exc:
        raise PermissionDenied("The Stock Movement Line is outside the selected company.") from exc
    deleted_id = line.id
    line.delete(_inventory_token=_LINE_MUTATION_TOKEN)
    _record_update(context, movement, change="line_removed", line_id=str(deleted_id))


def _validate_posting_line(context, movement, line):
    variant = _variant(context, line.product_variant_id)
    source = _warehouse(context, line.source_warehouse_id, "source_warehouse")
    destination = _warehouse(context, line.destination_warehouse_id, "destination_warehouse")
    _validate_route(movement.movement_type, source, destination)
    _quantity(line.quantity)
    if line.company_id != movement.company_id or line.uom_id != variant.product.default_uom_id:
        raise ValidationError(
            f"{variant.sku} uses an incompatible unit of measure; conversion is not supported."
        )
    if not line.uom.is_active:
        raise ValidationError(f"{variant.sku} requires an active unit of measure before posting.")
    if StockMovementLine.objects.filter(
        company_id=context.company_id,
        product_variant_id=variant.id,
        movement__status=StockMovement.Status.POSTED,
    ).exclude(uom_id=line.uom_id).exists():
        raise ValidationError(
            f"{variant.sku} conflicts with the unit of measure in posted stock history."
        )


@transaction.atomic
def post_stock_movement(context: BusinessContext, *, movement_id) -> StockMovement:
    _lock_company_and_authorize(context, POST_MOVEMENTS)
    movement = _locked_movement(context, movement_id)
    if movement.status == StockMovement.Status.POSTED:
        return movement
    lines = list(
        movement.lines.select_related(
            "product_variant__product__default_uom",
            "uom",
            "source_warehouse__branch",
            "destination_warehouse__branch",
        )
    )
    if not lines:
        raise ValidationError("A Stock Movement requires at least one line before posting.")
    for line in lines:
        _validate_posting_line(context, movement, line)
    posted_at = timezone.now()
    movement = StockMovement.objects.get_queryset()._post_locked_movement(
        movement_id=movement.id,
        expected_status=StockMovement.Status.DRAFT,
        posted_at=posted_at,
        token=_POSTING_TOKEN,
    )
    record_audit_entry(
        context=context,
        action="inventory.movement.posted",
        object_type="inventory.StockMovement",
        object_id=movement.id,
        metadata={
            "number": movement.number,
            "movement_type": movement.movement_type,
            "effective_at": movement.effective_at.isoformat(),
            "line_count": len(lines),
        },
    )
    return movement
