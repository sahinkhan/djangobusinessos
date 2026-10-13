from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.db.models import Max, Q
from django.utils import timezone

from businessos.core.access.policies import require_final_permission, require_permission
from businessos.core.audit.services import record_audit_entry
from businessos.core.common.context import BusinessContext
from businessos.core.database import business_atomic, business_atomic_context
from businessos.core.organization.models import Company
from businessos.core.organization.time import company_local_date
from businessos.modules.party.models import Party

from . import domain
from .manifest import CREATE_ENTRIES, MANAGE_ACCOUNTS, MANAGE_JOURNALS, POST_ENTRIES, UPDATE_ENTRIES
from .models import _POST_TOKEN, _WRITE_TOKEN, Account, Journal, JournalEntry, JournalEntryLine


def _value(field, function, value, **kwargs):
    try:
        return function(value, **kwargs)
    except ValueError as exc:
        raise ValidationError({field: str(exc)}) from exc


def _authorize(context: BusinessContext, permission):
    company = (
        Company.objects.select_for_update()
        .filter(
            pk=context.company_id,
            is_active=True,
        )
        .first()
    )
    if company is None:
        raise PermissionDenied("The selected company does not exist or is inactive.")
    require_permission(context, permission)
    return company


def _audit(context, instance, action, **metadata):
    record_audit_entry(
        context=context,
        action=f"accounting.{action}",
        object_type=f"accounting.{type(instance).__name__}",
        object_id=instance.pk,
        metadata=metadata,
    )


def _locked(context, model, identity, field):
    identity = _value(field, domain.identity, identity)
    try:
        return model.objects.select_for_update().get(pk=identity, company_id=context.company_id)
    except model.DoesNotExist as exc:
        raise ValidationError({field: "Select a record in this company."}) from exc


def _activity(value):
    if type(value) is not bool:
        raise ValidationError({"is_active": "Use a boolean activity value."})
    return value


def _create_reference(context, permission, model, code, name, is_active, **extra):
    code = _value("code", domain.text, code, maximum=32, required=True, uppercase=True, trim=True)
    name = _value("name", domain.text, name, maximum=160, required=True, trim=True)
    if model.objects.filter(company_id=context.company_id, code=code).exists():
        raise ValidationError({"code": "A record with this normalized code already exists."})
    row = model(
        company_id=context.company_id, code=code, name=name, is_active=_activity(is_active), **extra
    )
    require_final_permission(context, permission)
    try:
        with business_atomic_context():
            row._persist(_WRITE_TOKEN, creating=True)
    except IntegrityError as exc:
        if model.objects.filter(company_id=context.company_id, code=code).exists():
            raise ValidationError({"code": "This normalized code already exists."}) from exc
        raise
    _audit(context, row, f"{model.__name__.lower()}.created", code=code)
    return row


def _update_reference(context, permission, model, identity, changes):
    if changes.keys() - {"name", "is_active"}:
        raise ValidationError("Only name/activity may change; reference identity is immutable.")
    row = _locked(context, model, identity, model.__name__.lower())
    before = {f: getattr(row, f) for f in ("name", "is_active")}
    if "name" in changes:
        row.name = _value(
            "name", domain.text, changes["name"], maximum=160, required=True, trim=True
        )
    if "is_active" in changes:
        row.is_active = _activity(changes["is_active"])
    fields = [f for f in before if before[f] != getattr(row, f)]
    require_final_permission(context, permission)
    if fields:
        row._persist(_WRITE_TOKEN)
        _audit(context, row, f"{model.__name__.lower()}.updated", fields=fields)
    return row


@business_atomic
def create_account(context: BusinessContext, *, code, name, type, is_active=True):
    _authorize(context, MANAGE_ACCOUNTS)
    if type not in Account.Type.values:
        raise ValidationError({"type": "Select a supported Account type."})
    return _create_reference(context, MANAGE_ACCOUNTS, Account, code, name, is_active, type=type)


@business_atomic
def update_account(context: BusinessContext, account_id, **changes):
    _authorize(context, MANAGE_ACCOUNTS)
    return _update_reference(context, MANAGE_ACCOUNTS, Account, account_id, changes)


@business_atomic
def create_journal(context: BusinessContext, *, code, name, is_active=True):
    _authorize(context, MANAGE_JOURNALS)
    return _create_reference(context, MANAGE_JOURNALS, Journal, code, name, is_active)


@business_atomic
def update_journal(context: BusinessContext, journal_id, **changes):
    _authorize(context, MANAGE_JOURNALS)
    return _update_reference(context, MANAGE_JOURNALS, Journal, journal_id, changes)


def _draft(entry):
    if entry.status != JournalEntry.Status.DRAFT:
        raise ValidationError("Only draft journal entries may change.")


def _journals(context, ids, *, active_ids=None):
    rows = {
        row.pk: row
        for row in Journal.objects.select_for_update()
        .filter(
            pk__in=ids,
            company_id=context.company_id,
        )
        .order_by("id")
    }
    required = set(ids) if active_ids is None else active_ids
    if set(rows) != set(ids) or any(not rows[i].is_active for i in required):
        raise ValidationError({"journal": "Select an active journal in this company."})
    return rows


