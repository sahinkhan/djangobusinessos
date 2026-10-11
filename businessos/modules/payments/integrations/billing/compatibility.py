"""Explicit installation/profile checks, not exception-based capability discovery."""

from django.apps import apps
from django.db import connections
from django.db.migrations.recorder import MigrationRecorder

from businessos.core.database import current_database_alias

EXPECTED_MIGRATIONS = frozenset({"0001_initial", "0002_register_manifest"})
EXPECTED_FIELDS = frozenset(
    {
        "id",
        "created_at",
        "updated_at",
        "company_id",
        "payment_id",
        "invoice_id",
        "amount",
        "idempotency_key",
    }
)
EXPECTED_CONSTRAINTS = frozenset(
    {
        "allocation_company_key_uniq",
        "allocation_amount_positive",
        "allocation_amount_range",
        "allocation_key_bounds",
    }
)
POSTGRES_CHECKS = {
    "allocation_amount_positive": "CHECK ((amount > (0)::numeric))",
    "allocation_amount_range": ("CHECK ((amount < '1000000000000000000000000000000'::numeric))"),
    "allocation_key_bounds": (
        "CHECK (((length(TRIM(BOTH FROM idempotency_key)) > 0) AND "
        "(length((idempotency_key)::text) <= 128) AND "
        r"((idempotency_key)::text ~ '\S'::text)))"
    ),
}

# Only relations read by the financial basis/completeness proof (plus its
# migration coverage and Company provenance). Resolve their actual identities
# on this connection; do not assume public or compare unqualified FK names.
FINANCIAL_RELATIONS = (
    ("payments_billing", "PaymentAllocation"),
    ("payments", "Payment"),
    ("payments", "PaymentMethod"),
    ("billing", "Invoice"),
    ("billing", "InvoiceLine"),
    ("party", "Party"),
    ("reference", "Currency"),
    ("organization", "Company"),
)
# Django PROTECT is a Python deletion rule; the installed PostgreSQL backstop
# is a validated NO ACTION FK. These are the fixed edges used by this proof.
FINANCIAL_FOREIGN_KEYS = {
    "PaymentAllocation": {"company": "Company", "payment": "Payment", "invoice": "Invoice"},
    "Payment": {
        "company": "Company",
        "payer_party": "Party",
        "currency": "Currency",
        "payment_method": "PaymentMethod",
    },
    "Invoice": {"company": "Company", "bill_to_party": "Party", "currency": "Currency"},
    "InvoiceLine": {"company": "Company", "invoice": "Invoice"},
    "PaymentMethod": {"company": "Company"},
    "Party": {"company": "Company"},
}


def _postgres_financial_profile(cursor):
    models = {name: apps.get_model(app, name) for app, name in FINANCIAL_RELATIONS}
    tables = {name: model._meta.db_table for name, model in models.items()}
    tables["Migration"] = MigrationRecorder.Migration._meta.db_table
    cursor.execute(
        "SELECT rolsuper, rolbypassrls FROM pg_catalog.pg_roles WHERE rolname = current_user"
    )
    role = cursor.fetchone()
    if role is None:
        return "incompatible"
    unrestricted = any(role)
    identities = {}
    for name, table in tables.items():
        cursor.execute(
            "SELECT oid, relkind, relrowsecurity, relforcerowsecurity "
            "FROM pg_catalog.pg_class WHERE oid = pg_catalog.to_regclass(%s)",
            [table],
        )
        relation = cursor.fetchone()
        if relation is None:
            return "incomplete"
        oid, kind, rls, force_rls = relation
        if kind != "r" or ((rls or force_rls) and not unrestricted):
            return "incompatible"
        identities[name] = oid
    for source, edges in FINANCIAL_FOREIGN_KEYS.items():
        cursor.execute(
            "SELECT ARRAY(SELECT a.attname FROM unnest(c.conkey) WITH ORDINALITY k(num, pos) "
            "JOIN pg_catalog.pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.num "
            "ORDER BY k.pos), c.confrelid, "
            "ARRAY(SELECT a.attname FROM unnest(c.confkey) WITH ORDINALITY k(num, pos) "
            "JOIN pg_catalog.pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=k.num "
            "ORDER BY k.pos), c.confdeltype, c.convalidated "
            "FROM pg_catalog.pg_constraint c WHERE c.conrelid=%s AND c.contype='f'",
            [identities[source]],
        )
        constraints = list(cursor)
        for field, target in edges.items():
            expected = (
                [models[source]._meta.get_field(field).column],
                identities[target],
                [models[target]._meta.pk.column],
                "a",
                True,
            )
            matching = [row for row in constraints if row[0] == expected[0]]
            if matching != [expected]:
                return "incompatible"
    return None


def evidence_profile():
    if not apps.is_installed("businessos.modules.payments.integrations.billing"):
        return "not_installed"
    from businessos.modules.billing.selectors import FINANCIAL_BASIS_VERSION
    from businessos.modules.payments.selectors import RECEIPT_BASIS_VERSION

    from .domain import CONTRACT_VERSION
    from .models import PaymentAllocation

    if (CONTRACT_VERSION, FINANCIAL_BASIS_VERSION, RECEIPT_BASIS_VERSION) != (1, 1, 1):
        return "incompatible"
    connection = connections[current_database_alias()]
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            reason = _postgres_financial_profile(cursor)
            if reason:
                return reason
        tables = connection.introspection.table_names(cursor)
        if "django_migrations" not in tables:
            return "incomplete"
        applied = set(
            MigrationRecorder(connection)
            .migration_qs.filter(app="payments_billing")
            .values_list("name", flat=True)
        )
        if applied < EXPECTED_MIGRATIONS or not EXPECTED_MIGRATIONS <= applied:
            return "incomplete"
        if applied != EXPECTED_MIGRATIONS:
            return "incompatible"  # No unreviewed backfill/coverage promise.
        table = PaymentAllocation._meta.db_table
        if table not in tables:
            return "incomplete"
        columns = connection.introspection.get_table_description(cursor, table)
        if {column.name for column in columns} != EXPECTED_FIELDS:
            return "incompatible"
        if any(column.null_ok for column in columns):
            return "incompatible"
        constraints = connection.introspection.get_constraints(cursor, table)
        if not EXPECTED_CONSTRAINTS <= constraints.keys():
            return "incompatible"
        unique = constraints["allocation_company_key_uniq"]
        if not unique["unique"] or unique["columns"] != ["company_id", "idempotency_key"]:
            return "incompatible"
        for column, owner in (
            ("company_id", "organization_company"),
            ("payment_id", "payments_payment"),
            ("invoice_id", "billing_invoice"),
        ):
            if not any(
                constraint["columns"] == [column] and constraint["foreign_key"] == (owner, "id")
                for constraint in constraints.values()
            ):
                return "incompatible"
        if connection.vendor == "postgresql":
            amount = next(column for column in columns if column.name == "amount")
            if (amount.precision, amount.scale) != (38, 8):
                return "incompatible"
            cursor.execute(
                "SELECT conname, convalidated, pg_get_constraintdef(oid) "
                "FROM pg_constraint WHERE conrelid = to_regclass(%s) AND contype = 'c'",
                [table],
            )
            checks = {name: (validated, definition) for name, validated, definition in cursor}
            if any(
                checks.get(name) != (True, expected) for name, expected in POSTGRES_CHECKS.items()
            ):
                return "incompatible"
    return None
