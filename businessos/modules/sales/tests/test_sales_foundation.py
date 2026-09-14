import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from pathlib import Path
from threading import Event
from time import monotonic, sleep

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction

from businessos.core.access import services as access_services
from businessos.core.access.models import Permission, RolePermission
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.services import register_manifest
from businessos.modules.sales import services as sales_services
from businessos.modules.sales.forms import SalesOrderForm
from businessos.modules.sales.manifest import (
    CANCEL_ORDERS,
    CONFIRM_ORDERS,
    CREATE_ORDERS,
    MODULE,
    SALES_PERMISSION_DECLARATIONS,
    UPDATE_ORDERS,
    VIEW_ORDERS,
)
from businessos.modules.sales.models import SalesOrder, SalesOrderLine
from businessos.modules.sales.selectors import sales_orders_for_company


def _drop_permission(role, code):
    RolePermission.objects.filter(role=role, permission__code=code).delete()


@pytest.mark.django_db
def test_manifest_and_bootstrap_freeze_exact_sales_permissions():
    expected = [
        VIEW_ORDERS,
        CREATE_ORDERS,
        UPDATE_ORDERS,
        CONFIRM_ORDERS,
        CANCEL_ORDERS,
    ]
    module = BusinessModule.objects.get(code="sales")

    assert MODULE["permissions"] == expected
    assert module.declared_permissions == sorted(expected)
    assert list(
        Permission.objects.filter(code__startswith="sales.").order_by("code").values_list(
            "code", "name"
        )
    ) == sorted(SALES_PERMISSION_DECLARATIONS)


@pytest.mark.django_db
def test_manifest_reregistration_preserves_enablement_and_retired_permissions():
    module = register_manifest(MODULE, enabled=True)
    retired = Permission.objects.get(code=VIEW_ORDERS)
    retired.is_active = False
    retired.save()

    same_module = register_manifest(MODULE)
    retired.refresh_from_db()

    assert same_module.id == module.id
    assert same_module.is_enabled
    assert not retired.is_active


@pytest.mark.django_db
@pytest.mark.parametrize("registry_state", ["disabled", "missing"])
def test_module_registry_state_does_not_disable_installed_python_services(
    business_context, customer, currency, registry_state
):
    if registry_state == "missing":
        BusinessModule.objects.filter(code="sales").delete()
    else:
        BusinessModule.objects.filter(code="sales").update(is_enabled=False)

    order = sales_services.create_sales_order(
        business_context,
        customer_id=customer.id,
        order_date=date(2026, 9, 14),
        currency_id=currency.id,
    )

    assert order.company_id == business_context.company_id
    assert order.status == SalesOrder.Status.DRAFT


def test_sales_has_no_phase2_module_imports_or_integration_writes():
    sales_root = Path(__file__).resolve().parents[1]
    forbidden = (
        "businessos.modules.inventory",
        "businessos.modules.procurement",
        "businessos.modules.billing",
        "businessos.modules.accounting",
    )
    imported = set()
    for path in sales_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)

    assert not any(name.startswith(forbidden) for name in imported)


@pytest.mark.django_db
def test_view_permission_is_required_for_sales_selectors(
    business_context, sales_permissions
):
    _drop_permission(sales_permissions, VIEW_ORDERS)

    with pytest.raises(PermissionDenied, match=VIEW_ORDERS):
        list(sales_orders_for_company(business_context))


@pytest.mark.django_db
def test_create_permission_is_required_and_denial_has_no_effect(
    business_context, sales_permissions, customer, currency
):
    _drop_permission(sales_permissions, CREATE_ORDERS)
    audit_count = AuditEntry.objects.count()

    with pytest.raises(PermissionDenied, match=CREATE_ORDERS):
        sales_services.create_sales_order(
            business_context,
            customer_id=customer.id,
            order_date=date(2026, 9, 14),
            currency_id=currency.id,
        )

    assert not SalesOrder.objects.exists()
    assert AuditEntry.objects.count() == audit_count


