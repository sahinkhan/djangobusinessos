from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Event
from time import monotonic, sleep

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction

from businessos.core.access import services as access_services
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.modules.procurement.manifest import (
    CANCEL_ORDERS,
    CONFIRM_ORDERS,
    RECEIVE_ORDERS,
    UPDATE_ORDERS,
)
from businessos.modules.procurement.models import PurchaseOrder, PurchaseOrderLine
from businessos.modules.procurement.services import (
    add_purchase_order_line,
    cancel_purchase_order,
    confirm_purchase_order,
    receive_purchase_order,
    remove_purchase_order_line,
    update_purchase_order,
    update_purchase_order_line,
)


def _wait_until_blocked(worker_pid):
    deadline = monotonic() + 10
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            cursor.execute("SELECT pg_backend_pid() = ANY(pg_blocking_pids(%s))", [worker_pid])
            if cursor.fetchone()[0]:
                return
            sleep(0.01)
    pytest.fail("The Procurement operation did not wait on the current transaction.")


def _worker(operation, ready, pid):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SET statement_timeout = '15s'")
            cursor.execute("SELECT pg_backend_pid()")
            pid.append(cursor.fetchone()[0])
        ready.set()
        return operation()
    finally:
        connections.close_all()


@pytest.fixture
def confirmed_with_line(business_context, draft_purchase_order, purchasable_variant):
    line = add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=Decimal("5"),
        unit_cost=Decimal("1"),
    )
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    return draft_purchase_order, line


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("revocation", ["role", "permission", "company_access"])
@pytest.mark.parametrize(
    "operation_name,permission_code",
    [
        ("update", UPDATE_ORDERS),
        ("confirm", CONFIRM_ORDERS),
        ("cancel", CANCEL_ORDERS),
        ("receive", RECEIVE_ORDERS),
    ],
)
def test_waiting_mutation_rechecks_revoked_authority(
    business_context,
    company,
    operator,
    procurement_permissions,
    draft_purchase_order,
    purchasable_variant,
    operation_name,
    permission_code,
    revocation,
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    line = None
    if operation_name in {"confirm", "cancel", "receive"}:
        line = add_purchase_order_line(
            business_context,
            order_id=draft_purchase_order.id,
            product_variant_id=purchasable_variant.id,
            quantity=Decimal("2"),
            unit_cost=Decimal("1"),
        )
    if operation_name in {"cancel", "receive"}:
        confirm_purchase_order(business_context, order_id=draft_purchase_order.id)

    operations = {
        "update": lambda: update_purchase_order(
            business_context,
            order_id=draft_purchase_order.id,
            notes="stale authority",
        ),
        "confirm": lambda: confirm_purchase_order(
            business_context, order_id=draft_purchase_order.id
        ),
        "cancel": lambda: cancel_purchase_order(
            business_context, order_id=draft_purchase_order.id
        ),
        "receive": lambda: receive_purchase_order(
            business_context,
            purchase_order_id=draft_purchase_order.id,
            receipt_date=date(2026, 9, 14),
            idempotency_key=f"revoked-{revocation}",
            lines=[{"purchase_order_line_id": line.id, "quantity_received": "1"}],
        ),
    }
    access_services.register_core_permissions()
    root = get_user_model().objects.create_superuser(
        f"procurement-root-{operation_name}-{revocation}@example.com", "password"
    )
    admin_context = BusinessContext(actor_id=root.id, company_id=company.id)
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            if revocation == "role":
                access_services.revoke_role(
                    admin_context,
                    user_id=operator.id,
                    role_id=procurement_permissions.id,
                )
            elif revocation == "permission":
                access_services.revoke_role_permission(
                    admin_context,
                    role_id=procurement_permissions.id,
                    permission_code=permission_code,
                )
            else:
                access_services.revoke_company_access(
                    admin_context,
                    user_id=operator.id,
                )
            audit_count = AuditEntry.objects.count()
            future = executor.submit(
                _worker,
                operations[operation_name],
                ready,
                pid,
            )
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        denial_message = (
            "access to this company" if revocation == "company_access" else permission_code
        )
        with pytest.raises(PermissionDenied, match=denial_message):
            future.result(timeout=20)
    draft_purchase_order.refresh_from_db()
    assert AuditEntry.objects.count() == audit_count
    if operation_name == "update":
        assert draft_purchase_order.notes == "Priority supplier"
    elif operation_name == "confirm":
        assert draft_purchase_order.status == PurchaseOrder.Status.DRAFT
    elif operation_name == "cancel":
        assert draft_purchase_order.status == PurchaseOrder.Status.CONFIRMED
    else:
        assert not draft_purchase_order.receipts.exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("winner", ["receipt", "cancel"])
def test_receipt_and_cancel_serialize_without_cancelled_receipt(
    business_context, confirmed_with_line, winner
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    order, line = confirmed_with_line

    def receive():
        return receive_purchase_order(
            business_context,
            purchase_order_id=order.id,
            receipt_date=date(2026, 9, 14),
            idempotency_key=f"race-{winner}",
            lines=[{"purchase_order_line_id": line.id, "quantity_received": "1"}],
        )

    def cancel():
        return cancel_purchase_order(business_context, order_id=order.id)

    ready, pid = Event(), []
    first, second = (receive, cancel) if winner == "receipt" else (cancel, receive)
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            first()
            future = executor.submit(_worker, second, ready, pid)
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        with pytest.raises(ValidationError):
            future.result(timeout=20)
    order.refresh_from_db()
    if winner == "receipt":
        assert order.status == PurchaseOrder.Status.CONFIRMED
        assert order.receipts.count() == 1
    else:
        assert order.status == PurchaseOrder.Status.CANCELLED
        assert not order.receipts.exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_receipts_prevent_over_receipt(business_context, confirmed_with_line):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    order, line = confirmed_with_line

    def receive(key):
        return receive_purchase_order(
            business_context,
            purchase_order_id=order.id,
            receipt_date=date(2026, 9, 14),
            idempotency_key=key,
            lines=[{"purchase_order_line_id": line.id, "quantity_received": "3"}],
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(receive, f"over-{index}") for index in range(2)]
        outcomes = []
        for future in futures:
            try:
                outcomes.append(future.result(timeout=20))
            except ValidationError:
                outcomes.append(None)
    connections.close_all()
    assert sum(result is not None for result in outcomes) == 1
    assert order.receipts.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_confirmation_is_retry_safe(
    business_context, draft_purchase_order, purchasable_variant
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=1,
        unit_cost=1,
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                confirm_purchase_order,
                business_context,
                order_id=draft_purchase_order.id,
            )
            for _index in range(2)
        ]
        results = [future.result(timeout=20) for future in futures]
    connections.close_all()
    assert {result.id for result in results} == {draft_purchase_order.id}
    assert (
        AuditEntry.objects.filter(
            action="procurement.order.confirmed", object_id=str(draft_purchase_order.id)
        ).count()
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_concurrent_line_positions_are_unique(
    business_context, draft_purchase_order, purchasable_variant
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")

    def add():
        try:
            return add_purchase_order_line(
                business_context,
                order_id=draft_purchase_order.id,
                product_variant_id=purchasable_variant.id,
                quantity=1,
                unit_cost=1,
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(add) for _index in range(2)]
        results = [future.result(timeout=20) for future in futures]
    assert sorted(line.position for line in results) == [1, 2]


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("conflicting", [False, True])
def test_concurrent_same_key_receipts_are_idempotent_or_conflict(
    business_context, confirmed_with_line, conflicting
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    order, line = confirmed_with_line

    def receive(quantity):
        try:
            return receive_purchase_order(
                business_context,
                purchase_order_id=order.id,
                receipt_date="2026-09-14",
                idempotency_key="same-key",
                lines=[{"purchase_order_line_id": line.id, "quantity_received": quantity}],
            )
        finally:
            connections.close_all()

    quantities = ["1", "2" if conflicting else "1"]
    outcomes = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        for future in [executor.submit(receive, quantity) for quantity in quantities]:
            try:
                outcomes.append(future.result(timeout=20))
            except ValidationError:
                outcomes.append(None)
    assert order.receipts.count() == 1
    assert AuditEntry.objects.filter(action="procurement.receipt.posted").count() == 1
    if conflicting:
        assert sum(result is None for result in outcomes) == 1
    else:
        assert {result.id for result in outcomes} == {order.receipts.get().id}


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mutation", ["header", "line_edit", "line_remove"])
def test_confirmation_wins_over_waiting_draft_mutation(
    business_context,
    draft_purchase_order,
    purchasable_variant,
    mutation,
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    line = add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=Decimal("2"),
        unit_cost=Decimal("1"),
    )
    operations = {
        "header": lambda: update_purchase_order(
            business_context,
            order_id=draft_purchase_order.id,
            notes="must not alter confirmed history",
        ),
        "line_edit": lambda: update_purchase_order_line(
            business_context,
            line_id=line.id,
            product_variant_id=purchasable_variant.id,
            quantity=Decimal("3"),
            unit_cost=Decimal("2"),
            description="must not alter confirmed history",
        ),
        "line_remove": lambda: remove_purchase_order_line(
            business_context,
            line_id=line.id,
        ),
    }
    update_audits = AuditEntry.objects.filter(
        action="procurement.order.updated", object_id=str(draft_purchase_order.id)
    ).count()
    ready, pid = Event(), []

    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
            future = executor.submit(_worker, operations[mutation], ready, pid)
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        with pytest.raises(ValidationError, match="Only draft"):
            future.result(timeout=20)

    draft_purchase_order.refresh_from_db()
    line.refresh_from_db()
    assert draft_purchase_order.status == PurchaseOrder.Status.CONFIRMED
    assert draft_purchase_order.notes == "Priority supplier"
    assert line.quantity == Decimal("2")
    assert line.unit_cost == Decimal("1")
    assert AuditEntry.objects.filter(
        action="procurement.order.updated", object_id=str(draft_purchase_order.id)
    ).count() == update_audits
    assert AuditEntry.objects.filter(
        action="procurement.order.confirmed", object_id=str(draft_purchase_order.id)
    ).count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mutation", ["header", "line_edit", "line_remove"])
def test_committed_draft_mutation_is_observed_by_waiting_confirmation(
    business_context,
    draft_purchase_order,
    purchasable_variant,
    mutation,
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    line = add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=Decimal("2"),
        unit_cost=Decimal("1"),
    )
    surviving_line = None
    if mutation == "line_remove":
        surviving_line = add_purchase_order_line(
            business_context,
            order_id=draft_purchase_order.id,
            product_variant_id=purchasable_variant.id,
            quantity=Decimal("1"),
            unit_cost=Decimal("1"),
        )
    ready, pid = Event(), []

    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            if mutation == "header":
                update_purchase_order(
                    business_context,
                    order_id=draft_purchase_order.id,
                    notes="committed before confirmation",
                )
            elif mutation == "line_edit":
                update_purchase_order_line(
                    business_context,
                    line_id=line.id,
                    product_variant_id=purchasable_variant.id,
                    quantity=Decimal("3"),
                    unit_cost=Decimal("2"),
                    description="committed before confirmation",
                )
            else:
                remove_purchase_order_line(business_context, line_id=line.id)
            future = executor.submit(
                _worker,
                lambda: confirm_purchase_order(
                    business_context, order_id=draft_purchase_order.id
                ),
                ready,
                pid,
            )
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        confirmed = future.result(timeout=20)

    draft_purchase_order.refresh_from_db()
    assert confirmed.status == PurchaseOrder.Status.CONFIRMED
    assert draft_purchase_order.status == PurchaseOrder.Status.CONFIRMED
    if mutation == "header":
        assert draft_purchase_order.notes == "committed before confirmation"
    elif mutation == "line_edit":
        line.refresh_from_db()
        assert line.quantity == Decimal("3")
        assert line.unit_cost == Decimal("2")
    else:
        assert not PurchaseOrderLine.objects.filter(pk=line.pk).exists()
        assert PurchaseOrderLine.objects.filter(pk=surviving_line.pk).exists()
    assert AuditEntry.objects.filter(
        action="procurement.order.confirmed", object_id=str(draft_purchase_order.id)
    ).count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("delete_target", ["order", "line"])
def test_confirmation_wins_over_waiting_stale_instance_delete(
    business_context,
    draft_purchase_order,
    purchasable_variant,
    delete_target,
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    line = add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=Decimal("1"),
        unit_cost=Decimal("1"),
    )
    stale_target = (
        PurchaseOrder.objects.get(pk=draft_purchase_order.pk)
        if delete_target == "order"
        else PurchaseOrderLine.objects.get(pk=line.pk)
    )
    update_audits = AuditEntry.objects.filter(
        action="procurement.order.updated", object_id=str(draft_purchase_order.id)
    ).count()
    ready, pid = Event(), []

    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
            future = executor.submit(_worker, stale_target.delete, ready, pid)
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        with pytest.raises(ValidationError):
            future.result(timeout=20)

    assert PurchaseOrder.objects.filter(
        pk=draft_purchase_order.pk, status=PurchaseOrder.Status.CONFIRMED
    ).exists()
    assert PurchaseOrderLine.objects.filter(pk=line.pk).exists()
    assert AuditEntry.objects.filter(
        action="procurement.order.updated", object_id=str(draft_purchase_order.id)
    ).count() == update_audits
    assert AuditEntry.objects.filter(
        action="procurement.order.confirmed", object_id=str(draft_purchase_order.id)
    ).count() == 1
