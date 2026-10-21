"""Bounded materialized HR read surfaces under current final authorization."""

from datetime import UTC, date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import OuterRef, Q, Subquery

from businessos.core.access.models import UserCompanyAccess
from businessos.core.access.policies import has_permission
from businessos.core.organization.models import Branch
from businessos.modules.party.models import Party

from . import domain
from .admission import ResourceBudgetExceeded, hr_operation
from .conflicts import certify_leave
from .history import certify_attendance
from .manifest import (
    APPROVE_LEAVE,
    CANCEL_LEAVE,
    CORRECT_ATTENDANCE,
    MANAGE_DEPARTMENTS,
    MANAGE_EMPLOYEES,
    MANAGE_LEAVE_TYPES,
    RECORD_ATTENDANCE,
    REQUEST_LEAVE,
    VIEW_ATTENDANCE,
    VIEW_DEPARTMENTS,
    VIEW_EMPLOYEES,
    VIEW_LEAVE,
)
from .models import Attendance, AttendanceRevision, Department, Employee, LeaveRequest, LeaveType
from .support import (
    active_employee,
    active_person,
    company_context,
    fact,
    identity,
    locked,
    person_projection,
    references,
    scope,
    today,
    value,
)


def _page(query, page, transform):
    if (
        isinstance(page, bool)
        or not isinstance(page, (int, str))
        or not str(page).isdigit()
        or int(page) < 1
    ):
        raise ValidationError({"page": "Use a positive integer page."})
    paginator = Paginator(query, 50)
    count = paginator.count
    result = paginator.get_page(int(page))
    result.object_list = tuple(transform(row) for row in result.object_list)
    # Keep only bounded scalar results. Even paginator.object_list must not retain
    # a lazy query that could be evaluated outside the authorization transaction.
    paginator.object_list = result.object_list
    paginator.count = count
    return result


def _search(query, search, *names):
    search = value("search", domain.text, search, maximum=200)
    if search:
        predicate = Q()
        for name in names:
            predicate |= Q(**{f"{name}__icontains": search})
        query = query.filter(predicate)
    return query


def _setup_page(context, model, *, search="", page=1, active="", **unused):
    with hr_operation(context, [VIEW_DEPARTMENTS if model is Department else VIEW_LEAVE]) as op:
        query = _search(
            model.objects.using(op.alias).filter(company_id=context.company_id),
            search,
            "code",
            "name",
        )
        if active in {"yes", "no"}:
            query = query.filter(is_active=active == "yes")
        result = _page(query.order_by("code", "pk"), page, fact)
        op.authorize()
        return result


def department_page(context, **kwargs):
    return _setup_page(context, Department, **kwargs)


def leave_type_page(context, **kwargs):
    return _setup_page(context, LeaveType, **kwargs)


def _setup_detail(context, model, row_id):
    with hr_operation(context, [VIEW_DEPARTMENTS if model is Department else VIEW_LEAVE]) as op:
        row = locked(model, context, row_id)
        op.declare_anchors([(model._meta.label_lower, row.pk)])
        result = fact(row)
        op.authorize()
        return result


def department_detail(context, department_id):
    return _setup_detail(context, Department, department_id)


def leave_type_detail(context, leave_type_id):
    return _setup_detail(context, LeaveType, leave_type_id)


def _employee_facts(op, rows, department_visible):
    # Query page rows, then lock the complete Employee UUID set in fixed order.
    rows = list(rows)
    op.declare_anchors(("hr.employee", row.pk) for row in rows)
    employees = op.lock_rows(Employee, [row.pk for row in rows])
    op.declare_anchors(("hr.employee", row.pk) for row in employees)
    refs = references(
        op,
        department_ids=[row.department_id for row in employees],
        branch_ids=[op.context.branch_id, *[row.branch_id for row in employees]],
        party_ids=[row.party_id for row in employees],
    )
    by_id = {}
    for row in employees:
        scope(op.context, row.branch_id)
        related = {"party": person_projection(refs[Party][row.party_id])}
        if department_visible and row.department_id:
            related["department"] = fact(refs[Department][row.department_id])
        by_id[row.pk] = fact(row, related=related, department_visible=department_visible)
    return by_id


