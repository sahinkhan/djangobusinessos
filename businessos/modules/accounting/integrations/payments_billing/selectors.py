from django.core.exceptions import ValidationError

from businessos.modules.payments.integrations.billing.models import PaymentAllocation
from businessos.modules.payments.integrations.billing.selectors import allocation_accounting_basis

from ..admission import admission, authorize
from ..billing.selectors import invoice_posting_reference
from ..domain import PostingOutcomeV1, uuid
from ..evidence import (
    invoice_certificate,
    lock_entries,
    raw_provenance,
    require_base,
    source_in_scope,
    validate_posting,
)
from .models import EFFECT, AllocationPosting


def certificate(context, binding, basis, prior):
    if (
        prior is None
        or prior.id != binding.invoice_posting_id
        or prior.invoice_id != basis.invoice_id
        or prior.ar_account_id != binding.ar_account_id
        or prior.created_at > binding.created_at
        or basis.created_at > binding.created_at
        or basis.recorded_at > binding.created_at
    ):
        raise ValidationError("Invoice posting prerequisite is incompatible.")
    invoice_certificate(context, prior)
    return validate_posting(
        context,
        binding,
        source="allocation",
        amount=basis.amount,
        business_date=basis.payment_date,
        party_id=basis.payer_party_id,
        first_id=binding.cash_account_id,
        second_id=binding.ar_account_id,
        effect=EFFECT,
        currency_code=basis.payment_currency_code,
        source_precision=basis.payment_precision,
    )


def allocation_posting_status(context, allocation_id):
    return _status(context, allocation_id)


def allocation_action_basis(context, allocation_id):
    return _status(context, allocation_id, create=True)


def _status(context, allocation_id, *, create=False):
    allocation_id = uuid("allocation_id", allocation_id)
    try:
        with admission(context, allocation=True, create=create) as company:
            source_in_scope(PaymentAllocation, context, allocation_id)
            raw_provenance(context, allocation=True)
            basis = allocation_accounting_basis(context, allocation_id)
            authorize(context, allocation=True, create=create)
            require_base(company, basis.payment_currency_id, basis.payment_currency_code)
            prior = invoice_posting_reference(context, basis.invoice_id)
            authorize(context, allocation=True, create=create)
            binding = AllocationPosting.objects.filter(
                company_id=context.company_id, allocation_id=allocation_id
            ).first()
            if prior is None:
                if binding is not None:
                    raise ValidationError("Missing prerequisite for existing allocation posting.")
                return PostingOutcomeV1(
                    "NOT_POSTED",
                    source_id=allocation_id,
                    effect=EFFECT,
                    reason="invoice_accounting_not_posted",
                )
            lock_entries(
                context,
                *(
                    [prior.journal_entry_id, binding.journal_entry_id]
                    if binding
                    else [prior.journal_entry_id]
                ),
            )
            invoice_certificate(context, prior)
            authorize(context, allocation=True, create=create)
            if binding is not None:
                outcome = certificate(context, binding, basis, prior)
                authorize(context, allocation=True, create=create)
                return outcome
            outcome = PostingOutcomeV1(
                "NOT_POSTED",
                source_id=allocation_id,
                effect=EFFECT,
                amount=basis.amount,
                business_date=basis.payment_date,
                currency_code=basis.payment_currency_code,
                precision=basis.payment_precision,
            )
            authorize(context, allocation=True, create=create)
            return outcome
    except ValidationError:
        return PostingOutcomeV1.unavailable("incompatible")
