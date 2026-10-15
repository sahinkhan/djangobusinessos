from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from businessos.core.access.models import UserCompanyAccess, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.modules.hr import selectors, services
from businessos.modules.hr.models import Attendance, AttendanceRevision, LeaveRequest
from tests import test_hr_services as _setup_fixtures

hr_context = _setup_fixtures.hr_context
hr_person = _setup_fixtures.hr_person

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def employee(hr_context, hr_person):
    return services.create_employee(
        hr_context, party_id=hr_person.pk, employee_number="E-1", joining_date=date(2020, 1, 1)
    )


@pytest.fixture
def approver(hr_context):
    user = get_user_model().objects.create_user("synthetic-approver@example.test", "unused")
    UserCompanyAccess.objects.create(user=user, company_id=hr_context.company_id)
    assignment = UserRoleAssignment.objects.get(user_id=hr_context.actor_id)
    UserRoleAssignment.objects.create(
        user=user, company_id=hr_context.company_id, role_id=assignment.role_id
    )
    return BusinessContext(actor_id=user.pk, company_id=hr_context.company_id)


def _record(context, employee, start, end, key=None):
    return services.record_attendance(
        context, employee_id=employee.id, request_key=key or uuid4(), start_at=start, end_at=end
    )


def test_completed_sessions_long_intervals_adjacency_and_overlap(hr_context, employee):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    original = _record(hr_context, employee, start, start + timedelta(hours=61))
    with pytest.raises(ValidationError, match="conflicts"):
        _record(hr_context, employee, start + timedelta(hours=60), start + timedelta(hours=62))
    adjacent = _record(
        hr_context, employee, start + timedelta(hours=61), start + timedelta(hours=62)
    )
    assert original.receipt.local_end_date == date(2024, 1, 3)
    assert adjacent.attendance.id != original.attendance.id
    assert Attendance.objects.count() == 2
    assert AttendanceRevision.objects.count() == 2


def test_revision_receipt_is_historical_not_latest_and_no_repeat_audit(hr_context, employee):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    original = _record(hr_context, employee, start, start + timedelta(hours=2))
    key = uuid4()
    changed = services.revise_attendance(
        hr_context,
        attendance_id=original.attendance.id,
        expected_revision=1,
        request_key=key,
        operation="CORRECT",
        start_at=start,
        end_at=start + timedelta(hours=3),
        reason="corrected",
    )
    voided = services.revise_attendance(
        hr_context,
        attendance_id=original.attendance.id,
        expected_revision=2,
        request_key=uuid4(),
        operation="VOID",
        reason="voided",
    )
    assert voided.current.effect == "VOIDED"
    retried = services.revise_attendance(
        hr_context,
        attendance_id=original.attendance.id,
        expected_revision=1,
        request_key=key,
        operation="CORRECT",
        start_at=start,
        end_at=start + timedelta(hours=3),
        reason="corrected",
    )
    assert changed.receipt.id == retried.receipt.id
    assert retried.receipt.number == 2 and retried.current.number == 3
    assert retried.historical_retry
    assert AuditEntry.objects.filter(action="hr.attendance.corrected").count() == 1
    reinstated = services.revise_attendance(
        hr_context,
        attendance_id=original.attendance.id,
        expected_revision=3,
        request_key=uuid4(),
        operation="REINSTATE",
        start_at=start,
        end_at=start + timedelta(hours=3),
        reason="restored",
    )
    assert reinstated.current.number == 4 and reinstated.current.effect == "ACTIVE_INTERVAL"
    details = selectors.attendance_detail(hr_context, original.attendance.id)
    assert details.current.number == 4
    assert selectors.revision_page(hr_context, details.id).paginator.count == 4


def test_record_retry_preserves_old_branch_timezone_and_precision(
    hr_context, employee, branch, company
):
    start = datetime(2024, 1, 1, 1, 30, 45, 123456, tzinfo=UTC)
    key = uuid4()
    original = _record(hr_context, employee, start, start + timedelta(hours=2), key)
    services.transfer_employee_branch(
        hr_context, employee_id=employee.id, expected_revision=1, branch_id=branch.pk
    )
    company.timezone = "America/New_York"
    company.save()
    retried = _record(hr_context, employee, start, start + timedelta(hours=2), key)
    assert retried.attendance.id == original.attendance.id
    assert retried.attendance.branch_id is None and retried.attendance.timezone == "UTC"
    assert retried.receipt.start_at == start
    assert retried.historical_retry
    assert AuditEntry.objects.filter(action="hr.attendance.recorded").count() == 1


