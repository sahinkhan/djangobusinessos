"""PAYINT1-R1--R4: actual catalog/reader behavior and immutable retry facts."""

from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.apps import apps
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, models
from django.db.models import Sum
from django.test.utils import CaptureQueriesContext

if not apps.is_installed("businessos.modules.payments.integrations.billing"):
    pytest.skip("Optional payments_billing deployment is not installed.", allow_module_level=True)

from businessos.core.audit.models import AuditEntry
from businessos.core.organization.models import Company
from businessos.core.reference.models import Currency
from businessos.modules.billing.models import Invoice, InvoiceLine
from businessos.modules.party.models import Party
from businessos.modules.payments.models import Payment

from .. import compatibility, selectors, services
from ..models import PaymentAllocation
from .test_allocations import create

pytestmark = pytest.mark.django_db


@pytest.fixture
def postgres():
    if connection.vendor != "postgresql":
        pytest.skip("Requires real PostgreSQL RLS/catalog/FK validation-state evidence.")


@contextmanager
def restricted_reader(database=connection):
    from psycopg import sql

    name = "payint_reader_" + uuid4().hex
    with database.cursor() as cursor:
        cursor.execute(
            sql.SQL("CREATE ROLE {} NOSUPERUSER NOBYPASSRLS").format(sql.Identifier(name))
        )
        cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(name)))
        cursor.execute(
            sql.SQL("GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {}").format(
                sql.Identifier(name)
            )
        )
        cursor.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(name)))
        cursor.execute("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user")
        assert cursor.fetchone() == (False, False)
    try:
        yield
    finally:
        with database.cursor() as cursor:
            cursor.execute("RESET ROLE")
            cursor.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(name)))
            cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))


def assert_unavailable(context, parents):
    for selector, parent in (
        (selectors.payment_allocation_evidence, parents[0]),
        (selectors.invoice_allocation_evidence, parents[1]),
    ):
        result = selector(context, parent.pk, search="nothing-visible", page=2)
        assert result.state == "UNAVAILABLE" and result.reason == "incompatible"
        assert result.applied is result.remaining is result.history is result.count is None


@pytest.mark.parametrize(
    "table",
    [
        "payments_billing_paymentallocation",
        "payments_payment",
        "payments_paymentmethod",
        "billing_invoice",
        "billing_invoiceline",
        "party_party",
        "reference_currency",
        "organization_company",
        "django_migrations",
    ],
)
def test_r1_rls_cannot_certify_hidden_financial_evidence(
    postgres, business_context, parents, table
):
    from psycopg import sql

    fact = create(business_context, parents, amount="80")
    before = AuditEntry.objects.count()
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(
            sql.SQL("ALTER TABLE {} ENABLE ROW LEVEL SECURITY").format(sql.Identifier(table))
        )
        # Company must remain accessible for ordinary context admission. Even a
        # permissive policy is not guessed safe by this nonprivileged profile.
        predicate = sql.SQL("true" if table == "organization_company" else "false")
        cursor.execute(
            sql.SQL("CREATE POLICY hidden_financial_rows ON {} USING ({})").format(
                sql.Identifier(table), predicate
            )
        )
    with restricted_reader():
        if table == PaymentAllocation._meta.db_table:
            assert not PaymentAllocation.objects.filter(pk=fact.pk).exists()
        assert compatibility.evidence_profile() == "incompatible"
        assert_unavailable(business_context, parents)
        with pytest.raises(ValidationError, match="unavailable"):
            create(business_context, parents, amount="80", key="second")
    assert PaymentAllocation.objects.aggregate(total=Sum("amount"))["total"] == 80
    assert PaymentAllocation.objects.count() == 1 and AuditEntry.objects.count() == before


