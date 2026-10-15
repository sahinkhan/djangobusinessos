"""Finite section-10 permission and Company-confinement regression table.

Expected codes are written independently of the implementation's action map.
These are real public calls with valid native fixtures, not policy-only mocks.
"""

from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connections

from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserBranchAccess,
    UserCompanyAccess,
    UserRoleAssignment,
)
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import database_execution
from businessos.core.modules.models import BusinessModule
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
from businessos.modules.party.models import Party
from tests import test_hr_services as _fixtures

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)

EV, EM = "hr.employee.view", "hr.employee.manage"
DV, DM = "hr.department.view", "hr.department.manage"
AV, AR, AC = "hr.attendance.view", "hr.attendance.record", "hr.attendance.correct"
LV, LR, LA, LC, LM = (
    "hr.leave.view",
    "hr.leave.request",
    "hr.leave.approve",
    "hr.leave.cancel",
    "hr.leave_type.manage",
)

# Frozen plan section 10, including conditional Department and approval reads.
REQUIRED = {
    "department_page": (DV,),
    "department_detail": (DV,),
    "create_department": (DM, DV),
    "update_department": (DM, DV),
    "leave_type_page": (LV,),
    "leave_type_detail": (LV,),
    "leave_type_choices": (LV,),
    "create_leave_type": (LM, LV),
    "update_leave_type": (LM, LV),
    "employee_page": (EV,),
    "employee_detail": (EV,),
    "person_choices": (EV,),
    "user_association_choices": (EM, EV),
    "create_employee": (EM, EV),
    "create_employee_department": (EM, EV, DV),
    "update_employee": (EM, EV),
    "update_employee_department": (EM, EV, DV),
    "transfer_employee_branch": (EM, EV),
    "end_employee": (EM, EV),
    "attendance_page": (AV, EV),
    "attendance_detail": (AV, EV),
    "revision_page": (AV, EV),
    "record_attendance": (AR, AV, EV),
    "record_retry": (AR, AV, EV),
    "correct_attendance": (AC, AV, EV),
    "correct_retry": (AC, AV, EV),
    "void_attendance": (AC, AV, EV),
    "reinstate_attendance": (AC, AV, EV),
    "leave_page": (LV, EV),
    "leave_detail": (LV, EV),
    "create_leave": (LR, LV, EV),
    "update_leave": (LR, LV, EV),
    "submit_leave": (LR, LV, EV),
    "submit_retry": (LR, LV, EV),
    "approve_leave": (LA, LV, EV),
    "reject_leave": (LA, LV, EV),
    "approval_retry": (LA, LV, EV),
    "cancel_draft": (LC, LV, EV),
    "cancel_submitted": (LC, LV, EV),
    "cancel_approved": (LC, LV, EV, LA),
    "cancel_approved_retry": (LC, LV, EV, LA),
}


@pytest.fixture
def permission_world(hr_context, hr_person, company, branch):
    assert not get_user_model().objects.get(pk=hr_context.actor_id).is_superuser
    department = services.create_department(hr_context, code="P", name="Permission Department")
    leave_type = services.create_leave_type(hr_context, code="P", name="Permission Leave")
    employee = services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="PERM-1",
        joining_date=date(2020, 1, 1),
    )
    approver = get_user_model().objects.create_user("permission-approver@example.test", "unused")
    UserCompanyAccess.objects.create(user=approver, company=company)
    role = UserRoleAssignment.objects.get(user_id=hr_context.actor_id).role
    UserRoleAssignment.objects.create(user=approver, company=company, role=role)
    return {
        "context": hr_context,
        "approver": BusinessContext(actor_id=approver.pk, company_id=company.pk),
        "company": company,
        "branch": branch,
        "department": department,
        "leave_type": leave_type,
        "employee": employee,
    }


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


