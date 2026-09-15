from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from businessos.core.access.policies import require_permission
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Warehouse
from businessos.modules.catalog.models import ProductVariant

from .manifest import VIEW_BALANCES, VIEW_MOVEMENTS
from .models import StockMovement, StockMovementLine


@dataclass(frozen=True, slots=True)
class StockBalance:
    product_variant: ProductVariant
    uom: object
    quantity: Decimal


def movements_for_company(context: BusinessContext, *, search="", movement_type="", status=""):
    require_permission(context, VIEW_MOVEMENTS)
    queryset = StockMovement.objects.filter(company_id=context.company_id).select_related(
        "company"
    )
    if search.strip():
        term = search.strip()
        queryset = queryset.filter(Q(number__icontains=term) | Q(reference__icontains=term))
    if movement_type:
        queryset = queryset.filter(movement_type=movement_type)
    if status:
        queryset = queryset.filter(status=status)
    return queryset


def movement_detail(context: BusinessContext, *, movement_id):
    require_permission(context, VIEW_MOVEMENTS)
    return (
        StockMovement.objects.filter(id=movement_id, company_id=context.company_id)
        .select_related("company")
        .prefetch_related(
            "lines__product_variant__product",
            "lines__uom",
            "lines__source_warehouse",
            "lines__destination_warehouse",
        )
        .get()
    )


def _scoped_warehouse(context, warehouse_id):
    try:
        return Warehouse.objects.get(id=warehouse_id, company_id=context.company_id)
    except Warehouse.DoesNotExist as exc:
        raise PermissionDenied("The Warehouse is outside the selected company.") from exc


def _scoped_variant(context, product_variant_id):
    try:
        return ProductVariant.objects.get(
            id=product_variant_id, company_id=context.company_id
        )
    except ProductVariant.DoesNotExist as exc:
        raise PermissionDenied("The Product Variant is outside the selected company.") from exc


def stock_balance(context: BusinessContext, *, warehouse_id, product_variant_id):
    require_permission(context, VIEW_BALANCES)
    warehouse = _scoped_warehouse(context, warehouse_id)
    variant = _scoped_variant(context, product_variant_id)
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
    require_permission(context, VIEW_BALANCES)
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
        row = grouped[key]
        delta = Decimal("0")
        if line.destination_warehouse_id == warehouse.id:
            delta += line.quantity
        if line.source_warehouse_id == warehouse.id:
            delta -= line.quantity
        grouped[key] = StockBalance(row.product_variant, row.uom, row.quantity + delta)
    return sorted(grouped.values(), key=lambda row: row.product_variant.sku)


def movement_history(context: BusinessContext, *, warehouse_id=None, product_variant_id=None):
    require_permission(context, VIEW_BALANCES)
    queryset = StockMovement.objects.filter(
        company_id=context.company_id, status=StockMovement.Status.POSTED
    ).select_related("company").prefetch_related(
        "lines__product_variant", "lines__uom"
    )
    if warehouse_id:
        _scoped_warehouse(context, warehouse_id)
        queryset = queryset.filter(
            Q(lines__source_warehouse_id=warehouse_id)
            | Q(lines__destination_warehouse_id=warehouse_id)
        )
    if product_variant_id:
        _scoped_variant(context, product_variant_id)
        queryset = queryset.filter(lines__product_variant_id=product_variant_id)
    return queryset.distinct()
