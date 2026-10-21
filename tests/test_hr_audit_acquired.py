"""HR1-AUD-003: declared identities are not acquired transaction locks."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Event
from uuid import uuid4

import pytest
from django.db import close_old_connections, connections, transaction

from businessos.core.access.models import Permission, Role, RolePermission, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import current_database_alias, database_execution
from businessos.modules.hr import admission as admission_module
from businessos.modules.hr import persistence, services
from businessos.modules.hr.admission import AdmissionError, hr_operation
from businessos.modules.hr.models import (
    Attendance,
    AttendanceRevision,
    Department,
    Employee,
    LeaveRequest,
    LeaveType,
)
from businessos.modules.hr.support import references
from tests import test_hr_services as _setup_fixtures

hr_context = _setup_fixtures.hr_context
hr_person = _setup_fixtures.hr_person

pytestmark = pytest.mark.django_db(transaction=True)
PERMISSIONS = ("hr.department.manage", "hr.department.view")


@pytest.fixture
def acquired_world(company, operator):
    role = Role.objects.create(company=company, code="AUD3", name="Acquired lock test")
    for code in PERMISSIONS:
        permission, _ = Permission.objects.get_or_create(code=code, defaults={"name": code})
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(company=company, user=operator, role=role)
    context = BusinessContext(actor_id=operator.pk, company_id=company.pk)
    target = services.create_department(context, code="AUD3", name="Original")
    return context, target


def test_declared_but_unacquired_target_cannot_enter_authority(acquired_world):
    context, target = acquired_world
    baseline = AuditEntry.objects.count()
    with pytest.raises(AdmissionError, match="unacquired"):
        with hr_operation(context, PERMISSIONS, anchors=[("hr.department", target.id)]) as op:
            op.authorize()
            services.update_department(
                context,
                department_id=target.id,
                expected_revision=1,
                name="Unprotected late effect",
                is_active=True,
            )
    assert Department.objects.get(pk=target.id).name == "Original"
    assert AuditEntry.objects.count() == baseline


def test_caught_incomplete_authority_cannot_reuse_partial_acquisition(acquired_world):
    context, target = acquired_world
    baseline = AuditEntry.objects.count()
    with pytest.raises(AdmissionError, match="identity coverage"):
        with hr_operation(context, PERMISSIONS) as op:
            op.lock_rows(Department, [target.id])
            try:
                op.authorize(user_ids=[uuid4()])
            except AdmissionError:
                pass
            assert not op.admitted and not op.user_ids
            op.authorize()
    assert not op.acquired_anchors and not op.user_ids
    assert not op.role_ids and not op.permission_ids
    assert AuditEntry.objects.count() == baseline


def test_proper_prelock_protects_nested_update_and_keeps_native_final_guards(
    acquired_world, monkeypatch
):
    context, target = acquired_world
    connection = connections[current_database_alias()]
    statements = []
    guards = []
    native_guard = admission_module.require_final_permission

    def capture(execute, sql, params, many, execution_context):
        statements.append(sql)
        return execute(sql, params, many, execution_context)

    def final_guard(supplied, code):
        guards.append((supplied, code))
        return native_guard(supplied, code)

    monkeypatch.setattr(admission_module, "require_final_permission", final_guard)
    with connection.execute_wrapper(capture):
        with hr_operation(context, PERMISSIONS, anchors=[("hr.department", target.id)]) as op:
            row = op.lock_rows(Department, [target.id])[0]
            assert row.pk == target.id
            assert ("hr.department", target.id) in op.acquired_anchors
            op.authorize()
            changed = services.update_department(
                context,
                department_id=target.id,
                expected_revision=1,
                name="Protected nested update",
                is_active=True,
            )
            same = services.update_department(
                context,
                department_id=target.id,
                expected_revision=2,
                name="Protected nested update",
                is_active=True,
            )
    assert changed.revision == same.revision == 2
    assert {code for supplied, code in guards if supplied == context} == set(PERMISSIONS)
    assert len(guards) >= 6  # Outer authority and every nested successful return recheck.
    assert Department.objects.get(pk=target.id).name == "Protected nested update"
    assert AuditEntry.objects.filter(action="hr.department.updated").count() == 1
    if connection.vendor == "postgresql":
        target_locks = [
            index
            for index, sql in enumerate(statements)
            if 'FROM "hr_department"' in sql and "FOR UPDATE" in sql
        ]
        authority = next(
            index
            for index, sql in enumerate(statements)
            if 'LOCK TABLE "public"."identity_user" IN ROW SHARE MODE NOWAIT' in sql
        )
        assert target_locks and all(index < authority for index in target_locks)
    assert op.finished and not op.acquired_anchors


def test_held_unacquired_target_rejects_before_domain_sql_or_authority(acquired_world):
    context, target = acquired_world
    alias = current_database_alias()
    connection = connections[alias]
    if connection.vendor != "postgresql":
        pytest.skip("Real independently held domain-row locks require PostgreSQL")
    ready, release = Event(), Event()
    holder_pid = []
    statements = []
    before = AuditEntry.objects.count()

    def hold_target():
        close_old_connections()
        worker = connections[alias]
        try:
            with database_execution(alias), transaction.atomic(using=alias):
                Department.objects.using(alias).select_for_update(of=("self",)).get(pk=target.id)
                with worker.cursor() as cursor:
                    cursor.execute("SELECT pg_catalog.pg_backend_pid()")
                    holder_pid.append(cursor.fetchone()[0])
                ready.set()
                assert release.wait(15), "Held-target regression was not released"
        finally:
            worker.close()

    def capture(execute, sql, params, many, execution_context):
        statements.append(sql)
        return execute(sql, params, many, execution_context)

    with ThreadPoolExecutor(max_workers=1) as pool:
        held = pool.submit(hold_target)
        try:
            assert ready.wait(10), "Independent holder did not lock Department"
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT state FROM pg_catalog.pg_stat_activity WHERE pid=%s",
                    [holder_pid[0]],
                )
                assert cursor.fetchone()[0] == "idle in transaction"
                cursor.execute(
                    "SELECT COUNT(*) FROM pg_catalog.pg_locks "
                    "WHERE pid=%s AND relation='public.hr_department'::regclass "
                    "AND mode='RowShareLock' AND granted",
                    [holder_pid[0]],
                )
                assert cursor.fetchone()[0] == 1
            with connection.execute_wrapper(capture):
                with pytest.raises(AdmissionError, match="unacquired"):
                    with hr_operation(
                        context, PERMISSIONS, anchors=[("hr.department", target.id)]
                    ) as op:
                        op.authorize()
                        services.update_department(
                            context,
                            department_id=target.id,
                            expected_revision=1,
                            name="Must never wait for held target",
                            is_active=True,
                        )
            assert not any('FROM "hr_department"' in sql for sql in statements)
            assert not any("IN ROW SHARE MODE NOWAIT" in sql for sql in statements)
        finally:
            release.set()
            held.result(timeout=10)
    assert Department.objects.get(pk=target.id).name == "Original"
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("rollback", [False, True], ids=["committed", "rolled-back"])
def test_finished_acquisition_evidence_cannot_be_reused(acquired_world, rollback):
    context, target = acquired_world
    connection = connections[current_database_alias()]
    try:
        with hr_operation(context, PERMISSIONS) as old:
            old.lock_rows(Department, [target.id])
            old.authorize()
            if rollback:
                raise ValueError("Synthetic outer rollback")
    except ValueError:
        assert rollback
    assert old.finished and not old.acquired_anchors
    statements = []

    def capture(execute, sql, params, many, execution_context):
        statements.append(sql)
        return execute(sql, params, many, execution_context)

    with connection.execute_wrapper(capture):
        with pytest.raises(AdmissionError, match="no longer belongs"):
            old.lock_rows(Department, [target.id])
        with pytest.raises(AdmissionError, match="no longer belongs"):
            old.authorize()
    assert not statements
    with hr_operation(context, PERMISSIONS) as fresh:
        assert fresh is not old and not fresh.acquired_anchors
        fresh.authorize()


def test_foreign_connection_cannot_reuse_live_acquisition_evidence(acquired_world):
    context, target = acquired_world
    alias = current_database_alias()

    def foreign_connection(old):
        close_old_connections()
        worker = connections[alias]
        try:
            assert worker is not old.connection
            with pytest.raises(AdmissionError, match="no longer belongs"):
                old.lock_rows(Department, [target.id])
        finally:
            worker.close()

    with hr_operation(context, PERMISSIONS) as op:
        op.lock_rows(Department, [target.id])
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(foreign_connection, op).result(timeout=10)
        op.authorize()


@pytest.mark.parametrize("after_authority", [False, True])
def test_savepoint_cannot_create_or_reuse_acquisition_evidence(acquired_world, after_authority):
    context, target = acquired_world
    connection = connections[current_database_alias()]
    before = AuditEntry.objects.count()
    with pytest.raises(AdmissionError):
        with hr_operation(context, PERMISSIONS) as op:
            if after_authority:
                op.lock_rows(Department, [target.id])
                op.authorize()
                services.create_department(context, code="SAVEPOINT-PRIOR", name="Roll back")
            try:
                with transaction.atomic(using=connection.alias):
                    op.lock_rows(Department, [target.id])
                    raise ValueError("The temporary savepoint must not retain a lock receipt")
            except (AdmissionError, ValueError):
                pass
            if not after_authority:
                op.authorize()
    assert AuditEntry.objects.count() == before
    assert not Department.objects.filter(code="SAVEPOINT-PRIOR").exists()


def test_caught_new_target_refusal_rolls_back_prior_registered_insert(acquired_world):
    context, target = acquired_world
    before = AuditEntry.objects.count()
    with pytest.raises(AdmissionError):
        with hr_operation(context, PERMISSIONS) as op:
            op.authorize()
            prior = services.create_department(context, code="REGISTERED-PRIOR", name="Roll back")
            assert ("hr.department", prior.id) in op.acquired_anchors
            try:
                services.update_department(
                    context,
                    department_id=target.id,
                    expected_revision=1,
                    name="No new blocking lock",
                    is_active=True,
                )
            except AdmissionError:
                pass
    assert Department.objects.get(pk=target.id).name == "Original"
    assert not Department.objects.filter(code="REGISTERED-PRIOR").exists()
    assert AuditEntry.objects.count() == before


def test_new_attendance_reservation_is_not_an_acquired_existing_anchor(acquired_world):
    context, _ = acquired_world
    identity = uuid4()
    with hr_operation(context, PERMISSIONS) as op:
        op.reserve_attendance(identity)
        assert ("hr.attendance", identity) in op.anchors
        assert identity in op.reserved_attendance_ids
        assert ("hr.attendance", identity) not in op.acquired_anchors
        op.authorize()
    assert not op.acquired_anchors and not op.reserved_attendance_ids


def test_selected_alias_prelock_nested_update_and_expired_evidence_default_cursor_trap(
    acquired_world, django_db_blocker, monkeypatch
):
    context, target = acquired_world
    default = connections["default"]
    alias = "hr_audit_acquired_selected"
    config = dict(default.settings_dict)
    config["TEST"] = dict(config.get("TEST", {}))
    connections.databases[alias] = config

    def forbidden_default(*args, **kwargs):
        pytest.fail("Selected-alias domain protection touched the default cursor")

    try:
        with django_db_blocker.unblock(), monkeypatch.context() as patched:
            patched.setattr(default, "cursor", forbidden_default)
            with database_execution(alias):
                with hr_operation(context, PERMISSIONS) as op:
                    op.lock_rows(Department, [target.id])
                    op.authorize()
                    changed = services.update_department(
                        context,
                        department_id=target.id,
                        expected_revision=1,
                        name="Selected protected update",
                        is_active=True,
                    )
                assert op.alias == alias and changed.revision == 2
            with pytest.raises(AdmissionError, match="no longer belongs"):
                op.lock_rows(Department, [target.id])
        assert Department.objects.get(pk=target.id).name == "Selected protected update"
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]


def test_plain_existing_row_cannot_be_registered_as_freshly_inserted(acquired_world):
    context, target = acquired_world
    connection = connections[current_database_alias()]
    before = AuditEntry.objects.count()
    statements = []

    def capture(execute, sql, params, many, execution_context):
        statements.append(sql)
        return execute(sql, params, many, execution_context)

    with pytest.raises(AdmissionError):
        with hr_operation(context, PERMISSIONS) as op:
            op.authorize()
            services.create_department(context, code="REGISTRATION-PRIOR", name="Must roll back")
            existing = Department.objects.using(op.alias).get(pk=target.id)
            assert ("hr.department", existing.pk) not in op.acquired_anchors
            try:
                with connection.execute_wrapper(capture):
                    op.register_created_row(existing)
            except AdmissionError:
                pass
    assert not statements  # Registration must reject before any target/authority SQL.
    assert Department.objects.get(pk=target.id).name == "Original"
    assert not Department.objects.filter(code="REGISTRATION-PRIOR").exists()
    assert AuditEntry.objects.count() == before


def test_pending_attendance_cannot_be_completed_without_actual_initial_revision_insert(
    hr_context, hr_person
):
    from businessos.modules.hr.manifest import HR_PERMISSION_DECLARATIONS

    employee = services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="PENDING-COMPLETE",
        joining_date=date(2020, 1, 1),
    )
    alias = current_database_alias()
    connection = connections[alias]

    def native_state():
        return tuple(
            tuple(model.objects.using(alias).order_by("pk").values())
            for model in (
                Department,
                Employee,
                Attendance,
                AttendanceRevision,
                LeaveType,
                LeaveRequest,
                AuditEntry,
            )
        )

    def session_settings():
        if connection.vendor != "postgresql":
            return None
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT current_setting('statement_timeout'), "
                "current_setting('lock_timeout'), "
                "current_setting('idle_in_transaction_session_timeout'), "
                "current_setting('transaction_isolation'), pg_backend_pid()"
            )
            return cursor.fetchone()

    before = native_state()
    original_settings = session_settings()
    raw_connection = connection.connection
    op = parent = prior = inner_error = None
    reached_completion = False
    permissions = tuple(code for code, _ in HR_PERMISSION_DECLARATIONS)
    try:
        with pytest.raises(AdmissionError, match="no complete initial revision"):
            with hr_operation(hr_context, permissions) as op:
                op.lock_rows(Employee, [employee.id])
                references(op, party_ids=[hr_person.pk])
                new_id = uuid4()
                op.reserve_attendance(new_id)
                op.authorize()
                prior = services.create_department(
                    hr_context, code="PENDING-PRIOR", name="Must roll back"
                )
                assert (
                    Department.objects.using(alias)
                    .filter(pk=prior.id, company_id=hr_context.company_id, code="PENDING-PRIOR")
                    .exists()
                )
                assert (
                    AuditEntry.objects.using(alias)
                    .filter(
                        company_id=hr_context.company_id,
                        actor_id=hr_context.actor_id,
                        action="hr.department.created",
                        object_type="hr.Department",
                        object_id=str(prior.id),
                        metadata={"revision": 1},
                    )
                    .exists()
                )
                parent = persistence._create_attendance(
                    attendance_id=new_id,
                    company_id=hr_context.company_id,
                    employee_id=employee.id,
                    branch_id=None,
                    timezone_name=op.company.timezone,
                    record_request_key=uuid4(),
                    recorded_by_id=hr_context.actor_id,
                )
                assert op.alias == alias and op.connection is connection
                assert connection.connection is raw_connection
                assert not parent._state.adding and parent._state.db == alias
                assert (
                    Attendance.objects.using(alias)
                    .filter(
                        pk=parent.pk,
                        company_id=hr_context.company_id,
                        employee_id=employee.id,
                    )
                    .exists()
                )
                assert parent.pk in op.pending_attendance_ids
                assert ("hr.attendance", parent.pk) in op.acquired_anchors
                assert (
                    not AttendanceRevision.objects.using(alias)
                    .filter(attendance_id=parent.pk)
                    .exists()
                )
                reached_completion = True
                with pytest.raises(
                    AdmissionError, match="initial revision has no pending"
                ) as invalid:
                    op.complete_attendance_creation(parent.pk)
                inner_error = invalid.value
                assert op.poisoned is inner_error
                assert connection.needs_rollback
                assert transaction.get_rollback(using=alias)
                # No SQL after catching the refusal in the poisoned outer unit.
    finally:
        # This executes even for an unexpected earlier failure, but only AFTER
        # the real owning boundary has completed its rollback. Never query an
        # aborted PostgreSQL transaction to manufacture successful readback.
        assert current_database_alias() == alias
        assert admission_module._CURRENT.get() is None
        assert not connection.in_atomic_block and not connection.needs_rollback
        assert connection.get_autocommit() and not connection.savepoint_ids
        assert connection.connection is raw_connection
        if connection.vendor == "postgresql":
            assert raw_connection.info.transaction_status.name == "IDLE"
        if op is not None:
            assert op.finished
        after = native_state()
        restored_settings = session_settings()
        print(
            "HR1_PENDING_ROLLBACK "
            + json.dumps(
                {
                    "alias": alias,
                    "post_parent_pre_completion_reached": reached_completion,
                    "intended_error": type(inner_error).__name__ if inner_error else None,
                    "native_baseline_restored": after == before,
                    "session_settings_restored": restored_settings == original_settings,
                    "autocommit": connection.get_autocommit(),
                    "needs_rollback": connection.needs_rollback,
                }
            )
        )
        assert after == before
        assert restored_settings == original_settings
    assert reached_completion and parent is not None and prior is not None
    assert inner_error is not None
