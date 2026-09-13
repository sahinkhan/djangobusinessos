from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from businessos.core.access.policies import validate_business_context
from businessos.core.common.context import BusinessContext
from businessos.core.reference.models import Currency
from businessos.modules.catalog.models import ProductVariant
from businessos.modules.party.models import Party

from .models import SalesOrder, SalesOrderLine


def _customer(context: BusinessContext, customer_id) -> Party:
    try:
        return Party.objects.get(
            id=customer_id,
            company_id=context.company_id,
            is_active=True,
            is_customer=True,
        )
    except Party.DoesNotExist as exc:
        raise PermissionDenied("Select an active customer in the selected company.") from exc


def _currency(currency_id) -> Currency:
    try:
        return Currency.objects.get(id=currency_id, is_active=True)
    except Currency.DoesNotExist as exc:
        raise ValidationError({"currency": "Select an active currency."}) from exc


def _variant(context: BusinessContext, variant_id) -> ProductVariant:
    try:
        return ProductVariant.objects.select_related("product").get(
            id=variant_id,
            company_id=context.company_id,
            is_active=True,
            product__is_active=True,
            product__is_sellable=True,
        )
    except ProductVariant.DoesNotExist as exc:
        raise PermissionDenied(
            "Select an active sellable product variant in the selected company."
        ) from exc


def _locked_order(context: BusinessContext, order_id) -> SalesOrder:
    try:
        return SalesOrder.objects.select_for_update().get(
            id=order_id, company_id=context.company_id
        )
    except SalesOrder.DoesNotExist as exc:
        raise PermissionDenied("The Sales Order is outside the selected company.") from exc


def _require_draft(order: SalesOrder) -> None:
    if order.status != SalesOrder.Status.DRAFT:
        raise ValidationError("Only draft Sales Orders may be changed.")


def _order_number() -> str:
    return f"SO-{uuid4().hex.upper()}"


@transaction.atomic
def create_sales_order(
    context: BusinessContext,
    *,
    customer_id,
    order_date,
    currency_id,
    notes: str = "",
) -> SalesOrder:
    validate_business_context(context)
    order = SalesOrder(
        company_id=context.company_id,
        number=_order_number(),
        customer=_customer(context, customer_id),
        order_date=order_date,
        currency=_currency(currency_id),
        notes=notes,
    )
    order.save()
    return order


@transaction.atomic
def update_sales_order(context: BusinessContext, *, order_id, **changes) -> SalesOrder:
    validate_business_context(context)
    order = _locked_order(context, order_id)
    _require_draft(order)
    allowed = {"customer_id", "order_date", "currency_id", "notes"}
    unknown = changes.keys() - allowed
    if unknown:
        raise ValidationError(f"Unsupported Sales Order fields: {', '.join(sorted(unknown))}")
    if "customer_id" in changes:
        order.customer = _customer(context, changes.pop("customer_id"))
    if "currency_id" in changes:
        order.currency = _currency(changes.pop("currency_id"))
    for field_name, value in changes.items():
        setattr(order, field_name, value)
    order.save()
    return order


@transaction.atomic
def add_sales_order_line(
    context: BusinessContext,
    *,
    order_id,
    product_variant_id,
    quantity,
    unit_price,
    description: str | None = None,
    position: int | None = None,
) -> SalesOrderLine:
    validate_business_context(context)
    order = _locked_order(context, order_id)
    _require_draft(order)
    variant = _variant(context, product_variant_id)
    if position is None:
        position = (order.lines.aggregate(value=Max("position"))["value"] or 0) + 1
    line = SalesOrderLine(
        company_id=context.company_id,
        sales_order=order,
        product_variant=variant,
        sku_snapshot=variant.sku,
        name_snapshot=variant.product.name,
        description_snapshot=(
            variant.product.sales_description if description is None else description
        ),
        quantity=quantity,
        unit_price=unit_price,
        position=position,
    )
    line.save()
    return line


@transaction.atomic
def update_sales_order_line(
    context: BusinessContext,
    *,
    line_id,
    product_variant_id,
    quantity,
    unit_price,
    description: str,
    position: int | None,
) -> SalesOrderLine:
    validate_business_context(context)
    try:
        line = SalesOrderLine.objects.select_related("sales_order").get(
            id=line_id, company_id=context.company_id
        )
    except SalesOrderLine.DoesNotExist as exc:
        raise PermissionDenied("The Sales Order line is outside the selected company.") from exc
    order = _locked_order(context, line.sales_order_id)
    _require_draft(order)
    variant = _variant(context, product_variant_id)
    line.product_variant = variant
    line.sku_snapshot = variant.sku
    line.name_snapshot = variant.product.name
    line.description_snapshot = description
    line.quantity = quantity
    line.unit_price = unit_price
    if position is not None:
        line.position = position
    line.save()
    return line


@transaction.atomic
def remove_sales_order_line(context: BusinessContext, *, line_id) -> None:
    validate_business_context(context)
    try:
        line = SalesOrderLine.objects.select_related("sales_order").get(
            id=line_id, company_id=context.company_id
        )
    except SalesOrderLine.DoesNotExist as exc:
        raise PermissionDenied("The Sales Order line is outside the selected company.") from exc
    order = _locked_order(context, line.sales_order_id)
    _require_draft(order)
    line.delete()


@transaction.atomic
def confirm_sales_order(context: BusinessContext, *, order_id) -> SalesOrder:
    validate_business_context(context)
    order = _locked_order(context, order_id)
    if order.status == SalesOrder.Status.CONFIRMED:
        return order
    if order.status == SalesOrder.Status.CANCELLED:
        raise ValidationError("A cancelled Sales Order cannot be confirmed.")
    _customer(context, order.customer_id)
    lines = list(order.lines.select_related("product_variant__product"))
    if not lines:
        raise ValidationError("A Sales Order requires at least one line before confirmation.")
    for line in lines:
        _variant(context, line.product_variant_id)
        line.full_clean()
    order.status = SalesOrder.Status.CONFIRMED
    order.confirmed_at = timezone.now()
    order.save()
    return order


@transaction.atomic
def cancel_sales_order(context: BusinessContext, *, order_id) -> SalesOrder:
    validate_business_context(context)
    order = _locked_order(context, order_id)
    if order.status == SalesOrder.Status.CANCELLED:
        return order
    if order.status != SalesOrder.Status.CONFIRMED:
        raise ValidationError("Only a confirmed Sales Order may be cancelled.")
    order.status = SalesOrder.Status.CANCELLED
    order.save()
    return order
