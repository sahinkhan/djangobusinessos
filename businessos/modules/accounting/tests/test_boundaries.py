from decimal import Decimal, localcontext
from unittest.mock import patch

import pytest
from asgiref.sync import async_to_sync
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models

from businessos.core.access.models import Permission
from businessos.core.audit.models import AuditEntry
from businessos.modules.accounting import domain, selectors, services
from businessos.modules.accounting.models import Account, JournalEntry, JournalEntryLine

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "places,value,valid",
    [
        (0, "100.000000000000", True),
        (0, "100.1", False),
        (2, "10.500000000000", True),
        (2, "10.501", False),
        (8, "0.00000001", True),
        (8, "0.000000001", False),
    ],
)
def test_precision_representability(places, value, valid):
    with localcontext() as ctx:
        ctx.prec = 2
        if valid:
            assert domain.amount(value, places) == Decimal(value)
        else:
            with pytest.raises(ValueError):
                domain.amount(value, places)


@pytest.mark.parametrize("places", [True, False, "2", 2.0, -1, 9, None])
def test_invalid_precision(places):
    with pytest.raises(ValueError):
        domain.precision(places)


def test_frozen_precision_and_currency_retirement(business_context, entry, account, currency):
    currency.decimal_places = 0
    currency.is_active = False
    currency.save()
    with pytest.raises(ValidationError):
        services.update_journal_entry(
            business_context, entry.pk, base_currency_precision_snapshot=0
        )
    for debit, credit in [("1.23", "0"), ("0", "1.23")]:
        services.add_journal_entry_line(
            business_context, entry.pk, account_id=account.pk, debit=debit, credit=credit
        )
    posted = services.post_journal_entry(business_context, entry.pk)
    assert posted.base_currency_precision_snapshot == 2


@pytest.mark.parametrize(
    "model_field,value",
    [
        ("company_id", None),
        ("journal_entry_id", None),
        ("position", 123),
        ("debit", Decimal("NaN")),
        ("credit", Decimal("Infinity")),
    ],
)
def test_stale_substituted_line_public_guard(business_context, balanced, model_field, value):
    stale = balanced.lines.first()
    before = list(balanced.lines.values())
    services.post_journal_entry(business_context, balanced.pk)
    setattr(stale, model_field, value)
    for action in (stale.save, stale.delete):
        with pytest.raises(ValidationError):
            action()
    assert list(balanced.lines.values()) == before


def test_removed_line_cannot_resurrect(business_context, balanced):
    stale = balanced.lines.first()
    services.remove_journal_entry_line(business_context, balanced.pk, stale.pk)
    with pytest.raises(ValidationError):
        stale.save()
    with pytest.raises(ValidationError):
        services.update_journal_entry_line(
            business_context, balanced.pk, stale.pk, description="No"
        )
    assert not JournalEntryLine.objects.filter(pk=stale.pk).exists()


def test_post_retry_retired_permission(business_context, balanced):
    services.post_journal_entry(business_context, balanced.pk)
    permission = Permission.objects.get(code="accounting.entry.post")
    permission.is_active = False
    permission.save()
    with pytest.raises(PermissionDenied):
        services.post_journal_entry(business_context, balanced.pk)
    assert AuditEntry.objects.filter(action="accounting.entry.posted").count() == 1


def test_noop_timestamps_and_all_changed_fields_audited(business_context, balanced, account, party):
    line = balanced.lines.first()
    original = (line.updated_at, AuditEntry.objects.count())
    returned = services.update_journal_entry_line(
        business_context,
        balanced.pk,
        line.pk,
        debit="10.50000000",
        credit="0.0000000000",
        description="",
        account_id=account.pk,
        party_id=party.pk,
    )
    assert (returned.updated_at, AuditEntry.objects.count()) == original
    services.update_journal_entry_line(
        business_context, balanced.pk, line.pk, party_id=None, description="New"
    )
    audit = AuditEntry.objects.order_by("-occurred_at").first()
    assert set(audit.metadata["fields"]) == {"party_id", "description"}
    assert audit.metadata["line_id"] == str(line.pk)
    services.remove_journal_entry_line(business_context, balanced.pk, line.pk)
    audit = AuditEntry.objects.order_by("-occurred_at").first()
    assert audit.metadata["operation"] == "line_removed" and audit.metadata["line_id"] == str(
        line.pk
    )