def _references(context, account_ids, party_ids, *, active_accounts=None, active_parties=None):
    accounts = {
        row.pk: row
        for row in Account.objects.select_for_update()
        .filter(
            pk__in=account_ids,
            company_id=context.company_id,
        )
        .order_by("id")
    }
    parties = {
        row.pk: row
        for row in Party.objects.select_for_update()
        .filter(
            pk__in=party_ids,
            company_id=context.company_id,
        )
        .order_by("id")
    }
    required_accounts = account_ids if active_accounts is None else active_accounts
    required_parties = party_ids if active_parties is None else active_parties
    if set(accounts) != set(account_ids) or any(
        not accounts[i].is_active for i in required_accounts
    ):
        raise ValidationError({"account": "Select an active account in this company."})
    if set(parties) != set(party_ids) or any(
        not parties[i].is_active or parties[i].party_type not in Party.Type.values
        for i in required_parties
    ):
        raise ValidationError({"party": "Select an active person/organization in this company."})
    return accounts, parties


def _collision(exc):
    constraint = getattr(getattr(exc.__cause__, "diag", None), "constraint_name", None)
    return constraint in {"accounting_journalentry_pkey", "accounting_entry_number_uniq"} or str(
        exc
    ) in {
        "UNIQUE constraint failed: accounting_journalentry.id",
        "UNIQUE constraint failed: accounting_journalentry.company_id, "
        "accounting_journalentry.number",
    }


@business_atomic
def create_journal_entry(context: BusinessContext, *, journal_id, entry_date=None, memo=""):
    company = _authorize(context, CREATE_ENTRIES)
    journal_id = _value("journal", domain.identity, journal_id)
    journal = _journals(context, {journal_id})[journal_id]
    currency = company.base_currency
    places = _value("currency", domain.precision, currency.decimal_places)
    if not isinstance(currency.code, str) or len(currency.code) != 3:
        raise ValidationError(
            {"currency": "Company base currency code must have three characters."}
        )
    date = _value(
        "entry_date",
        domain.business_date,
        company_local_date(context.company_id) if entry_date is None else entry_date,
    )
    memo = _value("memo", domain.text, memo)
    require_final_permission(context, CREATE_ENTRIES)
    for attempt in range(3):
        identity = uuid4()
        entry = JournalEntry(
            id=identity,
            number=f"JE-{identity.hex}",
            company_id=context.company_id,
            journal=journal,
            entry_date=date,
            memo=memo,
            base_currency_code_snapshot=currency.code,
            base_currency_precision_snapshot=places,
        )
        try:
            with business_atomic_context():
                entry._persist(_WRITE_TOKEN, creating=True)
        except IntegrityError as exc:
            if (
                not _collision(exc)
                or not JournalEntry.objects.filter(
                    Q(pk=identity) | Q(company_id=context.company_id, number=entry.number),
                ).exists()
            ):
                raise
            if attempt == 2:
                raise ValidationError(
                    "Could not allocate a unique journal entry identity."
                ) from exc
        else:
            break
    _audit(context, entry, "entry.created", number=entry.number)
    return entry


@business_atomic
def update_journal_entry(context: BusinessContext, entry_id, **changes):
    _authorize(context, UPDATE_ENTRIES)
    entry = _locked(context, JournalEntry, entry_id, "entry")
    _draft(entry)
    fields = ("journal_id", "entry_date", "memo")
    if changes.keys() - set(fields):
        raise ValidationError("Unsupported journal entry fields.")
    before = {f: getattr(entry, f) for f in fields}
    proposed_id = _value("journal", domain.identity, changes.get("journal_id", entry.journal_id))
    journals = _journals(
        context,
        {entry.journal_id, proposed_id},
        active_ids={proposed_id} if "journal_id" in changes else set(),
    )
    entry.journal = journals[proposed_id]
    if "entry_date" in changes:
        entry.entry_date = _value("entry_date", domain.business_date, changes["entry_date"])
    if "memo" in changes:
        entry.memo = _value("memo", domain.text, changes["memo"])
    changed = [f for f in fields if before[f] != getattr(entry, f)]
    require_final_permission(context, UPDATE_ENTRIES)
    if changed:
        entry._persist(_WRITE_TOKEN)
        _audit(context, entry, "entry.updated", operation="header", fields=changed)
    return entry


def _line(entry, line_id):
    identity = _value("line", domain.identity, line_id)
    try:
        return JournalEntryLine.objects.select_for_update().get(
            pk=identity,
            journal_entry_id=entry.pk,
            company_id=entry.company_id,
        )
    except JournalEntryLine.DoesNotExist as exc:
        raise ValidationError("Line is outside this entry/company or was removed.") from exc


