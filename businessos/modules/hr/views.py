"""Thin HR request/context adapters; no ORM mutation or HR rule ownership."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from businessos.core.access.context import business_context_from_request
from businessos.core.modules.decorators import module_required

from . import selectors, services
from .admission import AuthorityBusy, ResourceBudgetExceeded
from .forms import (
    AttendanceForm,
    ChoiceFilterForm,
    EmployeeForm,
    EndEmployeeForm,
    FilterForm,
    LeaveActionForm,
    LeaveForm,
    SetupForm,
    TransferEmployeeForm,
)

_LABELS = {
    "employee": "Employees",
    "department": "Departments",
    "attendance": "Attendance",
    "leave": "Leave",
    "leave_type": "Leave types",
}

_CREATE = {
    "employee": ("create_employee", "employee_create", "employee"),
    "department": ("create_department", "department_create", "department"),
    "attendance": ("record_attendance", "attendance_record", "attendance"),
    "leave": ("create_leave", "leave_create", "leave request"),
    "leave_type": ("create_leave_type", "leave_type_create", "leave type"),
}

_CHOICE_SEARCH = {
    "create_employee": ("party_q", "user_q", "department_q", "branch_q"),
    "update_employee": ("user_q", "department_q"),
    "transfer_employee_branch": ("branch_q",),
    "record_attendance": ("employee_q",),
    "create_leave": ("employee_q", "type_q"),
    "update_leave": ("type_q",),
}
_CHOICE_PARAMETERS = {
    "party_q": "party_search",
    "user_q": "user_search",
    "department_q": "department_search",
    "branch_q": "branch_search",
    "employee_q": "employee_search",
    "type_q": "leave_type_search",
}


def _errors(form, error):
    if hasattr(error, "message_dict"):
        for field, errors in error.message_dict.items():
            for message in errors:
                form.add_error(field if field in form.fields else None, message)
    else:
        form.add_error(None, str(error))


def _read_error(request, error):
    status = 409 if isinstance(error, AuthorityBusy) else 422
    return render(request, "hr/error.html", {"error": str(error)}, status=status)


@login_required
@module_required("hr")
@require_http_methods(["GET"])
def record_list(request, kind="employee"):
    context = business_context_from_request(request)
    form = FilterForm(request.GET)
    valid = form.is_valid()
    data = dict(form.cleaned_data) if valid else {}
    data["search"] = data.pop("q", "")
    try:
        page = getattr(selectors, f"{kind}_page")(context, page=request.GET.get("page", 1), **data)
    except (ValidationError, ResourceBudgetExceeded) as exc:
        _errors(form, exc)
        valid = False
        page = Paginator((), 50).get_page(1)
    except AuthorityBusy as exc:
        return _read_error(request, exc)
    if not valid:
        page = Paginator((), 50).get_page(1)
    flags = selectors.action_flags(context)
    create_operation, create_route, singular = _CREATE[kind]
    return render(
        request,
        "hr/list.html",
        {
            "kind": kind,
            "heading": _LABELS[kind],
            "page_obj": page,
            "records": page.object_list,
            "filter_form": form,
            "can_create": flags[create_operation],
            "create_url": reverse(f"hr:{create_route}"),
            "singular_label": singular,
        },
        status=200 if valid else 400,
    )


@login_required
@module_required("hr")
@require_http_methods(["GET"])
def record_detail(request, record_id, kind="employee"):
    context = business_context_from_request(request)
    try:
        record = getattr(selectors, f"{kind}_detail")(context, record_id)
    except (ValidationError, ResourceBudgetExceeded, AuthorityBusy) as exc:
        return _read_error(request, exc)
    flags = selectors.action_flags(context)
    display = {
        "can_edit": flags.get(f"update_{kind}", False),
        "can_end": flags["end_employee"],
        "can_transfer": flags["transfer_employee_branch"],
        "can_correct": flags["revise_attendance"],
        "can_submit": flags["submit_leave"],
        "can_decide": flags["decide_leave"],
        "can_cancel": flags["cancel_leave"],
    }
    if kind == "leave":
        display["can_edit"] &= record.status == "DRAFT"
        display["can_submit"] &= record.status == "DRAFT"
        display["can_decide"] &= record.status == "SUBMITTED"
        display["can_cancel"] &= record.status in {"DRAFT", "SUBMITTED", "APPROVED"}
        if record.decision == "APPROVED":
            display["can_cancel"] &= flags["decide_leave"]
    return render(
        request,
        "hr/detail.html",
        {"kind": kind, "record": record, "heading": _LABELS[kind], **display},
    )


@login_required
@module_required("hr")
@require_http_methods(["GET"])
def revision_history(request, attendance_id):
    context = business_context_from_request(request)
    try:
        record = selectors.attendance_detail(context, attendance_id)
        page = selectors.revision_page(context, attendance_id, page=request.GET.get("page", 1))
    except (ValidationError, ResourceBudgetExceeded, AuthorityBusy) as exc:
        return _read_error(request, exc)
    return render(
        request,
        "hr/revisions.html",
        {
            "record": record,
            "page_obj": page,
            "records": page.object_list,
        },
    )


def _form_for(operation, admission, request, context, *, presentation_operation=None):
    record, choices = admission["record"], admission.get("choices", {})
    initial = dict(record.values) if record else {}
    if record is not None and hasattr(record, "revision"):
        initial["expected_revision"] = record.revision
    common = {
        "company_id": context.company_id,
        "branch_id": context.branch_id,
        "choices": choices,
        "initial": initial,
    }
    data = request.POST if request.method == "POST" else None
    if operation in {
        "create_department",
        "update_department",
        "create_leave_type",
        "update_leave_type",
    }:
        if record is not None:
            initial["is_active"] = "true" if record.is_active else "false"
        return SetupForm(data, editing=record is not None, **common)
    if operation in {"create_employee", "update_employee"}:
        return EmployeeForm(
            data,
            editing=record is not None,
            ended=bool(record and record.status == "ENDED"),
            **common,
        )
    if operation == "end_employee":
        return EndEmployeeForm(data, **common)
    if operation == "transfer_employee_branch":
        return TransferEmployeeForm(data, **common)
    if operation in {"record_attendance", "revise_attendance"}:
        latest = admission.get("latest")
        originals = {}
        if latest:
            initial.update(
                {
                    "expected_revision": latest.number,
                    "start_at": latest.start_at,
                    "end_at": latest.end_at,
                }
            )
            originals = {"start_at": latest.start_at, "end_at": latest.end_at}
        return AttendanceForm(
            data,
            zone=admission["zone"],
            operation=presentation_operation or "RECORD",
            originals=originals,
            **common,
        )
    if operation in {"create_leave", "update_leave"}:
        return LeaveForm(data, editing=record is not None, **common)
    return LeaveActionForm(data, operation=presentation_operation or operation, **common)


@login_required
@module_required("hr")
@require_http_methods(["GET", "POST"])
def record_action(request, operation, kind, record_id=None, presentation_operation=None):
    context = business_context_from_request(request)
    choice_filter = ChoiceFilterForm(request.GET)
    valid_choice_filter = choice_filter.is_valid()
    # This selector owns complete GET/action authorization and bounded choices,
    # including frozen/current Branch semantics. POST re-enters it independently.
    try:
        admission = selectors.action_admission(
            context,
            operation,
            object_id=record_id,
            search=choice_filter.cleaned_data.get("choices_q", "") if valid_choice_filter else "",
            **{
                parameter: choice_filter.cleaned_data.get(field, "")
                if valid_choice_filter and field in request.GET
                else None
                for field, parameter in _CHOICE_PARAMETERS.items()
                if field in _CHOICE_SEARCH.get(operation, ())
            },
        )
    except (ValidationError, ResourceBudgetExceeded, AuthorityBusy) as exc:
        return _read_error(request, exc)
    form = _form_for(
        operation, admission, request, context, presentation_operation=presentation_operation
    )
    response_status = 200
    if not valid_choice_filter:
        response_status = 400
    if request.method == "POST" and valid_choice_filter and form.is_valid():
        data = dict(form.cleaned_data)
        if record_id is not None:
            data[f"{kind}_id"] = record_id
        if operation == "revise_attendance":
            data["operation"] = presentation_operation
        if operation == "decide_leave":
            data["decision"] = (
                "REJECTED" if presentation_operation == "reject_leave" else "APPROVED"
            )
        try:
            result = getattr(services, operation)(context, **data)
        except ValidationError as exc:
            _errors(form, exc)
            response_status = 400
        except AuthorityBusy as exc:
            _errors(form, exc)
            response_status = 409
        except ResourceBudgetExceeded as exc:
            _errors(form, exc)
            response_status = 422
        else:
            messages.success(request, "HR operation completed.")
            # Services may return a historical receipt with a separately-labelled
            # current record; a receipt is never presented as current document data.
            result_id = getattr(result, "id", None)
            if result_id is None:
                owner = getattr(result, "attendance", None) or getattr(result, "leave", None)
                result_id = getattr(owner, "id", None)
            if result_id is None:
                result_id = record_id
            return redirect(f"hr:{kind}_detail", record_id=result_id)
    elif request.method == "POST":
        response_status = 400
    title_operation = presentation_operation or operation
    return render(
        request,
        "hr/form.html",
        {
            "form": form,
            "heading": title_operation.replace("_", " ").capitalize(),
            "kind": kind,
            "record": admission["record"],
            "business_timezone": admission["zone"],
            "choice_filter": choice_filter,
            "choice_search_fields": [
                choice_filter[name] for name in ("choices_q", *_CHOICE_SEARCH.get(operation, ()))
            ],
            "has_choice_search": bool(request.GET),
            "has_choices": operation
            in {
                "create_employee",
                "update_employee",
                "transfer_employee_branch",
                "record_attendance",
                "create_leave",
                "update_leave",
            },
        },
        status=response_status,
    )
