"""Real SQL complete-chain certification, not a latest/predecessor mock."""

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, models
from django.test.utils import CaptureQueriesContext

from businessos.core.database import business_atomic_context
from businessos.core.organization.models import Company
from businessos.modules.hr.civil_time import occupied_dates
from businessos.modules.hr.history import certify_attendance
from businessos.modules.hr.models import AttendanceRevision
from businessos.modules.hr.persistence import _create_attendance, _create_employee
from businessos.modules.party.models import Party

pytestmark = pytest.mark.django_db


@pytest.fixture
def history_parent(company, operator):
    company.timezone = "UTC"
    company.save(update_fields=["timezone"])
    party = Party.objects.create(
        company=company, party_type=Party.Type.PERSON, display_name="Synthetic HR"
    )
    with business_atomic_context():
        employee = _create_employee(
            company_id=company.pk,
            party_id=party.pk,
            employee_number="HISTORY-1",
            joining_date=date(1, 1, 1),
        )
        parent = _create_attendance(
            company_id=company.pk,
            employee_id=employee.pk,
            branch_id=None,
            timezone_name="UTC",
            record_request_key=uuid4(),
            recorded_by_id=operator.pk,
        )
    return parent


def _revision(parent, number, operation=None, *, start=None, end=None, **extra):
    """Raw synthetic insertion permits corruption services correctly refuse."""
    operation = operation or ("RECORD" if number == 1 else "CORRECT")
    start = start or datetime(2026, 1, 2, 9, tzinfo=UTC) + timedelta(minutes=number)
    end = end or start + timedelta(hours=1)
    first, last = occupied_dates(start, end, parent.timezone)
    values = dict(
        company_id=parent.company_id,
        employee_id=parent.employee_id,
        attendance_id=parent.pk,
        number=number,
        expected_revision=number - 1,
        operation=operation,
        effect="VOIDED" if operation == "VOID" else "ACTIVE_INTERVAL",
        start_at=start,
        end_at=end,
        local_start_date=first,
        local_end_date=last,
        reason="" if number == 1 else "Synthetic correction",
        actor_id=parent.recorded_by_id,
        request_key=parent.record_request_key if number == 1 else uuid4(),
    )
    values.update(extra)
    row = AttendanceRevision(**values)
    # This is deliberately a fixture-only base save, never an application path.
    models.Model.save_base(row, using=connection.alias, force_insert=True)
    return row


def _corrupt(row, **values):
    fields = {field.name: field for field in row._meta.concrete_fields}
    assignments, parameters = [], []
    for name, value in values.items():
        field = fields[name]
        assignments.append(f"{connection.ops.quote_name(field.column)}=%s")
        parameters.append(field.get_db_prep_save(value, connection))
    parameters.append(row._meta.pk.get_db_prep_value(row.pk, connection))
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {connection.ops.quote_name(row._meta.db_table)} "
            f"SET {','.join(assignments)} WHERE id=%s",
            parameters,
        )


def _certify(parent):
    with business_atomic_context():
        return certify_attendance(parent)


@pytest.mark.parametrize("ordinals", [[1], [1, 2], [1, 2, 3], [1, 2, 3, 4]])
def test_every_contiguous_legal_correct_chain_certifies(history_parent, ordinals):
    for number in ordinals:
        _revision(history_parent, number)
    assert _certify(history_parent).number == ordinals[-1]


@pytest.mark.parametrize("ordinals", [[], [3], [1, 3], [1, 3, 4], [1, 2, 4], [2, 3, 4]])
def test_gaps_and_missing_original_reject_even_with_a_valid_latest_pair(history_parent, ordinals):
    for number in ordinals:
        _revision(history_parent, number)
    with pytest.raises(ValidationError, match="sequence"):
        _certify(history_parent)


def test_record_void_reinstate_complete_chain_certifies(history_parent):
    original = _revision(history_parent, 1)
    _revision(history_parent, 2, "VOID", start=original.start_at, end=original.end_at)
    latest = _revision(history_parent, 3, "REINSTATE")
    assert _certify(history_parent).pk == latest.pk


