# Phase 2 — Commercial Core

Status: IN PROGRESS — GATE 4A/4B CLOSED; GATE 4C FORMALLY ACCEPTED, ADOPTION PENDING

Canonical Gate 4 base: `f2d48c1d1a6f12c7b27c925e2c6f14f922d53beb`

Historical standalone-plan base: `361d832713dcd2325363b4059a4f3b6cac7d3715`

Architecture decision: `docs/decisions/0006-phase-2-commercial-core-contracts.md`

## Goal

Build the first reusable transactional core of BusinessOS without turning the Django monolith into a tightly coupled ERP.

Phase 2 delivers minimum standalone Sales, Procurement, Inventory, Billing and Accounting capabilities, then adds a small set of explicit optional integrations after the standalone contracts pass review.

Speed matters, but Inventory and Accounting correctness is more important than feature breadth.

## Required reading

Before any Phase 2 implementation, read and obey:

- `AGENTS.md`
- `docs/ROADMAP.md`
- `docs/architecture/BASELINE.md`
- `docs/architecture/MODULE_BOUNDARIES.md`
- `docs/architecture/DEPENDENCY_MAP.md`
- `docs/decisions/0002-hard-dependencies-and-optional-integrations.md`
- `docs/decisions/0003-catalog-variant-contract.md`
- `docs/decisions/0004-phase-1-party-catalog-contract-freeze.md`
- `docs/decisions/0005-deployment-module-gating-and-simple-variant-lifecycle.md`
- `docs/decisions/0006-phase-2-commercial-core-contracts.md`
- `docs/decisions/0007-standalone-sales-acceptance.md`
- this execution plan

Do not silently change these architecture contracts.

---

# Parallelization strategy

The listed branches below record the historical standalone-development strategy. Canonical Gate 4
adoption is sequential and separately authorized: Sales first, then Procurement, then Inventory.
Gate 4A and Gate 4B are accepted, adopted, and closed.
Gate 4C is authorized only as an isolated candidate awaiting independent audit. Billing,
Accounting, and integrations remain unauthorized.

Recommended branches:

```text
phase2-sales
phase2-procurement
phase2-inventory
phase2-billing
phase2-accounting
```

Each module agent owns primarily:

```text
businessos/modules/<module>/
```

Minimal wiring changes to settings/URLs/tests are allowed. Shared-file conflicts must be resolved later on an integration branch; module agents must not redesign shared architecture to avoid a small merge conflict.

Do not create or populate a canonical integration branch until the relevant Gate 4 adoption steps receive independent acceptance and separate authorization. Historical branches remain read-only evidence and are not merged or cherry-picked into the canonical line.

Do not run independent agents against the same branch/worktree concurrently.

---

# Batch 2A — Sales

## Historical standalone implementation record

Standalone Sales was historically accepted at implementation commit
`a79cb95d031bb38719bcdccfb5b14670cc76cd17`; see ADR 0007. It remains on
`phase2-sales`, outside `main` and the future `phase2-commercial-core` integration branch, until
the planned integration gate. Sales confirmation revalidates the active customer, active
currency, and every active/sellable ProductVariant while holding the order row lock. Draft line
mutations share that order-lock protocol. Monetary totals are derived from lines and displayed
using the Currency `decimal_places` value with `ROUND_HALF_UP`; unit prices display the model's
full four-decimal precision. No Inventory, Billing, or Accounting writes occur.

The independent technical and architecture review passed at
`7e5f5b407415d3b5b32188c94c4e9b4d7dd7a555`. Completion QA on 2026-09-14 exercised the
representative customer -> draft -> service ProductVariant line -> confirm flow at 1280x720 and
390x844. It verified desktop and mobile list/form/detail layouts, mobile navigation, full
four-decimal unit-price display (`USD 0.0049`), currency total display (`USD 0.49`), and confirmed
content immutability. QA exposed narrow-screen page overflow from the long generated order number
and order-lines grid; `a79cb95d031bb38719bcdccfb5b14670cc76cd17` contains and regression-tests
that layout. Hosted CI run 25 passed on that exact commit.

