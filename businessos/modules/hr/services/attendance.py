"""Completed sessions and immutable historical revision receipts."""

from dataclasses import dataclass
from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError

from businessos.modules.party.models import Party

from .. import domain, persistence
from ..admission import hr_operation
from ..civil_time import normalize_instant, occupied_dates
from ..conflicts import (
    attendance_candidates,
    leave_candidates,
    reject_attendance_overlap,
    reject_leave_overlap,
)
from ..history import certify_attendance
from ..manifest import CORRECT_ATTENDANCE, RECORD_ATTENDANCE, VIEW_ATTENDANCE, VIEW_EMPLOYEES
from ..models import Attendance, AttendanceRevision, Employee
from ..support import (
    active_employee,
    active_person,
    audit,
    employment_dates,
    fact,
    identity,
    locked,
    references,
    scope,
    value,
)


@dataclass(frozen=True, slots=True)
class AttendanceReceipt:
    attendance: object
    receipt: object
    current: object
    historical_retry: bool


def _receipt(parent, matched, current, *, retry):
    return AttendanceReceipt(fact(parent), fact(matched), fact(current), retry)


def record_attendance(context, *, employee_id, request_key, start_at, end_at, reason=""):
    with hr_operation(context, (RECORD_ATTENDANCE, VIEW_ATTENDANCE, VIEW_EMPLOYEES)) as op:
        employee_id = identity("employee_id", employee_id)
        request_key = identity("request_key", request_key)
        start_at = value("start_at", normalize_instant, start_at)
        end_at = value("end_at", normalize_instant, end_at)
        reason = value("reason", domain.text, reason)
        old = (
            Attendance.objects.using(op.alias)
            .filter(company_id=context.company_id, record_request_key=request_key)
            .first()
        )
        employee = locked(Employee, context, old.employee_id if old else employee_id)
        op.declare_anchors([("hr.employee", employee.pk)])
        refs = references(
            op,
            branch_ids=[context.branch_id, employee.branch_id, old.branch_id if old else None],
            party_ids=[employee.party_id],
        )
        if old is not None:
            parent = locked(Attendance, context, old.pk)
            op.declare_anchors([("hr.attendance", parent.pk)])
            scope(context, parent.branch_id)
            current = certify_attendance(parent)
            original = AttendanceRevision.objects.using(op.alias).get(
                attendance_id=parent.pk, number=1
            )
            if employee_id != parent.employee_id or (
                original.actor_id,
                original.request_key,
                original.start_at,
                original.end_at,
                original.reason,
            ) != (context.actor_id, request_key, start_at, end_at, reason):
                raise ValidationError(
                    "The record request key belongs to a different original effect."
                )
            op.authorize()
            return _receipt(parent, original, current, retry=True)
        scope(context, employee.branch_id)
        active_employee(employee)
        active_person(refs[Party][employee.party_id])
        for model, rows in refs.items():
            if model._meta.label_lower == "organization.branch" and any(
                not row.is_active for row in rows.values()
            ):
                raise ValidationError("New Attendance requires an active assigned Branch.")
        first, last = value(
            "interval", occupied_dates, start_at, end=end_at, zone=op.company.timezone
        )
        employment_dates(employee, first, last)
        candidates = attendance_candidates(op, employee, start_at, end_at)
        reject_attendance_overlap(candidates, start_at, end_at)
        leaves = leave_candidates(op, employee, start_at, end_at, approved_only=True)
        reject_leave_overlap(leaves, start_at, end_at, approved_only=True)
        new_id = uuid4()
        op.reserve_attendance(new_id)
        op.authorize()
        parent = persistence._create_attendance(
            attendance_id=new_id,
            company_id=context.company_id,
            employee_id=employee.pk,
            branch_id=employee.branch_id,
            timezone_name=op.company.timezone,
            record_request_key=request_key,
            recorded_by_id=context.actor_id,
        )
        original = persistence._append_attendance_revision(
            company_id=context.company_id,
            attendance_id=parent.pk,
            expected_revision=0,
            operation="RECORD",
            start_at=start_at,
            end_at=end_at,
            local_start_date=first,
            local_end_date=last,
            reason=reason,
            actor_id=context.actor_id,
            request_key=request_key,
        )
        audit(context, parent, "hr.attendance.recorded", revision_id=str(original.pk), revision=1)
        return _receipt(parent, original, original, retry=False)


