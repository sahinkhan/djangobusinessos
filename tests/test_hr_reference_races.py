"""Supported owner-reference retirement races required by frozen HR section 14."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Event
from time import monotonic
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connections

from businessos.core.access.models import UserCompanyAccess
from businessos.core.audit.models import AuditEntry
from businessos.core.database import (
    business_atomic_context,
    current_database_alias,
    database_execution,
)
from businessos.core.organization.models import Branch
from businessos.modules.hr import selectors, services
from businessos.modules.hr.models import (
    Attendance,
    AttendanceRevision,
    Department,
    Employee,
    LeaveRequest,
    LeaveType,
)
from businessos.modules.hr.services import attendance, leave
from businessos.modules.party import services as party_services
from tests import test_hr_services as _fixtures

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)


def _postgresql():
    if connections[current_database_alias()].vendor != "postgresql":
        pytest.skip("PostgreSQL-only supported owner-reference retirement row-lock race.")


def _worker(alias, operation, pids):
    try:
        with database_execution(alias):
            with connections[alias].cursor() as cursor:
                cursor.execute("SET statement_timeout = '10s'")
                cursor.execute("SELECT pg_backend_pid()")
                pids.append(cursor.fetchone()[0])
            return operation()
    finally:
        connections[alias].close()


def _reference_race(monkeypatch, winner, loser, *, module=None, action=None, loser_fails=False):
    """Pause a supported owner's actual effect, then prove its competing row wait.

    External Party/Branch APIs do not offer an Audit callback. Their real call is
    enclosed in a test-owned transaction solely to retain its native locks until
    the controller observes blocking. HR winners retain their own admitted UOW:
    no unknown outer transaction or fabricated authorization is introduced.
    """
    alias = current_database_alias()
    held, release = Event(), Event()
    winner_pids, loser_pids = [], []

    if module is None:

        def held_winner():
            with business_atomic_context():
                result = winner()
                held.set()
                assert release.wait(5), "Controller did not release the native owner effect"
                return result

    else:
        original = module.audit

        def held_audit(*args, **kwargs):
            original(*args, **kwargs)
            if args[2] == action:
                held.set()
                assert release.wait(5), "Controller did not release the HR effect/Audit"

        monkeypatch.setattr(module, "audit", held_audit)
        held_winner = winner

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_worker, alias, held_winner, winner_pids)
        try:
            assert held.wait(5), "Winner did not persist its actual supported owner effect"
            second = pool.submit(_worker, alias, loser, loser_pids)
            deadline = monotonic() + 1.5
            with connections[alias].cursor() as cursor:
                while monotonic() < deadline:
                    if loser_pids:
                        cursor.execute(
                            "SELECT %s = ANY(pg_blocking_pids(%s))",
                            [winner_pids[0], loser_pids[0]],
                        )
                        if cursor.fetchone()[0]:
                            break
                    # Poll backoff only; success requires the real PostgreSQL
                    # blocker relation, never elapsed time or a guessed sleep.
                    Event().wait(0.01)
                else:
                    if second.done():
                        second.result()
                    pytest.fail("Competing operation never waited on the native winning owner")
        finally:
            release.set()
        result = first.result(timeout=5)
        if loser_fails:
            with pytest.raises(ValidationError):
                second.result(timeout=5)
        else:
            second.result(timeout=5)
        return result


def _employee(context, party, *, number="REFERENCE", **kwargs):
    return services.create_employee(
        context,
        party_id=party.pk,
        employee_number=number,
        joining_date=date(2020, 1, 1),
        **kwargs,
    )


@pytest.mark.parametrize("change", [{"is_active": False}, {"party_type": "organization"}])
@pytest.mark.parametrize("use", ["create", "associate"])
@pytest.mark.parametrize("retirement_first", [False, True])
def test_party_owner_retirement_vs_new_employee_or_association(
    hr_context, hr_person, monkeypatch, change, use, retirement_first
):
    _postgresql()
    employee = _employee(hr_context, hr_person) if use == "associate" else None
    user = get_user_model().objects.create_user("hr-reference-link@example.invalid", "synthetic")
    UserCompanyAccess.objects.create(user=user, company_id=hr_context.company_id)
    before = dict(Employee.objects.get(pk=employee.id).__dict__) if employee else None
    if before:
        before.pop("_state")
    before_audits = AuditEntry.objects.filter(action__startswith="hr.").count()

    def retire():
        return party_services.update_party(hr_context, party_id=hr_person.pk, **change)

    def new_use():
        if employee is None:
            return _employee(hr_context, hr_person)
        return services.update_employee(
            hr_context, employee_id=employee.id, expected_revision=1, user_id=user.pk
        )

    _reference_race(
        monkeypatch,
        retire if retirement_first else new_use,
        new_use if retirement_first else retire,
        module=None if retirement_first else services,
        action=f"hr.employee.{'created' if use == 'create' else 'updated'}",
        loser_fails=retirement_first,
    )
    hr_person.refresh_from_db()
    assert all(getattr(hr_person, field) == value for field, value in change.items())
    assert AuditEntry.objects.filter(action__startswith="hr.").count() == before_audits + int(
        not retirement_first
    )
    if retirement_first and employee is None:
        assert not Employee.objects.exists()
    elif retirement_first:
        stored = dict(Employee.objects.get(pk=employee.id).__dict__)
        stored.pop("_state")
        assert stored == before
    else:
        stored = Employee.objects.get()
        assert stored.party_id == hr_person.pk
        assert stored.user_id == (user.pk if use == "associate" else None)
        assert stored.revision == (2 if use == "associate" else 1)
        projected = selectors.employee_detail(hr_context, stored.pk)
        assert projected.party["is_active"] == hr_person.is_active
        assert projected.party["party_type"] == hr_person.party_type


@pytest.mark.parametrize("use", ["create", "assign"])
@pytest.mark.parametrize("retirement_first", [False, True])
def test_department_retirement_vs_active_assignment_keeps_exact_winner(
    hr_context, hr_person, monkeypatch, use, retirement_first
):
    _postgresql()
    department = services.create_department(hr_context, code="REF", name="Reference Department")
    employee = _employee(hr_context, hr_person) if use == "assign" else None

    def retire():
        return services.update_department(
            hr_context,
            department_id=department.id,
            expected_revision=1,
            name=department.name,
            is_active=False,
        )

    def assign():
        if employee is None:
            return _employee(hr_context, hr_person, department_id=department.id)
        return services.update_employee(
            hr_context, employee_id=employee.id, expected_revision=1, department_id=department.id
        )

    _reference_race(
        monkeypatch,
        retire if retirement_first else assign,
        assign if retirement_first else retire,
        module=services,
        action="hr.department.updated"
        if retirement_first
        else f"hr.employee.{'created' if use == 'create' else 'updated'}",
        loser_fails=True,
    )
    stored_department = Department.objects.get(pk=department.id)
    assert stored_department.is_active == (not retirement_first)
    assert stored_department.revision == (2 if retirement_first else 1)
    assert AuditEntry.objects.filter(action="hr.department.updated").count() == int(
        retirement_first
    )
    if retirement_first and employee is None:
        assert not Employee.objects.exists()
    else:
        stored = Employee.objects.get()
        assert stored.department_id == (None if retirement_first else department.id)
        assert stored.revision == (2 if use == "assign" and not retirement_first else 1)
        assert AuditEntry.objects.filter(action="hr.employee.updated").count() == int(
            use == "assign" and not retirement_first
        )
    assert AuditEntry.objects.filter(action="hr.employee.created").count() == (
        1 if use == "assign" or not retirement_first else 0
    )


@pytest.mark.parametrize("use", ["create", "submit"])
@pytest.mark.parametrize("retirement_first", [False, True])
def test_leave_type_retirement_vs_new_or_submitted_leave_preserves_facts(
    hr_context, hr_person, monkeypatch, use, retirement_first
):
    _postgresql()
    employee = _employee(hr_context, hr_person)
    leave_type = services.create_leave_type(hr_context, code="REF", name="Reference Leave")

    def create():
        return services.create_leave(
            hr_context,
            employee_id=employee.id,
            create_request_key=uuid4(),
            leave_type_id=leave_type.id,
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 2),
        )

    draft = create() if use == "submit" else None

    def retire():
        return services.update_leave_type(
            hr_context,
            leave_type_id=leave_type.id,
            expected_revision=1,
            name=leave_type.name,
            is_active=False,
        )

    def new_use():
        if draft is None:
            return create()
        return services.submit_leave(
            hr_context, leave_id=draft.leave.id, expected_revision=1, request_key=uuid4()
        )

    _reference_race(
        monkeypatch,
        retire if retirement_first else new_use,
        new_use if retirement_first else retire,
        module=services if retirement_first else leave,
        action="hr.leave_type.updated"
        if retirement_first
        else f"hr.leave.{'created' if use == 'create' else 'submitted'}",
        loser_fails=retirement_first,
    )
    assert LeaveType.objects.get(pk=leave_type.id).is_active is False
    assert AuditEntry.objects.filter(action="hr.leave_type.updated").count() == 1
    assert AuditEntry.objects.filter(action="hr.leave.created").count() == int(
        use == "submit" or not retirement_first
    )
    assert AuditEntry.objects.filter(action="hr.leave.submitted").count() == int(
        use == "submit" and not retirement_first
    )
    if retirement_first and draft is None:
        assert not LeaveRequest.objects.exists()
    else:
        stored = LeaveRequest.objects.get()
        assert stored.leave_type_id == leave_type.id
        assert stored.status == (
            "SUBMITTED" if use == "submit" and not retirement_first else "DRAFT"
        )
        assert stored.revision == (2 if stored.status == "SUBMITTED" else 1)
        assert (stored.submit_key is not None) == (stored.status == "SUBMITTED")
        projected = selectors.leave_detail(hr_context, stored.pk)
        assert projected.leave_type.is_active is False


@pytest.mark.parametrize("use", ["transfer", "record"])
@pytest.mark.parametrize("retirement_first", [False, True])
def test_validated_branch_retirement_vs_transfer_or_record_preserves_scope_snapshot(
    hr_context, hr_person, branch, monkeypatch, use, retirement_first
):
    _postgresql()
    employee = _employee(
        hr_context, hr_person, **({"branch_id": branch.pk} if use == "record" else {})
    )

    def retire():
        # This is the accepted Organization owner path, not an unsafe bulk update.
        current = Branch.objects.get(pk=branch.pk)
        current.is_active = False
        current.save(update_fields=["is_active", "updated_at"])
        return current

    def new_use():
        if use == "transfer":
            return services.transfer_employee_branch(
                hr_context, employee_id=employee.id, expected_revision=1, branch_id=branch.pk
            )
        return services.record_attendance(
            hr_context,
            employee_id=employee.id,
            request_key=uuid4(),
            start_at=datetime(2024, 1, 2, 9, tzinfo=UTC),
            end_at=datetime(2024, 1, 2, 10, tzinfo=UTC),
        )

    _reference_race(
        monkeypatch,
        retire if retirement_first else new_use,
        new_use if retirement_first else retire,
        module=None if retirement_first else services if use == "transfer" else attendance,
        action="hr.employee.branch_changed" if use == "transfer" else "hr.attendance.recorded",
        loser_fails=retirement_first,
    )
    assert Branch.objects.get(pk=branch.pk).is_active is False
    stored_employee = Employee.objects.get(pk=employee.id)
    if use == "transfer":
        assert stored_employee.branch_id == (None if retirement_first else branch.pk)
        assert stored_employee.revision == (1 if retirement_first else 2)
        assert AuditEntry.objects.filter(action="hr.employee.branch_changed").count() == int(
            not retirement_first
        )
    else:
        assert stored_employee.branch_id == branch.pk
        assert Attendance.objects.count() == int(not retirement_first)
        assert AttendanceRevision.objects.count() == int(not retirement_first)
        assert AuditEntry.objects.filter(action="hr.attendance.recorded").count() == int(
            not retirement_first
        )
        if not retirement_first:
            stored = Attendance.objects.get()
            assert stored.branch_id == branch.pk
            projected = selectors.attendance_detail(hr_context, stored.pk)
            assert projected.branch_id == branch.pk
