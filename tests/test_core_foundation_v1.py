from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserBranchAccess,
    UserCompanyAccess,
    UserRoleAssignment,
    UserWarehouseAccess,
)
from businessos.core.access.permissions import CORE_PERMISSION_DECLARATIONS
from businessos.core.access.policies import has_permission, require_permission
from businessos.core.access.services import (
    assign_role,
    create_role,
    grant_branch_access,
    grant_company_access,
    grant_role_permission,
    grant_warehouse_access,
    register_core_permissions,
    revoke_company_access,
    revoke_role,
    revoke_role_permission,
)
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.modules.services import register_manifest
from businessos.core.organization.models import Branch, Company, Warehouse
from businessos.core.organization.time import company_local_date, company_local_datetime
from businessos.core.reference.models import Country, Currency, Language, UnitOfMeasure


@pytest.fixture
def superuser(db):
    return get_user_model().objects.create_superuser("root@example.com", "password")


@pytest.fixture
def admin_context(superuser, company):
    return BusinessContext(actor_id=superuser.id, company_id=company.id)


def create_other_company(company, *, code="OTHER", timezone="UTC"):
    return Company.objects.create(
        code=code,
        name=code.title(),
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
        timezone=timezone,
    )


@pytest.mark.django_db
def test_business_rbac_denies_by_default_and_allows_company_role(
    operator, company, business_context
):
    permission = Permission.objects.create(code="example.record.view", name="View records")
    role = Role.objects.create(company=company, code="VIEWER", name="Viewer")
    RolePermission.objects.create(role=role, permission=permission)

    assert not has_permission(business_context, permission.code)
    with pytest.raises(PermissionDenied, match="example.record.view"):
        require_permission(business_context, permission.code)

    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    assert has_permission(business_context, permission.code)
    assert require_permission(business_context, permission.code) is business_context


@pytest.mark.django_db
def test_role_assignments_are_company_scoped(operator, company):
    other = create_other_company(company)
    UserCompanyAccess.objects.create(user=operator, company=other)
    role = Role.objects.create(company=other, code="SALES_MANAGER", name="Sales Manager")

    with pytest.raises(ValidationError, match="assigned company"):
        UserRoleAssignment.objects.create(user=operator, company=company, role=role)


@pytest.mark.django_db
def test_same_user_can_hold_distinct_roles_in_each_company(operator, company):
    other = create_other_company(company)
    third = create_other_company(company, code="THIRD")
    for scoped_company in (other, third):
        UserCompanyAccess.objects.create(user=operator, company=scoped_company)
    roles = [
        Role.objects.create(company=company, code="ADMIN", name="Administrator"),
        Role.objects.create(company=other, code="SALES", name="Sales Manager"),
        Role.objects.create(company=third, code="VIEWER", name="Viewer"),
    ]
    for role in roles:
        UserRoleAssignment.objects.create(user=operator, company=role.company, role=role)

    assert set(
        UserRoleAssignment.objects.filter(user=operator).values_list("role__code", flat=True)
    ) == {"ADMIN", "SALES", "VIEWER"}


@pytest.mark.django_db
def test_core_management_permissions_bootstrap_and_reregister_idempotently():
    expected = {code for code, _ in CORE_PERMISSION_DECLARATIONS}
    before = {
        permission.code: permission.id
        for permission in Permission.objects.filter(code__in=expected, is_active=True)
    }

    first = register_core_permissions()
    second = register_core_permissions()

    assert set(before) == expected
    assert {permission.code: permission.id for permission in first} == before
    assert {permission.code: permission.id for permission in second} == before

    retired = Permission.objects.get(code="access.role.manage")
    retired.is_active = False
    retired.save()
    register_core_permissions()
    retired.refresh_from_db()
    assert not retired.is_active


