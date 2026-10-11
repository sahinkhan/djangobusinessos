from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import database_execution
from businessos.core.organization.models import Company
from businessos.core.reference.models import Country, Currency, Language
from businessos.modules.accounting import selectors, services
from businessos.modules.accounting.models import JournalEntry
from businessos.modules.party.models import Party


def test_nondefault_full_workflow(django_db_blocker, monkeypatch):
    alias = "accounting_verification_alias"
    config = dict(connections.databases["default"])
    postgres = config["ENGINE"] == "django.db.backends.postgresql"
    admin = None
    if postgres:
        import psycopg
        from psycopg import sql

        admin = psycopg.connect(
            dbname="postgres",
            user=config["USER"],
            password=config["PASSWORD"],
            host=config["HOST"],
            port=config["PORT"],
            autocommit=True,
        )
        config["NAME"] = "acc1_alias_" + uuid4().hex
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(config["NAME"])))
    else:
        config.update(NAME=":memory:", OPTIONS={})
    connections.databases[alias] = config
    statements = []

    def trace(execute, sql, params, many, context):
        statements.append(sql)
        return execute(sql, params, many, context)

    def forbidden(*args, **kwargs):
        pytest.fail("Accounting accessed default while another alias was selected.")

    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(connections["default"], "cursor", forbidden)
            with django_db_blocker.unblock(), database_execution(alias):
                executor = MigrationExecutor(connections[alias])
                executor.migrate(executor.loader.graph.leaf_nodes())
                company = Company.objects.create(
                    code="ALIAS",
                    name="Alias",
                    base_currency=Currency.objects.create(code="USD", name="Dollar"),
                    country=Country.objects.create(code="US", name="US"),
                    default_language=Language.objects.create(code="EN", name="English"),
                )
                actor = get_user_model().objects.create_superuser(
                    "alias@accounting.test", "test-only"
                )
                context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
                party = Party.objects.create(
                    company=company, party_type="person", display_name="Alias"
                )
                with connections[alias].execute_wrapper(trace):
                    account = services.create_account(
                        context, code="CASH", name="Cash", type="ASSET"
                    )
                    journal = services.create_journal(context, code="GEN", name="General")
                    services.update_account(context, account.pk, name="Cash 2")
                    services.update_journal(context, journal.pk, name="General 2")
                    entry = services.create_journal_entry(context, journal_id=journal.pk)
                    services.update_journal_entry(context, entry.pk, memo="Alias")
                    debit = services.add_journal_entry_line(
                        context,
                        entry.pk,
                        account_id=account.pk,
                        party_id=party.pk,
                        debit=2,
                        credit=0,
                    )
                    services.update_journal_entry_line(
                        context, entry.pk, debit.pk, description="Debit"
                    )
                    removed = services.add_journal_entry_line(
                        context, entry.pk, account_id=account.pk, debit=0, credit=2
                    )
                    services.remove_journal_entry_line(context, entry.pk, removed.pk)
                    services.add_journal_entry_line(
                        context, entry.pk, account_id=account.pk, debit=0, credit=2
                    )
                    before = AuditEntry.objects.count()
                    with patch.object(
                        services, "record_audit_entry", side_effect=RuntimeError("audit")
                    ):
                        with pytest.raises(RuntimeError):
                            services.post_journal_entry(context, entry.pk)
                    entry.refresh_from_db()
                    assert entry.status == "DRAFT" and AuditEntry.objects.count() == before
                    posted = services.post_journal_entry(context, entry.pk)
                    assert (
                        services.post_journal_entry(context, entry.pk).posted_at == posted.posted_at
                    )
                    assert selectors.journal_entry_detail(context, entry.pk)._state.db == alias
                    assert len(selectors.general_ledger(context)) == 2
                    assert selectors.trial_balance(context)[0].net == 0
                    lazy_page = selectors.general_ledger(
                        context, account_id=account.pk, to_date=entry.entry_date
                    )[:1]
                    assert lazy_page.db == alias
                    page = Paginator(selectors.general_ledger(context), 1).page(2)
                    assert len(page.object_list) == 1
                    assert (
                        selectors.trial_balance(context, account_id=account.pk)[0].account._state.db
                        == alias
                    )
                    assert not list(selectors.general_ledger(context, from_date="9999-01-01"))
                    assert selectors.trial_balance(context, from_date="9999-01-01") == []
                    assert JournalEntry.objects.count() == 1
                    assert all(a._state.db == alias for a in AuditEntry.objects.all())
                assert any("SAVEPOINT" in statement for statement in statements)
                if postgres:
                    assert any("FOR UPDATE" in statement for statement in statements)
                assert any("LIMIT 1 OFFSET 1" in statement for statement in statements)
                assert any(
                    "SUM(" in statement and "GROUP BY" in statement for statement in statements
                )
            # Deferred GL evaluation cannot switch to default after context exit.
            with django_db_blocker.unblock():
                assert list(lazy_page)[0]._state.db == alias
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
        if admin is not None:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(config["NAME"])))
            admin.close()