@pytest.mark.django_db
def test_update_permission_is_required(
    business_context, sales_permissions, draft_order
):
    _drop_permission(sales_permissions, UPDATE_ORDERS)

    with pytest.raises(PermissionDenied, match=UPDATE_ORDERS):
        sales_services.update_sales_order(
            business_context, order_id=draft_order.id, notes="Denied"
        )

    draft_order.refresh_from_db()
    assert draft_order.notes == "Priority customer"


@pytest.mark.django_db
def test_confirm_and_cancel_permissions_are_independent(
    business_context, sales_permissions, draft_order, variant
):
    sales_services.add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=Decimal("1"),
        unit_price=Decimal("10"),
    )
    _drop_permission(sales_permissions, CONFIRM_ORDERS)
    with pytest.raises(PermissionDenied, match=CONFIRM_ORDERS):
        sales_services.confirm_sales_order(business_context, order_id=draft_order.id)

    RolePermission.objects.create(
        role=sales_permissions,
        permission=Permission.objects.get(code=CONFIRM_ORDERS),
    )
    confirmed = sales_services.confirm_sales_order(
        business_context, order_id=draft_order.id
    )
    _drop_permission(sales_permissions, CANCEL_ORDERS)
    with pytest.raises(PermissionDenied, match=CANCEL_ORDERS):
        sales_services.cancel_sales_order(business_context, order_id=confirmed.id)


@pytest.mark.django_db
def test_sales_audit_vocabulary_is_atomic_and_retry_safe(
    business_context, draft_order, variant
):
    created = AuditEntry.objects.get(
        action="sales.order.created", object_id=str(draft_order.id)
    )
    assert created.actor_id == business_context.actor_id
    assert created.company_id == business_context.company_id
    assert created.object_type == "sales.SalesOrder"

    line = sales_services.add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=Decimal("2"),
        unit_price=Decimal("5"),
    )
    sales_services.update_sales_order(
        business_context, order_id=draft_order.id, notes="Priority customer"
    )
    sales_services.update_sales_order_line(
        business_context,
        line_id=line.id,
        product_variant_id=variant.id,
        quantity=Decimal("2"),
        unit_price=Decimal("5"),
        description=line.description_snapshot,
    )
    assert AuditEntry.objects.filter(
        action="sales.order.updated", object_id=str(draft_order.id)
    ).count() == 1

    sales_services.confirm_sales_order(business_context, order_id=draft_order.id)
    sales_services.confirm_sales_order(business_context, order_id=draft_order.id)
    assert AuditEntry.objects.filter(
        action="sales.order.confirmed", object_id=str(draft_order.id)
    ).count() == 1

    sales_services.cancel_sales_order(business_context, order_id=draft_order.id)
    sales_services.cancel_sales_order(business_context, order_id=draft_order.id)
    assert AuditEntry.objects.filter(
        action="sales.order.cancelled", object_id=str(draft_order.id)
    ).count() == 1


@pytest.mark.django_db
def test_sales_mutation_and_audit_roll_back_together(
    business_context, customer, currency, monkeypatch
):
    def unavailable_audit(**kwargs):
        raise RuntimeError("Audit storage unavailable")

    monkeypatch.setattr(sales_services, "record_audit_entry", unavailable_audit)
    with pytest.raises(RuntimeError, match="Audit storage"):
        sales_services.create_sales_order(
            business_context,
            customer_id=customer.id,
            order_date=date(2026, 9, 14),
            currency_id=currency.id,
        )

    assert not SalesOrder.objects.exists()


