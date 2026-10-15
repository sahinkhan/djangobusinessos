"""Exact HR civil-midnight geometry from the very bytes used by ZoneInfo.

This module is framework neutral. It does not ask the database to interpret an
IANA name and does not infer transitions by sampling. RFC 9636 v2/v3/v4 records
and the POSIX footer provide the complete rule basis. Unsupported coverage is
an error, never permission to approximate a date or truncate a requested span.
"""

from __future__ import annotations

import calendar
import hashlib
import io
import re
import struct
import zoneinfo
from bisect import bisect_right
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from importlib import resources
from pathlib import Path

SECOND_US = 1_000_000
DAY_US = 86_400 * SECOND_US
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
EPOCH_ORDINAL = date(1970, 1, 1).toordinal()
MIN_US = (date.min.toordinal() - EPOCH_ORDINAL) * DAY_US
MAX_US = (date.max.toordinal() - EPOCH_ORDINAL + 1) * DAY_US


class UnsupportedCalendarBoundary(ValueError):
    """The exact requested civil geometry cannot be represented/certified."""


class ResourceBudgetExceeded(RuntimeError):
    """A rule-analysis resource budget expired; this does not imply no conflict."""


@dataclass(frozen=True)
class OffsetSegment:
    """Half-open UTC microsecond range with one exact integer-second offset."""

    utc_start_us: int
    utc_end_us: int
    offset_seconds: int


@dataclass(frozen=True)
class InvalidWallInterval:
    """Skipped/repeated local wall interval at one actual offset transition."""

    transition_us: int
    wall_start_us: int
    wall_end_us: int

    @property
    def first_midnight_us(self):
        return -(-self.wall_start_us // DAY_US) * DAY_US


@dataclass(frozen=True)
class CalendarBasis:
    zone: str
    tzif_sha256: str
    segments: tuple[OffsetSegment, ...]
    invalid_wall_intervals: tuple[InvalidWallInterval, ...]


def normalize_instant(value, field="datetime"):
    """Accept aware instants only; retain the exact UTC microsecond identity."""
    if not isinstance(value, datetime):
        raise ValueError(f"{field} must be an aware datetime.")
    try:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field} must be an aware datetime.")
        return value.astimezone(UTC)
    except (OverflowError, TypeError) as exc:
        raise UnsupportedCalendarBoundary(f"{field} is outside the UTC datetime domain.") from exc


def instant_us(value):
    delta = normalize_instant(value) - EPOCH
    return delta.days * DAY_US + delta.seconds * SECOND_US + delta.microseconds


def instant_from_us(value):
    try:
        return EPOCH + timedelta(microseconds=value)
    except (OverflowError, TypeError) as exc:
        raise UnsupportedCalendarBoundary("UTC instant is not representable.") from exc


def _wall_us(value):
    return (value.toordinal() - EPOCH_ORDINAL) * DAY_US


def _days_before_year(year):
    """Proleptic Gregorian arithmetic, including the footer's boundary halo."""
    prior = year - 1
    return 365 * prior + prior // 4 - prior // 100 + prior // 400


def _day_number(year, month=1, day=1):
    before = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
    ordinal = _days_before_year(year) + before[month - 1] + day
    if month > 2 and calendar.isleap(year):
        ordinal += 1
    return ordinal - EPOCH_ORDINAL


@dataclass(frozen=True)
class _Rule:
    kind: str
    values: tuple[int, ...]
    seconds: int = 7200
    basis: str = "w"

    def wall_seconds(self, year):
        if self.kind == "M":
            month, week, weekday = self.values
            first = _day_number(year, month)
            month_days = calendar.monthrange(2000 if calendar.isleap(year) else 2001, month)[1]
            day = 1 + (weekday - (first + 4) % 7) % 7 + (week - 1) * 7
            if day > month_days:
                day -= 7
            days = first + day - 1
        else:
            (number,) = self.values
            days = _day_number(year) + number
            if self.kind == "J":
                days -= 1
                if number >= 60 and calendar.isleap(year):
                    days += 1
        return days * 86400 + self.seconds

    def utc_seconds(self, year, standard_offset, prior_offset):
        basis_offset = {"w": prior_offset, "s": standard_offset, "u": 0}[self.basis]
        return self.wall_seconds(year) - basis_offset


