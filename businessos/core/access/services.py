from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from businessos.core.audit.services import record_audit_entry
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Branch, Company, Warehouse

from .models import (
    Permission,
    Role,
    RolePermission,
    UserBranchAccess,
    UserCompanyAccess,
    UserRoleAssignment,
    UserWarehouseAccess,
)
from .permissions import CORE_PERMISSION_DECLARATIONS
from .policies import require_permission

MANAGE_ORGANIZATIONAL_ACCESS = CORE_PERMISSION_DECLARATIONS[0][0]
MANAGE_ROLES = CORE_PERMISSION_DECLARATIONS[1][0]


@transaction.atomic
def register_core_permissions() -> tuple[Permission, ...]:
    registered = []
    for code, name in CORE_PERMISSION_DECLARATIONS:
        permission, created = Permission.objects.get_or_create(
            code=code,
            defaults={"name": name, "is_active": True},
        )
        if not created and permission.name != name:
            Permission.objects.filter(id=permission.id).update(name=name)
            permission.name = name
        registered.append(permission)
    return tuple(registered)


def _target_user(user_id: UUID, *, require_active: bool = True):
    query = get_user_model().objects.filter(id=user_id)
    if require_active:
        query = query.filter(is_active=True)
    user = query.first()
    if user is None:
        message = (
            "The target user does not exist or is inactive."
            if require_active
            else "The target user does not exist."
        )
        raise ValidationError(message)
    return user


def _lock_context_company(context: BusinessContext) -> Company:
    # Every scoped security mutation takes this lock BEFORE reading authorization.
    # Under PostgreSQL READ COMMITTED, waiters then see committed revocations.
    company = (
        Company.objects.select_for_update().filter(id=context.company_id, is_active=True).first()
    )
    if company is None:
        raise PermissionDenied("The selected company does not exist or is inactive.")
    return company


@transaction.atomic
def grant_company_access(context: BusinessContext, *, user_id: UUID) -> UserCompanyAccess:
    company = _lock_context_company(context)
    require_permission(context, MANAGE_ORGANIZATIONAL_ACCESS)
    user = _target_user(user_id)
    access, created = UserCompanyAccess.objects.get_or_create(user=user, company=company)
    if created:
        record_audit_entry(
            context=context,
            action="access.company.granted",
            object_type="access.UserCompanyAccess",
            object_id=access.id,
            metadata={"user_id": str(user.id)},
        )
    return access


@transaction.atomic
def revoke_company_access(context: BusinessContext, *, user_id: UUID) -> bool:
    _lock_context_company(context)
    require_permission(context, MANAGE_ORGANIZATIONAL_ACCESS)
    user = _target_user(user_id, require_active=False)
    branch_count, _ = UserBranchAccess.objects.filter(
        user=user, branch__company_id=context.company_id
    ).delete()
    warehouse_count, _ = UserWarehouseAccess.objects.filter(
        user=user, warehouse__company_id=context.company_id
    ).delete()
    assignments = list(
        UserRoleAssignment.objects.filter(user=user, company_id=context.company_id).values_list(
            "id", flat=True
        )
    )
    UserRoleAssignment.objects.filter(id__in=assignments).delete()
    deleted, _ = UserCompanyAccess.objects.filter(user=user, company_id=context.company_id).delete()
    if deleted:
        record_audit_entry(
            context=context,
            action="access.company.revoked",
            object_type="identity.User",
            object_id=user.id,
            metadata={
                "branch_grants_removed": branch_count,
                "warehouse_grants_removed": warehouse_count,
                "role_assignments_removed": len(assignments),
            },
        )
    return bool(deleted)


@transaction.atomic
def grant_branch_access(
    context: BusinessContext, *, user_id: UUID, branch_id: UUID
) -> UserBranchAccess:
    _lock_context_company(context)
    require_permission(context, MANAGE_ORGANIZATIONAL_ACCESS)
    user = _target_user(user_id)
    branch = (
        Branch.objects.select_for_update()
        .filter(id=branch_id, company_id=context.company_id, is_active=True)
        .first()
    )
    if branch is None:
        raise ValidationError("The branch is outside the selected company or inactive.")
    if not UserCompanyAccess.objects.filter(user=user, company_id=context.company_id).exists():
        raise ValidationError("Grant company access before branch access.")
    access, created = UserBranchAccess.objects.get_or_create(user=user, branch=branch)
    if created:
        record_audit_entry(
            context=context,
            action="access.branch.granted",
            object_type="access.UserBranchAccess",
            object_id=access.id,
            metadata={"user_id": str(user.id), "branch_id": str(branch.id)},
        )
    return access


@transaction.atomic
def revoke_branch_access(context: BusinessContext, *, user_id: UUID, branch_id: UUID) -> bool:
    _lock_context_company(context)
    require_permission(context, MANAGE_ORGANIZATIONAL_ACCESS)
    user = _target_user(user_id, require_active=False)
    branch = Branch.objects.filter(id=branch_id, company_id=context.company_id).first()
    if branch is None:
        raise ValidationError("The branch is outside the selected company.")
    deleted, _ = UserBranchAccess.objects.filter(user=user, branch=branch).delete()
    if deleted:
        record_audit_entry(
            context=context,
            action="access.branch.revoked",
            object_type="organization.Branch",
            object_id=branch.id,
            metadata={"user_id": str(user.id)},
        )
    return bool(deleted)


