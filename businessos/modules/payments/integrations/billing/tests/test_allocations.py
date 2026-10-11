import importlib
from decimal import Decimal, localcontext
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.apps import apps
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, models
from django.test.utils import CaptureQueriesContext

if not apps.is_installed("businessos.modules.payments.integrations.billing"):
    pytest.skip("Optional payments_billing deployment is not installed.", allow_module_level=True)

from businessos.core.access.models import Permission, RolePermission, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company
from businessos.modules.billing.models import Invoice, InvoiceLine
from businessos.modules.billing.selectors import invoice_financial_basis
from businessos.modules.payments.models import Payment
from businessos.modules.payments.selectors import payment_receipt_basis

from .. import selectors, services
from ..compatibility import evidence_profile
from ..manifest import CREATE_ALLOCATIONS, MODULE, VIEW_ALLOCATIONS
from ..models import PaymentAllocation

pytestmark = pytest.mark.django_db


def create(context, parents, *, amount="10", key="key"):
    return services.create_payment_allocation(
        context,
        payment_id=parents[0].pk,
        invoice_id=parents[1].pk,
        amount=amount,
        idempotency_key=key,
    )


def test_functional_many_to_many(business_context, parents, financial_factory):
    payment, invoice = parents
    second_payment, second_invoice = financial_factory()
    create(business_context, parents, amount="30", key="a")
    create(business_context, parents, amount="20", key="b")
    create(business_context, (payment, second_invoice), amount="50", key="c")
    create(business_context, (second_payment, invoice), amount="50", key="d")
    p = selectors.payment_allocation_evidence(business_context, payment.pk)
    i = selectors.invoice_allocation_evidence(business_context, invoice.pk)
    assert (p.applied, p.remaining, p.count) == (100, 0, 3)
    assert (i.applied, i.remaining, i.count) == (100, 0, 3)
    assert AuditEntry.objects.filter(action="payments.allocation.created").count() == 4
    assert not apps.get_model("accounting", "JournalEntry").objects.exists()
    assert Payment.objects.count() == 2 and Invoice.objects.count() == 2


def test_full_retry_and_reference_retirement(business_context, parents, currency, allocation_party):
    first = create(business_context, parents, amount="100.00000000", key=" key ")
    allocation_party.is_active = False
    allocation_party.save()
    currency.decimal_places = 3
    currency.is_active = False
    currency.save()
    method = parents[0].payment_method
    models.QuerySet.update(
        type(method).objects.filter(pk=method.pk), is_active=False, name="Retired"
    )
    times = (first.created_at, first.updated_at)
    result = create(business_context, parents, amount=100, key="key")
    assert result.pk == first.pk and (result.created_at, result.updated_at) == times
    assert PaymentAllocation.objects.count() == 1
    assert AuditEntry.objects.filter(action="payments.allocation.created").count() == 1
    assert selectors.payment_allocation_evidence(business_context, parents[0].pk).remaining == 0


@pytest.mark.parametrize("field", ["amount", "payment", "invoice"])
def test_key_conflict(business_context, parents, financial_factory, field):
    create(business_context, parents)
    alternate = financial_factory()
    proposed = (
        (alternate[0], parents[1])
        if field == "payment"
        else (parents[0], alternate[1])
        if field == "invoice"
        else parents
    )
    with pytest.raises(ValidationError) as error:
        create(business_context, proposed, amount="11" if field == "amount" else "10")
    assert error.value.code == "idempotency_conflict"
    assert PaymentAllocation.objects.count() == 1


@pytest.mark.parametrize(
    "amount",
    [
        0,
        -1,
        "NaN",
        "sNaN",
        "Infinity",
        "-Infinity",
        True,
        False,
        1.5,
        "bad",
        "",
        None,
        "1e30",
        "0.001",
        "1.001000000",
    ],
)
def test_invalid_amount_no_write(business_context, parents, amount):
    before = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        create(business_context, parents, amount=amount)
    assert not PaymentAllocation.objects.exists() and AuditEntry.objects.count() == before


