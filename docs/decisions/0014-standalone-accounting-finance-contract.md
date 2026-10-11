# ADR 0014 — Standalone Accounting & Finance Contract

Status: Proposed — Gate ACC-0

Date: 2026-10-11

## Authority, evidence and gate boundary

This is the documentation-only ACC-0 candidate, not an accepted ADR, Accounting implementation,
production approval or integration authorization. It is prepared on `acc0-accounting-contract`
directly from canonical `main` at `9ac3f0944fff65f013efd9c3a3e9b841022ce87f`.

PAY-1 is canonically closed at that baseline. Annotated `payments-v1` has tag object
`05dcb375d0b05ad6ee9f819faa2c4e57dbfd3a34` and peels to the baseline. Main **Phase 0 checks #105 —
SUCCESS**, run ID `38078381136`
([evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38078381136)), checked out
that exact SHA and passed fresh migrations, **1,009 PostgreSQL tests** and mandatory checks.
That evidence verifies the starting baseline, not this later ACC-0 candidate.

ACC-0 authorizes one proposed contract commit, normal branch publication and exact-head hosted CI.
Independent read-only audit and successful exact-candidate CI are both required before a separately
authorized documentation acceptance commit. Canonical adoption then requires another authorization.
ADR 0014 must remain Proposed in this milestone. No `accounting-contract-v1` tag, main update,
ACC-1 implementation or Billing/Payments/Accounting integration is authorized.

### Precedence and explicit refinement

- [ADR 0011](0011-modular-billing-payments-accounting-boundary.md) remains authoritative for
  Billing / Payments / Accounting ownership separation and optional composition.
- [ADR 0013](0013-standalone-payments-contract.md) remains authoritative for standalone Payments;
  no Payments behavior or PaymentAllocation ownership changes here.
- Upon formal acceptance, ADR 0014 is the authoritative detailed ACC-1 standalone Accounting
  contract. While Proposed, it is the reviewable specification, not permission to override an
  accepted contract or begin implementation.
- It refines only Accounting details in [ADR 0006](0006-phase-2-commercial-core-contracts.md) and
  the older [Phase 2 plan](../exec-plans/active/PHASE_2_COMMERCIAL_CORE.md). In particular, the old
  optional header idempotency-key proposal is superseded on acceptance by the explicit same-entry
  retry / deferred external-source composition distinction below. ADR 0006's requirement for
  duplicate external posting protection when an integration is retried still applies to that future
  integration; it does not require a generic key field in standalone ACC-1.
- Historical documents and checkpoint evidence are retained. Unrelated Core, Party, Catalog,
  Sales, Procurement, Inventory, Billing, Payments, UI, module-gating and execution contracts remain
  unchanged. ADRs 0002, 0005, 0009 and 0012 continue to govern their respective boundaries.

## Ownership and independent installation

Accounting owns Account / Chart of Accounts identity, Journal, JournalEntry, JournalEntryLine,
manual entry lifecycle, exact balanced posting, immutable posted ledger facts and derived General
Ledger (GL) / Trial Balance (TB). A chart is the Company's collection of Accounts, not another
ACC-1 aggregate. Manual balanced entries make the module usable independently.

It does not own Invoice/InvoiceLine, Payment/PaymentMethod/PaymentAllocation, SalesOrder,
PurchaseOrder/PurchaseReceipt, stock movement, payroll or tax calculation, bank reconciliation or
gateway settlement. It does not infer invoice settlement, outstanding or payment allocation from
journal entries. JournalEntry is not a replacement for PaymentAllocation.

Future manifest dependencies must be **exactly**:

```text
party
organization
reference
access
```

Approved Core audit, database execution, common primitives, identity/business-time helpers and
module-registry utilities are infrastructure, not additional business-module dependencies.
Accounting has no hard dependency, eager import, FK, migration/startup requirement or service call
to Billing, Payments, Sales, Procurement, Inventory, Catalog, Ecommerce, HR or any vertical.
The existing dependency map permits this exact direction; Core/Party never import Accounting.

Future Accounting is installed and registered as `accounting`, disabled by default. Registration
preserves existing enablement, declares the exact permissions below and freezes historical
permission declarations inside its registration migration. Missing/disabled registration hides
navigation and returns HTTP 404. It neither removes migrations nor disables installed Python APIs.
Non-HTTP services remain governed by BusinessContext and RBAC, not `BusinessModule.is_enabled`.
No dynamic installer, resolver or service-level enablement gate is introduced.

