# ADR 0008 — Standalone Procurement Acceptance

Status: Accepted (historical standalone contract); canonical Gate 4B adoption awaiting audit

Date: 2026-09-14

## Context

Historical Batch 2B introduced standalone Procurement on `phase2-procurement`. Independent review
accepted implementation `09ee59db53ee1f6f90faa1f31170e50098a0a9ec`; its documentation closure
head is `a99377ca55355a2e4cdebd64ff73cf29fd3eff83`.

Gate 4B replays that behavior onto canonical Core Foundation v1 and the adopted Party, Catalog,
and Sales baseline. The implementation candidate is
`395da2ad874fc2efb72219da71316b9a6d8f73bf` on `gate4b-procurement-adoption`. It is not merged,
formally accepted, or closed; independent Gate 4B audit remains mandatory.

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
Gate 4B audit are still pending.

## Consequences

Gate 4B may be accepted and adopted only through a later separately authorized operation after
independent audit. `main`, Gate 4C Inventory, Billing, Accounting, optional integrations, and
Procurement-to-Inventory posting remain outside this decision.
