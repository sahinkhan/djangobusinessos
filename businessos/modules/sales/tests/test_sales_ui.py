from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserCompanyAccess,
    UserRoleAssignment,
)
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.services import register_manifest
from businessos.core.reference.models import Currency
from businessos.modules.catalog.models import Product
from businessos.modules.catalog.services import create_simple_product
from businessos.modules.party.models import Party
from businessos.modules.party.services import create_party
from businessos.modules.sales.forms import SalesOrderLineForm
from businessos.modules.sales.manifest import (
    MODULE as SALES_MANIFEST,
)
from businessos.modules.sales.manifest import (
    VIEW_ORDERS,
)
from businessos.modules.sales.models import SalesOrder
from businessos.modules.sales.services import add_sales_order_line, create_sales_order
from businessos.modules.sales.templatetags.sales_format import currency_amount


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

    BusinessModule.objects.filter(code="sales").delete()
    missing_home = sales_client.get(reverse("home"))
    assert b'href="/sales/orders/"' not in missing_home.content
    assert sales_client.get(reverse("sales:order_list")).status_code == 404


@pytest.mark.django_db
def test_enabled_module_does_not_bypass_action_permissions(
    sales_client,
    sales_permissions,
    business_context,
    customer,
    currency,
    variant,
):
    register_manifest(SALES_MANIFEST, enabled=True)
    order = create_sales_order(
        business_context,
        customer_id=customer.id,
        order_date=date.today(),
        currency_id=currency.id,
    )
    add_sales_order_line(
        business_context,
        order_id=order.id,
        product_variant_id=variant.id,
        quantity=1,
        unit_price=10,
    )
    RolePermission.objects.filter(role=sales_permissions).exclude(
        permission__code=VIEW_ORDERS
    ).delete()

    detail = sales_client.get(reverse("sales:order_detail", args=[order.id]))
    assert sales_client.get(reverse("sales:order_list")).status_code == 200
    assert detail.status_code == 200
    assert b"Edit order" not in detail.content
    assert b"Confirm order" not in detail.content
    assert sales_client.get(reverse("sales:order_create")).status_code == 403
    assert sales_client.get(reverse("sales:order_edit", args=[order.id])).status_code == 403
    assert sales_client.get(reverse("sales:line_create", args=[order.id])).status_code == 403
    assert sales_client.post(reverse("sales:order_confirm", args=[order.id])).status_code == 403
    assert sales_client.post(reverse("sales:order_cancel", args=[order.id])).status_code == 403


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
            "position": "99",
            "scope_company_id": str(company.id),
        },
    )
    confirm_response = sales_client.post(
        reverse("sales:order_confirm", args=[order.id]), follow=True
    )
    order.refresh_from_db()

    assert create_response.status_code == 302
    assert line_response.status_code == 302
    assert order.lines.get().position == 1
    assert confirm_response.status_code == 200
    assert order.status == SalesOrder.Status.CONFIRMED
    assert b"UI Customer" in confirm_response.content
    assert b"UI-SVC-1" in confirm_response.content
    assert b"151.00" in confirm_response.content
    assert b"does not reserve or issue stock" in confirm_response.content
    assert b"Edit order" not in confirm_response.content


@pytest.mark.django_db
def test_sales_form_rejects_stale_company_scope(
    sales_client, business_context, operator, company, country, currency, language
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
        code="SWITCH",
        name="Switched Company",
        base_currency=currency,
        country=country,
        default_language=language,
    )
    UserCompanyAccess.objects.create(user=operator, company=other_company)
    role = Role.objects.create(company=other_company, code="sales-create", name="Sales creator")
    RolePermission.objects.create(
        role=role,
        permission=Permission.objects.get(code="sales.order.create"),
    )
    UserRoleAssignment.objects.create(user=operator, company=other_company, role=role)
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


@pytest.mark.django_db
def test_quantity_form_uses_exact_decimal_boundaries(company):
    field = SalesOrderLineForm(company_id=company.id).fields["quantity"]

    assert field.clean("0.0001") == Decimal("0.0001")
    with pytest.raises(ValidationError):
        field.clean("0")
    with pytest.raises(ValidationError):
        field.clean("0.00001")


@pytest.mark.django_db
def test_sales_ui_preserves_unit_price_and_currency_precision(
    sales_client, business_context, company, currency, uom
):
    register_manifest(SALES_MANIFEST, enabled=True)
    customer = create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Precision Customer",
        is_customer=True,
    )
    variant = create_simple_product(
        business_context,
        name="Precision Service",
        sku="PRECISION-1",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
    ).variants.get()
    low_price_order = create_sales_order(
        business_context,
        customer_id=customer.id,
        order_date=date.today(),
        currency_id=currency.id,
    )
    add_sales_order_line(
        business_context,
        order_id=low_price_order.id,
        product_variant_id=variant.id,
        quantity=Decimal("100"),
        unit_price=Decimal("0.0049"),
    )

    low_price_page = sales_client.get(
        reverse("sales:order_detail", args=[low_price_order.id])
    )
    assert b"USD 0.0049" in low_price_page.content
    assert b"USD 0.49" in low_price_page.content
    assert b"overflow-wrap: anywhere" in low_price_page.content
    assert b"min-w-0 font-medium text-slate-700" in low_price_page.content
    assert b"card min-w-0 lg:col-span-2" in low_price_page.content

    three_decimal_currency = Currency.objects.create(
        code="TDC", name="Three decimal currency", decimal_places=3
    )
    three_decimal_order = create_sales_order(
        business_context,
        customer_id=customer.id,
        order_date=date.today(),
        currency_id=three_decimal_currency.id,
    )
    add_sales_order_line(
        business_context,
        order_id=three_decimal_order.id,
        product_variant_id=variant.id,
        quantity=1,
        unit_price=Decimal("1.234"),
    )

    detail_page = sales_client.get(
        reverse("sales:order_detail", args=[three_decimal_order.id])
    )
    list_page = sales_client.get(reverse("sales:order_list"))
    assert b"TDC 1.2340" in detail_page.content
    assert b"TDC 1.234" in detail_page.content
    assert b"TDC 1.234" in list_page.content
    assert currency_amount(Decimal("1.2345"), 3) == "1.235"
