"""Private bounded conflict discovery; parent identity is always authoritative."""

from django.core.exceptions import ValidationError
from django.db.models import Q

from .admission import ResourceBudgetExceeded
from .civil_time import leave_window
from .history import certify_attendance
from .models import Attendance, AttendanceRevision, LeaveRequest


def attendance_candidates(op, employee, start, end, *, target_id=None):
    ids = list(
        AttendanceRevision.objects.using(op.alias)
        .filter(
            attendance__company_id=employee.company_id,
            attendance__employee_id=employee.pk,
            start_at__lt=end,
            end_at__gt=start,
        )
        .order_by("start_at", "pk")
        .values_list("attendance_id", flat=True)[:1001]
    )
    if len(ids) > 1000:
        raise ResourceBudgetExceeded("Attendance candidates exceed the complete-evidence budget.")
    targets = set(ids)
    if target_id is not None:
        targets.add(target_id)
    op.declare_anchors(("hr.attendance", key) for key in targets)
    parents = op.lock_rows(Attendance, targets)
    if any(row.employee_id != employee.pk for row in parents):
        raise ValidationError("The Attendance parent evidence is incomplete.")
    op.declare_anchors(("hr.attendance", row.pk) for row in parents)
    return {parent.pk: (parent, certify_attendance(parent)) for parent in parents}


def reject_attendance_overlap(candidates, start, end, *, exclude=None):
    for parent_id, (_, current) in candidates.items():
        if (
            parent_id != exclude
            and current.effect == "ACTIVE_INTERVAL"
            and current.start_at < end
            and current.end_at > start
        ):
            raise ValidationError("The interval conflicts with effective Attendance.")


def certify_leave(row):
    # full_clean validates the explicit portable receipt/check/FK invariants; it
    # does not renew activity of historical actors or reference identities.
    row.full_clean()
    if row.employee.company_id != row.company_id or row.leave_type.company_id != row.company_id:
        raise ValidationError("The Leave ownership evidence is corrupt.")
    if row.branch_id and row.branch.company_id != row.company_id:
        raise ValidationError("The frozen Leave Branch ownership is corrupt.")
    if row.decision_key is not None and row.decided_by_id in {
        row.requester_id,
        row.beneficiary_user_at_submission_id,
    }:
        raise ValidationError("The retained Leave decision violates intrinsic separation.")
    if leave_window(row.start_date, row.end_date, row.timezone) != (
        row.window_start_at,
        row.window_end_at,
    ):
        raise ValidationError("The frozen Leave calendar window is corrupt.")
    return row


def leave_candidates(
    op, employee, start, end, *, first=None, last=None, target_id=None, approved_only=False
):
    conditions = Q(window_start_at__lt=end, window_end_at__gt=start)
    if first is not None:
        conditions |= Q(start_date__lte=last, end_date__gte=first)
    discovered = list(
        LeaveRequest.objects.using(op.alias)
        .filter(
            company_id=employee.company_id,
            employee_id=employee.pk,
            status__in=["APPROVED"] if approved_only else ["SUBMITTED", "APPROVED"],
        )
        .filter(conditions | Q(pk=target_id))
        .order_by("pk")[:1001]
    )
    if len(discovered) > 1000:
        raise ResourceBudgetExceeded("Leave candidates exceed the complete-evidence budget.")
    # A DRAFT/terminal target must still join the fixed parent lock union.
    all_ids = {row.pk for row in discovered}
    if target_id is not None:
        all_ids.add(target_id)
    op.declare_anchors(("hr.leaverequest", key) for key in all_ids)
    rows = op.lock_rows(LeaveRequest, all_ids)
    if any(row.employee_id != employee.pk for row in rows):
        raise ValidationError("The Leave parent evidence is incomplete.")
    op.declare_anchors(("hr.leaverequest", row.pk) for row in rows)
    return [certify_leave(row) for row in rows]


def reject_leave_overlap(
    rows, start, end, *, first=None, last=None, exclude=None, approved_only=False
):
    for row in rows:
        if row.pk == exclude or row.status not in (
            {"APPROVED"} if approved_only else {"SUBMITTED", "APPROVED"}
        ):
            continue
        if (row.window_start_at < end and row.window_end_at > start) or (
            first is not None and row.start_date <= last and row.end_date >= first
        ):
            raise ValidationError("The request conflicts with existing Leave.")
