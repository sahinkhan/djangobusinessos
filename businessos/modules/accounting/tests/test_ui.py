from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import RolePermission, UserCompanyAccess
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company
from businessos.modules.accounting import selectors, services
from businessos.modules.accounting.models import Account, Journal, JournalEntry

pytestmark = pytest.mark.django_db


@pytest.fixture
def logged(client, operator, company, accounting_role):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.pk)
    session.save()
    BusinessModule.objects.filter(code="accounting").update(is_enabled=True)
    return client


def routes(account, journal, balanced):
    entry, line = balanced.pk, balanced.lines.first().pk
    return {
        "accounts": ({}, "accounting.account.view"),
        "account_create": ({}, "accounting.account.manage"),
        "account_edit": ({"reference_id": account.pk}, "accounting.account.manage"),
        "journals": ({}, "accounting.journal.view"),
        "journal_create": ({}, "accounting.journal.manage"),
        "journal_edit": ({"reference_id": journal.pk}, "accounting.journal.manage"),
        "list": ({}, "accounting.entry.view"),
        "detail": ({"entry_id": entry}, "accounting.entry.view"),
        "create": ({}, "accounting.entry.create"),
        "edit": ({"entry_id": entry}, "accounting.entry.update"),
        "line_add": ({"entry_id": entry}, "accounting.entry.update"),
        "line_edit": ({"entry_id": entry, "line_id": line}, "accounting.entry.update"),
        "line_remove": ({"entry_id": entry, "line_id": line}, "accounting.entry.update"),
        "post": ({"entry_id": entry}, "accounting.entry.post"),
        "gl": ({}, "accounting.entry.view"),
        "tb": ({}, "accounting.entry.view"),
    }


@pytest.mark.parametrize(
    "name",
    [
        "accounts",
        "account_create",
        "account_edit",
        "journals",
        "journal_create",
        "journal_edit",
        "list",
        "detail",
        "create",
        "edit",
        "line_add",
        "line_edit",
        "post",
        "gl",
        "tb",
    ],
)
def test_action_get_permissions(logged, account, journal, balanced, accounting_role, name):
    args, permission = routes(account, journal, balanced)[name]
    url = reverse("accounting:" + name, kwargs=args)
    before = AuditEntry.objects.count()
    assert logged.get(url).status_code == 200
    assert AuditEntry.objects.count() == before
    RolePermission.objects.filter(role=accounting_role, permission__code=permission).delete()
    assert logged.get(url).status_code == 403
    assert logged.post(url, {}).status_code in {403, 405}


@pytest.mark.parametrize("registry", ["missing", "disabled"])
def test_gating_all_routes_and_installed_services(
    logged, account, journal, balanced, registry, business_context
):
    if registry == "missing":
        BusinessModule.objects.filter(code="accounting").delete()
    else:
        BusinessModule.objects.filter(code="accounting").update(is_enabled=False)
    for name, (args, _) in routes(account, journal, balanced).items():
        url = reverse("accounting:" + name, kwargs=args)
        assert logged.get(url).status_code == 404
        assert logged.post(url, {}).status_code == 404
    assert b'data-nav-root="/accounting/"' not in logged.get("/").content
    assert services.post_journal_entry(business_context, balanced.pk).status == "POSTED"


def test_navigation_permission_and_get_remove(logged, account, journal, balanced, accounting_role):
    assert b'data-nav-root="/accounting/"' in logged.get("/").content
    url = reverse(
        "accounting:line_remove",
        kwargs={"entry_id": balanced.pk, "line_id": balanced.lines.first().pk},
    )
    assert logged.get(url).status_code == 405
    RolePermission.objects.filter(role=accounting_role).delete()
    assert b'data-nav-root="/accounting/"' not in logged.get("/").content


@pytest.mark.parametrize(
    "name",
    [
        "account_create",
        "account_edit",
        "journal_create",
        "journal_edit",
        "create",
        "edit",
        "line_add",
        "line_edit",
        "line_remove",
        "post",
    ],
)
def test_stale_company_http_matrix(logged, account, journal, balanced, company, operator, name):
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=company.base_currency,
        country=company.country,
        default_language=company.default_language,
    )
    UserCompanyAccess.objects.create(user=operator, company=other)
    args, _ = routes(account, journal, balanced)[name]
    url = reverse("accounting:" + name, kwargs=args)
    data = dict(
        scope_company_id=str(other.pk),
        code="OTHER",
        name="Other",
        type="ASSET",
        is_active="true",
        journal=str(journal.pk),
        entry_date="2026-10-11",
        memo="No",
        account=str(account.pk),
        party="",
        debit="1",
        credit="0",
        description="No",
    )
    before = [list(m.objects.values()) for m in (Account, Journal, JournalEntry, AuditEntry)]
    assert logged.post(url, data).status_code in {200, 400}
    assert [
        list(m.objects.values()) for m in (Account, Journal, JournalEntry, AuditEntry)
    ] == before
    # Actual session switch: old company's identities must now be inaccessible.
    session = logged.session
    session[SESSION_COMPANY_KEY] = str(other.pk)
    session.save()
    assert logged.post(url, data | {"scope_company_id": str(company.pk)}).status_code == 403


