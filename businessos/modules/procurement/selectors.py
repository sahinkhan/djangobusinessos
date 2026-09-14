from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Prefetch, Q, Sum, Value
from django.db.models.functions import Coalesce

from businessos.core.access.policies import require_permission
from businessos.core.common.context import BusinessContext

from .manifest import VIEW_ORDERS
from .models import PurchaseOrder, PurchaseOrderLine, PurchaseReceipt

QUANTITY_FIELD = DecimalField(max_digits=18, decimal_places=4)
TOTAL_FIELD = DecimalField(max_digits=38, decimal_places=8)


def _with_total(queryset):
    line_total = ExpressionWrapper(
        F("lines__quantity") * F("lines__unit_cost"), output_field=TOTAL_FIELD
    )
    return queryset.annotate(
        total=Coalesce(Sum(line_total), Value(Decimal("0")), output_field=TOTAL_FIELD)
    )


def _lines_with_receipt_quantities():
    received = Coalesce(
        Sum("receipt_lines__quantity_received"),
        Value(Decimal("0")),
        output_field=QUANTITY_FIELD,
    )
    return (
        PurchaseOrderLine.objects.select_related("product_variant__product")
        .annotate(received_quantity=received)
        .annotate(
            remaining_quantity=ExpressionWrapper(
                F("quantity") - F("received_quantity"), output_field=QUANTITY_FIELD
            )
        )
        .order_by("position", "created_at")
    )


def purchase_orders_for_company(context: BusinessContext, *, search: str = "", status: str = ""):
    require_permission(context, VIEW_ORDERS)
    queryset = PurchaseOrder.objects.select_related("supplier", "currency").filter(
        company_id=context.company_id
    )
    if search.strip():
        term = search.strip()
        queryset = queryset.filter(
            Q(number__icontains=term) | Q(supplier__display_name__icontains=term)
        )
    if status:
        queryset = queryset.filter(status=status)
    return _with_total(queryset).order_by("-order_date", "-created_at")


def purchase_order_detail(context: BusinessContext, *, order_id) -> PurchaseOrder:
    require_permission(context, VIEW_ORDERS)
    return _with_total(
        PurchaseOrder.objects.select_related("supplier", "currency")
        .prefetch_related(Prefetch("lines", queryset=_lines_with_receipt_quantities()), "receipts")
        .filter(id=order_id, company_id=context.company_id)
    ).get()


def purchase_receipt_detail(context: BusinessContext, *, receipt_id) -> PurchaseReceipt:
    require_permission(context, VIEW_ORDERS)
    return (
        PurchaseReceipt.objects.select_related("purchase_order", "company")
        .prefetch_related("lines__purchase_order_line")
        .get(id=receipt_id, company_id=context.company_id)
    )


def purchase_order_total(context: BusinessContext, *, order_id) -> Decimal:
    return purchase_order_detail(context, order_id=order_id).total


def receipts_for_purchase_order(context: BusinessContext, *, purchase_order_id):
    require_permission(context, VIEW_ORDERS)
    return PurchaseReceipt.objects.select_related("purchase_order").filter(
        company_id=context.company_id,
        purchase_order_id=purchase_order_id,
        purchase_order__company_id=context.company_id,
    )


def received_quantity_for_line(context: BusinessContext, *, purchase_order_line_id) -> Decimal:
    require_permission(context, VIEW_ORDERS)
    line = PurchaseOrderLine.objects.filter(
        id=purchase_order_line_id, company_id=context.company_id
    ).first()
    if line is None:
        raise PurchaseOrderLine.DoesNotExist
    return line.receipt_lines.aggregate(
        total=Coalesce(
            Sum("quantity_received"),
            Value(Decimal("0")),
            output_field=QUANTITY_FIELD,
        )
    )["total"]


def remaining_quantity_for_line(context: BusinessContext, *, purchase_order_line_id) -> Decimal:
    require_permission(context, VIEW_ORDERS)
    line = PurchaseOrderLine.objects.get(id=purchase_order_line_id, company_id=context.company_id)
    return line.quantity - received_quantity_for_line(
        context, purchase_order_line_id=purchase_order_line_id
    )
