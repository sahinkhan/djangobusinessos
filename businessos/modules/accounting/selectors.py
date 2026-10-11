from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import DecimalField, F, Max, Q, Sum
from django.db.models.functions import Round

from businessos.core.access.policies import require_permission
from businessos.core.database import current_database_alias
from businessos.core.organization.models import Company

from . import domain
from .manifest import VIEW_ACCOUNTS, VIEW_ENTRIES, VIEW_JOURNALS
from .models import Account, Journal, JournalEntry, JournalEntryLine


def accounts_for_company(context, *, search="", active=""):
    require_permission(context, VIEW_ACCOUNTS)
    return _references(Account, context, search, active)


def journals_for_company(context, *, search="", active=""):
    require_permission(context, VIEW_JOURNALS)
    return _references(Journal, context, search, active)


def _references(model, context, search, active):
    rows = model.objects.filter(company_id=context.company_id)
    if search.strip():
        rows = rows.filter(Q(code__icontains=search.strip()) | Q(name__icontains=search.strip()))
    if active in {"yes", "no"}:
        rows = rows.filter(is_active=active == "yes")
    return rows.order_by("code", "id")


def journal_entries_for_company(context, *, search="", status=""):
    require_permission(context, VIEW_ENTRIES)
    rows = JournalEntry.objects.filter(company_id=context.company_id).select_related("journal")
    if search.strip():
        rows = rows.filter(Q(number__icontains=search.strip()) | Q(memo__icontains=search.strip()))
    if status in JournalEntry.Status.values:
        rows = rows.filter(status=status)
    return rows.order_by("-entry_date", "-created_at", "id")


def journal_entry_detail(context, entry_id):
    return (
        journal_entries_for_company(context)
        .prefetch_related(
            "lines__account",
            "lines__party",
        )
        .get(pk=entry_id)
    )


def _date(value):
    try:
        return domain.business_date(value) if value is not None else None
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def _report_scope(context, *, from_date=None, to_date=None, account_id=None):
    require_permission(context, VIEW_ENTRIES)
    alias = current_database_alias()
    start, end = _date(from_date), _date(to_date)
    if start and end and start > end:
        raise ValidationError("From date must not follow to date.")
    if account_id is not None:
        try:
            account_id = domain.identity(account_id)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if (
            not Account.objects.using(alias)
            .filter(pk=account_id, company_id=context.company_id)
            .exists()
        ):
            raise ValidationError("Account filter is outside this company.")
    code = (
        Company.objects.using(alias)
        .values_list("base_currency__code", flat=True)
        .get(pk=context.company_id)
    )
    _validate_report_history(context.company_id, code, alias)
    rows = JournalEntryLine.objects.using(alias).filter(
        company_id=context.company_id,
        journal_entry__company_id=context.company_id,
        journal_entry__status=JournalEntry.Status.POSTED,
    )
    if start:
        rows = rows.filter(journal_entry__entry_date__gte=start)
    if end:
        rows = rows.filter(journal_entry__entry_date__lte=end)
    if account_id is not None:
        rows = rows.filter(account_id=account_id)
    return rows, code


def _validate_report_history(company_id, code, alias):
    # Include either ownership side, including corruption OUTSIDE requested filters.
    # EXISTS returns one constant, never memo/description/reference/model payloads.
    history = JournalEntryLine.objects.using(alias).filter(
        Q(company_id=company_id) | Q(journal_entry__company_id=company_id),
        journal_entry__status=JournalEntry.Status.POSTED,
    )
    valid = (
        Q(
            company_id=company_id,
            journal_entry__company_id=company_id,
            account__company_id=company_id,
            journal_entry__journal__company_id=company_id,
            journal_entry__base_currency_code_snapshot=code,
            journal_entry__base_currency_precision_snapshot__gte=0,
            journal_entry__base_currency_precision_snapshot__lte=8,
            position__gte=1,
            position__lte=domain.MAX_POSITION,
            debit__gte=0,
            debit__lt=domain.AMOUNT_LIMIT,
            credit__gte=0,
            credit__lt=domain.AMOUNT_LIMIT,
        )
        & (Q(party_id__isnull=True) | Q(party__company_id=company_id))
        & (Q(debit__gt=0, credit=0) | Q(credit__gt=0, debit=0))
    )
    if history.exclude(valid).exists():
        raise ValidationError("Accounting history has incompatible company/currency provenance.")
    # Preserve line.clean's exact frozen-scale validation without Python line reads.
    # SQL ROUND is only an equality probe; report amounts are NEVER rounded.
    if (
        history.alias(
            valid_debit=Round("debit", F("journal_entry__base_currency_precision_snapshot")),
            valid_credit=Round("credit", F("journal_entry__base_currency_precision_snapshot")),
        )
        .exclude(debit=F("valid_debit"), credit=F("valid_credit"))
        .exists()
    ):
        raise ValidationError("Accounting history exceeds frozen currency precision.")


def general_ledger(context, *, from_date=None, to_date=None, account_id=None):
    """Authorized, scoped lazy payload. Slice/Paginator BEFORE evaluating rows.

    Pin the alias at authorization time, even if evaluated after execution scope exit.
    Whole-history integrity is separate from SQL-filtered/page-bounded payload reads.
    """
    rows, _ = _report_scope(context, from_date=from_date, to_date=to_date, account_id=account_id)
    return rows.select_related("journal_entry", "account", "party").order_by(
        "journal_entry__entry_date",
        "journal_entry__number",
        "journal_entry_id",
        "position",
        "id",
    )


@dataclass(frozen=True)
class TrialBalanceRow:
    account: Account
    total_debit: Decimal
    total_credit: Decimal
    net: Decimal
    ending_debit: Decimal
    ending_credit: Decimal
    currency_code: str
    precision: int

    @property
    def formatted_debit(self):
        return domain.display(self.total_debit, self.precision)

    @property
    def formatted_credit(self):
        return domain.display(self.total_credit, self.precision)

    @property
    def formatted_ending_debit(self):
        return domain.display(self.ending_debit, self.precision)

    @property
    def formatted_ending_credit(self):
        return domain.display(self.ending_credit, self.precision)


def trial_balance(context, **filters):
    lines, code = _report_scope(context, **filters)
    # PostgreSQL SUM(numeric) has no single-line typmod. A deliberately unbounded
    # output field preserves its exact Decimal; never cast to numeric(38,8) or float.
    account_fields = [field.attname for field in Account._meta.concrete_fields]
    grouped = list(
        lines.order_by()
        .values(*(f"account__{field}" for field in account_fields))
        .annotate(
            total_debit=Sum("debit", output_field=DecimalField()),
            total_credit=Sum("credit", output_field=DecimalField()),
            precision=Max("journal_entry__base_currency_precision_snapshot"),
        )
        .order_by("account__code", "account__id")
    )
    # Existing presentation uses one report-wide maximum, >= each Account maximum.
    places = max((row["precision"] for row in grouped), default=0)
    result = []
    for group in grouped:
        debit, credit = group["total_debit"], group["total_credit"]
        net = domain.net(debit, credit)
        result.append(
            TrialBalanceRow(
                Account.from_db(
                    lines.db,
                    account_fields,
                    [group[f"account__{field}"] for field in account_fields],
                ),
                debit,
                credit,
                net,
                max(net, Decimal(0)),
                max(domain.net(Decimal(0), net), Decimal(0)),
                code,
                places,
            )
        )
    return result
