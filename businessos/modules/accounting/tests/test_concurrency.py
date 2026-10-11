from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic, sleep

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction

from businessos.core.access import services as access_services
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.modules.accounting import services
from businessos.modules.accounting.models import Account, Journal, JournalEntry, JournalEntryLine

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Requires real PostgreSQL row locks and independent connections.")


def worker(operation, ready, pid):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET statement_timeout='20s'")
            cursor.execute("SELECT pg_backend_pid()")
            pid.append(cursor.fetchone()[0])
        ready.set()
        return operation()
    finally:
        connections.close_all()


def blocked(pid):
    deadline = monotonic() + 10
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            cursor.execute("SELECT pg_backend_pid()=ANY(pg_blocking_pids(%s))", [pid])
            if cursor.fetchone()[0]:
                return
            sleep(0.01)  # Poll actual lock state; elapsed time is never race evidence.
    pytest.fail("Worker did not wait on the held PostgreSQL lock.")


def race(first, second, *, error=None):
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            first_result = first()
            future = pool.submit(worker, second, ready, pid)
            assert ready.wait(10)
            blocked(pid[0])
        if error:
            with pytest.raises(error):
                future.result(15)
            return first_result, None
        return first_result, future.result(15)


def test_concurrent_post_one_effect(business_context, balanced):
    first, second = race(
        lambda: services.post_journal_entry(business_context, balanced.pk),
        lambda: services.post_journal_entry(business_context, balanced.pk),
    )
    assert first.pk == second.pk and first.posted_at == second.posted_at
    assert AuditEntry.objects.filter(action="accounting.entry.posted").count() == 1
    assert JournalEntryLine.objects.count() == 2


@pytest.mark.parametrize("operation", ["header", "line", "add", "remove"])
@pytest.mark.parametrize("post_first", [True, False])
def test_post_vs_draft_mutation(business_context, balanced, account, operation, post_first):
    line = balanced.lines.first()
    mutation = {
        "header": lambda: services.update_journal_entry(
            business_context, balanced.pk, memo="Committed edit"
        ),
        "line": lambda: services.update_journal_entry_line(
            business_context, balanced.pk, line.pk, description="Committed edit"
        ),
        "add": lambda: services.add_journal_entry_line(
            business_context, balanced.pk, account_id=account.pk, debit=1, credit=0
        ),
        "remove": lambda: services.remove_journal_entry_line(
            business_context, balanced.pk, line.pk
        ),
    }[operation]

    def post():
        return services.post_journal_entry(business_context, balanced.pk)

    first, second = (post, mutation) if post_first else (mutation, post)
    expected_error = post_first or operation in {"add", "remove"}
    race(first, second, error=ValidationError if expected_error else None)
    balanced.refresh_from_db()
    assert balanced.status == (
        "DRAFT" if not post_first and operation in {"add", "remove"} else "POSTED"
    )
    if not post_first and operation == "header":
        assert balanced.memo == "Committed edit"
    if not post_first and operation == "line":
        line.refresh_from_db()
        assert line.description == "Committed edit"


@pytest.mark.parametrize("entity", ["entry", "line"])
@pytest.mark.parametrize("api", ["save", "delete"])
def test_post_vs_stale_instance(business_context, balanced, entity, api):
    stale = balanced if entity == "entry" else balanced.lines.first()

    def stale_attempt():
        # Company lock coordinates the unsupported public call with the real transition.
        with transaction.atomic():
            Company.objects.select_for_update().get(pk=business_context.company_id)
            return getattr(stale, api)()

    race(
        lambda: services.post_journal_entry(business_context, balanced.pk),
        stale_attempt,
        error=ValidationError,
    )
    assert JournalEntry.objects.filter(pk=balanced.pk, status="POSTED").exists()
    assert balanced.lines.count() == 2


@pytest.mark.parametrize("reference", ["account", "journal", "party"])
@pytest.mark.parametrize("post_first", [True, False])
def test_post_vs_retirement(
    business_context, balanced, account, journal, party, reference, post_first
):
    def retire():
        if reference == "account":
            return services.update_account(business_context, account.pk, is_active=False)
        if reference == "journal":
            return services.update_journal(business_context, journal.pk, is_active=False)
        party.is_active = False
        party.save()
        return party

    def post():
        return services.post_journal_entry(business_context, balanced.pk)

    if reference == "party" and not post_first:
        # Party does not take the Company lock. Hold its row while testing reference re-read.
        first = retire
    else:
        first = post if post_first else retire
    race(first, retire if post_first else post, error=None if post_first else ValidationError)
    balanced.refresh_from_db()
    assert balanced.status == ("POSTED" if post_first else "DRAFT")


