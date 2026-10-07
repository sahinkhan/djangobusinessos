from uuid import uuid4

import pytest
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import RolePermission
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.modules.models import BusinessModule
from businessos.modules.payments import services
from businessos.modules.payments.models import Payment

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("action", ["record", "method_create", "method_edit", "method_activity"])
def test_actual_company_switch_stale_post(browser, operator, company, method, post_data, action):
    from businessos.core.organization.models import Company

    other = Company.objects.create(
        code="SWITCH",
        name="Switched",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    operator.is_superuser = True
    operator.save()
    target = services.create_payment_method(
        BusinessContext(actor_id=operator.pk, company_id=other.pk),
        code="CASH",
        name="Other cash",
    )
    session = browser.session
    session[SESSION_COMPANY_KEY] = str(other.pk)
    session.save()
    data = post_data | {"code": "BANK", "name": "Wrong", "is_active": "false"}
    kwargs = {"method_id": target.pk} if action in {"method_edit", "method_activity"} else {}
    before = AuditEntry.objects.count()
    response = browser.post(reverse(f"payments:{action}", kwargs=kwargs), data)
    assert response.status_code in {200, 400}
    assert b"Company scope changed" in response.content
    target.refresh_from_db()
    assert target.name == "Other cash" and target.is_active
    assert not Payment.objects.exists() and AuditEntry.objects.count() == before


@pytest.fixture
def browser(client, operator, company, payments_role):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.pk)
    session.save()
    BusinessModule.objects.filter(code="payments").update(is_enabled=True)
    return client


@pytest.fixture
def post_data(company, payload):
    return {
        "scope_company_id": str(company.pk),
        "payer_party": str(payload["payer_party_id"]),
        "currency": str(payload["currency_id"]),
        "amount": "12.50",
        "payment_method": str(payload["payment_method_id"]),
        "payment_date": "2026-10-08",
        "idempotency_key": "http-key",
        "notes": "",
        "external_reference": "",
    }


@pytest.mark.parametrize(
    "action,permission",
    [
        ("list", "payment.view"),
        ("detail", "payment.view"),
        ("record", "payment.record"),
        ("methods", "method.view"),
        ("method_create", "method.manage"),
        ("method_edit", "method.manage"),
        ("method_activity", "method.manage"),
    ],
)
def test_http_permissions(
    browser, business_context, payload, method, payments_role, action, permission
):
    receipt = services.record_payment(business_context, **payload)
    RolePermission.objects.filter(
        role=payments_role, permission__code=f"payments.{permission}"
    ).delete()
    kwargs = (
        {"payment_id": receipt.pk}
        if action == "detail"
        else ({"method_id": method.pk} if action in {"method_edit", "method_activity"} else {})
    )
    url = reverse(f"payments:{action}", kwargs=kwargs)
    if action != "method_activity":
        assert browser.get(url).status_code == 403
    if action in {"record", "method_create", "method_edit", "method_activity"}:
        assert browser.post(url, {}).status_code == 403


@pytest.mark.parametrize("action", ["record", "method_create", "method_edit", "method_activity"])
def test_stale_company(browser, method, post_data, action):
    data = post_data | {
        "scope_company_id": str(uuid4()),
        "code": "BANK",
        "name": "Changed",
        "is_active": "false",
    }
    kwargs = {"method_id": method.pk} if action in {"method_edit", "method_activity"} else {}
    before = AuditEntry.objects.count()
    response = browser.post(reverse(f"payments:{action}", kwargs=kwargs), data)
    assert response.status_code in {200, 400}
    assert b"Company scope changed" in response.content
    assert not Payment.objects.exists()
    method.refresh_from_db()
    assert method.name == "Cash" and method.is_active
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("missing", [True, False])
def test_http_only_module_gate(browser, business_context, payload, missing):
    module = BusinessModule.objects.filter(code="payments")
    if missing:
        module.delete()
    else:
        module.update(is_enabled=False)
    assert browser.get(reverse("payments:list")).status_code == 404
    assert b'href="/payments/receipts/"' not in browser.get("/").content
    assert services.record_payment(business_context, **payload).pk


def test_http_retry_and_historical_display(browser, business_context, post_data, method):
    first = browser.post(reverse("payments:record"), post_data)
    assert first.status_code == 302
    services.set_payment_method_active(
        business_context, payment_method_id=method.pk, is_active=False
    )
    retry = browser.post(reverse("payments:record"), post_data)
    assert retry.status_code == 302 and retry.url == first.url
    assert Payment.objects.count() == 1
    detail = browser.get(first.url)
    assert detail.status_code == 200 and b"12.50" in detail.content and b"Cash" in detail.content
    assert b"overflow-wrap: anywhere" in detail.content


def test_action_without_view(browser, post_data, method, payments_role):
    RolePermission.objects.filter(
        role=payments_role, permission__code__in=["payments.method.view", "payments.payment.view"]
    ).delete()
    assert browser.get(reverse("payments:record")).status_code == 200
    assert browser.post(reverse("payments:record"), post_data).status_code == 302
    assert browser.get(reverse("payments:method_edit", args=[method.pk])).status_code == 200


def test_pagination_htmx_fallback(browser, business_context, payload):
    for _ in range(51):
        services.record_payment(business_context, **payload)
    url = reverse("payments:list")
    first = browser.get(url, {"q": "Payer"})
    assert first.status_code == 200 and len(first.context["payments"]) == 50
    second = browser.get(url, {"q": "Payer", "page": 2}, HTTP_HX_REQUEST="true")
    assert second.status_code == 200 and len(second.context["payments"]) == 1
    assert b"q=Payer" in first.content and b'id="list-results"' in first.content
    for index in range(50):
        services.create_payment_method(business_context, code=f"M{index:03}", name="Method")
    response = browser.get(reverse("payments:methods"))
    assert response.status_code == 200 and len(response.context["methods"]) == 50