def employee_page(context, *, search="", page=1, status="", branch_id=None, **unused):
    with hr_operation(context, [VIEW_EMPLOYEES]) as op:
        include_department = has_permission(context, VIEW_DEPARTMENTS)
        if include_department:
            op.declare_permissions([VIEW_DEPARTMENTS])
        query = Employee.objects.using(op.alias).filter(company_id=context.company_id)
        if context.branch_id:
            query = query.filter(branch_id=context.branch_id)
        if branch_id:
            query = query.filter(branch_id=identity("branch_id", branch_id))
        if status:
            if status not in Employee.Status.values:
                raise ValidationError("Unsupported Employee status.")
            query = query.filter(status=status)
        query = _search(query, search, "employee_number", "party__display_name")
        result = _page(query.order_by("employee_number", "pk"), page, lambda row: row)
        facts = _employee_facts(op, result.object_list, include_department)
        result.object_list = tuple(facts[row.pk] for row in result.object_list)
        result.paginator.object_list = result.object_list
        op.authorize()
        return result


def employee_detail(context, employee_id):
    with hr_operation(context, [VIEW_EMPLOYEES]) as op:
        row = locked(Employee, context, employee_id)
        include_department = has_permission(context, VIEW_DEPARTMENTS)
        if include_department:
            op.declare_permissions([VIEW_DEPARTMENTS])
        result = _employee_facts(op, [row], include_department)[row.pk]
        op.authorize()
        return result


def _history_detail(op, context, model, row_id):
    row = (
        model.objects.using(op.alias)
        .filter(pk=identity("id", row_id), company_id=context.company_id)
        .first()
    )
    if row is None:
        raise PermissionDenied("The HR fact is unavailable in this scope.")
    return _history_facts(op, context, model, [row])[row.pk]


def _history_facts(op, context, model, rows):
    rows = list(rows)
    op.declare_anchors(("hr.employee", row.employee_id) for row in rows)
    employees = op.lock_rows(Employee, {row.employee_id for row in rows})
    by_employee = {row.pk: row for row in employees}
    if set(by_employee) != {row.employee_id for row in rows}:
        raise ValidationError("The historical Employee ownership is incomplete.")
    op.declare_anchors(("hr.employee", row.pk) for row in employees)
    refs = references(
        op,
        branch_ids=[context.branch_id, *[row.branch_id for row in rows]],
        party_ids=[row.party_id for row in employees],
        leave_type_ids=[row.leave_type_id for row in rows] if model is LeaveRequest else [],
    )
    op.declare_anchors((model._meta.label_lower, row.pk) for row in rows)
    parents = op.lock_rows(model, [row.pk for row in rows])
    if len(parents) != len(rows):
        raise ValidationError("The historical parent evidence is incomplete.")
    op.declare_anchors((model._meta.label_lower, row.pk) for row in parents)
    results = {}
    for row in parents:
        scope(context, row.branch_id)
        employee = by_employee[row.employee_id]
        related = {
            "party": person_projection(refs[Party][employee.party_id]),
            "employee_number": employee.employee_number,
        }
        if model is Attendance:
            related["current"] = fact(certify_attendance(row))
        else:
            certify_leave(row)
            related["leave_type"] = fact(refs[LeaveType][row.leave_type_id])
        results[row.pk] = fact(row, related=related)
    return results


def attendance_detail(context, attendance_id):
    with hr_operation(context, [VIEW_ATTENDANCE, VIEW_EMPLOYEES]) as op:
        result = _history_detail(op, context, Attendance, attendance_id)
        op.authorize()
        return result


def leave_detail(context, leave_id):
    with hr_operation(context, [VIEW_LEAVE, VIEW_EMPLOYEES]) as op:
        result = _history_detail(op, context, LeaveRequest, leave_id)
        op.authorize()
        return result


def revision_page(context, attendance_id, *, page=1):
    with hr_operation(context, [VIEW_ATTENDANCE, VIEW_EMPLOYEES]) as op:
        parent = _history_detail(op, context, Attendance, attendance_id)
        result = _page(
            AttendanceRevision.objects.using(op.alias)
            .filter(attendance_id=parent.id)
            .order_by("-number", "pk"),
            page,
            fact,
        )
        op.authorize()
        return result


