"""Exact receipt values and canonical request inputs; no ORM or HTTP dependencies."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

AMOUNT_LIMIT = Decimal("1e30")


def currency_precision(value):
    if type(value) is not int or not 0 <= value <= 8:
        raise ValueError("Currency precision must be an integer from zero to eight.")
    return value


def receipt_amount(value, precision):
    currency_precision(precision)
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise ValueError("Use an exact Decimal, integer or numeric string.")
    try:
        number = Decimal(value.strip() if isinstance(value, str) else value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Enter a valid decimal amount.") from exc
    if not number.is_finite() or not 0 < number < AMOUNT_LIMIT:
        raise ValueError("Amount must be finite, positive and less than 10^30.")
    sign, digits, exponent = number.as_tuple()
    digits = list(digits)
    # Tuple normalization is exact even with 38 digits or a small ambient Decimal context.
    while exponent < 0 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    if exponent < -precision:
        raise ValueError(
            "Amount exceeds the currency's supported precision; rounding is forbidden."
        )
    return Decimal((sign, tuple(digits), exponent))


def format_amount(value, precision):
    return format(receipt_amount(value, precision), f".{precision}f")


def canonical_uuid(value):
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise ValueError("Enter a valid UUID.")
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError("Enter a valid UUID.") from exc


def canonical_date(value):
    if value is None:
        return None
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Enter a date as YYYY-MM-DD.") from exc
        if parsed.isoformat() != value:
            raise ValueError("Enter a date as YYYY-MM-DD.")
        value = parsed
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValueError("Enter a date, not a datetime.")
    return value


def normalized_text(value, *, maximum=None, required=False, uppercase=False, nullable=False):
    if value is None and not required:
        value = ""
    if not isinstance(value, str):
        raise ValueError("Enter text.")
    value = value.strip()
    if uppercase:
        value = value.upper()
    if required and not value:
        raise ValueError("This value is required.")
    if maximum is not None and len(value) > maximum:
        raise ValueError(f"Use at most {maximum} characters.")
    return value or (None if nullable else "")
