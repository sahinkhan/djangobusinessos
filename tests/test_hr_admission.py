"""Actual HR admission boundary tests; PostgreSQL proves locking/catalog behavior."""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier, Event
from time import monotonic
from uuid import UUID, uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, close_old_connections, connections, transaction

from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserCompanyAccess,
    UserRoleAssignment,
)
from businessos.core.audit.models import AuditEntry
from businessos.core.audit.services import record_audit_entry
from businessos.core.common.context import BusinessContext
from businessos.core.database import business_atomic_context, current_database_alias
from businessos.core.reference.models import Country
from businessos.modules.hr.admission import (
    AdmissionError,
    AuthorityBusy,
    ResourceBudgetExceeded,
    hr_operation,
)

pytestmark = pytest.mark.django_db(transaction=True)
VIEW = "hr.employee.view"
MANAGE = "hr.employee.manage"


@pytest.fixture
def admission_world(company, operator):
    permissions = tuple(
        Permission.objects.get_or_create(code=code, defaults={"name": code})[0]
        for code in (VIEW, MANAGE, "hr.department.view", "hr.department.manage")
    )
    role = Role.objects.create(company=company, code="HR_ADMISSION", name="HR admission")
    for permission in permissions:
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return BusinessContext(actor_id=operator.id, company_id=company.id), role, permissions


def _postgresql():
    connection = connections[current_database_alias()]
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL relation/row-lock/catalog admission proof only.")
    return connection


def test_unknown_outer_transaction_rejected_before_sql(admission_world):
    context, _, _ = admission_world
    statements = []

    def capture(execute, sql, params, many, context):
        statements.append(sql)
        return execute(sql, params, many, context)

    connection = connections[current_database_alias()]
    with business_atomic_context(), connection.execute_wrapper(capture):
        with pytest.raises(AdmissionError, match="unknown or prelocked"):
            with hr_operation(context, [VIEW]):
                pytest.fail("Unknown outer transaction entered")
    assert statements == []


def test_missing_final_admission_rolls_back_all_effects(admission_world):
    context, _, _ = admission_world
    with pytest.raises(AdmissionError, match="without complete"):
        with hr_operation(context, [VIEW]):
            record_audit_entry(
                context=context,
                action="hr.employee.updated",
                object_type="hr.Employee",
                object_id=uuid4(),
            )
    assert not AuditEntry.objects.filter(action="hr.employee.updated").exists()


def test_complete_inactive_authority_and_compound_native_guards(admission_world):
    context, _, _ = admission_world
    inactive, _ = Permission.objects.get_or_create(
        code="hr.leave.approve", defaults={"name": "Retired admission evidence"}
    )
    inactive.is_active = False
    inactive.save(update_fields=["is_active"])
    role = Role.objects.create(
        company_id=context.company_id, code="INACTIVE", name="Inactive", is_active=False
    )
    RolePermission.objects.create(role=role, permission=inactive)
    UserRoleAssignment.objects.create(
        user_id=context.actor_id, company_id=context.company_id, role=role
    )
    with hr_operation(context, [MANAGE, VIEW]) as operation:
        operation.authorize()
        assert context.actor_id in operation.user_ids
        assert role.id in operation.role_ids
        assert inactive.id in operation.permission_ids
        assert operation.permissions == (MANAGE, VIEW)
        operation.authorize()  # No cached authorization on repeated successful return.


@pytest.mark.parametrize("expansion", ["anchor", "permission"])
def test_dynamic_compound_and_anchor_declaration_freezes_at_authorization(
    admission_world, expansion
):
    context, _, _ = admission_world
    anchor = ("hr.employee", uuid4())
    with pytest.raises(AdmissionError, match="cannot expand"):
        with hr_operation(context, [VIEW]) as operation:
            operation.declare_anchors([anchor])
            operation.declare_permissions([MANAGE])
            operation.authorize()
            assert operation.anchors == frozenset([anchor])
            assert operation.permissions == (MANAGE, VIEW)
            operation.declare_anchors([anchor])  # Reusing a covered subset is admitted.
            operation.declare_permissions([MANAGE])
            with pytest.raises(AdmissionError, match="cannot expand"):
                if expansion == "anchor":
                    operation.declare_anchors([("hr.employee", uuid4())])
                else:
                    operation.declare_permissions(["hr.department.view"])


def test_admitted_nested_subset_reuses_outer_and_rechecks_guards(admission_world):
    context, _, _ = admission_world
    anchor = ("hr.employee", uuid4())
    connection = connections[current_database_alias()]
    with hr_operation(context, [VIEW, MANAGE], anchors=[anchor]) as outer:
        outer.authorize()
        block = connection.atomic_blocks[0]
        with hr_operation(context, [VIEW], anchors=[anchor]) as nested:
            assert nested is outer
            assert connection.atomic_blocks[0] is block
            assert not connection.savepoint_ids
        outer.checkpoint()


@pytest.mark.parametrize("change", ["user", "anchor", "permission", "actor", "company"])
def test_nested_expansion_rejected_before_sql(admission_world, change):
    context, _, _ = admission_world
    connection = connections[current_database_alias()]
    statements = []

    def capture(execute, sql, params, many, context):
        statements.append(sql)
        return execute(sql, params, many, context)

    options = {"anchors": (), "user_ids": ()}
    permissions = [VIEW]
    nested_context = context
    if change == "user":
        options["user_ids"] = [uuid4()]
    elif change == "anchor":
        options["anchors"] = [("hr.employee", uuid4())]
    elif change == "permission":
        permissions = [MANAGE]
    elif change == "actor":
        nested_context = BusinessContext(actor_id=uuid4(), company_id=context.company_id)
    else:
        nested_context = BusinessContext(actor_id=context.actor_id, company_id=uuid4())
    with pytest.raises(AdmissionError, match="predeclared complete"):
        with hr_operation(context, [VIEW]) as outer:
            outer.authorize()
            with connection.execute_wrapper(capture):
                with pytest.raises(AdmissionError, match="predeclared complete"):
                    with hr_operation(nested_context, permissions, **options):
                        pytest.fail("Expanded nested operation entered")
            assert statements == []


def test_caught_nested_failure_cannot_commit_outer_audit(admission_world):
    context, _, _ = admission_world
    with pytest.raises(ValueError, match="synthetic nested failure"):
        with hr_operation(context, [VIEW]) as outer:
            outer.authorize()
            record_audit_entry(
                context=context,
                action="hr.employee.updated",
                object_type="hr.Employee",
                object_id=uuid4(),
            )
            try:
                with hr_operation(context, [VIEW]):
                    raise ValueError("synthetic nested failure")
            except ValueError:
                pass
    assert not AuditEntry.objects.filter(action="hr.employee.updated").exists()


def test_user_union_requires_exact_existing_coverage(admission_world):
    context, _, _ = admission_world
    with pytest.raises(AdmissionError, match="identity coverage"):
        with hr_operation(context, [VIEW]) as operation:
            operation.authorize(user_ids=[uuid4()])


def test_user_union_overflow_never_materializes_truncated_authority(admission_world):
    context, _, _ = admission_world
    with pytest.raises(ResourceBudgetExceeded, match="User set"):
        with hr_operation(context, [VIEW]) as operation:
            operation.authorize(user_ids=[uuid4() for _ in range(1_000)])


