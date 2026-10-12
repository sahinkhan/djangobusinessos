import os
import subprocess
import sys
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

from businessos.core.database import database_execution

TOPOLOGY_SCRIPT = """
import os, sys
from django.conf import settings
mode = os.environ["ACCINT_TOPOLOGY"]
if mode in {"accounting", "billing", "payments", "invoice_no_payments", "billing_accounting"}:
    owners = (
        {"party", "accounting", "billing"}
        if mode in {"invoice_no_payments", "billing_accounting"} else {"party", mode}
    )
    allowed = {"businessos.modules." + owner for owner in owners}
    if mode == "invoice_no_payments":
        allowed.add("businessos.modules.accounting.integrations.billing")
    settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS
        if not app.startswith("businessos.modules.") or app in allowed]
import django
django.setup()
from django.core.management import call_command
call_command("migrate", verbosity=0)
from django.contrib.auth import get_user_model
from businessos.core.common.context import BusinessContext
from businessos.core.reference.models import Currency, Country, Language
from businessos.core.organization.models import Company
from businessos.modules.party.models import Party
currency = Currency.objects.create(code="USD", name="Synthetic dollar")
company = Company.objects.create(code="SYN", name="Synthetic", base_currency=currency,
    country=Country.objects.create(code="US",name="US"),
    default_language=Language.objects.create(code="EN",name="English"))
actor = get_user_model().objects.create_superuser("topology@synthetic.test","test-only")
context = BusinessContext(actor_id=actor.pk,company_id=company.pk)
party = Party.objects.create(company=company,party_type="person",display_name="Synthetic")
if mode in {"billing","invoice_no_payments","billing_accounting"}:
    from businessos.modules.billing.services import create_invoice,add_invoice_line,issue_invoice
    invoice = create_invoice(context,bill_to_party_id=party.pk,currency_id=currency.pk)
    add_invoice_line(context,invoice.pk,description="One",quantity="1",unit_price="1")
    issue_invoice(context,invoice.pk)
if mode in {"accounting","invoice_no_payments","billing_accounting"}:
    from businessos.modules.accounting.services import create_account,create_journal
    ar=create_account(context,code="AR",name="AR",type="ASSET")
    revenue=create_account(context,code="REV",name="Revenue",type="INCOME")
    journal=create_journal(context,code="GEN",name="General")
if mode == "invoice_no_payments":
    from businessos.modules.accounting.integrations.billing.services import (
        post_billing_invoice_outcome,
    )
    result=post_billing_invoice_outcome(
        context,invoice_id=invoice.pk,journal_id=journal.pk,
        ar_account_id=ar.pk,revenue_account_id=revenue.pk)
    assert result.state == "POSTED" and result.amount == 1
if mode in {"accounting","billing","payments","invoice_no_payments","billing_accounting"}:
    absent = {"accounting","billing","payments"} - owners
    assert not any(any(name.startswith("businessos.modules."+owner)
                       for owner in absent) for name in sys.modules)
print("ACC-INT topology fresh bootstrap PASS")
"""


@pytest.mark.parametrize(
    "mode,invoice,allocation,payint",
    [
        ("accounting", "0", "0", "0"),
        ("billing", "0", "0", "0"),
        ("payments", "0", "0", "0"),
        ("billing_accounting", "0", "0", "0"),
        ("owners_without_integrations", "0", "0", "0"),
        ("payint_without_accounting_integrations", "0", "0", "1"),
        ("invoice_no_payments", "1", "0", "0"),
        ("combined", "1", "0", "1"),
        ("all", "1", "1", "1"),
        ("unsupported", "0", "1", "1"),
        ("unsupported", "1", "1", "0"),
    ],
)
@pytest.mark.parametrize("backend", ["sqlite", "postgresql"])
def test_installation_topology(mode, invoice, allocation, payint, backend):
    config = connections.databases["default"]
    if backend == "postgresql" and config["ENGINE"] != "django.db.backends.postgresql":
        pytest.skip("Fresh PostgreSQL installation topology requires PostgreSQL.")
    admin = None
    name = "accint1_topology_" + uuid4().hex
    env = os.environ | {
        "ACCINT_TOPOLOGY": mode,
        "BUSINESSOS_INSTALL_ACCOUNTING_BILLING": invoice,
        "BUSINESSOS_INSTALL_ACCOUNTING_PAYMENTS_BILLING": allocation,
        "BUSINESSOS_INSTALL_PAYMENTS_BILLING": payint,
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
            [sys.executable, "-c", TOPOLOGY_SCRIPT],
            env=env,
            capture_output=True,
            text=True,
            timeout=100,
        )
        if mode == "unsupported":
            assert result.returncode != 0 and "requires" in result.stderr
        else:
            assert result.returncode == 0, result.stdout + result.stderr
            assert "fresh bootstrap PASS" in result.stdout
    finally:
        if admin:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
            admin.close()


