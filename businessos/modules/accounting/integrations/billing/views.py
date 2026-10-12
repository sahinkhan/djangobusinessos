from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest, PermissionDenied, ValidationError
from django.shortcuts import redirect, render

from businessos.core.access.context import business_context_from_request
from businessos.core.access.policies import require_permission
from businessos.core.database import business_atomic_context
from businessos.core.organization.models import Company
from businessos.modules.billing import views as billing_views

from ..admission import admission
from ..forms import PostingForm, identifiers
from ..http import evidence_errors
from .selectors import invoice_action_basis
from .services import post_billing_invoice_outcome


@login_required
def invoice_detail(request, invoice_id):
    # Keep ordinary owner facts and every installed evidence panel in one Company admission.
    context = business_context_from_request(request)
    with business_atomic_context():
        if (
            not Company.objects.select_for_update()
            .filter(pk=context.company_id, is_active=True)
            .exists()
        ):
            raise PermissionDenied("Active company required.")
        require_permission(context, "billing.invoice.view")
        return billing_views.invoice_detail_view(request, invoice_id)


@login_required
@evidence_errors
def invoice_post(request, invoice_id):
    context = business_context_from_request(request)
    with admission(context, create=True, http=True):
        basis = invoice_action_basis(context, invoice_id)
        if request.method == "POST" and basis.state in {"UNAVAILABLE", "NO_ACCOUNTING_EFFECT"}:
            raise BadRequest("No eligible Accounting posting action is available.")
        if request.method != "POST" and basis.state in {
            "UNAVAILABLE",
            "POSTED",
            "NO_ACCOUNTING_EFFECT",
        }:
            return render(
                request,
                "accounting_outcomes/detail.html",
                {"heading": "Invoice Accounting", "accounting_status": basis},
            )
        form = PostingForm(request.POST if request.method == "POST" else None, context=context)
        if request.method == "POST" and form.is_valid():
            try:
                post_billing_invoice_outcome(
                    context, invoice_id=invoice_id, **identifiers(form.cleaned_data)
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                return redirect("billing:detail", invoice_id=invoice_id)
        return render(
            request,
            "accounting_outcomes/form.html",
            {
                "form": form,
                "heading": "Post invoice Accounting",
                "description": "Explicit AR debit and Revenue credit; no payment or stock effect.",
            },
        )
