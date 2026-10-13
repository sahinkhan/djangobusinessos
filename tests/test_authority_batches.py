"""PH2-AUTH-CORR-1: complete authority sets versus ordered batch writers."""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from uuid import UUID, uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import connections
from django.db.models.deletion import ProtectedError

from businessos.core.access import models as access_models
from businessos.core.access import policies
from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserCompanyAccess,
    UserRoleAssignment,
)
from businessos.core.access.services import register_core_permissions
from businessos.core.audit.models import AuditEntry
from businessos.core.database import (
    business_atomic_context,
    current_database_alias,
    database_execution,
)
from businessos.core.organization.models import Company
from businessos.core.reference.models import Country, Currency, Language
from businessos.modules.accounting import services as accounting
from businessos.modules.accounting.integrations.billing.models import InvoicePosting
from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
from businessos.modules.accounting.integrations.tests.conftest import (
    outcome_role as outcome_role,
)
from businessos.modules.accounting.integrations.tests.conftest import outcomes as outcomes
from businessos.modules.accounting.integrations.tests.test_outcomes import (
    allocation_post,
    invoice_post,
)
from businessos.modules.accounting.models import JournalEntry, JournalEntryLine
from tests.test_final_authorization import backend_pid, blocked, pg_only, worker

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def batch_world(outcomes, outcome_role, operator, business_context):
    # Deliberately reverse code-index order versus UUID order. Old per-action
    # locking could retain UPDATE (100) then request POST (200), while UPDATE's
    # code index visits POST (200) before UPDATE (100).
    ids = []
    for identity, code in ((100, accounting.UPDATE_ENTRIES), (200, accounting.POST_ENTRIES)):
        old = Permission.objects.get(code=code)
        RolePermission.objects.filter(permission=old).delete()
        old.delete()
        permission = Permission.objects.create(id=UUID(int=identity), code=code, name=code)
        ids.append(permission.pk)
    roles = []
    for identity, code, permission in ((100, "ZZ", ids[0]), (200, "AA", ids[1])):
        role = Role.objects.create(
            id=UUID(int=identity), company=outcome_role.company, code=code, name=code
        )
        RolePermission.objects.create(role=role, permission_id=permission)
        UserRoleAssignment.objects.create(user=operator, company=role.company, role=role)
        roles.append(role.pk)
    return outcomes, business_context, ids, roles


def plan(connection, mode):
    with connection.cursor() as cursor:
        if mode == "heap":
            cursor.execute("SET LOCAL enable_indexscan=off; SET LOCAL enable_bitmapscan=off")
            cursor.execute("SET LOCAL enable_seqscan=on")
        else:
            cursor.execute("SET LOCAL enable_seqscan=off; SET LOCAL enable_bitmapscan=off")
            cursor.execute("SET LOCAL enable_indexscan=on")


def mutation(kind, method, identities, company_id, mode, plans):
    model = Permission if kind == "permission" else Role
    alias = current_database_alias()
    with business_atomic_context():
        connection = connections[alias]
        plan(connection, mode)
        codes = (
            [accounting.UPDATE_ENTRIES, accounting.POST_ENTRIES]
            if kind == "permission"
            else ["ZZ", "AA"]
        )
        query = model.objects.filter(code__in=codes).order_by("-pk")
        if kind == "role":
            query = query.filter(company_id=company_id)
        assert set(query.values_list("pk", flat=True)) == set(identities)

        def observe_actual_update(execute, sql, params, many, sql_context):
            if sql.lstrip().startswith("UPDATE"):
                with connection.cursor() as cursor:
                    cursor.execute("EXPLAIN " + sql, params)
                    plans.extend(row[0] for row in cursor.fetchall())
            return execute(sql, params, many, sql_context)

        with connection.execute_wrapper(observe_actual_update):
            if method == "update":
                return query.update(is_active=False)
            if method == "bulk_update":
                rows = list(query)
                for row in rows:
                    row.is_active = False
                # Complete target prelocking MUST precede even a one-row batch.
                return query.bulk_update(rows, ["is_active"], batch_size=1)
            return query.delete()


