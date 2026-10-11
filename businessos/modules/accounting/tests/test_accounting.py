from datetime import date, datetime
from decimal import Decimal, localcontext
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, models, transaction

from businessos.core.access.models import UserCompanyAccess
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
    assert selectors.general_ledger(business_context) == []
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