@transaction.atomic
def grant_warehouse_access(
    context: BusinessContext, *, user_id: UUID, warehouse_id: UUID
) -> UserWarehouseAccess:
    _lock_context_company(context)
    require_permission(context, MANAGE_ORGANIZATIONAL_ACCESS)
    user = _target_user(user_id)
    warehouse = (
        Warehouse.objects.select_for_update()
        .filter(id=warehouse_id, company_id=context.company_id, is_active=True)
        .first()
    )
    if warehouse is None:
        raise ValidationError("The warehouse is outside the selected company or inactive.")
    if not UserCompanyAccess.objects.filter(user=user, company_id=context.company_id).exists():
        raise ValidationError("Grant company access before warehouse access.")
    access, created = UserWarehouseAccess.objects.get_or_create(user=user, warehouse=warehouse)
    if created:
        record_audit_entry(
            context=context,
            action="access.warehouse.granted",
            object_type="access.UserWarehouseAccess",
            object_id=access.id,
            metadata={"user_id": str(user.id), "warehouse_id": str(warehouse.id)},
        )
    return access


@transaction.atomic
def revoke_warehouse_access(context: BusinessContext, *, user_id: UUID, warehouse_id: UUID) -> bool:
    _lock_context_company(context)
    require_permission(context, MANAGE_ORGANIZATIONAL_ACCESS)
    user = _target_user(user_id, require_active=False)
    warehouse = Warehouse.objects.filter(id=warehouse_id, company_id=context.company_id).first()
    if warehouse is None:
        raise ValidationError("The warehouse is outside the selected company.")
    deleted, _ = UserWarehouseAccess.objects.filter(user=user, warehouse=warehouse).delete()
    if deleted:
        record_audit_entry(
            context=context,
            action="access.warehouse.revoked",
            object_type="organization.Warehouse",
            object_id=warehouse.id,
            metadata={"user_id": str(user.id)},
        )
    return bool(deleted)


@transaction.atomic
def create_role(context: BusinessContext, *, code: str, name: str) -> Role:
    _lock_context_company(context)
    require_permission(context, MANAGE_ROLES)
    role = Role(company_id=context.company_id, code=code, name=name)
    role.save()
    record_audit_entry(
        context=context,
        action="access.role.created",
        object_type="access.Role",
        object_id=role.id,
    )
    return role


@transaction.atomic
def grant_role_permission(
    context: BusinessContext, *, role_id: UUID, permission_code: str
) -> RolePermission:
    _lock_context_company(context)
    require_permission(context, MANAGE_ROLES)
    role = (
        Role.objects.select_for_update()
        .filter(id=role_id, company_id=context.company_id, is_active=True)
        .first()
    )
    if role is None:
        raise ValidationError("The role is outside the selected company or inactive.")
    permission = Permission.objects.filter(code=permission_code, is_active=True).first()
    if permission is None:
        raise ValidationError("The permission does not exist or is inactive.")
    link, created = RolePermission.objects.get_or_create(role=role, permission=permission)
    if created:
        record_audit_entry(
            context=context,
            action="access.role_permissions.changed",
            object_type="access.Role",
            object_id=role.id,
            metadata={"permission_code": permission.code, "change": "granted"},
        )
    return link


@transaction.atomic
def revoke_role_permission(
    context: BusinessContext, *, role_id: UUID, permission_code: str
) -> bool:
    _lock_context_company(context)
    require_permission(context, MANAGE_ROLES)
    role = Role.objects.filter(id=role_id, company_id=context.company_id).first()
    if role is None:
        raise ValidationError("The role is outside the selected company.")
    deleted, _ = RolePermission.objects.filter(role=role, permission__code=permission_code).delete()
    if deleted:
        record_audit_entry(
            context=context,
            action="access.role_permissions.changed",
            object_type="access.Role",
            object_id=role.id,
            metadata={"permission_code": permission_code, "change": "revoked"},
        )
    return bool(deleted)


@transaction.atomic
def assign_role(context: BusinessContext, *, user_id: UUID, role_id: UUID) -> UserRoleAssignment:
    _lock_context_company(context)
    require_permission(context, MANAGE_ROLES)
    user = _target_user(user_id)
    role = Role.objects.filter(id=role_id, company_id=context.company_id, is_active=True).first()
    if role is None:
        raise ValidationError("The role is outside the selected company or inactive.")
    if not UserCompanyAccess.objects.filter(user=user, company_id=context.company_id).exists():
        raise ValidationError("Grant company access before assigning a role.")
    assignment, created = UserRoleAssignment.objects.get_or_create(
        user=user, company_id=context.company_id, role=role
    )
    if created:
        record_audit_entry(
            context=context,
            action="access.role.assigned",
            object_type="access.UserRoleAssignment",
            object_id=assignment.id,
            metadata={"user_id": str(user.id), "role_id": str(role.id)},
        )
    return assignment


@transaction.atomic
def revoke_role(context: BusinessContext, *, user_id: UUID, role_id: UUID) -> bool:
    _lock_context_company(context)
    require_permission(context, MANAGE_ROLES)
    role = Role.objects.filter(id=role_id, company_id=context.company_id).first()
    if role is None:
        raise ValidationError("The role is outside the selected company.")
    deleted, _ = UserRoleAssignment.objects.filter(
        user_id=user_id, company_id=context.company_id, role=role
    ).delete()
    if deleted:
        record_audit_entry(
            context=context,
            action="access.role.revoked",
            object_type="access.Role",
            object_id=role.id,
            metadata={"user_id": str(user_id)},
        )
    return bool(deleted)
