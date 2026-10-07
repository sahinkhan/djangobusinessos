from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.utils import timezone

from businessos.core.access.policies import require_permission
from businessos.core.audit.services import record_audit_entry
from businessos.core.common.context import BusinessContext
from businessos.core.database import business_atomic, business_atomic_context
from businessos.core.organization.models import Company
from businessos.core.organization.time import company_local_date
from businessos.core.reference.models import Currency
from businessos.modules.party.models import Party

from . import domain
from .manifest import MANAGE_METHODS, RECORD_PAYMENTS
from .models import _METHOD_WRITE_TOKEN, _RECEIPT_INSERT_TOKEN, Payment, PaymentMethod


def _value(field, normalizer, value, **kwargs):
    try:
        return normalizer(value, **kwargs)
    except ValueError as exc:
        raise ValidationError({field: str(exc)}) from exc


def _authorize(context, permission):
    company = (
        Company.objects.select_for_update().filter(pk=context.company_id, is_active=True).first()
    )
    if company is None:
        raise PermissionDenied("The selected company does not exist or is inactive.")
    require_permission(context, permission)


def _audit(context, instance, action, **metadata):
    record_audit_entry(
        context=context,
        action=action,
        object_type=f"payments.{type(instance).__name__}",
        object_id=instance.pk,
        metadata=metadata,
    )


def _locked_method(context, payment_method_id):
    identity = _value("payment_method", domain.canonical_uuid, payment_method_id)
    try:
        return PaymentMethod.objects.select_for_update().get(
            pk=identity, company_id=context.company_id
        )
    except PaymentMethod.DoesNotExist as exc:
        raise ValidationError({"payment_method": "Select a method in this company."}) from exc


@business_atomic
def create_payment_method(context: BusinessContext, *, code, name):
    _authorize(context, MANAGE_METHODS)
    method = PaymentMethod(
        company_id=context.company_id,
        code=_value(
            "code", domain.normalized_text, code, maximum=32, required=True, uppercase=True
        ),
        name=_value("name", domain.normalized_text, name, maximum=160, required=True),
    )
    if PaymentMethod.objects.filter(company_id=context.company_id, code=method.code).exists():
        raise ValidationError({"code": "A payment method with this code already exists."})
    method._persist(_METHOD_WRITE_TOKEN, creating=True)
    _audit(context, method, "payments.method.created", code=method.code)
    return method


@business_atomic
def update_payment_method(context: BusinessContext, *, payment_method_id, name):
    _authorize(context, MANAGE_METHODS)
    method = _locked_method(context, payment_method_id)
    name = _value("name", domain.normalized_text, name, maximum=160, required=True)
    if method.name != name:
        method.name = name
        method._persist(_METHOD_WRITE_TOKEN)
        _audit(context, method, "payments.method.updated", fields=["name"])
    return method


@business_atomic
def set_payment_method_active(context: BusinessContext, *, payment_method_id, is_active):
    _authorize(context, MANAGE_METHODS)
    method = _locked_method(context, payment_method_id)
    if type(is_active) is not bool:
        raise ValidationError({"is_active": "Use a boolean activity value."})
    if method.is_active != is_active:
        method.is_active = is_active
        method._persist(_METHOD_WRITE_TOKEN)
        _audit(
            context, method, "payments.method.updated", fields=["is_active"], is_active=is_active
        )
    return method


def _number():
    return f"PAY-{uuid4().hex.upper()}"


def _collision(exc):
    """Only positively identified uniqueness constraints qualify for recovery."""
    diag = getattr(exc.__cause__, "diag", None)
    constraint = getattr(diag, "constraint_name", None)
    for kind, name, column in (
        ("number", "payments_company_number_uniq", "number"),
        ("key", "payments_company_key_uniq", "idempotency_key"),
    ):
        sqlite_message = (
            "UNIQUE constraint failed: payments_payment.company_id, payments_payment." + column
        )
        if constraint == name or str(exc) == sqlite_message:
            return kind
    return None


