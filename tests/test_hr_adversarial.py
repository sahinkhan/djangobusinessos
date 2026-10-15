"""Bounded lifecycle rollback, scoped readback and native-value regressions."""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from businessos.core.access.models import RolePermission, UserCompanyAccess, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.modules.hr import selectors, services
from businessos.modules.hr.models import Attendance, AttendanceRevision, LeaveRequest
from businessos.modules.party.models import Party
from tests import test_hr_services as _fixtures

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)
START = datetime(2024, 1, 2, 8, tzinfo=UTC)


@pytest.fixture
def employee(hr_context, hr_person):
    return services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="ADVERSARIAL",
        joining_date=date(2020, 1, 1),
    )


@pytest.fixture
def approver(hr_context):
    user = get_user_model().objects.create_user("adversarial-approver@example.test", "synthetic")
    UserCompanyAccess.objects.create(user=user, company_id=hr_context.company_id)
    role_id = UserRoleAssignment.objects.get(user_id=hr_context.actor_id).role_id
    UserRoleAssignment.objects.create(user=user, company_id=hr_context.company_id, role_id=role_id)
    return BusinessContext(actor_id=user.pk, company_id=hr_context.company_id)


def _record(context, employee, start=START):
    return services.record_attendance(
        context,
        employee_id=employee.id,
        request_key=uuid4(),
        start_at=start,
        end_at=start + timedelta(hours=1),
    )


def _snapshot(*models):
    return tuple(tuple(model.objects.order_by("pk").values()) for model in models)


def _raw_update(row, **changes):
    values, assignments = [], []
    for name, value in changes.items():
        field = row._meta.get_field(name)
        assignments.append(f"{connection.ops.quote_name(field.column)}=%s")
        values.append(field.get_db_prep_save(value, connection))
    values.append(row._meta.pk.get_db_prep_value(row.pk, connection))
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {connection.ops.quote_name(row._meta.db_table)} "
            f"SET {','.join(assignments)} WHERE id=%s",
            values,
        )


@pytest.mark.parametrize("operation", ["RECORD", "CORRECT", "VOID", "REINSTATE"])
def test_every_attendance_effect_and_audit_roll_back_together(hr_context, employee, operation):
    original = None if operation == "RECORD" else _record(hr_context, employee)
    ordinal = 1
    if operation == "REINSTATE":
        services.revise_attendance(
            hr_context,
            attendance_id=original.attendance.id,
            expected_revision=1,
            request_key=uuid4(),
            operation="VOID",
            reason="Synthetic prior void",
        )
        ordinal = 2
    before = _snapshot(Attendance, AttendanceRevision, AuditEntry)
    with (
        patch(
            "businessos.modules.hr.services.attendance.audit",
            side_effect=RuntimeError("Synthetic Audit failure"),
        ),
        pytest.raises(RuntimeError, match="Synthetic Audit failure"),
    ):
        if operation == "RECORD":
            _record(hr_context, employee)
        else:
            values = (
                {}
                if operation == "VOID"
                else {"start_at": START, "end_at": START + timedelta(hours=2)}
            )
            services.revise_attendance(
                hr_context,
                attendance_id=original.attendance.id,
                expected_revision=ordinal,
                request_key=uuid4(),
                operation=operation,
                reason="Synthetic correction",
                **values,
            )
    assert _snapshot(Attendance, AttendanceRevision, AuditEntry) == before


def _draft(context, employee):
    leave_type = services.create_leave_type(context, code="ADV-LEAVE", name="Synthetic Leave")
    return services.create_leave(
        context,
        employee_id=employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2024, 1, 2),
        end_date=date(2024, 1, 3),
        reason="Original synthetic reason",
    )


@pytest.mark.parametrize(
    "operation",
    [
        "CREATE",
        "UPDATE",
        "SUBMIT",
        "APPROVE",
        "REJECT",
        "CANCEL_DRAFT",
        "CANCEL_SUBMITTED",
        "CANCEL_APPROVED",
    ],
)
def test_every_leave_effect_and_audit_roll_back_without_partial_receipts(
    hr_context, approver, employee, operation
):
    draft = _draft(hr_context, employee)
    ordinal = 1
    if operation in {"APPROVE", "REJECT", "CANCEL_SUBMITTED", "CANCEL_APPROVED"}:
        services.submit_leave(
            hr_context, leave_id=draft.leave.id, expected_revision=1, request_key=uuid4()
        )
        ordinal = 2
    if operation == "CANCEL_APPROVED":
        services.decide_leave(
            approver,
            leave_id=draft.leave.id,
            expected_revision=2,
            request_key=uuid4(),
            decision="APPROVED",
        )
        ordinal = 3
    before = _snapshot(LeaveRequest, AuditEntry)
    with (
        patch(
            "businessos.modules.hr.services.leave.audit",
            side_effect=RuntimeError("Synthetic Audit failure"),
        ),
        pytest.raises(RuntimeError, match="Synthetic Audit failure"),
    ):
        if operation == "CREATE":
            services.create_leave(
                hr_context,
                employee_id=employee.id,
                create_request_key=uuid4(),
                leave_type_id=draft.leave.leave_type_id,
                start_date=date(2024, 2, 1),
                end_date=date(2024, 2, 1),
            )
        elif operation == "UPDATE":
            services.update_leave(
                hr_context,
                leave_id=draft.leave.id,
                expected_revision=1,
                leave_type_id=draft.leave.leave_type_id,
                start_date=date(2024, 1, 2),
                end_date=date(2024, 1, 4),
                reason="Changed synthetic reason",
            )
        elif operation == "SUBMIT":
            services.submit_leave(
                hr_context, leave_id=draft.leave.id, expected_revision=1, request_key=uuid4()
            )
        elif operation in {"APPROVE", "REJECT"}:
            services.decide_leave(
                approver,
                leave_id=draft.leave.id,
                expected_revision=ordinal,
                request_key=uuid4(),
                decision="APPROVED" if operation == "APPROVE" else "REJECTED",
                reason="Synthetic decision reason",
            )
        else:
            services.cancel_leave(
                approver,
                leave_id=draft.leave.id,
                expected_revision=ordinal,
                request_key=uuid4(),
                reason="Synthetic cancellation reason",
            )
    assert _snapshot(LeaveRequest, AuditEntry) == before


