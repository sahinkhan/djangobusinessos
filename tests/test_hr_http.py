"""HR HTTP adapters, stale scope, trusted civil-time inputs and bounded pages."""

from datetime import UTC, date, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from django.core.exceptions import ValidationError

from businessos.modules.hr.forms import (
    AttendanceForm,
    EmployeeForm,
    EndEmployeeForm,
    FrozenDateTimeField,
    LeaveActionForm,
    LeaveForm,
    SetupForm,
    TransferEmployeeForm,
)


@pytest.fixture
def hr_http(transactional_db, company, operator, client):
    from businessos.core.access.models import Permission, Role, RolePermission, UserRoleAssignment
    from businessos.core.common.context import BusinessContext
    from businessos.core.modules.models import BusinessModule
    from businessos.modules.hr.manifest import HR_PERMISSION_DECLARATIONS

    role = Role.objects.create(company=company, code="HR-HTTP", name="HR HTTP synthetic operator")
    for code, _ in HR_PERMISSION_DECLARATIONS:
        permission, _ = Permission.objects.get_or_create(code=code, defaults={"name": code})
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    module, _ = BusinessModule.objects.get_or_create(
        code="hr", defaults={"name": "Human Resources", "version": "0.1.0"}
    )
    module.is_enabled = True
    module.save()
    client.force_login(operator)
    session = client.session
    session["businessos_company_id"] = str(company.pk)
    session.save()
    return client, BusinessContext(actor_id=operator.pk, company_id=company.pk)


@pytest.fixture
def http_employee(hr_http, company):
    from businessos.modules.hr import services
    from businessos.modules.party.models import Party

    person = Party.objects.create(
        company=company, party_type="person", display_name="<script>" + "X" * 180
    )
    _, context = hr_http
    return services.create_employee(
        context, party_id=person.pk, employee_number="UI-1", joining_date=date(2020, 1, 1)
    )


@pytest.mark.parametrize("utc_hour", [5, 6])
def test_hr_trusted_unchanged_fold_preserves_exact_instant(utc_hour):
    original = datetime(2026, 11, 1, utc_hour, 30, 45, 123456, tzinfo=UTC)
    field = FrozenDateTimeField(business_timezone=ZoneInfo("America/New_York"), original=original)
    result = field.clean("2026-11-01T01:30")
    assert result is original
    assert result.astimezone(ZoneInfo("America/New_York")).fold == utc_hour - 5
    changed = field.clean("2026-11-01T03:00")
    assert changed.astimezone(UTC) == datetime(2026, 11, 1, 8, tzinfo=UTC)
    assert (changed.second, changed.microsecond) == (0, 0)


@pytest.mark.parametrize("raw", ["2026-11-01T01:30", "2026-03-08T02:30"])
def test_hr_new_ambiguous_or_nonexistent_local_time_rejects(raw):
    field = FrozenDateTimeField(business_timezone=ZoneInfo("America/New_York"))
    with pytest.raises(ValidationError):
        field.clean(raw)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "form_type,extra",
    [
        (SetupForm, {}),
        (EmployeeForm, {}),
        (EndEmployeeForm, {}),
        (TransferEmployeeForm, {}),
        (AttendanceForm, {"zone": "UTC"}),
        (LeaveForm, {}),
        (LeaveActionForm, {"operation": "submit_leave"}),
        (LeaveActionForm, {"operation": "reject_leave"}),
        (LeaveActionForm, {"operation": "cancel_leave"}),
    ],
)
def test_every_hr_form_family_rejects_stale_company(company, form_type, extra):
    form = form_type(
        {"scope_company_id": str(uuid4()), "scope_branch_id": ""}, company_id=company.pk, **extra
    )
    assert not form.is_valid()
    assert "Company scope changed" in str(form.non_field_errors())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "rendered,submitted", [(None, "foreign"), ("selected", ""), ("selected", "foreign")]
)
def test_every_hr_form_rechecks_rendered_branch_scope(company, rendered, submitted):
    branch_id, foreign = uuid4(), uuid4()
    form = SetupForm(
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": str(foreign) if submitted == "foreign" else "",
            "code": "A",
            "name": "Test",
        },
        company_id=company.pk,
        branch_id=branch_id if rendered else None,
    )
    assert not form.is_valid()
    assert "Branch scope changed" in str(form.non_field_errors())


