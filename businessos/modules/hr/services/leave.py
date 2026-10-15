"""Full-day Leave lifecycle with retained, separately labelled event receipts."""

from dataclasses import dataclass

from django.core.exceptions import PermissionDenied, ValidationError

from businessos.modules.party.models import Party

from .. import domain, persistence
from ..admission import hr_operation
from ..civil_time import leave_window
from ..conflicts import (
    attendance_candidates,
    certify_leave,
    leave_candidates,
    reject_attendance_overlap,
    reject_leave_overlap,
)
from ..manifest import APPROVE_LEAVE, CANCEL_LEAVE, REQUEST_LEAVE, VIEW_EMPLOYEES, VIEW_LEAVE
from ..models import Employee, LeaveRequest, LeaveType
from ..support import (
    active_employee,
    active_person,
    audit,
    employment_dates,
    expected,
    fact,
    identity,
    locked,
    references,
    scope,
    value,
)


@dataclass(frozen=True, slots=True)
class LeaveReceipt:
    leave: object
    event: str
    receipt_revision: int
    current_revision: int
    current_status: str
    historical_retry: bool


def _receipt(row, event, retry=False):
    ordinal = row.revision if event in {"create", "update"} else getattr(row, f"{event}_revision")
    return LeaveReceipt(fact(row), event, ordinal, row.revision, row.status, retry)


def _dates(employee, first, last, zone):
    first = value("start_date", domain.calendar_date, first)
    last = value("end_date", domain.calendar_date, last)
    employment_dates(employee, first, last)
    window = value("dates", leave_window, first, end_date=last, zone=zone)
    return first, last, *window


def _eligibility(employee, refs, leave_type_id):
    active_employee(employee)
    active_person(refs[Party][employee.party_id])
    if not refs[LeaveType][leave_type_id].is_active:
        raise ValidationError("New Leave activity requires an active LeaveType.")


def _discover(op, context, leave_id):
    row = (
        LeaveRequest.objects.using(op.alias)
        .filter(pk=identity("leave_id", leave_id), company_id=context.company_id)
        .first()
    )
    if row is None:
        raise PermissionDenied("The Leave is unavailable in this scope.")
    scope(context, row.branch_id)
    employee = locked(Employee, context, row.employee_id)
    op.declare_anchors([("hr.employee", employee.pk)])
    return row, employee


def _key_available(op, company_id, family, key, row=None):
    query = LeaveRequest.objects.using(op.alias).filter(
        company_id=company_id, **{f"{family}_key": key}
    )
    if row is not None:
        query = query.exclude(pk=row.pk)
        other_keys = [
            getattr(row, f"{other}_key")
            for other in ("submit", "decision", "cancel")
            if other != family
        ]
        if key in other_keys:
            raise ValidationError("Leave event keys must be distinct within a request.")
    if query.exists():
        raise ValidationError("The Company event key is already reserved by another Leave.")


def create_leave(
    context, *, employee_id, create_request_key, leave_type_id, start_date, end_date, reason=""
):
    with hr_operation(context, (REQUEST_LEAVE, VIEW_LEAVE, VIEW_EMPLOYEES)) as op:
        employee = locked(Employee, context, employee_id)
        op.declare_anchors([("hr.employee", employee.pk)])
        scope(context, employee.branch_id)
        leave_type_id = identity("leave_type_id", leave_type_id)
        refs = references(
            op,
            branch_ids=[context.branch_id, employee.branch_id],
            party_ids=[employee.party_id],
            leave_type_ids=[leave_type_id],
        )
        _eligibility(employee, refs, leave_type_id)
        for model, rows in refs.items():
            if model._meta.label_lower == "organization.branch" and any(
                not row.is_active for row in rows.values()
            ):
                raise ValidationError("New Leave requires an active assigned Branch.")
        first, last, start, end = _dates(employee, start_date, end_date, op.company.timezone)
        key = identity("create_request_key", create_request_key)
        if (
            LeaveRequest.objects.using(op.alias)
            .filter(company_id=context.company_id, create_request_key=key)
            .exists()
        ):
            raise ValidationError("The Leave create key already exists; use an authorized lookup.")
        reason = value("reason", domain.text, reason)
        op.authorize()
        row = persistence._create_leave(
            company_id=context.company_id,
            employee_id=employee.pk,
            branch_id=employee.branch_id,
            timezone_name=op.company.timezone,
            create_request_key=key,
            requester_id=context.actor_id,
            leave_type_id=leave_type_id,
            start_date=first,
            end_date=last,
            window_start_at=start,
            window_end_at=end,
            reason=reason,
        )
        audit(context, row, "hr.leave.created", revision=row.revision)
        return _receipt(row, "create")


def update_leave(
    context, *, leave_id, expected_revision, leave_type_id, start_date, end_date, reason
):
    with hr_operation(context, (REQUEST_LEAVE, VIEW_LEAVE, VIEW_EMPLOYEES)) as op:
        discovered, employee = _discover(op, context, leave_id)
        leave_type_id = identity("leave_type_id", leave_type_id)
        refs = references(
            op,
            branch_ids=[context.branch_id, discovered.branch_id],
            party_ids=[employee.party_id],
            leave_type_ids=[discovered.leave_type_id, leave_type_id],
        )
        row = locked(LeaveRequest, context, discovered.pk)
        op.declare_anchors([("hr.leaverequest", row.pk)])
        certify_leave(row)
        expected(row, expected_revision)
        if row.status != "DRAFT":
            raise ValidationError("Only a DRAFT Leave can be edited.")
        _eligibility(employee, refs, leave_type_id)
        first, last, start, end = _dates(employee, start_date, end_date, row.timezone)
        proposed = {
            "leave_type_id": leave_type_id,
            "start_date": first,
            "end_date": last,
            "window_start_at": start,
            "window_end_at": end,
            "reason": value("reason", domain.text, reason),
        }
        changed = [name for name, data in proposed.items() if getattr(row, name) != data]
        op.authorize()
        if changed:
            row = persistence._update_leave(
                company_id=context.company_id,
                leave_id=row.pk,
                expected_revision=expected_revision,
                **proposed,
            )
            audit(context, row, "hr.leave.updated", fields=changed, revision=row.revision)
        return _receipt(row, "update")


