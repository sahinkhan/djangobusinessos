"""Current Employee scope versus immutable historical Branch snapshots."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied

from businessos.core.access.models import UserBranchAccess
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Branch, Company
from businessos.modules.hr import selectors, services
from businessos.modules.hr.models import (
    Attendance,
    AttendanceRevision,
    Department,
    Employee,
    LeaveRequest,
    LeaveType,
)
from tests import test_hr_services as _fixtures

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)
DATES = {"start_date": date(2024, 1, 1), "end_date": date(2024, 1, 31)}


def _native():
    return tuple(
        tuple(model.objects.order_by("pk").values())
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


def _denied(call, *args, **kwargs):
    before = _native()
    with pytest.raises(PermissionDenied):
        call(*args, **kwargs)
    assert _native() == before


@pytest.fixture
def branch_world(hr_context, hr_person):
    branches = {
        code: Branch.objects.create(company_id=hr_context.company_id, code=code, name=code)
        for code in ("A", "B")
    }
    contexts = {}
    for code, branch in branches.items():
        UserBranchAccess.objects.create(user_id=hr_context.actor_id, branch=branch)
        contexts[code] = BusinessContext(
            actor_id=hr_context.actor_id,
            company_id=hr_context.company_id,
            branch_id=branch.pk,
        )
    department = services.create_department(hr_context, code="SCOPE", name="Company-wide setup")
    leave_type = services.create_leave_type(hr_context, code="SCOPE", name="Company-wide type")
    employee = services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="SCOPE",
        joining_date=date(2020, 1, 1),
        department_id=department.id,
    )
    records, requests, inputs = {}, {}, {}
    for label, day in (("null", 1), ("A", 3)):
        if label == "A":
            services.transfer_employee_branch(
                hr_context,
                employee_id=employee.id,
                expected_revision=1,
                branch_id=branches["A"].pk,
            )
        start = datetime(2024, 1, day, 8, 0, 45, 123456, tzinfo=UTC)
        inputs[label] = {
            "employee_id": employee.id,
            "request_key": uuid4(),
            "start_at": start,
            "end_at": start + timedelta(hours=1),
            "reason": f"Original {label} scope",
        }
        records[label] = services.record_attendance(hr_context, **inputs[label]).attendance.id
        requests[label] = services.create_leave(
            hr_context,
            employee_id=employee.id,
            create_request_key=uuid4(),
            leave_type_id=leave_type.id,
            start_date=date(2024, 1, day + 1),
            end_date=date(2024, 1, day + 1),
            reason=f"Original {label} request",
        ).leave.id
    services.transfer_employee_branch(
        hr_context,
        employee_id=employee.id,
        expected_revision=2,
        branch_id=branches["B"].pk,
    )
    return {
        "company": hr_context,
        "contexts": contexts,
        "branches": branches,
        "employee": employee.id,
        "department": department.id,
        "leave_type": leave_type.id,
        "attendance": records,
        "leave": requests,
        "record_inputs": inputs,
    }


def test_employee_current_branch_and_company_wide_setup_are_distinct(branch_world):
    world = branch_world
    a, b = world["contexts"]["A"], world["contexts"]["B"]
    _denied(selectors.employee_detail, a, world["employee"])
    assert selectors.employee_page(a).paginator.count == 0
    current = selectors.employee_detail(b, world["employee"])
    assert current.branch_id == world["branches"]["B"].pk and current.revision == 3
    assert tuple(row.id for row in selectors.employee_page(b).object_list) == (world["employee"],)
    for context in (a, b):
        assert selectors.department_detail(context, world["department"]).id == world["department"]
        assert selectors.leave_type_detail(context, world["leave_type"]).id == world["leave_type"]
    # A Branch-only grant never authorizes Company-wide transfer/setup mutation.
    _denied(
        services.transfer_employee_branch,
        b,
        employee_id=world["employee"],
        expected_revision=3,
        branch_id=None,
    )


@pytest.mark.parametrize("kind", ["attendance", "leave"])
def test_historical_direct_search_and_pages_use_frozen_a_not_current_b(branch_world, kind):
    world = branch_world
    own, other = world["contexts"]["A"], world["contexts"]["B"]
    row_id = world[kind]["A"]
    detail, page = getattr(selectors, f"{kind}_detail"), getattr(selectors, f"{kind}_page")
    assert detail(own, row_id).branch_id == world["branches"]["A"].pk
    _denied(detail, other, row_id)
    assert tuple(row.id for row in page(own, search="SCOPE", **DATES).object_list) == (row_id,)
    assert page(other, search="SCOPE", **DATES).paginator.count == 0
    assert page(world["company"], **DATES).paginator.count == 2
    if kind == "attendance":
        assert selectors.revision_page(own, row_id).paginator.count == 1
        _denied(selectors.revision_page, other, row_id)


def test_null_snapshots_are_company_visible_but_never_branch_visible(branch_world):
    world = branch_world
    for kind in ("attendance", "leave"):
        row_id = world[kind]["null"]
        detail = getattr(selectors, f"{kind}_detail")
        assert detail(world["company"], row_id).branch_id is None
        for context in world["contexts"].values():
            _denied(detail, context, row_id)
            page = getattr(selectors, f"{kind}_page")(context, **DATES)
            assert row_id not in {row.id for row in page.object_list}
    for context in world["contexts"].values():
        _denied(selectors.revision_page, context, world["attendance"]["null"])


def test_new_activity_uses_current_b_and_does_not_inherit_historical_a(branch_world):
    world = branch_world
    a, b = world["contexts"]["A"], world["contexts"]["B"]
    record = {
        "employee_id": world["employee"],
        "request_key": uuid4(),
        "start_at": datetime(2024, 1, 10, 8, tzinfo=UTC),
        "end_at": datetime(2024, 1, 10, 9, tzinfo=UTC),
    }
    request = {
        "employee_id": world["employee"],
        "create_request_key": uuid4(),
        "leave_type_id": world["leave_type"],
        "start_date": date(2024, 1, 11),
        "end_date": date(2024, 1, 11),
    }
    _denied(services.record_attendance, a, **record)
    _denied(services.create_leave, a, **request)
    assert services.record_attendance(b, **record).attendance.branch_id == b.branch_id
    assert services.create_leave(b, **request).leave.branch_id == b.branch_id
    for operation in ("record_attendance", "create_leave"):
        choices = selectors.action_admission(a, operation)["choices"].get("employee_id", ())
        assert world["employee"] not in {key for key, _ in choices}


def test_frozen_a_record_retry_and_correction_after_transfer_and_zone_change(branch_world):
    world = branch_world
    a, b = world["contexts"]["A"], world["contexts"]["B"]
    company = Company.objects.get(pk=a.company_id)
    company.timezone = "America/New_York"
    company.save(update_fields=["timezone", "updated_at"])
    payload = world["record_inputs"]["A"]
    before = _native()
    retry = services.record_attendance(a, **payload)
    assert retry.historical_retry and retry.receipt.number == 1
    assert retry.attendance.branch_id == a.branch_id and retry.attendance.timezone == "UTC"
    assert retry.receipt.start_at == payload["start_at"]
    assert _native() == before
    _denied(services.record_attendance, b, **payload)
    changed = services.revise_attendance(
        a,
        attendance_id=retry.attendance.id,
        expected_revision=1,
        request_key=uuid4(),
        operation="CORRECT",
        start_at=payload["start_at"],
        end_at=payload["end_at"] + timedelta(minutes=5),
        reason="Frozen A correction after transfer",
    )
    assert changed.current.number == 2 and changed.attendance.branch_id == a.branch_id
    before = _native()
    historical = services.record_attendance(a, **payload)
    assert historical.receipt.number == 1 and historical.current.number == 2
    assert _native() == before


def test_frozen_a_leave_mutations_and_historical_submit_retry_after_transfer(branch_world):
    world = branch_world
    a, b = world["contexts"]["A"], world["contexts"]["B"]
    request_id = world["leave"]["A"]
    payload = {
        "leave_id": request_id,
        "expected_revision": 1,
        "leave_type_id": world["leave_type"],
        "start_date": date(2024, 1, 4),
        "end_date": date(2024, 1, 4),
        "reason": "Frozen A edit after transfer",
    }
    _denied(services.update_leave, b, **payload)
    assert services.update_leave(a, **payload).current_revision == 2
    submit = {"leave_id": request_id, "expected_revision": 2, "request_key": uuid4()}
    _denied(services.submit_leave, b, **submit)
    assert services.submit_leave(a, **submit).receipt_revision == 3
    services.cancel_leave(
        a,
        leave_id=request_id,
        expected_revision=3,
        request_key=uuid4(),
        reason="Frozen A cancellation after transfer",
    )
    before = _native()
    retry = services.submit_leave(a, **submit)
    assert retry.historical_retry and retry.receipt_revision == 3
    assert retry.current_revision == 4 and retry.current_status == "CANCELLED"
    assert _native() == before
    _denied(services.submit_leave, b, **submit)


def test_inactive_historical_a_requires_valid_company_context_without_erasing_facts(branch_world):
    world = branch_world
    a, b = world["contexts"]["A"], world["contexts"]["B"]
    branch = world["branches"]["A"]
    branch.is_active = False
    branch.save(update_fields=["is_active", "updated_at"])
    attendance_id, leave_id = world["attendance"]["A"], world["leave"]["A"]
    _denied(selectors.attendance_detail, a, attendance_id)
    _denied(selectors.leave_detail, a, leave_id)
    _denied(selectors.attendance_detail, b, attendance_id)
    _denied(selectors.leave_detail, b, leave_id)
    company = world["company"]
    assert selectors.attendance_detail(company, attendance_id).branch_id == branch.pk
    assert selectors.leave_detail(company, leave_id).branch_id == branch.pk
    services.revise_attendance(
        company,
        attendance_id=attendance_id,
        expected_revision=1,
        request_key=uuid4(),
        operation="VOID",
        reason="Authorized inactive-Branch historical correction",
    )
    services.cancel_leave(
        company,
        leave_id=leave_id,
        expected_revision=1,
        request_key=uuid4(),
        reason="Authorized inactive-Branch historical cancellation",
    )
    assert selectors.attendance_detail(company, attendance_id).current.effect == "VOIDED"
    assert selectors.leave_detail(company, leave_id).status == "CANCELLED"
    assert Attendance.objects.get(pk=attendance_id).branch_id == branch.pk
    assert LeaveRequest.objects.get(pk=leave_id).branch_id == branch.pk
    assert Employee.objects.get(pk=world["employee"]).branch_id == world["branches"]["B"].pk
