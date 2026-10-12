from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.core.exceptions import ValidationError

from businessos.modules.billing.models import Invoice
from businessos.modules.billing.selectors import invoice_accounting_basis

from ..admission import admission, authorize
from ..domain import PostingOutcomeV1, uuid
from ..evidence import (
    invoice_certificate,
    lock_entries,
    raw_provenance,
    require_base,
    source_in_scope,
)
from .models import EFFECT, InvoicePosting


@dataclass(frozen=True, slots=True)
class InvoicePostingReferenceV1:
    id: UUID
    company_id: UUID
    invoice_id: UUID
    effect: str
    journal_entry_id: UUID
    journal_id: UUID
    ar_account_id: UUID
    revenue_account_id: UUID
    created_at: datetime
    updated_at: datetime

    @property
    def pk(self):
        return self.id


def _reference(binding):
    if binding is None:
        return None
    return InvoicePostingReferenceV1(
        binding.pk,
        binding.company_id,
        binding.invoice_id,
        binding.effect,
        binding.journal_entry_id,
        binding.journal_id,
        binding.ar_account_id,
        binding.revenue_account_id,
        binding.created_at,
        binding.updated_at,
    )


def invoice_posting_reference(context, invoice_id):
    invoice_id = uuid("invoice_id", invoice_id)
    with admission(context):
        source_in_scope(Invoice, context, invoice_id)
        raw_provenance(context)
        invoice_accounting_basis(context, invoice_id, lock=False)
        reference = _reference(
            InvoicePosting.objects.filter(
                invoice_id=invoice_id, company_id=context.company_id
            ).first()
        )
        authorize(context)
        return reference


def invoice_posting_status(context, invoice_id):
    return _status(context, invoice_id)


def invoice_action_basis(context, invoice_id):
    """Prepare an explicit action using create (not implied posting.view) authority."""
    return _status(context, invoice_id, create=True)


def _status(context, invoice_id, *, create=False):
    invoice_id = uuid("invoice_id", invoice_id)
    try:
        with admission(context, create=create) as company:
            source_in_scope(Invoice, context, invoice_id)
            raw_provenance(context)
            basis = invoice_accounting_basis(context, invoice_id)
            authorize(context, create=create)
            require_base(company, basis.currency_id, basis.currency_code)
            binding = InvoicePosting.objects.filter(
                invoice_id=invoice_id, company_id=context.company_id
            ).first()
            if binding is not None:
                lock_entries(context, binding.journal_entry_id)
                outcome = invoice_certificate(context, binding)
                authorize(context, create=create)
                return outcome
            outcome = PostingOutcomeV1(
                "NO_ACCOUNTING_EFFECT" if basis.original_total == 0 else "NOT_POSTED",
                source_id=invoice_id,
                effect=EFFECT,
                amount=basis.original_total,
                business_date=basis.invoice_date,
                currency_code=basis.currency_code,
                precision=basis.precision,
            )
            authorize(context, create=create)
            return outcome
    except ValidationError:
        return PostingOutcomeV1.unavailable("incompatible")