def attendance_page(
    context,
    *,
    search="",
    page=1,
    employee_id=None,
    branch_id=None,
    start_date=None,
    end_date=None,
    status="",
    **unused,
):
    with hr_operation(context, [VIEW_ATTENDANCE, VIEW_EMPLOYEES]) as op:
        last = (
            today(op.company)
            if end_date is None
            else value("end_date", domain.calendar_date, end_date)
        )
        first = (
            last - timedelta(days=30)
            if start_date is None
            else value("start_date", domain.calendar_date, start_date)
        )
        if first > last:
            raise ValidationError("Use an ordered date range.")
        if status not in {"", "ACTIVE_INTERVAL", "VOIDED"}:
            raise ValidationError("Unsupported Attendance effect filter.")
        envelope_start = datetime.combine(
            date.fromordinal(max(1, first.toordinal() - 1)), datetime.min.time(), tzinfo=UTC
        )
        envelope_end = (
            datetime.max.replace(tzinfo=UTC)
            if last.toordinal() + 2 > date.max.toordinal()
            else datetime.combine(
                date.fromordinal(last.toordinal() + 2), datetime.min.time(), tzinfo=UTC
            )
        )
        query = AttendanceRevision.objects.using(op.alias).filter(
            attendance__company_id=context.company_id,
            start_at__lt=envelope_end,
            end_at__gt=envelope_start,
        )
        if context.branch_id:
            query = query.filter(attendance__branch_id=context.branch_id)
        if employee_id:
            query = query.filter(attendance__employee_id=identity("employee_id", employee_id))
        if branch_id:
            query = query.filter(attendance__branch_id=identity("branch_id", branch_id))
        query = _search(
            query,
            search,
            "attendance__employee__employee_number",
            "attendance__employee__party__display_name",
        )
        ids = list(query.order_by("start_at", "pk").values_list("attendance_id", flat=True)[:1001])
        if len(ids) > 1000:
            raise ResourceBudgetExceeded("Narrow the Attendance date/search filters.")
        # Each scoped detail is prepared before admission; no nested public API
        # starts a second transaction or dynamically adds locks after admission.
        parents = list(
            Attendance.objects.using(op.alias)
            .filter(company_id=context.company_id, pk__in=set(ids))
            .order_by("pk")
        )
        facts = _history_facts(op, context, Attendance, parents)
        newest = (
            AttendanceRevision.objects.using(op.alias)
            .filter(attendance_id=OuterRef("pk"))
            .order_by("-number")
        )
        current = (
            Attendance.objects.using(op.alias)
            .filter(company_id=context.company_id, pk__in=facts)
            .annotate(
                current_start=Subquery(newest.values("start_at")[:1]),
                current_first=Subquery(newest.values("local_start_date")[:1]),
                current_last=Subquery(newest.values("local_end_date")[:1]),
                current_effect=Subquery(newest.values("effect")[:1]),
            )
            .filter(
                current_first__lte=last,
                current_last__gte=first,
                current_effect=status or "ACTIVE_INTERVAL",
            )
            .order_by("-current_start", "pk")
        )
        result = _page(current, page, lambda row: facts[row.pk])
        op.authorize()
        return result


def leave_page(
    context,
    *,
    search="",
    page=1,
    employee_id=None,
    branch_id=None,
    start_date=None,
    end_date=None,
    status="",
    **unused,
):
    with hr_operation(context, [VIEW_LEAVE, VIEW_EMPLOYEES]) as op:
        current = today(op.company)
        first = (
            current - timedelta(days=31)
            if start_date is None
            else value("start_date", domain.calendar_date, start_date)
        )
        last = (
            current + timedelta(days=31)
            if end_date is None
            else value("end_date", domain.calendar_date, end_date)
        )
        if first > last:
            raise ValidationError("Use an ordered date range.")
        query = LeaveRequest.objects.using(op.alias).filter(
            company_id=context.company_id, start_date__lte=last, end_date__gte=first
        )
        if context.branch_id:
            query = query.filter(branch_id=context.branch_id)
        if employee_id:
            query = query.filter(employee_id=identity("employee_id", employee_id))
        if branch_id:
            query = query.filter(branch_id=identity("branch_id", branch_id))
        if status:
            if status not in LeaveRequest.Status.values:
                raise ValidationError("Unsupported Leave status.")
            query = query.filter(status=status)
        query = _search(query, search, "employee__employee_number", "employee__party__display_name")
        result = _page(query.order_by("-start_date", "pk"), page, lambda row: row)
        facts = _history_facts(op, context, LeaveRequest, result.object_list)
        result.object_list = tuple(facts[row.pk] for row in result.object_list)
        result.paginator.object_list = result.object_list
        op.authorize()
        return result


