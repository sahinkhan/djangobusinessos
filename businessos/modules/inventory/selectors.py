from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Q

from businessos.core.access.policies import validate_business_context
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Warehouse
from businessos.modules.catalog.models import ProductVariant

from .models import StockMovement, StockMovementLine


@dataclass(frozen=True, slots=True)
class StockBalance:
    product_variant: ProductVariant
    uom: object
    quantity: Decimal


def movements_for_company(context: BusinessContext, *, search="", movement_type="", status=""):
    validate_business_context(context)
    queryset = StockMovement.objects.filter(company_id=context.company_id)
    if search:
        queryset = queryset.filter(Q(number__icontains=search) | Q(reference__icontains=search))
    if movement_type:
        queryset = queryset.filter(movement_type=movement_type)
    if status:
        queryset = queryset.filter(status=status)
    return queryset


def movement_detail(context: BusinessContext, *, movement_id):
    validate_business_context(context)
    return (
        StockMovement.objects.filter(company_id=context.company_id)
        .prefetch_related(
            "lines__product_variant__product",
            "lines__uom",
            "lines__source_warehouse",
            "lines__destination_warehouse",
        )
        .get(id=movement_id)
    )


def movement_by_idempotency_key(context: BusinessContext, *, idempotency_key):
    validate_business_context(context)
    return StockMovement.objects.get(
        company_id=context.company_id, idempotency_key=idempotency_key.strip()
    )


def _scoped_warehouse(context, warehouse_id):
    try:
        return Warehouse.objects.get(id=warehouse_id, company_id=context.company_id)
    except Warehouse.DoesNotExist as exc:
        raise ValidationError("Warehouse was not found in the active company.") from exc


def stock_balance(context: BusinessContext, *, warehouse_id, product_variant_id):
    validate_business_context(context)
    warehouse = _scoped_warehouse(context, warehouse_id)
    try:
        variant = ProductVariant.objects.get(id=product_variant_id, company_id=context.company_id)
    except ProductVariant.DoesNotExist as exc:
        raise ValidationError("Product variant was not found in the active company.") from exc
    lines = StockMovementLine.objects.filter(
        company_id=context.company_id,
        product_variant=variant,
        movement__status=StockMovement.Status.POSTED,
    ).filter(Q(source_warehouse=warehouse) | Q(destination_warehouse=warehouse))
    quantity = Decimal("0")
    for line in lines:
        if line.destination_warehouse_id == warehouse.id:
            quantity += line.quantity
        if line.source_warehouse_id == warehouse.id:
            quantity -= line.quantity
    return quantity


def balances_for_warehouse(context: BusinessContext, *, warehouse_id):
    validate_business_context(context)
    warehouse = _scoped_warehouse(context, warehouse_id)
    lines = (
        StockMovementLine.objects.filter(
            company_id=context.company_id, movement__status=StockMovement.Status.POSTED
        )
        .filter(Q(source_warehouse=warehouse) | Q(destination_warehouse=warehouse))
        .select_related("product_variant__product", "uom")
    )
    grouped = {}
    for line in lines:
        key = (line.product_variant_id, line.uom_id)
        if key not in grouped:
            grouped[key] = StockBalance(line.product_variant, line.uom, Decimal("0"))
        delta = line.quantity if line.destination_warehouse_id == warehouse.id else -line.quantity
        row = grouped[key]
        grouped[key] = StockBalance(row.product_variant, row.uom, row.quantity + delta)
    return sorted(grouped.values(), key=lambda row: row.product_variant.sku)


def movement_history(context: BusinessContext, *, warehouse_id=None, product_variant_id=None):
    validate_business_context(context)
    queryset = StockMovement.objects.filter(
        company_id=context.company_id, status=StockMovement.Status.POSTED
    ).prefetch_related("lines__product_variant", "lines__uom")
    if warehouse_id:
        _scoped_warehouse(context, warehouse_id)
        queryset = queryset.filter(
            Q(lines__source_warehouse_id=warehouse_id)
            | Q(lines__destination_warehouse_id=warehouse_id)
        )
    if product_variant_id:
        if not ProductVariant.objects.filter(
            id=product_variant_id, company_id=context.company_id
        ).exists():
            raise ValidationError("Product variant was not found in the active company.")
        queryset = queryset.filter(lines__product_variant_id=product_variant_id)
    return queryset.distinct()
