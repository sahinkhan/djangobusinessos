from datetime import date, datetime, timedelta
from decimal import Decimal, localcontext
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, connection, models, transaction
from django.test.utils import CaptureQueriesContext

from businessos.core.access.models import RolePermission, UserCompanyAccess
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.modules.accounting import domain, selectors, services
from businessos.modules.accounting.models import Account, Journal, JournalEntry, JournalEntryLine
from businessos.modules.party.models import Party

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("kind", ["account", "journal"])
@pytest.mark.parametrize(
    "code,name,valid",
    [
        (" a ", " Name ", True),
        ("a" * 32, "x" * 160, True),
        ("a" * 33, "Name", False),
        ("ß" * 17, "Name", False),
        ("ß" * 16, "Name", True),
        ("x", "a" * 161, False),
        (" ", "Name", False),
        ("x", " ", False),
        (None, "Name", False),
        (42, "Name", False),
        ("x", None, False),
    ],
)
def test_reference_bounds(business_context, accounting_role, kind, code, name, valid):
    create = services.create_account if kind == "account" else services.create_journal
    data = dict(code=code, name=name) | ({"type": "ASSET"} if kind == "account" else {})
    before = AuditEntry.objects.count()
    if valid:
        row = create(business_context, **data)
        row.refresh_from_db()
        assert row.code == code.strip().upper() and row.name == name.strip()
    else:
        with pytest.raises(ValidationError):
            create(business_context, **data)
        assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("kind", ["account", "journal"])
@pytest.mark.parametrize("activity", [None, "false", 0, 1])
def test_reference_activity_strict(business_context, accounting_role, kind, activity):
    create = services.create_account if kind == "account" else services.create_journal
    with pytest.raises(ValidationError):
        create(
            business_context,
            code="x",
            name="X",
            is_active=activity,
            **({"type": "ASSET"} if kind == "account" else {}),
        )


@pytest.mark.parametrize("kind", ["account", "journal"])
def test_reference_noops_identity_uniqueness(business_context, account, journal, kind):
    row = account if kind == "account" else journal
    update = services.update_account if kind == "account" else services.update_journal
    create = services.create_account if kind == "account" else services.create_journal
    before = AuditEntry.objects.count()
    stamp = row.updated_at
    update(business_context, row.pk, name=row.name, is_active=True)
    row.refresh_from_db()
    assert row.updated_at == stamp and AuditEntry.objects.count() == before
    update(business_context, row.pk, name="New", is_active=False)
    row.refresh_from_db()
    assert row.name == "New" and not row.is_active
    for field in ("company_id", "code", "type"):
        with pytest.raises(ValidationError):
            update(business_context, row.pk, **{field: "bad"})
    with pytest.raises(ValidationError):
        create(
            business_context,
            code=row.code.lower(),
            name="Duplicate",
            **({"type": "ASSET"} if kind == "account" else {}),
        )


@pytest.mark.parametrize(
    "value",
    [
        "10",
        "10.5",
        "10.50",
        "10.5000",
        "1.05000000000e1",
        10,
        Decimal("10.50000000000000000000000"),
    ],
)
def test_redundant_zero_amount(business_context, entry, account, value):
    line = services.add_journal_entry_line(
        business_context, entry.pk, account_id=account.pk, debit=value, credit="0.000000000000"
    )
    line.refresh_from_db()
    assert line.debit == Decimal(str(value)) and line.credit == 0


@pytest.mark.parametrize("field", ["debit", "credit"])
@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        10.5,
        None,
        object(),
        "",
        "bad",
        "NaN",
        "sNaN",
        "Infinity",
        "-Infinity",
        "-1",
        "1e30",
        "10.501",
        "1e-9",
    ],
)
def test_bad_amount_no_partial_audit(business_context, entry, account, field, value):
    data = dict(debit="0", credit="0")
    data[field] = value
    before = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        services.add_journal_entry_line(business_context, entry.pk, account_id=account.pk, **data)
    assert not entry.lines.exists() and AuditEntry.objects.count() == before


@pytest.mark.parametrize("debit,credit", [("0", "0"), ("1", "1"), ("-0", "+0")])
def test_line_sides(business_context, entry, account, debit, credit):
    with pytest.raises(ValidationError):
        services.add_journal_entry_line(
            business_context, entry.pk, account_id=account.pk, debit=debit, credit=credit
        )


