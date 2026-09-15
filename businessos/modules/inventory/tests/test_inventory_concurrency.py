from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from time import monotonic, sleep

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.utils import timezone

from businessos.core.access import services as access_services
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.modules.inventory.manifest import (
    CREATE_MOVEMENTS,
    POST_MOVEMENTS,
    UPDATE_MOVEMENTS,
)
from businessos.modules.inventory.models import (
    _LINE_MUTATION_TOKEN,
    _MOVEMENT_MUTATION_TOKEN,
    StockMovement,
    StockMovementLine,
)
from businessos.modules.inventory.services import (
    add_stock_movement_line,
    create_stock_movement,
    post_stock_movement,
    remove_stock_movement_line,
    update_stock_movement,
    update_stock_movement_line,
)


def _postgresql_only():
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and separate connections.")


def _wait_until_blocked(worker_pid):
    deadline = monotonic() + 10
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            cursor.execute("SELECT pg_backend_pid() = ANY(pg_blocking_pids(%s))", [worker_pid])
            if cursor.fetchone()[0]:
                return
            sleep(0.01)
    pytest.fail("The Inventory operation did not wait on the current transaction.")


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


def _call_and_close(operation):
    try:
        return operation()
    finally:
        connections.close_all()


def _add_receipt_line(context, movement, variant, warehouse, quantity="2"):
    return add_stock_movement_line(
        context,
        movement_id=movement.id,
        product_variant_id=variant.id,
        quantity=quantity,
        destination_warehouse_id=warehouse.id,
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("revocation", ["role", "permission", "company_access"])
@pytest.mark.parametrize(
    "operation_name,permission_code",
    [
        ("create", CREATE_MOVEMENTS),
        ("update", UPDATE_MOVEMENTS),
        ("line", UPDATE_MOVEMENTS),
        ("post", POST_MOVEMENTS),
    ],
)
def test_waiting_mutation_rechecks_revoked_authority(
    business_context,
    company,
    operator,
    inventory_permissions,
    draft_receipt,
    stockable_variant,
    warehouse,
    operation_name,
    permission_code,
    revocation,
):
    _postgresql_only()
    line = _add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )
    operations = {
        "create": lambda: create_stock_movement(
            business_context,
            movement_type=StockMovement.Type.RECEIPT,
            effective_at=timezone.now(),
        ),
        "update": lambda: update_stock_movement(
            business_context,
            movement_id=draft_receipt.id,
            notes="stale authority",
        ),
        "line": lambda: update_stock_movement_line(
            business_context,
            movement_id=draft_receipt.id,
            line_id=line.id,
            product_variant_id=stockable_variant.id,
            quantity="3",
            destination_warehouse_id=warehouse.id,
        ),
        "post": lambda: post_stock_movement(
            business_context, movement_id=draft_receipt.id
        ),
    }
    access_services.register_core_permissions()
    root = get_user_model().objects.create_superuser(
        f"inventory-root-{operation_name}-{revocation}@example.com", "password"
    )
    admin_context = BusinessContext(actor_id=root.id, company_id=company.id)
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            if revocation == "role":
                access_services.revoke_role(
                    admin_context,
                    user_id=operator.id,
                    role_id=inventory_permissions.id,
                )
            elif revocation == "permission":
                access_services.revoke_role_permission(
                    admin_context,
                    role_id=inventory_permissions.id,
                    permission_code=permission_code,
                )
            else:
                access_services.revoke_company_access(
                    admin_context,
                    user_id=operator.id,
                )
            audit_count = AuditEntry.objects.count()
            future = executor.submit(
                _worker, operations[operation_name], ready, pid
            )
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        message = (
            "access to this company"
            if revocation == "company_access"
            else permission_code
        )
        with pytest.raises(PermissionDenied, match=message):
            future.result(timeout=20)

    draft_receipt.refresh_from_db()
    line.refresh_from_db()
    assert AuditEntry.objects.count() == audit_count
    assert draft_receipt.status == StockMovement.Status.DRAFT
    assert draft_receipt.notes == ""
    assert line.quantity == Decimal("2")
    if operation_name == "create":
        assert StockMovement.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_post_is_retry_safe(
    business_context, draft_receipt, stockable_variant, warehouse
):
    _postgresql_only()
    line = _add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [
            future.result(timeout=20)
            for future in [
                executor.submit(
                    _call_and_close,
                    lambda: post_stock_movement(
                        business_context, movement_id=draft_receipt.id
                    ),
                )
                for _index in range(2)
            ]
        ]
    connections.close_all()
    draft_receipt.refresh_from_db()
    assert {result.id for result in results} == {draft_receipt.id}
    assert draft_receipt.status == StockMovement.Status.POSTED
    assert draft_receipt.lines.get().id == line.id
    assert (
        AuditEntry.objects.filter(
            action="inventory.movement.posted", object_id=str(draft_receipt.id)
        ).count()
        == 1
    )