## Canonical Gate 4A adoption status

The first canonical adoption implementation is `28c8028950be1997b4f3d0816b1ec04764222068`; its initial audit/documentation head is `fc609bcd81916c13921c2d1cc7b6a59eda1c1e19`. Independent audit blocked acceptance pending explicit module-gating reconciliation, Sales-local ORM bulk-write/delete protection, transition-vs-edit/delete PostgreSQL regressions, and restoration of these canonical Phase 2 records. Remediation implementation `d62c34e36f0a8b11f59bfdb058143e27f5231c5d` closed those findings. Independent re-audit gave candidate `23338f1cfed11d21d4fa8fd7e92f8de120450977` FINAL PASS, and exact-head hosted CI #48 succeeded with 283 PostgreSQL tests and all required checks passing. Documentation-only acceptance commit `e0c848f34da0bce9b9c6e010a396026ac5889cf4` was adopted into canonical `main` by normal fast-forward, and exact-head main CI #50 succeeded. Gate 4A is accepted, adopted, and closed.

The authoritative module-gating contract remains: `BusinessModule.is_enabled` controls navigation and HTTP availability only. Installed non-HTTP Python services remain callable and require valid `BusinessContext` plus the exact BusinessOS RBAC permission.

## Canonical Gate 4B adoption closure

Gate 4B reconstructs historical standalone Procurement behavior from accepted implementation
`09ee59db53ee1f6f90faa1f31170e50098a0a9ec` onto canonical main
`fb9028bbbec5dfc56e7d579c3c351abcde764833`, without merging or cherry-picking historical
branches. The code-bearing candidate is `395da2ad874fc2efb72219da71316b9a6d8f73bf` on
`gate4b-procurement-adoption`.

It adopts Core Foundation v1 BusinessContext, Company-lock-before-authorization ordering, exact
six-permission RBAC, atomic immutable audit, business-local date defaults, HTTP-only module
gating, and Procurement-local ORM hardening. Purchase Receipts remain Procurement facts and do
not write Inventory, Billing, or Accounting. Local PostgreSQL verification passed 323 tests and
the 40-test Procurement suite; SQLite passed 270 with 53 expected PostgreSQL-only skips.

Candidate documentation head `12d1a1f90689979048cdf3b4f59836b026dd153f` passed hosted CI #53.
Completion review nevertheless returned BLOCKED because deterministic PostgreSQL coverage was
missing for role/company-access revocation across representative mutations and for confirmation
versus header edit, line edit/removal, and stale instance deletion. Remediation
`b8c49e1fb5b62f9169038b59e35b6d4e7adfb8e0` adds the complete matrix without changing production
code or migrations. Local remediation verification passed 342 PostgreSQL tests, including 27
Procurement concurrency cases, and 270 SQLite tests with 72 expected PostgreSQL-only skips.

