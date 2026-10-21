"""HR schema/private-persistence tests, not service authorization evidence."""

import importlib
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, connection, models

from businessos.core.access.models import UserCompanyAccess, UserRoleAssignment
from businessos.core.common.context import BusinessContext
from businessos.core.database import business_atomic_context
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Branch
from businessos.modules.hr import persistence, services
from businessos.modules.hr.admission import hr_operation
from businessos.modules.hr.manifest import HR_PERMISSION_DECLARATIONS, MODULE
from businessos.modules.hr.models import (
    MAX_ORDINAL,
    Attendance,
    AttendanceRevision,
    Department,
    Employee,
    HRQuerySet,
    LeaveRequest,
    LeaveType,
)
from businessos.modules.party.models import Party
from tests import test_hr_services as _setup

hr_context = _setup.hr_context

HR_MODELS = (Department, Employee, Attendance, AttendanceRevision, LeaveType, LeaveRequest)


@contextmanager
def _owner(context, *rows, user_ids=(), attendance_id=None):
    """Private tests use the same real prelocked owner boundary as services."""
    selected = {
        model: set()
        for model in (Employee, Department, Branch, Party, LeaveType, Attendance, LeaveRequest)
    }
    for row in rows:
        selected[type(row)].add(row.pk)
        if isinstance(row, Employee):
            selected[Party].add(row.party_id)
            for model, key in ((Department, row.department_id), (Branch, row.branch_id)):
                if key is not None:
                    selected[model].add(key)
    with hr_operation(context, [code for code, _ in HR_PERMISSION_DECLARATIONS]) as op:
        for model, identities in selected.items():
            if identities:
                op.lock_rows(model, identities)
        if attendance_id is not None:
            op.reserve_attendance(attendance_id)
        op.authorize(user_ids=user_ids)
        yield op


@pytest.fixture
def hr_employee(company, hr_context):
    party = Party.objects.create(
        company=company, party_type=Party.Type.PERSON, display_name="HR Person"
    )
    row = services.create_employee(
        hr_context, party_id=party.pk, employee_number=" person-1 ", joining_date=date(2020, 1, 1)
    )
    return Employee.objects.get(pk=row.id)


@pytest.fixture
def hr_type(company, hr_context):
    row = services.create_leave_type(hr_context, code=" annual ", name="Annual")
    return LeaveType.objects.get(pk=row.id)


@pytest.mark.django_db
@pytest.mark.parametrize("model", HR_MODELS)
@pytest.mark.parametrize("manager_name", ["objects", "_base_manager", "_default_manager"])
@pytest.mark.parametrize(
    "operation",
    [
        "create",
        "update",
        "delete",
        "bulk_create",
        "bulk_update",
        "get_or_create",
        "update_or_create",
    ],
)
def test_all_public_hr_manager_mutations_reject(model, manager_name, operation):
    manager = getattr(model, manager_name)
    assert isinstance(manager.all(), HRQuerySet)
    with pytest.raises(ValidationError):
        if operation == "bulk_create":
            manager.bulk_create([model()], ignore_conflicts=True)
        elif operation == "bulk_update":
            manager.bulk_update([model()], ["company"])
        elif operation == "update":
            manager.filter(pk=uuid4()).update(company_id=uuid4())
        else:
            getattr(manager, operation)()


@pytest.mark.parametrize("model", HR_MODELS)
@pytest.mark.parametrize(
    "operation,options",
    [
        ("save", {}),
        ("save", {"force_insert": True}),
        ("save", {"force_update": True}),
        ("save", {"update_fields": ["company"]}),
        ("save_base", {}),
        ("save_base", {"raw": True}),
        ("save_base", {"force_insert": True}),
        ("save_base", {"force_update": True}),
        ("save_base", {"update_fields": ["company"]}),
        ("delete", {}),
        ("delete", {"using": "unconfigured_alias", "keep_parents": True}),
    ],
)
def test_all_public_hr_instance_writes_reject(model, operation, options):
    # No database marker: every supported calling variant must reject before SQL,
    # including raw fixture writes and callers supplying a different alias.
    with pytest.raises(ValidationError):
        getattr(model(), operation)(**options)


