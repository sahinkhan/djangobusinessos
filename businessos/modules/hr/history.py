"""Private database-side certification of complete selected Attendance chains.

Only scalar summaries, violation existence and the latest revision leave SQL.
No history-count ceiling and no employee-wide Python history collection exists.
"""

from datetime import UTC, date, datetime

from django.core.exceptions import ValidationError
from django.db import connections

from businessos.core.database import current_database_alias

from .civil_time import DAY_US, EPOCH_ORDINAL, ResourceBudgetExceeded, calendar_basis, instant_us
from .domain import MAX_REVISION
from .models import Attendance, AttendanceRevision

# Exact Python str.strip whitespace set for accepted Python 3.13. Explicit data
# avoids backend/locale-dependent interpretations of a required nonblank reason.
_STRIP_WHITESPACE = (
    "\t\n\v\f\r\x1c\x1d\x1e\x1f \x85\xa0\u1680"
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    "\u2028\u2029\u202f\u205f\u3000"
)

# Fixed candidate migration identities, not expectations learned from the
# database being certified. No ordinary/non-public namespace is filtered out.
_SOURCE_TABLES = {
    "r": "hr_attendancerevision",
    "a": "hr_attendance",
    "e": "hr_employee",
    "u": "identity_user",
    "p": "party_party",
    "b": "organization_branch",
}


def _source_tables(connection):
    q = connection.ops.quote_name
    if connection.vendor != "postgresql":
        return {alias: q(name) for alias, name in _SOURCE_TABLES.items()}
    names = tuple(_SOURCE_TABLES.values())
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT n.nspname,c.relname,c.relkind,c.oid,c.relrowsecurity,c.relforcerowsecurity,"
            "EXISTS(SELECT 1 FROM pg_catalog.pg_policy p WHERE p.polrelid=c.oid) "
            "FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace "
            "WHERE c.relname=ANY(%s)",
            [list(names)],
        )
        rows = cursor.fetchall()
        if len(rows) != len(names) or any(
            namespace != "public" or name not in names or kind != "r" or rls or force or policies
            for namespace, name, kind, _, rls, force, policies in rows
        ):
            raise ValidationError("Unsupported Attendance source relation/namespace/RLS evidence.")
        actual = {name: oid for _, name, _, oid, _, _, _ in rows}
        if set(actual) != set(names):
            raise ValidationError("Missing or shadowed Attendance source relation.")
        qualified = ",".join(f"{q('public')}.{q(name)}" for name in sorted(names))
        cursor.execute(f"LOCK TABLE {qualified} IN ACCESS SHARE MODE NOWAIT")
        # Protect exact source identities/policy flags against DDL during the
        # certification, then recheck after admission (not check-then-lock).
        cursor.execute(
            "SELECT c.oid,c.relrowsecurity,c.relforcerowsecurity,"
            "EXISTS(SELECT 1 FROM pg_catalog.pg_policy p WHERE p.polrelid=c.oid) "
            "FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace "
            "WHERE n.nspname='public' AND c.relname=ANY(%s)",
            [list(names)],
        )
        locked_rows = cursor.fetchall()
        if {row[0] for row in locked_rows} != set(actual.values()) or any(
            rls or force or policies for _, rls, force, policies in locked_rows
        ):
            raise ValidationError(
                "Attendance source relation identity/policy changed during admission."
            )
        for name, oid in actual.items():
            cursor.execute("SELECT pg_catalog.to_regclass(%s)::oid", [name])
            if cursor.fetchone()[0] != oid:
                raise ValidationError("Attendance source search-path resolution is unsupported.")
    return {alias: f"{q('public')}.{q(name)}" for alias, name in _SOURCE_TABLES.items()}


def _sqlite_instant(value):
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return instant_us(parsed)


def _sqlite_ordinal(value):
    return None if value is None else date.fromisoformat(value).toordinal()


