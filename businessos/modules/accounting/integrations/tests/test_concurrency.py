from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from time import monotonic, sleep
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, models, transaction
from django.http import Http404

from businessos.core.access.models import (
    Permission,
    RolePermission,
    UserCompanyAccess,
    UserRoleAssignment,
)
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company
from businessos.core.reference.models import Currency
from businessos.modules.accounting.integrations.admission import admission, permissions
from businessos.modules.accounting.integrations.billing.models import InvoicePosting
from businessos.modules.accounting.integrations.billing.selectors import invoice_posting_status
from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
from businessos.modules.accounting.models import JournalEntry, JournalEntryLine
from businessos.modules.billing.models import Invoice
from businessos.modules.payments.models import Payment

from .test_outcomes import allocation_post, invoice_post

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Requires real PostgreSQL row blocking and independent worker connections.")


def worker(operation, ready, pid):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET statement_timeout='25s'")
            cursor.execute("SELECT pg_backend_pid()")
            pid.append(cursor.fetchone()[0])
        ready.set()
        return operation()
    finally:
        connections.close_all()


def blocked(pid, holder=None):
    deadline = monotonic() + 12
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            if holder is None:
                cursor.execute("SELECT pg_backend_pid()=ANY(pg_blocking_pids(%s))", [pid])
            else:
                cursor.execute("SELECT %s=ANY(pg_blocking_pids(%s))", [holder, pid])
            if cursor.fetchone()[0]:
                return
            sleep(0.01)  # Poll observed lock state, never infer a lock from elapsed time.
    pytest.fail("Worker did not demonstrably block on the held PostgreSQL lock.")


def race(first, second, error=None):
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            result = first()
            future = pool.submit(worker, second, ready, pid)
            assert ready.wait(12)
            blocked(pid[0])
        if error:
            with pytest.raises(error):
                future.result(25)
            return result, None
        return result, future.result(25)


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize("conflicting", [False, True])
@pytest.mark.parametrize("reverse", [False, True])
def test_same_source_races(business_context, outcomes, effect, conflicting, reverse):
    invoice, _, allocation = outcomes["sources"]()
    if effect == "allocation":
        invoice_post(business_context, outcomes, invoice)
    post, source = (invoice_post, invoice) if effect == "invoice" else (allocation_post, allocation)
    from businessos.modules.accounting import services as owner

    alternative = owner.create_journal(business_context, code="ALT", name="Alternate")
    choices = [outcomes["journal"].pk, alternative.pk if conflicting else outcomes["journal"].pk]
    if reverse:
        choices.reverse()
    first, second = race(
        lambda: post(business_context, outcomes, source, journal_id=choices[0]),
        lambda: post(business_context, outcomes, source, journal_id=choices[1]),
        ValidationError if conflicting else None,
    )
    if second:
        assert first == second
    assert InvoicePosting.objects.count() == 1
    assert AllocationPosting.objects.count() == int(effect == "allocation")
    assert JournalEntry.objects.count() == (2 if effect == "allocation" else 1)
    assert JournalEntryLine.objects.count() == (4 if effect == "allocation" else 2)
    assert AuditEntry.objects.filter(action__endswith="posting.created").count() == (
        2 if effect == "allocation" else 1
    )


@pytest.mark.parametrize("invoice_first", [False, True])
def test_cross_effect_lock_order(business_context, outcomes, invoice_first):
    invoice, _, allocation = outcomes["sources"]()
    if invoice_first:
        race(
            lambda: invoice_post(business_context, outcomes, invoice),
            lambda: allocation_post(business_context, outcomes, allocation),
        )
        assert JournalEntry.objects.count() == 2
    else:

        def missing():
            Company.objects.select_for_update().get(pk=business_context.company_id)
            with transaction.atomic(), pytest.raises(ValidationError):
                allocation_post(business_context, outcomes, allocation)

        race(missing, lambda: invoice_post(business_context, outcomes, invoice))
        assert JournalEntry.objects.count() == 1
        allocation_post(business_context, outcomes, allocation)
    assert InvoicePosting.objects.count() == AllocationPosting.objects.count() == 1
    assert JournalEntry.objects.count() == 2 and JournalEntryLine.objects.count() == 4
    assert AuditEntry.objects.filter(action__endswith="posting.created").count() == 2


