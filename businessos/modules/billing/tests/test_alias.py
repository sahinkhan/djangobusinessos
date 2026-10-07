from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.migrations.executor import MigrationExecutor

from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import database_execution
from businessos.core.organization.models import Company
from businessos.core.reference.models import Country, Currency, Language
from businessos.modules.billing import selectors, services
from businessos.modules.billing.models import Invoice, InvoiceLine
from businessos.modules.party.models import Party


def test_billing_nondefault_alias_bootstrap_and_rollback(django_db_blocker, monkeypatch):
    alias = "billing_test_alias"
    config = dict(connections.databases["default"])
    config.update(ENGINE="django.db.backends.sqlite3", NAME=":memory:", OPTIONS={})
    connections.databases[alias] = config

    def forbidden(*args, **kwargs):
        pytest.fail("Billing used default instead of the selected database.")

    monkeypatch.setattr(connections["default"], "cursor", forbidden)
    try:
        with django_db_blocker.unblock(), database_execution(alias):
            executor = MigrationExecutor(connections[alias])
            executor.migrate(executor.loader.graph.leaf_nodes())
            currency = Currency.objects.create(code="AAA", name="Alias currency")
            country = Country.objects.create(code="US", name="US")
            language = Language.objects.create(code="EN", name="English")
            company = Company.objects.create(
                code="ALIAS",
                name="Alias",
                base_currency=currency,
                country=country,
                default_language=language,
            )
            actor = get_user_model().objects.create_superuser("alias@billing.test", "test-only")
            party = Party.objects.create(company=company, party_type="person", display_name="Alias")
            context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
            invoice = services.create_invoice(
                context, bill_to_party_id=party.pk, currency_id=currency.pk
            )
            line = services.add_invoice_line(
                context, invoice.pk, description="Service", quantity=1, unit_price=2
            )
            services.update_invoice(context, invoice.pk, notes="Alias only")
            services.update_invoice_line(context, invoice.pk, line.pk, quantity=3)
            assert selectors.invoice_total(context, invoice.pk) == 6
            before = AuditEntry.objects.count()
            with patch.object(services, "record_audit_entry", side_effect=RuntimeError("audit")):
                with pytest.raises(RuntimeError):
                    services.remove_invoice_line(context, invoice.pk, line.pk)
            assert InvoiceLine.objects.count() == 1 and AuditEntry.objects.count() == before
            issued = services.issue_invoice(context, invoice.pk)
            assert services.issue_invoice(context, invoice.pk).issued_at == issued.issued_at
            assert invoice._state.db == alias
            assert selectors.invoice_detail(context, invoice.pk)._state.db == alias
            assert Invoice.objects.count() == 1
            assert all(entry._state.db == alias for entry in AuditEntry.objects.all())
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