_ACTIONS = {
    "create_department": (MANAGE_DEPARTMENTS, VIEW_DEPARTMENTS),
    "update_department": (MANAGE_DEPARTMENTS, VIEW_DEPARTMENTS),
    "create_leave_type": (MANAGE_LEAVE_TYPES, VIEW_LEAVE),
    "update_leave_type": (MANAGE_LEAVE_TYPES, VIEW_LEAVE),
    "create_employee": (MANAGE_EMPLOYEES, VIEW_EMPLOYEES),
    "update_employee": (MANAGE_EMPLOYEES, VIEW_EMPLOYEES),
    "end_employee": (MANAGE_EMPLOYEES, VIEW_EMPLOYEES),
    "transfer_employee_branch": (MANAGE_EMPLOYEES, VIEW_EMPLOYEES),
    "record_attendance": (RECORD_ATTENDANCE, VIEW_ATTENDANCE, VIEW_EMPLOYEES),
    "revise_attendance": (CORRECT_ATTENDANCE, VIEW_ATTENDANCE, VIEW_EMPLOYEES),
    "create_leave": (REQUEST_LEAVE, VIEW_LEAVE, VIEW_EMPLOYEES),
    "update_leave": (REQUEST_LEAVE, VIEW_LEAVE, VIEW_EMPLOYEES),
    "submit_leave": (REQUEST_LEAVE, VIEW_LEAVE, VIEW_EMPLOYEES),
    "decide_leave": (APPROVE_LEAVE, VIEW_LEAVE, VIEW_EMPLOYEES),
    "cancel_leave": (CANCEL_LEAVE, VIEW_LEAVE, VIEW_EMPLOYEES),
}


