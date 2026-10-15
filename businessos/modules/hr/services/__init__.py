"""Explicit HR owner use cases; all public results are materialized HR facts."""

from django.core.exceptions import ValidationError

from .. import domain, persistence
from ..admission import ResourceBudgetExceeded, hr_operation
from ..history import certify_attendance
from ..manifest import (
    MANAGE_DEPARTMENTS,
    MANAGE_EMPLOYEES,
    MANAGE_LEAVE_TYPES,
    VIEW_DEPARTMENTS,
    VIEW_EMPLOYEES,
    VIEW_LEAVE,
)
from ..models import Attendance, AttendanceRevision, Department, Employee, LeaveRequest, LeaveType
from ..support import (
    active_person,
    association_eligible,
    audit,
    company_context,
    expected,
    fact,
    identity,
    locked,
    person_projection,
    references,
    scope,
    today,
    value,
)
from .attendance import record_attendance, revise_attendance  # noqa: F401
from .leave import (  # noqa: F401
    cancel_leave,
    create_leave,
    decide_leave,
    submit_leave,
    update_leave,
)


def _setup_create(context, model, code, name):
    codes = (
        (MANAGE_DEPARTMENTS, VIEW_DEPARTMENTS)
        if model is Department
        else (MANAGE_LEAVE_TYPES, VIEW_LEAVE)
    )
    with hr_operation(context, codes) as op:
        company_context(context)
        code = value("code", domain.code, code)
        name = value("name", domain.text, name, maximum=160, required=True)
        if model.objects.using(op.alias).filter(company_id=context.company_id, code=code).exists():
            raise ValidationError({"code": "This Company code is already reserved."})
        op.authorize()
        create = (
            persistence._create_department
            if model is Department
            else persistence._create_leave_type
        )
        row = create(company_id=context.company_id, code=code, name=name)
        audit(
            context,
            row,
            f"hr.{'department' if model is Department else 'leave_type'}.created",
            revision=row.revision,
        )
        return fact(row)


def create_department(context, *, code, name):
    return _setup_create(context, Department, code, name)


def create_leave_type(context, *, code, name):
    return _setup_create(context, LeaveType, code, name)


def _setup_update(context, model, row_id, expected_revision, name, is_active):
    codes = (
        (MANAGE_DEPARTMENTS, VIEW_DEPARTMENTS)
        if model is Department
        else (MANAGE_LEAVE_TYPES, VIEW_LEAVE)
    )
    with hr_operation(context, codes) as op:
        company_context(context)
        row = locked(model, context, row_id)
        op.declare_anchors([(model._meta.label_lower, row.pk)])
        expected(row, expected_revision)
        proposed = {
            "name": value("name", domain.text, name, maximum=160, required=True),
            "is_active": value("is_active", domain.boolean, is_active),
        }
        if (
            model is Department
            and not proposed["is_active"]
            and Employee.objects.using(op.alias)
            .filter(
                company_id=context.company_id, department_id=row.pk, status=Employee.Status.ACTIVE
            )
            .exists()
        ):
            raise ValidationError("Reassign active Employees before retiring their Department.")
        changed = [field for field, data in proposed.items() if getattr(row, field) != data]
        op.authorize()
        if changed:
            kwargs = {
                "company_id": context.company_id,
                "expected_revision": expected_revision,
                **proposed,
            }
            if model is Department:
                row = persistence._update_department(department_id=row.pk, **kwargs)
            else:
                row = persistence._update_leave_type(leave_type_id=row.pk, **kwargs)
            audit(
                context,
                row,
                f"hr.{'department' if model is Department else 'leave_type'}.updated",
                fields=changed,
                revision=row.revision,
            )
        return fact(row)


def update_department(context, *, department_id, expected_revision, name, is_active):
    return _setup_update(context, Department, department_id, expected_revision, name, is_active)


def update_leave_type(context, *, leave_type_id, expected_revision, name, is_active):
    return _setup_update(context, LeaveType, leave_type_id, expected_revision, name, is_active)