def _prepare(name, world):
    """Return one valid public invocation and its matching optional HTTP GET."""
    context = world["context"]
    employee, department, leave_type = (
        world["employee"],
        world["department"],
        world["leave_type"],
    )
    target_id = None
    path = None
    function_name = name
    owner = services
    args = ()
    kwargs = {}
    if name in {"department_page", "leave_type_page", "leave_type_choices", "employee_page"}:
        owner = selectors
        path = {
            "department_page": "/hr/departments/",
            "leave_type_page": "/hr/leave-types/",
            "leave_type_choices": None,
            "employee_page": "/hr/employees/",
        }[name]
    elif name in {"department_detail", "leave_type_detail", "employee_detail"}:
        owner = selectors
        row = {"department_detail": department, "leave_type_detail": leave_type}.get(name, employee)
        args = (row.id,)
        target_id = row.id
        directory = {
            "department_detail": "departments",
            "leave_type_detail": "leave-types",
            "employee_detail": "employees",
        }[name]
        path = f"/hr/{directory}/{row.id}/"
    elif name in {"person_choices", "user_association_choices"}:
        owner = selectors
    elif name in {"create_department", "create_leave_type"}:
        kwargs = {"code": "NEW", "name": "Created by non-superuser"}
        path = f"/hr/{'departments' if name == 'create_department' else 'leave-types'}/new/"
    elif name in {"update_department", "update_leave_type"}:
        row = department if name == "update_department" else leave_type
        target_id = row.id
        kwargs = {
            f"{'department' if name == 'update_department' else 'leave_type'}_id": row.id,
            "expected_revision": 1,
            "name": "Changed by non-superuser",
            "is_active": True,
        }
        path = (
            f"/hr/{'departments' if name == 'update_department' else 'leave-types'}/{row.id}/edit/"
        )
    elif name in {"create_employee", "create_employee_department"}:
        function_name = "create_employee"
        person = Party.objects.create(
            company=world["company"], party_type="person", display_name="Unused Permission Person"
        )
        kwargs = {"party_id": person.pk, "employee_number": "NEW", "joining_date": date(2020, 1, 1)}
        if name.endswith("_department"):
            kwargs["department_id"] = department.id
        path = "/hr/employees/new/"
    elif name in {
        "update_employee",
        "update_employee_department",
        "end_employee",
        "transfer_employee_branch",
    }:
        target_id = employee.id
        kwargs = {"employee_id": employee.id, "expected_revision": 1}
        if name.endswith("_department"):
            services.update_employee(context, **kwargs, department_id=department.id)
            kwargs["expected_revision"] = 2
            function_name = "update_employee"
        elif name == "end_employee":
            kwargs["leaving_date"] = date(2025, 1, 1)
        elif name == "transfer_employee_branch":
            kwargs["branch_id"] = world["branch"].pk
        else:
            kwargs["joining_date"] = date(2019, 1, 1)
        suffix = (
            "end"
            if name == "end_employee"
            else "transfer"
            if name == "transfer_employee_branch"
            else "edit"
        )
        path = f"/hr/employees/{employee.id}/{suffix}/"
    elif "attendance" in name or name in {"revision_page", "record_retry", "correct_retry"}:
        start = datetime(2024, 1, 1, 8, tzinfo=UTC)
        key = uuid4()
        kwargs = {
            "employee_id": employee.id,
            "request_key": key,
            "start_at": start,
            "end_at": start + timedelta(hours=1),
        }
        if name == "record_attendance":
            path = "/hr/attendance/new/"
        else:
            original = services.record_attendance(context, **kwargs)
            target_id = original.attendance.id
            if name == "record_retry":
                function_name = "record_attendance"
            elif name in {"attendance_page", "attendance_detail", "revision_page"}:
                owner = selectors
                kwargs = {}
                if name == "attendance_page":
                    kwargs = {"start_date": date(2024, 1, 1), "end_date": date(2024, 1, 1)}
                    path = "/hr/attendance/?start_date=2024-01-01&end_date=2024-01-01"
                else:
                    args = (target_id,)
                    path = f"/hr/attendance/{target_id}/" + (
                        "revisions/" if name == "revision_page" else ""
                    )
            else:
                function_name = "revise_attendance"
                kwargs = {
                    "attendance_id": target_id,
                    "expected_revision": 1,
                    "request_key": uuid4(),
                    "operation": "CORRECT",
                    "start_at": start,
                    "end_at": start + timedelta(hours=2),
                    "reason": "Authorized correction",
                }
                if name == "void_attendance":
                    kwargs["operation"] = "VOID"
                    kwargs.pop("start_at")
                    kwargs.pop("end_at")
                elif name == "reinstate_attendance":
                    services.revise_attendance(
                        context,
                        attendance_id=target_id,
                        expected_revision=1,
                        request_key=uuid4(),
                        operation="VOID",
                        reason="Original void",
                    )
                    kwargs.update(expected_revision=2, operation="REINSTATE")
                elif name == "correct_retry":
                    services.revise_attendance(context, **kwargs)
                suffix = (
                    "void"
                    if name == "void_attendance"
                    else "reinstate"
                    if name == "reinstate_attendance"
                    else "correct"
                )
                path = f"/hr/attendance/{target_id}/{suffix}/"
    else:
        create = {
            "employee_id": employee.id,
            "create_request_key": uuid4(),
            "leave_type_id": leave_type.id,
            "start_date": date(2024, 2, 1),
            "end_date": date(2024, 2, 2),
            "reason": "Original synthetic request",
        }
        if name == "create_leave":
            kwargs = create
            path = "/hr/leave/new/"
        else:
            draft = services.create_leave(context, **create)
            target_id = draft.leave.id
            if name in {"leave_page", "leave_detail"}:
                owner = selectors
                if name == "leave_page":
                    kwargs = {"start_date": date(2024, 2, 1), "end_date": date(2024, 2, 2)}
                    path = "/hr/leave/?start_date=2024-02-01&end_date=2024-02-02"
                else:
                    args = (target_id,)
                    path = f"/hr/leave/{target_id}/"
            elif name == "update_leave":
                kwargs = {
                    "leave_id": target_id,
                    "expected_revision": 1,
                    "leave_type_id": leave_type.id,
                    "start_date": create["start_date"],
                    "end_date": create["end_date"],
                    "reason": "Changed synthetic request",
                }
                path = f"/hr/leave/{target_id}/edit/"
            else:
                kwargs = {"leave_id": target_id, "expected_revision": 1, "request_key": uuid4()}
                if name in {"submit_leave", "submit_retry"}:
                    function_name = "submit_leave"
                    if name == "submit_retry":
                        services.submit_leave(context, **kwargs)
                    path = f"/hr/leave/{target_id}/submit/"
                else:
                    if name != "cancel_draft":
                        services.submit_leave(context, **kwargs)
                        kwargs.update(expected_revision=2, request_key=uuid4())
                    if name.startswith("cancel"):
                        function_name = "cancel_leave"
                        kwargs["reason"] = "Authorized cancellation"
                        if name in {"cancel_approved", "cancel_approved_retry"}:
                            services.decide_leave(
                                world["approver"],
                                leave_id=target_id,
                                expected_revision=2,
                                request_key=uuid4(),
                                decision="APPROVED",
                            )
                            context = world["approver"]
                            kwargs.update(expected_revision=3, request_key=uuid4())
                            if name == "cancel_approved_retry":
                                services.cancel_leave(context, **kwargs)
                        path = f"/hr/leave/{target_id}/cancel/"
                    else:
                        function_name = "decide_leave"
                        context = world["approver"]
                        kwargs["decision"] = "REJECTED" if name == "reject_leave" else "APPROVED"
                        kwargs["reason"] = "Explicit synthetic decision"
                        if name == "approval_retry":
                            services.decide_leave(context, **kwargs)
                        suffix = "reject" if name == "reject_leave" else "approve"
                        path = f"/hr/leave/{target_id}/{suffix}/"
    return (
        lambda supplied_context: getattr(owner, function_name)(supplied_context, *args, **kwargs),
        context,
        path,
        target_id,
    )


