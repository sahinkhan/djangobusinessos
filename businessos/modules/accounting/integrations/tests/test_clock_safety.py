"""Wall-clock metadata is preserved; immutable structural evidence is authoritative."""

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from businessos.core.audit.models import AuditEntry
from businessos.modules.accounting import services as accounting
from businessos.modules.accounting.integrations.billing.models import InvoicePosting
from businessos.modules.accounting.integrations.billing.selectors import invoice_posting_status
from businessos.modules.accounting.integrations.evidence import _timestamps
from businessos.modules.accounting.integrations.history import validate_binding_history
from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
from businessos.modules.accounting.integrations.payments_billing.selectors import (
    allocation_posting_status,
)
from businessos.modules.accounting.models import JournalEntry, JournalEntryLine
from businessos.modules.accounting.selectors import posted_journal_basis

from .test_outcomes import allocation_post, invoice_post

pytestmark = pytest.mark.django_db


def stored_state():
    # Independently reload native timestamps/identities, not cached outcome objects.
    return tuple(
        tuple(model.objects.order_by("id").values_list(*fields))
        for model, fields in (
            (JournalEntry, ("id", "created_at", "updated_at", "posted_at")),
            (JournalEntryLine, ("id", "created_at", "updated_at", "debit", "credit")),
            (InvoicePosting, ("id", "journal_entry_id", "created_at", "updated_at")),
            (AllocationPosting, ("id", "journal_entry_id", "created_at", "updated_at")),
            (AuditEntry, ("id", "action", "object_id")),
        )
    )


def assert_effect(context, world, result, effect):
    basis = posted_journal_basis(context, result.journal_entry_id)
    amount = Decimal("41.37" if effect == "invoice" else "17.25")
    first = world["ar" if effect == "invoice" else "cash"].pk
    second = world["revenue" if effect == "invoice" else "ar"].pk
    assert [(row.position, row.account_id, row.debit, row.credit) for row in basis.lines] == [
        (1, first, amount, Decimal(0)),
        (2, second, Decimal(0), amount),
    ]
    assert [row.party_id for row in basis.lines] == (
        [world["party"].pk, None] if effect == "invoice" else [None, world["party"].pk]
    )
    assert result.amount == amount and basis.debit == basis.credit == amount
    assert result.posted_at == basis.posted_at
    assert basis.updated_at == basis.posted_at
    assert (
        AuditEntry.objects.filter(
            action="accounting.entry.posted", object_id=str(result.journal_entry_id)
        ).count()
        == 1
    )
    assert (
        AuditEntry.objects.filter(
            action=f"accounting.{effect}_posting.created", object_id=str(result.binding_id)
        ).count()
        == 1
    )


