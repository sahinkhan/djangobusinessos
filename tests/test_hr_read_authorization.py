"""Delayed public selector results must not escape current view authorization.

These tests observe a real PostgreSQL blocker, then commit a supported authority
change before releasing that blocker. An exception, never a returned DTO/Page,
is the externally observable result. SQLite cannot certify this ordering.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Event
from time import monotonic

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import connections, transaction

from businessos.core.access import services as access_services
from businessos.core.access.models import Permission, Role, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import current_database_alias, database_execution
from businessos.core.organization.models import Company
from businessos.modules.hr import selectors, services
from businessos.modules.hr.models import (
    Attendance,
    AttendanceRevision,
    Department,
    Employee,
    LeaveRequest,
    LeaveType,
)
from businessos.modules.party.models import Party
from tests import test_hr_services as _fixtures

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def read_employee(hr_context, hr_person):
    if connections[current_database_alias()].vendor != "postgresql":
        pytest.skip("PostgreSQL-only observed Company/reference row-lock selector revocation.")
    return services.create_employee(
        hr_context,
        party_id=hr_person.pk,
        employee_number="READ-AUTH",
        joining_date=date(2020, 1, 1),
    )


def _native_and_hr_audit():
    alias = current_database_alias()
    return tuple(
        tuple(model.objects.using(alias).order_by("pk").values())
        for model in (Department, Employee, Attendance, AttendanceRevision, LeaveType, LeaveRequest)
    ), tuple(
        AuditEntry.objects.using(alias).filter(action__startswith="hr.").order_by("pk").values()
    )


def _reader(alias, context, employee_id, pids, started, surface):
    connection = connections[alias]
    try:
        connection.close()
        with database_execution(alias):
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.append(cursor.fetchone()[0])
            started.set()
            if surface == "detail":
                return selectors.employee_detail(context, employee_id)
            return selectors.employee_page(context, search="READ-AUTH")
    finally:
        connection.close()


def _observe_wait(connection, pids, started, expected_table):
    assert started.wait(10), "Selector worker did not establish its own connection"
    deadline = monotonic() + 3
    last_observed = None
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            # pg_stat_activity can retain an earlier snapshot for this long-lived
            # controller transaction even though pg_blocking_pids is current.
            # Refresh the statistics snapshot before classifying the actual SQL.
            cursor.execute("SELECT pg_stat_clear_snapshot()")
            cursor.execute(
                "SELECT pg_backend_pid() = ANY(pg_blocking_pids(pid)), query, wait_event_type "
                "FROM pg_stat_activity WHERE pid = %s",
                [pids[0]],
            )
            observed = cursor.fetchone()
            last_observed = observed
            if (
                observed
                and observed[0]
                and observed[2] == "Lock"
                and expected_table in observed[1]
                and "FOR UPDATE" in observed[1].upper()
            ):
                return
            # Bounded coordination polling, not an assumed sleep-based winner.
            Event().wait(0.005)
    pytest.fail(
        f"Selector never visibly waited on its {expected_table} FOR UPDATE blocker; "
        f"last observed activity={last_observed!r}"
    )


def _revoker(context):
    for code in (access_services.MANAGE_ORGANIZATIONAL_ACCESS, access_services.MANAGE_ROLES):
        Permission.objects.get_or_create(code=code, defaults={"name": code})
    user = get_user_model().objects.create_superuser(
        "hr-selector-revoker@example.test", "synthetic-only"
    )
    return BusinessContext(actor_id=user.pk, company_id=context.company_id)


@pytest.mark.parametrize("surface", ["detail", "page"])
@pytest.mark.parametrize("revocation", ["company_access", "role_assignment", "role_permission"])
def test_selector_rechecks_supported_revocation_after_real_company_wait(
    hr_context, read_employee, surface, revocation
):
    alias = current_database_alias()
    connection = connections[alias]
    admin = _revoker(hr_context)
    role_id = UserRoleAssignment.objects.using(alias).get(user_id=hr_context.actor_id).role_id
    before = _native_and_hr_audit()
    pids, started = [], Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(using=alias):
            Company.objects.using(alias).select_for_update().get(pk=hr_context.company_id)
            future = pool.submit(
                _reader, alias, hr_context, read_employee.id, pids, started, surface
            )
            _observe_wait(connection, pids, started, "organization_company")
            if revocation == "company_access":
                access_services.revoke_company_access(admin, user_id=hr_context.actor_id)
            elif revocation == "role_assignment":
                access_services.revoke_role(admin, user_id=hr_context.actor_id, role_id=role_id)
            else:
                access_services.revoke_role_permission(
                    admin, role_id=role_id, permission_code="hr.employee.view"
                )
        with pytest.raises(PermissionDenied):
            future.result(timeout=10)
    assert _native_and_hr_audit() == before


@pytest.mark.parametrize("surface", ["detail", "page"])
@pytest.mark.parametrize("revocation", ["actor", "role", "permission"])
def test_selector_rechecks_activity_after_observed_party_reference_wait(
    hr_context, hr_person, read_employee, surface, revocation
):
    alias = current_database_alias()
    connection = connections[alias]
    role_id = UserRoleAssignment.objects.using(alias).get(user_id=hr_context.actor_id).role_id
    before = _native_and_hr_audit()
    pids, started = [], Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(using=alias):
            Party.objects.using(alias).select_for_update().get(pk=hr_person.pk)
            future = pool.submit(
                _reader, alias, hr_context, read_employee.id, pids, started, surface
            )
            _observe_wait(connection, pids, started, "party_party")
            # These unchanged supported owner activity writers do not depend on
            # HR's already-held Company mutex. Initial permission checks have
            # passed, as proven by reaching the later Party reference lock.
            if revocation == "actor":
                get_user_model().objects.using(alias).filter(pk=hr_context.actor_id).update(
                    is_active=False
                )
            elif revocation == "role":
                Role.objects.using(alias).filter(pk=role_id).update(is_active=False)
            else:
                Permission.objects.using(alias).filter(code="hr.employee.view").update(
                    is_active=False
                )
        with pytest.raises(PermissionDenied):
            future.result(timeout=10)
    assert _native_and_hr_audit() == before