def test_positions_exhaustion_and_tail_reuse(business_context, entry, account):
    def add():
        return services.add_journal_entry_line(
            business_context, entry.pk, account_id=account.pk, debit=1, credit=0
        )

    first, tail = add(), add()
    assert [first.position, tail.position] == [1, 2]
    services.remove_journal_entry_line(business_context, entry.pk, tail.pk)
    assert add().position == 2
    # Adversarial fixture only, bypass guarded public APIs to reach storage boundary.
    models.QuerySet.update(
        JournalEntryLine.objects.filter(pk=first.pk), position=domain.MAX_POSITION
    )
    first.refresh_from_db()
    first.full_clean()
    before = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        add()
    assert entry.lines.count() == 2 and AuditEntry.objects.count() == before
    services.remove_journal_entry_line(business_context, entry.pk, first.pk)
    assert add().position == 3


@pytest.mark.parametrize("value", [0, -1, 2147483648, True, "1", 1.0, Decimal(1)])
def test_position_domain(value):
    with pytest.raises(ValueError):
        domain.position(value)


def test_long_text_dates_number_noop(business_context, entry, account):
    memo = " precise\n" + "x" * 12000
    entry = services.update_journal_entry(
        business_context, entry.pk, memo=memo, entry_date=date(2026, 10, 10)
    )
    assert entry.number == f"JE-{entry.pk.hex}" and len(entry.number) == 35
    line = services.add_journal_entry_line(
        business_context, entry.pk, account_id=account.pk, debit=1, credit=0, description=memo
    )
    entry.refresh_from_db()
    line.refresh_from_db()
    assert entry.memo == memo == line.description
    before = AuditEntry.objects.count()
    services.update_journal_entry(business_context, entry.pk, memo=memo)
    services.update_journal_entry_line(business_context, entry.pk, line.pk, description=memo)
    assert AuditEntry.objects.count() == before
    for value in [None, 3]:
        with pytest.raises(ValidationError):
            services.update_journal_entry(business_context, entry.pk, memo=value)
        with pytest.raises(ValidationError):
            services.update_journal_entry_line(
                business_context, entry.pk, line.pk, description=value
            )


@pytest.mark.parametrize("value", ["20261011", "2026-02-30", "bad", datetime(2026, 10, 11), 42])
def test_date_rejection(business_context, journal, value):
    with pytest.raises(ValidationError):
        services.create_journal_entry(business_context, journal_id=journal.pk, entry_date=value)


def test_local_default_date_once(business_context, journal):
    with patch.object(services, "company_local_date", return_value=date(2026, 10, 12)) as local:
        entry = services.create_journal_entry(business_context, journal_id=journal.pk)
    assert entry.entry_date == date(2026, 10, 12)
    local.assert_called_once_with(business_context.company_id)


def test_number_collisions_and_unrelated_integrity(business_context, journal, entry):
    with patch.object(services, "uuid4", side_effect=[entry.pk, entry.pk, uuid4()]):
        created = services.create_journal_entry(business_context, journal_id=journal.pk)
        assert created.pk != entry.pk
    before = AuditEntry.objects.count()
    with patch.object(services, "uuid4", return_value=entry.pk):
        with pytest.raises(ValidationError):
            services.create_journal_entry(business_context, journal_id=journal.pk)
    assert AuditEntry.objects.count() == before
    with patch.object(JournalEntry, "_persist", side_effect=IntegrityError("unrelated")):
        with pytest.raises(IntegrityError):
            services.create_journal_entry(business_context, journal_id=journal.pk)


def test_posting_retry_retired_references(
    business_context, balanced, account, journal, party, company
):
    assert list(selectors.general_ledger(business_context)) == []
    posted = services.post_journal_entry(business_context, balanced.pk)
    stamp = posted.posted_at
    assert len(selectors.general_ledger(business_context)) == 2
    services.update_account(business_context, account.pk, is_active=False)
    services.update_journal(business_context, journal.pk, is_active=False)
    party.is_active = False
    party.save()
    before = AuditEntry.objects.count()
    retried = services.post_journal_entry(business_context, balanced.pk)
    assert retried.posted_at == stamp and AuditEntry.objects.count() == before
    assert len(selectors.trial_balance(business_context)) == 1
    assert selectors.trial_balance(business_context)[0].net == 0
    UserCompanyAccess.objects.filter(company=company).delete()
    with pytest.raises(PermissionDenied):
        services.post_journal_entry(business_context, balanced.pk)


