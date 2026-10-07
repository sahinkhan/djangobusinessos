from datetime import date, datetime
from decimal import Decimal, localcontext
from unittest.mock import patch

import pytest
from asgiref.sync import async_to_sync
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError

from businessos.core.audit.models import AuditEntry
from businessos.modules.payments import domain, services
from businessos.modules.payments.models import Payment, PaymentMethod

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("kind", ["method", "receipt"])
@pytest.mark.parametrize(
    "operation", ["asave", "adelete", "aupdate", "abulk_create", "abulk_update"]
)
def test_async_write_guards(business_context, payload, method, kind, operation):
    instance = method if kind == "method" else services.record_payment(business_context, **payload)
    manager = type(instance).objects

    async def invoke():
        if operation in {"asave", "adelete"}:
            await getattr(instance, operation)()
        elif operation == "aupdate":
            await manager.aupdate(company_id=instance.company_id)
        elif operation == "abulk_create":
            await manager.abulk_create([instance])
        else:
            await manager.abulk_update([instance], ["company"])

    with pytest.raises(ValidationError):
        async_to_sync(invoke)()


def test_uuid_date_numeric_canonicalization(business_context, payload):
    first = services.record_payment(
        business_context,
        **payload,
        idempotency_key="key",
        notes=" hello ",
        external_reference=" ref ",
    )
    retry = services.record_payment(
        business_context,
        **(
            payload
            | {
                "payer_party_id": str(payload["payer_party_id"]).upper(),
                "currency_id": str(payload["currency_id"]),
                "payment_method_id": str(payload["payment_method_id"]),
                "payment_date": date(2026, 10, 8),
                "amount": Decimal("12.500000"),
            }
        ),
        idempotency_key=" key ",
        notes="hello",
        external_reference="ref",
    )
    assert retry.pk == first.pk


@pytest.mark.parametrize("field", ["payer_party_id", "currency_id", "payment_method_id"])
def test_identity_retry_conflict(business_context, payload, field):
    from uuid import uuid4

    services.record_payment(business_context, **payload, idempotency_key="key")
    with pytest.raises(ValidationError, match="different receipt"):
        services.record_payment(
            business_context, **(payload | {field: uuid4()}), idempotency_key="key"
        )


@pytest.mark.parametrize("precision,amount", [(0, "1.00000"), (2, "0.01"), (8, "0.00000001")])
def test_currency_precision_boundaries(business_context, payload, currency, precision, amount):
    currency.decimal_places = precision
    currency.save()
    payment = services.record_payment(business_context, **(payload | {"amount": amount}))
    assert payment.amount == Decimal(amount)
    assert payment.currency_decimal_places_snapshot == precision


@pytest.mark.parametrize("reference", ["payer_party", "currency", "payment_method"])
def test_receipt_references_protected(business_context, payload, reference):
    from django.db.models.deletion import ProtectedError

    receipt = services.record_payment(business_context, **payload)
    related = getattr(receipt, reference)
    with pytest.raises((ProtectedError, ValidationError)):
        related.delete()
    assert Payment.objects.filter(pk=receipt.pk).exists()


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        1.2,
        "oops",
        "",
        "NaN",
        "Infinity",
        "-Infinity",
        "0",
        "-1",
        "0.001",
        "1e30",
    ],
)
def test_invalid_amount_rolls_back(business_context, payload, value):
    before = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        services.record_payment(business_context, **(payload | {"amount": value}))
    assert not Payment.objects.exists()
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("value", ["12.50000000000", Decimal("12.500"), "1.250e1"])
def test_exact_normalized_retry(business_context, payload, value):
    first = services.record_payment(business_context, **payload, idempotency_key=" Key ")
    retry = services.record_payment(
        business_context, **(payload | {"amount": value}), idempotency_key="Key"
    )
    assert retry.pk == first.pk
    assert Payment.objects.count() == 1
    assert AuditEntry.objects.filter(action="payments.payment.recorded").count() == 1


def test_domain_full_precision_independent_of_decimal_context():
    value = "999999999999999999999999999999.99999999"
    with localcontext() as context:
        context.prec = 6
        assert str(domain.receipt_amount(value, 8)) == value
        assert domain.format_amount(value, 8) == value


@pytest.mark.parametrize("precision", [-1, 9, True, "2", None])
def test_invalid_precision(precision):
    with pytest.raises(ValueError):
        domain.receipt_amount("1", precision)


@pytest.mark.parametrize(
    "field,value",
    [
        ("payment_date", "20261008"),
        ("payment_date", datetime(2026, 10, 8)),
        ("payer_party_id", "invalid"),
        ("currency_id", "invalid"),
        ("payment_method_id", "invalid"),
        ("external_reference", "x" * 129),
        ("notes", 7),
        ("idempotency_key", "x" * 129),
    ],
)
def test_invalid_payload(business_context, payload, field, value):
    with pytest.raises(ValidationError):
        services.record_payment(business_context, **(payload | {field: value}))
    assert not Payment.objects.exists()


def test_retry_preserves_retired_reference_snapshots(
    business_context, payload, payer, method, currency
):
    first = services.record_payment(business_context, **payload, idempotency_key="key")
    services.update_payment_method(business_context, payment_method_id=method.pk, name="Renamed")
    services.set_payment_method_active(
        business_context, payment_method_id=method.pk, is_active=False
    )
    payer.display_name = "Changed"
    payer.is_active = False
    payer.save()
    currency.decimal_places = 0
    currency.is_active = False
    currency.save()
    retry = services.record_payment(business_context, **payload, idempotency_key="key")
    assert retry.pk == first.pk
    assert retry.payer_display_name_snapshot == "Payer"
    assert retry.payment_method_name_snapshot == "Cash"
    assert retry.formatted_amount == "12.50"
    with pytest.raises(ValidationError):
        services.record_payment(business_context, **payload)


