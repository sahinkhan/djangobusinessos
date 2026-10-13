"""Direct owner certificates, independent of optional integration admission."""

from contextlib import contextmanager
from decimal import Decimal
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connections
from django.db.migrations.recorder import MigrationRecorder

from businessos.core.audit.models import AuditEntry
from businessos.core.database import current_database_alias
from businessos.core.organization.models import Company
from businessos.core.reference.models import Currency
from businessos.modules.accounting import services as accounting
from businessos.modules.accounting.models import Account, Journal, JournalEntry, JournalEntryLine
from businessos.modules.accounting.selectors import posted_journal_basis
from businessos.modules.billing import services as billing
from businessos.modules.billing.models import Invoice, InvoiceLine
from businessos.modules.billing.selectors import invoice_accounting_basis
from businessos.modules.party.models import Party

pytestmark = pytest.mark.django_db


@pytest.fixture
def direct_sources(business_context, outcomes, currency):
    return build_sources(business_context, outcomes, currency)


def build_sources(business_context, outcomes, currency):
    invoice = billing.create_invoice(
        business_context, bill_to_party_id=outcomes["party"].pk, currency_id=currency.pk
    )
    for amount in ("20.00", "21.37"):
        billing.add_invoice_line(
            business_context, invoice.pk, description="Synthetic", quantity="1", unit_price=amount
        )
    billing.issue_invoice(business_context, invoice.pk)
    entry = accounting.create_journal_entry(business_context, journal_id=outcomes["journal"].pk)
    for amount in ("41.37", "5.00"):
        accounting.add_journal_entry_line(
            business_context, entry.pk, account_id=outcomes["ar"].pk, debit=amount, credit="0"
        )
        accounting.add_journal_entry_line(
            business_context, entry.pk, account_id=outcomes["revenue"].pk, debit="0", credit=amount
        )
    accounting.post_journal_entry(business_context, entry.pk)
    valid = accounting.create_journal_entry(business_context, journal_id=outcomes["journal"].pk)
    accounting.add_journal_entry_line(
        business_context, valid.pk, account_id=outcomes["ar"].pk, debit="41.37", credit="0"
    )
    accounting.add_journal_entry_line(
        business_context, valid.pk, account_id=outcomes["revenue"].pk, debit="0", credit="41.37"
    )
    accounting.post_journal_entry(business_context, valid.pk)
    return {"invoice": invoice, "entry": entry, "valid_entry": valid}


@contextmanager
def reader_role(connection, kind="reader", *, owned_table=None):
    if kind == "superuser":
        with connection.cursor() as cursor:
            cursor.execute("SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname=current_user")
            assert cursor.fetchone() == (True,)
            yield cursor
        return
    role = "accint1_owner_reader_" + uuid4().hex
    quoted = connection.ops.quote_name(role)
    with connection.cursor() as cursor:
        bypass = "BYPASSRLS" if kind == "bypass" else "NOBYPASSRLS"
        cursor.execute(f"CREATE ROLE {quoted} NOSUPERUSER {bypass} NOLOGIN")
        cursor.execute(f"GRANT USAGE ON SCHEMA public TO {quoted}")
        cursor.execute(f"GRANT SELECT, UPDATE ON ALL TABLES IN SCHEMA public TO {quoted}")
        original_owner = None
        if owned_table:
            cursor.execute(
                "SELECT r.rolname FROM pg_catalog.pg_class c "
                "JOIN pg_catalog.pg_roles r ON r.oid=c.relowner "
                "WHERE c.oid=pg_catalog.to_regclass(%s)",
                ["public." + owned_table],
            )
            original_owner = cursor.fetchone()[0]
            cursor.execute(
                f"ALTER TABLE public.{connection.ops.quote_name(owned_table)} OWNER TO {quoted}"
            )
        try:
            cursor.execute(f"SET LOCAL ROLE {quoted}")
            cursor.execute(
                "SELECT rolsuper,rolbypassrls FROM pg_catalog.pg_roles WHERE rolname=current_user"
            )
            assert cursor.fetchone() == (False, kind == "bypass")
            yield cursor
        finally:
            cursor.execute("RESET ROLE")
            if original_owner:
                cursor.execute(
                    f"ALTER TABLE public.{connection.ops.quote_name(owned_table)} "
                    f"OWNER TO {connection.ops.quote_name(original_owner)}"
                )
            cursor.execute(f"DROP OWNED BY {quoted}")
            cursor.execute(f"DROP ROLE {quoted}")


