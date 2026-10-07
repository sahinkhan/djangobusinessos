from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from businessos.core.access.context import business_context_from_request
from businessos.core.access.policies import has_permission, require_permission
from businessos.core.modules.decorators import module_required

from . import selectors, services
from .forms import MethodActivityForm, MethodFilterForm, PaymentForm, PaymentMethodForm, SearchForm
from .manifest import MANAGE_METHODS, RECORD_PAYMENTS, VIEW_METHODS, VIEW_PAYMENTS
from .models import Payment, PaymentMethod


def _errors(form, error):
    if hasattr(error, "message_dict"):
        for field, errors in error.message_dict.items():
            for message in errors:
                form.add_error(field if field in form.fields else None, message)
    else:
        form.add_error(None, error)


@login_required
@module_required("payments")
def payment_list(request):
    context = business_context_from_request(request)
    form = SearchForm(request.GET)
    form.is_valid()
    page = Paginator(
        selectors.payments_for_company(context, search=form.cleaned_data.get("q", "")), 50
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "payments/payment_list.html",
        {
            "page_obj": page,
            "payments": page.object_list,
            "filter_form": form,
            "can_record": has_permission(context, RECORD_PAYMENTS),
            "can_view_methods": has_permission(context, VIEW_METHODS),
            "can_manage_methods": has_permission(context, MANAGE_METHODS),
        },
    )


@login_required
@module_required("payments")
def payment_detail(request, payment_id):
    context = business_context_from_request(request)
    try:
        payment = selectors.payment_detail(context, payment_id)
    except Payment.DoesNotExist as exc:
        raise Http404 from exc
    return render(request, "payments/payment_detail.html", {"payment": payment})


@login_required
@module_required("payments")
def payment_record(request):
    context = business_context_from_request(request)
    require_permission(context, RECORD_PAYMENTS)
    form = PaymentForm(
        request.POST if request.method == "POST" else None, company_id=context.company_id
    )
    if request.method == "POST" and form.is_valid():
        data = dict(form.cleaned_data)
        for field in ("payer_party", "currency", "payment_method"):
            data[f"{field}_id"] = data.pop(field).pk
        try:
            payment = services.record_payment(context, **data)
        except ValidationError as exc:
            _errors(form, exc)
        else:
            messages.success(request, f"Receipt {payment.number} recorded.")
            if has_permission(context, VIEW_PAYMENTS):
                return redirect("payments:detail", payment_id=payment.pk)
            return redirect("payments:record")
    return render(
        request, "payments/payment_form.html", {"form": form, "heading": "Record receipt"}
    )


@login_required
@module_required("payments")
def method_list(request):
    context = business_context_from_request(request)
    form = MethodFilterForm(request.GET)
    form.is_valid()
    page = Paginator(
        selectors.payment_methods_for_company(
            context,
            search=form.cleaned_data.get("q", ""),
            active=form.cleaned_data.get("active", ""),
        ),
        50,
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "payments/method_list.html",
        {
            "page_obj": page,
            "methods": page.object_list,
            "filter_form": form,
            "can_manage": has_permission(context, MANAGE_METHODS),
            "can_view_payments": has_permission(context, VIEW_PAYMENTS),
            "can_record": has_permission(context, RECORD_PAYMENTS),
        },
    )


@login_required
@module_required("payments")
def method_form(request, method_id=None):
    context = business_context_from_request(request)
    require_permission(context, MANAGE_METHODS)
    method = None
    if method_id is not None:
        method = get_object_or_404(PaymentMethod, pk=method_id, company_id=context.company_id)
    form = PaymentMethodForm(
        request.POST if request.method == "POST" else None,
        company_id=context.company_id,
        editing=method is not None,
        initial={"name": method.name} if method else {},
    )
    if request.method == "POST" and form.is_valid():
        try:
            if method is None:
                method = services.create_payment_method(context, **form.cleaned_data)
            else:
                method = services.update_payment_method(
                    context, payment_method_id=method.pk, **form.cleaned_data
                )
        except ValidationError as exc:
            _errors(form, exc)
        else:
            messages.success(request, "Payment method saved.")
            return redirect("payments:method_edit", method_id=method.pk)
    return render(
        request,
        "payments/method_form.html",
        {
            "form": form,
            "method": method,
            "heading": "Edit payment method" if method else "New payment method",
            "activity_form": MethodActivityForm(
                company_id=context.company_id,
                initial={"is_active": "true" if method and method.is_active else "false"},
            ),
            "can_view_methods": has_permission(context, VIEW_METHODS),
        },
    )


@login_required
@module_required("payments")
@require_POST
def method_activity(request, method_id):
    context = business_context_from_request(request)
    require_permission(context, MANAGE_METHODS)
    get_object_or_404(PaymentMethod, pk=method_id, company_id=context.company_id)
    form = MethodActivityForm(request.POST, company_id=context.company_id)
    if form.is_valid():
        try:
            services.set_payment_method_active(
                context, payment_method_id=method_id, **form.cleaned_data
            )
        except ValidationError as exc:
            _errors(form, exc)
        else:
            return redirect("payments:method_edit", method_id=method_id)
    return render(request, "payments/action_error.html", {"form": form}, status=400)