def test_attendance_effect_filter_is_exact_and_unknown_filters_reject(hr_context, employee):
    voided = _record(hr_context, employee)
    services.revise_attendance(
        hr_context,
        attendance_id=voided.attendance.id,
        expected_revision=1,
        request_key=uuid4(),
        operation="VOID",
        reason="Synthetic void",
    )
    active = _record(hr_context, employee, START + timedelta(hours=2))
    filters = {"start_date": date(2024, 1, 2), "end_date": date(2024, 1, 2)}
    assert [
        row.id for row in selectors.attendance_page(hr_context, status="VOIDED", **filters)
    ] == [voided.attendance.id]
    assert [row.id for row in selectors.attendance_page(hr_context, **filters)] == [
        active.attendance.id
    ]
    with pytest.raises(ValidationError, match="effect"):
        selectors.attendance_page(hr_context, status="UNREVIEWED", **filters)


def test_utc_discovery_cannot_hide_a_revision_with_corrupted_cached_dates(hr_context, employee):
    recorded = _record(hr_context, employee)
    row = AttendanceRevision.objects.get(pk=recorded.receipt.id)
    _raw_update(row, local_start_date=date(2030, 1, 1), local_end_date=date(2030, 1, 1))
    before = AuditEntry.objects.count()
    with pytest.raises(ValidationError, match="retained facts"):
        selectors.attendance_page(
            hr_context, start_date=date(2024, 1, 2), end_date=date(2024, 1, 2)
        )
    assert AuditEntry.objects.count() == before


def test_attendance_latest_count_and_stable_fifty_row_paging_are_sql_scoped(
    hr_context, employee, company
):
    other_party = Party.objects.create(
        company=company, party_type=Party.Type.PERSON, display_name="Another synthetic PERSON"
    )
    another = services.create_employee(
        hr_context,
        party_id=other_party.pk,
        employee_number="ADV-SECOND",
        joining_date=date(2020, 1, 1),
    )
    receipts = [_record(hr_context, employee, START + timedelta(hours=i)) for i in range(50)]
    receipts.append(_record(hr_context, another, START))  # exact start tie must use UUID
    expected = sorted(receipts, key=lambda row: row.attendance.id.int)
    expected.sort(key=lambda row: row.current.start_at, reverse=True)
    with CaptureQueriesContext(connection) as captured:
        first = selectors.attendance_page(
            hr_context, start_date=date(2024, 1, 1), end_date=date(2024, 1, 5), page=1
        )
        second = selectors.attendance_page(
            hr_context, start_date=date(2024, 1, 1), end_date=date(2024, 1, 5), page=2
        )
    assert first.paginator.count == second.paginator.count == 51
    assert len(first.object_list) == 50 and len(second.object_list) == 1
    assert [row.id for row in (*first.object_list, *second.object_list)] == [
        row.attendance.id for row in expected
    ]
    assert isinstance(first.object_list, tuple) and isinstance(first.paginator.object_list, tuple)
    assert any("LIMIT 50" in entry["sql"].upper() for entry in captured)
    assert any("OFFSET 50" in entry["sql"].upper() for entry in captured)
    assert any(
        "COUNT(*)" in entry["sql"].upper() and '"hr_attendance"' in entry["sql"]
        for entry in captured
    )