def test_omitted_date_retry_across_midnight(business_context, payload):
    payload["payment_date"] = None
    with patch.object(services, "company_local_date", return_value=date(2026, 10, 8)):
        first = services.record_payment(business_context, **payload, idempotency_key="key")
    with patch.object(services, "company_local_date", side_effect=AssertionError("No new date")):
        assert (
            services.record_payment(business_context, **payload, idempotency_key="key").pk
            == first.pk
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("amount", "13"),
        ("payment_date", "2026-10-09"),
        ("notes", "different"),
        ("external_reference", "new"),
    ],
)
def test_conflicting_retry(business_context, payload, field, value):
    services.record_payment(business_context, **payload, idempotency_key="key")
    with pytest.raises(ValidationError, match="different receipt"):
        services.record_payment(
            business_context, **(payload | {field: value}), idempotency_key="key"
        )
    assert Payment.objects.count() == 1


def test_unkeyed_requests_and_case_sensitive_keys(business_context, payload):
    for key in [None, "", " ", "Key", "key"]:
        services.record_payment(business_context, **payload, idempotency_key=key)
    assert Payment.objects.count() == 5
    assert Payment.objects.filter(idempotency_key__isnull=True).count() == 3


def test_method_normalization_noops_and_boolean(business_context, method):
    assert (method.code, method.name) == ("CASH", "Cash")
    before = AuditEntry.objects.count()
    services.update_payment_method(business_context, payment_method_id=method.pk, name=" Cash ")
    services.set_payment_method_active(
        business_context, payment_method_id=method.pk, is_active=True
    )
    assert AuditEntry.objects.count() == before
    with pytest.raises(ValidationError):
        services.create_payment_method(business_context, code="cash", name="Duplicate")
    with pytest.raises(ValidationError):
        services.set_payment_method_active(
            business_context, payment_method_id=method.pk, is_active="false"
        )


@pytest.mark.parametrize("operation", ["create", "rename", "activity", "record"])
def test_audit_failure_atomicity(business_context, payload, method, operation):
    before = AuditEntry.objects.count()
    with patch.object(services, "record_audit_entry", side_effect=RuntimeError("audit")):
        with pytest.raises(RuntimeError, match="audit"):
            if operation == "create":
                services.create_payment_method(business_context, code="BANK", name="Bank")
            elif operation == "rename":
                services.update_payment_method(
                    business_context, payment_method_id=method.pk, name="Changed"
                )
            elif operation == "activity":
                services.set_payment_method_active(
                    business_context, payment_method_id=method.pk, is_active=False
                )
            else:
                services.record_payment(business_context, **payload)
    method.refresh_from_db()
    assert method.name == "Cash" and method.is_active
    assert PaymentMethod.objects.count() == 1
    assert not Payment.objects.exists()
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("kind", ["method", "receipt"])
@pytest.mark.parametrize(
    "operation",
    [
        "save",
        "delete",
        "update",
        "bulk_update",
        "bulk_create",
        "ignore",
        "upsert",
        "query_delete",
        "create",
    ],
)
def test_public_write_paths_blocked(business_context, payload, method, kind, operation):
    instance = method if kind == "method" else services.record_payment(business_context, **payload)
    model = type(instance)
    field = "name" if kind == "method" else "notes"
    setattr(instance, field, "Tampered")
    with pytest.raises(ValidationError):
        if operation == "save":
            instance.save()
        elif operation == "delete":
            instance.delete()
        elif operation == "update":
            model.objects.filter(pk=instance.pk).update(**{field: "Tampered"})
        elif operation == "bulk_update":
            model.objects.bulk_update([instance], [field])
        elif operation in {"bulk_create", "ignore", "upsert"}:
            model.objects.bulk_create(
                [instance],
                ignore_conflicts=operation == "ignore",
                update_conflicts=operation == "upsert",
                update_fields=[field],
                unique_fields=["id"],
            )
        elif operation == "query_delete":
            model.objects.filter(pk=instance.pk).delete()
        else:
            model.objects.create()
    instance.refresh_from_db()
    assert getattr(instance, field) != "Tampered"


def test_number_collision_retries_only_number_constraint(business_context, payload):
    first = services.record_payment(business_context, **payload)
    with patch.object(services, "_number", side_effect=[first.number, "PAY-" + "A" * 32]):
        second = services.record_payment(business_context, **payload)
    assert second.number == "PAY-" + "A" * 32
    with patch.object(services, "_number", return_value=first.number) as number:
        with pytest.raises(ValidationError, match="allocate"):
            services.record_payment(business_context, **payload)
        assert number.call_count == 3
    with patch.object(Payment, "_insert", side_effect=IntegrityError("unrelated")):
        with pytest.raises(IntegrityError, match="unrelated"):
            services.record_payment(business_context, **payload)
    assert Payment.objects.count() == 2


def test_permission_required_even_for_retry(business_context, payload, payments_role):
    from businessos.core.access.models import RolePermission

    services.record_payment(business_context, **payload, idempotency_key="key")
    RolePermission.objects.filter(role=payments_role).delete()
    with pytest.raises(PermissionDenied):
        services.record_payment(business_context, **payload, idempotency_key="key")