## Minimum persistence and identity

All four entities use UUID primary keys and explicit Company ownership. `created_at` / `updated_at`
are server-generated aware timestamps stored in UTC. Referenced Company, Journal, Account and Party
identities are protected from deletion while referenced; no cascaded deletion of accounting history.
Names/descriptions/memos are text, not encoded identifiers or integration commands. No tenant ID,
branch requirement, mutable balance, external-document key or speculative hierarchy is added.

| Entity | Required persisted fields | Optional fields / null semantics |
| --- | --- | --- |
| Account | `id`, `company`, `code`, `name`, `type`, `is_active`, `created_at`, `updated_at` | None |
| Journal | `id`, `company`, `code`, `name`, `is_active`, `created_at`, `updated_at` | None |
| JournalEntry | `id`, `company`, `number`, `journal`, `entry_date`, `memo`, `status`, `base_currency_code_snapshot`, `base_currency_precision_snapshot`, `created_at`, `updated_at` | `posted_at`: null in DRAFT, aware server timestamp in POSTED |
| JournalEntryLine | `id`, `company`, `journal_entry`, `account`, `description`, `debit`, `credit`, `position`, `created_at`, `updated_at` | `party`: null means no Party association, not unknown customer/vendor or a synthesized identity |

`memo` and `description` allow empty string, not null. Account/Journal names are required nonblank
strings after outer-whitespace trimming. Codes use trim + uppercase, must be nonblank and have
database-enforced `(company, code)` uniqueness separately for Account and Journal. No normalization
through float, locale, fuzzy identity matching or client-specific rules is permitted.
Account/Journal activity defaults to true on creation; supplied activity must be a boolean, not
truthiness-coerced text/null. Database constraints enforce the stated type/status choices, Company
code/number and Entry-position uniqueness, precision range, line-side nonnegativity/one-sidedness
and DRAFT-null / POSTED-non-null posted_at consistency. Cross-row balance and reference eligibility
remain authoritative service validations; a database constraint is not a substitute for those.

### Account

Types are exactly `ASSET`, `LIABILITY`, `EQUITY`, `INCOME`, `EXPENSE`. Company, code and type are
immutable after creation. Name and activity may change only through Accounting services. No public
hard delete; retire with `is_active=False`. No parent/child account hierarchy in ACC-1.

An inactive Account cannot be selected for a new/changed draft line or used on initial posting.
Retirement does not rewrite POSTED lines or remove historical activity from GL/TB. Duplicate Account
references across distinct lines are valid; no artificial one-line-per-account constraint.

### Journal

Company and code are immutable. Name/activity are service-mutable; no public hard delete. Journal
must be active for new entries, draft Journal changes and initial posting. Deactivation does not
invalidate posted history. Advanced journal types, localization classes and sequence policies are
deferred.

### JournalEntry identity, dates and currency

Number format is frozen as `JE-` plus the entry UUID's 32 lowercase hexadecimal digits (35
characters), generated by the creation service, immutable and company-unique in the database.
Generate a fresh UUID/number only while attempting first creation. Use at most three collision
attempts, each isolated in an alias-aware savepoint so an actual uniqueness collision does not
poison the outer transaction. Retry only a proven generated-identity/number collision; unrelated
integrity errors propagate and roll back. Exhaustion is an explicit conflict. Never `MAX()+1`,
unbounded retry, public supplied number or a generic numbering framework. Fiscal/gapless numbering
is not claimed. No successful creation retry contract exists: callers retain the returned UUID.

Explicit `entry_date` is a canonical valid date. Services normalize a valid ISO date string or
date object before validation and reject malformed dates/datetime values rather than implicitly
truncating them. If omitted on first creation, resolve Company-local today exactly once using the
existing Company-time helper inside the transaction; never server-local or UTC-today substitution.
Draft date changes are explicit, authorized service operations. Date is immutable after posting.