def test_malformed_earlier_void_rejects_despite_valid_latest_reinstate(history_parent):
    _revision(history_parent, 1)
    _revision(history_parent, 2, "VOID")  # row CHECKs pass, predecessor equality does not
    _revision(history_parent, 3, "REINSTATE")
    with pytest.raises(ValidationError, match="retained facts"):
        _certify(history_parent)


@pytest.mark.parametrize("operation", ["VOID", "REINSTATE"])
def test_invalid_historical_transition_rejects(history_parent, operation):
    original = _revision(history_parent, 1)
    if operation == "VOID":
        _revision(history_parent, 2, "VOID", start=original.start_at, end=original.end_at)
        _revision(history_parent, 3, "VOID", start=original.start_at, end=original.end_at)
    else:
        _revision(history_parent, 2, "REINSTATE")
        _revision(history_parent, 3)
    with pytest.raises(ValidationError, match="retained facts"):
        _certify(history_parent)


def test_no_change_correct_is_not_an_effect(history_parent):
    original = _revision(history_parent, 1)
    _revision(history_parent, 2, "CORRECT", start=original.start_at, end=original.end_at)
    with pytest.raises(ValidationError, match="retained facts"):
        _certify(history_parent)


@pytest.mark.parametrize("reason", [" ", "\t\n", "\u2003\u3000", "\x85\xa0"])
def test_whitespace_only_earlier_reason_rejects(history_parent, reason):
    _revision(history_parent, 1)
    _revision(history_parent, 2, reason=reason)
    _revision(history_parent, 3)
    with pytest.raises(ValidationError, match="retained facts"):
        _certify(history_parent)


def test_incorrect_cached_earlier_date_is_not_hidden_by_later_valid_revisions(history_parent):
    original = _revision(history_parent, 1)
    _revision(history_parent, 2)
    _revision(history_parent, 3)
    _corrupt(original, local_start_date=date(2026, 1, 3), local_end_date=date(2026, 1, 3))
    with pytest.raises(ValidationError, match="retained facts"):
        _certify(history_parent)


def test_revision_scope_does_not_override_authoritative_parent(history_parent, company):
    other = Company.objects.create(
        code="OTHER-HR",
        name="Other synthetic Company",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    _revision(history_parent, 1, company_id=other.pk)
    _revision(history_parent, 2)
    with pytest.raises(ValidationError, match="retained facts"):
        _certify(history_parent)


def test_original_actor_and_request_are_intrinsic_history_identity(history_parent):
    another = get_user_model().objects.create_user("history2@example.test", "synthetic")
    row = _revision(history_parent, 1, actor_id=another.pk)
    with pytest.raises(ValidationError, match="retained facts"):
        _certify(history_parent)
    _corrupt(row, actor=history_parent.recorded_by_id, request_key=uuid4())
    with pytest.raises(ValidationError, match="retained facts"):
        _certify(history_parent)


def test_historical_activity_is_not_renewed(history_parent):
    original = _revision(history_parent, 1)
    user = get_user_model().objects.get(pk=history_parent.recorded_by_id)
    user.is_active = False
    user.save(update_fields=["is_active"])
    party = history_parent.employee.party
    party.is_active = False
    party.party_type = Party.Type.ORGANIZATION
    party.save(update_fields=["is_active", "party_type"])
    assert _certify(history_parent).pk == original.pk


@pytest.mark.parametrize("year", [1, 1900, 2026, 9999])
def test_sql_utc_date_arithmetic_keeps_extreme_year_and_microsecond_precision(history_parent, year):
    start = datetime(year, 1, 2, 23, 59, 59, 999999, tzinfo=UTC)
    end = datetime(year, 1, 3, 0, 0, 0, 1, tzinfo=UTC)
    row = _revision(history_parent, 1, start=start, end=end)
    certified = _certify(history_parent)
    assert (certified.start_at, certified.end_at) == (start, end)
    assert certified.pk == row.pk


def test_chain_certification_materializes_only_aggregates_violation_and_latest(history_parent):
    for number in range(1, 1002):
        _revision(history_parent, number)
    with CaptureQueriesContext(connection) as captured:
        assert _certify(history_parent).number == 1001
    selects = [
        entry["sql"]
        for entry in captured
        if entry["sql"].lstrip().upper().startswith("SELECT") and "pg_catalog" not in entry["sql"]
    ]
    assert len(selects) == 3
    assert "COUNT(DISTINCT number)" in selects[0]
    assert "previous.number=r.number-1" in selects[1]
    assert "LIMIT 1" in selects[1]
    assert "LIMIT 21" in selects[2]  # unique latest ORM get, not history materialization


def test_exclusive_end_midnight_geometry_is_checked_in_each_historical_row(history_parent):
    start = datetime(2026, 9, 5, 12, tzinfo=UTC)
    end = start + timedelta(hours=1)
    _revision(history_parent, 1, start=start, end=end)
    # This row's endpoints are both valid Sep5 civil instants in Santiago, but
    # Sep6 exclusive midnight is skipped. A raw frozen-zone corruption must not
    # become certified merely because neither UTC endpoint is in the gap.
    _corrupt(history_parent, timezone="America/Santiago")
    history_parent.timezone = "America/Santiago"
    with pytest.raises(ValidationError, match="retained facts"):
        _certify(history_parent)


def test_distinct_ordinal_scalar_oracle_rejects_duplicate_plus_gap():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*),COUNT(DISTINCT number),MIN(number),MAX(number) FROM "
            "(SELECT 1 AS number UNION ALL SELECT 2 UNION ALL SELECT 2 UNION ALL SELECT 4) evidence"
        )
        count, distinct, first, last = cursor.fetchone()
    assert count == last == 4 and first == 1
    assert count != distinct  # COUNT==MAX alone would falsely certify this chain


