"""Remaining frozen section-14 domain races with actual PostgreSQL blockers."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Event
from time import monotonic
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connections

from businessos.core.access.models import UserCompanyAccess, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import current_database_alias
from businessos.modules.hr import services
from businessos.modules.hr.models import Attendance, AttendanceRevision, Employee, LeaveRequest
from businessos.modules.hr.services import attendance, leave
from tests import test_hr_services as _fixtures
from tests.test_hr_concurrency import _worker

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def _postgresql_only():
    if connections[current_database_alias()].vendor != "postgresql":
        pytest.skip("PostgreSQL-only frozen HR domain-race row-lock/blocker oracle.")


@pytest.fixture
def employee(hr_context, hr_person):
    return services.create_employee(
        hr_context, party_id=hr_person.pk, employee_number="DOMAIN", joining_date=date(2020, 1, 1)
    )


def _approver(context, suffix="one"):
    user = get_user_model().objects.create_user(f"domain-{suffix}@example.test", "synthetic-only")
    UserCompanyAccess.objects.create(user=user, company_id=context.company_id)
    role_id = UserRoleAssignment.objects.get(user_id=context.actor_id).role_id
    UserRoleAssignment.objects.create(user=user, company_id=context.company_id, role_id=role_id)
    return BusinessContext(actor_id=user.pk, company_id=context.company_id)


def _draft(context, employee, *, day=2):
    leave_type = services.create_leave_type(context, code=f"L-{uuid4().hex[:8]}", name="Synthetic")
    return services.create_leave(
        context,
        employee_id=employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2024, 1, day),
        end_date=date(2024, 1, day),
        reason="Synthetic domain-race request",
    )


def _submit(context, row):
    return services.submit_leave(
        context, leave_id=row.leave.id, expected_revision=1, request_key=uuid4()
    )


def _decide(context, row, decision="APPROVED"):
    return services.decide_leave(
        context,
        leave_id=row.leave.id,
        expected_revision=2,
        request_key=uuid4(),
        decision=decision,
        reason="Synthetic domain-race decision",
    )


def _record(context, employee, *, day=2, end_day=None):
    return services.record_attendance(
        context,
        employee_id=employee.id,
        request_key=uuid4(),
        start_at=datetime(2024, 1, day, 9, tzinfo=UTC),
        end_at=datetime(2024, 1, end_day or day, 10, tzinfo=UTC),
    )


def _audits():
    return Counter(
        AuditEntry.objects.filter(action__startswith="hr.").values_list("action", flat=True)
    )


def _delta(before):
    after = _audits()
    assert not before - after, "No historical Audit may disappear."
    return after - before


def _signal_or_worker_failure(signal, future, message):
    """Surface a real worker exception instead of hiding it behind an Event timeout."""
    deadline = monotonic() + 15
    while not signal.is_set():
        if future.done():
            future.result()  # Preserve the actual source exception and traceback.
            pytest.fail(message)
        remaining = deadline - monotonic()
        if remaining <= 0:
            if future.done():
                future.result()
            pytest.fail(message)
        signal.wait(min(remaining, 0.01))


def _observe_worker_blocked_by(alias, blocked_pids, blocker_pids, future):
    """The actual PostgreSQL blocker graph, never elapsed time, orders the race."""
    deadline = monotonic() + 1.5
    with connections[alias].cursor() as cursor:
        while monotonic() < deadline:
            if future.done():
                future.result()
                pytest.fail("The competing operation completed without its required row wait.")
            if blocked_pids:
                cursor.execute("SELECT pg_stat_clear_snapshot()")
                cursor.execute(
                    "SELECT %s=ANY(pg_blocking_pids(%s))", [blocker_pids[0], blocked_pids[0]]
                )
                if cursor.fetchone()[0]:
                    return
            Event().wait(0.01)
    if future.done():
        future.result()
    pytest.fail("The competing operation was not observed waiting on the real HR transaction.")


def _race(monkeypatch, module, action, winner, loser, *, loser_fails=True):
    """Hold a real winning effect/Audit; retain native failures on either worker."""
    alias = current_database_alias()
    held, release = Event(), Event()
    winner_pids, loser_pids = [], []
    original = module.audit

    def hold(*args, **kwargs):
        original(*args, **kwargs)
        if args[2] == action:
            held.set()
            assert release.wait(15), "Controller did not release the completed HR winner."

    monkeypatch.setattr(module, "audit", hold)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_worker, alias, winner, winner_pids)
        try:
            _signal_or_worker_failure(
                held, first, "Winner did not reach its persisted effect/Audit."
            )
            other = pool.submit(_worker, alias, loser, loser_pids)
            _observe_worker_blocked_by(alias, loser_pids, winner_pids, other)
        finally:
            release.set()
        first_result = first.result(timeout=15)
        if loser_fails:
            with pytest.raises(ValidationError):
                other.result(timeout=15)
            return first_result, None
        return first_result, other.result(timeout=15)


def _refused_approval_then_waiting_void(monkeypatch, approving, voiding):
    """An approval with an existing conflict cannot be manufactured as a winner."""
    alias = current_database_alias()
    held, release = Event(), Event()
    first_pids, second_pids = [], []
    original = leave.reject_attendance_overlap

    def before_conflict_check(*args, **kwargs):
        held.set()
        assert release.wait(15), "Controller did not release the approval's real conflict check."
        return original(*args, **kwargs)

    monkeypatch.setattr(leave, "reject_attendance_overlap", before_conflict_check)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(_worker, alias, approving, first_pids)
        try:
            _signal_or_worker_failure(
                held, first, "Approval did not reach its real conflict check."
            )
            second = pool.submit(_worker, alias, voiding, second_pids)
            _observe_worker_blocked_by(alias, second_pids, first_pids, second)
        finally:
            release.set()
        with pytest.raises(ValidationError, match="conflicts"):
            first.result(timeout=15)
        return second.result(timeout=15)


@pytest.mark.parametrize("transfer_first", [False, True])
def test_branch_transfer_vs_leave_create_freezes_the_committed_winning_assignment(
    hr_context, employee, branch, monkeypatch, transfer_first
):
    leave_type = services.create_leave_type(hr_context, code="TRANSFER", name="Synthetic")
    before = _audits()

    def transferring():
        return services.transfer_employee_branch(
            hr_context, employee_id=employee.id, expected_revision=1, branch_id=branch.pk
        )

    def creating():
        return services.create_leave(
            hr_context,
            employee_id=employee.id,
            create_request_key=uuid4(),
            leave_type_id=leave_type.id,
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 2),
        )

    _race(
        monkeypatch,
        services if transfer_first else leave,
        "hr.employee.branch_changed" if transfer_first else "hr.leave.created",
        transferring if transfer_first else creating,
        creating if transfer_first else transferring,
        loser_fails=False,
    )
    native = LeaveRequest.objects.get()
    assert native.branch_id == (branch.pk if transfer_first else None)
    assert native.status == "DRAFT" and native.revision == 1
    assert native.timezone == "UTC"
    assert Employee.objects.get(pk=employee.id).branch_id == branch.pk
    assert Employee.objects.get(pk=employee.id).revision == 2
    assert _delta(before) == {"hr.employee.branch_changed": 1, "hr.leave.created": 1}


@pytest.mark.parametrize("operation", ["CORRECT", "VOID", "REINSTATE"])
@pytest.mark.parametrize("approval_first", [False, True])
def test_attendance_revision_vs_approval_rechecks_current_effect_in_both_orders(
    hr_context, employee, monkeypatch, operation, approval_first
):
    approver = _approver(hr_context)
    record = _record(hr_context, employee, day=1 if operation == "CORRECT" else 2)
    expected = 1
    if operation == "REINSTATE":
        services.revise_attendance(
            hr_context,
            attendance_id=record.attendance.id,
            expected_revision=1,
            request_key=uuid4(),
            operation="VOID",
            reason="Initial synthetic void",
        )
        expected = 2
    draft = _draft(hr_context, employee)
    _submit(hr_context, draft)
    before = _audits()
    before_revisions = AttendanceRevision.objects.count()
    transition_key = uuid4()

    def revising():
        payload = (
            {}
            if operation == "VOID"
            else {
                "start_at": datetime(2024, 1, 2, 9, tzinfo=UTC),
                "end_at": datetime(2024, 1, 2, 10, tzinfo=UTC),
            }
        )
        return services.revise_attendance(
            hr_context,
            attendance_id=record.attendance.id,
            expected_revision=expected,
            request_key=transition_key,
            operation=operation,
            reason="Synthetic revision race",
            **payload,
        )

    def approving():
        return _decide(approver, draft)

    action = {"CORRECT": "corrected", "VOID": "voided", "REINSTATE": "reinstated"}[operation]
    if operation == "VOID" and approval_first:
        _refused_approval_then_waiting_void(monkeypatch, approving, revising)
    else:
        _race(
            monkeypatch,
            leave if approval_first else attendance,
            "hr.leave.approved" if approval_first else f"hr.attendance.{action}",
            approving if approval_first else revising,
            revising if approval_first else approving,
            loser_fails=operation != "VOID",
        )
    revision_wins = not approval_first or operation == "VOID"
    approval_wins = (
        approval_first and operation != "VOID" or operation == "VOID" and not approval_first
    )
    native = LeaveRequest.objects.get(pk=draft.leave.id)
    assert native.status == ("APPROVED" if approval_wins else "SUBMITTED")
    assert native.revision == (3 if approval_wins else 2)
    assert (native.decision_key is not None) == approval_wins
    assert AttendanceRevision.objects.count() == before_revisions + int(revision_wins)
    assert AttendanceRevision.objects.filter(request_key=transition_key).exists() == revision_wins
    changes = Counter()
    if revision_wins:
        changes[f"hr.attendance.{action}"] = 1
    if approval_wins:
        changes["hr.leave.approved"] = 1
    assert _delta(before) == changes
    assert Attendance.objects.count() == 1


@pytest.mark.parametrize("reverse", [False, True])
def test_overlapping_submit_attempts_have_one_receipt_and_audit(
    hr_context, employee, monkeypatch, reverse
):
    drafts = [_draft(hr_context, employee), _draft(hr_context, employee)]
    if reverse:
        drafts.reverse()
    before = _audits()
    _race(
        monkeypatch,
        leave,
        "hr.leave.submitted",
        lambda: _submit(hr_context, drafts[0]),
        lambda: _submit(hr_context, drafts[1]),
    )
    winner, loser = [LeaveRequest.objects.get(pk=row.leave.id) for row in drafts]
    assert (winner.status, winner.revision) == ("SUBMITTED", 2)
    assert winner.submit_key is not None and winner.submit_revision == 2
    assert (loser.status, loser.revision) == ("DRAFT", 1)
    assert loser.submit_key is None and loser.submitted_by_id is None
    assert _delta(before) == {"hr.leave.submitted": 1}


@pytest.mark.parametrize("other_decision", ["APPROVED", "REJECTED"])
@pytest.mark.parametrize("other_first", [False, True])
def test_competing_leave_decisions_retain_only_the_first_exact_receipt(
    hr_context, employee, monkeypatch, other_decision, other_first
):
    first_actor, other_actor = _approver(hr_context), _approver(hr_context, "two")
    draft = _draft(hr_context, employee)
    _submit(hr_context, draft)
    before = _audits()
    decisions = [(first_actor, "APPROVED"), (other_actor, other_decision)]
    if other_first:
        decisions.reverse()
    _race(
        monkeypatch,
        leave,
        "hr.leave.approved" if decisions[0][1] == "APPROVED" else "hr.leave.rejected",
        lambda: _decide(decisions[0][0], draft, decisions[0][1]),
        lambda: _decide(decisions[1][0], draft, decisions[1][1]),
    )
    native = LeaveRequest.objects.get(pk=draft.leave.id)
    assert native.status == native.decision == decisions[0][1]
    assert native.decided_by_id == decisions[0][0].actor_id
    assert native.revision == native.decision_revision == 3
    assert native.decision_from_revision == 2 and native.decision_key is not None
    assert native.cancel_key is None
    assert _delta(before) == {f"hr.leave.{decisions[0][1].lower()}": 1}


@pytest.mark.parametrize("approval_first", [False, True])
def test_approval_vs_stale_cancellation_preserves_both_legal_event_receipts(
    hr_context, employee, monkeypatch, approval_first
):
    approver = _approver(hr_context)
    draft = _draft(hr_context, employee)
    _submit(hr_context, draft)
    before = _audits()

    def cancelling(expected_revision=2):
        return services.cancel_leave(
            approver,
            leave_id=draft.leave.id,
            expected_revision=expected_revision,
            request_key=uuid4(),
            reason="Synthetic cancellation race",
        )

    _race(
        monkeypatch,
        leave,
        "hr.leave.approved" if approval_first else "hr.leave.cancelled",
        lambda: _decide(approver, draft) if approval_first else cancelling(),
        lambda: cancelling() if approval_first else _decide(approver, draft),
    )
    native = LeaveRequest.objects.get(pk=draft.leave.id)
    assert native.status == ("APPROVED" if approval_first else "CANCELLED")
    assert native.revision == 3
    assert (native.decision_key is not None) == approval_first
    assert (native.cancel_key is not None) == (not approval_first)
    assert _delta(before) == {"hr.leave.approved" if approval_first else "hr.leave.cancelled": 1}
    if approval_first:
        retained_decision = (native.decision_key, native.decided_by_id, native.decision_revision)
        cancelling(expected_revision=3)
        native.refresh_from_db()
        assert native.status == "CANCELLED" and native.revision == 4
        assert retained_decision == (
            native.decision_key,
            native.decided_by_id,
            native.decision_revision,
        )
        assert native.cancel_from_revision == 3 and native.cancel_revision == 4
        assert _delta(before) == {"hr.leave.approved": 1, "hr.leave.cancelled": 1}


@pytest.mark.parametrize("history", ["attendance", "approved_leave"])
@pytest.mark.parametrize("edit_first", [False, True])
def test_employment_date_edit_vs_new_effect_cannot_erase_eligibility(
    hr_context, employee, monkeypatch, history, edit_first
):
    approver = _approver(hr_context)
    draft = _draft(hr_context, employee) if history == "approved_leave" else None
    before = _audits()

    def editing():
        return services.update_employee(
            hr_context,
            employee_id=employee.id,
            expected_revision=1,
            joining_date=date(2024, 1, 3),
        )

    def creating_history():
        if history == "attendance":
            return _record(hr_context, employee)
        # Submission itself is protected history. The approval-first order
        # deliberately finishes that public workflow before the competing edit.
        _submit(hr_context, draft)
        return _decide(approver, draft)

    effect_module, effect_action = (
        (attendance, "hr.attendance.recorded")
        if history == "attendance"
        else (leave, "hr.leave.approved")
    )
    _race(
        monkeypatch,
        services if edit_first else effect_module,
        "hr.employee.updated" if edit_first else effect_action,
        editing if edit_first else creating_history,
        creating_history if edit_first else editing,
    )
    native_employee = Employee.objects.get(pk=employee.id)
    assert native_employee.joining_date == (date(2024, 1, 3) if edit_first else date(2020, 1, 1))
    assert native_employee.revision == (2 if edit_first else 1)
    if history == "attendance":
        assert (
            Attendance.objects.count() == AttendanceRevision.objects.count() == int(not edit_first)
        )
        expected = {"hr.employee.updated": 1} if edit_first else {"hr.attendance.recorded": 1}
    else:
        native_leave = LeaveRequest.objects.get(pk=draft.leave.id)
        assert (native_leave.status, native_leave.revision) == (
            ("DRAFT", 1) if edit_first else ("APPROVED", 3)
        )
        assert (native_leave.submit_key is not None) == (not edit_first)
        assert (native_leave.decision_key is not None) == (not edit_first)
        expected = (
            {"hr.employee.updated": 1}
            if edit_first
            else {"hr.leave.submitted": 1, "hr.leave.approved": 1}
        )
    assert _delta(before) == expected


@pytest.mark.parametrize("correction_first", [False, True])
def test_long_correction_vs_new_long_record_has_one_nonoverlapping_winner(
    hr_context, employee, monkeypatch, correction_first
):
    original = _record(hr_context, employee, day=1)
    before = _audits()
    correction_key, record_key = uuid4(), uuid4()

    def correcting():
        return services.revise_attendance(
            hr_context,
            attendance_id=original.attendance.id,
            expected_revision=1,
            request_key=correction_key,
            operation="CORRECT",
            start_at=datetime(2024, 1, 1, 9, tzinfo=UTC),
            end_at=datetime(2024, 1, 4, 10, tzinfo=UTC),
            reason="Synthetic 73-hour correction",
        )

    def recording():
        return services.record_attendance(
            hr_context,
            employee_id=employee.id,
            request_key=record_key,
            start_at=datetime(2024, 1, 3, 9, tzinfo=UTC),
            end_at=datetime(2024, 1, 6, 10, tzinfo=UTC),
        )

    _race(
        monkeypatch,
        attendance,
        "hr.attendance.corrected" if correction_first else "hr.attendance.recorded",
        correcting if correction_first else recording,
        recording if correction_first else correcting,
    )
    assert Attendance.objects.count() == (1 if correction_first else 2)
    assert AttendanceRevision.objects.count() == 2
    assert (
        AttendanceRevision.objects.filter(request_key=correction_key).exists() == correction_first
    )
    assert Attendance.objects.filter(record_request_key=record_key).exists() == (
        not correction_first
    )
    assert _delta(before) == {
        "hr.attendance.corrected" if correction_first else "hr.attendance.recorded": 1
    }


@pytest.mark.parametrize("long_first", [False, True])
def test_long_record_vs_inner_record_has_one_exact_winner_receipt(
    hr_context, employee, monkeypatch, long_first
):
    intervals = [
        (datetime(2024, 1, 1, 9, tzinfo=UTC), datetime(2024, 1, 4, 10, tzinfo=UTC)),
        (datetime(2024, 1, 3, 9, tzinfo=UTC), datetime(2024, 1, 3, 10, tzinfo=UTC)),
    ]
    if not long_first:
        intervals.reverse()
    winner_key, loser_key = uuid4(), uuid4()
    before = _audits()

    def recording(interval, key):
        return services.record_attendance(
            hr_context,
            employee_id=employee.id,
            request_key=key,
            start_at=interval[0],
            end_at=interval[1],
        )

    winner, _ = _race(
        monkeypatch,
        attendance,
        "hr.attendance.recorded",
        lambda: recording(intervals[0], winner_key),
        lambda: recording(intervals[1], loser_key),
    )
    native = Attendance.objects.get()
    revision = AttendanceRevision.objects.get()
    assert native.pk == winner.attendance.id
    assert native.record_request_key == winner_key
    assert revision.pk == winner.receipt.id
    assert revision.attendance_id == native.pk
    assert revision.request_key == winner_key
    assert (revision.number, revision.expected_revision) == (1, 0)
    assert (revision.operation, revision.effect) == ("RECORD", "ACTIVE_INTERVAL")
    assert (revision.start_at, revision.end_at) == intervals[0]
    assert (winner.receipt.start_at, winner.receipt.end_at) == intervals[0]
    assert not Attendance.objects.filter(record_request_key=loser_key).exists()
    assert not AttendanceRevision.objects.filter(request_key=loser_key).exists()
    assert _delta(before) == {"hr.attendance.recorded": 1}