@pytest.mark.parametrize("revoke", ["role", "permission", "company_access"])
@pytest.mark.parametrize(
    "operation",
    [
        "account_create",
        "account_update",
        "journal_create",
        "journal_update",
        "entry_create",
        "entry_update",
        "line_add",
        "line_update",
        "line_remove",
        "post",
        "retry",
    ],
)
def test_authorization_after_company_wait(
    business_context,
    balanced,
    account,
    journal,
    accounting_role,
    company,
    operator,
    revoke,
    operation,
):
    root = get_user_model().objects.create_superuser("acc-root@example.test", "synthetic-only")
    admin = BusinessContext(actor_id=root.pk, company_id=company.pk)
    access_services.register_core_permissions()
    if operation == "retry":
        services.post_journal_entry(business_context, balanced.pk)
    permission = (
        "accounting.account.manage"
        if operation.startswith("account")
        else "accounting.journal.manage"
        if operation.startswith("journal")
        else "accounting.entry.create"
        if operation == "entry_create"
        else "accounting.entry.post"
        if operation in {"post", "retry"}
        else "accounting.entry.update"
    )
    line = balanced.lines.first()
    operations = {
        "account_create": lambda: services.create_account(
            business_context, code="NO", name="No", type="ASSET"
        ),
        "account_update": lambda: services.update_account(business_context, account.pk, name="No"),
        "journal_create": lambda: services.create_journal(business_context, code="NO", name="No"),
        "journal_update": lambda: services.update_journal(business_context, journal.pk, name="No"),
        "entry_create": lambda: services.create_journal_entry(
            business_context, journal_id=journal.pk
        ),
        "entry_update": lambda: services.update_journal_entry(
            business_context, balanced.pk, memo="No"
        ),
        "line_add": lambda: services.add_journal_entry_line(
            business_context, balanced.pk, account_id=account.pk, debit=1, credit=0
        ),
        "line_update": lambda: services.update_journal_entry_line(
            business_context, balanced.pk, line.pk, description="No"
        ),
        "line_remove": lambda: services.remove_journal_entry_line(
            business_context, balanced.pk, line.pk
        ),
        "post": lambda: services.post_journal_entry(business_context, balanced.pk),
        "retry": lambda: services.post_journal_entry(business_context, balanced.pk),
    }
    before = None

    def revocation():
        nonlocal before
        Company.objects.select_for_update().get(pk=company.pk)
        if revoke == "role":
            access_services.revoke_role(admin, user_id=operator.pk, role_id=accounting_role.pk)
        elif revoke == "permission":
            access_services.revoke_role_permission(
                admin, role_id=accounting_role.pk, permission_code=permission
            )
        else:
            access_services.revoke_company_access(admin, user_id=operator.pk)
        before = AuditEntry.objects.count()

    race(revocation, operations[operation], error=PermissionDenied)
    assert AuditEntry.objects.count() == before
    assert Account.objects.count() == Journal.objects.count() == JournalEntry.objects.count() == 1
    assert balanced.lines.count() == 2


def test_concurrent_position_allocation(business_context, entry, account):
    def add():
        return services.add_journal_entry_line(
            business_context, entry.pk, account_id=account.pk, debit=1, credit=0
        )

    first, second = race(add, add)
    assert (first.position, second.position) == (1, 2)


def test_remove_wins_waiting_line_edit_cannot_resurrect(business_context, balanced):
    line = balanced.lines.first()
    race(
        lambda: services.remove_journal_entry_line(business_context, balanced.pk, line.pk),
        lambda: services.update_journal_entry_line(
            business_context, balanced.pk, line.pk, description="Stale"
        ),
        error=ValidationError,
    )
    assert not JournalEntryLine.objects.filter(pk=line.pk).exists()
    assert (
        AuditEntry.objects.filter(
            action="accounting.entry.updated", metadata__operation="line_removed"
        ).count()
        == 1
    )


@pytest.mark.parametrize("kind", ["account", "journal"])
def test_concurrent_normalized_code(business_context, accounting_role, kind):
    create = services.create_account if kind == "account" else services.create_journal

    def add(code):
        return create(
            business_context,
            code=code,
            name="Collision",
            **({"type": "ASSET"} if kind == "account" else {}),
        )

    race(lambda: add(" code "), lambda: add("CODE"), error=ValidationError)
    model = Account if kind == "account" else Journal
    assert model.objects.count() == 1
