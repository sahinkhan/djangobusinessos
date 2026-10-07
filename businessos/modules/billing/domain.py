"""Exact invoice arithmetic; no ORM, HTTP, or settlement assumptions."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext

MAX_INPUT = Decimal("99999999999999.9999")
AGGREGATE_LIMIT = Decimal("1e30")


def decimal_input(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise ValueError("Use an exact Decimal, integer or numeric string.")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Enter a valid decimal number.") from exc
    if not number.is_finite():
        raise ValueError("A finite decimal is required.")
    if number.as_tuple().exponent < -4:
        raise ValueError("At most four decimal places are supported.")
    if number < (Decimal("0.0001") if positive else 0) or number > MAX_INPUT:
        raise ValueError("Value is outside the supported Decimal(18,4) range.")
    return number


def currency_precision(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 8:
        raise ValueError("Currency precision must be between zero and eight.")
    return value


def line_amount(quantity, unit_price):
    with localcontext() as context:
        context.prec = 50
        return decimal_input(quantity, positive=True) * decimal_input(unit_price)


def calculate_total(lines, decimal_places):
    """Sum exact line products, range-check, then round the document once."""
    currency_precision(decimal_places)
    with localcontext() as context:
        context.prec = 50
        raw = Decimal(0)
        for quantity, unit_price in lines:
            raw += line_amount(quantity, unit_price)
            if raw >= AGGREGATE_LIMIT:
                raise ValueError("Invoice total exceeds the supported aggregate range.")
        rounded = raw.quantize(Decimal(1).scaleb(-decimal_places), rounding=ROUND_HALF_UP)
        if not rounded.is_finite() or not 0 <= rounded < AGGREGATE_LIMIT:
            raise ValueError("Invoice total exceeds the supported aggregate range.")
        return rounded
