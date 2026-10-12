"""PAY-INT-owned immutable allocation accounting facts; not unused capacity."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from businessos.core.database import business_atomic
from businessos.modules.billing.accounting_basis import invoice_accounting_basis
from businessos.modules.payments.selectors import payment_receipt_basis

from .authorization import authorize
from .manifest import VIEW_ALLOCATIONS
from .models import PaymentAllocation
from .selectors import validate_history

ACCOUNTING_BASIS_VERSION = 1


@dataclass(frozen=True, slots=True)
class AllocationAccountingBasisV1:
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    payment_id: UUID
    invoice_id: UUID
    amount: Decimal
    payer_party_id: UUID
    bill_to_party_id: UUID
    payment_currency_id: UUID
    invoice_currency_id: UUID
    payment_currency_code: str
    invoice_currency_code: str
    payment_precision: int
    invoice_precision: int
    original_receipt_amount: Decimal
    original_invoice_total: Decimal
    payment_date: date
    recorded_at: datetime
    issued_at: datetime


@business_atomic
def allocation_accounting_basis(context, allocation_id):
    authorize(context, VIEW_ALLOCATIONS)
    allocation = PaymentAllocation.objects.filter(
        pk=allocation_id, company_id=context.company_id
    ).first()
    if allocation is None:
        raise PermissionDenied("Allocation is unavailable.")
    # Persisted IDs, never alternate caller choices, define the parent lock sequence.
    payment = payment_receipt_basis(context, allocation.payment_id)
    authorize(context, VIEW_ALLOCATIONS)
    invoice = invoice_accounting_basis(context, allocation.invoice_id)
    authorize(context, VIEW_ALLOCATIONS)
    validate_history(context)
    if (payment.payer_party_id, payment.currency_id, payment.currency_code, payment.precision) != (
        invoice.bill_to_party_id,
        invoice.currency_id,
        invoice.currency_code,
        invoice.precision,
    ) or not 0 < allocation.amount <= min(payment.amount, invoice.original_total):
        raise ValidationError("Allocation accounting provenance is incompatible.")
    for stamp in (allocation.created_at, allocation.updated_at, payment.recorded_at):
        if stamp is None or timezone.is_naive(stamp):
            raise ValidationError("Allocation accounting timestamp is incomplete.")
    return AllocationAccountingBasisV1(
        allocation.pk,
        allocation.company_id,
        allocation.created_at,
        allocation.updated_at,
        payment.id,
        invoice.id,
        allocation.amount,
        payment.payer_party_id,
        invoice.bill_to_party_id,
        payment.currency_id,
        invoice.currency_id,
        payment.currency_code,
        invoice.currency_code,
        payment.precision,
        invoice.precision,
        payment.amount,
        invoice.original_total,
        payment.payment_date,
        payment.recorded_at,
        invoice.issued_at,
    )