@pytest.mark.parametrize("operation", REQUIRED)
@pytest.mark.parametrize("execution", ["default", "selected"])
def test_non_superuser_valid_public_section_ten_calls(
    permission_world, operation, execution, django_db_blocker, monkeypatch
):
    call, context, _, _ = _prepare(operation, permission_world)
    if execution == "default":
        assert call(context) is not None
        return
    # New independently resolved connection, same disposable synthetic test DB.
    # Fixture creation precedes the trap; the invocation takes only IDs/scalars.
    alias = "hr_permission_selected"
    default = connections["default"]
    config = dict(default.settings_dict)
    config["TEST"] = dict(config.get("TEST", {}))
    connections.databases[alias] = config

    def forbidden_default(*args, **kwargs):
        pytest.fail(f"{operation} attempted the default cursor under selected execution")

    try:
        with django_db_blocker.unblock(), monkeypatch.context() as patched:
            patched.setattr(default, "cursor", forbidden_default)
            with database_execution(alias):
                assert call(context) is not None
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]


@pytest.mark.parametrize(
    "operation,missing", [(name, code) for name, codes in REQUIRED.items() for code in codes]
)
def test_each_individual_compound_code_is_required_and_denial_has_no_native_effect(
    permission_world, operation, missing
):
    call, context, _, _ = _prepare(operation, permission_world)
    RolePermission.objects.filter(permission__code=missing).delete()
    before = _native()
    with pytest.raises(PermissionDenied):
        call(context)
    assert _native() == before