def posting(batch_world, effect):
    outcomes, context, _, _ = batch_world
    invoice, _, allocation = outcomes["sources"]()
    if effect == "allocation":
        invoice_post(context, outcomes, invoice)
    source = invoice if effect == "invoice" else allocation
    public = invoice_post if effect == "invoice" else allocation_post
    return lambda: public(context, outcomes, source), source


def financial_state():
    return tuple(
        list(model.objects.order_by("pk").values())
        for model in (JournalEntry, JournalEntryLine, InvoicePosting, AllocationPosting, AuditEntry)
    )


def assert_effect(result, outcomes, context, source, effect):
    entry = JournalEntry.objects.get(pk=result.journal_entry_id)
    assert entry.status == JournalEntry.Status.POSTED
    lines = list(entry.lines.order_by("position"))
    amount = Decimal("100") if effect == "invoice" else Decimal("40")
    expected_accounts = (
        (outcomes["ar"].pk, outcomes["revenue"].pk)
        if effect == "invoice"
        else (outcomes["cash"].pk, outcomes["ar"].pk)
    )
    assert tuple(line.account_id for line in lines) == expected_accounts
    assert [(line.debit, line.credit) for line in lines] == [(amount, 0), (0, amount)]
    if effect == "allocation":
        binding = AllocationPosting.objects.get(pk=result.binding_id)
        assert binding.invoice_posting.ar_account_id == outcomes["ar"].pk
        assert entry.entry_date == source.payment.payment_date
    before = financial_state()
    with pytest.raises(PermissionDenied):
        (invoice_post if effect == "invoice" else allocation_post)(context, outcomes, source)
    assert financial_state() == before


@pytest.mark.parametrize("kind", ["permission", "role"])
@pytest.mark.parametrize("method", ["update", "bulk_update"])
@pytest.mark.parametrize("mode", ["heap", "index"])
@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize("business_first", [True, False])
def test_batch_activity_vs_public_nested_posting(
    batch_world, monkeypatch, kind, method, mode, effect, business_first
):
    pg_only()
    outcomes, context, permissions, roles = batch_world
    identities = permissions if kind == "permission" else roles
    operation, source = posting(batch_world, effect)
    before = financial_state()
    plans = []

    def writer():
        return mutation(kind, method, identities, context.company_id, mode, plans)

    ready, pid = Event(), []
    if business_first:
        acquired, proceed = Event(), Event()
        real = accounting.require_final_permission

        def hold_first_complete_set(ctx, code):
            result = real(ctx, code)
            if not acquired.is_set():
                acquired.set()
                assert proceed.wait(15)
            return result

        monkeypatch.setattr(accounting, "require_final_permission", hold_first_complete_set)
        business_ready, business_pid = Event(), []
        with ThreadPoolExecutor(max_workers=2) as pool:
            business = pool.submit(
                worker, current_database_alias(), operation, business_ready, business_pid
            )
            assert acquired.wait(15)
            retirement = pool.submit(worker, current_database_alias(), writer, ready, pid)
            try:
                assert ready.wait(10)
                blocked(pid[0], business_pid[0])
            finally:
                proceed.set()
            result = business.result(25)
            assert retirement.result(25) == 2
        assert_effect(result, outcomes, context, source, effect)
    else:
        with ThreadPoolExecutor(max_workers=1) as pool:
            with business_atomic_context():
                assert writer() == 2
                holder = backend_pid()
                future = pool.submit(worker, current_database_alias(), operation, ready, pid)
                assert ready.wait(10)
                blocked(pid[0], holder)
            with pytest.raises(PermissionDenied):
                future.result(25)
        assert financial_state() == before
    assert (
        any("Index Scan" in item for item in plans)
        if mode == "index"
        else any("Seq Scan" in item for item in plans)
    )


