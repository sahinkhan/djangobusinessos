from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from inspect import signature
from threading import Barrier

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection

from businessos.core.access.models import UserCompanyAccess
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.modules.catalog.models import Product, ProductVariant
from businessos.modules.catalog.services import (
    create_simple_product,
    create_variable_product,
    update_product,
)
from businessos.modules.party.models import Party
from businessos.modules.party.services import create_party
from businessos.modules.procurement.manifest import MODULE
from businessos.modules.procurement.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseReceipt,
    PurchaseReceiptLine,
)
from businessos.modules.procurement.selectors import (
    confirmed_purchase_orders,
    purchase_order_detail,
    purchase_order_total,
    purchase_orders_for_company,
    purchase_receipt_detail,
    receipts_for_purchase_order,
    received_quantity_for_line,
    remaining_quantity_for_line,
)
from businessos.modules.procurement.services import (
    add_purchase_order_line,
    cancel_purchase_order,
    confirm_purchase_order,
    create_purchase_order,
    receive_purchase_order,
    remove_purchase_order_line,
    update_purchase_order,
    update_purchase_order_line,
)


@pytest.fixture
def supplier(business_context):
    return create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Northwind Supplier",
        is_supplier=True,
    )


@pytest.fixture
def variant(business_context, uom):
    return create_simple_product(
        business_context,
        name="Procurement Service",
        sku="PROCURE-001",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
        purchase_description="Procurement service day",
    ).variants.get()


@pytest.fixture
def draft_order(business_context, supplier, currency):
    return create_purchase_order(
        business_context,
        supplier_id=supplier.id,
        order_date=date(2026, 9, 14),
        currency_id=currency.id,
        notes="Priority supplier",
    )


def _add_line(context, order, variant, *, quantity="10", cost="12.5000"):
    return add_purchase_order_line(
        context,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=Decimal(quantity),
        unit_cost=Decimal(cost),
    )


def _confirm_with_line(context, order, variant, *, quantity="10"):
    line = _add_line(context, order, variant, quantity=quantity)
    confirm_purchase_order(context, order_id=order.id)
    return line


@pytest.mark.django_db
def test_manifest_schema_and_service_boundaries():
    assert MODULE == {
        "code": "procurement",
        "name": "Procurement",
        "version": "0.1.0",
        "depends": ["party", "catalog", "organization", "reference", "access"],
    }
    assert PurchaseOrderLine._meta.get_field("product_variant").related_model is ProductVariant
    assert {field.name for field in PurchaseOrder._meta.fields}.isdisjoint(
        {"warehouse", "stock_quantity", "vendor_bill", "invoice"}
    )
    assert "request" not in signature(receive_purchase_order).parameters
    assert not any(field.name == "stock" for field in Product._meta.fields)


@pytest.mark.django_db
def test_create_order_and_simple_variable_variant_lines(
    business_context, draft_order, variant, uom
):
    first = _add_line(business_context, draft_order, variant, quantity="2.5")
    variable = create_variable_product(
        business_context,
        name="Variable supply",
        variants=[{"sku": "SUP-BLK", "is_default": True}],
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
        purchase_description="Variable supply snapshot",
    ).variants.get()
    second = _add_line(business_context, draft_order, variable)

    assert draft_order.number.startswith("PO-") and len(draft_order.number) == 35
    assert first.product_variant == variant
    assert first.sku_snapshot == "PROCURE-001"
    assert first.name_snapshot == "Procurement Service"
    assert first.description_snapshot == "Procurement service day"
    assert (first.position, second.position) == (1, 2)


@pytest.mark.django_db
def test_supplier_and_variant_scope_activity_and_roles_are_enforced(
    business_context, company, currency, draft_order, variant, uom
):
    customer = create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Customer only",
        is_customer=True,
    )
    with pytest.raises(PermissionDenied, match="active supplier"):
        create_purchase_order(
            business_context,
            supplier_id=customer.id,
            order_date=date.today(),
            currency_id=currency.id,
        )
    supplier = create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Inactive supplier",
        is_supplier=True,
        is_active=False,
    )
    with pytest.raises(PermissionDenied, match="active supplier"):
        create_purchase_order(
            business_context,
            supplier_id=supplier.id,
            order_date=date.today(),
            currency_id=currency.id,
        )
    not_purchasable = create_simple_product(
        business_context,
        name="Sales only",
        sku="SALES-ONLY",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
        is_purchasable=False,
    ).variants.get()
    with pytest.raises(PermissionDenied, match="active purchasable"):
        _add_line(business_context, draft_order, not_purchasable)
    with pytest.raises(ValidationError, match="greater than zero"):
        _add_line(business_context, draft_order, variant, quantity="0")
    with pytest.raises(ValidationError, match="cannot be negative"):
        _add_line(business_context, draft_order, variant, cost="-0.0001")
    assert not PurchaseOrderLine.objects.filter(company=company).exists()


