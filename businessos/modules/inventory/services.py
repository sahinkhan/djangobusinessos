from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Warehouse
from businessos.modules.catalog.models import Product, ProductVariant

from .models import StockMovement, StockMovementLine


def _quantity(value) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValidationError({"quantity": "Enter a valid quantity."}) from exc
    if not result.is_finite() or result <= 0:
        raise ValidationError({"quantity": "Quantity must be finite and greater than zero."})
    if result.as_tuple().exponent < -4 or len(result.as_tuple().digits) > 18:
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


def _variant(context: BusinessContext, variant_id):
    try:
        variant = ProductVariant.objects.select_related("product", "product__default_uom").get(
            id=variant_id, company_id=context.company_id
        )
    except ProductVariant.DoesNotExist as exc:
        raise ValidationError(
            {"product_variant": "Select a variant from the active company."}
        ) from exc
    if not variant.is_active or not variant.product.is_active:
        raise ValidationError({"product_variant": "An active product variant is required."})
    if variant.product.product_type == Product.Type.SERVICE:
        raise ValidationError({"product_variant": "Service products cannot carry stock."})
    return variant


def _warehouse(context: BusinessContext, warehouse_id, field):
    if warehouse_id is None:
        return None
    try:
        warehouse = Warehouse.objects.get(id=warehouse_id, company_id=context.company_id)
    except Warehouse.DoesNotExist as exc:
        raise ValidationError({field: "Select a warehouse from the active company."}) from exc
    if not warehouse.is_active:
        raise ValidationError({field: "An active warehouse is required."})
    return warehouse


def _validate_route(movement_type, source, destination):
    if movement_type == StockMovement.Type.RECEIPT and (source is not None or destination is None):
        raise ValidationError("A receipt requires only a destination warehouse.")
    if movement_type == StockMovement.Type.ISSUE and (source is None or destination is not None):
        raise ValidationError("An issue requires only a source warehouse.")
    if movement_type == StockMovement.Type.TRANSFER and (source is None or destination is None):
        raise ValidationError("A transfer requires source and destination warehouses.")
    if source is not None and destination is not None and source.id == destination.id:
        raise ValidationError("Source and destination warehouses must differ.")


@transaction.atomic
def create_stock_movement(
    context: BusinessContext,
    *,
    number,
    movement_type,
    effective_at,
    reference="",
    notes="",
    idempotency_key=None,
    source_module=None,
    source_type=None,
    source_id=None,
):
    key = idempotency_key.strip() if idempotency_key else None
    source_module, source_type, source_id = _source(source_module, source_type, source_id)
    movement = StockMovement(
        company_id=context.company_id,
        number=number,
        movement_type=movement_type,
        effective_at=effective_at,
        reference=reference,
        notes=notes,
        idempotency_key=key,
        source_module=source_module,
        source_type=source_type,
        source_id=source_id,
    )
    movement.full_clean(validate_unique=False, validate_constraints=False)
    try:
        with transaction.atomic():
            movement.save()
    except IntegrityError as exc:
        if (
            key
            and StockMovement.objects.filter(
                company_id=context.company_id, idempotency_key=key
            ).exists()
        ):
            raise ValidationError(
                {"idempotency_key": "This idempotency key is already in use."}
            ) from exc
        if StockMovement.objects.filter(
            company_id=context.company_id, number=movement.number
        ).exists():
            raise ValidationError({"number": "This movement number is already in use."}) from exc
        raise
    return movement


@transaction.atomic
def update_stock_movement(context: BusinessContext, *, movement_id, **changes):
    try:
        movement = StockMovement.objects.select_for_update().get(
            id=movement_id, company_id=context.company_id
        )
    except StockMovement.DoesNotExist as exc:
        raise ValidationError("Stock movement was not found in the active company.") from exc
    if movement.status != StockMovement.Status.DRAFT:
        raise ValidationError("Posted stock movements are immutable.")
    allowed = {"number", "movement_type", "effective_at", "reference", "notes"}
    if set(changes) - allowed:
        raise ValidationError("Only draft movement details can be updated.")
    if "movement_type" in changes and changes["movement_type"] != movement.movement_type:
        if movement.lines.exists():
            raise ValidationError("Movement type cannot change after lines are added.")
    for field, value in changes.items():
        setattr(movement, field, value)
    movement.full_clean()
    movement.save()
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
    try:
        movement = StockMovement.objects.select_for_update().get(
            id=movement_id, company_id=context.company_id
        )
    except StockMovement.DoesNotExist as exc:
        raise ValidationError("Stock movement was not found in the active company.") from exc
    if movement.status != StockMovement.Status.DRAFT:
        raise ValidationError("Lines can be added only to draft movements.")
    line = StockMovementLine(
        company_id=context.company_id, movement=movement, **_line_values(context, movement, **data)
    )
    line.save()
    return line


