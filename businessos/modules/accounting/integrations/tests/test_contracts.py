from decimal import Decimal
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models

from businessos.core.audit.models import AuditEntry
from businessos.core.reference.models import Currency
from businessos.modules.accounting import services as accounting
from businessos.modules.accounting.integrations.billing.models import InvoicePosting
from businessos.modules.accounting.integrations.billing.selectors import invoice_posting_status
from businessos.modules.accounting.integrations.domain import source_amount
from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
from businessos.modules.accounting.models import JournalEntry, JournalEntryLine
from businessos.modules.billing.models import InvoiceLine

from .test_outcomes import allocation_post, invoice_post

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("precision", range(9))
@pytest.mark.parametrize("same", [False, True])
def test_frozen_and_live_precision(business_context, outcomes, currency, precision, same):
    Currency.objects.filter(pk=currency.pk).update(decimal_places=precision)
    invoice, _, _ = outcomes["sources"]("1", None)
    if not same:
        Currency.objects.filter(pk=currency.pk).update(decimal_places=(precision + 1) % 9)
    result = invoice_post(business_context, outcomes, invoice)
    assert result.amount == 1
    assert result.precision == (precision if same else (precision + 1) % 9)
    Currency.objects.filter(pk=currency.pk).update(decimal_places=(precision + 3) % 9)
    assert invoice_post(business_context, outcomes, invoice) == result


@pytest.mark.parametrize(
    "raw",
    [
        float("nan"),
        1.0,
        True,
        False,
        "NaN",
        "Infinity",
        "-Infinity",
        "not-a-number",
        "1e30",
        "-1",
        "0.000000001",
    ],
)
def test_exact_amount_rules(raw):
    with pytest.raises(ValidationError):
        source_amount(raw, 8)


@pytest.mark.parametrize("precision", range(9))
def test_exact_amount_boundary(precision):
    number = Decimal("999999999999999999999999999999." + "9" * precision)
    assert source_amount(number, precision) == number
    assert source_amount("1.00000000", precision) == 1


@pytest.mark.parametrize("field", ["journal_id", "ar_account_id", "revenue_account_id"])
def test_retry_alternate_uuid_never_looked_up(business_context, outcomes, field):
    invoice, _, _ = outcomes["sources"]("100", None)
    first = invoice_post(business_context, outcomes, invoice)
    with pytest.raises(ValidationError) as error:
        invoice_post(business_context, outcomes, invoice, **{field: uuid4()})
    assert error.value.code == "idempotency_conflict"
    assert invoice_post(business_context, outcomes, invoice) == first


@pytest.mark.parametrize("field", ["journal_id", "ar_account_id", "cash_account_id"])
def test_allocation_retry_choices(business_context, outcomes, field):
    invoice, _, allocation = outcomes["sources"]()
    invoice_post(business_context, outcomes, invoice)
    first = allocation_post(business_context, outcomes, allocation)
    with pytest.raises(ValidationError) as error:
        allocation_post(business_context, outcomes, allocation, **{field: uuid4()})
    assert error.value.code == "idempotency_conflict"
    assert allocation_post(business_context, outcomes, allocation) == first


@pytest.mark.parametrize("retired", ["journal", "ar", "revenue", "party"])
def test_new_activity_and_historical_retry(business_context, outcomes, retired):
    invoice, _, _ = outcomes["sources"]("100", None)
    row = outcomes[retired]
    models.QuerySet.update(type(row).objects.filter(pk=row.pk), is_active=False)
    with pytest.raises(ValidationError):
        invoice_post(business_context, outcomes, invoice)
    models.QuerySet.update(type(row).objects.filter(pk=row.pk), is_active=True)
    first = invoice_post(business_context, outcomes, invoice)
    models.QuerySet.update(type(row).objects.filter(pk=row.pk), is_active=False)
    assert invoice_post(business_context, outcomes, invoice) == first


