from decimal import Decimal, localcontext
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection

from businessos.core.reference.models import Currency
from businessos.modules.accounting.integrations.billing.selectors import invoice_posting_status
from businessos.modules.accounting.models import JournalEntry
from businessos.modules.billing import services as billing

from .test_outcomes import invoice_post

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Exact high-precision SQL, raw provenance and nonprivileged PostgreSQL RLS.")


def test_38_digit_sql_basis_independent_oracle(business_context, outcomes, currency):
    Currency.objects.filter(pk=currency.pk).update(decimal_places=8)
    invoice = billing.create_invoice(
        business_context,
        bill_to_party_id=outcomes["party"].pk,
        currency_id=currency.pk,
        invoice_date="2026-10-12",
    )
    for _ in range(100):
        billing.add_invoice_line(
            business_context,
            invoice.pk,
            description="Boundary",
            quantity="99999999999999.9999",
            unit_price="99999999999999.9999",
        )
    invoice = billing.issue_invoice(business_context, invoice.pk)
    with localcontext() as ctx:
        ctx.prec = 80
        expected = (Decimal("99999999999999.9999") ** 2 * 100).quantize(Decimal("0.00000001"))
    assert len(expected.as_tuple().digits) == 38
    outcome = invoice_post(business_context, outcomes, invoice)
    assert outcome.amount == expected
    assert invoice_posting_status(business_context, invoice.pk).amount == expected


@pytest.mark.parametrize(
    "table", ["accounting_billing_invoiceposting", "accounting_journalentryline"]
)
def test_nonprivileged_hidden_posted_history_fails_closed(business_context, outcomes, table):
    invoice, _, _ = outcomes["sources"]("1", None)
    invoice_post(business_context, outcomes, invoice)
    role = "accint1_hidden_" + uuid4().hex
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(f'CREATE ROLE "{role}" NOSUPERUSER NOBYPASSRLS NOLOGIN')
        cursor.execute(f'GRANT USAGE ON SCHEMA public TO "{role}"')
        cursor.execute(f'GRANT ALL ON ALL TABLES IN SCHEMA public TO "{role}"')
        cursor.execute(f'GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO "{role}"')
        cursor.execute(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY')
        cursor.execute(f'CREATE POLICY hide_history ON public."{table}" USING(false)')
        try:
            cursor.execute(f'SET LOCAL ROLE "{role}"')
            cursor.execute(f'SELECT count(*) FROM public."{table}"')
            assert cursor.fetchone()[0] == 0
            assert invoice_posting_status(business_context, invoice.pk).state == "UNAVAILABLE"
            with pytest.raises(ValidationError):
                invoice_post(business_context, outcomes, invoice)
        finally:
            cursor.execute("RESET ROLE")
            cursor.execute(f'DROP OWNED BY "{role}"')
            cursor.execute(f'DROP ROLE "{role}"')
    assert JournalEntry.objects.count() == 1


def test_raw_orphan_is_not_known_absence(business_context, outcomes):
    invoice, _, _ = outcomes["sources"]("1", None)
    with connection.cursor() as cursor:
        # Synthetic deferred-FK fault; roll back this savepoint without committing bad data.
        cursor.execute("SAVEPOINT orphan_probe")
        cursor.execute(
            "UPDATE billing_invoiceline SET invoice_id=%s WHERE invoice_id=%s",
            [uuid4(), invoice.pk],
        )
        try:
            assert invoice_posting_status(business_context, invoice.pk).state == "UNAVAILABLE"
            with pytest.raises(ValidationError):
                invoice_post(business_context, outcomes, invoice)
        finally:
            cursor.execute("ROLLBACK TO SAVEPOINT orphan_probe")
            cursor.execute("RELEASE SAVEPOINT orphan_probe")
    assert not JournalEntry.objects.exists()
