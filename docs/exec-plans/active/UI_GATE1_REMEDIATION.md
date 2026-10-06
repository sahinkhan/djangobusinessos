# Gate UI 1 corrective remediation

Status: locally verified; awaiting independent re-audit. No publication or merge authorized.

## Scope and checkpoint

Immutable failed candidate: `879f9c9350aa9a923dc598955b9042fda8050b91`.
Corrective branch: `ui-gate1-remediation`; its single corrective SHA is reported after commit.
Canonical `main` and `origin/main` remain `b7fdd543cab5239d4f4657ecf87eccbfa66164e0`.
No services, models, domain rules, migrations, authorization, company filters, transactions,
audit behavior, or POST semantics change. Selector edits only append a unique ordering key.

Changed files: five module `selectors.py` files (Party, Catalog, Sales, Procurement, Inventory),
`templates/base.html`, `templates/inventory/movement_list.html`, `static/js/app-navigation.js`,
generated `static/css/tailwind.css`, `tests/test_ui.py`, `tests/test_list_pagination.py`,
`tests/js/test_app_navigation.cjs`, and this record.

## F1 History privacy

The shared body, including login, uses `hx-history="false"`; HTMX config disables snapshots with
`historyCacheSize=0` and full refresh on history miss. URLs still push normally. The documented
[history privacy control](https://htmx.org/attributes/hx-history/) prevents new snapshots.
Earlier cached HTML needs separate protection: cancel the documented
[`htmx:historyCacheHit`](https://htmx.org/events/#htmx:historyCacheHit) event before restoration,
then full-navigate to its same-origin history path. No storage internals, identity partitions,
or JavaScript authorization are used. Old bytes are not explicitly purged but cannot be restored
by the corrected handler. The navigation asset URL is versioned to avoid the old JS bundle.

Real browser test: normal User A with only AUDITA access opened Party filtered to `A_ONLY`
using the vulnerable bundle and navigated to Catalog, priming the old snapshot. After logout,
normal User B with only AUDITB access logged in and selected AUDITB. Six Back, five Forward,
and another Back/Forward pair exposed no AUDITA data or User A identity. The old Party URL
returned User B's empty scoped result. Server logs confirmed old history URLs were requested.

## F2 Session recovery

Before a successful fragment swap, require `#app-content` and the expected app/list target.
If missing, cancel the swap and full-navigate to the final same-origin `xhr.responseURL`.
No login-path special case exists. Cross-tab logout followed by Party click reached the full
login screen at `/login/?next=/parties/`, without stale shell or blank content. Expiring the
disposable database session reproduced the same behavior. Both cases had no console errors.
Login to a business deep link without company selection still correctly returns the existing
403; the user must select company scope. Server authorization remains unchanged.

## F3 Deterministic pagination

| Surface | Preserved primary sort plus UUID tie-breaker | Traversal |
| --- | --- | --- |
| Party | `display_name, id` | 401 duplicate names, 9 pages, each permitted ID exactly once; foreign duplicate excluded |
| Catalog | `name, id` | 151 duplicate names, 4 pages, each ID exactly once |
| Sales | `-order_date, -created_at, id` | 61 identical date/timestamp rows, 2 pages, exactly once |
| Procurement | `-order_date, -created_at, id` | 61 identical date/timestamp rows, 2 pages, exactly once |
| Inventory movements | `-effective_at, -created_at, id` | 61 identical timestamp rows, 2 pages, exactly once |
| Inventory history | `-effective_at, -created_at, id` | Same 61 posted rows with warehouse/variant filters, exactly once |

HTTP tests assert 50 rows/page, exact expected IDs, no duplicates/omissions, UUID tie order,
and queryset ordering. Offset pagination is not a snapshot when records change between requests.

## F4 Query-preserving fallback

Use HTMX's effective `pathInfo.finalRequestPath`, not the base `requestConfig.path`.
Same-origin validation and duplicate-navigation protection remain generic. A disposable local
proxy injected errors only on HTMX GETs and forwarded normal requests without altering auth.

- Search 500 retained `q=A_ONLY%20Movement1&type=&status=` and returned 50 rows.
- One-filter 403 retained `q=&type=receipt&status=` and returned 50 receipt rows.
- Multi-filter 500 retained `q=A_ONLY%20Movement1&type=receipt&status=posted`.
- Filter/page 500 retained `q=A_ONLY+Movement1&type=receipt&status=posted&page=2`; 11 rows, Page 2 of 2.
- Real socket shutdown retained `q=A_ONLY%20Movement3&type=receipt&status=posted`; correct empty result.

`%20` versus `+` reflects the actual form versus pagination link encoding; fallback kept each
attempted URL. 404 shares the tested response-error handler; injected browser statuses were
500/403. Expected injected errors and favicon 404 are not unexplained application errors.

## F5 and F6 Accessibility

Native `<dialog>.showModal()` makes background controls inert. A small boundary handler wraps
Tab/Shift+Tab around visible controls, avoiding escape into browser chrome. At 390px, 40 final-code
keyboard presses remained in the drawer; Escape returned focus to Open navigation. Desktop resize
closes the modal and desktop sidebar behavior remains unchanged. No dependency is added.
Inventory type/status have associated sr-only labels, exposed as Movement type and Movement status
combobox names. Search also has a label. Inventory History already has proper associated labels.

## Ordinary browser matrix

Dashboard, Party, Catalog, Sales, Procurement, Inventory, and History passed all 21 screen checks
at actual verified widths 390/768/1280px without page-level horizontal overflow. Sales/Procurement
detail documents with unbroken 168-character names/notes and maximum PostgreSQL quantity/price
values also passed at all widths; audited wrapping and local table scrolling remain intact.
Ordinary HTMX GETs preserve the shell, title, and active aria-current. Party search swaps
`#list-results`, preserves `q=B_ONLY`, and shows the scoped row. Back restores filter values via
server response; Forward returns to Catalog. Direct deep links and refresh render complete pages.

Native GET was verified by removing all enhancement scripts from the initial proxy HTML: zero
scripts and zero hx-get forms, followed by search/type/status submission retaining all parameters
and rendering 50 rows. The subsequent response loaded normal scripts again; this is not an
engine-wide JavaScript-disable test. POST forms are unchanged. Normal navigation, session loss,
responsive checks and focus testing produced no application console errors. Company isolation,
RBAC, disabled/missing-module gating and mutation regressions remain green in the full suites.

## Verification results

Date: 2026-10-06. Disposable Docker project: `ui-gate1-qa`.

- Focused SQLite UI/pagination: 15 passed.
- Focused PostgreSQL UI/pagination and affected module regressions: 103 passed.
- Node transport/history/focus tests: 21 passed.
- Full PostgreSQL, Python 3.13: 506 passed in 201.56s, no teardown warning.
- Full SQLite, local Python 3.12: 410 passed, 96 expected PostgreSQL-only skips.
- Fresh PostgreSQL bootstrap: new Compose volume and fresh pytest database migrated successfully.
- Ruff, Django checks and `makemigrations --check --dry-run`: pass.
- Tailwind consecutive builds match SHA256 `304d2320968a01476aa48eb98d3b58d48b6807075a26e34a2deb1e707ced9553`.
- Both JS syntax checks and `git diff --check`: pass.

Temporary proxy/seed scripts are removed before commit. No migration is created. Failed UI
commits, main, historical branch targets and archive tags are unchanged. The corrective commit
is local only: no hosted CI can run until separately authorized publication.

Recommendation: PASS FOR INDEPENDENT GATE UI-1 RE-AUDIT. This is not independent acceptance,
production approval, or permission to push/merge. No further feature work is authorized.
