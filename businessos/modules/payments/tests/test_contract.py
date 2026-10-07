import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import connection
from django.urls import reverse

from businessos.core.access.models import UserCompanyAccess
from businessos.core.common.context import BusinessContext
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company
from businessos.modules.party.models import Party
from businessos.modules.payments import selectors, services
from businessos.modules.payments.manifest import MODULE
from businessos.modules.payments.models import Payment

pytestmark = pytest.mark.django_db


def test_standalone_bootstrap_without_other_commercial_modules():
    script = """
from django.conf import settings
settings.INSTALLED_APPS = [app for app in settings.INSTALLED_APPS
    if not app.startswith("businessos.modules.") or app.rsplit(".", 1)[-1] in {"party", "payments"}]
settings.ROOT_URLCONF = "businessos.modules.payments.urls"
import django
django.setup()
from django.core.management import call_command
call_command("migrate", verbosity=0)
call_command("check")
from businessos.core.reference.models import Currency, Country, Language
from businessos.core.organization.models import Company
from businessos.core.common.context import BusinessContext
from django.contrib.auth import get_user_model
from businessos.modules.party.models import Party
from businessos.modules.payments.services import create_payment_method, record_payment
c = Currency.objects.create(code="USD", name="Dollar")
company = Company.objects.create(code="ONLY", name="Only Payments", base_currency=c,
    country=Country.objects.create(code="US", name="US"),
    default_language=Language.objects.create(code="EN", name="English"))
actor = get_user_model().objects.create_superuser("standalone@example.test", "test-only")
context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
party = Party.objects.create(company=company, party_type="organization", display_name="Payer")
method = create_payment_method(context, code="CASH", name="Cash")
receipt = record_payment(context, payer_party_id=party.pk, currency_id=c.pk,
                         payment_method_id=method.pk, amount="1")
assert receipt.amount == 1
import sys
assert not any(name.startswith(("businessos.modules.billing", "businessos.modules.accounting",
    "businessos.modules.inventory", "businessos.modules.sales", "businessos.modules.procurement"))
    for name in sys.modules)
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


def test_manifest_schema_dependency_contract():
    assert MODULE["depends"] == ["party", "organization", "reference", "access"]
    assert set(MODULE["permissions"]) == {
        "payments.method.view",
        "payments.method.manage",
        "payments.payment.view",
        "payments.payment.record",
    }
    assert {model.__name__ for model in apps.get_app_config("payments").get_models()} == {
        "Payment",
        "PaymentMethod",
    }
    fields = {field.name for field in Payment._meta.fields}
    assert not fields & {"status", "invoice", "allocation", "outstanding", "balance", "tenant_id"}
    assert (
        Payment._meta.get_field("amount").max_digits,
        Payment._meta.get_field("amount").decimal_places,
    ) == (38, 8)
    root = Path(__file__).parents[1]
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    f"modules.{name}" in (node.module or "")
                    for name in ["billing", "accounting", "inventory", "sales", "procurement"]
                )


def test_registration_frozen_and_preserves_enablement():
    migration = importlib.import_module(
        "businessos.modules.payments.migrations.0002_register_manifest"
    )
    module = BusinessModule.objects.get(code="payments")
    assert not module.is_enabled
    BusinessModule.objects.filter(pk=module.pk).update(is_enabled=True)
    migration.register_payments(apps, SimpleNamespace(connection=connection))
    module.refresh_from_db()
    assert module.is_enabled
    assert set(module.declared_permissions) == set(MODULE["permissions"])
    assert "manifest import" not in Path(migration.__file__).read_text()


def test_company_isolation(business_context, payload, company, operator, method, client):
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    other_payer = Party.objects.create(company=other, party_type="person", display_name="Other")
    with pytest.raises(ValidationError):
        services.record_payment(business_context, **(payload | {"payer_party_id": other_payer.pk}))
    receipt = services.record_payment(business_context, **payload)
    UserCompanyAccess.objects.create(user=operator, company=other)
    # Superuser still requires active registered permission; permits comparison of both scopes.
    operator.is_superuser = True
    operator.save()
    other_context = BusinessContext(actor_id=operator.pk, company_id=other.pk)
    assert not selectors.payments_for_company(other_context).exists()
    assert not selectors.payment_methods_for_company(other_context).exists()
    with pytest.raises(Payment.DoesNotExist):
        selectors.payment_detail(other_context, receipt.pk)
    with pytest.raises(ValidationError):
        services.update_payment_method(other_context, payment_method_id=method.pk, name="Wrong")
    with pytest.raises(ValidationError):
        services.record_payment(other_context, **payload)
    other_method = services.create_payment_method(other_context, code="cash", name="Other cash")
    assert other_method.code == method.code
    client.force_login(operator)
    from businessos.core.access.context import SESSION_COMPANY_KEY

    session = client.session
    session[SESSION_COMPANY_KEY] = str(other.pk)
    session.save()
    BusinessModule.objects.filter(code="payments").update(is_enabled=True)
    assert client.get(reverse("payments:detail", args=[receipt.pk])).status_code == 404
    assert client.get(reverse("payments:method_edit", args=[method.pk])).status_code == 404


@pytest.mark.parametrize("kind", ["method", "receipt"])
@pytest.mark.parametrize("operation", ["get_or_create", "update_or_create", "private_token"])
def test_additional_write_guards(business_context, payload, method, kind, operation):
    instance = method if kind == "method" else services.record_payment(business_context, **payload)
    with pytest.raises(ValidationError):
        if operation == "private_token":
            if kind == "method":
                instance._persist(object())
            else:
                instance._insert(object())
        elif operation == "get_or_create":
            type(instance).objects.get_or_create(pk=uuid4())
        else:
            type(instance).objects.update_or_create(pk=instance.pk, defaults={})


def test_postgres_38_digit_storage_and_retry(business_context, payload, currency):
    if connection.vendor != "postgresql":
        from businessos.modules.payments.domain import receipt_amount

        # SQLite's NUMERIC affinity cannot round-trip 38 digits; validate the portable domain.
        maximum = "999999999999999999999999999999.99999999"
        assert str(receipt_amount(maximum, 8)) == maximum
        return
    currency.decimal_places = 8
    currency.save()
    payload["amount"] = "999999999999999999999999999999.99999999"
    receipt = services.record_payment(business_context, **payload, idempotency_key="maximum")
    receipt.refresh_from_db()
    assert str(receipt.amount) == payload["amount"]
    assert (
        services.record_payment(business_context, **payload, idempotency_key="maximum").pk
        == receipt.pk
    )