@pytest.mark.django_db
def test_delegated_administrator_can_manage_roles_and_organization(
    admin_context, company
):
    delegate = get_user_model().objects.create_user("delegate@example.com", "password")
    managed_user = get_user_model().objects.create_user("managed@example.com", "password")
    grant_company_access(admin_context, user_id=delegate.id)
    administrator = create_role(admin_context, code="ADMINISTRATOR", name="Administrator")
    for permission_code, _ in CORE_PERMISSION_DECLARATIONS:
        grant_role_permission(
            admin_context, role_id=administrator.id, permission_code=permission_code
        )
    assign_role(admin_context, user_id=delegate.id, role_id=administrator.id)
    delegated_context = BusinessContext(actor_id=delegate.id, company_id=company.id)

    assert has_permission(delegated_context, "access.role.manage")
    assert has_permission(delegated_context, "access.organization.manage")
    assert create_role(delegated_context, code="VIEWER", name="Viewer").company == company
    assert grant_company_access(delegated_context, user_id=managed_user.id).company == company


@pytest.mark.django_db
def test_superuser_bypasses_role_grants_only(superuser, company, branch):
    context = BusinessContext(actor_id=superuser.id, company_id=company.id)
    permission = Permission.objects.get(code="access.role.manage")

    assert has_permission(context, permission.code)
    assert not has_permission(context, "unregistered.permission.code")
    with pytest.raises(PermissionDenied, match="unregistered.permission.code"):
        require_permission(context, "unregistered.permission.code")

    permission.is_active = False
    permission.save()
    assert not has_permission(context, permission.code)
    with pytest.raises(PermissionDenied, match="access.role.manage"):
        require_permission(context, permission.code)

    with pytest.raises(ValueError, match="module.resource.action"):
        has_permission(context, "invalid")

    other = create_other_company(company)
    bad_context = BusinessContext(
        actor_id=superuser.id, company_id=other.id, branch_id=branch.id
    )
    with pytest.raises(PermissionDenied, match="outside the selected company"):
        has_permission(bad_context, "access.role.manage")


@pytest.mark.django_db
def test_inactive_actor_and_company_are_denied_before_rbac(operator, company, business_context):
    operator.is_active = False
    operator.save()
    with pytest.raises(PermissionDenied, match="actor"):
        has_permission(business_context, "sales.order.view")
    operator.is_active = True
    operator.save()
    company.is_active = False
    company.save()
    with pytest.raises(PermissionDenied, match="company"):
        has_permission(business_context, "sales.order.view")


@pytest.mark.django_db
def test_grant_revoke_regrant_does_not_resurrect_subordinate_access(
    admin_context, company, branch, warehouse
):
    target = get_user_model().objects.create_user("target@example.com", "password")
    grant_company_access(admin_context, user_id=target.id)
    grant_branch_access(admin_context, user_id=target.id, branch_id=branch.id)
    grant_warehouse_access(admin_context, user_id=target.id, warehouse_id=warehouse.id)
    role = Role.objects.create(company=company, code="VIEWER", name="Viewer")
    UserRoleAssignment.objects.create(user=target, company=company, role=role)

    assert revoke_company_access(admin_context, user_id=target.id)
    grant_company_access(admin_context, user_id=target.id)

    assert UserCompanyAccess.objects.filter(user=target, company=company).exists()
    assert not UserBranchAccess.objects.filter(user=target).exists()
    assert not UserWarehouseAccess.objects.filter(user=target).exists()
    assert not UserRoleAssignment.objects.filter(user=target).exists()


@pytest.mark.django_db
def test_organizational_grants_reject_cross_company_scope(
    admin_context, company, branch, warehouse
):
    target = get_user_model().objects.create_user("target@example.com", "password")
    grant_company_access(admin_context, user_id=target.id)
    other = create_other_company(company)
    other_branch = Branch.objects.create(company=other, code="HQ", name="Other HQ")
    other_warehouse = Warehouse.objects.create(
        company=other, branch=other_branch, code="MAIN", name="Other warehouse"
    )

    with pytest.raises(ValidationError, match="outside the selected company"):
        grant_branch_access(admin_context, user_id=target.id, branch_id=other_branch.id)
    with pytest.raises(ValidationError, match="outside the selected company"):
        grant_warehouse_access(admin_context, user_id=target.id, warehouse_id=other_warehouse.id)


