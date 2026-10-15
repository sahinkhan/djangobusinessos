"""Independent arithmetic and same-byte ZoneInfo oracles for HR civil dates."""

import io
import struct
from datetime import UTC, date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from businessos.modules.hr import civil_time as civil


def _tzif(
    footer="UTC0",
    *,
    transitions=(),
    records=((0, 0, 0),),
    names=b"UTC\0",
    version=3,
    standard_flags=b"",
    utc_flags=b"",
):
    def header(count):
        return (
            b"TZif"
            + str(version).encode()
            + bytes(15)
            + struct.pack(
                ">6I", len(utc_flags), len(standard_flags), 0, count, len(records), len(names)
            )
        )

    def block(width):
        code = "q" if width == 8 else "i"
        return (
            b"".join(struct.pack(">" + code, point) for point, _ in transitions)
            + bytes(index for _, index in transitions)
            + b"".join(struct.pack(">iBB", *record) for record in records)
            + names
            + standard_flags
            + utc_flags
        )

    return (
        header(len(transitions))
        + block(4)
        + header(len(transitions))
        + block(8)
        + ("\n" + footer + "\n").encode()
    )


def _install(monkeypatch, raw):
    monkeypatch.setattr(civil, "_read_zone_bytes", lambda key: raw)
    return ZoneInfo.from_file(io.BytesIO(raw), key="Synthetic/Review")


def _utc(year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0):
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=UTC)


@pytest.mark.parametrize("fold,hour", [(0, 5), (1, 6)])
def test_fold_api_instants_preserve_exact_utc_microseconds(fold, hour):
    local = datetime(2026, 11, 1, 1, 30, 45, 123456, tzinfo=ZoneInfo("America/New_York"), fold=fold)
    assert civil.normalize_instant(local) == _utc(2026, 11, 1, hour, 30, 45, 123456)


@pytest.mark.parametrize("value", [None, "2026-01-01", date(2026, 1, 1), datetime(2026, 1, 1)])
def test_only_aware_datetime_inputs(value):
    with pytest.raises(ValueError):
        civil.normalize_instant(value)


def test_utc_normalization_boundary_overflow_is_explicit():
    with pytest.raises(civil.UnsupportedCalendarBoundary):
        civil.normalize_instant(datetime(1, 1, 1, tzinfo=timezone(timedelta(hours=1))))


def test_integer_microseconds_do_not_round_large_or_negative_instants():
    for instant in (
        _utc(1, 1, 2, microsecond=1),
        _utc(1969, 12, 31, 23, 59, 59, 999999),
        _utc(9999, 12, 30, 23, 59, 59, 999999),
    ):
        assert civil.instant_from_us(civil.instant_us(instant)) == instant


@pytest.mark.parametrize("days", [365, 366, 367, 1461, 10000])
def test_leave_has_no_span_ceiling(days):
    first = date(2026, 1, 1)
    last = first + timedelta(days=days - 1)
    start, end = civil.leave_window(first, last, "America/New_York")
    assert start.astimezone(ZoneInfo("America/New_York")).date() == first
    assert end.astimezone(ZoneInfo("America/New_York")).date() == last + timedelta(days=1)
    assert (last - first).days + 1 == days


def test_full_representable_span_is_transition_driven_not_date_iteration(monkeypatch):
    original = civil._Rule.wall_seconds
    calls = []

    def counted(self, year):
        calls.append(year)
        return original(self, year)

    monkeypatch.setattr(civil._Rule, "wall_seconds", counted)
    start, end = civil.leave_window(date(1, 1, 2), date(9999, 12, 29), "America/New_York")
    assert start.year == 1 and end.year == 9999
    assert len(calls) < 23000  # annual transitions + one parity cycle, not 3.65 million dates


def test_utc_entire_native_date_domain_except_unrepresentable_exclusive_maximum():
    start, end = civil.leave_window(date.min, date(9999, 12, 30), "UTC")
    assert start == _utc(1) and end == _utc(9999, 12, 31)
    with pytest.raises(civil.UnsupportedCalendarBoundary, match="exclusive|Exclusive"):
        civil.leave_window(date(9999, 12, 31), date.max, "UTC")


