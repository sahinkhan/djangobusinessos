"""Exact result values; no ORM/HTTP or independent financial calculation."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError

from businessos.modules.accounting.domain import amount, identity


def value(field, function, raw, *args):
    try:
        return function(raw, *args)
    except ValueError as exc:
        raise ValidationError({field: str(exc)}) from exc


def source_amount(raw, precision):
    return value("amount", amount, raw, precision)


def uuid(field, raw):
    return value(field, identity, raw)


@dataclass(frozen=True, slots=True)
class PostingOutcomeV1:
    state: str
    source_id: UUID | None = None
    effect: str | None = None
    binding_id: UUID | None = None
    journal_entry_id: UUID | None = None
    entry_number: str | None = None
    amount: Decimal | None = None
    business_date: date | None = None
    currency_code: str | None = None
    precision: int | None = None
    posted_at: datetime | None = None
    created_at: datetime | None = None
    reason: str | None = None

    @classmethod
    def unavailable(cls, reason):
        if reason not in {
            "not_installed",
            "http_disabled",
            "forbidden",
            "incompatible",
            "incomplete",
            "stale",
        }:
            raise ValueError("Unsupported unavailable reason.")
        return cls("UNAVAILABLE", reason=reason)

    @property
    def formatted_amount(self):
        return None if self.amount is None else format(self.amount, f".{self.precision}f")