def revise_attendance(
    context,
    *,
    attendance_id,
    expected_revision,
    request_key,
    operation,
    start_at=None,
    end_at=None,
    reason,
):
    with hr_operation(context, (CORRECT_ATTENDANCE, VIEW_ATTENDANCE, VIEW_EMPLOYEES)) as op:
        request_key = identity("request_key", request_key)
        expected_revision = value("expected_revision", domain.revision, expected_revision)
        reason = value("reason", domain.text, reason, required=True)
        if operation not in {"CORRECT", "VOID", "REINSTATE"}:
            raise ValidationError({"operation": "Use CORRECT, VOID or REINSTATE."})
        if operation == "VOID" and (start_at is not None or end_at is not None):
            raise ValidationError("VOID does not accept replacement interval inputs.")
        if operation != "VOID":
            start_at = value("start_at", normalize_instant, start_at)
            end_at = value("end_at", normalize_instant, end_at)
        discovered = (
            Attendance.objects.using(op.alias)
            .filter(pk=identity("attendance_id", attendance_id), company_id=context.company_id)
            .first()
        )
        if discovered is None:
            raise PermissionDenied("The Attendance is unavailable in this scope.")
        employee = locked(Employee, context, discovered.employee_id)
        op.declare_anchors([("hr.employee", employee.pk)])
        references(
            op, branch_ids=[context.branch_id, discovered.branch_id], party_ids=[employee.party_id]
        )
        scope(context, discovered.branch_id)
        # The Company mutex serializes supported appends during plain discovery.
        current = certify_attendance(discovered)
        matched = (
            AttendanceRevision.objects.using(op.alias)
            .filter(attendance_id=discovered.pk, request_key=request_key)
            .first()
        )
        if matched is not None:
            parent = locked(Attendance, context, discovered.pk)
            op.declare_anchors([("hr.attendance", parent.pk)])
            if (
                (matched.operation, matched.expected_revision, matched.actor_id, matched.reason)
                != (operation, expected_revision, context.actor_id, reason)
                or operation != "VOID"
                and (matched.start_at, matched.end_at) != (start_at, end_at)
            ):
                raise ValidationError("The correction key belongs to different retained input.")
            op.authorize()
            return _receipt(parent, matched, current, retry=True)
        if current.number != expected_revision:
            raise ValidationError("The Attendance revision changed.")
        if operation == "VOID":
            start_at, end_at = current.start_at, current.end_at
        first, last = value(
            "interval", occupied_dates, start_at, end=end_at, zone=discovered.timezone
        )
        employment_dates(employee, first, last)
        candidates = attendance_candidates(op, employee, start_at, end_at, target_id=discovered.pk)
        parent, current = candidates[discovered.pk]
        if operation != "VOID":
            reject_attendance_overlap(candidates, start_at, end_at, exclude=parent.pk)
        leaves = leave_candidates(op, employee, start_at, end_at, approved_only=True)
        if operation != "VOID":
            reject_leave_overlap(leaves, start_at, end_at, approved_only=True)
        op.authorize()
        revision = persistence._append_attendance_revision(
            company_id=context.company_id,
            attendance_id=parent.pk,
            expected_revision=expected_revision,
            operation=operation,
            start_at=start_at,
            end_at=end_at,
            local_start_date=first,
            local_end_date=last,
            reason=reason,
            actor_id=context.actor_id,
            request_key=request_key,
        )
        action = {"CORRECT": "corrected", "VOID": "voided", "REINSTATE": "reinstated"}[operation]
        audit(
            context,
            parent,
            f"hr.attendance.{action}",
            revision_id=str(revision.pk),
            revision=revision.number,
        )
        return _receipt(parent, revision, revision, retry=False)