@pytest.mark.parametrize("owner", ["billing", "accounting"])
def test_hidden_lines_cannot_be_directly_certified(business_context, direct_sources, owner):
    connection = connections[current_database_alias()]
    if connection.vendor != "postgresql":
        pytest.skip("Direct owner financial evidence requires actual PostgreSQL roles and RLS.")
    invoice, entry = direct_sources["invoice"], direct_sources["entry"]
    model = InvoiceLine if owner == "billing" else JournalEntryLine
    table = connection.ops.quote_name(model._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        parent = "invoice_id" if owner == "billing" else "journal_entry_id"
        identity = invoice.pk if owner == "billing" else entry.pk
        cursor.execute(f"SELECT count(*) FROM public.{table} WHERE {parent}=%s", [identity])
        assert cursor.fetchone()[0] == (2 if owner == "billing" else 4)
        if owner == "billing":
            cursor.execute(
                f"SELECT SUM(quantity*unit_price) FROM public.{table} WHERE {parent}=%s", [identity]
            )
            assert cursor.fetchone()[0] == Decimal("41.37")
            assert invoice_accounting_basis(business_context, invoice.pk).original_total == Decimal(
                "41.37"
            )
        else:
            cursor.execute(
                f"SELECT SUM(debit),SUM(credit) FROM public.{table} WHERE {parent}=%s", [identity]
            )
            assert cursor.fetchone() == (Decimal("46.37"), Decimal("46.37"))
            # ADR 0016 excludes complete manual four-line entries from this two-line API.
            with pytest.raises(ValidationError, match="exactly two"):
                posted_journal_basis(business_context, entry.pk)
        predicate = "position=1" if owner == "billing" else "position<=2"
        cursor.execute(f"CREATE POLICY owner_hide ON public.{table} USING ({predicate})")
        cursor.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
    with reader_role(connection) as cursor:
        cursor.execute(f"SELECT count(*) FROM public.{table} WHERE {parent}=%s", [identity])
        assert cursor.fetchone()[0] == (1 if owner == "billing" else 2)
        if owner == "billing":
            cursor.execute(
                f"SELECT SUM(quantity*unit_price) FROM public.{table} WHERE {parent}=%s", [identity]
            )
            assert cursor.fetchone()[0] == Decimal("20.00")
            with pytest.raises(ValidationError, match="evidence.*incompatible"):
                invoice_accounting_basis(business_context, invoice.pk)
        else:
            cursor.execute(
                f"SELECT SUM(debit),SUM(credit) FROM public.{table} WHERE {parent}=%s", [identity]
            )
            assert cursor.fetchone() == (Decimal("41.37"), Decimal("41.37"))
            with pytest.raises(ValidationError, match="evidence.*incompatible"):
                posted_journal_basis(business_context, entry.pk)


FINANCIAL_RELATIONS = [
    ("billing", model)
    for model in (Invoice, InvoiceLine, Company, Party, Currency, MigrationRecorder.Migration)
] + [
    ("accounting", model)
    for model in (
        JournalEntry,
        JournalEntryLine,
        Journal,
        Account,
        Company,
        Party,
        Currency,
        MigrationRecorder.Migration,
    )
]


def direct_basis(context, sources, owner):
    if owner == "billing":
        return invoice_accounting_basis(context, sources["invoice"].pk)
    return posted_journal_basis(context, sources["valid_entry"].pk)


def require_postgres():
    connection = connections[current_database_alias()]
    if connection.vendor != "postgresql":
        pytest.skip("Owner-local RLS/schema admission requires PostgreSQL catalog and roles.")
    return connection


@pytest.mark.parametrize("owner", ["billing", "accounting"])
@pytest.mark.parametrize("kind", ["reader", "bypass", "superuser", "owner"])
def test_supported_role_returns_complete_certificate(business_context, direct_sources, owner, kind):
    connection = require_postgres()
    model = InvoiceLine if owner == "billing" else JournalEntryLine
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
    before = AuditEntry.objects.count()
    with reader_role(
        connection, kind, owned_table=model._meta.db_table if kind == "owner" else None
    ):
        result = direct_basis(business_context, direct_sources, owner)
        if owner == "billing":
            assert result.original_total == Decimal("41.37")
        else:
            assert len(result.lines) == 2
            assert result.debit == result.credit == Decimal("41.37")
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("owner,model", FINANCIAL_RELATIONS)
@pytest.mark.parametrize("mode", ["enabled", "forced", "disabled_policy"])
def test_each_relevant_relation_policy_fails_closed(
    business_context, direct_sources, owner, model, mode
):
    connection = require_postgres()
    table = connection.ops.quote_name(model._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(f"CREATE POLICY owner_hide ON public.{table} USING(false)")
        if mode != "disabled_policy":
            cursor.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        if mode == "forced":
            cursor.execute(f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY")
    with reader_role(connection):
        with pytest.raises(ValidationError) as caught:
            direct_basis(business_context, direct_sources, owner)
        assert caught.value.code == "incompatible"


@pytest.mark.parametrize("owner", ["billing", "accounting"])
@pytest.mark.parametrize("kind", ["bypass", "superuser", "owner"])
@pytest.mark.parametrize("forced", [False, True])
def test_privilege_does_not_legalize_rls(business_context, direct_sources, owner, kind, forced):
    connection = require_postgres()
    model = InvoiceLine if owner == "billing" else JournalEntryLine
    table = connection.ops.quote_name(model._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(f"CREATE POLICY owner_hide ON public.{table} USING(false)")
        cursor.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        if forced:
            cursor.execute(f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY")
    with reader_role(
        connection, kind, owned_table=model._meta.db_table if kind == "owner" else None
    ):
        with pytest.raises(ValidationError) as caught:
            direct_basis(business_context, direct_sources, owner)
        assert caught.value.code == "incompatible"


@pytest.mark.parametrize("owner", ["billing", "accounting"])
def test_unrelated_catalog_rls_does_not_disable_owner(business_context, direct_sources, owner):
    connection = require_postgres()
    from businessos.modules.catalog.models import Product

    table = connection.ops.quote_name(Product._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(f"CREATE POLICY unrelated_hide ON public.{table} USING(false)")
        cursor.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        cursor.execute(f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY")
    with reader_role(connection):
        result = direct_basis(business_context, direct_sources, owner)
        assert (result.original_total if owner == "billing" else result.debit) == Decimal("41.37")


# Critical FK edges taken from the accepted owner migrations, not from the admission helper.
FOREIGN_KEYS = [
    ("billing", Invoice, "company"),
    ("billing", Invoice, "bill_to_party"),
    ("billing", Invoice, "currency"),
    ("billing", InvoiceLine, "company"),
    ("billing", InvoiceLine, "invoice"),
    ("billing", Company, "base_currency"),
    ("billing", Party, "company"),
    ("accounting", JournalEntry, "company"),
    ("accounting", JournalEntry, "journal"),
    ("accounting", JournalEntryLine, "company"),
    ("accounting", JournalEntryLine, "journal_entry"),
    ("accounting", JournalEntryLine, "account"),
    ("accounting", JournalEntryLine, "party"),
    ("accounting", Journal, "company"),
    ("accounting", Account, "company"),
    ("accounting", Company, "base_currency"),
    ("accounting", Party, "company"),
]


@pytest.mark.parametrize("owner,model,field", FOREIGN_KEYS)
@pytest.mark.parametrize("drift", ["missing", "not_valid", "weakened"])
def test_direct_owner_rejects_critical_fk_drift(
    business_context, direct_sources, owner, model, field, drift
):
    connection = require_postgres()
    table = connection.ops.quote_name(model._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(
            "SELECT k.conname,pg_catalog.pg_get_constraintdef(k.oid,true) "
            "FROM pg_catalog.pg_constraint k "
            "WHERE k.conrelid=pg_catalog.to_regclass(%s) AND k.contype='f' "
            "AND ARRAY(SELECT a.attname FROM pg_catalog.unnest(k.conkey) WITH ORDINALITY x(n,p) "
            "JOIN pg_catalog.pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=x.n "
            "ORDER BY x.p)=%s::name[]",
            ["public." + model._meta.db_table, [model._meta.get_field(field).column]],
        )
        name, definition = cursor.fetchone()
        quoted = connection.ops.quote_name(name)
        cursor.execute(f"ALTER TABLE public.{table} DROP CONSTRAINT {quoted}")
        if drift != "missing":
            definition = (
                definition + " NOT VALID"
                if drift == "not_valid"
                else definition.replace(" DEFERRABLE", " ON DELETE CASCADE DEFERRABLE")
            )
            cursor.execute(f"ALTER TABLE public.{table} ADD CONSTRAINT {quoted} {definition}")
    with pytest.raises(ValidationError) as caught:
        direct_basis(business_context, direct_sources, owner)
    assert caught.value.code == "incompatible"


@pytest.mark.parametrize("owner", ["billing", "accounting"])
def test_direct_owner_nondefault_alias(django_db_blocker, monkeypatch, owner):
    import psycopg
    from django.contrib.auth import get_user_model
    from django.db.migrations.executor import MigrationExecutor
    from psycopg import sql

    from businessos.core.common.context import BusinessContext
    from businessos.core.database import business_atomic_context, database_execution
    from businessos.core.reference.models import Country, Language

    config = dict(connections.databases[current_database_alias()])
    if config["ENGINE"] != "django.db.backends.postgresql":
        pytest.skip("Fresh direct owner PostgreSQL alias with RLS and default-cursor trap.")
    alias = "accint1_owner_alias"
    name = "accint1_owner_alias_" + uuid4().hex
    admin = psycopg.connect(
        dbname="postgres",
        user=config["USER"],
        password=config["PASSWORD"],
        host=config["HOST"],
        port=config["PORT"],
        autocommit=True,
    )
    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    config["NAME"] = name
    connections.databases[alias] = config

    def forbidden(*args, **kwargs):
        pytest.fail("Direct owner admission attempted the default cursor.")

    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(connections["default"], "cursor", forbidden)
            with django_db_blocker.unblock(), database_execution(alias):
                connection = connections[alias]
                executor = MigrationExecutor(connection)
                executor.migrate(executor.loader.graph.leaf_nodes())
                currency = Currency.objects.create(code="USD", name="Synthetic")
                company = Company.objects.create(
                    code="OWNER",
                    name="Synthetic owner",
                    base_currency=currency,
                    country=Country.objects.create(code="US", name="US"),
                    default_language=Language.objects.create(code="EN", name="English"),
                )
                actor = get_user_model().objects.create_superuser(
                    "owner@synthetic.test", "test-only"
                )
                context = BusinessContext(actor_id=actor.pk, company_id=company.pk)
                party = Party.objects.create(
                    company=company, party_type="person", display_name="Synthetic"
                )
                choices = {
                    "party": party,
                    "journal": accounting.create_journal(context, code="GEN", name="General"),
                    "ar": accounting.create_account(context, code="AR", name="AR", type="ASSET"),
                    "revenue": accounting.create_account(
                        context, code="REV", name="Revenue", type="INCOME"
                    ),
                }
                sources = build_sources(context, choices, currency)
                with business_atomic_context():
                    with reader_role(connection):
                        result = direct_basis(context, sources, owner)
                        assert (
                            result.original_total if owner == "billing" else result.debit
                        ) == Decimal("41.37")
                    table = connection.ops.quote_name(
                        (InvoiceLine if owner == "billing" else JournalEntryLine)._meta.db_table
                    )
                    predicate = "position=1" if owner == "billing" else "position<=2"
                    with connection.cursor() as cursor:
                        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                        cursor.execute(
                            f"CREATE POLICY alias_hide ON public.{table} USING({predicate})"
                        )
                        cursor.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
                    with reader_role(connection):
                        with pytest.raises(ValidationError) as caught:
                            if owner == "billing":
                                invoice_accounting_basis(context, sources["invoice"].pk)
                            else:
                                posted_journal_basis(context, sources["entry"].pk)
                        assert caught.value.code == "incompatible"
    finally:
        connections[alias].close()
        del connections[alias]
        del connections.databases[alias]
        admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
        admin.close()


@pytest.mark.parametrize(
    "owner,model",
    [
        ("billing", Invoice),
        ("billing", InvoiceLine),
        ("billing", MigrationRecorder.Migration),
        ("accounting", JournalEntry),
        ("accounting", JournalEntryLine),
        ("accounting", MigrationRecorder.Migration),
    ],
)
@pytest.mark.parametrize("drift", ["relocated", "shadow_path", "view", "column"])
def test_direct_owner_relation_identity_and_shape(
    business_context, direct_sources, owner, model, drift
):
    connection = require_postgres()
    table = connection.ops.quote_name(model._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("CREATE SCHEMA owner_probe")
        if drift == "relocated":
            cursor.execute(f"ALTER TABLE public.{table} SET SCHEMA owner_probe")
            cursor.execute("SET LOCAL search_path=owner_probe,public")
        elif drift == "shadow_path":
            cursor.execute(f"CREATE TABLE owner_probe.{table} (LIKE public.{table} INCLUDING ALL)")
            cursor.execute("SET LOCAL search_path=owner_probe,public")
        elif drift == "view":
            saved = connection.ops.quote_name("saved_" + model._meta.db_table)
            cursor.execute(f"ALTER TABLE public.{table} RENAME TO {saved}")
            cursor.execute(f"CREATE VIEW public.{table} AS SELECT * FROM public.{saved}")
        else:
            cursor.execute(f"ALTER TABLE public.{table} ADD COLUMN unreviewed integer")
    with pytest.raises(ValidationError) as caught:
        direct_basis(business_context, direct_sources, owner)
    assert caught.value.code == "incompatible"


@pytest.mark.parametrize("owner", ["billing", "accounting"])
@pytest.mark.parametrize("app", ["owner", "organization", "party", "reference"])
@pytest.mark.parametrize("drift", ["unknown", "missing", "duplicate"])
def test_direct_owner_migration_provenance(business_context, direct_sources, owner, app, drift):
    connection = require_postgres()
    app = owner if app == "owner" else app
    with connection.cursor() as cursor:
        if drift == "unknown":
            cursor.execute(
                "INSERT INTO public.django_migrations(app,name,applied) "
                "VALUES(%s,'9999_unreviewed',CURRENT_TIMESTAMP)",
                [app],
            )
        elif drift == "missing":
            cursor.execute("DELETE FROM public.django_migrations WHERE app=%s", [app])
        else:
            cursor.execute(
                "INSERT INTO public.django_migrations(app,name,applied) "
                "VALUES(%s,'0001_initial',CURRENT_TIMESTAMP)",
                [app],
            )
    with pytest.raises(ValidationError) as caught:
        direct_basis(business_context, direct_sources, owner)
    assert caught.value.code == "incompatible"


@pytest.mark.parametrize("owner", ["billing", "accounting"])
def test_other_owner_migration_does_not_disable_certificate(
    business_context, direct_sources, owner
):
    connection = require_postgres()
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO public.django_migrations(app,name,applied) "
            "VALUES(%s,'9999_unrelated',CURRENT_TIMESTAMP)",
            ["accounting" if owner == "billing" else "billing"],
        )
    result = direct_basis(business_context, direct_sources, owner)
    assert (result.original_total if owner == "billing" else result.debit) == Decimal("41.37")


# Fixed CHECK definitions from canonical owner migration SQL, independent of the new helpers.
CHECKS = [
    ("billing", Invoice, "CHECK (currency_decimal_places_snapshot <= 8)"),
    ("billing", Invoice, "CHECK (currency_decimal_places_snapshot >= 0)"),
    ("billing", Invoice, "CHECK (due_date IS NULL OR due_date >= invoice_date)"),
    (
        "billing",
        Invoice,
        (
            "CHECK (issued_at IS NULL AND status::text = 'draft'::text OR issued_at IS "
            "NOT NULL AND status::text = 'issued'::text)"
        ),
    ),
    ("billing", InvoiceLine, 'CHECK ("position" > 0)'),
    ("billing", InvoiceLine, 'CHECK ("position" >= 0)'),
    ("billing", InvoiceLine, "CHECK (quantity > 0::numeric)"),
    ("billing", InvoiceLine, "CHECK (unit_price >= 0::numeric)"),
    ("billing", Currency, "CHECK (decimal_places >= 0)"),
    (
        "accounting",
        JournalEntry,
        "CHECK (base_currency_precision_snapshot >= 0 AND base_currency_precision_snapshot <= 8)",
    ),
    ("accounting", JournalEntry, "CHECK (base_currency_precision_snapshot >= 0)"),
    (
        "accounting",
        JournalEntry,
        (
            "CHECK (posted_at IS NULL AND status::text = 'DRAFT'::text OR posted_at IS "
            "NOT NULL AND status::text = 'POSTED'::text)"
        ),
    ),
    ("accounting", JournalEntryLine, 'CHECK ("position" > 0 AND "position" <= 2147483647)'),
    ("accounting", JournalEntryLine, 'CHECK ("position" >= 0)'),
    (
        "accounting",
        JournalEntryLine,
        (
            "CHECK (credit = 0::numeric AND debit > 0::numeric OR credit > 0::numeric "
            "AND debit = 0::numeric)"
        ),
    ),
    (
        "accounting",
        JournalEntryLine,
        (
            "CHECK (credit >= 0::numeric AND credit < "
            "'1000000000000000000000000000000'::numeric AND debit >= 0::numeric AND "
            "debit < '1000000000000000000000000000000'::numeric)"
        ),
    ),
    (
        "accounting",
        Account,
        (
            "CHECK (type::text = ANY (ARRAY['ASSET'::character varying, "
            "'LIABILITY'::character varying, 'EQUITY'::character varying, "
            "'INCOME'::character varying, 'EXPENSE'::character varying]::text[]))"
        ),
    ),
    ("accounting", Currency, "CHECK (decimal_places >= 0)"),
]


@pytest.mark.parametrize("owner,model,definition", CHECKS)
@pytest.mark.parametrize("drift", ["missing", "not_valid", "weakened"])
def test_direct_owner_rejects_critical_check_drift(
    business_context, direct_sources, owner, model, definition, drift
):
    connection = require_postgres()
    table = connection.ops.quote_name(model._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(
            "SELECT conname FROM pg_catalog.pg_constraint "
            "WHERE conrelid=pg_catalog.to_regclass(%s) AND contype='c' "
            "AND pg_catalog.pg_get_constraintdef(oid,true)=%s",
            ["public." + model._meta.db_table, definition],
        )
        (name,) = cursor.fetchone()
        quoted = connection.ops.quote_name(name)
        cursor.execute(f"ALTER TABLE public.{table} DROP CONSTRAINT {quoted}")
        if drift != "missing":
            replacement = definition + " NOT VALID" if drift == "not_valid" else "CHECK (true)"
            cursor.execute(f"ALTER TABLE public.{table} ADD CONSTRAINT {quoted} {replacement}")
    with pytest.raises(ValidationError) as caught:
        direct_basis(business_context, direct_sources, owner)
    assert caught.value.code == "incompatible"


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("owner", ["billing", "accounting"])
def test_direct_owner_proof_stabilizes_strong_ddl(business_context, direct_sources, owner):
    connection = require_postgres()
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from businessos.core.database import business_atomic_context

    from .test_concurrency import blocked, worker

    model = InvoiceLine if owner == "billing" else JournalEntryLine
    table = connection.ops.quote_name(model._meta.db_table)

    def ddl():
        with connections[current_database_alias()].cursor() as cursor:
            cursor.execute(f"ALTER TABLE public.{table} ADD COLUMN owner_drift integer")

    read_ready, ddl_ready = Event(), Event()
    read_pid, ddl_pid = [], []
    with ThreadPoolExecutor(max_workers=2) as pool:
        with business_atomic_context():
            Company.objects.select_for_update().get(pk=business_context.company_id)
            reader = pool.submit(
                worker,
                lambda: direct_basis(business_context, direct_sources, owner),
                read_ready,
                read_pid,
            )
            assert read_ready.wait(12)
            blocked(read_pid[0])  # Waiting at Company, before reading any financial rows.
            change = pool.submit(worker, ddl, ddl_ready, ddl_pid)
            assert ddl_ready.wait(12)
            blocked(ddl_pid[0], holder=read_pid[0])
        result = reader.result(25)
        change.result(25)
    assert (result.original_total if owner == "billing" else result.debit) == Decimal("41.37")
    try:
        with pytest.raises(ValidationError) as caught:
            direct_basis(business_context, direct_sources, owner)
        assert caught.value.code == "incompatible"
    finally:
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE public.{table} DROP COLUMN owner_drift")
