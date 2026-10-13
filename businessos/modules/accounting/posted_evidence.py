"""Owner-local evidence admission pinned to canonical 4419bdc4 migrations.

No optional-integration imports. Only this certificate's financial/provenance
relations participate; unrelated module policies do not affect the owner API.
"""

import json

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import connections
from django.db.migrations.recorder import MigrationRecorder

from businessos.core.database import current_database_alias

MODELS = {
    "Entry": ("accounting", "JournalEntry"),
    "Line": ("accounting", "JournalEntryLine"),
    "Journal": ("accounting", "Journal"),
    "Account": ("accounting", "Account"),
    "Company": ("organization", "Company"),
    "Party": ("party", "Party"),
    "Currency": ("reference", "Currency"),
}

FOREIGN_KEYS = {
    "Entry": {"company": "Company", "journal": "Journal"},
    "Line": {
        "company": "Company",
        "journal_entry": "Entry",
        "account": "Account",
        "party": "Party",
    },
    "Journal": {"company": "Company"},
    "Account": {"company": "Company"},
    "Company": {"base_currency": "Currency"},
    "Party": {"company": "Company"},
}

HEADS = {
    "accounting": ("0001_initial", "0002_register_manifest"),
    "organization": ("0001_initial",),
    "party": ("0001_initial", "0002_register_manifest"),
    "reference": ("0001_initial",),
}

