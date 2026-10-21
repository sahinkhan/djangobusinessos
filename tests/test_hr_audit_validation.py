"""HR1-AUD-004: every public validation error poisons admitted outer work."""

import json
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from time import monotonic
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import OperationalError, connections, transaction

from businessos.core.audit.models import AuditEntry
from businessos.core.database import current_database_alias, database_execution
from businessos.modules.hr import services
from businessos.modules.hr.admission import _CURRENT, ResourceBudgetExceeded, hr_operation
from businessos.modules.hr.manifest import HR_PERMISSION_DECLARATIONS
from businessos.modules.hr.models import (
    Attendance,
    AttendanceRevision,
    Department,
    Employee,
    LeaveRequest,
    LeaveType,
)
from businessos.modules.hr.support import locked, references
from tests import test_hr_services as _setup_fixtures

hr_context = _setup_fixtures.hr_context
hr_person = _setup_fixtures.hr_person

pytestmark = pytest.mark.django_db(transaction=True)
PERMISSIONS = tuple(code for code, _ in HR_PERMISSION_DECLARATIONS)
CASES = (
    "record_employee_uuid",
    "record_request_uuid",
    "record_start_datetime",
    "record_end_datetime",
    "record_reason",
    "revise_request_uuid",
    "revise_expected_revision",
    "revise_reason",
    "revise_operation",
    "revise_void_replacement",
    "revise_start_datetime",
    "revise_end_datetime",
    "revise_attendance_uuid",
    "employee_unknown_field",
)


def _native():
    return tuple(
        tuple(model.objects.order_by("pk").values_list())
        for model in (
            Department,
            Employee,
            Attendance,
            AttendanceRevision,
            LeaveType,
            LeaveRequest,
            AuditEntry,
        )
    )


def _session_settings(connection):
    if connection.vendor != "postgresql":
        return None
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_setting('statement_timeout'), current_setting('lock_timeout'), "
            "current_setting('idle_in_transaction_session_timeout'), "
            "current_setting('transaction_isolation'), pg_catalog.pg_backend_pid()"
        )
        return cursor.fetchone()


def _assert_clean_connection(connection, original_settings):
    assert _CURRENT.get() is None
    assert not connection.in_atomic_block
    assert not connection.needs_rollback
    assert not connection.savepoint_ids
    assert connection.get_autocommit()
    if connection.vendor == "postgresql":
        assert connection.connection.info.transaction_status.name == "IDLE"
    assert _session_settings(connection) == original_settings


def _assert_department_and_audit(context, department):
    # Two necessary native readbacks, before poisoning; no diagnostic SQL loop
    # or queries after a caught failure inside the rollback-only transaction.
    row = Department.objects.get(pk=department.id)
    assert (row.company_id, row.code, row.name, row.revision) == (
        context.company_id,
        department.code,
        department.name,
        1,
    )
    entry = AuditEntry.objects.get(
        company_id=context.company_id,
        actor_id=context.actor_id,
        action="hr.department.created",
        object_type="hr.Department",
        object_id=str(department.id),
    )
    assert entry.metadata == {"revision": 1}


def _invalid_call(context, case):
    start = datetime(2024, 1, 1, tzinfo=UTC)
    if case.startswith("record_"):
        kwargs = {
            "employee_id": uuid4(),
            "request_key": uuid4(),
            "start_at": start,
            "end_at": start + timedelta(hours=1),
            "reason": "Synthetic validation failure",
        }
        key, invalid = {
            "record_employee_uuid": ("employee_id", "not-a-uuid"),
            "record_request_uuid": ("request_key", "not-a-uuid"),
            "record_start_datetime": ("start_at", datetime(2024, 1, 1)),
            "record_end_datetime": ("end_at", "2024-01-01T01:00"),
            "record_reason": ("reason", None),
        }[case]
        kwargs[key] = invalid
        return services.record_attendance(context, **kwargs)
    if case.startswith("revise_"):
        kwargs = {
            "attendance_id": uuid4(),
            "expected_revision": 1,
            "request_key": uuid4(),
            "operation": "CORRECT",
            "start_at": start,
            "end_at": start + timedelta(hours=1),
            "reason": "Synthetic correction",
        }
        key, invalid = {
            "revise_request_uuid": ("request_key", "not-a-uuid"),
            "revise_expected_revision": ("expected_revision", True),
            "revise_reason": ("reason", " "),
            "revise_operation": ("operation", "REWRITE"),
            "revise_void_replacement": ("operation", "VOID"),
            "revise_start_datetime": ("start_at", datetime(2024, 1, 1)),
            "revise_end_datetime": ("end_at", None),
            "revise_attendance_uuid": ("attendance_id", "not-a-uuid"),
        }[case]
        kwargs[key] = invalid
        return services.revise_attendance(context, **kwargs)
    return services.update_employee(
        context, employee_id=uuid4(), expected_revision=1, employee_number="NOT-EDITABLE"
    )


