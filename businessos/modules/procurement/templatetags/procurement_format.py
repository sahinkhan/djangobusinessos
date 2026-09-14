from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext

from django import template

register = template.Library()


@register.filter
def currency_amount(value, decimal_places):
    try:
        number = Decimal(str(value))
        places = int(decimal_places)
    except (InvalidOperation, TypeError, ValueError):
        return ""
    if places < 0:
        return ""
    with localcontext() as context:
        context.prec = max(38, len(number.as_tuple().digits) + places + 1)
        quantized = number.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return f"{quantized:.{places}f}"


@register.filter
def decimal_quantity(value):
    display = format(value or Decimal("0"), "f")
    return display.rstrip("0").rstrip(".") if "." in display else display
