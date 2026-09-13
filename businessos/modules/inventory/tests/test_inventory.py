from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier, Event
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection, connections
from django.urls import reverse
from django.utils import timezone

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company, Warehouse
from businessos.core.reference.models import Currency, UnitOfMeasure
from businessos.modules.catalog.models import Product
from businessos.modules.catalog.services import create_simple_product
from businessos.modules.inventory.manifest import MODULE
from businessos.modules.inventory.models import StockMovement, StockMovementLine
from businessos.modules.inventory.selectors import (
    balances_for_warehouse,
    movement_history,
    stock_balance,
)
from businessos.modules.inventory.services import (
    add_stock_movement_line,
    create_stock_movement,
    post_stock_movement,
    remove_stock_movement_line,
    update_stock_movement_line,
)


def product(context, uom, *, sku="ITEM-1", kind=Product.Type.STOCKABLE):
    return create_simple_product(
        context, name=sku, sku=sku, product_type=kind, default_uom_id=uom.id
    )


def movement(context, kind=StockMovement.Type.RECEIPT, **kwargs):
    return create_stock_movement(
        context,
        number=kwargs.pop("number", f"SM-{uuid4().hex[:8]}"),
        movement_type=kind,
        effective_at=timezone.now(),
        **kwargs,
    )


def add_line(context, record, variant, warehouse, *, quantity="2", other=None):
    data = {"product_variant_id": variant.id, "quantity": quantity}
    if record.movement_type == StockMovement.Type.RECEIPT:
        data["destination_warehouse_id"] = warehouse.id
    elif record.movement_type == StockMovement.Type.ISSUE:
        data["source_warehouse_id"] = warehouse.id
    else:
        data.update(source_warehouse_id=warehouse.id, destination_warehouse_id=other.id)
    return add_stock_movement_line(context, movement_id=record.id, **data)


@pytest.mark.django_db
def test_manifest_has_only_approved_dependencies():
    assert MODULE["depends"] == ["catalog", "organization", "access"]


@pytest.mark.django_db
def test_catalog_and_warehouse_have_no_authoritative_stock_field():
    from businessos.modules.catalog.models import ProductVariant

    prohibited = {"stock", "stock_quantity", "quantity_on_hand", "balance"}
    for model in (Product, ProductVariant, Warehouse):
        assert prohibited.isdisjoint(field.name for field in model._meta.fields)


@pytest.mark.django_db
def test_receipt_issue_and_transfer_derive_balances(
    business_context, company, branch, warehouse, uom
):
    variant = product(business_context, uom).variants.get()
    other = Warehouse.objects.create(company=company, branch=branch, code="SECOND", name="Second")
    receipt = movement(business_context)
    add_line(business_context, receipt, variant, warehouse, quantity="10")
    post_stock_movement(business_context, movement_id=receipt.id)
    issue = movement(business_context, StockMovement.Type.ISSUE)
    add_line(business_context, issue, variant, warehouse, quantity="12")
    post_stock_movement(business_context, movement_id=issue.id)
    transfer = movement(business_context, StockMovement.Type.TRANSFER)
    add_line(business_context, transfer, variant, warehouse, quantity="3", other=other)
    post_stock_movement(business_context, movement_id=transfer.id)

    assert stock_balance(
        business_context, warehouse_id=warehouse.id, product_variant_id=variant.id
    ) == Decimal("-5")
    assert stock_balance(
        business_context, warehouse_id=other.id, product_variant_id=variant.id
    ) == Decimal("3")
    assert balances_for_warehouse(business_context, warehouse_id=warehouse.id)[
        0
    ].quantity == Decimal("-5")
    assert movement_history(business_context, warehouse_id=warehouse.id).count() == 3