def _existing(context, key):
    if key is None:
        return None
    return (
        Payment.objects.select_for_update()
        .filter(company_id=context.company_id, idempotency_key=key)
        .first()
    )


def _recover(existing, payload):
    proposed = dict(payload)
    proposed["payment_date"] = proposed["payment_date"] or existing.payment_date
    proposed["amount"] = _value(
        "amount",
        domain.receipt_amount,
        proposed["amount"],
        precision=existing.currency_decimal_places_snapshot,
    )
    if any(getattr(existing, field) != value for field, value in proposed.items()):
        raise ValidationError("Idempotency key belongs to a different receipt request.")
    return existing


@business_atomic
def record_payment(
    context: BusinessContext,
    *,
    payer_party_id,
    currency_id,
    amount,
    payment_method_id,
    payment_date=None,
    external_reference=None,
    idempotency_key=None,
    notes=None,
):
    _authorize(context, RECORD_PAYMENTS)
    key = _value(
        "idempotency_key", domain.normalized_text, idempotency_key, maximum=128, nullable=True
    )
    payload = {
        "payer_party_id": _value("payer_party", domain.canonical_uuid, payer_party_id),
        "currency_id": _value("currency", domain.canonical_uuid, currency_id),
        "payment_method_id": _value("payment_method", domain.canonical_uuid, payment_method_id),
        "payment_date": _value("payment_date", domain.canonical_date, payment_date),
        "amount": amount,
        "external_reference": _value(
            "external_reference", domain.normalized_text, external_reference, maximum=128
        ),
        "notes": _value("notes", domain.normalized_text, notes),
    }
    existing = _existing(context, key)
    if existing is not None:
        return _recover(existing, payload)
    method = _locked_method(context, payload["payment_method_id"])
    if not method.is_active:
        raise ValidationError({"payment_method": "Select an active payment method."})
    try:
        party = Party.objects.select_for_update().get(
            pk=payload["payer_party_id"],
            company_id=context.company_id,
            is_active=True,
            party_type__in=[Party.Type.PERSON, Party.Type.ORGANIZATION],
        )
    except Party.DoesNotExist as exc:
        raise ValidationError({"payer_party": "Select an active payer in this company."}) from exc
    try:
        currency = Currency.objects.select_for_update().get(
            pk=payload["currency_id"], is_active=True
        )
    except Currency.DoesNotExist as exc:
        raise ValidationError({"currency": "Select an active currency."}) from exc
    precision = _value("currency", domain.currency_precision, currency.decimal_places)
    # Keep omitted date in request payload for collision recovery across local midnight.
    data = dict(payload)
    data["payment_date"] = data["payment_date"] or company_local_date(context.company_id)
    data["amount"] = _value("amount", domain.receipt_amount, amount, precision=precision)
    payment = Payment(
        company_id=context.company_id,
        **data,
        idempotency_key=key,
        payer_display_name_snapshot=party.display_name,
        payer_legal_name_snapshot=party.legal_name,
        currency_code_snapshot=currency.code,
        currency_decimal_places_snapshot=precision,
        payment_method_code_snapshot=method.code,
        payment_method_name_snapshot=method.name,
        recorded_at=timezone.now(),
    )
    for attempt in range(3):
        payment.number = _number()
        try:
            with business_atomic_context():
                payment._insert(_RECEIPT_INSERT_TOKEN)
        except IntegrityError as exc:
            collision = _collision(exc)
            if collision == "key":
                existing = _existing(context, key)
                if existing is not None:
                    return _recover(existing, payload)
            if (
                collision != "number"
                or not Payment.objects.filter(
                    company_id=context.company_id, number=payment.number
                ).exists()
            ):
                raise
            if attempt == 2:
                raise ValidationError("Could not allocate a unique receipt number.") from exc
        else:
            break
    _audit(
        context,
        payment,
        "payments.payment.recorded",
        number=payment.number,
        currency=payment.currency_code_snapshot,
        amount=payment.formatted_amount,
        payment_method_id=str(method.pk),
    )
    return payment
