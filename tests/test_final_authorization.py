"""PH2-FINAL-AUD-1: selected-alias authority at the last mutation boundary.

Workers use independent connections and actual pg_blocking_pids observations;
poll delays are not used as evidence that a race occurred.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Event
from time import monotonic, sleep
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import connections
from django.utils import timezone

from businessos.core.access import policies
from businessos.core.access import services as access_services
from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserCompanyAccess,
    UserRoleAssignment,
)
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import (
    business_atomic_context,
    current_database_alias,
    database_execution,
)
from businessos.core.modules.services import register_manifest
from businessos.core.organization.models import Company, Warehouse
from businessos.core.reference.models import Country, Currency, Language, UnitOfMeasure
from businessos.modules.accounting import services as accounting
from businessos.modules.accounting.manifest import MODULE as ACCOUNTING
from businessos.modules.accounting.models import Account, Journal, JournalEntry, JournalEntryLine
from businessos.modules.billing import services as billing
from businessos.modules.billing.manifest import MODULE as BILLING
from businessos.modules.billing.models import Invoice, InvoiceLine
from businessos.modules.catalog.services import create_simple_product
from businessos.modules.inventory import services as inventory
from businessos.modules.inventory.manifest import MODULE as INVENTORY
from businessos.modules.inventory.models import StockMovement, StockMovementLine
from businessos.modules.inventory.selectors import stock_balance
from businessos.modules.party.models import Party
from businessos.modules.payments import services as payments
from businessos.modules.payments.manifest import MODULE as PAYMENTS
from businessos.modules.payments.models import Payment, PaymentMethod
from businessos.modules.procurement import services as procurement
from businessos.modules.procurement.manifest import MODULE as PROCUREMENT
from businessos.modules.procurement.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseReceipt,
    PurchaseReceiptLine,
)
from businessos.modules.sales import services as sales
from businessos.modules.sales.manifest import MODULE as SALES
from businessos.modules.sales.models import SalesOrder, SalesOrderLine

pytestmark = pytest.mark.django_db(transaction=True)

OWNERS = (sales, procurement, inventory, billing, payments, accounting)
MODELS = (
    SalesOrder,
    SalesOrderLine,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseReceipt,
    PurchaseReceiptLine,
    StockMovement,
    StockMovementLine,
    Invoice,
    InvoiceLine,
    PaymentMethod,
    Payment,
    Account,
    Journal,
    JournalEntry,
    JournalEntryLine,
)
DATE = date(2026, 10, 13)


@pytest.fixture
def world(operator, company, business_context, currency, uom, warehouse):
    return make_world(operator, company, business_context, currency, uom, warehouse)


def make_world(operator, company, business_context, currency, uom, warehouse):
    access_services.register_core_permissions()
    for manifest in (SALES, PROCUREMENT, INVENTORY, BILLING, PAYMENTS, ACCOUNTING):
        register_manifest(manifest)
    role = Role.objects.create(company=company, code="FINAL-AUTH", name="Synthetic authority")
    for permission in Permission.objects.all():
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    party = Party.objects.create(
        company=company,
        party_type="person",
        display_name="Synthetic person",
        is_customer=True,
        is_supplier=True,
    )
    product = create_simple_product(
        business_context,
        name="Synthetic item",
        sku="AUTH-1",
        product_type="stockable",
        default_uom_id=uom.pk,
    )
    variant = product.variants.get()
    order = sales.create_sales_order(
        business_context,
        customer_id=party.pk,
        order_date=DATE,
        currency_id=currency.pk,
    )
    sales_line = sales.add_sales_order_line(
        business_context,
        order_id=order.pk,
        product_variant_id=variant.pk,
        quantity="2",
        unit_price="10",
    )
    purchase = procurement.create_purchase_order(
        business_context,
        supplier_id=party.pk,
        order_date=DATE,
        currency_id=currency.pk,
    )
    purchase_line = procurement.add_purchase_order_line(
        business_context,
        order_id=purchase.pk,
        product_variant_id=variant.pk,
        quantity="2",
        unit_cost="10",
    )
    movement = inventory.create_stock_movement(
        business_context,
        movement_type="receipt",
        effective_at=timezone.now(),
    )
    movement_line = inventory.add_stock_movement_line(
        business_context,
        movement_id=movement.pk,
        product_variant_id=variant.pk,
        quantity="2",
        destination_warehouse_id=warehouse.pk,
    )
    invoice = billing.create_invoice(
        business_context,
        bill_to_party_id=party.pk,
        currency_id=currency.pk,
        invoice_date=DATE,
    )
    invoice_line = billing.add_invoice_line(
        business_context,
        invoice.pk,
        description="Synthetic",
        quantity="2",
        unit_price="10",
    )
    method = payments.create_payment_method(business_context, code="CASH", name="Cash")
    journal = accounting.create_journal(business_context, code="GEN", name="General")
    account = accounting.create_account(
        business_context,
        code="CASH",
        name="Cash",
        type="ASSET",
    )
    entry = accounting.create_journal_entry(
        business_context, journal_id=journal.pk, entry_date=DATE
    )
    entry_lines = [
        accounting.add_journal_entry_line(
            business_context,
            entry.pk,
            account_id=account.pk,
            party_id=party.pk,
            debit=debit,
            credit=credit,
        )
        for debit, credit in (("20", "0"), ("0", "20"))
    ]
    return SimpleNamespace(
        actor=operator,
        company=company,
        context=business_context,
        currency=currency,
        uom=uom,
        role=role,
        party=party,
        variant=variant,
        warehouse=warehouse,
        order=order,
        sales_line=sales_line,
        purchase=purchase,
        purchase_line=purchase_line,
        movement=movement,
        movement_line=movement_line,
        invoice=invoice,
        invoice_line=invoice_line,
        method=method,
        journal=journal,
        account=account,
        entry=entry,
        entry_line=entry_lines[0],
    )


def payment_args(w):
    return dict(
        payer_party_id=w.party.pk,
        currency_id=w.currency.pk,
        amount="20",
        payment_method_id=w.method.pk,
        payment_date=DATE,
        idempotency_key="final-auth-receipt",
    )


def receipt_args(w):
    return dict(
        purchase_order_id=w.purchase.pk,
        receipt_date=DATE,
        idempotency_key="final-auth-receive",
        lines=[dict(purchase_order_line_id=w.purchase_line.pk, quantity_received="1")],
    )


def operations(w):
    c = w.context
    v = w.variant.pk
    return {
        "sales.create": lambda: sales.create_sales_order(
            c, customer_id=w.party.pk, order_date=DATE, currency_id=w.currency.pk
        ),
        "sales.update": lambda: sales.update_sales_order(c, order_id=w.order.pk, notes="Changed"),
        "sales.add": lambda: sales.add_sales_order_line(
            c, order_id=w.order.pk, product_variant_id=v, quantity="1", unit_price="10"
        ),
        "sales.line": lambda: sales.update_sales_order_line(
            c,
            line_id=w.sales_line.pk,
            product_variant_id=v,
            quantity="1",
            unit_price="10",
            description="Changed",
        ),
        "sales.remove": lambda: sales.remove_sales_order_line(c, line_id=w.sales_line.pk),
        "sales.confirm": lambda: sales.confirm_sales_order(c, order_id=w.order.pk),
        "sales.cancel": lambda: sales.cancel_sales_order(c, order_id=w.order.pk),
        "procurement.create": lambda: procurement.create_purchase_order(
            c, supplier_id=w.party.pk, order_date=DATE, currency_id=w.currency.pk
        ),
        "procurement.update": lambda: procurement.update_purchase_order(
            c, order_id=w.purchase.pk, notes="Changed"
        ),
        "procurement.add": lambda: procurement.add_purchase_order_line(
            c, order_id=w.purchase.pk, product_variant_id=v, quantity="1", unit_cost="10"
        ),
        "procurement.line": lambda: procurement.update_purchase_order_line(
            c,
            line_id=w.purchase_line.pk,
            product_variant_id=v,
            quantity="1",
            unit_cost="10",
            description="Changed",
        ),
        "procurement.remove": lambda: procurement.remove_purchase_order_line(
            c, line_id=w.purchase_line.pk
        ),
        "procurement.confirm": lambda: procurement.confirm_purchase_order(
            c, order_id=w.purchase.pk
        ),
        "procurement.cancel": lambda: procurement.cancel_purchase_order(c, order_id=w.purchase.pk),
        "procurement.receive": lambda: procurement.receive_purchase_order(c, **receipt_args(w)),
        "inventory.create": lambda: inventory.create_stock_movement(
            c, movement_type="receipt", effective_at=timezone.now()
        ),
        "inventory.update": lambda: inventory.update_stock_movement(
            c, movement_id=w.movement.pk, notes="Changed"
        ),
        "inventory.add": lambda: inventory.add_stock_movement_line(
            c,
            movement_id=w.movement.pk,
            product_variant_id=v,
            quantity="1",
            destination_warehouse_id=w.warehouse.pk,
        ),
        "inventory.line": lambda: inventory.update_stock_movement_line(
            c,
            movement_id=w.movement.pk,
            line_id=w.movement_line.pk,
            product_variant_id=v,
            quantity="1",
            destination_warehouse_id=w.warehouse.pk,
        ),
        "inventory.remove": lambda: inventory.remove_stock_movement_line(
            c, movement_id=w.movement.pk, line_id=w.movement_line.pk
        ),
        "inventory.post": lambda: inventory.post_stock_movement(c, movement_id=w.movement.pk),
        "billing.create": lambda: billing.create_invoice(
            c, bill_to_party_id=w.party.pk, currency_id=w.currency.pk, invoice_date=DATE
        ),
        "billing.update": lambda: billing.update_invoice(c, w.invoice.pk, notes="Changed"),
        "billing.add": lambda: billing.add_invoice_line(
            c, w.invoice.pk, description="Changed", quantity="1", unit_price="10"
        ),
        "billing.line": lambda: billing.update_invoice_line(
            c, w.invoice.pk, w.invoice_line.pk, description="Changed"
        ),
        "billing.remove": lambda: billing.remove_invoice_line(c, w.invoice.pk, w.invoice_line.pk),
        "billing.issue": lambda: billing.issue_invoice(c, w.invoice.pk),
        "payments.create": lambda: payments.create_payment_method(c, code="BANK", name="Bank"),
        "payments.update": lambda: payments.update_payment_method(
            c, payment_method_id=w.method.pk, name="Changed"
        ),
        "payments.active": lambda: payments.set_payment_method_active(
            c, payment_method_id=w.method.pk, is_active=False
        ),
        "payments.record": lambda: payments.record_payment(c, **payment_args(w)),
        "accounting.account_create": lambda: accounting.create_account(
            c, code="BANK", name="Bank", type="ASSET"
        ),
        "accounting.account_update": lambda: accounting.update_account(
            c, w.account.pk, name="Changed"
        ),
        "accounting.journal_create": lambda: accounting.create_journal(c, code="BANK", name="Bank"),
        "accounting.journal_update": lambda: accounting.update_journal(
            c, w.journal.pk, name="Changed"
        ),
        "accounting.create": lambda: accounting.create_journal_entry(
            c, journal_id=w.journal.pk, entry_date=DATE
        ),
        "accounting.update": lambda: accounting.update_journal_entry(c, w.entry.pk, memo="Changed"),
        "accounting.add": lambda: accounting.add_journal_entry_line(
            c, w.entry.pk, account_id=w.account.pk, party_id=w.party.pk, debit="1", credit="0"
        ),
        "accounting.line": lambda: accounting.update_journal_entry_line(
            c, w.entry.pk, w.entry_line.pk, description="Changed"
        ),
        "accounting.remove": lambda: accounting.remove_journal_entry_line(
            c, w.entry.pk, w.entry_line.pk
        ),
        "accounting.post": lambda: accounting.post_journal_entry(c, w.entry.pk),
    }


OPERATION_NAMES = (
    "sales.create sales.update sales.add sales.line sales.remove sales.confirm sales.cancel "
    "procurement.create procurement.update procurement.add procurement.line procurement.remove "
    "procurement.confirm procurement.cancel procurement.receive "
    "inventory.create inventory.update inventory.add inventory.line inventory.remove "
    "inventory.post "
    "billing.create billing.update billing.add billing.line billing.remove billing.issue "
    "payments.create payments.update payments.active payments.record "
    "accounting.account_create accounting.account_update accounting.journal_create "
    "accounting.journal_update accounting.create accounting.update accounting.add accounting.line "
    "accounting.remove accounting.post"
).split()


def prepare(w, name):
    if name == "sales.cancel":
        sales.confirm_sales_order(w.context, order_id=w.order.pk)
    if name in {"procurement.cancel", "procurement.receive"}:
        procurement.confirm_purchase_order(w.context, order_id=w.purchase.pk)


def state():
    return {
        model._meta.label: list(model.objects.order_by("pk").values())
        for model in (*MODELS, AuditEntry)
    }


@pytest.mark.parametrize("name", OPERATION_NAMES)
def test_every_public_mutation_rechecks_at_final_boundary(world, monkeypatch, name):
    prepare(world, name)
    before = state()
    calls = []
    real = policies.require_final_permission

    def revoke_then_check(context, permission):
        calls.append(permission)
        get_user_model().objects.filter(pk=context.actor_id).update(is_active=False)
        return real(context, permission)

    owner = next(
        module for module in OWNERS if module.__name__.split(".")[-2] == name.split(".")[0]
    )
    monkeypatch.setattr(owner, "require_final_permission", revoke_then_check)
    with pytest.raises(PermissionDenied):
        operations(world)[name]()
    assert len(calls) == 1
    assert state() == before


def pg_only():
    if connections[current_database_alias()].vendor != "postgresql":
        pytest.skip("PostgreSQL-only final-authority row-lock/blocking coordination.")


def worker(alias, operation, ready, pid):
    try:
        with database_execution(alias):
            with connections[alias].cursor() as cursor:
                cursor.execute("SET statement_timeout='20s'")
                cursor.execute("SELECT pg_backend_pid()")
                pid.append(cursor.fetchone()[0])
            ready.set()
            return operation()
    finally:
        connections.close_all()


def backend_pid():
    with connections[current_database_alias()].cursor() as cursor:
        cursor.execute("SELECT pg_backend_pid()")
        return cursor.fetchone()[0]


def blocked(worker_pid, blocker_pid):
    deadline = monotonic() + 10
    with connections[current_database_alias()].cursor() as cursor:
        while monotonic() < deadline:
            cursor.execute("SELECT %s=ANY(pg_blocking_pids(%s))", [blocker_pid, worker_pid])
            if cursor.fetchone()[0]:
                return
            sleep(0.01)  # Observe the database lock graph, not elapsed-time ordering.
    pytest.fail("Expected PostgreSQL lock wait was not observed.")


def retire(w, kind, permission):
    if kind == "actor":
        get_user_model().objects.filter(pk=w.actor.pk).update(is_active=False)
    elif kind == "permission":
        Permission.objects.filter(code=permission).update(is_active=False)
    elif kind == "role_inactive":
        Role.objects.filter(pk=w.role.pk).update(is_active=False)
    else:
        raise AssertionError(kind)


CASES = (
    ("sales.create", "actor", "currency", sales.CREATE_ORDERS),
    ("procurement.create", "actor", "currency", procurement.CREATE_ORDERS),
    ("inventory.add", "actor", "uom", inventory.UPDATE_MOVEMENTS),
    ("sales.confirm", "actor", "order", sales.CONFIRM_ORDERS),
    ("procurement.confirm", "actor", "purchase", procurement.CONFIRM_ORDERS),
    ("inventory.post", "actor", "movement", inventory.POST_MOVEMENTS),
    ("billing.issue", "actor", "currency", billing.ISSUE_INVOICES),
    ("payments.record", "actor", "currency", payments.RECORD_PAYMENTS),
    ("payments.record", "permission", "currency", payments.RECORD_PAYMENTS),
    ("accounting.post", "permission", "journal", accounting.POST_ENTRIES),
    ("accounting.post", "actor", "party", accounting.POST_ENTRIES),
)


@pytest.mark.parametrize("name,kind,reference,permission", CASES)
def test_original_counterexample_denies_after_domain_wait(world, name, kind, reference, permission):
    pg_only()
    before = state()
    ready, pid = Event(), []
    row = getattr(world, reference)
    alias = current_database_alias()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            type(row).objects.select_for_update().get(pk=row.pk)
            blocker = backend_pid()
            future = pool.submit(worker, alias, operations(world)[name], ready, pid)
            assert ready.wait(10)
            blocked(pid[0], blocker)
            retire(world, kind, permission)
        with pytest.raises(PermissionDenied):
            future.result(15)
    assert state() == before
    assert (
        stock_balance(
            world.context
            if kind != "actor"
            else BusinessContext(
                actor_id=get_user_model()
                .objects.create_superuser("balance@example.com", "test-only")
                .pk,
                company_id=world.company.pk,
            ),
            product_variant_id=world.variant.pk,
            warehouse_id=world.warehouse.pk,
        )
        == 0
    )


@pytest.mark.parametrize(
    "name,reference,permission",
    [
        ("sales.confirm", "order", sales.CONFIRM_ORDERS),
        ("procurement.confirm", "purchase", procurement.CONFIRM_ORDERS),
        ("inventory.post", "movement", inventory.POST_MOVEMENTS),
        ("billing.issue", "currency", billing.ISSUE_INVOICES),
        ("payments.record", "currency", payments.RECORD_PAYMENTS),
        ("accounting.post", "journal", accounting.POST_ENTRIES),
    ],
)
@pytest.mark.parametrize("kind", ["permission", "role_inactive"])
def test_global_authority_changes_during_domain_wait(world, name, reference, permission, kind):
    pg_only()
    before = state()
    row = getattr(world, reference)
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            type(row).objects.select_for_update().get(pk=row.pk)
            blocker = backend_pid()
            future = pool.submit(
                worker, current_database_alias(), operations(world)[name], ready, pid
            )
            assert ready.wait(10)
            blocked(pid[0], blocker)
            retire(world, kind, permission)
        with pytest.raises(PermissionDenied):
            future.result(15)
    assert state() == before


def test_cross_company_public_billing_currency_contention(world):
    pg_only()
    other = Company.objects.create(
        code="OTHER",
        name="Other synthetic",
        base_currency=world.currency,
        country=world.company.country,
        default_language=world.company.default_language,
    )
    actor = get_user_model().objects.create_superuser("other@example.com", "test-only")
    context = BusinessContext(actor_id=actor.pk, company_id=other.pk)
    party = Party.objects.create(company=other, party_type="person", display_name="Other person")
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            invoice = billing.create_invoice(
                context, bill_to_party_id=party.pk, currency_id=world.currency.pk
            )
            blocker = backend_pid()
            future = pool.submit(
                worker, current_database_alias(), operations(world)["payments.record"], ready, pid
            )
            assert ready.wait(10)
            blocked(pid[0], blocker)
            retire(world, "actor", payments.RECORD_PAYMENTS)
        with pytest.raises(PermissionDenied):
            future.result(15)
    assert Invoice.objects.filter(pk=invoice.pk).exists()
    assert Payment.objects.count() == 0
    assert not AuditEntry.objects.filter(action="payments.payment.recorded").exists()


@pytest.mark.parametrize("kind", ["actor", "permission", "role_inactive"])
@pytest.mark.parametrize(
    "name,permission,action",
    [
        ("sales.confirm", sales.CONFIRM_ORDERS, "sales.order.confirmed"),
        ("procurement.confirm", procurement.CONFIRM_ORDERS, "procurement.order.confirmed"),
        ("inventory.post", inventory.POST_MOVEMENTS, "inventory.movement.posted"),
        ("billing.issue", billing.ISSUE_INVOICES, "billing.invoice.issued"),
        ("payments.record", payments.RECORD_PAYMENTS, "payments.payment.recorded"),
        ("accounting.post", accounting.POST_ENTRIES, "accounting.entry.posted"),
    ],
)
def test_operation_wins_final_authority_retirement_waits(
    world, monkeypatch, kind, name, permission, action
):
    pg_only()
    guarded, release = Event(), Event()
    real = policies.require_final_permission
    operation_pid = []

    def pause_after_real_guard(context, permission):
        result = real(context, permission)
        operation_pid.append(backend_pid())
        guarded.set()
        assert release.wait(15)
        return result

    owner = next(
        module for module in OWNERS if module.__name__.split(".")[-2] == name.split(".")[0]
    )
    monkeypatch.setattr(owner, "require_final_permission", pause_after_real_guard)
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=2) as pool:
        effect = pool.submit(worker, current_database_alias(), operations(world)[name], Event(), [])
        try:
            assert guarded.wait(10)
            retirement = pool.submit(
                worker,
                current_database_alias(),
                lambda: retire(world, kind, permission),
                ready,
                pid,
            )
            assert ready.wait(10)
            blocked(pid[0], operation_pid[0])
        finally:
            release.set()
        result = effect.result(15)
        retirement.result(15)
    assert type(result).objects.filter(pk=result.pk).count() == 1
    assert AuditEntry.objects.filter(action=action).count() == 1


@pytest.mark.parametrize(
    "kind", ["role", "link", "company_access", "company", "branch", "warehouse"]
)
def test_company_serialized_authority_recheck(world, kind):
    pg_only()
    admin = get_user_model().objects.create_superuser("admin@example.com", "test-only")
    admin_context = BusinessContext(actor_id=admin.pk, company_id=world.company.pk)
    if kind in {"branch", "warehouse"}:
        access_services.grant_branch_access(
            admin_context, user_id=world.actor.pk, branch_id=world.warehouse.branch_id
        )
        access_services.grant_warehouse_access(
            admin_context, user_id=world.actor.pk, warehouse_id=world.warehouse.pk
        )
        world.context = BusinessContext(
            actor_id=world.actor.pk,
            company_id=world.company.pk,
            branch_id=world.warehouse.branch_id,
            warehouse_id=world.warehouse.pk,
        )
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            Company.objects.select_for_update().get(pk=world.company.pk)
            blocker = backend_pid()
            future = pool.submit(
                worker, current_database_alias(), operations(world)["sales.confirm"], ready, pid
            )
            assert ready.wait(10)
            blocked(pid[0], blocker)
            if kind == "role":
                access_services.revoke_role(
                    admin_context, user_id=world.actor.pk, role_id=world.role.pk
                )
            elif kind == "link":
                access_services.revoke_role_permission(
                    admin_context, role_id=world.role.pk, permission_code=sales.CONFIRM_ORDERS
                )
            elif kind == "company_access":
                access_services.revoke_company_access(admin_context, user_id=world.actor.pk)
            elif kind == "company":
                Company.objects.filter(pk=world.company.pk).update(is_active=False)
            elif kind == "branch":
                access_services.revoke_branch_access(
                    admin_context, user_id=world.actor.pk, branch_id=world.warehouse.branch_id
                )
            else:
                access_services.revoke_warehouse_access(
                    admin_context, user_id=world.actor.pk, warehouse_id=world.warehouse.pk
                )
        with pytest.raises(PermissionDenied):
            future.result(15)
    world.order.refresh_from_db()
    assert world.order.status == "draft"
    assert not AuditEntry.objects.filter(action="sales.order.confirmed").exists()


@pytest.mark.parametrize(
    "name",
    [
        "sales.confirm",
        "sales.cancel",
        "procurement.confirm",
        "procurement.cancel",
        "procurement.receive",
        "inventory.post",
        "billing.issue",
        "payments.record",
        "accounting.post",
    ],
)
def test_successful_retry_rechecks_without_duplicate_audit(world, monkeypatch, name):
    prepare(world, name)
    operation = operations(world)[name]
    first = operation()
    before = state()
    calls = []
    real = policies.require_final_permission

    def observe(context, permission):
        calls.append(permission)
        return real(context, permission)

    owner = next(
        module for module in OWNERS if module.__name__.split(".")[-2] == name.split(".")[0]
    )
    monkeypatch.setattr(owner, "require_final_permission", observe)
    assert operation().pk == first.pk
    assert len(calls) == 1
    assert state() == before
    get_user_model().objects.filter(pk=world.actor.pk).update(is_active=False)
    with pytest.raises(PermissionDenied):
        operation()
    assert state() == before


def test_core_final_guard_requires_transaction(world):
    with pytest.raises(RuntimeError, match="transaction"):
        policies.require_final_permission(world.context, sales.CONFIRM_ORDERS)


@pytest.mark.parametrize(
    "name,permission",
    [
        ("sales.confirm", sales.CONFIRM_ORDERS),
        ("sales.cancel", sales.CANCEL_ORDERS),
        ("procurement.confirm", procurement.CONFIRM_ORDERS),
        ("procurement.cancel", procurement.CANCEL_ORDERS),
        ("procurement.receive", procurement.RECEIVE_ORDERS),
        ("inventory.post", inventory.POST_MOVEMENTS),
        ("billing.issue", billing.ISSUE_INVOICES),
        ("payments.record", payments.RECORD_PAYMENTS),
        ("accounting.post", accounting.POST_ENTRIES),
    ],
)
@pytest.mark.parametrize("kind", ["actor", "permission"])
def test_matching_retry_denies_authority_change_during_historical_row_wait(
    world, name, permission, kind
):
    pg_only()
    prepare(world, name)
    operation = operations(world)[name]
    first = operation()
    row = world.purchase if name == "procurement.receive" else first
    before = state()
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            type(row).objects.select_for_update().get(pk=row.pk)
            blocker = backend_pid()
            future = pool.submit(worker, current_database_alias(), operation, ready, pid)
            assert ready.wait(10)
            blocked(pid[0], blocker)
            retire(world, kind, permission)
        with pytest.raises(PermissionDenied):
            future.result(15)
    assert state() == before


def test_same_actor_permission_share_locks_allow_other_company_guard(world):
    pg_only()
    other = Company.objects.create(
        code="SHARED",
        name="Other synthetic",
        base_currency=world.currency,
        country=world.company.country,
        default_language=world.company.default_language,
    )
    UserCompanyAccess.objects.create(user=world.actor, company=other)
    role = Role.objects.create(company=other, code="SHARED", name="Shared actor role")
    RolePermission.objects.create(
        role=role, permission=Permission.objects.get(code=sales.CONFIRM_ORDERS)
    )
    UserRoleAssignment.objects.create(user=world.actor, company=other, role=role)
    context = BusinessContext(actor_id=world.actor.pk, company_id=other.pk)

    def second_guard():
        with business_atomic_context():
            Company.objects.select_for_update().get(pk=other.pk)
            return policies.require_final_permission(context, sales.CONFIRM_ORDERS)

    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            Company.objects.select_for_update().get(pk=world.company.pk)
            policies.require_final_permission(world.context, sales.CONFIRM_ORDERS)
            future = pool.submit(worker, current_database_alias(), second_guard, Event(), [])
            assert future.result(10) == context


@pytest.mark.parametrize("kind", ["actor", "permission", "role_inactive"])
def test_core_guard_rereads_after_its_own_authority_wait(world, kind):
    pg_only()
    model, identity = {
        "actor": (get_user_model(), world.actor.pk),
        "permission": (Permission, Permission.objects.get(code=sales.CONFIRM_ORDERS).pk),
        "role_inactive": (Role, world.role.pk),
    }[kind]
    ready, pid = Event(), []

    def guard():
        with business_atomic_context():
            Company.objects.select_for_update().get(pk=world.company.pk)
            return policies.require_final_permission(world.context, sales.CONFIRM_ORDERS)

    with ThreadPoolExecutor(max_workers=1) as pool:
        with business_atomic_context():
            model.objects.select_for_update().get(pk=identity)
            blocker = backend_pid()
            future = pool.submit(worker, current_database_alias(), guard, ready, pid)
            assert ready.wait(10)
            blocked(pid[0], blocker)
            retire(world, kind, sales.CONFIRM_ORDERS)
        with pytest.raises(PermissionDenied):
            future.result(15)


def test_selected_alias_fresh_bootstrap_and_default_cursor_trap(
    world, monkeypatch, django_db_blocker
):
    """Same actor UUID on two databases cannot borrow the default's activity/grants."""
    pg_only()
    alias = "final_auth_selected"
    database_name = "ph2_auth_alias_" + uuid4().hex
    source_alias = current_database_alias()
    config = dict(connections.databases[source_alias])
    config.update(NAME=database_name, CONN_MAX_AGE=0)
    with connections[source_alias].cursor() as cursor:
        cursor.execute(f"CREATE DATABASE {connections[source_alias].ops.quote_name(database_name)}")
    connections.databases[alias] = config
    try:
        with django_db_blocker.unblock(), database_execution(alias):
            call_command("migrate", database=alias, verbosity=0)
            currency = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
            country = Country.objects.create(code="US", name="United States")
            language = Language.objects.create(code="EN", name="English")
            company = Company.objects.create(
                code="ALIAS",
                name="Synthetic selected",
                base_currency=currency,
                country=country,
                default_language=language,
            )
            uom = UnitOfMeasure.objects.create(code="EA", name="Each", symbol="ea")
            warehouse = Warehouse.objects.create(company=company, code="MAIN", name="Main")
            actor = get_user_model().objects.create_user(
                "selected@example.com",
                "test-only",
                id=world.actor.pk,
            )
            UserCompanyAccess.objects.create(user=actor, company=company)
            context = BusinessContext(actor_id=actor.pk, company_id=company.pk)

            def forbidden_default(*args, **kwargs):
                pytest.fail("Final authority/business operation queried the default database.")

            with monkeypatch.context() as patch:
                patch.setattr(connections[source_alias], "cursor", forbidden_default)
                selected = make_world(actor, company, context, currency, uom, warehouse)
                for name in (
                    "sales.confirm",
                    "procurement.confirm",
                    "inventory.post",
                    "billing.issue",
                    "payments.record",
                    "accounting.post",
                ):
                    result = operations(selected)[name]()
                    assert result._state.db == alias
                    before = state()
                    assert operations(selected)[name]().pk == result.pk
                    assert state() == before
                get_user_model().objects.filter(pk=actor.pk).update(is_active=False)
                with business_atomic_context(), pytest.raises(PermissionDenied):
                    Company.objects.select_for_update().get(pk=company.pk)
                    policies.require_final_permission(context, sales.CONFIRM_ORDERS)
                get_user_model().objects.filter(pk=actor.pk).update(is_active=True)
                Permission.objects.filter(code=payments.RECORD_PAYMENTS).update(is_active=False)
                with pytest.raises(PermissionDenied):
                    operations(selected)["payments.record"]()
                Permission.objects.filter(code=payments.RECORD_PAYMENTS).update(is_active=True)
                # The selected-alias guard also observes a genuine actor retirement race.
                test_core_guard_rereads_after_its_own_authority_wait(selected, "actor")
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
        with connections[source_alias].cursor() as cursor:
            cursor.execute(
                f"DROP DATABASE {connections[source_alias].ops.quote_name(database_name)}"
            )
