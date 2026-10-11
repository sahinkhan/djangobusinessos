"""Exact, framework-neutral allocation inputs and immutable evidence results."""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from uuid import UUID

AMOUNT_LIMIT = Decimal("1e30")
CONTRACT_VERSION = 1
PAGE_SIZE = 50
UNAVAILABLE_REASONS = frozenset(
    {
        "not_installed",
        "http_disabled",
        "forbidden",
        "incompatible",
        "incomplete",
        "stale",
    }
)


def amount(value, precision):
    if type(precision) is not int or not 0 <= precision <= 8:
        raise ValueError("Invalid frozen precision.")
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
        raise ValueError("Use an exact Decimal, integer or numeric string.")
    try:
        number = Decimal(value)
    except (ValueError, ArithmeticError) as exc:
        raise ValueError("Enter a valid decimal amount.") from exc
    if not number.is_finite() or not 0 < number < AMOUNT_LIMIT:
        raise ValueError("Amount must be positive, finite and less than 10^30.")
    sign, digits, exponent = number.as_tuple()
    digits = list(digits)
    while exponent < 0 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    if exponent < -precision:
        raise ValueError("Amount exceeds frozen precision; rounding is forbidden.")
    return Decimal((sign, tuple(digits), exponent))


def identity(value):
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise ValueError("Enter a UUID, not an object.")
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError("Enter a valid UUID.") from exc


def key(value):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > 128:
        raise ValueError("A nonblank text key of at most 128 characters is required.")
    return value.strip()


def subtract(left, right):
    with localcontext() as context:
        context.prec = max(60, len(left.as_tuple().digits), len(right.as_tuple().digits)) + 2
        return left - right


@dataclass(frozen=True, slots=True)
class AllocationEvidence:
    state: str
    reason: str | None = None
    applied: Decimal | None = None
    remaining: Decimal | None = None
    original: Decimal | None = None
    currency_code: str | None = None
    precision: int | None = None
    history: tuple | None = None
    count: int | None = None
    page: int | None = None
    pages: int | None = None

    @classmethod
    def unavailable(cls, reason):
        if reason not in UNAVAILABLE_REASONS:
            raise ValueError("Unsupported evidence reason.")
        return cls("UNAVAILABLE", reason=reason)

    @property
    def formatted_applied(self):
        return None if self.applied is None else format(self.applied, f".{self.precision}f")

    @property
    def formatted_remaining(self):
        return None if self.remaining is None else format(self.remaining, f".{self.precision}f")