def test_cross_effect_invoice_rollback_does_not_admit_allocation(business_context, outcomes):
    invoice, _, allocation = outcomes["sources"]()
    before = AuditEntry.objects.count()

    def rolled_back():
        Company.objects.select_for_update().get(pk=business_context.company_id)
        with transaction.atomic(), pytest.raises(RuntimeError, match="injected"):
            from businessos.modules.accounting.integrations.billing import services

            with patch.object(services, "record_audit_entry", side_effect=RuntimeError("injected")):
                invoice_post(business_context, outcomes, invoice)

    race(
        rolled_back,
        lambda: allocation_post(business_context, outcomes, allocation),
        ValidationError,
    )
    assert not InvoicePosting.objects.exists() and not AllocationPosting.objects.exists()
    assert not JournalEntry.objects.exists() and not JournalEntryLine.objects.exists()
    assert AuditEntry.objects.count() == before
    invoice_post(business_context, outcomes, invoice)
    allocation_post(business_context, outcomes, allocation)
    assert JournalEntry.objects.count() == 2 and JournalEntryLine.objects.count() == 4


@pytest.mark.parametrize("target", ["journal", "ar", "cash"])
@pytest.mark.parametrize("post_first", [False, True])
def test_allocation_reference_activity_races(business_context, outcomes, target, post_first):
    invoice, _, allocation = outcomes["sources"]()
    invoice_post(business_context, outcomes, invoice)
    row = outcomes[target]

    @transaction.atomic
    def retire():
        type(row).objects.select_for_update().get(pk=row.pk)
        models.QuerySet.update(type(row).objects.filter(pk=row.pk), is_active=False)

    if post_first:
        first, _ = race(lambda: allocation_post(business_context, outcomes, allocation), retire)
        assert allocation_post(business_context, outcomes, allocation) == first
    else:
        race(
            retire, lambda: allocation_post(business_context, outcomes, allocation), ValidationError
        )
    assert AllocationPosting.objects.count() == int(post_first)
    assert JournalEntry.objects.count() == 1 + int(post_first)


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize(
    "revocation", ["role", "role_permission", "permission", "company_access", "actor", "company"]
)
@pytest.mark.parametrize("retry", [False, True])
def test_company_wait_revocation(
    business_context, outcomes, outcome_role, operator, company, effect, revocation, retry
):
    invoice, _, allocation = outcomes["sources"]()
    if effect == "allocation":
        invoice_post(business_context, outcomes, invoice)
    post, source = (invoice_post, invoice) if effect == "invoice" else (allocation_post, allocation)
    if retry:
        post(business_context, outcomes, source)
    initial_entries = JournalEntry.objects.count()
    grant = permissions(allocation=effect == "allocation", create=True)[0]

    def revoke():
        Company.objects.select_for_update().get(pk=company.pk)
        if revocation == "role":
            UserRoleAssignment.objects.filter(user=operator, role=outcome_role).delete()
        elif revocation == "role_permission":
            RolePermission.objects.filter(role=outcome_role, permission__code=grant).delete()
        elif revocation == "permission":
            Permission.objects.filter(code=grant).update(is_active=False)
        elif revocation == "company_access":
            UserCompanyAccess.objects.filter(user=operator, company=company).delete()
        elif revocation == "actor":
            get_user_model().objects.filter(pk=operator.pk).update(is_active=False)
        else:
            Company.objects.filter(pk=company.pk).update(is_active=False)
        return AuditEntry.objects.count()

    before, _ = race(revoke, lambda: post(business_context, outcomes, source), PermissionDenied)
    assert JournalEntry.objects.count() == initial_entries and AuditEntry.objects.count() == before


