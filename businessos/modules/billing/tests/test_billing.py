from datetime import date
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

import pytest
from django.apps import apps
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.db.models.deletion import ProtectedError

from businessos.core.access.models import RolePermission
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company
from businessos.core.reference.models import Currency
from businessos.modules.billing import domain, services
from businessos.modules.billing.manifest import MODULE
from businessos.modules.billing.models import Invoice, InvoiceLine
from businessos.modules.billing.selectors import invoice_detail, invoice_total, invoices_for_company
from businessos.modules.party.models import Party

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("field", ["quantity", "unit_price"])
@pytest.mark.parametrize(
    "value",
    ["NaN", "Infinity", "-Infinity", "bad", "", True, 0.5, "0.00001", "100000000000000", "-1"],
)
def test_rejected_decimal_inputs_are_atomic(business_context, invoice, line, field, value):
    before = AuditEntry.objects.count()
    data = {"description": "Test", "quantity": "1", "unit_price": "1", field: value}
    with pytest.raises(ValidationError):
        services.add_invoice_line(business_context, invoice.pk, **data)
    with pytest.raises(ValidationError):
        services.update_invoice_line(business_context, invoice.pk, line.pk, **{field: value})
    line.refresh_from_db()
    assert (line.quantity, line.unit_price) == (Decimal(2), Decimal("0.0050"))
    assert invoice.lines.count() == 1
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("value", [0, "0", "-0"])
def test_zero_quantity_rejected(business_context, invoice, value):
    with pytest.raises(ValidationError):
        services.add_invoice_line(
            business_context, invoice.pk, description="X", quantity=value, unit_price=0
        )


@pytest.mark.parametrize("precision", [0, 2, 8])
def test_round_once_frozen_precision(business_context, invoice, currency, precision):
    currency.decimal_places = precision
    currency.save()
    services.update_invoice(business_context, invoice.pk, currency_id=currency.pk)
    for _ in range(2):
        services.add_invoice_line(
            business_context, invoice.pk, description="Small", quantity="1", unit_price="0.0050"
        )
    expected = {0: Decimal(0), 2: Decimal("0.01"), 8: Decimal("0.01000000")}[precision]
    assert invoice_total(business_context, invoice.pk) == expected
    issued = services.issue_invoice(business_context, invoice.pk)
    currency.decimal_places = 1
    currency.save()
    assert invoice_total(business_context, invoice.pk) == expected
    assert services.issue_invoice(business_context, invoice.pk).issued_at == issued.issued_at
    assert AuditEntry.objects.filter(action="billing.invoice.issued").count() == 1


def test_generic_zero_total_and_dates(business_context, invoice, party, company):
    assert not party.is_customer
    assert invoice.invoice_date == services.company_local_date(company.pk)
    services.add_invoice_line(
        business_context, invoice.pk, description="Free service", quantity="0.0001", unit_price=0
    )
    assert services.issue_invoice(business_context, invoice.pk).total == 0
    assert not any(
        f.name in {"product", "product_variant", "total", "amount_due", "payment_status"}
        for m in [Invoice, InvoiceLine]
        for f in m._meta.fields
    )


def test_dates_and_empty_issue(business_context, invoice):
    for data in [
        {"invoice_date": "not-date"},
        {"invoice_date": "2026-10-07", "due_date": "2026-10-06"},
    ]:
        with pytest.raises(ValidationError):
            services.update_invoice(business_context, invoice.pk, **data)
    with pytest.raises(ValidationError, match="at least one"):
        services.issue_invoice(business_context, invoice.pk)
    updated = services.update_invoice(
        business_context, invoice.pk, invoice_date="2026-10-07", due_date="2026-10-08"
    )
    assert updated.due_date == date(2026, 10, 8)


def test_snapshot_refresh_noop_and_freeze(business_context, invoice, party, line):
    before = AuditEntry.objects.count()
    services.update_invoice(business_context, invoice.pk, bill_to_party_id=party.pk)
    assert AuditEntry.objects.count() == before
    party.display_name = "Renamed"
    party.legal_name = "Legal entity"
    party.save()
    assert (
        invoice_detail(business_context, invoice.pk).bill_to_display_name_snapshot
        == "Generic client"
    )
    services.update_invoice(business_context, invoice.pk, bill_to_party_id=party.pk)
    assert AuditEntry.objects.count() == before + 1
    services.update_invoice_line(business_context, invoice.pk, line.pk, quantity="2.0000")
    assert AuditEntry.objects.count() == before + 1
    services.issue_invoice(business_context, invoice.pk)
    party.display_name = "Later"
    party.save()
    assert invoice_detail(business_context, invoice.pk).bill_to_display_name_snapshot == "Renamed"
    for obj in [party, invoice.currency]:
        with pytest.raises(ProtectedError):
            obj.delete()


