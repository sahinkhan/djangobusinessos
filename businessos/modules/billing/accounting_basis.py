"""Versioned Billing-owned read contract; totals remain Billing's responsibility."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import connections
from django.utils import timezone

from businessos.core.database import business_atomic, current_database_alias

from .accounting_evidence import admit_owner_basis
from .models import Invoice
from .selectors import invoice_financial_basis

ACCOUNTING_BASIS_VERSION = 1


@dataclass(frozen=True, slots=True)
class InvoiceAccountingBasisV1:
    id: UUID
    company_id: UUID
    bill_to_party_id: UUID
    status: str
    issued_at: datetime
    invoice_date: date
    currency_id: UUID
    currency_code: str
    precision: int
    original_total: Decimal


def invoice_accounting_basis(context, invoice_id, *, lock=True):
    if not lock and not connections[current_database_alias()].in_atomic_block:
        raise ValidationError("Nonlocking basis requires an outer selected-alias transaction.")
    return _invoice_accounting_basis(context, invoice_id, lock=lock)


@business_atomic
def _invoice_accounting_basis(context, invoice_id, *, lock):
    admit_owner_basis()
    # Existing owner admission always stabilizes Company; lock=False only skips Invoice.
    basis = invoice_financial_basis(context, invoice_id, lock=lock)
    invoice = Invoice.objects.select_related("bill_to_party").get(pk=basis.id)
    invoice_date = invoice.invoice_date
    if invoice.bill_to_party.party_type not in {"person", "organization"}:
        raise ValidationError("Unsupported bill-to Party type.")
    if basis.issued_at is None or timezone.is_naive(basis.issued_at):
        raise ValidationError("Issued timestamp is incomplete.")
    return InvoiceAccountingBasisV1(
        basis.id,
        basis.company_id,
        basis.bill_to_party_id,
        basis.status,
        basis.issued_at,
        invoice_date,
        basis.currency_id,
        basis.currency_code,
        basis.precision,
        basis.original_total,
    )
