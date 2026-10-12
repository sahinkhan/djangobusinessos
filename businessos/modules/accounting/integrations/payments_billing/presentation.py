from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404

from businessos.core.access.context import business_context_from_request

from ..admission import admission


def allocation_links(request):
    match = request.resolver_match
    if match is None or match.view_name not in {"billing:detail", "payments:detail"}:
        return {}
    try:
        context = business_context_from_request(request)
        with admission(context, allocation=True, http=True):
            # Rows remain PAY-INT-owned, bounded and filtered by its existing history selector.
            # No per-row Accounting queries or uncertified "posted/not posted" badges.
            return {"allocation_accounting_links": True}
    except (PermissionDenied, Http404, ValidationError):
        return {}
