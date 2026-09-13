from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max, Sum
from django.utils import timezone

from businessos.core.access.policies import validate_business_context
from businessos.core.common.context import BusinessContext
from businessos.core.reference.models import Currency
from businessos.modules.catalog.models import ProductVariant
from businessos.modules.party.models import Party

from .models import PurchaseOrder, PurchaseOrderLine, PurchaseReceipt, PurchaseReceiptLine


def _supplier(context: BusinessContext, supplier_id) -> Party:
    try:
        return Party.objects.get(
            id=supplier_id,
            company_id=context.company_id,
            is_active=True,
            is_supplier=True,
        )
    except Party.DoesNotExist as exc:
        raise PermissionDenied("Select an active supplier in the selected company.") from exc


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
            product__is_purchasable=True,
        )
    except ProductVariant.DoesNotExist as exc:
        raise PermissionDenied(
            "Select an active purchasable product variant in the selected company."
        ) from exc


def _locked_order(context: BusinessContext, order_id) -> PurchaseOrder:
    try:
        return PurchaseOrder.objects.select_for_update().get(
            id=order_id, company_id=context.company_id
        )
    except PurchaseOrder.DoesNotExist as exc:
        raise PermissionDenied("The Purchase Order is outside the selected company.") from exc


def _line_order_id(context: BusinessContext, line_id):
    order_id = (
        PurchaseOrderLine.objects.filter(id=line_id, company_id=context.company_id)
        .values_list("purchase_order_id", flat=True)
        .first()
    )
    if order_id is None:
        raise PermissionDenied("The Purchase Order line is outside the selected company.")
    return order_id


def _require_draft(order: PurchaseOrder) -> None:
    if order.status != PurchaseOrder.Status.DRAFT:
        raise ValidationError("Only draft Purchase Orders may be changed.")


def _order_number() -> str:
    return f"PO-{uuid4().hex.upper()}"


def _receipt_number() -> str:
    return f"PR-{uuid4().hex.upper()}"


def _persist_lifecycle_transition(
    order: PurchaseOrder, *, status: str, confirmed_at=None
) -> PurchaseOrder:
    changed_at = timezone.now()
    updates = {"status": status, "updated_at": changed_at}
    if confirmed_at is not None:
        updates["confirmed_at"] = confirmed_at
    PurchaseOrder.objects.filter(pk=order.pk).update(**updates)
    order.status = status
    order.updated_at = changed_at
    if confirmed_at is not None:
        order.confirmed_at = confirmed_at
    return order


def _normalize_receipt_lines(lines) -> dict[UUID, Decimal]:
    normalized: dict[UUID, Decimal] = {}
    for item in lines:
        try:
            line_id = UUID(str(item["purchase_order_line_id"]))
            quantity = Decimal(str(item["quantity_received"]))
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise ValidationError(
                "Each receipt line requires a valid line ID and quantity."
            ) from exc
        if line_id in normalized:
            raise ValidationError("A Purchase Order line may appear only once in a receipt.")
        if not quantity.is_finite() or quantity <= 0:
            raise ValidationError("Received quantity must be greater than zero.")
        normalized[line_id] = quantity
    if not normalized:
        raise ValidationError("A Purchase Receipt requires at least one line.")
    return normalized


def _receipt_payload(receipt: PurchaseReceipt) -> dict[UUID, Decimal]:
    return {
        line.purchase_order_line_id: line.quantity_received
        for line in receipt.lines.all()
    }


def _validate_idempotent_match(
    receipt: PurchaseReceipt,
    *,
    purchase_order_id,
    receipt_date,
    normalized_lines: dict[UUID, Decimal],
) -> PurchaseReceipt:
    if (
        receipt.purchase_order_id != purchase_order_id
        or receipt.receipt_date != receipt_date
        or _receipt_payload(receipt) != normalized_lines
    ):
        raise ValidationError(
            "The idempotency key is already used by a different Purchase Receipt request."
        )
    return receipt


def _receipt_for_key(context: BusinessContext, idempotency_key: str):
    return (
        PurchaseReceipt.objects.prefetch_related("lines")
        .filter(company_id=context.company_id, idempotency_key=idempotency_key)
        .first()
    )