def action_admission(
    context,
    operation,
    *,
    object_id=None,
    search="",
    party_search=None,
    user_search=None,
    department_search=None,
    branch_search=None,
    employee_search=None,
    leave_type_search=None,
    **unused,
):
    if operation not in _ACTIONS:
        raise ValidationError("Unknown HR action.")
    with hr_operation(context, _ACTIONS[operation]) as op:
        search = value("choices_q", domain.text, search, maximum=200)
        (
            party_search,
            user_search,
            department_search,
            branch_search,
            employee_search,
            leave_type_search,
        ) = (
            search if term is None else value("choices_q", domain.text, term, maximum=200)
            for term in (
                party_search,
                user_search,
                department_search,
                branch_search,
                employee_search,
                leave_type_search,
            )
        )
        if operation in {
            "create_department",
            "update_department",
            "create_leave_type",
            "update_leave_type",
            "create_employee",
            "transfer_employee_branch",
        }:
            company_context(context)
        model = (
            Attendance
            if "attendance" in operation
            else LeaveType
            if "leave_type" in operation
            else LeaveRequest
            if "leave" in operation
            else Department
            if "department" in operation
            else Employee
        )
        target = None
        if object_id is not None:
            target = (
                model.objects.using(op.alias)
                .filter(pk=identity("object_id", object_id), company_id=context.company_id)
                .first()
            )
            if target is None:
                raise PermissionDenied("The HR record is unavailable in this scope.")
            if hasattr(target, "branch_id"):
                scope(context, target.branch_id)
        employee_ids = set()
        if target is not None and model is Employee:
            employee_ids.add(target.pk)
        elif target is not None and model in {Attendance, LeaveRequest}:
            employee_ids.add(target.employee_id)
        employee_choices = []
        if operation in {"record_attendance", "create_leave"}:
            query = Employee.objects.using(op.alias).filter(
                company_id=context.company_id,
                status="ACTIVE",
                party__company_id=context.company_id,
                party__is_active=True,
                party__party_type="person",
            )
            if context.branch_id:
                query = query.filter(branch_id=context.branch_id)
            employee_choices = list(
                _search(query, employee_search, "employee_number", "party__display_name")
                .order_by("employee_number", "pk")
                .values_list("pk", "employee_number")[:50]
            )
            employee_ids.update(key for key, _ in employee_choices)
        op.declare_anchors(("hr.employee", key) for key in employee_ids)
        employees = op.lock_rows(Employee, employee_ids)
        if {row.pk for row in employees} != employee_ids:
            raise ValidationError("The Employee reference evidence is incomplete.")
        op.declare_anchors(("hr.employee", key) for key in employee_ids)
        by_employee = {row.pk: row for row in employees}
        include_department = operation in {"create_employee", "update_employee"} and has_permission(
            context, VIEW_DEPARTMENTS
        )
        if (
            target is not None
            and model is Employee
            and target.department_id
            and operation == "update_employee"
        ):
            include_department = True
        if include_department:
            op.declare_permissions([VIEW_DEPARTMENTS])
        department_choices = (
            list(
                _search(
                    Department.objects.using(op.alias).filter(
                        company_id=context.company_id, is_active=True
                    ),
                    department_search,
                    "code",
                    "name",
                )
                .order_by("code", "pk")
                .values_list("pk", "name")[:50]
            )
            if include_department
            else []
        )
        party_choices = (
            list(
                _search(
                    Party.objects.using(op.alias).filter(
                        company_id=context.company_id, is_active=True, party_type="person"
                    ),
                    party_search,
                    "display_name",
                )
                .order_by("display_name", "pk")
                .values_list("pk", "display_name")[:50]
            )
            if operation == "create_employee"
            else []
        )
        branch_choices = (
            list(
                _search(
                    Branch.objects.using(op.alias).filter(
                        company_id=context.company_id, is_active=True
                    ),
                    branch_search,
                    "code",
                    "name",
                )
                .order_by("code", "pk")
                .values_list("pk", "name")[:50]
            )
            if operation in {"create_employee", "transfer_employee_branch"}
            else []
        )
        type_choices = (
            list(
                _search(
                    LeaveType.objects.using(op.alias).filter(
                        company_id=context.company_id, is_active=True
                    ),
                    leave_type_search,
                    "code",
                    "name",
                )
                .order_by("code", "pk")
                .values_list("pk", "name")[:50]
            )
            if operation in {"create_leave", "update_leave"}
            else []
        )
        refs = references(
            op,
            department_ids=[
                *[key for key, _ in department_choices],
                *[row.department_id for row in employees],
                target.pk if target is not None and model is Department else None,
            ],
            branch_ids=[
                context.branch_id,
                *[row.branch_id for row in employees],
                *[key for key, _ in branch_choices],
                target.branch_id
                if target is not None and model in {Attendance, LeaveRequest}
                else None,
            ],
            party_ids=[*[row.party_id for row in employees], *[key for key, _ in party_choices]],
            leave_type_ids=[
                *[key for key, _ in type_choices],
                target.leave_type_id
                if target is not None and model is LeaveRequest
                else target.pk
                if target is not None and model is LeaveType
                else None,
            ],
        )
        choices = {}
        for key, _ in party_choices:
            active_person(refs[Party][key])
        for key, _ in employee_choices:
            active_employee(by_employee[key])
            scope(context, by_employee[key].branch_id)
            active_person(refs[Party][by_employee[key].party_id])
        if employee_choices:
            choices["employee_id"] = tuple(employee_choices)
        if party_choices:
            choices["party_id"] = tuple(
                (key, refs[Party][key].display_name) for key, _ in party_choices
            )
        if include_department:
            choices["department_id"] = tuple(
                (key, refs[Department][key].name) for key, _ in department_choices
            )
        if operation in {"create_employee", "transfer_employee_branch"}:
            choices["branch_id"] = tuple((key, refs[Branch][key].name) for key, _ in branch_choices)
        if operation in {"create_leave", "update_leave"}:
            choices["leave_type_id"] = tuple(
                (key, refs[LeaveType][key].name) for key, _ in type_choices
            )
        record = None
        if target is not None:
            related = {}
            if model is Employee:
                target = by_employee[target.pk]
                scope(context, target.branch_id)
                related["party"] = person_projection(refs[Party][target.party_id])
            elif model in {Attendance, LeaveRequest}:
                target = locked(model, context, target.pk)
                op.declare_anchors([(model._meta.label_lower, target.pk)])
                employee = by_employee[target.employee_id]
                related.update(
                    party=person_projection(refs[Party][employee.party_id]),
                    employee_number=employee.employee_number,
                )
                if model is Attendance:
                    related["current"] = fact(certify_attendance(target))
                else:
                    certify_leave(target)
                    related["leave_type"] = fact(refs[LeaveType][target.leave_type_id])
                    if operation == "cancel_leave" and target.decision == "APPROVED":
                        op.declare_permissions([APPROVE_LEAVE])
            else:
                target = refs[model][target.pk]
            record = fact(target, related=related, department_visible=include_department)
        users = []
        if operation in {"create_employee", "update_employee"}:
            eligible = (
                get_user_model()
                .objects.using(op.alias)
                .filter(is_active=True)
                .filter(
                    Q(is_superuser=True)
                    | Q(
                        pk__in=UserCompanyAccess.objects.using(op.alias)
                        .filter(company_id=context.company_id)
                        .values("user_id")
                    )
                )
            )
            if user_search:
                try:
                    user_key = domain.identity(user_search)
                except (ValueError, TypeError):
                    eligible = eligible.none()
                else:
                    eligible = eligible.filter(pk=user_key)
            users = list(eligible.order_by("pk").values_list("pk", flat=True)[:50])
            choices["user_id"] = tuple((key, str(key)) for key in users)
            if (
                target is not None
                and model is Employee
                and target.user_id
                and target.user_id not in users
            ):
                choices["user_id"] = (*choices["user_id"], (target.user_id, str(target.user_id)))
            if (
                target is not None
                and model is Employee
                and target.department_id
                and include_department
                and all(key != target.department_id for key, _ in choices["department_id"])
            ):
                choices["department_id"] = (
                    *choices["department_id"],
                    (target.department_id, refs[Department][target.department_id].name),
                )
        if (
            target is not None
            and model is Employee
            and "branch_id" in choices
            and target.branch_id is not None
            and all(key != target.branch_id for key, _ in choices["branch_id"])
        ):
            choices["branch_id"] = (
                *choices["branch_id"],
                (target.branch_id, refs[Branch][target.branch_id].name),
            )
        if (
            target is not None
            and model is LeaveRequest
            and "leave_type_id" in choices
            and all(key != target.leave_type_id for key, _ in choices["leave_type_id"])
        ):
            choices["leave_type_id"] = (
                *choices["leave_type_id"],
                (target.leave_type_id, refs[LeaveType][target.leave_type_id].name),
            )
        op.authorize(user_ids=users)
        # User eligibility must be re-read AFTER the returned complete set is held.
        if users:
            from .support import association_eligible

            for key in users:
                association_eligible(key, context.company_id)
        return {
            "record": record,
            "choices": choices,
            "zone": record.timezone
            if record is not None and "timezone" in record.values
            else op.company.timezone,
            "latest": getattr(record, "current", None),
        }


