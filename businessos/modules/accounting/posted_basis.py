"""Bounded owner certificate for ACC-INT-1, not a general journal report."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connections
from django.utils import timezone

from businessos.core.database import business_atomic, current_database_alias

from . import domain
from .manifest import VIEW_ENTRIES
from .models import JournalEntry
from .services import _authorize

POSTED_BASIS_VERSION = 1


@dataclass(frozen=True, slots=True)
class PostedLineV1:
    id: UUID
    company_id: UUID
    journal_entry_id: UUID
    position: int
    account_id: UUID
    account_type: str
    party_id: UUID | None
    description: str
    debit: Decimal
    credit: Decimal
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PostedJournalBasisV1:
    id: UUID
    company_id: UUID
    journal_id: UUID
    number: str
    entry_date: date
    memo: str
    currency_code: str
    precision: int
    status: str
    posted_at: datetime
    created_at: datetime
    updated_at: datetime
    debit: Decimal
    credit: Decimal
    lines: tuple[PostedLineV1, ...]


def posted_journal_basis(context, entry_id, *, lock=True):
    if not lock and not connections[current_database_alias()].in_atomic_block:
        raise ValidationError("Nonlocking basis requires an outer selected-alias transaction.")
    return _posted_journal_basis(context, entry_id, lock=lock)


@business_atomic
def _posted_journal_basis(context, entry_id, *, lock):
    _authorize(context, VIEW_ENTRIES)
    entries = JournalEntry.objects.filter(pk=entry_id, company_id=context.company_id)
    if lock:
        entries = entries.select_for_update()
    entry = entries.first()
    _authorize(context, VIEW_ENTRIES)
    if entry is None:
        raise PermissionDenied("Journal entry is unavailable.")
    if (
        entry.status != JournalEntry.Status.POSTED
        or entry.number != f"JE-{entry.pk.hex}"
        or entry.journal.company_id != context.company_id
        or entry.posted_at is None
    ):
        raise ValidationError("Posted journal header is incompatible.")
    rows = entry.lines.select_related("account", "party").order_by("position", "id")
    # Prove cardinality before bounded materialization, never validate a truncated subset.
    if rows.count() != 2:
        raise ValidationError("ACC-INT-1 requires exactly two complete journal lines.")
    lines = []
    for line in rows:
        if (
            line.company_id != context.company_id
            or line.account.company_id != context.company_id
            or (line.party_id and line.party.company_id != context.company_id)
        ):
            raise ValidationError("Posted line ownership is incompatible.")
        try:
            domain.sides(line.debit, line.credit, entry.base_currency_precision_snapshot)
            domain.position(line.position)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        for stamp in (line.created_at, line.updated_at):
            if stamp is None or timezone.is_naive(stamp):
                raise ValidationError("Posted line timestamp is incomplete.")
        lines.append(
            PostedLineV1(
                line.pk,
                line.company_id,
                line.journal_entry_id,
                line.position,
                line.account_id,
                line.account.type,
                line.party_id,
                line.description,
                line.debit,
                line.credit,
                line.created_at,
                line.updated_at,
            )
        )
    for stamp in (entry.posted_at, entry.created_at, entry.updated_at):
        if stamp is None or timezone.is_naive(stamp):
            raise ValidationError("Posted header timestamp is incomplete.")
    if not entry.created_at <= entry.updated_at == entry.posted_at:
        raise ValidationError("Posted header timestamp order is incompatible.")
    if any(
        not entry.created_at <= line.created_at <= line.updated_at <= entry.posted_at
        for line in lines
    ):
        raise ValidationError("Posted line timestamp order is incompatible.")
    debit, credit = domain.totals((line.debit, line.credit) for line in lines)
    if debit <= 0 or debit != credit:
        raise ValidationError("Posted journal is not balanced.")
    _authorize(context, VIEW_ENTRIES)
    return PostedJournalBasisV1(
        entry.pk,
        entry.company_id,
        entry.journal_id,
        entry.number,
        entry.entry_date,
        entry.memo,
        entry.base_currency_code_snapshot,
        entry.base_currency_precision_snapshot,
        entry.status,
        entry.posted_at,
        entry.created_at,
        entry.updated_at,
        debit,
        credit,
        tuple(lines),
    )