Creation resolves the Company's immutable base Currency identity on the selected alias and freezes
its code and integer precision `0..8`. Missing/incompatible currency configuration rejects creation.
The snapshots are immutable even while DRAFT; there is no currency-change/refresh service. All line
validation, posting and historical display use the frozen precision. A subsequent Reference
precision/name/activity change cannot reinterpret stored amounts or refresh these snapshots.
Initial posting verifies Company's base currency code still matches the entry's frozen identity;
it does not replace precision with the current Reference value. There is no additional Currency
activity gate beyond the specified Journal/Account/Party eligibility: retirement cannot silently
change the unit of an existing draft. Ordinary Company base-currency immutability is not weakened.

Only Company-base-currency entries exist. No transaction currency, foreign-currency amount, exchange
rate, FX conversion, gain/loss or revaluation is implemented. Server-generated `posted_at` records
first successful posting, not entry_date or a user-supplied historical timestamp.

### JournalEntryLine identity, scope and position

Line Company must match its persisted parent. Account and optional Party must belong to that same
Company on the same execution alias. Party is a person/organization identity, not a requirement for
`is_customer` / `is_supplier`; neither role is invented by Accounting. A supplied Party must be
active when assigned/changed and on initial posting. A null Party is valid. Later retirement never
invalidates already-posted history or a valid post retry.
Account/Journal/Party names in reports are current reference labels, not invented historical name
snapshots. Stable referenced identities and immutable ledger values are preserved; this scope does
not claim to reproduce a reference name as it appeared on the original entry date.

Company, parent, UUID and position are immutable. Assign positive positions internally under the
Entry lock, with database uniqueness `(journal_entry, position)`. Positions increase above the
largest retained position; removals leave gaps and never renumber surviving rows. There is no
client-supplied position or reordering endpoint. Reads order by position then UUID. Every header
and line selection, relationship validation and lock is scoped by the authoritative Company.

## Financial Decimal contract

Both debit and credit use `Decimal(38,8)` storage. Accept Decimal, valid base-10 numeric string or
integer; reject bool, float, malformed strings and unsupported types with field-specific
ValidationError before arithmetic/comparison. Canonicalize both sides before comparing. Reject
NaN, signalling NaN and positive/negative Infinity. Finite amounts must be nonnegative and strictly
below `10^30`. Exactly one side is positive; the other is exactly zero. Both-positive and both-zero
lines are invalid; zero of either sign is semantically zero.

The numeric value must be exactly representable at the Entry's frozen precision. Redundant trailing
zeros are valid even if the input exponent exceeds that precision or storage scale. For precision
2, `10`, `10.5`, `10.50`, `10.5000` are valid; `10.501` is not. For precision 0, `100`, `100.0`,
`100.000` are valid; `100.1` is not. Validate representability without rounding nonzero digits;
canonical storage conversion may strip redundant zeros, never change numeric value. Unsupported
scale/range is rejected before persistence, not left to database rounding or Decimal exceptions.

Calculations are framework-neutral where practical. Use an explicit sufficiently large Decimal
context for multiplication-by-scale/comparisons and accumulation, independent of the process's
default precision. A sum over N storage-bounded amounts needs at least `38 + digits(max(N, 1)) + 2`
significant digits; implementation may use a larger safe bound. Totals may exceed a single line's
storage range because they are derived, not persisted in a `Decimal(38,8)` balance column. SQL
numeric sums and Python results must agree exactly. No float, per-line rounding, total rounding to
manufacture balance or silent clamping of report totals. Display every currency-significant digit.

## Lifecycle, mutation and immutable history

The only states and transition are:

```text
DRAFT -> POSTED
```

Empty DRAFT headers are allowed. Draft services may change Journal, entry_date and memo, and add,
edit or remove lines. Journal changes revalidate active same-company identity. Account changes
revalidate active same-company identity. Unchanged references are rechecked for eligibility when
needed; initial posting always revalidates the complete line set. Snapshots/number/ownership do not
become mutable through header or line update.

Initial posting requires DRAFT, active Journal, at least two valid lines, active Accounts, valid
same-company optional Parties, exact positive debit/credit totals and exact equality. Reject
unbalanced entries even if currency rounding would make them appear equal. Atomically freeze the
existing validated header/line facts, set POSTED/posted_at once and append the success audit. Do not
silently regenerate the line set or infer balancing lines, suspense accounts or upstream effects.