def test_zero_ordinal_is_rejected_by_the_normal_database_boundary(history_parent):
    with pytest.raises(IntegrityError), business_atomic_context():
        _revision(history_parent, 0, "CORRECT")


@pytest.mark.skipif(connection.vendor != "postgresql", reason="PostgreSQL catalog/RLS proof")
@pytest.mark.parametrize("enabled", [False, True])
def test_ordinary_reader_cannot_certify_rls_hidden_chain_or_disabled_policy(
    history_parent, enabled
):
    _revision(history_parent, 1)
    role = f"hr_history_reader_{uuid4().hex}"
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(f'CREATE ROLE "{role}" NOSUPERUSER NOBYPASSRLS NOLOGIN')
        cursor.execute(f'GRANT USAGE ON SCHEMA public TO "{role}"')
        cursor.execute(f'GRANT SELECT ON ALL TABLES IN SCHEMA public TO "{role}"')
        cursor.execute("CREATE POLICY synthetic_hide ON public.hr_attendancerevision USING(false)")
        if enabled:
            cursor.execute("ALTER TABLE public.hr_attendancerevision ENABLE ROW LEVEL SECURITY")
        cursor.execute(f'SET LOCAL ROLE "{role}"')
    try:
        with pytest.raises(ValidationError, match="RLS"):
            _certify(history_parent)
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET ROLE")


@pytest.mark.skipif(connection.vendor != "postgresql", reason="PostgreSQL relation identity proof")
@pytest.mark.parametrize("rls", [False, True])
def test_non_public_relocation_never_hides_from_literal_catalog_classification(history_parent, rls):
    _revision(history_parent, 1)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("CREATE SCHEMA pgx_review")
        cursor.execute("ALTER TABLE public.hr_attendancerevision SET SCHEMA pgx_review")
        if rls:
            cursor.execute(
                "CREATE POLICY synthetic_hide ON pgx_review.hr_attendancerevision USING(false)"
            )
            cursor.execute("ALTER TABLE pgx_review.hr_attendancerevision ENABLE ROW LEVEL SECURITY")
        cursor.execute("SET LOCAL search_path=pgx_review,public")
    with pytest.raises(ValidationError, match="namespace"):
        _certify(history_parent)


@pytest.mark.skipif(connection.vendor != "postgresql", reason="PostgreSQL shadow identity proof")
def test_shadow_relation_and_changed_search_path_reject_before_payload_sql(history_parent):
    _revision(history_parent, 1)
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA pgx_review")
        cursor.execute(
            "CREATE TABLE pgx_review.hr_attendancerevision "
            "(LIKE public.hr_attendancerevision INCLUDING ALL)"
        )
        cursor.execute("SET LOCAL search_path=pgx_review,public")
    with pytest.raises(ValidationError, match="namespace"):
        _certify(history_parent)
