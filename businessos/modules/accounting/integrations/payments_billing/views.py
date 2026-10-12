from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, PermissionDenied, ValidationError
from django.shortcuts import redirect, render

from businessos.core.access.context import business_context_from_request
from businessos.core.access.policies import require_permission
from businessos.core.database import business_atomic_context
from businessos.core.organization.models import Company
from businessos.modules.payments import views as payment_views

from ..admission import admission
from ..forms import PostingForm, identifiers
from ..http import evidence_errors
from .selectors import allocation_action_basis, allocation_posting_status
from .services import post_payment_allocation_outcome


@login_required
def payment_detail(request, payment_id):
    context = business_context_from_request(request)
    with business_atomic_context():
        if (
            not Company.objects.select_for_update()
            .filter(pk=context.company_id, is_active=True)
            .exists()
        ):
            raise PermissionDenied("Active company required.")
        require_permission(context, "payments.payment.view")
        return payment_views.payment_detail(request, payment_id)


@login_required
@evidence_errors
def allocation_detail(request, allocation_id):
    context = business_context_from_request(request)
    with admission(context, allocation=True, http=True):
        status = allocation_posting_status(context, allocation_id)
        action_url = request.path + "post/"
        can_post = False
        try:
            with admission(context, allocation=True, create=True, http=True):
                can_post = True
        except PermissionDenied:
            pass
        return render(
            request,
            "accounting_outcomes/detail.html",
            {
                "heading": "Allocation Accounting",
                "accounting_status": status,
                "post_url": action_url
                if can_post and status.state == "NOT_POSTED" and status.reason is None
                else None,
            },
        )


@login_required
@evidence_errors
def allocation_post(request, allocation_id):
    context = business_context_from_request(request)
    with admission(context, allocation=True, create=True, http=True):
        basis = allocation_action_basis(context, allocation_id)
        if request.method == "POST" and (basis.state == "UNAVAILABLE" or basis.reason):
            raise BadRequest("No eligible Accounting posting action is available.")
        if request.method != "POST" and (basis.state != "NOT_POSTED" or basis.reason):
            return render(
                request,
                "accounting_outcomes/detail.html",
                {"heading": "Allocation Accounting", "accounting_status": basis},
            )
        form = PostingForm(
            request.POST if request.method == "POST" else None, context=context, allocation=True
        )
        if request.method == "POST" and form.is_valid():
            try:
                outcome = post_payment_allocation_outcome(
                    context, allocation_id=allocation_id, **identifiers(form.cleaned_data)
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                return redirect("accounting:detail", entry_id=outcome.journal_entry_id)
        return render(
            request,
            "accounting_outcomes/form.html",
            {
                "form": form,
                "heading": "Post allocation Accounting",
                "description": (
                    "Cash/Bank debit and matching invoice AR credit; no Revenue duplication."
                ),
            },
        )
