from datetime import date

import pytest
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import UserCompanyAccess
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.services import register_manifest
from businessos.modules.catalog.models import Product
from businessos.modules.catalog.services import create_simple_product
from businessos.modules.party.models import Party
from businessos.modules.party.services import create_party
from businessos.modules.sales.manifest import MODULE as SALES_MANIFEST
from businessos.modules.sales.models import SalesOrder


@pytest.fixture
def sales_client(client, operator, company):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    return client


@pytest.mark.django_db
def test_sales_module_gating_controls_navigation_and_direct_http(sales_client):
    module = BusinessModule.objects.get(code="sales")
    assert module.is_enabled is False
    disabled_home = sales_client.get(reverse("home"))
    assert b'href="/sales/orders/"' not in disabled_home.content
    assert sales_client.get(reverse("sales:order_list")).status_code == 404

    register_manifest(SALES_MANIFEST, enabled=True)
    enabled_home = sales_client.get(reverse("home"))
    assert b'href="/sales/orders/"' in enabled_home.content
    assert sales_client.get(reverse("sales:order_list")).status_code == 200


@pytest.mark.django_db
def test_customer_to_order_to_confirm_ui_flow(
    sales_client, business_context, company, currency, uom
):
    register_manifest(SALES_MANIFEST, enabled=True)
    customer = create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="UI Customer",
        is_customer=True,
    )
    variant = create_simple_product(
        business_context,
        name="UI Service",
        sku="UI-SVC-1",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
    ).variants.get()
    create_response = sales_client.post(
        reverse("sales:order_create"),
        {
            "customer": str(customer.id),
            "order_date": date.today().isoformat(),
            "currency": str(currency.id),
            "notes": "UI smoke order",
            "scope_company_id": str(company.id),
        },
    )
    order = SalesOrder.objects.get(customer=customer)
    line_response = sales_client.post(
        reverse("sales:line_create", args=[order.id]),
        {
            "product_variant": str(variant.id),
            "quantity": "2",
            "unit_price": "75.50",
            "description": "Delivery milestone",
            "scope_company_id": str(company.id),
        },
    )
    confirm_response = sales_client.post(
        reverse("sales:order_confirm", args=[order.id]), follow=True
    )
    order.refresh_from_db()

    assert create_response.status_code == 302
    assert line_response.status_code == 302
    assert confirm_response.status_code == 200
    assert order.status == SalesOrder.Status.CONFIRMED
    assert b"UI Customer" in confirm_response.content
    assert b"UI-SVC-1" in confirm_response.content
    assert b"151.00" in confirm_response.content
    assert b"does not reserve or issue stock" in confirm_response.content
    assert b"Edit order" not in confirm_response.content


@pytest.mark.django_db
def test_sales_form_rejects_stale_company_scope(
    sales_client, business_context, operator, company, currency
):
    register_manifest(SALES_MANIFEST, enabled=True)
    customer = create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Scoped Customer",
        is_customer=True,
    )
    opened = sales_client.get(reverse("sales:order_create"))
    other_company = type(company).objects.create(
        code="SWITCH", name="Switched Company", base_currency=currency
    )
    UserCompanyAccess.objects.create(user=operator, company=other_company)
    session = sales_client.session
    session[SESSION_COMPANY_KEY] = str(other_company.id)
    session.save()
    response = sales_client.post(
        reverse("sales:order_create"),
        {
            "customer": str(customer.id),
            "order_date": date.today().isoformat(),
            "currency": str(currency.id),
            "scope_company_id": str(opened.context["form"].initial["scope_company_id"]),
        },
    )

    assert response.status_code == 200
    assert b"Company scope changed after this form was opened" in response.content
    assert not SalesOrder.objects.exists()
