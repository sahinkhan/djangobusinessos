# Gate UI 1 corrective remediation

Status: locally verified; awaiting independent re-audit. No publication or merge authorized.

The original F1-F6 execution record below is retained as historical evidence, not as the
visual recovery target. The subsequent selective recovery record at the end supersedes its
mobile-only launcher description, presentation-file inventory, and verification counts.

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

## Selective preserved-UI recovery — 2026-10-06

Status: locally verified; awaiting independent visual + Gate UI-1 re-audit. Not published,
accepted, or merged. The user explicitly authorized continuation of the partially applied
recovery, overriding the previous read-only/clean-tree precondition; no partial work was reset.

- Branch: `ui-gate1-remediation`.
- Starting remediation: `641f9aa9b21440febb6ad58a1608b5d7daed6629`.
- Authoritative visual source: `65600700395d2df923f2cf2b2a5fec5d0c96c8d8`.
- `879f9c9350aa9a923dc598955b9042fda8050b91` remains historical failed-candidate evidence,
  **not** the intended visual baseline.
- Exactly one local recovery commit is authorized; its final SHA is reported after commit.
- `main` and `origin/main` remain `b7fdd543cab5239d4f4657ecf87eccbfa66164e0`.
- No push, merge, tag, history rewrite, Billing, Payments, Accounting, or further feature work.

### Source and scope reconciliation

The byte-for-byte ZIP remains unchanged evidence at
`C:\Users\HP\.codex\visualizations\2026\09\15\01a0a5f8-8232-7f00-b97e-7e621ef2505e\option-a-preservation\working-tree-before.zip`.
The earlier read-only investigation verified all 77 preserved files against its manifest and
the preservation commit; it did not find a newer UI state. No archive extraction, checkout,
reset, cherry-pick, or whole-branch restore was used for this recovery.

44 presentation files are reconciled: base/login/403, dashboard/company selection, shared
header/launcher/heading/scope/messages/empty-state/form components, Party/Catalog lists and
records/forms, Sales orders/lines, Procurement orders/lines/receipts, Inventory movements,
history/balances, three CSS/source files, shared navigation JavaScript, and Tailwind config.
Existing breadcrumbs/pagination components already match the source and remain unchanged.

After line-ending normalization, 37 presentation files match the preserved source exactly.
The seven remaining files have explained reconciliation differences:

| File | Difference from preserved source |
| --- | --- |
| `templates/base.html` | F1 history controls and asset version; native modal at all widths; trusted opener tracking for F5 |
| `templates/components/header.html` | Both launcher buttons record their actual opener and expose expanded/controls state |
| `templates/components/sidebar.html` | Close action uses the corrected launcher lifecycle |
| `templates/inventory/movement_list.html` | F6 associated sr-only select labels, with preserved compact layout |
| `static/css/businessos.css` | One transparent native-dialog backdrop rule, avoiding additional UA tint over the preserved overlay |
| `static/js/app-navigation.js` | Retained F1/F2/F4 safeguards and native focus boundary handling, combined with preserved routing/header/pager synchronization |
| `static/css/tailwind.css` | Regenerated from the reconciled, non-Billing template set and preserved source/config |

Deliberately excluded: all Billing implementation/migrations/templates and Payment or
PaymentAllocation code; preservation-branch architecture/Billing documentation; its business
models/services/views/settings; all unrelated work. No Billing/Payment/Odoo reference is
introduced in the active templates, frontend assets, or Tailwind config.

Four test files are restored/reconciled or added for presentation recovery. Existing F1-F6
Node and pagination regressions are retained unchanged. No `businessos/`, runtime configuration,
dependency, migration, service, domain, permission, transaction, or audit implementation changes
occur relative to the starting remediation. Its five deterministic selector fixes remain intact.
POST forms remain native Django; no HTMX POST/create/edit behavior is activated.

### Real-browser visual verification

Reference rendering loads the preservation ZIP's active templates/assets read-only into a
temporary QA process, excluding Billing, with the same current backend and synthetic data as
the recovered UI. It does not activate historical business code or alter a Git ref/worktree.

22 screens were compared at actual widths **390, 768, and 1280px** (900px height): dashboard,
company selector; Party list/detail/form; Catalog list/detail/form/categories/attributes;
Sales list/detail/form; Procurement list/detail/form/receipt detail; Inventory list/history/
balances/detail/form. All 66 comparisons match sampled region geometry, computed typography,
colors, and layout. Header/control panels/pagers, centered 1120px dashboard, plum accents,
shared record/forms and responsive layouts match. No page-level horizontal overflow occurred.
This is real rendered-region comparison plus screenshot inspection, not a claim of exhaustive
pixel-for-pixel equivalence for every state.

Launcher reference/recovery comparisons also match at all three widths: search, grid/tile,
navigation and aside geometry/styles. The 44px plum header is preserved; no fixed slate desktop
sidebar, tall white header, or former large dashboard cards return. Search for Inventory exposes
only its tile; module header/title/active state synchronize after enhanced navigation.