@dataclass(frozen=True)
class _Tail:
    standard: int
    daylight: int | None = None
    start: _Rule | None = None
    end: _Rule | None = None

    @property
    def constant_offset(self):
        if self.daylight is None or self.daylight == self.standard:
            return self.standard
        # RFC 9636 section 3.3.1's perpetual negative-DST representation.
        if (
            self.daylight < self.standard
            and self.start == _Rule("N", (0,), 0)
            and self.end == _Rule("J", (365,), 86400 + self.daylight - self.standard)
        ):
            return self.daylight
        return None

    def events(self, first_year, last_year):
        if self.constant_offset is not None:
            return []
        result = []
        for year in range(first_year, last_year + 1):
            result.append(
                (self.start.utc_seconds(year, self.standard, self.standard), self.daylight)
            )
            result.append((self.end.utc_seconds(year, self.standard, self.daylight), self.standard))
        result.sort()
        if any(a[0] == b[0] for a, b in zip(result, result[1:], strict=False)):
            raise UnsupportedCalendarBoundary("Coincident POSIX transitions are unsupported.")
        return result


class _PosixParser:
    def __init__(self, text, version):
        self.text, self.position, self.version = text, 0, version

    def match(self, pattern):
        found = re.match(pattern, self.text[self.position :], flags=re.ASCII)
        if found is None:
            raise UnsupportedCalendarBoundary("Malformed or unsupported POSIX TZ footer.")
        self.position += found.end()
        return found.group()

    def name(self):
        return self.match(r"(?:[A-Za-z]{3,}|<[A-Za-z0-9+\-]{3,}>)")

    def clock(self, *, transition=False):
        token = self.match(r"[+-]?\d{1,3}(?::\d{1,2}(?::\d{1,2})?)?")
        parts = token.lstrip("+-").split(":")
        hours, minutes, seconds = (int(part) for part in (parts + ["0", "0"])[:3])
        maximum = 167 if transition and self.version >= 3 else 24
        if hours > maximum or minutes > 59 or seconds > 59:
            raise UnsupportedCalendarBoundary("POSIX time is outside the supported format.")
        if transition and self.version == 2 and token.startswith(("-", "+")):
            raise UnsupportedCalendarBoundary("Signed transition requires TZif v3 or v4.")
        return (-1 if token.startswith("-") else 1) * (hours * 3600 + minutes * 60 + seconds)

    def rule(self):
        token = self.match(r"(?:M\d{1,2}\.\d\.\d|J\d{1,3}|\d{1,3})")
        if token.startswith("M"):
            values = tuple(int(part) for part in token[1:].split("."))
            if not (1 <= values[0] <= 12 and 1 <= values[1] <= 5 and 0 <= values[2] <= 6):
                raise UnsupportedCalendarBoundary("Invalid POSIX month/week/day rule.")
            kind = "M"
        else:
            kind = "J" if token.startswith("J") else "N"
            values = (int(token[1:] if kind == "J" else token),)
            if not ((1 <= values[0] <= 365) if kind == "J" else (0 <= values[0] <= 365)):
                raise UnsupportedCalendarBoundary("Invalid POSIX ordinal rule.")
        seconds, basis = 7200, "w"
        if self.text[self.position :].startswith("/"):
            self.position += 1
            seconds = self.clock(transition=True)
            if self.text[self.position : 1 + self.position] in ("w", "s", "u", "g", "z"):
                basis = self.text[self.position]
                self.position += 1
                basis = "u" if basis in ("g", "z") else basis
        return _Rule(kind, values, seconds, basis)

    def parse(self):
        self.name()
        standard = -self.clock()
        if abs(standard) >= 86400:
            raise UnsupportedCalendarBoundary("Offset cannot be represented by Python datetime.")
        if self.position == len(self.text):
            return _Tail(standard)
        self.name()
        daylight = standard + 3600
        if not self.text[self.position :].startswith(","):
            daylight = -self.clock()
        if abs(daylight) >= 86400:
            raise UnsupportedCalendarBoundary("Offset cannot be represented by Python datetime.")
        self.match(",")
        start = self.rule()
        self.match(",")
        end = self.rule()
        if self.position != len(self.text):
            raise UnsupportedCalendarBoundary("Unconsumed POSIX TZ footer content.")
        return _Tail(standard, daylight, start, end)


