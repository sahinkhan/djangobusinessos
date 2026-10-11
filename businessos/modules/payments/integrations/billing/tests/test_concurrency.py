from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Event
from time import monotonic, sleep
from unittest.mock import patch

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.http import Http404
from django.test import Client
from django.urls import reverse

if not apps.is_installed("businessos.modules.payments.integrations.billing"):
    pytest.skip("Optional payments_billing deployment is not installed.", allow_module_level=True)

from businessos.core.access import services as access
from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import Permission
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company
from businessos.modules.billing import services as billing
from businessos.modules.billing import views as billing_views
from businessos.modules.billing.models import InvoiceLine

from .. import selectors
from ..admission import http_admission
from ..manifest import CREATE_ALLOCATIONS
from ..models import PaymentAllocation
from .test_allocations import create

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Requires real PostgreSQL row blocking and separate worker connections.")


def worker(operation, ready, pid):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET statement_timeout='20s'")
            cursor.execute("SELECT pg_backend_pid()")
            pid.append(cursor.fetchone()[0])
        ready.set()
        return operation()
    finally:
        connections.close_all()


def blocked(pid, *, holder=None):
    deadline = monotonic() + 10
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            if holder is None:
                cursor.execute("SELECT pg_backend_pid()=ANY(pg_blocking_pids(%s))", [pid])
            else:
                cursor.execute("SELECT %s=ANY(pg_blocking_pids(%s))", [holder, pid])
            if cursor.fetchone()[0]:
                return
            sleep(0.01)  # Poll observed server state, never infer a lock from a delay.
    pytest.fail("Worker never blocked on the held PostgreSQL row lock.")


def race(first, second, *, error=None):
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            result = first()
            future = pool.submit(worker, second, ready, pid)
            assert ready.wait(10)
            blocked(pid[0])
        if error is not None:
            with pytest.raises(error):
                future.result(20)
            return result, None
        return result, future.result(20)


@pytest.mark.parametrize("shape", ["pair", "same_payment", "same_invoice"])
@pytest.mark.parametrize("amount", ["40", "50", "60"])
@pytest.mark.parametrize("reverse", [False, True])
def test_financial_capacity_races(
    business_context, parents, financial_factory, shape, amount, reverse
):
    alternate = financial_factory()
    second = (
        parents
        if shape == "pair"
        else (parents[0], alternate[1])
        if shape == "same_payment"
        else (alternate[0], parents[1])
    )
    first, second = (second, parents) if reverse else (parents, second)
    race(
        lambda: create(business_context, first, amount=amount, key="winner"),
        lambda: create(business_context, second, amount=amount, key="waiter"),
        error=ValidationError if amount == "60" else None,
    )
    assert PaymentAllocation.objects.count() == (1 if amount == "60" else 2)
    assert (
        AuditEntry.objects.filter(action="payments.allocation.created").count()
        == PaymentAllocation.objects.count()
    )
    for pair in (parents, alternate):
        assert selectors.payment_allocation_evidence(business_context, pair[0].pk).remaining >= 0
        assert selectors.invoice_allocation_evidence(business_context, pair[1].pk).remaining >= 0


@pytest.mark.parametrize("conflict", [False, True])
@pytest.mark.parametrize("reverse", [False, True])
def test_keyed_races(business_context, parents, conflict, reverse):
    amounts = ("20", "30") if conflict else ("20", "20.00000000")
    if reverse:
        amounts = amounts[::-1]
    first, second = race(
        lambda: create(business_context, parents, amount=amounts[0]),
        lambda: create(business_context, parents, amount=amounts[1]),
        error=ValidationError if conflict else None,
    )
    if not conflict:
        assert first.pk == second.pk and first.created_at == second.created_at
    assert PaymentAllocation.objects.count() == 1
    assert AuditEntry.objects.filter(action="payments.allocation.created").count() == 1