@pytest.mark.parametrize("category", ["Role", "Permission"])
def test_complete_distinct_discovery_uses_overflow_sentinel(admission_world, monkeypatch, category):
    from businessos.modules.hr import admission

    context, role, _ = admission_world
    if category == "Role":
        for index in range(2):
            extra = Role.objects.create(
                company_id=context.company_id, code=f"SENTINEL_{index}", name="Sentinel"
            )
            UserRoleAssignment.objects.create(
                user_id=context.actor_id, company_id=context.company_id, role=extra
            )
    else:
        # Several links to one Permission must not disguise a later third ID.
        extra = Role.objects.create(company_id=context.company_id, code="DUP", name="Duplicate")
        UserRoleAssignment.objects.create(
            user_id=context.actor_id, company_id=context.company_id, role=extra
        )
        for permission in Permission.objects.filter(role_links__role=role):
            RolePermission.objects.create(role=extra, permission=permission)
    monkeypatch.setattr(admission, "AUTHORITY_CLASS_LIMIT", 2)
    with pytest.raises(ResourceBudgetExceeded, match=f"complete {category} set"):
        with hr_operation(context, [VIEW]) as operation:
            operation.authorize()


def test_cumulative_budget_is_not_reset_by_small_queries(admission_world, monkeypatch):
    from businessos.modules.hr import admission

    context, _, _ = admission_world
    clock = [100.0]
    monkeypatch.setattr(admission, "monotonic", lambda: clock[0])
    with pytest.raises(ResourceBudgetExceeded, match="cumulative"):
        with hr_operation(context, [VIEW]) as operation:
            operation.authorize()
            for _ in range(3):
                clock[0] += 0.5
                operation.checkpoint()
            clock[0] += 0.5
            operation.checkpoint()


def test_admission_failure_observability_records_category_alias_counts_not_personal_data(
    admission_world, caplog
):
    context, _, _ = admission_world
    with caplog.at_level("WARNING", logger="businessos.modules.hr.admission"):
        with pytest.raises(AdmissionError, match="without complete"):
            with hr_operation(context, [VIEW]):
                pass
    record = caplog.records[-1]
    assert record.hr_error_category == "AdmissionError"
    assert record.hr_alias == current_database_alias()
    assert record.hr_permissions == (VIEW,)
    assert record.hr_role_count == record.hr_permission_count == 0
    assert str(context.actor_id) not in caplog.text
    assert "phase1@example.com" not in caplog.text


def test_warehouse_context_is_rejected(admission_world):
    context, _, _ = admission_world
    warehouse_context = BusinessContext(
        actor_id=context.actor_id, company_id=context.company_id, warehouse_id=uuid4()
    )
    with pytest.raises(PermissionDenied, match="Warehouse"):
        with hr_operation(warehouse_context, [VIEW]):
            pytest.fail("Warehouse context entered")


def test_superuser_namespace_includes_inactive_permission_rows(admission_world):
    context, _, _ = admission_world
    actor = get_user_model().objects.get(pk=context.actor_id)
    actor.is_superuser = True
    actor.save(update_fields=["is_superuser"])
    inactive, _ = Permission.objects.get_or_create(
        code="hr.leave.cancel", defaults={"name": "Inactive namespace evidence"}
    )
    inactive.is_active = False
    inactive.save(update_fields=["is_active"])
    with hr_operation(context, [VIEW]) as operation:
        operation.authorize()
        assert operation.superuser
        assert not operation.role_ids
        assert inactive.id in operation.permission_ids
        assert operation.permission_ids == frozenset(
            Permission.objects.values_list("id", flat=True)
        )


@pytest.mark.parametrize("superuser", [False, True])
def test_postgresql_relation_modes_and_complete_final_sql(admission_world, superuser):
    connection = _postgresql()
    context, role, permissions = admission_world
    statements = []
    if superuser:
        get_user_model().objects.filter(pk=context.actor_id).update(is_superuser=True)

    def capture(execute, sql, params, many, context):
        statements.append((sql, params))
        return execute(sql, params, many, context)

    with connection.execute_wrapper(capture), hr_operation(context, [VIEW, MANAGE]) as operation:
        operation.authorize()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT c.relname, l.mode FROM pg_catalog.pg_locks l "
                "JOIN pg_catalog.pg_class c ON c.oid = l.relation "
                "WHERE l.pid = pg_catalog.pg_backend_pid() AND l.granted "
                "AND c.relname IN ('identity_user', 'access_role', 'access_permission')"
            )
            held = cursor.fetchall()
        assert all(
            (name, "RowShareLock") in held
            for name in ("identity_user", "access_role", "access_permission")
        )
        assert not any(mode in {"ExclusiveLock", "AccessExclusiveLock"} for _, mode in held)
        assert operation.role_ids == (frozenset() if superuser else frozenset([role.id]))
        assert {value.id for value in permissions} <= operation.permission_ids
    qualified = [sql for sql, _ in statements if "FOR SHARE NOWAIT" in sql]
    assert any('"public"."identity_user"' in sql for sql in qualified)
    if not superuser:
        assert any('"public"."access_role"' in sql for sql in qualified)
    assert any('"public"."access_permission"' in sql for sql in qualified)
    native = [(sql, params) for sql, params in statements if sql.rstrip().endswith("FOR SHARE")]
    assert len(native) >= (4 if superuser else 6)
    coverage = {
        "identity_user": operation.user_ids,
        "access_role": operation.role_ids,
        "access_permission": operation.permission_ids,
    }
    observed = {name: set() for name in coverage}
    for sql, params in native:
        matches = [name for name in coverage if f'FROM "{name}" ' in sql]
        assert len(matches) == 1
        name = matches[0]
        requested = {UUID(str(value)) for value in params}
        assert requested <= coverage[name], "Native Core introduced an uncovered authority row"
        observed[name].update(requested)
    assert all(observed[name] == coverage[name] for name in coverage)


def test_postgresql_unknown_manual_transaction_rejected(admission_world):
    connection = _postgresql()
    context, _, _ = admission_world
    connection.set_autocommit(False)
    try:
        with pytest.raises(AdmissionError, match="unknown or prelocked"):
            with hr_operation(context, [VIEW]):
                pytest.fail("Manual transaction entered")
    finally:
        connection.rollback()
        connection.set_autocommit(True)


@pytest.mark.parametrize("mode", ["REPEATABLE READ", "SERIALIZABLE"])
def test_postgresql_non_read_committed_isolation_rejected(admission_world, mode):
    connection = _postgresql()
    context, _, _ = admission_world
    with connection.cursor() as cursor:
        cursor.execute(f"SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL {mode}")
    try:
        with pytest.raises(AdmissionError, match="READ COMMITTED"):
            with hr_operation(context, [VIEW]):
                pytest.fail("Unsupported isolation admitted")
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                "SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL READ COMMITTED"
            )


