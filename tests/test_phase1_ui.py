import pytest
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import UserCompanyAccess
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.services import register_manifest
from businessos.core.organization.models import Company
from businessos.modules.catalog.manifest import MODULE as CATALOG_MANIFEST
from businessos.modules.catalog.models import Product, ProductCategory
from businessos.modules.party.manifest import MODULE as PARTY_MANIFEST
from businessos.modules.party.models import Party


@pytest.fixture
def enabled_phase1_modules(db):
    register_manifest(PARTY_MANIFEST, enabled=True)
    register_manifest(CATALOG_MANIFEST, enabled=True)


@pytest.fixture
def scoped_client(client, operator, company, enabled_phase1_modules):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    return client


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("code", "url_name", "navigation_url"),
    [
        ("party", "party:list", "/parties/"),
        ("catalog", "catalog:product_list", "/catalog/products/"),
    ],
)
def test_module_state_controls_navigation_and_direct_http_access(
    scoped_client, code, url_name, navigation_url
):
    module = BusinessModule.objects.get(code=code)
    module.is_enabled = False
    module.save()

    disabled_home = scoped_client.get(reverse("home"))
    assert navigation_url.encode() not in disabled_home.content
    assert scoped_client.get(reverse(url_name)).status_code == 404

    module.delete()
    assert scoped_client.get(reverse(url_name)).status_code == 404

    manifest = PARTY_MANIFEST if code == "party" else CATALOG_MANIFEST
    register_manifest(manifest, enabled=True)
    enabled_home = scoped_client.get(reverse("home"))
    assert navigation_url.encode() in enabled_home.content
    assert scoped_client.get(reverse(url_name)).status_code == 200


@pytest.mark.django_db
def test_party_workflow_renders_in_shared_ui(scoped_client, company):
    response = scoped_client.post(
        reverse("party:create"),
        {
            "party_type": "organization",
            "display_name": "Northwind Traders",
            "legal_name": "Northwind Traders Ltd",
            "is_customer": "on",
            "is_supplier": "on",
            "is_active": "on",
            "scope_company_id": str(company.id),
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
def test_simple_product_workflow_hides_variant_management(scoped_client, company, uom):
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
            "scope_company_id": str(company.id),
        },
        follow=True,
    )

    product = Product.objects.get(name="Organic Honey")
    assert response.status_code == 200
    assert product.variants.count() == 1
    assert b"Internal default variant" in response.content
    assert b"Add variant" not in response.content


@pytest.mark.django_db
def test_variable_product_workflow_allows_explicit_additional_variant(
    scoped_client, company, uom
):
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
            "scope_company_id": str(company.id),
        },
        follow=True,
    )
    product = Product.objects.get(name="Premium T-Shirt")
    add_response = scoped_client.post(
        reverse("catalog:variant_create", args=[product.id]),
        {
            "sku": "TS-WHT-L",
            "is_active": "on",
            "scope_company_id": str(company.id),
        },
        follow=True,
    )

    assert create_response.status_code == 200
    assert add_response.status_code == 200
    assert list(product.variants.order_by("sku").values_list("sku", flat=True)) == [
        "TS-BLK-M",
        "TS-WHT-L",
    ]
    assert b"Assign attributes" in add_response.content


@pytest.mark.django_db
def test_root_and_child_category_creation_over_http(scoped_client, company):
    root_response = scoped_client.post(
        reverse("catalog:categories"),
        {
            "name": "Apparel",
            "is_active": "on",
            "scope_company_id": str(company.id),
        },
    )
    root = ProductCategory.objects.get(name="Apparel")
    child_response = scoped_client.post(
        reverse("catalog:categories"),
        {
            "name": "Shirts",
            "parent": str(root.id),
            "is_active": "on",
            "scope_company_id": str(company.id),
        },
    )

    assert root_response.status_code == 302
    assert child_response.status_code == 302
    assert ProductCategory.objects.get(name="Shirts").parent == root


@pytest.mark.django_db
def test_stale_form_cannot_write_after_company_scope_switch(
    scoped_client, operator, company, currency
):
    opened_response = scoped_client.get(reverse("party:create"))
    opened_company_id = opened_response.context["form"].initial["scope_company_id"]
    other_company = Company.objects.create(
        code="OTHER",
        name="Other Company",
        base_currency=currency,
        country=company.country,
        default_language=company.default_language,
    )
    UserCompanyAccess.objects.create(user=operator, company=other_company)
    session = scoped_client.session
    session[SESSION_COMPANY_KEY] = str(other_company.id)
    session.save()

    response = scoped_client.post(
        reverse("party:create"),
        {
            "party_type": "organization",
            "display_name": "Wrong-company write",
            "is_customer": "on",
            "is_active": "on",
            "scope_company_id": str(opened_company_id),
        },
    )

    assert response.status_code == 200
    assert not Party.objects.filter(display_name="Wrong-company write").exists()
    assert b"Company scope changed after this form was opened" in response.content
    assert b"OTHER" in response.content