def test_r1_supported_nonprivileged_non_rls_reader(postgres, business_context, parents):
    create(business_context, parents, amount="80")
    with restricted_reader():
        assert compatibility.evidence_profile() is None
        result = selectors.payment_allocation_evidence(business_context, parents[0].pk)
        assert (result.applied, result.remaining) == (80, 20)
        create(business_context, parents, amount="20", key="rest")
    assert PaymentAllocation.objects.aggregate(total=Sum("amount"))["total"] == 100


def foreign_key(table, column):
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(
            "SELECT c.conname, pg_get_constraintdef(c.oid) FROM pg_constraint c "
            "JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=ANY(c.conkey) "
            "WHERE c.conrelid=to_regclass(%s) AND c.contype='f' AND a.attname=%s",
            [table, column],
        )
        result = cursor.fetchone()
        assert result is not None
        return result


@pytest.mark.parametrize(
    "table,column",
    [
        ("payments_billing_paymentallocation", "company_id"),
        ("payments_billing_paymentallocation", "payment_id"),
        ("payments_billing_paymentallocation", "invoice_id"),
        ("payments_payment", "company_id"),
        ("payments_payment", "payer_party_id"),
        ("payments_payment", "currency_id"),
        ("payments_payment", "payment_method_id"),
        ("billing_invoice", "company_id"),
        ("billing_invoice", "bill_to_party_id"),
        ("billing_invoice", "currency_id"),
        ("billing_invoiceline", "company_id"),
        ("billing_invoiceline", "invoice_id"),
        ("payments_paymentmethod", "company_id"),
        ("party_party", "company_id"),
    ],
)
@pytest.mark.parametrize("drift", ["not_valid", "missing", "delete_cascade"])
def test_r2_expected_fk_definition_and_validation(
    postgres, business_context, parents, table, column, drift
):
    from psycopg import sql

    create(business_context, parents, amount="80")
    before = AuditEntry.objects.count()
    name, definition = foreign_key(table, column)
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("ALTER TABLE {} DROP CONSTRAINT {}").format(
                sql.Identifier(table), sql.Identifier(name)
            )
        )
        if drift != "missing":
            if drift == "delete_cascade":
                definition = definition.replace(" DEFERRABLE", " ON DELETE CASCADE DEFERRABLE")
            cursor.execute(
                sql.SQL("ALTER TABLE {} ADD CONSTRAINT {} {}{}").format(
                    sql.Identifier(table),
                    sql.Identifier(name),
                    sql.SQL(definition),
                    sql.SQL(" NOT VALID" if drift == "not_valid" else ""),
                )
            )
    assert compatibility.evidence_profile() == "incompatible"
    assert_unavailable(business_context, parents)
    with pytest.raises(ValidationError, match="unavailable"):
        create(business_context, parents, amount="20", key="rest")
    assert PaymentAllocation.objects.count() == 1 and AuditEntry.objects.count() == before


@pytest.mark.parametrize("side", ["payment", "invoice"])
def test_r2_orphan_outside_history_filter_is_not_omitted(postgres, business_context, parents, side):
    from psycopg import sql

    create(business_context, parents, amount="80")
    orphan = create(business_context, parents, amount="1", key="orphan")
    before = AuditEntry.objects.count()
    table = PaymentAllocation._meta.db_table
    name, definition = foreign_key(table, side + "_id")
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("ALTER TABLE {} DROP CONSTRAINT {}").format(
                sql.Identifier(table), sql.Identifier(name)
            )
        )
        cursor.execute(
            sql.SQL("UPDATE {} SET {}=%s WHERE id=%s").format(
                sql.Identifier(table), sql.Identifier(side + "_id")
            ),
            [uuid4(), orphan.pk],
        )
        cursor.execute(
            sql.SQL("ALTER TABLE {} ADD CONSTRAINT {} {} NOT VALID").format(
                sql.Identifier(table), sql.Identifier(name), sql.SQL(definition)
            )
        )
    assert compatibility.evidence_profile() == "incompatible"
    assert_unavailable(business_context, parents)
    with pytest.raises(ValidationError, match="unavailable"):
        create(business_context, parents, amount="20", key="rest")
    # Independent raw-history probe, without relying on the profile rejection.
    with pytest.raises(ValidationError, match="Missing allocation parent"):
        selectors.validate_history(business_context)
    assert PaymentAllocation.objects.count() == 2 and AuditEntry.objects.count() == before
    assert PaymentAllocation.objects.aggregate(total=Sum("amount"))["total"] == 81
    # Preserve malformed low-level fixture until assertions, then restore for
    # pytest's deferred-constraint teardown (DDL/data otherwise rollback).
    models.QuerySet.update(
        PaymentAllocation.objects.filter(pk=orphan.pk),
        **{side + "_id": parents[0 if side == "payment" else 1].pk},
    )