def test_person_choices_are_minimal_company_scoped_and_independent_from_user_administration(
    hr_context, hr_person, company
):
    Party.objects.create(
        company=company, party_type=Party.Type.PERSON, display_name="Inactive", is_active=False
    )
    Party.objects.create(
        company=company, party_type=Party.Type.ORGANIZATION, display_name="Organization"
    )
    other = Company.objects.create(
        code="ADV-OTHER",
        name="Other synthetic Company",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    Party.objects.create(company=other, party_type=Party.Type.PERSON, display_name="Foreign")
    RolePermission.objects.filter(permission__code="hr.employee.manage").delete()
    with CaptureQueriesContext(connection) as captured:
        choices = selectors.person_choices(hr_context)
    assert [row["id"] for row in choices] == [hr_person.pk]
    assert set(choices.object_list[0]) == {
        "id",
        "company_id",
        "party_type",
        "display_name",
        "is_active",
    }
    assert not any(
        "party_address" in entry["sql"] or "party_contactmethod" in entry["sql"]
        for entry in captured
    )
    with pytest.raises(PermissionDenied):
        selectors.user_association_choices(hr_context)


@pytest.mark.parametrize("surface", ["person", "create_employee", "record_attendance"])
def test_choice_eligibility_is_rechecked_after_real_database_retirement(
    hr_context, hr_person, employee, surface
):
    original = selectors.references

    def retire_before_reference_lock(operation, **kwargs):
        party = Party.objects.get(pk=hr_person.pk)
        party.is_active = False
        party.save(update_fields=["is_active"])
        return original(operation, **kwargs)

    with patch(
        "businessos.modules.hr.selectors.references", side_effect=retire_before_reference_lock
    ):
        with pytest.raises(ValidationError, match="active"):
            if surface == "person":
                selectors.person_choices(hr_context)
            else:
                selectors.action_admission(hr_context, surface)


@pytest.mark.parametrize("corrupt_actor", ["requester", "frozen_beneficiary"])
def test_retained_decision_intrinsic_separation_rejects_corruption(
    hr_context, approver, employee, corrupt_actor
):
    beneficiary = get_user_model().objects.create_user(
        "frozen-beneficiary@example.test", "synthetic"
    )
    UserCompanyAccess.objects.create(user=beneficiary, company_id=hr_context.company_id)
    services.update_employee(
        hr_context, employee_id=employee.id, expected_revision=1, user_id=beneficiary.pk
    )
    draft = _draft(hr_context, employee)
    services.submit_leave(
        hr_context, leave_id=draft.leave.id, expected_revision=1, request_key=uuid4()
    )
    services.decide_leave(
        approver,
        leave_id=draft.leave.id,
        expected_revision=2,
        request_key=uuid4(),
        decision="APPROVED",
    )
    row = LeaveRequest.objects.get(pk=draft.leave.id)
    _raw_update(
        row, decided_by=hr_context.actor_id if corrupt_actor == "requester" else beneficiary.pk
    )
    with pytest.raises(ValidationError, match="separation|provenance|requester|beneficiary"):
        selectors.leave_detail(hr_context, row.pk)


def test_later_current_beneficiary_link_does_not_rewrite_historical_decision(
    hr_context, approver, employee
):
    draft = _draft(hr_context, employee)
    services.submit_leave(
        hr_context, leave_id=draft.leave.id, expected_revision=1, request_key=uuid4()
    )
    decision_key = uuid4()
    services.decide_leave(
        approver,
        leave_id=draft.leave.id,
        expected_revision=2,
        request_key=decision_key,
        decision="APPROVED",
    )
    services.update_employee(
        hr_context, employee_id=employee.id, expected_revision=1, user_id=approver.actor_id
    )
    assert selectors.leave_detail(hr_context, draft.leave.id).decision == "APPROVED"
    with pytest.raises(ValidationError, match="Requester|beneficiary"):
        services.decide_leave(
            approver,
            leave_id=draft.leave.id,
            expected_revision=2,
            request_key=decision_key,
            decision="APPROVED",
        )


@pytest.mark.parametrize("corruption", ["earlier_reason", "interior_gap"])
def test_public_append_cannot_extend_corrupt_complete_history_or_emit_audit(
    hr_context, employee, corruption
):
    original = _record(hr_context, employee)
    parent_id = original.attendance.id
    for expected in (1, 2):
        services.revise_attendance(
            hr_context,
            attendance_id=parent_id,
            expected_revision=expected,
            request_key=uuid4(),
            operation="CORRECT",
            start_at=START,
            end_at=START + timedelta(hours=expected + 1),
            reason="Valid correction",
        )
    earlier = AttendanceRevision.objects.get(attendance_id=parent_id, number=2)
    if corruption == "earlier_reason":
        _raw_update(earlier, reason="\t\u2003")
    else:
        # Fixture-only unrestricted SQL creates a 1,3 chain with a valid latest
        # row; public deletion is itself forbidden by the HR persistence guard.
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM hr_attendancerevision WHERE id=%s",
                [AttendanceRevision._meta.pk.get_db_prep_value(earlier.pk, connection)],
            )
    before = _snapshot(Attendance, AttendanceRevision, AuditEntry)
    with pytest.raises(ValidationError):
        services.revise_attendance(
            hr_context,
            attendance_id=parent_id,
            expected_revision=3,
            request_key=uuid4(),
            operation="CORRECT",
            start_at=START,
            end_at=START + timedelta(hours=4),
            reason="Must not append",
        )
    assert _snapshot(Attendance, AttendanceRevision, AuditEntry) == before