@pytest.mark.django_db
def test_hr_choice_adapter_accepts_only_bounded_admitted_identities(company):
    person = uuid4()
    form = EmployeeForm(
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": "",
            "party_id": str(uuid4()),
            "employee_number": "PERSON-1",
            "joining_date": "2020-01-01",
            "user_id": "",
            "department_id": "",
            "branch_id": "",
        },
        company_id=company.pk,
        choices={"party_id": [(person, "Permitted Person")]},
    )
    assert not form.is_valid()
    assert "party_id" in form.errors


def test_hr_module_gating_and_no_get_mutation(hr_http):
    from businessos.core.modules.models import BusinessModule
    from businessos.modules.hr.models import Department

    client, _ = hr_http
    before = Department.objects.count()
    response = client.get("/hr/departments/new/")
    assert response.status_code == 200
    assert Department.objects.count() == before
    module = BusinessModule.objects.get(code="hr")
    module.is_enabled = False
    module.save()
    assert client.get("/hr/").status_code == 404
    assert client.post("/hr/departments/new/", {}).status_code == 404
    assert Department.objects.count() == before


def test_hr_setup_form_uses_real_service_and_stale_company_does_not_write(hr_http, company):
    from businessos.modules.hr.models import Department

    client, _ = hr_http
    wrong = client.post(
        "/hr/departments/new/",
        {
            "scope_company_id": str(uuid4()),
            "scope_branch_id": "",
            "code": "UI",
            "name": "UI Department",
        },
    )
    assert wrong.status_code == 400
    assert not Department.objects.exists()
    result = client.post(
        "/hr/departments/new/",
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": "",
            "code": "UI",
            "name": "UI Department",
        },
    )
    assert result.status_code == 302
    row = Department.objects.get(code="UI")
    assert result.url == f"/hr/departments/{row.pk}/"
    assert client.get(result.url).status_code == 200


def test_hr_action_get_requires_complete_permissions_before_form(hr_http):
    from businessos.core.access.models import RolePermission

    client, _ = hr_http
    RolePermission.objects.filter(permission__code="hr.employee.manage").delete()
    assert client.get("/hr/employees/new/").status_code == 403
    assert client.get("/hr/").status_code == 200


def test_hr_employee_detail_escapes_long_person_name(hr_http, http_employee):
    client, _ = hr_http
    response = client.get(f"/hr/employees/{http_employee.id}/")
    assert response.status_code == 200
    assert b"&lt;script&gt;" in response.content
    assert b"<script>" not in response.content
    assert b"overflow-wrap:anywhere" in response.content


def test_hr_employee_lists_pagination_and_query_preservation(hr_http, http_employee):
    client, _ = hr_http
    response = client.get("/hr/?q=UI&status=ACTIVE&page=1")
    assert response.status_code == 200
    page = response.context["page_obj"]
    assert page.paginator.per_page == 50
    assert tuple(row.id for row in page.object_list) == (http_employee.id,)
    assert response.context["filter_form"].cleaned_data["q"] == "UI"
    assert b'id="list-results"' in response.content
    assert b"data-list-filter" in response.content
    assert b'<td class="whitespace-nowrap">ACTIVE</td>' in response.content


def test_hr_post_requires_csrf(hr_http, company):
    from django.test import Client

    client, _ = hr_http
    protected = Client(enforce_csrf_checks=True)
    protected.cookies = client.cookies
    response = protected.post(
        "/hr/departments/new/",
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": "",
            "code": "DENIED",
            "name": "CSRF denied",
        },
    )
    assert response.status_code == 403


@pytest.mark.parametrize(
    "path",
    [
        "/hr/",
        "/hr/departments/",
        "/hr/leave-types/",
        "/hr/attendance/",
        "/hr/leave/",
        "/hr/employees/new/",
        "/hr/departments/new/",
        "/hr/leave-types/new/",
        "/hr/attendance/new/",
        "/hr/leave/new/",
    ],
)
def test_hr_minimum_read_and_creation_surfaces_render(hr_http, path):
    client, _ = hr_http
    response = client.get(path)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "path,code",
    [
        ("/hr/employees/new/", "hr.employee.view"),
        ("/hr/departments/new/", "hr.department.manage"),
        ("/hr/departments/new/", "hr.department.view"),
        ("/hr/leave-types/new/", "hr.leave_type.manage"),
        ("/hr/leave-types/new/", "hr.leave.view"),
        ("/hr/attendance/new/", "hr.attendance.record"),
        ("/hr/attendance/new/", "hr.attendance.view"),
        ("/hr/attendance/new/", "hr.employee.view"),
        ("/hr/leave/new/", "hr.leave.request"),
        ("/hr/leave/new/", "hr.leave.view"),
        ("/hr/leave/new/", "hr.employee.view"),
    ],
)
def test_hr_each_creation_get_compound_permission_is_required(hr_http, path, code):
    from businessos.core.access.models import RolePermission

    client, _ = hr_http
    RolePermission.objects.filter(permission__code=code).delete()
    assert client.get(path).status_code == 403


