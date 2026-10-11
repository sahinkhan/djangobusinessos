"""Opt-in context processor; standalone owners never import the optional app."""

from django.core.exceptions import BadRequest, PermissionDenied, ValidationError
from django.http import Http404

from businessos.core.access.context import business_context_from_request
from businessos.core.access.policies import has_permission

from .admission import http_admission
from .domain import AllocationEvidence
from .manifest import CREATE_ALLOCATIONS, VIEW_ALLOCATIONS
from .selectors import invoice_allocation_evidence, payment_allocation_evidence


def parent_evidence(request):
    match = request.resolver_match
    if match is None or match.view_name not in {"payments:detail", "billing:detail"}:
        return {}
    try:
        context = business_context_from_request(request)
    except PermissionDenied:
        # Error templates also run context processors using the original route.
        # Preserve the owner's normal 403/scope-selection UI, not a second error.
        return {}
    parent = "payment" if match.view_name == "payments:detail" else "invoice"
    identity = match.kwargs[f"{parent}_id"]
    can_create = False
    try:
        # Creation authority intentionally does not imply allocation.view.
        with http_admission(context, CREATE_ALLOCATIONS):
            can_create = has_permission(context, CREATE_ALLOCATIONS)
    except (PermissionDenied, Http404):
        pass
    try:
        page = int(request.GET.get("allocation_page", "1"))
    except ValueError:
        page = 0
    try:
        with http_admission(context, VIEW_ALLOCATIONS):
            selector = (
                payment_allocation_evidence if parent == "payment" else invoice_allocation_evidence
            )
            evidence = selector(
                context, identity, page=page, search=request.GET.get("allocation_q", "")
            )
    except PermissionDenied:
        evidence = AllocationEvidence.unavailable("forbidden")
    except Http404:
        evidence = AllocationEvidence.unavailable("http_disabled")
    except ValidationError as exc:
        # Invalid filters are input errors, not stale financial evidence.
        raise BadRequest("Invalid allocation history filters.") from exc
    return {
        "allocation_evidence": evidence,
        "allocation_parent": parent,
        "allocation_parent_id": identity,
        "can_allocate": can_create,
    }