def certify_attendance(attendance):
    """Certify every retained revision before returning the private latest row.

    Caller owns Company/Employee and selected parent serialization. Historical
    activity is deliberately NOT renewed; existence, identities and facts are.
    """
    alias = current_database_alias()
    connection = connections[alias]
    if not connection.in_atomic_block or attendance._state.db != alias:
        raise ValidationError("Attendance certification requires its owning transaction/alias.")
    tables = _source_tables(connection)
    pk = Attendance._meta.pk.get_db_prep_value(attendance.pk, connection)
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*),COUNT(DISTINCT number),MIN(number),MAX(number),"
            f"MIN(start_at),MAX(end_at) FROM {tables['r']} WHERE attendance_id=%s",
            [pk],
        )
        count, distinct, first, last, minimum, maximum = cursor.fetchone()
    if not count or first != 1 or count != distinct or count != last or last > MAX_REVISION:
        raise ValidationError("The complete Attendance revision sequence is corrupt.")
    if isinstance(minimum, str):
        minimum, maximum = datetime.fromisoformat(minimum), datetime.fromisoformat(maximum)
    if minimum.tzinfo is None:
        minimum, maximum = minimum.replace(tzinfo=UTC), maximum.replace(tzinfo=UTC)
    try:
        basis = calendar_basis(minimum, maximum, attendance.timezone)
    except (ValueError, OverflowError) as exc:
        raise ValidationError("The retained Attendance timezone evidence is unsupported.") from exc
    if connection.vendor == "postgresql":

        def micros(column):
            return f"(EXTRACT(EPOCH FROM {column})*1000000)::bigint"

        def ordinal(column):
            return f"(({column}-DATE '1970-01-01')+{EPOCH_ORDINAL})"

        trim_function = "BTRIM"
    elif connection.vendor == "sqlite":
        connection.connection.create_function(
            "hr_instant_us", 1, _sqlite_instant, deterministic=True
        )
        connection.connection.create_function(
            "hr_date_ordinal", 1, _sqlite_ordinal, deterministic=True
        )

        def micros(column):
            return f"hr_instant_us({column})"

        def ordinal(column):
            return f"hr_date_ordinal({column})"

        trim_function = "TRIM"
    else:
        raise ValidationError("Unsupported Attendance certification backend.")
    parameters = []

    # SQLite must use integer arithmetic even at representable extreme years.
    # For signed integers, (x - ((x % d + d) % d))/d is exact floor division.
    def exact_derived_date(expression):
        pieces = []
        for segment in basis.segments:
            value = f"({expression}+{segment.offset_seconds * 1_000_000})"
            floor = f"(({value}-(({value}%%{DAY_US}+{DAY_US})%%{DAY_US}))/{DAY_US})"
            pieces.append(f"WHEN {expression}>=%s AND {expression}<%s THEN {floor}+{EPOCH_ORDINAL}")
            parameters.extend((segment.utc_start_us, segment.utc_end_us))
        return "(CASE " + " ".join(pieces) + " ELSE NULL END)"

    # Both engines use exact integer microsecond arithmetic; no float epoch.
    convert = exact_derived_date
    start_date = convert(micros("r.start_at"))
    end_date = convert(f"({micros('r.end_at')}-1)")
    bad_geometry = []
    for interval in basis.invalid_wall_intervals:
        first_midnight = interval.first_midnight_us
        if first_midnight < interval.wall_end_us:
            low = first_midnight // DAY_US + EPOCH_ORDINAL
            high = (interval.wall_end_us - 1) // DAY_US + EPOCH_ORDINAL
            bad_geometry.append(
                f"({ordinal('r.local_start_date')}<=%s AND ({ordinal('r.local_end_date')}+1)>=%s)"
            )
            parameters.extend((high, low))
    geometry = " OR ".join(bad_geometry) or "FALSE"
    # IS DISTINCT FROM is deliberately null-safe on PostgreSQL and supported SQLite.
    invalid = f"""
        r.company_id IS DISTINCT FROM a.company_id
        OR r.employee_id IS DISTINCT FROM a.employee_id
        OR e.company_id IS DISTINCT FROM a.company_id
        OR p.company_id IS DISTINCT FROM a.company_id
        OR a.company_id IS DISTINCT FROM %s OR a.employee_id IS DISTINCT FROM %s
        OR e.id IS NULL OR p.id IS NULL OR u.id IS NULL OR original_actor.id IS NULL
        OR (a.branch_id IS NOT NULL AND (
            b.id IS NULL OR b.company_id IS DISTINCT FROM a.company_id))
        OR r.number<1 OR r.number>{MAX_REVISION}
        OR r.expected_revision IS DISTINCT FROM r.number-1
        OR r.operation IS NULL OR r.operation NOT IN ('RECORD','CORRECT','VOID','REINSTATE')
        OR r.effect IS NULL OR r.effect NOT IN ('ACTIVE_INTERVAL','VOIDED')
        OR r.start_at IS NULL OR r.end_at IS NULL OR r.start_at>=r.end_at
        OR r.local_start_date IS NULL OR r.local_end_date IS NULL
        OR r.local_start_date>r.local_end_date
        OR r.created_at IS NULL OR r.updated_at IS NULL
        OR a.created_at IS NULL OR a.updated_at IS NULL
        OR r.reason IS NULL OR r.request_key IS NULL OR a.record_request_key IS NULL
        OR LENGTH(r.reason)>2000
        OR (r.number=1 AND (
            r.operation IS DISTINCT FROM 'RECORD' OR r.effect IS DISTINCT FROM 'ACTIVE_INTERVAL'
            OR r.actor_id IS DISTINCT FROM a.recorded_by_id
            OR r.request_key IS DISTINCT FROM a.record_request_key))
        OR (r.number>1 AND (
            previous.id IS NULL OR LENGTH({trim_function}(r.reason,%s))=0
            OR NOT (
                (r.operation='CORRECT' AND previous.effect='ACTIVE_INTERVAL'
                    AND r.effect='ACTIVE_INTERVAL'
                    AND (r.start_at IS DISTINCT FROM previous.start_at
                         OR r.end_at IS DISTINCT FROM previous.end_at))
                OR (r.operation='VOID' AND previous.effect='ACTIVE_INTERVAL' AND r.effect='VOIDED'
                    AND r.start_at IS NOT DISTINCT FROM previous.start_at
                    AND r.end_at IS NOT DISTINCT FROM previous.end_at
                    AND r.local_start_date IS NOT DISTINCT FROM previous.local_start_date
                    AND r.local_end_date IS NOT DISTINCT FROM previous.local_end_date)
                OR (r.operation='REINSTATE' AND previous.effect='VOIDED'
                    AND r.effect='ACTIVE_INTERVAL')
            )))
    """
    scope_parameters = [
        Attendance._meta.get_field("company").get_db_prep_value(attendance.company_id, connection),
        Attendance._meta.get_field("employee").get_db_prep_value(
            attendance.employee_id, connection
        ),
    ]
    sql = f"""
        SELECT 1 FROM {tables["r"]} r
        JOIN {tables["a"]} a ON a.id=r.attendance_id
        LEFT JOIN {tables["r"]} previous ON previous.attendance_id=r.attendance_id
            AND previous.number=r.number-1
        LEFT JOIN {tables["e"]} e ON e.id=a.employee_id
        LEFT JOIN {tables["p"]} p ON p.id=e.party_id
        LEFT JOIN {tables["u"]} u ON u.id=r.actor_id
        LEFT JOIN {tables["u"]} original_actor ON original_actor.id=a.recorded_by_id
        LEFT JOIN {tables["b"]} b ON b.id=a.branch_id
        WHERE r.attendance_id=%s AND (
            {ordinal("r.local_start_date")} IS DISTINCT FROM {start_date}
            OR {ordinal("r.local_end_date")} IS DISTINCT FROM {end_date}
            OR {geometry} OR {invalid}
        ) LIMIT 1
    """
    query_parameters = [pk, *parameters, *scope_parameters, _STRIP_WHITESPACE]
    if connection.vendor == "postgresql":
        parameter_limit = 65535  # PostgreSQL extended-query protocol's actual limit
    else:
        from sqlite3 import SQLITE_LIMIT_VARIABLE_NUMBER

        parameter_limit = connection.connection.getlimit(SQLITE_LIMIT_VARIABLE_NUMBER)
    if len(query_parameters) > parameter_limit:
        raise ResourceBudgetExceeded(
            "Attendance SQL rule parameters exceed the backend resource limit."
        )
    with connection.cursor() as cursor:
        cursor.execute(sql, query_parameters)
        if cursor.fetchone() is not None:
            raise ValidationError(
                "The complete Attendance history contains invalid retained facts."
            )
    return AttendanceRevision.objects.using(alias).get(attendance_id=attendance.pk, number=last)
