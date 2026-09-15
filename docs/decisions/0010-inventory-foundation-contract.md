# ADR 0010 — Inventory Foundation Contract

Status: Accepted historical closure — post-closure corrective re-audit pending

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
The candidate was formally accepted in documentation-only checkpoint
`eb2f52afc53fd8c36249bc6a1e61c15dba9effe8`; branch CI #61 passed, the checkpoint was adopted
into canonical `main` by normal fast-forward, and exact-head main
[CI #62](https://github.com/sahinkhan/djangobusinessos/actions/runs/34931069346) succeeded. Gate
4C is accepted, adopted, and closed. Billing, Accounting, Procurement-to-Inventory,
Sales-to-Inventory, other integrations, and production deployment remain unauthorized. Full
Phase 2 is not complete.

## Post-closure correctness remediation

The administrative acceptance/adoption/closure at
`60f879a036e0fd21eada1375fa695f32adc7dc91` remains part of the historical record. A later
independent correctness audit returned REVISE for four narrow P2 findings: company-local
`effective_at` render/parse and DST handling, combined movement-history filters matching
different lines, incomplete snapshot/UoM audit change detection, and balance/history page RBAC
occurring after filter construction.

Remediation `343c413bff7f7e520a5a031f92f461a8058db3cc` uses one explicit Company timezone for datetime
rendering and Django form parsing, requires combined history filters to match one line, compares
all persisted business-significant line fields for update audit decisions, and enforces
`inventory.balance.view` before HTTP filter construction. It adds no migration or cross-module
behavior. Status is IMPLEMENTED / AWAITING INDEPENDENT GATE 4C CORRECTIVE RE-AUDIT; this record
does not claim a new FINAL PASS or re-closure.

That correction was published through candidate
`23a12ae544be2e611ac3fd5bfa90d62299599648`. Independent corrective re-audit returned REVISE for
one residual form-round-trip issue: submitting the unchanged company-local minute could replace a
trusted persisted instant with a minute-normalized value and lose seconds and microseconds.
Remediation `b33e6faaf931777575292a42af775a1c11986984` passes the trusted server-side original timestamp to
the edit form and preserves it only when its displayed company-local minute is unchanged; an
explicitly changed minute continues to use the validated parsed value. The Company timezone and DST
validation contract is unchanged. Candidate head
`d7fc63c2af77e210cdbae8a72837c1497200f251` passed CI #68, but independent re-audit returned REVISE:
a persisted instant within a DST fall-back fold was rejected by generic ambiguity validation before
the trusted-original comparison ran. Final narrow remediation
`145c9d51a3507aa1df8d6548659e16e506940d1e` compares the raw minute to the persisted instant's
company-local rendered minute before generic conversion, preserving either fold exactly while
continuing to reject newly entered ambiguous or nonexistent times. Final corrective candidate
`09794e9293da78117e5873ebbff9f4b98fa5e1b7` passed CI #69 with 422 PostgreSQL tests, and independent
final corrective re-audit returned FINAL PASS. The post-closure corrective implementation is
formally ACCEPTED; canonical adoption and corrective-cycle closure remain pending. The original
historical Gate 4C closure remains preserved.
