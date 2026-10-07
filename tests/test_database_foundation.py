import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from django.contrib.sessions.models import Session
from django.db import connections, router
from django.db.migrations.state import ModelState, StateApps
from django.utils.connection import ConnectionDoesNotExist

from businessos.core.database import (
    business_atomic,
    business_atomic_context,
    current_database_alias,
    database_execution,
)
from businessos.core.database.router import BusinessDatabaseRouter
from businessos.core.reference.models import Currency


@pytest.fixture
def aliases(monkeypatch):
    # Alias-selection tests need no real tenant databases or credentials.
    monkeypatch.setattr(
        "businessos.core.database.execution.connections",
        {"default": None, "alpha": None, "beta": None},
    )


@pytest.fixture
def atomic_calls(monkeypatch):
    calls = []

    @contextmanager
    def atomic(*, using):
        calls.append(("enter", using))
        try:
            yield
        finally:
            calls.append(("exit", using))

    monkeypatch.setattr("businessos.core.database.transactions.transaction.atomic", atomic)
    return calls


def test_default_and_nested_execution_cleanup(aliases):
    assert current_database_alias() == "default"
    with database_execution("alpha"):
        with database_execution("alpha"):
            assert current_database_alias() == "alpha"
        with pytest.raises(RuntimeError), database_execution("beta"):
            assert current_database_alias() == "beta"
            raise RuntimeError("cleanup")
        assert current_database_alias() == "alpha"
    assert current_database_alias() == "default"


@pytest.mark.parametrize("alias", [None, "", 123, "missing"])
def test_invalid_alias_never_silently_falls_back(alias):
    error = ConnectionDoesNotExist if alias == "missing" else ValueError
    with pytest.raises(error), database_execution(alias):
        pytest.fail("Invalid alias entered")
    assert current_database_alias() == "default"


def test_thread_isolation(aliases):
    from threading import Barrier

    barrier = Barrier(2)

    def worker(alias):
        assert current_database_alias() == "default"
        with database_execution(alias):
            barrier.wait(timeout=5)
            return current_database_alias()

    with database_execution("beta"), ThreadPoolExecutor(max_workers=2) as pool:
        alpha = pool.submit(worker, "alpha")
        beta = pool.submit(worker, "beta")
        assert (alpha.result(timeout=5), beta.result(timeout=5)) == ("alpha", "beta")
        assert current_database_alias() == "beta"
    assert current_database_alias() == "default"


def test_async_task_isolation_and_exception_cleanup(aliases):
    async def run():
        ready = asyncio.Event()

        async def worker(alias):
            with database_execution(alias):
                ready.set()
                await asyncio.sleep(0)  # Yield, not timing-dependent coordination.
                assert current_database_alias() == alias
                if alias == "beta":
                    raise RuntimeError("task failure")
                return alias

        results = await asyncio.gather(worker("alpha"), worker("beta"), return_exceptions=True)
        await ready.wait()
        assert results[0] == "alpha"
        assert isinstance(results[1], RuntimeError)
        assert current_database_alias() == "default"

    asyncio.run(run())
    assert current_database_alias() == "default"


def test_decorator_resolves_alias_per_call_and_preserves_metadata(aliases, atomic_calls):
    @business_atomic
    def operation(value):
        """Operation documentation."""
        return value, current_database_alias()

    assert operation.__name__ == "operation"
    assert operation.__doc__ == "Operation documentation."
    assert operation(1) == (1, "default")
    with database_execution("alpha"):
        assert operation(2) == (2, "alpha")
    with database_execution("beta"):
        assert operation(3) == (3, "beta")
    assert atomic_calls[::2] == [("enter", "default"), ("enter", "alpha"), ("enter", "beta")]


def test_context_resolves_alias_at_enter_not_construction(aliases, atomic_calls):
    pending = business_atomic_context()
    with database_execution("alpha"), pending:
        assert current_database_alias() == "alpha"
    assert atomic_calls == [("enter", "alpha"), ("exit", "alpha")]


def test_nested_atomic_pins_alias_and_cleans_up_on_failure(aliases, atomic_calls):
    with pytest.raises(RuntimeError), database_execution("alpha"), business_atomic_context():
        with business_atomic_context():
            assert current_database_alias() == "alpha"
        with pytest.raises(ValueError), database_execution("beta"):
            pytest.fail("Cross-database nested transaction accepted")
        with pytest.raises(ValueError), business_atomic_context(using="beta"):
            pytest.fail("Cross-database explicit atomic accepted")
        raise RuntimeError("rollback")
    assert atomic_calls == [
        ("enter", "alpha"), ("enter", "alpha"), ("exit", "alpha"), ("exit", "alpha")
    ]
    with database_execution("beta"), business_atomic_context():
        assert current_database_alias() == "beta"
    assert current_database_alias() == "default"