def test_fall_back_day_is_25_hours_and_spring_day_is_23_hours():
    start, end = civil.leave_window(date(2026, 11, 1), date(2026, 11, 1), "America/New_York")
    assert end - start == timedelta(hours=25)
    start, end = civil.leave_window(date(2026, 3, 8), date(2026, 3, 8), "America/New_York")
    assert end - start == timedelta(hours=23)


def test_half_open_occupancy_microseconds_cross_midnight_long_and_adjacent():
    assert civil.occupied_dates(_utc(2026, 1, 1), _utc(2026, 1, 2), "UTC") == (
        date(2026, 1, 1),
        date(2026, 1, 1),
    )
    assert civil.occupied_dates(_utc(2026, 1, 1), _utc(2026, 1, 2, microsecond=1), "UTC") == (
        date(2026, 1, 1),
        date(2026, 1, 2),
    )
    assert civil.occupied_dates(_utc(2026, 1, 1), _utc(2026, 1, 5), "UTC") == (
        date(2026, 1, 1),
        date(2026, 1, 4),
    )


@pytest.mark.parametrize(
    "zone,first,last",
    [
        ("Pacific/Apia", date(2011, 12, 28), date(2012, 1, 2)),
        ("America/Havana", date(2026, 11, 1), date(2026, 11, 1)),
        ("America/Santiago", date(2026, 9, 6), date(2026, 9, 6)),
    ],
)
def test_skipped_dates_and_midnight_fold_gap_reject_even_inside_range(zone, first, last):
    with pytest.raises(civil.UnsupportedCalendarBoundary):
        civil.leave_window(first, last, zone)


def test_ordinary_two_am_fold_does_not_reject_midnight_geometry():
    assert civil.occupied_dates(_utc(2026, 11, 1, 5), _utc(2026, 11, 1, 8), "America/New_York") == (
        date(2026, 11, 1),
        date(2026, 11, 1),
    )


def test_interval_after_a_midnight_gap_still_rejects_the_dates_geometry():
    # This session itself is after Santiago's gap. Its first date nevertheless
    # has an unsupported midnight; chain SQL must receive that halo evidence.
    start, end = _utc(2026, 9, 6, 12), _utc(2026, 9, 6, 13)
    with pytest.raises(civil.UnsupportedCalendarBoundary):
        civil.occupied_dates(start, end, "America/Santiago")
    basis = civil.calendar_basis(start, end, "America/Santiago")
    assert basis.segments[0].utc_start_us == civil.instant_us(start)
    assert basis.segments[-1].utc_end_us == civil.instant_us(end)
    assert any(
        invalid.transition_us < civil.instant_us(start)
        and invalid.first_midnight_us < invalid.wall_end_us
        for invalid in basis.invalid_wall_intervals
    )


@pytest.mark.parametrize("zone", ["America/New_York", "Europe/London", "Australia/Sydney", "UTC"])
@pytest.mark.parametrize("year", [1900, 2026, 2050, 2400, 9998])
def test_segments_cover_range_exactly_and_match_native_each_transition_boundary(zone, year):
    start, end = _utc(year, 1, 2), _utc(year, 12, 29)
    basis = civil.calendar_basis(start, end, zone)
    assert len(basis.tzif_sha256) == 64
    assert basis.segments[0].utc_start_us == civil.instant_us(start)
    assert basis.segments[-1].utc_end_us == civil.instant_us(end)
    for left, right in zip(basis.segments, basis.segments[1:], strict=False):
        assert left.utc_end_us == right.utc_start_us
    for segment in basis.segments:
        assert segment.utc_start_us < segment.utc_end_us
        for point in (segment.utc_start_us, segment.utc_end_us - 1):
            utc = civil.instant_from_us(point)
            native = utc.astimezone(ZoneInfo(zone))
            # Independent integer arithmetic; no float Unix timestamps.
            expected = native.replace(tzinfo=UTC) - utc
            assert expected == timedelta(seconds=segment.offset_seconds)


@pytest.mark.parametrize("version", [2, 3, 4])
def test_same_file_tzif_versions_and_fixed_tails(monkeypatch, version):
    raw = _tzif("<+0530>-5:30", version=version)
    native = _install(monkeypatch, raw)
    segment = civil.offset_segments(_utc(2050), _utc(2051), "Synthetic/Review")[0]
    assert segment.offset_seconds == 19800
    assert _utc(2050).astimezone(native).utcoffset() == timedelta(seconds=19800)