@pytest.mark.parametrize(
    "missing,operation",
    [
        (DV, "create_department"),
        (DM, "create_department"),
        (LV, "create_leave_type"),
        (LM, "create_leave_type"),
        (EV, "create_employee"),
        (EM, "create_employee"),
        (AV, "record_attendance"),
        (AR, "record_attendance"),
        (AC, "correct_attendance"),
        (LR, "create_leave"),
        (LA, "approve_leave"),
        (LC, "cancel_draft"),
    ],
)
@pytest.mark.parametrize("namespace_state", ["retired", "absent"])
def test_superuser_does_not_bypass_missing_or_retired_registered_code(
    permission_world, missing, operation, namespace_state
):
    call, _, _, _ = _prepare(operation, permission_world)
    superuser = get_user_model().objects.create_superuser("permission-su@example.test", "unused")
    context = BusinessContext(actor_id=superuser.pk, company_id=permission_world["company"].pk)
    permission = Permission.objects.get(code=missing)
    if namespace_state == "retired":
        permission.is_active = False
        permission.save(update_fields=["is_active"])
    else:
        RolePermission.objects.filter(permission=permission).delete()
        permission.delete()
    before = _native()
    with pytest.raises(PermissionDenied):
        call(context)
    assert _native() == before


# Every independently different action surface, without duplicate retry URLs.
HTTP_OPERATIONS = (
    "department_page",
    "department_detail",
    "create_department",
    "update_department",
    "leave_type_page",
    "leave_type_detail",
    "create_leave_type",
    "update_leave_type",
    "employee_page",
    "employee_detail",
    "create_employee",
    "update_employee",
    "update_employee_department",
    "transfer_employee_branch",
    "end_employee",
    "attendance_page",
    "attendance_detail",
    "revision_page",
    "record_attendance",
    "correct_attendance",
    "void_attendance",
    "reinstate_attendance",
    "leave_page",
    "leave_detail",
    "create_leave",
    "update_leave",
    "submit_leave",
    "approve_leave",
    "reject_leave",
    "cancel_draft",
    "cancel_submitted",
    "cancel_approved",
)


def _client(client, context):
    module, _ = BusinessModule.objects.get_or_create(
        code="hr", defaults={"name": "Human Resources", "version": "0.1.0"}
    )
    module.is_enabled = True
    module.save()
    client.force_login(get_user_model().objects.get(pk=context.actor_id))
    session = client.session
    session["businessos_company_id"] = str(context.company_id)
    session.save()
    return client


@pytest.mark.parametrize("operation", HTTP_OPERATIONS)
def test_corresponding_get_surfaces_allow_valid_non_superuser_without_effect(
    permission_world, client, operation
):
    _, context, path, _ = _prepare(operation, permission_world)
    client = _client(client, context)
    before = _native()
    response = client.get(path)
    assert response.status_code == 200
    assert _native() == before


