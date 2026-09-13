from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext

from django import template

register = template.Library()


def _decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


@register.filter
def currency_amount(value, decimal_places):
    number = _decimal(value)
    try:
        places = int(decimal_places)
    except (TypeError, ValueError):
        return ""
    if number is None or places < 0:
        return ""
    with localcontext() as context:
        context.prec = max(38, len(number.as_tuple().digits) + places + 1)
        quantized = number.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return f"{quantized:.{places}f}"


@register.filter
def unit_cost(value):
    number = _decimal(value)
    if number is None:
        return ""
    return f"{number:.4f}"
