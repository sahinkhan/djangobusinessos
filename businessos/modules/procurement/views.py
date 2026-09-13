from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from businessos.core.access.context import business_context_from_request
from businessos.core.modules.decorators import module_required

from .forms import (
    PurchaseOrderFilterForm,
    PurchaseOrderForm,
    PurchaseOrderLineForm,
    PurchaseReceiptForm,
)
from .models import PurchaseOrder, PurchaseOrderLine, PurchaseReceipt
from .selectors import (
    purchase_order_detail,
    purchase_orders_for_company,
    purchase_receipt_detail,
)
from .services import (
    add_purchase_order_line,
    cancel_purchase_order,
    confirm_purchase_order,
    create_purchase_order,
    receive_purchase_order,
    remove_purchase_order_line,
    update_purchase_order,
    update_purchase_order_line,
)


def _add_service_error(form, error):
    if hasattr(error, "message_dict"):
        for field, errors in error.message_dict.items():
            target = field if field in form.fields else None
            for message in errors:
                form.add_error(target, message)
    else:
        form.add_error(None, error)


def _order_data(cleaned_data):
    data = cleaned_data.copy()
    data["supplier_id"] = data.pop("supplier").id
    data["currency_id"] = data.pop("currency").id
    return data


def _line_data(cleaned_data):
    data = cleaned_data.copy()
    data["product_variant_id"] = data.pop("product_variant").id
    return data


def _submitted_receipt_line_ids(data):
    submitted = set()
    for field_name in data:
        if not field_name.startswith("line_"):
            continue
        try:
            submitted.add(UUID(field_name.removeprefix("line_")))
        except ValueError as exc:
            raise ValidationError("The receipt contains an invalid Purchase Order line.") from exc
    return submitted


@login_required
@module_required("procurement")
def order_list(request):
    context = business_context_from_request(request)
    form = PurchaseOrderFilterForm(request.GET)
    form.is_valid()
    return render(
        request,
        "procurement/order_list.html",
        {
            "orders": purchase_orders_for_company(
                context,
                search=form.cleaned_data.get("q", ""),
                status=form.cleaned_data.get("status", ""),
            ),
            "filter_form": form,
        },
    )


@login_required
@module_required("procurement")
def order_create(request):
    context = business_context_from_request(request)
    form = PurchaseOrderForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        try:
            order = create_purchase_order(context, **_order_data(form.cleaned_data))
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Purchase Order created as draft.")
            return redirect("procurement:order_detail", order_id=order.id)
    return render(
        request,
        "procurement/order_form.html",
        {"form": form, "heading": "Create Purchase Order"},
    )


