"""ACC-INT-1 bounded schema/evidence admission, on the selected execution alias.

ACCESS SHARE serializes strong relation/constraint DDL, not policy/privilege
maintenance. Operators must freeze/drain weaker maintenance separately.
"""

import json
import re

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import connections

from businessos.core.database import current_database_alias

from .schema_profile import BASELINE, BINDINGS, SQLITE

PAYMENT_TABLES = {
    "payments_payment",
    "payments_paymentmethod",
    "payments_billing_paymentallocation",
    "accounting_payments_billing_allocationposting",
}
HEADS = {
    "identity": ("0001_initial",),
    "organization": ("0001_initial",),
    "reference": ("0001_initial",),
    "party": ("0001_initial", "0002_register_manifest"),
    "access": ("0001_initial", "0002_initial", "0003_register_core_permissions"),
    "business_audit": ("0001_initial", "0002_initial"),
    "module_registry": ("0001_initial",),
    "billing": ("0001_initial", "0002_register_manifest"),
    "accounting": ("0001_initial", "0002_register_manifest"),
    "accounting_billing": ("0001_initial", "0002_register_manifest"),
    "payments": ("0001_initial", "0002_register_manifest"),
    "payments_billing": ("0001_initial", "0002_register_manifest"),
    "accounting_payments_billing": ("0001_initial", "0002_register_manifest"),
}


def _reject():
    raise ValidationError("Accounting evidence profile is incompatible.", code="incompatible")


def _tables(allocation, http):
    # Cross-effect Entry reuse needs the other binding's proof when it is installed.
    allocation = allocation or apps.is_installed(
        "businessos.modules.accounting.integrations.payments_billing"
    )
    tables = BASELINE | BINDINGS
    return {
        name: facts
        for name, facts in tables.items()
        if (allocation or name not in PAYMENT_TABLES)
        and (http or name != "module_registry_businessmodule")
    }


def _postgres(cursor, expected, *, acquire):
    # Literal namespaces. pgx_review and other ordinary schemas are NOT system namespaces.
    cursor.execute(
        """
        SELECT c.oid, c.relname, n.nspname, c.relkind, c.relrowsecurity,
               c.relforcerowsecurity, EXISTS(SELECT 1 FROM pg_policy p WHERE p.polrelid=c.oid),
               to_regclass(quote_ident(c.relname))::oid,
               (SELECT jsonb_agg(jsonb_build_array(a.attname,
                   format_type(a.atttypid,a.atttypmod),a.attnotnull) ORDER BY a.attnum)
                FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attnum>0
                     AND NOT a.attisdropped),
               (SELECT coalesce(jsonb_agg(jsonb_build_array(k.contype,
                   pg_get_constraintdef(k.oid,true), k.convalidated)
                   ORDER BY k.contype,pg_get_constraintdef(k.oid,true)), '[]'::jsonb)
                FROM pg_constraint k WHERE k.conrelid=c.oid)
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE c.relname=ANY(%s) AND n.nspname NOT IN
              ('pg_catalog','information_schema','pg_toast')
        ORDER BY c.oid
        """,
        [list(expected)],
    )
    rows = cursor.fetchall()
    if len(rows) != len(expected):
        _reject()
    seen = set()
    for oid, name, schema, kind, rls, forced, policies, resolved, columns, constraints in rows:
        if name in seen or schema != "public" or kind != "r" or rls or forced or policies:
            _reject()
        seen.add(name)
        facts = expected[name]
        columns = json.loads(columns) if isinstance(columns, str) else columns
        constraints = json.loads(constraints) if isinstance(constraints, str) else constraints
        if oid != resolved or columns != facts["columns"] or constraints != facts["constraints"]:
            _reject()
    # One bounded catalog query, not one query per FK or payload row.
    cursor.execute(
        """
        SELECT pg_get_constraintdef(k.oid,true), n.nspname, c.relname,
               k.confdeltype,k.confupdtype,to_regclass(
                   format('public.%%I',c.relname))::oid=k.confrelid
        FROM pg_constraint k JOIN pg_class c ON c.oid=k.confrelid
        JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE k.conrelid=ANY(%s) AND k.contype='f'
        """,
        [[row[0] for row in rows]],
    )
    for definition, target_schema, target_name, delete, update, identity in cursor.fetchall():
        match = re.search(r"REFERENCES ([a-z_]+)\(", definition)
        if (
            not match
            or target_schema != "public"
            or target_name != match.group(1)
            or (delete, update) != ("a", "a")
            or not identity
        ):
            _reject()
    if acquire:
        # Names are fixed literals already matched to these OIDs, never user input.
        cursor.execute(
            "LOCK TABLE "
            + ",".join(f'public."{name}"' for _, name, *_ in rows)
            + " IN ACCESS SHARE MODE"
        )
        _postgres(cursor, expected, acquire=False)


def _sqlite(cursor, expected):
    cursor.execute("PRAGMA database_list")
    if any(name not in {"main", "temp"} for _, name, _ in cursor.fetchall()):
        _reject()
    cursor.execute("SELECT name,sql FROM main.sqlite_master WHERE type='table'")
    tables = dict(cursor.fetchall())
    cursor.execute("SELECT name FROM temp.sqlite_master WHERE type IN ('table','view')")
    if any(name in expected for (name,) in cursor.fetchall()):
        _reject()
    if any(tables.get(name) != SQLITE[name] for name in expected):
        _reject()


def admit_profile(*, allocation=False, http=False):
    connection = connections[current_database_alias()]
    if not connection.in_atomic_block:
        raise ValidationError("Evidence admission requires an outer selected-alias transaction.")
    expected = _tables(allocation, http)
    with connection.cursor() as cursor:
        if connection.vendor == "postgresql":
            _postgres(cursor, expected, acquire=True)
        elif connection.vendor == "sqlite":
            _sqlite(cursor, expected)
        else:
            _reject()
        # No MigrationLoader/unqualified application query before relation admission.
        heads = {
            app: names
            for app, names in HEADS.items()
            if not app.startswith("payments")
            and app != "accounting_payments_billing"
            or "payments_payment" in expected
        }
        cursor.execute(
            "SELECT app,name FROM django_migrations WHERE app IN ("
            + ",".join(["%s"] * len(heads))
            + ")",
            list(heads),
        )
        applied = {app: set() for app in heads}
        for app, name in cursor.fetchall():
            applied[app].add(name)
        if any(applied[app] != set(names) for app, names in heads.items()):
            _reject()
    from businessos.modules.accounting import selectors as accounting
    from businessos.modules.billing import selectors as billing

    if (
        billing.FINANCIAL_BASIS_VERSION,
        billing.ACCOUNTING_BASIS_VERSION,
        accounting.POSTED_BASIS_VERSION,
    ) != (1, 1, 1):
        _reject()
    if "payments_payment" in expected:
        from businessos.modules.payments import selectors as payments
        from businessos.modules.payments.integrations.billing import selectors as allocations

        if (payments.RECEIPT_BASIS_VERSION, allocations.ACCOUNTING_BASIS_VERSION) != (1, 1):
            _reject()
