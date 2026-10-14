"""Bounded posting proof shared by the two Accounting-owned effects."""

from decimal import Decimal

from django.apps import apps
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connections
from django.utils import timezone

from businessos.core.database import current_database_alias
from businessos.modules.accounting import services as accounting
from businessos.modules.accounting.models import Account, Journal, JournalEntry
from businessos.modules.accounting.selectors import posted_journal_basis
from businessos.modules.billing.selectors import invoice_accounting_basis
from businessos.modules.party.models import Party

from .admission import authorize
from .domain import PostingOutcomeV1, source_amount


def _bad():
    raise ValidationError("Accounting posting evidence is intrinsically incompatible.")


def raw_provenance(context, *, allocation=False):
    """Existence/ownership checks BEFORE INNER JOIN/scoped materialization can drop facts."""
    connection = connections[current_database_alias()]
    prefix = "public." if connection.vendor == "postgresql" else "main."

    def canonical(column):
        if connection.vendor == "postgresql":
            return f"CAST({column} AS text)"
        return (
            f"substr({column},1,8)||'-'||substr({column},9,4)||'-'||"
            f"substr({column},13,4)||'-'||substr({column},17,4)||'-'||"
            f"substr({column},21,12)"
        )

    def probe(query, params):
        # All table names are static application-owned identifiers admitted by profile.
        import re

        query = re.sub(
            r"\b(organization_company|reference_currency|party_party|billing_invoice(?:line)?|"
            r"accounting_(?:account|journalentryline|journalentry|journal)|"
            r"accounting_billing_invoiceposting|accounting_payments_billing_allocationposting|"
            r"payments_billing_paymentallocation|payments_payment)\b",
            lambda match: prefix + match.group(),
            query,
        )
        with connection.cursor() as cursor:
            if connection.vendor == "sqlite":
                params = [value.hex if hasattr(value, "hex") else value for value in params]
            cursor.execute("SELECT EXISTS(" + query + ")", params)
            if cursor.fetchone()[0]:
                _bad()

    probe(
        """
        SELECT 1 FROM billing_invoiceline l WHERE
        (l.company_id=%s OR EXISTS(SELECT 1 FROM billing_invoice i
            WHERE i.id=l.invoice_id AND i.company_id=%s))
        AND NOT EXISTS(SELECT 1 FROM billing_invoice i
            WHERE i.id=l.invoice_id AND i.company_id=l.company_id)
    """,
        [context.company_id, context.company_id],
    )
    probe(
        """
        SELECT 1 FROM billing_invoice i WHERE i.company_id=%s AND (
        NOT EXISTS(SELECT 1 FROM party_party p WHERE p.id=i.bill_to_party_id
            AND p.company_id=i.company_id)
        OR NOT EXISTS(SELECT 1 FROM reference_currency c WHERE c.id=i.currency_id))
    """,
        [context.company_id],
    )
    probe(
        f"""
        SELECT 1 FROM accounting_billing_invoiceposting b WHERE
        (b.company_id=%s OR EXISTS(SELECT 1 FROM billing_invoice i
            WHERE i.id=b.invoice_id AND i.company_id=%s)
         OR EXISTS(SELECT 1 FROM accounting_journalentry e
            WHERE e.id=b.journal_entry_id AND e.company_id=%s)) AND (
        b.effect<>'billing_invoice_ar_revenue_v1'
        OR NOT EXISTS(SELECT 1 FROM billing_invoice i
            WHERE i.id=b.invoice_id AND i.company_id=b.company_id)
        OR NOT EXISTS(SELECT 1 FROM accounting_journalentry e
            WHERE e.id=b.journal_entry_id AND e.company_id=b.company_id
            AND e.journal_id=b.journal_id AND e.status='POSTED'
            AND e.memo='ACC-INT-1 v1 invoice '||{canonical("b.invoice_id")})
        OR NOT EXISTS(SELECT 1 FROM accounting_journal j
            WHERE j.id=b.journal_id AND j.company_id=b.company_id)
        OR NOT EXISTS(SELECT 1 FROM accounting_account a
            WHERE a.id=b.ar_account_id AND a.company_id=b.company_id)
        OR NOT EXISTS(SELECT 1 FROM accounting_account a
            WHERE a.id=b.revenue_account_id AND a.company_id=b.company_id))
    """,
        [context.company_id] * 3,
    )
    probe(
        """
        SELECT 1 FROM accounting_journalentryline l WHERE
        (l.company_id=%s OR EXISTS(SELECT 1 FROM accounting_journalentry e
            WHERE e.id=l.journal_entry_id AND e.company_id=%s)) AND (
        NOT EXISTS(SELECT 1 FROM accounting_journalentry e
            WHERE e.id=l.journal_entry_id AND e.company_id=l.company_id)
        OR NOT EXISTS(SELECT 1 FROM accounting_account a
            WHERE a.id=l.account_id AND a.company_id=l.company_id)
        OR (l.party_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM party_party p
            WHERE p.id=l.party_id AND p.company_id=l.company_id)))
    """,
        [context.company_id] * 2,
    )
    if allocation or apps.is_installed(
        "businessos.modules.accounting.integrations.payments_billing"
    ):
        probe(
            """
            SELECT 1 FROM accounting_payments_billing_allocationposting b WHERE
            (b.company_id=%s OR EXISTS(SELECT 1 FROM payments_billing_paymentallocation a
                WHERE a.id=b.allocation_id AND a.company_id=%s)
             OR EXISTS(SELECT 1 FROM accounting_journalentry e
                WHERE e.id=b.journal_entry_id AND e.company_id=%s)) AND (
            b.effect<>'payment_allocation_cash_ar_v1'
            OR NOT EXISTS(SELECT 1 FROM payments_billing_paymentallocation a
                WHERE a.id=b.allocation_id AND a.company_id=b.company_id)
            OR NOT EXISTS(SELECT 1 FROM accounting_journalentry e
                WHERE e.id=b.journal_entry_id AND e.company_id=b.company_id)
            OR NOT EXISTS(SELECT 1 FROM accounting_billing_invoiceposting i
                WHERE i.id=b.invoice_posting_id AND i.company_id=b.company_id)
            OR NOT EXISTS(SELECT 1 FROM accounting_journal j
                WHERE j.id=b.journal_id AND j.company_id=b.company_id)
            OR NOT EXISTS(SELECT 1 FROM accounting_account a
                WHERE a.id=b.ar_account_id AND a.company_id=b.company_id)
            OR NOT EXISTS(SELECT 1 FROM accounting_account a
                WHERE a.id=b.cash_account_id AND a.company_id=b.company_id)
            OR EXISTS(SELECT 1 FROM accounting_billing_invoiceposting i
                WHERE i.journal_entry_id=b.journal_entry_id))
        """,
            [context.company_id] * 3,
        )

    from .history import validate_binding_history

    validate_binding_history(context, allocation=allocation)


