from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from businessos.core.access.context import business_context_from_request
from businessos.core.access.policies import has_permission, require_permission
from businessos.core.modules.decorators import module_required

from .forms import (
    BalanceFilterForm,
    HistoryFilterForm,
    MovementActionForm,
    MovementCreateForm,
    MovementForm,
    MovementLineForm,
)
from .manifest import CREATE_MOVEMENTS, POST_MOVEMENTS, UPDATE_MOVEMENTS, VIEW_BALANCES
from .models import StockMovement
from .selectors import (
    balances_for_warehouse,
    movement_detail,
    movement_history,
    movements_for_company,
)
from .services import (
    add_stock_movement_line,
    create_stock_movement,
    post_stock_movement,
    remove_stock_movement_line,
    update_stock_movement,
    update_stock_movement_line,
)


def _errors(form, error):
    if hasattr(error, "message_dict"):
        for field, values in error.message_dict.items():
            for value in values:
                form.add_error(field if field in form.fields else None, value)
    else:
        form.add_error(None, error)


def _movement(context, movement_id):
    try:
        return movement_detail(context, movement_id=movement_id)
    except StockMovement.DoesNotExist as exc:
        raise Http404 from exc


@login_required
@module_required("inventory")
def movement_list(request):
    context = business_context_from_request(request)
    return render(
        request,
        "inventory/movement_list.html",
        {
            "movements": movements_for_company(
                context,
                search=request.GET.get("q", ""),
                movement_type=request.GET.get("type", ""),
                status=request.GET.get("status", ""),
            ),
            "types": StockMovement.Type.choices,
            "statuses": StockMovement.Status.choices,
            "can_create": has_permission(context, CREATE_MOVEMENTS),
        },
    )


@login_required
@module_required("inventory")
def movement_create(request):
    context = business_context_from_request(request)
    require_permission(context, CREATE_MOVEMENTS)
    form = MovementCreateForm(request.POST or None, company_id=context.company_id)
    if request.method == "POST" and form.is_valid():
        try:
            movement = create_stock_movement(context, **form.cleaned_data)
        except (PermissionDenied, ValidationError) as error:
            _errors(form, error)
        else:
            messages.success(request, "Stock Movement created.")
            return redirect("inventory:detail", movement_id=movement.id)
    return render(
        request, "inventory/movement_form.html", {"form": form, "heading": "Create movement"}
    )


@login_required
@module_required("inventory")
def movement_edit(request, movement_id):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_MOVEMENTS)
    movement = _movement(context, movement_id)
    if movement.status != StockMovement.Status.DRAFT:
        raise Http404
    initial = {
        field: getattr(movement, field)
        for field in ("movement_type", "effective_at", "reference", "notes")
    }
    form = MovementForm(
        request.POST or None, company_id=context.company_id, initial=initial
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_stock_movement(context, movement_id=movement.id, **form.cleaned_data)
        except (PermissionDenied, ValidationError) as error:
            _errors(form, error)
        else:
            messages.success(request, "Stock Movement updated.")
            return redirect("inventory:detail", movement_id=movement.id)
    return render(
        request, "inventory/movement_form.html", {"form": form, "heading": "Edit movement"}
    )


@login_required
@module_required("inventory")
def movement_detail_view(request, movement_id):
    context = business_context_from_request(request)
    movement = _movement(context, movement_id)
    return render(
        request,
        "inventory/movement_detail.html",
        {
            "movement": movement,
            "action_form": MovementActionForm(company_id=context.company_id),
            "can_update": has_permission(context, UPDATE_MOVEMENTS),
            "can_post": has_permission(context, POST_MOVEMENTS),
        },
    )


def _line_data(cleaned):
    data = cleaned.copy()
    for field in ("product_variant", "source_warehouse", "destination_warehouse"):
        value = data.pop(field, None)
        data[f"{field}_id"] = value.id if value else None
    return data


@login_required
@module_required("inventory")
def line_create(request, movement_id):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_MOVEMENTS)
    movement = _movement(context, movement_id)
    if movement.status != StockMovement.Status.DRAFT:
        raise Http404
    form = MovementLineForm(
        request.POST or None,
        company_id=context.company_id,
        movement_type=movement.movement_type,
    )
    if request.method == "POST" and form.is_valid():
        try:
            add_stock_movement_line(
                context, movement_id=movement.id, **_line_data(form.cleaned_data)
            )
        except (PermissionDenied, ValidationError) as error:
            _errors(form, error)
        else:
            messages.success(request, "Movement line added.")
            return redirect("inventory:detail", movement_id=movement.id)
    return render(
        request, "inventory/movement_form.html", {"form": form, "heading": "Add movement line"}
    )


