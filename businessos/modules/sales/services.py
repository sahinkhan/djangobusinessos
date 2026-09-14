from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from businessos.core.access.policies import require_permission
from businessos.core.audit.services import record_audit_entry
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.core.reference.models import Currency
from businessos.modules.catalog.models import ProductVariant
from businessos.modules.party.models import Party

from .manifest import CANCEL_ORDERS, CONFIRM_ORDERS, CREATE_ORDERS, UPDATE_ORDERS
from .models import SalesOrder, SalesOrderLine


def _lock_company_and_authorize(context: BusinessContext, permission_code: str) -> Company:
    """Serialize scoped authorization with concurrent grant and revocation changes."""
    company = (
        Company.objects.select_for_update()
        .filter(id=context.company_id, is_active=True)
        .first()
    )
    if company is None:
        raise PermissionDenied("The selected company does not exist or is inactive.")
    require_permission(context, permission_code)
    return company


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


def _line_order_id(context: BusinessContext, line_id):
    order_id = (
        SalesOrderLine.objects.filter(id=line_id, company_id=context.company_id)
        .values_list("sales_order_id", flat=True)
        .first()
    )
    if order_id is None:
        raise PermissionDenied("The Sales Order line is outside the selected company.")
    return order_id


def _locked_line(context: BusinessContext, *, order: SalesOrder, line_id) -> SalesOrderLine:
    try:
        return SalesOrderLine.objects.get(
            id=line_id,
            company_id=context.company_id,
            sales_order_id=order.id,
        )
    except SalesOrderLine.DoesNotExist as exc:
        raise PermissionDenied("The Sales Order line is outside the selected company.") from exc


def _require_draft(order: SalesOrder) -> None:
    if order.status != SalesOrder.Status.DRAFT:
        raise ValidationError("Only draft Sales Orders may be changed.")


def _order_number() -> str:
    return f"SO-{uuid4().hex.upper()}"


def _persist_lifecycle_transition(
    order: SalesOrder, *, expected_status: str, status: str, confirmed_at=None
) -> SalesOrder:
    """Persist exactly one accepted transition after authorization and aggregate locking."""
    changed_at = timezone.now()
    return SalesOrder.objects.get_queryset()._transition_locked_order(
        order_id=order.pk,
        expected_status=expected_status,
        target_status=status,
        changed_at=changed_at,
        confirmed_at=confirmed_at,
    )


def _record_order_update(context: BusinessContext, order: SalesOrder, **metadata) -> None:
    record_audit_entry(
        context=context,
        action="sales.order.updated",
        object_type="sales.SalesOrder",
        object_id=order.id,
        metadata=metadata,
    )


@transaction.atomic
def create_sales_order(
    context: BusinessContext,
    *,
    customer_id,
    order_date,
    currency_id,
    notes: str = "",
) -> SalesOrder:
    _lock_company_and_authorize(context, CREATE_ORDERS)
    order = SalesOrder(
        company_id=context.company_id,
        number=_order_number(),
        customer=_customer(context, customer_id),
        order_date=order_date,
        currency=_currency(currency_id),
        notes=notes,
    )
    order.save()
    record_audit_entry(
        context=context,
        action="sales.order.created",
        object_type="sales.SalesOrder",
        object_id=order.id,
        metadata={"number": order.number, "customer_id": str(order.customer_id)},
    )
    return order