After POSTED, all persisted header and line business facts, ownership, identity, dates, memo,
currency snapshots, amounts, references, descriptions, positions and timestamps are immutable.
No add/edit/remove/delete/unpost. There is no APPROVED/CANCELLED/VOID/REVERSED state, reversal,
replacement-entry workflow or posted correction API. Public hard deletion of Entry headers is
deferred for DRAFT as well; supported draft deletion is line removal only.

ACC-1 must protect ordinary instance create/save/delete, QuerySet update/delete, bulk_update,
bulk_create and conflict-upsert paths from bypassing service-only mutation, lifecycle, ownership,
RBAC and audit. A module-local validated persistence path may serve the authorized services;
no generic public allow/skip-validation flag or global guard bypass. The private transition path
may only perform DRAFT -> POSTED with the validated locked state. It is not an arbitrary status
update API. Public ORM mutation cannot edit posted facts or create an already-posted document.

Instance guards resolve authoritative persisted ownership, lock Entry before line, reread/revalidate
after waiting and reject mutable in-memory company/parent substitution. A stale DRAFT object must
not delete or overwrite POSTED history, and an edit must not resurrect a concurrently removed line.
Integrity against arbitrary privileged raw SQL/private Python access is not claimed; that is a
deployment/security boundary, not a supported business mutation API.

## Post retry versus external-source idempotency

`post_journal_entry(context, entry_id)` always validates current actor/company/context and requires
the registered post permission after acquiring Company lock, including on retry. Lock/re-read the
company-scoped Entry. If already POSTED, return that original entry without another write, timestamp
refresh, line rewrite, ledger effect or `accounting.entry.posted` audit. Historical Account/Journal/
Party retirement does not invalidate this authorized retry. Inactive Company or revoked actor/
access/permission still rejects it. Concurrent calls on one Entry produce one posting effect.

ACC-1 has **no generic external-document idempotency key** on JournalEntry. The older optional
header-only key is not sufficient to freeze authoritative external retry semantics. Repeating
draft creation is not a posting retry and can create another draft; callers must retain its ID.

Future Billing/Payments/source integration must separately freeze source identity, complete header
and line set, exact amounts, posting transition, duplicate effects, conflicting retry behavior,
rollback and crash recovery as one authoritative composition. A header-only key or finding an
existing Entry is not proof of complete equivalent posting. That integration must provide atomic
source identity and duplicate-posting protection, not weaken it; its storage/API is deliberately
not guessed in ACC-0. Manual same-Entry retry safety and future external idempotency are distinct.

## Transaction, alias, authorization and lock order

Every mutation receives framework-neutral BusinessContext plus identifiers/data, never HttpRequest.
Use ADR 0012's current database execution context and `business_atomic` / `business_atomic_context()`
to resolve the configured alias at call/enter time. The default deployment remains single-database;
there is no tenant registry, tenant_id in BusinessContext or SaaS activation. Locks, reads, writes,
savepoints and audit all use the same selected alias. No hardcoded default connection, implicit
default `transaction.atomic()`, alias switch inside a business transaction or cross-alias object/FK.

Mutation order is fixed:

1. Enter the correct database execution context, then alias-aware atomic transaction.
2. Lock the active Company; after any wait, revalidate current actor/activity, BusinessContext,
   Company/branch/warehouse access and the operation's registered RBAC permission.
3. Lock/re-read the Accounting aggregate by persisted Company ownership.
4. Lock/re-read required references in deterministic order, validate, then persist and append
   Core Audit in the same transaction/alias.

For entry/header/line operations, Entry is always the aggregate lock. For posting: Company ->
current authorization -> Entry -> Journal -> lines by `(position, id)` -> Accounts by UUID ->
non-null Parties by UUID -> validate -> transition + audit. All paths needing multiple references
use the same type order; Account/Journal name/activity writers take Company before their own row.
Draft updates lock current/proposed references in that order before writing. A line-only operation
resolves its persisted parent through scoped reads, then locks Entry, then rechecks the line under
lock; it never trusts a supplied object parent. No cross-module writer contract is changed.

Company locking serializes Accounting and supported Access mutations on that Company; referenced
row locks protect validation against concurrent reference writes without changing their owners.
Permission or access checks performed before waiting are not reused afterward. Missing, inactive
or wrong-company references, stale state, revoked authority or audit failure leave no partial financial state or
success audit. Real PostgreSQL blocking tests must prove both race orders; sleeps are not evidence.

