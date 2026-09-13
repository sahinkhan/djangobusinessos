from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce

from businessos.core.access.policies import validate_business_context
from businessos.core.common.context import BusinessContext

from .models import SalesOrder

TOTAL_FIELD = DecimalField(max_digits=38, decimal_places=8)


def _with_total(queryset):
    line_total = ExpressionWrapper(
        F("lines__quantity") * F("lines__unit_price"), output_field=TOTAL_FIELD
    )
    return queryset.annotate(
        total=Coalesce(Sum(line_total), Value(Decimal("0")), output_field=TOTAL_FIELD)
    )


def sales_orders_for_company(
    context: BusinessContext, *, search: str = "", status: str = ""
):
    validate_business_context(context)
    queryset = SalesOrder.objects.select_related("customer", "currency").filter(
        company_id=context.company_id
    )
    if search.strip():
        term = search.strip()
        queryset = queryset.filter(
            Q(number__icontains=term) | Q(customer__display_name__icontains=term)
        )
    if status:
        queryset = queryset.filter(status=status)
    return _with_total(queryset).order_by("-order_date", "-created_at")


def confirmed_sales_orders(context: BusinessContext):
    return sales_orders_for_company(context, status=SalesOrder.Status.CONFIRMED)


def sales_order_detail(context: BusinessContext, *, order_id) -> SalesOrder:
    validate_business_context(context)
    return _with_total(
        SalesOrder.objects.select_related("customer", "currency")
        .prefetch_related("lines__product_variant__product")
        .filter(id=order_id, company_id=context.company_id)
    ).get()


def sales_order_total(context: BusinessContext, *, order_id) -> Decimal:
    return sales_order_detail(context, order_id=order_id).total