@pytest.mark.parametrize("retire", ["account", "journal", "party", "imbalance", "empty", "one"])
def test_invalid_post_rollback(business_context, balanced, account, journal, party, retire):
    if retire == "account":
        services.update_account(business_context, account.pk, is_active=False)
    elif retire == "journal":
        services.update_journal(business_context, journal.pk, is_active=False)
    elif retire == "party":
        party.is_active = False
        party.save()
    elif retire == "imbalance":
        services.update_journal_entry_line(
            business_context, balanced.pk, balanced.lines.first().pk, debit="10.49"
        )
    else:
        for line in list(balanced.lines.all())[: 2 if retire == "empty" else 1]:
            services.remove_journal_entry_line(business_context, balanced.pk, line.pk)
    before = AuditEntry.objects.count()
    with pytest.raises(ValidationError):
        services.post_journal_entry(business_context, balanced.pk)
    balanced.refresh_from_db()
    assert balanced.status == "DRAFT" and balanced.posted_at is None
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("model", [Account, Journal, JournalEntry, JournalEntryLine])
@pytest.mark.parametrize(
    "api", ["save", "delete", "update", "query_delete", "bulk_create", "bulk_update", "upsert"]
)
def test_public_orm_is_service_only(balanced, account, journal, model, api):
    row = model.objects.first()
    with pytest.raises(ValidationError):
        if api == "save":
            row.save()
        elif api == "delete":
            row.delete()
        elif api == "update":
            model.objects.filter(pk=row.pk).update(updated_at=row.updated_at)
        elif api == "query_delete":
            model.objects.all().delete()
        elif api == "bulk_create":
            model.objects.bulk_create([row])
        elif api == "bulk_update":
            model.objects.bulk_update([row], ["updated_at"])
        else:
            model.objects.bulk_create(
                [row], update_conflicts=True, update_fields=["updated_at"], unique_fields=["id"]
            )


@pytest.mark.parametrize(
    "operation",
    [
        "account_create",
        "account_update",
        "journal_create",
        "journal_update",
        "entry_create",
        "entry_update",
        "line_add",
        "line_update",
        "line_remove",
        "post",
    ],
)
def test_audit_failure_atomic(business_context, balanced, account, journal, operation):
    line = balanced.lines.first()
    calls = {
        "account_create": lambda: services.create_account(
            business_context, code="OTHER", name="Other", type="INCOME"
        ),
        "account_update": lambda: services.update_account(
            business_context, account.pk, name="Other"
        ),
        "journal_create": lambda: services.create_journal(
            business_context, code="OTHER", name="Other"
        ),
        "journal_update": lambda: services.update_journal(
            business_context, journal.pk, name="Other"
        ),
        "entry_create": lambda: services.create_journal_entry(
            business_context, journal_id=journal.pk
        ),
        "entry_update": lambda: services.update_journal_entry(
            business_context, balanced.pk, memo="Other"
        ),
        "line_add": lambda: services.add_journal_entry_line(
            business_context, balanced.pk, account_id=account.pk, debit=1, credit=0
        ),
        "line_update": lambda: services.update_journal_entry_line(
            business_context, balanced.pk, line.pk, description="Other"
        ),
        "line_remove": lambda: services.remove_journal_entry_line(
            business_context, balanced.pk, line.pk
        ),
        "post": lambda: services.post_journal_entry(business_context, balanced.pk),
    }

    def state():
        return [
            list(m.objects.values())
            for m in [Account, Journal, JournalEntry, JournalEntryLine, AuditEntry]
        ]

    before = state()
    with patch.object(services, "record_audit_entry", side_effect=RuntimeError("audit")):
        with pytest.raises(RuntimeError):
            calls[operation]()
    assert state() == before