def _line_data(context, entry, line, changes):
    account_id = _value("account", domain.identity, changes.get("account_id", line.account_id))
    party_id = changes.get("party_id", line.party_id)
    if party_id is not None:
        party_id = _value("party", domain.identity, party_id)
    account_ids = {account_id} | ({line.account_id} if line.account_id else set())
    party_ids = {i for i in (party_id, line.party_id) if i is not None}
    accounts, parties = _references(
        context,
        account_ids,
        party_ids,
        active_accounts={account_id},
        active_parties={party_id} if party_id else set(),
    )
    line.account = accounts[account_id]
    line.party = parties[party_id] if party_id else None
    for field in ("debit", "credit"):
        setattr(
            line,
            field,
            _value(
                field,
                domain.amount,
                changes.get(field, getattr(line, field)),
                places=entry.base_currency_precision_snapshot,
            ),
        )
    line.description = _value(
        "description", domain.text, changes.get("description", line.description)
    )
    line.clean()


@business_atomic
def add_journal_entry_line(
    context: BusinessContext, entry_id, *, account_id, debit, credit, party_id=None, description=""
):
    _authorize(context, UPDATE_ENTRIES)
    entry = _locked(context, JournalEntry, entry_id, "entry")
    _draft(entry)
    _journals(context, {entry.journal_id}, active_ids=set())
    largest = entry.lines.aggregate(value=Max("position"))["value"] or 0
    if largest >= domain.MAX_POSITION:
        raise ValidationError("Journal entry line position space is exhausted.")
    line = JournalEntryLine(
        company_id=context.company_id, journal_entry=entry, position=largest + 1, debit=0, credit=0
    )
    _line_data(
        context,
        entry,
        line,
        dict(
            account_id=account_id,
            party_id=party_id,
            description=description,
            debit=debit,
            credit=credit,
        ),
    )
    require_final_permission(context, UPDATE_ENTRIES)
    line._persist(_WRITE_TOKEN, creating=True)
    _audit(
        context,
        entry,
        "entry.updated",
        operation="line_added",
        line_id=str(line.pk),
        fields=["account_id", "party_id", "description", "debit", "credit", "position"],
    )
    return line


@business_atomic
def update_journal_entry_line(context: BusinessContext, entry_id, line_id, **changes):
    _authorize(context, UPDATE_ENTRIES)
    entry = _locked(context, JournalEntry, entry_id, "entry")
    _draft(entry)
    _journals(context, {entry.journal_id}, active_ids=set())
    line = _line(entry, line_id)
    fields = ("account_id", "party_id", "description", "debit", "credit")
    if changes.keys() - set(fields):
        raise ValidationError("Unsupported line fields; ownership/position are immutable.")
    before = {f: getattr(line, f) for f in fields}
    _line_data(context, entry, line, changes)
    changed = [f for f in fields if before[f] != getattr(line, f)]
    require_final_permission(context, UPDATE_ENTRIES)
    if changed:
        line._persist(_WRITE_TOKEN)
        _audit(
            context,
            entry,
            "entry.updated",
            operation="line_updated",
            line_id=str(line.pk),
            fields=changed,
        )
    return line


@business_atomic
def remove_journal_entry_line(context: BusinessContext, entry_id, line_id):
    _authorize(context, UPDATE_ENTRIES)
    entry = _locked(context, JournalEntry, entry_id, "entry")
    _draft(entry)
    _journals(context, {entry.journal_id}, active_ids=set())
    line = _line(entry, line_id)
    identity = str(line.pk)
    require_final_permission(context, UPDATE_ENTRIES)
    line._persist(_WRITE_TOKEN, remove=True)
    _audit(
        context, entry, "entry.updated", operation="line_removed", line_id=identity, fields=["line"]
    )


@business_atomic
def post_journal_entry(context: BusinessContext, entry_id):
    company = _authorize(context, POST_ENTRIES)
    entry = _locked(context, JournalEntry, entry_id, "entry")
    if entry.status == JournalEntry.Status.POSTED:
        require_final_permission(context, POST_ENTRIES)
        return entry
    _draft(entry)
    entry.journal = _journals(context, {entry.journal_id})[entry.journal_id]
    lines = list(entry.lines.select_for_update().order_by("position", "id"))
    accounts, parties = _references(
        context,
        {line.account_id for line in lines},
        {line.party_id for line in lines if line.party_id},
    )
    if len(lines) < 2:
        raise ValidationError("Posting requires at least two lines.")
    if company.base_currency.code != entry.base_currency_code_snapshot:
        raise ValidationError("Frozen entry currency does not match Company base currency.")
    entry.full_clean()
    for line in lines:
        line.journal_entry = entry
        line.account = accounts[line.account_id]
        line.party = parties[line.party_id] if line.party_id else None
        line.clean()
        line.full_clean()
    debit, credit = domain.totals((line.debit, line.credit) for line in lines)
    if debit <= 0 or debit != credit:
        raise ValidationError(
            "Journal entry must balance exactly with positive debit/credit totals."
        )
    require_final_permission(context, POST_ENTRIES)
    entry._post(_POST_TOKEN, timezone.now())
    _audit(context, entry, "entry.posted", number=entry.number, line_count=len(lines))
    return entry
