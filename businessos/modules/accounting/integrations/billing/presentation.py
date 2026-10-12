from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.urls import reverse

from businessos.core.access.context import business_context_from_request

from ..admission import admission
from ..domain import PostingOutcomeV1
from .selectors import invoice_posting_status


def invoice_panel(request):
    match = request.resolver_match
    if match is None or match.view_name != "billing:detail":
        return {}
    try:
        context = business_context_from_request(request)
    except PermissionDenied:
        return {}
    invoice_id = match.kwargs["invoice_id"]
    try:
        with admission(context, http=True):
            status = invoice_posting_status(context, invoice_id)
    except PermissionDenied:
        status = PostingOutcomeV1.unavailable("forbidden")
    except Http404:
        status = PostingOutcomeV1.unavailable("http_disabled")
    except ValidationError:
        status = PostingOutcomeV1.unavailable("incompatible")
    can_post = False
    try:
        with admission(context, create=True, http=True):
            can_post = True
    except (PermissionDenied, Http404, ValidationError):
        pass
    return {
        "accounting_invoice_status": status,
        "accounting_invoice_action": reverse(
            "accounting_billing:post", kwargs={"invoice_id": invoice_id}
        )
        if can_post and (status.state == "NOT_POSTED" or status.reason == "forbidden")
        else None,
    }
