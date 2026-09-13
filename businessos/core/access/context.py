from uuid import UUID

from django.core.exceptions import PermissionDenied

from businessos.core.common.context import BusinessContext

from .policies import validate_business_context

SESSION_COMPANY_KEY = "businessos_company_id"
SESSION_BRANCH_KEY = "businessos_branch_id"
SESSION_WAREHOUSE_KEY = "businessos_warehouse_id"


def _session_uuid(session, key, *, required=False):
    value = session.get(key)
    if value in (None, ""):
        if required:
            raise PermissionDenied("No company has been selected.")
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise PermissionDenied(f"Invalid organizational scope in session: {key}.") from exc


def business_context_from_request(request) -> BusinessContext:
    """Validate authenticated session scope and return a framework-neutral context."""
    user = request.user
    if not user.is_authenticated or not user.is_active:
        raise PermissionDenied("Authentication is required.")

    context = BusinessContext(
        actor_id=user.id,
        company_id=_session_uuid(request.session, SESSION_COMPANY_KEY, required=True),
        branch_id=_session_uuid(request.session, SESSION_BRANCH_KEY),
        warehouse_id=_session_uuid(request.session, SESSION_WAREHOUSE_KEY),
    )
    return validate_business_context(context)
