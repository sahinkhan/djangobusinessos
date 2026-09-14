"""Adversarial regressions for the reopened Foundation acceptance gate."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic, sleep
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction

from businessos.core.access import services
from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserCompanyAccess,
    UserRoleAssignment,
)
from businessos.core.access.policies import has_permission, require_permission
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Branch, Company, Warehouse
from businessos.core.reference.models import Country, Currency, Language, UnitOfMeasure

pytestmark = pytest.mark.django_db


@pytest.fixture
def other_company(company):
    return Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )


@pytest.fixture
def security_setup(company, operator, branch, warehouse):
    services.register_core_permissions()
    root = get_user_model().objects.create_superuser("root@example.com", "password")
    admin = BusinessContext(actor_id=root.id, company_id=company.id)
    manager = BusinessContext(actor_id=operator.id, company_id=company.id)
    role = services.create_role(admin, code="MANAGER", name="Manager")
    for code in (services.MANAGE_ROLES, services.MANAGE_ORGANIZATIONAL_ACCESS):
        services.grant_role_permission(admin, role_id=role.id, permission_code=code)
    services.assign_role(admin, user_id=operator.id, role_id=role.id)
    services.grant_branch_access(admin, user_id=operator.id, branch_id=branch.id)
    services.grant_warehouse_access(admin, user_id=operator.id, warehouse_id=warehouse.id)
    return admin, manager, role


def _wait_until_blocked_by_this_connection(worker_pid):
    # Observe a real PostgreSQL lock wait, not an assumed thread scheduling delay.
    deadline = monotonic() + 10
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            cursor.execute("SELECT pg_backend_pid() = ANY(pg_blocking_pids(%s))", [worker_pid])
            if cursor.fetchone()[0]:
                return
            sleep(0.01)
    pytest.fail("The security operation did not wait for the company row lock.")


def _connection_worker(operation, ready, worker_pid):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SET statement_timeout = '15s'")
            cursor.execute("SELECT pg_backend_pid()")
            worker_pid.append(cursor.fetchone()[0])
        ready.set()
        return operation()
    finally:
        connections.close_all()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("revocation", ["role", "permission", "company"])
@pytest.mark.parametrize(
    "operation_name",
    [
        "grant_company_access",
        "revoke_company_access",
        "grant_branch_access",
        "revoke_branch_access",
        "grant_warehouse_access",
        "revoke_warehouse_access",
        "create_role",
        "grant_role_permission",
        "revoke_role_permission",
        "assign_role",
        "revoke_role",
    ],
)
def test_waiting_security_mutation_rechecks_revoked_authority(
    security_setup,
    company,
    operator,
    branch,
    warehouse,
    operation_name,
    revocation,
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    admin, manager, role = security_setup
    arguments = {
        "grant_company_access": {"user_id": operator.id},
        "revoke_company_access": {"user_id": operator.id},
        "grant_branch_access": {"user_id": operator.id, "branch_id": branch.id},
        "revoke_branch_access": {"user_id": operator.id, "branch_id": branch.id},
        "grant_warehouse_access": {"user_id": operator.id, "warehouse_id": warehouse.id},
        "revoke_warehouse_access": {"user_id": operator.id, "warehouse_id": warehouse.id},
        "create_role": {"code": "STALE", "name": "Stale"},
        "grant_role_permission": {"role_id": role.id, "permission_code": services.MANAGE_ROLES},
        "revoke_role_permission": {"role_id": role.id, "permission_code": services.MANAGE_ROLES},
        "assign_role": {"user_id": operator.id, "role_id": role.id},
        "revoke_role": {"user_id": operator.id, "role_id": role.id},
    }
    permission = (
        services.MANAGE_ORGANIZATIONAL_ACCESS
        if "_access" in operation_name
        else services.MANAGE_ROLES
    )
    assert has_permission(manager, permission)
    ready, worker_pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            if revocation == "role":
                services.revoke_role(admin, user_id=operator.id, role_id=role.id)
            elif revocation == "permission":
                services.revoke_role_permission(admin, role_id=role.id, permission_code=permission)
            else:
                services.revoke_company_access(admin, user_id=operator.id)
            audit_count = AuditEntry.objects.count()
            future = executor.submit(
                _connection_worker,
                lambda: getattr(services, operation_name)(manager, **arguments[operation_name]),
                ready,
                worker_pid,
            )
            assert ready.wait(10)
            _wait_until_blocked_by_this_connection(worker_pid[0])
        with pytest.raises(PermissionDenied):
            future.result(timeout=20)
    assert AuditEntry.objects.count() == audit_count
    if revocation == "company":
        assert not UserCompanyAccess.objects.filter(user=operator, company=company).exists()
    else:
        assert not has_permission(manager, permission)


@pytest.mark.django_db(transaction=True)
def test_self_assignment_commits_first_then_revocation_removes_authority(security_setup, operator):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    admin, manager, role = security_setup
    ready, worker_pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            services.assign_role(manager, user_id=operator.id, role_id=role.id)
            future = executor.submit(
                _connection_worker,
                lambda: services.revoke_role(admin, user_id=operator.id, role_id=role.id),
                ready,
                worker_pid,
            )
            assert ready.wait(10)
            _wait_until_blocked_by_this_connection(worker_pid[0])
        assert future.result(timeout=20)
    assert not has_permission(manager, services.MANAGE_ROLES)


def test_security_mutation_and_audit_roll_back_together(security_setup, monkeypatch):
    admin, _, _ = security_setup
    count = AuditEntry.objects.count()

    def unavailable_audit(**kwargs):
        raise RuntimeError("Audit storage unavailable")

    monkeypatch.setattr(services, "record_audit_entry", unavailable_audit)
    with pytest.raises(RuntimeError, match="Audit storage"):
        services.create_role(admin, code="ROLLBACK", name="Rollback")
    assert not Role.objects.filter(code="ROLLBACK").exists()
    assert AuditEntry.objects.count() == count


def _bulk_mutate(record, field, value, method):
    setattr(record, field, value)
    model = type(record)
    if method == "update":
        return model.objects.filter(pk=record.pk).update(**{field: value})
    if method == "bulk_update":
        return model.objects.bulk_update([record], [field])
    return model.objects.bulk_create(
        [record],
        update_conflicts=True,
        update_fields=[field],
        unique_fields=["id"],
    )


@pytest.mark.parametrize("method", ["update", "bulk_update", "upsert"])
@pytest.mark.parametrize(
    "model_name,field",
    [
        ("Branch", "company"),
        ("Branch", "company_id"),
        ("Branch", "is_active"),
        ("Warehouse", "company"),
        ("Warehouse", "company_id"),
        ("Warehouse", "branch"),
        ("Warehouse", "branch_id"),
        ("Warehouse", "is_active"),
    ],
)
def test_organization_bulk_paths_cannot_bypass_invariants(
    branch,
    warehouse,
    other_company,
    model_name,
    field,
    method,
):
    other_branch = Branch.objects.create(company=other_company, code="OTHER", name="Other")
    record = branch if model_name == "Branch" else warehouse
    values = {
        "company": other_company,
        "company_id": other_company.id,
        "branch": other_branch,
        "branch_id": other_branch.id,
        "is_active": False,
    }
    original = type(record).objects.filter(pk=record.pk).values().get()
    with pytest.raises(ValidationError):
        _bulk_mutate(record, field, values[field], method)
    assert type(record).objects.filter(pk=record.pk).values().get() == original


@pytest.mark.parametrize("method", ["update", "bulk_update", "upsert"])
@pytest.mark.parametrize(
    "field",
    [
        "base_currency",
        "base_currency_id",
        "timezone",
        "country",
        "country_id",
        "default_language",
        "default_language_id",
    ],
)
def test_company_bulk_paths_preserve_currency_timezone_and_active_references(
    company, field, method
):
    euro = Currency.objects.create(code="EUR", name="Euro")
    retired_country = Country.objects.create(code="GB", name="Retired", is_active=False)
    retired_language = Language.objects.create(code="FR", name="Retired", is_active=False)
    values = {
        "base_currency": euro,
        "base_currency_id": euro.id,
        "timezone": "Invalid/Timezone",
        "country": retired_country,
        "country_id": retired_country.id,
        "default_language": retired_language,
        "default_language_id": retired_language.id,
    }
    original = Company.objects.filter(pk=company.pk).values().get()
    with pytest.raises(ValidationError):
        _bulk_mutate(company, field, values[field], method)
    assert Company.objects.filter(pk=company.pk).values().get() == original


@pytest.mark.parametrize("method", ["bulk_update", "upsert"])
@pytest.mark.parametrize(
    "model,code,replacement",
    [
        (Country, "US", "GB"),
        (Currency, "USD", "EUR"),
        (Language, "EN", "FR"),
        (UnitOfMeasure, "EA", "KG"),
        (Permission, "example.record.view", "example.record.manage"),
    ],
)
def test_bulk_reference_and_permission_identity_rewrite_is_rejected(
    model, code, replacement, method
):
    record = model.objects.create(code=code, name="Original")
    with pytest.raises(ValidationError):
        _bulk_mutate(record, "code", replacement, method)
    record.refresh_from_db()
    assert record.code == code


@pytest.mark.parametrize("method", ["bulk_update", "upsert"])
def test_audit_evidence_cannot_be_rewritten_by_bulk_api(security_setup, method):
    entry = AuditEntry.objects.first()
    original = AuditEntry.objects.filter(pk=entry.pk).values().get()
    entry.action = "evidence.rewritten"
    entry.metadata = {"evidence": "replaced"}
    with pytest.raises(ValidationError, match="immutable"):
        if method == "bulk_update":
            AuditEntry.objects.bulk_update([entry], ["action", "metadata"])
        else:
            AuditEntry.objects.bulk_create(
                [entry],
                update_conflicts=True,
                update_fields=["action", "metadata"],
                unique_fields=["id"],
            )
    assert AuditEntry.objects.filter(pk=entry.pk).values().get() == original


def test_audit_allows_plain_append_only_bulk_insert(security_setup):
    admin, _, _ = security_setup
    entry = AuditEntry(
        actor_id=admin.actor_id,
        company_id=admin.company_id,
        action="example.record.created",
        object_type="example.Record",
        object_id=str(uuid4()),
        metadata={"created": True},
    )
    AuditEntry.objects.bulk_create([entry])
    assert AuditEntry.objects.get(pk=entry.pk).metadata == {"created": True}


def test_safe_labels_retirement_and_validated_company_updates_remain_supported(company):
    country = company.country
    country.name = "Corrected label"
    country.is_active = False
    Country.objects.bulk_update([country], ["name", "is_active"])
    country.refresh_from_db()
    assert country.name == "Corrected label" and not country.is_active
    replacement = Country.objects.create(code="GB", name="United Kingdom")
    company.country = replacement
    company.timezone = "Asia/Dhaka"
    company.save()
    company.refresh_from_db()
    assert company.country == replacement and company.timezone == "Asia/Dhaka"


def test_branch_cannot_retire_while_warehouses_are_active(branch, warehouse):
    branch.is_active = False
    with pytest.raises(ValidationError, match="Deactivate active warehouses"):
        branch.save()
    warehouse.is_active = False
    warehouse.save()
    branch.save()
    warehouse.is_active = True
    with pytest.raises(ValidationError, match="active branch"):
        warehouse.save()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("first", ["branch_retirement", "warehouse_activation"])
def test_branch_retirement_and_warehouse_activation_serialize(branch, warehouse, first):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    warehouse.is_active = False
    warehouse.save()
    ready, worker_pid = Event(), []

    def retire_branch():
        current = Branch.objects.get(pk=branch.pk)
        current.is_active = False
        current.save()

    def activate_warehouse():
        current = Warehouse.objects.select_related("branch").get(pk=warehouse.pk)
        current.is_active = True
        current.save()

    first_operation, waiting_operation = (
        (retire_branch, activate_warehouse)
        if first == "branch_retirement"
        else (activate_warehouse, retire_branch)
    )
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            first_operation()
            future = executor.submit(_connection_worker, waiting_operation, ready, worker_pid)
            assert ready.wait(10)
            _wait_until_blocked_by_this_connection(worker_pid[0])
        with pytest.raises(ValidationError):
            future.result(timeout=20)
    branch.refresh_from_db()
    warehouse.refresh_from_db()
    assert branch.is_active or not warehouse.is_active


@pytest.mark.parametrize(
    "model", [Company, Branch, Warehouse, Permission, Role, UserRoleAssignment]
)
def test_unvalidated_plain_bulk_creation_is_rejected(model):
    with pytest.raises(ValidationError, match="validated model saves"):
        model.objects.bulk_create([model()])


@pytest.mark.parametrize("method", ["update", "bulk_update", "upsert"])
def test_role_company_cannot_be_reassigned_through_bulk_paths(company, other_company, method):
    role = Role.objects.create(company=company, code="READER", name="Reader")
    with pytest.raises(ValidationError):
        _bulk_mutate(role, "company_id", other_company.id, method)
    role.refresh_from_db()
    assert role.company == company


@pytest.mark.parametrize("method", ["update", "bulk_update", "upsert", "insert"])
def test_role_assignment_bulk_paths_cannot_install_foreign_role(
    company,
    other_company,
    operator,
    method,
):
    local = Role.objects.create(company=company, code="LOCAL", name="Local")
    foreign = Role.objects.create(company=other_company, code="FOREIGN", name="Foreign")
    assignment = UserRoleAssignment.objects.create(user=operator, company=company, role=local)
    with pytest.raises(ValidationError):
        if method == "insert":
            UserRoleAssignment.objects.bulk_create(
                [
                    UserRoleAssignment(user=operator, company=company, role=foreign),
                ]
            )
        else:
            _bulk_mutate(assignment, "role_id", foreign.id, method)
    assignment.refresh_from_db()
    assert assignment.role == local
    assert UserRoleAssignment.objects.count() == 1


def test_malformed_cross_company_assignment_fails_closed(
    company,
    other_company,
    operator,
    business_context,
):
    local = Role.objects.create(company=company, code="LOCAL", name="Local")
    foreign = Role.objects.create(company=other_company, code="FOREIGN", name="Foreign")
    permission = Permission.objects.create(code="example.record.view", name="View")
    RolePermission.objects.create(role=foreign, permission=permission)
    assignment = UserRoleAssignment.objects.create(user=operator, company=company, role=local)
    # Simulate legacy/corrupt data after supported ORM paths have been closed.
    # Use the backend's UUID adaptation; this adversarial setup works on PostgreSQL and SQLite.
    table = connection.ops.quote_name(UserRoleAssignment._meta.db_table)
    role_id = Role._meta.pk.get_db_prep_value(foreign.pk, connection)
    assignment_id = UserRoleAssignment._meta.pk.get_db_prep_value(assignment.pk, connection)
    with connection.cursor() as cursor:
        cursor.execute(f"UPDATE {table} SET role_id = %s WHERE id = %s", [role_id, assignment_id])
    assert not has_permission(business_context, permission.code)
    with pytest.raises(PermissionDenied):
        require_permission(business_context, permission.code)