Hosted CI
[run #54](https://github.com/sahinkhan/djangobusinessos/actions/runs/34881374281) passed exact final
candidate `1eabb0e9806342cc2ba71f1468eb18af120cddb9` with 342 PostgreSQL tests, and independent
Gate 4B re-audit returned FINAL PASS. Documentation-only acceptance commit
`e4ea1791f0b2c7d1209ea574de3689970e1fc398` passed exact-head branch
[CI #55](https://github.com/sahinkhan/djangobusinessos/actions/runs/34919248812), was adopted into
canonical `main` by normal fast-forward, and passed exact-head main
[CI #56](https://github.com/sahinkhan/djangobusinessos/actions/runs/34919503196). Gate 4B is
accepted, adopted, and closed. At that checkpoint Gate 4C and later work remained unauthorized;
Gate 4C subsequently received candidate-only authorization recorded below.

## Ownership

Sales owns customer sales-order lifecycle only.

Phase 2 minimum models:

### SalesOrder

Minimum fields:

- UUID id
- company
- company-unique human-readable number
- customer -> Party
- order_date
- currency -> Currency
- status: DRAFT / CONFIRMED / CANCELLED
- notes
- confirmed_at
- created_at / updated_at

### SalesOrderLine

Minimum fields:

- UUID id
- company
- sales_order
- product_variant -> Catalog ProductVariant
- SKU/name/description snapshot as useful for historical readability
- quantity
- unit_price
- ordering/position if useful
- created_at / updated_at

## Rules

- customer must belong to the same company, be active and have customer role;
- ProductVariant/Product must belong to the same company, be active and sellable;
- quantity > 0;
- unit_price >= 0;
- order must contain at least one valid line before confirmation;
- draft order/lines may be edited through Sales services;
- confirmed order/lines are immutable for business-significant fields;
- cancellation is explicit and must not silently mutate Inventory/Billing/Accounting;
- confirmation must be atomic and retry-safe on the same order;
- ProductVariant is the item identity; do not branch on simple vs variable Product;
- no Inventory stock mutation on Sales confirmation.

## Services

Minimum useful services:

- create_sales_order
- update_sales_order
- add/update/remove_sales_order_line while draft
- confirm_sales_order
- cancel_sales_order where valid

Business services accept BusinessContext, never HttpRequest.

## Selectors

At minimum:

- sales_orders_for_company
- sales_order_detail
- confirmed_sales_orders
- order totals derived from lines

## UI

Minimum operational UI:

- list/search/filter
- create/edit draft order
- add/edit/remove lines
- detail
- confirm action
- cancel action if valid

Use existing module gating. Disabled Sales returns 404 and is absent from navigation.

## Explicitly not Sales Phase 2

- quotation workflow
- shipment/delivery
- reservation/allocation
- Inventory issue
- pricelists/promotions/tax
- commissions
- CRM pipeline
- returns/RMA

---

# Batch 2B — Procurement

## Ownership

Procurement owns purchase orders and business receipt records. It does not own stock balances.

Phase 2 minimum models:

### PurchaseOrder

- UUID id
- company
- company-unique human-readable number
- supplier -> Party
- order_date
- currency
- status: DRAFT / CONFIRMED / CANCELLED
- notes
- confirmed_at
- timestamps

### PurchaseOrderLine

- UUID id
- company
- purchase_order
- ProductVariant
- descriptive snapshots
- quantity
- unit_cost
- timestamps

### PurchaseReceipt

- UUID id
- company
- company-unique human-readable number
- purchase_order
- receipt_date
- idempotency_key or equivalent retry-safe key where required
- posted_at/created_at

### PurchaseReceiptLine

- UUID id
- company
- receipt
- purchase_order_line
- quantity_received

## Rules

- supplier must belong to company, be active and have supplier role;
- ProductVariant/Product must be same-company, active and purchasable;
- ordered/received quantity > 0;
- unit_cost >= 0;
- confirm only non-empty valid orders;
- confirmed order business-significant fields are immutable;
- receipt can be created only against a confirmed PurchaseOrder;
- cumulative received quantity cannot exceed ordered quantity in Phase 2;
- duplicate receipt execution with same approved idempotency key must not create duplicate receipt effects;
- Procurement receipt records do not directly write Inventory tables.

## Services

- create/update_purchase_order
- add/update/remove_purchase_order_line while draft
- confirm_purchase_order
- cancel_purchase_order where valid
- receive_purchase_order / create_purchase_receipt

## Selectors

- purchase_orders_for_company
- purchase_order_detail
- receipts_for_purchase_order
- received quantity / remaining quantity derived from receipts

## UI

- order list/create/edit/detail
- line editing
- confirm
- receive confirmed order including partial receipt
- receipt detail

## Explicitly not Procurement Phase 2

- RFQ/vendor tendering
- approval chains
- vendor bills/AP automation
- landed cost
- Inventory balance mutation inside Procurement
- tax/pricelist engine

---

# Batch 2C — Inventory

## Ownership

Inventory owns the stock movement ledger.

## Canonical Gate 4C adoption candidate

Gate 4C starts from canonical `main` at
`8d5a41f83c3f796fa31e7d3f8598c54f7dfc5b95`. Historical `phase2-inventory` at
`f45afdfea33d3fd03d469e6a0cd63d0e5358f38c` is remediation/reference evidence only; it was not
accepted canonically and was not merged or cherry-picked. The isolated
`gate4c-inventory-adoption` branch reconstructs Inventory against Core Foundation v1 with the
five frozen Inventory permissions, Company-lock-before-RBAC ordering, atomic audit, guarded ORM
paths, exact UoM/quantity rules, and deterministic PostgreSQL concurrency tests.

The candidate preserves a standalone posted movement ledger and creates no Sales, Procurement,
Billing, or Accounting effects. Original implementation
`e1e94307bd96b2834f677eb02b91d27b87843f21` was published at candidate head
`01037fc7f87e546382931a081750bf367bb78232`; hosted CI #59 passed with 406 PostgreSQL tests.
Independent audit nevertheless BLOCKED acceptance because mixed-UoM history could be summed by
`stock_balance()`, mutation forms lacked explicit action-page RBAC, the required stale-company
HTTP matrix was incomplete, and the no-authoritative-stock-field regression omitted
ProductVariant.

Narrow remediation `78ba3ae92366da9b2136b260cc9a380e22587e08` makes balance selectors fail
closed for incompatible posted UoMs, retains and regression-tests posting-time historical-UoM
rejection, enforces the exact action permission before rendering or executing HTTP mutation
forms, completes the stale-company matrix, and covers ProductVariant. Local verification passed
410 PostgreSQL tests, 314 SQLite tests with 96 expected PostgreSQL-only skips, the 68-test
PostgreSQL Inventory suite, fresh PostgreSQL bootstrap, Ruff, Django checks, migration drift, and
Tailwind reproducibility. Hosted CI #60 passed exact final candidate
`8b52270959a2f6623de225e08dc081aea8d1630b` with 410 PostgreSQL tests, and independent
re-audit returned FINAL PASS. Gate 4C is formally accepted at that candidate. Canonical adoption
and closure are pending this controlled execution; it remains unmerged at this acceptance stage.

Phase 2 minimum models:

### StockMovement

- UUID id
- company
- company-unique human-readable number
- movement_type: RECEIPT / ISSUE / TRANSFER
- status: DRAFT / POSTED
- effective_at/date
- reference/notes
- optional idempotency key with company-scoped uniqueness when supplied
- optional source_module/source_type/source_id metadata for traceability
- posted_at
- timestamps

### StockMovementLine

- UUID id
- company
- stock_movement
- ProductVariant
- quantity
- source_warehouse nullable
- destination_warehouse nullable
- descriptive snapshot if useful
- timestamps

## Rules

- quantity > 0;
- variant and warehouses must belong to the same company;
- RECEIPT requires destination warehouse and no source warehouse;
- ISSUE requires source warehouse and no destination warehouse;
- TRANSFER requires both and they must differ;
- new movements use active variants/warehouses;
- draft movement/lines may be edited through services;
- posting is atomic;
- repeated posting of the same movement must not duplicate effects;
- integration-created movement idempotency keys prevent duplicate authoritative movements;
- posted movement/lines are immutable for ledger-significant fields;
- balance selectors derive quantity from POSTED movements only;
- no authoritative Product/ProductVariant/Warehouse stock field;
- Phase 2 does not promise prevention of negative derived balance.

## Balance semantics

For a given warehouse + ProductVariant:

```text
RECEIPT destination -> +quantity
ISSUE source        -> -quantity
TRANSFER source     -> -quantity
TRANSFER destination-> +quantity
```

## Services

- create_stock_movement
- add/update/remove movement line while draft
- post_stock_movement

No hidden signals.

## Selectors

- movements_for_company
- movement_detail
- stock_balance(company, warehouse, variant)
- balances_for_warehouse
- movement history

## UI

- movement list/create/edit/detail
- receive/issue/transfer forms
- post action
- warehouse balance view
- movement history

## Required correctness tests

In addition to normal tests:

- transaction atomicity
- duplicate post/retry
- rollback after invalid line/failure
- posted immutability
- transfer source/destination arithmetic
- company isolation

## Explicitly not Inventory Phase 2

- reservation/allocation
- lot/serial/batch/expiry
- valuation/costing
- replenishment
- negative-stock configuration/enforcement
- warehouse bins/locations beyond current Warehouse model
- picking/packing/shipping

---

# Batch 2D — Billing

## Ownership

Billing owns generic invoices, payments and payment allocation. It must remain usable independently by Sales and by future verticals.

Phase 2 minimum models:

### Invoice

- UUID id
- company
- company-unique human-readable number
- bill_to_party -> Party
- invoice_date
- due_date optional
- currency
- status: DRAFT / ISSUED / VOID
- notes
- issued_at
- timestamps

### InvoiceLine

- UUID id
- company
- invoice
- description
- quantity
- unit_price
- optional stable source reference metadata
- timestamps

Do not hard-depend InvoiceLine on Catalog.

### Payment

- UUID id
- company
- company-unique human-readable number
- payer Party where appropriate
- payment_date
- currency
- amount
- method: minimal CASH / BANK / OTHER or equivalent
- external_reference optional
- idempotency_key optional with company-scoped uniqueness when supplied
- timestamps

### PaymentAllocation

- UUID id
- company
- payment
- invoice
- amount
- timestamps

## Rules

- bill-to/payer Party must be active and company-scoped; Billing does not require the Party to originate from Sales;
- invoice line quantity > 0;
- unit_price >= 0;
- issued invoice must contain at least one line and becomes immutable for financial fields;
- payment amount > 0;
- allocation currency/company must match;
- total allocations cannot exceed payment amount;
- invoice allocations cannot exceed current invoice outstanding amount;
- allocation operations use row locking/atomicity sufficient to prevent concurrent over-allocation;
- invoice total and outstanding are derived, not arbitrary mutable balances;
- duplicate payment creation with an idempotency key is retry-safe.

## Services

- create/update_invoice draft
- add/update/remove_invoice_line draft
- issue_invoice
- void_invoice only if safe under current rules
- record_payment
- allocate_payment

## Selectors

- invoices_for_company
- invoice_detail
- invoice_total
- amount_paid
- amount_due
- payments_for_company
- unapplied_payment_amount

## UI

- invoice list/create/edit/detail
- issue
- payment list/record
- allocate payment to invoice
- display total/paid/due

## Explicitly not Billing Phase 2

- tax engine
- discount engine
- credit notes
- payment gateway
- automatic dunning
- recurring billing/subscriptions
- foreign-exchange conversion
- vendor AP bills

---

# Batch 2E — Accounting

## Ownership

Accounting owns chart of accounts, journals and balanced journal entries.

Phase 2 minimum models:

### Account

- UUID id
- company
- code unique within company
- name
- type: ASSET / LIABILITY / EQUITY / INCOME / EXPENSE
- is_active
- timestamps

### Journal

- UUID id
- company
- code unique within company
- name
- is_active
- timestamps

### JournalEntry

- UUID id
- company
- company-unique human-readable number
- journal
- entry_date
- memo
- status: DRAFT / POSTED
- optional idempotency key with company-scoped uniqueness when supplied
- posted_at
- timestamps

### JournalEntryLine

- UUID id
- company
- journal_entry
- account
- Party optional
- description
- debit
- credit
- timestamps

## Rules

- all records company-scoped;
- new/posting operations use active Journal/Accounts;
- each line has debit > 0 XOR credit > 0; not both, not neither;
- posting requires at least two lines and total debit == total credit > 0;
- posting is atomic and row-locked;
- retrying same entry post does not duplicate ledger effect;
- external integration idempotency key prevents duplicate JournalEntry creation;
- posted entry and lines are immutable for ledger-significant fields;
- no authoritative mutable account balance field;
- trial balance derives only from POSTED lines;
- Phase 2 journal posting is in Company base currency only.

## Services

- create/update account
- create/update journal
- create/update draft journal entry
- add/update/remove draft line
- post_journal_entry

## Selectors

- accounts_for_company
- journals_for_company
- journal_entries_for_company
- journal_entry_detail
- trial_balance as-of optional date/date range if practical

## UI

- chart of accounts
- journals
- journal entry create/edit/detail
- post action
- trial balance

## Required correctness tests

- balanced posting
- unbalanced rejection without partial effects
- duplicate posting/idempotency
- concurrent/retry behavior where relevant
- posted immutability
- trial balance totals
- company isolation

## Explicitly not Accounting Phase 2

- fiscal year closing
- period locks
- bank reconciliation
- AR/AP aging
- tax/VAT
- fixed assets
- budgeting
- treasury
- FX/revaluation
- consolidation
- payroll posting

---

# Batch 2F — Optional integrations and integration branch

Do not start this batch until standalone module branches have passed architecture review and are merged into `phase2-commercial-core`.

## Procurement -> Inventory

Implement an explicit retry-safe service that converts a posted PurchaseReceipt into a posted Inventory RECEIPT for inventory-tracked ProductVariants.

Requirements:

- both modules enabled;
- do not write Inventory models directly from Procurement;
- call Inventory public service;
- deterministic/idempotent integration key derived from PurchaseReceipt identity;
- retry does not create duplicate StockMovement;
- service Product lines do not create stock movement;
- failure must not corrupt the Procurement receipt.

## Sales -> Billing

Optional Phase 2 integration may create a Billing Invoice from a CONFIRMED SalesOrder.

Requirements:

- both modules enabled;
- no duplicate invoice on retry;
- copy line descriptions/quantity/unit price as snapshots;
- Billing remains independent of Catalog/Sales internally;
- source SalesOrder remains unchanged.

## Billing -> Accounting

Implement explicit posting services for base-currency documents only:

### Invoice posting

Minimum Phase 2 pattern:

```text
Dr Accounts Receivable
Cr Revenue
```

### Payment posting

Minimum Phase 2 pattern:

```text
Dr Cash/Bank
Cr Accounts Receivable
```

The integration may require explicit account IDs or a deliberately small Accounting-owned configuration. Do not build a generic accounting-rule engine.

Requirements:

- Accounting enabled;
- invoice/payment currency equals company base currency;
- call Accounting public services;
- deterministic idempotency key per source document/effect;
- retry cannot duplicate JournalEntry;
- accounting failure does not silently mark an unposted effect as posted.

## Explicitly deferred integration

Do NOT implement Sales confirmation -> Inventory issue in Phase 2.

Inventory should be affected by a future shipment/fulfillment/reservation contract, not merely by order confirmation.

---

# Module registry and navigation

Every new module:

- has a valid manifest;
- registers disabled by default;
- uses `@module_required("<code>")` or equivalent on user-facing views;
- is absent from shared navigation when disabled;
- returns 404 for direct module HTTP access when disabled.

Do not build automatic dependency resolution. Deployment configuration must explicitly enable required hard dependencies.

---

# Document numbers

Every transactional header has a company-scoped unique human-readable number.

Phase 2 may use collision-safe module-local generation. Do not use `MAX()+1` or another concurrency-racy counter.

Do not build a generic configurable sequence engine in Phase 2.

---

# Money and currency

Use Decimal fields with explicit precision appropriate for business transactions.

Sales/Procurement/Billing documents carry Currency.

Do not perform implicit currency conversion.

Accounting Phase 2 is base-currency ledger only.

Do not add tax/pricelist/FX engines.

---

# Company isolation

Every business record with operational ownership must carry explicit company scope where appropriate.

Services/selectors must filter by BusinessContext company and reject cross-company Party/ProductVariant/Warehouse/Account/document composition.

Historical document snapshots do not weaken authoritative ownership checks.

---

# Testing and quality gates

For every standalone module branch:

```bash
pytest
ruff check .
python manage.py check
python manage.py makemigrations --check
```

Also verify:

- fresh PostgreSQL migration bootstrap;
- module-local tests discovered;
- module disabled -> hidden navigation + HTTP 404;
- module enabled -> normal UI flow;
- company isolation;
- representative desktop/mobile UI;
- no reverse imports/circular dependency;
- no forbidden Phase 2 scope expansion.

For Inventory and Accounting additionally verify atomicity, failure rollback and duplicate-posting/idempotency behavior.

For Billing payment allocation verify concurrent/atomic over-allocation prevention.

After Batch 2F, run a complete PostgreSQL suite and end-to-end commercial-core smoke flows.

---

# End-to-end Phase 2 golden flows

By Phase 2 exit, demonstrate:

```text
Customer
-> Sales Order
-> Confirm
```

Optionally when Billing enabled:

```text
Confirmed Sales Order
-> Invoice
-> Payment
```

and when Accounting enabled/base currency:

```text
Invoice/Payment
-> Balanced Journal Entries
-> Trial Balance
```

Procurement:

```text
Supplier
-> Purchase Order
-> Confirm
-> Purchase Receipt
```

and when Inventory enabled:

```text
Purchase Receipt
-> Inventory Receipt
-> Warehouse Balance
```

Direct Inventory:

```text
Receipt
Issue
Transfer
-> derived Warehouse Balance + movement history
```

Accounting standalone:

```text
Journal Entry
-> Post
-> Trial Balance
```

---

# Explicitly forbidden in Phase 2

Do NOT add unless a new architecture decision explicitly changes scope:

- generic workflow/approval engine
- generic event bus
- command bus / DI container
- metadata/studio/dynamic UI engine
- React
- Redis/Celery
- Kafka/NATS
- Go services
- custom Python runtime/framework
- plugin marketplace/installer
- automatic module dependency resolver
- pricing/pricelist engine
- tax engine
- FX engine/revaluation
- inventory costing/valuation
- lot/serial/batch management
- sales shipping/picking/reservation
- advanced accounting close/reconciliation/consolidation
- client-specific hardcoding

---

# Exit criteria

Phase 2 can receive FINAL PASS only when:

1. Sales, Procurement, Inventory, Billing and Accounting each pass standalone architecture review;
2. company isolation is tested for all modules;
3. ProductVariant is used consistently for concrete Sales/Procurement/Inventory item identity;
4. Inventory source of truth is posted movement ledger only;
5. Accounting source of truth is posted balanced journal lines only;
6. Billing totals/outstanding are derived from lines/allocations;
7. posted/confirmed documents are protected against unsafe mutation;
8. Inventory/Accounting authoritative effects are retry-safe/idempotent where applicable;
9. approved optional integrations use public services and do not create hard circular dependencies;
10. module registry gating works for all five modules;
11. PostgreSQL full suite, Ruff, Django checks and migration drift checks pass;
12. no speculative platform framework was introduced;
13. architecture review explicitly accepts the Phase 2 contracts.

Phase 3 must not begin automatically.

## Current canonical gate status

```text
Historical standalone Sales       accepted at a79cb95d031bb38719bcdccfb5b14670cc76cd17
Canonical Gate 4A adoption        accepted, adopted, and closed
Sales adoption checkpoint         e0c848f34da0bce9b9c6e010a396026ac5889cf4
Canonical main                    8d5a41f83c3f796fa31e7d3f8598c54f7dfc5b95
Procurement accepted candidate    1eabb0e9806342cc2ba71f1468eb18af120cddb9
Procurement adoption checkpoint   e4ea1791f0b2c7d1209ea574de3689970e1fc398; closed
Inventory accepted candidate      8b522709; adoption/closure pending; not merged
Billing / Accounting              not authorized
Optional integrations             not authorized
```