def test_invalid_hr_filter_is_visible_and_not_silently_applied(hr_http, http_employee):
    client, _ = hr_http
    response = client.get("/hr/?q=" + "X" * 201)
    assert response.status_code == 400
    assert not response.context["page_obj"].object_list
    assert response.context["filter_form"].errors


def test_hr_navigation_hidden_when_module_disabled(hr_http):
    from businessos.core.modules.models import BusinessModule

    client, _ = hr_http
    response = client.get("/")
    assert b'href="/hr/"' in response.content
    module = BusinessModule.objects.get(code="hr")
    module.is_enabled = False
    module.save()
    response = client.get("/")
    assert b'href="/hr/"' not in response.content


@pytest.fixture
def hr_http_documents(hr_http, http_employee):
    from businessos.modules.hr import services

    _, context = hr_http
    department = services.create_department(context, code="HTTP", name="HTTP Department")
    leave_type = services.create_leave_type(context, code="HTTP", name="HTTP Leave")
    attendance = services.record_attendance(
        context,
        employee_id=http_employee.id,
        request_key=uuid4(),
        start_at=datetime(2023, 1, 1, 10, tzinfo=UTC),
        end_at=datetime(2023, 1, 1, 11, tzinfo=UTC),
    )
    leave = services.create_leave(
        context,
        employee_id=http_employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2030, 1, 1),
        end_date=date(2030, 1, 2),
        reason="Synthetic HTTP Leave",
    )
    return {
        "employee": str(http_employee.id),
        "department": str(department.id),
        "leave_type": str(leave_type.id),
        "attendance": str(attendance.attendance.id),
        "leave": str(leave.leave.id),
    }


_MUTATION_URLS = [
    "/hr/employees/new/",
    "/hr/employees/{employee}/edit/",
    "/hr/employees/{employee}/end/",
    "/hr/employees/{employee}/transfer/",
    "/hr/departments/new/",
    "/hr/departments/{department}/edit/",
    "/hr/leave-types/new/",
    "/hr/leave-types/{leave_type}/edit/",
    "/hr/attendance/new/",
    "/hr/attendance/{attendance}/correct/",
    "/hr/attendance/{attendance}/void/",
    "/hr/attendance/{attendance}/reinstate/",
    "/hr/leave/new/",
    "/hr/leave/{leave}/edit/",
    "/hr/leave/{leave}/submit/",
    "/hr/leave/{leave}/approve/",
    "/hr/leave/{leave}/reject/",
    "/hr/leave/{leave}/cancel/",
]


def _native_http_snapshot():
    from businessos.core.audit.models import AuditEntry
    from businessos.modules.hr.models import (
        Attendance,
        AttendanceRevision,
        Department,
        Employee,
        LeaveRequest,
        LeaveType,
    )

    return (
        tuple(
            tuple(model.objects.order_by("pk").values())
            for model in (
                Department,
                Employee,
                Attendance,
                AttendanceRevision,
                LeaveType,
                LeaveRequest,
            )
        ),
        AuditEntry.objects.count(),
    )


@pytest.mark.parametrize("path", _MUTATION_URLS)
@pytest.mark.parametrize("scope", ["company", "branch"])
def test_every_actual_hr_http_mutation_rejects_stale_scope_without_effect_or_audit(
    hr_http, hr_http_documents, company, path, scope
):
    client, _ = hr_http
    before = _native_http_snapshot()
    response = client.post(
        path.format(**hr_http_documents),
        {
            "scope_company_id": str(uuid4()) if scope == "company" else str(company.pk),
            "scope_branch_id": str(uuid4()) if scope == "branch" else "",
            "expected_revision": "1",
            "request_key": str(uuid4()),
        },
    )
    assert response.status_code == 400
    expected = "Company scope changed" if scope == "company" else "Branch scope changed"
    assert expected in response.content.decode()
    assert _native_http_snapshot() == before


