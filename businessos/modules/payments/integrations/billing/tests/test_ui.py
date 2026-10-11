import pytest
from django.apps import apps
from django.urls import reverse

if not apps.is_installed("businessos.modules.payments.integrations.billing"):
    pytest.skip("Optional payments_billing deployment is not installed.", allow_module_level=True)

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import RolePermission
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company

from ..manifest import CREATE_ALLOCATIONS, VIEW_ALLOCATIONS
from ..models import PaymentAllocation
from .test_allocations import create

pytestmark = pytest.mark.django_db


@pytest.fixture
def browser(client, operator, company, allocation_role):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.pk)
    session.save()
    BusinessModule.objects.filter(code__in=["billing", "payments", "payments_billing"]).update(
        is_enabled=True
    )
    return client


def data(company, parents):
    return {
        "scope_company_id": str(company.pk),
        "payment_id": str(parents[0].pk),
        "invoice_id": str(parents[1].pk),
        "amount": "10",
        "idempotency_key": "http",
    }


@pytest.mark.parametrize("code", ["billing", "payments", "payments_billing"])
@pytest.mark.parametrize("missing", [False, True])
@pytest.mark.parametrize("method", ["get", "post"])
def test_http_gating(browser, company, parents, code, missing, method):
    if missing:
        BusinessModule.objects.filter(code=code).delete()
    else:
        BusinessModule.objects.filter(code=code).update(is_enabled=False)
    response = getattr(browser, method)(
        reverse("payments_billing:create"), data(company, parents) if method == "post" else {}
    )
    assert response.status_code == 404 and not PaymentAllocation.objects.exists()
    if code != "payments":
        detail = browser.get(reverse("payments:detail", args=[parents[0].pk]))
        assert b"Allocation evidence unavailable" in detail.content
        assert b"Allocate receipt</a>" not in detail.content


@pytest.mark.parametrize(
    "grant", [CREATE_ALLOCATIONS, "payments.payment.view", "billing.invoice.view"]
)
@pytest.mark.parametrize("method", ["get", "post"])
def test_action_permission_matrix(browser, company, parents, allocation_role, grant, method):
    RolePermission.objects.filter(role=allocation_role, permission__code=grant).delete()
    response = getattr(browser, method)(
        reverse("payments_billing:create"), data(company, parents) if method == "post" else {}
    )
    assert response.status_code == 403 and not PaymentAllocation.objects.exists()


def test_normal_post_retry_and_parent_evidence(browser, company, parents):
    url = reverse("payments_billing:create")
    for _ in range(2):
        assert browser.post(url, data(company, parents)).status_code == 302
    assert PaymentAllocation.objects.count() == 1
    assert AuditEntry.objects.filter(action="payments.allocation.created").count() == 1
    for name, identity in (("payments:detail", parents[0].pk), ("billing:detail", parents[1].pk)):
        response = browser.get(reverse(name, args=[identity]))
        assert response.status_code == 200 and b"Applied" in response.content
        assert b"USD 10.00" in response.content and b"USD 90.00" in response.content


def test_stale_company_no_effect(browser, company, parents, operator):
    other = Company.objects.create(
        code="STALE",
        name="Other",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    operator.is_superuser = True
    operator.save()
    assert browser.get(reverse("payments_billing:create")).status_code == 200
    session = browser.session
    session[SESSION_COMPANY_KEY] = str(other.pk)
    session.save()
    before = AuditEntry.objects.count()
    response = browser.post(reverse("payments_billing:create"), data(company, parents))
    assert response.status_code == 200 and b"Company scope changed" in response.content
    assert not PaymentAllocation.objects.exists() and AuditEntry.objects.count() == before


@pytest.mark.parametrize("owner", ["payments", "billing"])
def test_optional_read_denied_does_not_fake_zero(browser, parents, allocation_role, owner):
    RolePermission.objects.filter(role=allocation_role, permission__code=VIEW_ALLOCATIONS).delete()
    response = browser.get(
        reverse(f"{owner}:detail", args=[parents[0 if owner == "payments" else 1].pk])
    )
    assert response.status_code == 200
    assert b"Allocation evidence unavailable (forbidden)" in response.content
    assert b"Outstanding</dt>" not in response.content and b"Unapplied</dt>" not in response.content
    assert b"Allocate receipt</a>" in response.content  # Create authority is independent of read.


def test_http_boundary_and_filter_pagination(browser, business_context, parents):
    for index in range(51):
        create(business_context, parents, amount="0.10", key=str(index))
    url = reverse("payments:detail", args=[parents[0].pk])
    response = browser.get(url, {"allocation_page": 2, "allocation_q": "PAY-"})
    assert response.status_code == 200
    assert b"Page 2 of 2" in response.content
    assert b"allocation_q=PAY-" in response.content
    assert b"USD 5.10" in response.content and b"USD 94.90" in response.content
    assert b"overflow-x-auto" in response.content and b"overflow-wrap: anywhere" in response.content
    htmx = browser.get(url, HTTP_HX_REQUEST="true")
    assert htmx.status_code == 200 and b"data-allocation-evidence" in htmx.content


def test_csrf_required(company, parents, operator, allocation_role):
    from django.test import Client

    browser = Client(enforce_csrf_checks=True)
    browser.force_login(operator)
    session = browser.session
    session[SESSION_COMPANY_KEY] = str(company.pk)
    session.save()
    BusinessModule.objects.filter(code__in=["billing", "payments", "payments_billing"]).update(
        is_enabled=True
    )
    assert (
        browser.post(reverse("payments_billing:create"), data(company, parents)).status_code == 403
    )
    assert not PaymentAllocation.objects.exists()


def test_invalid_form_errors_and_get_is_safe(browser, company, parents):
    before = AuditEntry.objects.count()
    assert (
        browser.get(reverse("payments_billing:create"), data(company, parents)).status_code == 200
    )
    response = browser.post(
        reverse("payments_billing:create"), data(company, parents) | {"amount": "NaN"}
    )
    assert response.status_code == 200 and b"finite" in response.content
    assert not PaymentAllocation.objects.exists() and AuditEntry.objects.count() == before


@pytest.mark.parametrize("page", ["bad", "0", "-1"])
def test_invalid_history_query_is_input_error(browser, parents, page):
    response = browser.get(
        reverse("payments:detail", args=[parents[0].pk]), {"allocation_page": page}
    )
    assert response.status_code == 400
    assert not PaymentAllocation.objects.exists()


@pytest.mark.parametrize("owner", ["billing", "payments"])
@pytest.mark.parametrize("scope", ["missing", "malformed", "inactive"])
def test_owner_scope_denial_retains_normal_403(browser, company, parents, owner, scope):
    if scope == "inactive":
        Company.objects.filter(pk=company.pk).update(is_active=False)
    else:
        session = browser.session
        if scope == "missing":
            session.pop(SESSION_COMPANY_KEY)
        else:
            session[SESSION_COMPANY_KEY] = "not-a-company-uuid"
        session.save()
    response = browser.get(
        reverse(f"{owner}:detail", args=[parents[0 if owner == "payments" else 1].pk])
    )
    assert response.status_code == 403
    assert b"Access required" in response.content
    assert b"PermissionDenied at" not in response.content
    assert b"data-allocation-evidence" not in response.content
    assert not PaymentAllocation.objects.exists()
