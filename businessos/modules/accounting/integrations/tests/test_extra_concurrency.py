import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, models, transaction

from businessos.core.access.models import Permission
from businessos.core.audit.models import AuditEntry
from businessos.core.organization.models import Company
from businessos.modules.accounting.integrations.admission import permissions
from businessos.modules.accounting.integrations.billing.selectors import invoice_posting_status
from businessos.modules.accounting.integrations.payments_billing.selectors import (
    allocation_posting_status,
)
from businessos.modules.accounting.manifest import VIEW_ENTRIES
from businessos.modules.accounting.models import JournalEntry
from businessos.modules.accounting.posted_basis import posted_journal_basis
from businessos.modules.billing import services as billing
from businessos.modules.billing.accounting_basis import invoice_accounting_basis
from businessos.modules.billing.manifest import VIEW_INVOICES
from businessos.modules.billing.models import Invoice, InvoiceLine
from businessos.modules.payments.integrations.billing.accounting_basis import (
    allocation_accounting_basis,
)
from businessos.modules.payments.integrations.billing.manifest import VIEW_ALLOCATIONS
from businessos.modules.payments.models import Payment

from .test_concurrency import race
from .test_outcomes import invoice_post

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Real independent PostgreSQL locks required.")


@pytest.mark.parametrize("basis", ["invoice", "allocation", "entry"])
def test_owner_read_contract_rechecks_after_source_wait(business_context, outcomes, basis):
    invoice, payment, allocation = outcomes["sources"]()
    result = invoice_post(business_context, outcomes, invoice)
    if basis == "invoice":
        reader, identity, model, row_id, grant = (
            invoice_accounting_basis,
            invoice.pk,
            Invoice,
            invoice.pk,
            VIEW_INVOICES,
        )
    elif basis == "allocation":
        reader, identity, model, row_id, grant = (
            allocation_accounting_basis,
            allocation.pk,
            Payment,
            payment.pk,
            VIEW_ALLOCATIONS,
        )
    else:
        reader, identity, model, row_id, grant = (
            posted_journal_basis,
            result.journal_entry_id,
            JournalEntry,
            result.journal_entry_id,
            VIEW_ENTRIES,
        )
    assert Permission.objects.filter(code=grant).exists()
    before = AuditEntry.objects.count()

    def revoke():
        model.objects.select_for_update().get(pk=row_id)
        Permission.objects.filter(code=grant).update(is_active=False)

    race(revoke, lambda: reader(business_context, identity), PermissionDenied)
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("waiting", ["source", "entry"])
@pytest.mark.parametrize(
    "effect,grant",
    [
        (effect, grant)
        for effect in ("invoice", "allocation")
        for grant in permissions(allocation=effect == "allocation")
    ],
)
def test_status_rechecks_complete_grants_after_wait(
    business_context, outcomes, effect, grant, waiting
):
    invoice, payment, allocation = outcomes["sources"]()
    prior = invoice_post(business_context, outcomes, invoice)
    reader, identity = (
        (invoice_posting_status, invoice.pk)
        if effect == "invoice"
        else (allocation_posting_status, allocation.pk)
    )
    model, row_id = (
        (JournalEntry, prior.journal_entry_id)
        if waiting == "entry"
        else ((Invoice, invoice.pk) if effect == "invoice" else (Payment, payment.pk))
    )
    before = AuditEntry.objects.count()

    def revoke():
        model.objects.select_for_update().get(pk=row_id)
        Permission.objects.filter(code=grant).update(is_active=False)

    race(revoke, lambda: reader(business_context, identity), PermissionDenied)
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("post_first", [False, True])
def test_issue_vs_post(business_context, outcomes, post_first):
    invoice, _, _ = outcomes["sources"]("1", None, issued=False)

    def issue():
        return billing.issue_invoice(business_context, invoice.pk)

    def ineligible():
        Company.objects.select_for_update().get(pk=business_context.company_id)
        with transaction.atomic(), pytest.raises(ValidationError):
            invoice_post(business_context, outcomes, invoice)

    if post_first:
        race(ineligible, issue)
        assert not JournalEntry.objects.exists()
    else:
        race(issue, lambda: invoice_post(business_context, outcomes, invoice))
        assert JournalEntry.objects.count() == 1


@pytest.mark.parametrize("post_first", [False, True])
@pytest.mark.parametrize("mutation", ["lifecycle", "description", "party"])
def test_source_integrity_winner(business_context, outcomes, post_first, mutation):
    invoice, _, _ = outcomes["sources"]("1", None)

    @transaction.atomic
    def corrupt():
        Invoice.objects.select_for_update().get(pk=invoice.pk)
        if mutation == "lifecycle":
            models.QuerySet.update(
                Invoice.objects.filter(pk=invoice.pk), status=Invoice.Status.DRAFT, issued_at=None
            )
        elif mutation == "description":
            models.QuerySet.update(InvoiceLine.objects.filter(invoice=invoice), description="")
        else:
            models.QuerySet.update(
                type(outcomes["party"]).objects.filter(pk=outcomes["party"].pk),
                party_type="unreviewed",
            )

    race(
        lambda: invoice_post(business_context, outcomes, invoice), corrupt
    ) if post_first else race(
        corrupt, lambda: invoice_post(business_context, outcomes, invoice), ValidationError
    )
    assert JournalEntry.objects.count() == int(post_first)
    assert invoice_posting_status(business_context, invoice.pk).state == "UNAVAILABLE"


def test_strong_ddl_waits_for_evidence_transaction(business_context, outcomes):
    invoice, _, _ = outcomes["sources"]("1", None)

    def ddl():
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE public.accounting_billing_invoiceposting "
                "ADD COLUMN synthetic_drift integer"
            )

    first, _ = race(lambda: invoice_posting_status(business_context, invoice.pk), ddl)
    assert first.state == "NOT_POSTED"
    try:
        assert invoice_posting_status(business_context, invoice.pk).state == "UNAVAILABLE"
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE public.accounting_billing_invoiceposting DROP COLUMN synthetic_drift"
            )