def test_postgresql_shadowed_authority_relation_rejected(admission_world):
    connection = _postgresql()
    context, _, _ = admission_world
    with connection.cursor() as cursor:
        cursor.execute("CREATE TEMP TABLE identity_user (id uuid)")
    try:
        # Initial ordinary authorization also sees this invalid shadow.  Use a
        # same-shaped clone so the native initial guard has an actual actor row.
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE pg_temp.identity_user")
            cursor.execute(
                "CREATE TEMP TABLE identity_user (LIKE public.identity_user INCLUDING ALL)"
            )
            cursor.execute("INSERT INTO pg_temp.identity_user SELECT * FROM public.identity_user")
        with pytest.raises(AdmissionError, match="identity/resolution"):
            with hr_operation(context, [VIEW]) as operation:
                operation.authorize()
    finally:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS pg_temp.identity_user")


@pytest.mark.parametrize("target", ["identity_user", "access_role", "access_permission"])
def test_postgresql_nowait_conflict_rolls_back_before_authority_busy(admission_world, target):
    connection = _postgresql()
    context, role, permissions = admission_world
    identity = {
        "identity_user": context.actor_id,
        "access_role": role.id,
        "access_permission": permissions[0].id,
    }[target]
    locked, release = Event(), Event()
    alias = connection.alias

    def writer():
        close_old_connections()
        worker = connections[alias]
        try:
            with transaction.atomic(using=alias), worker.cursor() as cursor:
                cursor.execute(
                    f'SELECT id FROM public."{target}" WHERE id = %s FOR UPDATE', [identity]
                )
                assert cursor.fetchone()[0] == identity
                locked.set()
                assert release.wait(10), "Reader failed to release coordinated writer"
        finally:
            worker.close()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(writer)
        try:
            assert locked.wait(10), "Writer did not acquire its row lock"
            with pytest.raises(AuthorityBusy):
                with hr_operation(context, [VIEW]) as operation:
                    # A harmless synthetic marker has no User FK, so it cannot
                    # itself introduce a pre-admission authority lock or wait.
                    Country.objects.create(code="XA", name="Synthetic rollback marker")
                    operation.authorize()
            assert not connection.in_atomic_block
            assert not Country.objects.filter(code="XA").exists()
            assert not AuditEntry.objects.filter(action="hr.employee.updated").exists()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM pg_catalog.pg_locks "
                    "WHERE pid = pg_catalog.pg_backend_pid() AND locktype = 'transactionid' "
                    "AND mode = 'ShareLock'"
                )
                assert cursor.fetchone()[0] == 0
        finally:
            release.set()
            future.result(timeout=10)
    with hr_operation(context, [VIEW]) as operation:
        operation.authorize()


def test_postgresql_timeout_settings_restore_after_outcome(admission_world):
    connection = _postgresql()
    context, _, _ = admission_world

    def settings():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_setting('statement_timeout'), current_setting('lock_timeout'), "
                "current_setting('idle_in_transaction_session_timeout')"
            )
            return cursor.fetchone()

    original = settings()
    with hr_operation(context, [VIEW]) as operation:
        operation.authorize()
        assert settings() != original
    assert settings() == original
    with pytest.raises(ValueError, match="synthetic rollback"):
        with hr_operation(context, [VIEW]) as operation:
            operation.authorize()
            raise ValueError("synthetic rollback")
    assert settings() == original


def test_selected_alias_bootstrap_and_default_cursor_trap(django_db_blocker, monkeypatch):
    from django.db.migrations.executor import MigrationExecutor

    from businessos.core.database import database_execution
    from businessos.core.organization.models import Company
    from businessos.core.reference.models import Country, Currency, Language

    alias = "hr_admission_selected"
    config = dict(connections.databases["default"])
    config.update(ENGINE="django.db.backends.sqlite3", NAME=":memory:", OPTIONS={})
    connections.databases[alias] = config

    def forbidden_default(*args, **kwargs):
        pytest.fail("HR admission attempted an implicit default cursor")

    try:
        with django_db_blocker.unblock(), database_execution(alias):
            monkeypatch.setattr(connections["default"], "cursor", forbidden_default)
            connection = connections[alias]
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
            currency = Currency.objects.create(code="HRT", name="HR test")
            country = Country.objects.create(code="ZZ", name="Synthetic")
            language = Language.objects.create(code="UND", name="Synthetic")
            company = Company.objects.create(
                code="HR_ALIAS",
                name="HR alias",
                base_currency=currency,
                country=country,
                default_language=language,
            )
            actor = get_user_model().objects.create_superuser("hr-alias@example.com", "test")
            UserCompanyAccess.objects.create(user=actor, company=company)
            Permission.objects.get_or_create(code=VIEW, defaults={"name": VIEW})
            context = BusinessContext(actor_id=actor.id, company_id=company.id)
            with hr_operation(context, [VIEW]) as operation:
                operation.authorize()
                assert operation.alias == alias
                assert operation.company._state.db == alias
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]


def _worker(alias, operation, ready=None, pids=None):
    from businessos.core.database import database_execution

    close_old_connections()
    try:
        with database_execution(alias):
            with connections[alias].cursor() as cursor:
                cursor.execute("SET statement_timeout = '10s'")
                cursor.execute("SELECT pg_backend_pid()")
                if pids is not None:
                    pids.append(cursor.fetchone()[0])
            if ready is not None:
                ready.set()
            return operation()
    finally:
        connections[alias].close()


def _observe_wait(connection, worker_pid):
    deadline = monotonic() + 5
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            cursor.execute("SELECT pg_backend_pid() = ANY(pg_blocking_pids(%s))", [worker_pid])
            if cursor.fetchone()[0]:
                return
            Event().wait(0.01)  # Actual lock graph, not delay, is the race oracle.
    pytest.fail("The required PostgreSQL row-lock wait was not observed.")


@pytest.mark.parametrize("kind", ["company_access", "role_assignment", "role_permission"])
def test_public_hr_waiter_rechecks_committed_company_revocation(admission_world, kind):
    from businessos.core.access import services as access
    from businessos.core.organization.models import Company
    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, role, _ = admission_world
    for code in (access.MANAGE_ORGANIZATIONAL_ACCESS, access.MANAGE_ROLES):
        Permission.objects.get_or_create(code=code, defaults={"name": code})
    admin = get_user_model().objects.create_superuser("hr-revoker@example.com", "test")
    admin_context = BusinessContext(actor_id=admin.id, company_id=context.company_id)
    ready, pids = Event(), []

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(using=connection.alias):
            Company.objects.select_for_update().get(pk=context.company_id)
            future = pool.submit(
                _worker,
                connection.alias,
                lambda: create_department(context, code="WAITING", name="Must not survive"),
                ready,
                pids,
            )
            assert ready.wait(5)
            _observe_wait(connection, pids[0])
            if kind == "company_access":
                access.revoke_company_access(admin_context, user_id=context.actor_id)
            elif kind == "role_assignment":
                access.revoke_role(admin_context, user_id=context.actor_id, role_id=role.id)
            else:
                access.revoke_role_permission(
                    admin_context, role_id=role.id, permission_code="hr.department.manage"
                )
        with pytest.raises(PermissionDenied):
            future.result(timeout=5)
    assert not Department.objects.filter(code="WAITING").exists()
    assert not AuditEntry.objects.filter(action="hr.department.created").exists()