@contextmanager
def _execution(selected, django_db_blocker, monkeypatch):
    if not selected:
        yield
        return
    alias = "hr_audit_validation_selected"
    default = connections["default"]
    config = dict(default.settings_dict)
    config["TEST"] = dict(config.get("TEST", {}))
    connections.databases[alias] = config

    def forbidden_default(*args, **kwargs):
        pytest.fail("Selected-alias HR validation touched the default cursor")

    try:
        with django_db_blocker.unblock(), monkeypatch.context() as patched:
            patched.setattr(default, "cursor", forbidden_default)
            with database_execution(alias):
                yield
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]


@pytest.mark.parametrize("case", CASES)
@pytest.mark.parametrize("selected", [False, True], ids=["default", "selected-alias"])
def test_caught_early_public_validation_rolls_back_prior_effect_and_audit(
    hr_context, django_db_blocker, monkeypatch, case, selected
):
    before = _native()
    with _execution(selected, django_db_blocker, monkeypatch):
        connection = connections[current_database_alias()]
        original_settings = _session_settings(connection)
        prior = inner_error = None
        with pytest.raises(ValidationError) as outer_error:
            with hr_operation(hr_context, PERMISSIONS) as outer:
                outer.authorize()
                prior = services.create_department(
                    hr_context, code="MUST-ROLL-BACK", name="Prior successful nested effect"
                )
                _assert_department_and_audit(hr_context, prior)
                with pytest.raises(ValidationError) as invalid:
                    _invalid_call(hr_context, case)
                inner_error = invalid.value
                if case == "record_employee_uuid":
                    assert set(inner_error.message_dict) == {"employee_id"}
                assert outer.poisoned is inner_error
                assert connection.needs_rollback
                assert transaction.get_rollback(using=connection.alias)
                rollback_only_at_catch = connection.needs_rollback
                # Do not issue SQL in this poisoned outer scope.
        assert prior is not None and inner_error is not None
        assert outer_error.value is inner_error
        assert outer.finished
        _assert_clean_connection(connection, original_settings)
        assert _native() == before
        if selected and case == "record_employee_uuid":
            print(
                "HR1_NORMAL_ORACLE "
                + json.dumps(
                    {
                        "alias": connection.alias,
                        "original_session_settings": original_settings,
                        "prior_department_and_audit_verified": prior is not None,
                        "domain_error_fields": sorted(inner_error.message_dict),
                        "same_inner_outer_error": outer_error.value is inner_error,
                        "rollback_only_at_catch": rollback_only_at_catch,
                        "native_baseline_restored": _native() == before,
                        "finished": outer.finished,
                    }
                )
            )
    assert _native() == before


