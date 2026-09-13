from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import UserCompanyAccess
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.services import register_manifest
from businessos.modules.catalog.models import Product
from businessos.modules.catalog.services import create_simple_product
from businessos.modules.party.models import Party
from businessos.modules.party.services import create_party
from businessos.modules.procurement.forms import PurchaseOrderLineForm, _display_quantity
from businessos.modules.procurement.manifest import MODULE as PROCUREMENT_MANIFEST
from businessos.modules.procurement.models import PurchaseOrder, PurchaseReceipt


@pytest.fixture
def procurement_client(client, operator, company):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    return client


@pytest.mark.django_db
def test_module_gating_controls_navigation_and_direct_http(procurement_client):
    module = BusinessModule.objects.get(code="procurement")
    assert module.is_enabled is False
    assert b'href="/procurement/orders/"' not in procurement_client.get(
        reverse("home")
    ).content
    assert procurement_client.get(reverse("procurement:order_list")).status_code == 404

    register_manifest(PROCUREMENT_MANIFEST, enabled=True)
    assert b'href="/procurement/orders/"' in procurement_client.get(reverse("home")).content
    assert procurement_client.get(reverse("procurement:order_list")).status_code == 200


@pytest.mark.django_db
def test_supplier_order_partial_receipt_ui_flow(
    procurement_client, business_context, company, currency, uom
):
    register_manifest(PROCUREMENT_MANIFEST, enabled=True)
    supplier = create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="UI Supplier",
        is_supplier=True,
    )
    variant = create_simple_product(
        business_context,
        name="UI Supply",
        sku="UI-PO-1",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    ).variants.get()
    response = procurement_client.post(
        reverse("procurement:order_create"),
        {
            "supplier": str(supplier.id),
            "order_date": date.today().isoformat(),
            "currency": str(currency.id),
            "notes": "UI smoke order",
            "scope_company_id": str(company.id),
        },
    )
    order = PurchaseOrder.objects.get(supplier=supplier)
    line_response = procurement_client.post(
        reverse("procurement:line_create", args=[order.id]),
        {
            "product_variant": str(variant.id),
            "quantity": "10",
            "unit_cost": "0.0049",
            "description": "Partial receipt UI",
            "position": "99",
            "scope_company_id": str(company.id),
        },
    )
    confirm_response = procurement_client.post(
        reverse("procurement:order_confirm", args=[order.id]), follow=True
    )
    receipt_response = procurement_client.post(
        reverse("procurement:order_receive", args=[order.id]),
        {
            "receipt_date": date.today().isoformat(),
            "idempotency_key": "ui-receipt-1",
            f"line_{order.lines.get().id}": "4",
            "scope_company_id": str(company.id),
        },
        follow=True,
    )
    order.refresh_from_db()
    receipt = PurchaseReceipt.objects.get(purchase_order=order)

    assert response.status_code == line_response.status_code == 302
    assert order.lines.get().position == 1
    assert confirm_response.status_code == 200
    assert b"No stock was created" in confirm_response.content
    assert order.status == PurchaseOrder.Status.CONFIRMED
    assert receipt_response.status_code == 200
    assert receipt.number.encode() in receipt_response.content
    assert b"Inventory was not changed" in receipt_response.content
    detail = procurement_client.get(reverse("procurement:order_detail", args=[order.id]))
    assert b"0.0049" in detail.content
    assert b">10<" in detail.content
    assert b">4<" in detail.content
    assert b">6<" in detail.content
    assert b"overflow-x-auto" in detail.content


@pytest.mark.django_db
def test_form_rejects_stale_company_scope(
    procurement_client, business_context, operator, company, currency
):
    register_manifest(PROCUREMENT_MANIFEST, enabled=True)
    supplier = create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Scoped Supplier",
        is_supplier=True,
    )
    opened = procurement_client.get(reverse("procurement:order_create"))
    other_company = type(company).objects.create(
        code="SWITCH", name="Switched Company", base_currency=currency
    )
    UserCompanyAccess.objects.create(user=operator, company=other_company)
    session = procurement_client.session
    session[SESSION_COMPANY_KEY] = str(other_company.id)
    session.save()
    response = procurement_client.post(
        reverse("procurement:order_create"),
        {
            "supplier": str(supplier.id),
            "order_date": date.today().isoformat(),
            "currency": str(currency.id),
            "scope_company_id": str(opened.context["form"].initial["scope_company_id"]),
        },
    )
    assert response.status_code == 200
    assert b"Company scope changed after this form was opened" in response.content
    assert not PurchaseOrder.objects.exists()


@pytest.mark.django_db
def test_line_form_uses_exact_decimal_boundaries(company):
    form = PurchaseOrderLineForm(company_id=company.id)
    assert form.fields["quantity"].clean("0.0001") == Decimal("0.0001")
    assert form.fields["unit_cost"].clean("0") == Decimal("0")
    with pytest.raises(ValidationError):
        form.fields["quantity"].clean("0")
    with pytest.raises(ValidationError):
        form.fields["quantity"].clean("0.00001")
    with pytest.raises(ValidationError):
        form.fields["unit_cost"].clean("-0.0001")


def test_quantity_display_preserves_integer_trailing_zeroes():
    assert _display_quantity(Decimal("10")) == "10"
    assert _display_quantity(Decimal("10.0000")) == "10"
    assert _display_quantity(Decimal("0.0040")) == "0.004"