@transaction.atomic
def update_stock_movement_line(context: BusinessContext, *, movement_id, line_id, **data):
    try:
        movement = StockMovement.objects.select_for_update().get(
            id=movement_id, company_id=context.company_id
        )
    except StockMovement.DoesNotExist as exc:
        raise ValidationError("Stock movement was not found in the active company.") from exc
    if movement.status != StockMovement.Status.DRAFT:
        raise ValidationError("Posted stock movement lines are immutable.")
    try:
        line = StockMovementLine.objects.get(
            id=line_id, movement=movement, company_id=context.company_id
        )
    except StockMovementLine.DoesNotExist as exc:
        raise ValidationError("Stock movement line no longer exists.") from exc
    for field, value in _line_values(context, movement, **data).items():
        setattr(line, field, value)
    line.save()
    return line


@transaction.atomic
def remove_stock_movement_line(context: BusinessContext, *, movement_id, line_id):
    try:
        movement = StockMovement.objects.select_for_update().get(
            id=movement_id, company_id=context.company_id
        )
    except StockMovement.DoesNotExist as exc:
        raise ValidationError("Stock movement was not found in the active company.") from exc
    if movement.status != StockMovement.Status.DRAFT:
        raise ValidationError("Posted stock movement lines are immutable.")
    try:
        line = StockMovementLine.objects.get(
            id=line_id, movement=movement, company_id=context.company_id
        )
    except StockMovementLine.DoesNotExist as exc:
        raise ValidationError("Stock movement line no longer exists.") from exc
    line.delete()


@transaction.atomic
def post_stock_movement(context: BusinessContext, *, movement_id):
    try:
        movement = StockMovement.objects.select_for_update().get(
            id=movement_id, company_id=context.company_id
        )
    except StockMovement.DoesNotExist as exc:
        raise ValidationError("Stock movement was not found in the active company.") from exc
    if movement.status == StockMovement.Status.POSTED:
        return movement
    lines = list(
        movement.lines.select_related(
            "product_variant__product__default_uom", "source_warehouse", "destination_warehouse"
        )
    )
    if not lines:
        raise ValidationError("A stock movement requires at least one line before posting.")
    for line in lines:
        variant = _variant(context, line.product_variant_id)
        source = _warehouse(context, line.source_warehouse_id, "source_warehouse")
        destination = _warehouse(context, line.destination_warehouse_id, "destination_warehouse")
        _validate_route(movement.movement_type, source, destination)
        _quantity(line.quantity)
        if line.uom_id != variant.product.default_uom_id:
            raise ValidationError(
                f"{variant.sku} uses a different current unit of measure; "
                "conversion is not supported."
            )
        historic_uoms = (
            StockMovementLine.objects.filter(
                company_id=context.company_id,
                product_variant_id=variant.id,
                movement__status=StockMovement.Status.POSTED,
            )
            .values_list("uom_id", flat=True)
            .distinct()
        )
        if any(uom_id != line.uom_id for uom_id in historic_uoms):
            raise ValidationError(
                f"{variant.sku} conflicts with the unit of measure in posted stock history."
            )
    posted_at = timezone.now()
    updated = StockMovement.objects.filter(
        pk=movement.pk, status=StockMovement.Status.DRAFT
    ).update(status=StockMovement.Status.POSTED, posted_at=posted_at, updated_at=posted_at)
    if updated != 1:
        raise ValidationError("Stock movement could not be posted.")
    movement.status = StockMovement.Status.POSTED
    movement.posted_at = posted_at
    movement.updated_at = posted_at
    return movement
