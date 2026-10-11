# ADR 0015 — Billing/Payments Allocation Integration Contract

Status: Accepted — Gate PAY-INT-0

Date: 2026-10-11

## Authority and exact starting point

This documentation contract is **formally accepted, not an implemented capability**. The original
proposal remains intact at `9d4fa5d3b7a12d4eb0ee2046d6e4ff306957e228` on
`payint0-billing-payments-contract`. Canonical starting main and ACC-1
freeze: `00e18a75e27bfe962ea290ab01f0cb0520f4427e`. Independent ACC-1 final reconciliation was
**PASS — ACC-1 IMPLEMENTATION APPROVED FOR PUBLICATION**; ACC1-R1 substantive retrieval and
ACC1-R2 P3 formatting findings are resolved. Candidate push CI #112 / `38127289623` and exact-head
main CI #114 / `38127960676` succeeded, the latter with **1,313 PostgreSQL tests**. See the
[closure record](../exec-plans/active/PHASE_2_COMMERCIAL_CORE.md#acc-1-final-reconciliation-publication-and-canonical-closure--2026-10-11).
Those are prior baseline/publication results, not PAY-INT-0 runtime test evidence. No
`accounting-v1` tag has been created. PR #1 was closed without merging.

The contract follows accepted [ADR 0002](0002-hard-dependencies-and-optional-integrations.md),
[ADR 0006](0006-phase-2-commercial-core-contracts.md),
[ADR 0011](0011-modular-billing-payments-accounting-boundary.md),
[ADR 0013](0013-standalone-payments-contract.md) and
[ADR 0014](0014-standalone-accounting-finance-contract.md), plus HTTP-only gating in
[ADR 0005](0005-deployment-module-gating-and-simple-variant-lifecycle.md) and alias execution in
[ADR 0012](0012-tenant-ready-database-execution-foundation.md). It fills the explicitly deferred
optional allocation seam; it does not supersede standalone ownership or financial behavior.

Governance: local candidate -> independent audit -> separately authorized publication/exact-head
hosted CI -> formal acceptance -> canonical normal fast-forward adoption. No PR is required.
**PAY-INT-1 implementation needs separate explicit authorization after contract approval/adoption.**
No source, test, schema, migration, permission, audit-action or UI implementation occurs here.

### Formal acceptance and canonical completion rule — 2026-10-11

The owner-supplied independent verdict for the exact proposal is **FINAL PASS — PAY-INT-0 CONTRACT
APPROVED FOR FORMAL ACCEPTANCE**, readiness **A**, with **no actionable candidate-owned P0, P1,
P2 or P3 findings**. This records the supplied independent review, not an audit performed by this
acceptance author. Normal branch publication preserved the reviewed proposal byte-for-byte.

Hosted candidate **Phase 0 checks #115 / 38133793295 — SUCCESS**
([run evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38133793295)) checked out
exact `9d4fa5d3b7a12d4eb0ee2046d6e4ff306957e228`: **1,313 PostgreSQL tests**, fresh migrations,
Ruff, Django checks, no migration drift, npm/Tailwind and generated CSS reproducibility passed.
Inherited eight npm advisories and Actions runtime warnings remain separate maintenance items;
no dependency/security maintenance or new allocation runtime test evidence is claimed.

**PAY-INT-0 formal acceptance: COMPLETE. Canonical adoption: PENDING at this acceptance checkpoint.**
The separately authorized publication flow requires this documentation-only acceptance commit's
own successful exact-head branch CI, then normal fast-forward adoption into unchanged canonical
main, then a separate successful exact-head main push CI. Only after all three steps succeed does
this same acceptance commit become the **PAY-INT-0 canonical freeze / CANONICALLY CLOSED** checkpoint.
The pending wording describes the acceptance stage, not a claim about a subsequently verified main.
Actual acceptance/main run IDs and the resulting commit SHA are reported after verification;
future CI evidence is not fabricated or retroactively inserted by amending this commit.

No exact PAY-INT-0 checkpoint tag is specified; no tag or release is created. **PAY-INT-1 and
Accounting automation: NOT STARTED / NOT AUTHORIZED. SaaS activation and production deployment:
NOT AUTHORIZED.** Acceptance/adoption authorizes no runtime work or full Phase 2 completion.

## Verified baseline and ownership

The following evidence is repository-local at the pinned SHA, not an assumption about future APIs:

| Owner | Existing contract/code | Relevant facts |
| --- | --- | --- |
| Billing | `businessos/modules/billing/models.py`, `domain.py`, `services.py`, `selectors.py`, `manifest.py`; ADR 0011 | Invoice/InvoiceLine; `draft` -> `issued`; protected UUID references; frozen Party/currency snapshots; exact line products summed then once-only HALF_UP original total; public `invoice_detail`, `invoice_total`, `invoices_for_company`; no payment-aware balance |
| Payments | `businessos/modules/payments/models.py`, `domain.py`, `services.py`, `selectors.py`, `manifest.py`; ADR 0013 | PaymentMethod and immutable incoming Payment; positive Decimal(38,8), frozen precision/code, payer UUID, receipt retry key; public `payment_detail`, `payments_for_company`, `record_payment`; no Invoice FK or allocation |
| Accounting | `businessos/modules/accounting/models.py`, `services.py`, `selectors.py`, `manifest.py`; ADR 0014 | Account/Journal/JournalEntry/JournalEntryLine; manual balanced immutable postings, bounded derived GL/TB; no Billing/Payments dependency or allocation authority |
| Core | `businessos/core/access/policies.py`, `modules/manifest.py`, `modules/services.py`, `database/transactions.py`, `database/router.py`, `audit/services.py` | Current context/RBAC, manifest namespace validation, explicit registration, owned namespace routing, alias-aware atomic/savepoints, caller-authorized append-only audit |

Billing retains Invoice identity/lifecycle, financial snapshots and derived **original total**.
Payments retains PaymentMethod, immutable receipts, PaymentAllocation, its rules/audit and derived
applied/unapplied amounts. Accounting retains journals/GL/TB. Physical optional integration
placement below never transfers allocation ownership to Billing or creates a second finance owner.

Forbidden authoritative fields/interpretations: `Billing.amount_paid`, `Billing.amount_due`,
`Billing.balance`, mutable authoritative `Billing.payment_status`, Invoice-owned allocation facts,
Accounting-derived allocation state, or cached authoritative balances in either parent. Existing
invoice issue and receipt recording remain allocation-free and unchanged.

## Selected optional composition mechanism

**Select a Payments-owned, explicitly installed Billing integration Django app**, proposed package
`businessos/modules/payments/integrations/billing/`, app label / registry code `payments_billing`.
It contains the one allocation model, Payments-owned services/selectors/domain rules and its
bounded HTTP adapter. It uses the ordinary Django app, migration, manifest and Core infrastructure,
not a dynamic loader, generic adapter registry or new platform framework.

Dependency direction is fixed:

```text
billing  -> party, organization, reference, access
payments -> party, organization, reference, access
accounting -> party, organization, reference, access

payments_billing (optional, Payments-owned) -> billing, payments
```

Only the opt-in app has migration dependencies and protected FKs to both installed owners. Neither
base app imports it at startup, depends on its migration, adds an Invoice FK, or invokes it during
ordinary mutations. The optional app's namespace is within `businessos.modules.*`, compatible
with the existing database router; its distinct label separates migrations from released Payments
history. Future new migrations, explicit deployment configuration and URL inclusion are required;
no released migration is edited and no setting changes in PAY-INT-0. Registration is disabled by
default, preserves existing enablement, and freezes declarations locally in its new migration.
Installing it without either owner is unsupported and must fail configuration/bootstrap checks.
Uninstalling while preserving financial history is **not** an approved migration/delete procedure.

Alternatives considered:

- Invoice FK in generic Payments: rejected, creates an unconditional Billing installation dependency.
- Generic type/UUID source reference: rejected for this concrete seam; lacks database Invoice FK
  protection and introduces unsupported polymorphic validation.
- Separate Billing-owned link/amount table: rejected, duplicates or transfers Payments authority.
- Selected opt-in Payments app: keeps real protected references and no reverse hard dependency;
  only this explicitly installed component composes the two public owner contracts.

Owner participation is read-only: future minimal public **Billing financial-basis** and **Payments
receipt-basis** selectors return the validated identities/frozen facts below under parent locks,
on the selected alias. These APIs **do not exist yet**. They must enforce existing owner view
permissions, perform their owner's integrity checks and avoid eager optional imports. Billing
calculates its own total; the adapter never redefines rounding or inserts/updates Invoice tables.
Payments' opt-in services alone write PaymentAllocation. No private owner persistence token,
unscoped ORM write or synthetic privileged BusinessContext is an integration interface.

## Minimum immutable PaymentAllocation schema

One successful creation is one immutable allocation fact. There is no DRAFT/POSTED/activity state,
mutable row, business date override, edit/delete/reversal API or allocation numbering framework.

| Persisted field | Proposed exact contract |
| --- | --- |
| `id` | UUID primary key, generated once on first successful creation |
| `company` | Non-null protected Company FK; immutable, equal to both authoritative parent Companies |
| `payment` | Non-null protected FK to `payments.Payment`; immutable |
| `invoice` | Non-null protected FK to `billing.Invoice`; immutable; stable UUID, not invoice number text |
| `amount` | Non-null Decimal(38,8), finite, strictly positive and less than `10^30`; exact at shared frozen precision |
| `idempotency_key` | Non-null required string, trim outer whitespace, case-sensitive, nonblank, maximum 128 normalized characters; unique `(company, idempotency_key)` |
| `created_at`, `updated_at` | Existing UUIDTimestampedModel convention; server-aware UTC at first insertion; remain unchanged thereafter, including retry |

No nullable field is proposed. No copied Currency FK/code/precision or Party/name snapshot is
necessary: protected immutable parents already retain those identities/facts. Validation/readback
must compare both parents, not today's Currency precision. No amount_paid/due/unapplied/balance
column, status flag, external-reference alias for the key or retained mutable totals. Core Audit
provides actor/occurrence/effect evidence; it is not a second allocation ledger.

Database backstops: UUID identity, protected references, company/key uniqueness, positive/range
amount CHECKs and bounded nonblank key. Index scoped histories by Company/parent/created_at/UUID.
There is deliberately no unique `(payment, invoice)` pair: a second **different** key can add a
further partial allocation, subject to capacity. Cross-row Company, currency, precision, Party
and aggregate capacity remain authoritative transactional service checks, not fictional SQL CHECKs.

Public instance create/save/delete, queryset update/delete, bulk update/create/upsert, convenience
create/update_or_create and async wrappers must not bypass the service, RBAC or audit. One
Payments-local private validated insertion path is sufficient; no public allow/skip-validation
flag. Every persisted field and timestamp is immutable after insertion. Privileged raw SQL/private
base-class calls are not supported business APIs or claimed protected deployment boundaries.

## Eligibility, exact amounts and capacity

New allocation requires all of the following on **one selected database alias**:

1. Valid current actor/active Company/context and the explicit operation permissions below.
2. Existing Payment and Invoice, each Company equal to context and allocation Company; no caller
   object or request-supplied parent/Company is trusted. Referenced payer, method and bill-to
   ownership must also be valid, even if malformed historical rows exist.
3. Payment is a valid immutable PAY-1 receipt, not a forged partial row; Invoice is Billing
   `issued` with non-null issued_at and valid frozen lines/basis. `draft` is never eligible.
4. Same Currency UUID, identical frozen currency code, and **identical** frozen integer precision
   `0..8`. Equal codes alone are insufficient; p=2 versus p=3 is rejected even for an amount that
   fits both. Cross-precision reconciliation/conversion is a future policy, not implicit rounding.
5. **Payment.payer_party_id equals Invoice.bill_to_party_id.** This deliberately restricts the
   MVP to the same Party; third-party/on-behalf payments need another contract. No fuzzy name
   match, duplicate merge, or `is_customer`/`is_supplier` requirement is inferred.
6. Exact positive amount and sufficient capacity on both parents after locked current reads.

Owner basis validation also checks that each frozen code agrees with its referenced immutable
Currency code. It must not replace either frozen precision with the live Reference precision or
require that reference to remain active. Matching two equally corrupt snapshots is not evidence.

Accept Decimal, integer excluding bool, or valid base-10 numeric string, consistent with PAY-1.
Reject floats/bools/unsupported types, malformed numbers, NaN/sNaN/infinities, zero/negative,
`>= 10^30`, and nonzero digits beyond frozen precision **before comparison/persistence**.
Redundant zeros and equivalent numeric strings compare by exact numeric value. Never use float,
ambient-context truncation, database scale rounding, quantization to make input valid, or clamping.
Use sufficiently large explicit Decimal accumulation/subtraction context and unrestricted SQL
NUMERIC aggregates; independent maximum-boundary tests must agree with Billing's exact total.

An already-issued zero-total invoice is valid Billing history but has no positive allocation
capacity. Existing receipt/issued invoice snapshots and referenced Party/Method/Currency identity
remain historical facts after reference rename/retirement or a live Currency precision change.
Allocation is application of already-recorded money, not NEW receipt/invoice creation: no fresh
Party/Method/Currency activity gate is added. Frozen mismatch still rejects; current actor/Company
or permission revocation always rejects. Ownership/identity corruption never becomes retirement.

Many-to-many partial application is supported: one receipt may cover multiple same-Party invoices;
one invoice may receive multiple same-Party receipts. Both limits are mandatory:

```text
A_payment = SUM(valid allocations referencing Payment)
A_invoice = SUM(valid allocations referencing Invoice)

A_payment + requested amount <= Payment.amount
A_invoice + requested amount <= Billing.original_total

Payment.unapplied = Payment.amount - A_payment
Invoice.outstanding = Billing.original_total - A_invoice
```

Over-allocation of either side is a ValidationError/domain-validation conflict, with stable reason
`payment_capacity_exceeded` or `invoice_capacity_exceeded`, no row or success audit. Invalid
references/eligibility/precision use field-specific ValidationError; current access failure uses
Core PermissionDenied without disclosing another Company's records. Exact human wording is not
an API. Corrupt existing allocation history blocks the entire operation instead of excluding bad
rows and fabricating spare capacity. No negative balance or approved overpayment/credit policy.

## Authorization and HTTP/module availability

Proposed optional manifest declares **exactly two new permissions**, in its own validated namespace:

| Proposed identity | Authority |
| --- | --- |
| `payments_billing.allocation.view` | Scoped allocation history and composed financial summaries |
| `payments_billing.allocation.create` | Allocation creation and matching retry, action GET/POST |

This naming respects Core's `module.resource.action` validation and module-prefix rule. It does
not change Payments' four standalone declarations or Billing's four. New identities only exist
if future optional migrations/registration are installed; undeclared/inactive permissions deny,
including Core's limited superuser bypass. No wildcard, staff/Django-model-permission shortcut.

**Deliberately require compound authority:** composed reads require allocation.view **and**
`payments.payment.view` **and** `billing.invoice.view`; create/retry requires allocation.create
**and those two owner view permissions**, not allocation.view, receipt.record or invoice.issue.
The two view grants are explicit cross-owner financial read admission, not incidental authority
silently inferred by calling an existing selector. This restriction applies equally to direct
Python callers and HTTP action forms. Existing standalone mutation permissions remain unchanged.
All required grants/context are checked after locks; form/button hiding is never enforcement.

Installation/configuration is explicit. HTTP/navigation require Billing, Payments and
`payments_billing` registered **and enabled**. Missing/disabled any prerequisite returns 404 for
integration URLs and hides their actions. Standalone owner's enabled pages/services still work
alone; they show original receipt/invoice facts and explicit integration-unavailable presentation.
No absent optional package is imported from a base app to discover a capability.

HTTP POST admission must be serialized separately from financial rules: an integration-local
HTTP adapter uses the same alias-aware outer transaction, takes Company first, then locks the
three registry rows in ascending code order (`billing`, `payments`, `payments_billing`), checks
current enablement, and calls the ordinary allocation service. It holds those row locks through
commit/rollback. Missing rows fail; after waiting, both context/RBAC and enablement are rechecked.
This is bounded presentation admission, not a generic framework or BusinessContext flag.
The ordinary service never receives HttpRequest or checks BusinessModule.is_enabled.

If disablement commits before registry admission, POST fails 404 without effect; if admitted POST
holds registry locks first, it can finish and disablement waits until commit. A stale GET is not
authorization for a later POST. This makes the race explicit rather than promising instantaneous
revocation of an already-admitted transaction. Module updates naturally contend on the same rows;
no new Core mutation path is proposed. HTTP queries/components must also check current admission,
not trust a cached enablement result as financial evidence.

Installed Python allocation APIs remain callable with missing/disabled registry rows when their
schema/public contracts exist and current permissions/context are valid, preserving ADR 0005.
Do not gate them on the HTTP adapter or is_enabled. Uninstalled/incompatible integration is not
an available Python capability; attempting composition returns unavailable as specified below.

## Transaction, lock order and revocation after waiting

Resolve the execution alias at business_atomic/business_atomic_context entry (ADR 0012). Accept
BusinessContext plus UUID/data, never HttpRequest, caller ORM objects, or alias inside tenant
identity. Core context, all owner reads/locks, aggregates, savepoints, inserts and Audit share that
alias; passing an object from another alias is not allowed. Cross-database allocation and alias
switches inside atomic execution reject. Actual SaaS routing/activation is not introduced.

Fixed order for one allocation:

1. Enter selected-alias transaction; lock active Company; reread actor/context/access and **all**
   required current registered permissions. Never reuse pre-wait authorization.
2. HTTP only: the registry admission locks above, then recheck context/permissions and enablement.
   Direct Python skips this step. Do not acquire registry locks before Company.
3. Canonicalize UUIDs/key/input type; find same-company existing key without mutating it. It is
   immutable, so an additional allocation-row lock is not needed for that lookup.
4. Lock Payment first, then Invoice through owner public basis selectors. Reread authoritative
   scope/frozen facts and context/permissions after each potentially blocking lock. A retry uses
   the existing fact's authoritative parents and rejects mismatching requested references.
5. For a NEW key, validate eligibility and complete relevant allocation history on both endpoints;
   compute exact SQL sums and both capacities while Company/parent locks remain held.
6. Insert one allocation through Payments' private validated path; append one Core Audit in the
   **same** transaction/alias; return only with normal transaction success.

Current supported Access/Billing/Payments writers take Company before their own aggregates. This
Company-wide serialization is intentional for this MVP; do not replace it with weaker optimistic
checks. Same Payment/same Invoice, same Payment/different Invoices, and different Payments/same
Invoice cannot overspend because every same-company creator follows this order and recomputes
after waiting. No Invoice -> Payment reverse lock path is permitted in the optional component.
Only one pair is created per call; any later multi-pair API needs a separately frozen order.
Immutable allocation rows need no row-by-row locking/materialization; parent locks plus Company
serialize every supported insertion. Future reversal writers would require a new shared contract.

Basis selectors do not lock live Method/Party/Currency activity rows: eligibility uses immutable
receipt/issued facts and ownership, not mutable activity/precision. Invoice draft edits/issue still
use their existing owner protocol; allocation waits, rereads issued state/total and fails if draft.
Reference retirement cannot reinterpret money. Any proven unsupported owner/alias/locking contract
must block implementation, not be bypassed with private services or a Core redesign.

Role, role-permission link, permission deactivation, Company-access/actor/Company revocation while
waiting must fail closed under current Core policies. Real PostgreSQL coordination must prove the
applicable revocation order, not substitute a preflight check, arbitrary sleep or mocked lock.
At a successful linearization point authorization is current; a later revocation cannot undo an
already committed immutable fact. Module-state races follow only the HTTP admission rules above.

## Required keyed retry and atomic audit

Future conceptual create service: `create_payment_allocation(context, *, payment_id, invoice_id,
amount, idempotency_key)`. Exact implementation spelling may vary without changing this contract.
The required allocation key is **independent** of optional PAY-1 receipt idempotency: receipt
recording itself remains unchanged and is never called implicitly by allocation creation.

Canonical request identity is `(Company, key)`; payload is canonical `(Payment UUID, Invoice UUID,
exact numeric amount)`. Currency/Party are derived from the protected parents, not user overrides.
Actor, timestamps, auto UUID and display names are not payload. Key text strips outer whitespace,
retains case, and is bounded/nonblank. Equivalent UUID/numeric representations compare equally.

- Matching current-authorized retry returns the original allocation UUID/amount/references/times;
  no second insert, audit, timestamp/snapshot refresh or capacity consumption.
- Same key with different canonical payload raises ValidationError reason `idempotency_conflict`;
  a different actor does not make a second logical allocation. Another Company has its own scope.
- Duplicate delivery/timeout/concurrent retry produces one fact. Once committed, loss of response
  is recoverable by key; an uncommitted failure leaves neither fact nor success audit and can retry.
- Find matching existing fact **before** NEW-capacity eligibility: a fully applied invoice/payment
  does not invalidate retry. Parent/reference retirement, changed live labels/precision and later
  HTTP disablement do not rewrite historical facts; HTTP still requires current admission, and
  Python still requires current authority. No unused-capacity recheck for matching committed retry.
- Invoice/Payment themselves have no inactive/void/reversed state in these accepted scopes. A
  future such lifecycle needs its own validity/correction contract. This version promises no new
  allocation to unsupported state and no stale balance certification: contradictory parent facts
  or scope/currency corruption fail closed. Retrieving an immutable retry fact is not a certificate
  that a later evolved financial read model remains valid.

Database `(company, key)` uniqueness is the final backstop. Only an identified key collision may
be recovered inside an alias-aware savepoint by loading/comparing the existing fact; unrelated
IntegrityError propagates/rolls back. UUID collision handling is bounded, not an unbounded retry
loop. Never recover using a broken outer transaction or create duplicate audit during recovery.

Exactly one proposed business success action: **`payments.allocation.created`**, using the existing
Payments owner prefix (not `payment.allocation.created`). Object type `payments.PaymentAllocation`,
UUID, actor, Company, server occurrence and minimal Payment/Invoice UUID, exact amount and frozen
currency/precision evidence. Keep credentials/unnecessary Party PII out. Audit metadata is evidence,
not the authoritative numeric row. No updated/removed/reversed action is introduced.
Insert and audit failure roll back together; invalid/revoked/conflicting requests emit no success
audit. A crash before commit leaves neither; a committed but unacknowledged request is key-retried.
No distributed/filesystem atomicity or gateway delivery guarantee is claimed.

## Complete-evidence read model and unavailable behavior

Future public optional selectors provide payment applied/unapplied, invoice applied/outstanding,
and each parent's allocation history. Return a bounded materialized summary/history-page DTO,
not a lazy cross-alias projection evaluated after authorization/transaction exit.

**Use one tagged financial-evidence result contract:**

| State | Exact meaning / amount fields |
| --- | --- |
| `AVAILABLE` | Complete compatible selected-alias, scoped, authorized evidence validated in this call; exact derived amounts, bounded history page/count and frozen unit provenance |
| `UNAVAILABLE(reason)` | Derived applied/unapplied/outstanding and history/count are null, not zero/empty; reasons `not_installed`, `http_disabled`, `forbidden`, `incompatible`, `incomplete`, `stale` |

`not_installed` is detected through explicit deployment configuration, not accidental ORM import
errors. `http_disabled` is a presentation-adapter result only; installed APIs never produce it from
registry state. `forbidden` may describe an optional component on an otherwise authorized standalone
parent page, without exposing allocation IDs/counts or absent foreign IDs. Direct unauthorized
selector calls/context/cross-company requests raise Core PermissionDenied; adapters translate only
the optional denied evidence into `UNAVAILABLE(forbidden)`, not another Company's existence.
Invalid filters/UUIDs use validation errors. Unexpected database/operational failure propagates as
an error, never an AVAILABLE fallback. Incompatible schema/provenance/precision is `incompatible`;
missing expected migration/complete coverage is `incomplete`. Caller-provided/cached or earlier
transaction evidence is `stale` and must be reread, not used to certify a current amount.

Billing's original total and Payment's receipt amount remain separately available under their
ordinary owner permissions. In UNAVAILABLE, show **Allocation evidence unavailable**; never claim
Paid=0, Unapplied=receipt amount or Outstanding=full invoice total. For a draft Invoice, original
Billing total remains readable but settlement composition is UNAVAILABLE(incompatible): no issued
financial basis exists yet. Zero-total issued invoices can be AVAILABLE with exact zero applied/
outstanding only after full evidence checks, and cannot accept positive allocations.

Completeness is within the installed recorded-ledger contract, not proof of external bank settlement
or all real-world debt. Require correct optional schema/migration/public-contract version, parent
identity/scope/frozen basis, valid allocations at **both** endpoints, and full unfiltered SQL sums.
Probe rows touching either Company/parent side, so a malformed cross-company allocation cannot be
silently filtered out. Invalid amount/scale, broken scope/Party/currency, over-capacity or contradictory
history makes the whole result unavailable, not a sum of just remaining good rows. No partial-page
sum, current-activity history filtering or catch-and-zero. An empty complete validated set alone
permits SUM=0. Historical backfill/import coverage is not invented; an unreviewed data migration
must block completeness until a separate approved reconciliation proves its scope.

Each composing call holds Company and its requested parent lock in one selected-alias
business_atomic_context, rechecks permissions after waits, validates integrity, computes totals and
materializes the bounded DTO before releasing locks. The Company lock stabilizes allocation inserts
and supported Access/owner mutations across multi-query READ COMMITTED reads; referenced receipt/
issued facts are immutable. No mixture of an earlier invoice total and later receipt sum. HTTP adds
its admission envelope. A payment summary locks Company -> Payment; an invoice summary locks
Company -> Invoice only, and never subsequently locks Payment. All other referenced-parent facts
are validated through scoped SQL joins/EXISTS, not a lock/load loop over all history. A call needing
both individual bases follows creation's Company -> Payment -> Invoice order. These per-parent
composition calls are not a general report engine or an unbounded multi-document locking API.

Billing's proposed financial-basis selector performs owner-owned SQL exact quantity*price sum,
line integrity/count checks, raw/rounded range validation and once-only HALF_UP at frozen precision,
matching `billing.domain.calculate_total`. It returns only Invoice identity, Company, bill-to UUID,
state/issued_at, Currency UUID/code/precision and original total. Payments' receipt-basis selector
returns validated Payment identity/Company, payer UUID, Currency UUID/code/precision, amount and
recorded receipt identity, without whole histories/notes. These are read-only additions, not new
owner mutation APIs or a change to Billing rounding. No integration loop calling invoice_detail
and materializing all descriptions per allocation.

Allocation aggregates/integrity use SQL SUM/EXISTS with bounded result payload; do not retain a
Python list of all allocations to validate or total. SQL may scan/index relevant history; no
constant database-work claim. Histories order **`created_at ASC, id ASC`**, page size **50**, with
SQL COUNT and LIMIT/OFFSET before materialization; supported filters/search run in SQL, preserve
query strings and cannot alter summary denominators. Select parent identities/numbers in the page
query, no N+1 basis/description loads. Memory is O(page) payload plus scalar aggregates; integrity
queries may visit necessary history in the database, not fetch unbounded text/model history.
Alias is explicit/pinned throughout, including pagination/count queries. No default connection
leak, narrow aggregate cast, mutable balance cache or ACC1-R1-style full-history Python filtering.

## Future UI boundary, accounting isolation and exclusions

PAY-INT-1 may add only bounded allocation forms/history/components to existing parent details:
Payment receipt amount + AVAILABLE applied/unapplied/history; Invoice original total + AVAILABLE
applied/outstanding/history. Display all frozen-precision digits and explicit unavailable state.
Action GET and normal CSRF-protected, company-bound POST enforce create + owner view grants; read
portions enforce view grants. Reuse deterministic 50-row pagination, safe GET navigation, normal
non-JavaScript fallback, keyboard/focus and responsive local scrolling/no page-wide overflow at
390/768/1280px, preserving all Gate UI-1 and audited financial boundary protections. No UI now.

**Invoice issue does not create JournalEntry. Payment receipt does not create JournalEntry.
Payment allocation does not create JournalEntry.** No Accounting dependency, import, account
selection, mutable posting marker or automated posting is added. ADR 0014 stays unchanged;
Accounting source identity/full-line/posting idempotency belongs to a future integration gate.

Allocation creation only; a wrongly applied immutable fact needs a separately reviewed reversal/
correction design, not editing/deleting history or interpreting an ordinary receipt retry as undo.
Explicitly excluded / not authorized by PAY-INT-0:

- PAY-INT-1 runtime implementation, new models/migrations/tests/permissions/audit actions/UI.
- Allocation editing/deletion/reversal, refunds/payment reversal, chargebacks, gateway/provider.
- Settlement/bank reconciliation, advance credit/overpayment, credit notes, invoice void.
- FX conversion/revaluation, cross-precision conversion, third-party/on-behalf Party application.
- Accounting automation, invoice/payment/allocation-to-journal posting, AR/AP policy or aging.
- Sales-to-Billing automation, Procurement/AP automation, Inventory effects or other integrations.
- Actual SaaS activation, tenant routing, customer migration/import, production deployment.
- Generic workflow/event/command/DI/plugin/metadata engines, Redis/Celery/React or new infrastructure.

## PAY-INT-1 acceptance matrix — future required evidence, not tests executed here

| Area | Objective acceptance evidence |
| --- | --- |
| Optional topology/ownership | Base Billing/Payments/Accounting install, migrate and operate without integration/each other; optional app with both owners has protected FKs and only Payments-owned allocation writes; absence fails configuration safely; no reverse dependency/eager import/cycle/private owner token |
| Schema/registration | One immutable UUID model with exact required fields/constraints; no duplicate balances/currency snapshots; required key/company uniqueness; fresh disabled registration, enablement preservation, exact two namespaced permissions and frozen new migration declarations |
| Functional | Full/partial allocations; multiple receipts -> one invoice; one receipt -> multiple same-Party invoices; distinct-key further partials; exact applied/unapplied/outstanding; complete empty set yields zero; issued zero-total capacity rejected without changing Billing history |
| Relationships/eligibility | Missing/malformed UUID, cross-company/context, wrong payer/bill-to, forged parent/child ownership, draft/unsupported Invoice state, invalid receipt; no customer-role inference; PROTECT references; no data disclosure/effect |
| Currency/Decimal | Different Currency UUID even with equal code; frozen code mismatch; precision 0..8/equal versus 2/3 mismatch; retired references/live precision change; max Decimal(38,8), numeric equivalence/redundant zeros; zero/negative/nonfinite/sNaN/float/bool/bad string/range/nonzero excess scale rejected before write/audit |
| Capacity/integrity | Payment and Invoice over-allocation independently reject; exact boundary totals; malformed allocations on either ownership endpoint, out of displayed filters/page, wrong units/scale and over-capacity fail closed; no filtered plausible balance or negative/clamped amount |
| Retry/conflict | Required-key null/blank/128/129 normalization; same canonical payload/UUID/number variants and another actor; conflict each payload field; timeout and already-committed retry; fully applied and retired reference retry; unsupported future lifecycle cannot certify stale balance; one UUID/timestamps/audit |
| PostgreSQL financial races | Real pg_blocking_pids/row-lock coordination for same Payment/same Invoice, same Payment/different Invoices, different Payments/same Invoice, same key equal/conflicting payload and both winner orders; sufficient/insufficient capacity after wait; no deadlock/duplicate effect |
| PostgreSQL admission/revocation | Role, role-permission removal, permission deactivation and Company-access/actor/Company revocation while creation/retry waits; recheck after Company/parent waits; stale Company forms; HTTP disablement versus admitted/waiting POST in both orders; installed Python APIs with missing/disabled registry retain RBAC |
| Owner-state races | Invoice issue/draft edit versus allocation in both orders; post-wait current issued basis, retired Party/Method/Currency and frozen precision; no refresh/reinterpretation; future unsupported state fails closed |
| Atomic failure/crash | Audit failure, insertion/constraint failure, validation, revoked authority and unrelated IntegrityError leave neither partial allocation nor success audit; alias savepoint collision recovery; rollback before commit and retry after committed response loss |
| ORM bypass | Instance/save/delete, bulk/upsert/queryset/convenience/async mutation paths blocked; in-memory Company/parent substitution and private insertion misuse cannot rewrite/create unsupported facts; retained history/totals/audit unchanged |
| Evidence/read consistency | AVAILABLE exact values only with complete coherent scoped evidence; all six UNAVAILABLE reasons/no fake zero/count/history; no stale cached input; concurrent allocation versus multi-query summaries/history; no mixed snapshot; ordinary parent facts readable without new grants |
| SQL bounds | >50/100 allocations with long text/boundary amounts: SQL COUNT/LIMIT/OFFSET before payload construction, both pages/stable tie-break; summaries include off-page facts; integrity EXISTS and unrestricted SUM, no whole-history Python list/N+1 invoice-lines payload; invalid filters return safely |
| Execution topology | Full representative allocation/read/retry/rollback/audit and pagination on non-default alias with default cursor forbidden; cross-alias object/context misuse rejects; fresh PostgreSQL zero-state and migration replay, both standalone and optional installation; historical migrations unchanged |
| HTTP/UI | Complete permission GET/POST/read matrix; disabled/missing prerequisites hidden/404, non-JS and safe GET fallback, query preservation, stale Company create, keyboard/focus/Enter; exact maximum values/long labels at 390/768/1280px, local tables and zero page overflow |
| Regression/quality | Full PostgreSQL and SQLite suites (explicit skips only actual PostgreSQL lock/numeric guarantees), clean worker connection teardown, module-local discovery, Ruff and every changed Python file formatted, Django check/drift/bootstrap, npm/Tailwind/CSS/JS/diff checks; Billing/Payments/Accounting/other modules and audited UI behavior unchanged |
| Governance | Independent code/security audit, exact-head candidate hosted CI, separate formal acceptance/adoption authority; no Accounting effects or production/SaaS claim; inherited maintenance warnings separately identified |

## Consequences and required next decision

The precise proposal trades an extra opt-in app and deliberately coarse Company locking for real
referential integrity, independently usable base modules and immutable audit-backed application.
Strict same-Party/same-frozen-precision eligibility deliberately excludes some future payment use
cases; matching historical retries and faithful reference retirement remain supported. No generic
framework, mutable financial duplicate or Accounting automation is needed.

The original proposal requested independent architecture review and stopped before publication or
acceptance. That chronology is retained at the audited proposal SHA. The supplied independent
FINAL PASS and exact-head candidate CI above now support formal acceptance without changing the
reviewed technical body or its future acceptance matrix. Accepted ADRs 0011/0013/0014 remain
unedited; no substantive override or runtime implementation occurs during this acceptance.

**Next within the separately authorized publication flow: acceptance exact-head CI, normal
fast-forward adoption and separate main exact-head CI; then canonical freeze and STOP.
PAY-INT-1 NOT STARTED / NOT AUTHORIZED.**
