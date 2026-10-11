from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Q

from businessos.core.access.policies import require_permission
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


def general_ledger(context, *, from_date=None, to_date=None, account_id=None):
    require_permission(context, VIEW_ENTRIES)
    start, end = _date(from_date), _date(to_date)
    if start and end and start > end:
        raise ValidationError("From date must not follow to date.")
    if account_id is not None:
        try:
            account_id = domain.identity(account_id)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if not Account.objects.filter(pk=account_id, company_id=context.company_id).exists():
            raise ValidationError("Account filter is outside this company.")
    code = (
        Company.objects.select_related("base_currency")
        .get(pk=context.company_id)
        .base_currency.code
    )
    # Include either ownership side, then FAIL rather than hide malformed history.
    rows = list(
        JournalEntryLine.objects.filter(
            Q(company_id=context.company_id) | Q(journal_entry__company_id=context.company_id),
            journal_entry__status=JournalEntry.Status.POSTED,
        )
        .select_related("journal_entry", "journal_entry__journal", "account", "party")
        .order_by(
            "journal_entry__entry_date",
            "journal_entry__number",
            "journal_entry_id",
            "position",
            "id",
        )
    )
    for row in rows:
        entry = row.journal_entry
        if (
            row.company_id != context.company_id
            or entry.company_id != context.company_id
            or row.account.company_id != context.company_id
            or entry.journal.company_id != context.company_id
            or (row.party_id and row.party.company_id != context.company_id)
            or entry.base_currency_code_snapshot != code
        ):
            raise ValidationError(
                "Accounting history has incompatible company/currency provenance."
            )
        row.clean()
    return [
        row
        for row in rows
        if (not start or row.journal_entry.entry_date >= start)
        and (not end or row.journal_entry.entry_date <= end)
        and (account_id is None or row.account_id == account_id)
    ]


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
    lines = general_ledger(context, **filters)
    grouped = {}
    places = max((line.journal_entry.base_currency_precision_snapshot for line in lines), default=0)
    for line in lines:
        grouped.setdefault(line.account_id, []).append(line)
    result = []
    for group in grouped.values():
        debit, credit = domain.totals((line.debit, line.credit) for line in group)
        net = domain.net(debit, credit)
        result.append(
            TrialBalanceRow(
                group[0].account,
                debit,
                credit,
                net,
                max(net, Decimal(0)),
                max(domain.net(Decimal(0), net), Decimal(0)),
                group[0].journal_entry.base_currency_code_snapshot,
                places,
            )
        )
    return sorted(result, key=lambda row: (row.account.code, row.account.pk))
