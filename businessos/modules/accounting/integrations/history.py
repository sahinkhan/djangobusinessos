"""SQL-only whole-binding integrity probes; no per-row certificate materialization."""

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db.models import (
    CharField,
    Count,
    DecimalField,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Value,
)
from django.db.models.functions import Cast, Coalesce, Concat, Replace, Round

from businessos.modules.accounting.models import JournalEntryLine
from businessos.modules.billing.selectors import issued_invoice_basis_query

from .billing.models import InvoicePosting


def _probe(context, posts, *, allocation=False, amounts=None):
    lines = JournalEntryLine.objects.filter(journal_entry_id=OuterRef("journal_entry_id"))
    counts = lines.order_by().values("journal_entry_id").annotate(total=Count("id")).values("total")
    aliases = {
        "proof_count": Coalesce(Subquery(counts, output_field=IntegerField()), 0),
        "proof_number": Concat(
            Value("JE-"),
            Replace(Cast(F("journal_entry_id"), output_field=CharField()), Value("-"), Value("")),
        ),
    }
    fields = (
        "id",
        "company_id",
        "account_id",
        "account__type",
        "party_id",
        "description",
        "debit",
        "credit",
        "created_at",
        "updated_at",
    )
    for position, prefix in ((1, "first"), (2, "second")):
        row = lines.filter(position=position)
        for field in fields:
            aliases[f"proof_{prefix}_{field.replace('__', '_')}"] = Subquery(row.values(field)[:1])
    if allocation:
        aliases["proof_amount"] = F("allocation__amount")
        date_field = "allocation__payment__payment_date"
        party_field = "allocation__payment__payer_party_id"
        unit_field = "allocation__payment__currency_code_snapshot"
        first_account, second_account = "cash_account_id", "ar_account_id"
    else:
        aliases["proof_amount"] = Subquery(
            amounts.filter(pk=OuterRef("invoice_id")).values("basis_total"),
            output_field=DecimalField(),
        )
        date_field, party_field, unit_field = (
            "invoice__invoice_date",
            "invoice__bill_to_party_id",
            "invoice__currency_code_snapshot",
        )
        first_account, second_account = "ar_account_id", "revenue_account_id"
    aliases["proof_first_rounded"] = Round(
        "proof_first_debit", F("journal_entry__base_currency_precision_snapshot")
    )
    aliases["proof_second_rounded"] = Round(
        "proof_second_credit", F("journal_entry__base_currency_precision_snapshot")
    )
    posts = posts.alias(**aliases)
    memo = F("journal_entry__memo")
    valid = Q(
        company_id=context.company_id,
        journal_entry__company_id=context.company_id,
        journal_entry__journal_id=F("journal_id"),
        journal_entry__status="POSTED",
        journal_entry__posted_at__isnull=False,
        journal_entry__number=F("proof_number"),
        journal_entry__entry_date=F(date_field),
        journal_entry__base_currency_code_snapshot=F(unit_field),
        journal_entry__created_at__isnull=False,
        # Same atomic _post UPDATE; unlike independent wall-clock reads, equality
        # of these two fields is guaranteed by the owner write contract.
        journal_entry__updated_at=F("journal_entry__posted_at"),
        created_at__isnull=False,
        updated_at__isnull=False,
        proof_amount__gt=0,
        proof_count=2,
        proof_first_id__isnull=False,
        proof_second_id__isnull=False,
        proof_first_company_id=context.company_id,
        proof_second_company_id=context.company_id,
        proof_first_account_id=F(first_account),
        proof_second_account_id=F(second_account),
        proof_first_account_type="ASSET",
        proof_second_account_type="ASSET" if allocation else "INCOME",
        proof_first_debit=F("proof_amount"),
        proof_first_credit=0,
        proof_second_debit=0,
        proof_second_credit=F("proof_amount"),
        proof_first_debit__exact=F("proof_first_rounded"),
        proof_second_credit__exact=F("proof_second_rounded"),
        proof_first_description=Concat(memo, Value(" / Cash-Bank" if allocation else " / AR")),
        proof_second_description=Concat(memo, Value(" / AR" if allocation else " / Revenue")),
        proof_first_created_at__isnull=False,
        proof_first_updated_at__isnull=False,
        proof_second_created_at__isnull=False,
        proof_second_updated_at__isnull=False,
    )
    if allocation:
        valid &= Q(
            proof_first_party_id__isnull=True,
            proof_second_party_id__isnull=False,
            proof_second_party_id=F(party_field),
            invoice_posting__invoice_id=F("allocation__invoice_id"),
            invoice_posting__ar_account_id=F("ar_account_id"),
            invoice_posting__created_at__isnull=False,
            allocation__created_at__isnull=False,
            allocation__payment__recorded_at__isnull=False,
            allocation__payment__currency_id=F("company__base_currency_id"),
        ) & ~Q(cash_account_id=F("ar_account_id"))
    else:
        valid &= Q(
            proof_first_party_id__isnull=False,
            proof_first_party_id=F(party_field),
            proof_second_party_id__isnull=True,
            invoice__bill_to_party__party_type__in=["person", "organization"],
            invoice__issued_at__isnull=False,
            invoice__currency_id=F("company__base_currency_id"),
        )
    if posts.exclude(valid).exists():
        raise ValidationError("Complete posting history contains incompatible native facts.")


def validate_binding_history(context, *, allocation=False):
    # Raw endpoint existence/ownership admission runs BEFORE these joins.
    invoices = InvoicePosting.objects.filter(company_id=context.company_id)
    amounts = issued_invoice_basis_query(context, invoice_ids=invoices.values("invoice_id"))
    if amounts.filter(basis_valid=False).exists():
        raise ValidationError("A bound Invoice has incomplete financial evidence.")
    _probe(context, invoices, amounts=amounts)
    if allocation:
        from businessos.modules.payments.integrations.billing.selectors import validate_history

        validate_history(context)
        # Explicit fixed opt-in app identity, not a plugin/runtime registry abstraction.
        model = apps.get_model("accounting_payments_billing", "AllocationPosting")
        posts = model.objects.filter(company_id=context.company_id)
        _probe(context, posts, allocation=True)
