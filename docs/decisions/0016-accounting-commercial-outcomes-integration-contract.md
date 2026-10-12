# ADR 0016 — Accounting Commercial Outcomes Integration Contract

Status: Accepted — Gate ACC-INT-0

Date: 2026-10-12

## Authority, baseline and evidence

This documentation/architecture contract is **FORMALLY ACCEPTED**. Canonical adoption is
**PENDING at this acceptance checkpoint**, subject to separate exact-head acceptance and main CI.
Audited proposal `207c78096f419b4d924326df256355a356a3f3d7` and its technical text below are
preserved unchanged; proposal-stage next-decision/status language is historical, superseded by
the [formal acceptance record](#independent-approval-and-formal-acceptance--2026-10-12).
Named proposed APIs/models/permissions remain unimplemented future declarations, not runtime code.
**ACC-INT-1: NOT STARTED / NOT AUTHORIZED.** No production approval or SaaS activation is granted.
Canonical starting main is `a1079985a2ef5645dfed338e3e58af54f5242e1a`.

PAY-INT-1 is **CANONICALLY CLOSED** at that SHA. Its original implementation
`4b8a072da4426a48988d4605641bf1fc846c06ee` received independent REVISE / readiness C;
corrective implementation `bef50fe8b20f97aaeefb8c610a46d412e9a05402` received the supplied
independent FINAL PASS / readiness A. PAYINT1-R1/R2/R3/R4 are RESOLVED. Hosted Phase 0 checks
[implementation #118 / 38162359131](https://github.com/sahinkhan/djangobusinessos/actions/runs/38162359131),
[acceptance #119 / 38163571737](https://github.com/sahinkhan/djangobusinessos/actions/runs/38163571737)
and [main #120 / 38164395135](https://github.com/sahinkhan/djangobusinessos/actions/runs/38164395135)
all succeeded; each passed **1,613 PostgreSQL tests** and mandatory checks. #118 tested the
corrective SHA; #119/#120 tested the canonical SHA. These are prior hosted results, not new
ACC-INT-0 tests. No PAY-INT-1 tag is specified or invented. Historical failures and acceptance-stage
pending wording remain in the [Phase 2 plan](../exec-plans/active/PHASE_2_COMMERCIAL_CORE.md).

This proposal fills the separately deferred external-posting seam in accepted
[ADR 0014](0014-standalone-accounting-finance-contract.md), following
[ADR 0011](0011-modular-billing-payments-accounting-boundary.md) ownership,
[ADR 0013](0013-standalone-payments-contract.md) receipts and
[ADR 0015](0015-billing-payments-allocation-integration-contract.md) allocations.
[ADR 0002](0002-hard-dependencies-and-optional-integrations.md) governs optional composition;
[ADR 0005](0005-deployment-module-gating-and-simple-variant-lifecycle.md),
[ADR 0006](0006-phase-2-commercial-core-contracts.md) and
[ADR 0012](0012-tenant-ready-database-execution-foundation.md) retain HTTP-only enablement,
immutable owner facts and selected-alias transactions. No accepted technical body changes here.

## Verified existing APIs versus proposed additions

Repository evidence below was inspected at the pinned canonical SHA. A named **proposed** API,
app, permission, model or audit action in this ADR does not currently exist.

| Owner / current evidence | Verified capability | Bounded future addition |
| --- | --- | --- |
| Billing `selectors.py`, `services.py`, `models.py`, `domain.py`, `manifest.py` | `invoice_financial_basis` / `InvoiceFinancialBasis`, version 1, locks Company then Invoice, rechecks view authority; exact owner SQL line products and `finalize_total`; issued immutable state; `invoice_date` persisted but absent from basis DTO | Read-only `invoice_accounting_basis`, new `InvoiceAccountingBasisV1`, adding the locked owner's invoice date to existing validated financial facts; no arithmetic or mutation change |
| Payments `selectors.py`, `services.py`, `manifest.py` | `payment_receipt_basis` / `PaymentReceiptBasis`, version 1, includes immutable `payment_date`, currency provenance, payer and amount; receipt recording locks Company, Method, Party, Currency | Reuse receipt basis; no new receipt mutation or base integration dependency |
| Payments-owned optional `payments/integrations/billing/` | `create_payment_allocation`; `evidence_profile`, `validate_history`, bounded allocation evidence; Company -> Payment -> Invoice locks, compound view grants, immutable keyed allocation | Public read-only `allocation_accounting_basis` / `AllocationAccountingBasisV1` by allocation UUID, owned here; stabilizes stored parents and certifies complete valid allocation provenance, without returning arbitrary histories |
| Accounting `services.py`, `selectors.py`, `models.py`, `manifest.py` | Public create entry, add line and post entry services compose within nested alias-aware atomic blocks; frozen base precision; Entry -> Journal -> ordered lines -> UUID-ordered Accounts -> UUID-ordered Parties on post; scoped reference selectors and entry detail | Read-only `posted_journal_basis` / `PostedJournalBasisV1` for bounded locked historical validity/readback. No new write primitive is required; reuse the three public mutation services |
| Core `access/policies.py`, `audit/services.py`, `modules/manifest.py`, `modules/services.py`, `database/router.py`, `database/transactions.py` | Active registered permissions required even for limited superuser bypass; append-only caller-authorized audit; underscore module codes and own-prefix permissions; installed `businessos.modules.*` routing; same-alias nested savepoints | No Core change, bypass authority, dynamic installer or generic integration framework |

Existing Accounting post retry returns a POSTED Entry early. That alone is **not** proof of
external source/header/line equivalence. The proposed bounded posted-basis read supplies that proof.
Existing PAY-INT catalog checks are useful prior evidence, not a sufficient automatic certificate
for new Accounting/binding relations. The stronger complete-evidence profile below is required.

Proposed read signatures and minimum DTO fields are fixed as follows:

- `billing.invoice_accounting_basis(context, invoice_id, *, lock=True)` returns version 1:
  Invoice UUID, Company UUID, bill-to UUID, ISSUED state, aware issued_at, canonical invoice_date,
  Currency UUID, frozen code/precision and owner original_total. It reuses Billing's financial
  basis under the same Invoice lock; no notes or line descriptions, no extra invoice arithmetic.
- `payments_billing.allocation_accounting_basis(context, allocation_id)` returns version 1:
  Allocation UUID/Company/created_at/updated_at, stored Payment and Invoice UUIDs, exact amount,
  payer and bill-to UUIDs, both parents' Currency UUID/code/precision, original receipt amount and
  invoice total, Payment.payment_date/recorded_at and Invoice.issued_at. It takes Company -> stored
  Payment -> stored Invoice, enforces allocation.view plus both owner views, runs the admitted
  profile and complete owner history validation, and rejects intrinsic/cumulative corruption.
  No current remaining capacity/activity prerequisite is added. Output is one bounded immutable DTO.
- `accounting.posted_journal_basis(context, entry_id, *, lock=True)` requires entry.view, locks
  Company then requested Entry (unless already stabilized under the required outer Company lock
  with lock=False), and returns version 1: header identity/Company/Journal/number/date/memo/frozen
  code/precision/status/posted_at/timestamps, exact debit/credit totals and the bounded requested
  line facts (UUID/Company/parent/position/Account/type/Party/description/debit/credit/timestamps).
  This is a bounded commercial-effect read contract, not a new general reporting API: complete
  count/integrity probes precede payload construction, and exactly two lines are required before
  materializing. Other manual journals retain their existing selectors and are not certified by
  this basis. No mutation grant/bypass.
- `accounting_billing.invoice_posting_reference(context, invoice_id)` returns a scoped immutable
  version-1 reference (binding UUID/Company/source/effect/Entry/Journal/AR/Revenue/timestamps) or
  known absence only after profile/raw-provenance checks, under an outer Company lock. Requires
  invoice-posting.view, billing.invoice.view and accounting.entry.view. It acquires no Entry lock,
  so the allocation component can gather at most two existing Entry IDs before locking them in
  UUID order. It is **not** a POSTED validity certificate; the full posted basis must be checked
  before using its AR or returning success. Source-total authority remains Billing's basis.

All non-locking modes require an already active selected-alias transaction with the same Company
stabilized; arbitrary cached/out-of-transaction DTO invocation cannot certify composition. Owner
view grants, schema admission and scope are checked on each call. Exact completeness/readback is
separate from a minimal immutable reference used only to establish deterministic lock order.

## Two effects and owner boundaries

Exactly two **explicitly requested**, downstream effects are proposed:

| Effect identity | Source / amount authority | Exact two-line journal |
| --- | --- | --- |
| `billing_invoice_ar_revenue_v1` | Eligible ISSUED Invoice; Billing's authoritative original total `X > 0` | Position 1: AR debit X / credit 0, bill-to Party. Position 2: Revenue debit 0 / credit X, Party null |
| `payment_allocation_cash_ar_v1` | Eligible immutable PAY-INT-1 PaymentAllocation; its exact `amount X > 0` | Position 1: Cash/Bank debit X / credit 0, Party null. Position 2: AR debit 0 / credit X, payer/bill-to Party |

Billing retains Invoice/InvoiceLine, lifecycle, snapshots and original amount. Payments retains
Payment/PaymentMethod; its optional `payments_billing` component retains PaymentAllocation and
applied/unapplied/outstanding composition. Accounting retains Account, Journal, JournalEntry,
JournalEntryLine, posting validity and derived GL/TB. Source reads are public and owner-owned;
only Accounting public services write journals. No source `accounting_posted` flag, duplicate
amount/balance ledger, mutable Account balance or journal-derived invoice outstanding is introduced.

Invoice issue, receipt recording and allocation creation **do not** call these integrations.
Posting means an explicit integration operation after those facts exist, not automatic issue-time
recognition. Each invoice recognizes Revenue/AR at most once; each allocation clears AR at most
once; a receipt alone never additionally clears AR; allocations never recognize Revenue.
Unallocated money has no accounting policy in this gate. No tax/product/category split or COGS.

## Selected optional topology and installation

Select **two Accounting-owned opt-in Django apps**, not one app that unnecessarily imports Payments
to post invoices. Exact proposed packages, labels/codes, version and direct manifest dependencies:

```text
businessos/modules/accounting/integrations/billing/
  accounting_billing, 0.1.0 -> accounting, billing

businessos/modules/accounting/integrations/payments_billing/
  accounting_payments_billing, 0.1.0 -> accounting, accounting_billing, payments_billing

payments_billing, already installed optionally -> billing, payments
```

The allocation component deliberately also requires `accounting_billing`: **the corresponding
positive invoice must already have a complete valid posted AR/Revenue binding**. This bounded
prerequisite prevents clearing an arbitrary/unrecognized AR account. It is a new proposed
integration eligibility rule, not a change to standalone allocation validity or PAY-INT-1.
The supplied AR account must equal that invoice binding's AR account. Cash/Bank and its Journal
remain explicit per request. No implicit invoice posting, backfill, request to create Payment,
or account inferred from PaymentMethod is allowed. An absent invoice posting yields
`invoice_accounting_not_posted` with no allocation journal. A corrupt/unavailable prerequisite
is an evidence error, not ordinary absence. Allocation accounting can follow a fully allocated
invoice; unused source capacity is not re-consumed. Zero invoices cannot have positive allocations.

The invoice path works without Payments/PAY-INT. A combined app was rejected for that unnecessary
dependency. An independent allocation app without invoice-posting provenance was rejected for
unmatched/arbitrarily routed AR credits. A generic polymorphic binding/rule registry is unnecessary.
Direct Accounting dependency is retained because both apps call its public services; the other
dependencies are the exact source/prerequisite contracts consumed, with no reverse import.

Proposed explicit configuration flags are `BUSINESSOS_INSTALL_ACCOUNTING_BILLING` and
`BUSINESSOS_INSTALL_ACCOUNTING_PAYMENTS_BILLING` (`1` opts in, unset/`0` absent). They do not
auto-install or auto-enable dependencies. Future static URL/component wiring belongs only to opted-in
configuration, never eager imports from base owners. App namespaces match the existing router;
underscore codes and `<module>.<resource>.<action>` permissions match existing manifest validation.
Future initial/registration migrations belong to each optional app, depend on the pinned owners
and invoice app where required, freeze local permission declarations, register disabled by default
and preserve existing enablement. No released migration is edited. Uninstall/history destruction
is not an approved operation. Today no setting, manifest or migration is added.

| Required tested installation | Result contract |
| --- | --- |
| Accounting alone / Billing alone / Payments alone | Existing standalone behavior unchanged |
| Billing + Accounting, no integration | No automatic entry; posting capability not installed |
| Payments or PAY-INT without Accounting integration | Receipt/allocation behavior unchanged, no ledger effect |
| Billing + Accounting + `accounting_billing`, no Payments | Invoice effect available independently |
| PAY-INT + Accounting + both Accounting integrations | Allocation effect after explicit valid invoice posting |
| All optional apps | Two separate, retry-safe effects; no cycle/startup import failure |
| Either optional app without any declared or transitive owner/prerequisite | Explicit configuration/bootstrap failure before serving; never guessed absence or automatic resolver |

## Account selection, currency, date and Party policy

**Select explicit UUIDs per request**, not a configuration table. This avoids introducing account
mapping lifecycle, defaults or policy-version management for two operations. A small configuration
was considered but rejected as unnecessary for the minimum gate; a future policy may replace this
only through separate versioned review. Source modules own no chart routing. No generic chart,
tax, product/category, method/provider or country/client mapping engine is proposed.

Positive invoice requests require `journal_id`, `ar_account_id`, `revenue_account_id`.
Allocation requests require `journal_id`, `cash_account_id`, `ar_account_id`; AR must additionally
equal the already-posted invoice binding. For NEW positive effects all selected identities are
same-company on the selected alias, Journal active, AR ASSET, Cash/Bank ASSET, Revenue INCOME,
and Accounts active. Cash/Bank and AR must be distinct UUIDs. AR and Revenue cannot be the same
Account because their immutable types differ. ACC-1 has no cash/control-account subtype or Journal
type; operator selection does not certify a bank account or settlement. No Account/Journal creation
is implicit. Renaming is irrelevant to identity; reference retirement cannot spoil valid retries.

Company.base_currency UUID is the authoritative unit. Source Currency UUID must equal it and
source frozen code must equal that immutable reference code. Equal code alone is insufficient.
Allocation Payment and Invoice must also share UUID, frozen code and frozen precision exactly
under ADR 0015, with matching payer/bill-to UUID. No FX or precision conversion.

Billing supplies the once-rounded original total at its frozen precision `p_source`; this proposal
does not multiply/sum/round InvoiceLines itself. Allocation supplies its stored exact amount.
All source precisions are integer 0..8 and amounts finite, nonnegative for invoices, strictly
positive for allocations, below `10^30`. Account lines use Decimal(38,8), no floats, booleans,
NaN/infinity, implicit truncation or ambient-context rounding.

On NEW entry creation, **reuse ACC-1's current base precision snapshot** `p_entry`, captured by
`create_journal_entry`; do not override it with a historical source precision. `p_entry` may differ
from `p_source` because Reference precision can change. Accept only if the exact source amount is
representable at both frozen precisions without discarding any nonzero digit. For example source
12.34 at p=2 fits a new entry at p=3; source 12.345 at p=3 does not fit p=2. Reject incompatibility
and roll back the new draft, lines and creation audit. Redundant zeros are equivalent values.
After creation use that Entry's frozen precision for all validation; a concurrent later Reference
precision change does not refresh it. Matching retries use persisted Entry precision, never today's
Reference precision. This retains ACC-1 semantics without a new currency snapshot/write API.

Dates have **no caller override**: invoice Entry.entry_date = immutable Invoice.invoice_date;
allocation Entry.entry_date = its immutable Payment.payment_date, not allocation creation date,
server today or recorded_at. No fiscal period/backdating control is claimed. A backdated receipt
may produce an entry date before invoice_date, preserving actual source dates, not rewriting them.
Posting occurrence remains the server-generated first Accounting posted_at.

Party policy is fixed as in the effect table. PAY-INT requires payer = bill-to; that UUID is the AR
credit Party. Revenue/Cash Parties are null. A Party must remain same-company and PERSON/ORGANIZATION;
ACC-1 additionally requires it active for NEW assignment/initial post. Thus a retired Party may
leave a valid source outcome not currently NEW-post eligible; no reactivation or alternate Party
is silently chosen. Historical retries validate ownership/type but not activity. No customer/supplier
role or receivable subledger is inferred. Stable Party IDs are traceability, not balance authority.

## Zero-total invoice outcome

An issued base-currency invoice with complete valid total exactly zero returns
**`NO_ACCOUNTING_EFFECT`**. No Entry, line, binding, success audit or timestamp is created.
All three account-selection arguments must be null/omitted for this case; supplying any is a
validation error, not silently ignored configuration. Positive invoices require all three UUIDs.
The result is source-derived, not a saved posted boolean or a claimed ledger posting.

Each authorized zero retry revalidates complete immutable source and posting evidence and returns
the same source/effect zero outcome. A positive binding referencing a now-zero basis is corruption
and fails closed; never prefer zero before inspecting hidden/contradictory binding evidence.
No zero-debit/zero-credit lines or artificial balanced-zero Entry are allowed. No durable zero-run
reservation is needed because supported issued source mutations cannot change that amount.

## Durable effect-specific binding schemas and canonical identity

Select two **immutable Accounting-integration-owned provenance models**, not a universal ledger:
`accounting_billing.InvoicePosting` and
`accounting_payments_billing.AllocationPosting`. Every non-null relationship uses PROTECT and a
validated same-alias PostgreSQL NO ACTION FK backstop. All fields are immutable after first commit.

| Field | InvoicePosting | AllocationPosting |
| --- | --- | --- |
| `id` | UUID PK, generated once | UUID PK, generated once |
| `company` | Required Company FK | Required Company FK |
| `invoice` / `allocation` | Required Billing Invoice FK | Required payments_billing PaymentAllocation FK |
| `effect` | Non-null bounded string, maximum 40; CHECK exactly `billing_invoice_ar_revenue_v1` | Non-null maximum 40; CHECK exactly `payment_allocation_cash_ar_v1` |
| `journal_entry` | Required unique Accounting Entry FK | Required unique Accounting Entry FK |
| `journal` | Required Accounting Journal FK | Required Accounting Journal FK |
| `ar_account` | Required Accounting Account FK | Required Accounting Account FK |
| `revenue_account` / `cash_account` | Required Accounting Account FK | Required Accounting Account FK |
| `invoice_posting` | Not a field | Required InvoicePosting FK; protected prerequisite provenance |
| `created_at`, `updated_at` | Existing aware UTC timestamp convention, set once | Same; retries never refresh |

No null fields, stored amount/balance, copied source payload, currency snapshot, mutable status,
caller key or reconciliation flag. Source UUID plus fixed effect is the natural retry identity;
explicit account/journal choices are request payload, not a second retry key. Database uniqueness:
`(company, invoice, effect)` / `(company, allocation, effect)`, and unique journal_entry in each
binding table. Entry company/journal and line account/Party/value correspondence are service and
readback invariants, not fictional cross-table CHECKs. Cross-app checks also prohibit one Entry
being bound by either effect to another source; Company-first serialization and a common Entry
lock protect the public service check. Supported services create a **fresh** Entry and never accept
an existing Entry ID, so cross-effect Entry reuse has no ordinary creation route. No claim that
per-table unique constraints alone enforce cross-table uniqueness against arbitrary SQL.

All normal instance/save/delete, queryset/bulk/update/upsert/convenience/async bypasses must reject.
One narrowly private validated insertion per app suffices; integrations do not borrow Accounting's
private tokens. Arbitrary privileged SQL or private Python abuse is outside supported ORM guarantees.

Canonical payload is version 1, comparing typed values, not a hash as sole proof:

```text
Invoice: Company UUID, Invoice UUID, fixed effect,
         Journal UUID, AR UUID, Revenue UUID,
         Billing original_total, invoice_date, bill-to UUID,
         source Currency UUID/code/precision, issued_at,
         fixed two-line/Party/memo policy v1.

Allocation: Company UUID, Allocation UUID, fixed effect,
            stored Payment UUID, Invoice UUID, InvoicePosting UUID,
            Journal UUID, Cash/Bank UUID, AR UUID,
            allocation.amount, Payment.payment_date, shared payer/bill-to UUID,
            matching source Currency UUID/code/precision,
            fixed two-line/Party/memo policy v1.
```

Amounts compare exact numeric Decimal values, UUID strings normalize to UUID, dates are canonical
date objects, instants compare as aware UTC. Actor, new binding/Entry/line UUIDs, generated Entry
number, current names/activity, current Reference precision and server timestamps are not caller
request identity. Persisted Entry precision is intrinsic generated history, not a caller override.
Derive all financial/date/Party facts from trusted owner reads; callers supply source and account/
Journal IDs only. Request-supplied facts, ORM objects, cached DTOs or free text cannot override them.

Exact memo: `ACC-INT-1 v1 invoice <canonical Invoice UUID>` or
`ACC-INT-1 v1 allocation <canonical Allocation UUID>`. Descriptions append ` / AR`, ` / Revenue`
or ` / Cash-Bank` as appropriate. No mutable notes/names are copied. Readback compares these exact
strings and the two fixed positions. The normal Accounting number remains its generated JE-UUID.

## Public operations, composition and retry

Proposed integration operations (BusinessContext plus IDs, never HttpRequest):

```text
accounting_billing.post_billing_invoice_outcome(
    context, *, invoice_id, journal_id=None, ar_account_id=None, revenue_account_id=None)

accounting_payments_billing.post_payment_allocation_outcome(
    context, *, allocation_id, journal_id, cash_account_id, ar_account_id)
```

Each returns a bounded immutable PostingOutcomeV1: source/effect, tagged result, and for POSTED
the original binding/Entry UUID, number, exact amount/date/unit/precision, original posted_at and
created_at. Zero has amount zero and null ledger fields. No lazy cross-alias model payload.

After Company lock, current compound authorization and compatibility checks, find the scoped
existing source/effect binding **before NEW eligibility**. Stored binding/source parents supply
lock/reference IDs. Validate intrinsic source, prerequisite and complete posted Entry/lines first;
then compare normalized requested Journal/Account IDs to stored IDs. A valid conflicting UUID,
even nonexistent/retired/wrong-company, gives `idempotency_conflict` without fetching that
requested foreign record. Malformed UUID remains input validation. Matching recovery returns
the original with no journal/line/binding/audit/time write. Another currently authorized actor can
recover it after response loss or restart. Never redo remaining allocation capacity, require fresh
reference activity, or recapture current currency precision for historical recovery.

Intrinsic validity includes correct source state/date/amount/unit/Party, allocation amount <= each
immutable original parent capacity, valid whole allocation provenance, prerequisite InvoicePosting,
same-company refs, immutable type compatibility, POSTED with aware posted_at, exact two one-sided
balanced positive lines, frozen precision, deterministic memo/date/Parties and one-to-one binding.
An existing row pointing to DRAFT, missing/extra/mismatched lines, wrong source/Entry ownership,
wrong effect or corrupt prerequisite fails closed; do not return early just because a row exists.

NEW positive composition uses one outer `business_atomic_context()` on the selected alias:
public Accounting `create_journal_entry` -> two `add_journal_entry_line` calls ->
`post_journal_entry` -> validated binding insertion -> integration audit. Existing services'
nested savepoints join that outer transaction; **no committed unbound draft or posting** survives
failure. Scoped public Account/Journal selectors validate types/choices under the explicit grants
below; mutation services revalidate activity under their own locks. No direct Accounting writes,
private persistence imports or synthetic elevated context. Proposed source bases and the posted
readback basis are the only necessary owner API additions, all read-only and separately tested.

Any Entry/line/post/binding/audit failure rolls back all Accounting and integration facts/audits.
Billing issue/Payment/Allocation remain unchanged. A crash before commit has no effect; a crash or
response loss after commit recovers the one durable binding. No on_commit/background delivery,
filesystem/distributed atomicity or external-bank guarantee is claimed.

Only a positively identified source/effect uniqueness violation permits recovery: surround the
**whole new composition**, not just binding INSERT, with an alias-aware savepoint. Roll it back
before reading the winning binding, reacquire/recheck scope/authority and intrinsic payload, then
return or conflict. Otherwise a losing unbound Entry could survive. Unrelated IntegrityError
propagates and rolls back. UUID/Entry-number collision handling remains bounded (at most three
attempts); no catch-all retry loop or querying a broken transaction. Supported Company serialization
normally avoids a source-key collision, but database uniqueness remains the backstop.

## Exact lock protocol, alias and authorization linearization

Observed existing order: Billing mutation Company -> Invoice -> Party -> Currency -> affected
lines; its basis Company -> Invoice. Payments recording Company -> keyed receipt (retry), or
Method -> Party -> Currency (NEW). PAY-INT uses Company -> Payment -> Invoice, no mutable-reference
activity locks. Accounting post uses Company -> Entry -> Journal -> lines(position,id) ->
Accounts(UUID) -> non-null Parties(UUID). Preserve those orders, not guessed inverse owner calls.

Proposed invocation paths:

1. Resolve configured alias at outer transaction entry; perform catalog-only identity/visibility
   admission before authorization, migration or financial data reads. Lock active Company, then
   revalidate actor/context and **every** required current grant and complete schema admission.
   A failed visibility admission is not safe authorization or evidence of absence.
2. HTTP only: lock all required registry rows once in ascending code order, recheck enablement
   and all authority after waits, hold through commit. Python skips registry admission.
3. Invoice: use Billing accounting basis to lock Invoice and recheck authority. Allocation:
   use stored allocation identity to resolve and lock Payment **then** Invoice through public
   owner bases, rechecking the entire compound permission set after either wait. Immutable
   Allocation is re-read/validated after parent locks, not an authority to reverse their order.
4. Read existing immutable source/effect binding; if present its Entry is locked before Accounting
   references. Allocation also validates the InvoicePosting prerequisite; when both existing
   Entries are involved, lock their UUIDs in ascending order before Journal/lines/reference locks.
   This bounded two-entry set is not an unbounded report lock. Never take Payment after Invoice.
5. NEW: create a fresh private-to-this-transaction draft via Accounting's public create service
   (which locks Journal); only this transaction can see that new Entry. For that new Entry reuse
   public add-line/post protocols; subsequent Entry/Journal/ref locks are reentrant where already
   held. Post itself retains Entry -> Journal -> ordered lines -> Accounts -> Parties. Source and
   existing prerequisite Entries are acquired before creation. No other actor can contend on the
   uncommitted new Entry, so its creation-time Journal lock introduces no shared Entry inversion.
6. Recheck compound authority after any blocking lock and immediately before completing effect
   plus audit. Validate scoped choices after their lock waits. Commit once at outer boundary.

Company-first serialization already spans supported Access/Billing/Payments/Accounting writers
on that Company; this uses the existing coarse lock rather than inventing a new global lock.
Permission/access revocation committed while a call waits must be seen and denied after waiting.
If the admitted operation commits first, subsequent revocation/retirement cannot undo that fact.
Journal/Account writers take Company before own rows; NEW eligibility uses the winning committed
state, historical retries retain valid retired history. Reference/Party row updates remain covered
by Accounting's existing locks; immutable issued/receipt facts are never refreshed.

All reads, locks, catalog checks, migration records, binding/prerequisite queries, owner bases,
savepoints, Entry/lines, audit and status use that single alias. Router namespaces are infrastructure,
not Company authorization. Reject alias switching/cross-database objects or IDs paired with foreign
evidence; never fallback to default or a privileged connection. Actual tenant routing/SaaS deferred.
Read selectors hold Company/source/Entry stabilization and materialize DTOs before releasing locks;
no mixed earlier source total/later posting lookup or cached evidence is accepted.

## Complete-evidence compatibility and historical validity

Before migration recorder, source financial reads, retry/absence or reconciliation, the future
optional component must admit **its actual proof closure**, not borrow PAY-INT's certificate.
For invoice: Company/base Currency, Invoice/InvoiceLine, Party, Accounting Account/Journal/Entry/
Line, InvoicePosting and migration recorder. Allocation adds Payment/Method/Allocation and both
posting tables. Authorization/audit participation adds identity User, Company/Branch/Warehouse,
Access company/branch/warehouse grants, role/assignment/link/Permission, BusinessModule for HTTP,
and AuditEntry. Include every relation actually relied on; no incidental unrelated module scan.

Pin schema expectations from canonical owner migrations plus future reviewed optional migrations,
not dynamically infer expected constraints from the database being validated. Before querying
coverage, verify schema-qualified approved relation identity (baseline `public`), ordinary-table
kind `r`, current search-path resolution to that same OID and no shadow/relocation ambiguity.
Catalog joins use `pg_catalog` and actual OIDs; no wildcard system-namespace exclusion. A non-public
or changed-resolution deployment requires separate compatibility review, not silent normalization.

For these proof relations, **reject any RLS/forced-RLS flag or policy, including disabled policies**,
even when the current role could bypass it. This conservative supported profile admits ordinary
non-superuser/non-BYPASSRLS readers without policies and never selects privilege to recover hidden
rows. No RLS disablement or security setting change. Unsupported RLS could hide a complete subtree
or prior binding and make SUM/NOT EXISTS falsely plausible. Fail before financial/absence reads.

Verify approved migration heads and public basis versions; reject unknown/backfilled history and
missing coverage. Verify actual columns, nullability, types/scale, PK/unique identity and fixed
validated CHECK definitions, not merely constraint names or mentioned substrings. Validate each
relied-on FK by source/target OIDs and ordered columns, **convalidated=True** and expected NO ACTION
delete behavior; Python PROTECT alone is insufficient. This includes source/child, Company/base
Currency, Account/Journal/Entry/Line/Party and each binding/prerequisite edge. Same-field NOT VALID,
missing/weakened FK/CHECK or substituted table cannot establish compatibility. New migration-derived
profile constants must be fixed in ACC-INT-1 and independently probed, not invented as present code.

Raw SQL EXISTS probes check either ownership endpoint before INNER JOIN filtering: Company,
referenced source, bound Entry and prerequisite can all bring a malformed row into scope. Detect
orphans, cross-company/duplicate binding, unsupported effect, extra/missing Entry lines, invalid
amount/position/Party/currency, and conflicting source/Entry provenance even off-page/outside UI
filters. Do not SUM only valid-looking remaining rows. Billing alone computes Invoice totals from
complete lines. Payments alone certifies complete allocations and both original capacities through
its proposed public basis, reusing its owner history validation rather than copying arithmetic.
Accounting supplies bounded complete posted basis; no narrow numeric SUM cast or float conversion.

Checks and amounts must use coherent selected-alias Company-stabilized evidence in the same
transaction; no cross-call cached success certificate. Acquire transaction-duration ACCESS SHARE
locks on the qualified proof relations in ascending verified OID order before the final profile
check; recheck identities after acquisition. This prevents DROP/relocation/replacement and ordinary
ACCESS EXCLUSIVE table/constraint alterations from committing during proof, without blocking
ordinary row writers or adding a global business mutex. Verify those actual DDL conflicts in tests.
ACCESS SHARE does **not** serialize every policy/catalog maintenance operation (for example policy
DDL with weaker lock modes). Concurrent security-policy, role-privilege, migration or unsupported
catalog changes require operator maintenance/drain and are outside this supported execution
profile. Do not claim jointly atomic catalog/security administration or that row locks protect
against a malicious DBA. The exporter/maintenance framework is not reused or expanded here.

Unavailable/corrupt evidence blocks NEW posting and successful retry. Original owner facts remain
readable under their ordinary contracts, but unknown posting evidence is **never NOT_POSTED**.
Historical validity does not depend on live names/activity/remaining capacity/current precision;
it does require valid immutable source amounts, dates, units, references and exact posted facts.

## Compound RBAC, HTTP admission and audit

Proposed permissions, **only** if future optional migrations install their declarations:

```text
accounting_billing.posting.view
accounting_billing.posting.create
accounting_payments_billing.posting.view
accounting_payments_billing.posting.create
```

Each app declares just its own two codes. These are not created by ACC-INT-0.

| Operation | Required current registered permissions (all, not alternatives) |
| --- | --- |
| Invoice status/provenance | `accounting_billing.posting.view`, `billing.invoice.view`, `accounting.entry.view` |
| Invoice post / retry / zero request, action GET/POST | `accounting_billing.posting.create`, `billing.invoice.view`, `accounting.entry.view`, `accounting.account.view`, `accounting.journal.view`, `accounting.entry.create`, `accounting.entry.update`, `accounting.entry.post` |
| Allocation status/provenance | `accounting_payments_billing.posting.view`, `accounting_billing.posting.view`, `payments_billing.allocation.view`, `payments.payment.view`, `billing.invoice.view`, `accounting.entry.view` |
| Allocation post / retry, action GET/POST | `accounting_payments_billing.posting.create`, `accounting_billing.posting.view`, `payments_billing.allocation.view`, `payments.payment.view`, `billing.invoice.view`, `accounting.entry.view`, `accounting.account.view`, `accounting.journal.view`, `accounting.entry.create`, `accounting.entry.update`, `accounting.entry.post` |

Accounting reference-view grants are deliberately required to consume existing public scoped
choice/type selectors; both posting operations require entry.view for complete posted-basis
validation/recovery. No hidden new manage authority. Allocation posting additionally reads
invoice-posting provenance, hence its explicit view grant. No receipt.record, invoice.issue,
allocation.create, Account/Journal.manage, staff or Django model-permission substitute is needed.
Action authority does not imply its own posting.view; rendering a read panel/link separately needs
the read grants. All current mutation grants remain required even for matching/zero retries.
Missing/inactive declarations deny before Core's limited superuser bypass; scope never bypassed.

HTTP prerequisite row sets are fixed, locked in the shown ascending code order:

```text
Invoice: accounting, accounting_billing, billing
Allocation: accounting, accounting_billing, accounting_payments_billing,
            billing, payments, payments_billing
```

Missing/disabled any relevant prerequisite means hidden action/component or integration URL 404.
Only HTTP checks enablement, once under outer Company-before-registry locks through commit;
no nested admission with a different registry order. If disablement wins, waiting POST rejects;
if POST admission wins, disablement waits until completion. Stale GET never authorizes POST.
Installed Python APIs require schema, BusinessContext and compound RBAC, **not registry enablement**.
Module registration preserves enablement; no dependency resolver, licensing or dynamic installer.

Accounting-owned integration audit actions are exactly **`accounting.invoice_posting.created`**
and **`accounting.allocation_posting.created`**, with object types
`accounting.InvoicePosting` / `accounting.AllocationPosting` and binding UUID. Record Company,
actor, source UUID/effect, Entry UUID, Journal/Account UUIDs, exact amount/unit/precision, source
business date and prerequisite binding UUID when applicable. No unnecessary names/PII/free text.
Existing Accounting service audits are retained: one entry.created, two entry.updated (line adds),
one entry.posted plus **one** integration success audit on first positive effect. They are distinct
evidence for one journal, not five financial effects. Retry/zero/failure emits no new success audit.
All are in the outer transaction; any audit failure rolls back journal and binding. No Billing/
Payments success action is reused or source audit written as if posting mutated that owner.

## Tagged read model and minimal future UI

Future materialized status selectors: `invoice_posting_status` and `allocation_posting_status`.
Known source scope plus complete compatible evidence yields one of:

| Tag | Meaning |
| --- | --- |
| `NOT_POSTED` | Complete validated known absence of this positive source/effect binding; not a certificate of NEW eligibility. Allocation may include reason `invoice_accounting_not_posted` |
| `POSTED` | Complete valid binding and exact posted Entry/lines; bounded provenance with original UUIDs/date/amount/unit/posted_at |
| `NO_ACCOUNTING_EFFECT` | Valid issued base-currency zero Invoice, validated absence of contradicting posting; amount zero and null ledger fields |
| `UNAVAILABLE(reason)` | No safe status certification; ledger/binding/amount fields null, not zero. Reasons `not_installed`, `http_disabled`, `forbidden`, `incompatible`, `incomplete`, `stale` |

Draft invoices are UNAVAILABLE(incompatible), not eligible absent postings. A foreign/missing
source or unauthorized direct selector raises scoped PermissionDenied without disclosing existence;
an optional panel on an otherwise authorized source page may show forbidden without binding/count
leaks. Operational database errors propagate, not fake NOT_POSTED/zero. Installed Python selectors
never infer http_disabled. A valid historical POSTED tag survives reference retirement; NEW
eligibility/error must not replace the status of an existing intrinsic valid posting.

Future UI only: invoice detail status/post form/linked Entry; allocation bounded history or detail
status/post form/linked Entry. Request explicit Journal/Accounts with scoped choices; zero displays
No accounting effect, without account fields/action to create zero lines. Normal company-bound
CSRF POST, action-specific GET/POST RBAC, stale Company rejection, independent module admission;
no GET writes. Preserve non-JS fallback, safe HTMX GET, deterministic 50-row histories and query
strings, keyboard/focus and local scrolling/no page overflow at 390/768/1280px. Source/status
rendering shares coherent Company stabilization through materialization/rendering; do not compose
an earlier draft view with a later issued posting status. Bounded page queries join only required
provenance; complete anomaly probes precede filters, no N+1/unbounded full-history Python payload.
No templates, actions, JavaScript or CSS are implemented in this contract gate.

## ACC-INT-1 future acceptance matrix — requirements, not executed tests

| ID / area | Objective required evidence before independent implementation acceptance |
| --- | --- |
| I01 topology | Every installation row above bootstraps and operates; invoice app works without Payments/PAY-INT; allocation app missing invoice app/owner rejects configuration; no eager base imports/reverse dependency/cycle |
| I02 schema/registration | Exactly effect-specific immutable bindings, protected refs, fixed effects, source/effect and Entry uniqueness; frozen new migrations; no monetary balance/source flag; defaults disabled and existing enablement retained; exactly four proposed permissions |
| I03 Invoice correctness | Complete issued base-currency Invoice -> exact owner original total, exactly AR debit / Revenue credit and deterministic Party/date/memo; independently computed fixture oracle agrees, no redefined Billing rounding |
| I04 Allocation correctness | Partial/full allocation -> exactly its amount Cash debit / AR credit, not whole Payment; prior valid invoice posting required and same AR; no receipt-only or Revenue duplication; no change to allocation-derived outstanding |
| I05 unit/precision | Different UUID/equal code, corrupt frozen code, foreign currency reject; source/Entry p=0..8 equal and unequal exactly representable cases; excessive nonzero scale/range/nonfinite/bool/float reject with no effect; redundant zeros and 38-digit boundary retain exact value |
| I06 zero/source provenance | Zero returns repeatable NO_ACCOUNTING_EFFECT with no Entry/line/binding/audit; forbidden extra account arguments reject; hidden/corrupt positive binding never becomes zero; source immutable dates, both Party types, inactive NEW versus valid historical retry, no invented role/period |
| I07 account choices | Active same-company Journal and ASSET AR/Cash, INCOME Revenue; distinct Cash/AR; explicit arbitrary valid choices, no subtype/default/auto-config; cross-company/missing/retired NEW selections reject |
| I08 canonical retry | Each Journal/Account conflict independently, including valid nonexistent/wrong-company UUID; equal UUID/numeric representations, different currently authorized actor; same original UUIDs/times/lines/audit counts after response loss/process restart; no live precision/activity/capacity refresh |
| I09 intrinsic retry | Corrupt stored source, allocation original capacity, prerequisite, Company/unit/date/Party, duplicate Entry binding, DRAFT/extra/missing/wrong lines/memo/effect/time fail closed; fully allocated/retired valid history still recovers |
| I10 PostgreSQL source races | Real pg_blocking_pids/row-lock coordination, no arbitrary sleeps: two Invoice or Allocation calls same payload -> one complete journal/binding; different choices one winner/conflict; assert all line/binding/audit counts and clean worker connections |
| I11 revocation | Role grant/link, Permission, Company access/actor/Company revocation while waiting at Company/source/prerequisite/Entry/ref lock rechecked; operation-first/revocation-first where meaningful; denied retry leaves no success audit or financial leak |
| I12 reference/source races | Journal and each AR/Revenue/Cash activity update, Party retirement, Reference precision drift and source issue/integrity versus posting, both winning orders; re-read committed facts; immutable source cannot change; fresh Entry freeze exact after precision race |
| I13 atomic failures | Inject Entry create, first/second line, post, binding and each audit failure; whole outer transaction rolls back all journals/lines/bindings/audits, source untouched; source-key collision savepoint rolls back losing complete composition; unrelated IntegrityError not swallowed |
| I14 complete evidence | Non-superuser/non-BYPASSRLS: source-line/complete source subtree, prior binding, Entry/lines and authorization RLS hide rows; forced/disabled-policy cases and privileged role also reject supported-profile drift before reads; no duplicate/false absent/zero |
| I15 database provenance | Each relied-on NOT VALID/missing/weakened FK/CHECK, orphan on either endpoint, cross-company/off-page corrupt fact, namespace relocation/shadow/search-path or kind drift, unknown migrations/version fail; exact independent pinned expectations; ACCESS EXCLUSIVE replacement/relocation versus admitted proof blocks; weaker policy/catalog maintenance explicitly requires drain, not an asserted row-lock guarantee |
| I16 read consistency/bounds | Every status/unavailable reason, known absence versus unknown, no lazy/cached certificate; posting versus source-page multi-query read both orders; >50 records filters/COUNT/LIMIT/OFFSET, integrity outside page/filter, no full text/history materialization or narrow NUMERIC sum |
| I17 alias | Fresh zero-state non-default migrations + both effects/status/retry/rollback/audit, default cursor forbidden; no cross-alias object/evidence or nested switch, independent source/effect namespaces on aliases |
| I18 ORM boundaries | All supported instance/queryset/bulk/upsert/convenience/async binding mutations reject; posted headers/lines immutable; no private Accounting persistence use or Billing/Payments ledger writes; bound Entries cannot be edited/unposted |
| I19 module/RBAC HTTP | Every required permission independently removed; action/read grants separated; disabled/missing all prerequisite rows, stale-company forms, HTTP-disablement/admission races, Python services work with disabled/missing registry under valid grants; no staff bypass |
| I20 UI | Truthful Posted/Not posted/Unavailable/No effect, explicit choices/action/link, denied/no existence leak; CSRF, non-JS, safe GET, focus/Tab/Enter, refresh/history/query pagination; boundary amounts/long labels 390/768/1280 with no page overflow |
| I21 regression/quality/governance | Existing standalone Billing/Payments/Accounting, PAY-INT, Core and other modules unchanged; fresh PostgreSQL bootstrap, full PostgreSQL/SQLite suites with classified backend-only skips, focused actual-PG races, architecture guards, Ruff/changed-Python formatting/Django/drift, npm/Tailwind/CSS/JS and doc checks; independent audit then exact-head hosted CI and separate acceptance/adoption authority |

## Exclusions, consequences and next decision

Creation/posting only. POSTED Entries and source bindings cannot be edited/deleted to correct an
error. Separate future contracts must define reversals and corrections; mistakes remain visible
immutable history meanwhile. No journal reversal automation, credit notes, invoice void, Payment/
Allocation refund/reversal/chargeback, settlement/bank reconciliation, write-off/bad debt, FX/
revaluation, tax, Inventory valuation/COGS, Sales-to-Billing, Procurement/AP/payables, expenses,
period/fiscal closing, SaaS activation, production deployment or Phase 3 is authorized. No generic
accounting rules/event/workflow/command/template/chart-mapping/queue engine, new infrastructure,
Redis/Celery or speculative extension system.

Cost of the selected minimum: two opt-in apps, conservative schema/RLS compatibility, explicit
account choices, coarse existing Company serialization, and invoice-first accounting prerequisite
for allocations. Live precision drift may make NEW posting unrepresentable; valid historical
retry remains possible. These are visible eligibility limits, not altered upstream ownership.

This is the **final currently proposed Accounting composition gate before a later Phase 2
completion review**, unless independent contract audit identifies a prerequisite gap. That does
not approve all other optional integrations or close Phase 2. Independent architecture review
must decide this proposed topology, bindings, account/precision/zero policies, compound authority
and public read additions before publication/formal acceptance/adoption and any separately
authorized ACC-INT-1. **PROPOSED — NOT ACCEPTED; NOT PUBLISHED; ACC-INT-1 NOT STARTED;
PHASE 2 NOT COMPLETE; PHASE 3 NOT AUTHORIZED.**

## Independent approval and formal acceptance — 2026-10-12

Audited proposal: `207c78096f419b4d924326df256355a356a3f3d7`, directly above canonical
`a1079985a2ef5645dfed338e3e58af54f5242e1a`. The supplied independent architecture review returned
**FINAL PASS — ACC-INT-0 CONTRACT APPROVED FOR FORMAL ACCEPTANCE**, readiness **A**, with
**no candidate-owned P0/P1/P2/P3 findings**. This is supplied independent evidence, not an audit
performed by the acceptance session. Inherited non-blocking **ACCINT0-DOC-1 (P3)** remains
separately governed documentation maintenance; no older architecture summary is corrected here.

Normal publication preserved the exact audited proposal. Hosted **Phase 0 checks #125 /
38203841663 — SUCCESS**
([run](https://github.com/sahinkhan/djangobusinessos/actions/runs/38203841663)), event `push`,
branch `accint0-accounting-outcomes-contract`, checked out that exact SHA. **1,613 PostgreSQL
tests passed**; fresh migrations, Ruff, Django checks, migration drift, npm/Tailwind and generated
CSS reproducibility passed. Eight inherited npm advisories (two moderate, six high), Actions/Node
deprecation and outdated Browserslist warnings remain maintenance evidence, not newly corrected
dependencies or production readiness.

The ten independent conclusions are accepted without reinterpretation:

1. The two-app topology is accepted; invoice posting works independently of Payments.
2. `accounting_payments_billing` hard-dependency on `accounting_billing` is accepted for this contract.
3. Explicit Account/Journal UUID selection is accepted.
4. AR/Cash ASSET semantics provide no unimplemented subtype/control-account/bank certification.
5. `Payment.payment_date` is the accepted allocation-posting date policy.
6. Zero-total `NO_ACCOUNTING_EFFECT` without a persistent binding is accepted.
7. Source/effect binding architecture is concurrency-safe by contract, not yet implemented/tested.
8. Existing Accounting public services are sufficient for future atomic composition.
9. Incomplete/hidden evidence cannot validly become `NOT_POSTED`.
10. The contract is precise enough for separately authorized ACC-INT-1 implementation; readiness A.

**Formal acceptance: COMPLETE. Canonical adoption: PENDING at this acceptance checkpoint.**
The audited technical body, effect shapes, bindings, account/currency/date/Party/zero policies,
retry/evidence/lock requirements, four future permissions and I01–I21 matrix are unchanged.
Only this ADR, the roadmap and Phase 2 plan change; all runtime, schemas, migrations, settings,
manifests, permissions, tests, frontend and existing accepted ADR semantics remain untouched.

This acceptance commit requires its own exact-head branch push CI, not reused proposal CI.
Then revalidate unchanged starting main and straight ancestry, adopt by the authorized direct
fast-forward/no-PR normal push, and require separate exact-head main push CI. Only successful
completion makes this same acceptance commit the **ACC-INT-0 canonical freeze / CANONICALLY
CLOSED** checkpoint. Pending wording then remains acceptance-stage evidence; actual acceptance/
main run IDs and freeze SHA are reported from verified publication results, not fabricated here.
No extra closure commit, amendment, merge commit, squash, rebase, force push, tag or release.
No exact ACC-INT-0 checkpoint tag name is specified: **NO TAG CREATED**.

**ACC-INT-1 NOT STARTED / NOT AUTHORIZED. Accounting automation runtime NOT STARTED.
PHASE 2 NOT COMPLETE; final completion review NOT YET PERFORMED. PHASE 3 NOT AUTHORIZED.
SaaS activation and production deployment NOT AUTHORIZED; production readiness NOT CLAIMED.**
STOP after the authorized publication/adoption verification; do not begin another milestone.