@pytest.mark.django_db
def test_drafts_do_not_affect_balance(business_context, warehouse, uom):
    variant = product(business_context, uom).variants.get()
    draft = movement(business_context)
    add_line(business_context, draft, variant, warehouse)
    assert (
        stock_balance(business_context, warehouse_id=warehouse.id, product_variant_id=variant.id)
        == 0
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind", [StockMovement.Type.RECEIPT, StockMovement.Type.ISSUE, StockMovement.Type.TRANSFER]
)
def test_routes_are_structurally_validated(business_context, warehouse, uom, kind):
    variant = product(business_context, uom, sku=f"{kind}-1").variants.get()
    record = movement(business_context, kind)
    with pytest.raises(ValidationError):
        add_stock_movement_line(
            business_context,
            movement_id=record.id,
            product_variant_id=variant.id,
            quantity="1",
            source_warehouse_id=warehouse.id,
            destination_warehouse_id=warehouse.id,
        )


@pytest.mark.django_db
def test_service_variant_is_rejected(business_context, warehouse, uom):
    variant = product(
        business_context, uom, sku="SERVICE", kind=Product.Type.SERVICE
    ).variants.get()
    with pytest.raises(ValidationError, match="Service"):
        add_line(business_context, movement(business_context), variant, warehouse)


@pytest.mark.django_db
def test_company_isolation_rejects_variant_and_warehouse(business_context, warehouse, uom):
    other_currency = Currency.objects.create(code="EUR", name="Euro")
    other_company = Company.objects.create(code="OTHER", name="Other", base_currency=other_currency)
    other_warehouse = Warehouse.objects.create(company=other_company, code="OTHER", name="Other")
    variant = product(business_context, uom).variants.get()
    record = movement(business_context)
    with pytest.raises(ValidationError, match="active company"):
        add_stock_movement_line(
            business_context,
            movement_id=record.id,
            product_variant_id=variant.id,
            quantity="1",
            destination_warehouse_id=other_warehouse.id,
        )


@pytest.mark.django_db
def test_quantity_precision_is_exact(business_context, warehouse, uom):
    variant = product(business_context, uom).variants.get()
    record = movement(business_context)
    add_line(business_context, record, variant, warehouse, quantity="0.0001")
    with pytest.raises(ValidationError, match="4 decimal"):
        add_line(business_context, record, variant, warehouse, quantity="0.00001")


@pytest.mark.django_db
def test_post_is_retry_safe_and_posted_graph_is_immutable(business_context, warehouse, uom):
    variant = product(business_context, uom).variants.get()
    record = movement(business_context)
    line = add_line(business_context, record, variant, warehouse)
    posted = post_stock_movement(business_context, movement_id=record.id)
    retry = post_stock_movement(business_context, movement_id=record.id)
    assert retry.posted_at == posted.posted_at
    stale = StockMovement.objects.get(id=record.id)
    stale.notes = "changed"
    with pytest.raises(ValidationError, match="immutable"):
        stale.save()
    with pytest.raises(ValidationError, match="immutable"):
        line.delete()
    with pytest.raises(ValidationError, match="cannot be deleted"):
        stale.delete()


@pytest.mark.django_db
def test_model_cannot_bypass_posting_service(business_context):
    record = movement(business_context)
    record.status = StockMovement.Status.POSTED
    record.posted_at = timezone.now()
    with pytest.raises(ValidationError, match="posting service"):
        record.save()


@pytest.mark.django_db
def test_uom_snapshot_and_posted_history_conflict(business_context, warehouse, uom):
    variant = product(business_context, uom).variants.get()
    first = movement(business_context)
    line = add_line(business_context, first, variant, warehouse)
    post_stock_movement(business_context, movement_id=first.id)
    assert line.uom_id == uom.id
    new_uom = UnitOfMeasure.objects.create(code="KG", name="Kilogram")
    variant.product.default_uom = new_uom
    variant.product.save()
    second = movement(business_context)
    add_line(business_context, second, variant, warehouse)
    with pytest.raises(ValidationError, match="posted stock history"):
        post_stock_movement(business_context, movement_id=second.id)


