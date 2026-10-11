from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from businessos.core.access.context import business_context_from_request
from businessos.modules.billing import views as billing_views
from businessos.modules.payments import views as payments_views

from .admission import http_admission, parent_read_admission
from .forms import AllocationForm
from .manifest import CREATE_ALLOCATIONS
from .services import create_payment_allocation


@login_required
def invoice_parent_detail(request, invoice_id):
    with parent_read_admission(business_context_from_request(request)):
        return billing_views.invoice_detail_view(request, invoice_id)


@login_required
def payment_parent_detail(request, payment_id):
    with parent_read_admission(business_context_from_request(request)):
        return payments_views.payment_detail(request, payment_id)


@login_required
def allocation_create(request):
    context = business_context_from_request(request)
    with http_admission(context, CREATE_ALLOCATIONS):
        form = AllocationForm(
            request.POST if request.method == "POST" else None,
            company_id=context.company_id,
            initial={
                "payment_id": request.GET.get("payment_id", ""),
                "invoice_id": request.GET.get("invoice_id", ""),
                "idempotency_key": uuid4().hex,
            },
        )
        if request.method == "POST" and form.is_valid():
            try:
                allocation = create_payment_allocation(context, **form.cleaned_data)
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            form.add_error(field if field in form.fields else None, error)
                else:
                    form.add_error(None, exc)
            else:
                messages.success(request, "Payment allocation recorded.")
                return redirect("payments:detail", payment_id=allocation.payment_id)
        return render(
            request,
            "payments_billing/allocation_form.html",
            {"form": form, "heading": "Allocate receipt"},
        )