@pytest.mark.parametrize(
    "operation,missing", [(name, code) for name in HTTP_OPERATIONS for code in REQUIRED[name]]
)
def test_corresponding_get_requires_each_individual_code_before_rendering_form(
    permission_world, client, operation, missing
):
    _, context, path, _ = _prepare(operation, permission_world)
    client = _client(client, context)
    RolePermission.objects.filter(permission__code=missing).delete()
    before = _native()
    response = client.get(path)
    assert response.status_code == 403
    assert _native() == before
    if operation not in {
        "department_page",
        "department_detail",
        "leave_type_page",
        "leave_type_detail",
        "employee_page",
        "employee_detail",
        "attendance_page",
        "attendance_detail",
        "revision_page",
        "leave_page",
        "leave_detail",
    }:
        # POST admission is independently enforced before validating any fields;
        # an empty form must not downgrade missing authority into a form error.
        assert client.post(path, {}).status_code == 403
        assert _native() == before


@pytest.fixture
def other_company_world(permission_world):
    company = permission_world["company"]
    other = Company.objects.create(
        code="OTHER-PERM",
        name="Other permission Company",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    actor_id = permission_world["context"].actor_id
    UserCompanyAccess.objects.create(user_id=actor_id, company=other)
    role = Role.objects.create(company=other, code="HR-OTHER", name="Other Company HR")
    for permission in Permission.objects.filter(code__startswith="hr."):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user_id=actor_id, company=other, role=role)
    context = BusinessContext(actor_id=actor_id, company_id=other.pk)
    person = Party.objects.create(
        company=other, party_type="person", display_name="Foreign confidential person"
    )
    department = services.create_department(context, code="FOREIGN", name="Foreign Department")
    leave_type = services.create_leave_type(context, code="FOREIGN", name="Foreign Leave")
    employee = services.create_employee(
        context, party_id=person.pk, employee_number="FOREIGN", joining_date=date(2020, 1, 1)
    )
    attendance = services.record_attendance(
        context,
        employee_id=employee.id,
        request_key=uuid4(),
        start_at=datetime(2024, 1, 1, tzinfo=UTC),
        end_at=datetime(2024, 1, 1, 1, tzinfo=UTC),
    )
    leave = services.create_leave(
        context,
        employee_id=employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2024, 2, 1),
        end_date=date(2024, 2, 2),
    )
    branch = Branch.objects.create(company=other, code="FOREIGN", name="Foreign Branch")
    return {
        "company": other,
        "person": person,
        "department": department,
        "leave_type": leave_type,
        "employee": employee,
        "attendance": attendance.attendance,
        "leave": leave.leave,
        "branch": branch,
    }


@pytest.mark.parametrize(
    "surface,entity",
    [
        ("department_detail", "department"),
        ("leave_type_detail", "leave_type"),
        ("employee_detail", "employee"),
        ("attendance_detail", "attendance"),
        ("revision_page", "attendance"),
        ("leave_detail", "leave"),
    ],
)
def test_every_direct_selector_rejects_foreign_identity_even_when_actor_has_both_companies(
    permission_world, other_company_world, surface, entity
):
    before = _native()
    with pytest.raises(PermissionDenied):
        getattr(selectors, surface)(permission_world["context"], other_company_world[entity].id)
    assert _native() == before


@pytest.mark.parametrize(
    "surface",
    [
        "department_page",
        "leave_type_page",
        "leave_type_choices",
        "employee_page",
        "attendance_page",
        "leave_page",
        "person_choices",
    ],
)
@pytest.mark.parametrize("search", ["", "Foreign"])
def test_every_payload_list_search_and_choice_excludes_other_company(
    permission_world, other_company_world, surface, search
):
    kwargs = {"search": search}
    if surface in {"attendance_page", "leave_page"}:
        kwargs.update(start_date=date(2024, 1, 1), end_date=date(2024, 3, 1))
    page = getattr(selectors, surface)(permission_world["context"], **kwargs)
    foreign = {str(row.id) for row in other_company_world.values() if hasattr(row, "id")}
    assert not foreign.intersection(
        str(row["id"] if isinstance(row, Mapping) else row.id) for row in page.object_list
    )
    assert "Foreign" not in str(page.object_list)
    if search:
        assert page.paginator.count == 0


