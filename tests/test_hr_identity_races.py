"""Actual Company-serialized uniqueness and retirement winners for HR owners."""

from datetime import date

import pytest
from django.db import connections

from businessos.core.audit.models import AuditEntry
from businessos.core.database import current_database_alias
from businessos.modules.hr import services
from businessos.modules.hr.models import Department, Employee, LeaveType
from businessos.modules.party.models import Party
from tests import test_hr_services as _fixtures
from tests.test_hr_concurrency import _race

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)


def _postgresql():
    if connections[current_database_alias()].vendor != "postgresql":
        pytest.skip("PostgreSQL-only actual HR uniqueness/retirement row-lock race.")


@pytest.mark.parametrize("identity_kind", ["party", "number", "user"])
@pytest.mark.parametrize("reverse", [False, True])
def test_employee_unique_identity_races_observe_one_committed_winner(
    hr_context, hr_person, monkeypatch, identity_kind, reverse
):
    _postgresql()
    other = Party.objects.create(
        company_id=hr_context.company_id, party_type="person", display_name="Other synthetic person"
    )
    values = [
        {"party_id": hr_person.pk, "employee_number": "FIRST"},
        {
            "party_id": hr_person.pk if identity_kind == "party" else other.pk,
            "employee_number": "FIRST" if identity_kind == "number" else "SECOND",
        },
    ]
    if identity_kind == "user":
        for payload in values:
            payload["user_id"] = hr_context.actor_id
    if reverse:
        values.reverse()

    def create(payload):
        return services.create_employee(hr_context, joining_date=date(2020, 1, 1), **payload)

    winner, _ = _race(
        monkeypatch,
        services,
        "hr.employee.created",
        lambda: create(values[0]),
        lambda: create(values[1]),
    )
    assert Employee.objects.count() == 1
    assert Employee.objects.get().pk == winner.id
    assert winner.employee_number == values[0]["employee_number"]
    assert AuditEntry.objects.filter(action="hr.employee.created").count() == 1


@pytest.mark.parametrize("kind", ["department", "leave_type"])
@pytest.mark.parametrize("reverse", [False, True])
def test_setup_code_races_keep_exact_winner_and_one_audit(hr_context, monkeypatch, kind, reverse):
    _postgresql()
    operation, model = (
        (services.create_department, Department)
        if kind == "department"
        else (services.create_leave_type, LeaveType)
    )
    names = ["First synthetic name", "Second synthetic name"]
    if reverse:
        names.reverse()
    winner, _ = _race(
        monkeypatch,
        services,
        f"hr.{kind}.created",
        lambda: operation(hr_context, code="SAME", name=names[0]),
        lambda: operation(hr_context, code=" same ", name=names[1]),
    )
    assert model.objects.count() == 1
    assert model.objects.get().pk == winner.id
    assert winner.name == names[0]
    assert AuditEntry.objects.filter(action=f"hr.{kind}.created").count() == 1


@pytest.mark.parametrize("retirement_first", [False, True])
def test_department_retirement_vs_new_active_assignment_both_winners(
    hr_context, hr_person, monkeypatch, retirement_first
):
    _postgresql()
    department = services.create_department(hr_context, code="RACE", name="Synthetic Department")

    def retire():
        return services.update_department(
            hr_context,
            department_id=department.id,
            expected_revision=1,
            name=department.name,
            is_active=False,
        )

    def assign():
        return services.create_employee(
            hr_context,
            party_id=hr_person.pk,
            employee_number="ASSIGN",
            joining_date=date(2020, 1, 1),
            department_id=department.id,
        )

    _race(
        monkeypatch,
        services,
        "hr.department.updated" if retirement_first else "hr.employee.created",
        retire if retirement_first else assign,
        assign if retirement_first else retire,
    )
    assert Department.objects.get().is_active == (not retirement_first)
    assert Employee.objects.count() == int(not retirement_first)
    assert AuditEntry.objects.filter(action="hr.department.updated").count() == int(
        retirement_first
    )
    assert AuditEntry.objects.filter(action="hr.employee.created").count() == int(
        not retirement_first
    )
