from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import BooleanField, Case, F, Q, Value, When
from django.db.models.functions import Round

from businessos.core.access.policies import require_permission
from businessos.core.database import business_atomic, current_database_alias
from businessos.core.organization.models import Company

from .domain import receipt_amount
from .manifest import VIEW_METHODS, VIEW_PAYMENTS
from .models import Payment, PaymentMethod


def payment_methods_for_company(context, *, search="", active=""):
    require_permission(context, VIEW_METHODS)
    methods = PaymentMethod.objects.filter(company_id=context.company_id)
    if search.strip():
        methods = methods.filter(
            Q(code__icontains=search.strip()) | Q(name__icontains=search.strip())
        )
    if active in {"yes", "no"}:
        methods = methods.filter(is_active=active == "yes")
    return methods.order_by("code", "id")


def payments_for_company(context, *, search=""):
    require_permission(context, VIEW_PAYMENTS)
    payments = Payment.objects.filter(company_id=context.company_id)
    if search.strip():
        payments = payments.filter(
            Q(number__icontains=search.strip())
            | Q(payer_display_name_snapshot__icontains=search.strip())
            | Q(external_reference__icontains=search.strip())
        )
    return payments.order_by("-payment_date", "-recorded_at", "id")


def payment_detail(context, payment_id):
    return payments_for_company(context).select_related("company").get(pk=payment_id)


RECEIPT_BASIS_VERSION = 1


def receipt_basis_query(context, *, payment_ids):
    """Pinned scalar SQL receipt validation for complete allocation history."""
    require_permission(context, VIEW_PAYMENTS)
    rows = (
        Payment.objects.using(current_database_alias())
        .filter(pk__in=payment_ids, company_id=context.company_id)
        .alias(basis_amount=Round("amount", F("currency_decimal_places_snapshot")))
    )
    valid = Q(
        company_id=context.company_id,
        payer_party__company_id=context.company_id,
        payment_method__company_id=context.company_id,
        payment_method__code=F("payment_method_code_snapshot"),
        currency__code=F("currency_code_snapshot"),
        currency_decimal_places_snapshot__gte=0,
        currency_decimal_places_snapshot__lte=8,
        recorded_at__isnull=False,
        amount__gt=0,
        amount__lt=Decimal("1e30"),
        amount=F("basis_amount"),
        number__regex=r"^PAY-[0-9A-F]{32}$",
    )
    return rows.annotate(
        basis_valid=Case(
            When(valid, then=Value(True)), default=Value(False), output_field=BooleanField()
        )
    )


@dataclass(frozen=True, slots=True)
class PaymentReceiptBasis:
    id: UUID
    company_id: UUID
    payer_party_id: UUID
    currency_id: UUID
    currency_code: str
    precision: int
    amount: Decimal
    number: str
    payment_date: date
    recorded_at: datetime


@business_atomic
def payment_receipt_basis(context, payment_id, *, lock=True):
    """Read immutable receipt facts without applying current reference activity."""
    alias = current_database_alias()
    if (
        not Company.objects.using(alias)
        .select_for_update()
        .filter(pk=context.company_id, is_active=True)
        .exists()
    ):
        raise PermissionDenied("The selected company is unavailable.")
    require_permission(context, VIEW_PAYMENTS)
    rows = Payment.objects.using(alias)
    if lock:
        rows = rows.select_for_update()
    payment = rows.filter(pk=payment_id, company_id=context.company_id).first()
    require_permission(context, VIEW_PAYMENTS)
    if payment is None:
        raise PermissionDenied("Payment is outside the authorized company.")
    if (
        payment.recorded_at is None
        or not payment.number.startswith("PAY-")
        or len(payment.number) != 36
        or not Payment.objects.using(alias)
        .filter(
            pk=payment.pk,
            payer_party__company_id=context.company_id,
            payment_method__company_id=context.company_id,
            payment_method__code=F("payment_method_code_snapshot"),
            currency__code=F("currency_code_snapshot"),
        )
        .exists()
    ):
        raise ValidationError("Receipt financial basis is incompatible.")
    try:
        if UUID(payment.number[4:]).hex.upper() != payment.number[4:]:
            raise ValueError("Noncanonical receipt identity.")
        amount = receipt_amount(payment.amount, payment.currency_decimal_places_snapshot)
    except ValueError as exc:
        raise ValidationError("Receipt financial basis is incompatible.") from exc
    return PaymentReceiptBasis(
        payment.pk,
        payment.company_id,
        payment.payer_party_id,
        payment.currency_id,
        payment.currency_code_snapshot,
        payment.currency_decimal_places_snapshot,
        amount,
        payment.number,
        payment.payment_date,
        payment.recorded_at,
    )