@pytest.mark.django_db
def test_draft_header_and_line_replacement_refresh_snapshots(
    business_context, draft_order, variant, supplier, currency, uom
):
    line = _add_line(business_context, draft_order, variant)
    replacement = create_simple_product(
        business_context,
        name="Replacement supply",
        sku="REPLACE-PO",
        product_type=Product.Type.CONSUMABLE,
        default_uom_id=uom.id,
        purchase_description="Replacement purchase text",
    ).variants.get()
    update_purchase_order(
        business_context,
        order_id=draft_order.id,
        supplier_id=supplier.id,
        order_date=date(2026, 9, 15),
        currency_id=currency.id,
        notes="Updated",
    )
    update_purchase_order_line(
        business_context,
        line_id=line.id,
        product_variant_id=replacement.id,
        quantity=Decimal("3"),
        unit_cost=Decimal("7.25"),
        description="Replacement snapshot",
    )
    line.refresh_from_db()
    draft_order.refresh_from_db()
    assert draft_order.notes == "Updated"
    assert line.product_variant == replacement
    assert line.sku_snapshot == "REPLACE-PO"
    assert line.name_snapshot == "Replacement supply"
    assert line.description_snapshot == "Replacement snapshot"
    assert line.position == 1
    remove_purchase_order_line(business_context, line_id=line.id)
    assert not PurchaseOrderLine.objects.filter(id=line.id).exists()


@pytest.mark.django_db
def test_confirmation_retry_revalidation_and_model_protection(
    business_context, draft_order, variant
):
    with pytest.raises(ValidationError, match="at least one line"):
        confirm_purchase_order(business_context, order_id=draft_order.id)
    line = _add_line(business_context, draft_order, variant)

    draft_order.status = PurchaseOrder.Status.CONFIRMED
    with pytest.raises(ValidationError, match="only change through lifecycle services"):
        draft_order.save()
    first = confirm_purchase_order(business_context, order_id=draft_order.id)
    second = confirm_purchase_order(business_context, order_id=draft_order.id)
    assert first.status == second.status == PurchaseOrder.Status.CONFIRMED
    assert first.confirmed_at == second.confirmed_at

    draft_order.refresh_from_db()
    draft_order.notes = "Bypass"
    with pytest.raises(ValidationError, match="immutable"):
        draft_order.save()
    line.refresh_from_db()
    line.quantity = 20
    with pytest.raises(ValidationError, match="only be changed"):
        line.save()
    with pytest.raises(ValidationError, match="only be removed"):
        line.delete()
    with pytest.raises(ValidationError, match="cannot be deleted"):
        draft_order.delete()


@pytest.mark.django_db
def test_confirmation_revalidates_supplier_variant_and_currency(
    business_context, draft_order, variant, supplier, currency
):
    _add_line(business_context, draft_order, variant)
    supplier.is_active = False
    supplier.save()
    with pytest.raises(PermissionDenied, match="active supplier"):
        confirm_purchase_order(business_context, order_id=draft_order.id)
    supplier.is_active = True
    supplier.save()
    update_product(business_context, product_id=variant.product_id, is_purchasable=False)
    with pytest.raises(PermissionDenied, match="active purchasable"):
        confirm_purchase_order(business_context, order_id=draft_order.id)
    update_product(business_context, product_id=variant.product_id, is_purchasable=True)
    currency.is_active = False
    currency.save()
    with pytest.raises(ValidationError, match="active currency"):
        confirm_purchase_order(business_context, order_id=draft_order.id)


@pytest.mark.django_db
def test_company_unique_order_number_is_enforced(company, supplier, currency, draft_order):
    duplicate = PurchaseOrder(
        company=company,
        number=draft_order.number.lower(),
        supplier=supplier,
        order_date=date.today(),
        currency=currency,
    )
    with pytest.raises(ValidationError, match="already exists"):
        duplicate.save()


