"""HR1-AUD-002: private primitives cannot rewrite owner identity or receipts."""

from datetime import date
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError

from businessos.core.audit.models import AuditEntry
from businessos.core.database import business_atomic_context
from businessos.core.organization.models import Company
from businessos.modules.hr import persistence, services
from businessos.modules.hr.models import Attendance, Department, Employee, LeaveRequest
from businessos.modules.party.models import Party
from tests import test_hr_services as _setup
from tests.test_hr_models import _owner

hr_context = _setup.hr_context
hr_person = _setup.hr_person
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def employee(hr_context, hr_person):
    return services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="AUDIT-EMPLOYEE",
        joining_date=date(2020, 1, 1),
    )


def _other_company(company):
    return Company.objects.create(
        code="OTHER-AUDIT",
        name="Other synthetic company",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )


@pytest.mark.parametrize("change", ["number", "party", "company"])
def test_generic_employee_write_cannot_reassign_persisted_identity(
    hr_context, employee, company, change
):
    row = Employee.objects.get(pk=employee.id)
    before = tuple(Employee.objects.filter(pk=row.pk).values().get().items())
    audits = AuditEntry.objects.count()
    if change == "number":
        row.employee_number = "REWRITTEN"
        fields = ["employee_number"]
    else:
        owner = _other_company(company) if change == "company" else company
        party = Party.objects.create(
            company=owner, party_type=Party.Type.PERSON, display_name="Other synthetic person"
        )
        row.party_id = party.pk
        fields = ["party_id"]
        if change == "company":
            row.company_id = owner.pk
            fields.append("company_id")
    with pytest.raises(ValidationError):
        with business_atomic_context():
            persistence._write_changed(row, fields)
    assert tuple(Employee.objects.filter(pk=employee.id).values().get().items()) == before
    assert AuditEntry.objects.count() == audits


def test_generic_setup_write_cannot_repurpose_retired_code(hr_context):
    created = services.create_department(hr_context, code="ORIGINAL", name="Original")
    services.update_department(
        hr_context, department_id=created.id, expected_revision=1, name="Retired", is_active=False
    )
    row = Department.objects.get(pk=created.id)
    row.code = "REUSED"
    audits = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        with business_atomic_context():
            persistence._write_changed(row, ["code"])
    row.refresh_from_db()
    assert row.code == "ORIGINAL" and row.revision == 2 and row.is_active is False
    assert AuditEntry.objects.count() == audits


def test_generic_submitted_leave_write_cannot_replace_frozen_content_or_receipt(
    hr_context, employee
):
    leave_type = services.create_leave_type(hr_context, code="ANNUAL", name="Annual")
    leave = services.create_leave(
        hr_context,
        employee_id=employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 2),
        reason="Original reason",
    )
    services.submit_leave(
        hr_context, leave_id=leave.leave.id, expected_revision=1, request_key=uuid4()
    )
    row = LeaveRequest.objects.get(pk=leave.leave.id)
    before = dict(LeaveRequest.objects.filter(pk=row.pk).values().get())
    audits = AuditEntry.objects.count()
    row.reason = "Rewritten submitted content"
    row.submit_key = uuid4()
    row.submit_from_revision = 2
    row.submit_revision = 3
    with pytest.raises(ValidationError):
        with business_atomic_context():
            persistence._write_changed(
                row, ["reason", "submit_key", "submit_from_revision", "submit_revision"]
            )
    assert LeaveRequest.objects.filter(pk=row.pk).values().get() == before
    assert AuditEntry.objects.count() == audits


def test_generic_insert_cannot_create_cross_company_attendance_without_revision_one(
    hr_context, employee, company
):
    other = _other_company(company)
    row = Attendance(
        company=other,
        employee_id=employee.id,
        timezone="UTC",
        record_request_key=uuid4(),
        recorded_by_id=hr_context.actor_id,
    )
    audits = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        with business_atomic_context():
            persistence._insert(row)
    assert not Attendance.objects.filter(pk=row.pk).exists()
    assert AuditEntry.objects.count() == audits