@pytest.mark.parametrize("change", ["inactive_party", "inactive_currency", "precision", "type"])
def test_issue_reference_revalidation(business_context, invoice, line, party, currency, change):
    if change == "inactive_party":
        Party.objects.filter(pk=party.pk).update(is_active=False)
    elif change == "inactive_currency":
        Currency.objects.filter(pk=currency.pk).update(is_active=False)
    elif change == "type":
        Party.objects.filter(pk=party.pk).update(party_type="invalid")
    else:
        Currency.objects.filter(pk=currency.pk).update(decimal_places=8)
    before = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        services.issue_invoice(business_context, invoice.pk)
    invoice.refresh_from_db()
    assert invoice.status == "draft"
    assert AuditEntry.objects.count() == before
    if change == "precision":
        services.update_invoice(business_context, invoice.pk, currency_id=currency.pk)
        assert services.issue_invoice(business_context, invoice.pk).status == "issued"


def test_unsupported_currency_and_cross_company(
    business_context, invoice, party, currency, company
):
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=currency,
        country=company.country,
        default_language=company.default_language,
    )
    other_party = Party.objects.create(
        company=other, party_type="organization", display_name="Other"
    )
    with pytest.raises(ValidationError):
        services.update_invoice(business_context, invoice.pk, bill_to_party_id=other_party.pk)
    currency.decimal_places = 9
    currency.save()
    with pytest.raises(ValidationError):
        services.create_invoice(
            business_context, bill_to_party_id=party.pk, currency_id=currency.pk
        )
    from dataclasses import replace

    wrong = replace(business_context, company_id=other.pk)
    with pytest.raises(PermissionDenied):
        invoice_detail(wrong, invoice.pk)
    with pytest.raises(PermissionDenied):
        services.update_invoice(wrong, invoice.pk, notes="invalid")


@pytest.mark.parametrize("operation", ["create", "update", "add", "line_update", "remove", "issue"])
def test_audit_failure_rolls_back(business_context, invoice, line, party, currency, operation):
    before = AuditEntry.objects.count()
    actions = {
        "create": lambda: services.create_invoice(
            business_context, bill_to_party_id=party.pk, currency_id=currency.pk
        ),
        "update": lambda: services.update_invoice(
            business_context, invoice.pk, notes="changed", bill_to_party_id=party.pk
        ),
        "add": lambda: services.add_invoice_line(
            business_context, invoice.pk, description="New", quantity=1, unit_price=1
        ),
        "line_update": lambda: services.update_invoice_line(
            business_context, invoice.pk, line.pk, quantity=3
        ),
        "remove": lambda: services.remove_invoice_line(business_context, invoice.pk, line.pk),
        "issue": lambda: services.issue_invoice(business_context, invoice.pk),
    }
    with patch.object(services, "record_audit_entry", side_effect=RuntimeError("audit failure")):
        with pytest.raises(RuntimeError):
            actions[operation]()
    invoice.refresh_from_db()
    line.refresh_from_db()
    assert invoice.status == "draft" and invoice.notes == ""
    assert line.quantity == 2 and invoice.lines.count() == 1
    assert Invoice.objects.count() == 1 and AuditEntry.objects.count() == before


@pytest.mark.parametrize("permission", MODULE["permissions"])
def test_rbac_services_and_selectors(
    business_context, invoice, line, billing_role, party, currency, permission
):
    RolePermission.objects.filter(role=billing_role, permission__code=permission).delete()
    actions = {
        "billing.invoice.view": lambda: invoices_for_company(business_context),
        "billing.invoice.create": lambda: services.create_invoice(
            business_context, bill_to_party_id=party.pk, currency_id=currency.pk
        ),
        "billing.invoice.update": lambda: services.update_invoice(
            business_context, invoice.pk, notes="X"
        ),
        "billing.invoice.issue": lambda: services.issue_invoice(business_context, invoice.pk),
    }
    with pytest.raises(PermissionDenied):
        actions[permission]()