@pytest.mark.django_db
def test_grants_are_retry_safe_and_audited_once(admin_context, company):
    target = get_user_model().objects.create_user("target@example.com", "password")
    first = grant_company_access(admin_context, user_id=target.id)
    second = grant_company_access(admin_context, user_id=target.id)

    assert first.id == second.id
    entries = AuditEntry.objects.filter(action="access.company.granted")
    assert entries.count() == 1
    entry = entries.get()
    assert entry.actor_id == admin_context.actor_id
    assert entry.company == company
    assert entry.object_id == str(first.id)
    assert entry.metadata == {"user_id": str(target.id)}


@pytest.mark.django_db
def test_company_access_can_be_revoked_after_target_user_is_deactivated(
    admin_context, company
):
    target = get_user_model().objects.create_user("target@example.com", "password")
    grant_company_access(admin_context, user_id=target.id)
    target.is_active = False
    target.save()

    assert revoke_company_access(admin_context, user_id=target.id)
    assert not UserCompanyAccess.objects.filter(user=target, company=company).exists()


@pytest.mark.django_db
def test_role_services_are_company_safe_retry_safe_and_audited(admin_context, company):
    target = get_user_model().objects.create_user("target@example.com", "password")
    grant_company_access(admin_context, user_id=target.id)
    permission = Permission.objects.create(code="example.record.view", name="View records")
    role = create_role(admin_context, code="viewer", name="Viewer")
    first_link = grant_role_permission(
        admin_context, role_id=role.id, permission_code=permission.code
    )
    second_link = grant_role_permission(
        admin_context, role_id=role.id, permission_code=permission.code
    )
    first_assignment = assign_role(admin_context, user_id=target.id, role_id=role.id)
    second_assignment = assign_role(admin_context, user_id=target.id, role_id=role.id)

    assert first_link.id == second_link.id
    assert first_assignment.id == second_assignment.id
    assert AuditEntry.objects.filter(action="access.role_permissions.changed").count() == 1
    assert AuditEntry.objects.filter(action="access.role.assigned").count() == 1
    assert revoke_role_permission(
        admin_context, role_id=role.id, permission_code=permission.code
    )
    assert revoke_role(admin_context, user_id=target.id, role_id=role.id)
    assert AuditEntry.objects.filter(action="access.role.revoked").count() == 1


@pytest.mark.django_db
def test_audit_entries_are_immutable(admin_context):
    target = get_user_model().objects.create_user("target@example.com", "password")
    grant_company_access(admin_context, user_id=target.id)
    entry = AuditEntry.objects.get(action="access.company.granted")
    entry.action = "rewritten"

    with pytest.raises(ValidationError, match="immutable"):
        entry.save()
    with pytest.raises(ValidationError, match="immutable"):
        entry.delete()
    with pytest.raises(ValidationError, match="immutable"):
        AuditEntry.objects.filter(id=entry.id).update(action="rewritten")
    with pytest.raises(ValidationError, match="immutable"):
        AuditEntry.objects.filter(id=entry.id).delete()


@pytest.mark.django_db
def test_manifest_permissions_are_validated_registered_and_not_implicitly_deleted(company):
    manifest = {
        "code": "sales",
        "name": "Sales",
        "version": "0.1.0",
        "depends": ["party"],
        "permissions": ["sales.order.update", "sales.order.view"],
    }
    module = register_manifest(manifest, enabled=True)
    permission = Permission.objects.get(code="sales.order.view")
    role = Role.objects.create(company=company, code="VIEWER", name="Viewer")
    link = RolePermission.objects.create(role=role, permission=permission)

    same_module = register_manifest({**manifest, "permissions": []})

    assert same_module.id == module.id
    assert same_module.is_enabled
    assert same_module.declared_permissions == []
    assert Permission.objects.filter(id=permission.id, is_active=True).exists()
    assert RolePermission.objects.filter(id=link.id).exists()

    permission.is_active = False
    permission.save()
    register_manifest(manifest)
    permission.refresh_from_db()
    assert not permission.is_active