@pytest.mark.parametrize("include_column", [False, True])
def test_named_employee_edit_rejects_extra_immutable_identity_even_if_omitted(
    hr_context, employee, monkeypatch, include_column
):
    original = persistence._write_changed
    before = Employee.objects.filter(pk=employee.id).values().get()
    audits = AuditEntry.objects.count()

    def inject(row, fields):
        row.employee_number = "SUBSTITUTED"
        return original(row, [*fields, "employee_number"] if include_column else fields)

    monkeypatch.setattr(persistence, "_write_changed", inject)
    with pytest.raises(ValidationError):
        services.update_employee(
            hr_context, employee_id=employee.id, expected_revision=1, joining_date=date(2019, 1, 1)
        )
    assert Employee.objects.filter(pk=employee.id).values().get() == before
    assert AuditEntry.objects.count() == audits


def test_named_setup_write_rechecks_persisted_revision_before_save(hr_context, monkeypatch):
    created = services.create_department(hr_context, code="STALE", name="Original")
    services.update_department(
        hr_context, department_id=created.id, expected_revision=1, name="Current", is_active=True
    )
    original = persistence._write_changed
    audits = AuditEntry.objects.count()

    def inject_stale(row, fields):
        row.revision = 1
        return original(row, fields)

    monkeypatch.setattr(persistence, "_write_changed", inject_stale)
    with pytest.raises(ValidationError, match="revision"):
        services.update_department(
            hr_context, department_id=created.id, expected_revision=2, name="Stale", is_active=True
        )
    current = Department.objects.get(pk=created.id)
    assert (current.name, current.revision) == ("Current", 2)
    assert AuditEntry.objects.count() == audits


@pytest.mark.parametrize(
    "field", ["reason", "submit_key", "submitted_by_id", "beneficiary_user_at_submission_id"]
)
def test_legitimate_cancel_cannot_alter_retained_submit_evidence(
    hr_context, employee, monkeypatch, field
):
    leave_type = services.create_leave_type(hr_context, code="FROZEN", name="Frozen")
    leave = services.create_leave(
        hr_context,
        employee_id=employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 2),
        reason="Frozen content",
    )
    services.submit_leave(
        hr_context, leave_id=leave.leave.id, expected_revision=1, request_key=uuid4()
    )
    before = LeaveRequest.objects.filter(pk=leave.leave.id).values().get()
    audits = AuditEntry.objects.count()
    original = persistence._write_changed

    def inject(row, fields):
        setattr(row, field, "Rewritten" if field == "reason" else uuid4())
        return original(row, fields)

    monkeypatch.setattr(persistence, "_write_changed", inject)
    with pytest.raises(ValidationError):
        services.cancel_leave(
            hr_context,
            leave_id=leave.leave.id,
            expected_revision=2,
            request_key=uuid4(),
            reason="Legitimate cancellation",
        )
    assert LeaveRequest.objects.filter(pk=leave.leave.id).values().get() == before
    assert AuditEntry.objects.count() == audits


def test_generic_write_stays_closed_inside_a_valid_admitted_operation(hr_context, employee):
    row = Employee.objects.get(pk=employee.id)
    row.joining_date = date(2019, 1, 1)
    with pytest.raises(ValidationError), _owner(hr_context, Employee.objects.get(pk=row.pk)):
        persistence._write_changed(row, ["joining_date"])
    assert Employee.objects.get(pk=row.pk).joining_date == employee.joining_date


def test_named_primitive_refuses_missing_authority(hr_context):
    from businessos.modules.hr.admission import hr_operation

    with (
        pytest.raises(ValidationError),
        hr_operation(hr_context, ["hr.department.manage", "hr.department.view"]),
    ):
        persistence._create_department(
            company_id=hr_context.company_id, code="NOAUTH", name="No authority"
        )
    assert not Department.objects.exists()


def test_initial_attendance_parent_cannot_commit_without_revision_one(hr_context, employee):
    from businessos.modules.hr.admission import AdmissionError

    parent_id = uuid4()
    audits = AuditEntry.objects.count()
    with (
        pytest.raises((AdmissionError, ValidationError)),
        _owner(hr_context, Employee.objects.get(pk=employee.id), attendance_id=parent_id),
    ):
        persistence._create_attendance(
            company_id=hr_context.company_id,
            employee_id=employee.id,
            branch_id=None,
            timezone_name="UTC",
            record_request_key=uuid4(),
            recorded_by_id=hr_context.actor_id,
            attendance_id=parent_id,
        )
    assert not Attendance.objects.filter(pk=parent_id).exists()
    assert AuditEntry.objects.count() == audits