@pytest.mark.parametrize("model", HR_MODELS)
@pytest.mark.parametrize("manager_name", ["objects", "_base_manager", "_default_manager"])
@pytest.mark.parametrize(
    "options",
    [
        {},
        {"ignore_conflicts": True},
        {"update_conflicts": True, "update_fields": ["company"], "unique_fields": ["id"]},
        {"ignore_conflicts": True, "update_conflicts": True},
    ],
)
def test_public_bulk_creation_and_upsert_variants_reject_before_sql(model, manager_name, options):
    with pytest.raises(ValidationError):
        getattr(model, manager_name).bulk_create([model()], **options)


def test_exact_schema_and_fk_protection():
    expected = {
        Department: {"company", "code", "name", "is_active", "revision"},
        LeaveType: {"company", "code", "name", "is_active", "revision"},
        Employee: {
            "company",
            "party",
            "employee_number",
            "user",
            "department",
            "branch",
            "status",
            "joining_date",
            "leaving_date",
            "revision",
        },
        Attendance: {
            "company",
            "employee",
            "branch",
            "timezone",
            "record_request_key",
            "recorded_by",
        },
        AttendanceRevision: {
            "company",
            "employee",
            "attendance",
            "number",
            "expected_revision",
            "operation",
            "effect",
            "start_at",
            "end_at",
            "local_start_date",
            "local_end_date",
            "reason",
            "actor",
            "request_key",
        },
        LeaveRequest: {
            "company",
            "employee",
            "branch",
            "timezone",
            "create_request_key",
            "requester",
            "leave_type",
            "start_date",
            "end_date",
            "reason",
            "window_start_at",
            "window_end_at",
            "status",
            "revision",
            "submit_key",
            "submitted_by",
            "submitted_at",
            "submit_from_revision",
            "submit_revision",
            "beneficiary_user_at_submission",
            "decision_key",
            "decided_by",
            "decided_at",
            "decision_from_revision",
            "decision_revision",
            "decision",
            "decision_reason",
            "cancel_key",
            "cancelled_by",
            "cancelled_at",
            "cancel_from_revision",
            "cancel_revision",
            "cancel_reason",
        },
    }
    for model, fields in expected.items():
        assert {field.name for field in model._meta.local_fields} == fields | {
            "id",
            "created_at",
            "updated_at",
        }
        for field in model._meta.local_fields:
            if isinstance(field, models.ForeignKey):
                assert field.remote_field.on_delete is models.PROTECT


@pytest.mark.django_db
def test_manifest_has_exact_twelve_frozen_permissions_and_starts_disabled():
    assert MODULE["code"] == "hr"
    assert MODULE["depends"] == ["party", "organization", "reference", "access"]
    assert len(HR_PERMISSION_DECLARATIONS) == 12
    assert set(MODULE["permissions"]) == {
        "hr.employee.view",
        "hr.employee.manage",
        "hr.department.view",
        "hr.department.manage",
        "hr.attendance.view",
        "hr.attendance.record",
        "hr.attendance.correct",
        "hr.leave.view",
        "hr.leave.request",
        "hr.leave.approve",
        "hr.leave.cancel",
        "hr.leave_type.manage",
    }
    assert BusinessModule.objects.get(code="hr").is_enabled is False
    migration = importlib.import_module("businessos.modules.hr.migrations.0002_register_manifest")
    assert migration.PERMISSIONS == HR_PERMISSION_DECLARATIONS


@pytest.mark.django_db
def test_manifest_reregistration_preserves_enablement_and_retirement():
    from django.db.migrations.executor import MigrationExecutor

    from businessos.core.access.models import Permission

    module = BusinessModule.objects.get(code="hr")
    module.is_enabled = True
    module.save()
    permission = Permission.objects.get(code="hr.employee.view")
    permission.is_active = False
    permission.save()
    migration = importlib.import_module("businessos.modules.hr.migrations.0002_register_manifest")
    historical = MigrationExecutor(connection).loader.project_state().apps
    migration.register_hr(historical, SimpleNamespace(connection=connection))
    module.refresh_from_db()
    permission.refresh_from_db()
    assert module.is_enabled is True
    assert permission.is_active is False


