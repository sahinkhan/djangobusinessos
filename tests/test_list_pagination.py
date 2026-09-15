from datetime import date

import pytest
from django.urls import reverse
from django.utils import timezone

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.modules.services import register_manifest
from businessos.core.organization.models import Company
from businessos.modules.catalog.manifest import MODULE as CATALOG_MODULE
from businessos.modules.catalog.models import Product
from businessos.modules.catalog.services import create_simple_product
from businessos.modules.inventory import services as inventory_services
from businessos.modules.inventory.manifest import MODULE as INVENTORY_MODULE
from businessos.modules.party.manifest import MODULE as PARTY_MODULE
from businessos.modules.party.models import Party
from businessos.modules.procurement.manifest import MODULE as PROCUREMENT_MODULE
from businessos.modules.procurement.models import PurchaseOrder
from businessos.modules.sales.manifest import MODULE as SALES_MODULE
from businessos.modules.sales.models import SalesOrder

PAGE_SIZE = 50


@pytest.fixture
def pagination_client(client, operator, company):
    operator.is_superuser = True
    operator.save(update_fields=["is_superuser"])
    for manifest in (
        PARTY_MODULE,
        CATALOG_MODULE,
        SALES_MODULE,
        PROCUREMENT_MODULE,
        INVENTORY_MODULE,
    ):
        register_manifest(manifest, enabled=True)
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    return client


@pytest.mark.django_db
def test_large_company_lists_are_filtered_then_paginated(
    pagination_client,
    business_context,
    company,
    currency,
    country,
    language,
    uom,
    warehouse,
):
    customer = Party.objects.create(
        company=company,
        party_type=Party.Type.ORGANIZATION,
        display_name="Needle Customer",
        is_customer=True,
    )
    supplier = Party.objects.create(
        company=company,
        party_type=Party.Type.ORGANIZATION,
        display_name="Needle Supplier",
        is_supplier=True,
    )
    Party.objects.bulk_create(
        [
            Party(
                company=company,
                party_type=Party.Type.ORGANIZATION,
                display_name=f"Paged Party {index:03d}",
            )
            for index in range(51)
        ]
    )
    other_company = Company.objects.create(
        code="OTHER",
        name="Other Company",
        base_currency=currency,
        country=country,
        default_language=language,
    )
    Party.objects.create(
        company=other_company,
        party_type=Party.Type.ORGANIZATION,
        display_name="Paged Party Outside Scope",
    )

    for index in range(51):
        create_simple_product(
            business_context,
            name=f"Paged Product {index:03d}",
            sku=f"PAGE-{index:03d}",
            product_type=Product.Type.SERVICE,
            default_uom_id=uom.id,
        )
        SalesOrder.objects.create(
            company=company,
            number=f"SO-PAGED-{index:03d}",
            customer=customer,
            order_date=date(2026, 9, 16),
            currency=currency,
        )
        PurchaseOrder.objects.create(
            company=company,
            number=f"PO-PAGED-{index:03d}",
            supplier=supplier,
            order_date=date(2026, 9, 16),
            currency=currency,
        )

    stockable = create_simple_product(
        business_context,
        name="Paged Stock Item",
        sku="PAGED-STOCK",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    ).variants.get()
    for index in range(51):
        movement = inventory_services.create_stock_movement(
            business_context,
            movement_type="receipt",
            effective_at=timezone.now(),
            reference=f"Paged movement {index:03d}",
        )
        inventory_services.add_stock_movement_line(
            business_context,
            movement_id=movement.id,
            product_variant_id=stockable.id,
            quantity="1",
            destination_warehouse_id=warehouse.id,
        )
        inventory_services.post_stock_movement(business_context, movement_id=movement.id)

    cases = (
        ("party:list", {"q": "Paged Party", "page": "2"}, "parties"),
        (
            "catalog:product_list",
            {"q": "Paged Product", "type": Product.Type.SERVICE, "page": "2"},
            "products",
        ),
        (
            "sales:order_list",
            {"q": "Needle", "status": SalesOrder.Status.DRAFT, "page": "2"},
            "orders",
        ),
        (
            "procurement:order_list",
            {"q": "Needle", "status": PurchaseOrder.Status.DRAFT, "page": "2"},
            "orders",
        ),
        (
            "inventory:list",
            {"q": "Paged movement", "type": "receipt", "status": "posted", "page": "2"},
            "movements",
        ),
        (
            "inventory:history",
            {
                "warehouse": str(warehouse.id),
                "product_variant": str(stockable.id),
                "page": "2",
            },
            "movements",
        ),
    )
    for route_name, query, collection_name in cases:
        response = pagination_client.get(reverse(route_name), query)

        assert response.status_code == 200
        assert response.context["page_obj"].number == 2
        assert response.context["page_obj"].paginator.per_page == PAGE_SIZE
        assert len(response.context[collection_name]) == 1
        assert b"data-list-filter" in response.content
        assert b"data-list-results-shell" in response.content
        assert b'id="list-results"' in response.content
        assert b"data-list-results-status" in response.content
        assert b"data-list-page" in response.content

    party_page = pagination_client.get(reverse("party:list"), {"q": "Paged Party"})
    assert len(party_page.context["parties"]) == PAGE_SIZE
    assert b"Paged Party Outside Scope" not in party_page.content

    filtered_sales = pagination_client.get(
        reverse("sales:order_list"),
        {"q": "Needle", "status": SalesOrder.Status.DRAFT},
    )
    assert (
        b'href="?q=Needle&amp;status=draft&amp;page=2"'
        in filtered_sales.content
    )
    assert b'data-list-page aria-controls="list-results"' in filtered_sales.content
    assert (
        b'class="btn-secondary" data-app-nav href="?q=Needle'
        not in filtered_sales.content
    )

    htmx_sales = pagination_client.get(
        reverse("sales:order_list"),
        {"q": "Needle", "status": SalesOrder.Status.DRAFT, "page": "2"},
        HTTP_HX_REQUEST="true",
    )
    assert b"<!doctype html>" in htmx_sales.content
    assert b'id="app-content"' in htmx_sales.content
    assert b'id="list-results"' in htmx_sales.content

    empty_page = pagination_client.get(reverse("party:list"), {"q": "No such party"})
    assert empty_page.status_code == 200
    assert empty_page.context["page_obj"].number == 1
    assert list(empty_page.context["parties"]) == []

@pytest.mark.django_db
@pytest.mark.parametrize(
    ("page", "expected_page"),
    [
        (None, 1),
        ("1", 1),
        ("2", 2),
        ("3", 3),
        ("0", 3),
        ("-1", 3),
        ("invalid", 1),
        ("999", 3),
    ],
)
def test_invalid_and_out_of_range_pages_are_controlled(
    pagination_client, company, page, expected_page
):
    Party.objects.bulk_create(
        [
            Party(
                company=company,
                party_type=Party.Type.ORGANIZATION,
                display_name=f"Boundary Party {index:03d}",
            )
            for index in range(101)
        ]
    )
    query = {} if page is None else {"page": page}

    response = pagination_client.get(reverse("party:list"), query)

    assert response.status_code == 200
    assert response.context["page_obj"].number == expected_page
    assert len(response.context["parties"]) == (1 if expected_page == 3 else 50)
