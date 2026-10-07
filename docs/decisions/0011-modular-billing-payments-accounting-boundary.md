# ADR 0011 — Modular Billing, Payments and Accounting Ownership Boundary

Status: Accepted — Gate BILL-0

Date: 2026-10-07

## Formal BILL-0 acceptance

Acceptance date: 2026-10-07. Independent audit verdict:
**FINAL PASS — BILLING OPTION A CONTRACT APPROVED**.
Accepted contract candidate and exact hosted-CI checkout:
`24d73be43cc09ef66f4405453a210d8f07fcca7f`.
Hosted **Phase 0 checks #91 — SUCCESS**
([run 37579298801](https://github.com/sahinkhan/djangobusinessos/actions/runs/37579298801))
verified that candidate, including 769 PostgreSQL tests and mandatory repository checks.

This is documentation-only BILL-0 contract acceptance; canonical main adoption remains pending.
BILL-0 acceptance does **not** mean Billing implementation is complete. BILL-1 remains not
started and requires separate explicit authorization. Payment implementation, Accounting
implementation, optional integrations and actual SaaS activation are not authorized.
The future implementation proposals and verification gates below are preserved; this acceptance
does not declare BILL-1, PAY-1 or ACC-1 implemented or accepted.

## Baseline, evidence and supersession

Canonical base: `d65eeee14923910a6b28f11a840a465b1d28ac6f`, tagged
`tenant-db-foundation-v1`; the preserved UI checkpoint is `ui-foundation-v1` at
`65a0e46b51a05aab16de0958e6e0ea5882b3f7fd`. Gate TDB-1 main CI #89
([run 37574139311](https://github.com/sahinkhan/djangobusinessos/actions/runs/37574139311))
passed 769 PostgreSQL tests and all mandatory checks. ADR 0012's execution contract applies.
Its original candidate-status prose is historical evidence, not a new implementation blocker.

Read-only evidence: `billing-option-a-reconciliation` at
`65600700395d2df923f2cf2b2a5fec5d0c96c8d8`, particularly its draft ADR 0011 and
ownership/dependency/Phase 2 reconciliation. Its accepted label and disconnected WIP do not
constitute acceptance or implementation of this canonical candidate. No files or migrations
from that WIP are restored. Its unconditional `payments -> billing` dependency is refined below.

This Option A candidate supersedes only ADR 0006 section 7's Billing ownership of Payment and
PaymentAllocation, its combined outstanding/payment scope, section 12's Billing-owned payment
posting seam, and the resulting five-module delivery assumption. Unrelated Sales, Procurement,
Inventory, Accounting, numbering, lifecycle and module-gating contracts remain accepted.
ADR 0002 is preserved. ADR 0012 is neither overwritten nor renumbered. Independent BILL-0
review and formal documentation acceptance are complete; no Billing
implementation, registration, migration or integration is authorized by this milestone.

## Decision: three horizontal modules

Delivery sequence (not a hard-dependency graph):

```text
Gate BILL-1: Billing & Invoicing
    -> Gate PAY-1: Payments
    -> Gate ACC-1: Accounting & Finance Core
```

| Owner | Authoritative concepts | Exclusions |
| --- | --- | --- |
| Billing | Invoice, InvoiceLine, invoice identity/numbering, financial snapshots, currency, totals, draft editing and issue; future approved invoice corrections/void/credit policy | Payment, PaymentAllocation, PaymentMethod, payment receipts, settlement, reconciliation, refunds, gateways, payment retry keys, journals, stock, Sales lifecycle |
| Payments | Payment/Receipt, PaymentMethod, PaymentAllocation, partial payments, payment idempotency, allocation validation, settlement; refunds/reversals when separately approved | Invoice/InvoiceLine ownership, journals/GL, stock |
| Accounting | Chart of Accounts/Account, Journal, JournalEntry/JournalEntryLine, balanced postings and derived General Ledger/Trial Balance | Authoritative invoices, payment receipts, allocations and mutable authoritative balances |

Procurement PurchaseReceipt remains a goods/service receipt fact; it is not a Payments receipt.
Billing is reusable by Retail, School, Hospital, Hotel, Services, Ecommerce and other verticals.
Generic financial lines support services/non-stock charges without Catalog, Sales or Procurement.

## Dependencies and optional composition

Hard dependency notation is `consumer -> dependency`:

```text
billing    -> party, organization, reference, access
payments   -> party, organization, reference, access
accounting -> party, organization, reference, access
```

Each may consume existing Core common/identity/time/audit/registry/database APIs as appropriate.
Core Database is infrastructure, not a registered module dependency. None of these three modules
hard-depends on another; Billing also has no Sales, Procurement, Inventory or Catalog dependency.
Accounting remains meaningful through manual balanced entries without Billing or Payments.

Generic Payments records standalone receipts without invoice allocation. Invoice allocation is
a separately approved optional integration requiring both Payments and Billing. The optional
composition code may import both public contracts, validate invoice eligibility through Billing,
and invoke Payments' authoritative allocation service. Allocation facts remain Payments-owned;
Billing never imports Payments models/services. Payments' base models, migrations, startup and
manifest must remain usable with Billing absent: no unconditional Invoice FK or eager Billing
import in the generic Payments core. The concrete optional linkage/storage design and stable
invoice-reference validation must be reviewed at PAY-1/integration design, not guessed here.

Billing invoice -> Accounting and Payments outcome -> Accounting automation are also optional
composition, using Accounting's public posting services. These are business-flow arrows, not
permission for reverse imports or direct cross-module writes. Invoice issue creates no Payment,
JournalEntry, Inventory movement or Sales/Procurement transition. No event bus, plugin loader,
generic financial framework or dependency-resolution engine is introduced.

## Invoice total versus settlement-adjusted outstanding

Billing derives the original invoice total exclusively from its financial snapshots. Draft totals
are previews; an issued total is the original invoice charge, not proof of an unpaid balance.
Standalone BILL-1 exposes invoice total, currency, invoice/due dates and document status. It does
not expose `amount_paid`, payment status, `amount_due` or settlement-adjusted outstanding.
UI wording is **Invoice total** and **Payment status unavailable**; it must not label the total as
fully unpaid, overdue balance or outstanding, even if Payments is installed elsewhere. No default
zero-allocation assumption is permitted. A due date alone does not prove an overdue debt.

Future approved composition derives outstanding from Billing's issued financial state and valid
Payments-owned allocation evidence. For the no-credit/no-reversal case only:
`outstanding = issued invoice total - valid applied amount`. Evidence must identify the same
database execution scope, company, invoice, currency and precision, and be complete/consistent at
the read or allocation transaction boundary. Missing/incompatible/stale evidence yields unavailable
or a validation failure, never a guessed zero-paid value. Allocation mutation must lock/recheck
eligible invoice state and payment/allocation state atomically to prevent concurrent over-allocation.
Concrete APIs, lock protocol, refunds/credits and availability semantics require separate review.

No PaymentAllocation table, mutable paid/balance column, journal-derived replacement for payment
allocations, or duplicate financial source of truth is introduced in Billing. A future pure Billing
calculation may interpret explicitly validated evidence; it must not fetch Payments data itself.

## BILL-1: proposed minimum document contract

This is the proposed implementation specification to review, not implemented schema/API evidence.

**Invoice:** UUID; immutable company; stable company-unique generated number; bill_to_party identity;
bill-to display/legal-name snapshots; invoice_date; optional due_date; Currency identity and
code/decimal-place snapshots; status `DRAFT`/`ISSUED`; notes; issued_at; created_at/updated_at.
No mutable total, balance, payment status or tenant_id. Currency is a shared Core Reference identity
within the selected database, not a company-owned currency row. It may differ from Company base
currency; this grants no FX conversion or Accounting posting capability.

**InvoiceLine:** UUID; immutable company and invoice parent; required nonblank generic description;
quantity; unit_price; stable per-invoice position; timestamps. Description/quantity/unit price are
invoice financial snapshots. No Product/ProductVariant, SalesOrder or PurchaseOrder FK is required.
An optional external source identifier, if later approved, is traceability only and never authority
to import an upstream module or silently regenerate issued lines.

Minimum services: `create_invoice`, `update_invoice`, `add_invoice_line`, `update_invoice_line`,
`remove_invoice_line`, `issue_invoice`; each accepts BusinessContext and explicit data/identifiers.
Minimum reads: `invoices_for_company`, `invoice_detail`, `invoice_total`, protected by view permission
and company scope. Listing has deterministic ordering and the accepted 50-row pagination pattern.
UI: list/search/filter, create/edit draft, line editing, detail and normal POST issue action, using
the accepted responsive shell and navigation/security conventions. No payment screen or action.

### Financial and lifecycle invariants

- Quantity and unit price follow existing Sales/Procurement `Decimal(18, 4)` input precision:
  quantity `0.0001..99999999999999.9999`; price `0..99999999999999.9999`. Parse Decimal-compatible
  strings/integers/Decimals before comparison; reject malformed values, NaN, infinities, booleans,
  binary floats, excessive fractional precision and range overflow with field ValidationError.
  Never silently round an input to fit persistence. Zero-price lines and a zero-total invoice are
  allowed if there is at least one valid positive-quantity line; no payment/paid status is inferred.
- Multiply exact quantities/prices (up to eight fractional places); sum unrounded line products,
  then round the document total once using `ROUND_HALF_UP` at the invoice's currency precision.
  Use sufficient Decimal arithmetic precision (at least 50 digits), consistent SQL/Python results,
  and a checked `Decimal(38, 8)` aggregate range before persistence/issue: raw and rounded amounts
  must be nonnegative and below `10^30`. Exceeding the supported range rejects the operation.
  No floating-point money and no arbitrary authoritative stored total.
- BILL-1 proposes currency decimal places `0..8`, matching the aggregate's maximum fractional
  scale; unsupported Reference configurations fail validation locally without changing Core.
  Snapshot code/precision on draft creation or an explicit currency change. Issue requires the
  active Currency still matches those snapshots; otherwise explicitly refresh the draft before
  issue. Issued computation/display always uses frozen precision, even after Reference changes.
  Unit prices display all four decimal places. Line products must remain available at full
  precision; currency-rounded line displays are non-additive previews where rounding differs
  from the once-rounded document total. The UI explains that policy rather than hiding precision.
- bill_to_party must be active, person or organization, and belong to the invoice company on
  create/change and issue. No Sales origin or `is_customer` role is required by generic Billing.
  Party remains the identity owner; draft bill-to change/explicit refresh updates snapshots with
  audit, while issue freezes the existing displayed snapshots. Later Party rename/retirement
  cannot rewrite issued history. Party and Currency references are protected from deletion while
  referenced. Revalidate reference eligibility during issue using the current transaction state.
- Dates are validated canonical dates; invoice_date defaults to company-local today, optional
  due_date must not precede invoice_date. issued_at is a server-generated aware UTC timestamp,
  displayed through accepted company-time helpers. Dates do not enable scheduling/dunning.
- Number is generated by Billing's service, immutable after creation, and unique under a database
  `(company, number)` constraint. Use collision-safe module-local generation, not `MAX()+1`;
  no configurable sequence engine or claim of jurisdiction-compliant gapless numbering.
- Draft header/lines may change through owning services. Empty drafts are allowed; issue requires
  at least one valid line. Company/parent/number cannot be reassigned. Header deletion is deferred
  from BILL-1; draft line removal is supported. Direct model paths must preserve ownership and
  lifecycle invariants; public bulk update/create/upsert/queryset-delete paths must not bypass
  them. Only a narrowly controlled internal issue transition may alter lifecycle state.
- `DRAFT -> ISSUED` is the sole transition. Issued header and lines, including notes/snapshots,
  dates/currency and relationships, cannot be edited, removed or returned to draft. A stale model
  object or substituted in-memory parent must not bypass persisted ownership/status checks.
- Repeating issue on the same issued invoice reauthorizes the caller and returns that invoice
  without another transition, timestamp change or success audit. Concurrent issue has one effect.
  The initial draft-create operation does not promise request-key deduplication; callers retain
  the returned ID and never replay creation as an issue retry. External import/integration creation
  needs separately approved source-key idempotency before exposure. No payment retry keys exist here.
- Void, credit notes, financial reversal, issued deletion and cancellation are explicitly deferred.
  BILL-1 has no `VOID` state or void endpoint. Even an apparently unpaid issued invoice cannot be
  voided using absent allocation evidence. A later contract must account for Payments/Accounting
  effects, corrections, concurrency and historical evidence before those operations are allowed.

### Foundation, RBAC, audit and concurrency

Proposed exact permission vocabulary: `billing.invoice.view`, `billing.invoice.create`,
`billing.invoice.update`, `billing.invoice.issue`. Update covers draft header and line changes.
HTTP action GET forms and POST handlers enforce their action permission; views are presentation
adapters. Reads require view permission. Services authorize independently for non-HTTP callers.

Every mutation uses ADR 0012 `business_atomic`/`business_atomic_context()` at call/enter time, with
aggregate writes, locks, audit and related reads on the same selected alias. Lock active Company,
then revalidate BusinessContext/RBAC after any wait, then lock/re-read the authoritative invoice
and affected lines. Never trust mutable in-memory parent IDs. Serialize issue against edit/remove;
if issue wins, waiting edits fail; if a draft edit wins, issue validates the committed new state.
No implicit-default atomic block, forced-default ORM operation, alias switching inside a business
transaction, cached cross-database objects or cross-database FK is permitted.

Audit actions: `billing.invoice.created`, `billing.invoice.updated` (including add/update/remove
line and every persisted snapshot change), and `billing.invoice.issued`. Record actor, company,
object identity and minimal structured change metadata through Core Audit in the same transaction.
True no-ops and successful issue retries do not duplicate success events. Audit failure rolls back
the mutation; validation/permission failures leave no partial document, line or success audit.

Manifest hard dependencies are exactly Party/organization/reference/access; deterministic permission
registration preserves existing enablement and uses migration-local frozen declarations. Fresh
module registration is disabled by default. Missing/disabled module means hidden navigation and
HTTP 404. Installed Python services remain callable with valid context and permission regardless
of module enablement. No custom loader or service-level registry enablement gate is introduced.
Company stays explicit business scope; BusinessContext is unchanged, with no tenant_id or SaaS
activation. This contract authorizes no current registry, permission or database changes.

## Subsequent gates and deliberate deferrals

PAY-1 separately specifies standalone payment receipts/methods, positive finite amounts, company/
currency/Party validity, payment retry keys and derived unapplied amounts. Invoice allocations
remain Payments-owned but require the optional Billing integration contract described above;
partial allocations, atomic concurrent over-allocation rejection and retry safety must be audited
before enabling that integration. PaymentAllocation linkage/schema, settlement details, refund/
reversal lifecycle and permission vocabulary are intentionally not frozen by BILL-1.

ACC-1 preserves ADR 0006's independent Company-base-currency balanced journal core, posted
immutability, rollback/idempotency and derived trial balance. Neither invoice issue nor payment
receipt automatically posts a journal until a separately reviewed integration is authorized.

Deferred beyond BILL-1: payment gateways; customer refunds; vendor/AP billing; credit notes/void;
recurring invoices; subscriptions; advanced taxes (no tax calculation in this MVP); discounts/
promotions; FX conversion; Accounting automation; Sales-to-Billing automation; Ecommerce checkout;
payment reconciliation/settlement processing; dunning; fiscal/localized numbering. Defining future
ownership does not approve those features. Billing owns approved invoice correction semantics,
Payments owns approved payment refund/settlement semantics, Accounting owns ledger corrections.

## Reconciliation and acceptance evidence required

| Conflicting evidence | Resolution in this candidate |
| --- | --- |
| ADR 0006 section 7 and old Batch 2D put Payment/PaymentAllocation in Billing | Invoice-only BILL-1; Payments owns those concepts under PAY-1 |
| Old Billing `amount_paid`/`amount_due` and paid/due UI imply allocations exist | Original invoice total only; settlement-aware amounts unavailable until valid optional composition |
| Old `DRAFT / ISSUED / VOID` and "void if safe" have no approved safety policy | DRAFT/ISSUED only; void/credit explicitly deferred |
| Boundaries/map assign payment orchestration to Billing | Separate owner for each fact; optional composition performs automation |
| Preserved ADR/map make generic Payments require Billing | Generic Payments independent; optional invoice allocation consumes Billing public contracts |
| Old Accounting integration calls a Billing payment source | Separate Billing invoice and Payments outcome integrations; independent Accounting retained |
| Five-module Phase 2 count and combined Invoice/Payment flow | Six standalone modules; BILL-1, PAY-1 and ACC-1 individually gated |

Independent BILL-0 contract review is complete. Before BILL-1 implementation, separate explicit
implementation authorization remains required. Before BILL-1 acceptance: PostgreSQL/SQLite tests, fresh bootstrap,
Ruff/Django/drift checks; boundary Decimals/rounding/currency snapshots; cross-company rejection;
issue retry/rollback; bulk/stale-instance immutability; real PostgreSQL lock coordination for issue
versus edit/remove and permission/access revocation; HTTP action RBAC and stale-company forms;
module gating; non-HTTP permission enforcement; generic lines without Catalog; no payment/ledger/
stock effects; and responsive UI at supported boundary values. Reuse the frozen UI/read-path and
database architecture guards. Do not weaken accepted Core or other module contracts for tests.

Consequences: standalone Billing cannot report payment-aware debt yet; invoice corrections wait
for a financial safety contract; generic Payments remains installable without Billing; optional
integration storage and atomicity must be specified before allocations are built. Existing npm
advisories and Action runtime warnings remain separate pre-production maintenance follow-ups.