def test_explicit_alias_scopes_reads_too(aliases, atomic_calls):
    with business_atomic_context(using="alpha"):
        assert router.db_for_read(Currency) == "alpha"
        assert router.db_for_write(Currency) == "alpha"
    assert current_database_alias() == "default"
    assert atomic_calls == [("enter", "alpha"), ("exit", "alpha")]


def test_async_atomic_decorator_is_rejected():
    async def operation():
        pass

    with pytest.raises(TypeError):
        business_atomic(operation)


def test_router_owned_namespaces_and_conservative_technical_policy(aliases):
    policy = BusinessDatabaseRouter()
    assert router.db_for_read(Currency) == "default"
    assert router.db_for_write(Currency) == "default"
    assert router.db_for_read(Session) == "default"
    with database_execution("alpha"):
        assert Currency.objects.all().db == "alpha"
        assert router.db_for_write(Currency) == "alpha"
        future_model = SimpleNamespace(
            _meta=SimpleNamespace(app_config=SimpleNamespace(name="businessos.modules.future"))
        )
        assert policy.db_for_read(future_model) == "alpha"
        assert policy.db_for_write(future_model) == "alpha"
        assert policy.db_for_read(Session) is None
        assert policy.db_for_write(Session) is None
        assert policy.allow_migrate("alpha", "reference") is None
        assert policy.allow_relation(Currency(), Session()) is None


def test_router_resolves_historical_model_ownership(aliases):
    state_apps = StateApps({}, {("reference", "currency"): ModelState.from_model(Currency)})
    historical_currency = state_apps.get_model("reference", "Currency")
    assert historical_currency._meta.app_config.name == "reference"
    with database_execution("alpha"):
        assert router.db_for_read(historical_currency) == "alpha"
        assert router.db_for_write(historical_currency) == "alpha"


@pytest.mark.django_db(transaction=True)
def test_real_default_transaction_savepoint_and_rollback():
    with business_atomic_context():
        assert connections[current_database_alias()].in_atomic_block
        Currency.objects.create(code="AAA", name="Outer")
        with pytest.raises(RuntimeError), business_atomic_context():
            Currency.objects.create(code="BBB", name="Inner")
            raise RuntimeError("inner rollback")
        assert Currency.objects.filter(code="AAA").exists()
        assert not Currency.objects.filter(code="BBB").exists()
    assert Currency.objects.filter(code="AAA").exists()
    with pytest.raises(RuntimeError), business_atomic_context():
        Currency.objects.create(code="CCC", name="Outer rollback")
        raise RuntimeError("outer rollback")
    assert not Currency.objects.filter(code="CCC").exists()


def test_real_nondefault_orm_and_transaction_alignment(django_db_blocker):
    """One disposable in-memory table, not tenant provisioning or a second runtime DB."""
    alias = "foundation_test"
    config = dict(connections.databases["default"])
    config.update(ENGINE="django.db.backends.sqlite3", NAME=":memory:", OPTIONS={})
    connections.databases[alias] = config
    try:
        with django_db_blocker.unblock(), database_execution(alias):
            connection = connections[alias]
            with connection.schema_editor() as editor:
                editor.create_model(Currency)
            with business_atomic_context():
                currency = Currency.objects.create(code="AAA", name="Alias test")
                assert currency._state.db == alias
                assert connection.in_atomic_block
                with pytest.raises(RuntimeError), business_atomic_context():
                    Currency.objects.create(code="BBB", name="Rollback")
                    raise RuntimeError("rollback")
            assert Currency.objects.count() == 1
            with pytest.raises(RuntimeError), business_atomic_context():
                Currency.objects.create(code="CCC", name="Rollback")
                raise RuntimeError("rollback")
            assert Currency.objects.count() == 1
    finally:
        if alias in connections.databases:
            connections[alias].close()
            del connections[alias]
            del connections.databases[alias]
    assert current_database_alias() == "default"