@pytest.mark.parametrize(
    "footer",
    [
        "AAA3BBB,M3.5.0/-2,M10.5.0/-1",
        "AAA3BBB,M3.5.0/26,M10.5.0/25",
        "AAA3BBB,J60/2,J300/2",
        "AAA3BBB,M10.1.0/2,M3.1.0/2",
        "XXX3EDT4,0/0,J365/23",
    ],
)
def test_posix_month_julian_ordinal_extended_negative_southern_and_all_year(monkeypatch, footer):
    native = _install(monkeypatch, _tzif(footer))
    basis = civil.calendar_basis(_utc(2400, 1, 2), _utc(2400, 12, 29), "Synthetic/Review")
    for segment in basis.segments:
        for point in (segment.utc_start_us, segment.utc_end_us - 1):
            assert civil.instant_from_us(point).astimezone(native).utcoffset() == timedelta(
                seconds=segment.offset_seconds
            )


@pytest.mark.parametrize(
    "suffix,expected", [("w", 10800), ("s", 10800), ("u", 0), ("g", 0), ("z", 0)]
)
def test_transition_time_bases_are_parsed_explicitly(suffix, expected):
    tail = civil._PosixParser(f"AAA3BBB,M3.5.0/2{suffix},M10.5.0/2{suffix}", 3).parse()
    point = tail.start.utc_seconds(2050, tail.standard, tail.standard)
    assert point - tail.start.wall_seconds(2050) == expected
    point = tail.end.utc_seconds(2050, tail.standard, tail.daylight)
    expected_end = 7200 if suffix == "w" else expected
    assert point - tail.end.wall_seconds(2050) == expected_end


def test_bare_ordinal_rule_is_zero_based_including_leap_day():
    rule = civil._PosixParser("AAA3BBB,59/2,300/2", 3).parse().start
    assert rule.wall_seconds(2400) == civil.instant_us(_utc(2400, 2, 29, 2)) // civil.SECOND_US
    assert rule.wall_seconds(2401) == civil.instant_us(_utc(2401, 3, 1, 2)) // civil.SECOND_US


def test_native_ordinal_footer_parity_mismatch_rejects_without_guessing(monkeypatch):
    # CPython 3.13's native ordinal interpretation differs from POSIX zero-based
    # arithmetic. Pin the actual supported-runtime failure, do not imitate it.
    _install(monkeypatch, _tzif("AAA3BBB,59/2,300/2"))
    with pytest.raises(civil.UnsupportedCalendarBoundary, match="parity"):
        civil.calendar_basis(_utc(2400, 1, 2), _utc(2400, 12, 29), "Synthetic/Review")


def test_explicit_records_keep_historical_second_offsets_and_transition_midnights(monkeypatch):
    point = 86400
    raw = _tzif("UTC0", transitions=((point, 1),), records=((123, 0, 0), (0, 0, 0)))
    _install(monkeypatch, raw)
    basis = civil.calendar_basis(_utc(1970), _utc(1970, 1, 3), "Synthetic/Review")
    assert [segment.offset_seconds for segment in basis.segments] == [123, 0]
    assert basis.invalid_wall_intervals[0].first_midnight_us == point * civil.SECOND_US
    with pytest.raises(civil.UnsupportedCalendarBoundary):
        civil.leave_window(date(1970, 1, 1), date(1970, 1, 2), "Synthetic/Review")


def test_empty_footer_cannot_falsely_certify_after_last_explicit_record(monkeypatch):
    _install(monkeypatch, _tzif("", transitions=((86400, 0),)))
    with pytest.raises(civil.UnsupportedCalendarBoundary, match="future"):
        civil.offset_segments(_utc(1970), _utc(2050), "Synthetic/Review")


def test_footer_must_match_final_explicit_offset(monkeypatch):
    raw = _tzif("AAA-1", transitions=((86400, 0),))
    _install(monkeypatch, raw)
    with pytest.raises(civil.UnsupportedCalendarBoundary, match="contradicts"):
        civil.calendar_basis(_utc(2026), _utc(2027), "Synthetic/Review")