@pytest.mark.parametrize("mode", ["heap", "index"])
@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize("business_first", [True, False])
def test_role_batch_delete_vs_posting(batch_world, mode, effect, business_first):
    pg_only()
    outcomes, context, _, roles = batch_world
    operation, source = posting(batch_world, effect)
    before = financial_state()

    def writer():
        return mutation("role", "delete", roles, context.company_id, mode, [])

    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            if business_first:
                result = operation()
                future = pool.submit(worker, current_database_alias(), writer, ready, pid)
            else:
                deleted, _ = writer()
                assert deleted >= 2
                future = pool.submit(worker, current_database_alias(), operation, ready, pid)
            assert ready.wait(10)
            blocked(pid[0], backend_pid())
        if business_first:
            assert future.result(25)[0] >= 2
        else:
            with pytest.raises(PermissionDenied):
                future.result(25)
    if business_first:
        assert_effect(result, outcomes, context, source, effect)
    else:
        assert financial_state() == before


@pytest.mark.parametrize("kind", ["permission", "role"])
@pytest.mark.parametrize("method", ["update", "bulk_update", "delete"])
def test_writer_target_lock_order_is_uuid_not_queryset_order(batch_world, kind, method):
    pg_only()
    _, context, permissions, roles = batch_world
    identities = permissions if kind == "permission" else roles
    observed = []

    def trace(execute, sql, params, many, sql_context):
        if "FOR UPDATE" in sql and "access_" + kind in sql:
            observed.append(params[0])
        return execute(sql, params, many, sql_context)

    connection = connections[current_database_alias()]
    with connection.execute_wrapper(trace):
        if kind == "permission" and method == "delete":
            with pytest.raises(ProtectedError):
                mutation(kind, method, identities, context.company_id, "heap", [])
        else:
            mutation(kind, method, identities, context.company_id, "heap", [])
    assert observed[:2] == sorted(identities)
    if method == "bulk_update":
        # Nested Django batch updates only re-lock anchors already held.
        assert set(observed[2:]) <= set(observed[:2])


@pytest.mark.parametrize("kind", ["permission", "role"])
def test_instance_deletion_uses_writer_protocol(batch_world, monkeypatch, kind):
    _, context, _, _ = batch_world
    model = Permission if kind == "permission" else Role
    kwargs = {"code": "unused.authority.delete", "name": "Unreferenced"}
    if kind == "role":
        kwargs.update(code="UNUSED", company_id=context.company_id)
    row = model.objects.create(**kwargs)
    identity = row.pk
    seen = []
    real = access_models._lock_authority_targets

    def observe(query):
        assert connections[query.db].in_atomic_block
        seen.extend(query.values_list("pk", flat=True))
        return real(query)

    monkeypatch.setattr(access_models, "_lock_authority_targets", observe)
    assert row.delete()[0] == 1
    assert seen == [identity] and row.pk is None


def guard(context, code=accounting.CREATE_ENTRIES):
    Company.objects.select_for_update().get(pk=context.company_id)
    return policies.require_final_permission(context, code)


@pytest.mark.parametrize("inner_acquisition_rolled_back", [False, True])
def test_savepoint_rollback_reacquires_or_retains_authority(
    batch_world, inner_acquisition_rolled_back
):
    pg_only()
    _, context, permissions, _ = batch_world
    target = permissions[0]
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            if not inner_acquisition_rolled_back:
                guard(context)
            with pytest.raises(RuntimeError, match="rollback inner"):
                with business_atomic_context():
                    guard(context)
                    raise RuntimeError("rollback inner")
            future = pool.submit(
                worker,
                current_database_alias(),
                lambda: Permission.objects.filter(pk=target).update(is_active=False),
                ready,
                pid,
            )
            assert ready.wait(10)
            if inner_acquisition_rolled_back:
                assert future.result(10) == 1
                with pytest.raises(PermissionDenied):
                    guard(context, accounting.UPDATE_ENTRIES)
            else:
                blocked(pid[0], backend_pid())
                guard(context, accounting.UPDATE_ENTRIES)
        assert future.result(15) == 1


