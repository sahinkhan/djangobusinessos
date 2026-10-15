"""Small, framework-neutral HR input rules; no persistence or authorization."""

import re
from datetime import date
from uuid import UUID

MAX_REVISION = 2_147_483_647
MATERIALIZATION_LIMIT = 1_000
CODE = re.compile(r"[A-Z0-9][A-Z0-9_-]{0,31}\Z", re.ASCII)


def identity(value):
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        raise ValueError("Use a UUID identity.")
    result = UUID(value)
    if str(result) != value.lower():
        raise ValueError("Use a canonical UUID identity.")
    return result


def text(value, *, maximum=2000, required=False):
    if not isinstance(value, str):
        raise ValueError("Use text, not null or another type.")
    result = value.strip()
    if len(result) > maximum or (required and not result):
        raise ValueError(f"Use {'1' if required else '0'}..{maximum} characters.")
    return result


def code(value):
    original = text(value, maximum=32, required=True)
    result = original.upper()
    if not original.isascii() or not CODE.fullmatch(result):
        raise ValueError("Use an ASCII letter/digit followed by letters, digits, _ or -.")
    return result


def calendar_date(value):
    if type(value) is not date:
        raise ValueError("Use an actual calendar date, not a datetime or string.")
    return value


def revision(value, *, allow_zero=False):
    lower = 0 if allow_zero else 1
    if type(value) is not int or not lower <= value <= MAX_REVISION:
        raise ValueError(f"Use an integer revision in {lower}..{MAX_REVISION}.")
    return value


def next_revision(value):
    return revision(revision(value) + 1)


def boolean(value):
    if type(value) is not bool:
        raise ValueError("Use an actual boolean.")
    return value