@pytest.mark.parametrize(
    "revocation", ["role", "role_permission", "permission", "company_access", "actor", "company"]
)
@pytest.mark.parametrize("retry", [False, True])
def test_revocation_after_company_wait(
    business_context, parents, allocation_role, operator, company, revocation, retry
):
    if retry:
        create(business_context, parents)
    root = get_user_model().objects.create_superuser("allocation-root@synthetic.test", "test-only")
    admin = BusinessContext(actor_id=root.pk, company_id=company.pk)
    access.register_core_permissions()

    def revoke():
        Company.objects.select_for_update().get(pk=company.pk)
        if revocation == "role":
            access.revoke_role(admin, user_id=operator.pk, role_id=allocation_role.pk)
        elif revocation == "role_permission":
            access.revoke_role_permission(
                admin, role_id=allocation_role.pk, permission_code=CREATE_ALLOCATIONS
            )
        elif revocation == "company_access":
            access.revoke_company_access(admin, user_id=operator.pk)
        elif revocation == "permission":
            Permission.objects.filter(code=CREATE_ALLOCATIONS).update(is_active=False)
        elif revocation == "actor":
            get_user_model().objects.filter(pk=operator.pk).update(is_active=False)
        else:
            Company.objects.filter(pk=company.pk).update(is_active=False)
        return AuditEntry.objects.count()

    before, _ = race(revoke, lambda: create(business_context, parents), error=PermissionDenied)
    assert PaymentAllocation.objects.count() == int(retry)
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("parent", ["payment", "invoice"])
@pytest.mark.parametrize(
    "grant", [CREATE_ALLOCATIONS, "payments.payment.view", "billing.invoice.view"]
)
def test_permission_recheck_after_parent_wait(business_context, parents, parent, grant):
    # Raw administrative permission retirement does not take Company. This probes
    # the additional post-parent-wait check instead of relying on Company ordering.
    model = type(parents[0 if parent == "payment" else 1])
    identity = parents[0 if parent == "payment" else 1].pk

    def hold_and_revoke():
        model.objects.select_for_update().get(pk=identity)
        Permission.objects.filter(code=grant).update(is_active=False)

    race(hold_and_revoke, lambda: create(business_context, parents), error=PermissionDenied)
    assert not PaymentAllocation.objects.exists()


@pytest.mark.parametrize("issue_first", [False, True])
def test_issue_vs_allocation(business_context, financial_factory, issue_first):
    parents = financial_factory(issued=False)

    def issue():
        return billing.issue_invoice(business_context, parents[1].pk)

    def allocate():
        return create(business_context, parents)

    if issue_first:
        race(issue, allocate)
        assert PaymentAllocation.objects.count() == 1
    else:

        def failed_allocation():
            Company.objects.select_for_update().get(pk=business_context.company_id)
            with pytest.raises(ValidationError):
                with transaction.atomic():
                    allocate()

        race(failed_allocation, issue)
        assert not PaymentAllocation.objects.exists()


@pytest.mark.parametrize("edit_first", [False, True])
def test_draft_edit_issue_vs_allocation(business_context, financial_factory, edit_first):
    parents = financial_factory(issued=False)
    line = InvoiceLine.objects.get(invoice_id=parents[1].pk)

    def edit_and_issue():
        billing.update_invoice_line(
            business_context,
            parents[1].pk,
            line.pk,
            description="Edited",
            quantity="1",
            unit_price="25",
        )
        return billing.issue_invoice(business_context, parents[1].pk)

    if edit_first:
        race(edit_and_issue, lambda: create(business_context, parents, amount="25"))
        assert selectors.invoice_allocation_evidence(business_context, parents[1].pk).remaining == 0
    else:

        def draft_attempt():
            Company.objects.select_for_update().get(pk=business_context.company_id)
            with pytest.raises(ValidationError):
                with transaction.atomic():
                    create(business_context, parents, amount="25")

        race(draft_attempt, edit_and_issue)
        assert not PaymentAllocation.objects.exists()


@pytest.mark.parametrize("disable_first", [False, True])
@pytest.mark.parametrize("code", ["billing", "payments", "payments_billing"])
def test_http_disable_admission_race(business_context, parents, disable_first, code):
    BusinessModule.objects.filter(code__in=["billing", "payments", "payments_billing"]).update(
        is_enabled=True
    )

    def disable():
        return BusinessModule.objects.filter(code=code).update(is_enabled=False)

    def post():
        with http_admission(business_context, CREATE_ALLOCATIONS):
            return create(business_context, parents)

    first, second = (disable, post) if disable_first else (post, disable)
    race(first, second, error=Http404 if disable_first else None)
    assert PaymentAllocation.objects.count() == int(not disable_first)
    assert not BusinessModule.objects.get(code=code).is_enabled


