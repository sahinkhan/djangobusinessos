"""Private, operation-specific persistence.  These are not authorization APIs.

Owning services enter the admitted transaction, lock the complete reference set,
validate domain rules and obtain final Core authorization before invoking these
small primitives. Ordinary managers never provide a writable escape hatch.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connections, models
from django.utils import timezone

from businessos.core.database import current_database_alias
from businessos.core.organization.models import Branch, Company
from businessos.modules.party.models import Party

from . import domain
from .civil_time import leave_window, occupied_dates
from .models import Attendance, AttendanceRevision, Department, Employee, LeaveRequest, LeaveType


def _value(field, normalizer, value, **kwargs):
    try:
        return normalizer(value, **kwargs)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError({field: str(exc)}) from exc


def _identity(field, value, *, optional=False):
    if optional and value is None:
        return None
    return _value(field, domain.identity, value)


def _alias():
    alias = current_database_alias()
    if not connections[alias].in_atomic_block:
        raise ValidationError("HR private persistence requires an owning transaction.")
    return alias


def _locked(model, identity, company_id):
    alias = _alias()
    identity = _identity("id", identity)
    from .admission import _CURRENT, require_domain_anchors

    if _CURRENT.get() is not None:
        require_domain_anchors([(model._meta.label_lower, identity)])
    row = (
        model.objects.using(alias)
        .select_for_update()
        .filter(pk=identity, company_id=_identity("company", company_id))
        .first()
    )
    if row is None:
        raise ValidationError("The HR record is unavailable in the selected company.")
    return row


def _expected(row, expected_revision):
    expected = _value("expected_revision", domain.revision, expected_revision)
    if row.revision != expected:
        raise ValidationError({"expected_revision": "The HR record revision has changed."})


def _insert(row):
    alias = _alias()
    if not row._state.adding or row._state.db not in (None, alias):
        raise ValidationError("Private HR insertion requires a new selected-alias instance.")
    row._state.db = alias
    row.full_clean()
    # Deliberately call the base implementation: public save/save_base stay closed.
    # No mutable enable flag or publicly usable generic persistence method exists.
    models.Model.save_base(row, using=alias, force_insert=True)
    return row


def _write_changed(row, fields):
    alias = _alias()
    if row._state.adding or row._state.db != alias:
        raise ValidationError("Private HR update requires a persisted selected-alias instance.")
    row.revision = _value("revision", domain.next_revision, row.revision)
    row.updated_at = timezone.now()
    row.full_clean()
    models.Model.save_base(
        row,
        using=alias,
        force_update=True,
        update_fields=frozenset([*fields, "revision", "updated_at"]),
    )
    return row


def _scoped_reference(model, identity, company_id, field, *, active=False):
    if identity is None:
        return None
    query = model.objects.using(_alias()).filter(
        pk=_identity(field, identity), company_id=company_id
    )
    if active:
        query = query.filter(is_active=True)
    row = query.first()
    if row is None:
        raise ValidationError({field: "The reference is outside the company or unavailable."})
    return row


def _new_user(user_id):
    if user_id is None:
        return None
    identity = _identity("user", user_id)
    if not get_user_model().objects.using(_alias()).filter(pk=identity, is_active=True).exists():
        raise ValidationError({"user": "The association User must exist and be active."})
    return identity


def _create_department(*, company_id, code, name):
    return _insert(
        Department(
            company_id=_identity("company", company_id),
            code=_value("code", domain.code, code),
            name=_value("name", domain.text, name, maximum=160, required=True),
        )
    )


def _update_department(*, company_id, department_id, expected_revision, name, is_active):
    row = _locked(Department, department_id, company_id)
    _expected(row, expected_revision)
    values = {
        "name": _value("name", domain.text, name, maximum=160, required=True),
        "is_active": _value("is_active", domain.boolean, is_active),
    }
    if (
        not values["is_active"]
        and Employee.objects.using(_alias())
        .filter(company_id=row.company_id, department_id=row.pk, status=Employee.Status.ACTIVE)
        .exists()
    ):
        raise ValidationError(
            {"is_active": "Reassign active Employees before retiring a Department."}
        )
    changed = [field for field, value in values.items() if getattr(row, field) != value]
    for field in changed:
        setattr(row, field, values[field])
    return _write_changed(row, changed) if changed else row


def _create_leave_type(*, company_id, code, name):
    return _insert(
        LeaveType(
            company_id=_identity("company", company_id),
            code=_value("code", domain.code, code),
            name=_value("name", domain.text, name, maximum=160, required=True),
        )
    )


def _update_leave_type(*, company_id, leave_type_id, expected_revision, name, is_active):
    row = _locked(LeaveType, leave_type_id, company_id)
    _expected(row, expected_revision)
    values = {
        "name": _value("name", domain.text, name, maximum=160, required=True),
        "is_active": _value("is_active", domain.boolean, is_active),
    }
    changed = [field for field, value in values.items() if getattr(row, field) != value]
    for field in changed:
        setattr(row, field, values[field])
    return _write_changed(row, changed) if changed else row


def _create_employee(
    *,
    company_id,
    party_id,
    employee_number,
    joining_date,
    user_id=None,
    department_id=None,
    branch_id=None,
):
    company_id = _identity("company", company_id)
    party = _scoped_reference(Party, party_id, company_id, "party", active=True)
    if party is None or party.party_type != Party.Type.PERSON:
        raise ValidationError({"party": "An active same-company PERSON is required."})
    _scoped_reference(Department, department_id, company_id, "department", active=True)
    _scoped_reference(Branch, branch_id, company_id, "branch", active=True)
    return _insert(
        Employee(
            company_id=company_id,
            party_id=party.pk,
            employee_number=_value("employee_number", domain.code, employee_number),
            joining_date=_value("joining_date", domain.calendar_date, joining_date),
            user_id=_new_user(user_id),
            department_id=_identity("department", department_id, optional=True),
            branch_id=_identity("branch", branch_id, optional=True),
        )
    )


def _update_employee(
    *,
    company_id,
    employee_id,
    expected_revision,
    joining_date,
    user_id,
    department_id,
    leaving_date,
):
    row = _locked(Employee, employee_id, company_id)
    _expected(row, expected_revision)
    new_user = _identity("user", user_id, optional=True)
    new_department = _identity("department", department_id, optional=True)
    if new_user != row.user_id:
        _new_user(new_user)
    if new_department != row.department_id:
        _scoped_reference(Department, new_department, row.company_id, "department", active=True)
    if row.status == Employee.Status.ACTIVE and leaving_date is not None:
        raise ValidationError({"leaving_date": "Use end_employee to end an active Employee."})
    values = {
        "joining_date": _value("joining_date", domain.calendar_date, joining_date),
        "user_id": new_user,
        "department_id": new_department,
        "leaving_date": None
        if leaving_date is None
        else _value("leaving_date", domain.calendar_date, leaving_date),
    }
    changed = [field for field, value in values.items() if getattr(row, field) != value]
    for field in changed:
        setattr(row, field, values[field])
    # Exact column sets intentionally do not rewrite an unchanged historical User FK.
    return _write_changed(row, changed) if changed else row


def _end_employee(*, company_id, employee_id, expected_revision, leaving_date):
    row = _locked(Employee, employee_id, company_id)
    _expected(row, expected_revision)
    leaving_date = _value("leaving_date", domain.calendar_date, leaving_date)
    if row.status == Employee.Status.ENDED:
        if row.leaving_date != leaving_date:
            raise ValidationError({"leaving_date": "Use an explicit date correction after ending."})
        return row
    if row.status != Employee.Status.ACTIVE:
        raise ValidationError({"status": "Unsupported persisted Employee lifecycle."})
    row.status = Employee.Status.ENDED
    row.leaving_date = leaving_date
    return _write_changed(row, ["status", "leaving_date"])


def _transfer_employee_branch(*, company_id, employee_id, expected_revision, branch_id):
    row = _locked(Employee, employee_id, company_id)
    _expected(row, expected_revision)
    branch_id = _identity("branch", branch_id, optional=True)
    if row.branch_id == branch_id:
        return row
    _scoped_reference(Branch, branch_id, row.company_id, "branch", active=True)
    row.branch_id = branch_id
    return _write_changed(row, ["branch_id"])


def _zone(value):
    if not isinstance(value, str) or not value or len(value) > 64:
        raise ValidationError({"timezone": "Use an IANA timezone identity."})
    try:
        ZoneInfo(value)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ValidationError({"timezone": "Use a known IANA timezone identity."}) from exc
    return value


def _new_snapshot_zone(company_id, timezone_name):
    value = _zone(timezone_name)
    if (
        not Company.objects.using(_alias())
        .filter(pk=company_id, is_active=True, timezone=value)
        .exists()
    ):
        raise ValidationError({"timezone": "New snapshots use the active Company's current zone."})
    return value


def _instant(field, value):
    if not isinstance(value, datetime):
        raise ValidationError({field: "Use an aware datetime instant."})
    try:
        if timezone.is_naive(value):
            raise ValidationError({field: "Use an aware datetime instant."})
        return value.astimezone(UTC)
    except (ValueError, OverflowError) as exc:
        raise ValidationError(
            {field: "The instant is outside the supported representation."}
        ) from exc


def _actor(value):
    value = _identity("actor", value)
    if not get_user_model().objects.using(_alias()).filter(pk=value).exists():
        raise ValidationError({"actor": "The actor identity does not exist."})
    return value


def _create_attendance(
    *,
    company_id,
    employee_id,
    branch_id,
    timezone_name,
    record_request_key,
    recorded_by_id,
    attendance_id=None,
):
    company_id = _identity("company", company_id)
    employee = _scoped_reference(Employee, employee_id, company_id, "employee")
    if employee is None or employee.status != Employee.Status.ACTIVE:
        raise ValidationError({"employee": "New Attendance requires an active Employee."})
    branch_id = _identity("branch", branch_id, optional=True)
    if employee.branch_id != branch_id:
        raise ValidationError({"branch": "The new Attendance snapshot must match the Employee."})
    _scoped_reference(Branch, branch_id, company_id, "branch", active=True)
    row = Attendance(
        company_id=company_id,
        employee_id=employee.pk,
        branch_id=branch_id,
        timezone=_new_snapshot_zone(company_id, timezone_name),
        record_request_key=_identity("record_request_key", record_request_key),
        recorded_by_id=_actor(recorded_by_id),
    )
    if attendance_id is not None:
        row.pk = _identity("attendance_id", attendance_id)
    return _insert(row)


def _append_attendance_revision(
    *,
    company_id,
    attendance_id,
    expected_revision,
    operation,
    start_at,
    end_at,
    local_start_date,
    local_end_date,
    reason,
    actor_id,
    request_key,
):
    parent = _locked(Attendance, attendance_id, company_id)
    expected = _value("expected_revision", domain.revision, expected_revision, allow_zero=True)
    actor_id = _actor(actor_id)
    request_key = _identity("request_key", request_key)
    reason = _value("reason", domain.text, reason)
    start_at, end_at = _instant("start_at", start_at), _instant("end_at", end_at)
    local_start_date = _value("local_start_date", domain.calendar_date, local_start_date)
    local_end_date = _value("local_end_date", domain.calendar_date, local_end_date)
    if expected == 0:
        if AttendanceRevision.objects.using(_alias()).filter(attendance_id=parent.pk).exists():
            raise ValidationError({"expected_revision": "The Attendance already has history."})
        if (
            operation != AttendanceRevision.Operation.RECORD
            or actor_id != parent.recorded_by_id
            or request_key != parent.record_request_key
        ):
            raise ValidationError(
                "The original revision must retain the Attendance recording identity."
            )
    else:
        # This owner helper certifies EVERY persisted predecessor and historical
        # geometry in the selected chain; latest-only validation is not sufficient.
        from .history import certify_attendance

        latest = certify_attendance(parent)
        if latest.number != expected:
            raise ValidationError({"expected_revision": "The Attendance revision has changed."})
        if not reason:
            raise ValidationError({"reason": "A correction reason is required."})
        if operation == AttendanceRevision.Operation.CORRECT:
            if latest.effect != AttendanceRevision.Effect.ACTIVE_INTERVAL:
                raise ValidationError("Only an active interval can be corrected.")
            if (latest.start_at, latest.end_at) == (start_at, end_at):
                raise ValidationError("A correction must change the effective interval.")
        elif operation == AttendanceRevision.Operation.VOID:
            if latest.effect != AttendanceRevision.Effect.ACTIVE_INTERVAL:
                raise ValidationError("Only an active interval can be voided.")
            if (start_at, end_at, local_start_date, local_end_date) != (
                latest.start_at,
                latest.end_at,
                latest.local_start_date,
                latest.local_end_date,
            ):
                raise ValidationError("A void retains the complete preceding interval and dates.")
        elif operation == AttendanceRevision.Operation.REINSTATE:
            if latest.effect != AttendanceRevision.Effect.VOIDED:
                raise ValidationError("Only a voided interval can be reinstated.")
        else:
            raise ValidationError({"operation": "Unsupported Attendance transition."})
    if start_at >= end_at:
        raise ValidationError({"end_at": "The completed interval must end after its start."})
    try:
        dates = occupied_dates(start_at, end_at, parent.timezone)
    except (ValueError, OverflowError) as exc:
        raise ValidationError({"start_at": str(exc)}) from exc
    if dates != (local_start_date, local_end_date):
        raise ValidationError("Attendance search dates do not match the frozen-zone interval.")
    return _insert(
        AttendanceRevision(
            company_id=parent.company_id,
            employee_id=parent.employee_id,
            attendance_id=parent.pk,
            number=_value("number", domain.next_revision, expected) if expected else 1,
            expected_revision=expected,
            operation=operation,
            effect=AttendanceRevision.Effect.VOIDED
            if operation == AttendanceRevision.Operation.VOID
            else AttendanceRevision.Effect.ACTIVE_INTERVAL,
            start_at=start_at,
            end_at=end_at,
            local_start_date=local_start_date,
            local_end_date=local_end_date,
            reason=reason,
            actor_id=actor_id,
            request_key=request_key,
        )
    )


def _leave_window(start_date, end_date, window_start_at, window_end_at, zone):
    start_date = _value("start_date", domain.calendar_date, start_date)
    end_date = _value("end_date", domain.calendar_date, end_date)
    start_at = _instant("window_start_at", window_start_at)
    end_at = _instant("window_end_at", window_end_at)
    if start_date > end_date or start_at >= end_at:
        raise ValidationError("Leave dates/window are not ordered.")
    try:
        expected_window = leave_window(start_date, end_date, zone)
    except (ValueError, OverflowError) as exc:
        raise ValidationError({"start_date": str(exc)}) from exc
    if (start_at, end_at) != expected_window:
        raise ValidationError(
            "Leave window does not match the exact frozen-zone calendar boundaries."
        )
    return start_date, end_date, start_at, end_at


def _create_leave(
    *,
    company_id,
    employee_id,
    branch_id,
    timezone_name,
    create_request_key,
    requester_id,
    leave_type_id,
    start_date,
    end_date,
    window_start_at,
    window_end_at,
    reason="",
):
    company_id = _identity("company", company_id)
    employee = _scoped_reference(Employee, employee_id, company_id, "employee")
    if employee is None or employee.status != Employee.Status.ACTIVE:
        raise ValidationError({"employee": "New Leave requires an active Employee."})
    branch_id = _identity("branch", branch_id, optional=True)
    if branch_id != employee.branch_id:
        raise ValidationError({"branch": "The new Leave snapshot must match the Employee."})
    _scoped_reference(Branch, branch_id, company_id, "branch", active=True)
    leave_type = _scoped_reference(LeaveType, leave_type_id, company_id, "leave_type", active=True)
    if leave_type is None:
        raise ValidationError({"leave_type": "A LeaveType is required."})
    snapshot_zone = _new_snapshot_zone(company_id, timezone_name)
    start_date, end_date, window_start_at, window_end_at = _leave_window(
        start_date, end_date, window_start_at, window_end_at, snapshot_zone
    )
    return _insert(
        LeaveRequest(
            company_id=company_id,
            employee_id=employee.pk,
            branch_id=branch_id,
            timezone=snapshot_zone,
            create_request_key=_identity("create_request_key", create_request_key),
            requester_id=_actor(requester_id),
            leave_type_id=leave_type.pk,
            start_date=start_date,
            end_date=end_date,
            reason=_value("reason", domain.text, reason),
            window_start_at=window_start_at,
            window_end_at=window_end_at,
        )
    )


def _update_leave(
    *,
    company_id,
    leave_id,
    expected_revision,
    leave_type_id,
    start_date,
    end_date,
    window_start_at,
    window_end_at,
    reason,
):
    row = _locked(LeaveRequest, leave_id, company_id)
    _expected(row, expected_revision)
    if row.status != LeaveRequest.Status.DRAFT:
        raise ValidationError("Only a DRAFT LeaveRequest can be edited.")
    leave_type = _scoped_reference(
        LeaveType, leave_type_id, row.company_id, "leave_type", active=True
    )
    if leave_type is None:
        raise ValidationError({"leave_type": "A LeaveType is required."})
    start_date, end_date, window_start_at, window_end_at = _leave_window(
        start_date, end_date, window_start_at, window_end_at, row.timezone
    )
    values = {
        "leave_type_id": leave_type.pk,
        "start_date": start_date,
        "end_date": end_date,
        "window_start_at": window_start_at,
        "window_end_at": window_end_at,
        "reason": _value("reason", domain.text, reason),
    }
    changed = [field for field, value in values.items() if getattr(row, field) != value]
    for field in changed:
        setattr(row, field, values[field])
    return _write_changed(row, changed) if changed else row


def _submit_leave(*, company_id, leave_id, expected_revision, request_key, actor_id):
    row = _locked(LeaveRequest, leave_id, company_id)
    _expected(row, expected_revision)
    if row.status != LeaveRequest.Status.DRAFT:
        raise ValidationError("Only a DRAFT LeaveRequest can be submitted.")
    employee = _scoped_reference(Employee, row.employee_id, row.company_id, "employee")
    if employee is None:
        raise ValidationError("The Leave Employee is unavailable.")
    row.status = LeaveRequest.Status.SUBMITTED
    row.submit_key = _identity("request_key", request_key)
    row.submitted_by_id = _actor(actor_id)
    row.submitted_at = timezone.now()
    row.submit_from_revision = row.revision
    row.submit_revision = _value("submit_revision", domain.next_revision, row.revision)
    row.beneficiary_user_at_submission_id = employee.user_id
    return _write_changed(
        row,
        [
            "status",
            "submit_key",
            "submitted_by_id",
            "submitted_at",
            "submit_from_revision",
            "submit_revision",
            "beneficiary_user_at_submission_id",
        ],
    )


def _decide_leave(
    *,
    company_id,
    leave_id,
    expected_revision,
    request_key,
    actor_id,
    decision,
    reason="",
):
    row = _locked(LeaveRequest, leave_id, company_id)
    _expected(row, expected_revision)
    if row.status != LeaveRequest.Status.SUBMITTED:
        raise ValidationError("Only a SUBMITTED LeaveRequest can be decided.")
    actor_id = _actor(actor_id)
    employee = _scoped_reference(Employee, row.employee_id, row.company_id, "employee")
    if employee is None or actor_id in {
        row.requester_id,
        employee.user_id,
        row.beneficiary_user_at_submission_id,
    }:
        raise ValidationError("The requester or beneficiary association cannot decide this Leave.")
    if decision not in LeaveRequest.Decision.values:
        raise ValidationError({"decision": "Use APPROVED or REJECTED."})
    row.decision_reason = _value(
        "reason", domain.text, reason, required=decision == LeaveRequest.Decision.REJECTED
    )
    row.status = decision
    row.decision = decision
    row.decision_key = _identity("request_key", request_key)
    row.decided_by_id = actor_id
    row.decided_at = timezone.now()
    row.decision_from_revision = row.revision
    row.decision_revision = _value("decision_revision", domain.next_revision, row.revision)
    return _write_changed(
        row,
        [
            "status",
            "decision",
            "decision_key",
            "decided_by_id",
            "decided_at",
            "decision_from_revision",
            "decision_revision",
            "decision_reason",
        ],
    )


def _cancel_leave(*, company_id, leave_id, expected_revision, request_key, actor_id, reason):
    row = _locked(LeaveRequest, leave_id, company_id)
    _expected(row, expected_revision)
    if row.status not in {
        LeaveRequest.Status.DRAFT,
        LeaveRequest.Status.SUBMITTED,
        LeaveRequest.Status.APPROVED,
    }:
        raise ValidationError("This LeaveRequest cannot be cancelled.")
    row.cancel_reason = _value("reason", domain.text, reason, required=True)
    row.status = LeaveRequest.Status.CANCELLED
    row.cancel_key = _identity("request_key", request_key)
    row.cancelled_by_id = _actor(actor_id)
    row.cancelled_at = timezone.now()
    row.cancel_from_revision = row.revision
    row.cancel_revision = _value("cancel_revision", domain.next_revision, row.revision)
    return _write_changed(
        row,
        [
            "status",
            "cancel_key",
            "cancelled_by_id",
            "cancelled_at",
            "cancel_from_revision",
            "cancel_revision",
            "cancel_reason",
        ],
    )