@pytest.mark.parametrize(
    "permissions",
    [
        ["sales.order"],
        ["Sales.order.view"],
        ["catalog.product.view"],
        ["sales.order.view", "sales.order.view"],
    ],
)
@pytest.mark.django_db
def test_manifest_rejects_invalid_duplicate_or_foreign_permission_codes(permissions):
    with pytest.raises(ValueError):
        register_manifest(
            {
                "code": "sales",
                "name": "Sales",
                "version": "0.1.0",
                "depends": [],
                "permissions": permissions,
            }
        )


@pytest.mark.django_db
def test_permission_code_is_validated_and_immutable():
    with pytest.raises(ValidationError, match="module.resource.action"):
        Permission.objects.create(code="bad", name="Bad")
    permission = Permission.objects.create(code="example.record.view", name="View")
    permission.code = "example.record.update"
    with pytest.raises(ValidationError, match="immutable"):
        permission.save()
    with pytest.raises(ValidationError, match="immutable"):
        Permission.objects.filter(id=permission.id).update(code="example.record.update")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,code",
    [(Country, "BD"), (Currency, "BDT"), (Language, "BN"), (UnitOfMeasure, "KG")],
)
def test_reference_codes_are_immutable_but_labels_and_retirement_are_allowed(model, code):
    record = model.objects.create(code=code, name="Original")
    record.name = "Updated label"
    record.is_active = False
    record.save()
    record.code = f"{code}X"

    with pytest.raises(ValidationError, match="immutable"):
        record.save()
    with pytest.raises(ValidationError, match="immutable"):
        model.objects.filter(id=record.id).update(code=code)

    record.refresh_from_db()
    assert record.name == "Updated label"
    assert not record.is_active


@pytest.mark.django_db
def test_company_identity_validates_timezone_and_base_currency_is_immutable(company):
    company.timezone = "Not/A_Timezone"
    with pytest.raises(ValidationError, match="IANA"):
        company.save()
    company.refresh_from_db()
    replacement = Currency.objects.create(code="EUR", name="Euro")
    company.base_currency = replacement
    with pytest.raises(ValidationError, match="immutable"):
        company.save()
    with pytest.raises(ValidationError, match="immutable"):
        Company.objects.filter(id=company.id).update(base_currency=replacement)
    with pytest.raises(ValidationError, match="validated Company model save"):
        Company.objects.filter(id=company.id).update(timezone="Not/A_Timezone")


@pytest.mark.django_db
def test_company_creation_requires_active_country_language_and_currency(
    country, language, currency
):
    country.is_active = False
    country.save()
    with pytest.raises(ValidationError, match="active reference"):
        Company.objects.create(
            code="BLOCKED",
            name="Blocked",
            country=country,
            default_language=language,
            base_currency=currency,
        )


@pytest.mark.django_db
def test_company_business_time_converts_across_utc_date_boundary(company):
    company.timezone = "Asia/Dhaka"
    company.save()
    instant = datetime(2026, 9, 13, 20, 30, tzinfo=UTC)

    local = company_local_datetime(company.id, instant)

    assert local.isoformat() == "2026-09-14T02:30:00+06:00"
    assert company_local_date(company.id, instant).isoformat() == "2026-09-14"


@pytest.mark.django_db
def test_company_business_time_rejects_naive_datetime(company):
    with pytest.raises(ValidationError, match="timezone-aware"):
        company_local_datetime(company.id, datetime(2026, 9, 14, 10, 0))