@transaction.atomic
def create_purchase_order(
    context: BusinessContext,
    *,
    supplier_id,
    order_date,
    currency_id,
    notes: str = "",
) -> PurchaseOrder:
    validate_business_context(context)
    order = PurchaseOrder(
        company_id=context.company_id,
        number=_order_number(),
        supplier=_supplier(context, supplier_id),
        order_date=order_date,
        currency=_currency(currency_id),
        notes=notes,
    )
    order.save()
    return order


@transaction.atomic
def update_purchase_order(context: BusinessContext, *, order_id, **changes) -> PurchaseOrder:
    validate_business_context(context)
    order = _locked_order(context, order_id)
    _require_draft(order)
    allowed = {"supplier_id", "order_date", "currency_id", "notes"}
    unknown = changes.keys() - allowed
    if unknown:
        raise ValidationError(
            f"Unsupported Purchase Order fields: {', '.join(sorted(unknown))}"
        )
    if "supplier_id" in changes:
        order.supplier = _supplier(context, changes.pop("supplier_id"))
    if "currency_id" in changes:
        order.currency = _currency(changes.pop("currency_id"))
    for field_name, value in changes.items():
        setattr(order, field_name, value)
    order.save()
    return order


@transaction.atomic
def add_purchase_order_line(
    context: BusinessContext,
    *,
    order_id,
    product_variant_id,
    quantity,
    unit_cost,
    description: str | None = None,
) -> PurchaseOrderLine:
    validate_business_context(context)
    order = _locked_order(context, order_id)
    _require_draft(order)
    variant = _variant(context, product_variant_id)
    position = (order.lines.aggregate(value=Max("position"))["value"] or 0) + 1
    line = PurchaseOrderLine(
        company_id=context.company_id,
        purchase_order=order,
        product_variant=variant,
        sku_snapshot=variant.sku,
        name_snapshot=variant.product.name,
        description_snapshot=(
            variant.product.purchase_description if description is None else description
        ),
        quantity=quantity,
        unit_cost=unit_cost,
        position=position,
    )
    line.save()
    return line


@transaction.atomic
def update_purchase_order_line(
    context: BusinessContext,
    *,
    line_id,
    product_variant_id,
    quantity,
    unit_cost,
    description: str,
) -> PurchaseOrderLine:
    validate_business_context(context)
    order_id = _line_order_id(context, line_id)
    order = _locked_order(context, order_id)
    _require_draft(order)
    try:
        line = PurchaseOrderLine.objects.get(
            id=line_id,
            company_id=context.company_id,
            purchase_order_id=order.id,
        )
    except PurchaseOrderLine.DoesNotExist as exc:
        raise PermissionDenied("The Purchase Order line is outside the selected company.") from exc
    variant = _variant(context, product_variant_id)
    line.product_variant = variant
    line.sku_snapshot = variant.sku
    line.name_snapshot = variant.product.name
    line.description_snapshot = description
    line.quantity = quantity
    line.unit_cost = unit_cost
    line.save()
    return line


@transaction.atomic
def remove_purchase_order_line(context: BusinessContext, *, line_id) -> None:
    validate_business_context(context)
    order_id = _line_order_id(context, line_id)
    order = _locked_order(context, order_id)
    _require_draft(order)
    try:
        line = PurchaseOrderLine.objects.get(
            id=line_id,
            company_id=context.company_id,
            purchase_order_id=order.id,
        )
    except PurchaseOrderLine.DoesNotExist as exc:
        raise PermissionDenied("The Purchase Order line is outside the selected company.") from exc
    line.delete()


@transaction.atomic
def confirm_purchase_order(context: BusinessContext, *, order_id) -> PurchaseOrder:
    validate_business_context(context)
    order = _locked_order(context, order_id)
    if order.status == PurchaseOrder.Status.CONFIRMED:
        return order
    if order.status == PurchaseOrder.Status.CANCELLED:
        raise ValidationError("A cancelled Purchase Order cannot be confirmed.")
    _supplier(context, order.supplier_id)
    _currency(order.currency_id)
    lines = list(order.lines.select_related("product_variant__product"))
    if not lines:
        raise ValidationError("A Purchase Order requires at least one line before confirmation.")
    for line in lines:
        _variant(context, line.product_variant_id)
        line.full_clean()
    return _persist_lifecycle_transition(
        order,
        status=PurchaseOrder.Status.CONFIRMED,
        confirmed_at=timezone.now(),
    )


