from decimal import ROUND_HALF_UP, Decimal, localcontext
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.audit.models import AuditEntry
from businessos.core.reference.models import Currency
from businessos.modules.accounting.integrations.billing.selectors import invoice_posting_status
from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
from businessos.modules.accounting.integrations.payments_billing.selectors import (
    allocation_posting_status,
)
from businessos.modules.accounting.models import JournalEntry, JournalEntryLine
from businessos.modules.billing import services as billing
from businessos.modules.billing.models import InvoiceLine

from .test_outcomes import allocation_post, invoice_post

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("precision", range(9))
def test_fractional_source_rounds_once_and_posting_never_rounds(
    business_context, outcomes, currency, precision
):
    from django.db import connection

    if connection.vendor == "sqlite" and precision > 4:
        pytest.skip("SQLite's binary SQL arithmetic is not authoritative high-precision evidence.")
    Currency.objects.filter(pk=currency.pk).update(decimal_places=precision)
    invoice = billing.create_invoice(
        business_context, bill_to_party_id=outcomes["party"].pk, currency_id=currency.pk
    )
    for _ in range(2):
        billing.add_invoice_line(
            business_context,
            invoice.pk,
            description="Fraction",
            quantity="1.2345",
            unit_price="6.7890",
        )
    invoice = billing.issue_invoice(business_context, invoice.pk)
    with localcontext() as ctx:
        ctx.prec = 80
        expected = (Decimal("1.2345") * Decimal("6.7890") * 2).quantize(
            Decimal(1).scaleb(-precision), rounding=ROUND_HALF_UP
        )
    assert invoice_post(business_context, outcomes, invoice).amount == expected


def test_nonrepresentable_live_precision_rolls_back(business_context, outcomes, currency):
    invoice, _, _ = outcomes["sources"]("1.01", None)
    Currency.objects.filter(pk=currency.pk).update(decimal_places=0)
    before = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        invoice_post(business_context, outcomes, invoice)
    assert not JournalEntry.objects.exists() and AuditEntry.objects.count() == before


@pytest.mark.parametrize("zero", [False, True])
def test_foreign_currency_is_not_eligible_even_for_zero(business_context, outcomes, zero):
    eur = Currency.objects.create(code="EUR", name="Euro")
    invoice = billing.create_invoice(
        business_context, bill_to_party_id=outcomes["party"].pk, currency_id=eur.pk
    )
    billing.add_invoice_line(
        business_context,
        invoice.pk,
        description="Foreign",
        quantity="1",
        unit_price="0" if zero else "1",
    )
    invoice = billing.issue_invoice(business_context, invoice.pk)
    assert invoice_posting_status(business_context, invoice.pk).state == "UNAVAILABLE"
    with pytest.raises(ValidationError):
        invoice_post(business_context, outcomes, invoice)
    assert not JournalEntry.objects.exists()


def test_organization_and_matching_ar(business_context, outcomes):
    outcomes["party"].party_type = "organization"
    outcomes["party"].save()
    invoice, _, allocation = outcomes["sources"]()
    invoice_post(business_context, outcomes, invoice)
    with pytest.raises(ValidationError):
        allocation_post(business_context, outcomes, allocation, cash_account_id=outcomes["ar"].pk)
    with pytest.raises(ValidationError):
        allocation_post(business_context, outcomes, allocation, ar_account_id=outcomes["cash"].pk)
    assert allocation_post(business_context, outcomes, allocation).amount == 40


def test_unrequested_bound_corruption_is_not_ignored(business_context, outcomes):
    first, _, _ = outcomes["sources"]("1", None)
    unrelated, _, _ = outcomes["sources"]("2", None)
    invoice_post(business_context, outcomes, first)
    corrupted = invoice_post(business_context, outcomes, unrelated)
    models.QuerySet.update(
        JournalEntryLine.objects.filter(journal_entry_id=corrupted.journal_entry_id, position=2),
        credit="3",
    )
    assert invoice_posting_status(business_context, first.pk).state == "UNAVAILABLE"
    with pytest.raises(ValidationError):
        invoice_post(business_context, outcomes, first)


@pytest.mark.parametrize(
    "mutation",
    ["wrong_ar", "same_cash_ar", "entry_reuse", "source_amount", "timestamp", "prerequisite"],
)
def test_corrupt_allocation_never_certified(business_context, outcomes, mutation):
    invoice, _, allocation = outcomes["sources"]()
    prior = invoice_post(business_context, outcomes, invoice)
    posted = allocation_post(business_context, outcomes, allocation)
    binding = AllocationPosting.objects.get(pk=posted.binding_id)
    changes = {
        "wrong_ar": {"ar_account_id": outcomes["cash"].pk},
        "same_cash_ar": {"cash_account_id": outcomes["ar"].pk},
        "entry_reuse": {"journal_entry_id": prior.journal_entry_id},
        "timestamp": {"created_at": "2000-01-01T00:00:00Z"},
        "prerequisite": {"invoice_posting_id": uuid4()},
    }
    if mutation == "source_amount":
        models.QuerySet.update(type(allocation).objects.filter(pk=allocation.pk), amount="41")
    elif mutation == "prerequisite":
        # Valid FK but semantically wrong prerequisite from a different issued invoice.
        other, _, _ = outcomes["sources"]("1", None)
        other_posted = invoice_post(business_context, outcomes, other)
        models.QuerySet.update(
            AllocationPosting.objects.filter(pk=binding.pk),
            invoice_posting_id=other_posted.binding_id,
        )
    else:
        models.QuerySet.update(AllocationPosting.objects.filter(pk=binding.pk), **changes[mutation])
    assert allocation_posting_status(business_context, allocation.pk).state == "UNAVAILABLE"
    with pytest.raises(ValidationError):
        allocation_post(business_context, outcomes, allocation)


def test_zero_malformed_source_is_not_no_effect(business_context, outcomes):
    zero, _, _ = outcomes["sources"]("0", None)
    models.QuerySet.update(InvoiceLine.objects.filter(invoice=zero), description="")
    assert invoice_posting_status(business_context, zero.pk).state == "UNAVAILABLE"
    with pytest.raises(ValidationError):
        invoice_post(business_context, outcomes, zero)
    assert not JournalEntry.objects.exists()