GRANTS = [
    (effect, grant)
    for effect in ("invoice", "allocation")
    for grant in permissions(allocation=effect == "allocation", create=True)
]


@pytest.mark.parametrize("effect,grant", GRANTS)
@pytest.mark.parametrize(
    "waiting", ["source", "entry", "journal", "ar", "other", "party", "currency"]
)
def test_full_authorization_after_source_wait(
    business_context, outcomes, currency, effect, grant, waiting
):
    invoice, payment, allocation = outcomes["sources"]()
    prior = None
    if effect == "allocation" or waiting == "entry":
        prior = invoice_post(business_context, outcomes, invoice)
    post, source, model, identity = (
        (invoice_post, invoice, Invoice, invoice.pk)
        if effect == "invoice"
        else (allocation_post, allocation, Payment, payment.pk)
    )
    if waiting == "entry":
        model, identity = JournalEntry, prior.journal_entry_id
    elif waiting != "source":
        key = ("revenue" if effect == "invoice" else "cash") if waiting == "other" else waiting
        row = currency if key == "currency" else outcomes[key]
        model, identity = type(row), row.pk
    before_entries, before_audits = JournalEntry.objects.count(), AuditEntry.objects.count()

    def revoke():
        model.objects.select_for_update().get(pk=identity)
        Permission.objects.filter(code=grant).update(is_active=False)

    race(revoke, lambda: post(business_context, outcomes, source), PermissionDenied)
    assert JournalEntry.objects.count() == before_entries
    assert AuditEntry.objects.count() == before_audits


@pytest.mark.parametrize("target", ["journal", "ar", "revenue", "party", "currency"])
@pytest.mark.parametrize("post_first", [False, True])
def test_reference_wait_and_current_precision(
    business_context, outcomes, currency, target, post_first
):
    invoice, _, _ = outcomes["sources"]("0.01", None)
    row = currency if target == "currency" else outcomes[target]

    @transaction.atomic
    def retire():
        type(row).objects.select_for_update().get(pk=row.pk)
        if target == "currency":
            Currency.objects.filter(pk=row.pk).update(decimal_places=0)
        else:
            models.QuerySet.update(type(row).objects.filter(pk=row.pk), is_active=False)

    if post_first:
        first, _ = race(lambda: invoice_post(business_context, outcomes, invoice), retire)
        assert first.amount == Decimal("0.01")
        assert invoice_post(business_context, outcomes, invoice) == first
    else:
        race(retire, lambda: invoice_post(business_context, outcomes, invoice), ValidationError)
        assert not JournalEntry.objects.exists()


@pytest.mark.parametrize("disabled_first", [False, True])
@pytest.mark.parametrize(
    "code",
    [
        "accounting",
        "accounting_billing",
        "accounting_payments_billing",
        "billing",
        "payments",
        "payments_billing",
    ],
)
def test_http_registry_lock_races(business_context, outcomes, disabled_first, code):
    invoice, _, allocation = outcomes["sources"]()
    invoice_post(business_context, outcomes, invoice)
    BusinessModule.objects.update(is_enabled=True)

    def disable():
        BusinessModule.objects.filter(code=code).update(is_enabled=False)

    def post():
        with admission(business_context, allocation=True, create=True, http=True):
            return allocation_post(business_context, outcomes, allocation)

    race(
        disable if disabled_first else post,
        post if disabled_first else disable,
        Http404 if disabled_first else None,
    )
    assert AllocationPosting.objects.count() == int(not disabled_first)


@pytest.mark.parametrize("post_first", [False, True])
def test_status_and_posting_share_company_boundary(business_context, outcomes, post_first):
    invoice, _, _ = outcomes["sources"]("100", None)

    def post():
        return invoice_post(business_context, outcomes, invoice)

    def read():
        return invoice_posting_status(business_context, invoice.pk)

    first, second = race(post if post_first else read, read if post_first else post)
    assert (second if post_first else first).state == ("POSTED" if post_first else "NOT_POSTED")