@transaction.atomic
def update_sales_order(context: BusinessContext, *, order_id, **changes) -> SalesOrder:
    _lock_company_and_authorize(context, UPDATE_ORDERS)
    order = _locked_order(context, order_id)
    _require_draft(order)
    allowed = {"customer_id", "order_date", "currency_id", "notes"}
    unknown = changes.keys() - allowed
    if unknown:
        raise ValidationError(f"Unsupported Sales Order fields: {', '.join(sorted(unknown))}")
    before = {
        "customer_id": order.customer_id,
        "order_date": order.order_date,
        "currency_id": order.currency_id,
        "notes": order.notes,
    }
    if "customer_id" in changes:
        order.customer = _customer(context, changes.pop("customer_id"))
    if "currency_id" in changes:
        order.currency = _currency(changes.pop("currency_id"))
    for field_name, value in changes.items():
        setattr(order, field_name, value)
    order.save()
    changed_fields = [
        field_name
        for field_name, old_value in before.items()
        if old_value != getattr(order, field_name)
    ]
    if changed_fields:
        _record_order_update(context, order, change="header", fields=changed_fields)
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
) -> SalesOrderLine:
    _lock_company_and_authorize(context, UPDATE_ORDERS)
    order = _locked_order(context, order_id)
    _require_draft(order)
    variant = _variant(context, product_variant_id)
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
    _record_order_update(
        context,
        order,
        change="line_added",
        line_id=str(line.id),
        product_variant_id=str(variant.id),
    )
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
) -> SalesOrderLine:
    _lock_company_and_authorize(context, UPDATE_ORDERS)
    order_id = _line_order_id(context, line_id)
    order = _locked_order(context, order_id)
    _require_draft(order)
    line = _locked_line(context, order=order, line_id=line_id)
    variant = _variant(context, product_variant_id)
    before = (
        line.product_variant_id,
        line.description_snapshot,
        line.quantity,
        line.unit_price,
    )
    line.product_variant = variant
    line.sku_snapshot = variant.sku
    line.name_snapshot = variant.product.name
    line.description_snapshot = description
    line.quantity = quantity
    line.unit_price = unit_price
    line.save()
    after = (
        line.product_variant_id,
        line.description_snapshot,
        line.quantity,
        line.unit_price,
    )
    if before != after:
        _record_order_update(context, order, change="line_updated", line_id=str(line.id))
    return line


@transaction.atomic
def remove_sales_order_line(context: BusinessContext, *, line_id) -> None:
    _lock_company_and_authorize(context, UPDATE_ORDERS)
    order_id = _line_order_id(context, line_id)
    order = _locked_order(context, order_id)
    _require_draft(order)
    line = _locked_line(context, order=order, line_id=line_id)
    deleted_line_id = line.id
    line.delete()
    _record_order_update(
        context, order, change="line_removed", line_id=str(deleted_line_id)
    )


@transaction.atomic
def confirm_sales_order(context: BusinessContext, *, order_id) -> SalesOrder:
    _lock_company_and_authorize(context, CONFIRM_ORDERS)
    order = _locked_order(context, order_id)
    if order.status == SalesOrder.Status.CONFIRMED:
        return order
    if order.status == SalesOrder.Status.CANCELLED:
        raise ValidationError("A cancelled Sales Order cannot be confirmed.")
    _customer(context, order.customer_id)
    _currency(order.currency_id)
    lines = list(order.lines.select_related("product_variant__product"))
    if not lines:
        raise ValidationError("A Sales Order requires at least one line before confirmation.")
    for line in lines:
        _variant(context, line.product_variant_id)
        line.full_clean()
    confirmed_at = timezone.now()
    order = _persist_lifecycle_transition(
        order,
        expected_status=SalesOrder.Status.DRAFT,
        status=SalesOrder.Status.CONFIRMED,
        confirmed_at=confirmed_at,
    )
    record_audit_entry(
        context=context,
        action="sales.order.confirmed",
        object_type="sales.SalesOrder",
        object_id=order.id,
        metadata={"number": order.number},
    )
    return order


@transaction.atomic
def cancel_sales_order(context: BusinessContext, *, order_id) -> SalesOrder:
    _lock_company_and_authorize(context, CANCEL_ORDERS)
    order = _locked_order(context, order_id)
    if order.status == SalesOrder.Status.CANCELLED:
        return order
    if order.status != SalesOrder.Status.CONFIRMED:
        raise ValidationError("Only a confirmed Sales Order may be cancelled.")
    order = _persist_lifecycle_transition(
        order,
        expected_status=SalesOrder.Status.CONFIRMED,
        status=SalesOrder.Status.CANCELLED,
    )
    record_audit_entry(
        context=context,
        action="sales.order.cancelled",
        object_type="sales.SalesOrder",
        object_id=order.id,
        metadata={"number": order.number},
    )
    return order
