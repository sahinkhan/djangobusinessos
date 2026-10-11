from decimal import Decimal, localcontext
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.apps import apps
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, models
from django.db.migrations.recorder import MigrationRecorder
from django.db.models.deletion import ProtectedError

if not apps.is_installed("businessos.modules.payments.integrations.billing"):
    pytest.skip("Optional payments_billing deployment is not installed.", allow_module_level=True)

from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.core.reference.models import Currency
from businessos.modules.billing import services as billing
from businessos.modules.billing.models import Invoice, InvoiceLine
from businessos.modules.billing.selectors import invoice_financial_basis
from businessos.modules.party.models import Party
from businessos.modules.payments.models import Payment

from .. import compatibility, domain, selectors, services
from ..models import PaymentAllocation
from .test_allocations import create

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("precision", range(9))
def test_independent_sql_rounding_oracle(business_context, currency, financial_factory, precision):
    currency.decimal_places = precision
    currency.save()
    parents = financial_factory(issued=False, total="0.0050")
    billing.add_invoice_line(
        business_context, parents[1].pk, description="Second", quantity="1", unit_price="0.0050"
    )
    billing.issue_invoice(business_context, parents[1].pk)
    expected = (
        Decimal("0") if precision == 0 else Decimal("0.0") if precision == 1 else Decimal("0.01")
    )
    assert invoice_financial_basis(business_context, parents[1].pk).original_total == expected
    evidence = selectors.invoice_allocation_evidence(business_context, parents[1].pk)
    assert evidence.original == evidence.remaining == expected and evidence.applied == 0


def test_postgres_maximum_and_wide_owner_sum(business_context, financial_factory, currency):
    if connection.vendor != "postgresql":
        pytest.skip("SQLite NUMERIC affinity cannot certify exact 38-digit monetary storage/sums.")
    currency.decimal_places = 8
    currency.save()
    parents = financial_factory(
        receipt="999999999999999999999999999999.99999999", issued=False, total="0"
    )
    line = InvoiceLine.objects.get(invoice_id=parents[1].pk)
    billing.remove_invoice_line(business_context, parents[1].pk, line.pk)
    maximum = "99999999999999.9999"
    for _index in range(100):
        billing.add_invoice_line(
            business_context,
            parents[1].pk,
            description="X" * 12000,
            quantity=maximum,
            unit_price=maximum,
        )
    billing.issue_invoice(business_context, parents[1].pk)
    expected = Decimal("999999999999999998000000000000.00000100")
    # Literal oracle, independent of owner/integration aggregate and ambient context.
    with localcontext() as context:
        context.prec = 4
        assert invoice_financial_basis(business_context, parents[1].pk).original_total == expected
        result = create(business_context, parents, amount=str(expected))
    result.refresh_from_db()
    assert result.amount == expected
    evidence = selectors.invoice_allocation_evidence(business_context, parents[1].pk)
    assert evidence.applied == expected and evidence.remaining == 0
    assert selectors.payment_allocation_evidence(
        business_context, parents[0].pk
    ).remaining == Decimal("1999999999999.99999899")


@pytest.mark.parametrize("change", ["party", "currency", "precision", "snapshot", "method_company"])
def test_parent_incompatibility(
    business_context, parents, company, currency, allocation_party, change
):
    if change == "party":
        other = Party.objects.create(
            company=company, party_type="organization", display_name="Different"
        )
        models.QuerySet.update(Invoice.objects.filter(pk=parents[1].pk), bill_to_party_id=other.pk)
    elif change == "currency":
        other = Currency.objects.create(code="EUR", name="Euro")
        models.QuerySet.update(
            Invoice.objects.filter(pk=parents[1].pk),
            currency_id=other.pk,
            currency_code_snapshot="EUR",
        )
    elif change == "precision":
        models.QuerySet.update(
            Invoice.objects.filter(pk=parents[1].pk), currency_decimal_places_snapshot=3
        )
    elif change == "snapshot":
        models.QuerySet.update(
            Payment.objects.filter(pk=parents[0].pk), currency_code_snapshot="BAD"
        )
    else:
        other = Company.objects.create(
            code="OTHER",
            name="Other",
            base_currency=currency,
            country=company.country,
            default_language=company.default_language,
        )
        method = parents[0].payment_method
        models.QuerySet.update(type(method).objects.filter(pk=method.pk), company_id=other.pk)
    with pytest.raises(ValidationError):
        create(business_context, parents)
    assert not PaymentAllocation.objects.exists()


@pytest.mark.parametrize("side", ["payment", "invoice", "company"])
def test_cross_company_cannot_be_disclosed_or_mutated(
    business_context, parents, company, operator, side
):
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    if side == "company":
        context = BusinessContext(actor_id=operator.pk, company_id=other.pk)
    else:
        context = business_context
        model = Payment if side == "payment" else Invoice
        models.QuerySet.update(
            model.objects.filter(pk=parents[0 if side == "payment" else 1].pk), company_id=other.pk
        )
    with pytest.raises(PermissionDenied):
        create(context, parents)
    assert not PaymentAllocation.objects.exists()


