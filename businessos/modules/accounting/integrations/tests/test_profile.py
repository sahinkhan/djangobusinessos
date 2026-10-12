from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import connection

from businessos.core.audit.models import AuditEntry
from businessos.modules.accounting.integrations.admission import admission
from businessos.modules.accounting.integrations.billing.selectors import invoice_posting_status
from businessos.modules.accounting.integrations.compatibility import admit_profile
from businessos.modules.accounting.integrations.schema_profile import BASELINE, BINDINGS
from businessos.modules.accounting.models import JournalEntry

from .test_outcomes import invoice_post

pytestmark = pytest.mark.django_db

FIXED = BASELINE | BINDINGS
CRITICAL_CONSTRAINTS = [
    (table, definition, kind)
    for table, facts in FIXED.items()
    for kind, definition, validated in facts["constraints"]
    if kind in {"f", "c"}
]


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL catalog, DDL, policies and real database roles.")


def unavailable(context, outcomes, invoice):
    before = AuditEntry.objects.count()
    result = invoice_posting_status(context, invoice.pk)
    assert result.state == "UNAVAILABLE" and result.reason == "incompatible"
    assert result.amount is None and result.binding_id is None
    with pytest.raises(ValidationError):
        invoice_post(context, outcomes, invoice)
    assert not JournalEntry.objects.exists()
    assert AuditEntry.objects.count() == before


@pytest.mark.parametrize("table,definition,kind", CRITICAL_CONSTRAINTS)
@pytest.mark.parametrize("drift", ["missing", "not_valid", "weakened"])
def test_every_fixed_fk_and_check(business_context, outcomes, table, definition, kind, drift):
    invoice, _, _ = outcomes["sources"]("1", None)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conrelid=to_regclass(%s) "
            "AND pg_get_constraintdef(oid,true)=%s",
            [f"public.{table}", definition],
        )
        (name,) = cursor.fetchone()
        cursor.execute(f'ALTER TABLE public."{table}" DROP CONSTRAINT "{name}"')
        if drift != "missing":
            replacement = definition
            if drift == "weakened":
                replacement = (
                    "CHECK (true)"
                    if kind == "c"
                    else definition.replace(" DEFERRABLE", " ON DELETE CASCADE DEFERRABLE")
                )
            else:
                replacement += " NOT VALID"
            cursor.execute(f'ALTER TABLE public."{table}" ADD CONSTRAINT "{name}" {replacement}')
    unavailable(business_context, outcomes, invoice)


@pytest.mark.parametrize("table", list(FIXED))
@pytest.mark.parametrize("mode", ["enabled", "forced", "disabled_policy"])
@pytest.mark.parametrize("privileged", [False, True])
def test_rls_and_policies_rejected_before_reads(
    business_context, outcomes, table, mode, privileged
):
    invoice, _, _ = outcomes["sources"]("1", None)
    role = "accint1_reader_" + uuid4().hex
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute(f'CREATE ROLE "{role}" NOSUPERUSER NOBYPASSRLS NOLOGIN')
        cursor.execute(f'GRANT USAGE ON SCHEMA public TO "{role}"')
        cursor.execute(f'GRANT ALL ON ALL TABLES IN SCHEMA public TO "{role}"')
        cursor.execute(f'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO "{role}"')
        cursor.execute(f'CREATE POLICY synthetic_hide ON public."{table}" USING (false)')
        if mode != "disabled_policy":
            cursor.execute(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY')
        if mode == "forced":
            cursor.execute(f'ALTER TABLE public."{table}" FORCE ROW LEVEL SECURITY')
        try:
            if not privileged:
                cursor.execute(f'SET LOCAL ROLE "{role}"')
                cursor.execute(
                    "SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user"
                )
                assert cursor.fetchone() == (False, False)
            # Even a privileged role must not certify a supported profile with policies.
            if table == "module_registry_businessmodule":
                # Registry is HTTP evidence only; Python APIs ignore enablement.
                with pytest.raises(ValidationError), admission(business_context, http=True):
                    pytest.fail("Unsupported HTTP registry evidence was admitted.")
            else:
                unavailable(business_context, outcomes, invoice)
        finally:
            cursor.execute("RESET ROLE")
            cursor.execute(f'DROP OWNED BY "{role}"')
            cursor.execute(f'DROP ROLE "{role}"')


@pytest.mark.parametrize(
    "table",
    [
        "django_migrations",
        "identity_user",
        "party_party",
        "billing_invoice",
        "billing_invoiceline",
        "accounting_journalentry",
        "accounting_billing_invoiceposting",
    ],
)
@pytest.mark.parametrize("mode", ["relocated", "shadow", "shadow_path", "relocated_rls", "view"])
def test_namespace_resolution_and_kind(business_context, outcomes, table, mode):
    invoice, _, _ = outcomes["sources"]("1", None)
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("CREATE SCHEMA pgx_review")
        if mode.startswith("relocated"):
            cursor.execute(f'ALTER TABLE public."{table}" SET SCHEMA pgx_review')
            if mode == "relocated_rls":
                cursor.execute(f'ALTER TABLE pgx_review."{table}" ENABLE ROW LEVEL SECURITY')
                cursor.execute(f'CREATE POLICY hidden_subtree ON pgx_review."{table}" USING(false)')
                role = "accint1_reader_" + uuid4().hex
                cursor.execute(f'CREATE ROLE "{role}" NOSUPERUSER NOBYPASSRLS NOLOGIN')
                cursor.execute(f'GRANT USAGE ON SCHEMA public,pgx_review TO "{role}"')
                cursor.execute(f'GRANT ALL ON ALL TABLES IN SCHEMA public,pgx_review TO "{role}"')
                cursor.execute(f'SET LOCAL ROLE "{role}"')
            cursor.execute("SET LOCAL search_path=pgx_review,public")
        elif mode.startswith("shadow"):
            cursor.execute(
                f'CREATE TABLE pgx_review."{table}" (LIKE public."{table}" INCLUDING ALL)'
            )
            if mode == "shadow_path":
                cursor.execute("SET LOCAL search_path=pgx_review,public")
        else:
            cursor.execute(f'ALTER TABLE public."{table}" RENAME TO "saved_{table}"')
            cursor.execute(f'CREATE VIEW public."{table}" AS SELECT * FROM public."saved_{table}"')
        try:
            result = invoice_posting_status(business_context, invoice.pk)
            assert result.state == "UNAVAILABLE" and result.amount is None
        finally:
            cursor.execute("RESET ROLE")
            if mode == "relocated_rls":
                cursor.execute(f'DROP OWNED BY "{role}"')
                cursor.execute(f'DROP ROLE "{role}"')


def test_unknown_migration_not_known_absence(business_context, outcomes):
    invoice, _, _ = outcomes["sources"]("1", None)
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO django_migrations(app,name,applied) VALUES "
            "('billing','9999_unreviewed',CURRENT_TIMESTAMP)"
        )
    unavailable(business_context, outcomes, invoice)


def test_pinned_profile_admits_clean_baseline():
    admit_profile(allocation=True, http=True)