def test_selected_department_statement_timeout_rolls_back_and_does_not_poison_fresh_request(
    hr_context, django_db_blocker, monkeypatch
):
    """Oracle B: deliberate real 57014, NOT historical root-cause reproduction."""
    if connections["default"].vendor != "postgresql":
        pytest.skip("Real PostgreSQL Department-stage 57014 and session cleanup proof")
    before = _native()
    with _execution(True, django_db_blocker, monkeypatch):
        connection = connections[current_database_alias()]
        original_settings = _session_settings(connection)
        raw_connection = connection.connection
        observed = {}

        def department_timeout(execute, sql, params, many, execution_context):
            if sql.startswith("SELECT pg_catalog.set_config('statement_timeout'"):
                result = execute(sql, params, many, execution_context)
                # The adapter intentionally does not consume this existing
                # configuration result. Observe it without another SQL query.
                observed["settings"] = execution_context["cursor"].fetchone()
                return result
            if (
                'FROM "hr_department" WHERE ("hr_department"."code" = %s' not in sql
                or params[1] != "TIMEOUT-NEXT"
            ):
                return execute(sql, params, many, execution_context)
            assert "sqlstate" not in observed
            assert execution_context["connection"] is connection
            assert _CURRENT.get() is outer
            assert connection.connection is raw_connection
            observed.update(
                alias=connection.alias,
                pid=raw_connection.info.backend_pid,
                transaction=raw_connection.info.transaction_status.name,
                atomic_depth=len(connection.atomic_blocks),
                savepoints=tuple(connection.savepoint_ids),
                remaining=outer.checkpoint(),
            )
            assert outer.authority_started_at == authority_started_at
            started = monotonic()
            try:
                # TEST-ONLY augmentation of the real duplicate-code EXISTS.
                # Existing production remaining-budget settings cancel the
                # deliberate 3s work; no timeout or HR clock is modified.
                return execute(
                    f"SELECT ({sql}) AS hr_test_exists, pg_catalog.pg_sleep(3)",
                    params,
                    many,
                    execution_context,
                )
            except OperationalError as error:
                observed["sqlstate"] = error.__cause__.sqlstate
                observed["diagnostic"] = error.__cause__.diag.message_primary
                raise
            finally:
                observed["duration"] = monotonic() - started

        with pytest.raises(ResourceBudgetExceeded) as classified:
            with hr_operation(hr_context, PERMISSIONS) as outer:
                outer.authorize()
                authority_started_at = outer.authority_started_at
                prior = services.create_department(
                    hr_context, code="TIMEOUT-PRIOR", name="Prior synthetic effect"
                )
                _assert_department_and_audit(hr_context, prior)
                with connection.execute_wrapper(department_timeout):
                    with pytest.raises(OperationalError) as database_error:
                        services.create_department(
                            hr_context, code="TIMEOUT-NEXT", name="Injected negative control"
                        )
                assert observed["sqlstate"] == "57014"
                assert database_error.value.__cause__.sqlstate == "57014"
                assert "statement timeout" in observed["diagnostic"]
                assert outer.poisoned is database_error.value
                assert transaction.get_rollback(using=connection.alias)
                assert connection.needs_rollback
                observed["rollback_only_at_catch"] = connection.needs_rollback
                # No attempted SQL or savepoint recovery after catching 57014.
        assert classified.value.__cause__ is database_error.value
        assert outer.finished
        assert observed["alias"] == "hr_audit_validation_selected"
        assert observed["pid"] == original_settings[-1]
        assert observed["transaction"] == "INTRANS"
        assert observed["atomic_depth"] == 1 and observed["savepoints"] == ()
        assert 0 < observed["remaining"] <= 2
        assert observed["settings"][0] == observed["settings"][1]
        _assert_clean_connection(connection, original_settings)
        assert _native() == before
        observed["native_baseline_restored"] = True
        observed["original_session_settings"] = original_settings

        # Independent request, same selected session, injection removed: real
        # service/persistence/Audit prove the preceding timeout did not leak.
        fresh = services.create_department(
            hr_context, code="TIMEOUT-FRESH", name="Fresh synthetic request"
        )
        assert connection.connection is raw_connection
        _assert_department_and_audit(hr_context, fresh)
        after = _native()
        assert after[1:6] == before[1:6]
        assert len(after[0]) == len(before[0]) + 1
        assert len(after[6]) == len(before[6]) + 1
        _assert_clean_connection(connection, original_settings)
        observed["fresh_request_same_session"] = connection.connection is raw_connection
        observed["classified"] = type(classified.value).__name__
        print("HR1_CONTROLLED_57014 " + json.dumps(observed))


@pytest.mark.parametrize("case", CASES)
def test_direct_invalid_public_call_has_no_effect_or_receipt(hr_context, case):
    before = _native()
    with pytest.raises(ValidationError):
        _invalid_call(hr_context, case)
    assert _native() == before


@pytest.mark.parametrize("case", ["record_request_uuid", "revise_operation"])
def test_caught_attendance_validation_rolls_back_combined_leave_and_department_work(
    hr_context, hr_person, case
):
    employee = services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="COMBINED",
        joining_date=date(2020, 1, 1),
    )
    leave_type = services.create_leave_type(hr_context, code="COMBINED", name="Synthetic")
    before = _native()
    with pytest.raises(ValidationError):
        with hr_operation(hr_context, PERMISSIONS) as outer:
            locked(Employee, hr_context, employee.id)
            references(outer, party_ids=[hr_person.pk], leave_type_ids=[leave_type.id])
            outer.authorize()
            services.create_department(hr_context, code="PRIOR", name="Must roll back")
            services.create_leave(
                hr_context,
                employee_id=employee.id,
                create_request_key=uuid4(),
                leave_type_id=leave_type.id,
                start_date=date(2024, 2, 1),
                end_date=date(2024, 2, 2),
                reason="Prior nested Leave effect",
            )
            with pytest.raises(ValidationError):
                _invalid_call(hr_context, case)
    assert _native() == before
