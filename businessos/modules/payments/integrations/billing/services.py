from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from businessos.core.audit.services import record_audit_entry
from businessos.core.database import (
    business_atomic,
    business_atomic_context,
    current_database_alias,
)
from businessos.modules.billing.selectors import invoice_financial_basis
from businessos.modules.payments.selectors import payment_receipt_basis

from . import domain
from .authorization import authorize
from .compatibility import evidence_profile
from .manifest import CREATE_ALLOCATIONS
from .models import _INSERT_TOKEN, PaymentAllocation
from .selectors import applied, validate_history, value


def _collision(error):
    name = getattr(getattr(error.__cause__, "diag", None), "constraint_name", None)
    if name == "allocation_company_key_uniq" or str(error) == (
        "UNIQUE constraint failed: payments_billing_paymentallocation.company_id, "
        "payments_billing_paymentallocation.idempotency_key"
    ):
        return "key"
    if name == "payments_billing_paymentallocation_pkey" or str(error) == (
        "UNIQUE constraint failed: payments_billing_paymentallocation.id"
    ):
        return "id"
    return None


def _recover(existing, payment_id, invoice_id, amount):
    if (existing.payment_id, existing.invoice_id, existing.amount) != (
        payment_id,
        invoice_id,
        amount,
    ):
        raise ValidationError(
            "Key belongs to a different allocation request.", code="idempotency_conflict"
        )
    return existing


@business_atomic
def create_payment_allocation(context, *, payment_id, invoice_id, amount, idempotency_key):
    authorize(context, CREATE_ALLOCATIONS)
    alias = current_database_alias()
    reason = evidence_profile()
    if reason:
        raise ValidationError(f"Allocation schema is unavailable: {reason}.")
    payment_id = value("payment_id", domain.identity, payment_id)
    invoice_id = value("invoice_id", domain.identity, invoice_id)
    key = value("idempotency_key", domain.key, idempotency_key)
    amount = value("amount", domain.amount, amount, 8)
    existing = (
        PaymentAllocation.objects.using(alias)
        .filter(company_id=context.company_id, idempotency_key=key)
        .first()
    )
    payment = payment_receipt_basis(context, payment_id)
    authorize(context, CREATE_ALLOCATIONS)
    invoice = invoice_financial_basis(context, invoice_id)
    authorize(context, CREATE_ALLOCATIONS)
    amount = value("amount", domain.amount, amount, payment.precision)
    if (payment.payer_party_id, payment.currency_id, payment.currency_code, payment.precision) != (
        invoice.bill_to_party_id,
        invoice.currency_id,
        invoice.currency_code,
        invoice.precision,
    ):
        raise ValidationError(
            {"invoice_id": "Invoice and receipt must share Party, currency and frozen precision."}
        )
    if existing is not None:
        return _recover(existing, payment_id, invoice_id, amount)
    history = validate_history(context)
    if amount > domain.subtract(payment.amount, applied(history.filter(payment_id=payment_id))):
        raise ValidationError("Payment capacity exceeded.", code="payment_capacity_exceeded")
    if amount > domain.subtract(
        invoice.original_total, applied(history.filter(invoice_id=invoice_id))
    ):
        raise ValidationError("Invoice capacity exceeded.", code="invoice_capacity_exceeded")
    allocation = PaymentAllocation(
        company_id=context.company_id,
        payment_id=payment_id,
        invoice_id=invoice_id,
        amount=amount,
        idempotency_key=key,
    )
    for attempt in range(3):
        allocation.id = uuid4()
        try:
            with business_atomic_context():
                allocation._insert(_INSERT_TOKEN)
        except IntegrityError as exc:
            collision = _collision(exc)
            if collision == "key":
                existing = (
                    PaymentAllocation.objects.using(alias)
                    .filter(company_id=context.company_id, idempotency_key=key)
                    .first()
                )
                if existing is not None:
                    return _recover(existing, payment_id, invoice_id, amount)
            if (
                collision != "id"
                or not PaymentAllocation.objects.using(alias).filter(pk=allocation.pk).exists()
            ):
                raise
            if attempt == 2:
                raise ValidationError("Allocation UUID collision exhausted.") from exc
        else:
            break
    record_audit_entry(
        context=context,
        action="payments.allocation.created",
        object_type="payments.PaymentAllocation",
        object_id=allocation.pk,
        metadata={
            "payment_id": str(payment_id),
            "invoice_id": str(invoice_id),
            "amount": format(amount, f".{payment.precision}f"),
            "currency": payment.currency_code,
            "precision": payment.precision,
        },
    )
    return allocation
