"""Real public HR domain races, with observed PostgreSQL Company-lock waits."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, date, datetime
from threading import Event
from time import monotonic
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connections, transaction

from businessos.core.access import services as access_services
from businessos.core.access.models import Permission, UserCompanyAccess, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import current_database_alias, database_execution
from businessos.core.organization.models import Company
from businessos.modules.hr import services
from businessos.modules.hr.admission import AuthorityBusy
from businessos.modules.hr.models import Attendance, AttendanceRevision, Employee, LeaveRequest
from businessos.modules.hr.services import attendance, leave

pytest_plugins = ("tests.test_hr_services",)
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def race_employee(hr_context, hr_person):
    if connections[current_database_alias()].vendor != "postgresql":
        pytest.skip("PostgreSQL-only actual HR domain row-lock concurrency oracle.")
    return services.create_employee(
        hr_context, party_id=hr_person.id, employee_number="RACE", joining_date=date(2020, 1, 1)
    )


def _worker(alias, operation, pids):
    try:
        with database_execution(alias):
            with connections[alias].cursor() as cursor:
                cursor.execute("SET statement_timeout='10s'")
                cursor.execute("SELECT pg_backend_pid()")
                pids.append(cursor.fetchone()[0])
            return operation()
    finally:
        connections[alias].close()


def _race(monkeypatch, module, action, winner, loser, *, loser_fails=True):
    """Hold a real completed winner effect before commit; observe the actual wait."""
    alias = current_database_alias()
    held, release = Event(), Event()
    winner_pids, loser_pids = [], []
    original = module.audit

    def hold(*args, **kwargs):
        original(*args, **kwargs)
        if args[2] == action:
            held.set()
            assert release.wait(5), "Controller did not release the completed winner"

    monkeypatch.setattr(module, "audit", hold)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_worker, alias, winner, winner_pids)
        try:
            assert held.wait(5), "Winner did not reach its actual persisted effect/Audit"
            other = pool.submit(_worker, alias, loser, loser_pids)
            deadline = monotonic() + 1.5
            with connections[alias].cursor() as cursor:
                while monotonic() < deadline:
                    if loser_pids:
                        cursor.execute(
                            "SELECT %s=ANY(pg_blocking_pids(%s))",
                            [winner_pids[0], loser_pids[0]],
                        )
                        if cursor.fetchone()[0]:
                            break
                    Event().wait(0.01)
                else:
                    pytest.fail("Loser was not observed waiting on the real HR winner")
        finally:
            release.set()
        first_result = first.result(timeout=5)
        if loser_fails:
            with pytest.raises(ValidationError):
                other.result(timeout=5)
            return first_result, None
        return first_result, other.result(timeout=5)


def _record(context, employee):
    return services.record_attendance(
        context,
        employee_id=employee.id,
        request_key=uuid4(),
        start_at=datetime(2024, 1, 2, 9, tzinfo=UTC),
        end_at=datetime(2024, 1, 2, 10, tzinfo=UTC),
    )


@pytest.mark.parametrize("end_first", [False, True])
def test_employment_end_vs_record_both_real_winner_orders(
    hr_context, race_employee, monkeypatch, end_first
):
    def ending():
        return services.end_employee(
            hr_context,
            employee_id=race_employee.id,
            expected_revision=1,
            leaving_date=date(2024, 1, 1),
        )

    def recording():
        return _record(hr_context, race_employee)

    _race(
        monkeypatch,
        services if end_first else attendance,
        "hr.employee.ended" if end_first else "hr.attendance.recorded",
        ending if end_first else recording,
        recording if end_first else ending,
    )
    assert Employee.objects.get(pk=race_employee.id).status == ("ENDED" if end_first else "ACTIVE")
    assert Attendance.objects.count() == (0 if end_first else 1)
    assert AttendanceRevision.objects.count() == (0 if end_first else 1)
    assert AuditEntry.objects.filter(action="hr.employee.ended").count() == int(end_first)
    assert AuditEntry.objects.filter(action="hr.attendance.recorded").count() == int(not end_first)


@pytest.mark.parametrize("transfer_first", [False, True])
def test_branch_transfer_vs_record_preserves_winning_snapshot(
    hr_context, race_employee, branch, monkeypatch, transfer_first
):
    def transferring():
        return services.transfer_employee_branch(
            hr_context,
            employee_id=race_employee.id,
            expected_revision=1,
            branch_id=branch.id,
        )

    def recording():
        return _record(hr_context, race_employee)

    _race(
        monkeypatch,
        services if transfer_first else attendance,
        "hr.employee.branch_changed" if transfer_first else "hr.attendance.recorded",
        transferring if transfer_first else recording,
        recording if transfer_first else transferring,
        loser_fails=False,
    )
    assert Employee.objects.get(pk=race_employee.id).branch_id == branch.id
    assert Attendance.objects.get().branch_id == (branch.id if transfer_first else None)
    assert AttendanceRevision.objects.count() == 1
    assert AuditEntry.objects.filter(action="hr.employee.branch_changed").count() == 1
    assert AuditEntry.objects.filter(action="hr.attendance.recorded").count() == 1


def test_concurrent_overlapping_records_have_one_effect(hr_context, race_employee, monkeypatch):
    _race(
        monkeypatch,
        attendance,
        "hr.attendance.recorded",
        lambda: _record(hr_context, race_employee),
        lambda: _record(hr_context, race_employee),
    )
    assert Attendance.objects.count() == AttendanceRevision.objects.count() == 1
    assert AuditEntry.objects.filter(action="hr.attendance.recorded").count() == 1


@pytest.mark.parametrize("longer_first", [False, True])
def test_two_corrections_same_expected_revision_have_one_effect(
    hr_context, race_employee, monkeypatch, longer_first
):
    original = _record(hr_context, race_employee)

    def correct(hour):
        return services.revise_attendance(
            hr_context,
            attendance_id=original.attendance.id,
            expected_revision=1,
            request_key=uuid4(),
            operation="CORRECT",
            start_at=datetime(2024, 1, 2, 9, tzinfo=UTC),
            end_at=datetime(2024, 1, 2, hour, tzinfo=UTC),
            reason="Synthetic correction",
        )

    winner_hour, loser_hour = (12, 11) if longer_first else (11, 12)
    _race(
        monkeypatch,
        attendance,
        "hr.attendance.corrected",
        lambda: correct(winner_hour),
        lambda: correct(loser_hour),
    )
    assert AttendanceRevision.objects.count() == 2
    assert AttendanceRevision.objects.get(number=2).end_at.hour == winner_hour
    assert AuditEntry.objects.filter(action="hr.attendance.corrected").count() == 1


@pytest.mark.parametrize("approval_first", [False, True])
def test_leave_approval_vs_attendance_both_real_winner_orders(
    hr_context, race_employee, monkeypatch, approval_first
):
    approver = get_user_model().objects.create_user("hr-race-approver@example.com", "test")
    UserCompanyAccess.objects.create(user=approver, company_id=hr_context.company_id)
    role_id = UserRoleAssignment.objects.get(user_id=hr_context.actor_id).role_id
    UserRoleAssignment.objects.create(
        user=approver, company_id=hr_context.company_id, role_id=role_id
    )
    approval_context = BusinessContext(actor_id=approver.id, company_id=hr_context.company_id)
    leave_type = services.create_leave_type(hr_context, code="RACE", name="Synthetic Leave")
    draft = services.create_leave(
        hr_context,
        employee_id=race_employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 2),
    )
    services.submit_leave(
        hr_context, leave_id=draft.leave.id, expected_revision=1, request_key=uuid4()
    )

    def approving():
        return services.decide_leave(
            approval_context,
            leave_id=draft.leave.id,
            expected_revision=2,
            request_key=uuid4(),
            decision="APPROVED",
        )

    def recording():
        return _record(hr_context, race_employee)

    _race(
        monkeypatch,
        leave if approval_first else attendance,
        "hr.leave.approved" if approval_first else "hr.attendance.recorded",
        approving if approval_first else recording,
        recording if approval_first else approving,
    )
    stored = LeaveRequest.objects.get(pk=draft.leave.id)
    assert stored.status == ("APPROVED" if approval_first else "SUBMITTED")
    assert (stored.decision_key is not None) == approval_first
    assert Attendance.objects.count() == (0 if approval_first else 1)
    assert AttendanceRevision.objects.count() == (0 if approval_first else 1)
    assert AuditEntry.objects.filter(action="hr.leave.approved").count() == int(approval_first)
    assert AuditEntry.objects.filter(action="hr.attendance.recorded").count() == int(
        not approval_first
    )


@contextmanager
def _held_user_row(user_id):
    alias = current_database_alias()
    held, release = Event(), Event()

    def locker():
        with transaction.atomic(using=alias):
            get_user_model().objects.select_for_update().get(pk=user_id)
            held.set()
            assert release.wait(5)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_worker, alias, locker, [])
        try:
            assert held.wait(5)
            yield
        finally:
            release.set()
            future.result(timeout=5)


def _linked_user(context, email):
    user = get_user_model().objects.create_user(email, "synthetic-only")
    UserCompanyAccess.objects.create(user=user, company_id=context.company_id)
    return user


@pytest.mark.parametrize("clear", [False, True])
def test_inactive_removed_user_lock_does_not_block_public_unlink_or_relink(
    hr_context, race_employee, clear
):
    old = _linked_user(hr_context, "hr-old-link@example.test")
    new = _linked_user(hr_context, "hr-new-link@example.test")
    services.update_employee(
        hr_context, employee_id=race_employee.id, expected_revision=1, user_id=old.id
    )
    old.is_active = False
    old.save(update_fields=["is_active"])
    with _held_user_row(old.id):
        result = services.update_employee(
            hr_context,
            employee_id=race_employee.id,
            expected_revision=2,
            user_id=None if clear else new.id,
        )
    assert result.user_id == (None if clear else new.id)
    assert Employee.objects.get(pk=race_employee.id).revision == 3
    assert AuditEntry.objects.filter(action="hr.employee.updated").count() == 2


def test_public_relink_writer_first_deactivation_is_busy_then_currently_ineligible(
    hr_context, race_employee
):
    target = _linked_user(hr_context, "hr-deactivating-link@example.test")
    alias = current_database_alias()
    held, release = Event(), Event()

    def writer():
        with transaction.atomic(using=alias):
            get_user_model().objects.filter(pk=target.id).update(is_active=False)
            held.set()
            assert release.wait(5)

    baseline = AuditEntry.objects.count()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_worker, alias, writer, [])
        try:
            assert held.wait(5)
            with pytest.raises(AuthorityBusy):
                services.update_employee(
                    hr_context,
                    employee_id=race_employee.id,
                    expected_revision=1,
                    user_id=target.id,
                )
        finally:
            release.set()
            future.result(timeout=5)
    with pytest.raises(ValidationError, match="active Company-eligible"):
        services.update_employee(
            hr_context,
            employee_id=race_employee.id,
            expected_revision=1,
            user_id=target.id,
        )
    assert Employee.objects.get(pk=race_employee.id).user_id is None
    assert Employee.objects.get(pk=race_employee.id).revision == 1
    assert AuditEntry.objects.count() == baseline


def test_public_relink_hr_first_deactivation_waits_then_retains_identity(
    hr_context, race_employee, monkeypatch
):
    target = _linked_user(hr_context, "hr-protected-new-link@example.test")
    _race(
        monkeypatch,
        services,
        "hr.employee.updated",
        lambda: services.update_employee(
            hr_context,
            employee_id=race_employee.id,
            expected_revision=1,
            user_id=target.id,
        ),
        lambda: get_user_model().objects.filter(pk=target.id).update(is_active=False),
        loser_fails=False,
    )
    assert not get_user_model().objects.get(pk=target.id).is_active
    assert Employee.objects.get(pk=race_employee.id).user_id == target.id
    assert Employee.objects.get(pk=race_employee.id).revision == 2
    assert AuditEntry.objects.filter(action="hr.employee.updated").count() == 1


def _revoker(context):
    for code in (access_services.MANAGE_ORGANIZATIONAL_ACCESS, access_services.MANAGE_ROLES):
        Permission.objects.get_or_create(code=code, defaults={"name": code})
    admin = get_user_model().objects.create_superuser("hr-revoker@example.test", "synthetic-only")
    return BusinessContext(actor_id=admin.id, company_id=context.company_id)


def test_hr_first_company_access_revoker_waits_until_valid_effect_commits(
    hr_context, race_employee, monkeypatch
):
    admin = _revoker(hr_context)
    _race(
        monkeypatch,
        services,
        "hr.department.created",
        lambda: services.create_department(hr_context, code="BEFORE_REVOKE", name="Valid winner"),
        lambda: access_services.revoke_company_access(admin, user_id=hr_context.actor_id),
        loser_fails=False,
    )
    assert AuditEntry.objects.filter(action="hr.department.created").count() == 1
    assert not UserCompanyAccess.objects.filter(
        user_id=hr_context.actor_id, company_id=hr_context.company_id
    ).exists()
    with pytest.raises(PermissionDenied):
        services.create_department(hr_context, code="AFTER_REVOKE", name="Must deny")


@pytest.mark.parametrize("revocation", ["company", "permission"])
def test_historical_correction_retry_ignores_inactive_provenance_but_rechecks_current_revocation(
    hr_context, race_employee, revocation
):
    original = _record(hr_context, race_employee)
    corrector = _linked_user(hr_context, "hr-corrector@example.test")
    role_id = UserRoleAssignment.objects.get(user_id=hr_context.actor_id).role_id
    UserRoleAssignment.objects.create(
        user=corrector, company_id=hr_context.company_id, role_id=role_id
    )
    current = BusinessContext(actor_id=corrector.id, company_id=hr_context.company_id)
    key = uuid4()
    payload = dict(
        attendance_id=original.attendance.id,
        expected_revision=1,
        request_key=key,
        operation="CORRECT",
        start_at=datetime(2024, 1, 2, 9, tzinfo=UTC),
        end_at=datetime(2024, 1, 2, 11, tzinfo=UTC),
        reason="Retained correction",
    )
    services.revise_attendance(current, **payload)
    services.revise_attendance(
        current,
        attendance_id=original.attendance.id,
        expected_revision=2,
        request_key=uuid4(),
        operation="VOID",
        reason="Later state",
    )
    get_user_model().objects.filter(pk=hr_context.actor_id).update(is_active=False)
    with _held_user_row(hr_context.actor_id):
        retry = services.revise_attendance(current, **payload)
    assert retry.historical_retry and retry.receipt.number == 2 and retry.current.number == 3
    assert retry.current.effect == "VOIDED"
    baseline = AuditEntry.objects.filter(action__startswith="hr.").count()
    admin = _revoker(hr_context)
    alias = current_database_alias()
    pids = []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(using=alias):
            Company.objects.select_for_update().get(pk=hr_context.company_id)
            future = pool.submit(
                _worker, alias, lambda: services.revise_attendance(current, **payload), pids
            )
            deadline = monotonic() + 1.5
            with connections[alias].cursor() as cursor:
                while monotonic() < deadline:
                    if pids:
                        cursor.execute(
                            "SELECT pg_backend_pid()=ANY(pg_blocking_pids(%s))", [pids[0]]
                        )
                        if cursor.fetchone()[0]:
                            break
                    Event().wait(0.01)
                else:
                    pytest.fail("Historical retry did not wait on the revoker's Company lock")
            if revocation == "company":
                access_services.revoke_company_access(admin, user_id=corrector.id)
            else:
                access_services.revoke_role_permission(
                    admin,
                    role_id=role_id,
                    permission_code="hr.attendance.correct",
                )
        with pytest.raises(PermissionDenied):
            future.result(timeout=5)
    assert AttendanceRevision.objects.count() == 3
    assert AuditEntry.objects.filter(action__startswith="hr.").count() == baseline