@pytest.mark.parametrize("issued", [False, True])
@pytest.mark.parametrize(
    "path", ["save", "delete", "update", "bulk_update", "bulk_create", "upsert", "qs_delete"]
)
def test_public_orm_blocked(business_context, invoice, line, issued, path):
    if issued:
        services.issue_invoice(business_context, invoice.pk)
    for obj in [invoice, line]:
        model = type(obj)
        actions = {
            "save": obj.save,
            "delete": obj.delete,
            "update": lambda model=model, obj=obj: model.objects.filter(pk=obj.pk).update(
                company_id=invoice.company_id
            ),
            "bulk_update": lambda model=model, obj=obj: model.objects.bulk_update(
                [obj], ["company"]
            ),
            "bulk_create": lambda model=model, obj=obj: model.objects.bulk_create([obj]),
            "upsert": lambda model=model, obj=obj: model.objects.bulk_create(
                [obj], update_conflicts=True, update_fields=["company"], unique_fields=["id"]
            ),
            "qs_delete": lambda model=model, obj=obj: model.objects.filter(pk=obj.pk).delete(),
        }
        with pytest.raises(ValidationError):
            actions[path]()
    assert Invoice.objects.count() == 1 and InvoiceLine.objects.count() == 1


def test_stale_parent_substitution_and_issued_service_writes(
    business_context, invoice, line, party, currency
):
    other = services.create_invoice(
        business_context, bill_to_party_id=party.pk, currency_id=currency.pk
    )
    services.issue_invoice(business_context, invoice.pk)
    line.invoice_id = other.pk
    with pytest.raises(ValidationError):
        line.delete()
    with pytest.raises(PermissionDenied):
        services.remove_invoice_line(business_context, other.pk, line.pk)
    for call in [
        lambda: services.update_invoice(business_context, invoice.pk, notes="changed"),
        lambda: services.update_invoice_line(business_context, invoice.pk, line.pk, quantity=3),
        lambda: services.remove_invoice_line(business_context, invoice.pk, line.pk),
    ]:
        with pytest.raises(ValidationError):
            call()
    assert InvoiceLine.objects.get(pk=line.pk).invoice_id == invoice.pk


def test_number_collision_savepoint_and_stable_positions(
    business_context, invoice, line, party, currency
):
    with patch.object(services, "_number", side_effect=[invoice.number, "INV-UNIQUE"]):
        new = services.create_invoice(
            business_context, bill_to_party_id=party.pk, currency_id=currency.pk
        )
    assert new.number == "INV-UNIQUE"
    second = services.add_invoice_line(
        business_context, invoice.pk, description="Two", quantity=1, unit_price=1
    )
    services.remove_invoice_line(business_context, invoice.pk, line.pk)
    third = services.add_invoice_line(
        business_context, invoice.pk, description="Three", quantity=1, unit_price=1
    )
    assert (second.position, third.position) == (2, 3)


def test_manifest_registration_and_services_without_registry(business_context, invoice, line):
    migration = import_module("businessos.modules.billing.migrations.0002_register_manifest")
    BusinessModule.objects.filter(code="billing").update(is_enabled=True)
    migration.register_billing(apps, connection.schema_editor())
    assert BusinessModule.objects.get(code="billing").is_enabled
    BusinessModule.objects.filter(code="billing").delete()
    migration.register_billing(apps, connection.schema_editor())
    assert not BusinessModule.objects.get(code="billing").is_enabled
    BusinessModule.objects.filter(code="billing").delete()
    assert services.issue_invoice(business_context, invoice.pk).status == "issued"
    assert MODULE["depends"] == ["party", "organization", "reference", "access"]
    root = Path(__file__).resolve().parents[1]
    for source in root.glob("*.py"):
        text = source.read_text()
        for name in ["catalog", "sales", "procurement", "inventory", "payments", "accounting"]:
            assert f"businessos.modules.{name}" not in text


def test_decimal_maximum_and_aggregate_boundary():
    maximum = domain.MAX_INPUT
    product = domain.line_amount(maximum, maximum)
    assert product == Decimal("9999999999999999980000000000.00000001")
    assert domain.calculate_total([(maximum, maximum)] * 100, 8) < Decimal("1e30")
    with pytest.raises(ValueError, match="aggregate"):
        domain.calculate_total([(maximum, maximum)] * 101, 8)
    assert domain.calculate_total([(1, "0.0050"), (1, "0.0050")], 2) == Decimal("0.01")
    assert domain.calculate_total([(1, "0.0050")], 2) == Decimal("0.01")
