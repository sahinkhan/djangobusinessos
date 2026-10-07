from unittest.mock import patch
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import database_execution
from businessos.core.organization.models import Company
from businessos.core.reference.models import Country, Currency, Language
from businessos.modules.party.models import Party
from businessos.modules.payments import selectors, services
from businessos.modules.payments.models import Payment


def test_selected_alias_bootstrap_lifecycle_rollback(django_db_blocker, monkeypatch):
    """Use a real additional PostgreSQL database in PG runs, SQLite otherwise."""
    alias = "payments_verification_alias"
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
        config["NAME"] = "pay1_alias_" + uuid4().hex
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(config["NAME"])))
    else:
        config.update(NAME=":memory:", OPTIONS={})
    connections.databases[alias] = config
    statements = []

    def trace(execute, sql, params, many, context):
        statements.append(sql)
        return execute(sql, params, many, context)

    def forbidden(*args, **kwargs):
        pytest.fail("Payments accessed default while another alias was selected.")

    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(connections["default"], "cursor", forbidden)
            with django_db_blocker.unblock(), database_execution(alias):
                executor = MigrationExecutor(connections[alias])
                executor.migrate(executor.loader.graph.leaf_nodes())
                currency = Currency.objects.create(code="AAA", name="Alias")
                country = Country.objects.create(code="US", name="US")
                language = Language.objects.create(code="EN", name="English")
                company = Company.objects.create(
                    code="ALIAS",
                    name="Alias",
                    base_currency=currency,
                    country=country,
                    default_language=language,
                )
                actor = get_user_model().objects.create_superuser(
                    "alias@payments.test", "test-only"
                )
                context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
                payer = Party.objects.create(
                    company=company, party_type="person", display_name="Alias"
                )
                with connections[alias].execute_wrapper(trace):
                    method = services.create_payment_method(context, code="CASH", name="Cash")
                    services.update_payment_method(
                        context, payment_method_id=method.pk, name="Cash 2"
                    )
                    payload = dict(
                        payer_party_id=payer.pk,
                        currency_id=currency.pk,
                        amount="2",
                        payment_method_id=method.pk,
                        idempotency_key="key",
                    )
                    receipt = services.record_payment(context, **payload)
                    services.set_payment_method_active(
                        context, payment_method_id=method.pk, is_active=False
                    )
                    assert services.record_payment(context, **payload).pk == receipt.pk
                    before = AuditEntry.objects.count()
                    with patch.object(
                        services, "record_audit_entry", side_effect=RuntimeError("audit")
                    ):
                        with pytest.raises(RuntimeError):
                            services.set_payment_method_active(
                                context, payment_method_id=method.pk, is_active=True
                            )
                    method.refresh_from_db()
                    assert not method.is_active and AuditEntry.objects.count() == before
                    assert selectors.payment_detail(context, receipt.pk)._state.db == alias
                    assert Payment.objects.count() == 1
                    assert all(entry._state.db == alias for entry in AuditEntry.objects.all())
                if postgres:
                    assert any("FOR UPDATE" in sql for sql in statements)
                assert any("SAVEPOINT" in sql for sql in statements)
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
        if admin is not None:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(config["NAME"])))
            admin.close()