@pytest.mark.parametrize("key", [None, "", " \t\n ", "k" * 129, 12, False])
def test_key_bounds(business_context, parents, key):
    with pytest.raises(ValidationError):
        create(business_context, parents, key=key)
    assert not PaymentAllocation.objects.exists()


@pytest.mark.parametrize("precision", range(9))
def test_precision_numeric_equivalence(business_context, currency, financial_factory, precision):
    currency.decimal_places = precision
    currency.save()
    parents = financial_factory()
    with localcontext() as context:
        context.prec = 4
        first = create(business_context, parents, amount="10.000000000000000", key="k" * 128)
        second = create(business_context, parents, amount=Decimal("1E1"), key="k" * 128)
    assert second.pk == first.pk
    assert (
        selectors.payment_allocation_evidence(business_context, parents[0].pk).precision
        == precision
    )


@pytest.mark.parametrize("side", ["payment", "invoice"])
def test_capacity(business_context, financial_factory, side):
    parents = financial_factory(
        receipt="5" if side == "payment" else "100", total="5" if side == "invoice" else "100"
    )
    create(business_context, parents, amount="5", key="full")
    with pytest.raises(ValidationError) as error:
        create(business_context, parents, amount="0.01", key="over")
    assert error.value.code == f"{side}_capacity_exceeded"
    assert PaymentAllocation.objects.count() == 1


@pytest.mark.parametrize("issued,total", [(False, "100"), (True, "0")])
def test_draft_and_zero(business_context, financial_factory, issued, total):
    parents = financial_factory(issued=issued, total=total)
    with pytest.raises(ValidationError):
        create(business_context, parents)
    evidence = selectors.invoice_allocation_evidence(business_context, parents[1].pk)
    assert evidence.state == ("AVAILABLE" if issued else "UNAVAILABLE")
    if issued:
        assert evidence.applied == evidence.remaining == 0
    else:
        assert evidence.applied is evidence.history is evidence.count is None


@pytest.mark.parametrize("identity", ["not-uuid", None, True, 12])
@pytest.mark.parametrize("side", [0, 1])
def test_uuid_validation(business_context, parents, identity, side):
    args = dict(
        payment_id=parents[0].pk, invoice_id=parents[1].pk, amount="1", idempotency_key="bad"
    )
    args["payment_id" if side == 0 else "invoice_id"] = identity
    with pytest.raises(ValidationError):
        services.create_payment_allocation(business_context, **args)


def test_missing_ids_and_objects_rejected(business_context, parents):
    with pytest.raises(PermissionDenied):
        services.create_payment_allocation(
            business_context,
            payment_id=uuid4(),
            invoice_id=parents[1].pk,
            amount="1",
            idempotency_key="missing",
        )
    with pytest.raises(ValidationError):
        services.create_payment_allocation(
            business_context,
            payment_id=parents[0],
            invoice_id=parents[1].pk,
            amount="1",
            idempotency_key="object",
        )


@pytest.mark.parametrize(
    "grant", [CREATE_ALLOCATIONS, "payments.payment.view", "billing.invoice.view"]
)
def test_compound_create_permission(business_context, parents, allocation_role, grant):
    RolePermission.objects.filter(role=allocation_role, permission__code=grant).delete()
    with pytest.raises(PermissionDenied):
        create(business_context, parents)
    assert not PaymentAllocation.objects.exists()


def test_create_does_not_require_read_or_record_or_issue(
    business_context, parents, allocation_role
):
    RolePermission.objects.filter(
        role=allocation_role,
        permission__code__in=[VIEW_ALLOCATIONS, "payments.payment.record", "billing.invoice.issue"],
    ).delete()
    result = create(business_context, parents)
    assert result.pk
    with pytest.raises(PermissionDenied):
        selectors.payment_allocation_evidence(business_context, parents[0].pk)


def test_python_apis_ignore_http_registry(business_context, parents):
    BusinessModule.objects.filter(code="payments_billing").delete()
    create(business_context, parents)
    assert selectors.invoice_allocation_evidence(business_context, parents[1].pk).applied == 10