@login_required
@module_required("inventory")
def line_edit(request, movement_id, line_id):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_MOVEMENTS)
    movement = _movement(context, movement_id)
    if movement.status != StockMovement.Status.DRAFT:
        raise Http404
    try:
        line = movement.lines.get(id=line_id)
    except movement.lines.model.DoesNotExist as exc:
        raise Http404 from exc
    form = MovementLineForm(
        request.POST or None,
        company_id=context.company_id,
        movement_type=movement.movement_type,
        initial={
            "product_variant": line.product_variant_id,
            "quantity": line.quantity,
            "source_warehouse": line.source_warehouse_id,
            "destination_warehouse": line.destination_warehouse_id,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_stock_movement_line(
                context,
                movement_id=movement.id,
                line_id=line.id,
                **_line_data(form.cleaned_data),
            )
        except (PermissionDenied, ValidationError) as error:
            _errors(form, error)
        else:
            messages.success(request, "Movement line updated.")
            return redirect("inventory:detail", movement_id=movement.id)
    return render(
        request, "inventory/movement_form.html", {"form": form, "heading": "Edit movement line"}
    )


@login_required
@module_required("inventory")
@require_POST
def line_remove(request, movement_id, line_id):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_MOVEMENTS)
    form = MovementActionForm(request.POST, company_id=context.company_id)
    if not form.is_valid():
        messages.error(request, "; ".join(form.non_field_errors()))
        return redirect("inventory:detail", movement_id=movement_id)
    try:
        remove_stock_movement_line(context, movement_id=movement_id, line_id=line_id)
    except (PermissionDenied, ValidationError) as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Movement line removed.")
    return redirect("inventory:detail", movement_id=movement_id)


@login_required
@module_required("inventory")
@require_POST
def movement_post(request, movement_id):
    context = business_context_from_request(request)
    require_permission(context, POST_MOVEMENTS)
    form = MovementActionForm(request.POST, company_id=context.company_id)
    if not form.is_valid():
        messages.error(request, "; ".join(form.non_field_errors()))
        return redirect("inventory:detail", movement_id=movement_id)
    try:
        post_stock_movement(context, movement_id=movement_id)
    except (PermissionDenied, ValidationError) as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Stock Movement posted.")
    return redirect("inventory:detail", movement_id=movement_id)


@login_required
@module_required("inventory")
def balances(request):
    context = business_context_from_request(request)
    require_permission(context, VIEW_BALANCES)
    form = BalanceFilterForm(request.GET or None, company_id=context.company_id)
    rows, warehouse = [], None
    if form.is_valid():
        warehouse = form.cleaned_data["warehouse"]
        rows = balances_for_warehouse(context, warehouse_id=warehouse.id)
    return render(
        request, "inventory/balances.html", {"form": form, "rows": rows, "warehouse": warehouse}
    )


@login_required
@module_required("inventory")
def history(request):
    context = business_context_from_request(request)
    require_permission(context, VIEW_BALANCES)
    form = HistoryFilterForm(request.GET or None, company_id=context.company_id)
    rows = movement_history(context)
    if form.is_valid():
        warehouse = form.cleaned_data.get("warehouse")
        variant = form.cleaned_data.get("product_variant")
        rows = movement_history(
            context,
            warehouse_id=warehouse.id if warehouse else None,
            product_variant_id=variant.id if variant else None,
        )
    return render(request, "inventory/history.html", {"form": form, "movements": rows})