@pytest.mark.django_db
def test_draft_and_cancelled_orders_cannot_be_received(
    business_context, draft_order, variant
):
    line = _add_line(business_context, draft_order, variant)
    payload = [{"purchase_order_line_id": line.id, "quantity_received": "1"}]
    with pytest.raises(ValidationError, match="confirmed"):
        receive_purchase_order(
            business_context,
            purchase_order_id=draft_order.id,
            receipt_date=date.today(),
            idempotency_key="draft-receipt",
            lines=payload,
        )
    confirm_purchase_order(business_context, order_id=draft_order.id)
    cancel_purchase_order(business_context, order_id=draft_order.id)
    with pytest.raises(ValidationError, match="confirmed"):
        receive_purchase_order(
            business_context,
            purchase_order_id=draft_order.id,
            receipt_date=date.today(),
            idempotency_key="cancelled-receipt",
            lines=payload,
        )


@pytest.mark.django_db
def test_partial_receipts_idempotency_totals_and_cancellation(
    business_context, draft_order, variant
):
    line = _confirm_with_line(business_context, draft_order, variant, quantity="10")
    payload = [{"purchase_order_line_id": line.id, "quantity_received": "4"}]
    first = receive_purchase_order(
        business_context,
        purchase_order_id=draft_order.id,
        receipt_date=date(2026, 9, 15),
        idempotency_key="receipt-1",
        lines=payload,
    )
    retry = receive_purchase_order(
        business_context,
        purchase_order_id=draft_order.id,
        receipt_date=date(2026, 9, 15),
        idempotency_key="receipt-1",
        lines=payload,
    )
    second = receive_purchase_order(
        business_context,
        purchase_order_id=draft_order.id,
        receipt_date=date(2026, 9, 16),
        idempotency_key="receipt-2",
        lines=[{"purchase_order_line_id": line.id, "quantity_received": "3"}],
    )
    assert retry.id == first.id
    assert first.number.startswith("PR-") and len(first.number) == 35
    assert first.posted_at is not None
    assert PurchaseReceipt.objects.count() == 2
    assert list(receipts_for_purchase_order(
        business_context, purchase_order_id=draft_order.id
    )) == [second, first]
    assert received_quantity_for_line(
        business_context, purchase_order_line_id=line.id
    ) == Decimal("7")
    assert remaining_quantity_for_line(
        business_context, purchase_order_line_id=line.id
    ) == Decimal("3")
    detail_line = purchase_order_detail(business_context, order_id=draft_order.id).lines.get()
    assert detail_line.received_quantity == Decimal("7")
    assert detail_line.remaining_quantity == Decimal("3")
    with pytest.raises(ValidationError, match="cannot be cancelled"):
        cancel_purchase_order(business_context, order_id=draft_order.id)
    with pytest.raises(ValidationError, match="exceeds"):
        receive_purchase_order(
            business_context,
            purchase_order_id=draft_order.id,
            receipt_date=date(2026, 9, 17),
            idempotency_key="receipt-over",
            lines=[{"purchase_order_line_id": line.id, "quantity_received": "4"}],
        )
    assert PurchaseReceipt.objects.count() == 2


@pytest.mark.django_db
def test_receipt_input_validation_conflicting_key_and_atomic_rollback(
    business_context, draft_order, variant
):
    first_line = _confirm_with_line(business_context, draft_order, variant, quantity="5")
    with pytest.raises(ValidationError, match="at least one line"):
        receive_purchase_order(
            business_context,
            purchase_order_id=draft_order.id,
            receipt_date=date.today(),
            idempotency_key="empty",
            lines=[],
        )
    with pytest.raises(ValidationError, match="only once"):
        receive_purchase_order(
            business_context,
            purchase_order_id=draft_order.id,
            receipt_date=date.today(),
            idempotency_key="duplicate",
            lines=[
                {"purchase_order_line_id": first_line.id, "quantity_received": "1"},
                {"purchase_order_line_id": first_line.id, "quantity_received": "1"},
            ],
        )
    with pytest.raises(ValidationError, match="greater than zero"):
        receive_purchase_order(
            business_context,
            purchase_order_id=draft_order.id,
            receipt_date=date.today(),
            idempotency_key="zero",
            lines=[{"purchase_order_line_id": first_line.id, "quantity_received": "0"}],
        )
    receipt = receive_purchase_order(
        business_context,
        purchase_order_id=draft_order.id,
        receipt_date=date(2026, 9, 15),
        idempotency_key="same-key",
        lines=[{"purchase_order_line_id": first_line.id, "quantity_received": "2"}],
    )
    with pytest.raises(ValidationError, match="different Purchase Receipt"):
        receive_purchase_order(
            business_context,
            purchase_order_id=draft_order.id,
            receipt_date=date(2026, 9, 16),
            idempotency_key="same-key",
            lines=[{"purchase_order_line_id": first_line.id, "quantity_received": "2"}],
        )
    assert PurchaseReceipt.objects.count() == 1
    assert PurchaseReceiptLine.objects.filter(purchase_receipt=receipt).count() == 1