## Exact RBAC and HTTP action map

| Permission identity | Protected operations |
| --- | --- |
| `accounting.account.view` | Account list/detail/search |
| `accounting.account.manage` | Account create and name/activity update; action GET forms and POST |
| `accounting.journal.view` | Journal list/detail/search |
| `accounting.journal.manage` | Journal create and name/activity update; action GET forms and POST |
| `accounting.entry.view` | Entry list/detail/search, GL and TB reads |
| `accounting.entry.create` | Entry create form/POST and create service |
| `accounting.entry.update` | Draft header/line add/edit/remove forms/POST and services |
| `accounting.entry.post` | Post confirmation GET/POST and post service, including retry |

Exactly these eight permissions; no wildcard, implicit module super-permission, Django model-perm
substitution or incidental view permission used instead of mutation authority. Selectors enforce
their relevant view permission and scope. Services authorize independently of HTTP. Action forms
and POST actions require the mapped action permission; navigation/buttons are hidden where
unauthorized, not a substitute for server checks. Read selectors for financial GL/TB require
`accounting.entry.view`, not manage/post authority.

Internal same-company Account/Journal/Party validation for an authorized entry mutation is not an
unscoped public read or a new requirement for unrelated manage permissions. Entry create/update
action authority permits the minimal active same-company choices needed by that form (identity,
code/display name), not unrelated Account/Journal/Party details, history or a general list API.
HTTP detail portions require view permission when displayed; action authority alone suffices for
the framework-neutral mutation service. Core's superuser bypass applies only to active registered
permissions and never bypasses Company/context/ownership validity. Missing permissions deny.

Company-bound forms reject stale Company submissions for entry/account/journal creation/edit,
line mutation and posting. UUID detail/action URLs, search/filter pagination and direct Python
selectors never expose or mutate another Company's data. Module gating is HTTP/navigation only.

## Exact audit vocabulary and atomicity

Audit actions are exactly:

```text
accounting.account.created
accounting.account.updated
accounting.journal.created
accounting.journal.updated
accounting.entry.created
accounting.entry.updated
accounting.entry.posted
```

Use Core append-only Audit, not a competing journal-event store. Record actor, Company, aggregate
identity, server occurrence time and minimal structured change evidence. Entry line add/update/
remove emits `accounting.entry.updated` with operation, line UUID and changed field identities;
removal evidence retains removed-line identity. Header/reference/name/activity changes use the
corresponding owner action. Every actually changed persisted business field participates in change
detection. True no-op updates and already-POSTED retry emit no duplicate success action and do not
refresh timestamps. Never put passwords, credentials or unnecessary sensitive Party data in audit.
Validation/permission failures produce no success audit. Audit/persistence failure rolls back
both business and audit state on the selected alias. Audit is evidence, not the ledger itself.

## Derived General Ledger and Trial Balance

Only immutable lines whose parent Entry is POSTED contribute. DRAFT never contributes. All report
queries constrain parent and line Company and referenced Account ownership; malformed cross-company
history must fail closed, not be silently summed or hidden as a plausible complete report.

`general_ledger` accepts explicit Company context, optional inclusive from/to entry_date bounds and
optional same-company Account ID. Invalid/reversed ranges or cross-company filters reject. With
no from bound, include all prior posted history through the optional to bound; with neither bound,
include all posted history. It exposes entry/line identities, date, number, Account, optional Party,
description/memo, exact debit/credit and frozen currency provenance. Order by
`entry_date, number, entry_id, position, line_id` for deterministic pagination. It is a read-only
projection, not a posting service or mutable balance table.

`trial_balance` applies the same inclusive date/filter scope and derives per Account:

```text
total_debit   = sum(posted debit in the requested scope)
total_credit  = sum(posted credit in the requested scope)
net           = total_debit - total_credit
ending_debit  = max(net, 0)
ending_credit = max(-net, 0)
```

Date-range totals are movement/net within that range, not an invented opening/fiscal closing
balance. As-of reporting uses no lower bound. Label the scope explicitly in UI. Include every
Account with posted activity in scope, even if net is zero or the Account is now inactive; do not
filter historical ledger activity by current Account/Journal/Party activity. Stable Account code
then UUID ordering. An Account with no activity need not have a synthetic zero row.

