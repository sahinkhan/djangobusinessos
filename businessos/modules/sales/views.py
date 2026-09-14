from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from businessos.core.access.context import business_context_from_request
from businessos.core.access.policies import has_permission, require_permission
from businessos.core.modules.decorators import module_required

from .forms import SalesOrderFilterForm, SalesOrderForm, SalesOrderLineForm
from .models import SalesOrder, SalesOrderLine
from .selectors import sales_order_detail, sales_orders_for_company
from .services import (
    CANCEL_ORDERS,
    CONFIRM_ORDERS,
    CREATE_ORDERS,
    UPDATE_ORDERS,
    add_sales_order_line,
    cancel_sales_order,
    confirm_sales_order,
    create_sales_order,
    remove_sales_order_line,
    update_sales_order,
    update_sales_order_line,
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
    data["customer_id"] = data.pop("customer").id
    data["currency_id"] = data.pop("currency").id
    return data


def _line_data(cleaned_data):
    data = cleaned_data.copy()
    data["product_variant_id"] = data.pop("product_variant").id
    return data


@login_required
@module_required("sales")
def order_list(request):
    context = business_context_from_request(request)
    form = SalesOrderFilterForm(request.GET)
    form.is_valid()
    search = form.cleaned_data.get("q", "")
    status = form.cleaned_data.get("status", "")
    return render(
        request,
        "sales/order_list.html",
        {
            "orders": sales_orders_for_company(context, search=search, status=status),
            "filter_form": form,
            "can_create": has_permission(context, CREATE_ORDERS),
        },
    )


@login_required
@module_required("sales")
def order_create(request):
    context = business_context_from_request(request)
    require_permission(context, CREATE_ORDERS)
    form = SalesOrderForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        try:
            order = create_sales_order(context, **_order_data(form.cleaned_data))
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Sales Order created as draft.")
            return redirect("sales:order_detail", order_id=order.id)
    return render(
        request, "sales/order_form.html", {"form": form, "heading": "Create Sales Order"}
    )


@login_required
@module_required("sales")
def order_edit(request, order_id):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_ORDERS)
    try:
        order = SalesOrder.objects.select_related("customer", "currency").get(
            id=order_id, company_id=context.company_id
        )
    except SalesOrder.DoesNotExist as exc:
        raise Http404 from exc
    if order.status != SalesOrder.Status.DRAFT:
        messages.error(request, "Only draft Sales Orders may be edited.")
        return redirect("sales:order_detail", order_id=order.id)
    form = SalesOrderForm(
        request.POST or None,
        company_id=context.company_id,
        initial={
            "customer": order.customer_id,
            "order_date": order.order_date,
            "currency": order.currency_id,
            "notes": order.notes,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_sales_order(context, order_id=order.id, **_order_data(form.cleaned_data))
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Sales Order updated.")
            return redirect("sales:order_detail", order_id=order.id)
    return render(
        request, "sales/order_form.html", {"form": form, "heading": "Edit Sales Order"}
    )


@login_required
@module_required("sales")
def order_detail_view(request, order_id):
    context = business_context_from_request(request)
    try:
        order = sales_order_detail(context, order_id=order_id)
    except SalesOrder.DoesNotExist as exc:
        raise Http404 from exc
    return render(
        request,
        "sales/order_detail.html",
        {
            "order": order,
            "can_update": has_permission(context, UPDATE_ORDERS),
            "can_confirm": has_permission(context, CONFIRM_ORDERS),
            "can_cancel": has_permission(context, CANCEL_ORDERS),
        },
    )


@login_required
@module_required("sales")
def line_create(request, order_id):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_ORDERS)
    try:
        order = SalesOrder.objects.get(id=order_id, company_id=context.company_id)
    except SalesOrder.DoesNotExist as exc:
        raise Http404 from exc
    if order.status != SalesOrder.Status.DRAFT:
        messages.error(request, "Lines may only be added to draft Sales Orders.")
        return redirect("sales:order_detail", order_id=order.id)
    form = SalesOrderLineForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        try:
            add_sales_order_line(context, order_id=order.id, **_line_data(form.cleaned_data))
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Sales Order line added.")
            return redirect("sales:order_detail", order_id=order.id)
    return render(
        request,
        "sales/line_form.html",
        {"form": form, "heading": f"Add line · {order.number}", "order": order},
    )


@login_required
@module_required("sales")
def line_edit(request, order_id, line_id):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_ORDERS)
    try:
        line = SalesOrderLine.objects.select_related("sales_order").get(
            id=line_id, sales_order_id=order_id, company_id=context.company_id
        )
    except SalesOrderLine.DoesNotExist as exc:
        raise Http404 from exc
    if line.sales_order.status != SalesOrder.Status.DRAFT:
        messages.error(request, "Lines may only be edited while the Sales Order is draft.")
        return redirect("sales:order_detail", order_id=order_id)
    form = SalesOrderLineForm(
        request.POST or None,
        company_id=context.company_id,
        initial={
            "product_variant": line.product_variant_id,
            "quantity": line.quantity,
            "unit_price": line.unit_price,
            "description": line.description_snapshot,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_sales_order_line(
                context, line_id=line.id, **_line_data(form.cleaned_data)
            )
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Sales Order line updated.")
            return redirect("sales:order_detail", order_id=order_id)
    return render(
        request,
        "sales/line_form.html",
        {
            "form": form,
            "heading": f"Edit line · {line.sales_order.number}",
            "order": line.sales_order,
        },
    )


@login_required
@module_required("sales")
@require_POST
def line_remove(request, order_id, line_id):
    context = business_context_from_request(request)
    if not SalesOrderLine.objects.filter(
        id=line_id, sales_order_id=order_id, company_id=context.company_id
    ).exists():
        raise Http404
    try:
        remove_sales_order_line(context, line_id=line_id)
    except ValidationError as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Sales Order line removed.")
    return redirect("sales:order_detail", order_id=order_id)


@login_required
@module_required("sales")
@require_POST
def order_confirm(request, order_id):
    context = business_context_from_request(request)
    try:
        confirm_sales_order(context, order_id=order_id)
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(request, "Sales Order confirmed. No stock or invoice was created.")
    return redirect("sales:order_detail", order_id=order_id)


@login_required
@module_required("sales")
@require_POST
def order_cancel(request, order_id):
    context = business_context_from_request(request)
    try:
        cancel_sales_order(context, order_id=order_id)
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(request, "Sales Order cancelled.")
    return redirect("sales:order_detail", order_id=order_id)
