from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from businessos.core.access.context import business_context_from_request
from businessos.core.access.forms import CompanyBoundForm
from businessos.core.access.policies import has_permission, require_permission
from businessos.core.modules.decorators import module_required

from . import services
from .forms import InvoiceFilterForm, InvoiceForm, InvoiceLineForm
from .manifest import CREATE_INVOICES, ISSUE_INVOICES, UPDATE_INVOICES
from .models import Invoice, InvoiceLine
from .selectors import invoice_detail, invoices_for_company


def _errors(form, error):
    if hasattr(error, "message_dict"):
        for field, errors in error.message_dict.items():
            for message in errors:
                form.add_error(field if field in form.fields else None, message)
    else:
        form.add_error(None, error)


def _header_data(data):
    data = data.copy()
    data["bill_to_party_id"] = data.pop("bill_to_party").pk
    data["currency_id"] = data.pop("currency").pk
    return data


@login_required
@module_required("billing")
def invoice_list(request):
    context = business_context_from_request(request)
    form = InvoiceFilterForm(request.GET)
    form.is_valid()
    page = Paginator(
        invoices_for_company(
            context,
            search=form.cleaned_data.get("q", ""),
            status=form.cleaned_data.get("status", ""),
        ),
        50,
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "billing/invoice_list.html",
        {
            "page_obj": page,
            "invoices": page.object_list,
            "filter_form": form,
            "can_create": has_permission(context, CREATE_INVOICES),
        },
    )


@login_required
@module_required("billing")
def invoice_detail_view(request, invoice_id):
    context = business_context_from_request(request)
    # Selector enforces view permission before object lookup.
    from django.http import Http404

    try:
        invoice = invoice_detail(context, invoice_id)
    except Invoice.DoesNotExist as exc:
        raise Http404 from exc
    return render(
        request,
        "billing/invoice_detail.html",
        {
            "invoice": invoice,
            "can_update": has_permission(context, UPDATE_INVOICES),
            "can_issue": has_permission(context, ISSUE_INVOICES),
            "action_form": CompanyBoundForm(company_id=context.company_id),
        },
    )


@login_required
@module_required("billing")
def invoice_create(request):
    context = business_context_from_request(request)
    require_permission(context, CREATE_INVOICES)
    form = InvoiceForm(
        request.POST if request.method == "POST" else None, company_id=context.company_id
    )
    if request.method == "POST" and form.is_valid():
        try:
            invoice = services.create_invoice(context, **_header_data(form.cleaned_data))
        except ValidationError as exc:
            _errors(form, exc)
        else:
            return redirect("billing:detail", invoice_id=invoice.pk)
    return render(request, "billing/invoice_form.html", {"form": form, "heading": "Create invoice"})


@login_required
@module_required("billing")
def invoice_edit(request, invoice_id):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_INVOICES)
    invoice = get_object_or_404(Invoice, pk=invoice_id, company_id=context.company_id)
    if invoice.status != Invoice.Status.DRAFT:
        return redirect("billing:detail", invoice_id=invoice.pk)
    initial = {f: getattr(invoice, f) for f in ["invoice_date", "due_date", "notes"]}
    initial.update(bill_to_party=invoice.bill_to_party_id, currency=invoice.currency_id)
    form = InvoiceForm(
        request.POST if request.method == "POST" else None,
        company_id=context.company_id,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        try:
            services.update_invoice(context, invoice_id, **_header_data(form.cleaned_data))
        except ValidationError as exc:
            _errors(form, exc)
        else:
            return redirect("billing:detail", invoice_id=invoice.pk)
    return render(request, "billing/invoice_form.html", {"form": form, "heading": "Edit invoice"})


@login_required
@module_required("billing")
def line_form(request, invoice_id, line_id=None):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_INVOICES)
    invoice = get_object_or_404(Invoice, pk=invoice_id, company_id=context.company_id)
    if invoice.status != Invoice.Status.DRAFT:
        return redirect("billing:detail", invoice_id=invoice.pk)
    initial = {}
    if line_id is not None:
        line = get_object_or_404(
            InvoiceLine, pk=line_id, invoice=invoice, company_id=context.company_id
        )
        initial = {f: getattr(line, f) for f in ["description", "quantity", "unit_price"]}
    form = InvoiceLineForm(
        request.POST if request.method == "POST" else None,
        company_id=context.company_id,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        try:
            if line_id is None:
                services.add_invoice_line(context, invoice_id, **form.cleaned_data)
            else:
                services.update_invoice_line(context, invoice_id, line_id, **form.cleaned_data)
        except ValidationError as exc:
            _errors(form, exc)
        else:
            return redirect("billing:detail", invoice_id=invoice.pk)
    return render(
        request,
        "billing/line_form.html",
        {
            "form": form,
            "invoice": invoice,
            "heading": "Edit line" if line_id else "Add line",
        },
    )


def _action(request, invoice_id, *, permission, operation):
    context = business_context_from_request(request)
    require_permission(context, permission)
    form = CompanyBoundForm(request.POST, company_id=context.company_id)
    if not form.is_valid():
        return render(request, "billing/action_error.html", {"form": form}, status=400)
    try:
        operation(context)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("billing:detail", invoice_id=invoice_id)


@login_required
@module_required("billing")
@require_POST
def invoice_issue(request, invoice_id):
    return _action(
        request,
        invoice_id,
        permission=ISSUE_INVOICES,
        operation=lambda context: services.issue_invoice(context, invoice_id),
    )


@login_required
@module_required("billing")
@require_POST
def line_remove(request, invoice_id, line_id):
    return _action(
        request,
        invoice_id,
        permission=UPDATE_INVOICES,
        operation=lambda context: services.remove_invoice_line(context, invoice_id, line_id),
    )