@login_required
@module_required("procurement")
def order_edit(request, order_id):
    context = business_context_from_request(request)
    try:
        order = purchase_order_detail(context, order_id=order_id)
    except PurchaseOrder.DoesNotExist as exc:
        raise Http404 from exc
    if order.status != PurchaseOrder.Status.DRAFT:
        messages.error(request, "Only draft Purchase Orders may be edited.")
        return redirect("procurement:order_detail", order_id=order.id)
    form = PurchaseOrderForm(
        request.POST or None,
        company_id=context.company_id,
        initial={
            "supplier": order.supplier_id,
            "order_date": order.order_date,
            "currency": order.currency_id,
            "notes": order.notes,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_purchase_order(context, order_id=order.id, **_order_data(form.cleaned_data))
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Purchase Order updated.")
            return redirect("procurement:order_detail", order_id=order.id)
    return render(
        request,
        "procurement/order_form.html",
        {"form": form, "heading": "Edit Purchase Order"},
    )


@login_required
@module_required("procurement")
def order_detail_view(request, order_id):
    context = business_context_from_request(request)
    try:
        order = purchase_order_detail(context, order_id=order_id)
    except PurchaseOrder.DoesNotExist as exc:
        raise Http404 from exc
    return render(request, "procurement/order_detail.html", {"order": order})


@login_required
@module_required("procurement")
def line_create(request, order_id):
    context = business_context_from_request(request)
    try:
        order = purchase_order_detail(context, order_id=order_id)
    except PurchaseOrder.DoesNotExist as exc:
        raise Http404 from exc
    if order.status != PurchaseOrder.Status.DRAFT:
        messages.error(request, "Lines may only be added to draft Purchase Orders.")
        return redirect("procurement:order_detail", order_id=order.id)
    form = PurchaseOrderLineForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        try:
            add_purchase_order_line(context, order_id=order.id, **_line_data(form.cleaned_data))
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Purchase Order line added.")
            return redirect("procurement:order_detail", order_id=order.id)
    return render(
        request,
        "procurement/line_form.html",
        {"form": form, "heading": f"Add line · {order.number}", "order": order},
    )


@login_required
@module_required("procurement")
def line_edit(request, order_id, line_id):
    context = business_context_from_request(request)
    try:
        line = PurchaseOrderLine.objects.select_related("purchase_order").get(
            id=line_id, purchase_order_id=order_id, company_id=context.company_id
        )
    except PurchaseOrderLine.DoesNotExist as exc:
        raise Http404 from exc
    if line.purchase_order.status != PurchaseOrder.Status.DRAFT:
        messages.error(request, "Lines may only be edited while the Purchase Order is draft.")
        return redirect("procurement:order_detail", order_id=order_id)
    form = PurchaseOrderLineForm(
        request.POST or None,
        company_id=context.company_id,
        initial={
            "product_variant": line.product_variant_id,
            "quantity": line.quantity,
            "unit_cost": line.unit_cost,
            "description": line.description_snapshot,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_purchase_order_line(context, line_id=line.id, **_line_data(form.cleaned_data))
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Purchase Order line updated.")
            return redirect("procurement:order_detail", order_id=order_id)
    return render(
        request,
        "procurement/line_form.html",
        {
            "form": form,
            "heading": f"Edit line · {line.purchase_order.number}",
            "order": line.purchase_order,
        },
    )


@login_required
@module_required("procurement")
@require_POST
def line_remove(request, order_id, line_id):
    context = business_context_from_request(request)
    if not PurchaseOrderLine.objects.filter(
        id=line_id, purchase_order_id=order_id, company_id=context.company_id
    ).exists():
        raise Http404
    try:
        remove_purchase_order_line(context, line_id=line_id)
    except ValidationError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Purchase Order line removed.")
    return redirect("procurement:order_detail", order_id=order_id)


@login_required
@module_required("procurement")
@require_POST
def order_confirm(request, order_id):
    context = business_context_from_request(request)
    try:
        confirm_purchase_order(context, order_id=order_id)
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(request, "Purchase Order confirmed. No stock was created.")
    return redirect("procurement:order_detail", order_id=order_id)


@login_required
@module_required("procurement")
@require_POST
def order_cancel(request, order_id):
    context = business_context_from_request(request)
    try:
        cancel_purchase_order(context, order_id=order_id)
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(request, "Purchase Order cancelled.")
    return redirect("procurement:order_detail", order_id=order_id)


@login_required
@module_required("procurement")
def order_receive(request, order_id):
    context = business_context_from_request(request)
    try:
        order = purchase_order_detail(context, order_id=order_id)
    except PurchaseOrder.DoesNotExist as exc:
        raise Http404 from exc
    if order.status != PurchaseOrder.Status.CONFIRMED:
        messages.error(request, "Only a confirmed Purchase Order may be received.")
        return redirect("procurement:order_detail", order_id=order.id)
    order_lines = list(order.lines.all())
    submitted_line_ids = set()
    submitted_line_error = None
    if request.method == "POST":
        try:
            submitted_line_ids = _submitted_receipt_line_ids(request.POST)
        except ValidationError as error:
            submitted_line_error = error
    lines = (
        order_lines
        if request.method == "POST"
        else [line for line in order_lines if line.remaining_quantity > 0]
    )
    form = PurchaseReceiptForm(
        request.POST or None,
        company_id=context.company_id,
        order_lines=lines,
        submitted_line_ids=submitted_line_ids,
    )
    form_is_valid = form.is_valid() if request.method == "POST" else False
    if submitted_line_error is not None:
        _add_service_error(form, submitted_line_error)
        form_is_valid = False
    if request.method == "POST" and form_is_valid:
        try:
            receipt = receive_purchase_order(
                context,
                purchase_order_id=order.id,
                receipt_date=form.cleaned_data["receipt_date"],
                idempotency_key=form.cleaned_data["idempotency_key"],
                lines=form.receipt_lines(),
            )
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Purchase Receipt posted. Inventory was not changed.")
            return redirect("procurement:receipt_detail", receipt_id=receipt.id)
    return render(
        request,
        "procurement/receipt_form.html",
        {"form": form, "order": order, "lines": lines},
    )


@login_required
@module_required("procurement")
def receipt_detail_view(request, receipt_id):
    context = business_context_from_request(request)
    try:
        receipt = purchase_receipt_detail(context, receipt_id=receipt_id)
    except PurchaseReceipt.DoesNotExist as exc:
        raise Http404 from exc
    return render(request, "procurement/receipt_detail.html", {"receipt": receipt})