SCHEMA = {
    "accounting_journalentry": {
        "columns": [
            ["id", "uuid", True],
            ["created_at", "timestamp with time zone", True],
            ["updated_at", "timestamp with time zone", True],
            ["number", "character varying(35)", True],
            ["entry_date", "date", True],
            ["memo", "text", True],
            ["status", "character varying(6)", True],
            ["base_currency_code_snapshot", "character varying(3)", True],
            ["base_currency_precision_snapshot", "smallint", True],
            ["posted_at", "timestamp with time zone", False],
            ["company_id", "uuid", True],
            ["journal_id", "uuid", True],
        ],
        "constraints": [
            [
                "c",
                "CHECK (base_currency_precision_snapshot >= 0 AND "
                "base_currency_precision_snapshot <= 8)",
                True,
            ],
            ["c", "CHECK (base_currency_precision_snapshot >= 0)", True],
            [
                "c",
                "CHECK (posted_at IS NULL AND status::text = "
                "'DRAFT'::text OR posted_at IS NOT NULL AND "
                "status::text = 'POSTED'::text)",
                True,
            ],
            ["p", "PRIMARY KEY (id)", True],
            ["u", "UNIQUE (company_id, number)", True],
        ],
    },
    "accounting_journalentryline": {
        "columns": [
            ["id", "uuid", True],
            ["created_at", "timestamp with time zone", True],
            ["updated_at", "timestamp with time zone", True],
            ["description", "text", True],
            ["debit", "numeric(38,8)", True],
            ["credit", "numeric(38,8)", True],
            ["position", "integer", True],
            ["account_id", "uuid", True],
            ["company_id", "uuid", True],
            ["journal_entry_id", "uuid", True],
            ["party_id", "uuid", False],
        ],
        "constraints": [
            ["c", 'CHECK ("position" > 0 AND "position" <= 2147483647)', True],
            ["c", 'CHECK ("position" >= 0)', True],
            [
                "c",
                "CHECK (credit = 0::numeric AND debit > "
                "0::numeric OR credit > 0::numeric AND debit = "
                "0::numeric)",
                True,
            ],
            [
                "c",
                "CHECK (credit >= 0::numeric AND credit < "
                "'1000000000000000000000000000000'::numeric AND "
                "debit >= 0::numeric AND debit < "
                "'1000000000000000000000000000000'::numeric)",
                True,
            ],
            ["p", "PRIMARY KEY (id)", True],
            ["u", 'UNIQUE (journal_entry_id, "position")', True],
        ],
    },
    "accounting_journal": {
        "columns": [
            ["id", "uuid", True],
            ["created_at", "timestamp with time zone", True],
            ["updated_at", "timestamp with time zone", True],
            ["code", "character varying(32)", True],
            ["name", "character varying(160)", True],
            ["is_active", "boolean", True],
            ["company_id", "uuid", True],
        ],
        "constraints": [["p", "PRIMARY KEY (id)", True], ["u", "UNIQUE (company_id, code)", True]],
    },
    "accounting_account": {
        "columns": [
            ["id", "uuid", True],
            ["created_at", "timestamp with time zone", True],
            ["updated_at", "timestamp with time zone", True],
            ["code", "character varying(32)", True],
            ["name", "character varying(160)", True],
            ["type", "character varying(9)", True],
            ["is_active", "boolean", True],
            ["company_id", "uuid", True],
        ],
        "constraints": [
            [
                "c",
                "CHECK (type::text = ANY (ARRAY['ASSET'::character "
                "varying, 'LIABILITY'::character varying, "
                "'EQUITY'::character varying, 'INCOME'::character "
                "varying, 'EXPENSE'::character varying]::text[]))",
                True,
            ],
            ["p", "PRIMARY KEY (id)", True],
            ["u", "UNIQUE (company_id, code)", True],
        ],
    },
    "organization_company": {
        "columns": [
            ["id", "uuid", True],
            ["created_at", "timestamp with time zone", True],
            ["updated_at", "timestamp with time zone", True],
            ["is_active", "boolean", True],
            ["code", "character varying(32)", True],
            ["name", "character varying(160)", True],
            ["timezone", "character varying(64)", True],
            ["base_currency_id", "uuid", True],
            ["country_id", "uuid", True],
            ["default_language_id", "uuid", True],
        ],
        "constraints": [["p", "PRIMARY KEY (id)", True], ["u", "UNIQUE (code)", True]],
    },
    "party_party": {
        "columns": [
            ["id", "uuid", True],
            ["created_at", "timestamp with time zone", True],
            ["updated_at", "timestamp with time zone", True],
            ["is_active", "boolean", True],
            ["party_type", "character varying(16)", True],
            ["display_name", "character varying(200)", True],
            ["legal_name", "character varying(200)", True],
            ["is_customer", "boolean", True],
            ["is_supplier", "boolean", True],
            ["company_id", "uuid", True],
        ],
        "constraints": [["p", "PRIMARY KEY (id)", True]],
    },
    "reference_currency": {
        "columns": [
            ["id", "uuid", True],
            ["created_at", "timestamp with time zone", True],
            ["updated_at", "timestamp with time zone", True],
            ["is_active", "boolean", True],
            ["name", "character varying(120)", True],
            ["code", "character varying(3)", True],
            ["symbol", "character varying(8)", True],
            ["decimal_places", "smallint", True],
        ],
        "constraints": [
            ["c", "CHECK (decimal_places >= 0)", True],
            ["p", "PRIMARY KEY (id)", True],
            ["u", "UNIQUE (code)", True],
        ],
    },
    "django_migrations": {
        "columns": [
            ["id", "bigint", True],
            ["app", "character varying(255)", True],
            ["name", "character varying(255)", True],
            ["applied", "timestamp with time zone", True],
        ],
        "constraints": [["p", "PRIMARY KEY (id)", True]],
    },
}