@pytest.mark.parametrize("reason", sorted(domain.UNAVAILABLE_REASONS))
def test_tagged_unavailable_has_no_fabricated_values(reason):
    result = domain.AllocationEvidence.unavailable(reason)
    assert result.state == "UNAVAILABLE" and result.reason == reason
    assert (
        result.applied
        is result.remaining
        is result.original
        is result.history
        is result.count
        is None
    )
    assert result.formatted_applied is result.formatted_remaining is None


def test_schema_migration_coverage_and_contract_version(business_context, parents):
    with patch.object(compatibility.apps, "is_installed", return_value=False):
        assert compatibility.evidence_profile() == "not_installed"
    with patch.object(domain, "CONTRACT_VERSION", 2):
        assert compatibility.evidence_profile() == "incompatible"
    MigrationRecorder(connection).migration_qs.filter(
        app="payments_billing", name="0002_register_manifest"
    ).delete()
    evidence = selectors.payment_allocation_evidence(business_context, parents[0].pk)
    assert evidence.reason == "incomplete" and evidence.history is None
    with pytest.raises(ValidationError):
        create(business_context, parents)


def test_operational_failures_are_not_zero(business_context, parents):
    with patch.object(selectors, "validate_history", side_effect=RuntimeError("storage offline")):
        with pytest.raises(RuntimeError):
            selectors.payment_allocation_evidence(business_context, parents[0].pk)


@pytest.mark.parametrize(
    "filters",
    [{"page": 0}, {"page": True}, {"page": "1"}, {"search": None}, {"counterpart_id": "bad"}],
)
def test_invalid_filters(business_context, parents, filters):
    with pytest.raises(ValidationError):
        selectors.payment_allocation_evidence(business_context, parents[0].pk, **filters)


def test_protect_and_cross_alias_objects(business_context, parents):
    create(business_context, parents)
    with pytest.raises(ProtectedError):
        models.Model.delete(parents[0])
    with pytest.raises(ProtectedError):
        models.Model.delete(parents[1])
    foreign_object = PaymentAllocation(
        company_id=business_context.company_id,
        payment_id=parents[0].pk,
        invoice_id=parents[1].pk,
        amount=1,
        idempotency_key="other",
    )
    foreign_object._state.db = "unapproved_alias"
    from ..models import _INSERT_TOKEN

    with pytest.raises(ValidationError):
        foreign_object._insert(_INSERT_TOKEN)


def test_uuid_collision_recovery_and_exhaustion(business_context, parents):
    first = create(business_context, parents)
    with patch.object(services, "uuid4", side_effect=[first.pk, uuid4()]):
        second = create(business_context, parents, key="second")
    assert second.pk != first.pk
    with patch.object(services, "uuid4", return_value=first.pk):
        with pytest.raises(ValidationError, match="collision exhausted"):
            create(business_context, parents, key="third")
    assert PaymentAllocation.objects.count() == 2


@pytest.mark.parametrize("drift", ["missing", "weakened", "not_valid"])
def test_postgres_schema_constraint_drift_fails_closed(business_context, parents, drift):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL CHECK definitions and validation-state drift.")
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE payments_billing_paymentallocation DROP CONSTRAINT allocation_amount_range"
        )
        if drift != "missing":
            definition = "amount < 1e31" if drift == "weakened" else "amount < 1e30"
            cursor.execute(
                "ALTER TABLE payments_billing_paymentallocation ADD CONSTRAINT "
                "allocation_amount_range CHECK ("
                + definition
                + ")"
                + (" NOT VALID" if drift == "not_valid" else "")
            )
    assert compatibility.evidence_profile() == "incompatible"
    assert selectors.payment_allocation_evidence(business_context, parents[0].pk).history is None
    with pytest.raises(ValidationError):
        create(business_context, parents)
    assert not PaymentAllocation.objects.exists()


def test_noncanonical_receipt_is_rejected_before_first_allocation(business_context, parents):
    models.QuerySet.update(
        Payment.objects.filter(pk=parents[0].pk),
        number="PAY-" + "a" * 32,
    )
    with pytest.raises(ValidationError, match="incompatible"):
        create(business_context, parents)
    assert not PaymentAllocation.objects.exists()


def test_noncanonical_historical_key_fails_closed(business_context, parents):
    fact = create(business_context, parents)
    models.QuerySet.update(PaymentAllocation.objects.filter(pk=fact.pk), idempotency_key="\tkey\n")
    rejected = selectors.payment_allocation_evidence(business_context, parents[0].pk)
    assert rejected.reason == "incompatible" and rejected.history is rejected.applied is None
    with pytest.raises(ValidationError, match="provenance"):
        create(business_context, parents, key="new")
