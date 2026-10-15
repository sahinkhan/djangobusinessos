"""Real candidate sentinels, query-plan inspection and noncausal wall clocks."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.utils import timezone

from businessos.core.audit.models import AuditEntry
from businessos.modules.hr import services
from businessos.modules.hr.admission import ResourceBudgetExceeded
from businessos.modules.hr.models import Attendance, AttendanceRevision
from tests import test_hr_services as _fixtures
from tests.test_hr_history import _revision

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def employee(hr_context, hr_person):
    return services.create_employee(
        hr_context, party_id=hr_person.pk, employee_number="BOUNDARY", joining_date=date(2020, 1, 1)
    )


def test_real_1000_plus_one_candidate_sentinel_is_not_a_truncated_success(hr_context, employee):
    start = datetime(2024, 1, 2, 9, tzinfo=UTC)
    initial = services.record_attendance(
        hr_context,
        employee_id=employee.id,
        request_key=uuid4(),
        start_at=start,
        end_at=start + timedelta(hours=1),
    )
    parent = Attendance.objects.get(pk=initial.attendance.id)
    for number in range(2, 1001):
        moved = start + timedelta(microseconds=number)
        _revision(parent, number, start=moved, end=moved + timedelta(hours=1))
    count = AuditEntry.objects.count()
    proposal = {
        "employee_id": employee.id,
        "request_key": uuid4(),
        "start_at": start,
        "end_at": start + timedelta(hours=2),
    }
    with pytest.raises(ValidationError, match="conflicts"):
        services.record_attendance(hr_context, **proposal)
    _revision(parent, 1001, start=start + timedelta(seconds=1), end=start + timedelta(hours=1))
    with pytest.raises(ResourceBudgetExceeded, match="candidates"):
        services.record_attendance(hr_context, **proposal)
    assert Attendance.objects.count() == 1
    assert AttendanceRevision.objects.count() == 1001
    assert AuditEntry.objects.count() == count

    # Inspect the actual database plan for the frozen no-lookback predicate.
    candidates = (
        AttendanceRevision.objects.filter(
            attendance__company_id=hr_context.company_id,
            attendance__employee_id=employee.id,
            start_at__lt=proposal["end_at"],
            end_at__gt=proposal["start_at"],
        )
        .order_by("start_at", "pk")
        .values_list("attendance_id", flat=True)[:1001]
    )
    plan = candidates.explain()
    assert plan.strip()
    assert "LIMIT 1001" in str(candidates.query).upper()
    assert "start_at" in str(candidates.query) and "end_at" in str(candidates.query)
    if connection.vendor == "postgresql":
        assert "Limit" in plan


def test_clock_rollback_does_not_invalidate_revision_causality(hr_context, employee, monkeypatch):
    start = datetime(2024, 1, 2, 9, tzinfo=UTC)
    original = services.record_attendance(
        hr_context,
        employee_id=employee.id,
        request_key=uuid4(),
        start_at=start,
        end_at=start + timedelta(hours=1),
    )
    earlier_clock = datetime(2020, 1, 2, tzinfo=UTC)
    monkeypatch.setattr(timezone, "now", lambda: earlier_clock)
    key = uuid4()
    changed = services.revise_attendance(
        hr_context,
        attendance_id=original.attendance.id,
        expected_revision=1,
        request_key=key,
        operation="CORRECT",
        start_at=start,
        end_at=start + timedelta(hours=2),
        reason="Synthetic correction after clock rollback",
    )
    assert changed.receipt.created_at == earlier_clock
    assert changed.receipt.created_at < original.receipt.created_at
    assert changed.current.number == 2
    retried = services.revise_attendance(
        hr_context,
        attendance_id=original.attendance.id,
        expected_revision=1,
        request_key=key,
        operation="CORRECT",
        start_at=start,
        end_at=start + timedelta(hours=2),
        reason="Synthetic correction after clock rollback",
    )
    assert retried.historical_retry
    assert AttendanceRevision.objects.count() == 2
    assert AuditEntry.objects.filter(action="hr.attendance.corrected").count() == 1