def _header(data, position):
    if len(data) < position + 44 or data[position : position + 4] != b"TZif":
        raise UnsupportedCalendarBoundary("Missing or truncated TZif header.")
    version = data[position + 4 : position + 5]
    if version not in (b"2", b"3", b"4"):
        raise UnsupportedCalendarBoundary("Only reviewed TZif v2/v3/v4 is supported.")
    counts = struct.unpack_from(">6I", data, position + 20)
    isut, isstd, _, _, types, characters = counts
    if not (1 <= types <= 256 and characters and isut in (0, types) and isstd in (0, types)):
        raise UnsupportedCalendarBoundary("Invalid TZif counts.")
    return int(version), counts


def _block_size(counts, width):
    isut, isstd, leaps, times, types, chars = counts
    return times * (width + 1) + types * 6 + chars + leaps * (width + 4) + isstd + isut


def _verify_tail(native, tail, transitions, offsets):
    """Certify footer interpretation at rule boundaries over a Gregorian cycle.

    POSIX Gregorian rules repeat every 400 years. Checking both sides of every
    generated nonzero-offset transition establishes native/parser parity for
    that finite rule basis; it is not coarse time sampling. Some valid POSIX
    forms are interpreted differently by particular ZoneInfo versions. Such a
    source is explicitly unsupported rather than silently adopting either set
    of civil dates.
    """
    if tail is None:
        return
    last = transitions[-1] if transitions else None
    if last is not None and last * SECOND_US >= MAX_US - 1:
        return  # footer is outside the entire requested datetime domain
    if last is not None and MIN_US <= last * SECOND_US < MAX_US:
        year = instant_from_us(last * SECOND_US).year
        constant = tail.constant_offset
        if constant is None:
            prior = [event for event in tail.events(year - 2, year + 2) if event[0] <= last]
            constant = prior[-1][1]
        if constant != offsets[-1]:
            raise UnsupportedCalendarBoundary("TZif footer contradicts the final transition.")
        first_year = max(2000, (year // 400 + 1) * 400)
        if first_year > 9600:
            first_year = year + 1
    else:
        first_year = 2000
    if first_year > 9999:
        return
    if tail.constant_offset is not None:
        probes = [(instant_us(datetime(first_year, 1, 2, tzinfo=UTC)), tail.constant_offset)]
    else:
        events = tail.events(first_year - 1, min(first_year + 400, 9999))
        probes = []
        for (previous_point, previous_offset), (point, offset) in zip(
            events, events[1:], strict=False
        ):
            if previous_point < point and previous_offset != offset:
                probes.extend(
                    ((point * SECOND_US - 1, previous_offset), (point * SECOND_US, offset))
                )
    for point, offset in probes:
        if MIN_US <= point < MAX_US and (last is None or point > last * SECOND_US):
            try:
                actual = instant_from_us(point).astimezone(native).utcoffset()
            except (OverflowError, ValueError) as exc:
                raise UnsupportedCalendarBoundary(
                    "Native POSIX boundary is unrepresentable."
                ) from exc
            if actual != timedelta(seconds=offset):
                raise UnsupportedCalendarBoundary("POSIX footer/ZoneInfo boundary parity mismatch.")


@dataclass(frozen=True)
class _Rules:
    zone: str
    digest: str
    native: zoneinfo.ZoneInfo
    transitions: tuple[int, ...]
    offsets: tuple[int | None, ...]
    initial_offset: int | None
    tail: _Tail | None

    def events(self, start_us, end_us):
        start = start_us // SECOND_US
        end = -(-end_us // SECOND_US)
        # Two years is a proven halo for the format's <=167:59:59 rule times
        # and <24-hour representable offsets, not an input duration bound.
        first_year = instant_from_us(max(MIN_US, start_us)).year - 2
        last_year = instant_from_us(min(MAX_US - 1, end_us - 1)).year + 2
        explicit = list(zip(self.transitions, self.offsets, strict=True))
        if self.transitions and self.tail is None and end > self.transitions[-1]:
            raise UnsupportedCalendarBoundary("TZif footer does not certify the requested future.")
        if self.tail is None:
            events, initial = explicit, self.initial_offset
        elif self.transitions:
            last = self.transitions[-1]
            events = explicit + [
                item for item in self.tail.events(first_year, last_year) if item[0] > last
            ]
            initial = self.initial_offset
            constant = self.tail.constant_offset
            if constant is not None:
                if constant != self.offsets[-1]:
                    raise UnsupportedCalendarBoundary("TZif footer contradicts the final record.")
            elif start > last:
                # If the last explicit record is far behind the requested year,
                # the generated halo supplies the prior state, not that old value.
                before = [event for event in events if event[0] <= start]
                if before:
                    initial = before[-1][1]
                events = [event for event in events if event[0] > start]
        else:
            constant = self.tail.constant_offset
            if constant is not None:
                events, initial = [], constant
            else:
                events = self.tail.events(first_year, last_year)
                before = [event for event in events if event[0] <= start]
                if not before:
                    raise UnsupportedCalendarBoundary("POSIX rule halo does not cover the request.")
                initial = before[-1][1]
                events = [event for event in events if event[0] > start]
        if any(a[0] >= b[0] for a, b in zip(events, events[1:], strict=False)):
            raise UnsupportedCalendarBoundary("Non-increasing transition rule basis.")
        times = [event[0] for event in events]
        index = bisect_right(times, start)
        if index:
            initial = events[index - 1][1]
        selected = [event for event in events[index:] if event[0] * SECOND_US < end_us]
        if initial is None or any(offset is None for _, offset in selected):
            raise UnsupportedCalendarBoundary("TZif has unspecified local-time coverage.")
        return initial, selected


@lru_cache(maxsize=64)
def _parse_rules(key, data):
    if len(data) > 4 * 1024 * 1024:
        raise ResourceBudgetExceeded("TZif byte materialization budget exceeded.")
    version, first = _header(data, 0)
    second_header = 44 + _block_size(first, 4)
    second_version, counts = _header(data, second_header)
    if second_version != version:
        raise UnsupportedCalendarBoundary("Inconsistent TZif versions.")
    isut, isstd, leaps, times, types, chars = counts
    position = second_header + 44
    end = position + _block_size(counts, 8)
    if end > len(data) or leaps:
        raise UnsupportedCalendarBoundary("Truncated or leap-second TZif is unsupported.")
    transitions = struct.unpack_from(f">{times}q", data, position)
    position += times * 8
    indexes = data[position : position + times]
    position += times
    type_records = [struct.unpack_from(">iBB", data, position + i * 6) for i in range(types)]
    position += types * 6
    designations = data[position : position + chars]
    position += chars
    standard_flags = data[position : position + isstd] if isstd else bytes(types)
    position += isstd
    utc_flags = data[position : position + isut] if isut else bytes(types)
    if any(flag not in (0, 1) for flag in standard_flags + utc_flags) or any(
        utc and not standard for utc, standard in zip(utc_flags, standard_flags, strict=True)
    ):
        raise UnsupportedCalendarBoundary("Invalid TZif time-basis indicators.")
    offsets = []
    for offset, dst, designation in type_records:
        if dst not in (0, 1) or abs(offset) >= 86400 or designation >= chars:
            raise UnsupportedCalendarBoundary("Unsupported TZif local-time type.")
        nul = designations.find(b"\0", designation)
        if nul < 0:
            raise UnsupportedCalendarBoundary("Unterminated TZif designation.")
        offsets.append(None if designations[designation:nul] == b"-00" else offset)
    if any(index >= types for index in indexes) or any(
        a >= b for a, b in zip(transitions, transitions[1:], strict=False)
    ):
        raise UnsupportedCalendarBoundary("Invalid TZif transition records.")
    footer_bytes = data[end:]
    if not footer_bytes.startswith(b"\n") or not footer_bytes.endswith(b"\n"):
        raise UnsupportedCalendarBoundary("Missing TZif footer framing.")
    try:
        footer = footer_bytes[1:-1].decode("ascii")
        tail = _PosixParser(footer, version).parse() if footer else None
        native = zoneinfo.ZoneInfo.from_file(io.BytesIO(data), key=key)
    except (UnicodeError, ValueError) as exc:
        raise UnsupportedCalendarBoundary("Unverified TZif/ZoneInfo rule interpretation.") from exc
    selected_offsets = tuple(offsets[index] for index in indexes)
    _verify_tail(native, tail, transitions, selected_offsets)
    return _Rules(
        key,
        hashlib.sha256(data).hexdigest(),
        native,
        transitions,
        selected_offsets,
        offsets[0],
        tail,
    )


def _read_zone_bytes(key):
    if (
        not isinstance(key, str)
        or not key
        or re.fullmatch(r"[A-Za-z0-9_+\-]+(?:/[A-Za-z0-9_+\-]+)*", key, flags=re.ASCII) is None
    ):
        raise UnsupportedCalendarBoundary("Invalid IANA zone identity.")
    for root in zoneinfo.TZPATH:
        candidate = Path(root).joinpath(*key.split("/"))
        if candidate.is_file():
            try:
                with candidate.open("rb") as stream:
                    return stream.read(4 * 1024 * 1024 + 1)
            except OSError as exc:
                raise UnsupportedCalendarBoundary("Configured TZif source is unreadable.") from exc
    try:
        return resources.files("tzdata.zoneinfo").joinpath(*key.split("/")).read_bytes()
    except (ModuleNotFoundError, FileNotFoundError, OSError) as exc:
        raise UnsupportedCalendarBoundary("IANA zone source is unavailable.") from exc


def _load_rules(key):
    return _parse_rules(key, _read_zone_bytes(key))


def _compile(rules, start_us, end_us, *, boundary_halo=False):
    if not MIN_US <= start_us < end_us <= MAX_US:
        raise UnsupportedCalendarBoundary("Invalid or unrepresentable UTC analysis range.")
    offset, events = rules.events(start_us, end_us)
    segments, invalid = [], []
    cursor = start_us
    for seconds, new_offset in events:
        point = seconds * SECOND_US
        segments.append(OffsetSegment(cursor, point, offset))
        if offset != new_offset:
            a, b = point + offset * SECOND_US, point + new_offset * SECOND_US
            invalid.append(InvalidWallInterval(point, min(a, b), max(a, b)))
        cursor, offset = point, new_offset
    segments.append(OffsetSegment(cursor, end_us, offset))
    # These checks are at every actual rule-segment boundary, not sampled
    # transition discovery. Native and compiled interpretations must agree.
    for segment in segments:
        for point in (segment.utc_start_us, segment.utc_end_us - 1):
            local_point = point + segment.offset_seconds * SECOND_US
            if boundary_halo and not MIN_US <= local_point < MAX_US:
                # The transition-analysis halo may cross year 1/10000. Its
                # integer wall arithmetic is valid, but is not a requested
                # application instant and cannot be passed to datetime.
                continue
            try:
                local = instant_from_us(point).astimezone(rules.native)
                actual = local.utcoffset()
                if actual != timedelta(seconds=segment.offset_seconds):
                    raise UnsupportedCalendarBoundary("TZif/ZoneInfo offset parity mismatch.")
            except (OverflowError, ValueError) as exc:
                raise UnsupportedCalendarBoundary("Local conversion is not representable.") from exc
    return CalendarBasis(rules.zone, rules.digest, tuple(segments), tuple(invalid))


def calendar_basis(start, end, zone):
    """Compile SQL proof parameters: exact segments plus a civil-boundary halo.

    A selected interval can start *after* its first date's invalid midnight.
    Therefore invalid wall intervals must include the proven two-day halo,
    even though segment coverage itself remains exactly [start,end).
    """
    rules = _load_rules(zone)
    first, last = instant_us(start), instant_us(end)
    exact = _compile(rules, first, last)
    halo = _compile(
        rules, max(MIN_US, first - 2 * DAY_US), min(MAX_US, last + 2 * DAY_US), boundary_halo=True
    )
    return CalendarBasis(zone, rules.digest, exact.segments, halo.invalid_wall_intervals)


def offset_segments(start, end, zone):
    return calendar_basis(start, end, zone).segments


def invalid_wall_intervals(start, end, zone):
    return calendar_basis(start, end, zone).invalid_wall_intervals


def _midnight(rules, value):
    wall = datetime.combine(value, datetime.min.time())
    candidates = set()
    for fold in (0, 1):
        try:
            aware = wall.replace(tzinfo=rules.native, fold=fold)
            candidate = aware.astimezone(UTC)
            if candidate.astimezone(rules.native).replace(tzinfo=None) == wall:
                candidates.add(candidate)
        except (OverflowError, ValueError) as exc:
            raise UnsupportedCalendarBoundary("Civil midnight is not representable.") from exc
    if len(candidates) != 1:
        raise UnsupportedCalendarBoundary("Civil midnight is ambiguous or nonexistent.")
    return candidates.pop()


def _certify_dates(rules, first, last):
    try:
        exclusive = last + timedelta(days=1)
    except OverflowError as exc:
        raise UnsupportedCalendarBoundary(
            "Exclusive civil-date boundary is unrepresentable."
        ) from exc
    start, end = _midnight(rules, first), _midnight(rules, exclusive)
    if start >= end:
        raise UnsupportedCalendarBoundary("Civil date boundaries are not strictly increasing.")
    # Include transitions just outside the UTC endpoint window: their wall gap
    # or fold can still contain an endpoint midnight. No per-date iteration.
    low = max(MIN_US, instant_us(start) - 2 * DAY_US)
    high = min(MAX_US, instant_us(end) + 2 * DAY_US)
    basis = _compile(rules, low, high, boundary_halo=True)
    first_wall, last_wall = _wall_us(first), _wall_us(exclusive)
    for invalid in basis.invalid_wall_intervals:
        midnight = max(invalid.first_midnight_us, first_wall)
        if midnight <= last_wall and midnight < invalid.wall_end_us:
            raise UnsupportedCalendarBoundary(
                "Requested dates contain a skipped/repeated midnight."
            )
    return start, end


def occupied_dates(start, end, zone):
    """Certified inclusive civil dates occupied by the half-open UTC interval."""
    start, end = normalize_instant(start, "start_at"), normalize_instant(end, "end_at")
    if start >= end:
        raise ValueError("start_at must precede end_at.")
    rules = _load_rules(zone)
    try:
        first = start.astimezone(rules.native).date()
        last = (end - timedelta(microseconds=1)).astimezone(rules.native).date()
    except (OverflowError, ValueError) as exc:
        raise UnsupportedCalendarBoundary("Occupied dates cannot be represented.") from exc
    if first > last:
        raise UnsupportedCalendarBoundary("Local date-line retreat is unsupported.")
    _certify_dates(rules, first, last)
    return first, last


def leave_window(start_date, end_date, zone):
    """One certified UTC window for inclusive full-calendar-day leave."""
    if (
        not isinstance(start_date, date)
        or isinstance(start_date, datetime)
        or not isinstance(end_date, date)
        or isinstance(end_date, datetime)
        or start_date > end_date
    ):
        raise ValueError("Leave dates must be ordered date values.")
    return _certify_dates(_load_rules(zone), start_date, end_date)