@pytest.mark.parametrize(
    "changed",
    ["issued", "draft", "currency", "nonexistent", "payment", "missing_payment", "amount", "scale"],
)
def test_r3_conflicts_lock_only_authoritative_stored_parents(
    business_context, parents, financial_factory, changed
):
    fact = create(business_context, parents, amount="10")
    before = AuditEntry.objects.count()
    proposed = parents
    amount = "10"
    if changed in {"issued", "draft", "currency", "payment"}:
        options = {"issued": changed != "draft"}
        if changed == "currency":
            options["currency_id"] = Currency.objects.create(code="EUR", name="Euro").pk
        alternative = financial_factory(**options)
        proposed = (
            (alternative[0], parents[1]) if changed == "payment" else (parents[0], alternative[1])
        )
    elif changed == "nonexistent":
        proposed = (parents[0], SimpleNamespace(pk=uuid4()))
    elif changed == "missing_payment":
        proposed = (SimpleNamespace(pk=uuid4()), parents[1])
    else:
        amount = "11" if changed == "amount" else "10.001"
    before = AuditEntry.objects.count()
    # Capture real owner locking calls while retaining actual implementation.
    with (
        patch.object(
            services, "payment_receipt_basis", wraps=services.payment_receipt_basis
        ) as payment_basis,
        patch.object(
            services, "invoice_financial_basis", wraps=services.invoice_financial_basis
        ) as invoice_basis,
        CaptureQueriesContext(connection) as queries,
    ):
        with pytest.raises(ValidationError) as error:
            create(business_context, proposed, amount=amount)
    assert error.value.code == "idempotency_conflict"
    payment_basis.assert_called_once_with(business_context, fact.payment_id)
    invoice_basis.assert_called_once_with(business_context, fact.invoice_id)
    locks = [q["sql"] for q in queries if "FOR UPDATE" in q["sql"]]
    if connection.vendor == "postgresql":
        p = next(i for i, q in enumerate(locks) if 'FROM "payments_payment"' in q)
        i = next(i for i, q in enumerate(locks) if 'FROM "billing_invoice"' in q)
        assert p < i
    assert PaymentAllocation.objects.count() == 1
    # Factory creation has its own audit; conflict has no additional success.
    assert AuditEntry.objects.filter(action="payments.allocation.created").count() == 1
    assert AuditEntry.objects.count() == before
    fact.refresh_from_db()
    assert (fact.payment_id, fact.invoice_id, fact.amount) == (parents[0].pk, parents[1].pk, 10)


@pytest.mark.parametrize("basis", ["payment", "invoice", "both"])
def test_r4_impossible_matching_fact_is_not_success(business_context, financial_factory, basis):
    parents = financial_factory(
        receipt="100" if basis != "invoice" else "200", total="100" if basis != "payment" else "200"
    )
    fact = create(business_context, parents, amount="10")
    models.QuerySet.update(PaymentAllocation.objects.filter(pk=fact.pk), amount=101)
    before = AuditEntry.objects.count()
    assert_unavailable(business_context, parents)
    with pytest.raises(ValidationError, match="intrinsically incompatible"):
        create(business_context, parents, amount="101")
    assert PaymentAllocation.objects.count() == 1 and AuditEntry.objects.count() == before
    fact.refresh_from_db()
    assert fact.amount == 101


