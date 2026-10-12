from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import IntegrityError

from businessos.core.audit.models import AuditEntry
from businessos.modules.accounting import services as owner
from businessos.modules.accounting.integrations.billing import services as invoices
from businessos.modules.accounting.integrations.billing.models import InvoicePosting
from businessos.modules.accounting.integrations.bindings import BindingQuerySet
from businessos.modules.accounting.integrations.payments_billing import services as allocations
from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
from businessos.modules.accounting.models import JournalEntry, JournalEntryLine

from .test_outcomes import allocation_post, invoice_post

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize(
    "failure",
    [
        "entry_create",
        "line_one",
        "line_two",
        "entry_post",
        "binding",
        "audit_create",
        "audit_line_one",
        "audit_line_two",
        "audit_post",
        "integration_audit",
    ],
)
def test_every_composition_failure(business_context, outcomes, effect, failure):
    invoice, _, allocation = outcomes["sources"]()
    if effect == "allocation":
        invoice_post(business_context, outcomes, invoice)
    service = invoices if effect == "invoice" else allocations
    model = InvoicePosting if effect == "invoice" else AllocationPosting
    post, source = (invoice_post, invoice) if effect == "invoice" else (allocation_post, allocation)
    before = (
        JournalEntry.objects.count(),
        JournalEntryLine.objects.count(),
        AuditEntry.objects.count(),
    )
    if failure == "binding":
        target = patch.object(model, "_insert", side_effect=RuntimeError("injected"))
    elif failure == "integration_audit":
        target = patch.object(service, "record_audit_entry", side_effect=RuntimeError("injected"))
    elif failure.startswith("audit_"):
        original = owner.record_audit_entry
        wanted = {"audit_create": 1, "audit_line_one": 2, "audit_line_two": 3, "audit_post": 4}[
            failure
        ]
        count = 0

        def audit(*args, **kwargs):
            nonlocal count
            count += 1
            if count == wanted:
                raise RuntimeError("injected")
            return original(*args, **kwargs)

        target = patch.object(owner, "record_audit_entry", side_effect=audit)
    elif failure.startswith("line_"):
        original = owner.add_journal_entry_line
        count = 0

        def line(*args, **kwargs):
            nonlocal count
            count += 1
            if count == (1 if failure == "line_one" else 2):
                raise RuntimeError("injected")
            return original(*args, **kwargs)

        target = patch.object(owner, "add_journal_entry_line", side_effect=line)
    else:
        target = patch.object(
            owner,
            "create_journal_entry" if failure == "entry_create" else "post_journal_entry",
            side_effect=RuntimeError("injected"),
        )
    with target, pytest.raises(RuntimeError, match="injected"):
        post(business_context, outcomes, source)
    assert before == (
        JournalEntry.objects.count(),
        JournalEntryLine.objects.count(),
        AuditEntry.objects.count(),
    )
    assert model.objects.count() == 0


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
def test_real_source_unique_conflict_rolls_back_losing_composition(
    business_context, outcomes, effect
):
    invoice, _, allocation = outcomes["sources"]()
    invoice_result = invoice_post(business_context, outcomes, invoice)
    post, source, model = (
        (invoice_post, invoice, InvoicePosting)
        if effect == "invoice"
        else (allocation_post, allocation, AllocationPosting)
    )
    winner = invoice_result if effect == "invoice" else post(business_context, outcomes, source)
    before = (
        JournalEntry.objects.count(),
        JournalEntryLine.objects.count(),
        AuditEntry.objects.count(),
    )
    original_first = BindingQuerySet.first
    hidden = False

    def missing_initial_lookup(queryset):
        nonlocal hidden
        if queryset.model is model and not hidden:
            hidden = True
            return None
        return original_first(queryset)

    observed = []
    original_collision = invoices._collision if effect == "invoice" else allocations._collision

    def collision(error):
        observed.append(error)
        assert isinstance(error, IntegrityError) and error.__cause__ is not None
        return original_collision(error)

    with (
        patch.object(BindingQuerySet, "first", missing_initial_lookup),
        patch.object(invoices if effect == "invoice" else allocations, "_collision", collision),
    ):
        recovered = post(business_context, outcomes, source)
    assert hidden and len(observed) == 1 and recovered == winner
    assert before == (
        JournalEntry.objects.count(),
        JournalEntryLine.objects.count(),
        AuditEntry.objects.count(),
    )


def test_unrelated_integrity_error_not_swallowed(business_context, outcomes):
    invoice, _, _ = outcomes["sources"]("100", None)
    with patch.object(InvoicePosting, "_insert", side_effect=IntegrityError("unrelated")):
        with pytest.raises(IntegrityError, match="unrelated"):
            invoice_post(business_context, outcomes, invoice)
    assert not JournalEntry.objects.exists()


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
def test_bounded_real_binding_uuid_collision(business_context, outcomes, effect):
    old_invoice, _, old_allocation = outcomes["sources"]()
    old_invoice_result = invoice_post(business_context, outcomes, old_invoice)
    if effect == "allocation":
        old = allocation_post(business_context, outcomes, old_allocation)
    else:
        old = old_invoice_result
    invoice, _, allocation = outcomes["sources"]()
    if effect == "allocation":
        invoice_post(business_context, outcomes, invoice)
    service = invoices if effect == "invoice" else allocations
    post, source = (invoice_post, invoice) if effect == "invoice" else (allocation_post, allocation)
    before = (
        JournalEntry.objects.count(),
        JournalEntryLine.objects.count(),
        AuditEntry.objects.count(),
    )
    with patch.object(service, "uuid4", side_effect=[old.binding_id, old.binding_id, uuid4()]):
        result = post(business_context, outcomes, source)
    assert result.binding_id != old.binding_id
    assert JournalEntry.objects.count() == before[0] + 1
    assert JournalEntryLine.objects.count() == before[1] + 2
    assert AuditEntry.objects.count() == before[2] + 5