@pytest.mark.django_db
def test_transition_and_audit_roll_back_together(
    business_context, draft_order, variant, monkeypatch
):
    sales_services.add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=1,
        unit_price=10,
    )
    real_audit = sales_services.record_audit_entry

    def unavailable_audit(**kwargs):
        raise RuntimeError("Audit storage unavailable")

    monkeypatch.setattr(sales_services, "record_audit_entry", unavailable_audit)
    with pytest.raises(RuntimeError, match="Audit storage"):
        sales_services.confirm_sales_order(business_context, order_id=draft_order.id)
    draft_order.refresh_from_db()
    assert draft_order.status == SalesOrder.Status.DRAFT
    assert draft_order.confirmed_at is None

    monkeypatch.setattr(sales_services, "record_audit_entry", real_audit)
    sales_services.confirm_sales_order(business_context, order_id=draft_order.id)
    monkeypatch.setattr(sales_services, "record_audit_entry", unavailable_audit)
    with pytest.raises(RuntimeError, match="Audit storage"):
        sales_services.cancel_sales_order(business_context, order_id=draft_order.id)
    draft_order.refresh_from_db()
    assert draft_order.status == SalesOrder.Status.CONFIRMED


@pytest.mark.django_db
def test_sales_form_uses_company_local_business_date(company, monkeypatch):
    expected = date(2026, 9, 15)
    monkeypatch.setattr(
        "businessos.modules.sales.forms.company_local_date",
        lambda company_id: expected,
    )

    form = SalesOrderForm(company_id=company.id)

    assert form.initial["order_date"] == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "quantity,unit_price",
    [
        (Decimal("0.00001"), Decimal("1")),
        (Decimal("1"), Decimal("0.00001")),
        (Decimal("100000000000000"), Decimal("1")),
        (Decimal("1"), Decimal("100000000000000")),
    ],
)
def test_service_rejects_unsupported_quantity_and_price_precision(
    business_context, draft_order, variant, quantity, unit_price
):
    audit_count = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        sales_services.add_sales_order_line(
            business_context,
            order_id=draft_order.id,
            product_variant_id=variant.id,
            quantity=quantity,
            unit_price=unit_price,
        )

    assert not draft_order.lines.exists()
    assert AuditEntry.objects.count() == audit_count