@pytest.mark.parametrize("side", ["payment", "invoice", "both"])
def test_r4_fully_applied_history_retry_does_not_use_new_capacity(
    business_context, parents, financial_factory, side
):
    first = create(business_context, parents, amount="60", key="first")
    alternative = financial_factory()
    second_pair = (
        parents
        if side == "both"
        else (parents[0], alternative[1])
        if side == "payment"
        else (alternative[0], parents[1])
    )
    create(business_context, second_pair, amount="40", key="second")
    before = AuditEntry.objects.count()
    result = services.create_payment_allocation(
        business_context,
        payment_id=str(parents[0].pk).upper(),
        invoice_id=parents[1].pk.hex,
        amount=Decimal("6E1"),
        idempotency_key=" first ",
    )
    assert result.pk == first.pk
    assert (result.created_at, result.updated_at) == (first.created_at, first.updated_at)
    assert PaymentAllocation.objects.count() == 2 and AuditEntry.objects.count() == before
    selector = (
        selectors.invoice_allocation_evidence
        if side == "invoice"
        else selectors.payment_allocation_evidence
    )
    identity = parents[1].pk if side == "invoice" else parents[0].pk
    assert selector(business_context, identity).remaining == 0


@pytest.mark.parametrize(
    "corruption",
    ["company", "party", "currency", "code", "precision", "scale", "receipt", "line", "draft"],
)
def test_r4_matching_retry_revalidates_immutable_basis(
    business_context, parents, company, corruption
):
    first = create(business_context, parents, amount="10")
    original_times = (first.created_at, first.updated_at)
    if corruption == "company":
        other = Company.objects.create(
            code="OTHER",
            name="Other",
            base_currency=company.base_currency,
            country=company.country,
            default_language=company.default_language,
        )
        models.QuerySet.update(Payment.objects.filter(pk=parents[0].pk), company_id=other.pk)
    elif corruption == "party":
        other = Party.objects.create(company=company, party_type="person", display_name="Other")
        models.QuerySet.update(Invoice.objects.filter(pk=parents[1].pk), bill_to_party_id=other.pk)
    elif corruption == "currency":
        other = Currency.objects.create(code="EUR", name="Euro")
        models.QuerySet.update(
            Invoice.objects.filter(pk=parents[1].pk),
            currency_id=other.pk,
            currency_code_snapshot="EUR",
        )
    elif corruption == "code":
        # Equal corrupt frozen codes are not proof of matching currency provenance.
        for model, parent in ((Payment, parents[0]), (Invoice, parents[1])):
            models.QuerySet.update(model.objects.filter(pk=parent.pk), currency_code_snapshot="BAD")
    elif corruption == "precision":
        models.QuerySet.update(
            Invoice.objects.filter(pk=parents[1].pk), currency_decimal_places_snapshot=3
        )
    elif corruption == "scale":
        models.QuerySet.update(PaymentAllocation.objects.filter(pk=first.pk), amount="10.001")
    elif corruption == "receipt":
        models.QuerySet.update(Payment.objects.filter(pk=parents[0].pk), number="PAY-" + "a" * 32)
    elif corruption == "line":
        models.QuerySet.update(
            InvoiceLine.objects.filter(invoice_id=parents[1].pk), description=" "
        )
    else:
        models.QuerySet.update(
            Invoice.objects.filter(pk=parents[1].pk), status="draft", issued_at=None
        )
    before = AuditEntry.objects.count()
    with pytest.raises((ValidationError, PermissionDenied)):
        create(business_context, parents, amount="10.001" if corruption == "scale" else "10")
    assert PaymentAllocation.objects.count() == 1 and AuditEntry.objects.count() == before
    first.refresh_from_db()
    assert (first.created_at, first.updated_at) == original_times
