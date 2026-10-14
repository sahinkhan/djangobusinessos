"""PH2-AUTH2-AUD-1: relation intent precedes Django's upsert row lock."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier, Event
from uuid import uuid4

import pytest
from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connections

from businessos.core.access.models import Permission, UserCompanyAccess
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import (
    business_atomic_context,
    current_database_alias,
    database_execution,
)
from businessos.core.organization.models import Company
from businessos.core.reference.models import Country, Currency, Language
from businessos.modules.accounting import services as accounting
from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
from businessos.modules.accounting.integrations.tests.conftest import outcome_role, outcomes
from businessos.modules.accounting.integrations.tests.test_outcomes import (
    allocation_post,
    invoice_post,
)
from businessos.modules.accounting.models import JournalEntry, JournalEntryLine
from tests.test_authority_batches import financial_state
from tests.test_final_authorization import backend_pid, blocked, pg_only, worker

pytestmark = pytest.mark.django_db(transaction=True)


def assert_relation_wait(waiter, holder, mode):
    blocked(waiter, holder)
    with connections[current_database_alias()].cursor() as cursor:
        cursor.execute(
            "SELECT mode, granted FROM pg_locks WHERE pid=%s "
            "AND relation='access_permission'::regclass AND locktype='relation'",
            [waiter],
        )
        assert (mode, False) in cursor.fetchall()
        cursor.execute("SELECT pg_blocking_pids(%s)", [holder])
        assert cursor.fetchone()[0] == [], "The winner must have no wait edge back to the loser."


def checked_worker(alias, operation, ready, pids, detector):
    def run():
        connection = connections[alias]
        with connection.cursor() as cursor:
            cursor.execute("SET deadlock_timeout=%s", [detector])
        if alias == "default":
            return operation()

        def forbidden(*args, **kwargs):
            pytest.fail("Selected-alias worker used a default cursor.")

        with connections["default"].execute_wrapper(forbidden):
            return operation()

    return worker(alias, run, ready, pids)


def exercise_race(world, context, monkeypatch, effect, business_first, retire, superuser, detector):
    alias = current_database_alias()
    get_user_model().objects.filter(pk=context.actor_id).update(is_superuser=superuser)
    invoice, _, allocation = world["sources"](total="41.37", allocated="17.25")
    if effect == "allocation":
        invoice_post(context, world, invoice)
    source = invoice if effect == "invoice" else allocation
    public = invoice_post if effect == "invoice" else allocation_post

    def operation():
        return public(context, world, source)

    before = financial_state()
    permission = Permission.objects.get(code=accounting.POST_ENTRIES)
    held, release, ready_business, ready_writer = Event(), Event(), Event(), Event()
    business_pid, writer_pid, writer_row_sql = [], [], []
    real = accounting.require_final_permission

    def hold_guard(ctx, code):
        result = real(ctx, code)
        if business_first and not held.is_set():
            held.set()
            assert release.wait(15)
        return result

    def activity():
        if not business_first:
            held.set()  # Django resolved defaults after its existing-row FOR UPDATE.
            assert release.wait(15)
        return not retire

    def writer():
        def observe(execute, sql, params, many, sql_context):
            if "FOR UPDATE" in sql and "access_permission" in sql:
                writer_row_sql.append(sql)
            return execute(sql, params, many, sql_context)

        with connections[alias].execute_wrapper(observe):
            return Permission.objects.update_or_create(
                code=permission.code, defaults={"is_active": activity, "name": "Updated"}
            )

    monkeypatch.setattr(accounting, "require_final_permission", hold_guard)
    # Swap which backend would detect an old cycle first. Prove an acyclic wait
    # graph in both configurations, rather than accepting nondeterministic victims.
    timeouts = ("100ms", "5s") if detector == "business" else ("5s", "100ms")
    with ThreadPoolExecutor(max_workers=2) as pool:
        try:
            if business_first:
                business = pool.submit(
                    checked_worker, alias, operation, ready_business, business_pid, timeouts[0]
                )
                assert held.wait(15)
                change = pool.submit(
                    checked_worker, alias, writer, ready_writer, writer_pid, timeouts[1]
                )
                assert ready_writer.wait(10)
                if superuser:
                    assert_relation_wait(writer_pid[0], business_pid[0], "RowExclusiveLock")
                    assert writer_row_sql == []  # Has not reached Django's row-lock query.
                else:
                    blocked(writer_pid[0], business_pid[0])
            else:
                change = pool.submit(
                    checked_worker, alias, writer, ready_writer, writer_pid, timeouts[1]
                )
                assert held.wait(15)
                business = pool.submit(
                    checked_worker, alias, operation, ready_business, business_pid, timeouts[0]
                )
                assert ready_business.wait(10)
                if superuser:
                    assert_relation_wait(business_pid[0], writer_pid[0], "ShareLock")
                else:
                    blocked(business_pid[0], writer_pid[0])
        finally:
            release.set()
        row, created = change.result(25)
        assert not created and row.pk == permission.pk and row.is_active == (not retire)
        if not business_first and retire:
            with pytest.raises(PermissionDenied):
                business.result(25)
            assert financial_state() == before
            return
        result = business.result(25)
    entry = JournalEntry.objects.get(pk=result.journal_entry_id)
    amount = Decimal("41.37") if effect == "invoice" else Decimal("17.25")
    accounts = (
        (world["ar"].pk, world["revenue"].pk)
        if effect == "invoice"
        else (world["cash"].pk, world["ar"].pk)
    )
    lines = list(JournalEntryLine.objects.filter(journal_entry=entry).order_by("position"))
    assert [(line.account_id, line.debit, line.credit) for line in lines] == [
        (accounts[0], amount, 0),
        (accounts[1], 0, amount),
    ]
    assert (
        AuditEntry.objects.filter(action="accounting.entry.posted", object_id=str(entry.pk)).count()
        == 1
    )
    action = (
        "accounting.invoice_posting.created"
        if effect == "invoice"
        else "accounting.allocation_posting.created"
    )
    assert AuditEntry.objects.filter(action=action, object_id=str(result.binding_id)).count() == 1
    if effect == "allocation":
        binding = AllocationPosting.objects.get(pk=result.binding_id)
        assert binding.invoice_posting.ar_account_id == world["ar"].pk
        assert entry.entry_date == source.payment.payment_date
    state = financial_state()
    if retire:
        with pytest.raises(PermissionDenied):
            operation()
    else:
        assert operation() == result
    assert financial_state() == state


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize("business_first", [True, False])
@pytest.mark.parametrize("retire", [True, False])
@pytest.mark.parametrize("superuser", [True, False])
@pytest.mark.parametrize("detector", ["business", "writer"])
def test_upsert_vs_nested_posting(
    outcomes, business_context, monkeypatch, effect, business_first, retire, superuser, detector
):
    pg_only()
    exercise_race(
        outcomes, business_context, monkeypatch, effect, business_first, retire, superuser, detector
    )


def test_upsert_defaults_create_defaults_identity_and_transactions(monkeypatch):
    assert Permission.objects.update_or_create.alters_data
    assert Permission.objects.aupdate_or_create.alters_data
    connection = connections[current_database_alias()]
    assert not connection.in_atomic_block
    calls = []
    code = "synthetic.upsert.use"
    row, created = Permission.objects.update_or_create(
        code=code,
        defaults={"name": lambda: calls.append("update") or "Updated"},
        create_defaults={"name": lambda: calls.append("create") or "Created", "is_active": False},
    )
    assert created and row.name == "Created" and calls == ["create"]
    identity = row.pk
    with business_atomic_context():
        row, created = Permission.objects.update_or_create(
            code=code,
            defaults={"is_active": True, "name": lambda: calls.append("update") or "Updated"},
            create_defaults={"name": "Ignored"},
        )
    assert not created and row.pk == identity and row.is_active and row.name == "Updated"
    assert calls == ["create", "update"]
    with pytest.raises(ValidationError, match="immutable"):
        Permission.objects.update_or_create(pk=identity, defaults={"code": "synthetic.changed.use"})
    row.refresh_from_db()
    assert row.code == code and Permission.objects.filter(code=code).count() == 1
    # Model validation owns duplicate PK rejection before insertion.
    with pytest.raises(ValidationError, match="already exists"):
        Permission.objects.update_or_create(
            code="synthetic.collision.use", create_defaults={"id": identity, "name": "Collision"}
        )

    def rejected_insert(*args, **kwargs):
        raise IntegrityError("synthetic constraint failure")

    with monkeypatch.context() as patch:
        patch.setattr(Permission, "save", rejected_insert)
        with pytest.raises(IntegrityError, match="synthetic constraint failure"):
            Permission.objects.update_or_create(
                code="synthetic.failed.use", defaults={"name": "New"}
            )
    assert not Permission.objects.filter(code="synthetic.failed.use").exists()
    assert not connection.in_atomic_block and not connection.needs_rollback


def test_async_upsert_routes_through_sync_override(monkeypatch):
    seen = []
    queryset = type(Permission.objects.all())
    real = queryset.update_or_create

    def observed(self, *args, **kwargs):
        seen.append(self.db)
        return real(self, *args, **kwargs)

    monkeypatch.setattr(queryset, "update_or_create", observed)

    async def run():
        try:
            first, created = await Permission.objects.aupdate_or_create(
                code="synthetic.async.use", defaults={"name": "Created"}
            )
            assert created
            second, created = await Permission.objects.aupdate_or_create(
                code=first.code, defaults={"is_active": False}
            )
            assert not created and second.pk == first.pk and not second.is_active
        finally:
            await sync_to_async(connections.close_all)()

    async_to_sync(run)()
    assert seen == [current_database_alias()] * 2


def test_create_upserts_same_code_concurrently():
    pg_only()
    rendezvous = Barrier(2)
    alias = current_database_alias()

    def insert():
        def before_insert(execute, sql, params, many, sql_context):
            if sql.startswith('INSERT INTO "access_permission"'):
                rendezvous.wait(10)  # Both model validations completed before insert.
            return execute(sql, params, many, sql_context)

        with connections[alias].execute_wrapper(before_insert):
            return Permission.objects.update_or_create(
                code="synthetic.concurrent.use", defaults={"name": "Same accepted value"}
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker, alias, insert, Event(), []) for _ in range(2)]
        results = [future.result(25) for future in futures]
    assert sorted(created for _, created in results) == [False, True]
    assert results[0][0].pk == results[1][0].pk
    assert Permission.objects.filter(code="synthetic.concurrent.use").count() == 1


@pytest.mark.parametrize("method", ["create", "save", "get_or_create", "update_or_create"])
def test_namespace_blocks_writer_before_any_permission_row(outcomes, business_context, method):
    pg_only()
    get_user_model().objects.filter(pk=business_context.actor_id).update(is_superuser=True)
    invoice, _, _ = outcomes["sources"](total="41.37", allocated=None)
    row = Permission.objects.get(code=accounting.POST_ENTRIES)
    seen = []

    def write():
        def observe(execute, sql, params, many, sql_context):
            if "FOR UPDATE" in sql:
                seen.append(sql)
            return execute(sql, params, many, sql_context)

        with connections[current_database_alias()].execute_wrapper(observe):
            if method == "save":
                row.name = "Saved label"
                row.save()
            elif method == "create":
                Permission.objects.create(code="synthetic.namespace.use", name="New")
            else:
                getattr(Permission.objects, method)(
                    code="synthetic.namespace.use", defaults={"name": "New"}
                )

    ready, pids = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            invoice_post(business_context, outcomes, invoice)
            future = pool.submit(worker, current_database_alias(), write, ready, pids)
            assert ready.wait(10)
            assert_relation_wait(pids[0], backend_pid(), "RowExclusiveLock")
            assert seen == []
        future.result(25)


@pytest.mark.parametrize("outer_intent", [True, False])
def test_upsert_savepoint_rollback_and_superuser_posting(outcomes, business_context, outer_intent):
    pg_only()
    get_user_model().objects.filter(pk=business_context.actor_id).update(is_superuser=True)
    invoice, _, _ = outcomes["sources"](total="41.37", allocated=None)
    code = accounting.POST_ENTRIES
    ready, pids = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            if outer_intent:
                Permission.objects.update_or_create(code=code, defaults={"name": "Outer label"})
            with pytest.raises(RuntimeError, match="inner rollback"):
                with business_atomic_context():
                    Permission.objects.update_or_create(code=code, defaults={"is_active": False})
                    raise RuntimeError("inner rollback")
            assert Permission.objects.get(code=code).is_active
            future = pool.submit(
                worker,
                current_database_alias(),
                lambda: invoice_post(business_context, outcomes, invoice),
                ready,
                pids,
            )
            assert ready.wait(10)
            if outer_intent:
                assert_relation_wait(pids[0], backend_pid(), "ShareLock")
            else:
                assert future.result(25).state == "POSTED"
        assert future.result(25).state == "POSTED"


@pytest.mark.parametrize("business_first", [True, False])
@pytest.mark.parametrize("effect", ["invoice", "allocation"])
def test_fresh_alias_upsert_and_composition_default_cursor_trap(
    outcomes, business_context, monkeypatch, django_db_blocker, business_first, effect
):
    pg_only()
    source_alias = current_database_alias()
    alias = "authority_upsert_selected"
    name = "ph2_auth3_alias_" + uuid4().hex
    config = dict(connections.databases[source_alias])
    config.update(NAME=name, CONN_MAX_AGE=0)
    with connections[source_alias].cursor() as cursor:
        cursor.execute(f"CREATE DATABASE {connections[source_alias].ops.quote_name(name)}")
    connections.databases[alias] = config
    default_permission = Permission.objects.get(code=accounting.POST_ENTRIES)
    try:
        with django_db_blocker.unblock(), database_execution(alias):
            call_command("migrate", database=alias, verbosity=0)

            def forbidden(*args, **kwargs):
                pytest.fail("Selected-alias upsert used the default cursor.")

            with monkeypatch.context() as patch:
                patch.setattr(connections[source_alias], "cursor", forbidden)
                currency = Currency.objects.create(code="USD", name="USD")
                company = Company.objects.create(
                    id=business_context.company_id,
                    code="ALIAS",
                    name="Synthetic",
                    base_currency=currency,
                    country=Country.objects.create(code="US", name="US"),
                    default_language=Language.objects.create(code="EN", name="English"),
                )
                actor = get_user_model().objects.create_superuser(
                    "alias@example.com", "synthetic-only", id=business_context.actor_id
                )
                context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
                UserCompanyAccess.objects.create(user=actor, company=company)
                Permission.objects.filter(code=default_permission.code).delete()
                copied, created = Permission.objects.using(alias).update_or_create(
                    code=default_permission.code,
                    create_defaults={"id": default_permission.pk, "name": "Selected"},
                )
                assert created and copied.pk == default_permission.pk
                role = outcome_role.__wrapped__(company, actor)
                world = outcomes_fixture(company, currency, role, context)
                exercise_race(world, context, patch, effect, business_first, True, True, "writer")
        default_permission.refresh_from_db()
        assert default_permission.is_active
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
        with connections[source_alias].cursor() as cursor:
            cursor.execute(f"DROP DATABASE {connections[source_alias].ops.quote_name(name)}")


def outcomes_fixture(company, currency, role, context):
    return outcomes.__wrapped__(context, company, currency, role)