@pytest.mark.parametrize("span", [1, 365, 366, 367, 1461])
def test_leave_full_calendar_spans_without_duration_cap(hr_context, employee, span):
    leave_type = services.create_leave_type(hr_context, code="L", name="Synthetic Leave")
    first = date(2020, 1, 1)
    last = first + timedelta(days=span - 1)
    result = services.create_leave(
        hr_context,
        employee_id=employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=first,
        end_date=last,
    )
    assert result.leave.end_date == last
    assert (result.leave.end_date - result.leave.start_date).days + 1 == span


def test_leave_decision_cancel_and_retained_approval_receipt(hr_context, approver, employee):
    leave_type = services.create_leave_type(hr_context, code="L", name="Synthetic Leave")
    draft = services.create_leave(
        hr_context,
        employee_id=employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 2),
    )
    submitted = services.submit_leave(
        hr_context, leave_id=draft.leave.id, expected_revision=1, request_key=uuid4()
    )
    assert submitted.current_status == "SUBMITTED"
    with pytest.raises(ValidationError, match="Requester"):
        services.decide_leave(
            hr_context,
            leave_id=draft.leave.id,
            expected_revision=2,
            request_key=uuid4(),
            decision="APPROVED",
        )
    decision_key = uuid4()
    approved = services.decide_leave(
        approver,
        leave_id=draft.leave.id,
        expected_revision=2,
        request_key=decision_key,
        decision="APPROVED",
    )
    assert approved.current_status == "APPROVED"
    cancelled = services.cancel_leave(
        approver,
        leave_id=draft.leave.id,
        expected_revision=3,
        request_key=uuid4(),
        reason="cancelled",
    )
    assert cancelled.current_status == "CANCELLED"
    retried = services.decide_leave(
        approver,
        leave_id=draft.leave.id,
        expected_revision=2,
        request_key=decision_key,
        decision="APPROVED",
    )
    assert retried.receipt_revision == 3 and retried.current_revision == 4
    assert retried.current_status == "CANCELLED" and retried.historical_retry
    assert AuditEntry.objects.filter(action="hr.leave.approved").count() == 1
    assert LeaveRequest.objects.get(pk=draft.leave.id).decision == "APPROVED"


@pytest.mark.parametrize("attendance_first", [True, False])
def test_attendance_and_approved_leave_conflict_in_both_winner_orders(
    hr_context, approver, employee, attendance_first
):
    leave_type = services.create_leave_type(hr_context, code="L", name="Synthetic Leave")
    draft = services.create_leave(
        hr_context,
        employee_id=employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )
    services.submit_leave(
        hr_context, leave_id=draft.leave.id, expected_revision=1, request_key=uuid4()
    )
    start = datetime(2024, 1, 1, 8, tzinfo=UTC)
    if attendance_first:
        _record(hr_context, employee, start, start + timedelta(hours=1))
        with pytest.raises(ValidationError, match="conflicts"):
            services.decide_leave(
                approver,
                leave_id=draft.leave.id,
                expected_revision=2,
                request_key=uuid4(),
                decision="APPROVED",
            )
        assert LeaveRequest.objects.get(pk=draft.leave.id).status == "SUBMITTED"
    else:
        services.decide_leave(
            approver,
            leave_id=draft.leave.id,
            expected_revision=2,
            request_key=uuid4(),
            decision="APPROVED",
        )
        with pytest.raises(ValidationError, match="conflicts"):
            _record(hr_context, employee, start, start + timedelta(hours=1))
        assert not Attendance.objects.exists()


def test_employment_date_edit_cannot_erase_effective_history(hr_context, employee):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    _record(hr_context, employee, start, start + timedelta(hours=61))
    with pytest.raises(ValidationError, match="Attendance"):
        services.end_employee(
            hr_context, employee_id=employee.id, expected_revision=1, leaving_date=date(2024, 1, 2)
        )


def test_read_pages_materialized_and_department_projection_gated(hr_context, employee):
    page = selectors.employee_page(hr_context)
    assert page.paginator.count == 1 and page.object_list[0].id == employee.id
    assert isinstance(page.object_list, tuple)
    from businessos.core.access.models import RolePermission

    RolePermission.objects.filter(permission__code="hr.department.view").delete()
    detail = selectors.employee_detail(hr_context, employee.id)
    assert "department_id" not in detail.values
    assert set(detail.party) == {"id", "company_id", "party_type", "display_name", "is_active"}