def person_choices(context, *, search="", page=1):
    with hr_operation(context, [VIEW_EMPLOYEES]) as op:
        query = _search(
            Party.objects.using(op.alias).filter(
                company_id=context.company_id, is_active=True, party_type=Party.Type.PERSON
            ),
            search,
            "display_name",
        )
        result = _page(
            query.only("id", "company_id", "party_type", "display_name", "is_active").order_by(
                "display_name", "pk"
            ),
            page,
            lambda row: row,
        )
        ids = [row.pk for row in result.object_list]
        refs = references(op, party_ids=ids)[Party]
        for key in ids:
            active_person(refs[key])
        result.object_list = tuple(person_projection(refs[key]) for key in ids)
        result.paginator.object_list = result.object_list
        op.authorize()
        return result


def action_flags(context):
    """Display hints only; action_admission and services always reauthorize."""
    result = {
        operation: all(has_permission(context, code) for code in codes)
        for operation, codes in _ACTIONS.items()
    }
    if context.branch_id:
        for operation in (
            "create_department",
            "update_department",
            "create_leave_type",
            "update_leave_type",
            "create_employee",
            "transfer_employee_branch",
        ):
            result[operation] = False
    return result


def user_association_choices(context, *, page=1):
    with hr_operation(context, [MANAGE_EMPLOYEES, VIEW_EMPLOYEES]) as op:
        query = (
            get_user_model()
            .objects.using(op.alias)
            .filter(is_active=True)
            .filter(
                Q(is_superuser=True)
                | Q(
                    pk__in=UserCompanyAccess.objects.using(op.alias)
                    .filter(company_id=context.company_id)
                    .values("user_id")
                )
            )
            .order_by("pk")
        )
        result = _page(query.values("id", "is_active"), page, lambda row: row)
        op.authorize(user_ids=[row["id"] for row in result.object_list])
        from .support import association_eligible

        for row in result.object_list:
            association_eligible(row["id"], context.company_id)
        result.object_list = tuple((row["id"], row["is_active"]) for row in result.object_list)
        result.paginator.object_list = result.object_list
        return result


def leave_type_choices(context, **kwargs):
    return leave_type_page(context, **kwargs)
