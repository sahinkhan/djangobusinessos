from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Event
from time import monotonic, sleep

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction

from businessos.core.access.models import RolePermission
from businessos.core.audit.models import AuditEntry
from businessos.modules.procurement.manifest import UPDATE_ORDERS
from businessos.modules.procurement.models import PurchaseOrder
from businessos.modules.procurement.services import (
    add_purchase_order_line,
    cancel_purchase_order,
    confirm_purchase_order,
    receive_purchase_order,
    update_purchase_order,
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
def test_waiting_mutation_rechecks_revoked_permission(
    business_context, company, procurement_permissions, draft_purchase_order
):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            company.__class__.objects.select_for_update().get(pk=company.pk)
            RolePermission.objects.filter(
                role=procurement_permissions, permission__code=UPDATE_ORDERS
            ).delete()
            future = executor.submit(
                _worker,
                lambda: update_purchase_order(
                    business_context,
                    order_id=draft_purchase_order.id,
                    notes="stale authority",
                ),
                ready,
                pid,
            )
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        with pytest.raises(PermissionDenied, match=UPDATE_ORDERS):
            future.result(timeout=20)


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
