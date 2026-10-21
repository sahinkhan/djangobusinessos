"""HR1-AUD-001: retained SQL geometry must equal the civil-rule boundary proof."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection, models

from businessos.core.audit.models import AuditEntry
from businessos.core.database import business_atomic_context
from businessos.modules.hr import civil_time, selectors, services
from businessos.modules.hr.civil_time import UnsupportedCalendarBoundary, occupied_dates
from businessos.modules.hr.history import certify_attendance
from businessos.modules.hr.models import Attendance, AttendanceRevision, Employee
from tests import test_hr_civil_time as _civil_fixtures
from tests import test_hr_services as _setup_fixtures

hr_context = _setup_fixtures.hr_context
hr_person = _setup_fixtures.hr_person

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(params=["exclusive_final_overflow", "first_midnight_underflow"])
def boundary_case(request):
    if request.param == "exclusive_final_overflow":
        return (
            "UTC",
            datetime(9999, 12, 31, 12, tzinfo=UTC),
            date.max,
            datetime(9999, 12, 30, 12, tzinfo=UTC),
        )
    return (
        "Asia/Dhaka",
        datetime(1, 1, 1, 6, tzinfo=UTC),
        date.min,
        datetime(1, 1, 2, 6, tzinfo=UTC),
    )


def _raw_revision(parent, number, start, end, first, last, *, operation=None):
    """Fixture-only base insertion deliberately models corrupt retained evidence."""
    row = AttendanceRevision(
        company_id=parent.company_id,
        employee_id=parent.employee_id,
        attendance_id=parent.pk,
        number=number,
        expected_revision=number - 1,
        operation=operation or ("RECORD" if number == 1 else "CORRECT"),
        effect="VOIDED" if operation == "VOID" else "ACTIVE_INTERVAL",
        start_at=start,
        end_at=end,
        local_start_date=first,
        local_end_date=last,
        reason="" if number == 1 else "Synthetic historical correction",
        actor_id=parent.recorded_by_id,
        request_key=parent.record_request_key if number == 1 else uuid4(),
    )
    models.Model.save_base(row, using=connection.alias, force_insert=True)
    return row


def _retained_history(hr_context, hr_person, boundary_case, *, earlier=False, voided=False):
    zone, invalid_start, invalid_date, valid_start = boundary_case
    employee = services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="AUDIT-CIVIL",
        joining_date=date.min,
    )
    parent = Attendance(
        company_id=hr_context.company_id,
        employee_id=employee.id,
        timezone=zone,
        record_request_key=uuid4(),
        recorded_by_id=hr_context.actor_id,
    )
    models.Model.save_base(parent, using=connection.alias, force_insert=True)
    original = _raw_revision(
        parent,
        1,
        invalid_start,
        invalid_start + timedelta(hours=1),
        invalid_date,
        invalid_date,
    )
    current = original
    if earlier or voided:
        valid_end = valid_start + timedelta(hours=1)
        first, last = occupied_dates(valid_start, valid_end, zone)
        current = _raw_revision(parent, 2, valid_start, valid_end, first, last)
    if voided:
        current = _raw_revision(
            parent,
            3,
            current.start_at,
            current.end_at,
            current.local_start_date,
            current.local_end_date,
            operation="VOID",
        )
    return parent, original, current, valid_start


def _snapshot():
    return tuple(
        tuple(model.objects.order_by("pk").values_list())
        for model in (Attendance, AttendanceRevision, Employee, AuditEntry)
    )


@pytest.mark.parametrize("earlier", [False, True])
@pytest.mark.parametrize(
    "action", ["certificate", "detail", "history", "list", "record_retry", "correct", "void"]
)
def test_all_authoritative_paths_reject_unrepresentable_retained_boundary(
    hr_context, hr_person, boundary_case, earlier, action
):
    parent, original, current, valid_start = _retained_history(
        hr_context, hr_person, boundary_case, earlier=earlier
    )
    with pytest.raises(UnsupportedCalendarBoundary):
        occupied_dates(original.start_at, original.end_at, parent.timezone)
    before = _snapshot()
    with pytest.raises(ValidationError, match="retained facts"):
        if action == "certificate":
            with business_atomic_context():
                certify_attendance(parent)
        elif action == "detail":
            selectors.attendance_detail(hr_context, parent.pk)
        elif action == "history":
            selectors.revision_page(hr_context, parent.pk)
        elif action == "list":
            selectors.attendance_page(
                hr_context,
                start_date=current.local_start_date,
                end_date=current.local_end_date,
            )
        elif action == "record_retry":
            services.record_attendance(
                hr_context,
                employee_id=parent.employee_id,
                request_key=parent.record_request_key,
                start_at=original.start_at,
                end_at=original.end_at,
            )
        else:
            replacement = valid_start + timedelta(hours=2)
            services.revise_attendance(
                hr_context,
                attendance_id=parent.pk,
                expected_revision=current.number,
                request_key=uuid4(),
                operation=action.upper(),
                reason="Synthetic correction must not certify corrupt history",
                **(
                    {}
                    if action == "void"
                    else {"start_at": replacement, "end_at": replacement + timedelta(hours=1)}
                ),
            )
    assert _snapshot() == before


def test_revision_retry_does_not_certify_valid_later_event_over_corrupt_original(
    hr_context, hr_person, boundary_case
):
    parent, _, current, _ = _retained_history(hr_context, hr_person, boundary_case, earlier=True)
    before = _snapshot()
    with pytest.raises(ValidationError, match="retained facts"):
        services.revise_attendance(
            hr_context,
            attendance_id=parent.pk,
            expected_revision=1,
            request_key=current.request_key,
            operation="CORRECT",
            start_at=current.start_at,
            end_at=current.end_at,
            reason=current.reason,
        )
    assert _snapshot() == before


def test_reinstate_cannot_skip_corrupt_earlier_geometry(hr_context, hr_person, boundary_case):
    parent, _, current, valid_start = _retained_history(
        hr_context, hr_person, boundary_case, voided=True
    )
    before = _snapshot()
    with pytest.raises(ValidationError, match="retained facts"):
        services.revise_attendance(
            hr_context,
            attendance_id=parent.pk,
            expected_revision=current.number,
            request_key=uuid4(),
            operation="REINSTATE",
            start_at=valid_start,
            end_at=valid_start + timedelta(hours=1),
            reason="Synthetic reinstatement must fail closed",
        )
    assert _snapshot() == before


def test_conflict_discovery_certifies_entire_candidate_not_only_latest(
    hr_context, hr_person, boundary_case
):
    parent, _, current, _ = _retained_history(hr_context, hr_person, boundary_case, earlier=True)
    # For the future extreme the current Company must use that frozen zone too;
    # otherwise this checks UTC's identical supported December 30 geometry.
    before = _snapshot()
    with pytest.raises(ValidationError, match="retained facts"):
        services.record_attendance(
            hr_context,
            employee_id=parent.employee_id,
            request_key=uuid4(),
            start_at=current.start_at,
            end_at=current.end_at,
        )
    assert _snapshot() == before


def test_employment_eligibility_cannot_skip_corrupt_superseded_boundary(hr_context, hr_person):
    case = (
        "Asia/Dhaka",
        datetime(1, 1, 1, 6, tzinfo=UTC),
        date.min,
        datetime(1, 1, 2, 6, tzinfo=UTC),
    )
    parent, _, _, _ = _retained_history(hr_context, hr_person, case, earlier=True)
    before = _snapshot()
    with pytest.raises(ValidationError, match="retained facts"):
        services.update_employee(
            hr_context,
            employee_id=parent.employee_id,
            expected_revision=1,
            joining_date=date(1, 1, 2),
        )
    assert _snapshot() == before


@pytest.mark.parametrize(
    ("zone", "start"),
    [
        ("UTC", datetime(9999, 12, 30, 12, tzinfo=UTC)),
        ("Asia/Dhaka", datetime(1, 1, 2, 6, tzinfo=UTC)),
    ],
)
def test_supported_adjacent_extreme_boundaries_remain_certifiable(
    hr_context, hr_person, zone, start
):
    employee = services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="AUDIT-CIVIL-VALID",
        joining_date=date.min,
    )
    parent = Attendance(
        company_id=hr_context.company_id,
        employee_id=employee.id,
        timezone=zone,
        record_request_key=uuid4(),
        recorded_by_id=hr_context.actor_id,
    )
    models.Model.save_base(parent, using=connection.alias, force_insert=True)
    end = start + timedelta(hours=1)
    first, last = occupied_dates(start, end, zone)
    revision = _raw_revision(parent, 1, start, end, first, last)
    with business_atomic_context():
        assert certify_attendance(parent).pk == revision.pk
    assert selectors.attendance_detail(hr_context, parent.pk).current.id == revision.pk


def test_boundary_proof_includes_second_midnight_candidate_beyond_old_two_day_halo(
    hr_context, hr_person, monkeypatch
):
    start = datetime(2026, 1, 1, 1, 30, tzinfo=UTC)
    end = datetime(2026, 1, 1, 2, tzinfo=UTC)
    transition = datetime(2026, 1, 3, 6, tzinfo=UTC)
    transition_second = civil_time.instant_us(transition) // civil_time.SECOND_US
    raw = _civil_fixtures._tzif(
        "NEW23",
        transitions=((transition_second, 1),),
        records=((23 * 3600, 0, 0), (-23 * 3600, 0, 4)),
        names=b"OLD\0NEW\0",
    )
    native = _civil_fixtures._install(monkeypatch, raw)
    exclusive_wall = datetime(2026, 1, 3)
    midnight_candidates = {
        exclusive_wall.replace(tzinfo=native, fold=fold).astimezone(UTC) for fold in (0, 1)
    }
    assert len(midnight_candidates) == 2
    assert transition > end + timedelta(days=2)
    assert max(midnight_candidates) > end + timedelta(days=2)
    with pytest.raises(UnsupportedCalendarBoundary):
        occupied_dates(start, end, "Synthetic/Review")
    employee = services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="AUDIT-CIVIL-HALO",
        joining_date=date.min,
    )
    parent = Attendance(
        company_id=hr_context.company_id,
        employee_id=employee.id,
        timezone="Synthetic/Review",
        record_request_key=uuid4(),
        recorded_by_id=hr_context.actor_id,
    )
    models.Model.save_base(parent, using=connection.alias, force_insert=True)
    _raw_revision(parent, 1, start, end, date(2026, 1, 2), date(2026, 1, 2))
    before = _snapshot()
    with pytest.raises(ValidationError, match="retained facts"):
        with business_atomic_context():
            certify_attendance(parent)
    assert _snapshot() == before
