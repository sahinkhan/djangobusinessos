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
from businessos.modules.payments import services
from businessos.modules.payments.models import Payment, PaymentMethod

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks and independent worker connections.")


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
            sleep(0.01)  # Poll real server lock state, never infer ordering from elapsed time.
    pytest.fail("Worker did not block on the held PostgreSQL lock.")


@pytest.mark.parametrize("different", [False, True])
def test_same_key_race(business_context, payload, different):
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            first = services.record_payment(business_context, **payload, idempotency_key="race")
            competing = payload | ({"amount": "13"} if different else {})
            future = pool.submit(
                worker,
                lambda: services.record_payment(
                    business_context, **competing, idempotency_key="race"
                ),
                ready,
                pid,
            )
            assert ready.wait(10)
            blocked(pid[0])
        if different:
            with pytest.raises(ValidationError):
                future.result(15)
        else:
            assert future.result(15).pk == first.pk
    assert Payment.objects.count() == 1
    assert AuditEntry.objects.filter(action="payments.payment.recorded").count() == 1


@pytest.mark.parametrize("change", ["rename", "deactivate"])
@pytest.mark.parametrize("record_first", [False, True])
def test_method_race(business_context, payload, method, change, record_first):
    def change_method():
        if change == "rename":
            return services.update_payment_method(
                business_context, payment_method_id=method.pk, name="New name"
            )
        return services.set_payment_method_active(
            business_context, payment_method_id=method.pk, is_active=False
        )

    def record():
        return services.record_payment(business_context, **payload)

    first, second = (record, change_method) if record_first else (change_method, record)
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            first()
            future = pool.submit(worker, second, ready, pid)
            assert ready.wait(10)
            blocked(pid[0])
        if not record_first and change == "deactivate":
            with pytest.raises(ValidationError):
                future.result(15)
            assert not Payment.objects.exists()
        else:
            future.result(15)
            receipt = Payment.objects.get()
            assert receipt.payment_method_name_snapshot == (
                "New name" if not record_first else "Cash"
            )


@pytest.mark.parametrize("revoke", ["role", "permission", "company_access"])
@pytest.mark.parametrize("operation", ["create", "rename", "activity", "record", "retry"])
def test_authorization_after_wait(
    business_context, payload, method, payments_role, company, operator, revoke, operation
):
    root = get_user_model().objects.create_superuser("payments-root@example.com", "test-only")
    admin = BusinessContext(actor_id=root.pk, company_id=company.pk)
    access_services.register_core_permissions()
    if operation == "retry":
        services.record_payment(business_context, **payload, idempotency_key="key")
    permission = (
        "payments.payment.record"
        if operation in {"record", "retry"}
        else ("payments.method.manage")
    )
    operations = {
        "create": lambda: services.create_payment_method(
            business_context, code="BANK", name="Bank"
        ),
        "rename": lambda: services.update_payment_method(
            business_context, payment_method_id=method.pk, name="No"
        ),
        "activity": lambda: services.set_payment_method_active(
            business_context, payment_method_id=method.pk, is_active=False
        ),
        "record": lambda: services.record_payment(business_context, **payload),
        "retry": lambda: services.record_payment(
            business_context, **payload, idempotency_key="key"
        ),
    }
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            Company.objects.select_for_update().get(pk=company.pk)
            if revoke == "role":
                access_services.revoke_role(admin, user_id=operator.pk, role_id=payments_role.pk)
            elif revoke == "permission":
                access_services.revoke_role_permission(
                    admin, role_id=payments_role.pk, permission_code=permission
                )
            else:
                access_services.revoke_company_access(admin, user_id=operator.pk)
            before = AuditEntry.objects.count()
            future = pool.submit(worker, operations[operation], ready, pid)
            assert ready.wait(10)
            blocked(pid[0])
        with pytest.raises(PermissionDenied):
            future.result(15)
    method.refresh_from_db()
    assert method.name == "Cash" and method.is_active
    assert PaymentMethod.objects.count() == 1
    assert Payment.objects.count() == int(operation == "retry")
    assert AuditEntry.objects.count() == before


def test_method_code_race(business_context, payments_role):
    ready, pid = Event(), []
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            services.create_payment_method(business_context, code="bank", name="Bank")
            future = pool.submit(
                worker,
                lambda: services.create_payment_method(
                    business_context, code=" BANK ", name="Duplicate"
                ),
                ready,
                pid,
            )
            assert ready.wait(10)
            blocked(pid[0])
        with pytest.raises(ValidationError):
            future.result(15)
    assert PaymentMethod.objects.count() == 1