@pytest.mark.parametrize(
    "mutation",
    [
        "entry_memo",
        "entry_date",
        "entry_draft",
        "entry_currency",
        "entry_precision",
        "line_amount",
        "line_description",
        "line_party",
        "line_position",
        "missing_line",
        "extra_line",
        "binding_effect",
        "binding_account",
        "binding_journal",
        "source_total",
    ],
)
def test_corrupt_intrinsic_never_certified(business_context, outcomes, mutation):
    invoice, _, _ = outcomes["sources"]("100", None)
    first = invoice_post(business_context, outcomes, invoice)
    entry = JournalEntry.objects.get(pk=first.journal_entry_id)
    line = JournalEntryLine.objects.filter(journal_entry=entry).first()
    binding = InvoicePosting.objects.get(pk=first.binding_id)
    if mutation.startswith("entry_"):
        changes = {
            "entry_memo": {"memo": "corrupt"},
            "entry_date": {"entry_date": "2026-10-11"},
            "entry_draft": {"status": "DRAFT", "posted_at": None},
            "entry_currency": {"base_currency_code_snapshot": "EUR"},
            "entry_precision": {"base_currency_precision_snapshot": 0},
        }[mutation]
        if mutation == "entry_precision":
            models.QuerySet.update(JournalEntryLine.objects.filter(pk=line.pk), debit="100.1")
        models.QuerySet.update(JournalEntry.objects.filter(pk=entry.pk), **changes)
    elif mutation == "missing_line":
        models.QuerySet.delete(JournalEntryLine.objects.filter(pk=line.pk))
    elif mutation == "extra_line":
        clone = JournalEntryLine.objects.get(pk=line.pk)
        clone.pk = uuid4()
        clone.position = 3
        models.Model.save(clone, force_insert=True)
    elif mutation.startswith("line_"):
        changes = {
            "line_amount": {"debit": "99"},
            "line_description": {"description": "corrupt"},
            "line_party": {"party_id": None},
            "line_position": {"position": 3},
        }[mutation]
        models.QuerySet.update(JournalEntryLine.objects.filter(pk=line.pk), **changes)
    elif mutation == "binding_effect":
        # A CHECK backs the effect, so exercise semantic corruption through an allowed field.
        models.QuerySet.update(
            InvoicePosting.objects.filter(pk=binding.pk),
            invoice_id=outcomes["sources"]("1", None)[0].pk,
        )
    elif mutation == "binding_account":
        models.QuerySet.update(
            InvoicePosting.objects.filter(pk=binding.pk), ar_account_id=outcomes["cash"].pk
        )
    elif mutation == "binding_journal":
        journal = accounting.create_journal(business_context, code="OTHER", name="Other")
        models.QuerySet.update(InvoicePosting.objects.filter(pk=binding.pk), journal_id=journal.pk)
    else:
        models.QuerySet.update(InvoiceLine.objects.filter(invoice=invoice), unit_price="0")
    source_id = binding.invoice_id
    binding.refresh_from_db()
    if mutation == "binding_effect":
        source_id = binding.invoice_id
    assert invoice_posting_status(business_context, source_id).state == "UNAVAILABLE"
    with pytest.raises(ValidationError):
        from businessos.modules.accounting.integrations.billing.services import (
            post_billing_invoice_outcome,
        )

        post_billing_invoice_outcome(
            business_context,
            invoice_id=source_id,
            journal_id=outcomes["journal"].pk,
            ar_account_id=outcomes["ar"].pk,
            revenue_account_id=outcomes["revenue"].pk,
        )


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize(
    "path",
    [
        "save",
        "delete",
        "update",
        "bulk_update",
        "bulk_create",
        "queryset_delete",
        "create",
        "get_or_create",
        "update_or_create",
    ],
)
def test_public_binding_orm_rejected(business_context, outcomes, effect, path):
    invoice, _, allocation = outcomes["sources"]()
    first = invoice_post(business_context, outcomes, invoice)
    if effect == "allocation":
        first = allocation_post(business_context, outcomes, allocation)
    model = InvoicePosting if effect == "invoice" else AllocationPosting
    binding = model.objects.get(pk=first.binding_id)
    qs = model.objects.filter(pk=binding.pk)
    operation = {
        "save": lambda: binding.save(),
        "delete": lambda: binding.delete(),
        "update": lambda: qs.update(effect="other"),
        "bulk_update": lambda: model.objects.bulk_update([binding], ["effect"]),
        "bulk_create": lambda: model.objects.bulk_create([binding], ignore_conflicts=True),
        "queryset_delete": lambda: qs.delete(),
        "create": lambda: model.objects.create(),
        "get_or_create": lambda: model.objects.get_or_create(pk=binding.pk),
        "update_or_create": lambda: model.objects.update_or_create(pk=binding.pk),
    }[path]
    before = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        operation()
    assert model.objects.count() == 1 and AuditEntry.objects.count() == before


def test_direct_missing_source_is_denied(business_context):
    with pytest.raises(PermissionDenied):
        invoice_posting_status(business_context, uuid4())


def test_no_automatic_accounting_write(business_context, outcomes):
    outcomes["sources"]()
    assert not JournalEntry.objects.exists()
    assert not InvoicePosting.objects.exists()
    assert not AllocationPosting.objects.exists()