@pytest.mark.parametrize("path", _MUTATION_URLS)
def test_real_session_branch_switch_cannot_mutate_old_company_wide_form(
    hr_http, hr_http_documents, company, operator, branch, path
):
    from businessos.core.access.models import UserBranchAccess

    client, _ = hr_http
    UserBranchAccess.objects.create(user=operator, branch=branch)
    session = client.session
    session["businessos_branch_id"] = str(branch.pk)
    session.save()
    before = _native_http_snapshot()
    response = client.post(
        path.format(**hr_http_documents),
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": "",
            "expected_revision": "1",
            "request_key": str(uuid4()),
        },
    )
    assert response.status_code in {400, 403}
    assert _native_http_snapshot() == before


@pytest.mark.parametrize("path", _MUTATION_URLS)
def test_real_session_company_switch_cannot_mutate_old_company_form(
    hr_http, hr_http_documents, company, operator, path
):
    from businessos.core.access.models import (
        Permission,
        Role,
        RolePermission,
        UserCompanyAccess,
        UserRoleAssignment,
    )
    from businessos.core.organization.models import Company
    from businessos.modules.hr.manifest import HR_PERMISSION_DECLARATIONS

    client, _ = hr_http
    other = Company.objects.create(
        code="HTTP-OTHER",
        name="Other synthetic Company",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    UserCompanyAccess.objects.create(user=operator, company=other)
    role = Role.objects.create(company=other, code="HR-OTHER", name="Other Company HR")
    for code, _ in HR_PERMISSION_DECLARATIONS:
        RolePermission.objects.create(role=role, permission=Permission.objects.get(code=code))
    UserRoleAssignment.objects.create(user=operator, company=other, role=role)
    session = client.session
    session["businessos_company_id"] = str(other.pk)
    session.save()
    before = _native_http_snapshot()
    response = client.post(
        path.format(**hr_http_documents),
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": "",
            "expected_revision": "1",
            "request_key": str(uuid4()),
        },
    )
    assert response.status_code in {400, 403}
    assert _native_http_snapshot() == before


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["approve_leave", "reject_leave", "cancel_leave"])
def test_leave_action_reason_never_reuses_original_request_narrative(company, operation):
    form = LeaveActionForm(
        company_id=company.pk,
        operation=operation,
        initial={"reason": "Original private request narrative"},
    )
    assert form["reason"].value() in {None, ""}


@pytest.mark.parametrize("utc_hour", [5, 6])
def test_http_correction_uses_trusted_frozen_fold_and_preserves_start_precision(
    hr_http, http_employee, company, utc_hour
):
    from businessos.modules.hr import services
    from businessos.modules.hr.models import AttendanceRevision

    client, context = hr_http
    company.timezone = "America/New_York"
    company.save()
    start = datetime(2025, 11, 2, utc_hour, 30, 45, 123456, tzinfo=UTC)
    end = datetime(2025, 11, 2, utc_hour, 45, 45, 123456, tzinfo=UTC)
    receipt = services.record_attendance(
        context, employee_id=http_employee.id, request_key=uuid4(), start_at=start, end_at=end
    )
    company.timezone = "UTC"
    company.save()
    response = client.get(f"/hr/attendance/{receipt.attendance.id}/correct/")
    assert response.status_code == 200
    form = response.context["form"]
    assert form.fields["start_at"].original == start
    assert form.fields["start_at"].business_timezone.key == "America/New_York"
    assert 'value="2025-11-02T01:30"' in str(form["start_at"])
    result = client.post(
        f"/hr/attendance/{receipt.attendance.id}/correct/",
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": "",
            "expected_revision": "1",
            "request_key": str(uuid4()),
            "reason": "Corrected exact end",
            "start_at": "2025-11-02T01:30",
            "end_at": "2025-11-02T02:00",
            "original_start_at": "2030-01-01T00:00Z",
        },
    )
    assert result.status_code == 302
    revision = AttendanceRevision.objects.get(attendance_id=receipt.attendance.id, number=2)
    assert revision.start_at == start
    assert revision.end_at == datetime(2025, 11, 2, 7, tzinfo=UTC)
    assert revision.start_at.astimezone(ZoneInfo("America/New_York")).fold == utc_hour - 5