Company's base currency code is the unit for aggregation. A mismatched historical code is an
integrity error, not a sum across currencies. Entry precision snapshots can legitimately differ
after a Reference precision change; amounts remain exact units of the same code. GL retains each
entry's precision; TB displays at least the greatest frozen precision of contributing entries and
never truncates using today's Reference precision. Do not invent FX or round a report to hide
differences. Exact grand totals and per-Account values remain derived and may exceed single-line
storage magnitude. No aggregate-range truncation through a narrowed ORM output type.

There is no authoritative `Account.balance`, `Account.current_balance`, `Journal.balance` or
mutable GL/TB balance row. Future caching/materialization requires another gate and must remain
rebuildable from the immutable posted facts. No financial statement beyond minimum GL/TB is claimed.

## Future ACC-1 public surface and UI

Conceptual minimum services: `create_account`, `update_account`, `create_journal`, `update_journal`,
`create_journal_entry`, `update_journal_entry`, `add_journal_entry_line`,
`update_journal_entry_line`, `remove_journal_entry_line`, `post_journal_entry`.
Exact Python signatures may be finalized in ACC-1 without changing the above authority, data,
lifecycle, precision or lock contracts. No external-source posting service is frozen here.

Minimum scoped selectors: `accounts_for_company`, `journals_for_company`,
`journal_entries_for_company`, `journal_entry_detail`, `general_ledger`, `trial_balance`.
Use explicit context/filter IDs, selected execution alias, scoped relationship reads and stable
ordering. Ordinary list UI uses existing backend 50-row pagination and safe GET interactions;
actions remain normal Django POST with CSRF and Company-bound form protection.

Future UI uses the accepted BusinessOS shell: Account list/create/edit; Journal list/create/edit;
Entry list/create/draft edit/detail/line management/post confirmation; GL and TB reports. Inputs
and errors reflect exact precision, and historical values remain readable at supported maximum
magnitudes with local table scrolling/no page overflow. Responsive desktop/mobile, non-JavaScript
fallback, safe HTMX navigation, focus and audited shared read-path behavior are retained. No React
or new framework. **No UI or runtime is implemented by ACC-0.**

## Optional integration boundary and explicit deferrals

Future authorized composition may consume Billing's issued invoice or Payments' receipt/outcome
public contract and call Accounting's public posting services. The composition may depend on both
contracts; base modules stay independent. Source modules never directly insert/update Accounting
tables; Accounting never imports Billing/Payments merely to work standalone. No current invoice
issue/payment receipt/order confirmation/stock posting creates a JournalEntry.

PaymentAllocation remains Payments-owned. Future invoice allocation is Payments + Billing
composition, separate from Accounting posting. ACC-1 does not absorb allocations or derive them
from journals. An unallocated receipt has no guessed receivable, settlement or invoice effect.

Explicitly deferred beyond standalone ACC-1:

- Billing/Payments/Sales/Procurement automatic journals and Inventory valuation/accounting.
- PaymentAllocation, AR/AP automation, automatic customer/vendor subledgers and aging.
- Tax/VAT/GST calculation, fiscal periods/period locking, year-end close and retained earnings.
- Reversal/correction/approval workflows, recurring journals and account hierarchy.
- Analytic dimensions, cost/profit centers, budgets, bank reconciliation/feeds and cheque management.
- Treasury, fixed assets/depreciation and payroll journals.
- Foreign-currency ledger, FX conversion/gain/loss/revaluation, consolidation and intercompany.
- Financial statements beyond GL/TB, localized charts and regulatory/fiscal sequential numbering.
- Generic workflow/rule/metadata/event engines, command bus, dynamic plugins, custom framework,
  SaaS activation, Redis/Celery, React, additional services or infrastructure.

These are separately governed future features, not defects or implicit ACC-1 requirements. Minimum
manual ledger capability is not complete finance/compliance capability or production-launch approval.

## ACC-1 acceptance matrix — requirements, not executed ACC-0 tests