SQLITE = {
    "accounting_journalentry": 'CREATE TABLE "accounting_journalentry" ("id" char(32) NOT NULL '
    'PRIMARY KEY, "created_at" datetime NOT NULL, "updated_at" datetime '
    'NOT NULL, "number" varchar(35) NOT NULL, "entry_date" date NOT NULL, '
    '"memo" text NOT NULL, "status" varchar(6) NOT NULL, '
    '"base_currency_code_snapshot" varchar(3) NOT NULL, '
    '"base_currency_precision_snapshot" smallint unsigned NOT NULL CHECK '
    '("base_currency_precision_snapshot" >= 0), "posted_at" datetime NULL, '
    '"company_id" char(32) NOT NULL REFERENCES "organization_company" '
    '("id") DEFERRABLE INITIALLY DEFERRED, "journal_id" char(32) NOT NULL '
    'REFERENCES "accounting_journal" ("id") DEFERRABLE INITIALLY DEFERRED, '
    'CONSTRAINT "accounting_entry_number_uniq" UNIQUE ("company_id", '
    '"number"), CONSTRAINT "accounting_entry_lifecycle" CHECK '
    '((("posted_at" IS NULL AND "status" = \'DRAFT\') OR ("posted_at" IS '
    "NOT NULL AND \"status\" = 'POSTED'))), CONSTRAINT "
    '"accounting_entry_precision" CHECK '
    '(("base_currency_precision_snapshot" >= 0 AND '
    '"base_currency_precision_snapshot" <= 8)))',
    "accounting_journalentryline": 'CREATE TABLE "accounting_journalentryline" ("id" char(32) NOT '
    'NULL PRIMARY KEY, "created_at" datetime NOT NULL, "updated_at" '
    'datetime NOT NULL, "description" text NOT NULL, "debit" decimal '
    'NOT NULL, "credit" decimal NOT NULL, "position" integer unsigned '
    'NOT NULL CHECK ("position" >= 0), "account_id" char(32) NOT NULL '
    'REFERENCES "accounting_account" ("id") DEFERRABLE INITIALLY '
    'DEFERRED, "company_id" char(32) NOT NULL REFERENCES '
    '"organization_company" ("id") DEFERRABLE INITIALLY DEFERRED, '
    '"journal_entry_id" char(32) NOT NULL REFERENCES '
    '"accounting_journalentry" ("id") DEFERRABLE INITIALLY DEFERRED, '
    '"party_id" char(32) NULL REFERENCES "party_party" ("id") '
    "DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "
    '"accounting_line_position_uniq" UNIQUE ("journal_entry_id", '
    '"position"), CONSTRAINT "accounting_line_position" CHECK '
    '(("position" > 0 AND "position" <= 2147483647)), CONSTRAINT '
    '"accounting_line_amount_range" CHECK (("credit" >= \'0\' AND '
    '"credit" < \'1E+30\' AND "debit" >= \'0\' AND "debit" < '
    '\'1E+30\')), CONSTRAINT "accounting_line_sides" CHECK ((("credit" '
    "= '0' AND \"debit\" > '0') OR (\"credit\" > '0' AND \"debit\" = "
    "'0'))))",
    "accounting_journal": 'CREATE TABLE "accounting_journal" ("id" char(32) NOT NULL PRIMARY KEY, '
    '"created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "code" '
    'varchar(32) NOT NULL, "name" varchar(160) NOT NULL, "is_active" bool NOT '
    'NULL, "company_id" char(32) NOT NULL REFERENCES "organization_company" '
    '("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT '
    '"accounting_journal_code_uniq" UNIQUE ("company_id", "code"))',
    "accounting_account": 'CREATE TABLE "accounting_account" ("id" char(32) NOT NULL PRIMARY KEY, '
    '"created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "code" '
    'varchar(32) NOT NULL, "name" varchar(160) NOT NULL, "type" varchar(9) NOT '
    'NULL, "is_active" bool NOT NULL, "company_id" char(32) NOT NULL REFERENCES '
    '"organization_company" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT '
    '"accounting_account_code_uniq" UNIQUE ("company_id", "code"), CONSTRAINT '
    "\"accounting_account_type\" CHECK (\"type\" IN ('ASSET', 'LIABILITY', "
    "'EQUITY', 'INCOME', 'EXPENSE')))",
    "organization_company": 'CREATE TABLE "organization_company" '
    '("id" char(32) NOT NULL PRIMARY KEY, '
    '"created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, '
    '"is_active" bool NOT NULL, "code" varchar(32) NOT NULL UNIQUE, "name" '
    'varchar(160) NOT NULL, "timezone" varchar(64) NOT NULL, '
    '"base_currency_id" char(32) NOT NULL REFERENCES "reference_currency" '
    '("id") DEFERRABLE INITIALLY DEFERRED, "country_id" char(32) NOT NULL '
    'REFERENCES "reference_country" ("id") DEFERRABLE INITIALLY DEFERRED, '
    '"default_language_id" char(32) NOT NULL REFERENCES "reference_language" '
    '("id") DEFERRABLE INITIALLY DEFERRED)',
    "party_party": 'CREATE TABLE "party_party" ("id" char(32) NOT NULL PRIMARY KEY, "created_at" '
    'datetime NOT NULL, "updated_at" datetime NOT NULL, "is_active" bool NOT NULL, '
    '"party_type" varchar(16) NOT NULL, "display_name" varchar(200) NOT NULL, '
    '"legal_name" varchar(200) NOT NULL, "is_customer" bool NOT NULL, "is_supplier" '
    'bool NOT NULL, "company_id" char(32) NOT NULL REFERENCES "organization_company" '
    '("id") DEFERRABLE INITIALLY DEFERRED)',
    "reference_currency": 'CREATE TABLE "reference_currency" ("id" char(32) NOT NULL PRIMARY KEY, '
    '"created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, '
    '"is_active" bool NOT NULL, "name" varchar(120) NOT NULL, "code" varchar(3) '
    'NOT NULL UNIQUE, "symbol" varchar(8) NOT NULL, "decimal_places" smallint '
    'unsigned NOT NULL CHECK ("decimal_places" >= 0))',
    "django_migrations": 'CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY '
    'AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, '
    '"applied" datetime NOT NULL)',
}


