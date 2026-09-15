# ADR 0010 — Inventory Foundation Contract

Status: Accepted — Gate 4C technical candidate accepted; canonical adoption pending

Date: 2026-09-15

## Context

Canonical `main` contains Core Foundation v1, Party, Catalog, Sales, and Procurement. The
historical `phase2-inventory` head
`f45afdfea33d3fd03d469e6a0cd63d0e5358f38c` is remediation/reference evidence only: it was not
canonically accepted and is not merged or cherry-picked. Gate 4C reconstructs Inventory from
canonical `main` at `8d5a41f83c3f796fa31e7d3f8598c54f7dfc5b95`.

## Decision

Inventory owns `StockMovement` and `StockMovementLine`. A movement is a company-scoped DRAFT
receipt, issue, or transfer which may transition once to POSTED. Posted movement lines are the
authoritative stock ledger and are immutable. Warehouse/ProductVariant balances are derived only
from posted lines:

```text
destination quantity -> positive
source quantity      -> negative
```

Negative balances are allowed. Gate 4C does not implement reservation, fulfillment, availability
policy, or valuation.

Lines reference Catalog `ProductVariant`, preserve SKU and product-name snapshots, and accept
only active STOCKABLE or CONSUMABLE products in the same company. SERVICE products are rejected.
Each line freezes the Product's active default UoM. Quantity is exact decimal `(18, 4)`; Inventory
does not convert UoMs or silently round unsupported precision. Posted history remains readable
after a UoM becomes inactive, while new lines and posting require the active current UoM.

Routes are exact:

```text
RECEIPT  source none, destination required
ISSUE    source required, destination none
TRANSFER source and destination required and different
```

Movement numbers are immutable collision-safe `SM-<UUID>` identities unique within a company.
Optional `source_module`, `source_type`, and `source_id` provenance is all-or-none and immutable.
It reserves a later optional integration boundary; Inventory does not import or read Sales or
Procurement. Optional normalized idempotency keys are company-unique. Posting is retry-safe and
creates exactly one success audit.

Inventory depends only on Catalog, Organization, Reference, and Access. It declares exactly:

```text
inventory.movement.view
inventory.movement.create
inventory.movement.update
inventory.movement.post
inventory.balance.view
```

State-changing services accept `BusinessContext` and, within one transaction, lock the active
Company before rechecking RBAC, lock the Stock Movement aggregate, validate persisted state,
mutate, and append an audit entry. Audit actions are:

```text
inventory.movement.created
inventory.movement.updated
inventory.movement.posted
```

Module enablement controls navigation and HTTP access only. Missing or disabled registry state
does not disable the installed Python services, which remain governed by BusinessContext and
RBAC. Inventory defaults disabled and re-registration preserves explicit enablement.

Inventory-local guarded QuerySets reject public bulk update, bulk create/upsert, and queryset
delete paths for movements and lines. Validated instance paths require narrow service tokens.
Posting uses a private token-constrained primitive which permits only DRAFT to POSTED and changes
only status, posted time, and update time.

## Consequences

- Catalog, Warehouse, and ProductVariant do not gain authoritative stock fields.
- Sales confirmation and Procurement receipts create no Inventory effects in Gate 4C.
- Transfers conserve global quantity while moving quantity between warehouses.
- A future integration must call an explicit Inventory service and receive separate acceptance.
- A future availability or valuation contract can build on immutable posted facts without
  rewriting them.

## Gate status

The original `gate4c-inventory-adoption` implementation candidate is
`e1e94307bd96b2834f677eb02b91d27b87843f21`, published at candidate head
`01037fc7f87e546382931a081750bf367bb78232`. Independent audit BLOCKED acceptance on mixed-UoM
balance safety, HTTP mutation-form RBAC, stale-company HTTP coverage, and a missing
ProductVariant stock-field assertion. Narrow remediation
`78ba3ae92366da9b2136b260cc9a380e22587e08` closed those findings at final candidate
`8b52270959a2f6623de225e08dc081aea8d1630b`. Hosted CI
[run #60](https://github.com/sahinkhan/djangobusinessos/actions/runs/34925582449) passed that exact
head with 410 PostgreSQL tests and all standard checks. Independent re-audit returned FINAL PASS.
The candidate is formally accepted. Canonical adoption and Gate 4C closure remain pending this
controlled execution; Billing, Accounting, integrations, and production deployment remain
unauthorized.
