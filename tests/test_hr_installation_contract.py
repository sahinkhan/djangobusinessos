"""Installed API admission and retired-Party eligibility, without fake history."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from businessos.core.access.models import RolePermission, UserCompanyAccess, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import current_database_alias
from businessos.core.modules.models import BusinessModule
from businessos.modules.hr import selectors, services
from businessos.modules.hr.models import (
    Attendance,
    AttendanceRevision,
    Department,
    Employee,
    LeaveRequest,
    LeaveType,
)
from businessos.modules.party.models import Party
from tests import test_hr_services as _fixtures

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)
START = datetime(2024, 1, 1, 8, tzinfo=UTC)


def _user(context, email, *, with_role=False):
    alias = current_database_alias()
    user = get_user_model().objects.db_manager(alias).create_user(email, "synthetic-only")
    UserCompanyAccess.objects.using(alias).create(user=user, company_id=context.company_id)
    if with_role:
        role_id = UserRoleAssignment.objects.using(alias).get(user_id=context.actor_id).role_id
        UserRoleAssignment.objects.using(alias).create(
            user=user, company_id=context.company_id, role_id=role_id
        )
    return user


@pytest.fixture
def eligibility_world(hr_context, hr_person):
    alias = current_database_alias()
    employee = services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="ELIGIBILITY",
        joining_date=date(2020, 1, 1),
    )
    unused = Party.objects.using(alias).create(
        company_id=hr_context.company_id,
        party_type="person",
        display_name="Unassigned synthetic person",
    )
    user = _user(hr_context, "hr-eligibility-link@example.test")
    approver_user = _user(hr_context, "hr-eligibility-approver@example.test", with_role=True)
    approver = BusinessContext(actor_id=approver_user.pk, company_id=hr_context.company_id)
    leave_type = services.create_leave_type(hr_context, code="ELIG", name="Synthetic eligibility")
    record_inputs = dict(
        employee_id=employee.id,
        request_key=uuid4(),
        start_at=START,
        end_at=datetime(2024, 1, 1, 9, tzinfo=UTC),
        reason="Original eligibility fixture",
    )
    attendance = services.record_attendance(hr_context, **record_inputs)
    leaves = {}
    submit_inputs = {}
    for name, day in (("draft", 3), ("submitted", 4), ("approved", 5)):
        leaves[name] = services.create_leave(
            hr_context,
            employee_id=employee.id,
            create_request_key=uuid4(),
            leave_type_id=leave_type.id,
            start_date=date(2024, 1, day),
            end_date=date(2024, 1, day),
            reason="Original eligibility fixture",
        ).leave.id
        if name != "draft":
            submit_inputs[name] = dict(
                leave_id=leaves[name], expected_revision=1, request_key=uuid4()
            )
            services.submit_leave(hr_context, **submit_inputs[name])
    approval_inputs = dict(
        leave_id=leaves["approved"],
        expected_revision=2,
        request_key=uuid4(),
        decision="APPROVED",
        reason="Original legal approval",
    )
    services.decide_leave(approver, **approval_inputs)
    return {
        "context": hr_context,
        "person": hr_person,
        "unused_person": unused,
        "employee": employee,
        "new_user": user,
        "approver": approver,
        "leave_type": leave_type,
        "attendance": attendance,
        "record_inputs": record_inputs,
        "leaves": leaves,
        "submit_inputs": submit_inputs,
        "approval_inputs": approval_inputs,
    }


def _change_party(world, change):
    for key in ("person", "unused_person"):
        row = world[key]
        if change == "inactive":
            row.is_active = False
            row.save(update_fields=["is_active"])
        else:
            row.party_type = Party.Type.ORGANIZATION
            row.save(update_fields=["party_type"])


def _native():
    alias = current_database_alias()
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


def test_missing_registry_is_http_only_while_installed_setup_and_record_still_require_rbac(
    eligibility_world, client
):
    world = eligibility_world
    context = world["context"]
    alias = current_database_alias()
    BusinessModule.objects.using(alias).filter(code="hr").delete()
    client.force_login(get_user_model().objects.using(alias).get(pk=context.actor_id))
    session = client.session
    session["businessos_company_id"] = str(context.company_id)
    session.save()
    for path in ("/hr/", "/hr/employees/", "/hr/departments/new/", "/hr/attendance/new/"):
        assert client.get(path).status_code == 404
    assert b'href="/hr/"' not in client.get("/").content
    department = services.create_department(context, code="NO-REGISTRY", name="Installed API")
    inputs = dict(
        employee_id=world["employee"].id,
        request_key=uuid4(),
        start_at=datetime(2024, 1, 2, 8, tzinfo=UTC),
        end_at=datetime(2024, 1, 2, 9, tzinfo=UTC),
    )
    result = services.record_attendance(context, **inputs)
    assert department.code == "NO-REGISTRY" and result.receipt.number == 1
    assert not BusinessModule.objects.using(alias).filter(code="hr").exists()
    RolePermission.objects.using(alias).filter(permission__code="hr.attendance.record").delete()
    before = _native()
    with pytest.raises(PermissionDenied):
        services.record_attendance(context, **{**inputs, "request_key": uuid4()})
    assert _native() == before


@pytest.mark.parametrize("change", ["inactive", "non_person"])
@pytest.mark.parametrize(
    "action", ["employee", "record", "leave_create", "leave_edit", "submit", "approve", "link"]
)
def test_current_party_ineligibility_denies_new_effect_without_partial_native_or_audit(
    eligibility_world, change, action
):
    world = eligibility_world
    context = world["context"]
    _change_party(world, change)
    before = _native()
    with pytest.raises(ValidationError, match="active same-Company PERSON"):
        if action == "employee":
            services.create_employee(
                context,
                party_id=world["unused_person"].pk,
                employee_number="INELIGIBLE",
                joining_date=date(2020, 1, 1),
            )
        elif action == "record":
            services.record_attendance(
                context,
                employee_id=world["employee"].id,
                request_key=uuid4(),
                start_at=datetime(2024, 1, 2, 8, tzinfo=UTC),
                end_at=datetime(2024, 1, 2, 9, tzinfo=UTC),
            )
        elif action == "leave_create":
            services.create_leave(
                context,
                employee_id=world["employee"].id,
                create_request_key=uuid4(),
                leave_type_id=world["leave_type"].id,
                start_date=date(2024, 1, 7),
                end_date=date(2024, 1, 7),
            )
        elif action == "leave_edit":
            services.update_leave(
                context,
                leave_id=world["leaves"]["draft"],
                expected_revision=1,
                leave_type_id=world["leave_type"].id,
                start_date=date(2024, 1, 3),
                end_date=date(2024, 1, 3),
                reason="New ineligible edit",
            )
        elif action == "submit":
            services.submit_leave(
                context,
                leave_id=world["leaves"]["draft"],
                expected_revision=1,
                request_key=uuid4(),
            )
        elif action == "approve":
            services.decide_leave(
                world["approver"],
                leave_id=world["leaves"]["submitted"],
                expected_revision=2,
                request_key=uuid4(),
                decision="APPROVED",
            )
        else:
            services.update_employee(
                context,
                employee_id=world["employee"].id,
                expected_revision=1,
                user_id=world["new_user"].pk,
            )
    assert _native() == before


@pytest.mark.parametrize("change", ["inactive", "non_person"])
def test_current_ineligible_party_does_not_rewrite_or_block_authorized_attendance_history(
    eligibility_world, change
):
    world = eligibility_world
    context = world["context"]
    _change_party(world, change)
    attendance_id = world["attendance"].attendance.id
    employee = selectors.employee_detail(context, world["employee"].id)
    assert set(employee.party) == {"id", "company_id", "party_type", "display_name", "is_active"}
    assert employee.party["party_type"] == world["person"].party_type
    assert employee.party["is_active"] == world["person"].is_active
    assert selectors.attendance_detail(context, attendance_id).current.number == 1
    for ordinal, operation in ((1, "CORRECT"), (2, "VOID"), (3, "REINSTATE")):
        result = services.revise_attendance(
            context,
            attendance_id=attendance_id,
            expected_revision=ordinal,
            request_key=uuid4(),
            operation=operation,
            reason="Authorized historical maintenance",
            **(
                {}
                if operation == "VOID"
                else {"start_at": START, "end_at": datetime(2024, 1, 1, 10, tzinfo=UTC)}
            ),
        )
        assert result.receipt.number == ordinal + 1
    before = _native()
    retry = services.record_attendance(context, **world["record_inputs"])
    assert retry.historical_retry and retry.receipt.number == 1 and retry.current.number == 4
    assert _native() == before
    assert selectors.revision_page(context, attendance_id).paginator.count == 4


@pytest.mark.parametrize("change", ["inactive", "non_person"])
def test_ineligible_party_allows_historical_leave_rejection_cancellation_and_receipts(
    eligibility_world, change
):
    world = eligibility_world
    context = world["context"]
    _change_party(world, change)
    submitted_id = world["leaves"]["submitted"]
    rejected = services.decide_leave(
        world["approver"],
        leave_id=submitted_id,
        expected_revision=2,
        request_key=uuid4(),
        decision="REJECTED",
        reason="Authorized historical rejection",
    )
    assert rejected.current_status == "REJECTED"
    for state, revision in (("draft", 1), ("approved", 3)):
        cancelled = services.cancel_leave(
            world["approver"],
            leave_id=world["leaves"][state],
            expected_revision=revision,
            request_key=uuid4(),
            reason="Authorized historical cancellation",
        )
        assert cancelled.current_status == "CANCELLED"
    before = _native()
    for state in ("submitted", "approved"):
        retry = services.submit_leave(context, **world["submit_inputs"][state])
        assert retry.historical_retry and retry.receipt_revision == 2
        assert retry.current_status == ("REJECTED" if state == "submitted" else "CANCELLED")
        detail = selectors.leave_detail(context, world["leaves"][state])
        assert detail.party["party_type"] == world["person"].party_type
        assert detail.party["is_active"] == world["person"].is_active
    approval_retry = services.decide_leave(world["approver"], **world["approval_inputs"])
    assert approval_retry.historical_retry and approval_retry.current_status == "CANCELLED"
    assert _native() == before
