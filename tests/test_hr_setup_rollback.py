"""Setup/Employee native effects and their owner-local Audit are one unit."""

from datetime import date
from unittest.mock import patch

import pytest

from businessos.core.audit.models import AuditEntry
from businessos.core.database import current_database_alias
from businessos.modules.hr import services
from businessos.modules.hr.models import (
    Attendance,
    AttendanceRevision,
    Department,
    Employee,
    LeaveRequest,
    LeaveType,
)
from tests import test_hr_services as _fixtures

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)


def _native():
    alias = current_database_alias()
    return tuple(
        tuple(model.objects.using(alias).order_by("pk").values())
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


@pytest.mark.parametrize(
    "operation",
    [
        "employee_create",
        "employee_update",
        "employee_end",
        "employee_transfer",
        "leave_type_create",
        "leave_type_update",
    ],
)
def test_each_setup_and_employee_effect_rolls_back_when_its_audit_fails(
    hr_context, hr_person, branch, operation
):
    alias = current_database_alias()
    employee = None
    leave_type = None
    if operation in {"employee_update", "employee_end", "employee_transfer"}:
        employee = services.create_employee(
            hr_context,
            party_id=hr_person.pk,
            employee_number="ROLLBACK",
            joining_date=date(2020, 1, 1),
        )
    if operation == "leave_type_update":
        leave_type = services.create_leave_type(hr_context, code="RB", name="Original leave type")
    before = _native()

    def fail_after_native_effect(context, row, action, **metadata):
        assert context == hr_context
        assert _native() != before, "Audit failure must follow the actual native business effect"
        if operation == "employee_create":
            persisted = Employee.objects.using(alias).get(pk=row.pk)
            assert persisted.employee_number == "ROLLBACK" and persisted.revision == 1
            assert action == "hr.employee.created"
        elif operation == "employee_update":
            persisted = Employee.objects.using(alias).get(pk=employee.id)
            assert persisted.joining_date == date(2019, 1, 1) and persisted.revision == 2
            assert action == "hr.employee.updated"
        elif operation == "employee_end":
            persisted = Employee.objects.using(alias).get(pk=employee.id)
            assert persisted.status == "ENDED" and persisted.leaving_date == date(2024, 1, 1)
            assert persisted.revision == 2 and action == "hr.employee.ended"
        elif operation == "employee_transfer":
            persisted = Employee.objects.using(alias).get(pk=employee.id)
            assert persisted.branch_id == branch.pk and persisted.revision == 2
            assert action == "hr.employee.branch_changed"
        elif operation == "leave_type_create":
            persisted = LeaveType.objects.using(alias).get(pk=row.pk)
            assert persisted.code == "RB" and persisted.revision == 1
            assert action == "hr.leave_type.created"
        else:
            persisted = LeaveType.objects.using(alias).get(pk=leave_type.id)
            assert persisted.name == "Changed leave type" and persisted.revision == 2
            assert action == "hr.leave_type.updated"
        raise RuntimeError("Synthetic owner-local Audit failure after native effect")

    with (
        patch(
            "businessos.modules.hr.services.audit", side_effect=fail_after_native_effect
        ) as audit,
        pytest.raises(RuntimeError, match="owner-local Audit failure"),
    ):
        if operation == "employee_create":
            services.create_employee(
                hr_context,
                party_id=hr_person.pk,
                employee_number="ROLLBACK",
                joining_date=date(2020, 1, 1),
            )
        elif operation == "employee_update":
            services.update_employee(
                hr_context,
                employee_id=employee.id,
                expected_revision=1,
                joining_date=date(2019, 1, 1),
            )
        elif operation == "employee_end":
            services.end_employee(
                hr_context,
                employee_id=employee.id,
                expected_revision=1,
                leaving_date=date(2024, 1, 1),
            )
        elif operation == "employee_transfer":
            services.transfer_employee_branch(
                hr_context,
                employee_id=employee.id,
                expected_revision=1,
                branch_id=branch.pk,
            )
        elif operation == "leave_type_create":
            services.create_leave_type(hr_context, code="RB", name="Created leave type")
        else:
            services.update_leave_type(
                hr_context,
                leave_type_id=leave_type.id,
                expected_revision=1,
                name="Changed leave type",
                is_active=True,
            )
    audit.assert_called_once()
    assert _native() == before