def test_currency_precision_drift_reports_and_filters(
    business_context, balanced, account, currency, journal
):
    services.post_journal_entry(business_context, balanced.pk)
    currency.decimal_places = 3
    currency.save()
    second = services.create_journal_entry(
        business_context, journal_id=journal.pk, entry_date="2026-10-12"
    )
    for debit, credit in [("1.234", "0"), ("0", "1.234")]:
        services.add_journal_entry_line(
            business_context, second.pk, account_id=account.pk, debit=debit, credit=credit
        )
    services.post_journal_entry(business_context, second.pk)
    currency.decimal_places = 0
    currency.save()
    row = selectors.trial_balance(business_context)[0]
    assert row.total_debit == Decimal("11.734") and row.formatted_debit == "11.734"
    assert len(selectors.general_ledger(business_context, to_date="2026-10-11")) == 2
    assert (
        len(
            selectors.general_ledger(business_context, from_date="2026-10-12", to_date="2026-10-12")
        )
        == 2
    )
    assert len(selectors.general_ledger(business_context, account_id=account.pk)) == 4
    with pytest.raises(ValidationError):
        selectors.general_ledger(business_context, from_date="2026-10-12", to_date="2026-10-11")
    models.QuerySet.update(
        JournalEntry.objects.filter(pk=second.pk), base_currency_code_snapshot="EUR"
    )
    for selector in [selectors.general_ledger, selectors.trial_balance]:
        with pytest.raises(ValidationError):
            selector(business_context)


def test_company_isolation_all_relationships(
    business_context, account, journal, entry, operator, company
):
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    operator.is_superuser = True
    operator.save()
    context = BusinessContext(actor_id=operator.pk, company_id=other.pk)
    other_account = services.create_account(context, code="CASH", name="Other", type="ASSET")
    other_journal = services.create_journal(context, code="GEN", name="Other")
    other_party = Party.objects.create(
        company=other, party_type="organization", display_name="Other"
    )
    assert not selectors.accounts_for_company(context).filter(pk=account.pk).exists()
    assert not selectors.journals_for_company(context).filter(pk=journal.pk).exists()
    with pytest.raises(JournalEntry.DoesNotExist):
        selectors.journal_entry_detail(context, entry.pk)
    for kwargs in [{"account_id": other_account.pk}, {"party_id": other_party.pk}]:
        with pytest.raises(ValidationError):
            services.add_journal_entry_line(
                business_context,
                entry.pk,
                **(dict(account_id=account.pk, debit=1, credit=0) | kwargs),
            )
    with pytest.raises(ValidationError):
        services.update_journal_entry(business_context, entry.pk, journal_id=other_journal.pk)
    with pytest.raises(ValidationError):
        selectors.trial_balance(business_context, account_id=other_account.pk)


@pytest.mark.skipif(
    connection.vendor != "postgresql", reason="SQLite numeric affinity is not exact numeric(38,8)."
)
def test_large_exact_post_sql_python_and_low_context(business_context, journal, account, currency):
    currency.decimal_places = 8
    currency.save()
    entry = services.create_journal_entry(business_context, journal_id=journal.pk)
    maximum = "999999999999999999999999999999.99999999"
    with localcontext() as ctx:
        ctx.prec = 6
        for _ in range(3):
            for debit, credit in [(maximum, "0"), ("0", maximum)]:
                services.add_journal_entry_line(
                    business_context, entry.pk, account_id=account.pk, debit=debit, credit=credit
                )
        services.post_journal_entry(business_context, entry.pk)
        assert entry.totals == (Decimal("2999999999999999999999999999999.99999997"),) * 2
        tb = selectors.trial_balance(business_context)[0]
        assert tb.net == 0 and tb.formatted_debit == "2999999999999999999999999999999.99999997"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT SUM(debit), SUM(credit) FROM accounting_journalentryline "
            "WHERE journal_entry_id=%s",
            [entry.pk],
        )
        assert cursor.fetchone() == entry.totals


@pytest.mark.parametrize(
    "model,changes",
    [
        (Account, {"type": "BAD"}),
        (JournalEntry, {"status": "POSTED"}),
        (JournalEntry, {"base_currency_precision_snapshot": 9}),
        (JournalEntryLine, {"position": 0}),
        (JournalEntryLine, {"debit": -1}),
        (JournalEntryLine, {"debit": 1, "credit": 1}),
    ],
)
def test_database_constraints(balanced, account, model, changes):
    with pytest.raises(IntegrityError), transaction.atomic():
        models.QuerySet.update(model.objects.all(), **changes)