@pytest.mark.parametrize("kind", ["actor", "role", "permission"])
def test_public_hr_rechecks_actor_and_authority_after_domain_wait(admission_world, kind):
    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department, update_department

    connection = _postgresql()
    context, role, _ = admission_world
    department = create_department(context, code="LOCKED", name="Original")
    baseline = AuditEntry.objects.count()
    ready, pids = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(using=connection.alias):
            Department.objects.select_for_update().get(pk=department.id)
            future = pool.submit(
                _worker,
                connection.alias,
                lambda: update_department(
                    context,
                    department_id=department.id,
                    expected_revision=1,
                    name="Must not survive",
                    is_active=True,
                ),
                ready,
                pids,
            )
            assert ready.wait(5)
            _observe_wait(connection, pids[0])
            if kind == "actor":
                get_user_model().objects.filter(pk=context.actor_id).update(is_active=False)
            elif kind == "role":
                Role.objects.filter(pk=role.id).update(is_active=False)
            else:
                Permission.objects.filter(code="hr.department.manage").update(is_active=False)
        with pytest.raises(PermissionDenied):
            future.result(timeout=5)
    stored = Department.objects.get(pk=department.id)
    assert (stored.name, stored.revision) == ("Original", 1)
    assert AuditEntry.objects.count() == baseline


@pytest.mark.parametrize("reverse", [False, True])
def test_public_employee_writer_first_unordered_user_batches_fail_closed(admission_world, reverse):
    from businessos.core.organization.models import Company
    from businessos.modules.hr.models import Employee
    from businessos.modules.hr.services import create_employee
    from businessos.modules.party.models import Party

    connection = _postgresql()
    context, _, _ = admission_world
    beneficiary = get_user_model().objects.create_user("hr-beneficiary@example.com", "test")
    UserCompanyAccess.objects.create(user=beneficiary, company_id=context.company_id)
    party = Party.objects.create(
        company_id=context.company_id, party_type=Party.Type.PERSON, display_name="Synthetic person"
    )
    identities = sorted([context.actor_id, beneficiary.id], reverse=reverse)
    held, release = Event(), Event()

    def writer():
        with transaction.atomic(using=connection.alias):
            rows = {row.pk: row for row in get_user_model().objects.filter(pk__in=identities)}
            ordered = [rows[identity] for identity in identities]
            for row in ordered:
                row.is_active = False

            def hold_first_update(execute, sql, params, many, context):
                result = execute(sql, params, many, context)
                if sql.startswith('UPDATE "identity_user"') and not held.is_set():
                    held.set()  # The actual first batch UPDATE now owns its lock.
                    assert release.wait(5)
                return result

            with connections[connection.alias].execute_wrapper(hold_first_update):
                get_user_model().objects.bulk_update(ordered, ["is_active"], batch_size=1)

    def probe_released_anchors():
        with transaction.atomic(using=connection.alias):
            Company.objects.select_for_update(nowait=True).get(pk=context.company_id)
            Party.objects.select_for_update(nowait=True).get(pk=party.id)
            get_user_model().objects.select_for_update(nowait=True).get(pk=identities[1])
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(_worker, connection.alias, writer)
        try:
            assert held.wait(5)
            with pytest.raises(AuthorityBusy):
                create_employee(
                    context,
                    party_id=party.id,
                    employee_number="NO_EFFECT",
                    joining_date=date(2020, 1, 1),
                    user_id=beneficiary.id,
                )
            assert not Employee.objects.exists()
            assert not AuditEntry.objects.filter(action="hr.employee.created").exists()
            assert pool.submit(_worker, connection.alias, probe_released_anchors).result(timeout=5)
        finally:
            release.set()
            future.result(timeout=5)
    with pytest.raises(PermissionDenied):
        create_employee(
            context,
            party_id=party.id,
            employee_number="NO_EFFECT",
            joining_date=date(2020, 1, 1),
            user_id=beneficiary.id,
        )


