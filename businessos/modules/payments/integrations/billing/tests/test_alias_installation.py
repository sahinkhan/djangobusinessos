import os
import subprocess
import sys
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

if not apps.is_installed("businessos.modules.payments.integrations.billing"):
    pytest.skip("Optional payments_billing deployment is not installed.", allow_module_level=True)

from businessos.core.database import database_execution

STANDALONE_SCRIPT = """
from django.conf import settings
import os
owner = os.environ["PAYINT_TEST_OWNER"]
settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS
    if not app.startswith("businessos.modules.") or app in
    {"businessos.modules.party", "businessos.modules." + owner}]
settings.ROOT_URLCONF = "businessos.modules." + owner + ".urls"
import django
django.setup()
from django.core.management import call_command
call_command("migrate", verbosity=0)
call_command("check")
from django.contrib.auth import get_user_model
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.core.reference.models import Country, Currency, Language
from businessos.modules.party.models import Party
currency = Currency.objects.create(code="USD", name="Dollar")
company = Company.objects.create(code="ONLY", name="Standalone",
    base_currency=currency, country=Country.objects.create(code="US", name="US"),
    default_language=Language.objects.create(code="EN", name="English"))
actor = get_user_model().objects.create_superuser("standalone@synthetic.test", "test-only")
context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
party = Party.objects.create(company=company, party_type="person", display_name="Payer")
if owner == "payments":
    from businessos.modules.payments.services import create_payment_method, record_payment
    from businessos.modules.payments.selectors import payment_receipt_basis
    method = create_payment_method(context, code="CASH", name="Cash")
    payment = record_payment(context, payer_party_id=party.pk, currency_id=currency.pk,
                             amount="1", payment_method_id=method.pk)
    assert payment_receipt_basis(context, payment.pk).amount == 1
else:
    from businessos.modules.billing.services import create_invoice, add_invoice_line, issue_invoice
    from businessos.modules.billing.selectors import invoice_financial_basis
    invoice = create_invoice(context, bill_to_party_id=party.pk, currency_id=currency.pk)
    add_invoice_line(context, invoice.pk, description="One", quantity="1", unit_price="1")
    issue_invoice(context, invoice.pk)
    assert invoice_financial_basis(context, invoice.pk).original_total == 1
import sys
assert not any(name.startswith("businessos.modules.payments.integrations.") for name in sys.modules)
absent = "billing" if owner == "payments" else "payments"
assert not any(name.startswith("businessos.modules." + absent) for name in sys.modules)
assert not any(name.startswith("businessos.modules.accounting") for name in sys.modules)
print("standalone owner bootstrap and public basis PASS")
"""


