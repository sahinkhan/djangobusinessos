from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic, sleep

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction

from businessos.core.access import services as access_services
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.modules.billing import services
from businessos.modules.billing.models import InvoiceLine

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Requires actual PostgreSQL row locks and separate worker connections.")


def worker(operation, ready, pid):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET statement_timeout = '20s'")
            cursor.execute("SELECT pg_backend_pid()")
            pid.append(cursor.fetchone()[0])
        ready.set()
        return operation()
    finally:
        connections.close_all()


def blocked(pid):
    deadline = monotonic() + 10
    with connection.cursor() as cursor:
        while monotonic() < deadline:
            cursor.execute("SELECT pg_backend_pid() = ANY(pg_blocking_pids(%s))", [pid])
            if cursor.fetchone()[0]:
                return
            sleep(0.01)  # Poll observed lock state, not timing-based ordering.
    pytest.fail("Worker did not block on the held PostgreSQL lock.")


@pytest.mark.parametrize("action", ["header", "line", "remove", "issue"])
def test_issue_wins(business_context, invoice, line, action):
    operations = {
        "header": lambda: services.update_invoice(business_context, invoice.pk, notes="late"),
        "line": lambda: services.update_invoice_line(
            business_context, invoice.pk, line.pk, quantity=3
        ),
        "remove": lambda: services.remove_invoice_line(business_context, invoice.pk, line.pk),
        "issue": lambda: services.issue_invoice(business_context, invoice.pk),
    }
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            issued = services.issue_invoice(business_context, invoice.pk)
            future = pool.submit(worker, operations[action], ready, pid)
            assert ready.wait(10)
            blocked(pid[0])
        if action == "issue":
            assert future.result(15).issued_at == issued.issued_at
        else:
            with pytest.raises(ValidationError, match="draft"):
                future.result(15)
    invoice.refresh_from_db()
    line.refresh_from_db()
    assert invoice.status == "issued" and invoice.notes == ""
    assert line.quantity == 2
    assert AuditEntry.objects.filter(action="billing.invoice.issued").count() == 1


@pytest.mark.parametrize("action", ["header", "line", "remove"])
def test_edit_wins_issue_observes_commit(business_context, invoice, line, action):
    extra = services.add_invoice_line(
        business_context, invoice.pk, description="Surviving line", quantity=1, unit_price=1
    )
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            if action == "header":
                services.update_invoice(business_context, invoice.pk, notes="first")
            elif action == "line":
                services.update_invoice_line(business_context, invoice.pk, line.pk, quantity=3)
            else:
                services.remove_invoice_line(business_context, invoice.pk, line.pk)
            future = pool.submit(
                worker, lambda: services.issue_invoice(business_context, invoice.pk), ready, pid
            )
            assert ready.wait(10)
            blocked(pid[0])
        issued = future.result(15)
    assert issued.status == "issued"
    if action == "header":
        assert issued.notes == "first"
    elif action == "line":
        assert InvoiceLine.objects.get(pk=line.pk).quantity == 3
    else:
        assert list(issued.lines.values_list("id", flat=True)) == [extra.pk]


def test_serialized_line_positions(business_context, invoice, company):
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            first = services.add_invoice_line(
                business_context, invoice.pk, description="First", quantity=1, unit_price=1
            )
            future = pool.submit(
                worker,
                lambda: services.add_invoice_line(
                    business_context, invoice.pk, description="Second", quantity=1, unit_price=1
                ),
                ready,
                pid,
            )
            assert ready.wait(10)
            blocked(pid[0])
        second = future.result(15)
    assert (first.position, second.position) == (1, 2)


@pytest.mark.parametrize("revoke", ["role", "permission", "company_access"])
@pytest.mark.parametrize("operation", ["create", "header", "line", "remove", "issue"])
def test_rechecks_authority_after_company_lock(
    business_context,
    invoice,
    line,
    party,
    currency,
    billing_role,
    operator,
    company,
    revoke,
    operation,
):
    root = get_user_model().objects.create_superuser("billing-root@example.com", "test-only")
    admin = BusinessContext(actor_id=root.pk, company_id=company.pk)
    access_services.register_core_permissions()
    permission = {"create": "billing.invoice.create", "issue": "billing.invoice.issue"}.get(
        operation, "billing.invoice.update"
    )
    operations = {
        "create": lambda: services.create_invoice(
            business_context, bill_to_party_id=party.pk, currency_id=currency.pk
        ),
        "header": lambda: services.update_invoice(business_context, invoice.pk, notes="forbidden"),
        "line": lambda: services.update_invoice_line(
            business_context, invoice.pk, line.pk, quantity=3
        ),
        "remove": lambda: services.remove_invoice_line(business_context, invoice.pk, line.pk),
        "issue": lambda: services.issue_invoice(business_context, invoice.pk),
    }
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            Company.objects.select_for_update().get(pk=company.pk)
            if revoke == "role":
                access_services.revoke_role(admin, user_id=operator.pk, role_id=billing_role.pk)
            elif revoke == "permission":
                access_services.revoke_role_permission(
                    admin, role_id=billing_role.pk, permission_code=permission
                )
            else:
                access_services.revoke_company_access(admin, user_id=operator.pk)
            before = AuditEntry.objects.count()
            future = pool.submit(worker, operations[operation], ready, pid)
            assert ready.wait(10)
            blocked(pid[0])
        with pytest.raises(PermissionDenied):
            future.result(15)
    invoice.refresh_from_db()
    line.refresh_from_db()
    assert invoice.status == "draft" and invoice.notes == "" and line.quantity == 2
    assert AuditEntry.objects.count() == before