@pytest.mark.parametrize("same_actor", [False, True])
def test_public_employee_hr_first_writer_wait_is_row_not_global_gate(
    admission_world, monkeypatch, same_actor
):
    from businessos.modules.hr import services
    from businessos.modules.hr.models import Employee
    from businessos.modules.party.models import Party

    connection = _postgresql()
    context, _, _ = admission_world
    beneficiary = get_user_model().objects.get(pk=context.actor_id)
    if not same_actor:
        beneficiary = get_user_model().objects.create_user("hr-new-link@example.com", "test")
        UserCompanyAccess.objects.create(user=beneficiary, company_id=context.company_id)
    party = Party.objects.create(
        company_id=context.company_id, party_type=Party.Type.PERSON, display_name="Synthetic person"
    )
    held, release, writer_ready, writer_pids = Event(), Event(), Event(), []
    original_audit = services.audit

    def audited_hold(*args, **kwargs):
        original_audit(*args, **kwargs)
        held.set()
        assert release.wait(5)

    monkeypatch.setattr(services, "audit", audited_hold)

    def writer():
        user = get_user_model().objects.get(pk=beneficiary.id)
        user.is_active = False
        user.save(update_fields=["is_active"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        hr = pool.submit(
            _worker,
            connection.alias,
            lambda: services.create_employee(
                context,
                party_id=party.id,
                employee_number="KEPT",
                joining_date=date(2020, 1, 1),
                user_id=beneficiary.id,
            ),
        )
        try:
            assert held.wait(5)
            writer_future = pool.submit(
                _worker, connection.alias, writer, writer_ready, writer_pids
            )
            assert writer_ready.wait(5)
            # Main connection observes the HR worker (not itself) as blocker.
            deadline = monotonic() + 1.5
            with connection.cursor() as cursor:
                while monotonic() < deadline:
                    cursor.execute(
                        "SELECT wait_event_type, wait_event FROM pg_catalog.pg_stat_activity "
                        "WHERE pid=%s AND cardinality(pg_blocking_pids(pid)) > 0",
                        [writer_pids[0]],
                    )
                    row = cursor.fetchone()
                    if row is not None and row[0] == "Lock":
                        assert row[1] in {"transactionid", "tuple"}
                        break
                    Event().wait(0.01)
                else:
                    pytest.fail("User writer did not visibly wait on the relevant HR row lock")
        finally:
            release.set()
        result = hr.result(timeout=5)
        writer_future.result(timeout=5)
    assert Employee.objects.get(pk=result.id).user_id == beneficiary.id
    assert not get_user_model().objects.get(pk=beneficiary.id).is_active
    assert AuditEntry.objects.filter(action="hr.employee.created").count() == 1


def _second_company(context):
    from businessos.core.organization.models import Company

    source = Company.objects.get(pk=context.company_id)
    second = Company.objects.create(
        code="HR_SECOND",
        name="Second synthetic Company",
        base_currency_id=source.base_currency_id,
        country_id=source.country_id,
        default_language_id=source.default_language_id,
    )
    UserCompanyAccess.objects.create(user_id=context.actor_id, company=second)
    role = Role.objects.create(company=second, code="HR_SECOND", name="Second authority")
    for permission in Permission.objects.filter(
        code__in=["hr.department.manage", "hr.department.view"]
    ):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user_id=context.actor_id, company=second, role=role)
    return BusinessContext(actor_id=context.actor_id, company_id=second.id), role


@pytest.mark.parametrize("shared_actor", [True, False])
def test_public_hr_independent_companies_share_read_only_authority_without_global_gate(
    admission_world, shared_actor
):
    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, _, _ = admission_world
    second, role = _second_company(context)
    if not shared_actor:
        actor = get_user_model().objects.create_user("hr-independent@example.com", "test")
        UserCompanyAccess.objects.create(user=actor, company_id=second.company_id)
        UserRoleAssignment.objects.create(user=actor, company_id=second.company_id, role=role)
        second = BusinessContext(actor_id=actor.id, company_id=second.company_id)
    first_ready, second_ready, release = Event(), Event(), Event()

    def operation(scope, code, ready):
        with hr_operation(scope, ["hr.department.manage", "hr.department.view"]) as admitted:
            admitted.authorize()
            ready.set()
            assert release.wait(5)
            return create_department(scope, code=code, name=code)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(
            _worker, connection.alias, lambda: operation(context, "FIRST", first_ready)
        )
        other = pool.submit(
            _worker, connection.alias, lambda: operation(second, "SECOND", second_ready)
        )
        try:
            assert first_ready.wait(5)
            assert second_ready.wait(1.5), "A compatible cross-Company reader was globally blocked"
        finally:
            release.set()
        first.result(timeout=5)
        other.result(timeout=5)
    assert Department.objects.count() == 2
    assert AuditEntry.objects.filter(action="hr.department.created").count() == 2


def test_native_sales_public_service_can_progress_while_hr_holds_shared_authority(admission_world):
    from businessos.core.organization.models import Company
    from businessos.modules.party.models import Party
    from businessos.modules.sales.services import create_sales_order

    connection = _postgresql()
    context, _, _ = admission_world
    second, role = _second_company(context)
    permission, _ = Permission.objects.get_or_create(
        code="sales.order.create", defaults={"name": "Create Sales order"}
    )
    RolePermission.objects.create(role=role, permission=permission)
    customer = Party.objects.create(
        company_id=second.company_id,
        party_type=Party.Type.PERSON,
        display_name="Synthetic customer",
        is_customer=True,
    )
    currency_id = Company.objects.get(pk=second.company_id).base_currency_id
    with ThreadPoolExecutor(max_workers=1) as pool:
        with hr_operation(context, [VIEW]) as operation:
            operation.authorize()
            future = pool.submit(
                _worker,
                connection.alias,
                lambda: create_sales_order(
                    second,
                    customer_id=customer.id,
                    currency_id=currency_id,
                    order_date=date(2020, 1, 1),
                ),
            )
            order = future.result(timeout=1.5)
    assert order.company_id == second.company_id
    assert AuditEntry.objects.filter(action="sales.order.created").count() == 1


def test_actual_public_hr_service_nondefault_postgresql_alias_and_default_cursor_trap(
    admission_world, django_db_blocker, monkeypatch
):
    from businessos.core.database import database_execution
    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    default = _postgresql()
    context, _, _ = admission_world
    alias = "hr_authority_postgresql_selected"
    config = dict(default.settings_dict)
    config["TEST"] = dict(config.get("TEST", {}))
    connections.databases[alias] = config

    def forbidden_default(*args, **kwargs):
        pytest.fail("Selected PostgreSQL HR service touched the default cursor")

    try:
        with django_db_blocker.unblock(), monkeypatch.context() as patched:
            patched.setattr(default, "cursor", forbidden_default)
            with database_execution(alias):
                assert connections[alias].vendor == "postgresql"
                result = create_department(context, code="PG_ALIAS", name="Selected alias")
        assert Department.objects.get(pk=result.id).code == "PG_ALIAS"
        assert (
            AuditEntry.objects.filter(action="hr.department.created", object_id=result.id).count()
            == 1
        )
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]


def test_native_sales_first_shared_authority_does_not_block_public_hr(admission_world, monkeypatch):
    from businessos.core.organization.models import Company
    from businessos.modules.hr.services import create_department
    from businessos.modules.party.models import Party
    from businessos.modules.sales import services as sales

    connection = _postgresql()
    context, _, _ = admission_world
    second, role = _second_company(context)
    permission, _ = Permission.objects.get_or_create(
        code="sales.order.create", defaults={"name": "Create Sales order"}
    )
    RolePermission.objects.create(role=role, permission=permission)
    customer = Party.objects.create(
        company_id=second.company_id,
        party_type=Party.Type.PERSON,
        display_name="Synthetic customer",
        is_customer=True,
    )
    currency_id = Company.objects.get(pk=second.company_id).base_currency_id
    held, release = Event(), Event()
    original_audit = sales.record_audit_entry

    def hold(*args, **kwargs):
        original_audit(*args, **kwargs)
        held.set()
        assert release.wait(5)

    monkeypatch.setattr(sales, "record_audit_entry", hold)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            _worker,
            connection.alias,
            lambda: sales.create_sales_order(
                second,
                customer_id=customer.id,
                currency_id=currency_id,
                order_date=date(2020, 1, 1),
            ),
        )
        try:
            assert held.wait(5)
            department = create_department(context, code="COMPATIBLE", name="Compatible reader")
        finally:
            release.set()
        future.result(timeout=5)
    assert department.company_id == context.company_id
    assert AuditEntry.objects.filter(action="hr.department.created").count() == 1
    assert AuditEntry.objects.filter(action="sales.order.created").count() == 1


def test_implicit_for_share_nowait_still_waits_on_relation_negative_control(admission_world):
    connection = _postgresql()
    context, _, _ = admission_world
    ready, pids = Event(), []

    def implicit_reader():
        with (
            transaction.atomic(using=connection.alias),
            connections[connection.alias].cursor() as cursor,
        ):
            cursor.execute(
                "SELECT id FROM public.identity_user WHERE id=%s FOR SHARE NOWAIT",
                [context.actor_id],
            )
            return cursor.fetchone()[0]

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(using=connection.alias), connection.cursor() as cursor:
            cursor.execute("LOCK TABLE public.identity_user IN EXCLUSIVE MODE")
            future = pool.submit(_worker, connection.alias, implicit_reader, ready, pids)
            assert ready.wait(5)
            _observe_wait(connection, pids[0])
        assert future.result(timeout=5) == context.actor_id


def test_explicit_relation_admission_refuses_before_implicit_row_acquisition(admission_world):
    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, _, _ = admission_world
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(using=connection.alias), connection.cursor() as cursor:
            cursor.execute("LOCK TABLE public.identity_user IN EXCLUSIVE MODE")
            future = pool.submit(
                _worker,
                connection.alias,
                lambda: create_department(context, code="RELATION_BUSY", name="Must not survive"),
            )
            with pytest.raises(AuthorityBusy):
                future.result(timeout=1.5)
    assert not Department.objects.filter(code="RELATION_BUSY").exists()
    assert not AuditEntry.objects.filter(action="hr.department.created").exists()