def test_hr_header_and_bounded_related_choice_search(hr_http, company):
    from businessos.modules.hr.models import Employee
    from businessos.modules.party.models import Party

    client, _ = hr_http
    for number in range(51):
        Party.objects.create(
            company=company, party_type="person", display_name=f"Person {number:03d}"
        )
    target = Party.objects.create(
        company=company, party_type="person", display_name="Z related target"
    )
    response = client.get("/hr/employees/new/")
    assert response.status_code == 200
    assert str(target.pk) not in {
        str(key) for key, _ in response.context["form"].fields["party_id"].choices
    }
    header = response.content.decode().split('id="bos-current-app"', 1)[1].split("</a>", 1)[0]
    assert "Human Resources" in header
    html = response.content.decode()
    # Choice lookup needs the full content width, not the compact header tools.
    content_start = html.index('<div class="bos-view-content">')
    search_start = html.index('id="hr-choice-search"')
    mutation_start = html.index('id="record-form"')
    assert content_start < search_start < mutation_start
    assert html[search_start:mutation_start].count("</form>") == 1
    assert "record-form w-full min-w-0 max-w-full" in html
    narrowed = client.get("/hr/employees/new/?choices_q=Z%20related%20target")
    assert narrowed.status_code == 200
    assert (str(target.pk), target.display_name) in narrowed.context["form"].fields[
        "party_id"
    ].choices
    result = client.post(
        "/hr/employees/new/?choices_q=Z%20related%20target",
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": "",
            "party_id": str(target.pk),
            "employee_number": "CHOICE-TARGET",
            "joining_date": "2020-01-01",
            "user_id": "",
            "department_id": "",
            "branch_id": "",
        },
    )
    assert result.status_code == 302
    assert Employee.objects.get(employee_number="CHOICE-TARGET").party_id == target.pk
    missing = client.get("/hr/leave/new/?choices_q=no-matching-choice")
    assert missing.status_code == 200
    assert b'name="choices_q"' in missing.content
    too_long = client.get("/hr/employees/new/?choices_q=" + "X" * 201)
    assert too_long.status_code == 400
    assert too_long.context["choice_filter"].errors


def test_leave_required_employee_and_type_choice_searches_are_independent(
    hr_http, hr_http_documents, company
):
    from businessos.modules.hr.models import LeaveRequest

    client, _ = hr_http
    path = "/hr/leave/new/?employee_q=UI-1&type_q=HTTP"
    response = client.get(path)
    assert response.status_code == 200
    form = response.context["form"]
    assert hr_http_documents["employee"] in {
        str(key) for key, _ in form.fields["employee_id"].choices
    }
    assert hr_http_documents["leave_type"] in {
        str(key) for key, _ in form.fields["leave_type_id"].choices
    }
    assert b'name="employee_q"' in response.content and b'name="type_q"' in response.content
    assert b'name="party_q"' not in response.content
    result = client.post(
        path,
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": "",
            "employee_id": hr_http_documents["employee"],
            "create_request_key": str(uuid4()),
            "leave_type_id": hr_http_documents["leave_type"],
            "start_date": "2030-02-01",
            "end_date": "2030-02-02",
            "reason": "Independent choices",
        },
    )
    assert result.status_code == 302
    assert LeaveRequest.objects.filter(reason="Independent choices").exists()


def test_transfer_form_retains_inactive_current_branch_without_silent_clear(
    hr_http, http_employee, company, branch
):
    from businessos.core.audit.models import AuditEntry
    from businessos.modules.hr import services
    from businessos.modules.hr.models import Employee

    client, context = hr_http
    moved = services.transfer_employee_branch(
        context, employee_id=http_employee.id, expected_revision=1, branch_id=branch.pk
    )
    branch.is_active = False
    branch.save()
    response = client.get(f"/hr/employees/{moved.id}/transfer/?branch_q=no-match")
    assert response.status_code == 200
    form = response.context["form"]
    assert str(branch.pk) in {str(key) for key, _ in form.fields["branch_id"].choices}
    before = AuditEntry.objects.count()
    result = client.post(
        f"/hr/employees/{moved.id}/transfer/?branch_q=no-match",
        {
            "scope_company_id": str(company.pk),
            "scope_branch_id": "",
            "expected_revision": "2",
            "branch_id": str(branch.pk),
        },
    )
    assert result.status_code == 302
    row = Employee.objects.get(pk=moved.id)
    assert (row.branch_id, row.revision) == (branch.pk, 2)
    assert AuditEntry.objects.count() == before