@pytest.fixture
def report_history(business_context, journal, account, party, currency):
    """66 service-posted lines, with an independent ID/value/order oracle."""
    other = services.create_account(
        business_context, code="PAYABLE", name="Historical payable", type="LIABILITY"
    )
    expected = []
    for index in range(33):
        currency.decimal_places = 2 if index < 16 else 3
        currency.save()
        day = date(2026, 10, 1) + timedelta(days=index % 3)
        memo = f"memo-{index}:" + "m" * 12000
        entry = services.create_journal_entry(
            business_context, journal_id=journal.pk, entry_date=day, memo=memo
        )
        value = Decimal("1.25") if index < 16 else Decimal("1.234")
        for position, (target, debit, credit) in enumerate(
            [(account, value, Decimal(0)), (other, Decimal(0), value)], 1
        ):
            description = f"line-{index}-{position}:" + "d" * 12000
            line = services.add_journal_entry_line(
                business_context,
                entry.pk,
                account_id=target.pk,
                party_id=party.pk,
                debit=debit,
                credit=credit,
                description=description,
            )
            expected.append(
                dict(
                    id=line.pk,
                    entry_id=entry.pk,
                    account_id=target.pk,
                    day=day,
                    number=entry.number,
                    position=position,
                    memo=memo,
                    description=description,
                    debit=debit,
                    credit=credit,
                )
            )
        services.post_journal_entry(business_context, entry.pk)
    services.update_account(business_context, other.pk, is_active=False)
    expected.sort(
        key=lambda row: (row["day"], row["number"], row["entry_id"], row["position"], row["id"])
    )
    return expected


def _payload_queries(captured):
    return [
        query["sql"].lower()
        for query in captured
        if query["sql"].lstrip().lower().startswith("select")
        and '"accounting_journalentryline"."description"' in query["sql"].lower()
    ]


def _observe_loaded_lines(monkeypatch):
    loaded = []
    original = JournalEntryLine.from_db

    def observe(db, fields, values):
        loaded.append(values[fields.index("id")])
        return original(db, fields, values)

    monkeypatch.setattr(JournalEntryLine, "from_db", observe)
    return loaded


def test_report_future_gl_sql_filter(business_context, report_history, monkeypatch):
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries:
        rows = list(selectors.general_ledger(business_context, from_date="2027-01-01"))
    assert rows == []
    assert loaded == [], f"Empty GL materialized {len(loaded)} posted lines."
    payload = _payload_queries(queries)
    assert len(payload) == 1 and "2027-01-01" in payload[0] and ">=" in payload[0]


def test_report_gl_page_sql_bound(business_context, report_history, monkeypatch):
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries:
        page = Paginator(selectors.general_ledger(business_context), 50).page(1)
        rows = list(page.object_list)
    assert len(rows) == 50
    assert loaded == [row["id"] for row in report_history[:50]]
    payload = _payload_queries(queries)
    assert len(payload) == 1 and "limit 50" in payload[0]


def _assert_minimal_integrity(queries):
    probes = [
        query["sql"].lower()
        for query in queries
        if 'from "accounting_journalentryline"' in query["sql"].lower()
        and query["sql"].lower().startswith("select 1 ")
    ]
    assert 1 <= len(probes) <= 2
    for sql in probes:
        assert "limit 1" in sql
        assert "memo" not in sql and "description" not in sql
    return probes


def test_report_gl_page_two_order_and_long_text(business_context, report_history, monkeypatch):
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries:
        paginator = Paginator(selectors.general_ledger(business_context), 50)
        first = list(paginator.page(1).object_list)
        second = list(paginator.page(2).object_list)
    assert [line.pk for line in first + second] == [row["id"] for row in report_history]
    assert not {line.pk for line in first} & {line.pk for line in second}
    assert len(second) == 16
    assert loaded == [row["id"] for row in report_history]
    for line, expected in zip(first + second, report_history, strict=True):
        assert line.description == expected["description"]
        assert line.journal_entry.memo == expected["memo"]
        assert (line.debit, line.credit) == (expected["debit"], expected["credit"])
    payload = _payload_queries(queries)
    assert len(payload) == 2
    assert "limit 50" in payload[0]
    assert "limit 16" in payload[1] and "offset 50" in payload[1]
    for sql in payload:
        order = sql.split("order by", 1)[1]
        terms = ["entry_date", "number", "journal_entry_id", "position"]
        assert [order.index(term) for term in terms] == sorted(order.index(t) for t in terms)
    _assert_minimal_integrity(queries)