@pytest.mark.parametrize("superuser", [False, True])
def test_existing_superuser_namespace_is_not_a_new_ordinary_dml_gate(admission_world, superuser):
    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, _, _ = admission_world
    if superuser:
        get_user_model().objects.filter(pk=context.actor_id).update(is_superuser=True)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(using=connection.alias), connection.cursor() as cursor:
            cursor.execute("LOCK TABLE public.access_permission IN ROW EXCLUSIVE MODE")
            future = pool.submit(
                _worker,
                connection.alias,
                lambda: create_department(context, code="NAMESPACE", name="Namespace proof"),
            )
            if superuser:
                with pytest.raises(AuthorityBusy):
                    future.result(timeout=1.5)
            else:
                assert future.result(timeout=1.5).company_id == context.company_id
    assert Department.objects.filter(code="NAMESPACE").count() == (0 if superuser else 1)
    assert AuditEntry.objects.filter(action="hr.department.created").count() == (
        0 if superuser else 1
    )


@pytest.mark.parametrize("name", ["organization_company", "hr_department"])
def test_source_shadow_is_rejected_before_any_company_or_hr_data_read(admission_world, name):
    connection = _postgresql()
    context, _, _ = admission_world
    statements = []

    def capture(execute, sql, params, many, context):
        statements.append(sql)
        return execute(sql, params, many, context)

    with connection.cursor() as cursor:
        cursor.execute(f'CREATE TEMP TABLE "{name}" (LIKE public."{name}" INCLUDING ALL)')
    try:
        with connection.execute_wrapper(capture):
            with pytest.raises(AdmissionError, match="identity/resolution"):
                with hr_operation(context, [VIEW]):
                    pytest.fail("Source shadow was admitted")
        assert not any('FROM "organization_company"' in statement for statement in statements)
        assert not any('FROM "hr_department"' in statement for statement in statements)
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TABLE pg_temp."{name}"')


@pytest.mark.parametrize("name", ["hr_department", "access_rolepermission"])
@pytest.mark.parametrize("enabled", [False, True])
def test_source_rls_flags_and_disabled_policies_fail_closed(admission_world, name, enabled):
    connection = _postgresql()
    context, _, _ = admission_world
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE POLICY hr_synthetic_hide ON public."{name}" USING (false)')
        if enabled:
            cursor.execute(f'ALTER TABLE public."{name}" ENABLE ROW LEVEL SECURITY')
    try:
        with pytest.raises(AdmissionError, match="identity/resolution/policy"):
            with hr_operation(context, [VIEW]):
                pytest.fail("RLS-filterable source was admitted")
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f'DROP POLICY hr_synthetic_hide ON public."{name}"')
            cursor.execute(f'ALTER TABLE public."{name}" DISABLE ROW LEVEL SECURITY')


def test_source_relocated_table_fails_closed_without_normalizing_schema(admission_world):
    connection = _postgresql()
    context, _, _ = admission_world
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA hr_synthetic_review")
        cursor.execute("ALTER TABLE public.hr_department SET SCHEMA hr_synthetic_review")
    try:
        with pytest.raises(AdmissionError, match="missing or ambiguous"):
            with hr_operation(context, [VIEW]):
                pytest.fail("Relocated HR source was admitted")
    finally:
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE hr_synthetic_review.hr_department SET SCHEMA public")
            cursor.execute("DROP SCHEMA hr_synthetic_review")


def test_source_nonordinary_relation_kind_fails_closed(admission_world):
    connection = _postgresql()
    context, _, _ = admission_world
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE public.hr_department RENAME TO hr_synthetic_department")
        cursor.execute(
            "CREATE VIEW public.hr_department AS SELECT * FROM public.hr_synthetic_department"
        )
    try:
        with pytest.raises(AdmissionError, match="identity/resolution"):
            with hr_operation(context, [VIEW]):
                pytest.fail("Unexpected HR relation kind was admitted")
    finally:
        with connection.cursor() as cursor:
            cursor.execute("DROP VIEW public.hr_department")
            cursor.execute("ALTER TABLE public.hr_synthetic_department RENAME TO hr_department")


def test_original_blocking_user_order_deadlock_is_an_isolated_negative_control(admission_world):
    """T01 reproduces rejected old behavior; current HR never runs this protocol."""
    connection = _postgresql()
    context, _, _ = admission_world
    other = get_user_model().objects.create_user("old-reader-negative@example.com", "test")
    barrier = Barrier(2)

    def legacy(reader):
        try:
            with (
                transaction.atomic(using=connection.alias),
                connections[connection.alias].cursor() as cursor,
            ):
                if reader:
                    cursor.execute(
                        "SELECT id FROM public.identity_user WHERE id=%s FOR SHARE",
                        [context.actor_id],
                    )
                else:
                    cursor.execute(
                        "SELECT id FROM public.identity_user WHERE id=%s FOR UPDATE", [other.id]
                    )
                assert cursor.fetchone() is not None
                barrier.wait(timeout=5)
                if reader:
                    cursor.execute(
                        "SELECT id FROM public.identity_user WHERE id=%s FOR SHARE", [other.id]
                    )
                    assert cursor.fetchone() is not None
                else:
                    cursor.execute(
                        "UPDATE public.identity_user SET is_active=false WHERE id=%s",
                        [context.actor_id],
                    )
            return "committed"
        except DatabaseError as exc:
            code = getattr(exc.__cause__, "sqlstate", None)
            if code != "40P01":
                raise
            return code

    with ThreadPoolExecutor(max_workers=2) as pool:
        reader = pool.submit(_worker, connection.alias, lambda: legacy(True))
        writer = pool.submit(_worker, connection.alias, lambda: legacy(False))
        assert sorted([reader.result(timeout=10), writer.result(timeout=10)]) == [
            "40P01",
            "committed",
        ]
    assert not AuditEntry.objects.filter(action__startswith="hr.").exists()


def test_repeated_hot_role_refusals_are_bounded_then_fresh_request_succeeds(admission_world):
    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, role, _ = admission_world
    held, release = Event(), Event()

    def writer():
        with transaction.atomic(using=connection.alias):
            Role.objects.select_for_update().get(pk=role.id)
            held.set()
            assert release.wait(5)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_worker, connection.alias, writer)
        try:
            assert held.wait(5)
            for index in range(3):
                with pytest.raises(AuthorityBusy):
                    create_department(context, code=f"REFUSED_{index}", name="No effect")
                assert not connection.in_atomic_block
                assert not Department.objects.exists()
                assert not AuditEntry.objects.filter(action="hr.department.created").exists()
        finally:
            release.set()
            future.result(timeout=5)
    assert create_department(context, code="FRESH", name="Fresh independent request").revision == 1
    assert AuditEntry.objects.filter(action="hr.department.created").count() == 1


def test_real_django_constraint_check_swallowed_timeout_cannot_commit_hr_effect(admission_world):
    from django.db.models import BooleanField, Q, Value
    from django.db.models.expressions import RawSQL

    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, _, _ = admission_world
    checked = []
    with pytest.raises(ResourceBudgetExceeded) as outcome:
        with hr_operation(context, ["hr.department.manage", "hr.department.view"]) as operation:
            operation.authorize()
            # A real owning public mutation and successful Audit exist only in
            # this uncommitted outer transaction before the genuine SQL timeout.
            create_department(context, code="WITHHELD", name="Must be rolled back")
            checked.append(
                Q(slow=RawSQL("pg_sleep(3) IS NULL", [], output_field=BooleanField())).check(
                    {"slow": Value(True)}, using=connection.alias
                )
            )
    assert checked == [True]  # Actual Django fallback, not a mocked successful check.
    assert getattr(outcome.value.__cause__.__cause__, "sqlstate", None) == "57014"
    assert not connection.in_atomic_block
    assert not Department.objects.filter(code="WITHHELD").exists()
    assert not AuditEntry.objects.filter(action="hr.department.created").exists()