@pytest.mark.parametrize("parent", ["payment", "invoice"])
@pytest.mark.parametrize("allocation_first", [False, True])
def test_summary_vs_allocation_coherent(business_context, parents, parent, allocation_first):
    selector = (
        selectors.payment_allocation_evidence
        if parent == "payment"
        else selectors.invoice_allocation_evidence
    )
    identity = parents[0 if parent == "payment" else 1].pk

    def summary():
        return selector(business_context, identity)

    def allocate():
        return create(business_context, parents)

    first, second = race(
        allocate if allocation_first else summary, summary if allocation_first else allocate
    )
    evidence = second if allocation_first else first
    assert evidence.applied == (10 if allocation_first else 0)
    assert len(evidence.history) == evidence.count == int(allocation_first)
    assert evidence.remaining == (90 if allocation_first else 100)


@pytest.mark.parametrize("edit_first", [False, True])
def test_parent_page_and_allocation_evidence_share_read_boundary(
    business_context, financial_factory, operator, company, edit_first
):
    parents = financial_factory(issued=False)
    line = InvoiceLine.objects.get(invoice_id=parents[1].pk)
    browser = Client()
    browser.force_login(operator)
    session = browser.session
    session[SESSION_COMPANY_KEY] = str(company.pk)
    session.save()
    BusinessModule.objects.filter(code__in=["billing", "payments", "payments_billing"]).update(
        is_enabled=True
    )
    url = reverse("billing:detail", args=[parents[1].pk])

    def edit_and_issue():
        billing.update_invoice_line(
            business_context,
            parents[1].pk,
            line.pk,
            description="Edited",
            quantity="1",
            unit_price="25",
        )
        return billing.issue_invoice(business_context, parents[1].pk)

    if edit_first:
        _, response = race(edit_and_issue, lambda: browser.get(url))
    else:
        loaded, continue_render = Event(), Event()
        read_ready, edit_ready = Event(), Event()
        read_pid, edit_pid = [], []
        original_render = billing_views.render

        def paused_render(request, template, context):
            # The ordinary owner selector has already materialized draft lines.
            assert context["invoice"].total == Decimal("100")
            loaded.set()
            assert continue_render.wait(10)
            # Optional evidence is evaluated by context processors only now.
            return original_render(request, template, context)

        with patch.object(billing_views, "render", paused_render):
            with ThreadPoolExecutor(max_workers=2) as pool:
                read = pool.submit(worker, lambda: browser.get(url), read_ready, read_pid)
                try:
                    assert read_ready.wait(10) and loaded.wait(10)
                    edit = pool.submit(worker, edit_and_issue, edit_ready, edit_pid)
                    assert edit_ready.wait(10)
                    blocked(edit_pid[0], holder=read_pid[0])
                finally:
                    continue_render.set()
                response = read.result(20)
                edit.result(20)

    assert response.status_code == 200
    invoice = response.context["invoice"]
    evidence = response.context["allocation_evidence"]
    if edit_first:
        assert invoice.status == "issued" and invoice.total == Decimal("25")
        assert evidence.state == "AVAILABLE"
        assert evidence.original == evidence.remaining == Decimal("25")
    else:
        assert invoice.status == "draft" and invoice.total == Decimal("100")
        assert evidence.state == "UNAVAILABLE" and evidence.original is None
        assert b"Outstanding</dt>" not in response.content
    fresh = browser.get(url)
    assert fresh.context["invoice"].total == Decimal("25")
    assert fresh.context["allocation_evidence"].remaining == Decimal("25")
    assert not PaymentAllocation.objects.exists()


def test_uncommitted_failure_and_response_loss_retry(business_context, parents):
    with pytest.raises(RuntimeError):
        with transaction.atomic():
            create(business_context, parents)
            raise RuntimeError("process lost before commit")
    assert not PaymentAllocation.objects.exists()
    first, second = race(
        lambda: create(business_context, parents, amount="100"),
        lambda: create(business_context, parents, amount="100.00000"),
    )
    assert first.pk == second.pk
    assert AuditEntry.objects.filter(action="payments.allocation.created").count() == 1
