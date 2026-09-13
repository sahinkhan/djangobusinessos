# ADR 0008 — Standalone Procurement Acceptance

Status: Accepted

Date: 2026-09-14

## Context

Batch 2B introduced standalone Procurement on `phase2-procurement`. Independent technical and
architecture review accepted implementation commit
`09ee59db53ee1f6f90faa1f31170e50098a0a9ec` after the audit findings were closed.

The final review confirmed company-scoped Purchase Order lifecycle behavior, ProductVariant item
identity, immutable posted Purchase Receipts, partial and cumulative receiving, over-receipt
protection, exact-request idempotency, transaction rollback, concurrent receipt safety, module
gating, and the absence of Inventory coupling.

## Decision

Standalone Phase 2B Procurement is accepted and closed at implementation commit
`09ee59db53ee1f6f90faa1f31170e50098a0a9ec`.

The accepted contract is:

- Procurement owns company-scoped `PurchaseOrder`, `PurchaseOrderLine`, `PurchaseReceipt`, and
  `PurchaseReceiptLine` records.
- A supplier is an active, company-scoped Party with the supplier role.
- Purchase Order lines reference concrete, active, purchasable ProductVariants and retain
  historical item snapshots.
- Purchase Orders follow DRAFT -> CONFIRMED -> CANCELLED where cancellation is valid. Lifecycle
  transitions and conflicting mutations serialize on the persisted Purchase Order row.
- Draft headers and lines are editable only through Procurement services. Confirmed or cancelled
  business-significant content is immutable through ordinary model paths.
- Purchase Receipts are immutable posted Procurement facts created only through the validated,
  atomic `receive_purchase_order()` service. Ordinary receipt and receipt-line `save()` creation
  is rejected.
- Receipt quantities use the schema's 18-digit/four-decimal precision without implicit rounding.
  Received and remaining quantities are derived from immutable receipt lines.
- Partial receipts are supported, while cumulative receipt quantity cannot exceed ordered
  quantity. Stale payloads fail atomically rather than silently dropping submitted lines.
- Company-scoped idempotency keys return the existing receipt only for the same canonical order,
  date, line set, and quantities; conflicting reuse raises an explicit validation error.
- Deployment registration preserves existing module enablement, while a newly registered
  Procurement module is disabled by default.
- Procurement has no hard dependency on Sales, Inventory, Billing, or Accounting. Posting a
  Purchase Receipt creates no stock movement, vendor bill, or accounting entry.

Breaking these contracts requires a later explicit architecture decision and compatibility
assessment. Bulk ORM operations and raw SQL remain outside ordinary model/service guarantees.

## Verification basis

- Independent PostgreSQL review on Python 3.13.15 at the accepted implementation commit: 89 tests
  passed without a teardown warning.
- SQLite verification: 84 tests passed with five expected PostgreSQL-only skips.
- The 28 Procurement module-local tests passed on PostgreSQL, including concurrent confirmation,
  line-position allocation, over-receipt serialization, and cross-order idempotency collision.
- Stale HTTP receipt submission rejects the complete request; fully received exact HTTP retries
  return the existing receipt.
- Unsupported quantity precision/range is rejected before persistence, and canonical ISO dates
  remain stable across idempotent retries.
- Ruff, Django system checks, migration drift, fresh PostgreSQL bootstrap, and reproducible
  Tailwind compilation passed.
- Representative implementation QA at 1280x720 and 390x844 covered the Purchase Order and receipt
  workflows, module navigation, monetary/quantity presentation, and mobile overflow containment.
- Hosted CI run 34778722306 passed on exact commit
  `09ee59db53ee1f6f90faa1f31170e50098a0a9ec`.

## Consequences

The future `phase2-commercial-core` integration branch may consume the accepted standalone
Procurement module without reopening its Batch 2B contract. Procurement stays outside `main`
until that planned integration gate is executed.

This decision does not implement or accept Inventory, Billing, Accounting, optional integrations,
the full Phase 2 exit, or production launch readiness. Any future Purchase Receipt -> Inventory
automation must call Inventory's public service contract and must not make Inventory a hard
Procurement dependency.