def _observe_foreign_row_wait(connection, worker_pid, blocker_pid):
    deadline = monotonic() + 1.5
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            cursor.execute(
                "SELECT wait_event_type, wait_event FROM pg_catalog.pg_stat_activity "
                "WHERE pid=%s AND %s=ANY(pg_blocking_pids(pid))",
                [worker_pid, blocker_pid],
            )
            row = cursor.fetchone()
            if row is not None and row[0] == "Lock":
                assert row[1] in {"tuple", "transactionid"}
                return
            Event().wait(0.01)
    pytest.fail("The supported writer did not visibly wait on the HR row lock")


def _hr_first_writer(context, monkeypatch, writer, *, writer_error=None):
    from businessos.modules.hr import services
    from businessos.modules.hr.models import Department

    connection = connections[current_database_alias()]
    held, release, ready = Event(), Event(), Event()
    hr_pids, writer_pids = [], []
    original = services.audit

    def hold(*args, **kwargs):
        original(*args, **kwargs)
        held.set()
        assert release.wait(5)

    monkeypatch.setattr(services, "audit", hold)

    def hr():
        return services.create_department(context, code="HR_WON", name="Valid winner")

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_worker, connection.alias, hr, None, hr_pids)
        try:
            assert held.wait(5)
            other = pool.submit(_worker, connection.alias, writer, ready, writer_pids)
            assert ready.wait(5)
            _observe_foreign_row_wait(connection, writer_pids[0], hr_pids[0])
        finally:
            release.set()
        first.result(timeout=5)
        if writer_error is None:
            other.result(timeout=5)
        else:
            with pytest.raises(writer_error):
                other.result(timeout=5)
    assert Department.objects.filter(code="HR_WON").count() == 1
    assert AuditEntry.objects.filter(action="hr.department.created").count() == 1


def test_original_user_only_reader_mixed_role_writer_deadlock_negative_control(admission_world):
    connection = _postgresql()
    context, role, _ = admission_world
    barrier = Barrier(2)

    def legacy(reader):
        try:
            with transaction.atomic(using=connection.alias):
                with connections[connection.alias].cursor() as cursor:
                    if reader:
                        cursor.execute(
                            "SELECT id FROM public.identity_user WHERE id=%s FOR SHARE",
                            [context.actor_id],
                        )
                        assert cursor.fetchone()
                    else:
                        Role.objects.filter(pk=role.id).update(name="Writer first")
                    barrier.wait(timeout=5)
                    if reader:
                        cursor.execute(
                            "SELECT id FROM public.access_role WHERE id=%s FOR SHARE", [role.id]
                        )
                        assert cursor.fetchone()
                    else:
                        get_user_model().objects.filter(pk=context.actor_id).update(is_active=False)
            return "committed"
        except DatabaseError as exc:
            if getattr(exc.__cause__, "sqlstate", None) != "40P01":
                raise
            return "40P01"

    with ThreadPoolExecutor(max_workers=2) as pool:
        reader = pool.submit(_worker, connection.alias, lambda: legacy(True))
        writer = pool.submit(_worker, connection.alias, lambda: legacy(False))
        assert sorted([reader.result(timeout=10), writer.result(timeout=10)]) == [
            "40P01",
            "committed",
        ]


@pytest.mark.parametrize(
    "family",
    ["role_update", "role_retire", "permission_update", "permission_upsert", "permission_retire"],
)
@pytest.mark.parametrize("hr_first", [False, True])
def test_actual_mixed_authority_then_user_batch_both_winner_orders(
    admission_world, monkeypatch, family, hr_first
):
    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, role, _ = admission_world
    other_user = get_user_model().objects.create_user("hr-mixed-batch@example.test", "test")
    held, release = Event(), Event()

    def writer():
        with transaction.atomic(using=connection.alias):
            if family.startswith("role"):
                Role.objects.filter(pk=role.id).update(
                    **({"is_active": False} if family == "role_retire" else {"name": "Changed"})
                )
            elif family == "permission_upsert":
                Permission.objects.update_or_create(
                    code="hr.department.manage", defaults={"name": "Changed by update_or_create"}
                )
            else:
                Permission.objects.filter(code="hr.department.manage").update(
                    **(
                        {"is_active": False}
                        if family == "permission_retire"
                        else {"name": "Changed"}
                    )
                )
            if not hr_first:
                held.set()
                assert release.wait(5)
            rows = [
                get_user_model().objects.get(pk=other_user.id),
                get_user_model().objects.get(pk=context.actor_id),
            ]
            for row in rows:
                row.is_active = False
            get_user_model().objects.bulk_update(rows, ["is_active"], batch_size=1)

    if hr_first:
        _hr_first_writer(context, monkeypatch, writer)
    else:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_worker, connection.alias, writer)
            try:
                assert held.wait(5)
                with pytest.raises(AuthorityBusy) as refused:
                    create_department(context, code="MIXED_BUSY", name="Must not survive")
                assert getattr(refused.value.__cause__.__cause__, "sqlstate", None) == "55P03"
                assert not Department.objects.exists()
                assert not AuditEntry.objects.filter(action="hr.department.created").exists()
            finally:
                release.set()
                future.result(timeout=5)
    with pytest.raises(PermissionDenied):
        create_department(context, code="AFTER_MIXED", name="Current actor is inactive")


@pytest.mark.parametrize("form", ["save", "update", "email", "last_login", "prelock", "delete"])
@pytest.mark.parametrize("hr_first", [False, True])
def test_supported_identity_writer_forms_both_winner_orders(
    admission_world, monkeypatch, form, hr_first
):
    from django.contrib.auth.models import update_last_login
    from django.db import IntegrityError
    from django.db.models.deletion import ProtectedError

    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, _, _ = admission_world
    held, release = Event(), Event()
    # This is only the test worker's cleanup watchdog, not an HR SQL/authority
    # deadline. Leave room for a loaded Docker host to schedule the asserting
    # thread; the actual lock conflict remains the PostgreSQL 55P03 oracle.
    coordination_timeout = 15

    def writer():
        def hold_first_write(execute, sql, params, many, execution_context):
            result = execute(sql, params, many, execution_context)
            if (
                not hr_first
                and not held.is_set()
                and (
                    sql.startswith('UPDATE "identity_user"')
                    or sql.startswith('DELETE FROM "identity_user"')
                    or 'FROM "identity_user"' in sql
                    and sql.rstrip().endswith("FOR UPDATE")
                )
            ):
                held.set()
                assert release.wait(coordination_timeout)
            return result

        with (
            transaction.atomic(using=connection.alias),
            connections[connection.alias].execute_wrapper(hold_first_write),
        ):
            user = get_user_model().objects.get(pk=context.actor_id)
            if form == "save":
                user.is_active = False
                user.save(update_fields=["is_active"])
            elif form == "update":
                get_user_model().objects.filter(pk=user.id).update(is_active=False)
            elif form == "email":
                user.email = "hr-changed-email@example.test"
                user.save(update_fields=["email"])
            elif form == "last_login":
                update_last_login(None, user)
            elif form == "prelock":
                get_user_model().objects.select_for_update().get(pk=user.id)
            else:
                user.delete()

    if hr_first:
        _hr_first_writer(
            context,
            monkeypatch,
            writer,
            writer_error=(ProtectedError, IntegrityError) if form == "delete" else None,
        )
    else:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_worker, connection.alias, writer)
            try:
                assert held.wait(coordination_timeout)
                with pytest.raises(AuthorityBusy) as refused:
                    create_department(context, code="IDENTITY_BUSY", name="Must not survive")
                assert getattr(refused.value.__cause__.__cause__, "sqlstate", None) == "55P03"
                assert not Department.objects.exists()
                assert not AuditEntry.objects.filter(action="hr.department.created").exists()
            finally:
                release.set()
                future.result(timeout=coordination_timeout)
    if form in {"save", "update"} or form == "delete" and not hr_first:
        with pytest.raises(PermissionDenied):
            create_department(context, code="AFTER_IDENTITY", name="Must deny current actor")
    else:
        assert create_department(context, code="AFTER_IDENTITY", name="Fresh request").revision == 1