| Area | Required objective evidence before standalone implementation acceptance |
| --- | --- |
| Ownership/dependencies | Exactly four models, four manifest dependencies and eight permissions; no upstream module imports/FKs/effects; manual workflow with other commercial modules absent |
| Account/Journal | Code normalization/company uniqueness and concurrent collisions; immutable identity/type; active selection/posting; inactive historical report inclusion; no hard-delete/bulk bypass |
| Entry identity/date | JE-UUID identity, bounded savepoint-safe collision handling, Company-local omitted-date behavior including midnight/timezones, canonical explicit date, immutable number/currency snapshots |
| Monetary boundaries | Precision 0..8; redundant zeros including beyond storage exponent; max representable amount; `10^30`, excess nonzero scale, malformed strings, bool/float, NaN/sNaN and infinities reject field-specifically without mutation/audit |
| Balanced posting | Two or more valid lines, duplicate Accounts allowed, exact large sums, one-sided line validation, positive equal totals, imbalance that only rounds to equality rejects, snapshots never refreshed |
| Retry/rollback | Same-entry post retry and concurrent posting have one effect/timestamp/audit; current revoked authority still fails; inactive historical references do not spoil valid retry; persistence/audit failure rolls everything back |
| Immutability | Public instance/save/update/bulk/create/upsert/delete and private transition misuse; stale header/line deletion, in-memory parent substitution and edit-versus-remove cannot erase/recreate posted history |
| PostgreSQL races | Real row-lock coordination for post versus header edit, line edit/add/remove, stale Entry/line delete, reference retirement and concurrent position allocation; each race order; clean worker connections/explicit SQLite skips |
| Authorization waits | Role, permission and Company-access revocation while create/update/post waits on Company, with current recheck; action GET/POST matrix; direct non-HTTP services retain RBAC with registry disabled/missing |
| Company/alias scope | Two-Company relationship/UUID/report/search isolation and stale Company forms; full representative workflow on non-default alias; no cross-alias business/audit writes or implicit default atomic blocks |
| GL/TB | DRAFT excluded; exact field values, date boundaries/filter ordering, zero-net/inactive history, precision drift, large sums and per-Account/grand totals; malformed scope/currency fails closed; no authoritative balance field |
| Module/UI | Deterministic frozen permission bootstrap and enablement preservation; HTTP 404/navigation gating; module-local discovery; 390/768/1280px boundary-value workflows, no horizontal page overflow, safe shared UI fallback |
| Definition of Done | Fresh PostgreSQL zero-state migrations; full PostgreSQL/SQLite suites; Ruff, Django check, migration drift; npm/Tailwind/CSS/JS and architecture guards as applicable; exact-head hosted CI and independent audit |

ACC-1 needs explicit implementation authorization after ACC-0 acceptance/adoption. Implementation
review, publication, formal acceptance and canonical adoption remain separate gates; do not start
optional integrations automatically. No migration or runtime evidence is manufactured in ACC-0.

## Compatibility findings and maintenance exclusions

No material conflict exists with the current baseline, module boundaries or dependency map: all
retain independent Accounting, Party/Core dependencies, base-currency balanced journals and derived
balances. The older plan's optional header key is explicitly contextualized as historical and the
future integration requirement is retained, not silently implemented.

Outside authorized files, checkpoint-era PAY-1 candidate/adoption wording remains in BASELINE,
MODULE_BOUNDARIES, DEPENDENCY_MAP and ADR 0011; ADR 0006/Core restructuring also retain earlier
authorization wording. These status-maintenance findings do not change the accepted Accounting
ownership/dependency contracts. They are reported for later bounded cleanup, not edited here.
The current roadmap/Phase 2 status and the appended ADR 0013 closure note distinguish current PAY-1
closure from the earlier truthful checkpoints.

Favicon 404, eight inherited npm advisories (two moderate, six high), GitHub Actions runtime
warnings, stale Browserslist data, BILL-1 extreme badge wrapping P3 and unrelated documentation/
dependency maintenance remain outside ACC-0. No dependency upgrade or `npm audit fix` is authorized.

## Consequences and required next decision

This bounded proposal gives ACC-1 a precise manual, Company-isolated, base-currency ledger contract
without invented automatic finance/integration capabilities. Posted mistakes cannot be edited or
unposted under ACC-1; a later reviewed correction/reversal gate is necessary. Drafts have no generic
request-key deduplication; only retry on a retained Entry identity is promised. Historical reports
remain derived even when names/activity/Reference precision later change.

Next: independent read-only review of the exact published ACC-0 candidate and its hosted CI.
Do not record acceptance, move main, create a tag, implement ACC-1 or begin an integration here.
