"""Accounting-local exact value rules; no Django/ORM/HTTP dependencies."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, localcontext
from uuid import UUID

AMOUNT_LIMIT = Decimal("1e30")
MAX_POSITION = 2147483647


def precision(value):
    if type(value) is not int or not 0 <= value <= 8:
        raise ValueError("Currency precision must be an integer from zero to eight.")
    return value


def amount(value, places):
    precision(places)
    if isinstance(value, bool) or not isinstance(value, (Decimal, str, int)):
        raise ValueError("Use an exact Decimal, integer or numeric string, not float/bool.")
    try:
        number = Decimal(value.strip() if isinstance(value, str) else value)
    except (ValueError, InvalidOperation) as exc:
        raise ValueError("Enter a valid decimal amount.") from exc
    if not number.is_finite() or not 0 <= number < AMOUNT_LIMIT:
        raise ValueError("Amount must be finite, nonnegative and less than 10^30.")
    if number == 0:
        return Decimal(0)
    sign, digits, exponent = number.as_tuple()
    digits = list(digits)
    while exponent < 0 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    if exponent < -places:
        raise ValueError("Amount exceeds frozen currency precision; rounding is forbidden.")
    return Decimal((sign, tuple(digits), exponent))


def sides(debit, credit, places):
    debit, credit = amount(debit, places), amount(credit, places)
    if (debit > 0) == (credit > 0):
        raise ValueError(
            "Exactly one of debit and credit must be positive; the other must be zero."
        )
    return debit, credit


def totals(values):
    values = list(values)
    with localcontext() as ctx:
        ctx.prec = 38 + len(str(max(len(values), 1))) + 2
        return (
            sum((debit for debit, _ in values), Decimal(0)),
            sum((credit for _, credit in values), Decimal(0)),
        )


def net(debit, credit):
    with localcontext() as ctx:
        ctx.prec = max(len(debit.as_tuple().digits), len(credit.as_tuple().digits), 38) + 10
        return debit - credit


def text(value, *, maximum=None, uppercase=False, required=False, trim=False):
    if not isinstance(value, str):
        raise ValueError("Enter text; null is not supported.")
    if trim:
        value = value.strip()
    if uppercase:
        value = value.upper()
    if required and not value:
        raise ValueError("This value is required.")
    if maximum is not None and len(value) > maximum:
        raise ValueError(f"Use at most {maximum} characters after normalization.")
    return value


def identity(value):
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise ValueError("Enter a valid UUID.")
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError("Enter a valid UUID.") from exc


def business_date(value):
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Enter a canonical YYYY-MM-DD date.") from exc
        if parsed.isoformat() != value:
            raise ValueError("Enter a canonical YYYY-MM-DD date.")
        value = parsed
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ValueError("Enter a date, not a datetime.")
    return value


def position(value):
    if type(value) is not int or not 1 <= value <= MAX_POSITION:
        raise ValueError("Position must be an integer from 1 to 2,147,483,647.")
    return value


def display(value, places):
    precision(places)
    # Values have already been validated; derived totals may exceed one line's range.
    return format(value, f".{places}f")