@pytest.mark.django_db
def test_idempotency_key_is_normalized_unique_and_nullable(business_context):
    first = movement(business_context, idempotency_key=" key-1 ")
    assert first.idempotency_key == "key-1"
    with pytest.raises(ValidationError, match="already in use"):
        movement(business_context, idempotency_key="key-1")
    movement(business_context)
    movement(business_context)


@pytest.mark.django_db
def test_different_companies_can_reuse_idempotency_key(business_context, currency, operator):
    other = Company.objects.create(code="OTHER", name="Other", base_currency=currency)
    from businessos.core.common.context import BusinessContext

    other_context = BusinessContext(actor_id=operator.id, company_id=other.id)
    movement(business_context, idempotency_key="shared-key")
    movement(other_context, idempotency_key="shared-key")
    assert StockMovement.objects.filter(idempotency_key="shared-key").count() == 2


@pytest.mark.django_db
def test_source_identity_all_or_none_and_immutable(business_context):
    with pytest.raises(ValidationError, match="supplied together"):
        movement(business_context, source_module="procurement")
    record = movement(
        business_context, source_module="external", source_type="receipt", source_id=uuid4()
    )
    record.source_type = "changed"
    with pytest.raises(ValidationError, match="immutable"):
        record.save()


@pytest.mark.django_db
def test_lock_first_update_does_not_recreate_deleted_line(business_context, warehouse, uom):
    variant = product(business_context, uom).variants.get()
    record = movement(business_context)
    line = add_line(business_context, record, variant, warehouse)
    remove_stock_movement_line(business_context, movement_id=record.id, line_id=line.id)
    with pytest.raises(ValidationError, match="no longer exists"):
        update_stock_movement_line(
            business_context,
            movement_id=record.id,
            line_id=line.id,
            product_variant_id=variant.id,
            quantity="2",
            destination_warehouse_id=warehouse.id,
        )
    assert StockMovementLine.objects.filter(id=line.id).count() == 0


@pytest.mark.django_db
def test_inactive_entities_rejected_at_posting(business_context, warehouse, uom):
    variant = product(business_context, uom).variants.get()
    record = movement(business_context)
    add_line(business_context, record, variant, warehouse)
    warehouse.is_active = False
    warehouse.save()
    with pytest.raises(ValidationError, match="active warehouse"):
        post_stock_movement(business_context, movement_id=record.id)


@pytest.mark.django_db
def test_post_failure_rolls_back_status(business_context, warehouse, uom, monkeypatch):
    variant = product(business_context, uom).variants.get()
    record = movement(business_context)
    add_line(business_context, record, variant, warehouse)

    def fail_update(*args, **kwargs):
        raise RuntimeError("simulated persistence failure")

    queryset_type = type(StockMovement.objects.all())
    monkeypatch.setattr(queryset_type, "update", fail_update)
    with pytest.raises(RuntimeError, match="simulated"):
        post_stock_movement(business_context, movement_id=record.id)
    record.refresh_from_db()
    assert record.status == StockMovement.Status.DRAFT
    assert record.posted_at is None


@pytest.mark.django_db
def test_disabled_module_is_hidden_and_404_then_enabled_is_available(client, operator, company):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    module = BusinessModule.objects.get(code="inventory")
    module.is_enabled = False
    module.save()
    assert client.get(reverse("inventory:list")).status_code == 404
    assert b'href="/inventory/movements/"' not in client.get(reverse("home")).content
    module.is_enabled = True
    module.save()
    assert client.get(reverse("inventory:list")).status_code == 200
    assert b'href="/inventory/movements/"' in client.get(reverse("home")).content