def _reject():
    raise ValidationError(
        "Accounting posted evidence profile is incompatible.", code="incompatible"
    )


def _postgres(connection, cursor, tables, *, acquire):
    cursor.execute(
        """
        SELECT c.oid,c.relname,n.nspname,c.relkind,c.relrowsecurity,c.relforcerowsecurity,
               EXISTS(SELECT 1 FROM pg_catalog.pg_policy p WHERE p.polrelid=c.oid),
               pg_catalog.to_regclass(pg_catalog.quote_ident(c.relname))::oid,
               (SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(a.attname,
                   pg_catalog.format_type(a.atttypid,a.atttypmod),a.attnotnull) ORDER BY a.attnum)
                FROM pg_catalog.pg_attribute a WHERE a.attrelid=c.oid AND a.attnum>0
                     AND NOT a.attisdropped),
               (SELECT coalesce(pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(k.contype,
                   pg_catalog.pg_get_constraintdef(k.oid,true),k.convalidated)
                   ORDER BY k.contype,pg_catalog.pg_get_constraintdef(k.oid,true)), '[]'::jsonb)
                FROM pg_catalog.pg_constraint k WHERE k.conrelid=c.oid
                     AND k.contype IN ('p','u','c'))
        FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
        WHERE c.relname=ANY(%s) AND n.nspname NOT IN
              ('pg_catalog','information_schema','pg_toast')
        ORDER BY c.oid
        """,
        [list(tables.values())],
    )
    rows = cursor.fetchall()
    if len(rows) != len(tables):
        _reject()
    identities = {}
    for oid, name, schema, kind, rls, forced, policies, resolved, columns, constraints in rows:
        if name in identities or schema != "public" or kind != "r" or rls or forced or policies:
            _reject()
        identities[name] = oid
        facts = SCHEMA[name]
        columns = json.loads(columns) if isinstance(columns, str) else columns
        constraints = json.loads(constraints) if isinstance(constraints, str) else constraints
        if oid != resolved or columns != facts["columns"] or constraints != facts["constraints"]:
            _reject()
    cursor.execute(
        """
        SELECT k.conrelid,
               ARRAY(SELECT a.attname FROM pg_catalog.unnest(k.conkey) WITH ORDINALITY x(num,pos)
                     JOIN pg_catalog.pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=x.num
                     ORDER BY x.pos),
               k.confrelid,
               ARRAY(SELECT a.attname FROM pg_catalog.unnest(k.confkey) WITH ORDINALITY x(num,pos)
                     JOIN pg_catalog.pg_attribute a ON a.attrelid=k.confrelid AND a.attnum=x.num
                     ORDER BY x.pos),
               k.confdeltype,k.confupdtype,k.convalidated,k.condeferrable,k.condeferred
        FROM pg_catalog.pg_constraint k WHERE k.conrelid=ANY(%s) AND k.contype='f'
        """,
        [list(identities.values())],
    )
    foreign_keys = cursor.fetchall()
    for source, edges in FOREIGN_KEYS.items():
        model = apps.get_model(*MODELS[source])
        for field, target in edges.items():
            column = model._meta.get_field(field).column
            target_model = apps.get_model(*MODELS[target])
            expected = (
                identities[tables[source]],
                [column],
                identities[tables[target]],
                [target_model._meta.pk.column],
                "a",
                "a",
                True,
                True,
                True,
            )
            matching = [
                row for row in foreign_keys if row[0] == expected[0] and row[1] == expected[1]
            ]
            if matching != [expected]:
                _reject()
    if acquire:
        # Only actual identities already verified against the fixed approved profile.
        qualified = [
            connection.ops.quote_name(schema) + "." + connection.ops.quote_name(name)
            for _, name, schema, *_ in rows
        ]
        cursor.execute("LOCK TABLE " + ",".join(qualified) + " IN ACCESS SHARE MODE")
        _postgres(connection, cursor, tables, acquire=False)