def test_selected_alias_complete_posting_and_proof(django_db_blocker, monkeypatch):
    from django.contrib.auth import get_user_model

    from businessos.core.audit.models import AuditEntry
    from businessos.core.common.context import BusinessContext
    from businessos.core.organization.models import Company
    from businessos.core.reference.models import Country, Currency, Language
    from businessos.modules.accounting import services as accounting
    from businessos.modules.accounting.integrations.billing.models import InvoicePosting
    from businessos.modules.accounting.integrations.billing.selectors import invoice_posting_status
    from businessos.modules.accounting.integrations.billing.services import (
        post_billing_invoice_outcome,
    )
    from businessos.modules.accounting.integrations.payments_billing.models import AllocationPosting
    from businessos.modules.accounting.integrations.payments_billing.selectors import (
        allocation_posting_status,
    )
    from businessos.modules.accounting.integrations.payments_billing.services import (
        post_payment_allocation_outcome,
    )
    from businessos.modules.billing import services as billing
    from businessos.modules.party.models import Party
    from businessos.modules.payments import services as payments
    from businessos.modules.payments.integrations.billing.services import create_payment_allocation

    alias = "accint1_selected_alias"
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
        config["NAME"] = "accint1_alias_" + uuid4().hex
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(config["NAME"])))
    else:
        config.update(NAME=":memory:", OPTIONS={})
    connections.databases[alias] = config

    def forbidden(*args, **kwargs):
        pytest.fail("ACC-INT-1 attempted default database execution.")

    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(connections["default"], "cursor", forbidden)
            with django_db_blocker.unblock(), database_execution(alias):
                executor = MigrationExecutor(connections[alias])
                executor.migrate(executor.loader.graph.leaf_nodes())
                currency = Currency.objects.create(code="USD", name="Synthetic")
                country = Country.objects.create(code="US", name="US")
                language = Language.objects.create(code="EN", name="English")
                company = Company.objects.create(
                    code="ALIAS",
                    name="Synthetic",
                    base_currency=currency,
                    country=country,
                    default_language=language,
                )
                second = Company.objects.create(
                    code="ISOLATED",
                    name="Isolated",
                    base_currency=currency,
                    country=country,
                    default_language=language,
                )
                actor = get_user_model().objects.create_superuser(
                    "alias@synthetic.test", "test-only"
                )
                context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
                other = BusinessContext(actor_id=actor.pk, company_id=second.pk)
                party = Party.objects.create(
                    company=company, party_type="person", display_name="Synthetic"
                )
                invoice = billing.create_invoice(
                    context, bill_to_party_id=party.pk, currency_id=currency.pk
                )
                billing.add_invoice_line(
                    context, invoice.pk, description="One", quantity="1", unit_price="100"
                )
                billing.issue_invoice(context, invoice.pk)
                method = payments.create_payment_method(context, code="WIRE", name="Wire")
                payment = payments.record_payment(
                    context,
                    payer_party_id=party.pk,
                    currency_id=currency.pk,
                    amount="100",
                    payment_method_id=method.pk,
                )
                allocation = create_payment_allocation(
                    context,
                    payment_id=payment.pk,
                    invoice_id=invoice.pk,
                    amount="40",
                    idempotency_key="alias",
                )
                journal = accounting.create_journal(context, code="GEN", name="General")
                ar = accounting.create_account(context, code="AR", name="AR", type="ASSET")
                revenue = accounting.create_account(
                    context, code="REV", name="Revenue", type="INCOME"
                )
                cash = accounting.create_account(context, code="CASH", name="Cash", type="ASSET")
                kwargs = dict(
                    invoice_id=invoice.pk,
                    journal_id=journal.pk,
                    ar_account_id=ar.pk,
                    revenue_account_id=revenue.pk,
                )
                from businessos.modules.accounting.integrations.billing import services

                before = AuditEntry.objects.count()
                with patch.object(
                    services, "record_audit_entry", side_effect=RuntimeError("rollback")
                ):
                    with pytest.raises(RuntimeError):
                        post_billing_invoice_outcome(context, **kwargs)
                assert InvoicePosting.objects.count() == 0 and AuditEntry.objects.count() == before
                first = post_billing_invoice_outcome(context, **kwargs)
                assert post_billing_invoice_outcome(context, **kwargs) == first
                assert invoice_posting_status(context, invoice.pk) == first
                args = dict(
                    allocation_id=allocation.pk,
                    journal_id=journal.pk,
                    cash_account_id=cash.pk,
                    ar_account_id=ar.pk,
                )
                posted = post_payment_allocation_outcome(context, **args)
                assert post_payment_allocation_outcome(context, **args) == posted
                assert allocation_posting_status(context, allocation.pk) == posted
                from django.core.exceptions import PermissionDenied

                with pytest.raises(PermissionDenied):
                    invoice_posting_status(other, invoice.pk)
                assert all(row._state.db == alias for row in InvoicePosting.objects.all())
                assert all(row._state.db == alias for row in AllocationPosting.objects.all())
                assert all(row._state.db == alias for row in AuditEntry.objects.all())
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
        if admin:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(config["NAME"])))
            admin.close()