def _transition(
    context, *, leave_id, expected_revision, request_key, family, decision=None, reason=""
):
    permissions = {"submit": REQUEST_LEAVE, "decision": APPROVE_LEAVE, "cancel": CANCEL_LEAVE}
    with hr_operation(context, (permissions[family], VIEW_LEAVE, VIEW_EMPLOYEES)) as op:
        discovered, employee = _discover(op, context, leave_id)
        refs = references(
            op,
            branch_ids=[context.branch_id, discovered.branch_id],
            party_ids=[employee.party_id],
            leave_type_ids=[discovered.leave_type_id],
        )
        key = identity("request_key", request_key)
        expected_revision = value("expected_revision", domain.revision, expected_revision)
        reason = value(
            "reason", domain.text, reason, required=family == "cancel" or decision == "REJECTED"
        )
        if family == "decision" and decision not in {"APPROVED", "REJECTED"}:
            raise ValidationError("Use APPROVED or REJECTED.")
        # Discover and lock Attendance before ALL Leave parents. Even rejection
        # prepares no additional parent lock after authority admission.
        attendance = (
            attendance_candidates(
                op, employee, discovered.window_start_at, discovered.window_end_at
            )
            if family == "decision" and decision == "APPROVED"
            else {}
        )
        rows = leave_candidates(
            op,
            employee,
            discovered.window_start_at,
            discovered.window_end_at,
            first=discovered.start_date,
            last=discovered.end_date,
            target_id=discovered.pk,
        )
        row = next(row for row in rows if row.pk == discovered.pk)
        stored_key = getattr(row, f"{family}_key")
        retry = stored_key == key
        if family == "cancel" and row.decision == "APPROVED":
            op.declare_permissions([APPROVE_LEAVE])
        if family == "decision" and context.actor_id in {
            row.requester_id,
            employee.user_id,
            row.beneficiary_user_at_submission_id,
        }:
            raise ValidationError(
                "Requester and current/frozen beneficiary associations cannot decide Leave."
            )
        if retry:
            actor_field = {
                "submit": "submitted_by_id",
                "decision": "decided_by_id",
                "cancel": "cancelled_by_id",
            }[family]
            if (
                getattr(row, actor_field) != context.actor_id
                or getattr(row, f"{family}_from_revision") != expected_revision
            ):
                raise ValidationError("The retained event belongs to different input or actor.")
            if (
                family == "decision"
                and (row.decision != decision or row.decision_reason != reason)
                or family == "cancel"
                and row.cancel_reason != reason
            ):
                raise ValidationError("The retained event input differs.")
            op.authorize()
            return _receipt(row, family, retry=True)
        if stored_key is not None:
            raise ValidationError("This Leave already has a different retained event key.")
        expected(row, expected_revision)
        _key_available(op, context.company_id, family, key, row)
        if family == "submit" or family == "decision" and decision == "APPROVED":
            _eligibility(employee, refs, row.leave_type_id)
            employment_dates(employee, row.start_date, row.end_date)
            reject_leave_overlap(
                rows,
                row.window_start_at,
                row.window_end_at,
                first=row.start_date,
                last=row.end_date,
                exclude=row.pk,
            )
        if (
            family == "submit"
            and row.status != "DRAFT"
            or family == "decision"
            and row.status != "SUBMITTED"
            or family == "cancel"
            and row.status not in {"DRAFT", "SUBMITTED", "APPROVED"}
        ):
            raise ValidationError("This Leave lifecycle transition is not available.")
        if family == "decision" and decision == "APPROVED":
            reject_attendance_overlap(attendance, row.window_start_at, row.window_end_at)
        users = [employee.user_id] if family == "submit" and employee.user_id is not None else []
        op.authorize(user_ids=users)
        kwargs = dict(
            company_id=context.company_id,
            leave_id=row.pk,
            expected_revision=expected_revision,
            request_key=key,
            actor_id=context.actor_id,
        )
        if family == "submit":
            row = persistence._submit_leave(**kwargs)
            action = "submitted"
        elif family == "decision":
            row = persistence._decide_leave(**kwargs, decision=decision, reason=reason)
            action = "approved" if decision == "APPROVED" else "rejected"
        else:
            row = persistence._cancel_leave(**kwargs, reason=reason)
            action = "cancelled"
        audit(context, row, f"hr.leave.{action}", revision=row.revision)
        return _receipt(row, family)


def submit_leave(context, *, leave_id, expected_revision, request_key):
    return _transition(
        context,
        leave_id=leave_id,
        expected_revision=expected_revision,
        request_key=request_key,
        family="submit",
    )


def decide_leave(context, *, leave_id, expected_revision, request_key, decision, reason=""):
    return _transition(
        context,
        leave_id=leave_id,
        expected_revision=expected_revision,
        request_key=request_key,
        family="decision",
        decision=decision,
        reason=reason,
    )


def cancel_leave(context, *, leave_id, expected_revision, request_key, reason):
    return _transition(
        context,
        leave_id=leave_id,
        expected_revision=expected_revision,
        request_key=request_key,
        family="cancel",
        reason=reason,
    )
