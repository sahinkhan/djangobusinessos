from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import connections

from businessos.core.common.context import BusinessContext
from businessos.core.database import current_database_alias
from businessos.core.organization.models import Branch, Company, Warehouse

from .models import (
    Permission,
    Role,
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
    if (
        not user.is_superuser
        and not UserCompanyAccess.objects.filter(user=user, company_id=context.company_id).exists()
    ):
        raise PermissionDenied("You do not have access to this company.")

    branch = None
    if context.branch_id:
        branch = Branch.objects.filter(
            id=context.branch_id, company_id=context.company_id, is_active=True
        ).first()
        if branch is None:
            raise PermissionDenied("The branch is outside the selected company or inactive.")
        if (
            not user.is_superuser
            and not UserBranchAccess.objects.filter(user=user, branch=branch).exists()
        ):
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
        if (
            not user.is_superuser
            and not UserWarehouseAccess.objects.filter(user=user, warehouse=warehouse).exists()
        ):
            raise PermissionDenied("You do not have access to this warehouse.")

    return context


def has_permission(context: BusinessContext, permission_code: str) -> bool:
    """Return an explicit BusinessOS authorization decision; default is deny."""
    validate_business_context(context)
    validate_permission_code(permission_code)
    if not Permission.objects.filter(code=permission_code, is_active=True).exists():
        return False
    user = get_user_model().objects.get(id=context.actor_id)
    if user.is_superuser:
        return True
    return UserRoleAssignment.objects.filter(
        user_id=context.actor_id,
        company_id=context.company_id,
        role__company_id=context.company_id,
        role__is_active=True,
        role__permission_links__permission__code=permission_code,
        role__permission_links__permission__is_active=True,
    ).exists()


def require_permission(context: BusinessContext, permission_code: str) -> BusinessContext:
    if not has_permission(context, permission_code):
        raise PermissionDenied(f"Business permission required: {permission_code}.")
    return context


def _share_authority_row(connection, model, identity):
    """Hold activity/deletion stable without excluding other authorized readers."""
    quote = connection.ops.quote_name
    pk = model._meta.pk
    lock = " FOR SHARE" if connection.vendor == "postgresql" else ""
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT {quote(pk.column)} FROM {quote(model._meta.db_table)} "
            f"WHERE {quote(pk.column)} = %s{lock}",
            [pk.get_db_prep_value(identity, connection)],
        )
        return cursor.fetchone() is not None


def require_final_permission(context: BusinessContext, permission_code: str) -> BusinessContext:
    """Serialize current mutation authority after the caller's domain/reference locks.

    The caller must hold its active Company lock in the selected business transaction.
    Supported Access grant/link/assignment writers hold that same Company lock (ADR 0009).
    Global actor/Permission activity and Role activity need additional protection: lock
    actor, exact Permission, then one qualifying Role witness in UUID order. PostgreSQL
    FOR SHARE blocks activity updates/deletion through outer commit while allowing nested
    owner services and different-company readers to share authority anchors. Do not use
    this helper as a substitute for Company locking or as an authorization cache.
    SQLite retains the ordinary policy check; row-lock concurrency is PostgreSQL-only.
    """
    alias = current_database_alias()
    connection = connections[alias]
    if not connection.in_atomic_block:
        raise RuntimeError("Final mutation authorization requires a business transaction.")
    validate_permission_code(permission_code)
    user_model = get_user_model()
    if not _share_authority_row(connection, user_model, context.actor_id):
        raise PermissionDenied("The context actor does not exist or is inactive.")
    permission_id = (
        Permission.objects.using(alias)
        .filter(code=permission_code)
        .values_list("pk", flat=True)
        .first()
    )
    if permission_id is None or not _share_authority_row(connection, Permission, permission_id):
        raise PermissionDenied(f"Business permission required: {permission_code}.")
    user = user_model.objects.using(alias).get(pk=context.actor_id)
    if not user.is_superuser:
        assignments = UserRoleAssignment.objects.using(alias).filter(
            user_id=context.actor_id,
            company_id=context.company_id,
            role__company_id=context.company_id,
            role__is_active=True,
            role__permission_links__permission_id=permission_id,
            role__permission_links__permission__is_active=True,
        )
        role_ids = list(
            assignments.order_by("role_id").values_list("role_id", flat=True).distinct()
        )
        for role_id in role_ids:
            if (
                _share_authority_row(connection, Role, role_id)
                and assignments.filter(role_id=role_id).exists()
            ):
                break
        else:
            raise PermissionDenied(f"Business permission required: {permission_code}.")
    # Re-read context/activity/grants only AFTER every authority lock wait. A new,
    # unlocked role cannot replace the locked qualifying witness above.
    return require_permission(context, permission_code)
