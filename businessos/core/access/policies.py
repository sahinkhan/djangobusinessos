from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Branch, Company, Warehouse

from .models import (
    UserBranchAccess,
    UserCompanyAccess,
    UserRoleAssignment,
    UserWarehouseAccess,
)
from .permissions import validate_permission_code


def validate_business_context(context: BusinessContext) -> BusinessContext:
    """Validate scope integrity and grants for HTTP and non-HTTP service callers."""
    user = get_user_model().objects.filter(id=context.actor_id, is_active=True).first()
    if user is None:
        raise PermissionDenied("The context actor does not exist or is inactive.")

    if not Company.objects.filter(id=context.company_id, is_active=True).exists():
        raise PermissionDenied("The selected company does not exist or is inactive.")
    if not user.is_superuser and not UserCompanyAccess.objects.filter(
        user=user, company_id=context.company_id
    ).exists():
        raise PermissionDenied("You do not have access to this company.")

    branch = None
    if context.branch_id:
        branch = Branch.objects.filter(
            id=context.branch_id, company_id=context.company_id, is_active=True
        ).first()
        if branch is None:
            raise PermissionDenied("The branch is outside the selected company or inactive.")
        if not user.is_superuser and not UserBranchAccess.objects.filter(
            user=user, branch=branch
        ).exists():
            raise PermissionDenied("You do not have access to this branch.")

    if context.warehouse_id:
        warehouse = (
            Warehouse.objects.select_related("branch")
            .filter(id=context.warehouse_id, company_id=context.company_id, is_active=True)
            .first()
        )
        if warehouse is None:
            raise PermissionDenied("The warehouse is outside the selected company or inactive.")
        if warehouse.branch_id and not warehouse.branch.is_active:
            raise PermissionDenied("The warehouse branch is inactive.")
        if branch and warehouse.branch_id not in (None, branch.id):
            raise PermissionDenied("The warehouse does not belong to the selected branch.")
        if not user.is_superuser and not UserWarehouseAccess.objects.filter(
            user=user, warehouse=warehouse
        ).exists():
            raise PermissionDenied("You do not have access to this warehouse.")

    return context


def has_permission(context: BusinessContext, permission_code: str) -> bool:
    """Return an explicit BusinessOS authorization decision; default is deny."""
    validate_business_context(context)
    validate_permission_code(permission_code)
    user = get_user_model().objects.get(id=context.actor_id)
    if user.is_superuser:
        return True
    return UserRoleAssignment.objects.filter(
        user_id=context.actor_id,
        company_id=context.company_id,
        role__is_active=True,
        role__permission_links__permission__code=permission_code,
        role__permission_links__permission__is_active=True,
    ).exists()


def require_permission(context: BusinessContext, permission_code: str) -> BusinessContext:
    if not has_permission(context, permission_code):
        raise PermissionDenied(f"Business permission required: {permission_code}.")
    return context