def _sqlite(cursor, tables):
    cursor.execute("PRAGMA foreign_keys")
    if cursor.fetchone() != (1,):
        _reject()
    cursor.execute("PRAGMA database_list")
    if any(name not in {"main", "temp"} for _, name, _ in cursor.fetchall()):
        _reject()
    params = list(tables.values())
    placeholders = ",".join(["%s"] * len(params))
    cursor.execute(
        "SELECT name,sql FROM main.sqlite_master WHERE type='table' AND name IN ("
        + placeholders
        + ")",
        params,
    )
    actual = dict(cursor.fetchall())
    cursor.execute(
        "SELECT name FROM temp.sqlite_master WHERE name IN (" + placeholders + ")", params
    )
    if cursor.fetchone() is not None or any(actual.get(name) != SQLITE[name] for name in params):
        _reject()


def admit_owner_basis():
    """No financial reads, role changes or other database aliases in this admission.

    ACCESS SHARE stabilizes strong relation/constraint DDL until transaction end.
    Weaker policy, privilege and migration maintenance still requires operator drain.
    """
    connection = connections[current_database_alias()]
    if not connection.in_atomic_block:
        raise ValidationError("Owner evidence admission requires a selected-alias transaction.")
    tables = {name: apps.get_model(*identity)._meta.db_table for name, identity in MODELS.items()}
    tables["Migration"] = MigrationRecorder.Migration._meta.db_table
    if set(tables.values()) != set(SCHEMA):
        _reject()
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            _postgres(connection, cursor, tables, acquire=True)
            prefix = "public."
        elif connection.vendor == "sqlite":
            _sqlite(cursor, tables)
            prefix = "main."
        else:
            _reject()
        cursor.execute(
            "SELECT app,name FROM "
            + prefix
            + connection.ops.quote_name(tables["Migration"])
            + " WHERE app IN ("
            + ",".join(["%s"] * len(HEADS))
            + ")",
            list(HEADS),
        )
        applied = {app: [] for app in HEADS}
        for app, name in cursor.fetchall():
            applied[app].append(name)
        if any(sorted(applied[app]) != sorted(names) for app, names in HEADS.items()):
            _reject()