def test_employee_detail_omits_real_department_without_dv(permission_world):
    employee = permission_world["employee"]
    services.update_employee(
        permission_world["context"],
        employee_id=employee.id,
        expected_revision=1,
        department_id=permission_world["department"].id,
    )
    RolePermission.objects.filter(permission__code=DV).delete()
    detail = selectors.employee_detail(permission_world["context"], employee.id)
    assert "department_id" not in detail.values
    assert "department" not in detail.values


def test_duplicate_leave_create_is_conflict_not_an_invented_success_receipt(permission_world):
    call, context, _, _ = _prepare("create_leave", permission_world)
    call(context)
    before = _native()
    with pytest.raises(ValidationError, match="create key already exists"):
        call(context)
    assert _native() == before


@pytest.mark.parametrize(
    "operation",
    [
        "update_department",
        "update_leave_type",
        "create_employee_party",
        "create_employee_department",
        "create_employee_branch",
        "update_employee",
        "update_employee_department",
        "transfer_employee_branch",
        "transfer_foreign_branch",
        "end_employee",
        "record_attendance",
        "correct_attendance",
        "void_attendance",
        "reinstate_attendance",
        "create_leave",
        "create_leave_type_reference",
        "update_leave",
        "submit_leave",
        "approve_leave",
        "reject_leave",
        "cancel_leave",
    ],
)
def test_all_mutation_families_reject_foreign_parents_and_references_without_effect(
    permission_world, other_company_world, operation
):
    own, other = permission_world, other_company_world
    context = own["context"]
    function = operation
    if operation in {"update_department", "update_leave_type"}:
        kind = "department" if operation == "update_department" else "leave_type"
        kwargs = {
            f"{kind}_id": other[kind].id,
            "expected_revision": 1,
            "name": "Foreign rewrite denied",
            "is_active": True,
        }
    elif operation.startswith("create_employee"):
        function = "create_employee"
        person = Party.objects.create(
            company=own["company"], party_type="person", display_name="Unused own person"
        )
        kwargs = {
            "party_id": other["person"].pk if operation.endswith("_party") else person.pk,
            "employee_number": "FOREIGN-INPUT",
            "joining_date": date(2020, 1, 1),
        }
        if operation.endswith("_department"):
            kwargs["department_id"] = other["department"].id
        elif operation.endswith("_branch"):
            kwargs["branch_id"] = other["branch"].pk
    elif operation in {
        "update_employee",
        "update_employee_department",
        "transfer_employee_branch",
        "transfer_foreign_branch",
        "end_employee",
    }:
        kwargs = {"employee_id": other["employee"].id, "expected_revision": 1}
        if operation == "update_employee_department":
            function = "update_employee"
            kwargs.update(employee_id=own["employee"].id, department_id=other["department"].id)
        elif operation == "transfer_foreign_branch":
            function = "transfer_employee_branch"
            kwargs.update(employee_id=own["employee"].id, branch_id=other["branch"].pk)
        elif operation == "transfer_employee_branch":
            kwargs["branch_id"] = None
        elif operation == "end_employee":
            kwargs["leaving_date"] = date(2025, 1, 1)
        else:
            kwargs["joining_date"] = date(2019, 1, 1)
    elif operation == "record_attendance":
        kwargs = {
            "employee_id": other["employee"].id,
            "request_key": uuid4(),
            "start_at": datetime(2024, 3, 1, tzinfo=UTC),
            "end_at": datetime(2024, 3, 1, 1, tzinfo=UTC),
        }
    elif operation.endswith("_attendance"):
        function = "revise_attendance"
        effect = operation.split("_")[0].upper()
        kwargs = {
            "attendance_id": other["attendance"].id,
            "expected_revision": 1,
            "request_key": uuid4(),
            "operation": effect,
            "reason": "Foreign denied",
        }
        if effect != "VOID":
            kwargs.update(
                start_at=datetime(2024, 1, 1, tzinfo=UTC),
                end_at=datetime(2024, 1, 1, 2, tzinfo=UTC),
            )
    elif operation.startswith("create_leave"):
        function = "create_leave"
        kwargs = {
            "employee_id": other["employee"].id
            if operation == "create_leave"
            else own["employee"].id,
            "create_request_key": uuid4(),
            "leave_type_id": other["leave_type"].id,
            "start_date": date(2024, 3, 1),
            "end_date": date(2024, 3, 2),
        }
    elif operation == "update_leave":
        kwargs = {
            "leave_id": other["leave"].id,
            "expected_revision": 1,
            "leave_type_id": other["leave_type"].id,
            "start_date": date(2024, 2, 1),
            "end_date": date(2024, 2, 2),
            "reason": "Foreign denied",
        }
    else:
        kwargs = {"leave_id": other["leave"].id, "expected_revision": 1, "request_key": uuid4()}
        if operation in {"approve_leave", "reject_leave"}:
            function = "decide_leave"
            kwargs["decision"] = "APPROVED" if operation == "approve_leave" else "REJECTED"
            kwargs["reason"] = "Foreign decision denied"
        elif operation == "cancel_leave":
            kwargs["reason"] = "Foreign denied"
    before = _native()
    reference_validation = operation in {
        "create_employee_party",
        "create_employee_department",
        "create_employee_branch",
        "update_employee_department",
        "transfer_foreign_branch",
        "create_leave_type_reference",
    }
    with pytest.raises(ValidationError if reference_validation else PermissionDenied):
        getattr(services, function)(context, **kwargs)
    assert _native() == before


