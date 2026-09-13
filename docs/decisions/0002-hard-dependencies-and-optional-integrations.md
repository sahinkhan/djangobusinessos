# ADR 0002 — Hard Module Dependencies and Optional Integrations

Status: Accepted

## Context

BusinessOS is intended to compose reusable horizontal modules into many different products. A hard dependency that is convenient for one flow can make unrelated products unnecessarily heavy.

Examples:

- Sales must work for service businesses that do not manage stock.
- Procurement may be used for services/non-stock purchases.
- Billing must work for School, Hospital, Hotel and other verticals without requiring Sales or Procurement.
- Accounting must be reusable without requiring Billing.

Therefore module dependency declarations must distinguish between capabilities required for a module to function and optional integrations that become active only when both capabilities are present.

## Decision

### Hard dependency

A module may declare another module as a hard dependency only when it cannot provide its own meaningful core capability without that dependency.

Examples:

- Sales requires Party and Catalog.
- Inventory requires Catalog.
- Billing requires Party.

### Optional integration

Cross-module automation that enriches two otherwise-usable modules is an optional integration, not a hard dependency.

Examples:

- confirmed Sales Order -> Inventory reservation/issue
- Purchase receipt -> Inventory receipt
- Invoice/payment -> Accounting journal posting
- Ecommerce -> Inventory availability/reservation
- Hospital pharmacy -> Inventory

Optional integrations must use the owning module's public services/contracts and must not write another module's tables directly.

Do not build a generic plugin/event/DI framework for this. When the first real integration is implemented, use the smallest explicit integration seam that keeps both modules independently usable. An explicit integration/orchestration package may be introduced when justified.

## Consequences

- Standard modules remain reusable in more product combinations.
- Client deployments do not pull in unrelated modules merely because an integration exists elsewhere.
- Vertical modules can compose Billing, HR, Accounting, Inventory, etc. independently.
- Phase 2 must define concrete service contracts before implementing Sales/Inventory, Procurement/Inventory or Billing/Accounting automation.
- Circular imports remain prohibited.

## Rule

**Hard dependencies describe minimum capability requirements. Optional integrations describe cross-capability automation. Do not confuse the two.**
