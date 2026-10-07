# Phase 2 — Commercial Core

Status: IN PROGRESS — BILL-1 FORMALLY ACCEPTED FOR CANONICAL ADOPTION / ADOPTION PENDING

Current contract milestone: BILL-0 OPTION A CONTRACT — FORMALLY ACCEPTED, 2026-10-07.
Independent audit FINAL PASS and hosted Phase 0 checks #91 SUCCESS
([run 37579298801](https://github.com/sahinkhan/djangobusinessos/actions/runs/37579298801))
cover exact accepted candidate `24d73be43cc09ef66f4405453a210d8f07fcca7f`.
BILL-0 OPTION A CONTRACT CANONICALLY CLOSED at `b9dd8b185a301dca5b76ec7b6604c42805021174`,
checkpoint `billing-option-a-contract-v1`; main CI #93 SUCCESS (run `37581371586`).
Separately authorized BILL-1 implementation `6f1b5f719fe0848e37774b3247a7bd4300a006a6` is
FORMALLY ACCEPTED FOR CANONICAL ADOPTION after independent FINAL PASS and exact-head hosted
Phase 0 checks #95 / run `37639810038` SUCCESS (873 PostgreSQL tests). Formal acceptance is
COMPLETE; canonical adoption is PENDING and `main` remains at the BILL-0 checkpoint above.
Payments, Accounting, integrations and actual SaaS activation remain unauthorized.
The prior `tenant-db-foundation-v1` and `ui-foundation-v1` checkpoints are preserved.
Earlier acceptance/audit chronology below is preserved as historical evidence.

Canonical Gate 4 base: `f2d48c1d1a6f12c7b27c925e2c6f14f922d53beb`

Historical standalone-plan base: `361d832713dcd2325363b4059a4f3b6cac7d3715`

Architecture decision: `docs/decisions/0006-phase-2-commercial-core-contracts.md`

## Goal

Build the first reusable transactional core of BusinessOS without turning the Django monolith into a tightly coupled ERP.

Phase 2 delivers minimum standalone Sales, Procurement, Inventory, Billing & Invoicing, Payments
and Accounting & Finance capabilities, then separately approved optional integrations after their
standalone contracts pass review. This six-module future scope follows proposed ADR 0011.

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
- `docs/decisions/0011-modular-billing-payments-accounting-boundary.md`
- `docs/decisions/0012-tenant-ready-database-execution-foundation.md`
- this execution plan

Do not silently change these architecture contracts.

---

# Parallelization strategy

The listed branches below record the historical standalone-development strategy. Canonical Gate 4
adoption is sequential and separately authorized: Sales first, then Procurement, then Inventory.
Gate 4A and Gate 4B are accepted, adopted, and closed.
Gate 4C's historical adoption and post-closure correction are accepted, adopted, and closed.
Sales post-closure remediation has independent FINAL PASS, formal corrective acceptance, and
canonical adoption; the post-closure corrective cycle is closed.
BILL-1 was separately authorized and is formally accepted for canonical adoption, which remains
pending. Payments/Accounting implementation and integrations remain unauthorized. Remaining gates
are sequentially governed, not automatically launched in parallel.

Historical branch recommendations (not current implementation authorization):

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

## Gate 4A post-closure corrective status

An independent adversarial audit after the canonical Gate 4A closure returned REVISE for exactly
four narrow findings: persisted historical-line deletion could trust a substituted in-memory
parent; SKU/name snapshot-only refreshes could omit `sales.order.updated`; valid long customer
names and maximum totals could overflow the detail document; and non-finite Decimal values could
escape canonical validation.

Sales-local remediation `f9092cebe2f27504c0f3dfc772524645e25c1f91` starts from canonical
`main` at `cac7817a403be9c84d06d07127f927931ea4a3fc`. It revalidates persisted line ownership after
locking the authoritative aggregate, includes product variant/SKU/name/description/quantity/price
in update-audit comparison, contains the Sales document while retaining local table scrolling,
and rejects NaN and both infinities for quantity and unit price. Local verification passed 437
PostgreSQL tests, 98 Sales PostgreSQL tests, eight focused concurrency/revocation tests, and 341
SQLite tests with 96 expected PostgreSQL-only skips. Real-browser checks passed at 390x844 and
1280x720. No migration, generated CSS, shared module, or integration change was introduced.

The historical Gate 4A acceptance/adoption/closure remains preserved, including closure
`fb9028bbbec5dfc56e7d579c3c351abcde764833` and the later REVISE audit. Final corrective candidate
`b34a98a1f47c7d0c526fa4dbd60207d5123f9fe3` passed exact-head hosted CI
[#74](https://github.com/sahinkhan/djangobusinessos/actions/runs/34961977826) with 437 PostgreSQL
tests and all required checks; independent corrective re-audit returned FINAL PASS. The candidate
was formally accepted at documentation-only checkpoint
`5ccada2bdb8f28bbc031e25aae72a88f7f454e09`, adopted into canonical `main` by normal
fast-forward, and passed exact-head main CI #76
([run 34966070313](https://github.com/sahinkhan/djangobusinessos/actions/runs/34966070313)). Corrective
acceptance and canonical adoption are complete; this documentation closes the cycle. The current
frozen Sales foundation scope is canonically complete. Future Sales extensions remain open and
separately governed.

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
re-audit returned FINAL PASS. Documentation-only acceptance checkpoint
`eb2f52afc53fd8c36249bc6a1e61c15dba9effe8` passed branch CI #61, was adopted into canonical
`main` by normal fast-forward, and passed exact-head main
[CI #62](https://github.com/sahinkhan/djangobusinessos/actions/runs/34931069346). Gate 4C is
accepted, adopted, and closed. Billing, Accounting, Procurement-to-Inventory,
Sales-to-Inventory, and other integrations remain unauthorized. Full Phase 2 is not complete and
production deployment is not approved.

The closure checkpoint `60f879a036e0fd21eada1375fa695f32adc7dc91` remains historical
administrative evidence. A post-closure independent audit later returned REVISE for four P2
correctness findings: company-local `effective_at` render/parse and DST validation, combined
history filters matching different movement lines, incomplete snapshot/UoM audit detection, and
late balance/history HTTP permission checks. Narrow corrective implementation
`343c413bff7f7e520a5a031f92f461a8058db3cc` addressed those findings and was published through
candidate `23a12ae544be2e611ac3fd5bfa90d62299599648`. Independent corrective re-audit returned REVISE
for one residual issue: an unchanged minute-granular movement edit could truncate the existing
seconds and microseconds. Narrow remediation `b33e6faaf931777575292a42af775a1c11986984` preserves the
trusted original aware instant when the submitted company-local minute is unchanged and keeps the
validated normalized value when the minute changes. Candidate head
`d7fc63c2af77e210cdbae8a72837c1497200f251` passed CI #68, but independent re-audit returned REVISE
because generic ambiguity validation ran before trusted-original preservation for persisted DST
fall-back-fold minutes. Final narrow remediation
`145c9d51a3507aa1df8d6548659e16e506940d1e` matches the raw submitted minute against the trusted
persisted instant before generic conversion, while changed/new ambiguous or nonexistent input still
uses normal Django validation. Final corrective candidate
`09794e9293da78117e5873ebbff9f4b98fa5e1b7` passed exact-head CI #69 with 422 PostgreSQL tests, and
independent final corrective re-audit returned FINAL PASS. It has no migration or cross-module
behavior and is formally ACCEPTED at checkpoint
`35663e4f6b4112903838e0a8069f47885c83f7ce`. That checkpoint was adopted into canonical `main` by
normal fast-forward and passed exact-head main CI #71
([run 34957834165](https://github.com/sahinkhan/djangobusinessos/actions/runs/34957834165)). The Gate
4C post-closure corrective cycle is CLOSED; the original historical closure remains preserved.
Sales post-closure audit retains the historical REVISE result. Sales-local remediation
`f9092cebe2f27504c0f3dfc772524645e25c1f91` and final candidate
`b34a98a1f47c7d0c526fa4dbd60207d5123f9fe3` received independent corrective FINAL PASS and formal
acceptance. Acceptance checkpoint `5ccada2bdb8f28bbc031e25aae72a88f7f454e09` was adopted into
canonical `main` and passed exact-head main CI #76. The corrective cycle is closed. Billing,
Accounting, integrations, and production deployment remain unauthorized.

Procurement retains its historical Gate 4B acceptance/adoption/closure. A subsequent independent
post-closure audit returned REVISE for five narrow findings: historical-line parent substitution
on instance delete, noncanonical/duplicate receipt UUID field partial-processing risk, omitted
SKU/name snapshot audit detection, supported-value UI overflow, and non-finite order-line Decimal
validation. Procurement-local remediation `1ccaf0bc74816b11035cb33f24e172ff8f902329` is isolated on
`gate4b-procurement-postclosure-remediation`. Status: IMPLEMENTED / AWAITING INDEPENDENT
PROCUREMENT CORRECTIVE RE-AUDIT. It is not accepted, adopted into `main`, merged, or re-closed.

The first corrective re-audit returned REVISE for a single residual P3: invalid numeric strings on
order-line quantity/cost could escape comparison as uncontrolled `TypeError`. Residual remediation
`c34daec0d3ad876612c15536f8c94148f7f4664c` uses Django DecimalField-compatible normalization
before finite and business comparisons, with public add/update and direct-save rollback tests.
Final candidate `ad03000deeae72a1703f6935dd9d4cde46ede5cc` passed hosted CI #80 at the exact
head. The second independent corrective re-audit returned FINAL PASS, including 493 PostgreSQL
tests, 115 Procurement-local tests, 27 real-lock concurrency tests, SQLite verification, focused
adversarial probes, and desktop/mobile boundary QA. Status: ACCEPTED FOR CONTROLLED ADOPTION.
Documentation-only acceptance checkpoint `49052c0efd3a63ec55c409e0d38082425ce116c3` passed exact-head
branch [CI #81](https://github.com/sahinkhan/djangobusinessos/actions/runs/34992015192), was adopted
into canonical `main` by normal fast-forward, and passed exact-head main
[CI #82](https://github.com/sahinkhan/djangobusinessos/actions/runs/34993306285). Corrective
acceptance and canonical adoption are complete; this documentation closes the Procurement
post-closure corrective cycle. The current frozen Procurement foundation scope is canonically
complete. Future Procurement extensions remain open and separately governed.

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

# Gate BILL-1 — Standalone Billing & Invoicing (replaces combined Batch 2D)

Status: BILL-0 canonically closed. BILL-1 **FORMALLY ACCEPTED FOR CANONICAL ADOPTION**, 2026-10-07.
Accepted implementation candidate `6f1b5f719fe0848e37774b3247a7bd4300a006a6` on
`bill1-billing-invoicing` is directly above `b9dd8b185a301dca5b76ec7b6604c42805021174`,
with subject `feat: implement standalone billing invoicing`. Independent audit is FINAL PASS;
hosted candidate CI #95 / `37639810038` is SUCCESS. Formal acceptance is COMPLETE;
canonical adoption is **PENDING** and requires separate explicit authorization. No BILL-1
checkpoint tag, main adoption, PAY-1 authorization or production-readiness approval is claimed.

### BILL-1 implementation evidence — 2026-10-07

- Invoice/InvoiceLine only; generic Party billing without customer role or Catalog identity.
  Four exact Billing permissions, frozen disabled-by-default registration, enablement preservation,
  HTTP-only gating, alias-aware Company-lock-before-RBAC services and atomic created/updated/issued audit.
- Service-only writes, protected public ORM/bulk paths, immutable issued documents, collision-safe
  UUID numbering, snapshots and frozen currency precision; one pure Decimal calculation helper
  sums exact products and rounds once using HALF_UP. No stored total or payment/balance state.
- Create/edit/detail/line/issue pages use the accepted shell, action RBAC, company-bound POSTs,
  50-row deterministic pagination and explicit “Payment status unavailable”. No Payments,
  Accounting, Inventory effect, Catalog dependency or historical Billing WIP was introduced.
- PostgreSQL 17 / Python 3.13: full suite **873 passed**; Billing-local **104 passed**, including
  **23 real-lock concurrency cases** and a non-default-alias lifecycle/audit/rollback test.
  SQLite full suite **754 passed, 119 PostgreSQL-only skips**. Workers close their connections.
- Fresh disposable PostgreSQL migrations, Django checks, migration drift, database architecture
  guard, Ruff, npm/Tailwind/CSS reproducibility and diff checks passed. Existing npm advisories
  remain outside scope; no dependency/workflow changes.
- Browser QA uses disposable synthetic data: 200-character Party, long descriptions/notes,
  maximum supported line values and eight-decimal totals at 390/768/1280 CSS pixels. Table scrolling
  remains local; page layout stays bounded. Draft actions and issued read-only presentation verified.
- Two new Billing migrations only: `0001_initial`, `0002_register_manifest`; accepted migrations
  unchanged. Existing migration-count regression updated from five to six registered modules.
- Accepted ADR 0011 financial/dependency/lifecycle decisions remain unchanged. This evidence is
  implementation verification, **not independent acceptance**. PAY-1/ACC-1 remain unauthorized.

### BILL-1 independent audit and formal acceptance — 2026-10-07

The local implementation-verification record above remains historical evidence. Independent full
audit subsequently passed implementation correctness. The initial strict preservation audit was
procedurally BLOCKED only by a Codex-generated capture ref. Preservation re-audit under the
clarified authoritative-ref policy returned **FINAL PASS — BILL-1 APPROVED FOR HOSTED CI**;
the accepted candidate tree/content remained unchanged. This chronology is retained, not rewritten.

Hosted **Phase 0 checks #95 — SUCCESS**, run `37639810038`
([run](https://github.com/sahinkhan/djangobusinessos/actions/runs/37639810038)), checked out exact
implementation SHA `6f1b5f719fe0848e37774b3247a7bd4300a006a6` and passed **873 PostgreSQL tests**,
fresh migrations, migration drift, Ruff, Django checks, `npm ci`, Tailwind and CSS reproducibility.
BILL-1 is **FORMALLY ACCEPTED FOR CANONICAL ADOPTION**; acceptance is COMPLETE, adoption PENDING.
No runtime, schema, migration, UI or Option A ownership change accompanies this acceptance record.

Accepted nonblocking P3: at one extreme boundary-length 1280px list row the "Issued" badge may
wrap, without affecting financial correctness, authorization, database integrity, invoice lifecycle
or page-level overflow. Keep it for separately authorized UI maintenance. Existing eight npm
advisories (two moderate, six high) and GitHub Actions runtime warnings remain separate follow-ups.
Canonical `main` remains `b9dd8b185a301dca5b76ec7b6604c42805021174`; no BILL-1 tag is created.
PAY-1 and ACC-1 are NOT STARTED; integrations and actual SaaS activation remain unauthorized.

## Ownership and authoritative specification

Billing owns Invoice/InvoiceLine, invoice identity/numbering, currency and financial snapshots,
issue/finalization, document lifecycle, derived totals and future approved invoice correction
policy. It is reusable across Retail, School, Hospital, Hotel, Services, Ecommerce and other
verticals without Sales, Procurement or Catalog. It owns no Payment/PaymentAllocation/PaymentMethod,
payment receipt, gateway, payment retry key, settlement, reconciliation, refund, journal or stock.

The precise proposed fields, validation, rounding, snapshot, lifecycle, RBAC and audit contract is
[ADR 0011](../../decisions/0011-modular-billing-payments-accounting-boundary.md). That document
is the single detailed BILL-1 specification; the checklist below summarizes its acceptance scope.

## Minimum implementation for separate authorization

- Invoice: explicit company; company-unique stable generated number; active same-company bill-to
  Party (person/organization, no customer-role requirement); bill-to snapshots; invoice/due dates;
  Currency and code/precision snapshots; DRAFT/ISSUED; notes; server issued timestamp; timestamps.
- InvoiceLine: company, immutable parent, generic nonblank description, positive quantity,
  nonnegative unit price, position and timestamps. No required Catalog or upstream order reference.
- Decimal(18,4) inputs, finite-value/range/precision validation before persistence. Exact products,
  sum before once-only ROUND_HALF_UP at frozen currency precision, checked aggregate range.
  ADR 0011 specifies zero-total behavior, supported currency precision and boundary handling.
- Draft edits only; at least one valid line before issue; issued header/lines fully immutable.
  No void state/action, credit notes, issued deletion or reversal; safe correction policy deferred.
- Module-local collision-safe numbering plus database uniqueness, no `MAX()+1` or sequence engine.
- Services: create/update invoice, add/update/remove draft line, issue invoice. Same-invoice issue
  retry has one transition/audit; initial creation has no request-key replay guarantee.
- Reads: company-scoped invoices_for_company, invoice_detail, invoice_total. Deterministic 50-row
  list pagination; list/create/edit/detail/issue UI uses the accepted shell and normal POST actions.

## Amount presentation and future outstanding

Display **Invoice total**, not payment-aware amount due or fully unpaid balance. Payment status is
explicitly unavailable. No amount_paid/amount_due selector or mutable balance exists in BILL-1.
Only later approved composition may derive outstanding from frozen Billing financial state and
complete valid Payments-owned allocations. Missing evidence never means zero paid. A due date is
document information, not proof of unpaid/overdue debt. No fake allocation table in Billing.

## Foundation acceptance requirements

- Hard manifest dependencies: party, organization, reference, access; existing Core utilities allowed.
- Exact proposed permissions: billing.invoice.view/create/update/issue. Action GET forms and POST
  handlers enforce action RBAC; selectors and installed Python services enforce their own permissions.
- Mutation order: business_atomic -> active Company lock -> context/RBAC recheck -> invoice/line
  locks -> validation/write/audit. Reads, mutation and audit use the same execution alias (ADR 0012).
- Audit: billing.invoice.created/updated/issued. All persisted financial/snapshot changes covered;
  no duplicate success event for true no-op/issue retry; audit failure rolls back the entire operation.
- Public bulk ORM and stale-instance paths cannot bypass ownership, status or issued immutability.
- Deterministic frozen manifest/permission registration; preserve existing enablement; fresh module
  disabled. Missing/disabled HTTP returns 404 and hides navigation; installed APIs remain callable
  with valid BusinessContext and RBAC. No tenant_id, SaaS activation or service enablement gate.
- PostgreSQL real-lock regressions: issue versus edit/remove/stale deletes, issue retry, and role/
  permission/company-access revocation after Company-lock wait. SQLite skips only actual lock cases.
- Cross-company relationships, finite/invalid numeric inputs, currency snapshots/rounding, audit
  rollback, non-HTTP calls, HTTP permission/stale-company matrix and absent optional modules tested.
- Fresh migrations, module-local discovery, full suites/checks and responsive boundary-value UI QA.

## Deferred beyond BILL-1

Payment gateways, customer refunds, vendor/AP billing, credit notes/void, recurring invoices,
subscriptions, advanced taxes (no tax calculation in BILL-1), discounts/promotions, FX conversion,
Accounting integration, Sales-to-Billing automation, Ecommerce checkout, settlement/reconciliation,
dunning and localized fiscal numbering require separate approval. No preserved Billing WIP resumes.

---

# Gate PAY-1 — Standalone Payments

Status: ownership boundary proposed; detailed contract and implementation separately authorized.

Payments owns Payment/Receipt, PaymentMethod, PaymentAllocation, partial payments, payment
idempotency, allocation validation and settlement; refunds/reversals only when separately approved.
Procurement PurchaseReceipt remains unrelated goods/service receipt evidence.

Generic Payments hard dependencies: party, organization, reference, access plus existing Core
utilities. It must record standalone receipts with Billing absent. Proposed PAY-1 design covers
company-scoped receipts, payer Party, dates, currency, finite positive amounts, methods, numbering,
external references/retry keys, permissions/audit and derived unapplied amounts. Concrete schema,
receipt/settlement lifecycle and APIs require PAY-1 contract review before implementation.

Invoice allocation is optional composition with Billing, not a hard dependency of generic Payments.
Payments owns the allocation facts and writes; composition validates eligible Billing invoices
through public contracts. No unconditional Invoice FK or eager Billing import in generic Payments
models/migrations/startup. Optional linkage/storage, lock protocol and complete applied-amount
evidence must be explicitly designed before enabling allocations. Billing never imports Payments.

Allocation requires company/currency/identity agreement, no excess over payment availability or
invoice outstanding, concurrent lock/recheck protection, exact retry/idempotency, rollback and audit.
Those are acceptance requirements for the future optional integration, not present functionality.
Payment receipt processing must not automatically create an invoice or Accounting journal.

Gate PAY-1 requires independent standalone review; invoice-allocation integration requires its own
review/authorization. Gateway, refund/reversal and settlement processing are not implicitly approved.

---

# Gate ACC-1 — Accounting & Finance Core (formerly Batch 2E)

Status: future standalone gate, not implementation authorization. The following accepted journal
scope is preserved. Accounting depends on Party and Core, not Billing or Payments; automation
consumes separately approved source outcomes through optional composition and public services.

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

# Optional integrations — separately governed after standalone gates (formerly Batch 2F)

Do not start until the relevant standalone modules pass independent review and canonical adoption,
and the specific integration is explicitly authorized. The historical `phase2-commercial-core`
branch proposal is not an instruction to merge preserved branches or start integrations now.

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

## Payments + Billing invoice allocation

Separately approve optional composition consuming Billing invoice eligibility/financial snapshots
and Payments allocation services. PaymentAllocation remains Payments-owned. Validate company,
currency, invoice and payment identities; derive outstanding from complete valid allocation
evidence; serialize against competing allocations and any future invoice correction. Missing
evidence must fail or report unavailable. PAY-1/integration review must resolve optional storage
without making generic Payments require Billing. No direct cross-module authoritative writes.

## Billing / Payments outcomes -> Accounting

Implement explicit posting services for base-currency documents only:

### Billing invoice outcome posting

Minimum Phase 2 pattern:

```text
Dr Accounts Receivable
Cr Revenue
```

### Payments allocated-receipt outcome posting

Minimum Phase 2 pattern:

```text
Dr Cash/Bank
Cr Accounts Receivable
```

The integration may require explicit account IDs or a deliberately small Accounting-owned configuration. Do not build a generic accounting-rule engine.

The payment example applies to an approved receivable allocation, not every standalone receipt.
Unallocated receipts and settlement/refund mappings require their own explicit accounting policy.

Requirements:

- Accounting enabled;
- the relevant Billing or Payments capability and its specific integration enabled;
- invoice/payment currency equals company base currency;
- Billing supplies invoice outcomes; Payments supplies payment/allocation outcomes;
- Accounting owns all journal/GL writes; no payment posting service belongs to Billing;
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

Registry enablement controls HTTP/navigation only; installed Python services still require valid
BusinessContext and exact RBAC but remain callable with missing/disabled module registry state.
Deterministic registration preserves existing enablement and freezes migration-time declarations.

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

For BILL-1 verify the ADR 0011 invoice financial/snapshot/issue/immutability/RBAC/audit contract.
For Payments invoice allocation verify concurrent/atomic over-allocation prevention, retry safety
and complete settlement evidence through the approved optional integration. Never substitute
standalone invoice total for payment-aware outstanding.

After the separately approved integration gate, run the full PostgreSQL suite and relevant
end-to-end commercial-core smoke flows.

---

# End-to-end Phase 2 golden flows

By Phase 2 exit, demonstrate:

```text
Customer
-> Sales Order
-> Confirm
```

Optionally when Billing and Sales-to-Billing integration are approved and enabled:

```text
Confirmed Sales Order
-> Invoice
```

Then, only when Payments and invoice allocation are approved/enabled:

```text
Issued Billing Invoice + Payments Receipt
-> Payments-owned Allocation
-> settlement-adjusted outstanding through approved composition
```

and when Accounting enabled/base currency:

```text
Billing invoice / Payments allocation outcomes
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

1. Sales, Procurement, Inventory, Billing, Payments and Accounting each pass standalone architecture review;
2. company isolation is tested for all modules;
3. ProductVariant is used consistently for concrete Sales/Procurement/Inventory item identity;
4. Inventory source of truth is posted movement ledger only;
5. Accounting source of truth is posted balanced journal lines only;
6. Billing totals derive from frozen invoice financial data; settlement-adjusted outstanding derives
   only through approved composition with valid Payments-owned allocations, never a mutable balance;
7. posted/confirmed documents are protected against unsafe mutation;
8. Inventory/Accounting authoritative effects are retry-safe/idempotent where applicable;
9. approved optional integrations use public services and do not create hard circular dependencies;
10. module registry gating works for all six modules, preserving installed service RBAC semantics;
11. PostgreSQL full suite, Ruff, Django checks and migration drift checks pass;
12. no speculative platform framework was introduced;
13. architecture review explicitly accepts the Phase 2 contracts.

Phase 3 must not begin automatically.

## Current canonical gate status

```text
Historical standalone Sales       accepted at a79cb95d031bb38719bcdccfb5b14670cc76cd17
Canonical Gate 4A adoption        accepted, adopted, and closed
Sales adoption checkpoint         e0c848f34da0bce9b9c6e010a396026ac5889cf4
Canonical corrective adoption     35663e4f6b4112903838e0a8069f47885c83f7ce
Procurement accepted candidate    1eabb0e9806342cc2ba71f1468eb18af120cddb9
Procurement adoption checkpoint   e4ea1791f0b2c7d1209ea574de3689970e1fc398; closed
Procurement post-closure remediation 1ccaf0bc; first corrective re-audit REVISE
Procurement residual P3 remediation c34daec0; final candidate ad03000; FINAL PASS
Procurement corrective adoption      49052c0e; accepted / adopted / closed
Inventory accepted candidate      8b522709; historical FINAL PASS
Inventory adoption checkpoint     60f879a0; historically accepted, adopted, and closed
Inventory corrective candidate     23a12ae; independent corrective re-audit REVISE
Inventory precision candidate      d7fc63c; independent corrective re-audit REVISE
Inventory final corrective         09794e92; FINAL PASS
Inventory corrective adoption      35663e4f; accepted, adopted, and closed
Sales post-closure remediation      b34a98a1; FINAL PASS / accepted / adopted / closed
Gate TDB-1 foundation              canonically closed at d65eeee; tenant-db-foundation-v1
Billing Option A contract         BILL-0 canonically closed at b9dd8b18
Gate BILL-1 implementation         6f1b5f71; independent FINAL PASS; CI #95 SUCCESS (873 passed)
Gate BILL-1 formal acceptance      COMPLETE / FORMALLY ACCEPTED FOR CANONICAL ADOPTION
Gate BILL-1 canonical adoption     PENDING; no main adoption or BILL-1 checkpoint tag
Gate PAY-1 implementation          NOT STARTED / not authorized
Gate ACC-1 implementation          NOT STARTED / not authorized
Optional integrations             not authorized
```
