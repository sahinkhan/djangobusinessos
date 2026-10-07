# ADR 0013 — Standalone Payments and Receipt Contract

Status: Accepted — Gate PAY-0

Date: 2026-10-07

## Formal acceptance — 2026-10-07

Accepted contract candidate: `9ffb5eae09da680354776872a601bedd58163ab1`.
Independent audit verdict: **FINAL PASS — PAY-0 CONTRACT APPROVED**.
Implementation readiness: **A — precise enough for PAY-1 implementation**.
Hosted candidate **Phase 0 checks #99 — SUCCESS**, run ID `37656399267`
([run evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/37656399267)),
checked out exactly `9ffb5eae09da680354776872a601bedd58163ab1` and passed fresh PostgreSQL
migrations, **873 tests**, Ruff, Django checks, migration drift and mandatory npm/Tailwind/CSS checks.

PAY-0 formal acceptance is **COMPLETE**, as documentation/architecture acceptance only.
Canonical adoption is **PENDING**; PAY-0 is not canonically closed. This does not mean PAY-1 is
implemented: PAY-1 and ACC-1 are **NOT STARTED** and require separate implementation authorization.
PaymentAllocation and all integrations remain deferred. No runtime/schema, tag or main change
is authorized by this acceptance milestone.

The inherited nonblocking P3 concerning checkpoint-era ADR 0011/Billing authorization wording
in ADR 0006 and `CORE_FOUNDATION_V1_RESTRUCTURE.md` remains a documentation-maintenance follow-up.
Those files are unchanged; the follow-up does not alter this accepted contract.

## Authority, baseline and gate boundary

