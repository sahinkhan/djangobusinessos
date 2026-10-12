from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from businessos.core.audit.services import record_audit_entry
from businessos.core.database import business_atomic_context
from businessos.modules.payments.integrations.billing.models import PaymentAllocation
from businessos.modules.payments.integrations.billing.selectors import allocation_accounting_basis

from ..admission import admission, authorize
from ..billing.selectors import invoice_posting_reference
from ..domain import source_amount, uuid
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
from .models import _INSERT_TOKEN, EFFECT, AllocationPosting
from .selectors import certificate


def _collision(error):
    name = getattr(getattr(error.__cause__, "diag", None), "constraint_name", None)
    text = str(error)
    if name == "allocation_posting_source_uniq" or text == (
        "UNIQUE constraint failed: accounting_payments_billing_allocationposting.company_id, "
        "accounting_payments_billing_allocationposting.allocation_id, "
        "accounting_payments_billing_allocationposting.effect"
    ):
        return "source"
    if name == "accounting_payments_billing_allocationposting_pkey" or text == (
        "UNIQUE constraint failed: accounting_payments_billing_allocationposting.id"
    ):
        return "id"
    return None


def _recover(context, binding, basis, prior, selections):
    lock_entries(context, prior.journal_entry_id, binding.journal_entry_id)
    outcome = certificate(context, binding, basis, prior)
    conflict(binding, *selections, "cash_account_id")
    authorize(context, allocation=True, create=True)
    return outcome


def post_payment_allocation_outcome(
    context, *, allocation_id, journal_id, cash_account_id, ar_account_id
):
    allocation_id = uuid("allocation_id", allocation_id)
    journal_id = uuid("journal_id", journal_id)
    cash_account_id = uuid("cash_account_id", cash_account_id)
    ar_account_id = uuid("ar_account_id", ar_account_id)
    selections = (journal_id, ar_account_id, cash_account_id)
    with admission(context, allocation=True, create=True) as company:
        source_in_scope(PaymentAllocation, context, allocation_id)
        raw_provenance(context, allocation=True)
        basis = allocation_accounting_basis(context, allocation_id)
        authorize(context, allocation=True, create=True)
        require_base(company, basis.payment_currency_id, basis.payment_currency_code)
        prior = invoice_posting_reference(context, basis.invoice_id)
        binding = AllocationPosting.objects.filter(
            company_id=context.company_id, allocation_id=allocation_id
        ).first()
        if prior is None:
            raise ValidationError(
                "Explicit invoice Accounting posting is required first.",
                code="invoice_accounting_not_posted",
            )
        if binding is not None:
            return _recover(context, binding, basis, prior, selections)
        lock_entries(context, prior.journal_entry_id)
        invoice_certificate(context, prior)
        authorize(context, allocation=True, create=True)
        if prior.ar_account_id != ar_account_id:
            raise ValidationError("Allocation AR must match the prior invoice posting.")
        amount = source_amount(basis.amount, basis.payment_precision)
        currency = lock_choices(
            context,
            company,
            journal_id=journal_id,
            ar_account_id=ar_account_id,
            other_account_id=cash_account_id,
            other_type="ASSET",
            party_id=basis.payer_party_id,
            allocation=True,
        )
        source_amount(amount, currency.decimal_places)
        for attempt in range(3):
            try:
                with business_atomic_context():
                    entry = compose(
                        context,
                        journal_id=journal_id,
                        first_id=cash_account_id,
                        second_id=ar_account_id,
                        party_id=basis.payer_party_id,
                        amount=amount,
                        business_date=basis.payment_date,
                        source="allocation",
                        source_id=allocation_id,
                        allocation=True,
                    )
                    binding = AllocationPosting(
                        id=uuid4(),
                        company_id=context.company_id,
                        allocation_id=allocation_id,
                        effect=EFFECT,
                        journal_entry_id=entry.pk,
                        journal_id=journal_id,
                        ar_account_id=ar_account_id,
                        cash_account_id=cash_account_id,
                        invoice_posting_id=prior.id,
                    )
                    binding._insert(_INSERT_TOKEN)
                    authorize(context, allocation=True, create=True)
                    current_basis = allocation_accounting_basis(context, allocation_id)
                    outcome = certificate(context, binding, current_basis, prior)
                    record_audit_entry(
                        context=context,
                        action="accounting.allocation_posting.created",
                        object_type="accounting.AllocationPosting",
                        object_id=binding.pk,
                        metadata={
                            "allocation_id": str(allocation_id),
                            "effect": EFFECT,
                            "entry_id": str(entry.pk),
                            "invoice_posting_id": str(prior.id),
                            "journal_id": str(journal_id),
                            "ar_account_id": str(ar_account_id),
                            "cash_account_id": str(cash_account_id),
                            "amount": format(amount, f".{basis.payment_precision}f"),
                            "currency": basis.payment_currency_code,
                            "precision": basis.payment_precision,
                            "entry_precision": entry.base_currency_precision_snapshot,
                            "business_date": basis.payment_date.isoformat(),
                        },
                    )
                    authorize(context, allocation=True, create=True)
                    return outcome
            except IntegrityError as exc:
                kind = _collision(exc)
                if kind == "source":
                    existing = AllocationPosting.objects.filter(
                        company_id=context.company_id, allocation_id=allocation_id, effect=EFFECT
                    ).first()
                    if existing is not None:
                        return _recover(context, existing, basis, prior, selections)
                if kind != "id" or attempt == 2:
                    raise
        raise ValidationError("Posting UUID collision exhausted.")
