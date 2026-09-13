# ADR 0006 — Phase 2 Commercial Core Contracts

Status: Accepted

Date: 2026-09-13

## Context

Phase 1 froze company-scoped Party and variant-first Catalog contracts. Phase 2 introduces the first transactional business modules: Sales, Procurement, Inventory, Billing and Accounting.

These modules must be useful independently, remain compatible with deployment-level module gating, and avoid hard dependencies created only for cross-capability automation.

## Decision

### 1. Standalone modules first, optional integrations second

Phase 2 modules are implemented and audited as standalone capabilities before cross-module automation is added.

Hard dependencies remain those in `docs/architecture/DEPENDENCY_MAP.md`:

```text
sales -> party, catalog, organization, reference, access
procurement -> party, catalog, organization, reference, access
inventory -> catalog, organization, reference, access
billing -> party, organization, reference, access
accounting -> party, organization, reference, access
```

Inventory is not a hard dependency of Sales or Procurement. Accounting is not a hard dependency of Billing.

Optional integrations use explicit synchronous Python services and the owning module's public service contract. Phase 2 does not introduce an event bus, command bus, workflow engine, DI container or generic integration framework.

### 2. ProductVariant remains transactional item identity

SalesOrderLine, PurchaseOrderLine and StockMovementLine reference Catalog `ProductVariant` whenever a concrete SKU/item is required.

Simple and variable Products follow the same downstream item identity contract.

Transactional lines may store descriptive snapshots such as SKU/name/description so historical documents remain readable after Catalog labels change. Those snapshots do not become competing Catalog identities.

### 3. Transaction lifecycle rule

Draft business documents may be edited through their owning services.

Confirmed/issued/posted transactional documents become immutable for financially or operationally significant fields. Corrections must use explicit later lifecycle operations rather than silently rewriting posted history.

State transitions are atomic service operations and must be concurrency-safe where duplicate execution could create duplicate stock or ledger effects.

### 4. Sales Phase 2 scope

Sales owns SalesOrder and SalesOrderLine.

Minimum lifecycle:

```text
DRAFT -> CONFIRMED -> CANCELLED (where cancellation is valid)
```

Confirmation does not reduce stock in Phase 2. Stock reservation/fulfillment/shipment semantics are not yet defined, so Sales must not mutate Inventory on confirmation.

Sales quotations remain within Sales ownership but are deferred from the Phase 2 minimum until a real flow requires them.

### 5. Procurement Phase 2 scope

Procurement owns PurchaseOrder, PurchaseOrderLine, PurchaseReceipt and PurchaseReceiptLine.

A PurchaseReceipt records business receipt against a confirmed PurchaseOrder independently of Inventory. Cumulative received quantity must not exceed ordered quantity in the Phase 2 minimum.

When Inventory is enabled, an explicit optional integration may create/post an Inventory receipt from a posted Procurement receipt. Procurement must never write Inventory ledger rows directly.

### 6. Inventory source of truth

Inventory owns StockMovement and StockMovementLine.

Posted movements are the authoritative stock ledger. Phase 2 must not add authoritative mutable stock quantity fields to Product, ProductVariant, Warehouse or another balance row.

Minimum movement types:

```text
RECEIPT
ISSUE
TRANSFER
```

Balances are derived from posted movements.

Phase 2 does not implement reservation/allocation, costing, valuation, lot/serial tracking or a configurable negative-stock policy. A derived balance may therefore become negative; preventing negative stock is a later explicit policy requiring correct concurrency semantics.

Duplicate posting protection/idempotency is required for posting and integration-created movements.

### 7. Billing source of truth

Billing owns Invoice, InvoiceLine, Payment and PaymentAllocation.

Invoice lines are generic financial/document lines and do not hard-depend on Catalog. This keeps Billing reusable by Sales, School, Hospital, Hotel and other verticals.

Issued invoices are immutable for core financial fields. Invoice total and outstanding amount are derived from lines and allocations rather than maintained as arbitrary mutable balances.

Phase 2 excludes taxes, advanced discounts, credit notes, payment gateways and FX conversion.

### 8. Accounting source of truth

Accounting owns Account, Journal, JournalEntry and JournalEntryLine.

Only posted balanced journal entries are authoritative for the general ledger. No mutable authoritative account balance field is allowed.

Posting requires total debit == total credit and a non-zero balanced entry. Posted entries and lines are immutable for ledger-significant fields.

Trial Balance is derived from posted JournalEntryLine records.

Phase 2 Accounting posts only in the Company's base currency. Multi-currency transaction documents may exist in Sales/Procurement/Billing, but FX conversion/revaluation and foreign-currency ledger posting are deferred.

Duplicate external posting protection/idempotency is required where an integration can be retried.

### 9. Money and pricing rule

Sales and Procurement transactional lines store explicit unit price/cost snapshots. Billing stores explicit invoice-line amounts through quantity and unit price.

Catalog does not gain a pricing engine in Phase 2.

Phase 2 does not implement pricelists, promotions, tax calculation or a generic money framework.

### 10. Document number rule

Each owning module provides a stable company-unique human-readable document number generated through its service path.

Phase 2 does not introduce a shared configurable sequential-numbering platform. Implementations must not use a race-prone `MAX(number) + 1` strategy. Collision-safe module-local generation plus a database uniqueness constraint is sufficient for Phase 2.

Regulatory/localized numbering can be introduced later through an explicit compatible contract.

### 11. Module gating

Every Phase 2 module registers through the existing BusinessModule registry and is disabled by default.

`is_enabled` continues to control user-facing navigation and HTTP accessibility only. It does not dynamically install Python code or migrations.

Hard dependency enablement is explicit operational configuration in Phase 2; no automatic dependency-resolution engine is introduced.

### 12. Optional Phase 2 integration seams

After standalone module audits pass, Phase 2 may implement these explicit integrations:

```text
Procurement PurchaseReceipt -> Inventory receipt movement
Sales confirmed order -> Billing invoice creation
Billing issued invoice -> Accounting journal entry
Billing payment -> Accounting journal entry
```

Sales confirmation -> Inventory issue is deliberately NOT implemented until shipment/fulfillment or reservation semantics are defined.

Integration services must be retry-safe when they create authoritative Inventory or Accounting effects.

## Consequences

Benefits:

- five modules can be developed largely in parallel;
- Sales and Procurement remain usable for service/non-stock businesses;
- Billing remains reusable by verticals without Sales;
- Accounting remains usable without Billing;
- Inventory and Accounting have clear immutable ledger sources of truth;
- future workflow/events can be extracted from real repeated needs rather than invented now.

Costs:

- some end-to-end automation waits until standalone module contracts pass audit;
- Phase 2 document numbering is intentionally basic;
- no stock reservation/costing/negative-stock policy or foreign-currency ledger accounting is claimed yet.

## Phase 2 gate

Phase 2 is not complete until standalone module contracts and the approved optional integrations pass tests, company-scope checks, module-gating checks, atomicity/idempotency checks for Inventory/Accounting effects, and architecture review.