@pytest.mark.parametrize("failure", ["audit", "insert", "constraint"])
def test_failure_rolls_back(business_context, parents, failure):
    before = AuditEntry.objects.count()
    target = "record_audit_entry" if failure == "audit" else None
    with patch.object(
        services if target else PaymentAllocation,
        target or "_insert",
        side_effect=RuntimeError("audit")
        if failure == "audit"
        else IntegrityError("unrelated constraint"),
    ):
        with pytest.raises(RuntimeError if failure == "audit" else IntegrityError):
            create(business_context, parents)
    assert not PaymentAllocation.objects.exists() and AuditEntry.objects.count() == before


@pytest.mark.parametrize(
    "operation",
    [
        "save",
        "delete",
        "update",
        "bulk_update",
        "bulk_create",
        "upsert",
        "qs_delete",
        "create",
        "update_or_create",
        "private",
    ],
)
def test_orm_guards(business_context, parents, operation):
    fact = create(business_context, parents)
    operations = {
        "save": lambda: fact.save(),
        "delete": lambda: fact.delete(),
        "update": lambda: PaymentAllocation.objects.update(amount=1),
        "bulk_update": lambda: PaymentAllocation.objects.bulk_update([fact], ["amount"]),
        "bulk_create": lambda: PaymentAllocation.objects.bulk_create([fact]),
        "upsert": lambda: PaymentAllocation.objects.bulk_create(
            [fact], update_conflicts=True, update_fields=["amount"], unique_fields=["id"]
        ),
        "qs_delete": lambda: PaymentAllocation.objects.all().delete(),
        "create": lambda: PaymentAllocation.objects.create(
            company_id=fact.company_id,
            payment_id=fact.payment_id,
            invoice_id=fact.invoice_id,
            amount=1,
            idempotency_key="bypass",
        ),
        "update_or_create": lambda: PaymentAllocation.objects.update_or_create(
            pk=fact.pk, defaults={"amount": 1}
        ),
        "private": lambda: fact._insert(object()),
    }
    with pytest.raises(ValidationError):
        operations[operation]()
    fact.refresh_from_db()
    assert fact.amount == 10 and PaymentAllocation.objects.count() == 1


@pytest.mark.parametrize(
    "corruption",
    [
        "payer",
        "precision",
        "code",
        "line_company",
        "line_amount",
        "line_description",
        "receipt_company",
        "allocation_amount",
        "allocation_company",
    ],
)
def test_corrupt_off_page_history_fails_closed(business_context, parents, company, corruption):
    fact = create(business_context, parents)
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    if corruption == "payer":
        from businessos.modules.party.models import Party

        party = Party.objects.create(company=company, party_type="person", display_name="Other")
        models.QuerySet.update(Invoice.objects.filter(pk=parents[1].pk), bill_to_party_id=party.pk)
    elif corruption in {"precision", "code"}:
        models.QuerySet.update(
            Invoice.objects.filter(pk=parents[1].pk),
            **{"currency_decimal_places_snapshot": 3}
            if corruption == "precision"
            else {"currency_code_snapshot": "BAD"},
        )
    elif corruption.startswith("line_"):
        fields = {
            "line_company": {"company_id": other.pk},
            "line_amount": {"quantity": "99999999999999.9999", "unit_price": "99999999999999.9999"},
            "line_description": {"description": " "},
        }
        models.QuerySet.update(
            InvoiceLine.objects.filter(invoice_id=parents[1].pk), **fields[corruption]
        )
        if corruption == "line_amount":
            # Changed total alone remains compatible; corrupt by over-capacity instead.
            models.QuerySet.update(PaymentAllocation.objects.filter(pk=fact.pk), amount=101)
    elif corruption == "receipt_company":
        models.QuerySet.update(Payment.objects.filter(pk=parents[0].pk), company_id=other.pk)
    else:
        models.QuerySet.update(
            PaymentAllocation.objects.filter(pk=fact.pk),
            **({"amount": 101} if corruption == "allocation_amount" else {"company_id": other.pk}),
        )
    for selector, identity in (
        (selectors.payment_allocation_evidence, parents[0].pk),
        (selectors.invoice_allocation_evidence, parents[1].pk),
    ):
        if corruption == "receipt_company" and selector is selectors.payment_allocation_evidence:
            with pytest.raises(PermissionDenied):
                selector(business_context, identity)
        else:
            evidence = selector(business_context, identity, search="no-match")
            assert evidence.state == "UNAVAILABLE"
            assert (
                evidence.applied is evidence.remaining is evidence.count is evidence.history is None
            )
    with pytest.raises((PermissionDenied, ValidationError)):
        create(business_context, parents, amount="1", key="new")