def test_all_inactive_authorities_are_included_in_sorted_reader_set(batch_world, monkeypatch):
    _, context, permissions, roles = batch_world
    Role.objects.filter(pk=roles[0]).update(is_active=False)
    Permission.objects.filter(pk=permissions[1]).update(is_active=False)
    seen = []
    real = policies._share_authority_rows

    def observe(connection, model, identities):
        identities = sorted(set(identities))
        seen.extend((model, identity) for identity in identities)
        return real(connection, model, identities)

    monkeypatch.setattr(policies, "_share_authority_rows", observe)
    with business_atomic_context():
        guard(context)
        guard(context)
    role_ids = [identity for model, identity in seen if model is Role]
    permission_ids = [identity for model, identity in seen if model is Permission]
    assert roles[0] in role_ids and permissions[1] in permission_ids
    assert role_ids[: len(role_ids) // 2] == sorted(set(role_ids))
    assert permission_ids[: len(permission_ids) // 2] == sorted(set(permission_ids))


@pytest.mark.parametrize("method", ["update", "delete", "register"])
def test_superuser_freezes_declared_namespace_before_writer_rows(batch_world, method):
    pg_only()
    _, context, permissions, _ = batch_world
    get_user_model().objects.filter(pk=context.actor_id).update(is_superuser=True)
    if method == "delete":
        RolePermission.objects.filter(permission_id__in=permissions).delete()
    ready, pid = Event(), []

    def writer():
        if method == "register":
            return Permission.objects.create(code="new.authority.use", name="New")
        query = Permission.objects.filter(pk__in=permissions)
        return query.delete() if method == "delete" else query.update(is_active=False)

    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            guard(context)
            future = pool.submit(worker, current_database_alias(), writer, ready, pid)
            assert ready.wait(10)
            blocked(pid[0], backend_pid())
            guard(context, accounting.POST_ENTRIES)
        future.result(15)


def test_registration_label_changes_are_one_writer_set(batch_world, monkeypatch):
    register_core_permissions()
    query = Permission.objects.filter(code__startswith="access.")
    query.update(name="Old", is_active=False)
    seen = []
    real = access_models._lock_authority_targets

    def observe(target):
        seen.append(set(target.values_list("pk", flat=True)))
        return real(target)

    monkeypatch.setattr(access_models, "_lock_authority_targets", observe)
    expected = set(query.values_list("pk", flat=True))
    registered = register_core_permissions()
    assert seen[0] == expected and all(not permission.is_active for permission in registered)
    assert all(permission.name != "Old" for permission in registered)


def test_private_lock_primitives_require_transaction(batch_world):
    _, context, _, roles = batch_world
    connection = connections[current_database_alias()]
    assert not connection.in_atomic_block
    with pytest.raises(RuntimeError, match="transaction"):
        policies._share_authority_row(connection, get_user_model(), context.actor_id)
    with pytest.raises(RuntimeError, match="transaction"):
        policies._share_authority_rows(connection, Role, roles)
    with pytest.raises(RuntimeError, match="transaction"):
        access_models._lock_authority_targets(Role.objects.filter(pk__in=roles))


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
def test_public_composition_retry_and_audit_rollback(batch_world, monkeypatch, effect):
    outcomes, context, _, _ = batch_world
    operation, _ = posting(batch_world, effect)
    before = financial_state()
    real = accounting.record_audit_entry

    def fail_post(**kwargs):
        if kwargs["action"] == "accounting.entry.posted":
            raise RuntimeError("synthetic audit failure")
        return real(**kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(accounting, "record_audit_entry", fail_post)
        with pytest.raises(RuntimeError, match="synthetic audit failure"):
            operation()
    assert financial_state() == before
    result = operation()
    before = financial_state()
    assert operation() == result
    assert financial_state() == before


@pytest.mark.parametrize("kind", ["permission", "role"])
def test_fresh_selected_alias_writer_and_guard_default_cursor_trap(
    batch_world, monkeypatch, django_db_blocker, kind
):
    pg_only()
    _, context, permissions, roles = batch_world
    source_alias = current_database_alias()
    alias = "authority_batch_selected"
    database_name = "ph2_auth2_alias_" + uuid4().hex
    config = dict(connections.databases[source_alias])
    config.update(NAME=database_name, CONN_MAX_AGE=0)
    with connections[source_alias].cursor() as cursor:
        cursor.execute(f"CREATE DATABASE {connections[source_alias].ops.quote_name(database_name)}")
    connections.databases[alias] = config
    try:
        with django_db_blocker.unblock(), database_execution(alias):
            call_command("migrate", database=alias, verbosity=0)

            def forbidden_default(*args, **kwargs):
                pytest.fail("Authority batch or reader used the default cursor.")

            with monkeypatch.context() as patch:
                patch.setattr(connections[source_alias], "cursor", forbidden_default)
                currency = Currency.objects.create(code="USD", name="USD")
                country = Country.objects.create(code="US", name="US")
                language = Language.objects.create(code="EN", name="English")
                company = Company.objects.create(
                    id=context.company_id,
                    code="ALIAS",
                    name="Synthetic",
                    base_currency=currency,
                    country=country,
                    default_language=language,
                )
                actor = get_user_model().objects.create_user(
                    "alias@example.com", "synthetic-only", id=context.actor_id
                )
                UserCompanyAccess.objects.create(user=actor, company=company)
                for identity, code in zip(
                    permissions, (accounting.UPDATE_ENTRIES, accounting.POST_ENTRIES), strict=True
                ):
                    Permission.objects.filter(code=code).delete()
                    Permission.objects.create(id=identity, code=code, name=code)
                for identity, permission in zip(roles, permissions, strict=True):
                    role = Role.objects.create(
                        id=identity, company=company, code=str(identity), name="Selected"
                    )
                    RolePermission.objects.create(role=role, permission_id=permission)
                    UserRoleAssignment.objects.create(user=actor, company=company, role=role)
                guard_code = accounting.UPDATE_ENTRIES
                with business_atomic_context():
                    assert guard(context, guard_code) == context
                model = Permission if kind == "permission" else Role
                identities = permissions if kind == "permission" else roles
                query = model.objects.filter(pk__in=identities)
                assert query.update(is_active=False) == 2
                with business_atomic_context(), pytest.raises(PermissionDenied):
                    guard(context, guard_code)
                rows = list(query.order_by("-pk"))
                for row in rows:
                    row.is_active = True
                assert query.bulk_update(rows, ["is_active"], batch_size=1) == 2
                # Real business-wins wait in the selected DB, default connection trapped.
                ready, pid = Event(), []
                with ThreadPoolExecutor(max_workers=1) as pool:
                    with business_atomic_context():
                        guard(context, guard_code)
                        future = pool.submit(
                            worker, alias, lambda: query.update(is_active=False), ready, pid
                        )
                        assert ready.wait(10)
                        blocked(pid[0], backend_pid())
                    assert future.result(15) == 2
                if kind == "permission":
                    with pytest.raises(ProtectedError):
                        query.delete()
                    RolePermission.objects.filter(permission_id__in=permissions).delete()
                assert query.delete()[0] >= 2
        # Same UUIDs remain independently active in the source/default database.
        model = Permission if kind == "permission" else Role
        assert model.objects.filter(pk__in=identities, is_active=True).count() == 2
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
        with connections[source_alias].cursor() as cursor:
            cursor.execute(
                f"DROP DATABASE {connections[source_alias].ops.quote_name(database_name)}"
            )