@contextmanager
def clock_step(model, mode, observed):
    real_now = timezone.now
    original_insert = model._insert
    original_post = accounting.post_journal_entry
    original_pre_save = models.DateTimeField.pre_save

    def insert(binding, token):
        if mode not in {"binding_created", "binding_updated"}:
            return original_insert(binding, token)
        stamp = JournalEntry.objects.get(pk=binding.journal_entry_id).posted_at
        values = (
            (stamp - timedelta(milliseconds=1), stamp - timedelta(microseconds=999))
            if mode == "binding_created"
            else (stamp + timedelta(milliseconds=1), stamp)
        )
        with patch.object(timezone, "now", side_effect=values) as clock:
            result = original_insert(binding, token)
        assert clock.call_count == 2
        assert (binding.created_at, binding.updated_at) == values
        observed["binding"] = values
        return result

    def post(context, entry_id):
        if mode != "entry_post":
            return original_post(context, entry_id)
        entry = JournalEntry.objects.get(pk=entry_id)
        # The actual post clock reading is earlier than entry and line creation.
        stamp = entry.created_at - timedelta(milliseconds=1)
        with patch.object(timezone, "now", return_value=stamp):
            result = original_post(context, entry_id)
        observed["posted_at"] = stamp
        return result

    def pre_save(field, instance, add):
        if mode != "line_clock" or not isinstance(instance, JournalEntryLine):
            return original_pre_save(field, instance, add)
        if field.name not in {"created_at", "updated_at"}:
            return original_pre_save(field, instance, add)
        stamp = (
            instance.journal_entry.created_at - timedelta(milliseconds=1)
            if field.name == "created_at"
            else instance.created_at - timedelta(milliseconds=1)
        )
        with patch.object(timezone, "now", return_value=stamp):
            result = original_pre_save(field, instance, add)
        observed[(instance.pk, field.name)] = stamp
        return result

    with (
        patch.object(model, "_insert", insert),
        patch.object(accounting, "post_journal_entry", post),
        patch.object(models.DateTimeField, "pre_save", pre_save),
    ):
        yield
    assert timezone.now is real_now
    assert model._insert is original_insert
    assert accounting.post_journal_entry is original_post
    assert models.DateTimeField.pre_save is original_pre_save


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize(
    "mode", ["normal", "binding_created", "binding_updated", "entry_post", "line_clock"]
)
def test_clock_rollback_composes_and_reloads_without_refresh(
    business_context, outcomes, effect, mode
):
    invoice, payment, allocation = outcomes["sources"]("41.37", "17.25")
    if effect == "allocation":
        invoice_post(business_context, outcomes, invoice)
    model = InvoicePosting if effect == "invoice" else AllocationPosting
    post = invoice_post if effect == "invoice" else allocation_post
    status = invoice_posting_status if effect == "invoice" else allocation_posting_status
    source = invoice if effect == "invoice" else allocation
    observed = {}
    with clock_step(model, mode, observed):
        result = post(business_context, outcomes, source)
    assert result.state == "POSTED"
    binding = model.objects.get(pk=result.binding_id)
    basis = posted_journal_basis(business_context, result.journal_entry_id)
    if "binding" in observed:
        assert (binding.created_at, binding.updated_at) == observed["binding"]
    if mode == "binding_created":
        assert binding.created_at == basis.posted_at - timedelta(milliseconds=1)
    elif mode == "binding_updated":
        assert binding.updated_at == binding.created_at - timedelta(milliseconds=1)
    elif mode == "entry_post":
        assert basis.posted_at == observed["posted_at"] < basis.created_at
    elif mode == "line_clock":
        for line in basis.lines:
            assert line.created_at == observed[(line.id, "created_at")] < basis.created_at
            assert line.updated_at == observed[(line.id, "updated_at")] < line.created_at
    assert result.created_at == binding.created_at
    assert basis.entry_date == (
        invoice.invoice_date if effect == "invoice" else payment.payment_date
    )
    assert_effect(business_context, outcomes, result, effect)
    before = stored_state()
    source.refresh_from_db()
    assert post(business_context, outcomes, source) == result
    assert status(business_context, source.pk) == result
    validate_binding_history(business_context, allocation=True)
    assert stored_state() == before
    # A fresh ordinary composition after the patch verifies no clock-patch leakage.
    other, _, _ = outcomes["sources"]("41.37", None)
    assert_effect(
        business_context, outcomes, invoice_post(business_context, outcomes, other), "invoice"
    )