@pytest.mark.parametrize("kind", ["role", "permission"])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("hr_first", [False, True])
def test_reversed_active_inactive_authority_multirow_writers(
    admission_world, monkeypatch, kind, reverse, hr_first
):
    from businessos.modules.hr.models import Department
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, role, _ = admission_world
    inactive_role = Role.objects.create(
        company_id=context.company_id, code="INACTIVE_MULTI", name="Inactive", is_active=False
    )
    UserRoleAssignment.objects.create(
        user_id=context.actor_id, company_id=context.company_id, role=inactive_role
    )
    inactive, _ = Permission.objects.get_or_create(
        code="hr.leave.approve", defaults={"name": "Inactive"}
    )
    inactive.is_active = False
    inactive.save(update_fields=["is_active"])
    RolePermission.objects.create(role=inactive_role, permission=inactive)
    active = role if kind == "role" else Permission.objects.get(code="hr.department.manage")
    other = inactive_role if kind == "role" else inactive
    identities = [other.id, active.id] if reverse else [active.id, other.id]
    model = Role if kind == "role" else Permission
    held, release = Event(), Event()

    def writer():
        with transaction.atomic(using=connection.alias):
            for index, identity in enumerate(identities):
                row = model.objects.get(pk=identity)
                row.name = f"Changed {index}"
                row.save(update_fields=["name"])
                if index == 0 and not hr_first:
                    held.set()
                    assert release.wait(5)

    if hr_first:
        _hr_first_writer(context, monkeypatch, writer)
    else:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_worker, connection.alias, writer)
            try:
                assert held.wait(5)
                with pytest.raises(AuthorityBusy) as refused:
                    create_department(context, code="MULTI_BUSY", name="Must not survive")
                assert getattr(refused.value.__cause__.__cause__, "sqlstate", None) == "55P03"
                assert not Department.objects.exists()
                assert not AuditEntry.objects.filter(action="hr.department.created").exists()
            finally:
                release.set()
                future.result(timeout=5)
    assert (
        create_department(context, code="AFTER_MULTI", name="Fresh authorized request").revision
        == 1
    )


@pytest.mark.parametrize("hr_first", [False, True])
def test_unrelated_permission_update_or_create_and_user_writer_remain_compatible(
    admission_world, hr_first
):
    from businessos.modules.hr.services import create_department

    connection = _postgresql()
    context, _, _ = admission_world
    Permission.objects.get_or_create(code="access.role.manage", defaults={"name": "Unrelated"})
    other = get_user_model().objects.create_user("hr-unrelated-writer@example.test", "test")
    held, release = Event(), Event()

    def writer():
        with transaction.atomic(using=connection.alias):
            Permission.objects.update_or_create(
                code="access.role.manage", defaults={"name": "Unrelated changed"}
            )
            get_user_model().objects.filter(pk=other.id).update(is_active=False)
            if not hr_first:
                held.set()
                assert release.wait(5)

    with ThreadPoolExecutor(max_workers=1) as pool:
        if hr_first:
            with hr_operation(context, ["hr.department.manage", "hr.department.view"]) as operation:
                operation.authorize()
                future = pool.submit(_worker, connection.alias, writer)
                future.result(timeout=1.5)
                assert (
                    create_department(context, code="UNRELATED", name="No global gate").revision
                    == 1
                )
            return
        future = pool.submit(_worker, connection.alias, writer)
        try:
            assert held.wait(5)
            assert create_department(context, code="UNRELATED", name="No global gate").revision == 1
        finally:
            release.set()
            future.result(timeout=5)


def test_actual_orm_nowait_can_wait_for_implicit_relation_lock_negative_control(admission_world):
    connection = _postgresql()
    context, _, _ = admission_world
    ready, pids = Event(), []

    def reader():
        with transaction.atomic(using=connection.alias):
            return (
                get_user_model().objects.select_for_update(nowait=True).get(pk=context.actor_id).id
            )

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(using=connection.alias), connection.cursor() as cursor:
            cursor.execute("LOCK TABLE public.identity_user IN EXCLUSIVE MODE")
            future = pool.submit(_worker, connection.alias, reader, ready, pids)
            assert ready.wait(5)
            _observe_wait(connection, pids[0])
        assert future.result(timeout=5) == context.actor_id


def test_role_share_readers_are_compatible_without_bypassing_company_serialization(admission_world):
    connection = _postgresql()
    _, role, _ = admission_world
    barrier = Barrier(2)

    def reader():
        with (
            transaction.atomic(using=connection.alias),
            connections[connection.alias].cursor() as cursor,
        ):
            cursor.execute(
                "SELECT id FROM public.access_role WHERE id=%s FOR SHARE NOWAIT", [role.id]
            )
            assert cursor.fetchone()[0] == role.id
            # Both transactions actually hold this same row's compatible lock
            # before either releases it. This is a primitive proof, not a public
            # HR bypass of the Company mutex (proved by public domain races).
            barrier.wait(timeout=5)
        return True

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_worker, connection.alias, reader)
        second = pool.submit(_worker, connection.alias, reader)
        assert first.result(timeout=5) and second.result(timeout=5)


def test_actual_hr_admission_rejects_nested_alias_switch_before_sql(admission_world):
    from businessos.core.database import database_execution

    context, _, _ = admission_world
    selected = current_database_alias()
    connection = connections[selected]
    alternate = "hr_rejected_nested_alias"
    connections.databases[alternate] = dict(connection.settings_dict)
    statements = []

    def capture(execute, sql, params, many, execution_context):
        statements.append(sql)
        return execute(sql, params, many, execution_context)

    try:
        with hr_operation(context, [VIEW]) as operation:
            operation.authorize()
            with connection.execute_wrapper(capture):
                with pytest.raises(ValueError, match="Cannot switch databases"):
                    with database_execution(alternate):
                        pytest.fail("Cross-alias HR nesting entered")
            assert statements == []
            assert current_database_alias() == selected
    finally:
        connections[alternate].close()
        del connections[alternate]
        del connections.databases[alternate]