@pytest.mark.django_db
def test_receipt_and_lines_are_immutable_and_direct_creation_is_blocked(
    business_context, draft_order, variant
):
    line = _confirm_with_line(business_context, draft_order, variant)
    with pytest.raises(ValidationError, match="receive service"):
        PurchaseReceipt.objects.create(
            company=draft_order.company,
            number="PR-DIRECT",
            purchase_order=draft_order,
            receipt_date=date.today(),
            idempotency_key="direct",
            posted_at=draft_order.confirmed_at,
        )
    receipt = receive_purchase_order(
        business_context,
        purchase_order_id=draft_order.id,
        receipt_date=date.today(),
        idempotency_key="immutable",
        lines=[{"purchase_order_line_id": line.id, "quantity_received": "1"}],
    )
    receipt.receipt_date = date(2026, 9, 20)
    with pytest.raises(ValidationError, match="immutable"):
        receipt.save()
    receipt_line = receipt.lines.get()
    receipt_line.quantity_received = 2
    with pytest.raises(ValidationError, match="immutable"):
        receipt_line.save()
    with pytest.raises(ValidationError, match="cannot be deleted"):
        receipt.delete()
    with pytest.raises(ValidationError, match="cannot be deleted"):
        receipt_line.delete()
    assert purchase_receipt_detail(business_context, receipt_id=receipt.id).id == receipt.id


@pytest.mark.django_db
def test_cancel_confirmed_without_receipts_and_retry_is_safe(
    business_context, draft_order, variant
):
    with pytest.raises(ValidationError, match="Only a confirmed"):
        cancel_purchase_order(business_context, order_id=draft_order.id)
    _confirm_with_line(business_context, draft_order, variant)
    cancelled = cancel_purchase_order(business_context, order_id=draft_order.id)
    retry = cancel_purchase_order(business_context, order_id=draft_order.id)
    assert cancelled.status == retry.status == PurchaseOrder.Status.CANCELLED
    assert cancelled.confirmed_at == retry.confirmed_at
    with pytest.raises(ValidationError, match="cancelled"):
        confirm_purchase_order(business_context, order_id=draft_order.id)


@pytest.mark.django_db
def test_company_isolation_for_relationships_services_and_selectors(
    business_context, company, currency, draft_order, variant, uom
):
    other_company = Company.objects.create(
        code="OTHER", name="Other Company", base_currency=currency
    )
    other_user = get_user_model().objects.create_user("other-procurement@example.com", "password")
    UserCompanyAccess.objects.create(user=other_user, company=other_company)
    other_context = BusinessContext(actor_id=other_user.id, company_id=other_company.id)
    other_supplier = create_party(
        other_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Other Supplier",
        is_supplier=True,
    )
    other_variant = create_simple_product(
        other_context,
        name="Other supply",
        sku="OTHER-SUPPLY",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    ).variants.get()
    with pytest.raises(PermissionDenied):
        create_purchase_order(
            business_context,
            supplier_id=other_supplier.id,
            order_date=date.today(),
            currency_id=currency.id,
        )
    with pytest.raises(PermissionDenied):
        _add_line(business_context, draft_order, other_variant)
    with pytest.raises(PermissionDenied):
        update_purchase_order(other_context, order_id=draft_order.id, notes="Cross company")
    _confirm_with_line(business_context, draft_order, variant)
    other_order = create_purchase_order(
        other_context,
        supplier_id=other_supplier.id,
        order_date=date.today(),
        currency_id=currency.id,
    )
    other_line = _confirm_with_line(other_context, other_order, other_variant)
    with pytest.raises(PermissionDenied, match="must belong"):
        receive_purchase_order(
            business_context,
            purchase_order_id=draft_order.id,
            receipt_date=date.today(),
            idempotency_key="cross-company-line",
            lines=[{"purchase_order_line_id": other_line.id, "quantity_received": "1"}],
        )
    with pytest.raises(PurchaseOrder.DoesNotExist):
        purchase_order_detail(other_context, order_id=draft_order.id)
    assert list(purchase_orders_for_company(other_context)) == [other_order]
    assert draft_order.company == company


