from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from businessos.core.audit.services import record_audit_entry
from businessos.core.database import business_atomic_context
from businessos.modules.billing.models import Invoice
from businessos.modules.billing.selectors import invoice_accounting_basis

from ..admission import admission, authorize
from ..domain import PostingOutcomeV1, source_amount, uuid
from ..evidence import (
    compose,
    conflict,
    invoice_certificate,
    lock_choices,
    lock_entries,
    raw_provenance,
    require_base,
    source_in_scope,
)
from .models import _INSERT_TOKEN, EFFECT, InvoicePosting


def _collision(error):
    name = getattr(getattr(error.__cause__, "diag", None), "constraint_name", None)
    text = str(error)
    if name == "invoice_posting_source_uniq" or text == (
        "UNIQUE constraint failed: accounting_billing_invoiceposting.company_id, "
        "accounting_billing_invoiceposting.invoice_id, accounting_billing_invoiceposting.effect"
    ):
        return "source"
    if name == "accounting_billing_invoiceposting_pkey" or text == (
        "UNIQUE constraint failed: accounting_billing_invoiceposting.id"
    ):
        return "id"
    return None


def _recover(context, binding, journal_id, ar_account_id, revenue_account_id):
    lock_entries(context, binding.journal_entry_id)
    outcome = invoice_certificate(context, binding)
    conflict(binding, journal_id, ar_account_id, revenue_account_id, "revenue_account_id")
    authorize(context, create=True)
    return outcome


def post_billing_invoice_outcome(
    context, *, invoice_id, journal_id=None, ar_account_id=None, revenue_account_id=None
):
    invoice_id = uuid("invoice_id", invoice_id)
    selections = [
        uuid(field, raw) if raw is not None else None
        for field, raw in (
            ("journal_id", journal_id),
            ("ar_account_id", ar_account_id),
            ("revenue_account_id", revenue_account_id),
        )
    ]
    journal_id, ar_account_id, revenue_account_id = selections
    with admission(context, create=True) as company:
        source_in_scope(Invoice, context, invoice_id)
        raw_provenance(context)
        basis = invoice_accounting_basis(context, invoice_id)
        authorize(context, create=True)
        require_base(company, basis.currency_id, basis.currency_code)
        binding = InvoicePosting.objects.filter(
            company_id=context.company_id, invoice_id=invoice_id
        ).first()
        if binding is not None:
            return _recover(context, binding, *selections)
        amount = source_amount(basis.original_total, basis.precision)
        if amount == 0:
            if any(choice is not None for choice in selections):
                raise ValidationError("Zero-effect invoices must not supply accounting choices.")
            authorize(context, create=True)
            return PostingOutcomeV1(
                "NO_ACCOUNTING_EFFECT",
                source_id=invoice_id,
                effect=EFFECT,
                amount=amount,
                business_date=basis.invoice_date,
                currency_code=basis.currency_code,
                precision=basis.precision,
            )
        if any(choice is None for choice in selections):
            raise ValidationError("Explicit Journal, AR and Revenue accounts are required.")
        currency = lock_choices(
            context,
            company,
            journal_id=journal_id,
            ar_account_id=ar_account_id,
            other_account_id=revenue_account_id,
            other_type="INCOME",
            party_id=basis.bill_to_party_id,
        )
        source_amount(amount, currency.decimal_places)
        for attempt in range(3):
            try:
                # The losing COMPLETE composition is the savepoint unit, not just insert.
                with business_atomic_context():
                    entry = compose(
                        context,
                        journal_id=journal_id,
                        first_id=ar_account_id,
                        second_id=revenue_account_id,
                        party_id=basis.bill_to_party_id,
                        amount=amount,
                        business_date=basis.invoice_date,
                        source="invoice",
                        source_id=invoice_id,
                    )
                    binding = InvoicePosting(
                        id=uuid4(),
                        company_id=context.company_id,
                        invoice_id=invoice_id,
                        effect=EFFECT,
                        journal_entry_id=entry.pk,
                        journal_id=journal_id,
                        ar_account_id=ar_account_id,
                        revenue_account_id=revenue_account_id,
                    )
                    binding._insert(_INSERT_TOKEN)
                    authorize(context, create=True)
                    outcome = invoice_certificate(context, binding)
                    record_audit_entry(
                        context=context,
                        action="accounting.invoice_posting.created",
                        object_type="accounting.InvoicePosting",
                        object_id=binding.pk,
                        metadata={
                            "invoice_id": str(invoice_id),
                            "effect": EFFECT,
                            "entry_id": str(entry.pk),
                            "journal_id": str(journal_id),
                            "ar_account_id": str(ar_account_id),
                            "revenue_account_id": str(revenue_account_id),
                            "amount": format(amount, f".{basis.precision}f"),
                            "currency": basis.currency_code,
                            "precision": basis.precision,
                            "entry_precision": entry.base_currency_precision_snapshot,
                            "business_date": basis.invoice_date.isoformat(),
                        },
                    )
                    authorize(context, create=True)
                    return outcome
            except IntegrityError as exc:
                kind = _collision(exc)
                if kind == "source":
                    existing = InvoicePosting.objects.filter(
                        company_id=context.company_id, invoice_id=invoice_id, effect=EFFECT
                    ).first()
                    if existing is not None:
                        return _recover(context, existing, *selections)
                if kind != "id" or attempt == 2:
                    raise
        raise ValidationError("Posting UUID collision exhausted.")
