import pytest
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.modules.catalog.models import Product


@pytest.fixture
def scoped_client(client, operator, company):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    return client


@pytest.mark.django_db
def test_party_workflow_renders_in_shared_ui(scoped_client):
    response = scoped_client.post(
        reverse("party:create"),
        {
            "party_type": "organization",
            "display_name": "Northwind Traders",
            "legal_name": "Northwind Traders Ltd",
            "is_customer": "on",
            "is_supplier": "on",
            "is_active": "on",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert b"Northwind Traders" in response.content
    assert b"Customer" in response.content
    assert b"Supplier" in response.content


@pytest.mark.django_db
def test_user_can_select_an_explicit_company_scope(client, operator, company):
    client.force_login(operator)

    response = client.post(
        reverse("select_company"), {"company": str(company.id), "next": "/parties/"}
    )

    assert response.status_code == 302
    assert response.url == "/parties/"
    assert client.session[SESSION_COMPANY_KEY] == str(company.id)


@pytest.mark.django_db
def test_simple_product_workflow_hides_variant_management(scoped_client, uom):
    response = scoped_client.post(
        reverse("catalog:product_create"),
        {
            "name": "Organic Honey",
            "sku": "HONEY-001",
            "structure": "simple",
            "product_type": "stockable",
            "default_uom": str(uom.id),
            "is_sellable": "on",
            "is_purchasable": "on",
            "is_active": "on",
        },
        follow=True,
    )

    product = Product.objects.get(name="Organic Honey")
    assert response.status_code == 200
    assert product.variants.count() == 1
    assert b"Internal default variant" in response.content
    assert b"Add variant" not in response.content


@pytest.mark.django_db
def test_variable_product_workflow_allows_explicit_additional_variant(scoped_client, uom):
    create_response = scoped_client.post(
        reverse("catalog:product_create"),
        {
            "name": "Premium T-Shirt",
            "sku": "TS-BLK-M",
            "structure": "variable",
            "product_type": "stockable",
            "default_uom": str(uom.id),
            "is_sellable": "on",
            "is_purchasable": "on",
            "is_active": "on",
        },
        follow=True,
    )
    product = Product.objects.get(name="Premium T-Shirt")
    add_response = scoped_client.post(
        reverse("catalog:variant_create", args=[product.id]),
        {"sku": "TS-WHT-L", "is_active": "on"},
        follow=True,
    )

    assert create_response.status_code == 200
    assert add_response.status_code == 200
    assert list(product.variants.order_by("sku").values_list("sku", flat=True)) == [
        "TS-BLK-M",
        "TS-WHT-L",
    ]
    assert b"Assign attributes" in add_response.content