@pytest.mark.django_db(transaction=True)
def test_setup_normalization_revision_noop_and_retirement(company, hr_context, hr_employee):
    with _owner(hr_context):
        department = persistence._create_department(
            company_id=company.pk, code=" eng-1 ", name=" Engineering "
        )
        assert (department.code, department.name, department.revision) == (
            "ENG-1",
            "Engineering",
            1,
        )
    with _owner(hr_context, department):
        unchanged = persistence._update_department(
            company_id=company.pk,
            department_id=department.pk,
            expected_revision=1,
            name="Engineering",
            is_active=True,
        )
        assert unchanged.revision == 1
    with _owner(hr_context, department):
        changed = persistence._update_department(
            company_id=company.pk,
            department_id=department.pk,
            expected_revision=1,
            name="Engineering Operations",
            is_active=True,
        )
        assert changed.revision == 2
    with _owner(hr_context, hr_employee, department):
        persistence._update_employee(
            company_id=company.pk,
            employee_id=hr_employee.pk,
            expected_revision=1,
            joining_date=hr_employee.joining_date,
            user_id=None,
            department_id=department.pk,
            leaving_date=None,
        )
    with pytest.raises(ValidationError, match="Reassign"), _owner(hr_context, department):
        persistence._update_department(
            company_id=company.pk,
            department_id=department.pk,
            expected_revision=2,
            name=changed.name,
            is_active=False,
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("bad", [True, 1.0, "1", 0, MAX_ORDINAL + 1])
def test_private_setup_rejects_coerced_or_out_of_range_revision(company, hr_context, bad):
    with _owner(hr_context):
        department = persistence._create_department(company_id=company.pk, code="TEST", name="Test")
    with pytest.raises(ValidationError), _owner(hr_context, department):
        persistence._update_department(
            company_id=company.pk,
            department_id=department.pk,
            expected_revision=bad,
            name="Other",
            is_active=True,
        )
    department.refresh_from_db()
    assert department.revision == 1


@pytest.mark.django_db(transaction=True)
def test_employee_immutable_identity_end_and_stale_instance_guards(
    company, hr_context, hr_employee
):
    original = (hr_employee.company_id, hr_employee.party_id, hr_employee.employee_number)
    with _owner(hr_context, hr_employee):
        ended = persistence._end_employee(
            company_id=company.pk,
            employee_id=hr_employee.pk,
            expected_revision=1,
            leaving_date=date(2024, 1, 1),
        )
        assert ended.status == Employee.Status.ENDED
        assert ended.revision == 2
        assert (ended.company_id, ended.party_id, ended.employee_number) == original
    with pytest.raises(ValidationError), _owner(hr_context, ended):
        persistence._end_employee(
            company_id=company.pk,
            employee_id=ended.pk,
            expected_revision=1,
            leaving_date=date(2024, 1, 1),
        )
    hr_employee.company_id = uuid4()
    hr_employee.party_id = uuid4()
    with pytest.raises(ValidationError):
        hr_employee.save(update_fields=["status"])
    with pytest.raises(ValidationError):
        hr_employee.delete()
    assert Employee.objects.get(pk=hr_employee.pk).status == Employee.Status.ENDED


@pytest.mark.django_db(transaction=True)
def test_employee_unchanged_user_not_in_update_columns(company, operator, hr_context, hr_employee):
    from django.test.utils import CaptureQueriesContext

    with _owner(hr_context, hr_employee, user_ids=[operator.pk]):
        linked = persistence._update_employee(
            company_id=company.pk,
            employee_id=hr_employee.pk,
            expected_revision=1,
            joining_date=hr_employee.joining_date,
            user_id=operator.pk,
            department_id=None,
            leaving_date=None,
        )
    with _owner(hr_context, linked), CaptureQueriesContext(connection) as queries:
        persistence._update_employee(
            company_id=company.pk,
            employee_id=linked.pk,
            expected_revision=2,
            joining_date=date(2019, 1, 1),
            user_id=operator.pk,
            department_id=None,
            leaving_date=None,
        )
    updates = [entry["sql"] for entry in queries if entry["sql"].startswith("UPDATE ")]
    assert len(updates) == 1
    assert '"user_id" =' not in updates[0]
    assert '"party_id" =' not in updates[0]


@pytest.mark.django_db(transaction=True)
def test_attendance_initial_revision_has_no_duration_ceiling(
    company, operator, hr_context, hr_employee
):
    start = datetime(2023, 1, 1, 10, 0, 45, 123456, tzinfo=UTC)
    end = start + timedelta(hours=73)
    attendance_id = uuid4()
    with _owner(hr_context, hr_employee, attendance_id=attendance_id):
        attendance = persistence._create_attendance(
            company_id=company.pk,
            employee_id=hr_employee.pk,
            branch_id=None,
            timezone_name=company.timezone,
            record_request_key=uuid4(),
            recorded_by_id=operator.pk,
            attendance_id=attendance_id,
        )
        revision = persistence._append_attendance_revision(
            company_id=company.pk,
            attendance_id=attendance.pk,
            expected_revision=0,
            operation="RECORD",
            start_at=start,
            end_at=end,
            local_start_date=start.date(),
            local_end_date=(end - timedelta(microseconds=1)).date(),
            reason="",
            actor_id=operator.pk,
            request_key=attendance.record_request_key,
        )
    assert revision.end_at - revision.start_at == timedelta(hours=73)
    assert revision.start_at.microsecond == 123456
    assert revision.number == 1
    assert revision.effect == "ACTIVE_INTERVAL"


@pytest.mark.django_db(transaction=True)
def test_leave_private_transitions_retain_receipts(
    company, operator, hr_context, hr_employee, hr_type
):
    from django.contrib.auth import get_user_model

    decider = get_user_model().objects.create_user("hr-decider@example.com", "password")
    UserCompanyAccess.objects.create(company=company, user=decider)
    assignment = UserRoleAssignment.objects.get(user=operator, company=company)
    UserRoleAssignment.objects.create(company=company, user=decider, role_id=assignment.role_id)
    decider_context = BusinessContext(actor_id=decider.pk, company_id=company.pk)
    with _owner(hr_context, hr_employee, hr_type):
        leave = persistence._create_leave(
            company_id=company.pk,
            employee_id=hr_employee.pk,
            branch_id=None,
            timezone_name=company.timezone,
            create_request_key=uuid4(),
            requester_id=operator.pk,
            leave_type_id=hr_type.pk,
            start_date=date(2023, 1, 1),
            end_date=date(2024, 1, 2),
            window_start_at=datetime(2023, 1, 1, tzinfo=UTC),
            window_end_at=datetime(2024, 1, 3, tzinfo=UTC),
        )
    with _owner(hr_context, hr_employee, hr_type, leave):
        submitted = persistence._submit_leave(
            company_id=company.pk,
            leave_id=leave.pk,
            expected_revision=1,
            request_key=uuid4(),
            actor_id=operator.pk,
        )
    with pytest.raises(ValidationError), _owner(hr_context, hr_employee, hr_type, submitted):
        persistence._decide_leave(
            company_id=company.pk,
            leave_id=leave.pk,
            expected_revision=2,
            request_key=uuid4(),
            actor_id=operator.pk,
            decision="APPROVED",
        )
    with _owner(decider_context, hr_employee, hr_type, submitted):
        approved = persistence._decide_leave(
            company_id=company.pk,
            leave_id=leave.pk,
            expected_revision=2,
            request_key=uuid4(),
            actor_id=decider.pk,
            decision="APPROVED",
        )
    with _owner(hr_context, hr_employee, hr_type, approved):
        cancelled = persistence._cancel_leave(
            company_id=company.pk,
            leave_id=leave.pk,
            expected_revision=3,
            request_key=uuid4(),
            actor_id=operator.pk,
            reason="Changed plans",
        )
    assert cancelled.revision == 4
    assert cancelled.submit_key == submitted.submit_key
    assert cancelled.decision_key == approved.decision_key
    assert cancelled.decision == "APPROVED"
    assert cancelled.cancel_from_revision == 3
    assert cancelled.status == "CANCELLED"
    assert (cancelled.end_date - cancelled.start_date).days + 1 > 366


@pytest.mark.django_db(transaction=True)
def test_private_leave_rejects_forged_derived_window(
    company, operator, hr_context, hr_employee, hr_type
):
    with (
        pytest.raises(ValidationError, match="exact frozen-zone"),
        _owner(hr_context, hr_employee, hr_type),
    ):
        persistence._create_leave(
            company_id=company.pk,
            employee_id=hr_employee.pk,
            branch_id=None,
            timezone_name=company.timezone,
            create_request_key=uuid4(),
            requester_id=operator.pk,
            leave_type_id=hr_type.pk,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 2),
            window_start_at=datetime(2023, 1, 1, 1, tzinfo=UTC),
            window_end_at=datetime(2023, 1, 3, tzinfo=UTC),
        )
    assert not LeaveRequest.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_private_leave_rejects_interior_skipped_midnight(
    company, operator, hr_context, hr_employee, hr_type
):
    company.timezone = "Pacific/Apia"
    company.save()
    with pytest.raises(ValidationError, match="midnight"), _owner(hr_context, hr_employee, hr_type):
        persistence._create_leave(
            company_id=company.pk,
            employee_id=hr_employee.pk,
            branch_id=None,
            timezone_name=company.timezone,
            create_request_key=uuid4(),
            requester_id=operator.pk,
            leave_type_id=hr_type.pk,
            start_date=date(2011, 12, 29),
            end_date=date(2012, 1, 1),
            window_start_at=datetime(2011, 12, 29, 10, tzinfo=UTC),
            window_end_at=datetime(2012, 1, 1, 10, tzinfo=UTC),
        )
    assert not LeaveRequest.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_private_attendance_rejects_false_cached_dates(company, operator, hr_context, hr_employee):
    attendance_id = uuid4()
    with (
        pytest.raises(ValidationError, match="search dates"),
        _owner(hr_context, hr_employee, attendance_id=attendance_id),
    ):
        attendance = persistence._create_attendance(
            company_id=company.pk,
            employee_id=hr_employee.pk,
            branch_id=None,
            timezone_name=company.timezone,
            record_request_key=uuid4(),
            recorded_by_id=operator.pk,
            attendance_id=attendance_id,
        )
        persistence._append_attendance_revision(
            company_id=company.pk,
            attendance_id=attendance.pk,
            expected_revision=0,
            operation="RECORD",
            start_at=datetime(2023, 1, 1, tzinfo=UTC),
            end_at=datetime(2023, 1, 2, tzinfo=UTC),
            local_start_date=date(2023, 1, 1),
            local_end_date=date(2023, 1, 2),
            reason="",
            actor_id=operator.pk,
            request_key=attendance.record_request_key,
        )
    assert not AttendanceRevision.objects.exists()
    assert not Attendance.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_ordinal_exhaustion_has_no_partial_change(company, hr_context):
    with _owner(hr_context):
        department = persistence._create_department(company_id=company.pk, code="MAX", name="Max")
    with business_atomic_context():
        with connection.cursor() as cursor:
            cursor.execute(
                'UPDATE "hr_department" SET "revision" = %s WHERE "id" = %s',
                [
                    MAX_ORDINAL,
                    department.pk.hex if connection.vendor == "sqlite" else department.pk,
                ],
            )
    with pytest.raises(ValidationError), _owner(hr_context, department):
        persistence._update_department(
            company_id=company.pk,
            department_id=department.pk,
            expected_revision=MAX_ORDINAL,
            name="Changed",
            is_active=True,
        )
    department.refresh_from_db()
    assert (department.name, department.revision) == ("Max", MAX_ORDINAL)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,changes", [(Department, {"revision": 0}), (LeaveType, {"revision": MAX_ORDINAL + 1})]
)
def test_portable_setup_ordinal_checks_reject_raw_invalid_insert(company, model, changes):
    row = model(company=company, code="RAW", name="Raw", **changes)
    with pytest.raises((IntegrityError, DataError)) as caught, business_atomic_context():
        # Deliberate unsupported base-method write tests the DB CHECK, not a public HR API.
        models.Model.save_base(row, using=connection.alias, force_insert=True)
    if connection.vendor == "postgresql":
        # int4 rejects MAX+1 before evaluating CHECK; zero reaches the portable
        # lower-bound CHECK. Neither result permits omitting the explicit bounds.
        code = getattr(caught.value.__cause__, "sqlstate", None)
        assert code == ("22003" if changes["revision"] > MAX_ORDINAL else "23514")
    constraint = "hr_department_rev" if model is Department else "hr_leave_type_rev"
    with connection.cursor() as cursor:
        facts = connection.introspection.get_constraints(cursor, model._meta.db_table)
        assert facts[constraint]["check"] is True
        if connection.vendor == "postgresql":
            cursor.execute(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid = %s::regclass AND conname = %s",
                [model._meta.db_table, constraint],
            )
        else:
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = %s",
                [model._meta.db_table],
            )
        definition = "".join(cursor.fetchone()[0].replace('"', "").split())
    assert "revision>=1" in definition
    assert "revision<=2147483647" in definition


def test_all_six_models_are_registered():
    assert {model.__name__ for model in apps.get_app_config("hr").get_models()} == {
        "Department",
        "Employee",
        "Attendance",
        "AttendanceRevision",
        "LeaveType",
        "LeaveRequest",
    }
