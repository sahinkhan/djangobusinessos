from datetime import date
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from businessos.core.access.models import Role, RolePermission, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.modules.hr import services
from businessos.modules.hr.manifest import HR_PERMISSION_DECLARATIONS
from businessos.modules.hr.models import Department, Employee
from businessos.modules.party.models import Party

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def hr_context(company, operator):
    role = Role.objects.create(company=company, code="HR-OPERATOR", name="Synthetic HR operator")
    from businessos.core.access.models import Permission

    for code, _ in HR_PERMISSION_DECLARATIONS:
        permission, _ = Permission.objects.get_or_create(code=code, defaults={"name": code})
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return BusinessContext(actor_id=operator.pk, company_id=company.pk)


@pytest.fixture
def hr_person(company):
    return Party.objects.create(
        company=company, party_type=Party.Type.PERSON, display_name="Synthetic Person"
    )


def test_setup_lifecycle_noop_retirement_and_audit(hr_context):
    row = services.create_department(hr_context, code=" dev ", name="Engineering")
    assert row.code == "DEV" and row.revision == 1
    same = services.update_department(
        hr_context, department_id=row.id, expected_revision=1, name=row.name, is_active=True
    )
    assert same.revision == 1
    retired = services.update_department(
        hr_context, department_id=row.id, expected_revision=1, name="Development", is_active=False
    )
    assert retired.revision == 2 and not retired.is_active
    assert sorted(
        AuditEntry.objects.filter(object_id=str(row.id)).values_list("action", flat=True)
    ) == ["hr.department.created", "hr.department.updated"]
    with pytest.raises(ValidationError):
        services.create_department(hr_context, code="DEV", name="Reused")
    with pytest.raises(ValidationError):
        services.update_department(
            hr_context, department_id=row.id, expected_revision=1, name="Stale", is_active=True
        )


@pytest.mark.parametrize("code", ["", "a b", "é", "ß", "X" * 33, None, True])
def test_setup_strict_inputs(hr_context, code):
    with pytest.raises(ValidationError):
        services.create_department(hr_context, code=code, name="Synthetic")
    assert not Department.objects.exists()


def test_setup_requires_compound_permission(hr_context):
    RolePermission.objects.filter(permission__code="hr.department.view").delete()
    with pytest.raises(PermissionDenied):
        services.create_department(hr_context, code="D", name="Denied")
    assert not Department.objects.exists()


def test_employee_identity_associations_transfer_end(hr_context, hr_person, branch):
    department = services.create_department(hr_context, code="D", name="Department")
    row = services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number=" e-1 ",
        joining_date=date(2020, 1, 1),
        department_id=department.id,
    )
    assert row.employee_number == "E-1" and row.party["display_name"] == hr_person.display_name
    moved = services.transfer_employee_branch(
        hr_context, employee_id=row.id, expected_revision=1, branch_id=branch.pk
    )
    assert moved.branch_id == branch.pk and moved.revision == 2
    with pytest.raises(ValidationError):
        services.update_department(
            hr_context,
            department_id=department.id,
            expected_revision=1,
            name="Retired",
            is_active=False,
        )
    ended = services.end_employee(
        hr_context, employee_id=row.id, expected_revision=2, leaving_date=date(2025, 1, 1)
    )
    assert ended.status == "ENDED" and ended.revision == 3
    assert (
        services.end_employee(
            hr_context, employee_id=row.id, expected_revision=3, leaving_date=date(2025, 1, 1)
        ).revision
        == 3
    )
    with pytest.raises(ValidationError):
        services.update_employee(
            hr_context, employee_id=row.id, expected_revision=3, status="ACTIVE"
        )
    with pytest.raises(ValidationError):
        services.create_employee(
            hr_context,
            party_id=hr_person.pk,
            employee_number="OTHER",
            joining_date=date(2020, 1, 1),
        )


def test_new_user_link_requires_company_access(hr_context, hr_person):
    other = get_user_model().objects.create_user("synthetic-other@example.test", "unused")
    with pytest.raises(ValidationError):
        services.create_employee(
            hr_context,
            party_id=hr_person.pk,
            employee_number="E",
            joining_date=date(2020, 1, 1),
            user_id=other.pk,
        )
    assert not Employee.objects.exists()
    assert not AuditEntry.objects.filter(action="hr.employee.created").exists()


def test_noop_still_requires_current_authority(hr_context, hr_person):
    row = services.create_employee(
        hr_context, party_id=hr_person.pk, employee_number="E", joining_date=date(2020, 1, 1)
    )
    RolePermission.objects.filter(permission__code="hr.employee.manage").delete()
    with pytest.raises(PermissionDenied):
        services.update_employee(hr_context, employee_id=row.id, expected_revision=1)
    assert Employee.objects.get(pk=row.id).revision == 1


def test_audit_failure_rolls_back_owner_effect(hr_context):
    with patch(
        "businessos.modules.hr.support.record_audit_entry",
        side_effect=RuntimeError("synthetic audit failure"),
    ):
        with pytest.raises(RuntimeError, match="synthetic audit"):
            services.create_department(hr_context, code="D", name="Department")
    assert not Department.objects.exists()


def test_branch_context_cannot_mutate_company_setup(hr_context, branch):
    from businessos.core.access.models import UserBranchAccess

    UserBranchAccess.objects.create(user_id=hr_context.actor_id, branch=branch)
    context = BusinessContext(
        actor_id=hr_context.actor_id, company_id=hr_context.company_id, branch_id=branch.pk
    )
    with pytest.raises(PermissionDenied):
        services.create_department(context, code="D", name="Denied")


@pytest.mark.parametrize("revision", [True, 1.0, "1", 0, -1, 2_147_483_648])
def test_expected_revision_is_exact_positive_integer(hr_context, revision):
    row = services.create_department(hr_context, code="D", name="Department")
    with pytest.raises(ValidationError):
        services.update_department(
            hr_context,
            department_id=row.id,
            expected_revision=revision,
            name="Invalid",
            is_active=True,
        )
    assert Department.objects.get(pk=row.id).revision == 1
