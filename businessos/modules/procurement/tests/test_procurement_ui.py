from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from django.db import connection
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.services import register_manifest
from businessos.modules.procurement.manifest import MODULE
from businessos.modules.procurement.models import (
    PurchaseOrder,
    PurchaseReceipt,
    PurchaseReceiptLine,
)
from businessos.modules.procurement.services import add_purchase_order_line, confirm_purchase_order


@pytest.fixture
def procurement_client(client, operator, company):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    return client


@pytest.mark.django_db
def test_module_gating_controls_navigation_and_http(procurement_client):
    module = BusinessModule.objects.get(code="procurement")
    assert not module.is_enabled
    assert b'href="/procurement/orders/"' not in procurement_client.get(reverse("home")).content
    assert procurement_client.get(reverse("procurement:order_list")).status_code == 404
    register_manifest(MODULE, enabled=True)
    assert b'href="/procurement/orders/"' in procurement_client.get(reverse("home")).content
    assert procurement_client.get(reverse("procurement:order_list")).status_code == 200
    BusinessModule.objects.filter(code="procurement").delete()
    assert procurement_client.get(reverse("procurement:order_list")).status_code == 404


@pytest.mark.django_db
def test_supplier_to_receipt_ui_flow(
    procurement_client,
    business_context,
    company,
    supplier,
    currency,
    purchasable_variant,
):
    register_manifest(MODULE, enabled=True)
    response = procurement_client.post(
        reverse("procurement:order_create"),
        {
            "supplier": supplier.id,
            "order_date": date(2026, 9, 14).isoformat(),
            "currency": currency.id,
            "notes": "UI order",
            "scope_company_id": company.id,
        },
    )
    assert response.status_code == 302
    order = PurchaseOrder.objects.get(supplier=supplier)
    response = procurement_client.post(
        reverse("procurement:line_create", args=[order.id]),
        {
            "product_variant": purchasable_variant.id,
            "quantity": "2",
            "unit_cost": "12.3456",
            "description": "Long procurement line",
            "scope_company_id": company.id,
        },
    )
    assert response.status_code == 302
    assert (
        procurement_client.post(reverse("procurement:order_confirm", args=[order.id])).status_code
        == 302
    )
    line = order.lines.get()
    response = procurement_client.post(
        reverse("procurement:order_receive", args=[order.id]),
        {
            "receipt_date": "2026-09-14",
            "idempotency_key": "ui-receipt",
            f"line_{line.id}": "1",
            "scope_company_id": company.id,
        },
        follow=True,
    )
    assert response.status_code == 200
    assert b"Inventory was not changed" in response.content
    assert b"BUY-001" in response.content


@pytest.mark.django_db
def test_stale_receipt_payload_rejects_whole_request(
    procurement_client,
    business_context,
    company,
    draft_purchase_order,
    purchasable_variant,
):
    from businessos.modules.procurement.services import (
        add_purchase_order_line,
        confirm_purchase_order,
    )

    register_manifest(MODULE, enabled=True)
    line = add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=2,
        unit_cost=1,
    )
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    response = procurement_client.post(
        reverse("procurement:order_receive", args=[draft_purchase_order.id]),
        {
            "receipt_date": "2026-09-14",
            "idempotency_key": "stale",
            f"line_{line.id}": "1",
            "line_00000000-0000-0000-0000-000000000001": "1",
            "scope_company_id": company.id,
        },
    )
    assert response.status_code == 403
    assert not draft_purchase_order.receipts.exists()


def _uuid_alias(line_id, alias):
    canonical = str(line_id)
    if alias == "uppercase":
        return canonical.upper()
    if alias == "compact":
        return canonical.replace("-", "")
    if alias == "braces":
        return "{" + canonical + "}"
    raise AssertionError(alias)


