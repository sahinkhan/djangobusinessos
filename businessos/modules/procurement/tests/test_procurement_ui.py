from datetime import date

import pytest
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.services import register_manifest
from businessos.modules.procurement.manifest import MODULE
from businessos.modules.procurement.models import PurchaseOrder


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