@pytest.mark.parametrize(
    "operation,entity",
    [
        ("update_department", "department"),
        ("update_leave_type", "leave_type"),
        ("update_employee", "employee"),
        ("end_employee", "employee"),
        ("transfer_employee_branch", "employee"),
        ("revise_attendance", "attendance"),
        ("update_leave", "leave"),
        ("submit_leave", "leave"),
        ("decide_leave", "leave"),
        ("cancel_leave", "leave"),
    ],
)
def test_every_existing_target_action_admission_rejects_foreign_ids(
    permission_world, other_company_world, operation, entity
):
    before = _native()
    with pytest.raises(PermissionDenied):
        selectors.action_admission(
            permission_world["context"], operation, object_id=other_company_world[entity].id
        )
    assert _native() == before


def test_user_choices_exclude_an_identity_with_only_other_company_access(
    permission_world, other_company_world
):
    user = get_user_model().objects.create_user("foreign-only@example.test", "unused")
    UserCompanyAccess.objects.create(user=user, company=other_company_world["company"])
    result = selectors.user_association_choices(permission_world["context"])
    identifiers = {key for key, _ in result.object_list}
    assert user.pk not in identifiers
    assert permission_world["context"].actor_id in identifiers


@pytest.mark.parametrize("operation", ["create_employee", "record_attendance", "create_leave"])
def test_action_choices_exclude_other_company_payloads_and_relationships(
    permission_world, other_company_world, operation
):
    result = selectors.action_admission(permission_world["context"], operation)
    foreign_ids = {row.id for row in other_company_world.values() if hasattr(row, "id")}
    for field, choices in result["choices"].items():
        if field != "user_id":  # User is global; Company eligibility is independently tested.
            assert not foreign_ids.intersection(key for key, _ in choices)
    assert "Foreign" not in str(result["choices"])