The initial Gate PAY-0 instruction authorized a documentation candidate only, not acceptance,
publication or implementation. Subsequent independent review, candidate publication/CI and this
separately authorized docs-only formal acceptance complete the contract-review sequence.
Acceptance-commit publication/CI is authorized; canonical adoption remains separately gated.
No PAY-1 implementation, permission/module registration or ACC-1 work is authorized here.
Canonical starting main is `409e45eaa32fae1cf9c77042a762e57026d0349f`, checkpoint
`billing-invoicing-v1`. BILL-1 is canonically closed there; main Phase 0 checks #97
([run 37645584246](https://github.com/sahinkhan/djangobusinessos/actions/runs/37645584246))
succeeded, including fresh migrations and 873 PostgreSQL tests. The accepted UI, tenant-ready
database and BILL-0 checkpoints remain preserved. No historical Payments/Billing WIP is restored.

ADR 0011 remains Accepted and owns the Option A separation. This candidate refines its subsequent
Payments gate, not Billing v1 behavior or Accounting ownership. ADR 0002 governs optional
composition; ADR 0006 remains accepted except the explicitly superseded combined Billing scope
identified in ADR 0011. ADR 0012 governs database execution. Delivery order
`BILL-1 -> PAY-1 -> ACC-1` is not a hard-dependency graph. Independent PAY-0 contract review and
formal acceptance are complete; canonical adoption and PAY-1 implementation need separate authorization.

## Ownership versus first implementation scope

Payments is the sole owner of incoming Payment/Receipt, PaymentMethod, receipt identity/number,
amount, payer/currency/method financial snapshots and receipt retry identity. Future approved
PaymentAllocation, settlement and refund/reversal semantics also belong to Payments, not Billing
or Accounting. Ownership does not authorize or require those features in PAY-1.

The approved future PAY-1 MVP is **standalone incoming receipt recording**: only PaymentMethod and
Payment/Receipt. A Payment records money received from a Party; existence means successfully
recorded authoritative receipt. There is no separate Receipt model and no status field/state
machine: no DRAFT, SETTLED, FAILED, REFUNDED or REVERSED states. It is not a gateway-capture,
bank-settlement or reconciliation claim. Procurement PurchaseReceipt remains an unrelated
goods/service receipt fact.

All recorded Payment fields are immutable, including notes, external reference, dates, retry key
and timestamps. No Payment update/delete service or correction escape hatch exists. Correction,
refund and reversal require a later financial-safety contract. PaymentMethod administration has
its own narrowly mutable name/activity fields.

## Dependencies and no cross-module effects

The future manifest dependencies are exactly:

```text
payments -> party, organization, reference, access
```

Existing Core common/identity/audit/time/module-registry/database utilities are allowed without
new registered dependencies. No Billing, Sales, Procurement, Catalog, Inventory or Accounting
dependency, import, migration/startup dependency, selector/service call or FK belongs to standalone
Payments. In particular, no Invoice FK/import or Billing linkage field is added to generic Payment.
The module must remain installable and usable with Billing and Accounting absent.

Recording a receipt creates no invoice, edits no Billing data, marks no invoice paid, calculates no
invoice outstanding and changes no invoice lifecycle. Billing continues to expose original
**Invoice total** and **Payment status unavailable** until an approved allocation composition exists.
Recording creates no JournalEntry, bank/cash posting, GL change or stock effect. Accounting remains
usable without Payments or Billing. Future integrations call owning-module public contracts;
neither base module imports the other and no circular dependency is introduced.

## Future PAY-1 persistence contract

These are future PAY-1 fields/constraints, not schema or migration changes in PAY-0. UUID and
created/updated timestamps follow existing Core primitives. Referenced Company/Party/Currency/
PaymentMethod identities use PROTECT, not cascade deletion of recorded financial facts.

### PaymentMethod

| Field | Contract |
| --- | --- |
| `id` | UUID primary key |
| `company` | Explicit Company FK; immutable |
| `code` | Nonblank string, maximum 32 characters after strip/uppercase; immutable |
| `name` | Nonblank string, maximum 160 characters after strip; service-mutable |
| `is_active` | Boolean, initially true; service-mutable |
| `created_at`, `updated_at` | Existing aware timestamp primitives |

Database uniqueness is `(company, code)` over the normalized identity. Same code in different
companies is allowed. No hard-delete API is offered in PAY-1; deactivate instead. Referenced
methods must be deletion-protected. No gateway credentials/configuration, provider-specific code,
bank-account schema or hardcoded Cash/Card/provider behavior is introduced.

Inactive methods are unavailable for NEW receipts. Renaming/deactivating a method does not
invalidate historical receipts or change their frozen method code/name. Method input normalization
rejects nonstrings and blank identities/names; activity requires an actual boolean.

### Payment / receipt

| Field | Contract |
| --- | --- |
| `id` | UUID primary key |
| `company` | Explicit immutable Company FK |
| `number` | Generated nonblank immutable string, maximum 40 characters; company-unique |
| `payer_party` | Same-company Party FK; PERSON or ORGANIZATION |
| `payer_display_name_snapshot`, `payer_legal_name_snapshot` | Record-time names, maximum 200 characters each; legal name may be blank |
| `payment_date` | Business date, canonical date object |
| `currency` | Core Reference Currency FK; not company-owned |
| `currency_code_snapshot` | Record-time code, maximum 3 characters |
| `currency_decimal_places_snapshot` | Record-time integer precision, 0 through 8 inclusive |
| `amount` | Exact positive finite Decimal(38,8), less than `10^30`; currency precision rules below |
| `payment_method` | Same-company PaymentMethod FK |
| `payment_method_code_snapshot`, `payment_method_name_snapshot` | Record-time strings, maximum 32 / 160 characters |
| `external_reference` | Optional string, maximum 128 characters; blank stored as empty string |
| `idempotency_key` | Optional case-sensitive string, maximum 128 characters; blank stored as null |
| `notes` | Optional text; blank stored as empty string |
| `recorded_at` | Server-generated aware UTC instant, set once |
| `created_at`, `updated_at` | Existing aware timestamp primitives; unchanged on retry |

Database constraints require company-unique number, company-unique non-null idempotency key,
positive amount below `10^30`, and snapshot precision within 0..8. Cross-company membership and
exact precision are also service/model invariants; unsupported values fail before persistence.
No status, `is_active`, invoice/billing ID, amount_applied/amount_due/outstanding, allocation,
GL/journal, stock or tenant field belongs to Payment.

### Payer, currency and snapshot validity

For a NEW receipt, require an active same-company PERSON or ORGANIZATION Party; do not require
`is_customer` or `is_supplier`. Snapshot its current display/legal names once. Later Party rename
or deactivation changes neither history nor display. No client-name special cases exist.

For a NEW receipt, require an active Core Currency with integer precision 0..8. It may differ from
Company.base_currency; this authorizes no FX, revaluation, exchange gain/loss or journal posting.
Snapshot its code and precision once. Later Currency activity/precision/symbol changes do not
rewrite the receipt or change its amount formatting. Historical display uses the frozen code,
precision and exact amount, not current reference names/settings.

## Exact amount validation and presentation

Accept Decimal, integer (excluding bool), or Decimal-compatible numeric string. Strip numeric
strings and convert directly to Decimal; never pass through binary float. Reject float, bool,
unsupported objects, malformed/empty strings, NaN, positive/negative Infinity, zero, negative
values and values at or above `10^30`, with field-specific ValidationError before ordering or
persistence. Decimal/scientific notation is acceptable only when the resulting exact value meets
all domain rules. Do not permit conversion exceptions to escape as server errors.

The value must be exactly representable at the frozen currency precision `p`: an integer multiple
of `10^-p`, with `0 <= p <= 8`. Fractional scale means **nonredundant fractional digits**; removing
only trailing fractional zeros is representation normalization, not rounding. Thus USD precision 2
accepts `10`, `10.5`, `10.50` and `10.500`, but rejects `10.501`. JPY precision 0 accepts `100` and
`100.0`, but rejects `100.1`. Precision 8 accepts `0.00000001`, not `0.000000001`.
Database padding to eight places does not make a valid two-place value invalid on reload.

Decimal(38,8) allows up to 30 integer digits and eight fractional digits; the largest value is
`999999999999999999999999999999.99999999`. Currency precision may restrict it further.
No nonzero digit may be discarded, rounded or silently quantized to accept invalid input.
Validation/normalization must not use context-limited Decimal operations that round a 38-digit
value. Stored and compared values retain exact numeric meaning. Presentation pads accepted
amounts to exactly frozen `p` places without changing value; no current-currency rounding policy
is substituted. Display is **Receipt amount**, never a mutable financial balance.

## Number, dates and text normalization

Generate `PAY-` plus an uppercase UUID-derived value (32 hexadecimal characters). Database
`(company, number)` uniqueness is authoritative. Use a bounded module-local collision retry in a
savepoint, not `MAX(number)+1`, a fiscal sequence, or a shared numbering framework. Only a proven
number collision permits regeneration; unrelated integrity failures are not swallowed.
Localized fiscal numbering requires a later contract. Number never changes on receipt retry.

`payment_date` accepts a date (not datetime) or strict ISO `YYYY-MM-DD`; reject malformed dates,
noncanonical string forms and datetime values. Canonicalize before comparison/write. When omitted
or null on first creation, resolve once using `company_local_date(context.company_id)`. It is not
a settlement date. `recorded_at` comes from server time, is aware UTC, and is set once.

IDs accept UUID objects or UUID-compatible strings normalized to UUID identity; representations
of the same UUID compare equal. Reject invalid types/identities before persistence. Optional
external_reference, idempotency_key and notes accept string or null only. Strip surrounding
whitespace, preserve internal content/case, enforce bounded-field lengths after normalization;
null/blank reference and notes become `""`, null/blank key becomes null. No truncation, case-folding
of keys/references or hidden provider normalization occurs. external_reference is nonunique
human/business traceability, not retry identity. Provider transaction-ID uniqueness is future work.

## Idempotency: exact request identity and retry behavior

An absent key permits a new receipt for each valid call; identical data without a key is not
implicitly deduplicated. A present normalized key is unique within company on the selected database.
Authorize every call, including retries, before looking up/returning financial history.

The canonical comparison tuple is exactly:

```text
payer_party UUID
payment_date date
currency UUID
amount exact numeric Decimal value
payment_method UUID
normalized external_reference
normalized notes
```

Company and key locate the receipt. Actor, number, timestamps and derived snapshots are not
request identity. Equal valid numeric representations (`10`, `10.0`, `10.00`), canonical UUID
representations, ISO/date representations and normalized optional blanks compare identically.
Do not use rounded amounts, stringified database scale or current names as equality criteria.

On existing-key lookup, an omitted/null payment_date means the **existing receipt's frozen date**,
not newly computed today. An explicit date is compared normally and conflicts if different. Thus
an identical omitted-date retry after company-local midnight recovers the original receipt.
On first creation only, omission resolves to today's company-local date; concurrent same-key
waiters use the winning receipt's date. Callers wanting another dated receipt use a new key.

For a matching retry, revalidate active actor/company/context and `payments.payment.record`, then
compare IDs/payload against the persisted receipt and its frozen currency precision. Do not require
the original Party/Currency/method still to be active, refresh snapshots or re-evaluate precision
from changed reference data: this is recovery of history, not a new receipt. Permission/access
revocation still denies the retry. A different payload produces deterministic ValidationError/
conflict, never silent success or replacement. No timestamp or receipt/audit write occurs on match.

Concurrent same-key/same-payload calls produce one Payment and one `payments.payment.recorded`
audit and both return the same receipt. Different payloads have one winner and explicit conflict
for the other, with no partial writes. The Company lock serializes supported same-company calls;
database uniqueness is the final backstop. Any uniqueness-race handling uses a savepoint on the
same alias, re-reads the winning receipt, rechecks the tuple and distinguishes number collision,
retry-key conflict and unrelated integrity failure. Do not query a transaction left broken by an
IntegrityError. Separate companies/aliases have independent namespaces; no global retry cache.

## Permissions, services, selectors and audit

The exact future manifest permission vocabulary is:

| Permission | Authorized surface |
| --- | --- |
| `payments.method.view` | Company-scoped method list/detail |
| `payments.method.manage` | Method create/name update/activate/deactivate |
| `payments.payment.view` | Company-scoped receipt list/detail |
| `payments.payment.record` | New receipt recording and matching retry |

No payment update/delete/refund/allocate permission exists. Grants are independent, not implied
by Django staff/model permissions. Mutation services require their action permission, not an
incidental view permission from reusing a public read selector. Action forms may use private
company-scoped choices under that action grant. HTTP GET mutation forms and POST handlers enforce
the action permission; templates hide unauthorized actions. Public read selectors require the
matching view permission. Non-HTTP services authorize independently through BusinessContext/RBAC.

Minimum public state-changing services:

```text
create_payment_method(context, *, code, name)
update_payment_method(context, *, payment_method_id, name)
set_payment_method_active(context, *, payment_method_id, is_active)
record_payment(context, *, payer_party_id, currency_id, amount, payment_method_id,
               payment_date=None, external_reference=None, idempotency_key=None, notes=None)
```

All take IDs/data plus framework-neutral BusinessContext, never HttpRequest or untrusted model
instances as authorization/ownership evidence. No update/delete Payment service is provided.
Minimum reads: `payment_methods_for_company`, `payments_for_company`, `payment_detail`; any
method-detail adapter uses the same scope/view policy. Lists are deterministically ordered with
UUID tie-breakers, backend-paginated at 50 rows. Receipt reads include historical facts whose
references are now inactive and render snapshots rather than current mutable reference values.

Exact audit vocabulary: `payments.method.created`, `payments.method.updated`,
`payments.payment.recorded`. Activity changes use method.updated with actual changed-field
metadata. True method no-ops and matching receipt retries produce no success event. Method
mutations and first receipt creation append actor/company/object identity and minimal structured
change/receipt evidence through Core Audit within the business transaction. Do not duplicate
free-text/PII unnecessarily. Audit failure rolls back every business write; authorization/validation
failure leaves no success audit or partial receipt. Audit is evidence, not an authoritative balance.

## Transactions, locking and ORM invariants

All future mutations use `business_atomic` / `business_atomic_context()` at call/enter time:

```text
selected-alias business transaction
-> active Company row lock
-> current BusinessContext + action RBAC recheck after any wait
-> authoritative receipt/method/reference row locks
-> validation
-> business write + audit
```

For record_payment, after Company/auth, inspect a keyed existing receipt first and lock it if
present; matching recovery follows the historical retry rules above. For a NEW receipt, acquire
and re-read PaymentMethod, then Party, then Currency rows in that fixed order and validate current
activity/membership/precision before snapshot/write. Method administration takes Company/auth
then the authoritative method row. Re-read after waiting; no cached pre-lock authorization or
reference activity is reusable. Existing Party/Reference writers need not adopt new Payments
locks; their row updates serialize against these reference-row locks. New Payments paths preserve
Company-first ordering and do not introduce a generic lock framework or mutate another owner.

If method deactivation wins, the waiting new receipt fails; if recording wins, its receipt remains
valid and later deactivation may succeed without rewriting it. Name updates serialize against
recording so each receipt snapshots one committed method state. Revoked role, permission or
company access while waiting fails closed after Company lock. Company is business scope, not a
tenant; BusinessContext remains unchanged. Reads/locks/writes/audit/retry/savepoints use one
selected execution alias, with no implicit-default transaction, forced-default query, cross-alias
cached object/FK, mid-transaction alias switching, tenant_id or actual SaaS activation.

Payment normal public persistence must not bypass services: reject direct creation/mutation save,
instance deletion, QuerySet.update/delete, bulk_update, bulk_create/conflict-upsert and
update_or_create creation/update bypasses. Protect every field, including nonfinancial metadata
and timestamps, against stale instances and in-memory company/payer/currency/method substitution.
PAY-1 may use a narrowly private validated module-local persistence primitive, as accepted Billing
does, but no caller-settable public boolean permits creation or mutation. No Payment edit path is
hidden inside that primitive. PaymentMethod writes likewise require validated audited services;
public bulk/save/delete paths cannot bypass immutable company/code or authorized name/activity
changes. These guarantees cover supported ORM APIs, not arbitrary raw SQL, private-API abuse or
a malicious database administrator. Existing released migrations remain immutable.

## Future manifest, migration and presentation scope

Manifest: code `payments`, name `Payments`, version `0.1.0`, exact dependency/permission lists
above. Fresh registration is disabled. Updates preserve prior enablement, and historical
registration migrations freeze declarations locally rather than import mutable runtime constants.
No manifest, registration migration, permission record, installed-app wiring or navigation is
created in PAY-0.

Missing/disabled registry state hides Payments navigation and returns HTTP 404. Installed Python
services remain callable with valid BusinessContext/RBAC; module enablement is not service
authorization. This preserves ADR 0005/0006 and accepted Gate 4 semantics.

Future UI: method list/create/name-edit/activate/deactivate; receipt list/record/detail only.
Use the frozen BusinessOS shell, safe HTMX GET read-path/search/filter/pagination/query-history
patterns and non-JavaScript fallback; POST forms/actions stay normal Django. Bind every mutation
form to company and reject stale-company submissions before calling services. Verify direct
deep-links, action GET/POST RBAC and 50-row deterministic pagination. Preserve boundary-value
wrapping/local table scrolling and no page overflow at 390/768/1280px. No invoice-allocation,
refund, settlement, gateway, journal UI, redesign or current UI changes are authorized here.

## Allocation/balance deferral and later integration gate

PAY-1 exposes Receipt amount only. Do not expose Applied amount, Unapplied amount, allocation
status, invoice outstanding or fake zero-allocation assumptions in APIs/selectors/UI. ADR 0011's
earlier subsequent-gate mention of derived unapplied amounts is refined by this accepted deferral;
its authoritative ownership and accepted BILL-1 behavior remain unchanged.

PaymentAllocation stays Payments-owned but storage/schema/linkage is deferred to a separate
optional contract such as PAY-INT-1. Do not prematurely add an Invoice FK, allocation table or
generic integration engine. That gate must specify stable Billing invoice references without
unconditional Billing dependency; company/currency/frozen-precision agreement; payment availability;
invoice eligibility and complete allocation evidence; partial/over-allocation rules; PostgreSQL
lock ordering; retry/idempotency; audit; refund/reversal interaction; execution alias; and derived
outstanding. Absence/incomplete evidence must never be interpreted as zero paid. Future optional
Accounting composition calls Accounting services; it is not part of receipt recording.

## Required future PAY-1 verification

This contract defines acceptance tests; PAY-0 adds no runtime tests. PAY-1 must verify:

- PERSON/ORGANIZATION payer without customer role; active same-company new references; frozen
  payer/method/currency display after rename/deactivation/precision change; cross-company rejection.
- Method normalized-code uniqueness, immutable ownership/code, authorized name/activity changes,
  no-op audits, protected referenced deletion, and independent view/manage/record permission paths.
- Exact amount/type/range/precision boundaries, valid numeric strings, malformed strings,
  bool/float/nonfinite values, redundant zeros, eight-place maximum, direct ORM guards and rollback.
- Number uniqueness/collision handling, optional reference nonuniqueness, blank normalization,
  UUID/date canonicalization, omitted-date retry across company-local midnight, and incompatible
  payload conflicts. Matching retries after references retire/change preserve history; revoked
  actor/company access/permission still denies recovery. No timestamp/snapshot refresh.
- Real PostgreSQL row-lock coordination: same key/same payload -> one receipt/audit; same key/
  different payload -> one winner/conflict; role/permission and company-access revocation during
  Company-lock wait -> denial; method deactivation versus recording in both winning orders;
  method-name update versus snapshot; company/code creation uniqueness races. Assert persisted
  receipt/method and audit counts, not only returned values. No arbitrary sleeps as race evidence.
- Persistence/audit failure rollback, no success audit on failure, clean independent worker
  connections, non-default-alias receipts/retries/rollback/audit and independent alias namespaces.
  SQLite skips only genuinely PostgreSQL row-lock-specific cases, not ordinary boundary tests.
- Instance, stale-instance, QuerySet, bulk/upsert/update_or_create bypass rejection; all receipt
  fields immutable; method service-only mutation; no public creation flag or owner substitution.
- Missing/disabled HTTP/navigation, installed non-HTTP services with context/RBAC, fresh disabled
  registration and enablement preservation; frozen migration replay; module-local discovery.
- Action GET/POST permissions, stale-company form matrix, company-scoped list/detail and 50-row
  ordering/pagination, responsive boundary UI/fallback. Billing/Accounting absent at startup and
  runtime; no forbidden import, dependency, write, balance selector or extra permission.
- Fresh PostgreSQL zero-state bootstrap, full PostgreSQL/SQLite and local suites, Ruff, Django
  checks, migration drift, database architecture guard, npm/Tailwind/CSS reproducibility, exact-head
  hosted CI and independent PAY-1 audit before separately authorized acceptance/adoption.

## Explicit deferrals and consistency outcome

Defer PaymentAllocation/invoice integration, applied/unapplied/outstanding, refunds/reversals,
chargebacks, gateways/capture, reconciliation/settlement, outgoing/vendor/AP payments, Accounting
posting, FX/revaluation, fees, multi-party splitting, advance-credit application, customer
statements, provider-specific identities and fiscal/localized numbering. No generic workflow,
event bus, Redis/Celery, custom framework or SaaS activation is introduced.

Consistency review: one owner per receipt, invoice, allocation and journal; no duplicate mutable
balance, Billing/Payments dependency cycle or Core-to-module import. Core Audit records evidence;
Party/Reference/Organization supply identities and time; Access authorizes; Core Database selects
execution infrastructure. Payment existence is sufficient for the MVP, so no baseline contract
requires a speculative status field. No unresolved PAY-1 architecture decision is deliberately
left within this accepted scope; deferred features require their own future decisions. Gate PAY-0
is formally accepted, with canonical adoption pending; this is not PAY-1 implementation approval.