@pytest.mark.django_db
@pytest.mark.parametrize("alias", ["uppercase", "compact", "braces"])
def test_receipt_uuid_alias_rejects_entire_http_request(
    procurement_client, business_context, company, draft_purchase_order, purchasable_variant, alias
):
    register_manifest(MODULE, enabled=True)
    valid_line = add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=2,
        unit_cost=1,
    )
    unknown = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    response = procurement_client.post(
        reverse("procurement:order_receive", args=[draft_purchase_order.id]),
        {
            "receipt_date": "2026-09-14",
            "idempotency_key": f"alias-{alias}",
            f"line_{valid_line.id}": "1",
            f"line_{_uuid_alias(unknown, alias)}": "1",
            "scope_company_id": company.id,
        },
    )
    assert response.status_code == 200
    assert b"canonical lowercase hyphenated UUIDs" in response.content
    assert not PurchaseReceipt.objects.exists()
    assert not PurchaseReceiptLine.objects.exists()
    assert not AuditEntry.objects.filter(action="procurement.receipt.posted").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "extra_fields",
    [
        {"same-alias": "uppercase"},
        {"alias-one": "compact", "alias-two": "braces"},
        {"malformed": "not-a-uuid"},
    ],
    ids=["canonical-plus-alias", "two-aliases", "malformed"],
)
def test_receipt_ambiguous_or_malformed_fields_reject_entire_request(
    procurement_client,
    business_context,
    company,
    draft_purchase_order,
    purchasable_variant,
    extra_fields,
):
    register_manifest(MODULE, enabled=True)
    line = add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=2,
        unit_cost=1,
    )
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    data = {
        "receipt_date": "2026-09-14",
        "idempotency_key": "invalid-fields",
        f"line_{line.id}": "1",
        "scope_company_id": company.id,
    }
    for key, value in extra_fields.items():
        suffix = value if key == "malformed" else _uuid_alias(line.id, value)
        data[f"line_{suffix}"] = "1"
    response = procurement_client.post(
        reverse("procurement:order_receive", args=[draft_purchase_order.id]), data
    )
    assert response.status_code == 200
    assert not PurchaseReceipt.objects.exists()
    assert not PurchaseReceiptLine.objects.exists()
    assert not AuditEntry.objects.filter(action="procurement.receipt.posted").exists()


@pytest.mark.django_db
def test_duplicate_canonical_receipt_values_reject_entire_request(
    procurement_client, business_context, company, draft_purchase_order, purchasable_variant
):
    register_manifest(MODULE, enabled=True)
    line = add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=2,
        unit_cost=1,
    )
    confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    response = procurement_client.post(
        reverse("procurement:order_receive", args=[draft_purchase_order.id]),
        {
            "receipt_date": "2026-09-14",
            "idempotency_key": "duplicate-canonical",
            f"line_{line.id}": ["1", "2"],
            "scope_company_id": company.id,
        },
    )
    assert response.status_code == 200
    assert b"exactly once" in response.content
    assert not PurchaseReceipt.objects.exists()
    assert not AuditEntry.objects.filter(action="procurement.receipt.posted").exists()


@pytest.mark.django_db
def test_procurement_document_templates_contain_supported_values(
    procurement_client, business_context, company, supplier, currency, purchasable_variant
):
    register_manifest(MODULE, enabled=True)
    supplier.display_name = "S" * 168
    supplier.save()
    purchasable_variant.sku = "SKU-" + "X" * 52
    purchasable_variant.save()
    order = PurchaseOrder.objects.create(
        company=company,
        number="PO-BOUNDARY",
        supplier=supplier,
        order_date=date(2026, 9, 14),
        currency=currency,
        notes="N" * 168,
    )
    boundary = Decimal(
        "99999999999999.9999" if connection.vendor == "postgresql" else "9999999999.9999"
    )
    line = add_purchase_order_line(
        business_context,
        order_id=order.id,
        product_variant_id=purchasable_variant.id,
        quantity=boundary,
        unit_cost=boundary,
    )
    detail = procurement_client.get(reverse("procurement:order_detail", args=[order.id]))
    assert detail.status_code == 200
    assert b"data-procurement-document-boundary" in detail.content
    assert b"data-procurement-summary" in detail.content
    assert b"data-procurement-lines-scroll" in detail.content
    assert detail.content.count(b"overflow-wrap: anywhere") >= 4
    assert str(boundary).encode() in detail.content
    confirm_purchase_order(business_context, order_id=order.id)
    receipt_form = procurement_client.get(reverse("procurement:order_receive", args=[order.id]))
    assert receipt_form.status_code == 200
    assert b"data-procurement-receipt-form" in receipt_form.content
    assert purchasable_variant.sku.encode() in receipt_form.content
    assert f"line_{line.id}".encode() in receipt_form.content