def test_bounded_history_sql_and_denominator(business_context, parents):
    for index in range(101):
        create(business_context, parents, amount="0.10", key=str(index))
    with (
        CaptureQueriesContext(connection) as queries,
        patch.object(
            InvoiceLine, "from_db", side_effect=AssertionError("Unbounded invoice line payload")
        ),
    ):
        second = selectors.payment_allocation_evidence(business_context, parents[0].pk, page=2)
    assert second.count == 101 and len(second.history) == 50 and second.pages == 3
    assert second.applied == Decimal("10.10")
    assert any("LIMIT 50 OFFSET 50" in query["sql"] for query in queries)
    assert any("COUNT(" in query["sql"] for query in queries)
    filtered = selectors.payment_allocation_evidence(
        business_context, parents[0].pk, search="no-match"
    )
    assert filtered.count == 0 and filtered.history == () and filtered.applied == second.applied
    third = selectors.payment_allocation_evidence(business_context, parents[0].pk, page=3)
    ids = [row.id for row in second.history] + [row.id for row in third.history]
    assert len(ids) == len(set(ids)) == 51
    # Corrupt the final, off-page fact, not any of the first 50 visible rows.
    models.QuerySet.update(PaymentAllocation.objects.filter(pk=third.history[-1].id), amount=101)
    for selector, parent_id in (
        (selectors.payment_allocation_evidence, parents[0].pk),
        (selectors.invoice_allocation_evidence, parents[1].pk),
    ):
        rejected = selector(business_context, parent_id, page=1, search="no-match")
        assert rejected.state == "UNAVAILABLE" and rejected.reason == "incompatible"
        assert rejected.applied is rejected.history is rejected.count is None


def test_profile_registration_and_exact_schema(business_context, parents):
    assert evidence_profile() is None
    model = apps.get_app_config("payments_billing").get_model("PaymentAllocation")
    assert {field.name for field in model._meta.fields} == {
        "id",
        "company",
        "payment",
        "invoice",
        "amount",
        "idempotency_key",
        "created_at",
        "updated_at",
    }
    assert MODULE["depends"] == ["billing", "payments"]
    module = BusinessModule.objects.get(code="payments_billing")
    assert not module.is_enabled and set(module.declared_permissions) == {
        VIEW_ALLOCATIONS,
        CREATE_ALLOCATIONS,
    }
    BusinessModule.objects.filter(pk=module.pk).update(is_enabled=True)
    migration = importlib.import_module(
        "businessos.modules.payments.integrations.billing.migrations.0002_register_manifest"
    )
    migration.register(apps, SimpleNamespace(connection=connection))
    module.refresh_from_db()
    assert module.is_enabled
    assert Permission.objects.filter(code__startswith="payments_billing.").count() == 2


def test_owner_basis_exact_and_no_line_models(business_context, parents):
    with patch.object(InvoiceLine, "from_db", side_effect=AssertionError("Line materialized")):
        assert invoice_financial_basis(business_context, parents[1].pk).original_total == 100
    assert payment_receipt_basis(business_context, parents[0].pk).amount == 100


def test_retry_another_actor_and_revoked(
    business_context, parents, operator, company, allocation_role
):
    first = create(business_context, parents)
    from django.contrib.auth import get_user_model

    from businessos.core.access.models import UserCompanyAccess
    from businessos.core.common.context import BusinessContext

    actor = get_user_model().objects.create_user("retry@synthetic.test", "test-only")
    UserCompanyAccess.objects.create(user=actor, company=company)
    UserRoleAssignment.objects.create(user=actor, company=company, role=allocation_role)
    context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
    assert create(context, parents).pk == first.pk
    UserCompanyAccess.objects.filter(user=actor).delete()
    with pytest.raises(PermissionDenied):
        create(context, parents)