@pytest.mark.parametrize(
    "field",
    [
        "binding_created",
        "binding_updated",
        "entry_created",
        "line_created",
        "line_updated",
        "invoice_issued",
        "prior_created",
        "allocation_created",
        "payment_recorded",
    ],
)
def test_relative_timestamp_only_is_not_structural_corruption(business_context, outcomes, field):
    invoice, payment, allocation = outcomes["sources"]("41.37", "17.25")
    prior = invoice_post(business_context, outcomes, invoice)
    posted = allocation_post(business_context, outcomes, allocation)
    earlier = datetime(2000, 1, 1, tzinfo=UTC)
    later = datetime(2100, 1, 1, tzinfo=UTC)
    targets = {
        "binding_created": (
            AllocationPosting.objects.filter(pk=posted.binding_id),
            "created_at",
            earlier,
        ),
        "binding_updated": (
            AllocationPosting.objects.filter(pk=posted.binding_id),
            "updated_at",
            earlier,
        ),
        "entry_created": (
            JournalEntry.objects.filter(pk=posted.journal_entry_id),
            "created_at",
            later,
        ),
        "line_created": (
            JournalEntryLine.objects.filter(journal_entry_id=posted.journal_entry_id),
            "created_at",
            later,
        ),
        "line_updated": (
            JournalEntryLine.objects.filter(journal_entry_id=posted.journal_entry_id),
            "updated_at",
            later,
        ),
        "invoice_issued": (type(invoice).objects.filter(pk=invoice.pk), "issued_at", later),
        "prior_created": (InvoicePosting.objects.filter(pk=prior.binding_id), "created_at", later),
        "allocation_created": (
            type(allocation).objects.filter(pk=allocation.pk),
            "created_at",
            later,
        ),
        "payment_recorded": (type(payment).objects.filter(pk=payment.pk), "recorded_at", later),
    }
    rows, name, value = targets[field]
    # Privileged synthetic SQL is NOT an endorsed business mutation path. It isolates
    # chronology from provenance, including the former year-2000 corruption case.
    models.QuerySet.update(rows, **{name: value})
    before = stored_state()
    recovered = allocation_post(business_context, outcomes, allocation)
    assert recovered.state == "POSTED"
    assert recovered.binding_id == posted.binding_id
    assert recovered.journal_entry_id == posted.journal_entry_id
    assert allocation_posting_status(business_context, allocation.pk) == recovered
    assert invoice_posting_status(business_context, invoice.pk).state == "POSTED"
    validate_binding_history(business_context, allocation=True)
    assert stored_state() == before
    assert_effect(business_context, outcomes, recovered, "allocation")
    # Metadata acceptance must never mask a new structural inconsistency.
    models.QuerySet.update(
        JournalEntry.objects.filter(pk=posted.journal_entry_id), memo="corrupt provenance"
    )
    assert allocation_posting_status(business_context, allocation.pk).state == "UNAVAILABLE"
    with pytest.raises(ValidationError):
        allocation_post(business_context, outcomes, allocation)


def test_posted_same_write_equality_still_required(business_context, outcomes):
    invoice, _, _ = outcomes["sources"]("41.37", None)
    result = invoice_post(business_context, outcomes, invoice)
    models.QuerySet.update(
        JournalEntry.objects.filter(pk=result.journal_entry_id),
        updated_at=result.posted_at - timedelta(milliseconds=1),
    )
    with pytest.raises(ValidationError, match="same-write"):
        posted_journal_basis(business_context, result.journal_entry_id)
    assert invoice_posting_status(business_context, invoice.pk).state == "UNAVAILABLE"
    with pytest.raises(ValidationError):
        invoice_post(business_context, outcomes, invoice)


@pytest.mark.parametrize("field", ["created_at", "updated_at"])
@pytest.mark.parametrize("invalid", [None, datetime(2026, 1, 1)])
def test_binding_timestamp_presence_and_awareness_remain_required(field, invalid):
    data = dict(created_at=timezone.now(), updated_at=timezone.now())
    data[field] = invalid
    with pytest.raises(ValidationError):
        _timestamps(SimpleNamespace(**data))


@pytest.mark.parametrize(
    "model,field",
    [
        (JournalEntry, "posted_at"),
        (JournalEntry, "created_at"),
        (JournalEntry, "updated_at"),
        (JournalEntryLine, "created_at"),
        (JournalEntryLine, "updated_at"),
    ],
)
@pytest.mark.parametrize("invalid", [None, datetime(2026, 1, 1)])
def test_owner_timestamp_presence_and_awareness_remain_required(
    business_context, outcomes, model, field, invalid
):
    invoice, _, _ = outcomes["sources"]("41.37", None)
    result = invoice_post(business_context, outcomes, invoice)
    from_db = model.from_db

    def malformed_materialization(db, field_names, values):
        row = from_db(db, field_names, values)
        setattr(row, field, invalid)
        return row

    # Exercise owner validation of malformed materialized metadata without changing
    # schema constraints or relying on a backend accepting naive/null stored data.
    with patch.object(model, "from_db", side_effect=malformed_materialization):
        with pytest.raises(ValidationError):
            posted_journal_basis(business_context, result.journal_entry_id)
        assert invoice_posting_status(business_context, invoice.pk).state == "UNAVAILABLE"
    assert invoice_posting_status(business_context, invoice.pk) == result