def create_employee(
    context,
    *,
    party_id,
    employee_number,
    joining_date,
    user_id=None,
    department_id=None,
    branch_id=None,
):
    with hr_operation(context, (MANAGE_EMPLOYEES, VIEW_EMPLOYEES)) as op:
        company_context(context)
        party_id = identity("party_id", party_id)
        department_id = identity("department_id", department_id, optional=True)
        branch_id = identity("branch_id", branch_id, optional=True)
        user_id = identity("user_id", user_id, optional=True)
        refs = references(
            op, department_ids=[department_id], branch_ids=[branch_id], party_ids=[party_id]
        )
        party = refs[next(model for model in refs if model._meta.label_lower == "party.party")][
            party_id
        ]
        active_person(party)
        joining_date = value("joining_date", domain.calendar_date, joining_date)
        if joining_date > today(op.company):
            raise ValidationError({"joining_date": "Joining date cannot be in the future."})
        employee_number = value("employee_number", domain.code, employee_number)
        if department_id is not None:
            op.declare_permissions([VIEW_DEPARTMENTS])
        for model, rows in refs.items():
            if model._meta.label_lower != "party.party" and any(
                not row.is_active for row in rows.values()
            ):
                raise ValidationError("New assignments require active references.")
        op.authorize(user_ids=[] if user_id is None else [user_id])
        association_eligible(user_id, context.company_id)
        row = persistence._create_employee(
            company_id=context.company_id,
            party_id=party_id,
            employee_number=employee_number,
            joining_date=joining_date,
            user_id=user_id,
            department_id=department_id,
            branch_id=branch_id,
        )
        audit(context, row, "hr.employee.created", revision=row.revision)
        return fact(
            row,
            related={"party": person_projection(party)},
            department_visible=department_id is not None,
        )


def _eligibility_history(op, employee, joining_date, leaving_date):
    from django.db.models import Q

    outside = Q(local_start_date__lt=joining_date)
    if leaving_date is not None:
        outside |= Q(local_end_date__gt=leaving_date)
    candidate_ids = list(
        AttendanceRevision.objects.using(op.alias)
        .filter(attendance__company_id=employee.company_id, attendance__employee_id=employee.pk)
        .filter(outside)
        .order_by("id")
        .values_list("attendance_id", flat=True)[:1001]
    )
    if len(candidate_ids) > domain.MATERIALIZATION_LIMIT:
        raise ResourceBudgetExceeded("Employment eligibility evidence exceeds the work budget.")
    op.declare_anchors(("hr.attendance", key) for key in set(candidate_ids))
    parents = list(
        Attendance.objects.using(op.alias)
        .select_for_update()
        .filter(pk__in=candidate_ids)
        .order_by("pk")
    )
    op.declare_anchors(("hr.attendance", row.pk) for row in parents)
    for parent in parents:
        current = certify_attendance(parent)
        if current.effect == "ACTIVE_INTERVAL" and (
            current.local_start_date < joining_date
            or leaving_date is not None
            and current.local_end_date > leaving_date
        ):
            raise ValidationError(
                "Effective Attendance conflicts with the proposed employment dates."
            )
    leave_outside = Q(start_date__lt=joining_date)
    if leaving_date is not None:
        leave_outside |= Q(end_date__gt=leaving_date)
    leave_query = (
        LeaveRequest.objects.using(op.alias)
        .filter(
            company_id=employee.company_id,
            employee_id=employee.pk,
            status__in=["SUBMITTED", "APPROVED"],
        )
        .filter(leave_outside)
        .order_by("pk")
    )
    leave_ids = list(leave_query.values_list("pk", flat=True)[:1001])
    if len(leave_ids) > domain.MATERIALIZATION_LIMIT:
        raise ResourceBudgetExceeded("Employment Leave evidence exceeds the work budget.")
    op.declare_anchors(("hr.leaverequest", key) for key in leave_ids)
    leaves = list(leave_query.filter(pk__in=leave_ids).select_for_update())
    op.declare_anchors(("hr.leaverequest", row.pk) for row in leaves)
    if leaves:
        raise ValidationError("Existing Leave conflicts with the proposed employment dates.")