@transaction.atomic
def cancel_purchase_order(context: BusinessContext, *, order_id) -> PurchaseOrder:
    validate_business_context(context)
    order = _locked_order(context, order_id)
    if order.status == PurchaseOrder.Status.CANCELLED:
        return order
    if order.status != PurchaseOrder.Status.CONFIRMED:
        raise ValidationError("Only a confirmed Purchase Order may be cancelled.")
    if order.receipts.exists():
        raise ValidationError("A Purchase Order with receipts cannot be cancelled.")
    return _persist_lifecycle_transition(order, status=PurchaseOrder.Status.CANCELLED)


@transaction.atomic
def receive_purchase_order(
    context: BusinessContext,
    *,
    purchase_order_id,
    receipt_date,
    idempotency_key: str,
    lines,
) -> PurchaseReceipt:
    validate_business_context(context)
    try:
        purchase_order_id = UUID(str(purchase_order_id))
    except (TypeError, ValueError) as exc:
        raise ValidationError({"purchase_order_id": "Select a valid Purchase Order."}) from exc
    key = idempotency_key.strip()
    if not key:
        raise ValidationError({"idempotency_key": "Idempotency key is required."})
    normalized_lines = _normalize_receipt_lines(lines)
    existing = _receipt_for_key(context, key)
    if existing:
        return _validate_idempotent_match(
            existing,
            purchase_order_id=purchase_order_id,
            receipt_date=receipt_date,
            normalized_lines=normalized_lines,
        )

    order = _locked_order(context, purchase_order_id)
    if order.status != PurchaseOrder.Status.CONFIRMED:
        raise ValidationError("Only a confirmed Purchase Order may be received.")

    existing = _receipt_for_key(context, key)
    if existing:
        return _validate_idempotent_match(
            existing,
            purchase_order_id=order.id,
            receipt_date=receipt_date,
            normalized_lines=normalized_lines,
        )

    order_lines = {
        line.id: line
        for line in PurchaseOrderLine.objects.select_for_update().filter(
            id__in=normalized_lines,
            purchase_order=order,
            company_id=context.company_id,
        )
    }
    if set(order_lines) != set(normalized_lines):
        raise PermissionDenied("Every receipt line must belong to the selected Purchase Order.")

    already_received = {
        row["purchase_order_line_id"]: row["total"]
        for row in PurchaseReceiptLine.objects.filter(
            purchase_order_line_id__in=normalized_lines,
            company_id=context.company_id,
        )
        .values("purchase_order_line_id")
        .annotate(total=Sum("quantity_received"))
    }
    for line_id, quantity in normalized_lines.items():
        cumulative = already_received.get(line_id, Decimal("0")) + quantity
        if cumulative > order_lines[line_id].quantity:
            sku = order_lines[line_id].sku_snapshot
            raise ValidationError(
                f"Receipt quantity exceeds the ordered quantity for {sku}."
            )

    try:
        with transaction.atomic():
            posted_at = timezone.now()
            receipt = PurchaseReceipt(
                company_id=context.company_id,
                number=_receipt_number(),
                purchase_order=order,
                receipt_date=receipt_date,
                idempotency_key=key,
                posted_at=posted_at,
                created_at=posted_at,
                updated_at=posted_at,
            )
            PurchaseReceipt.objects.bulk_create([receipt])
            receipt_lines = [
                PurchaseReceiptLine(
                    company_id=context.company_id,
                    purchase_receipt=receipt,
                    purchase_order_line=order_lines[line_id],
                    quantity_received=quantity,
                    created_at=posted_at,
                    updated_at=posted_at,
                )
                for line_id, quantity in normalized_lines.items()
            ]
            PurchaseReceiptLine.objects.bulk_create(receipt_lines)
    except IntegrityError:
        existing = _receipt_for_key(context, key)
        if existing is None:
            raise
        return _validate_idempotent_match(
            existing,
            purchase_order_id=order.id,
            receipt_date=receipt_date,
            normalized_lines=normalized_lines,
        )
    return receipt