def lock_entries(context, *entry_ids):
    ids = sorted(set(entry_ids))
    rows = list(JournalEntry.objects.select_for_update().filter(pk__in=ids).order_by("id"))
    if len(rows) != len(ids) or any(row.company_id != context.company_id for row in rows):
        _bad()


def _timestamps(binding):
    if any(
        stamp is None or timezone.is_naive(stamp)
        for stamp in (binding.created_at, binding.updated_at)
    ):
        _bad()


def validate_posting(
    context,
    binding,
    *,
    source,
    amount,
    business_date,
    party_id,
    first_id,
    second_id,
    effect,
    currency_code,
    source_precision,
):
    _timestamps(binding)
    entry = posted_journal_basis(context, binding.journal_entry_id, lock=False)
    # Owner basis and exact immutable provenance establish validity, not ordering
    # of independent wall-clock reads. Preserve the recorded timestamps verbatim.
    source_id = binding.invoice_id if source == "invoice" else binding.allocation_id
    memo = f"ACC-INT-1 v1 {source} {source_id}"
    first, second = entry.lines
    suffixes = ("AR", "Revenue") if source == "invoice" else ("Cash-Bank", "AR")
    parties = (party_id, None) if source == "invoice" else (None, party_id)
    types = ("ASSET", "INCOME") if source == "invoice" else ("ASSET", "ASSET")
    amount = source_amount(amount, source_precision)
    source_amount(amount, entry.precision)
    if (
        amount <= 0
        or binding.company_id != context.company_id
        or binding.effect != effect
        or entry.journal_id != binding.journal_id
        or entry.entry_date != business_date
        or entry.memo != memo
        or entry.currency_code != currency_code
        or (first.position, second.position) != (1, 2)
        or (first.account_id, second.account_id) != (first_id, second_id)
        or (first.account_type, second.account_type) != types
        or (first.party_id, second.party_id) != parties
        or (first.description, second.description) != tuple(f"{memo} / {s}" for s in suffixes)
        or (first.debit, first.credit, second.debit, second.credit)
        != (amount, Decimal(0), Decimal(0), amount)
        or (entry.debit, entry.credit) != (amount, amount)
        or (source == "allocation" and first_id == second_id)
    ):
        _bad()
    return PostingOutcomeV1(
        "POSTED",
        binding.invoice_id if source == "invoice" else binding.allocation_id,
        effect,
        binding.pk,
        entry.id,
        entry.number,
        amount,
        business_date,
        currency_code,
        entry.precision,
        entry.posted_at,
        binding.created_at,
    )