@pytest.mark.django_db(transaction=True)
def test_concurrent_duplicate_idempotency_key_creates_at_most_one(
    business_context,
):
    _postgresql_only()

    def create(reference):
        try:
            return create_stock_movement(
                business_context,
                movement_type=StockMovement.Type.RECEIPT,
                effective_at=timezone.now(),
                reference=reference,
                idempotency_key="shared-key",
            )
        finally:
            connections.close_all()

    outcomes = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        for future in [executor.submit(create, value) for value in ("same", "different")]:
            try:
                outcomes.append(future.result(timeout=20))
            except ValidationError:
                outcomes.append(None)
    assert sum(result is not None for result in outcomes) == 1
    assert StockMovement.objects.filter(idempotency_key="shared-key").count() == 1
    assert AuditEntry.objects.filter(action="inventory.movement.created").count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mutation", ["header", "line_add", "line_edit", "line_remove"])
def test_posting_wins_over_waiting_draft_mutation(
    business_context,
    draft_receipt,
    stockable_variant,
    warehouse,
    mutation,
):
    _postgresql_only()
    line = _add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )
    operations = {
        "header": lambda: update_stock_movement(
            business_context,
            movement_id=draft_receipt.id,
            notes="must not alter posted history",
        ),
        "line_add": lambda: _add_receipt_line(
            business_context, draft_receipt, stockable_variant, warehouse, "1"
        ),
        "line_edit": lambda: update_stock_movement_line(
            business_context,
            movement_id=draft_receipt.id,
            line_id=line.id,
            product_variant_id=stockable_variant.id,
            quantity="3",
            destination_warehouse_id=warehouse.id,
        ),
        "line_remove": lambda: remove_stock_movement_line(
            business_context, movement_id=draft_receipt.id, line_id=line.id
        ),
    }
    update_count = AuditEntry.objects.filter(
        action="inventory.movement.updated", object_id=str(draft_receipt.id)
    ).count()
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            posted = post_stock_movement(
                business_context, movement_id=draft_receipt.id
            )
            posted_at = posted.posted_at
            future = executor.submit(_worker, operations[mutation], ready, pid)
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        with pytest.raises(ValidationError, match="Only draft"):
            future.result(timeout=20)

    draft_receipt.refresh_from_db()
    line.refresh_from_db()
    assert draft_receipt.status == StockMovement.Status.POSTED
    assert draft_receipt.posted_at == posted_at
    assert draft_receipt.notes == ""
    assert line.quantity == Decimal("2")
    assert draft_receipt.lines.count() == 1
    assert AuditEntry.objects.filter(
        action="inventory.movement.updated", object_id=str(draft_receipt.id)
    ).count() == update_count


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("mutation", ["header", "line_add", "line_edit", "line_remove"])
def test_committed_draft_mutation_is_observed_by_waiting_post(
    business_context,
    draft_receipt,
    stockable_variant,
    warehouse,
    mutation,
):
    _postgresql_only()
    line = _add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            if mutation == "header":
                update_stock_movement(
                    business_context,
                    movement_id=draft_receipt.id,
                    notes="committed before posting",
                )
            elif mutation == "line_add":
                _add_receipt_line(
                    business_context,
                    draft_receipt,
                    stockable_variant,
                    warehouse,
                    "1",
                )
            elif mutation == "line_edit":
                update_stock_movement_line(
                    business_context,
                    movement_id=draft_receipt.id,
                    line_id=line.id,
                    product_variant_id=stockable_variant.id,
                    quantity="3",
                    destination_warehouse_id=warehouse.id,
                )
            else:
                remove_stock_movement_line(
                    business_context,
                    movement_id=draft_receipt.id,
                    line_id=line.id,
                )
            future = executor.submit(
                _worker,
                lambda: post_stock_movement(
                    business_context, movement_id=draft_receipt.id
                ),
                ready,
                pid,
            )
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        if mutation == "line_remove":
            with pytest.raises(ValidationError, match="requires at least one line"):
                future.result(timeout=20)
        else:
            assert future.result(timeout=20).status == StockMovement.Status.POSTED

    draft_receipt.refresh_from_db()
    if mutation == "line_remove":
        assert draft_receipt.status == StockMovement.Status.DRAFT
        assert not draft_receipt.lines.exists()
    else:
        assert draft_receipt.status == StockMovement.Status.POSTED
        if mutation == "header":
            assert draft_receipt.notes == "committed before posting"
        elif mutation == "line_add":
            assert draft_receipt.lines.count() == 2
        else:
            line.refresh_from_db()
            assert line.quantity == Decimal("3")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("delete_target", ["movement", "line"])
def test_posting_wins_over_waiting_stale_instance_delete(
    business_context,
    draft_receipt,
    stockable_variant,
    warehouse,
    delete_target,
):
    _postgresql_only()
    line = _add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )
    stale = (
        StockMovement.objects.get(pk=draft_receipt.pk)
        if delete_target == "movement"
        else StockMovementLine.objects.get(pk=line.pk)
    )
    token = (
        _MOVEMENT_MUTATION_TOKEN
        if delete_target == "movement"
        else _LINE_MUTATION_TOKEN
    )
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            post_stock_movement(business_context, movement_id=draft_receipt.id)
            future = executor.submit(
                _worker,
                lambda: stale.delete(_inventory_token=token),
                ready,
                pid,
            )
            assert ready.wait(10)
            _wait_until_blocked(pid[0])
        with pytest.raises(ValidationError, match="Posted"):
            future.result(timeout=20)

    assert StockMovement.objects.filter(
        pk=draft_receipt.pk, status=StockMovement.Status.POSTED
    ).exists()
    assert StockMovementLine.objects.filter(pk=line.pk).exists()