@pytest.mark.parametrize("owner", ["billing", "payments"])
@pytest.mark.parametrize("backend", ["sqlite", "postgresql"])
def test_standalone_owner_bootstrap(owner, backend):
    config = connections.databases["default"]
    if backend == "postgresql" and config["ENGINE"] != "django.db.backends.postgresql":
        pytest.skip("Fresh standalone PostgreSQL bootstrap requires PostgreSQL.")
    admin = None
    name = "payint1_standalone_" + uuid4().hex
    env = os.environ | {
        "PAYINT_TEST_OWNER": owner,
        "BUSINESSOS_INSTALL_PAYMENTS_BILLING": "0",
        "DJANGO_SETTINGS_MODULE": "config.settings.test"
        if backend == "sqlite"
        else "config.settings.development",
    }
    try:
        if backend == "postgresql":
            import psycopg
            from psycopg import sql

            admin = psycopg.connect(
                dbname="postgres",
                user=config["USER"],
                password=config["PASSWORD"],
                host=config["HOST"],
                port=config["PORT"],
                autocommit=True,
            )
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
            env["POSTGRES_DB"] = name
        result = subprocess.run(
            [sys.executable, "-c", STANDALONE_SCRIPT],
            env=env,
            capture_output=True,
            text=True,
            timeout=90,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "public basis PASS" in result.stdout
    finally:
        if admin is not None:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
            admin.close()


@pytest.mark.parametrize("missing", ["billing", "payments"])
def test_optional_installation_requires_both_owners(missing):
    script = """
from django.conf import settings
import os
settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS
                         if app != "businessos.modules." + os.environ["PAYINT_MISSING"]]
import django
django.setup()
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=os.environ
        | {"DJANGO_SETTINGS_MODULE": "config.settings.test", "PAYINT_MISSING": missing},
        timeout=30,
    )
    assert result.returncode != 0
    assert "payments_billing requires installed Billing and Payments owners" in result.stderr


def test_selected_alias_complete_flow(django_db_blocker, monkeypatch):
    from django.contrib.auth import get_user_model

    from businessos.core.audit.models import AuditEntry
    from businessos.core.common.context import BusinessContext
    from businessos.core.organization.models import Company
    from businessos.core.reference.models import Country, Currency, Language
    from businessos.modules.billing import services as billing
    from businessos.modules.party.models import Party
    from businessos.modules.payments import services as payments

    from .. import compatibility, selectors, services
    from ..models import PaymentAllocation
    from .test_evidence_retry_integrity import restricted_reader

    alias = "payint1_selected_alias"
    config = dict(connections.databases["default"])
    postgres = config["ENGINE"] == "django.db.backends.postgresql"
    admin = None
    if postgres:
        import psycopg
        from psycopg import sql

        admin = psycopg.connect(
            dbname="postgres",
            user=config["USER"],
            password=config["PASSWORD"],
            host=config["HOST"],
            port=config["PORT"],
            autocommit=True,
        )
        config["NAME"] = "payint1_alias_" + uuid4().hex
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(config["NAME"])))
    else:
        config.update(NAME=":memory:", OPTIONS={})
    connections.databases[alias] = config
    statements = []

    def trace(execute, statement, params, many, context):
        statements.append(statement)
        return execute(statement, params, many, context)

    def forbidden(*args, **kwargs):
        pytest.fail("Allocation flow leaked to default connection.")

    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(connections["default"], "cursor", forbidden)
            with django_db_blocker.unblock(), database_execution(alias):
                executor = MigrationExecutor(connections[alias])
                executor.migrate(executor.loader.graph.leaf_nodes())
                currency = Currency.objects.create(code="USD", name="Dollar")
                company = Company.objects.create(
                    code="ALIAS",
                    name="Alias",
                    base_currency=currency,
                    country=Country.objects.create(code="US", name="US"),
                    default_language=Language.objects.create(code="EN", name="English"),
                )
                actor = get_user_model().objects.create_superuser(
                    "alias@synthetic.test", "test-only"
                )
                context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
                party = Party.objects.create(
                    company=company, party_type="person", display_name="Alias"
                )
                method = payments.create_payment_method(context, code="CASH", name="Cash")
                receipt = payments.record_payment(
                    context,
                    payer_party_id=party.pk,
                    currency_id=currency.pk,
                    amount="100",
                    payment_method_id=method.pk,
                )
                invoice = billing.create_invoice(
                    context, bill_to_party_id=party.pk, currency_id=currency.pk
                )
                billing.add_invoice_line(
                    context, invoice.pk, description="Alias", quantity="1", unit_price="100"
                )
                billing.issue_invoice(context, invoice.pk)
                args = dict(
                    payment_id=receipt.pk,
                    invoice_id=invoice.pk,
                    amount="1",
                    idempotency_key="first",
                )
                with connections[alias].execute_wrapper(trace):
                    first = services.create_payment_allocation(context, **args)
                    assert services.create_payment_allocation(context, **args).pk == first.pk
                    before = AuditEntry.objects.count()
                    with patch.object(
                        services, "record_audit_entry", side_effect=RuntimeError("audit")
                    ):
                        with pytest.raises(RuntimeError):
                            services.create_payment_allocation(
                                context, **(args | {"idempotency_key": "rollback"})
                            )
                    assert (
                        PaymentAllocation.objects.count() == 1
                        and AuditEntry.objects.count() == before
                    )
                    for index in range(50):
                        services.create_payment_allocation(
                            context, **(args | {"idempotency_key": str(index)})
                        )
                    payment_evidence = selectors.payment_allocation_evidence(
                        context, receipt.pk, page=2
                    )
                    invoice_evidence = selectors.invoice_allocation_evidence(
                        context, invoice.pk, page=2
                    )
                    assert payment_evidence.count == invoice_evidence.count == 51
                    assert len(payment_evidence.history) == len(invoice_evidence.history) == 1
                    assert payment_evidence.applied == invoice_evidence.applied == 51
                    assert all(row._state.db == alias for row in PaymentAllocation.objects.all())
                    assert all(row._state.db == alias for row in AuditEntry.objects.all())
                if postgres:
                    # Real limited role and RLS on the selected database. The
                    # default cursor remains forbidden for the entire probe.
                    with connections[alias].cursor() as cursor:
                        cursor.execute(
                            "ALTER TABLE payments_billing_paymentallocation "
                            "ENABLE ROW LEVEL SECURITY"
                        )
                        cursor.execute(
                            "CREATE POLICY hidden_alias_allocations ON "
                            "payments_billing_paymentallocation USING (false)"
                        )
                    try:
                        with restricted_reader(connections[alias]):
                            assert not PaymentAllocation.objects.exists()
                            assert compatibility.evidence_profile() == "incompatible"
                            result = selectors.payment_allocation_evidence(context, receipt.pk)
                            assert result.applied is result.history is result.count is None
                            with pytest.raises(ValidationError, match="unavailable"):
                                services.create_payment_allocation(
                                    context, **(args | {"idempotency_key": "hidden"})
                                )
                        assert PaymentAllocation.objects.count() == 51
                    finally:
                        with connections[alias].cursor() as cursor:
                            cursor.execute(
                                "DROP POLICY hidden_alias_allocations ON "
                                "payments_billing_paymentallocation"
                            )
                            cursor.execute(
                                "ALTER TABLE payments_billing_paymentallocation "
                                "DISABLE ROW LEVEL SECURITY"
                            )
                    assert compatibility.evidence_profile() is None
                assert any("LIMIT 50 OFFSET 50" in statement for statement in statements)
                if postgres:
                    assert any("FOR UPDATE" in statement for statement in statements)
                assert any("SAVEPOINT" in statement for statement in statements)
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
        if admin is not None:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(config["NAME"])))
            admin.close()
