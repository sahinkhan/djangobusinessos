from datetime import date
from importlib import import_module

import pytest
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.modules.services import register_manifest
from businessos.modules.party.models import Party
from businessos.modules.sales.models import SalesOrder


@pytest.fixture
def ui_client(client, operator, company):
    operator.is_superuser = True
    operator.save(update_fields=["is_superuser"])
    for module in ("party", "catalog", "sales", "procurement", "inventory"):
        manifest = import_module(f"businessos.modules.{module}.manifest").MODULE
        register_manifest(manifest, enabled=True)
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    return client


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    [
        "party:create",
        "catalog:product_create",
        "sales:order_create",
        "procurement:order_create",
        "inventory:create",
    ],
)
def test_shared_record_forms_keep_native_post_and_company_protection(ui_client, company, url_name):
    response = ui_client.get(reverse(url_name))

    assert response.status_code == 200
    assert b'<form method="post" id="record-form"' in response.content
    assert b'form="record-form"' in response.content
    assert b'name="csrfmiddlewaretoken"' in response.content
    assert b'name="scope_company_id"' in response.content
    assert str(company.id).encode() in response.content
    assert b"hx-post" not in response.content


@pytest.mark.django_db
def test_related_contact_form_uses_the_same_scoped_native_post(ui_client, company):
    party = Party.objects.create(company=company, party_type="person", display_name="Contact")

    response = ui_client.get(reverse("party:contact_create", args=[party.id]))

    assert response.status_code == 200
    assert b'id="record-form"' in response.content
    assert b'name="scope_company_id"' in response.content
    assert b'name="value"' in response.content


@pytest.mark.django_db
def test_invalid_form_keeps_user_input_and_accessible_errors(ui_client, company):
    response = ui_client.post(
        reverse("party:create"),
        {
            "display_name": "Unsaved & retained",
            "party_type": "invalid",
            "scope_company_id": str(company.id),
        },
    )

    assert response.status_code == 200
    assert b"Unsaved &amp; retained" in response.content
    assert b'aria-invalid="true"' in response.content
    assert b'aria-describedby="id_party_type_error"' in response.content
    assert b'id="id_party_type_error"' in response.content
    assert b'role="alert"' in response.content
    assert not Party.objects.exists()


@pytest.mark.django_db
def test_missing_company_explains_access_without_bypassing_scope(ui_client):
    session = ui_client.session
    session.pop(SESSION_COMPANY_KEY)
    session.save()

    home = ui_client.get(reverse("home"))
    denied = ui_client.get(reverse("party:list"))

    assert b"Choose your company to get started" in home.content
    assert b'data-company-selected="false"' in home.content
    assert denied.status_code == 403
    assert b"Select a company to continue" in denied.content
    assert b"?next=%2Fparties%2F" in denied.content


@pytest.mark.django_db
def test_error_page_keeps_permission_denial_and_does_not_leak_order(ui_client, operator, company):
    customer = Party.objects.create(
        company=company, party_type="person", display_name="Restricted customer", is_customer=True
    )
    order = SalesOrder.objects.create(
        company=company,
        number="SO-PRIVATE",
        customer=customer,
        order_date=date.today(),
        currency=company.base_currency,
    )
    operator.is_superuser = False
    operator.save(update_fields=["is_superuser"])

    response = ui_client.get(reverse("sales:order_detail", args=[order.id]))

    assert response.status_code == 403
    assert b"You do not have access to this page" in response.content
    assert b"SO-PRIVATE" not in response.content
    assert b"Restricted customer" not in response.content
