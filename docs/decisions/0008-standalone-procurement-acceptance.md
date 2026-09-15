# ADR 0008 — Standalone Procurement Acceptance

Status: Accepted — historical standalone and canonical Gate 4B adopted/closed

Date: 2026-09-14

## Context

Historical Batch 2B introduced standalone Procurement on `phase2-procurement`. Independent review
accepted implementation `09ee59db53ee1f6f90faa1f31170e50098a0a9ec`; its documentation closure
head is `a99377ca55355a2e4cdebd64ff73cf29fd3eff83`.

Gate 4B replays that behavior onto canonical Core Foundation v1 and the adopted Party, Catalog,
and Sales baseline. The implementation candidate is
`395da2ad874fc2efb72219da71316b9a6d8f73bf` on `gate4b-procurement-adoption`. At initial candidate
publication it was not merged, formally accepted, or closed. Candidate documentation head
`12d1a1f90689979048cdf3b4f59836b026dd153f` passed hosted CI #53, but completion review blocked
acceptance because its PostgreSQL suite did not yet cover the full authorization-revocation and
confirmation-versus-mutation concurrency matrix. Narrow test remediation
`b8c49e1fb5b62f9169038b59e35b6d4e7adfb8e0` closes those coverage gaps without changing
production code or migrations. Hosted CI #54 passed exact remediation head
`1eabb0e9806342cc2ba71f1468eb18af120cddb9` with 342 PostgreSQL tests, and independent Gate 4B
re-audit gave that candidate FINAL PASS. Documentation-only acceptance commit
`e4ea1791f0b2c7d1209ea574de3689970e1fc398` passed exact-head branch CI #55, was adopted into
canonical `main` by normal fast-forward, and passed exact-head main CI #56.

## Decision

The historical standalone Procurement contract remains accepted:

- Procurement owns company-scoped `PurchaseOrder`, `PurchaseOrderLine`, `PurchaseReceipt`, and
  `PurchaseReceiptLine` records.
- Purchase Orders follow DRAFT -> CONFIRMED -> CANCELLED where cancellation is valid. A Purchase
  Order with posted receipts cannot be cancelled.
- Suppliers are active same-company Parties with the supplier role. Lines reference active,
  purchasable, same-company ProductVariants and retain SKU/name/description snapshots.
- Purchase Receipts are immutable posted Procurement facts created only by the atomic,
  idempotent `receive_purchase_order()` service. They do not create Inventory movements, vendor
  bills, or Accounting entries.
- Partial and cumulative receiving are supported; cumulative receipts cannot exceed ordered
  quantities. Receipt quantity uses 18 digits and four decimal places without silent rounding.
- An exact company-scoped idempotent retry returns the existing receipt without duplicate lines
  or audit. Conflicting reuse fails atomically.
- Module enablement controls navigation and HTTP access only. Installed Python services remain
  callable with valid `BusinessContext` and RBAC permission.

Historical acceptance explicitly left bulk ORM operations and raw SQL outside ordinary
model/service guarantees. Canonical Gate 4B strengthens that boundary: Procurement-local
QuerySets reject public bulk update/create/upsert/delete paths, lifecycle transitions use a narrow
row-locked primitive, and posted receipts use a token-constrained internal insertion path. Raw SQL
remains outside the ORM contract. This hardening does not change Procurement business semantics.

Canonical Gate 4B freezes these permission identities for audit:

```text
procurement.order.view
procurement.order.create
procurement.order.update
procurement.order.confirm
procurement.order.cancel
procurement.receipt.receive
```

Significant successful mutations use these audit actions:

```text
procurement.order.created
procurement.order.updated
procurement.order.confirmed
procurement.order.cancelled
procurement.receipt.posted
```

## Verification basis

Local candidate evidence at implementation `395da2ad...`:

- fresh canonical Procurement migrations `0001_initial` and `0002_register_manifest`;
- PostgreSQL full suite: 323 passed; Procurement-local suite: 40 passed;
- SQLite full suite: 270 passed with 53 expected PostgreSQL-only skips;
- Ruff, Django checks, migration drift, module gating, RBAC, audit rollback, ORM hardening,
  idempotency, and PostgreSQL concurrency checks passed;
- Tailwind was rebuilt from a clean `npm ci`; the generated stylesheet change reflects only
  classes used by the new responsive Procurement templates.
- representative 1280px desktop and 390px mobile QA covered long PO/receipt/SKU/supplier/key
  identities, partial and cumulative display, service and variable ProductVariants, exact retry,
  cancellation without receipts, and explicit no-Inventory wording without page overflow.

This is candidate evidence, not an acceptance assertion. Exact-head hosted CI and independent
Gate 4B audit were required. Hosted CI #53 subsequently passed exact candidate head `12d1a1f...`,
but the completion review remained BLOCKED on missing deterministic PostgreSQL coverage for role
and company-access revocation across representative mutations, confirmation versus header/line
edit/removal, and confirmation versus stale order/line deletion.

Remediation `b8c49e1...` adds that coverage using observed PostgreSQL row-lock blocking rather than
timing assumptions. The authorization matrix covers role, permission, and company-access
revocation across order update, confirmation, cancellation, and receipt posting. Both sides of
the confirmation-versus-draft-mutation ordering and stale instance deletion are covered, with
atomic mutation/audit assertions. Local remediation verification passed 342 PostgreSQL tests,
including all 27 Procurement concurrency cases, plus 270 SQLite tests with 72 explicit
PostgreSQL-only skips. Hosted CI
[run #54](https://github.com/sahinkhan/djangobusinessos/actions/runs/34881374281) succeeded against
exact head `1eabb0e...`, and independent Gate 4B re-audit returned FINAL PASS.

## Consequences

Gate 4B is formally accepted at candidate `1eabb0e...`, adopted at checkpoint `e4ea179...`, and
closed. Gate 4C Inventory, Billing, Accounting, optional integrations, Procurement-to-Inventory
posting, production launch, and full Phase 2 completion remain outside this decision.

## Post-closure audit history

An independent Procurement post-closure audit returned REVISE for five narrow findings:

- historical `PurchaseOrderLine` deletion could authorize against a caller-mutated parent;
- receipt HTTP processing could silently discard noncanonical or duplicate UUID field aliases;
- SKU/name-only snapshot refreshes could persist without the canonical update audit;
- supported supplier, SKU, quantity, cost, and total values could overflow Procurement UI;
- non-finite order-line Decimal values could escape field-specific validation.

Procurement-local remediation is implemented at
`1ccaf0bc74816b11035cb33f24e172ff8f902329` on
`gate4b-procurement-postclosure-remediation`. It preserves the historical acceptance record and
adds no schema, integration, or cross-module behavior. Status: IMPLEMENTED / AWAITING INDEPENDENT
PROCUREMENT CORRECTIVE RE-AUDIT. It is not yet accepted, adopted into `main`, or re-closed.

That first corrective re-audit returned REVISE for one residual P3: invalid numeric strings could
reach `PurchaseOrderLine.clean()` comparisons and raise an uncontrolled `TypeError` instead of a
field-specific `ValidationError`. Residual remediation
`c34daec0d3ad876612c15536f8c94148f7f4664c` normalizes `quantity` and `unit_cost` through Django's
DecimalField conversion semantics before finite and business-rule comparisons. Status:
IMPLEMENTED / AWAITING SECOND INDEPENDENT PROCUREMENT CORRECTIVE RE-AUDIT. Historical acceptance
remains preserved; corrective adoption and Gate 4B re-closure remain pending and unauthorized.