def test_selected_alias_historical_bootstrap_and_business_flows(django_db_blocker, monkeypatch):
    """Replay unchanged migrations and exercise aggregate/audit writes off default."""
    from datetime import date

    from django.contrib.auth import get_user_model
    from django.core.management import call_command
    from django.db.migrations.executor import MigrationExecutor
    from django.utils import timezone

    from businessos.core.access.models import Permission, UserCompanyAccess
    from businessos.core.audit.models import AuditEntry
    from businessos.core.common.context import BusinessContext
    from businessos.core.modules.models import BusinessModule
    from businessos.core.organization.models import Branch, Company, Warehouse
    from businessos.modules.catalog.models import ProductVariant
    from businessos.modules.inventory.selectors import stock_balance
    from businessos.modules.inventory.services import (
        add_stock_movement_line,
        create_stock_movement,
        post_stock_movement,
    )
    from businessos.modules.party.models import Party
    from businessos.modules.procurement.services import (
        add_purchase_order_line,
        confirm_purchase_order,
        create_purchase_order,
        receive_purchase_order,
    )
    from businessos.modules.sales.services import (
        add_sales_order_line,
        confirm_sales_order,
        create_sales_order,
    )

    alias = "foundation_bootstrap_test"
    config = dict(connections.databases["default"])
    config.update(ENGINE="django.db.backends.sqlite3", NAME=":memory:", OPTIONS={})
    connections.databases[alias] = config

    def forbidden_default(*args, **kwargs):
        pytest.fail("Selected-alias business flow attempted a default database query")

    monkeypatch.setattr(connections["default"], "cursor", forbidden_default)
    try:
        with django_db_blocker.unblock(), database_execution(alias):
            executor = MigrationExecutor(connections[alias])
            executor.migrate(executor.loader.graph.leaf_nodes())
            assert BusinessModule.objects.count() == 7
            assert Permission.objects.filter(code__startswith="access.").count() == 2
            call_command("seed_reference_data", verbosity=0)
            call_command("seed_phase1_demo", verbosity=0)
            counts = (Party.objects.count(), ProductVariant.objects.count())
            call_command("seed_phase1_demo", verbosity=0)
            assert counts == (Party.objects.count(), ProductVariant.objects.count())
            company = Company.objects.get(code="DEMO")
            actor = get_user_model().objects.create_superuser("alias@example.com", "test-only")
            UserCompanyAccess.objects.create(user=actor, company=company)
            context = BusinessContext(actor_id=actor.id, company_id=company.id)
            variant = ProductVariant.objects.get(sku="HONEY-001")
            customer = Party.objects.get(is_customer=True)
            supplier = Party.objects.get(is_supplier=True)
            common = {"order_date": date(2026, 10, 7), "currency_id": company.base_currency_id}
            sales = create_sales_order(context, customer_id=customer.id, **common)
            add_sales_order_line(
                context, order_id=sales.id, product_variant_id=variant.id,
                quantity="2", unit_price="10",
            )
            assert confirm_sales_order(context, order_id=sales.id).status == "confirmed"
            purchase = create_purchase_order(context, supplier_id=supplier.id, **common)
            line = add_purchase_order_line(
                context, order_id=purchase.id, product_variant_id=variant.id,
                quantity="2", unit_cost="7",
            )
            confirm_purchase_order(context, order_id=purchase.id)
            receipt_args = {
                "purchase_order_id": purchase.id,
                "receipt_date": date(2026, 10, 7),
                "idempotency_key": "alias-retry",
                "lines": [{"purchase_order_line_id": line.id, "quantity_received": "1"}],
            }
            receipt = receive_purchase_order(context, **receipt_args)
            assert receive_purchase_order(context, **receipt_args).id == receipt.id
            branch = Branch.objects.create(company=company, code="QA", name="QA")
            warehouse = Warehouse.objects.create(
                company=company, branch=branch, code="QA", name="QA",
            )
            movement = create_stock_movement(
                context, movement_type="receipt", effective_at=timezone.now(),
            )
            add_stock_movement_line(
                context, movement_id=movement.id, product_variant_id=variant.id,
                quantity="2", destination_warehouse_id=warehouse.id,
            )
            assert post_stock_movement(context, movement_id=movement.id).status == "posted"
            assert post_stock_movement(context, movement_id=movement.id).status == "posted"
            assert stock_balance(
                context, product_variant_id=variant.id, warehouse_id=warehouse.id,
            ) == 2
            before = AuditEntry.objects.count()
            with pytest.raises(RuntimeError), business_atomic_context():
                create_sales_order(context, customer_id=customer.id, **common)
                raise RuntimeError("Atomic aggregate/audit rollback")
            assert AuditEntry.objects.count() == before
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
    assert current_database_alias() == "default"