def test_explicit_times_remain_utc_regardless_of_original_time_basis_flags(monkeypatch):
    raw = _tzif(
        "UTC0",
        transitions=((86400, 1),),
        records=((123, 0, 0), (0, 0, 0)),
        standard_flags=b"\x00\x01",
        utc_flags=b"\x00\x01",
    )
    _install(monkeypatch, raw)
    basis = civil.calendar_basis(_utc(1970), _utc(1970, 1, 3), "Synthetic/Review")
    assert basis.segments[0].utc_end_us == 86400 * civil.SECOND_US
    assert basis.segments[1].offset_seconds == 0


@pytest.mark.parametrize("standard,utc", [(b"\x00", b"\x01"), (b"\x02", b"\x00")])
def test_invalid_time_basis_flags_are_not_ignored(monkeypatch, standard, utc):
    monkeypatch.setattr(
        civil, "_read_zone_bytes", lambda key: _tzif(standard_flags=standard, utc_flags=utc)
    )
    with pytest.raises(civil.UnsupportedCalendarBoundary):
        civil.calendar_basis(_utc(2026), _utc(2027), "Synthetic/Review")


def test_leap_second_sources_are_explicitly_unsupported(monkeypatch):
    raw = bytearray(_tzif())
    # UTC placeholder first block is ten bytes, so second header begins54.
    struct.pack_into(">I", raw, 54 + 28, 1)
    monkeypatch.setattr(civil, "_read_zone_bytes", lambda key: bytes(raw))
    with pytest.raises(civil.UnsupportedCalendarBoundary):
        civil.calendar_basis(_utc(2026), _utc(2027), "Synthetic/Review")


def test_native_rejected_footer_basis_does_not_use_a_different_zone_source(monkeypatch):
    raw = _tzif("AAA3BBB,M3.5.0/2u,M10.5.0/2s")
    monkeypatch.setattr(civil, "_read_zone_bytes", lambda key: raw)
    with pytest.raises(civil.UnsupportedCalendarBoundary, match="interpretation"):
        civil.calendar_basis(_utc(2026), _utc(2027), "Synthetic/Review")


def test_rule_materialization_budget_is_not_a_duration_cap(monkeypatch):
    monkeypatch.setattr(civil, "_read_zone_bytes", lambda key: b"x" * (4 * 1024 * 1024 + 1))
    with pytest.raises(civil.ResourceBudgetExceeded):
        civil.calendar_basis(_utc(2026), _utc(2027), "Synthetic/Review")


@pytest.mark.parametrize(
    "raw",
    [
        b"TZif",
        _tzif()[:-1],
        _tzif().replace(b"TZif3", b"TZif1"),
        _tzif("AAA25"),
        _tzif("AAA0BBB,M13.1.0,M3.1.0"),
    ],
)
def test_malformed_unverified_format_fails_closed(monkeypatch, raw):
    monkeypatch.setattr(civil, "_read_zone_bytes", lambda key: raw)
    with pytest.raises(civil.UnsupportedCalendarBoundary):
        civil.leave_window(date(2026, 1, 1), date(2026, 1, 1), "Synthetic/Review")


@pytest.mark.parametrize(
    "key", ["../UTC", "/etc/passwd", "Asia/../UTC", "Asia\\Dhaka", "", "./UTC", "C:/UTC", "UTC\0"]
)
def test_zone_source_identity_rejects_noncanonical_paths(key):
    with pytest.raises(civil.UnsupportedCalendarBoundary):
        civil.leave_window(date(2026, 1, 1), date(2026, 1, 1), key)


def test_source_file_precedence_is_public_tzpath_and_same_bytes(monkeypatch, tmp_path):
    directory = tmp_path / "Synthetic"
    directory.mkdir()
    raw = _tzif("AAA-6")
    (directory / "Review").write_bytes(raw)
    monkeypatch.setattr(civil.zoneinfo, "TZPATH", (str(tmp_path),))
    basis = civil.calendar_basis(_utc(2026), _utc(2027), "Synthetic/Review")
    assert basis.segments == (
        civil.OffsetSegment(civil.instant_us(_utc(2026)), civil.instant_us(_utc(2027)), 21600),
    )


def test_reversed_intervals_and_dates_reject():
    with pytest.raises(ValueError):
        civil.occupied_dates(_utc(2026), _utc(2025), "UTC")
    with pytest.raises(ValueError):
        civil.leave_window(date(2026, 2, 1), date(2026, 1, 1), "UTC")