@pytest.mark.django_db
def test_stale_company_form_is_rejected(client, operator, company):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    module = BusinessModule.objects.get(code="inventory")
    module.is_enabled = True
    module.save()
    response = client.post(
        reverse("inventory:create"),
        {
            "scope_company_id": uuid4(),
            "number": "SM-X",
            "movement_type": "receipt",
            "effective_at": (timezone.now() - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M"),
        },
    )
    assert response.status_code == 200
    assert b"Company scope changed" in response.content
    assert not StockMovement.objects.filter(number="SM-X").exists()


@pytest.mark.django_db
def test_balance_http_filter_renders_derived_quantity(
    client, operator, company, warehouse, business_context, uom
):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    module = BusinessModule.objects.get(code="inventory")
    module.is_enabled = True
    module.save()
    variant = product(business_context, uom).variants.get()
    record = movement(business_context)
    add_line(business_context, record, variant, warehouse, quantity="4.2500")
    post_stock_movement(business_context, movement_id=record.id)

    response = client.get(reverse("inventory:balances"), {"warehouse": warehouse.id})

    assert response.status_code == 200
    assert b"4.2500" in response.content
    assert variant.sku.encode() in response.content


@pytest.mark.django_db(transaction=True)
def test_concurrent_post_is_retry_safe(business_context, warehouse, uom):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock concurrency contract requires PostgreSQL.")
    variant = product(business_context, uom).variants.get()
    record = movement(business_context)
    line = add_line(business_context, record, variant, warehouse)
    gate = Barrier(2)

    def post():
        close_old_connections()
        try:
            gate.wait()
            return post_stock_movement(business_context, movement_id=record.id).posted_at
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        posted_times = list(pool.map(lambda _: post(), range(2)))
    record.refresh_from_db()
    assert record.status == StockMovement.Status.POSTED
    assert posted_times[0] == posted_times[1] == record.posted_at
    assert StockMovementLine.objects.filter(id=line.id).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_idempotency_key_creates_one_movement(business_context):
    if connection.vendor != "postgresql":
        pytest.skip("Unique-key concurrency contract requires PostgreSQL.")
    gate = Barrier(2)

    def create(index):
        close_old_connections()
        try:
            gate.wait()
            return create_stock_movement(
                business_context,
                number=f"SM-IDEMPOTENT-{index}",
                movement_type=StockMovement.Type.RECEIPT,
                effective_at=timezone.now(),
                idempotency_key="concurrent-key",
            )
        except ValidationError as error:
            return error
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(create, range(2)))
    assert sum(isinstance(outcome, StockMovement) for outcome in outcomes) == 1
    assert sum(isinstance(outcome, ValidationError) for outcome in outcomes) == 1
    assert StockMovement.objects.filter(idempotency_key="concurrent-key").count() == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("operation", ["update", "delete"])
def test_line_change_waiting_on_post_cannot_change_posted_ledger(
    business_context, warehouse, uom, monkeypatch, operation
):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock concurrency contract requires PostgreSQL.")
    variant = product(business_context, uom).variants.get()
    record = movement(business_context)
    line = add_line(business_context, record, variant, warehouse)
    post_has_lock = Event()
    release_post = Event()
    from businessos.modules.inventory import services

    original_variant = services._variant

    def paused_variant(*args, **kwargs):
        post_has_lock.set()
        assert release_post.wait(timeout=10)
        return original_variant(*args, **kwargs)

    monkeypatch.setattr(services, "_variant", paused_variant)

    def post():
        close_old_connections()
        try:
            return post_stock_movement(business_context, movement_id=record.id)
        finally:
            connections.close_all()

    def mutate():
        close_old_connections()
        try:
            if operation == "delete":
                return remove_stock_movement_line(
                    business_context, movement_id=record.id, line_id=line.id
                )
            return update_stock_movement_line(
                business_context,
                movement_id=record.id,
                line_id=line.id,
                product_variant_id=variant.id,
                quantity="9",
                destination_warehouse_id=warehouse.id,
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        posted_future = pool.submit(post)
        assert post_has_lock.wait(timeout=10)
        mutation_future = pool.submit(mutate)
        release_post.set()
        posted_future.result(timeout=10)
        with pytest.raises(ValidationError, match="immutable"):
            mutation_future.result(timeout=10)
    line.refresh_from_db()
    assert line.quantity == Decimal("2")