@pytest.mark.django_db
def test_failed_receipt_rolls_back_header_lines_and_received_totals(
    business_context, draft_order, variant, uom, monkeypatch
):
    first_line = _add_line(business_context, draft_order, variant, quantity="5")
    second_variant = create_simple_product(
        business_context,
        name="Second supply",
        sku="SECOND-SUPPLY",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    ).variants.get()
    second_line = _add_line(
        business_context, draft_order, second_variant, quantity="5"
    )
    confirm_purchase_order(business_context, order_id=draft_order.id)
    original_save = PurchaseReceiptLine.save
    calls = 0

    def fail_second_line(instance, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated receipt-line persistence failure")
        return original_save(instance, *args, **kwargs)

    monkeypatch.setattr(PurchaseReceiptLine, "save", fail_second_line)
    with pytest.raises(RuntimeError, match="simulated"):
        receive_purchase_order(
            business_context,
            purchase_order_id=draft_order.id,
            receipt_date=date.today(),
            idempotency_key="rollback-receipt",
            lines=[
                {"purchase_order_line_id": first_line.id, "quantity_received": "2"},
                {"purchase_order_line_id": second_line.id, "quantity_received": "2"},
            ],
        )
    assert not PurchaseReceipt.objects.exists()
    assert not PurchaseReceiptLine.objects.exists()
    assert received_quantity_for_line(
        business_context, purchase_order_line_id=first_line.id
    ) == Decimal("0")
    assert received_quantity_for_line(
        business_context, purchase_order_line_id=second_line.id
    ) == Decimal("0")


@pytest.mark.django_db
def test_selectors_derive_order_total_and_status(
    business_context, draft_order, variant
):
    _add_line(business_context, draft_order, variant, quantity="2", cost="10")
    _add_line(business_context, draft_order, variant, quantity="0.5", cost="8")
    assert purchase_order_total(business_context, order_id=draft_order.id) == Decimal("24")
    assert list(purchase_orders_for_company(business_context, search="northwind")) == [draft_order]
    assert list(confirmed_purchase_orders(business_context)) == []
    confirm_purchase_order(business_context, order_id=draft_order.id)
    assert list(confirmed_purchase_orders(business_context)) == [draft_order]


@pytest.mark.django_db(transaction=True)
def test_concurrent_confirmation_serializes(business_context, draft_order, variant):
    if connection.vendor != "postgresql":
        pytest.skip("Purchase Order confirmation locking requires PostgreSQL.")
    _add_line(business_context, draft_order, variant)
    start = Barrier(2)

    def confirm():
        close_old_connections()
        try:
            start.wait(timeout=5)
            return confirm_purchase_order(
                business_context, order_id=draft_order.id
            ).confirmed_at
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        timestamps = [future.result(timeout=10) for future in [
            executor.submit(confirm), executor.submit(confirm)
        ]]
    draft_order.refresh_from_db()
    assert timestamps == [draft_order.confirmed_at, draft_order.confirmed_at]


@pytest.mark.django_db(transaction=True)
def test_concurrent_line_positions_are_unique(business_context, draft_order, variant):
    if connection.vendor != "postgresql":
        pytest.skip("Purchase Order line-position locking requires PostgreSQL.")
    start = Barrier(2)

    def add():
        close_old_connections()
        try:
            start.wait(timeout=5)
            return _add_line(business_context, draft_order, variant).position
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        positions = [future.result(timeout=10) for future in [
            executor.submit(add), executor.submit(add)
        ]]
    assert sorted(positions) == [1, 2]


@pytest.mark.django_db(transaction=True)
def test_concurrent_over_receipt_is_serialized(business_context, draft_order, variant):
    if connection.vendor != "postgresql":
        pytest.skip("Purchase Receipt locking requires PostgreSQL.")
    line = _confirm_with_line(business_context, draft_order, variant, quantity="10")
    start = Barrier(2)

    def receive(key):
        close_old_connections()
        try:
            start.wait(timeout=5)
            return receive_purchase_order(
                business_context,
                purchase_order_id=draft_order.id,
                receipt_date=date.today(),
                idempotency_key=key,
                lines=[{"purchase_order_line_id": line.id, "quantity_received": "7"}],
            )
        except Exception as error:
            return error
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [future.result(timeout=10) for future in [
            executor.submit(receive, "race-a"), executor.submit(receive, "race-b")
        ]]
    assert sum(isinstance(result, PurchaseReceipt) for result in results) == 1
    assert sum(isinstance(result, ValidationError) for result in results) == 1
    assert received_quantity_for_line(
        business_context, purchase_order_line_id=line.id
    ) == Decimal("7")
