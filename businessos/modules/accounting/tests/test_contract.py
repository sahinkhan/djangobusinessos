import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.db import connection

from businessos.core.modules.models import BusinessModule
from businessos.modules.accounting.manifest import MODULE, PERMISSIONS
from businessos.modules.accounting.models import Account, Journal, JournalEntry, JournalEntryLine

pytestmark = pytest.mark.django_db


def test_contract_no_balance_or_upstream_dependency():
    assert MODULE["depends"] == ["party", "organization", "reference", "access"]
    assert set(MODULE["permissions"]) == {
        "accounting.account.view",
        "accounting.account.manage",
        "accounting.journal.view",
        "accounting.journal.manage",
        "accounting.entry.view",
        "accounting.entry.create",
        "accounting.entry.update",
        "accounting.entry.post",
    }
    assert {m.__name__ for m in apps.get_app_config("accounting").get_models()} == {
        "Account",
        "Journal",
        "JournalEntry",
        "JournalEntryLine",
    }
    for model in (Account, Journal, JournalEntry, JournalEntryLine):
        fields = {field.name for field in model._meta.fields}
        assert not fields & {
            "balance",
            "current_balance",
            "invoice",
            "payment",
            "idempotency_key",
            "tenant_id",
            "parent",
        }
    assert JournalEntry._meta.get_field("number").max_length == 35
    assert (
        JournalEntryLine._meta.get_field("position").get_internal_type() == "PositiveIntegerField"
    )
    for field in ("debit", "credit"):
        f = JournalEntryLine._meta.get_field(field)
        assert (f.max_digits, f.decimal_places) == (38, 8)
    for path in Path(__file__).parents[1].glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    "modules." + name in (node.module or "")
                    for name in [
                        "billing",
                        "payments",
                        "catalog",
                        "sales",
                        "procurement",
                        "inventory",
                    ]
                )


def test_registration_freeze_and_preservation():
    migration = importlib.import_module(
        "businessos.modules.accounting.migrations.0002_register_manifest"
    )
    assert migration.PERMISSIONS == PERMISSIONS
    module = BusinessModule.objects.get(code="accounting")
    assert not module.is_enabled
    BusinessModule.objects.filter(pk=module.pk).update(is_enabled=True)
    migration.register_accounting(apps, SimpleNamespace(connection=connection))
    module.refresh_from_db()
    assert module.is_enabled and set(module.declared_permissions) == set(MODULE["permissions"])
    assert "manifest import" not in Path(migration.__file__).read_text()


def test_standalone_installed_without_commercial_modules():
    script = """
from django.conf import settings
settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS
    if not app.startswith("businessos.modules.")
    or app.rsplit(".",1)[-1] in {"party", "accounting"}]
settings.ROOT_URLCONF = "businessos.modules.accounting.urls"
import django
django.setup()
from django.core.management import call_command
call_command("migrate", verbosity=0)
call_command("check")
from django.contrib.auth import get_user_model
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.core.reference.models import Currency, Country, Language
from businessos.modules.accounting import services, selectors
company = Company.objects.create(code="ONLY", name="Only",
    base_currency=Currency.objects.create(code="USD", name="Dollar"),
    country=Country.objects.create(code="US", name="US"),
    default_language=Language.objects.create(code="EN", name="English"))
user = get_user_model().objects.create_superuser("only@accounting.test", "synthetic-only")
context = BusinessContext(actor_id=user.pk, company_id=company.pk)
account = services.create_account(context, code="CASH", name="Cash", type="ASSET")
journal = services.create_journal(context, code="GEN", name="General")
entry = services.create_journal_entry(context, journal_id=journal.pk)
for debit, credit in [(1,0),(0,1)]:
    services.add_journal_entry_line(context, entry.pk, account_id=account.pk,
        debit=debit, credit=credit)
services.post_journal_entry(context, entry.pk)
assert len(selectors.general_ledger(context)) == 2
assert selectors.trial_balance(context)[0].net == 0
import sys
assert not any(name.startswith(tuple("businessos.modules." + n for n in
    ["billing","payments","sales","procurement","inventory","catalog"])) for name in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=os.environ | {"DJANGO_SETTINGS_MODULE": "config.settings.test"},
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_existing_billing_payment_flows_have_no_accounting_effect(company, currency, party):
    from django.contrib.auth import get_user_model

    from businessos.core.audit.models import AuditEntry
    from businessos.core.common.context import BusinessContext
    from businessos.core.modules.services import register_manifest
    from businessos.modules.billing import services as billing
    from businessos.modules.billing.manifest import MODULE as BILLING
    from businessos.modules.payments import services as payments
    from businessos.modules.payments.manifest import MODULE as PAYMENTS

    register_manifest(BILLING)
    register_manifest(PAYMENTS)
    actor = get_user_model().objects.create_superuser("isolation@example.test", "synthetic-only")
    context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
    invoice = billing.create_invoice(context, bill_to_party_id=party.pk, currency_id=currency.pk)
    billing.add_invoice_line(
        context, invoice.pk, description="Standalone", quantity=1, unit_price=10
    )
    billing.issue_invoice(context, invoice.pk)
    method = payments.create_payment_method(context, code="CASH", name="Cash")
    payments.record_payment(
        context,
        payer_party_id=party.pk,
        currency_id=currency.pk,
        amount=10,
        payment_method_id=method.pk,
    )
    assert not JournalEntry.objects.exists() and not JournalEntryLine.objects.exists()
    assert not AuditEntry.objects.filter(action__startswith="accounting.").exists()