def test_retired_draft_reference_can_be_replaced(
    business_context, balanced, account, journal, party
):
    services.update_account(business_context, account.pk, is_active=False)
    services.update_journal(business_context, journal.pk, is_active=False)
    party.is_active = False
    party.save()
    replacement = services.create_account(business_context, code="NEW", name="New", type="ASSET")
    replacement_journal = services.create_journal(business_context, code="NEW", name="New")
    services.update_journal_entry(business_context, balanced.pk, journal_id=replacement_journal.pk)
    for line in balanced.lines.all():
        services.update_journal_entry_line(
            business_context, balanced.pk, line.pk, account_id=replacement.pk, party_id=None
        )
    services.post_journal_entry(business_context, balanced.pk)


@pytest.mark.parametrize("api", ["aupdate", "adelete", "abulk_create", "abulk_update"])
def test_async_public_query_guards(account, api):
    call = getattr(Account.objects.all(), api)
    args = {
        "aupdate": {"name": "No"},
        "adelete": {},
        "abulk_create": {"objs": [account]},
        "abulk_update": {"objs": [account], "fields": ["name"]},
    }[api]
    with pytest.raises(ValidationError):
        async_to_sync(call)(**args)


@pytest.mark.parametrize("field", ["company_id", "account_id", "journal_id", "currency"])
def test_reports_fail_closed_malformed_provenance(business_context, balanced, field):
    services.post_journal_entry(business_context, balanced.pk)
    if field == "currency":
        models.QuerySet.update(
            JournalEntry.objects.filter(pk=balanced.pk), base_currency_code_snapshot="XXX"
        )
    else:
        from businessos.core.organization.models import Company
        from businessos.modules.accounting.models import Journal

        company = Company.objects.get(pk=business_context.company_id)
        other = Company.objects.create(
            code="OTHER",
            name="Other",
            base_currency=company.base_currency,
            country=company.country,
            default_language=company.default_language,
        )
        if field == "company_id":
            models.QuerySet.update(
                JournalEntryLine.objects.filter(journal_entry=balanced), company_id=other.pk
            )
        elif field == "account_id":
            models.QuerySet.update(Account.objects.all(), company_id=other.pk)
        else:
            models.QuerySet.update(Journal.objects.all(), company_id=other.pk)
    for selector in [selectors.general_ledger, selectors.trial_balance]:
        with pytest.raises(ValidationError):
            selector(business_context)


def test_unauthorized_creation_and_post_have_no_state(business_context, journal, accounting_role):
    from businessos.core.access.models import RolePermission

    RolePermission.objects.filter(role=accounting_role).delete()
    with pytest.raises(PermissionDenied):
        services.create_journal_entry(business_context, journal_id=journal.pk)
    assert not JournalEntry.objects.exists()


def test_collision_unrelated_does_not_retry(business_context, journal):
    from django.db import IntegrityError

    with patch.object(
        JournalEntry, "_persist", side_effect=IntegrityError("foreign key")
    ) as insert:
        with pytest.raises(IntegrityError):
            services.create_journal_entry(business_context, journal_id=journal.pk)
        assert insert.call_count == 1


def test_trial_balance_positive_negative_and_range(business_context, journal, account):
    other = services.create_account(
        business_context, code="PAYABLE", name="Payable", type="LIABILITY"
    )
    entry = services.create_journal_entry(
        business_context, journal_id=journal.pk, entry_date="2026-10-01"
    )
    services.add_journal_entry_line(
        business_context, entry.pk, account_id=account.pk, debit="123.45", credit=0
    )
    services.add_journal_entry_line(
        business_context, entry.pk, account_id=other.pk, debit=0, credit="123.45"
    )
    services.post_journal_entry(business_context, entry.pk)
    services.update_account(business_context, other.pk, is_active=False)
    with localcontext() as ctx:
        ctx.prec = 2
        rows = selectors.trial_balance(business_context, to_date="2026-10-01")
        assert [(row.net, row.ending_debit, row.ending_credit) for row in rows] == [
            (Decimal("123.45"), Decimal("123.45"), Decimal(0)),
            (Decimal("-123.45"), Decimal(0), Decimal("123.45")),
        ]
        assert rows[1].formatted_ending_credit == "123.45"
    assert selectors.trial_balance(business_context, from_date="2026-10-02") == []
    assert (
        len(
            selectors.general_ledger(business_context, from_date="2026-10-01", to_date="2026-10-01")
        )
        == 2
    )


@pytest.mark.parametrize("inactive", ["company", "actor"])
def test_post_retry_current_active_context_required(
    business_context, balanced, company, operator, inactive
):
    services.post_journal_entry(business_context, balanced.pk)
    row = company if inactive == "company" else operator
    row.is_active = False
    row.save()
    before = AuditEntry.objects.count()
    with pytest.raises(PermissionDenied):
        services.post_journal_entry(business_context, balanced.pk)
    assert AuditEntry.objects.count() == before