def test_report_gl_account_and_inclusive_dates_sql(
    business_context, report_history, account, monkeypatch
):
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries:
        rows = list(
            selectors.general_ledger(
                business_context,
                from_date="2026-10-02",
                to_date="2026-10-02",
                account_id=account.pk,
            )
        )
    expected = [
        row["id"]
        for row in report_history
        if row["day"] == date(2026, 10, 2) and row["account_id"] == account.pk
    ]
    assert loaded == [line.pk for line in rows] == expected
    payload = _payload_queries(queries)
    assert len(payload) == 1
    where = payload[0].split(" where ", 1)[1].split(" order by ", 1)[0]
    assert "entry_date" in where and ">=" in where and "<=" in where
    assert str(account.pk).replace("-", "") in where.replace("-", "")
    assert '"accounting_journalentryline"."account_id" =' in where
    _assert_minimal_integrity(queries)


def test_report_future_tb_grouped_sql(business_context, report_history, monkeypatch):
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries:
        assert selectors.trial_balance(business_context, from_date="2027-01-01") == []
    assert loaded == [] and _payload_queries(queries) == []
    aggregates = [q["sql"].lower() for q in queries if "sum(" in q["sql"].lower()]
    assert len(aggregates) == 1
    assert "group by" in aggregates[0] and "max(" in aggregates[0]
    assert "2027-01-01" in aggregates[0] and ">=" in aggregates[0]
    _assert_minimal_integrity(queries)


def test_report_tb_aggregate_history_precision_and_zero_net(
    business_context, report_history, journal, currency, monkeypatch
):
    currency.decimal_places = 8
    currency.save()
    zero = services.create_account(business_context, code="ZERO", name="Zero net", type="ASSET")
    entry = services.create_journal_entry(
        business_context, journal_id=journal.pk, entry_date="2026-10-02"
    )
    for debit, credit in [("0.00000001", "0"), ("0", "0.00000001")]:
        services.add_journal_entry_line(
            business_context, entry.pk, account_id=zero.pk, debit=debit, credit=credit
        )
    services.post_journal_entry(business_context, entry.pk)
    currency.decimal_places = 0
    currency.save()
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries, localcontext() as ctx:
        ctx.prec = 2
        rows = selectors.trial_balance(business_context)
    assert loaded == [] and _payload_queries(queries) == []
    assert len(rows) == 3
    assert [row.account.code for row in rows] == ["CASH", "PAYABLE", "ZERO"]
    assert rows[0].total_debit == rows[1].total_credit == Decimal("40.978")
    assert rows[0].ending_debit == rows[1].ending_credit == Decimal("40.978")
    assert not rows[1].account.is_active
    assert rows[2].net == rows[2].ending_debit == rows[2].ending_credit == 0
    assert rows[2].total_debit == rows[2].total_credit == Decimal("0.00000001")
    assert all(row.precision == 8 for row in rows)
    assert rows[0].formatted_debit == "40.97800000"
    aggregates = [q["sql"].lower() for q in queries if "sum(" in q["sql"].lower()]
    assert len(aggregates) == 1
    assert "group by" in aggregates[0] and "max(" in aggregates[0]
    assert "memo" not in aggregates[0] and "description" not in aggregates[0]
    _assert_minimal_integrity(queries)


def test_report_tb_account_date_predicates(business_context, report_history, account, monkeypatch):
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries:
        rows = selectors.trial_balance(
            business_context,
            account_id=account.pk,
            from_date="2026-10-02",
            to_date="2026-10-02",
        )
    assert loaded == [] and len(rows) == 1
    expected = sum(
        (r["debit"] for r in report_history if r["day"] == date(2026, 10, 2)), Decimal(0)
    )
    assert rows[0].account.pk == account.pk and rows[0].total_debit == expected
    aggregate = next(q["sql"].lower() for q in queries if "sum(" in q["sql"].lower())
    where = aggregate.split(" where ", 1)[1].split(" group by ", 1)[0]
    assert "entry_date" in where and ">=" in where and "<=" in where
    assert '"accounting_journalentryline"."account_id" =' in where
    assert str(account.pk).replace("-", "") in where.replace("-", "")


