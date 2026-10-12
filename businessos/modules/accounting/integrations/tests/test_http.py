import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import RolePermission
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.modules.accounting.integrations.admission import permissions
from businessos.modules.accounting.models import JournalEntry
from businessos.modules.payments.integrations.billing.services import create_payment_allocation

from .test_outcomes import invoice_post

pytestmark = pytest.mark.django_db


@pytest.fixture
def browser(client, operator, company, outcomes):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.pk)
    session.save()
    BusinessModule.objects.update(is_enabled=True)
    return client


def action(effect, invoice, allocation):
    return reverse(
        "accounting_payments_billing:post" if effect == "allocation" else "accounting_billing:post",
        args=[allocation.pk if effect == "allocation" else invoice.pk],
    )


def data(company, outcomes, effect):
    return {
        "scope_company_id": str(company.pk),
        "journal_id": str(outcomes["journal"].pk),
        "ar_account_id": str(outcomes["ar"].pk),
        "cash_account_id" if effect == "allocation" else "revenue_account_id": str(
            outcomes["cash" if effect == "allocation" else "revenue"].pk
        ),
    }


GRANTS = [
    (effect, grant)
    for effect in ("invoice", "allocation")
    for grant in permissions(allocation=effect == "allocation", create=True)
]


@pytest.mark.parametrize("effect,grant", GRANTS)
@pytest.mark.parametrize("method", ["get", "post"])
def test_complete_action_rbac(
    browser, business_context, outcomes, company, outcome_role, effect, grant, method
):
    invoice, _, allocation = outcomes["sources"]()
    if effect == "allocation":
        invoice_post(business_context, outcomes, invoice)
    before = JournalEntry.objects.count(), AuditEntry.objects.count()
    RolePermission.objects.filter(role=outcome_role, permission__code=grant).delete()
    response = getattr(browser, method)(
        action(effect, invoice, allocation), data(company, outcomes, effect)
    )
    assert response.status_code == 403
    assert before == (JournalEntry.objects.count(), AuditEntry.objects.count())


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
@pytest.mark.parametrize("code", ["accounting", "accounting_billing", "billing"])
@pytest.mark.parametrize("missing", [False, True])
def test_module_admission(browser, outcomes, effect, code, missing):
    invoice, _, allocation = outcomes["sources"]()
    if missing:
        BusinessModule.objects.filter(code=code).delete()
    else:
        BusinessModule.objects.filter(code=code).update(is_enabled=False)
    assert browser.get(action(effect, invoice, allocation)).status_code == 404
    assert not JournalEntry.objects.exists()


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
def test_create_does_not_imply_view_and_normal_post(
    browser, business_context, outcomes, company, outcome_role, effect
):
    invoice, _, allocation = outcomes["sources"]()
    if effect == "allocation":
        invoice_post(business_context, outcomes, invoice)
    own = "accounting_payments_billing" if effect == "allocation" else "accounting_billing"
    RolePermission.objects.filter(
        role=outcome_role, permission__code=f"{own}.posting.view"
    ).delete()
    url = action(effect, invoice, allocation)
    before = AuditEntry.objects.count()
    assert browser.get(url).status_code == 200
    assert AuditEntry.objects.count() == before
    for _ in range(2):
        assert browser.post(url, data(company, outcomes, effect)).status_code == 302
    assert JournalEntry.objects.count() == (2 if effect == "allocation" else 1)


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
def test_stale_form_scope(browser, business_context, outcomes, company, effect):
    from uuid import uuid4

    invoice, _, allocation = outcomes["sources"]()
    if effect == "allocation":
        invoice_post(business_context, outcomes, invoice)
    before = JournalEntry.objects.count(), AuditEntry.objects.count()
    response = browser.post(
        action(effect, invoice, allocation),
        data(company, outcomes, effect) | {"scope_company_id": str(uuid4())},
    )
    assert response.status_code == 200 and b"Company scope changed" in response.content
    assert before == (JournalEntry.objects.count(), AuditEntry.objects.count())


@pytest.mark.parametrize("effect", ["invoice", "allocation"])
def test_csrf(browser, operator, company, outcomes, effect):
    invoice, _, allocation = outcomes["sources"]()
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(operator)
    session = strict.session
    session[SESSION_COMPANY_KEY] = str(company.pk)
    session.save()
    assert (
        strict.post(
            action(effect, invoice, allocation), data(company, outcomes, effect)
        ).status_code
        == 403
    )
    assert not JournalEntry.objects.exists()


def test_zero_and_prerequisite_have_no_fake_action(browser, outcomes, company):
    zero, _, _ = outcomes["sources"]("0", None)
    response = browser.get(reverse("accounting_billing:post", args=[zero.pk]))
    assert (
        b"No accounting effect" in response.content
        and b"<form" not in response.content.split(b"data-accounting-outcome")[1]
    )
    assert (
        browser.post(
            reverse("accounting_billing:post", args=[zero.pk]), data(company, outcomes, "invoice")
        ).status_code
        == 400
    )
    invoice, _, allocation = outcomes["sources"]()
    response = browser.get(action("allocation", invoice, allocation))
    assert b"invoice_accounting_not_posted" in response.content
    assert b"Post Accounting outcome</a>" not in response.content
    assert (
        browser.post(
            action("allocation", invoice, allocation), data(company, outcomes, "allocation")
        ).status_code
        == 400
    )
    assert not JournalEntry.objects.exists()


def test_parent_and_history_bounds(browser, business_context, outcomes):
    invoice, payment, allocation = outcomes["sources"]()
    invoice_post(business_context, outcomes, invoice)
    for i in range(51):
        create_payment_allocation(
            business_context,
            payment_id=payment.pk,
            invoice_id=invoice.pk,
            amount="0.10",
            idempotency_key=f"history-{i}",
        )
    url = reverse("payments:detail", args=[payment.pk])
    with CaptureQueriesContext(connection) as first:
        response = browser.get(url)
    assert response.status_code == 200 and response.content.count(b">Accounting outcome</a>") == 50
    with CaptureQueriesContext(connection) as second:
        response = browser.get(
            url, {"allocation_page": 2, "allocation_q": "PAY-"}, HTTP_HX_REQUEST="true"
        )
    assert response.status_code == 200 and response.content.count(b">Accounting outcome</a>") == 2
    assert b"Page 2 of 2" in response.content and b"allocation_q=PAY-" in response.content
    assert b"USD 45.10" in response.content and b"USD 54.90" in response.content
    assert abs(len(first) - len(second)) <= 3  # No certificate/query per history row.
    response = browser.get(reverse("billing:detail", args=[invoice.pk]))
    assert response.status_code == 200 and b"data-accounting-outcome" in response.content
    assert b"Posted" in response.content and b"USD 100.00" in response.content
