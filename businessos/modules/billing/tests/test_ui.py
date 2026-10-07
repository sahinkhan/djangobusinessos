from uuid import uuid4

import pytest
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import RolePermission
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.modules.billing import services
from businessos.modules.billing.models import Invoice

pytestmark = pytest.mark.django_db


@pytest.fixture
def browser(client, operator, company, billing_role):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.pk)
    session.save()
    BusinessModule.objects.filter(code="billing").update(is_enabled=True)
    return client


@pytest.mark.parametrize(
    "action", ["create", "edit", "line_create", "line_edit", "line_remove", "issue"]
)
def test_stale_company_http(browser, business_context, invoice, line, party, currency, action):
    kwargs = {} if action == "create" else {"invoice_id": invoice.pk}
    if action in {"line_edit", "line_remove"}:
        kwargs["line_id"] = line.pk
    data = {
        "scope_company_id": str(uuid4()),
        "bill_to_party": str(party.pk),
        "currency": str(currency.pk),
        "invoice_date": "2026-10-07",
        "notes": "Wrong scope",
        "description": "Wrong scope",
        "quantity": "4",
        "unit_price": "1",
    }
    before = AuditEntry.objects.count()
    response = browser.post(reverse(f"billing:{action}", kwargs=kwargs), data)
    assert response.status_code in [200, 400]
    assert b"Company scope changed" in response.content
    invoice.refresh_from_db()
    line.refresh_from_db()
    assert invoice.status == "draft" and invoice.notes == "" and line.quantity == 2
    assert Invoice.objects.count() == 1 and AuditEntry.objects.count() == before


@pytest.mark.parametrize(
    "action,permission",
    [
        ("list", "view"),
        ("detail", "view"),
        ("create", "create"),
        ("edit", "update"),
        ("line_create", "update"),
        ("line_edit", "update"),
        ("line_remove", "update"),
        ("issue", "issue"),
    ],
)
def test_http_action_permissions(browser, invoice, line, billing_role, company, action, permission):
    RolePermission.objects.filter(
        role=billing_role, permission__code=f"billing.invoice.{permission}"
    ).delete()
    kwargs = {} if action in {"list", "create"} else {"invoice_id": invoice.pk}
    if action in {"line_edit", "line_remove"}:
        kwargs["line_id"] = line.pk
    url = reverse(f"billing:{action}", kwargs=kwargs)
    if action not in {"line_remove", "issue"}:
        assert browser.get(url).status_code == 403
    if action not in {"list", "detail"}:
        assert browser.post(url, {"scope_company_id": str(company.pk)}).status_code == 403


@pytest.mark.parametrize("missing", [True, False])
def test_module_gating(browser, invoice, missing):
    module = BusinessModule.objects.filter(code="billing")
    if missing:
        module.delete()
    else:
        module.update(is_enabled=False)
    assert browser.get(reverse("billing:list")).status_code == 404
    assert b'href="/billing/invoices/"' not in browser.get("/").content


def test_pages_flow_pagination_and_payment_wording(
    browser, business_context, invoice, line, party, currency, company
):
    assert b'href="/billing/invoices/"' in browser.get("/").content
    for _ in range(50):
        services.create_invoice(
            business_context, bill_to_party_id=party.pk, currency_id=currency.pk
        )
    response = browser.get(reverse("billing:list"), {"q": "Generic", "status": "draft"})
    assert response.status_code == 200 and len(response.context["invoices"]) == 50
    assert response.context["page_obj"].paginator.count == 51
    assert b"q=Generic" in response.content and b"status=draft" in response.content
    assert len(browser.get(reverse("billing:list"), {"page": "2"}).context["invoices"]) == 1
    detail = browser.get(reverse("billing:detail", args=[invoice.pk]))
    assert b"Invoice total" in detail.content and b"Payment status unavailable" in detail.content
    for forbidden in [b"Amount paid", b"Amount due", b"Outstanding", b"Unpaid", b"Partially paid"]:
        assert forbidden not in detail.content
    result = browser.post(
        reverse("billing:issue", args=[invoice.pk]), {"scope_company_id": str(company.pk)}
    )
    assert result.status_code == 302
    detail = browser.get(reverse("billing:detail", args=[invoice.pk]))
    assert b"Issue invoice</button>" not in detail.content
    assert b"Add line</a>" not in detail.content


def test_mutation_http_flow_and_validation(browser, party, currency, company):
    header = {
        "scope_company_id": str(company.pk),
        "bill_to_party": str(party.pk),
        "currency": str(currency.pk),
        "invoice_date": "2026-10-07",
        "notes": "HTTP",
    }
    response = browser.post(reverse("billing:create"), header)
    assert response.status_code == 302
    invoice = Invoice.objects.get(notes="HTTP")
    assert browser.get(response.url).status_code == 200
    bad = browser.post(
        reverse("billing:line_create", args=[invoice.pk]),
        {
            "scope_company_id": str(company.pk),
            "description": "",
            "quantity": "0",
            "unit_price": "NaN",
        },
    )
    assert bad.status_code == 200 and bad.context["form"].errors
    assert invoice.lines.count() == 0
    line_data = {
        "scope_company_id": str(company.pk),
        "description": "Generic service",
        "quantity": "0.0001",
        "unit_price": "0",
    }
    assert (
        browser.post(reverse("billing:line_create", args=[invoice.pk]), line_data).status_code
        == 302
    )
    line = invoice.lines.get()
    line_data["quantity"] = "2"
    assert (
        browser.post(
            reverse("billing:line_edit", args=[invoice.pk, line.pk]), line_data
        ).status_code
        == 302
    )
    header["notes"] = "Updated"
    assert browser.post(reverse("billing:edit", args=[invoice.pk]), header).status_code == 302
    assert (
        browser.post(
            reverse("billing:line_remove", args=[invoice.pk, line.pk]),
            {"scope_company_id": str(company.pk)},
        ).status_code
        == 302
    )
    assert invoice.lines.count() == 0