@pytest.mark.parametrize("selector", [selectors.general_ledger, selectors.trial_balance])
@pytest.mark.parametrize(
    "corrupt", ["line_company", "entry_company", "account", "journal", "party", "currency", "scale"]
)
def test_report_outside_filter_corruption_minimal_fail_closed(
    business_context, balanced, account, journal, party, company, selector, corrupt, monkeypatch
):
    services.update_journal_entry(business_context, balanced.pk, memo="m" * 12000)
    services.post_journal_entry(business_context, balanced.pk)
    requested = services.create_account(
        business_context, code="REQUESTED", name="Requested", type="ASSET"
    )
    requested_journal = services.create_journal(
        business_context, code="REQUESTED", name="Requested journal"
    )
    valid_entry = services.create_journal_entry(
        business_context, journal_id=requested_journal.pk, entry_date="2027-01-01"
    )
    for debit, credit in [(1, 0), (0, 1)]:
        services.add_journal_entry_line(
            business_context, valid_entry.pk, account_id=requested.pk, debit=debit, credit=credit
        )
    services.post_journal_entry(business_context, valid_entry.pk)
    valid_scope = selector(business_context, from_date="2027-01-01", account_id=requested.pk)
    assert len(valid_scope) == (2 if selector == selectors.general_ledger else 1)
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    if corrupt == "line_company":
        models.QuerySet.update(balanced.lines.all(), company_id=other.pk)
    elif corrupt == "entry_company":
        models.QuerySet.update(JournalEntry.objects.filter(pk=balanced.pk), company_id=other.pk)
    elif corrupt in {"account", "journal", "party"}:
        row = {"account": account, "journal": journal, "party": party}[corrupt]
        models.QuerySet.update(type(row).objects.filter(pk=row.pk), company_id=other.pk)
    elif corrupt == "currency":
        models.QuerySet.update(
            JournalEntry.objects.filter(pk=balanced.pk), base_currency_code_snapshot="XXX"
        )
    else:
        models.QuerySet.update(
            JournalEntry.objects.filter(pk=balanced.pk), base_currency_precision_snapshot=0
        )
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries, pytest.raises(ValidationError):
        selector(business_context, from_date="2027-01-01", account_id=requested.pk)
    assert loaded == [] and _payload_queries(queries) == []
    _assert_minimal_integrity(queries)


@pytest.mark.skipif(connection.vendor != "postgresql", reason="Exact PostgreSQL numeric SUM.")
def test_report_large_tb_without_ledger_objects(
    business_context, balanced, account, currency, monkeypatch
):
    currency.decimal_places = 8
    currency.save()
    entry = services.create_journal_entry(
        business_context, journal_id=balanced.journal_id, entry_date="2026-10-03"
    )
    maximum = Decimal("999999999999999999999999999999.99999999")
    stamp = entry.created_at
    # Test-only storage fixture: 2,002 individually valid one-sided lines.
    # Bypassing public ORM here avoids timing writes; report behavior is the subject.
    lines = [
        JournalEntryLine(
            company_id=entry.company_id,
            journal_entry=entry,
            account=account,
            debit=maximum if i % 2 == 0 else 0,
            credit=maximum if i % 2 else 0,
            description="d" * 12000,
            position=i + 1,
            created_at=stamp,
            updated_at=stamp,
        )
        for i in range(2002)
    ]
    models.QuerySet.bulk_create(JournalEntryLine.objects.all(), lines, batch_size=100)
    services.post_journal_entry(business_context, entry.pk)
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries, localcontext() as ctx:
        ctx.prec = 2
        rows = selectors.trial_balance(business_context)
    assert loaded == [] and _payload_queries(queries) == [] and len(rows) == 1
    expected = Decimal("1000999999999999999999999999999999.99998999")
    assert rows[0].total_debit == rows[0].total_credit == expected
    assert rows[0].net == 0 and rows[0].precision == 8
    aggregate = next(q["sql"].lower() for q in queries if "sum(" in q["sql"].lower())
    assert "numeric(38" not in aggregate and "float" not in aggregate
    _assert_minimal_integrity(queries)


@pytest.mark.parametrize("selector", [selectors.general_ledger, selectors.trial_balance])
@pytest.mark.parametrize("revoked", ["permission", "access", "actor", "company"])
def test_report_authorization_before_payload(
    business_context, balanced, company, operator, accounting_role, selector, revoked, monkeypatch
):
    services.post_journal_entry(business_context, balanced.pk)
    if revoked == "permission":
        RolePermission.objects.filter(
            role=accounting_role, permission__code="accounting.entry.view"
        ).delete()
    elif revoked == "access":
        UserCompanyAccess.objects.filter(user=operator, company=company).delete()
    else:
        row = operator if revoked == "actor" else company
        row.is_active = False
        row.save()
    loaded = _observe_loaded_lines(monkeypatch)
    with CaptureQueriesContext(connection) as queries, pytest.raises(PermissionDenied):
        selector(business_context)
    assert loaded == [] and _payload_queries(queries) == []
    assert not any("accounting_journalentryline" in query["sql"] for query in queries)