def invoice_certificate(context, binding):
    basis = invoice_accounting_basis(context, binding.invoice_id, lock=False)
    return validate_posting(
        context,
        binding,
        source="invoice",
        amount=basis.original_total,
        business_date=basis.invoice_date,
        party_id=basis.bill_to_party_id,
        first_id=binding.ar_account_id,
        second_id=binding.revenue_account_id,
        effect="billing_invoice_ar_revenue_v1",
        currency_code=basis.currency_code,
        source_precision=basis.precision,
    )


def lock_choices(
    context,
    company,
    *,
    journal_id,
    ar_account_id,
    other_account_id,
    other_type,
    party_id,
    allocation=False,
):
    journal = (
        Journal.objects.select_for_update()
        .filter(pk=journal_id, company_id=context.company_id)
        .first()
    )
    authorize(context, allocation=allocation, create=True)
    if journal is None or not journal.is_active:
        raise ValidationError({"journal_id": "Select an active Journal in this company."})
    accounts = list(
        Account.objects.select_for_update()
        .filter(pk__in=sorted({ar_account_id, other_account_id}))
        .order_by("id")
    )
    authorize(context, allocation=allocation, create=True)
    by_id = {row.pk: row for row in accounts}
    if len(by_id) != len({ar_account_id, other_account_id}):
        raise ValidationError("Select existing Accounts in this company.")
    ar, other = by_id[ar_account_id], by_id[other_account_id]
    if (
        any(row.company_id != context.company_id or not row.is_active for row in accounts)
        or ar.type != "ASSET"
        or other.type != other_type
        or (allocation and ar.pk == other.pk)
    ):
        raise ValidationError("Account choices have incompatible ownership/activity/types.")
    party = Party.objects.select_for_update().filter(pk=party_id).first()
    authorize(context, allocation=allocation, create=True)
    if (
        party is None
        or party.company_id != context.company_id
        or not party.is_active
        or party.party_type not in {"person", "organization"}
    ):
        raise ValidationError("An active person/organization Party in this company is required.")
    # Currency precision is live only for NEW public Accounting entry creation.
    from businessos.core.reference.models import Currency

    currency = Currency.objects.select_for_update().get(pk=company.base_currency_id)
    authorize(context, allocation=allocation, create=True)
    return currency


def compose(
    context,
    *,
    journal_id,
    first_id,
    second_id,
    party_id,
    amount,
    business_date,
    source,
    source_id,
    allocation=False,
):
    memo = f"ACC-INT-1 v1 {source} {source_id}"
    entry = accounting.create_journal_entry(
        context, journal_id=journal_id, entry_date=business_date, memo=memo
    )
    source_amount(amount, entry.base_currency_precision_snapshot)
    suffixes = ("AR", "Revenue") if source == "invoice" else ("Cash-Bank", "AR")
    for index, account_id in enumerate((first_id, second_id)):
        accounting.add_journal_entry_line(
            context,
            entry.pk,
            account_id=account_id,
            party_id=party_id if index == (0 if source == "invoice" else 1) else None,
            description=f"{memo} / {suffixes[index]}",
            debit=amount if index == 0 else Decimal(0),
            credit=amount if index == 1 else Decimal(0),
        )
        authorize(context, allocation=allocation, create=True)
    accounting.post_journal_entry(context, entry.pk)
    authorize(context, allocation=allocation, create=True)
    return entry


def conflict(binding, journal_id, ar_account_id, other_account_id, other_field):
    # No alternate object lookup; request choices cannot contaminate intrinsic proof.
    if (binding.journal_id, binding.ar_account_id, getattr(binding, other_field)) != (
        journal_id,
        ar_account_id,
        other_account_id,
    ):
        raise ValidationError(
            "Posting choices differ from the original.", code="idempotency_conflict"
        )


def require_base(company, source_currency_id, code):
    if company.base_currency_id != source_currency_id or company.base_currency.code != code:
        raise ValidationError("Only the Company's authoritative base currency is supported.")


def source_in_scope(model, context, source_id):
    if not model.objects.filter(pk=source_id, company_id=context.company_id).exists():
        raise PermissionDenied("Source is unavailable in this company.")