def test_mutations_do_not_require_view_permission(
    logged, business_context, account, journal, accounting_role
):
    RolePermission.objects.filter(role=accounting_role, permission__code__endswith=".view").delete()
    url = reverse("accounting:create")
    assert logged.get(url).status_code == 200
    response = logged.post(
        url,
        {
            "scope_company_id": str(business_context.company_id),
            "journal": str(journal.pk),
            "entry_date": "2026-10-11",
            "memo": "Action only",
        },
    )
    assert response.status_code == 302
    entry = JournalEntry.objects.get(memo="Action only")
    line = services.add_journal_entry_line(
        business_context, entry.pk, account_id=account.pk, debit=1, credit=0
    )
    assert line.pk
    with pytest.raises(PermissionDenied):
        selectors.general_ledger(business_context)


@pytest.mark.parametrize("kind", ["accounts", "journals", "list"])
def test_paginated_lists_query_preservation(logged, business_context, kind):
    for index in range(52):
        if kind == "accounts":
            services.create_account(
                business_context, code=f"SEARCH-{index:03}", name="Search", type="ASSET"
            )
        elif kind == "journals":
            services.create_journal(business_context, code=f"SEARCH-{index:03}", name="Search")
        else:
            journal = services.create_journal(
                business_context, code=f"SEARCH-{index:03}", name="Search"
            )
            services.create_journal_entry(business_context, journal_id=journal.pk, memo="SEARCH")
    url = reverse("accounting:" + kind)
    first = logged.get(url + "?q=SEARCH")
    second = logged.get(url + "?q=SEARCH&page=2", HTTP_HX_REQUEST="true")
    assert len(first.context["page_obj"].object_list) == 50
    assert len(second.context["page_obj"].object_list) == 2
    assert b'id="list-results"' in second.content and b"q=SEARCH" in first.content
    assert not set(r.pk for r in first.context["page_obj"]) & set(
        r.pk for r in second.context["page_obj"]
    )


def test_foreign_uuid_urls(logged):
    for name, args in [
        ("detail", {"entry_id": uuid4()}),
        ("account_edit", {"reference_id": uuid4()}),
        ("journal_edit", {"reference_id": uuid4()}),
    ]:
        assert logged.get(reverse("accounting:" + name, kwargs=args)).status_code == 404


def test_boundary_detail_layout_and_posted_actions(logged, business_context, balanced):
    services.update_journal_entry(business_context, balanced.pk, memo="x" * 12000)
    response = logged.get(reverse("accounting:detail", kwargs={"entry_id": balanced.pk}))
    assert b"overflow-wrap:anywhere" in response.content
    assert b"overflow-x-auto" in response.content and b"x" * 12000 in response.content
    services.post_journal_entry(business_context, balanced.pk)
    response = logged.get(reverse("accounting:detail", kwargs={"entry_id": balanced.pk}))
    assert b"Posted facts are immutable" in response.content
    assert b">Edit draft</a>" not in response.content and b">Add line</a>" not in response.content
    # Invalid GET filters must remain visible inside the HTMX swap target.
    for report in ("gl", "tb"):
        response = logged.get(
            reverse("accounting:" + report),
            {"from_date": "2026-10-12", "to_date": "2026-10-11"},
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        assert response.content.index(
            b"From date must not follow to date."
        ) > response.content.index(b'id="list-results"')


def test_gl_http_report_payload_is_sql_paginated(logged, business_context, journal, account):
    # Page integration regression, distinct from direct-selector query assertions.
    for _ in range(33):
        entry = services.create_journal_entry(business_context, journal_id=journal.pk)
        for debit, credit in [(1, 0), (0, 1)]:
            services.add_journal_entry_line(
                business_context, entry.pk, account_id=account.pk, debit=debit, credit=credit
            )
        services.post_journal_entry(business_context, entry.pk)
    url = reverse("accounting:gl")
    first = logged.get(url, {"account": str(account.pk)})
    with CaptureQueriesContext(connection) as queries:
        second = logged.get(url, {"account": str(account.pk), "page": 2}, HTTP_HX_REQUEST="true")
    assert len(first.context["rows"]) == 50 and len(second.context["rows"]) == 16
    assert not {r.pk for r in first.context["rows"]} & {r.pk for r in second.context["rows"]}
    assert b"account=" in second.content and b'id="list-results"' in second.content
    payloads = [
        query["sql"].lower()
        for query in queries
        if '"accounting_journalentryline"."description"' in query["sql"].lower()
    ]
    assert len(payloads) == 1 and "limit 16" in payloads[0] and "offset 50" in payloads[0]
