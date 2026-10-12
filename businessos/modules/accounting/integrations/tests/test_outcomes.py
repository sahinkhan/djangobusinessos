from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError

from businessos.core.audit.models import AuditEntry
from businessos.modules.accounting.integrations.billing.models import EFFECT as INVOICE_EFFECT
from businessos.modules.accounting.integrations.billing.models import InvoicePosting
from businessos.modules.accounting.integrations.billing.selectors import invoice_posting_status
from businessos.modules.accounting.integrations.billing.services import post_billing_invoice_outcome
from businessos.modules.accounting.integrations.payments_billing.models import (
    EFFECT as ALLOCATION_EFFECT,
)
from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
from businessos.modules.accounting.integrations.payments_billing.selectors import (
    allocation_posting_status,
)
from businessos.modules.accounting.integrations.payments_billing.services import (
    post_payment_allocation_outcome,
)
from businessos.modules.accounting.models import JournalEntry, JournalEntryLine

pytestmark = pytest.mark.django_db


def invoice_post(context, sources, invoice, **changes):
    return post_billing_invoice_outcome(
        context,
        invoice_id=invoice.pk,
        **(
            {
                "journal_id": sources["journal"].pk,
                "ar_account_id": sources["ar"].pk,
                "revenue_account_id": sources["revenue"].pk,
            }
            | changes
        ),
    )


def allocation_post(context, sources, allocation, **changes):
    return post_payment_allocation_outcome(
        context,
        allocation_id=allocation.pk,
        **(
            {
                "journal_id": sources["journal"].pk,
                "ar_account_id": sources["ar"].pk,
                "cash_account_id": sources["cash"].pk,
            }
            | changes
        ),
    )


def test_exact_invoice_and_partial_allocation(business_context, outcomes):
    invoice, payment, allocation = outcomes["sources"]()
    assert not JournalEntry.objects.exists()
    result = invoice_post(business_context, outcomes, invoice)
    assert result.state == "POSTED" and result.amount == Decimal("100")
    lines = list(JournalEntryLine.objects.filter(journal_entry_id=result.journal_entry_id))
    assert [
        (line.position, line.account_id, line.party_id, line.debit, line.credit) for line in lines
    ] == [
        (1, outcomes["ar"].pk, outcomes["party"].pk, Decimal("100"), Decimal(0)),
        (2, outcomes["revenue"].pk, None, Decimal(0), Decimal("100")),
    ]
    allocated = allocation_post(business_context, outcomes, allocation)
    assert allocated.amount == Decimal("40")
    assert allocated.business_date == payment.payment_date
    assert allocated.journal_entry_id != result.journal_entry_id
    assert invoice_posting_status(business_context, invoice.pk) == result
    assert allocation_posting_status(business_context, allocation.pk) == allocated
    audits = AuditEntry.objects.filter(action__startswith="accounting.entry.")
    assert audits.count() == 8
    assert AuditEntry.objects.filter(action__endswith="posting.created").count() == 2
    for action, source_key, source, effect, outcome in (
        ("invoice", "invoice_id", invoice, INVOICE_EFFECT, result),
        ("allocation", "allocation_id", allocation, ALLOCATION_EFFECT, allocated),
    ):
        audit = AuditEntry.objects.get(action=f"accounting.{action}_posting.created")
        assert audit.metadata[source_key] == str(source.pk)
        assert audit.metadata["effect"] == effect
        assert audit.metadata["entry_id"] == str(outcome.journal_entry_id)


def test_allocation_uses_payment_date_before_invoice_date(business_context, outcomes):
    invoice, payment, allocation = outcomes["sources"](payment_date="2026-10-01")
    prior = invoice_post(business_context, outcomes, invoice)
    result = allocation_post(business_context, outcomes, allocation)
    assert result.business_date == payment.payment_date < invoice.invoice_date
    assert prior.business_date == invoice.invoice_date
    assert JournalEntry.objects.get(pk=result.journal_entry_id).entry_date == payment.payment_date


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
def test_retry_and_conflict(business_context, outcomes, effect):
    invoice, _, allocation = outcomes["sources"]()
    invoice_result = invoice_post(business_context, outcomes, invoice)
    post = invoice_post if effect == "invoice" else allocation_post
    source = invoice if effect == "invoice" else allocation
    first = invoice_result if effect == "invoice" else post(business_context, outcomes, source)
    audit_count = AuditEntry.objects.count()
    assert post(business_context, outcomes, source) == first
    with pytest.raises(ValidationError, match="differ"):
        post(business_context, outcomes, source, journal_id=uuid4())
    assert AuditEntry.objects.count() == audit_count
    assert JournalEntry.objects.count() == (1 if effect == "invoice" else 2)


def test_explicit_prerequisite(business_context, outcomes):
    invoice, _, allocation = outcomes["sources"]()
    with pytest.raises(ValidationError, match="required first"):
        allocation_post(business_context, outcomes, allocation)
    assert not JournalEntry.objects.exists()
    assert not AllocationPosting.objects.exists()
    assert allocation_posting_status(business_context, allocation.pk).reason == (
        "invoice_accounting_not_posted"
    )


def test_repeatable_zero(business_context, outcomes):
    invoice, _, _ = outcomes["sources"]("0", None)
    before = AuditEntry.objects.count()
    for _ in range(2):
        result = post_billing_invoice_outcome(business_context, invoice_id=invoice.pk)
        assert result.state == "NO_ACCOUNTING_EFFECT" and result.amount == 0
    assert not InvoicePosting.objects.exists() and not JournalEntry.objects.exists()
    assert AuditEntry.objects.count() == before
    with pytest.raises(ValidationError, match="must not supply"):
        invoice_post(business_context, outcomes, invoice)


@pytest.mark.parametrize(
    "failure", ["create", "first_line", "second_line", "post", "binding", "audit"]
)
def test_atomic_failure(business_context, outcomes, failure):
    invoice, _, _ = outcomes["sources"]("100", None)
    before = AuditEntry.objects.count()
    from businessos.modules.accounting import services as owner
    from businessos.modules.accounting.integrations.billing import services

    if failure == "binding":
        target = patch.object(InvoicePosting, "_insert", side_effect=RuntimeError("injected"))
    elif failure == "audit":
        target = patch.object(services, "record_audit_entry", side_effect=RuntimeError("injected"))
    elif failure in {"first_line", "second_line"}:
        original = owner.add_journal_entry_line
        count = 0

        def line(*args, **kwargs):
            nonlocal count
            count += 1
            if count == (1 if failure == "first_line" else 2):
                raise RuntimeError("injected")
            return original(*args, **kwargs)

        target = patch.object(owner, "add_journal_entry_line", side_effect=line)
    else:
        target = patch.object(
            owner,
            ("create_journal_entry" if failure == "create" else "post_journal_entry"),
            side_effect=RuntimeError("injected"),
        )
    with target, pytest.raises(RuntimeError, match="injected"):
        invoice_post(business_context, outcomes, invoice)
    assert not JournalEntry.objects.exists() and not JournalEntryLine.objects.exists()
    assert not InvoicePosting.objects.exists()
    assert AuditEntry.objects.count() == before