Additional boundary documents were rendered at all three widths: 168-character unbroken
customer/supplier/notes, 56-character SKU, and PostgreSQL-supported quantity/unit-price/cost
`99999999999999.9999`. Sales and Procurement orders and posted receipt retain every value;
no page-level overflow. At 390px the line tables scroll locally (315px viewport / 620px table).

### F1-F6 and browser functional results

| Gate | Recovery verification |
| --- | --- |
| F1 | Actual vulnerable preserved bundle primed User A/AUDITA Party snapshots, then corrected bundle served on the same origin without clearing storage. User B with AUDITB-only access logged in; six Back/six Forward plus repeated Back/Forward exposed no User A identity, AUDITA rows, or protected snapshot. Old filtered URLs returned freshly authorized User B results; server logs show fresh requests. |
| F2 | Cross-tab logout and separate actual QA session expiry both send enhanced navigation to full `/login/?next=/parties/`; authenticated shell/launcher disappears, with no blank page or console error. |
| F3 | Existing duplicate-key traversal tests pass, preserving unique ordering/50-row backend pagination for Party, Catalog, Sales, Procurement, Inventory movements/history. |
| F4 | Browser proxy injected 500 on enhanced Inventory GET only. Search + receipt + posted fallback retains the attempted effective query and 50 results; filtered page 2 retains all parameters and returns 11 rows. Generic transport/error Node regressions remain green. |
| F5 | All-width native modal makes background inert. 40 forward/reverse keyboard presses each at desktop and mobile remain contained; Escape closes and returns to Open apps. Search applications opener also receives focus on close. |
| F6 | Inventory selects expose Movement type/Movement status through associated sr-only labels; no visible control-panel redesign. |

Dashboard, Contacts, Catalog, Sales, Purchase, Inventory and Inventory History navigation passed;
module header synchronization and active aria-current are correct. Party search/pagination swaps
`#list-results`, synchronizes the compact pager and preserves `q`/`page`; Back, Forward, repeated
history, direct links and hard refresh restore correct server-scoped content.

With **all enhancement scripts omitted from every proxy HTML response**, native Inventory
search + both filters + pagination also preserve the query and return the correct 11 page-2 rows
(zero scripts, zero hx-get elements). This verifies native read-path fallback, not an engine-wide
JavaScript-disabled launcher audit. Native company-selection and login POSTs were exercised;
automated normal form/mutation regressions remain green. Company isolation, server RBAC,
disabled/missing-module gating and transaction/audit behavior remain covered by the full suite.

No unexplained browser console errors. The fault tab reports the two intentional injected
HTMX 500 errors; ordinary/navigation/session/history/focus tabs report none.

### Automated verification and evidence

- Focused SQLite recovery/UI/pagination: **38 passed**.
- Final focused PostgreSQL recovery/UI/pagination plus Sales/Procurement/Inventory regressions:
  **107 passed**, 46.88s.
- Full PostgreSQL / Python 3.13: **521 passed**, 194.75s, no teardown warning.
- Full SQLite / Python 3.12: **425 passed, 96 expected PostgreSQL-only skips**, 28.76s.
- Node transport/history/focus regressions: **21 passed**.
- Ruff: pass (container uses `--no-cache` for its read-only repository mount).
- Django system check: zero issues; migration drift: **No changes detected**, both databases.
- Fresh PostgreSQL zero-state migrations: pass, using new tmpfs database and fresh pytest database.
- Tailwind consecutive builds exactly match SHA256
  `e1bd72085b9ee644157694cab840fd3a3445d4a6a4707c1bbd815b3aa07730df`.
- JavaScript syntax and `git diff --check`: pass.

Screenshots, region measurements, synthetic fixtures and temporary QA scripts live outside the
repository under
`C:\Users\HP\.codex\visualizations\2026\09\13\01a09a3b-7a01-72e3-86bc-21a752d748fc`.
Evidence includes `ui-recovery-parity.json`, `ui-recovery-browser-evidence.json`, responsive
dashboard/launcher/module screenshots and three 390px boundary screenshots. Synthetic QA uses
only isolated `ui_recovery` PostgreSQL, localhost ports 8020-8024, read-only repository/ZIP mounts,
and disposable tmpfs storage. The existing preview/user database and preservation ZIP are untouched.
The six task-created QA containers and network were removed after verification; their synthetic
tmpfs database was discarded. Screenshots, measurements and rerunnable QA scripts remain as evidence.

Concerns/deviations: external fonts/Alpine/HTMX CDN dependencies are retained from the visual
source, not introduced as infrastructure; stale Browserslist data warning is non-blocking.
An unconfigured default local PostgreSQL connection emitted a credential warning on one check;
explicit SQLite test settings and the isolated PostgreSQL connection both subsequently passed
system/migration checks without that warning. No user database credentials or configuration changed.
No hosted CI is claimed for this unpublished recovery commit. Independent visual/security
acceptance and publication remain separate gates. Final local SHA and clean-tree/ref verification
are reported after the one authorized commit; no further implementation is authorized.

Recommendation: **PASS FOR INDEPENDENT VISUAL + GATE UI-1 RE-AUDIT**.