def update_employee(context, *, employee_id, expected_revision, **changes):
    allowed = {"joining_date", "user_id", "department_id", "leaving_date"}
    if changes.keys() - allowed:
        raise ValidationError("Unsupported Employee fields.")
    with hr_operation(context, (MANAGE_EMPLOYEES, VIEW_EMPLOYEES)) as op:
        row = locked(Employee, context, employee_id)
        op.declare_anchors([("hr.employee", row.pk)])
        scope(context, row.branch_id)
        expected(row, expected_revision)
        proposed = {name: getattr(row, name) for name in allowed}
        for name, raw in changes.items():
            proposed[name] = (
                identity(name, raw, optional=True)
                if name in {"user_id", "department_id"}
                else value(name, domain.calendar_date, raw)
            )
        refs = references(
            op,
            department_ids=[row.department_id, proposed["department_id"]],
            branch_ids=[context.branch_id, row.branch_id],
            party_ids=[row.party_id],
        )
        if row.department_id or proposed["department_id"]:
            op.declare_permissions([VIEW_DEPARTMENTS])
        if proposed["joining_date"] > today(op.company):
            raise ValidationError("Joining date cannot be in the future.")
        if row.status == "ACTIVE" and proposed["leaving_date"] is not None:
            raise ValidationError("End employment through its explicit operation.")
        if row.status == "ENDED" and (
            proposed["leaving_date"] is None
            or not proposed["joining_date"] <= proposed["leaving_date"] <= today(op.company)
        ):
            raise ValidationError("Ended employment needs ordered, non-future dates.")
        from businessos.modules.party.models import Party

        party = refs[Party][row.party_id]
        new_link = proposed["user_id"] is not None and proposed["user_id"] != row.user_id
        new_dept = (
            proposed["department_id"] is not None and proposed["department_id"] != row.department_id
        )
        if new_link or new_dept:
            active_person(party)
        if new_dept and not refs[Department][proposed["department_id"]].is_active:
            raise ValidationError("Select an active Department.")
        _eligibility_history(op, row, proposed["joining_date"], proposed["leaving_date"])
        changed = [name for name, data in proposed.items() if getattr(row, name) != data]
        op.authorize(user_ids=[proposed["user_id"]] if new_link else [])
        if new_link:
            association_eligible(proposed["user_id"], context.company_id)
        if changed:
            row = persistence._update_employee(
                company_id=context.company_id,
                employee_id=row.pk,
                expected_revision=expected_revision,
                **proposed,
            )
            audit(context, row, "hr.employee.updated", fields=changed, revision=row.revision)
        return fact(
            row,
            related={"party": person_projection(party)},
            department_visible=bool(row.department_id),
        )


def end_employee(context, *, employee_id, expected_revision, leaving_date):
    with hr_operation(context, (MANAGE_EMPLOYEES, VIEW_EMPLOYEES)) as op:
        row = locked(Employee, context, employee_id)
        op.declare_anchors([("hr.employee", row.pk)])
        scope(context, row.branch_id)
        expected(row, expected_revision)
        leaving_date = value("leaving_date", domain.calendar_date, leaving_date)
        references(op, branch_ids=[context.branch_id, row.branch_id], party_ids=[row.party_id])
        if not row.joining_date <= leaving_date <= today(op.company):
            raise ValidationError("Leaving date must be within employment and no later than today.")
        if row.status == "ENDED" and row.leaving_date != leaving_date:
            raise ValidationError("Use a versioned date correction for ended employment.")
        _eligibility_history(op, row, row.joining_date, leaving_date)
        op.authorize()
        if row.status == "ACTIVE":
            row = persistence._end_employee(
                company_id=context.company_id,
                employee_id=row.pk,
                expected_revision=expected_revision,
                leaving_date=leaving_date,
            )
            audit(context, row, "hr.employee.ended", revision=row.revision)
        return fact(row)


def transfer_employee_branch(context, *, employee_id, expected_revision, branch_id):
    with hr_operation(context, (MANAGE_EMPLOYEES, VIEW_EMPLOYEES)) as op:
        company_context(context)
        row = locked(Employee, context, employee_id)
        op.declare_anchors([("hr.employee", row.pk)])
        expected(row, expected_revision)
        branch_id = identity("branch_id", branch_id, optional=True)
        refs = references(op, branch_ids=[row.branch_id, branch_id], party_ids=[row.party_id])
        if branch_id != row.branch_id and branch_id is not None:
            from businessos.core.organization.models import Branch
            from businessos.modules.party.models import Party

            active_person(refs[Party][row.party_id])
            if not refs[Branch][branch_id].is_active:
                raise ValidationError("Select an active Branch.")
        op.authorize()
        if branch_id != row.branch_id:
            old_branch = row.branch_id
            row = persistence._transfer_employee_branch(
                company_id=context.company_id,
                employee_id=row.pk,
                expected_revision=expected_revision,
                branch_id=branch_id,
            )
            audit(
                context,
                row,
                "hr.employee.branch_changed",
                old_branch=str(old_branch) if old_branch else None,
                new_branch=str(branch_id) if branch_id else None,
                revision=row.revision,
            )
        return fact(row)