@pytest.mark.parametrize(
    "model,field,foreign_entity,detail,page",
    [
        (Employee, "party", "person", "employee_detail", "employee_page"),
        (Employee, "department", "department", "employee_detail", "employee_page"),
        (Employee, "branch", "branch", "employee_detail", "employee_page"),
        (Attendance, "employee", "employee", "attendance_detail", "attendance_page"),
        (Attendance, "branch", "branch", "attendance_detail", "attendance_page"),
        (AttendanceRevision, "employee", "employee", "attendance_detail", "attendance_page"),
        (AttendanceRevision, "company", "company", "attendance_detail", "attendance_page"),
        (LeaveRequest, "employee", "employee", "leave_detail", "leave_page"),
        (LeaveRequest, "leave_type", "leave_type", "leave_detail", "leave_page"),
        (LeaveRequest, "branch", "branch", "leave_detail", "leave_page"),
    ],
)
def test_raw_malformed_native_relationships_fail_closed_on_detail_and_list(
    permission_world, other_company_world, model, field, foreign_entity, detail, page
):
    own = permission_world
    if model is Employee:
        row = Employee.objects.get(pk=own["employee"].id)
        parent_id = row.pk
    elif model in {Attendance, AttendanceRevision}:
        original = services.record_attendance(
            own["context"],
            employee_id=own["employee"].id,
            request_key=uuid4(),
            start_at=datetime(2024, 1, 1, tzinfo=UTC),
            end_at=datetime(2024, 1, 1, 1, tzinfo=UTC),
        )
        parent_id = original.attendance.id
        row = (
            model.objects.get(pk=parent_id)
            if model is Attendance
            else model.objects.get(attendance_id=parent_id)
        )
    else:
        original = services.create_leave(
            own["context"],
            employee_id=own["employee"].id,
            create_request_key=uuid4(),
            leave_type_id=own["leave_type"].id,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 2),
        )
        parent_id = original.leave.id
        row = LeaveRequest.objects.get(pk=parent_id)
    connection = connections["default"]
    native_field = model._meta.get_field(field)
    foreign_id = other_company_world[foreign_entity].id
    # Raw synthetic corruption is deliberately outside the guarded ordinary API.
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {connection.ops.quote_name(model._meta.db_table)} "
            f"SET {connection.ops.quote_name(native_field.column)}=%s WHERE id=%s",
            [
                native_field.get_db_prep_save(foreign_id, connection),
                model._meta.pk.get_db_prep_value(row.pk, connection),
            ],
        )
    before = _native()
    with pytest.raises(ValidationError):
        getattr(selectors, detail)(own["context"], parent_id)
    kwargs = {}
    if page in {"attendance_page", "leave_page"}:
        kwargs.update(start_date=date(2024, 1, 1), end_date=date(2024, 3, 1))
    with pytest.raises(ValidationError):
        getattr(selectors, page)(own["context"], **kwargs)
    assert _native() == before


@pytest.mark.parametrize(
    "operation,change",
    [
        ("update_employee", "branch"),
        ("record_attendance", "branch"),
        ("create_leave", "branch"),
        ("record_attendance", "status"),
        ("create_leave", "status"),
    ],
)
def test_action_admission_rechecks_actual_employee_after_candidate_discovery(
    permission_world, operation, change
):
    from django.db.models.query import QuerySet

    world = permission_world
    services.transfer_employee_branch(
        world["context"],
        employee_id=world["employee"].id,
        expected_revision=1,
        branch_id=world["branch"].pk,
    )
    UserBranchAccess.objects.create(user_id=world["context"].actor_id, branch=world["branch"])
    other_branch = Branch.objects.create(company=world["company"], code="OTHER", name="Other")
    context = BusinessContext(
        actor_id=world["context"].actor_id,
        company_id=world["context"].company_id,
        branch_id=world["branch"].pk,
    )
    original = QuerySet._fetch_all
    changed = False
    before = _native()

    def change_before_protected_employee_read(query):
        nonlocal changed
        if query.model is Employee and query.query.select_for_update and not changed:
            changed = True
            connection = connections["default"]
            pk = Employee._meta.pk.get_db_prep_value(world["employee"].id, connection)
            with connection.cursor() as cursor:
                if change == "branch":
                    branch = Employee._meta.get_field("branch").get_db_prep_save(
                        other_branch.pk, connection
                    )
                    cursor.execute("UPDATE hr_employee SET branch_id=%s WHERE id=%s", [branch, pk])
                else:
                    cursor.execute(
                        "UPDATE hr_employee SET status='ENDED', leaving_date=%s WHERE id=%s",
                        [date(2024, 1, 1), pk],
                    )
        return original(query)

    with patch.object(QuerySet, "_fetch_all", change_before_protected_employee_read):
        with pytest.raises((PermissionDenied, ValidationError)):
            selectors.action_admission(
                context,
                operation,
                object_id=world["employee"].id if operation == "update_employee" else None,
            )
    assert changed
    assert _native() == before
    # This is an actual persisted, deterministic functional interleaving. It is
    # deliberately NOT advertised as a supported-writer PostgreSQL lock race.