def _wait_until_blocked_by_this_connection(worker_pid):
    deadline = monotonic() + 10
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            cursor.execute("SELECT pg_backend_pid() = ANY(pg_blocking_pids(%s))", [worker_pid])
            if cursor.fetchone()[0]:
                return
            sleep(0.01)
    pytest.fail("The Sales mutation did not wait for the current transaction lock.")


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
def test_waiting_sales_mutation_rechecks_revoked_permission(
    business_context, company, operator, sales_permissions, draft_order
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    manage_roles, _created = Permission.objects.get_or_create(
        code=access_services.MANAGE_ROLES,
        defaults={"name": "Manage BusinessOS roles", "is_active": True},
    )
    if not manage_roles.is_active:
        manage_roles.is_active = True
        manage_roles.save()
    root = get_user_model().objects.create_superuser("sales-root@example.com", "password")
    admin_context = BusinessContext(actor_id=root.id, company_id=company.id)
    ready, worker_pid = Event(), []

    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            access_services.revoke_role_permission(
                admin_context,
                role_id=sales_permissions.id,
                permission_code=UPDATE_ORDERS,
            )
            future = executor.submit(
                _connection_worker,
                lambda: sales_services.update_sales_order(
                    business_context, order_id=draft_order.id, notes="Stale authority"
                ),
                ready,
                worker_pid,
            )
            assert ready.wait(10)
            _wait_until_blocked_by_this_connection(worker_pid[0])
        with pytest.raises(PermissionDenied, match=UPDATE_ORDERS):
            future.result(timeout=20)

    draft_order.refresh_from_db()
    assert draft_order.notes == "Priority customer"


@pytest.mark.django_db(transaction=True)
def test_confirmation_wins_over_waiting_header_edit(
    business_context, draft_order, variant
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    sales_services.add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=Decimal("1"),
        unit_price=Decimal("10"),
    )
    updated_audits_before = AuditEntry.objects.filter(
        action="sales.order.updated", object_id=str(draft_order.id)
    ).count()
    ready, worker_pid = Event(), []

    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            sales_services.confirm_sales_order(
                business_context, order_id=draft_order.id
            )
            future = executor.submit(
                _connection_worker,
                lambda: sales_services.update_sales_order(
                    business_context,
                    order_id=draft_order.id,
                    notes="Must not reach confirmed history",
                ),
                ready,
                worker_pid,
            )
            assert ready.wait(10)
            _wait_until_blocked_by_this_connection(worker_pid[0])
        with pytest.raises(ValidationError, match="Only draft"):
            future.result(timeout=20)

    draft_order.refresh_from_db()
    assert draft_order.status == SalesOrder.Status.CONFIRMED
    assert draft_order.notes == "Priority customer"
    assert AuditEntry.objects.filter(
        action="sales.order.updated", object_id=str(draft_order.id)
    ).count() == updated_audits_before
    assert AuditEntry.objects.filter(
        action="sales.order.confirmed", object_id=str(draft_order.id)
    ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_committed_header_edit_is_observed_by_waiting_confirmation(
    business_context, draft_order, variant
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    sales_services.add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=Decimal("1"),
        unit_price=Decimal("10"),
    )
    ready, worker_pid = Event(), []

    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            sales_services.update_sales_order(
                business_context,
                order_id=draft_order.id,
                notes="Committed before confirmation",
            )
            future = executor.submit(
                _connection_worker,
                lambda: sales_services.confirm_sales_order(
                    business_context, order_id=draft_order.id
                ),
                ready,
                worker_pid,
            )
            assert ready.wait(10)
            _wait_until_blocked_by_this_connection(worker_pid[0])
        confirmed = future.result(timeout=20)

    draft_order.refresh_from_db()
    assert confirmed.status == SalesOrder.Status.CONFIRMED
    assert draft_order.status == SalesOrder.Status.CONFIRMED
    assert draft_order.notes == "Committed before confirmation"
    assert AuditEntry.objects.filter(
        action="sales.order.updated", object_id=str(draft_order.id)
    ).count() == 2
    assert AuditEntry.objects.filter(
        action="sales.order.confirmed", object_id=str(draft_order.id)
    ).count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("delete_target", ["order", "line"])
def test_confirmation_wins_over_waiting_stale_delete(
    business_context, draft_order, variant, delete_target
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    line = sales_services.add_sales_order_line(
        business_context,
        order_id=draft_order.id,
        product_variant_id=variant.id,
        quantity=Decimal("1"),
        unit_price=Decimal("10"),
    )
    stale_target = (
        SalesOrder.objects.get(pk=draft_order.pk)
        if delete_target == "order"
        else SalesOrderLine.objects.get(pk=line.pk)
    )
    updated_audits_before = AuditEntry.objects.filter(
        action="sales.order.updated", object_id=str(draft_order.id)
    ).count()
    ready, worker_pid = Event(), []

    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            sales_services.confirm_sales_order(
                business_context, order_id=draft_order.id
            )
            future = executor.submit(
                _connection_worker,
                stale_target.delete,
                ready,
                worker_pid,
            )
            assert ready.wait(10)
            _wait_until_blocked_by_this_connection(worker_pid[0])
        with pytest.raises(ValidationError):
            future.result(timeout=20)

    assert SalesOrder.objects.filter(
        pk=draft_order.pk, status=SalesOrder.Status.CONFIRMED
    ).exists()
    assert SalesOrderLine.objects.filter(pk=line.pk).exists()
    assert AuditEntry.objects.filter(
        action="sales.order.updated", object_id=str(draft_order.id)
    ).count() == updated_audits_before
    assert AuditEntry.objects.filter(
        action="sales.order.confirmed", object_id=str(draft_order.id)
    ).count() == 1
