# Phase 2 — Commercial Core

Status: FORMAL PHASE 2 CLOSURE COMPLETE FOR CANONICAL ADOPTION — CANONICAL ADOPTION PENDING

Current checkpoint — 2026-10-14: supplied combined independent **FINAL PASS / Readiness A**,
**13 PASS / 0 FAIL / 0 NOT PROVEN**, against corrective candidate
`4a2a7ecaa26e1e312a482e405cd763efdc5f2d74`; exact-head candidate hosted CI #131 SUCCESS,
3,015 PostgreSQL tests and mandatory gates PASS. All six findings, including PH2-FINAL-DOC-1
normalized by this documentation-only closure, are RESOLVED. See the
[formal closure record](#phase-2-formal-closure-for-canonical-adoption--2026-10-14).

Canonical `main` remains `669936df432ec1bb12792ed8d31741fbb1b1287a`, the **ACC-INT-1
CANONICALLY CLOSED** checkpoint with main CI #130 attempt 2 SUCCESS. This Phase 2 closure
requires its own branch CI and later separately authorized direct fast-forward/main CI;
**Phase 2 is not yet canonically closed**. No Phase 3, SaaS activation or production approval.

## Historical milestone chronology

The acceptance/remediation records below preserve their original evidence, failures, baseline
SHAs and pending/not-started states. They are not current gate declarations; the current status
above and final closure section supersede them without rewriting accepted technical contracts.

Historical canonical starting baseline for ACC-INT-1 acceptance: `4419bdc4f0210894065400923741dd5449ffd158`.
**ACC-INT-0 CANONICALLY CLOSED.** The following PAY-INT-1 and ACC-INT-0 acceptance-stage
records retain their historical baselines and completion rules.
**PAY-INT-1 CANONICALLY CLOSED** after acceptance CI #119 / `38163571737` and main
CI #120 / `38164395135` SUCCESS at that exact SHA; implementation CI #118 / `38162359131`
SUCCESS tested corrective `bef50fe8b20f97aaeefb8c610a46d412e9a05402`.
All three hosted runs passed **1,613 PostgreSQL tests** and mandatory checks.
Original `4b8a072da4426a48988d4605641bf1fc846c06ee` / REVISE / readiness C is preserved;
corrective independent FINAL PASS / readiness A resolved PAYINT1-R1/R2/R3/R4. See
[canonical closure](#pay-int-1-post-adoption-canonical-closure--2026-10-12).

Historical bounded task: **ACC-INT-0 formal acceptance and controlled canonical adoption**,
documentation only. Supplied independent FINAL PASS / readiness A approved exact proposal
`207c78096f419b4d924326df256355a356a3f3d7`; hosted candidate CI #125 / `38203841663` SUCCESS
tested that exact SHA (**1,613 PostgreSQL tests**, fresh migrations and mandatory checks).
**Formal acceptance COMPLETE; canonical adoption PENDING at this acceptance checkpoint.**
Accepted
[ADR 0016](../../decisions/0016-accounting-commercial-outcomes-integration-contract.md).
Contract branch `accint0-accounting-outcomes-contract` starts from the exact canonical baseline.
The authorized remaining sequence is exact-head acceptance CI, unchanged-main/ancestry
revalidation, direct fast-forward normal push and separate exact-head main CI; no runtime.
See [formal acceptance and completion rule](#acc-int-0-independent-approval-and-formal-acceptance--2026-10-12).
Historical bounded task: explicitly authorized **ACC-INT-1 corrective publication, docs-only formal
implementation acceptance and direct fast-forward canonical adoption** on `accint1-accounting-outcomes`,
from canonical base `4419bdc4f0210894065400923741dd5449ffd158`.
**FORMALLY ACCEPTED FOR CANONICAL ADOPTION; formal acceptance COMPLETE; adoption PENDING
at this acceptance checkpoint.** Corrective candidate `2c7c8109f875909b34cc089698cb6d7dde572266`
received the supplied independent **FINAL PASS / Readiness A**; **ACCINT1-AUD-1 RESOLVED**.
Hosted candidate CI **#128 / 38365702656 SUCCESS** tested that exact SHA: **2,755 PostgreSQL
tests passed**, fresh migrations and all configured mandatory checks passed.
The implementation preserves accepted ADR 0016: two Accounting-owned opt-in apps, owner read
contracts, immutable source/effect bindings, explicit public-service composition and bounded UI.
Original implementation `5bfc055b1fb6c2b806a4f4bbf04fc749cc9020fe` received independent
**REVISE — Readiness B**, with candidate-owned **ACCINT1-AUD-1 — P2**. That failure and local
corrective verification remain historical implementation evidence, distinct from the supplied
independent corrective review and verified hosted candidate CI. See the
[formal acceptance and completion rule](#acc-int-1-independent-corrective-approval-and-formal-implementation-acceptance--2026-10-13).
**PHASE 2 NOT COMPLETE; final completion audit NOT YET PERFORMED; PHASE 3 NOT AUTHORIZED.**
SaaS activation and deployment remain unauthorized. No PAY-INT-1 tag is invented.

Historical PAY-INT-1 implementation/acceptance-stage baseline:
`9ee4e0bd77350ddeef1e928e2a73b676b4cbb1ee`.
PAY-INT-0 acceptance CI #116 / `38134694017` and main CI #117 / `38135373053` both succeeded
against that exact SHA (1,313 PostgreSQL tests each), satisfying the historical completion rule.
PAY-INT-1 is **FORMALLY ACCEPTED FOR CANONICAL ADOPTION** on
`payint1-billing-payments-allocation`: corrective candidate
`bef50fe8b20f97aaeefb8c610a46d412e9a05402`, independent FINAL PASS / readiness A, exact-head
implementation CI #118 / `38162359131` SUCCESS (**1,613 PostgreSQL tests**).
**Formal acceptance: COMPLETE. Canonical adoption: PENDING at this acceptance checkpoint.**
This docs-only acceptance commit becomes the canonical freeze only after its own exact-head
branch CI, normal fast-forward adoption and separate exact-head main CI succeed. See the
[acceptance record and completion rule](#pay-int-1-independent-corrective-approval-and-formal-acceptance--2026-10-12),
[historical original implementation](#pay-int-1-local-implementation-and-verification--2026-10-11)
and [historical corrective evidence](#pay-int-1-local-corrective-remediation--2026-10-11).
The PAY-INT-0 acceptance-stage pending/not-authorized wording below is retained as historical
checkpoint evidence, not a contradiction of this later bounded implementation authorization.
Accounting automation, other integrations, SaaS activation and deployment remain unauthorized.

Canonical starting baseline / ACC-1 freeze: `00e18a75e27bfe962ea290ab01f0cb0520f4427e`.
**ACC-1 STANDALONE ACCOUNTING — CANONICALLY CLOSED**, 2026-10-11, following independent
**PASS — ACC-1 IMPLEMENTATION APPROVED FOR PUBLICATION**, candidate push CI #112 /
`38127289623` SUCCESS and exact-head main CI #114 / `38127960676` SUCCESS (**1,313 PostgreSQL
tests**, fresh migrations and all mandatory checks). ACC1-R1 substantive finding and ACC1-R2 P3
formatting finding are **RESOLVED**. PR #1 was closed without merging; adoption used the established
normal fast-forward flow. No `accounting-v1` tag has been created. The original REVISE, remediation
and verification chronology below remains historical evidence, not current pending status.

Historical acceptance-stage contract milestone: **PAY-INT-0 — Billing/Payments Allocation Integration
Contract**, documentation only, on `payint0-billing-payments-contract`.
[ADR 0015](../../decisions/0015-billing-payments-allocation-integration-contract.md) is
**Accepted — Gate PAY-INT-0**; audited proposal
`9d4fa5d3b7a12d4eb0ee2046d6e4ff306957e228` remains intact. Owner-supplied independent
**FINAL PASS — PAY-INT-0 CONTRACT APPROVED FOR FORMAL ACCEPTANCE**, readiness **A**, no actionable
candidate-owned P0–P3, and exact-head candidate CI **#115 / 38133793295 SUCCESS**
(**1,313 PostgreSQL tests**, fresh migrations and all mandatory checks) support formal acceptance.
**Acceptance: COMPLETE. Canonical adoption: PENDING at this acceptance checkpoint.** This same
acceptance metadata commit becomes **PAY-INT-0 CANONICALLY CLOSED / canonical freeze** only after
its own exact-head branch CI, normal fast-forward adoption and separate exact-head main CI all
succeed; the pending statement is then historical checkpoint evidence, not a new pending gate.
No future run ID/result or runtime capability is claimed. No exact PAY-INT-0 tag is specified.
PAY-INT-1 and Accounting integrations are **NOT STARTED / NOT AUTHORIZED**. No actual SaaS
activation, production Accounting readiness, deployment or full Phase 2 completion is claimed.

Historical ACC-0 formal acceptance-stage evidence (retained): documentation/architecture only, on
`acc0-accounting-contract` from `9ac3f0944fff65f013efd9c3a3e9b841022ce87f`. ADR 0014 is
Accepted — Gate ACC-0 at contract head `217b7a8f39b628571f616034a7d9d02b436ec03d`, after
corrective independent FINAL PASS, readiness A, and exact-head remediation CI #108 SUCCESS.
Formal acceptance is COMPLETE; canonical adoption is PENDING. This acceptance commit needs its
own exact-head CI. Main adoption, tagging, ACC-1 and integrations are not authorized;
production Accounting readiness is not claimed.

Historical BILL-0/BILL-1/PAY-0/PAY-1 contract/adoption chronology (retained):
BILL-0 OPTION A CONTRACT — FORMALLY ACCEPTED, 2026-10-07.
Independent audit FINAL PASS and hosted Phase 0 checks #91 SUCCESS
([run 37579298801](https://github.com/sahinkhan/djangobusinessos/actions/runs/37579298801))
cover exact accepted candidate `24d73be43cc09ef66f4405453a210d8f07fcca7f`.
BILL-0 OPTION A CONTRACT CANONICALLY CLOSED at `b9dd8b185a301dca5b76ec7b6604c42805021174`,
checkpoint `billing-option-a-contract-v1`; main CI #93 SUCCESS (run `37581371586`).
Separately authorized BILL-1 implementation `6f1b5f719fe0848e37774b3247a7bd4300a006a6` is
CANONICALLY CLOSED after independent FINAL PASS and exact-head hosted Phase 0 checks #95 /
run `37639810038` SUCCESS (873 PostgreSQL tests). Formal acceptance/adoption checkpoint
`409e45eaa32fae1cf9c77042a762e57026d0349f` was adopted by normal fast-forward and passed
main CI #97 / `37645584246` SUCCESS, with 873 PostgreSQL tests
and fresh migrations/all mandatory checks. Checkpoint `billing-invoicing-v1` resolves to that SHA.
Gate PAY-0 is **FORMALLY ACCEPTED**, 2026-10-07, as documentation/architecture only, on
`pay0-payments-contract` from that canonical main. ADR 0013 is **Accepted — Gate PAY-0**.
Accepted candidate `9ffb5eae09da680354776872a601bedd58163ab1` has independent FINAL PASS and
exact-head Phase 0 checks #99 / `37656399267` SUCCESS (873 PostgreSQL tests and all mandatory checks).
Formal acceptance and canonical adoption are COMPLETE at
`d12f3e8c3a955dd90f1e03f35a30fde789441764`, checkpoint `payments-contract-v1`;
exact-head main CI #101 / `37662202308` SUCCESS, 873 PostgreSQL tests.
Separately authorized PAY-1 implementation `86e15f9f0aea29a07694c251d511e4b60fc6d2ad` on
`pay1-payments` has independent FINAL PASS and exact-head hosted implementation CI #103 /
`38076354718` SUCCESS (1,009 PostgreSQL tests and all mandatory checks).
PAY-1 formal acceptance was COMPLETE, 2026-10-11, with adoption pending at that historical stage.
Subsequent separately authorized acceptance/adoption checkpoint
`9ac3f0944fff65f013efd9c3a3e9b841022ce87f` passed acceptance CI #104 / `38077428416`, was adopted
by normal fast-forward and passed exact-head main CI #105 / `38078381136` SUCCESS (1,009 PostgreSQL
tests, fresh migrations and all mandatory checks). PAY-1 STANDALONE PAYMENTS is CANONICALLY CLOSED,
checkpoint `payments-v1`. At that historical PAY-1 closure, ACC-1 was not started; it is now
canonically closed as recorded above. At that historical checkpoint PAY-INT-1 was unauthorized;
its later local-only authority is recorded at the top and in the implementation record. All other
integrations and actual SaaS activation remain unauthorized.
The prior `tenant-db-foundation-v1` and `ui-foundation-v1` checkpoints are preserved.
Earlier acceptance/audit chronology below is preserved as historical evidence.

Canonical Gate 4 base: `f2d48c1d1a6f12c7b27c925e2c6f14f922d53beb`

Historical standalone-plan base: `361d832713dcd2325363b4059a4f3b6cac7d3715`

Architecture decision: `docs/decisions/0006-phase-2-commercial-core-contracts.md`

## Goal

Build the first reusable transactional core of BusinessOS without turning the Django monolith into a tightly coupled ERP.

Phase 2 delivers minimum standalone Sales, Procurement, Inventory, Billing & Invoicing, Payments
and Accounting & Finance capabilities, then separately approved optional integrations after their
standalone contracts pass review. This six-module future scope follows accepted ADR 0011;
accepted ADR 0013 refines standalone incoming Payments without implementing it.

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
- `docs/decisions/0013-standalone-payments-contract.md` (Accepted — Gate PAY-0; canonically closed)
- `docs/decisions/0014-standalone-accounting-finance-contract.md` (Accepted — Gate ACC-0; canonically adopted contract, not automatic implementation authority)
- `docs/decisions/0015-billing-payments-allocation-integration-contract.md` (Accepted — Gate PAY-INT-0; documentation contract only, not implementation authority)
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
BILL-1 was separately authorized and is canonically closed at `409e45e...` (`billing-invoicing-v1`).
PAY-0 is documentation-only; PAY-1 implementation is canonically closed at `9ac3f094` (`payments-v1`).
ACC-0 is canonically adopted contract documentation; separately authorized ACC-1 is now canonically
closed at `00e18a75...`, with its original REVISE and resolved remediation history retained.
PAY-INT-0 and PAY-INT-1 are canonically closed. PAY-INT-1 corrective implementation has independent
FINAL PASS, successful hosted implementation/acceptance/main CI and completed normal fast-forward
adoption. Its earlier acceptance-stage completion rule remains historical below. ACC-INT-0 now
authorizes formal documentation acceptance, verified publication and controlled adoption only,
not Accounting integration runtime.
Remaining gates are sequentially
governed, not automatically launched in parallel.

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

Status: BILL-0 canonically closed. BILL-1 **CANONICALLY CLOSED**, 2026-10-07.
Accepted implementation candidate `6f1b5f719fe0848e37774b3247a7bd4300a006a6` on
`bill1-billing-invoicing` is directly above `b9dd8b185a301dca5b76ec7b6604c42805021174`,
with subject `feat: implement standalone billing invoicing`. Independent audit is FINAL PASS;
hosted candidate CI #95 / `37639810038` is SUCCESS. Formal acceptance and authorized canonical
adoption are COMPLETE at `409e45eaa32fae1cf9c77042a762e57026d0349f`, checkpoint
`billing-invoicing-v1`; exact-head main CI #97 / `37645584246` SUCCESS. PAY-1 authorization
and production-readiness approval are not claimed. The original implementation/audit chronology
below remains historical evidence.

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
At that acceptance stage BILL-1 was **FORMALLY ACCEPTED FOR CANONICAL ADOPTION**;
acceptance was COMPLETE, adoption PENDING. The subsequent adoption is recorded below.
No runtime, schema, migration, UI or Option A ownership change accompanies this acceptance record.

Accepted nonblocking P3: at one extreme boundary-length 1280px list row the "Issued" badge may
wrap, without affecting financial correctness, authorization, database integrity, invoice lifecycle
or page-level overflow. Keep it for separately authorized UI maintenance. Existing eight npm
advisories (two moderate, six high) and GitHub Actions runtime warnings remain separate follow-ups.
At that historical acceptance stage canonical `main` remained
`b9dd8b185a301dca5b76ec7b6604c42805021174`; no BILL-1 tag had yet been created.
PAY-1 and ACC-1 are NOT STARTED; integrations and actual SaaS activation remain unauthorized.

### BILL-1 canonical adoption and closure — 2026-10-07

Formal acceptance commit `409e45eaa32fae1cf9c77042a762e57026d0349f` received separately
authorized normal fast-forward adoption into `main`, which passed
exact-head **Phase 0 checks #97 — SUCCESS**
([run 37645584246](https://github.com/sahinkhan/djangobusinessos/actions/runs/37645584246)).
Main CI checked out that exact SHA and passed fresh PostgreSQL migrations, **873 tests**, Ruff,
Django checks, migration drift and mandatory npm/Tailwind/CSS checks. Annotated
`billing-invoicing-v1` resolves to the accepted/adopted SHA. BILL-1 is canonically closed, not a
local candidate or pending adoption. Earlier procedural/audit records and accepted semantics are
unchanged. The PAY-0 contract is documentation only and not production-readiness approval.

## Ownership and authoritative specification

Billing owns Invoice/InvoiceLine, invoice identity/numbering, currency and financial snapshots,
issue/finalization, document lifecycle, derived totals and future approved invoice correction
policy. It is reusable across Retail, School, Hospital, Hotel, Services, Ecommerce and other
verticals without Sales, Procurement or Catalog. It owns no Payment/PaymentAllocation/PaymentMethod,
payment receipt, gateway, payment retry key, settlement, reconciliation, refund, journal or stock.

The precise accepted fields, validation, rounding, snapshot, lifecycle, RBAC and audit contract is
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

# Gate PAY-0 — Standalone Payments Contract Freeze

Status: **FORMALLY ACCEPTED — Gate PAY-0**, 2026-10-07. Documentation-only
branch `pay0-payments-contract`, directly from canonical main
`409e45eaa32fae1cf9c77042a762e57026d0349f`.
Accepted contract candidate: `9ffb5eae09da680354776872a601bedd58163ab1`.
Independent verdict: **FINAL PASS — PAY-0 CONTRACT APPROVED**.
Implementation readiness: **A — precise enough for PAY-1 implementation**.
Hosted candidate **Phase 0 checks #99 — SUCCESS**, run ID `37656399267`
([run evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/37656399267)),
checked out that exact candidate and passed fresh PostgreSQL migrations, **873 tests**, Ruff,
Django checks, migration drift and mandatory npm/Tailwind/CSS reproducibility.
Formal acceptance and canonical adoption are **COMPLETE** at `d12f3e8c3a955dd90f1e03f35a30fde789441764`.
Checkpoint `payments-contract-v1`, main CI #101 / `37662202308` SUCCESS (873 PostgreSQL tests).
PAY-1 now has separate local implementation authorization; ACC-1 and integrations remain unauthorized.

The authoritative accepted specification is
[ADR 0013 — Standalone Payments and Receipt Contract](../../decisions/0013-standalone-payments-contract.md).
It refines accepted ADR 0011 without changing Billing/Payments/Accounting ownership. The original
PAY-0 candidate froze precise dependency, receipt, amount, normalization/retry, RBAC/audit, locking,
immutability and future-verification rules in one documentation commit, reconciling BILL-1 without
rewriting history. Its initial proposed/pending-review status is retained in candidate history;
subsequent independent audit, candidate publication/CI and separately authorized formal acceptance
completed contract review. Subsequent separately authorized adoption closed PAY-0;
the subsequent PAY-1 independent audit and formal acceptance are recorded below, while canonical
PAY-1 adoption remains pending.

Inherited nonblocking P3: checkpoint-era ADR 0011/Billing authorization wording in ADR 0006 and
`CORE_FOUNDATION_V1_RESTRUCTURE.md` remains a documentation-maintenance follow-up. Those files are
unchanged by this milestone; the follow-up does not alter PAY-0 semantics.

## PAY-1 — standalone incoming receipt recording (formally accepted; adoption pending)

Payments owns receipts/methods/numbering/amount/snapshots/idempotency and future allocations,
settlement and refund/reversal semantics. **Ownership is not PAY-1 implementation scope**.
The approved future PAY-1 MVP implements only PaymentMethod plus immutable incoming Payment/Receipt;
existence means a recorded receipt, with no status machine or edit/delete path. Procurement
PurchaseReceipt remains unrelated. PAY-1 must work with Billing and Accounting absent.

- Dependencies exactly `party, organization, reference, access` plus approved Core utilities.
  No Invoice FK/import, Billing startup/migration dependency or service/selector call; no Catalog,
  Sales, Procurement, Inventory or Accounting dependency/effect.
- PaymentMethod: UUID, explicit immutable company/code, company/code uniqueness, name, activity,
  timestamps. Authorized service-only name/activity administration; deactivate, no hard-delete API.
  Inactive methods cannot record NEW receipts; frozen code/name keeps historical receipts valid.
- Payment: UUID, explicit company, company-unique immutable UUID-derived PAY number, payer,
  frozen payer names, payment_date, Currency plus frozen code/precision, amount, method plus frozen
  code/name, optional reference/key/notes, recorded_at and timestamps. No status, invoice, balance,
  allocation, journal, stock or tenant fields. Active same-company PERSON/ORGANIZATION payer needs
  no customer role; active Core Currency may differ from Company.base_currency without FX.
- Exact positive finite Decimal(38,8), less than `10^30`, exactly representable at frozen currency
  precision 0..8. Decimal/integer/numeric strings only; no bool/float/nonfinite/malformed input,
  rounding or range/scale truncation. Redundant fractional zeros are representation only.
- Optional normalized company-unique key: same canonical payer/date/currency/amount/method/
  reference/notes returns the authorized original receipt, without snapshot/time/audit refresh;
  different payload conflicts. Omitted-date retry uses the original date across midnight.
  New receipts default date via company_local_date; server recorded_at is aware UTC.
- Permissions exactly `payments.method.view/manage`, `payments.payment.view/record`.
  Audit exactly `payments.method.created/updated`, `payments.payment.recorded`; real changes only,
  one audit per first receipt, rollback on audit failure. No receipt update/delete permission/API.
- Services: create_payment_method, update_payment_method, set_payment_method_active, record_payment.
  Reads: payment_methods_for_company, payments_for_company, payment_detail. All context/scoped/RBAC;
  mutation GET/POST surfaces enforce action grants independently of read grants.
- ADR 0012 transaction -> active Company lock -> authoritative context/RBAC recheck -> receipt/
  method/Party/Currency locks -> validation/write/audit, on one alias. Protect supported public ORM
  save/delete/bulk/upsert/update_or_create and stale-instance paths; no arbitrary raw-SQL guarantee.
- Manifest payments / Payments / 0.1.0, fresh disabled, existing enablement preserved, migration-local
  declarations. Missing/disabled HTTP/navigation unavailable; installed services remain callable
  with valid context/RBAC. No SaaS activation or service-level module-enabled authorization.
- UI limited to method administration and receipt list/record/detail in the accepted shell,
  deterministic 50-row backend pagination, safe GET swaps/fallback and normal company-bound POSTs.
  Responsive boundary QA at 390/768/1280px; no global redesign or financial integration screens.

### PAY-1 local implementation evidence — 2026-10-08

Branch: `pay1-payments`, directly from canonical
`d12f3e8c3a955dd90f1e03f35a30fde789441764`. Status at that local checkpoint:
**LOCAL IMPLEMENTATION CANDIDATE, AWAITING INDEPENDENT PAY-1 AUDIT**.
No publication, canonical adoption, tag, Accounting or
integration authorization is implied. ADR 0013 remains Accepted with its financial semantics
unchanged. No historical Payments WIP was restored.

Implementation:

- New `businessos/modules/payments/` contains the exact two models, manifest, framework-neutral
  amount/input normalization, company/RBAC services and selectors, presentation, and local tests.
- `0001_initial` adds only PaymentMethod/Payment with protected references, positive/range/precision
  checks and company-scoped method code, receipt number and non-null retry-key uniqueness.
  `0002_register_manifest` freezes the four permission identities locally, uses the migration
  connection alias, leaves fresh registration disabled and preserves existing enablement.
- Public instance and queryset write/delete/bulk/upsert paths reject, including asynchronous
  wrappers. Private token-controlled insertion/method administration is invoked by the authorized
  services only. No Payment edit, deletion, status, allocation or correction escape hatch exists.
- Recording serializes at the active Company before current context/RBAC recheck. A matching
  locked retry is recovered before NEW-reference eligibility, using frozen precision and date.
  New recording locks method, payer, then currency and snapshots their facts. Exact Decimal tuple
  normalization removes redundant zeros without ambient-context rounding. Three bounded receipt
  number attempts use nested alias savepoints; only identified number-constraint collisions
  regenerate a number. Other integrity failures propagate; keyed collisions recover or conflict.
- Mutation and audit share one transaction/alias. Retry and method no-op produce no duplicate
  success audit. Audit failure rolls back method creation/name/activity and receipt insertion.
- Payments-local UI uses the accepted shell. Navigation/dashboard/header/path matching only adds
  Payments; no shared security behavior or existing commercial production module was changed.
  Normal POSTs remain company-bound, with action-specific GET/POST RBAC. Lists use deterministic
  ordering and server-side 50-row pages. Receipts display frozen facts without allocation language.

Regression evidence includes exact numeric/date/UUID normalization, all receipt retry fields,
omitted-date midnight recovery, reference retirement/rename and precision change, invalid amounts,
38-digit PostgreSQL persistence, number collision/exhaustion, audit rollback, synchronous/asynchronous
ORM protection, cross-company relationship/selectors/deep-link checks, and actual A-to-B session
switches for recording and every method mutation. An isolated subprocess migrates and records a
receipt with Party/Payments as the only business modules: Billing, Accounting, Sales, Procurement,
Catalog and Inventory are absent. Another test migrates a separate real PostgreSQL alias, forbids
all default-connection access, and checks method lifecycle, receipt retry, audit rollback, locks
and savepoints on the selected alias (portable SQLite equivalent also runs).

The separate PostgreSQL concurrency suite has **22 passed** on Python **3.13.16**:
same-key matching/conflicting requests; method rename/deactivation versus recording in both
orders; same-code creation; and role/permission/company-access revocation across method creation,
rename, activity change, recording and matching retry. Coordination checks `pg_blocking_pids`,
not timing guesses; workers close their connections. SQLite explicitly skips these lock tests.

Real-browser QA used only synthetic data in a disposable local PostgreSQL database. Receipt
list/detail/entry and method list/edit were checked at **390 / 768 / 1280 px**; no page-level
horizontal overflow or out-of-viewport inputs were measured. Boundary receipt used a 199-character
unbroken payer, 128-character reference, long notes and the exact maximum numeric(38,8) amount.
Table scrolling stays local. Method creation/rename/deactivation and invalid `NaN` then valid
redundant-zero receipt POSTs succeeded as expected; immutable detail retained original method
facts. Browser GET search/filter swaps, Back/Forward, refresh/deep-link and 50/2-row pagination
with preserved `q` were verified. No JavaScript errors were reported. Non-JavaScript response
and POST behavior are additionally covered by ordinary Django client tests.

Existing eight npm advisories (two moderate, six high) and stale Browserslist data remain outside
PAY-1 scope; no dependency upgrade was made. The local virtualenv is Python 3.12.14, so supported
Python 3.13.16 PostgreSQL verification also uses the existing project Docker image with the
repository mounted read-only. Windows pytest's inherited temp-directory permission issue is
avoided with a dedicated ignored workspace scratch directory, without changing tests or settings.

Recovery verification — 2026-10-08:

- Case A: `pay1-payments` HEAD, local/remote main and peeled `payments-contract-v1` were
  `d12f3e8c3a955dd90f1e03f35a30fde789441764`. All 13 modified tracked files and 26 new
  Payments source/template files were preserved; no candidate commit or missing implementation
  was found. No production-code correction was needed during recovery.
- Previous test results were treated as historical. Final current-files verification used
  **Python 3.13.16 / Django 5.2.17 / PostgreSQL 17**: Payments-local **136 passed**;
  separate real-lock concurrency **22 passed**; full PostgreSQL **1,009 passed** with no warnings;
  full SQLite **868 passed / 141 expected PostgreSQL-only skips**.
- Dedicated database architecture regressions **222 passed**, including zero active-runtime
  violations; database execution/foundation checks separately **17 passed**. A fresh PostgreSQL
  database migrated from zero, registered exactly four active Payments permissions, and left
  Payments disabled. Migration drift, Django checks, Ruff, JavaScript syntax and diff checks passed.
- `npm ci` and Tailwind build passed; generated CSS remained byte-identical to the canonical
  baseline. Local Node was 24.20.0; no package/lockfile or CI configuration changed.
- Current focused real-browser smoke reconfirmed all five Payments screens at 390/768/1280px,
  exact boundary amount display, wrapping long payer/reference/notes, no receipt edit/delete,
  invalid-amount feedback, query-preserving 50/2 pagination and zero JavaScript console errors.
  Earlier browser workflow evidence above is historical, on unchanged presentation files.
- Final supported-runtime suites used fresh container-local `/tmp` directories; the inherited
  Windows temporary-directory failure did not recur. An interrupted full-run result was not
  inferred: the full PostgreSQL run was repeated with retained logs and actually completed.

At that historical recovery checkpoint this was a **local implementation candidate awaiting
independent PAY-1 audit**. Recovery authorized exactly one local
`feat: implement standalone payments receipts` commit, not publication, adoption, checkpoint
tagging, allocations, Accounting or integrations. Subsequent independent audit, publication/CI
and separately authorized formal acceptance are recorded below without rewriting that history.

### PAY-1 independent audit and formal acceptance — 2026-10-11

Implementation candidate: `86e15f9f0aea29a07694c251d511e4b60fc6d2ad`, one non-merge commit above
canonical `d12f3e8c3a955dd90f1e03f35a30fde789441764` (`payments-contract-v1`).
Independent verdict: **FINAL PASS — PAY-1 APPROVED FOR HOSTED CI**. The owner-supplied independent
record reports Python 3.13.16 / Django 5.2.17 / PostgreSQL 17.11; Payments PostgreSQL 136 passed,
22 real-lock concurrency cases, full PostgreSQL 1,009 passed, SQLite 868 passed / 141 expected
PostgreSQL-only skips, architecture guard 222 passed, 80 independent adversarial probes,
21 JavaScript checks and 18 responsive browser checks. Bootstrap, Ruff, Django/drift and
npm/Tailwind/CSS checks passed. These are independent-audit results, not new runs performed by this
documentation milestone; historical implementation-run results above remain separately identified.

Hosted implementation **Phase 0 checks #103 — SUCCESS**, run ID `38076354718`
([run evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38076354718)),
checked out exactly `86e15f9f0aea29a07694c251d511e4b60fc6d2ad`. Logs confirm **1,009 PostgreSQL
tests passed**, fresh migrations, Ruff, Django checks, no migration drift, `npm ci`, Tailwind build
and generated CSS reproducibility. Formal acceptance is **COMPLETE**:
**FORMALLY ACCEPTED FOR CANONICAL ADOPTION**. Canonical adoption is **PENDING**, not closed;
`main` remains `d12f3e8c3a955dd90f1e03f35a30fde789441764`. This later docs-only acceptance commit
requires its own exact-head hosted CI; implementation CI #103 is not substituted for that evidence.

Only the roadmap, ADR 0013 and this execution plan change. ADR 0013 remains Accepted — Gate PAY-0.
PaymentMethod administration and immutable incoming Payment/Receipt, exact Decimal(38,8), frozen
snapshots, current authorization, canonical retry/conflict, no-op audit and omitted-date midnight
recovery remain unchanged. No PaymentAllocation, receipt status/edit/delete, Billing dependency or
effect, Accounting or Inventory effect is added. No runtime/schema/migration/test/UI/dependency/
workflow changes, canonical adoption or tag are authorized. PAY-INT-1 and ACC-1 are NOT STARTED.

Known separate maintenance items: inherited ADR adoption wording (only necessary acceptance lines
factually normalized), favicon 404, eight npm advisories (two moderate, six high), Actions runtime
warnings and stale Browserslist data. No runtime maintenance or production approval is implied.

### PAY-1 post-adoption canonical closure — 2026-10-11

Current status: **PAY-1 STANDALONE PAYMENTS — CANONICALLY CLOSED**. The preceding pending/adoption
restrictions describe the historical formal-acceptance milestone and are retained as evidence.
Documentation-only acceptance `9ac3f0944fff65f013efd9c3a3e9b841022ce87f` passed exact-head
acceptance CI #104 / `38077428416`, then was adopted by normal fast-forward into canonical `main`.
Main **Phase 0 checks #105 — SUCCESS**
([run 38078381136](https://github.com/sahinkhan/djangobusinessos/actions/runs/38078381136))
checked out that exact SHA and passed fresh migrations, **1,009 PostgreSQL tests**, Ruff, Django
checks, no migration drift and npm/Tailwind/CSS checks. Annotated `payments-v1` object
`05dcb375d0b05ad6ee9f819faa2c4e57dbfd3a34` peels to that accepted canonical SHA.

No runtime change occurred during acceptance/adoption. PaymentMethod and immutable incoming
Payment/Receipt remain the only PAY-1 models. Earlier implementation, audit and acceptance evidence
is not overwritten. PaymentAllocation, PAY-INT-1 and Accounting/integration effects remain absent.
ACC-0 opens only the next documentation candidate; ACC-1 and production launch are not approved.

## Deferred allocation and acceptance requirements

PaymentAllocation stays Payments-owned but is NOT implemented in PAY-1. Applied/unapplied amounts,
invoice outstanding/status and allocation UI/selectors are deferred, not assumed to be zero.
Receipt amount is the standalone financial display; Billing still says Payment status unavailable.
A separate optional gate (such as PAY-INT-1) must approve stable Billing references/storage,
company/currency/frozen-precision agreement, availability/eligibility/complete evidence, partial/
over-allocation, PostgreSQL lock order, retry, audit, refund interaction, alias and outstanding
derivation. Do not prematurely freeze that storage or add an unconditional Billing dependency.

Future PAY-1 requires real PostgreSQL blocking coordination for same-key same/different payloads,
role/permission/company-access revocation after lock wait, method deactivation versus recording in
both orders, method snapshot updates and code-uniqueness races. Include canonical date/UUID/numeric
retry/midnight tests, historical retry after reference retirement, ORM bypass and audit/persistence
rollback, clean worker connections and non-default-alias checks; SQLite skips only lock-specific
cases. Add full suites/bootstrap/checks, module-local discovery, stale-company/RBAC HTTP matrix,
absent Billing/Accounting and responsive UI verification. Exact detail is in ADR 0013.

Also defer settlement/reconciliation, refund/reversal/chargeback/gateway, outgoing/vendor/AP,
Accounting posting, FX/revaluation, fees/splitting/advance credit/statements and fiscal/provider
numbering. PAY-0 and PAY-1 are canonically closed as recorded above. PAY-1 independent review,
implementation publication/CI, formal acceptance and separately authorized adoption are complete.
No integration is authorized and no historical experimental runtime is restored.

---

# Gate ACC-0 — Standalone Accounting & Finance Contract

Historical acceptance-stage status: **FORMALLY ACCEPTED — documentation/architecture only;
canonical adoption PENDING**, 2026-10-11. Subsequent ACC-0 adoption at `d5030e0e...` and ACC-1
canonical closure at `00e18a75...` are recorded in the current status and final closure sections.
Starting canonical `main`: `9ac3f0944fff65f013efd9c3a3e9b841022ce87f` (`payments-v1`).
Contract branch: `acc0-accounting-contract`. The detailed accepted specification is
[ADR 0014](../../decisions/0014-standalone-accounting-finance-contract.md), Accepted — Gate ACC-0.
No Accounting implementation, registration, migration, test or UI change is authorized here.

ACC-0 audit chronology: original candidate `c9f676349a72c585d16a6d3a467cdd676ee2db1d` passed
exact-head CI #107 / `38109947735` (1,009 PostgreSQL tests), then received independent **REVISE**
for F1/F2, two P2s concerning persistence/text bounds and position range/exhaustion, with no P0/P1.
Separately authorized remediation `217b7a8f39b628571f616034a7d9d02b436ec03d`,
`docs: remediate ACC-0 persistence bounds`, addressed only those findings and preserved the original
commit. Exact-head **Phase 0 checks #108 — SUCCESS**, run ID `38112122913`
([evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38112122913)), checked out
that branch/head and passed Python 3.13.16 / **1,009 PostgreSQL tests**, fresh migrations, Ruff,
Django checks, no migration drift, `npm ci`, Tailwind and CSS reproducibility.

The owner-supplied corrective independent verdict is **FINAL PASS — ACC-0 CONTRACT APPROVED FOR
FORMAL ACCEPTANCE**, implementation readiness **A**; F1/F2 resolved, no new P0/P1/P2/P3.
The exact formally accepted contract head is `217b7a8f39b628571f616034a7d9d02b436ec03d`, with
the original/remediation two-commit history intact. Formal acceptance is **COMPLETE**; canonical
adoption is **PENDING** and `accounting-contract-v1` is **NOT YET CREATED**. This docs-only acceptance
commit requires a new exact-head CI, not reuse of #108. ACC-1, PAY-INT-1, Billing/Payments Accounting
integrations and production deployment remain unauthorized. The audit is contract/architecture
acceptance, not executed ACC-1 runtime testing.

Accepted minimum ACC-1 contract, with adoption and implementation still separately authorized:

- Account and Journal: immutable Company/normalized code, company uniqueness, service-mutable
  name/activity; immutable Account type ASSET/LIABILITY/EQUITY/INCOME/EXPENSE; no hierarchy/hard delete.
- JournalEntry/lines: Company-base-currency only, immutable code/precision snapshots 0..8;
  `JE-<entry UUID hex>` number; Company-local default date; DRAFT -> POSTED only; draft service edits,
  immutable posted header/lines and protected public ORM bypass paths.
- Debit/credit Decimal(38,8), finite/nonnegative/below `10^30`, exactly one positive side;
  frozen-precision exact representability accepts redundant zeros, rejects float/nonfinite/excess
  nonzero scale, never silently rounds. Posting requires active Journal/Accounts, two valid lines
  and exact positive equal totals, with sufficiently large arithmetic context.
- Alias-aware Company lock -> current context/RBAC recheck -> Entry -> deterministic references
  -> validation -> state and audit in one transaction. Same-Entry post retry reauthorizes and returns
  original without duplicate timestamp/write/audit/effect. Real PostgreSQL race evidence required.
- Exactly eight permissions and seven audit actions in ADR 0014. HTTP action GET/POST enforces
  relevant permission; missing/disabled registry gates HTTP/navigation only, never installed APIs.
- Derived GL/TB use POSTED lines only, preserve inactive history, exact currency/precision and
  deterministic Company/date/Account scope. No authoritative Account/Journal/balance cache field.
- Exact dependencies: `party, organization, reference, access`; approved Core infrastructure only.
  No Billing/Payments/Catalog/other commercial dependency or effects. PaymentAllocation stays
  Payments-owned and absent from standalone Accounting.

**Explicit historical refinement:** standalone ACC-1 has no generic external-source header
idempotency field. Same-Entry transition retry is safe; future external composition must define
atomic source identity, header, complete lines, amounts and posting/duplicate effects at its own
integration gate. Following formal acceptance, ADR 0014 governs detailed ACC-1 and supersedes only
conflicting Accounting details in older notes. It does not remove ADR 0006's future integration
retry-safety requirement or change ADR 0011/0013 ownership. Its earlier Proposed state did not
constitute accepted authority; acceptance still does not authorize runtime implementation.

Historical initial candidate gate: exactly one docs-only commit, normal publication and exact-head CI; require
fresh PostgreSQL bootstrap/full current suite and mandatory checks, then STOP for independent audit.
At that initial stage no acceptance/adoption/tag or implementation was authorized. Remediation and
formal acceptance subsequently received separate authorization, one additional docs-only commit
each. At that acceptance milestone publication/CI had to STOP before canonical adoption, `accounting-contract-v1`,
ACC-1, PAY-INT-1 or any integration. No substantive contract semantics change during acceptance.
The ADR's acceptance matrix is a future ACC-1 requirement, not executed ACC-0 test evidence.

# Historical Accounting planning notes — formerly Batch 2E / Gate ACC-1

The original minimum journal notes below are retained as historical planning evidence, not the final
ACC-1 schema/API specification. In particular their optional idempotency-key and external header-key
bullets do not authorize a standalone key field. ADR 0014 above explicitly proposes that refinement;
acceptance/adoption and runtime work remain separately gated. Independent Accounting and optional
public-service composition remain unchanged. No historical experimental Accounting code is restored.

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

## Payments + Billing invoice allocation — PAY-INT-0

Current PAY-INT-1 implementation is canonically closed at `a1079985...`; see the
[post-adoption record](#pay-int-1-post-adoption-canonical-closure--2026-10-12).
The following PAY-INT-0 design/acceptance-stage notes remain historical, not current implementation
absence or pending adoption.

The formally accepted specification is
[ADR 0015](../../decisions/0015-billing-payments-allocation-integration-contract.md),
**Accepted — Gate PAY-INT-0**, from canonical `00e18a75e27bfe962ea290ab01f0cb0520f4427e`.
It selects a Payments-owned opt-in Billing integration app with protected Payment/Invoice FKs;
the base Payments and Billing manifests remain independent. New allocation facts are immutable,
partial and many-to-many, with a required company-scoped retry key, strict Party/currency/frozen
precision agreement, current authorization after Company lock, deterministic parent locking and
one atomic `payments.allocation.created` audit. Composed reads require complete compatible
evidence; unavailable is never zero paid. HTTP admission alone checks registry enablement;
installed Python APIs retain context/RBAC, not service-level module gating.

PAY-INT-0 is design only. Independent audit and exact-head proposal CI are complete; formal
acceptance is recorded without technical changes. Own exact-head acceptance CI -> canonical
fast-forward adoption -> separate exact-head main CI precede any separate PAY-INT-1 authority.
PAY-INT-1 is **NOT STARTED / NOT AUTHORIZED**. No allocation model, migration, permission, audit
action, selector, service or UI is implemented by this candidate. No Accounting posting follows
invoice issue, receipt recording or allocation. Accounting and other integration gates remain
unauthorized. ADR 0015 contains the future functional/adversarial/concurrency/rollback/alias/UI
acceptance matrix, not newly executed tests.

## Billing / Payments outcomes -> Accounting

Current specification: **Accepted — Gate ACC-INT-0**,
[ADR 0016](../../decisions/0016-accounting-commercial-outcomes-integration-contract.md).
It accepts the audited topology, source/effect bindings, explicit account selection, zero/precision/
date/Party policies, compound authority, complete-evidence and future acceptance matrix. The older
minimum patterns below are retained planning context; their imperative wording is **not ACC-INT-1
authorization**. HTTP enablement remains separate from installed Python services' context/RBAC.

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
For future standalone PAY-1 verify ADR 0013's receipt/method/snapshot/precision/idempotency,
Company-lock authorization recheck, method races, immutable ORM, alias and audit-rollback contract.
This accepted verification contract is not PAY-1 implementation authorization.
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
Gate BILL-1 formal acceptance      COMPLETE at 409e45eaa32fae1cf9c77042a762e57026d0349f
Gate BILL-1 canonical adoption     CLOSED / main CI #97 SUCCESS / billing-invoicing-v1
Gate PAY-0 accepted candidate      9ffb5eae09da680354776872a601bedd58163ab1 / independent FINAL PASS
Gate PAY-0 candidate hosted CI     #99 / 37656399267 SUCCESS / 873 PostgreSQL tests
Gate PAY-0 formal acceptance       COMPLETE / ADR 0013 Accepted / documentation-architecture only
Gate PAY-0 canonical adoption      CLOSED / d12f3e8c / payments-contract-v1 / main CI #101 PASS
Gate PAY-1 implementation          86e15f9f0aea29a07694c251d511e4b60fc6d2ad / published
Gate PAY-1 independent audit       FINAL PASS — PAY-1 APPROVED FOR HOSTED CI
Gate PAY-1 implementation CI        #103 / 38076354718 SUCCESS / 1,009 PostgreSQL tests
Gate PAY-1 formal acceptance       COMPLETE / FORMALLY ACCEPTED FOR CANONICAL ADOPTION
Gate PAY-1 canonical adoption      CLOSED / 9ac3f0944fff65f013efd9c3a3e9b841022ce87f / payments-v1
Gate PAY-1 final main CI           #105 / 38078381136 SUCCESS / 1,009 PostgreSQL tests
Gate PAY-INT-1 original audit       4b8a072d; REVISE / readiness C / R1-R4 retained
Gate ACC-0 contract                FORMALLY ACCEPTED / ADR 0014 / acc0-accounting-contract
Gate ACC-0 accepted contract head  217b7a8f39b628571f616034a7d9d02b436ec03d / CI #108 SUCCESS
Gate ACC-0 corrective review       FINAL PASS / readiness A / F1-F2 resolved / no P0-P3
Gate ACC-0 formal acceptance       COMPLETE / acceptance commit requires exact-head CI
Gate ACC-0 canonical adoption      COMPLETE / d5030e0e / accounting-contract-v1
Gate ACC-1 original audit          REVISE / readiness C / ACC1-R1 P2 / no reported P0/P1
Gate ACC-1 remediation             ACC1-R1 substantive / ACC1-R2 P3 formatting RESOLVED
Gate ACC-1 independent final       PASS — ACC-1 IMPLEMENTATION APPROVED FOR PUBLICATION
Gate ACC-1 candidate push CI       #112 / 38127289623 SUCCESS / exact 00e18a75...
Gate ACC-1 canonical closure       00e18a75e27bfe962ea290ab01f0cb0520f4427e / normal fast-forward
Gate ACC-1 main CI                 #114 / 38127960676 SUCCESS / 1,313 PostgreSQL tests
Gate ACC-1 accounting-v1 tag        NOT CREATED / no tag claimed
Gate PAY-INT-0 audited proposal    9d4fa5d3b7a12d4eb0ee2046d6e4ff306957e228 / intact
Gate PAY-INT-0 independent audit   FINAL PASS / readiness A / no actionable candidate-owned P0-P3
Gate PAY-INT-0 candidate push CI   #115 / 38133793295 SUCCESS / 1,313 PostgreSQL tests
Gate PAY-INT-0 formal acceptance   COMPLETE / Accepted ADR 0015 / metadata only
Gate PAY-INT-0 canonical adoption  CLOSED / 9ee4e0bd / acceptance CI #116 / main CI #117 SUCCESS
Gate PAY-INT-1 corrective candidate bef50fe8b20f97aaeefb8c610a46d412e9a05402 / published intact
Gate PAY-INT-1 corrective review    FINAL PASS / readiness A / R1-R4 RESOLVED / no new P0-P3
Gate PAY-INT-1 implementation CI    #118 / 38162359131 SUCCESS / 1,613 PostgreSQL tests
Gate PAY-INT-1 formal acceptance    COMPLETE / FORMALLY ACCEPTED FOR CANONICAL ADOPTION
Gate PAY-INT-1 canonical adoption   CLOSED / a1079985a2ef5645dfed338e3e58af54f5242e1a
Gate PAY-INT-1 acceptance CI        #119 / 38163571737 SUCCESS / 1,613 PostgreSQL tests
Gate PAY-INT-1 main CI              #120 / 38164395135 SUCCESS / 1,613 PostgreSQL tests
Gate ACC-INT-0 independent review  FINAL PASS / readiness A / no candidate-owned P0-P3
Gate ACC-INT-0 proposal CI         #125 / 38203841663 SUCCESS / 1,613 PostgreSQL tests
Gate ACC-INT-0 formal acceptance   COMPLETE / CANONICALLY CLOSED / canonical base 4419bdc4...
Gate ACC-INT-1 corrective review    FINAL PASS / readiness A / ACCINT1-AUD-1 RESOLVED
Gate ACC-INT-1 implementation CI    #128 / 38365702656 SUCCESS / 2,755 PostgreSQL tests
Gate ACC-INT-1 formal acceptance    COMPLETE / FORMALLY ACCEPTED FOR CANONICAL ADOPTION
Gate ACC-INT-1 canonical adoption   PENDING AT THIS ACCEPTANCE CHECKPOINT / acceptance and main CI required
Accounting integration runtime     corrective candidate published intact / formally accepted
Phase 2                            NOT COMPLETE
Phase 2 final completion audit     NOT YET PERFORMED
Phase 3                            NOT AUTHORIZED
Other integration implementation   not authorized
```

## ACC-1 local implementation verification — 2026-10-11

This is historical developer execution evidence for the single local implementation commit
containing this record, not independent acceptance or hosted ACC-1 CI. At that checkpoint
parent/main remained exactly
`d5030e0e807334fdc358a1aa3affce704ef4a0f0`. Existing `accounting-contract-v1` tag object
`7369a26d526e10e9a128b44cf79efca9cf353e89` peels to that SHA. ADR 0014 remains
**Accepted — Gate ACC-0**; no ACC-1 acceptance or release/foundation tag is created.

### Delivered behavior

- Four Company-owned UUID/timestamp models only: Account, Journal, JournalEntry and
  JournalEntryLine. Account code/type and Journal code are immutable; reference names/activity
  may change. Codes normalize by trim/uppercase with a 32-character post-normalization limit;
  names trim to a required maximum of 160 characters. Memo/description preserve exact blank,
  non-null, unbounded text. Relationships use PROTECT, with optional same-company Party only.
- New migrations `accounting.0001_initial` and `0002_register_manifest`; all released migrations
  are unchanged. Database uniqueness covers Company reference codes, Company entry numbers and
  entry/position. CHECKs cover Account type, DRAFT/null versus POSTED/non-null posting time,
  precision 0–8, position 1–2,147,483,647, nonnegative amounts below 10^30 and exactly one positive
  debit/credit side. Cross-row balance and Company ownership remain validated business rules.
- Manifest dependencies are exactly `party`, `organization`, `reference`, `access`. Its frozen
  registration declares eight permissions: `accounting.account.view/manage`,
  `accounting.journal.view/manage`, and `accounting.entry.view/create/update/post`. Fresh
  registration is disabled; existing enablement is preserved. HTTP/navigation gating does not
  disable installed Python services, which still require valid context and RBAC.
- Ten alias-aware services: create/update Account, create/update Journal, create/update entry,
  add/update/remove draft line, and post entry. Active Company lock precedes current authorization;
  then entry, Journal, ordered lines, UUID-ordered Accounts and non-null Parties are locked as
  applicable. Business transactions/savepoints resolve the selected execution alias at entry.
- Seven atomic audit actions: `accounting.account.created/updated`,
  `accounting.journal.created/updated`, `accounting.entry.created/updated/posted`. Line changes
  use entry.updated with operation, line UUID and changed fields. True no-ops do not rewrite
  timestamps or create success audit. Audit failure rolls back business mutations.
- Entry number is `JE-` plus its 32 lowercase UUID hex characters (35 total); three bounded
  attempts retry only proven generated identity collisions, not unrelated integrity failures.
  Creation captures Company-local date once if omitted and freezes base code/precision. Existing
  snapshots do not follow later Currency precision/activity changes.
- Exact finite Decimal/integer/numeric-string amounts only: no float/bool, no rounding to balance,
  and no precision loss beyond the frozen precision. Decimal(38,8) stores each side; aggregate
  arithmetic grows its context for totals above a single-line range. Stable positions allocate
  highest retained + 1, preserve internal gaps and reject exhaustion before write/audit.
- Only DRAFT → POSTED exists. Posting requires two or more lines, active referenced Journal/
  Accounts/optional Parties, compatible Company base currency, and positive exactly equal totals.
  Posted facts are immutable. Authorized same-entry retry returns the existing posting without
  another timestamp, ledger effect or audit, even after reference retirement; revoked/inactive
  current actor/Company authority still denies retry. No external-source idempotency field exists.
- Public instance save/delete, queryset update/delete, bulk update/create/upsert and corresponding
  async APIs are guarded. Narrow private persistence/transition paths serve authorized services;
  stale deleted lines cannot be reinserted. These guards do not pretend to constrain deliberate
  raw SQL or invocation of Django base-class internals outside the public business API.
- Selectors expose scoped Accounts, Journals, entries/detail, General Ledger and Trial Balance.
  GL uses posted lines only, stable ordering, inclusive date bounds and optional same-company
  Account filtering. Malformed Company/currency provenance fails closed before date filtering.
  TB groups posted activity by Account, retains inactive and zero-net activity, derives ending
  debit/credit exactly and displays the maximum contributing frozen precision, not current
  Currency precision. Ranges are movement/net, not invented opening/closing balances. Reference
  names are explicitly current labels, not fictional historical snapshots.
- Existing shell pages include references, draft entry/line editing/removal, detail, posting
  confirmation and GL/TB. Action GET/POST permissions are explicit; company-bound POSTs use CSRF,
  no GET mutation, and mutations do not acquire incidental view-permission requirements.
  Ordinary lists and reports use stable 50-row pagination with safe GET/HTMX behavior.

### Verification evidence

Supported runtime: disposable Linux Docker, Python **3.13.16**, Django **5.2.17**, PostgreSQL **17**.
Only new synthetic task databases were used; existing demos/customer data were not accessed.

| Check | Actual result |
| --- | --- |
| Full PostgreSQL suite (`pytest -q --ds=config.settings.development`) | **1,282 passed**, no skips or teardown warning |
| Accounting + database architecture guard | **495 passed**: Accounting **273**, guard **222** |
| Accounting PostgreSQL lock coordination | **56 passed**, real `pg_blocking_pids` observations; worker connections close in finally |
| Final Accounting HTTP/UI PostgreSQL subset | **34 passed**, including report errors within HTMX swap target |
| Full SQLite suite (`pytest -q --ds=config.settings.test`) | **1,084 passed, 198 expected skips** (row-lock/exact PostgreSQL numeric cases) |
| Fresh zero-state PostgreSQL migrations | PASS, including both new Accounting migrations; eight permissions and fresh disabled module verified |
| Non-default alias | PASS: fresh migration/CRUD/post/retry/rollback/audit/GL/TB; default cursor forbidden during selected-alias operations |
| Standalone installation | PASS: Party + Core + Accounting only; no other commercial module installed/imported |
| Existing Billing issue / Payments record | PASS: no Accounting entries, lines or audit effects |
| Ruff / module formatting / Django checks / migration drift | PASS; no missing migrations |
| JavaScript syntax / navigation tests | PASS; **21 JavaScript tests** |
| npm ci / Tailwind / generated CSS reproducibility / whitespace | PASS; no dependency/lockfile change |

Browser verification used only disposable synthetic Accounting data at **390, 768 and 1280 CSS
pixels**. Boundary fixtures included 32-character code, 160-character reference name, 35-character
number, 168-character Party label, 12,000-character memo/description and
`999999999999999999999999999999.99999999` amounts at frozen precision eight. Body scroll widths
were respectively **380 / 758 / 1270**, with no page-wide overflow; wide tables scroll locally.
Verified draft header/line edit/remove, Account/Journal creation, visible non-finite amount and
incomplete-post errors, normal POST and keyboard focus/Tab/Enter, successful posting/read-only
presentation, GL/TB exact amounts and zero-net row, date-filter errors, 50-row filter/pagination
query preservation, deep refresh and Back/Forward. Final fresh-origin browser console had no errors.
Report controls were adjusted only in the Accounting template to avoid clipping on mobile;
validation messages stay within `#list-results`. Cached QA CSS was identified and the latest
generated CSS verified on a fresh local origin, without modifying shared cache/security behavior.

Two overlapping intermediate PostgreSQL runs were discarded because their synthetic test-database
names collided; they are not PASS evidence. Subsequent full/focused runs used distinct primary
database names and passed. A Windows Python 3.12 attempt was stopped and is not authoritative
financial/concurrency evidence. Initial sandbox `npm ci` failed DNS; the authorized normal retry
succeeded. Eight inherited npm advisories (two moderate/six high), favicon 404, stale Browserslist,
Actions runtime warnings and BILL-1 badge wrapping remain excluded maintenance work.

No Billing/Payments dependency, PaymentAllocation, automatic integration, authoritative mutable
balance, SaaS activation or production deployment was introduced. `main`, historical branches,
accepted contracts and existing tags remain unchanged. Only one local implementation commit is
authorized; no push, merge, acceptance or tag. **Stop for independent ACC-1 implementation audit.**

## ACC1-R1 report-retrieval remediation — 2026-10-11

Original local implementation `8eaa084aee58cc7c09e6ce74fe663b1f47c7d9f3` is preserved unchanged.
The supplied independent verdict was **REVISE — ACC-1 IMPLEMENTATION REQUIRES REMEDIATION**,
readiness **C**, with one blocking **ACC1-R1 — P2** and no reported P0/P1. This batch addresses
that finding only. At that checkpoint it was local implementation-run evidence, **awaiting independent
corrective audit**, not FINAL PASS, publication, acceptance or adoption. The remediation SHA is the local
commit containing this record; its parent is the original candidate, whose parent/main is
`d5030e0e807334fdc358a1aa3affce704ef4a0f0`.

### Reproduction and bounded retrieval

Before production edits, two PostgreSQL regressions reproduced the defect with 33 posted entries,
66 lines and 12,000-character memo/description fields: future-date GL returned no rows but
constructed **66** JournalEntryLine objects; page one displayed 50 but constructed **66**.
Both tests failed against the original selector. Inspection confirmed whole-Company `list()`
materialization before Python filtering/pagination, with TB reusing that list and retaining
groups of contributing lines.

The corrected reads separate whole-Company integrity from requested payload:

- Two alias-pinned database anomaly probes return `SELECT 1 ... LIMIT 1`, not text/reference/model
  payload. They inspect either side of line/Entry ownership and reject Company, Account, Journal,
  optional Party, currency provenance, amount/position or frozen-precision violations before
  requested filters. The second probe compares amounts to SQL ROUND solely to detect incompatible
  frozen scale; it does not round returned amounts. Seven corruption classes outside a valid
  requested date/Account scope are tested for both selectors, with no line-object construction.
- GL returns an authorized, Company/POSTED-scoped lazy QuerySet with inclusive dates and Account
  predicates in SQL. Selected execution alias is pinned even for evaluation after scope exit.
  SQL ordering is Entry date, number, Entry UUID, position, line UUID. Existing 50-row Paginator
  now performs SQL COUNT plus `LIMIT 50`; the 66-line second page uses `LIMIT 16 OFFSET 50`.
  Only the requested page's descriptions, memos and references are constructed. An explicit
  non-UI caller evaluating its entire filtered QuerySet still requests that entire result;
  callers should slice before evaluation when they need a bounded batch.
- TB independently pushes the same scope into SQL `GROUP BY Account`, `SUM(debit/credit)` and
  `MAX(frozen precision)`. It constructs only aggregate Account rows, ordered by code/UUID.
  PostgreSQL SUM retains unrestricted NUMERIC output through an unbounded Decimal output field;
  no single-line numeric(38,8) cast, float conversion or silent report quantization is introduced.
  The 2,002-line boundary fixture proves exact debit/credit sums of
  `1000999999999999999999999999999999.99998999`, above the single-line range, with zero net.
  Inactive and zero-net Accounts with activity remain; current Currency precision does not
  reinterpret frozen history. Existing report-wide maximum precision is retained, at least
  each contributing Account's maximum.

Python memory for ordinary UI GL is O(page), TB O(aggregate Accounts), integrity O(1) result
payload. Integrity and aggregate SQL can still scan relevant history inside PostgreSQL; no
constant database-work or timing guarantee is claimed. No report cache, mutable balance,
export subsystem, write transaction, schema/index change or dependency was added.

Manual captured-query review independently inspected future-date and Account-filtered GL,
page one/page two, and TB: predicates precede materialization/aggregation; page SQL has
LIMIT/OFFSET; TB has SUM/GROUP BY/MAX; integrity SQL selects no memo/description. Ordinary GL/TB
requests do **not** materialize all Company history in Python. Default-cursor-forbidden alias
tests also cover lazy evaluation, pagination, filtered empty reports and grouped aggregation.

### Remediation verification

All application fixtures are new disposable synthetic PostgreSQL/SQLite databases on the
supported Linux Docker runtime (Python 3.13.16, Django 5.2.17, PostgreSQL 17). Existing demos,
customer deployments and the target repository are untouched.

| Check | Actual remediation result |
| --- | --- |
| Focused new report regressions | **31 passed**: 30 selector and one HTTP pagination; existing non-default alias test strengthened and passed in the Accounting suite |
| Accounting PostgreSQL suite | **304 passed**, including the unchanged **56** real-lock concurrency cases; no teardown warning |
| Full PostgreSQL suite | **1,313 passed**, no skips or teardown warning |
| Full SQLite suite | **1,114 passed, 199 expected PostgreSQL-only skips** |
| Database architecture guard | **222 passed** |
| Fresh PostgreSQL zero-state migrate / Django check / migration drift | PASS; zero issues / no changes detected; no migration added |
| Ruff / Accounting formatting / JS syntax / whitespace | PASS |
| JavaScript navigation tests | **21 passed** |
| npm ci / Tailwind build / CSS reproducibility | PASS; dependency/lockfiles/CSS unchanged; inherited 8 advisories (2 moderate, 6 high), no upgrades |

Real-browser report verification uses 34 synthetic posted entries/68 lines, 12,000-character
memo/description, 168-character Party label and maximum supported single-line amounts. At
**390 / 768 / 1280px**, body scroll widths are **380 / 758 / 1270px**; tables scroll locally,
controls remain visible and no page-wide overflow is observed. GL page one (50), page two (18),
Account filter (34), future empty result, reversed-date validation and TB exact large aggregates
were checked. Desktop Back/Forward and direct refresh retain the correct page; mobile app
navigation opens/closes normally. Fresh QA-origin console has no Accounting JavaScript errors.
No UI template, shared navigation, CSS or JavaScript changes are part of this remediation.

Two provisional PostgreSQL suite runs were stopped before their final repeats after strengthening
the corruption fixture to include valid in-range activity; they are not PASS evidence. An extra
focused launch used an unsupported DATABASE_URL variable and failed connection setup before
tests; the corrected launch uses the repository's POSTGRES_* variables. This is harness evidence,
not a source or production-settings change. Windows bare Ruff was unavailable and Docker's
read-only source cache rejected a check; final Docker Ruff/format checks passed with `--no-cache`.
Earlier implementation failures and verification
remain retained in the preceding historical record.

Only Accounting selectors, two view comments, three Accounting test files and this plan/roadmap
change. Models, domain, services, authorization, manifests, schemas/migrations, accepted ADR 0014,
other modules, templates/assets, settings and dependencies remain unchanged. No Billing/Payments
dependency/effect, PaymentAllocation, external integration, SaaS activation or production
deployment was introduced. One additional local commit is authorized, subject
`fix: bound accounting report retrieval`; no push, main update, merge, amendment or tag.
**Stop for independent ACC-1 corrective audit.**

## ACC-1 final reconciliation, publication and canonical closure — 2026-10-11

The preceding implementation and ACC1-R1 records remain historical and distinguish developer runs
from independent audit and hosted CI. They are not overwritten by this later closure.

| Preserved checkpoint | Outcome |
| --- | --- |
| `8eaa084aee58cc7c09e6ce74fe663b1f47c7d9f3` | Original implementation; independent REVISE / readiness C / ACC1-R1 P2 |
| `0aa759cbbc881ce8c3488f2a98c2095e8c9d2797` | SQL-bounded report remediation; ACC1-R1 RESOLVED |
| `00e18a75e27bfe962ea290ab01f0cb0520f4427e` | Narrow changed-file formatting remediation; ACC1-R2 P3 RESOLVED; frozen candidate |

ACC1-R2 formatted only `tests/test_database_foundation.py` and Accounting migrations
`0001_initial.py` / `0002_register_manifest.py`; migration semantics and the intentional module
count 7 -> 8 remained unchanged. Whole-project inherited format failures were not mass-remediated.
Final independent reconciliation: **PASS — ACC-1 IMPLEMENTATION APPROVED FOR PUBLICATION**.

Candidate **Phase 0 checks #112 / 38127289623 — SUCCESS**
([run](https://github.com/sahinkhan/djangobusinessos/actions/runs/38127289623)) checked out exactly
`00e18a75e27bfe962ea290ab01f0cb0520f4427e`, passing fresh PostgreSQL migrations, **1,313 tests**
and all mandatory checks. Unnecessary PR #1 was closed **without merging**; its supplementary
PR workflow is not the publication/adoption gate. The corrected established direct fast-forward
flow adopted that exact candidate into canonical `main` without squash/rebase/merge commit/force.

Canonical **Phase 0 checks #114 / 38127960676 — SUCCESS**
([run](https://github.com/sahinkhan/djangobusinessos/actions/runs/38127960676)) checked out the
same exact SHA and passed **1,313 PostgreSQL tests**, fresh migrations, Ruff, Django checks,
no migration drift, npm/Tailwind and generated CSS reproducibility. These are hosted publication
results, not runtime suites newly executed for PAY-INT-0. Earlier PostgreSQL/SQLite and browser
tables remain implementation-run evidence. Inherited npm/Actions maintenance warnings remain
separate; no dependency upgrade is claimed.

**ACC-1 STANDALONE ACCOUNTING — CANONICALLY CLOSED.** Freeze:
`00e18a75e27bfe962ea290ab01f0cb0520f4427e`. No `accounting-v1` tag exists or is invented here.
Manual balanced journals and derived GL/TB do not establish production Accounting readiness,
whole Phase 2 completion or automatic Billing/Payments posting.

At the local-preparation checkpoint the next proposal was **PAY-INT-0**, ADR 0015, documentation
only; independent audit, publication/CI, acceptance and adoption were still required. That
preparation created no PR and did not move main/tag/history. Later acceptance evidence follows.
PAY-INT-1, Accounting automation, all other integration runtime,
actual SaaS activation and production deployment remain **NOT STARTED / NOT AUTHORIZED**.

### PAY-INT-0 historical local documentation preparation checks — 2026-10-11

At that preparation checkpoint only this plan, the roadmap and new Proposed ADR 0015 changed.
UTF-8, code-fence/table structure,
new relative links/anchors, exact documentation-path scope and whitespace checks passed.
Canonical `ruff check . --no-cache`, Django system check (zero issues) and
`makemigrations --check --dry-run` (no changes) passed. Existing database-architecture/module
tests: **231 passed**, in a disposable read-only Linux QA container with in-memory SQLite and
network disabled. No application/demo database was accessed. Full PostgreSQL/SQLite, bootstrap,
frontend and browser suites were not repeated for unchanged runtime; the prior exact baseline
CI #114 remains separately identified above, not claimed as new candidate CI. No runtime/schema/
asset/accepted-ADR change, independent PAY-INT-0 audit, publication, main update or tag was claimed
at that historical preparation stage.

### PAY-INT-0 independent approval, publication and formal acceptance — 2026-10-11

The original documentation proposal is frozen at
`9d4fa5d3b7a12d4eb0ee2046d6e4ff306957e228`, parent
`00e18a75e27bfe962ea290ab01f0cb0520f4427e`. The owner supplied independent **FINAL PASS —
PAY-INT-0 CONTRACT APPROVED FOR FORMAL ACCEPTANCE**, readiness **A**, with no actionable
candidate-owned P0, P1, P2 or P3. This is supplied review evidence, not a self-performed audit.
Normal publication preserved that exact candidate. Hosted **Phase 0 checks #115 / 38133793295 —
SUCCESS** ([run](https://github.com/sahinkhan/djangobusinessos/actions/runs/38133793295)) checked out
the same exact SHA and passed **1,313 PostgreSQL tests**, fresh migrations, Ruff, Django checks,
no migration drift, npm/Tailwind and generated CSS reproducibility. Inherited eight npm advisories
and Actions runtime warnings remain separate; no dependency upgrade or production approval is claimed.

**Formal acceptance: COMPLETE. Canonical adoption: PENDING at this acceptance checkpoint.**
Only these three documentation files change during acceptance; ADR 0015's technical contract and
future acceptance matrix remain unchanged. Accepted ADRs 0011/0013/0014, runtime, tests, schemas,
migrations, settings, manifests and frontend assets are untouched. The original proposal/audit/
verification chronology remains intact. This acceptance commit requires its own exact-head branch
CI; candidate CI #115 is not substituted for it. The separately authorized no-PR sequence then
requires unchanged starting main, normal fast-forward adoption and a separate exact-head main
push CI. Only successful completion makes this same acceptance commit the **PAY-INT-0 canonical
freeze / CANONICALLY CLOSED** checkpoint. The pending wording is acceptance-stage evidence; actual
later run IDs and freeze SHA are reported from verified publication results, not invented here.
No extra closure commit, amendment, force push, merge commit, tag name or release is introduced.

**PAY-INT-1 and Accounting integrations: NOT STARTED / NOT AUTHORIZED. Actual SaaS activation and
production deployment: NOT AUTHORIZED.** Full Phase 2 is not complete. STOP after the authorized
publication/adoption verification; no runtime implementation or next milestone begins here.

## PAY-INT-1 local implementation and verification — 2026-10-11

**HISTORICAL ORIGINAL IMPLEMENTATION CHECKPOINT / BEFORE THE SUPPLIED REVISE AUDIT.
NOT PUBLISHED / NOT ACCEPTED / NOT CANONICALLY ADOPTED.** The owner's separate implementation
instruction authorizes one local
commit, subject `feat: implement PAY-INT-1 payment allocations`, from
`9ee4e0bd77350ddeef1e928e2a73b676b4cbb1ee` on `payint1-billing-payments-allocation`.
The resulting exact SHA is reported from Git after verification, not invented inside this commit.
Canonical local/remote main, historical branches/tags and the prior PAY-INT-0 chronology are
preserved. This is developer implementation/verification evidence, not an independent audit.

### Optional installation and frozen persistence

Deployment opt-in is `BUSINESSOS_INSTALL_PAYMENTS_BILLING=1`; unset/`0` leaves the optional app,
routes and parent-evidence context processor uninstalled. The explicit optional Django app under
`businessos/modules/payments/integrations/billing/` has label/registry code `payments_billing`,
version `0.1.0`, and dependencies exactly `billing`, `payments`. Its migrations are
`0001_initial` and `0002_register_manifest`; no released owner/Core migration changes.
Registration freezes exactly `payments_billing.allocation.view` and
`payments_billing.allocation.create`, defaults disabled and preserves prior enablement.
CI's existing PostgreSQL job explicitly opts in so future publication tests the new app rather
than silently skipping it. Actual hosted CI is not run or claimed in this local-only task.

`PaymentAllocation` contains exactly UUID `id`, PROTECT `company`/`payment`/`invoice`,
Decimal(38,8) `amount`, required max-128 `idempotency_key`, `created_at`, `updated_at`.
Checks enforce positive/<10^30 amount and nonblank key bounds; `(company, idempotency_key)` is
unique, with each parent's Company/created_at/UUID history index. Case-sensitive normalized keys
permit distinct repeated partial allocations for the same pair. There is no status, copied
currency/precision, persisted balance, reversal or Accounting marker. Ordinary save/delete,
QuerySet update/delete, bulk/upsert/convenience and async paths reject; the validated service has
one private insertion primitive. Public owner models/mutation authorities are unchanged.

### Owner bases, mutation and read contracts

Billing exposes read-only `invoice_financial_basis` and `issued_invoice_basis_query`; Payments
exposes `payment_receipt_basis` and `receipt_basis_query`, versioned `1`. Requested bases are
minimal immutable DTOs; whole-history owner validity uses scoped scalar SQL. Billing retains its
exact SQL quantity*price sum, line integrity checks and once-only HALF_UP original total. The
existing pure calculation and the new basis share `finalize_total`; no settlement math moves
into Billing. Frozen Currency provenance is checked without adding reference-activity gates.

`create_payment_allocation` accepts context and IDs/exact data only. It uses the selected-alias
transaction, active Company lock/current compound authorization, canonical keyed lookup,
Payment lock/reauthorization, Invoice lock/reauthorization, complete validity/capacity queries,
private insert and Core `payments.allocation.created` audit in the same transaction. Matching
retry returns the original UUID/timestamps without new capacity/audit; conflicting payloads fail
`idempotency_conflict`. Expected company-key and bounded UUID collisions are distinguished in
alias-aware savepoints; unrelated IntegrityError propagates. New amounts reject float/bool,
malformed/nonfinite/zero/negative/range/excess-scale values without rounding; redundant zeros
are canonical. Current authority remains necessary for fully-applied or retired-reference retries.

Reads require allocation.view plus both owner view permissions; creation/retry require
allocation.create plus both owner views, not allocation.view/record/issue. HTTP admission is
Company -> ordered registry locks (`billing`, `payments`, `payments_billing`) -> current
enablement/context/compound RBAC, held through commit. Missing/disabled HTTP prerequisites yield
404; installed Python APIs remain independent of UI registry state.

`payment_allocation_evidence` / `invoice_allocation_evidence` materialize a bounded tagged DTO
inside Company -> requested-parent locks. AVAILABLE uses full unfiltered SQL SUM and owner
EXISTS/scalar integrity, exact applied/remaining values, SQL-filtered count and 50-row history
ordered created_at/UUID, with LIMIT/OFFSET and joined parent numbers. Corrupt off-page/filtered
records invalidate evidence. Schema checks cover explicit installation/versions/migration
coverage, exact columns/non-nullness, unique/FK structure and PostgreSQL numeric(38,8)/validated
fixed CHECK definitions. No full allocation/description payload is constructed for integrity.
UNAVAILABLE reasons have null amounts/history/count, never fabricated zero. Direct unauthorized
and foreign-Company reads fail Core authorization; parent adapters can show forbidden/disabled
optional evidence while ordinary authorized owner facts remain readable. Invalid filters are
input errors, not stale evidence; unexpected operational/database errors propagate.

### Bounded UI and verification

The optional form route is `/payments/allocations/new/`, keeping the existing safe GET Payments
navigation prefix. Parent details include a bounded evidence/history component with an authorized
allocate action, query-preserving page links, normal GET/POST fallback, Company-bound scope and
CSRF. Shared navigation behavior/assets/design remain unchanged; only header/sidebar namespace
recognition is extended to keep the existing Payments active state on the optional form.
When the app is installed, explicit optional URL composition wraps only the existing owner
detail views in a selected-alias Company read boundary, held through rendering. Ordinary owner
permissions still apply and allocation-read authority is not required to see owner facts.
This prevents an earlier draft total/line snapshot from being combined with later issued
allocation evidence. Two real PostgreSQL blocking regressions passed with both winner orders:
read-first renders the intact draft with UNAVAILABLE evidence, while edit/issue-first renders
the updated issued total and matching outstanding amount. Other owner routes are unchanged;
standalone owners import no optional integration.

Real-browser verification used a separate localhost-only Linux Docker server and disposable
two-Company fixtures, a 190-character payer, precision 8, maximum receipt amount, maximum
quantity*unit-price invoice and 52 allocations. A valid Enter submission added the 53rd fact;
invalid NaN added none. For receipt and invoice screens at 390/768/1280px, document scroll/client
widths both measured 380/758/1270px. Form scroll/client widths both measured 390/768/1280px;
all four input widths matched at each breakpoint (about 325/213/395px). Wide tables scroll locally.
Visible plum focus ring, Tab order, Enter/normal POST, validation errors, page-one 50/page-two
remaining rows, query preservation, safe GET swaps, Back/Forward, refresh and foreign-Company
404 were checked. No QA-origin JavaScript errors were captured. Server HTTP tests separately
verify non-JS normal fallback, CSRF, missing permissions/module state and stale Company forms.

All runtime tests use new disposable synthetic PostgreSQL/SQLite fixtures on Linux Docker,
Python 3.13.16, Django 5.2.17, PostgreSQL 17. No demo/customer database or target repository is
accessed. Final verification results are recorded below after completion.

Earlier provisional checks are not substituted for final evidence: an overly broad captured-SQL
test assertion was corrected to prove no InvoiceLine object construction; a LIMIT-1 assertion
was corrected to the actual bounded LIMIT 50 OFFSET 50 page; async worker connection cleanup
was fixed after a provisional PostgreSQL teardown warning; full-suite verification identified
and retained Billing's unavailable-payment wording. Final consistency probes align single-receipt
and full-history canonical receipt identity checks and reject tab/newline-padded historical keys;
neither requires an owner mutation or schema change. Original contract semantics were not relaxed.
Final browser route verification also found a missing-Company session could cause the optional
context processor to repeat the permission error while rendering the owner's 403 template.
The optional processor now returns no optional context for denied source context; six tests
cover missing/malformed/inactive Company scope on both parent routes, preserving the normal
403 page and no evidence leakage. The focused SQLite UI suite passed **34 tests**. After this
correction the browser confirmed ordinary Company selection/403 behavior and repeated all nine
parent/form breakpoint measurements above, with no QA-origin console errors.
Inherited eight npm advisories (two moderate/six high), stale Browserslist data and Actions runtime
maintenance are not upgraded or claimed resolved. SQLite cannot certify PostgreSQL's exact
wide NUMERIC arithmetic, real row locks, CHECK-catalog drift or fresh PostgreSQL topology;
explicit skips describe those actual backend limitations, not substituted concurrency proof.

No invoice issue, receipt or allocation produces an Accounting entry. No automation, refund,
reversal, external financial reconciliation, FX, mutable balance, generic integration framework,
new infrastructure, customer migration or production readiness is introduced. **STOP for
independent PAY-INT-1 audit after the single local candidate commit.**

### Final frozen-candidate verification evidence

Commands ran against the same final runtime/test files in read-only Linux QA containers with
`BUSINESSOS_INSTALL_PAYMENTS_BILLING=1`. All application databases and output were synthetic and
task-created. The two status documents alone were updated after runtime freeze.

| Check / actual command | Developer verification result |
| --- | --- |
| `pytest --ds=config.settings.development -q` | **1,536 passed**, 1,168.93 seconds, no teardown warning |
| `pytest --ds=config.settings.test -q` | **1,274 passed, 262 skipped**, 524.82 seconds |
| `pytest --ds=config.settings.development -q businessos/modules/payments/integrations/billing/tests` | **223 passed**, 553.36 seconds, no teardown warning |
| New integration PostgreSQL concurrency tests (included above) | **57 passed**, actual backend-PID blocking coordination and clean worker connections |
| `python manage.py migrate --noinput` | PASS on new zero-state `payint1_final_bootstrap`; all migrations replayed, no cycle |
| `python manage.py check` | PASS, zero issues |
| `python manage.py makemigrations --check --dry-run` | PASS, no changes detected |
| `ruff check . --no-cache` | PASS on locked Linux runtime and local Ruff 0.16.7 |
| `ruff format --check` against every changed Python path explicitly | PASS, **32 files**, including both new migrations |
| `npm ci` | PASS with locked dependencies; eight inherited advisories remain separately recorded above |
| `npm run build:css` and CSS diff/hash comparison | PASS; generated CSS remains byte-for-byte baseline |
| `node --check static/js/app-navigation.js` | PASS |
| `node --test tests/js/test_app_navigation.cjs` | **21 passed** |
| Browser final parent/form route checks | PASS at 390/768/1280px; nine measurements above, normal 403 restored, no console errors |
| `git diff --check`, strict UTF-8/fences/relative documentation links | PASS |

The SQLite skips total 262: 199 inherited backend-specific cases and 63 integration cases
(57 real row-lock races, one exact wide-NUMERIC boundary, three PostgreSQL CHECK-catalog
drift tests and two standalone PostgreSQL bootstraps). These are not claims of SQLite locking
or exact PostgreSQL monetary storage. The PostgreSQL integration suite executes all 223,
including both standalone owner backends, missing-owner failures, fresh non-default-alias
bootstrap/business/audit flows, and default-cursor-leak rejection. Full-suite owner, Accounting,
database-foundation/architecture and module-registry regressions passed within the final
1,536-test PostgreSQL suite. The superseded intermediate run was stopped only after its exact
task-created container/database was identified; it is not counted as final evidence.

Adversarial coverage includes every requested malformed/exact-numeric boundary, mismatched
Party/Currency/frozen precision, zero-total/draft Invoice, capacity races, immutable public ORM
and async APIs, idempotency retry/conflict/collision, reference retirement, audit rollback,
Company-bound HTTP/CSRF/RBAC denial, complete off-page corruption detection, and wide exact
Billing totals without materializing description/history payloads for integrity checks.

Generated CSS SHA-256:
`c6dcdd8fd62ca871bc256b08d217cd5f26321cbc96e8100fc62ac2dbe2b8f902`.
No hosted CI, publication, acceptance, canonical adoption or independent review is claimed.
After successful final checks, both task QA web-container instances were stopped/removed, and
the verified task PostgreSQL tmpfs container and its isolated network were removed. This tears
down all task-created synthetic bootstrap/UI/test databases, including interrupted provisional
fixtures; that disposable data is intentionally not retained. Agent-created browser tabs were
closed and viewport overrides reset. Existing demo databases, user servers/containers and
other worktrees were not changed or removed.

### Candidate file inventory

There are **41 candidate files**, limited to the optional app, explicit opt-in wiring, minimal
owner read-only bases, bounded presentation, focused tests and these two status documents.
The paths below are repository-relative for Git review; no additional candidate file is implied.

```text
.github/workflows/ci.yml
businessos/modules/billing/domain.py
businessos/modules/billing/selectors.py
businessos/modules/payments/selectors.py
businessos/modules/payments/integrations/__init__.py
businessos/modules/payments/integrations/billing/__init__.py
businessos/modules/payments/integrations/billing/admission.py
businessos/modules/payments/integrations/billing/apps.py
businessos/modules/payments/integrations/billing/authorization.py
businessos/modules/payments/integrations/billing/compatibility.py
businessos/modules/payments/integrations/billing/domain.py
businessos/modules/payments/integrations/billing/forms.py
businessos/modules/payments/integrations/billing/manifest.py
businessos/modules/payments/integrations/billing/migrations/__init__.py
businessos/modules/payments/integrations/billing/migrations/0001_initial.py
businessos/modules/payments/integrations/billing/migrations/0002_register_manifest.py
businessos/modules/payments/integrations/billing/models.py
businessos/modules/payments/integrations/billing/presentation.py
businessos/modules/payments/integrations/billing/selectors.py
businessos/modules/payments/integrations/billing/services.py
businessos/modules/payments/integrations/billing/tests/__init__.py
businessos/modules/payments/integrations/billing/tests/conftest.py
businessos/modules/payments/integrations/billing/tests/test_alias_installation.py
businessos/modules/payments/integrations/billing/tests/test_allocations.py
businessos/modules/payments/integrations/billing/tests/test_async.py
businessos/modules/payments/integrations/billing/tests/test_boundaries.py
businessos/modules/payments/integrations/billing/tests/test_concurrency.py
businessos/modules/payments/integrations/billing/tests/test_ui.py
businessos/modules/payments/integrations/billing/urls.py
businessos/modules/payments/integrations/billing/views.py
config/settings/base.py
config/urls.py
docs/ROADMAP.md
docs/exec-plans/active/PHASE_2_COMMERCIAL_CORE.md
templates/billing/invoice_detail.html
templates/components/header.html
templates/components/sidebar.html
templates/payments/payment_detail.html
templates/payments_billing/allocation_form.html
templates/payments_billing/evidence.html
tests/test_database_foundation.py
```

## PAY-INT-1 local corrective remediation — 2026-10-11

**HISTORICAL CORRECTIVE CHECKPOINT: LOCAL ONLY / AWAITING INDEPENDENT CORRECTIVE RE-AUDIT.
NOT PUBLISHED / NOT ACCEPTED /
NOT CANONICALLY ADOPTED.** Original candidate
`4b8a072da4426a48988d4605641bf1fc846c06ee` is preserved exactly. The supplied independent
verdict was **REVISE — PAY-INT-1 IMPLEMENTATION REQUIRES SUBSTANTIVE REDESIGN / Readiness C**.
It identified PAYINT1-R1 P1, PAYINT1-R2 P1, PAYINT1-R3 P2 and PAYINT1-R4 P2. The owner's
subsequent instruction authorizes only corrective implementation, fresh verification and one
separate local commit above that candidate. Its exact corrective SHA is reported from Git after
checks, not fabricated or self-referentially embedded here. Only a future independent corrective
auditor may close the findings; developer verification below is not acceptance.

### Corrected evidence and retry implementation

- **PAYINT1-R1 P1 — remediated locally, independent verification pending.** The selected
  PostgreSQL connection resolves actual relation OIDs from Django table metadata. Its current
  role and each relation's kind/RLS/forced-RLS flags are checked before migration/financial reads.
  Unsupported RLS for a non-superuser/non-BYPASSRLS reader makes evidence incompatible; no
  policy is guessed safe, privileged connection selected or security setting altered. The exact
  proof set is PaymentAllocation, Payment, PaymentMethod, Invoice, InvoiceLine, Party, Currency,
  Company and the migration recorder: the actual financial, provenance and coverage reads, not
  unrelated module data. A genuine nonprivileged non-RLS deployment is also verified.
- **PAYINT1-R2 P1 — remediated locally, independent verification pending.** Fourteen relied-on
  FK edges are checked by actual source/target OIDs, ordered source/target columns, validated
  state and PostgreSQL NO ACTION delete backstop (Django PROTECT remains unchanged). Missing,
  NOT VALID or incompatible constraints fail closed. Raw scoped allocation EXISTS probes reject
  either missing endpoint before joined history validation. Allocation Company and either
  endpoint's Company can bring a row into the integrity scope; malformed off-page/filtered
  facts cannot disappear. Integrity/aggregation/pagination remain SQL-bounded.
- **PAYINT1-R3 P2 — remediated locally, independent verification pending.** A found Company/key
  fact supplies authoritative stored Payment then Invoice IDs for locking and current authority
  rechecks. Only after validating that stored basis/fact is the canonical requested tuple compared.
  Valid canonical changed parents, including draft/incompatible/nonexistent UUIDs, produce
  deterministic `idempotency_conflict` without inspecting or locking those requested parents.
- **PAYINT1-R4 P2 — remediated locally, independent verification pending.** Matching retry
  validates owner financial bases, Company/Party/Currency/frozen code/precision provenance and
  exact stored amount/range/scale, including amount <= each immutable original parent capacity.
  Impossible facts fail closed without mutation/audit. This is intrinsic historical validity,
  not a new remaining-capacity check: valid 60 + 40 histories still recover the original 60 fact,
  UUID and timestamps when either/both endpoints are now fully applied.

Accepted ADR 0015, exact eight-field schema, Decimal(38,8), migrations, PROTECT references,
two permission identities, registration defaults/enablement preservation and owner/Core
contracts are unchanged. New allocation retains Company -> Payment -> Invoice/current RBAC,
atomic insertion/audit and no Accounting effects. SQLite retains explicit backend limitations;
it is not represented as proving PostgreSQL RLS, catalog, numeric or row-lock properties.

### Fresh corrective developer verification

All application data is new disposable synthetic data on the isolated Linux Docker QA network;
source is bind-mounted read-only, PostgreSQL storage is task-created tmpfs, and no demo/customer
or target database is accessed. Runtime/test files remained unchanged through the final runs.
Python 3.13.16 / Django 5.2.17 / PostgreSQL 17 are used. Commands below have
`BUSINESSOS_INSTALL_PAYMENTS_BILLING=1` unless explicitly probing a standalone topology.

| Actual check | Developer result |
| --- | --- |
| New `test_evidence_retry_integrity.py` plus `test_alias_installation.py`, PostgreSQL | **84 passed**, 104.33 seconds; 77 new R1-R4 cases plus 7 existing alias/topology cases |
| Complete integration suite, `pytest --ds=config.settings.development -q businessos/modules/payments/integrations/billing/tests` | **300 passed**, 526.72 seconds, no teardown warning |
| Existing real-blocking concurrency/security suite, included above | **57 passed**: 18 capacity, 4 keyed, 12 Company-wait revocations, 6 parent-wait authorization rechecks, 4 issue/edit, 6 HTTP admission, 4 coherent summaries, 2 parent-page snapshots, 1 rollback/response-loss |
| Full PostgreSQL, `pytest --ds=config.settings.development -q` | **1,613 passed**, 1,215.66 seconds, no skips or teardown warning; includes Billing/Payments/Accounting, Access/security, database foundation/architecture and module registry |
| Full SQLite, `pytest --ds=config.settings.test -q` | **1,297 passed, 316 skipped**, 405.79 seconds |
| Fresh `python manage.py migrate --noinput` | PASS on new `payint_remediation_bootstrap`; zero-state optional schema initialized |
| `python manage.py check`; `python manage.py makemigrations --check --dry-run` | PASS, zero issues / no changes |
| Registration replay / standalone Billing and Payments / non-default execution alias | PASS within 300 integration cases; selected-alias RLS is real and default cursor remains forbidden |
| Standalone Accounting PostgreSQL bootstrap/posting/readback | PASS using the unchanged existing standalone probe against a separate fresh synthetic database |
| `ruff check . --no-cache` | PASS, local and locked Linux runtime |
| Explicit `ruff format --check` on every baseline-to-candidate Python path, including migrations | PASS, **33 files** |
| `npm ci`; `npm run build:css`; generated CSS comparison | PASS; CSS remains byte-for-byte original. Eight inherited npm advisories (2 moderate, 6 high) remain; no dependency upgrade authorized |
| `node --check static/js/app-navigation.js`; `node --test tests/js/test_app_navigation.cjs` | PASS / **21 passed** |
| Responsive browser parent/form/unavailable/denied paths | PASS at 390 / 768 / 1280px, details below |
| `git diff --check`, strict UTF-8, balanced fences and local links/anchors | PASS |

New case counts are R1 **10** (9 actual relation RLS states and 1 supported nonprivileged
non-RLS reader), R2 **44** (14 FK edges x 3 drifts, plus either orphan endpoint), R3 **8**
canonical conflict shapes and R4 **15** (3 impossible capacities, 3 fully-applied retry shapes,
9 immutable-basis corruptions). In addition, the existing selected-alias test now reproduces
hidden RLS evidence on the non-default database without permitting default cursor access.
The 316 SQLite skips are 199 inherited plus 117 integration cases: the original 63 integration
backend limitations plus 54 new RLS/catalog/FK tests. The remaining 23 new retry cases run on
both backends. Full PostgreSQL executes those catalog and blocking cases, not simulated skips.

Browser QA used only `localhost:8022`, two synthetic Companies (the QA actor sees only its
Company), a 190-character payer and 51 initial allocation facts. Receipt/invoice document
scroll/client widths matched **380 / 758 / 1270px**, and form widths matched
**390 / 768 / 1280px**; all four form fields were aligned at each size. Initial exact summaries
showed applied 5.10 / remaining 94.90. Invalid NaN was rejected; Tab moved amount -> request key,
the plum focus ring remained visible, and Enter/normal POST added exactly one fact/audit,
showing 6.10 / 93.90. Page 1 contained 50 history rows, page 2 contained 2, query parameters
survived pagination and direct refresh. With synthetic allocation permissions withdrawn,
ordinary owner facts stayed readable but evidence was `UNAVAILABLE(forbidden)` with no fabricated
remaining amount; the action route displayed the normal access-required page. A synthetic
NOT VALID FK produced `UNAVAILABLE(incompatible)` at all sizes and a normal POST validation
error without adding a fact/audit. The fixture FK was restored afterwards. No QA JavaScript
console errors were captured. A CSRF-enforcing localhost server-client probe returned 403
without a token and retained 52 facts/52 allocation audits. Existing HTTP cases cover ordinary
non-JavaScript GET/POST, stale Company forms, permissions and module denial. No UI/assets changed.

Superseded failures are retained, not counted as passes: the initial 67-case run reported
51 fixture failures / 16 passes because PostgreSQL deferred FK triggers were pending before
test ALTER TABLE; explicitly checking pending constraints in the test harness corrected this.
An isolated first reproduction failed for that same harness reason, then the intermediate
67 cases passed before the final 77-case expansion. The first browser seed lacked integration
grants; its continuation initially used an unnormalized role code. The final fixture setup
used the persisted role and exact registered grants. A preliminary standalone CSRF probe used
disallowed `testserver` and returned 400; the corrected localhost probe verified actual 403.
The first sandboxed npm install failed registry DNS; approved official-registry access succeeded.
One preliminary JavaScript invocation used the wrong test filename; the discovered repository
path above ran all 21 tests successfully. None of these setup errors changed production code
or is substituted for final successful evidence. Inherited Browserslist/advisory warnings remain.

Corrective paths are only `compatibility.py`, `selectors.py`, `services.py`,
`tests/test_alias_installation.py`, new `tests/test_evidence_retry_integrity.py` under the optional
integration, and this plan plus `docs/ROADMAP.md`. No owner/Core code, migration, configuration,
manifest, frontend or ADR file changes. Final whitespace/documentation/ref verification passed.
The verified task web server, PostgreSQL tmpfs container and isolated network were removed,
tearing down all task-created synthetic databases/output. The cleanup guard initially stopped
on a PowerShell property-collection count; fresh network inspection and an explicit dictionary
membership check confirmed the sole task container before removal. The QA tab was closed and
viewport reset. Existing demos/user resources and other worktrees remain untouched. No hosted
CI or publication is claimed.

**STOP FOR INDEPENDENT CORRECTIVE RE-AUDIT. All four findings remain pending independent
verification; no acceptance, canonical adoption, Accounting automation or production approval.**

## PAY-INT-1 independent corrective approval and formal acceptance — 2026-10-12

This later acceptance record preserves the original REVISE and all corrective developer evidence
above. It records the owner-supplied independent review, not an audit performed by this author.

| Preserved checkpoint | Disposition |
| --- | --- |
| Canonical baseline `9ee4e0bd77350ddeef1e928e2a73b676b4cbb1ee` | PAY-INT-0 freeze, unchanged before adoption |
| Original implementation `4b8a072da4426a48988d4605641bf1fc846c06ee` | Independent REVISE / readiness C; R1 P1, R2 P1, R3 P2, R4 P2 |
| Corrective implementation `bef50fe8b20f97aaeefb8c610a46d412e9a05402` | FINAL PASS — PAY-INT-1 CORRECTIVE IMPLEMENTATION APPROVED FOR HOSTED CI; readiness A |

PAYINT1-R1 P1, PAYINT1-R2 P1, PAYINT1-R3 P2 and PAYINT1-R4 P2 are **RESOLVED**.
The supplied review reports no new actionable candidate-owned P0–P3 finding. Its fresh evidence
is **55 independent corrective/adversarial scenarios**, **57 PostgreSQL concurrency/security
tests**, **300 complete integration tests**, **1,613 full PostgreSQL tests**, **1,297 SQLite tests
with 316 classified backend-specific skips**, **33 changed Python files format-clean**, and
**21 JavaScript tests**, all passed. Fresh migrations/checks/drift and real-browser checks at
390/768/1280px passed. These are supplied independent results, not hosted CI or new local runs
performed during acceptance. The earlier full-suite tables remain developer-run evidence.

Normal publication created only `payint1-billing-payments-allocation`, preserving both audited
commits and their direct ancestry. Hosted **Phase 0 checks #118 / 38162359131 — SUCCESS**
([run](https://github.com/sahinkhan/djangobusinessos/actions/runs/38162359131)), event `push`,
checked out exactly `bef50fe8b20f97aaeefb8c610a46d412e9a05402`. Job `test` and every mandatory
step succeeded: fresh PostgreSQL migrations (including both optional-app migrations), **1,613
tests passed**, Ruff, Django checks (zero issues), migration drift (no changes), `npm ci`,
Tailwind build and generated CSS reproducibility. Inherited eight npm advisories (two moderate,
six high), stale Browserslist and Actions runtime warnings remain separate maintenance work.

**PAY-INT-1 IMPLEMENTATION: FORMALLY ACCEPTED FOR CANONICAL ADOPTION. Formal acceptance:
COMPLETE. Canonical adoption: PENDING at this acceptance checkpoint. Production readiness:
NOT CLAIMED.** Only the roadmap, this plan and ADR 0015's factual implementation-acceptance
metadata change. Its accepted PAY-INT-0 technical body/matrix and all runtime, tests, schemas,
migrations, manifests, settings and frontend assets remain unchanged.

### Canonical completion rule

This acceptance commit must pass its **own** exact-head branch push CI; implementation CI #118
cannot substitute for it. Immediately before adoption, remote main must still equal the pinned
baseline above and be an ancestor with no divergence. The authorized established flow is normal
fast-forward-only adoption and non-force main push, then a **separate** successful exact-head
main push CI. Only after all those checks succeed is this same acceptance commit the
**PAY-INT-1 CANONICAL FREEZE / CANONICALLY CLOSED** checkpoint. The adoption-pending wording then
remains historical acceptance-stage evidence. Actual later acceptance/main run IDs and freeze SHA
are reported after verification; no future CI success is fabricated or amended into this commit.

No PR, merge commit, squash, rebase, amendment, force push or extra closure commit is introduced.
No exact PAY-INT-1 checkpoint tag is specified: **NO TAG CREATED**, no release. Accounting
automation, Invoice/Payment/Allocation -> JournalEntry, refunds/reversals, settlement/FX,
Sales-to-Billing or Procurement/AP automation are **NOT STARTED / NOT AUTHORIZED**. Actual SaaS
activation and production deployment remain **NOT AUTHORIZED**; full Phase 2 is not complete.
STOP after the authorized acceptance/adoption verification; do not begin another milestone.

## PAY-INT-1 post-adoption canonical closure — 2026-10-12

**PAY-INT-1 CANONICALLY CLOSED** at `a1079985a2ef5645dfed338e3e58af54f5242e1a`.
The preceding pending statements are truthful acceptance-stage history, not current pending work.
Original implementation `4b8a072da4426a48988d4605641bf1fc846c06ee` and its independent
REVISE / readiness C remain unchanged. Corrective implementation
`bef50fe8b20f97aaeefb8c610a46d412e9a05402` received the supplied independent FINAL PASS /
readiness A. **PAYINT1-R1, PAYINT1-R2, PAYINT1-R3, PAYINT1-R4: RESOLVED**.

| Hosted Phase 0 checks | Exact checkout | Result |
| --- | --- | --- |
| [Implementation #118 / 38162359131](https://github.com/sahinkhan/djangobusinessos/actions/runs/38162359131) | `bef50fe8b20f97aaeefb8c610a46d412e9a05402` | SUCCESS; 1,613 PostgreSQL tests |
| [Acceptance #119 / 38163571737](https://github.com/sahinkhan/djangobusinessos/actions/runs/38163571737) | `a1079985a2ef5645dfed338e3e58af54f5242e1a` | SUCCESS; 1,613 PostgreSQL tests |
| [Main #120 / 38164395135](https://github.com/sahinkhan/djangobusinessos/actions/runs/38164395135) | `a1079985a2ef5645dfed338e3e58af54f5242e1a` | SUCCESS; 1,613 PostgreSQL tests |

Each run passed fresh PostgreSQL migrations, Ruff, zero-issue Django checks, no migration drift
and mandatory npm/Tailwind/generated-CSS checks. The exact acceptance SHA was adopted by normal
fast-forward, with no PR/merge commit/squash/rebase/amendment/force push. There is no specified
PAY-INT-1 tag or release. Earlier implementation-run/full SQLite/browser evidence and the supplied
independent review are separate from these hosted results. Inherited npm/Actions/Browserslist
maintenance remains unresolved and outside this gate. Source financial ownership and accepted
ADR 0015 are unchanged. This closure is not production readiness or full Phase 2 completion.

## ACC-INT-0 local proposed contract — 2026-10-12

Historical proposal checkpoint `207c78096f419b4d924326df256355a356a3f3d7`; its local verification
and then-pending statements below are retained. The later formal acceptance record supersedes them.

Branch `accint0-accounting-outcomes-contract`, exact starting canonical main
`a1079985a2ef5645dfed338e3e58af54f5242e1a`. **PROPOSED — NOT ACCEPTED / NOT PUBLISHED**.
Only this plan, the roadmap and new
[ADR 0016](../../decisions/0016-accounting-commercial-outcomes-integration-contract.md) change.
Accepted ADRs 0011/0013/0014/0015 and all runtime, test, schema, migration, permission, manifest,
settings and frontend files remain untouched.

The reviewable contract chooses:

- `accounting_billing -> accounting, billing`, independent of Payments;
  `accounting_payments_billing -> accounting, accounting_billing, payments_billing`, requiring a
  valid posted invoice Accounting binding and the same AR account before allocation posting.
- Exactly two positive effects: owner Invoice original total -> Dr AR / Cr Revenue; owner
  Allocation.amount -> Dr Cash/Bank / Cr AR. No automatic effect on issue/receipt/allocation.
- Explicit Journal/Account UUIDs and type/activity validation, not a mapping configuration engine;
  effect-specific immutable protected bindings with database source/effect uniqueness.
- Source-derived date/Party/memo, exact base-currency identity and representability at source and
  ACC-1-created Entry precision. Zero invoice -> NO_ACCOUNTING_EFFECT without journal/binding/audit.
- Atomic composition of existing public Accounting create/add-line/post services plus binding/
  integration audit, Company-first post-wait authority and existing owner lock order. Proposed
  bounded public read-only source/posted-basis APIs are future additions, not claimed present APIs.
- Complete schema-qualified evidence admission, RLS/policy rejection, fixed validated FK/CHECK/
  migration profile, intrinsic historical retry validation, and truthful tagged status. Ordinary
  supported row writers are serialized; concurrent policy/privilege maintenance requires drain.
- Exact compound permissions and HTTP-only serialized registry admission, installed Python
  context/RBAC independence, bounded future status/action/link UI and I01–I21 acceptance matrix.

Independent ACC-INT-0 architecture audit is required next. This is the final currently proposed
Accounting composition gate before a later Phase 2 completion review, subject to audit identifying
any prerequisite gap. No acceptance, hosted candidate CI or future runtime test is claimed.
**ACC-INT-1 NOT STARTED / NOT AUTHORIZED. PHASE 2 NOT COMPLETE. PHASE 3 NOT AUTHORIZED.**
Other integrations, corrections/reversals, SaaS and production deployment remain separately gated.
One local docs-only proposed-contract commit is authorized, then STOP; no push/PR/merge/tag.

### ACC-INT-0 local documentation verification

Executed 2026-10-12 against this documentation candidate, not future ACC-INT-1 behavior:

| Check / exact command | Actual result |
| --- | --- |
| `ruff check . --no-cache` (host `.venv/Scripts/ruff.exe`, Ruff 0.16.7) | PASS; all checks passed |
| `python manage.py check --settings=config.settings.test` | PASS; zero issues |
| `python manage.py makemigrations --check --dry-run --settings=config.settings.test` | PASS; no changes detected |
| `pytest tests/test_database_architecture.py tests/test_modules.py --ds=config.settings.test -q -p no:cacheprovider --basetemp=/tmp/accint0-pytest` | PASS; 231 passed in 13.89s |
| Inline read-only PowerShell validation of the three candidate documents | PASS; strict UTF-8, balanced fences, 33 local links/anchors and 16 consistently shaped tables |
| `git diff --check` | PASS; no whitespace errors |

Python/Django checks ran in the existing Linux Docker QA image `ui-gate1-qa-web`, Python 3.13.16 /
Django 5.2.17, with the source bind-mounted read-only, `--network none`, a read-only container root,
temporary `/tmp` test storage and `--rm`. `config.settings.test` and
`BUSINESSOS_INSTALL_PAYMENTS_BILLING=1` exercised the installed canonical PAY-INT profile.
No adopted/demo/customer database or customer-migration preparation worktree was modified.
No new PostgreSQL full-suite, browser, npm/Tailwind or future integration test result is claimed;
those unchanged runtime checks were not rerun for a documentation-only candidate. Prior hosted
PAY-INT-1 results above remain separate evidence. Independent ACC-INT-0 audit is still pending.

## ACC-INT-0 independent approval and formal acceptance — 2026-10-12

Exact audited proposal `207c78096f419b4d924326df256355a356a3f3d7`, canonical parent
`a1079985a2ef5645dfed338e3e58af54f5242e1a`, branch `accint0-accounting-outcomes-contract`.
Supplied independent verdict **FINAL PASS — ACC-INT-0 CONTRACT APPROVED FOR FORMAL ACCEPTANCE**,
readiness **A**, **no candidate-owned P0/P1/P2/P3**. This is supplied independent evidence, not
self-audit. Inherited non-blocking **ACCINT0-DOC-1 P3** is retained as separately bounded
maintenance; BASELINE, MODULE_BOUNDARIES, DEPENDENCY_MAP and ADR 0011 are not modified.

Hosted **Phase 0 checks #125 / 38203841663 — SUCCESS**
([run](https://github.com/sahinkhan/djangobusinessos/actions/runs/38203841663)), event `push`,
checked out the exact audited proposal on its branch. **1,613 PostgreSQL tests passed**;
fresh migrations, Ruff, zero-issue Django checks, no migration drift, npm/Tailwind and generated
CSS reproducibility all passed. Eight inherited npm advisories (two moderate, six high),
Actions/Node deprecation and outdated Browserslist warnings remain outside this acceptance scope.

ADR 0016 is **Accepted — Gate ACC-INT-0**, preserving all ten independent conclusions:

1. Two Accounting-owned opt-in apps, invoice posting independent of Payments.
2. Allocation integration hard-dependency on `accounting_billing` for this contract.
3. Explicit Journal/Account UUID selection.
4. AR/Cash ASSET semantic limitation; no invented control-account or bank certification.
5. Immutable `Payment.payment_date` for allocation-posting date.
6. Zero-total `NO_ACCOUNTING_EFFECT`, no persistent binding.
7. Source/effect binding architecture concurrency-safe by contract.
8. Existing Accounting public services sufficient for future atomic composition.
9. Incomplete/hidden evidence cannot certify `NOT_POSTED`.
10. Precise enough for separately authorized ACC-INT-1; implementation readiness A.

**Formal acceptance: COMPLETE. Canonical adoption: PENDING at this acceptance checkpoint.**
Only this plan, the roadmap and ADR 0016 status/evidence change. Audited technical design, effect
shapes, ownership, account/unit/date/Party/zero rules, immutable binding identity, retry, complete
evidence, RLS/FK compatibility, lock order, four future permission codes and I01–I21 remain unchanged.
No runtime/test/schema/migration/settings/manifest/frontend changes, new permission or ADR 0011/
0013/0014/0015 semantic change. Historical proposal, PAY-INT-1 failures/remediation and verification
remain preserved. Ordinary CRUD, customer-migration preparation, demos and historical refs remain
untouched.

This acceptance commit requires NEW exact-head branch push CI; proposal CI is not substituted.
After success, fetch/revalidate canonical main still equals the pinned parent, verify no divergence,
and use the authorized no-PR/direct fast-forward normal push. Separate exact-head main push CI
must then succeed. Only that completed sequence makes this same acceptance commit **ACC-INT-0
CANONICALLY CLOSED / CANONICAL FREEZE**. Adoption-pending wording then remains acceptance-stage
evidence; actual acceptance/main run IDs and freeze SHA are reported from verified results rather
than invented before execution. No extra closure commit, amend, squash, rebase, merge commit or
force push. No exact checkpoint tag name is specified: **NO TAG CREATED**, no GitHub release.

**ACC-INT-1 NOT STARTED / NOT AUTHORIZED. Accounting automation runtime NOT STARTED.
PHASE 2 NOT COMPLETE; final completion review NOT YET PERFORMED. PHASE 3 NOT AUTHORIZED.
SaaS activation and production deployment NOT AUTHORIZED; production readiness NOT CLAIMED.**
STOP after publication/adoption verification; no next milestone begins here.

## ACC-INT-1 original local implementation verification — 2026-10-12

Historical checkpoint preserved for original candidate
`5bfc055b1fb6c2b806a4f4bbf04fc749cc9020fe`. The later independent audit returned
**REVISE — Readiness B**, with **ACCINT1-AUD-1 — P2 candidate-owned**. The original checks below
do not establish corrective approval; the current remediation record follows this history.

**LOCAL IMPLEMENTATION CANDIDATE / AWAITING INDEPENDENT AUDIT. NOT PUBLISHED / NOT ACCEPTED /
NOT CANONICALLY ADOPTED.** Branch `accint1-accounting-outcomes`, canonical parent
`4419bdc4f0210894065400923741dd5449ffd158`. The candidate is the single local implementation
commit containing this record; its exact SHA is frozen and reported after committing. This is
developer verification, not independent audit, hosted CI, formal acceptance or canonical adoption.
**ACC-INT-0 CANONICALLY CLOSED. PHASE 2 NOT COMPLETE. PHASE 3 NOT AUTHORIZED.** Earlier
acceptance-stage statements above retain their historical meaning.

Two Accounting-owned opt-in apps implement explicit Invoice AR/Revenue and Allocation Cash/AR
posting through public owner services, protected immutable source/effect bindings, atomic audit
composition, intrinsic retries, complete-evidence admission and bounded company-scoped UI.
Accepted ADR 0016, Core, owner financial semantics and released owner migrations are unchanged.

Verification used disposable synthetic PostgreSQL 17 and SQLite databases with all three
integration installation flags enabled. Source was mounted read-only into the verification
containers. The final full PostgreSQL run was serial and used development settings plus the
existing project test-only `django.contrib.auth.hashers.MD5PasswordHasher` from
`config.settings.test`, set in an external disposable settings module. Production repository
password-hasher configuration was not changed. The runner module contained only:

```python
from config.settings.development import *
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
```

| Local check | Actual result |
|---|---|
| Full PostgreSQL suite, serial disposable test settings | **2,530 passed; zero failures, zero skips** |
| ACC-INT-1 tests included in that full run | **917 passed**, including 228 actual PostgreSQL concurrency cases and 442 schema/security profile cases |
| Full supported SQLite suite | **1,525 passed; 1,005 backend-only skips**: 482 actual PostgreSQL lock cases, 502 catalog/DDL/RLS/security cases, 8 exact numeric cases, 13 fresh PostgreSQL bootstrap cases |
| Installation topology / selected execution alias | **22 topology cases plus one complete fresh non-default alias case passed**; unsupported combinations rejected, default cursor forbidden, both effects/status/retries/rollback/audit verified |
| Ruff / formatting | `ruff check . --no-cache` PASS; all **56 changed Python files**, including new migrations, pass `ruff format --check` |
| Django / migration drift | `manage.py check` PASS with zero issues; `makemigrations --check --dry-run` reports no changes |
| JavaScript / Tailwind | Node syntax check PASS; **21 JavaScript tests passed**; `npm ci` and Tailwind build PASS; generated CSS reproduced byte-for-byte |
| Browser | Synthetic normal POST, prerequisite/zero/denied/unavailable/rejected/posted states, backdated Payment allocation, keyboard GET filter and refresh verified; exact 38-digit money and long labels at **390/768/1280** with local table scrolling and no page overflow; console clear |

An earlier four-worker PostgreSQL run ended with 2,528 passes and two lock-observation timeout
failures. Both cases passed a serial recheck with normal development hashers, and both also
passed the final complete serial run above. An intervening normal-hasher serial run was explicitly
stopped after 322 passing cases to switch the disposable runner to the existing test-only hasher;
it is partial evidence, not a full-suite pass. Earlier test-harness defects (worker updates outside
atomic transactions and an uppercase Billing draft literal) were corrected before the final runs.
Eight inherited npm advisories (two moderate, six high) and the outdated Browserslist warning
remain; dependencies were not changed by this scope.

All required source/cross-effect winner orders, authority/reference/read rechecks after waits,
hidden/RLS and NOT VALID FK/CHECK evidence, corrupt/orphan provenance, zero-effect attacks,
composition failure points and HTTP module/RBAC/CSRF/stale-Company cases passed. One local
`feat: implement ACC-INT-1 accounting outcomes` commit is authorized, then STOP for independent
audit. Publication, PR, merge, tag, acceptance, canonical adoption and next-phase work remain gated.

## ACC-INT-1 owner-basis corrective remediation — 2026-10-13

The following is preserved **historical implementation-stage evidence**. Its local-remediation/
pending language describes the corrective checkpoint before independent re-audit and publication;
the [later formal acceptance record](#acc-int-1-independent-corrective-approval-and-formal-implementation-acceptance--2026-10-13)
supersedes that status without changing the recorded failures, corrections or verification results.

**LOCAL REMEDIATION / INDEPENDENT CORRECTIVE RE-AUDIT PENDING.** Preserved original candidate:
`5bfc055b1fb6c2b806a4f4bbf04fc749cc9020fe`; original parent and unchanged main/origin-main:
`4419bdc4f0210894065400923741dd5449ffd158`. The supplied independent implementation audit
returned **REVISE — Readiness B**, with exactly one candidate-owned blocker,
**ACCINT1-AUD-1 — P2: public owner-basis APIs could certify RLS-filtered incomplete financial
evidence**. This corrective commit's exact SHA is frozen and reported after committing; its
parent must be the preserved original candidate. Developer evidence marks the finding
**REMEDIATED LOCALLY — INDEPENDENT VERIFICATION PENDING**, not independently resolved.

Billing and Accounting now establish selected-alias owner evidence admission inside each
public basis transaction before financial reads. Billing inspects Invoice, InvoiceLine, Company,
Party, Currency and migration provenance. Accounting inspects Entry, EntryLine, Journal, Account,
Company, Party, Currency and migration provenance. Helpers remain inside their respective owner
modules, with no optional-integration import or new Core abstraction. Original financial
arithmetic, BusinessContext/company/RBAC checks and authorization rechecks after waits remain.
No models, migrations, accepted ADRs, settings, presentation files or financial authority changed.

PostgreSQL admission validates actual metadata-derived relation identities/OIDs, supported
ordinary public tables and search-path resolution, exact canonical column and PK/UNIQUE/CHECK
facts, critical validated FK targets/actions, and exact required owner migration history. It
rejects any relevant RLS flag, FORCE RLS flag or policy, including a policy on a disabled table
and privileged executions. It does not evaluate arbitrary policies or change aliases/roles/RLS.
Unrelated Catalog RLS and another owner's migration history do not disable an owner certificate.
Bounded catalog values are parameterized. Verified relation identifiers are quoted, acquired in
OID order with ACCESS SHARE and rechecked; strong DDL remains blocked through the transaction.
As in ADR 0016, weak policy/privilege/migration maintenance requires operator drain; this is not a
claim of serializing arbitrary live security maintenance. SQLite admits its pinned owner schema
with enabled FK enforcement and no shadow/attached namespace. Unsupported evidence raises
owner ValidationError(code="incompatible"), never a partial/zero certificate or presentation DTO.

Direct native reproductions initially failed against the original runtime: complete Invoice
41.37 became visible 20.00, and complete four-line balanced Entry 46.37 became a visible balanced
two-line subset 41.37 under an actual non-superuser/non-BYPASSRLS role. Corrected APIs reject both
RLS states. The owner explicitly clarified the four-line control: preserve ADR 0016's exactly
two-line posted-basis restriction, reject the complete four-line Entry and certify a separate
valid two-line 41.37 Entry. Supported ordinary, superuser, BYPASSRLS and owner executions certify
the valid controls only without relevant RLS/policies. Real role attributes and visible row
counts/totals are asserted; no financial mutations/audits result from certification.

Verification uses owned disposable PostgreSQL 17, SQLite and Node containers, synthetic data,
read-only source mounts and the same external test-only password-hasher runner documented in
the original checkpoint. Fresh non-default aliases trap every default cursor and exercise both
direct APIs. Strong-DDL probes hold Company before financial reads, prove the owner reader holds
the relation proof lock, then verify completion and rejection after DDL commits. Fresh topology
probes now call the direct APIs in standalone Billing, standalone Accounting and combined owners
without ACC-INT, while retaining absence-of-optional-import assertions.

| Corrective local check | Actual result |
|---|---|
| Full PostgreSQL suite, serial disposable test settings | **2,755 passed; zero failures, zero skips** in 1,819.20 seconds; includes all 1,142 ACC-INT cases and all 225 focused corrective cases |
| Complete ACC-INT integration suite | **1,142 passed; zero failures, zero skips**; includes **225 focused corrective direct-owner cases** |
| ACC-INT concurrency / schema-security | **230 concurrency cases passed** (198 original concurrency + 30 extra concurrency + two new owner strong-DDL cases); **663 schema/security/direct-owner compatibility cases passed** (442 existing profile + 221 new direct-owner RLS/schema/control cases); two additional new selected-alias cases passed |
| Fresh bootstrap / installation topology | **22 existing topology cases passed**, including Billing standalone, Accounting standalone, combined owners without ACC-INT and full topology; existing fresh integration alias plus **two new direct-owner fresh aliases** passed with default-cursor traps |
| Full supported SQLite suite | **1,525 passed; 1,230 classified skips**: 484 actual PostgreSQL lock cases, 723 catalog/DDL/RLS/security/direct-owner compatibility cases, 8 exact numeric cases, 15 fresh PostgreSQL bootstrap/alias cases |
| Ruff / canonical-base formatting | `ruff check . --no-cache` PASS; **59 changed Python files**, original migrations included, pass `ruff format --check`; no whitespace errors |
| Fresh migrations / Django / migration drift | Fresh full-topology migration PASS; `manage.py check` zero issues; `makemigrations --check --dry-run` no changes |
| JavaScript / Tailwind / CSS | Node syntax PASS; **21 JavaScript tests passed**; `npm ci`, Tailwind build and byte-identical generated CSS PASS; no frontend changes |
| Targeted real Chrome smoke | Invoice Posted **USD 41.37**, Allocation Posted **USD 10.00** and Entry links verified; relevant RLS shows Invoice **Accounting evidence unavailable**, removes allocation links and rejects the direct Allocation endpoint; restoring disposable metadata restores Posted |

The SQLite increase is exactly **225 new PostgreSQL-only cases**: 221 direct owner compatibility/
RLS/schema/control cases, two selected-alias cases and two strong-DDL concurrency cases. Skips
are backend capability limits, not missing execution on PostgreSQL. All npm advisories and the
Browserslist warning remain inherited; no dependency maintenance or hosted CI is claimed.
No deadlock or connection-health failures occurred. Verification source checksums were unchanged
through the full run. The completed complete ACC-INT run was 1,518.21 seconds; the SQLite run was
648.40 seconds. Real browser console was clear. Remote main was read with
`git ls-remote`, remaining at the canonical base; no final fetch/ref mutation was needed.

Exactly one local `fix: harden ACC-INT-1 owner evidence bases` commit is authorized above the
preserved original candidate, then STOP. **NOT PUBLISHED / NOT ACCEPTED / NOT CANONICALLY
ADOPTED. PHASE 2 NOT COMPLETE. PHASE 3 NOT AUTHORIZED.** A fresh independent corrective auditor
must verify the new exact SHA before closing ACCINT1-AUD-1; this implementation session does not
perform that independent audit.

## ACC-INT-1 independent corrective approval and formal implementation acceptance — 2026-10-13

Frozen history, preserved without amendment or reconstruction:

| Checkpoint | Exact identity / decision |
|---|---|
| Canonical ACC-INT-0 starting base | `4419bdc4f0210894065400923741dd5449ffd158` |
| Original ACC-INT-1 implementation | `5bfc055b1fb6c2b806a4f4bbf04fc749cc9020fe` — independent **REVISE / Readiness B** |
| Original blocker | **ACCINT1-AUD-1 — P2**: direct owner-basis APIs could certify RLS-filtered incomplete evidence |
| Corrective implementation | `2c7c8109f875909b34cc089698cb6d7dde572266`, directly above the original implementation |
| Supplied independent corrective verdict | **FINAL PASS — ACC-INT-1 CORRECTIVE IMPLEMENTATION APPROVED FOR HOSTED CI / Readiness A** |
| Finding disposition | **ACCINT1-AUD-1 independently RESOLVED**; no new actionable candidate-owned P0/P1/P2/P3 findings |
| Verified hosted implementation CI | **Phase 0 checks #128 / 38365702656 — SUCCESS**, `push`, `accint1-accounting-outcomes`, exact corrective SHA |

The supplied independent review reproduced the original RLS failure and verified both owner
bases and the unchanged ADR 0016 exactly-two-line rule. Its evidence includes **225 focused
corrective cases**, **1,142 ACC-INT cases**, **230 concurrency cases**, **663 schema/security/direct
compatibility cases**, **22 topology cases**, **59 changed Python files format-clean**, **21
JavaScript tests** and browser verification. Supplied independent full-suite results are **2,755
PostgreSQL passed / zero failures or skips** and **1,525 SQLite passed / 1,230 classified skips**.
These are supplied independent evidence, not an independent audit performed by this acceptance
session. The separate developer full-suite results in the preceding remediation record retain
their implementation-run provenance; unchanged full local suites were not rerun for acceptance.

The newly verified hosted [candidate run #128 / 38365702656](https://github.com/sahinkhan/djangobusinessos/actions/runs/38365702656)
checked out exactly `2c7c8109f875909b34cc089698cb6d7dde572266`, applied fresh PostgreSQL migrations,
collected **2,755 tests** and passed all **2,755** in **1,859.58 seconds**. Ruff, Django checks (zero
issues), migration drift (no changes), npm install, Tailwind build and byte-identical generated
CSS all passed. The configured hosted workflow has no separate JavaScript syntax/test step;
the 21 JavaScript tests above are independent/local evidence, not a hosted result. Eight inherited
npm advisories (two moderate, six high), Actions/Node deprecation and outdated Browserslist
warnings remain separately governed maintenance; no dependency correction is claimed here.

**ACC-INT-1 IMPLEMENTATION: FORMALLY ACCEPTED FOR CANONICAL ADOPTION. Formal acceptance
COMPLETE; canonical adoption PENDING at this acceptance checkpoint.** Only this plan, the
roadmap and ADR 0016 status/evidence metadata change. Both audited implementation commits,
all runtime/tests/migrations/frontend, accepted technical semantics and I01–I21 remain unchanged.

This single docs-only acceptance commit requires its own exact-head branch push CI. Revalidate
unchanged main `4419bdc4f0210894065400923741dd5449ffd158` and straight ancestry before the
authorized direct fast-forward/no-PR normal push; require separate exact-head main push CI.
Only verified success of all gates makes **this same acceptance commit** the **ACC-INT-1
canonical freeze / CANONICALLY CLOSED** checkpoint. Its acceptance-stage pending wording then
remains historical evidence. Actual acceptance/main run IDs and freeze SHA are reported from
verified results, not invented before the runs exist. No extra closure commit, amendment, PR,
merge commit, squash, rebase, force push, tag or GitHub release is authorized or created.
No exact ACC-INT-1 checkpoint tag is specified: **NO TAG CREATED**.

**PHASE 2 NOT COMPLETE; final completion audit NOT YET PERFORMED. PHASE 3 NOT AUTHORIZED.
SaaS activation and production deployment NOT AUTHORIZED; production readiness NOT CLAIMED.**
STOP after canonical publication/adoption verification; do not begin another milestone.

## PH2-FINAL-AUD-1 late-authorization corrective candidate — 2026-10-13

This is a separately authorized **local implementation/remediation record**, not independent
re-audit, publication, formal acceptance, Phase 2 closure, or Phase 3 authorization. The final
Phase 2 audit returned **REVISE / Readiness C**, with **PH2-FINAL-AUD-1 P1** blocking and
**PH2-FINAL-DOC-1 P3** nonblocking. Earlier implementation/audit/acceptance records above remain
historical evidence and are not rewritten.

### A–D: integrity, root cause, final guard and supported writers

Starting checkout, local `main` and fetched `origin/main` were clean at
`669936df432ec1bb12792ed8d31741fbb1b1287a`, ACC-INT-1 canonical freeze. Main CI #130 attempt 1
encountered the previously reported synthetic-policy/autovacuum deadlock; the separately
authorized failed-job rerun, #130 attempt 2, succeeded with **2,755 PostgreSQL tests** at the
same SHA. That prior hosted evidence is not hosted verification of this corrective candidate.
Only local `phase2-final-authorization-remediation` was created directly from that canonical
parent. No publication, tag, history reconstruction, or main update is authorized.

Source inspection confirmed the nine supplied counterexamples: initial authorization followed
Company locking, but a later Order/Movement/Currency/Journal/Party lock could wait while actor or
Permission activity changed. Resuming code reused the earlier decision through effect/audit or
successful retry. Another unlocked policy query alone would leave a check-to-commit window.

The small Access policy `require_final_permission` requires the selected business transaction
and the caller's held active Company lock. After domain/reference waits, it takes PostgreSQL
**FOR SHARE** on the actor User, exact registered Permission, then one qualifying same-company
Role witness (candidate UUID order), and rechecks current context/activity/grants. A committed
retirement before these locks denies; an operation winning these locks holds authority stable
through its outer commit. Shared rather than exclusive authority locks allow nested owner calls
and different-company readers to share an actor/Permission without a lock upgrade. The helper
is not an authorization cache or replacement for Company locking. SQLite executes ordinary
policy validation without claiming PostgreSQL row-lock concurrency guarantees.

All SQL locks and policy reads use ADR 0012's selected/pinned execution alias. Successful guards
outside an atomic transaction are rejected. Savepoint collision recovery is guarded again before
return; initial guards are outside insertion savepoints so insertion rollback does not drop their
authority locks. No earlier authorization is reused after an owner-operation failure.

Supported-path inspection, not an assumption about every possible ORM statement:

| Authority fact / path | Existing serialization and this correction |
|---|---|
| Actor activity/superuser state | Identity validated save/queryset update and technical User admin need no Company lock; actor shared lock now protects these facts through business commit |
| Exact Permission existence/activity | Validated save/queryset activity update can occur independently of Company; exact Permission shared lock protects retirement/deletion. Manifest registration only get-or-creates and preserves retirement; Core registration updates names, not activity |
| Role activity | Validated Role save/queryset activity changes need no Company lock; lock and revalidate a qualifying Role witness rather than assuming Company alone protects its activity |
| RolePermission / UserRoleAssignment / Company, Branch and Warehouse grants | All 11 supported audited Access mutation services acquire Company before current policy and mutation; this protocol is unchanged. ADR 0009 and inspection-only Access admin do not support direct unaudited link/assignment/grant mutations as application APIs |
| Company activity | Ordinary UPDATE conflicts with the already-held Company row lock |
| Branch/Warehouse activity and ownership | Validated saves take Company before Branch/Warehouse; queryset ownership/activity bypasses are already rejected. Existing context checks remain unchanged |
| Arbitrary privilege / transaction composition | No claim of serialization against privileged SQL, private persistence misuse, unaudited grant edits, arbitrary multi-company outer transactions, or arbitrary mixed-order multi-row administrative transactions. Existing single-company services and same-company optional compositions retain their contracts |

No Core model, permission vocabulary, ordinary CRUD policy, manifest, schema, migration, settings,
financial rule or integration contract is changed. Activity anchors do not lock grant-child rows
in reverse order against supported Company-first Access writers. Actor/Permission/Role writer
statements need not adopt a new framework: their existing PostgreSQL UPDATE locks contend with
the held shared rows. No global mutex, advisory lock, generic lock framework or new infrastructure.

### E–L: six-owner sweep, final boundaries and retries

Every standalone public mutation was inspected and exercised at the final boundary. **41 public
services: 37 C (later aggregate/reference/FK wait, corrected), 4 A (no later aggregate/shared
reference wait, still guarded), 0 B (already-safe final guard before this correction).** A/C below
classify the pre-correction paths, not an assertion that C remains vulnerable.

| Owner | Complete public mutation inventory / baseline classification | Final boundary |
|---|---|---|
| Sales (7 C) | `create_sales_order`, `update_sales_order`, `add_sales_order_line`, `update_sales_order_line`, `remove_sales_order_line`, `confirm_sales_order`, `cancel_sales_order` | Order, affected line and required Party/Currency/Variant locks before final guard; new FK references cannot introduce a late reference wait after authority anchors |
| Procurement (8 C) | `create_purchase_order`, `update_purchase_order`, `add_purchase_order_line`, `update_purchase_order_line`, `remove_purchase_order_line`, `confirm_purchase_order`, `cancel_purchase_order`, `receive_purchase_order` | Order/line/reference locks before final guard; receipt lines lock in UUID order; matching/collision receipt recovery reauthorized |
| Inventory (1 A, 5 C) | A: `create_stock_movement`; C: `update_stock_movement`, `add_stock_movement_line`, `update_stock_movement_line`, `remove_stock_movement_line`, `post_stock_movement` | Movement/affected line, Variant, route Warehouses and new-line UoM FK locks before guard; posted retry guarded |
| Billing (6 C) | `create_invoice`, `update_invoice`, `add_invoice_line`, `update_invoice_line`, `remove_invoice_line`, `issue_invoice` | Existing Invoice/line/Party/Currency locks precede final guard; issued retry and true no-ops reauthorized |
| Payments (1 A, 3 C) | A: `create_payment_method`; C: `update_payment_method`, `set_payment_method_active`, `record_payment` | Method/Party/Currency or historical Payment lock before guard; existing-key and uniqueness-collision recovery guarded |
| Accounting (2 A, 8 C) | A: `create_account`, `create_journal`; C: `update_account`, `update_journal`, `create_journal_entry`, `update_journal_entry`, `add_journal_entry_line`, `update_journal_entry_line`, `remove_journal_entry_line`, `post_journal_entry` | Entry/Journal/line/ordered Account/Party locks before guard; reference updates, no-ops and posted retry guarded |

The additional reference acquisition is service-local and precedes final authority. In particular,
new Sales/Procurement Currency FKs and Inventory line UoM FKs must not defer their first conflicting
reference wait until after actor locking. Variant/nullable Warehouse joins lock only their own
row (`of=("self",)`), not unrelated joined Product/Branch rows. Existing business eligibility,
immutable snapshots, arithmetic, source-of-truth and retry payload/conflict semantics are retained.

Sales confirms/cancels without stock or invoices; Procurement receipts do not create stock;
Inventory remains posted movement-line derived; Billing retains frozen once-only HALF_UP totals;
Payments retains immutable exact receipts; Accounting retains exact balanced base-currency entries.
Each final guard precedes authoritative persistence/success audit or an authorized retry/no-op.
Retries do not duplicate timestamps, effects or audits. PAY-INT/ACC-INT are not redesigned.

### M–O: new deterministic security/concurrency evidence

Final focused PostgreSQL execution: **122 passed, 0 failed, 0 skipped in 300.20 seconds**.
Worker connections close in `finally`; real `pg_blocking_pids` observations coordinate waits.
Polling delays only poll the database lock graph and are not elapsed-time race evidence.

| New group | Actual focused result |
|---|---|
| All public mutation final-boundary rollback | 41 passed; late actor denial leaves every persisted owner field and all audit rows unchanged |
| Original counterexamples + reference/FK waits | 12 passed: all nine supplied failures now deny with no effect/success audit, plus Sales create/Currency, Procurement create/Currency and Inventory line/UoM waits |
| Permission / Role activity during six-module domain waits | 12 passed |
| Operation wins before activity retirement | 18 passed: six owners x actor/Permission/Role; observed retirement wait, one committed effect/audit, then retirement completes |
| Company-first supported revocation / Company retirement | 6 passed: role, role-permission, Company access, Company, Branch grant and Warehouse grant |
| Matching retry while historical/aggregate row waits | 18 passed: nine retry paths x actor/Permission retirement; historical rows/audits remain intact |
| Successful matching retry / immediate revoked retry | 9 passed, unchanged UUID/state/audit on match |
| Direct Core / sharing / selected alias | 6 passed: transaction precondition, all three authority-row waits, concurrent shared actor/Permission across Companies, fresh PostgreSQL non-default alias with default-cursor trap and same actor UUID but independent activity/permission facts |

The new PostgreSQL-only subset is **71 tests**; **51** of the new tests also execute on SQLite.
Fresh selected-alias bootstrap is inside a separate synthetic PostgreSQL database. No default
cursor fallback, cross-alias activity borrowing, deadlock or worker connection teardown warning
occurred in the final focused run.

### P–U: verification record

Final full-suite execution is complete. These are fresh **implementation-run** results, not
independent re-audit or hosted candidate CI:

| Final mandatory gate | Actual result |
|---|---|
| Full PostgreSQL 17 | **2,877 passed / 0 failed / 0 skipped, 2,589.53 seconds (43m 09.53s)**; all 2,755 baseline tests plus 122 new tests |
| Full supported SQLite | **1,576 passed / 0 failed / 1,301 classified skips, 952.99 seconds (15m 52.99s)**; 51 new supported tests and 71 new PostgreSQL-only skips |
| Existing Core / six-module security/concurrency / PAY-INT / ACC-INT | All passed freshly within the full PostgreSQL run, including existing owner evidence, RLS/schema, retry/collision, composition, concurrency and read-path revocation regressions; no separate subset runtime is invented |
| Bootstrap / aliases / architecture | Fresh full-topology bootstrap, all existing optional/standalone topology and database/module-registry/permission/dependency guards passed; new fresh PostgreSQL selected-alias/default-cursor-trap case passed |
| Quality | `ruff check . --no-cache` PASS; explicit `ruff format --check` on all eight changed Python files PASS; Django zero issues, migration drift no changes, `git diff --check` PASS |
| Frontend | Node 22.23.3 syntax, 21 JS tests, npm install, Tailwind build and byte-identical CSS PASS; no frontend file changed |
| Connection/deadlock health | No full-suite teardown warning; no `deadlock detected` in the isolated task PostgreSQL server logs |

SQLite's 1,301 skips comprise **554 actual PostgreSQL lock tests, 723 catalog/DDL/RLS/security
tests, 8 exact numeric tests and 16 PostgreSQL bootstrap/alias tests**. The increase over the
baseline's 1,230 is exactly 70 lock-coordination tests plus one new PostgreSQL alias test, not
unexplained regressions. No PostgreSQL test was skipped to obtain a pass.

Already completed on the final runtime logic:

- Python **3.13.16**, Django **5.2.17**, PostgreSQL **17.11**; isolated task-owned Linux containers
  and newly created synthetic databases. PostgreSQL test-only external settings use the existing
  synthetic MD5 password hasher convention; source settings are unchanged.
- Fresh empty full-topology PostgreSQL migrations PASS; `manage.py check` zero issues;
  `makemigrations --check --dry-run` no changes. No migration is created/edited.
- Node **22.23.3**: `npm ci`, `node --check static/js/app-navigation.js`, all **21 JS tests**,
  `npm run build:css` and byte-identical generated CSS PASS in temporary container storage.
  Frontend source is mounted read-only. Eight inherited npm advisories (2 moderate, 6 high) and
  outdated Browserslist remain separately scoped maintenance.

Development verification history is retained: the first new focused harness run was **80 passed /
3 failed** (missing Core permission bootstrap after flush and wrong revoke-service argument), then
the corrected expanded draft passed **119**. The final reference-lock coverage passed **122**.
Early full-suite runners were deliberately stopped before the reference-lock refinement; those
partial runs are not PASS evidence. The first temporary CSS comparison identified a new Python
comment token interpreted as a Tailwind utility; replacing that comment word restored exact CSS
without any frontend edit or runtime-semantic change. Final full suites use the final runtime/test
logic; only that comment-only token correction and this documentation record changed afterward.

### V–X: candidate boundary and stop condition

Intended candidate files only: `businessos/core/access/policies.py`; the six standalone
`businessos/modules/{sales,procurement,inventory,billing,payments,accounting}/services.py` files;
`tests/test_final_authorization.py`; this active Phase 2 plan. Eight changed Python files require
explicit Ruff format checks. No other tracked file, model, migration, frontend, settings, registry
or integration code is authorized. Final commit SHA is reported after creating the single local
commit, rather than inventing a self-referential SHA in this record.

Current status: **PH2-FINAL-AUD-1 REMEDIATED LOCALLY — INDEPENDENT VERIFICATION PENDING**;
**PHASE 2 AUTHORIZATION CORRECTIVE CANDIDATE READY FOR INDEPENDENT RE-AUDIT**.
**PH2-FINAL-DOC-1 remains OPEN**, nonblocking and untouched (BASELINE, DEPENDENCY_MAP and ADR 0010
header are not normalized). **PHASE 2 NOT COMPLETE; PHASE 2 FINAL CLOSURE NOT AUTHORIZED;
PHASE 3 NOT AUTHORIZED.** After all mandatory checks, exactly one local corrective commit with
parent `669936df432ec1bb12792ed8d31741fbb1b1287a` is permitted; then STOP for independent re-audit.

## PH2-AUTH-CORR-1 second corrective implementation notes — 2026-10-13

### Design recorded before runtime edits

Starting branch `phase2-final-authorization-remediation` is clean at first corrective
`2fbd4a2ae02eda31c6273456a2599b0a2f90339a`, directly above canonical
`669936df432ec1bb12792ed8d31741fbb1b1287a`. The supplied independent re-audit is
**REVISE / Readiness B**: the original nine races individually deny, but exact-Permission / one-Role
locking can accumulate anchors in opposite order to supported batch activity writers during nested
Accounting composition. The previous exclusion of arbitrary administrative batching does not
exclude these supported `update` / `bulk_update` APIs. First-candidate evidence above is historical.

Proposed bounded protocol:

1. Retain active Company -> domain/reference facts before final authority. Company-first audited
   Access services continue to stabilize assignment/link/organizational-grant membership.
2. Share-lock the actor, then every assigned same-company Role, including inactive Roles, ordered
   by UUID. Then share-lock every Permission reachable through those Roles, including inactive
   Permissions, ordered by UUID. Re-read the exact requested policy after all waits. Nested owner
   calls resolve the same complete set, not a new per-action witness. Do not cache an approval.
3. For superusers, lock the Permission relation in PostgreSQL SHARE mode before enumerating and
   UUID-locking every declared Permission. This prevents newly registered identities from expanding
   the namespace mid-transaction. It is a normal database relation lock, not an advisory/global
   process mutex. Permission writers take ROW EXCLUSIVE relation mode before row prelocking,
   matching ordinary PostgreSQL UPDATE/INSERT; it cannot wait for a reader while holding rows.
4. Permission and Role queryset `update`, `bulk_update` (whole call, before batching), and deletion
   resolve actual target UUIDs on `queryset.db`, prelock those rows in UUID order, then execute the
   mutation over the fixed target set in the same alias-aware transaction. Do not rely on UPDATE's
   heap/index scan order. Instance deletion routes through that same guarded deletion protocol.
   Existing immutable-field rejection and allowed activity/name semantics stay unchanged.
5. Core permission registration is the existing multi-statement authority writer: collect label
   corrections and apply one ordered bulk update, rather than accumulate per-code row locks.
   Manifest registration only creates missing identities and preserves existing activity.
6. Actor activity writes contend on the actor row. Role writers do not acquire actor/Permission
   locks; Permission writers do not acquire Role/Company locks. Role deletion locks parent Roles
   before cascading assignment/link deletion; Permission deletion retains Django PROTECT. Scoped
   Access writers take Company before Role/link/grant mutations, so they cannot change the held
   actor/company graph concurrently. Ordinary CRUD authorization semantics are not expanded.
7. Require real transactions for lock primitives. Released nested savepoints retain locks until
   outer commit. A rolled-back first acquisition is not cached: the next call must reacquire the
   complete set and recheck. Test outer-held anchors across inner rollback and reauthorization
   after first-acquisition rollback explicitly.

Production composition inventory: Accounting's invoice and allocation outcome services both call
`evidence.compose`: public create Entry -> two public add Line calls -> public post Entry. These
need create/update/post permissions in one outer transaction and prelock existing Journal/Accounts/
Party/Currency before those calls. PAY-INT composes owner read-only bases, not multiple owner
mutations. Party/Catalog/demo setup has multiple operations but no Phase 2 RBAC final guard or
financial-posting orchestration. No other production transaction calls different Phase 2 owner
mutations. Same-company direct public-owner composition is covered by the complete authority set.

Planned evidence: real PostgreSQL blocking for both batch winners, Permission/Role update/bulk/
delete, two planner configurations, invoice/allocation effects/retries/rollback, savepoints,
superuser namespace and fresh non-default alias. Preserve/re-run the original 122 cases and full
mandatory suites. Only developer evidence may be recorded; independent acceptance is pending.
`PH2-FINAL-DOC-1` stays OPEN. No schema/migration, publication, main change, Phase 2 closure or
Phase 3 work is authorized.

### Implemented protocol and focused evidence

The final reader uses fixed-UUID `ORDER BY id FOR SHARE` set queries, rather than one round trip
per authority row. Actor, all assigned same-company Roles and all reachable Permissions retain
the recorded type/UUID order. Missing rows fail closed; every invocation rechecks current policy.
The private reader and writer locking primitives themselves reject calls outside a transaction.
No connection-level approval/lock cache is introduced. Superusers stabilize all declared identities
with the recorded Permission SHARE relation lock; Permission writers take ROW EXCLUSIVE before
UUID row prelocking. Role/Permission model deletion uses the same alias-aware queryset protocol.

Only three production files change in this second correction: Core Access `policies.py`,
`models.py`, and the registration batching in `services.py`. All six standalone final-boundary
placements from the first corrective commit, optional integration code, ordinary CRUD decision
rules, permission vocabulary, schemas, migrations, settings and frontend remain unchanged.

Final focused PostgreSQL command:

```text
python -m pytest tests/test_final_authorization.py tests/test_authority_batches.py -q
  --ds=qa_settings --junitxml=/tmp/focused-ordered-final.xml
```

**182 passed / 0 failed / 0 skipped in 489.38 seconds**: the original 122 cases plus 60 new cases.
This is developer execution evidence, not independent re-audit or hosted CI.

| New regression group | Final focused result |
|---|---|
| Permission/Role batch update and bulk_update | 32 passed: both writer/business winners, heap and index planner settings, public invoice and allocation posting; batch_size=1 still prelocks the complete set |
| Role batch deletion | 8 passed: both winners, both planners and both public effects; confirmed effects/history/audit survive the later authority deletion |
| Writer target ordering | 6 passed: update/bulk_update/delete over reverse-ordered targets; actual prelock UUID order observed; assigned Permission deletion still raises Django PROTECT |
| Instance deletion | 2 passed: ordinary Permission/Role deletion enters the ordered transactional writer protocol |
| Nested savepoints | 2 passed: outer-acquired anchors survive inner rollback; first acquisition rolled back is reacquired and revoked authority denied on the next guard |
| Inactive authority closure | 1 passed: inactive assigned Roles/reachable Permissions are included, and repeated complete sets are sorted |
| Superuser namespace | 3 passed: update, successful unlinked batch deletion and registration block before writer rows while the declared namespace is held |
| Core registration | 1 passed: two label corrections use one complete writer set and preserve explicit retirement |
| Private transaction precondition | 1 passed: actor/set reader and writer primitives reject autocommit invocation |
| Public composition rollback/retry | 2 passed: Invoice AR/Revenue and Allocation Cash/AR, exact AR prerequisite, injected posting-audit rollback and unchanged authorized retry |
| Fresh selected alias | 2 passed: separate PostgreSQL zero-state migrations, matching source UUIDs, default-cursor trap, update/bulk_update/delete, observed writer wait and independent default authority |

The 32 activity cases explain the **actual UPDATE SQL executed by Django**, under forced sequential
and index-capable planner settings. UUIDs deliberately oppose code-index order. Explicit ordered
prelocking, not the physical UPDATE scan, establishes the result. Every race uses worker Events
and observed `pg_blocking_pids`; no sleep is accepted as evidence of a race. Worker connections
close in `finally`. Public posting assertions verify the exact financial lines, stored prerequisite
and immutable Payment date; later revoked retries deny without effect/audit changes.

Original evidence remains freshly covered: **9/9 supplied counterexamples deny with zero committed
unauthorized effect/audit; all 18 opposite single-authority winners pass; all 41 standalone final
boundaries pass; all existing matching/no-op retries pass.** ACCINT1-AUD-1 is not reopened or
redesigned by this correction.

Final supported SQLite execution: **1,583 passed / 0 failed / 1,354 classified skips in 851.29
seconds**. New tests contribute **7 passes and 53 skips**: 51 actual PostgreSQL locking cases and
2 fresh PostgreSQL alias cases. Case-level XML classification across the full suite is **603
row-lock cases, 725 catalog/DDL/RLS/provenance cases, 8 exact-numeric cases, and 18 fresh bootstrap/
alias cases**. The earlier first-candidate category labels above are historical: two direct
RLS-hidden owner-evidence cases belong in RLS, not locking. Full totals are unchanged by that
classification correction; no unexpected skip is used to obtain a pass.

Verification history is retained: early new-harness execution passed 57, then the combined draft
passed 181 in 556.05 seconds. The executed-UPDATE planner refinement passed 181 in 550.75 seconds.
The final set-query/private-transaction version passed 182 as recorded above. Earlier partial full
runners were stopped before those refinements and are not PASS evidence. An unnecessary restart
of the completed final SQLite runner was immediately stopped; its retained XML and original
complete console result certify the 851.29-second run, not that aborted rerun. No source was changed
by runner control. Final complete PostgreSQL evidence is recorded below after completion.

### Final complete verification and exit-matrix evidence

Final complete PostgreSQL command:

```text
python -m pytest -q --ds=qa_settings --junitxml=/tmp/full-postgres.xml
```

**2,937 passed / 0 failed / 0 skipped in 2,713.58 seconds (45m 13.58s)**, on Python **3.13.16**,
Django **5.2.17**, PostgreSQL **17.11**. This includes all 2,877 first-candidate cases and 60 new
cases. Final runtime/test files were unchanged during both complete runs; only this evidence
documentation was completed afterward. The external synthetic-only QA settings select the existing
MD5 fixture hasher; source settings remain untouched. All three approved optional apps are opted in.
Full supported SQLite used `python -m pytest -q --ds=config.settings.test
--junitxml=/tmp/full-sqlite.xml` with the same optional topology.

Fresh complete suite results extracted from the final PostgreSQL XML, not inherited results:

| Defined complete group | Passed |
|---|---:|
| Core/foundation/database | 408 |
| Sales | 98 |
| Procurement | 115 |
| Inventory | 80 |
| Billing | 104 |
| Payments | 136 |
| Accounting | 304 |
| PAY-INT | 300 |
| ACC-INT | 1,142 |
| First corrective regression file | 122 |
| Second corrective regression file | 60 |
| Defined complete Core / six-owner / both-integration / corrective bundle | 2,869 |

Core here means complete `tests/test_{access,admin,core_foundation_v1,database_architecture,
database_foundation,foundation_correctness,identity,modules,organization}.py` files. The six owner
groups are their complete `tests/` directories; both integration groups are their complete test
directories. The 2,869-case bundle is deliberately broader than the supplied independent audit's
875-case selected bundle; it is not a claim that the same selection grew to 2,869. These groups ran
freshly inside the complete PostgreSQL invocation; no separate subset wall-clock time is invented.
All original counterexamples, opposite winners, retry/no-op, same-source/cross-effect composition,
owner evidence/RLS/constraint/schema checks and selected-alias tests passed.

Other final checks:

- Fresh empty full-topology PostgreSQL migrations PASS; database architecture, standalone/optional
  topology and fresh selected-alias/default-cursor-trap regressions PASS. `manage.py check` reports
  zero issues; `makemigrations --check --dry-run` reports no changes after the final code refinement.
- Ruff **0.16.7** `ruff check . --no-cache` PASS. Explicit `ruff format --check` covers **all 11
  changed Python files across the complete two-commit series**, including paths normally excluded
  by Ruff discovery if any existed (no migration changed). Whitespace checks PASS.
- Node **22.23.3**: `npm ci`, JS syntax, all **21 JS tests**, `npm run build:css` and byte-identical
  compiled CSS PASS after the final runtime refinement. No frontend file changes. Eight inherited
  npm advisories (2 moderate, 6 high) and stale Browserslist remain separately scoped maintenance.
- Final full test database and fresh alias databases were removed by normal teardown; only the two
  task-created base databases remained before container cleanup. No synthetic test role remained;
  only the task database owner and built-in roles existed. No worker connection warning or
  `deadlock detected` occurred in the task PostgreSQL log. Unrelated containers/databases were not
  touched. Task-created containers, network, anonymous database storage and copied XML outputs are
  removed after evidence inspection; no customer or demo database was accessed.

The supplied previous independent re-audit had **11 PASS / 2 FAIL / 0 NOT PROVEN**; criteria 1 and
13 failed, and criterion 10 passed. The following updates are **developer evidence ready for
independent verification**, not a new independent verdict or permission to close Phase 2:

| Criterion | Current developer evidence / outstanding gate |
|---|---|
| 1. Six standalone architectures | All 41 placements, original nine denials, 18 opposite winners and complete suites pass; new ordered-reader/batch-writer composition tests pass. Independent second corrective review still required |
| 2. Company isolation | Complete six-owner/Core suites and fresh independent-alias UUID/default-cursor cases pass; Company-first Access protocol unchanged |
| 3. Concrete ProductVariant identity | Owning models/services unchanged; complete Sales/Procurement/Inventory regressions pass |
| 4. Posted movement stock source | Inventory ledger/balance contract unchanged; complete Inventory regressions pass |
| 5. Balanced posted-line Accounting source | Accounting/ACC-INT suites and exact new AR/Revenue, Cash/AR assertions pass; no authoritative balance added |
| 6. Frozen Billing / derived settlement | Billing, Payments and PAY-INT complete suites pass; owner amount/basis contracts unchanged |
| 7. Immutable history | Guarded owner ORM/history suites pass; authority deletion cannot erase committed financial effects |
| 8. Retry safety | Nine original matching/no-op paths, new public integration rollback/retry and complete Accounting/Inventory/ACC-INT collision/race suites pass |
| 9. Public optional composition / dependency direction | Only `evidence.compose`'s two current public-owner compositions found; complete topology/dependency guards pass; no private owner write or reverse import added |
| 10. Module registry semantics | Prior independent PASS preserved; complete module/HTTP tests and 21 JS tests pass, installed Python service RBAC unaffected |
| 11. PostgreSQL / quality / drift | 2,937 PostgreSQL passes, zero failures/skips; complete SQLite and mandatory quality/bootstrap checks pass |
| 12. No speculative framework | Only Access-local row/set ordering and writer batching; no schema, generic lock framework, advisory lock, mutex, infrastructure or new model |
| 13. Explicit architecture acceptance | STILL PENDING: the second exact local corrective SHA needs fresh independent re-audit and separately authorized final closure; developer tests do not supply acceptance |

Final local candidate scope: `businessos/core/access/{models,policies,services}.py`,
`tests/test_authority_batches.py`, and this active plan, exactly five files. The first corrective
commit `2fbd4a2ae02eda31c6273456a2599b0a2f90339a` remains unchanged. Exactly one additional local
commit, `fix: order Phase 2 authority locks`, is authorized after verification; its exact SHA is
reported externally to avoid a self-referential commit hash. Canonical local/remote main remains
`669936df432ec1bb12792ed8d31741fbb1b1287a`.

**PHASE 2 AUTHORIZATION SECOND CORRECTIVE CANDIDATE READY FOR INDEPENDENT RE-AUDIT.**
**PH2-FINAL-AUD-1: ORIGINAL NINE RACES REMAIN REMEDIATED LOCALLY.**
**PH2-AUTH-CORR-1: REMEDIATED LOCALLY — INDEPENDENT VERIFICATION PENDING.**
**PH2-FINAL-DOC-1: OPEN — NONBLOCKING DOCUMENTATION MAINTENANCE.** BASELINE, DEPENDENCY_MAP and
ADR 0010 are not normalized. **PHASE 2 NOT COMPLETE; PHASE 2 FINAL CLOSURE NOT AUTHORIZED;
PHASE 3 NOT AUTHORIZED.** No push, PR, merge, tag, main update or earlier-commit amendment; STOP
after the single local commit for a fresh independent re-audit.

## PH2-AUTH2-AUD-1 third corrective implementation — 2026-10-14

Starting clean branch `phase2-final-authorization-remediation` is at second corrective
`368dc70aa7bdcefd3191661b4569ccfad29f4069`, with unchanged parents
`2fbd4a2ae02eda31c6273456a2599b0a2f90339a` and
`669936df432ec1bb12792ed8d31741fbb1b1287a`. Local main, origin/main and read-only live remote
main verification match that canonical parent. Supplied independent second-candidate audit:
**REVISE / Readiness B**. PH2-FINAL-AUD-1 and ACCINT1-AUD-1 are independently resolved; original
batch cases pass, but PH2-AUTH-CORR-1 cannot close while PH2-AUTH2-AUD-1 remains. The prior local
results above are preserved as historical evidence, not sufficient evidence for this correction.

### Installed Django analysis and bounded protocol

Inspection of installed Django **5.2.17** `QuerySet.update_or_create` confirms: set `_for_write`,
enter `atomic(using=self.db)`, call `select_for_update().get_or_create`, resolve update defaults,
then `obj.save(using=self.db, update_fields=...)`. On an existing row, FOR UPDATE precedes UPDATE's
ROW EXCLUSIVE relation lock. Against the superuser Permission SHARE namespace lock this can form
the reported relation/row cycle. A save-level fix would be too late.

The Permission-only override sets the write-routing flag, resolves `self.db`, enters
`business_atomic_context(using=alias)`, obtains PostgreSQL Permission ROW EXCLUSIVE, and delegates
unchanged defaults/create_defaults/lookup arguments to Django. That relation lock lasts through
the enclosing transaction. No row is selected first. SQLite retains Django behavior within the
alias-aware transaction without PostgreSQL LOCK syntax. No exception is swallowed. Superuser
namespace stabilization, ordinary complete authority sets, Role ordering and financial code stay
unchanged. No migration, new authorization rule or framework is introduced.

### Complete inspected Permission writer surface

| API / owner | Relation intent before Permission row? | Correction / alias evidence |
|---|---|---|
| `create`, instance `save` (also inherited `acreate`/`asave`) | Ordinary INSERT/UPDATE obtains ROW EXCLUSIVE before modifying rows; `full_clean` does not take row locks | No change; normal validated save and existing execution/explicit alias rules |
| queryset `update` / `aupdate` | Existing ordered writer obtains ROW EXCLUSIVE before fixed UUID prelocks | Retained; queryset.db |
| `bulk_update` / `abulk_update` | Existing whole-call prelock obtains relation intent before all batches | Retained; queryset.db; identity-code rewrite rejected |
| queryset `delete` / `adelete`, instance `delete` / `adelete` | Existing guarded deletion routes through relation-first ordered targets | Retained; queryset/instance-selected alias, PROTECT retained |
| `get_or_create` / `aget_or_create` | Existing-row path only reads; absent path INSERT obtains write intent before rows | No override needed; inherited method does not modify a found row |
| `update_or_create` | Inherited existing-row FOR UPDATE previously preceded relation write intent | Corrected at method entry before inherited row selection; queryset.db write routing |
| `aupdate_or_create` | Installed Django uses `sync_to_async(self.update_or_create)` | Inherits corrected override; no redundant async implementation |
| Core permission registration | get-or-create fixed declarations, one ordered label bulk update | Existing second correction retained; explicit retirement preserved |
| Module registration | get-or-create missing declarations, preserve existing records | No change; selected execution alias |
| Bulk create/conflict upsert | Explicitly rejected by existing model contract | Still rejected; no mutation |
| Admin / Access application services | Access admin inspection-only; services read Permission and write Company-first grant/link/Role facts, not Permission activity | No hidden Permission row-lock-then-save production path found |
| Explicit `select_for_update` chaining | A read alone, including existing-row chained get-or-create, does not subsequently request write intent | No production/documented Permission row-lock-then-save sequence found; arbitrary caller-built transactions are not newly certified. Any future such writer must obtain relation intent before its first row lock |

Search covered Core Access, registry, production module code and documentation, including aliases
and model-variable `select_for_update` uses. Existing integration test `test_extra_concurrency`
locks Invoice/Payment/JournalEntry before retiring Permission, not a Permission row. No supported
repository writer is excluded to avoid this finding. The override preserves `create_defaults`,
callables, returned `(object, created)`, validation, identity immutability and transaction errors.

### Verification scope

New tests use real PostgreSQL wait edges, Permission relation modes, and an assertion that the
winning backend has no reverse blocking edge. Business-first upsert must not even reach the
Permission FOR UPDATE statement while namespace SHARE is held. Writer-first business must wait
on namespace SHARE after upsert owns write intent. Both historical potential detector/victim
configurations use swapped 100ms/5s deadlock detector settings; assertions prove the acyclic graph,
not just absence of a randomly selected victim. Ordinary role actors, public invoice 41.37 and
allocation 17.25 composition, retirement denial, authorized/revoked retries, async delegation,
same-code insertion races, savepoints and fresh alias/default-cursor traps are included.

Only disposable synthetic PostgreSQL databases and read-only source-mounted QA runners are used.
The task PostgreSQL 17 container disables autovacuum to avoid unrelated synthetic DDL-policy versus
autovacuum races already recorded for canonical CI #130; application relation/row locks and both
deadlock detectors remain real. This is test-harness configuration, not source settings or runtime
deployment change. Final results and cleanup are recorded below after execution.

PH2-FINAL-DOC-1 remains OPEN — P3 NONBLOCKING; BASELINE, DEPENDENCY_MAP and ADR 0010 untouched.
Independent third-candidate re-audit is still required. No Phase 2 closure or Phase 3 authorization.

Verification history: the first new-suite run produced **2 passed / 43 failed in 316.78s**.
The disposable Debian cluster used `en_US.utf8`, whose constraint text ordering disagrees with the
fixed Accounting evidence profile. Diagnostic catalog comparison established that mismatch; the
new task cluster is initialized with `--locale=C --encoding=UTF8`, matching the pinned profile.
Two new-test fixture issues were also corrected: fresh alias role assignment needs Company access
even for a superuser, and duplicate-primary-key model creation is rejected by existing full_clean
before a database IntegrityError. A separate injected persistence IntegrityError proves propagation
and clean rollback. No accepted profile or model validation was weakened. An accidental restart of
the failed runner for diagnostics was stopped; that partial rerun is not pass evidence. The failed
cluster and its task-owned volume were removed before the C-locale runs. The runtime override also
preserves Django's `alters_data` marker. Final verification uses the finalized tests, including
explicit once-only owner/integration success-audit assertions.

### Finalized focused developer evidence

```text
python -m pytest tests/test_final_authorization.py tests/test_authority_batches.py
  tests/test_permission_upserts.py -q --ds=qa_settings --junitxml=/tmp/focused-final.xml
```

**227 passed / 0 failed / 0 skipped in 943.94 seconds (15m 43.94s)**, including the original
122, second-corrective 60 and third-corrective 45. The separate new-suite prototype on the
corrected C-locale setup passed 45 in 288.03s before final audit-count assertions; the combined
227 run uses those finalized assertions. A focused SQLite check of the finalized new file passed
**2 / 0 failed / 43 skipped in 36.84s**. These are implementation-run results, not independent audit.

| Third-corrective group | PostgreSQL result / objective evidence |
|---|---|
| Upsert versus public invoice/allocation | 32 passed: both winners, both activity outcomes, superuser/ordinary actor, both detector orders; relation mode and directed wait graph verified |
| Defaults and transactions | 1 passed: create_defaults/update defaults/callables, inactive-to-active, labels, autocommit/nested transaction, immutable code, validation and propagated persistence error; no leaked failed transaction |
| Async delegation | 1 passed: real inherited async create/update reaches the synchronous override; connection cleanup; Django alters_data retained |
| Same absent code race | 1 passed: both validations precede real concurrent INSERTs, one unique-key collision is recovered by Django, one identity, created True/False, no duplicate or swallowed unexpected error |
| Other namespace writers | 4 passed: create, save, get-or-create insertion and upsert insertion wait for ROW EXCLUSIVE before any Permission row-lock query |
| Savepoints | 2 passed: first acquisition rollback permits business progress; outer-held intent survives inner rollback and business waits until outer commit |
| Fresh selected alias | 4 passed: zero-state migrations, both winner orders for both effects, same actor/company/Permission UUIDs and codes in independent databases, default connection traps, unchanged default authority |

Exact authorized effects: Dr AR / Cr Revenue **41.37** and Dr Cash / Cr AR **17.25**; matching
invoice-posting AR prerequisite and immutable Payment.payment_date verified. Exactly one owner
posting audit and integration creation audit; authorized retry returns the same result with identical
stored effects/audit. Revoked retry denies; writer-first retirement commits no financial effect or
success audit. Real worker connections close in finally blocks. All prior Permission/Role batch
planner variants, both winners, original nine denials, 18 opposite winners, 41 final placements,
registration-preserves-retirement and rollback/retry cases freshly pass in the same invocation.

The first full supported SQLite invocation completed with **1,584 passed / 1 failed / 1,397
skipped in 1,376.20s**. Failure:
`businessos/modules/accounting/integrations/tests/test_http.py::test_complete_action_rbac[get-allocation-accounting.entry.post]`.
The fixture's invoice posting failed before revocation/HTTP assertions, at unchanged
`evidence.validate_posting`'s `posted_at <= binding.created_at <= binding.updated_at` check.
The three actual timestamp values were not captured in that first traceback. The exact isolated
test passed unchanged on a fresh SQLite database (**1 passed in 18.94s**). A separate direct Docker
wall-clock probe observed **45,169,027 samples / zero backward observations over 20s**; that does
not prove the earlier run's clock state. No Accounting validation, tests or timestamp policy was
changed or bypassed. Root cause is not yet proven; the full unchanged SQLite suite is rerun with
`--showlocals`. This failure remains visible as a verification concern, not silently discarded.

The full unchanged SQLite rerun completed with **1,585 passed / 0 failed / 1,397 skipped in
918.79s** using `python -m pytest -q --ds=config.settings.test --showlocals
--junitxml=/tmp/full-sqlite.xml`. All skips are explicitly PostgreSQL-specific: 642 real-lock
cases, 725 catalog/DDL/RLS cases, 8 exact-numeric cases and 22 fresh-alias/bootstrap cases.
The third correction adds 39 lock cases and four fresh-alias cases to those categories; its
two portable tests pass. A successful rerun does not explain or erase the original timestamp
failure. Candidate freeze remains blocked pending its disposition; no financial code/test
remediation or timestamp-policy change is authorized in this task.

Final quality commands: `ruff check . --no-cache` passes; explicit `ruff format --check` for
all 12 Python paths changed across the canonical-to-second-corrective history plus the new
third-corrective test file passes, including explicitly supplied paths rather than relying on
discovery. Both working-tree `git diff --check` and canonical-to-HEAD whitespace checks pass.
Fresh C-locale PostgreSQL full-topology `migrate --noinput`, Django `check` and
`makemigrations --check --dry-run` pass (zero issues / no changes). No migration was added or
modified. A temporary frontend copy passes `npm ci`, `node --check static/js/app-navigation.js`,
`node --test tests/js/test_app_navigation.cjs` (**21 passed**) and `npm run build:css`; regenerated
CSS is byte-identical. npm reports **eight inherited advisories (two moderate, six high)** and
the existing Browserslist age notice remains; neither dependencies nor frontend files changed.

### Full PostgreSQL result, integrity and stop condition

`python -m pytest -q --ds=qa_settings --junitxml=/tmp/full-postgres.xml` completed with
**2,982 passed / 0 failed / 0 skipped in 3,427.33s (57m 07.33s)** on Python **3.13.16**,
Django **5.2.17**, PostgreSQL **17.11**, Linux Docker, C-locale UTF-8. The finalized code/test
fingerprints below are unchanged across the focused and full runs.

| Complete group within the full run | Passed |
|---|---:|
| Core/foundation/database | 408 |
| Sales | 98 |
| Procurement | 115 |
| Inventory | 80 |
| Billing | 104 |
| Payments | 136 |
| Accounting | 304 |
| PAY-INT | 300 |
| ACC-INT | 1,142 |
| Original corrective | 122 |
| Second corrective | 60 |
| Third corrective | 45 |
| Other repository tests | 68 |
| **Total** | **2,982** |

Fresh topology/bootstrap, dependency/architecture guards, company/module isolation, independent
execution-alias cases, original deadlock/collision/RLS/provenance coverage and all corrective
tests pass in that run. Post-run PostgreSQL inspection found only task base databases `auth3`
and `auth3_full` plus PostgreSQL defaults; only the synthetic owner beyond builtin roles; no
other client sessions. No `deadlock detected` or test-database-in-use warnings appeared in the
task-cluster logs. All task-prefixed runners, the private network and verified task PostgreSQL
volume were removed after evidence collection. Existing demos and other task resources were
not removed. Inert XML test evidence remains outside the repository in the task QA directory.

| Working-tree file | SHA-256 of verified content |
|---|---|
| `businessos/core/access/models.py` | `9efb18b5703195ba62808713f24b24ff9f7f018a63ef7ec49b6eb75211f18aca` |
| `tests/test_permission_upserts.py` | `840a66964e041e5f69f6424f5facde6e4d0d6674be6ff40ecdd0c5df2088b63e` |

**BLOCKED — third corrective candidate freeze withheld.** The requested upsert correction and
its focused/full PostgreSQL verification are implemented, but the first SQLite timestamp failure
remains unexplained despite the unchanged isolated/full reruns passing. The owner's requirement
that unexplained failures block freeze is retained. No third corrective commit was created;
`PHASE2_AUTH_CORRECTIVE_3_SHA` is not assigned. Exactly three pending files remain: Access models,
the new upsert test file, and this plan. No financial/timestamp remediation was attempted.

HEAD remains `368dc70aa7bdcefd3191661b4569ccfad29f4069`; its first-corrective and canonical parents
remain unchanged. Local main, origin/main and live remote main remain
`669936df432ec1bb12792ed8d31741fbb1b1287a`. No staging, push, PR, merge, tag, amendment, rebase or
main update. The independent findings/history are preserved; these developer results do not
self-approve this pending implementation or supply independent closure. Further timestamp
investigation/disposition needs a separately bounded decision before candidate freeze.
PH2-FINAL-DOC-1 stays OPEN / P3 NONBLOCKING. Phase 2 is NOT COMPLETE; final closure and Phase 3
remain NOT AUTHORIZED.

### Subsequent bounded investigations and owner-authorized local freeze — 2026-10-14

The blocked checkpoint immediately above remains historical evidence. The owner subsequently
authorized finalizing only the existing third authorization correction after the following
bounded investigations and governance disposition. This is not independent third-candidate
approval, publication, canonical adoption or Phase 2 closure. The original SQLite failure and
all earlier failed attempts remain recorded; neither successful reruns nor synthetic injection
establish the cause of that historical failure.

Read-only SQLite investigation, with unchanged runtime/test fingerprints: 100 fresh-process
executions of the exact case passed on each of the dirty third-corrective candidate, canonical
`669936df432ec1bb12792ed8d31741fbb1b1287a`, and second corrective
`368dc70aa7bdcefd3191661b4569ccfad29f4069`. Repeated current RBAC matrices passed 190 cases;
current/canonical HTTP modules passed 174/116 cases. Predecessor, upsert, Accounting and
timestamp-manipulation order probes did not reproduce the original failure. Two additional
full unchanged current SQLite runs each passed **1,585 / 0 failed / 1,397 skipped**, in
1,747.03s and 1,749.99s; the canonical control passed **1,525 / 0 failed / 1,230 skipped** in
1,576.66s. These are diagnostic execution results, not independent acceptance. Initial external
telemetry assumed a model rather than a possible DTO; affected runners were stopped and excluded,
the external logger was corrected, and affected groups were rerun. No repository code changed.

A separate native Docker clock probe observed backward wall-clock movements of 2,841 and
3,540 microseconds while monotonic time advanced. No failed posting was captured crossing those
events. Therefore the original historical SQLite failure remains **CAUSE NOT PROVEN / NOT PROVEN
CLOCK-CAUSED**; those observations alone did not establish its attribution.

#### PH2-CLOCK-1 — inherited Accounting wall-clock causal-order sensitivity

**DEMONSTRATED ON CANONICAL; SEPARATE REMEDIATION REQUIRED; NOT CAUSED BY THIRD AUTHORIZATION
CORRECTION.** A further owner-authorized external canonical-source experiment used unchanged
`669936df432ec1bb12792ed8d31741fbb1b1287a` and disposable SQLite/PostgreSQL **17.11** databases.
The original exact test passed normally on each backend. Context-scoped clock instrumentation
then supplied `posted_at = T`, binding `created_at = T - 1ms`, and
`updated_at = T - 1ms + 1us`. The first tested step, **1ms**, reproduced the same
`evidence.validate_posting` timestamp-order failure on both backends; no larger step was needed.
This is the smallest tested reproducing step, not a measured absolute minimum or a reconstruction
of the original host clock adjustment.

Both direct Invoice and Allocation compositions reproduced the invariant failure. A second
sequence, `created_at = T + 1ms` followed by `updated_at = T`, also failed the same validator.
The error was `ValidationError("Accounting posting evidence is intrinsically incompatible.")`,
with no explicit error code, at `evidence.py:179-180` via `_bad()`. Normal controls preserved
Dr AR / Cr Revenue **41.37** and Dr Cash / Cr AR **17.25**. The final direct matrix passed
**6 diagnostic tests per backend**, including expected injected exceptions, rollback of
entry/line/binding/audit state, restoration of each clock patch, and ordinary unpatched
same-source posting after each failure. The original exact case also passed unpatched after
injection on both backends. Allocation's separately imported validator reference was explicitly
instrumented in the final matrix to capture its timestamp triple and traceback.

Classification: **INHERITED PRODUCT DEFECT / CLOCK-SENSITIVITY DEMONSTRATED**, an
application-wall-clock ordering sensitivity rather than a SQLite-only conversion issue.
Canonical code predates and does not contain the pending Permission upsert correction, so this
demonstration does not causally implicate that correction. The sensitivity is proven; attribution
of the original historical failure remains **NOT PROVEN**. Observed failure behavior is rejection
and atomic rollback, not demonstrated financial corruption. No tolerance, retry, timestamp policy,
Accounting model/service/evidence/history code, migration or ADR technical semantics was changed.
Task-created diagnostic containers/databases/networks were removed; inert external evidence remains
in the `sqlite_timestamp_investigation` and `clock_sensitivity` diagnostic directories.

#### Third authorization candidate finalization boundary

The owner explicitly dispositions the prior blocker separately as PH2-CLOCK-1 and authorizes
exactly one local third-corrective commit, `fix: serialize Permission upserts`, retaining the
verified Access runtime and upsert-test fingerprints above. The commit contains only
`businessos/core/access/models.py`, `tests/test_permission_upserts.py`, and this plan. Its parent
must be `368dc70aa7bdcefd3191661b4569ccfad29f4069`, preceded by
`2fbd4a2ae02eda31c6273456a2599b0a2f90339a` and canonical
`669936df432ec1bb12792ed8d31741fbb1b1287a`. The new
`PHASE2_AUTH_CORRECTIVE_3_SHA` is reported externally after commit, avoiding a self-referential hash.
Final narrow checks passed on Python **3.13.16** / Ruff **0.16.7** in a disposable Docker runner
with the source mounted read-only, all three optional integrations enabled, and
`DJANGO_SETTINGS_MODULE=config.settings.test` (disposable in-memory SQLite, no existing database):

- `ruff check businessos/core/access/models.py tests/test_permission_upserts.py --no-cache`:
  all checks passed.
- `ruff format --check --no-cache businessos/core/access/models.py tests/test_permission_upserts.py`:
  two files already formatted; no formatting writes.
- `python manage.py check`: zero issues.
- `python manage.py makemigrations --check --dry-run`: no changes detected.
- `git diff --check`: passed; runtime/test SHA-256 fingerprints remain exactly as recorded above.

Broad suites are not rerun for this unchanged implementation. Existing focused **227**, full PostgreSQL
**2,982**, PAY-INT **300**, ACC-INT **1,142**, and quality/bootstrap/frontend results above remain
developer verification evidence, not a new independent audit or newly executed full suite.

| Current item | Disposition at local candidate freeze |
|---|---|
| PH2-FINAL-AUD-1 | REMAINS REMEDIATED LOCALLY |
| PH2-AUTH-CORR-1 | ORIGINAL BATCH CYCLES REMAIN REMEDIATED LOCALLY |
| PH2-AUTH2-AUD-1 | REMEDIATED LOCALLY — INDEPENDENT VERIFICATION PENDING |
| PH2-CLOCK-1 | INHERITED PRODUCT DEFECT — CANONICAL CLOCK SENSITIVITY DEMONSTRATED; separate remediation required |
| Original SQLite failure attribution | NOT PROVEN |
| PH2-FINAL-DOC-1 | OPEN — P3 NONBLOCKING; no normalization in this task |
| Phase 2 | NOT COMPLETE |
| Phase 3 | NOT AUTHORIZED |

STOP after the single local candidate commit. No push, PR, merge, tag, main update, earlier-commit
amendment or additional authorization audit. The next task requires separately scoped inherited
Accounting clock-sensitivity remediation, followed by one combined independent Phase 2 corrective
audit. This local freeze does not repair PH2-CLOCK-1 or approve deployment.

## PH2-CLOCK-1 fourth corrective implementation — 2026-10-14

Owner-authorized bounded correction starting from clean third-corrective
`f4925f70fa2efc12a6c0dabad9facc515213efe9` on `phase2-final-authorization-remediation`.
Parents remain `368dc70aa7bdcefd3191661b4569ccfad29f4069`,
`2fbd4a2ae02eda31c6273456a2599b0a2f90339a`, and canonical
`669936df432ec1bb12792ed8d31741fbb1b1287a`. Main is not updated. The owner authorizes the narrow
ADR 0016 clarification: independent wall-clock order is not causal evidence. Original historical
SQLite failure attribution remains NOT PROVEN; the canonical sensitivity was separately reproduced.
This section records implementation evidence, not a fresh independent review or Phase 2 closure.

### Complete Phase 2 temporal comparison inventory and decision

Search covered all Phase 2 runtime modules, including multiline Python comparisons, ORM Q/F
lookups, owner basis readers, binding history, source selectors and model lifecycle checks.
The following entries classify the pre-correction comparisons; source positions can move with
this corrective diff. There are no other discovered independent-clock causal-order comparisons
in the inspected Phase 2 runtime.

| Location / comparison | Classification / action | Retained structural proof |
|---|---|---|
| `accounting/posted_basis.py`: Entry.created_at <= Entry.updated_at | Independent reads; remove inequality | Same-company POSTED Entry, canonical number, Journal provenance, complete exact two-line owner basis |
| Same owner basis: Entry.updated_at == Entry.posted_at | Same atomic `_post` UPDATE with one supplied value; KEEP | Owner write identity; presence/awareness also retained |
| Same owner basis: Entry.created_at <= Line.created_at <= Line.updated_at <= Entry.posted_at | Independent reads; remove all three inequalities | Exact parent FK, Company/Account/Party scope, valid positions/sides, two complete balanced lines; timestamps remain required and aware |
| `integrations/evidence.py`: Entry.posted_at <= Binding.created_at <= Binding.updated_at | Independent reads; remove both inequalities | Posted owner basis and exact binding/source/effect/Journal/accounts/Parties/amount/date/memo; aware binding metadata retained |
| Same file, `invoice_certificate`: Invoice.issued_at <= InvoicePosting.created_at | Independent reads; remove | Billing owner proves ISSUED state and immutable source facts; binding and exact owner Entry proof |
| `payments_billing/selectors.py`: prior InvoicePosting.created_at, PaymentAllocation.created_at, Payment.recorded_at <= AllocationPosting.created_at | Three independent-read comparisons; remove | Required exact prerequisite binding UUID/Invoice, same AR, complete invoice certificate and source allocation basis |
| `integrations/history.py`: Entry.created_at <= Entry.updated_at; Binding.created_at >= Entry.posted_at; Binding.updated_at >= Binding.created_at | Independent reads; replace ordering with explicit timestamp presence | SQL-only complete-history Company/provenance/POSTED/number/date/unit/count/amount/line-shape probes; same-write Entry equality retained |
| Same history: each line's created_at >= Entry.created_at, updated_at >= its created_at, updated_at <= Entry.posted_at | Six independent-read comparisons; replace with timestamp presence | First/second positions, exact identities/types/Parties/descriptions/debits/credits/precision; schema NOT NULL/timezone types and direct owner awareness checks |
| Same history: prior binding/Allocation/Payment times <= AllocationPosting.created_at | Three independent reads; replace with presence | Exact prerequisite source and same AR, complete PAY-INT history, raw FK/Company provenance and immutable financial facts |
| Same history: Invoice.issued_at <= InvoicePosting.created_at | Independent reads; replace with presence | Complete issued-invoice SQL basis, Party type/Company, currency identity, exact invoice amount |
| `billing/accounting_basis.py`, `payments/integrations/billing/accounting_basis.py` | Presence/awareness, not ordering; KEEP unchanged | Owner ISSUED/allocation/receipt evidence, matching parents/capacity/currency/Party |
| Billing/Accounting/Inventory/Procurement model lifecycle posted_at/issued_at null checks; Billing/Payments/PAY-INT selectors' timestamp presence checks | State/presence, not chronology; KEEP unchanged | Required lifecycle/source metadata |
| Sales/Procurement/Inventory/Billing/Payments/Accounting model/selector order_by and PAY-INT history created_at ordering | Presentation/stable pagination, not a causal certificate; KEEP unchanged | UUID tie-breakers and existing scope/bounds unchanged |
| Phase 2 user-requested business-date/effective-date filtering, snapshot metadata returns and schema-profile timestamp declarations | Filtering/traceability/schema, not independent-clock causal proof; KEEP unchanged | Existing source business-date policy and fixed schema admission |

No schema or DateTimeField definition changes, timestamp fabrication, tolerance, retry, sleep,
clock polling, monotonic-clock storage or historical rewrite. The four runtime changes are
Accounting `posted_basis.py` and integration `evidence.py`, `history.py`, and
`payments_billing/selectors.py`. Authorization and mutation services remain byte-for-byte
unchanged. Invoice 41.37 AR/Revenue and Allocation 17.25 Cash/AR, Payment.payment_date, zero,
exact prerequisite/same AR, uniqueness, immutable ORM, locks, outer atomicity, owner schema/RLS
admission and alias routing remain required. ADR 0016 records only this corrective clarification.

### Regression design and corruption reclassification

New `integrations/tests/test_clock_safety.py` exercises normal posting, 1ms Entry-to-binding
rollback, separate binding pre_save inversion, posting earlier than Entry/line creation, and
line pre_save inversion, for both effects. Test-scoped clocks preserve exact injected values.
Reloaded native rows, owner basis, status, matching retry and complete history must agree without
new Entry/binding/audit facts or refreshed timestamps; a fresh unpatched posting follows each
case. Separate tests preserve missing/naive metadata rejection and same-write equality.

The old `test_corrupt_allocation_never_certified[timestamp]` changed only created_at to year
2000, not structural provenance. It is reclassified, not discarded: the new isolated timestamp
matrix includes that case, plus binding updated_at, Entry/line times, Invoice.issued_at, prior
InvoicePosting.created_at, Allocation.created_at and Payment.recorded_at. Each must retain a
valid certificate and exact metadata; adding wrong immutable memo afterwards must fail closed.
These privileged synthetic alterations are not supported business mutation paths. Existing wrong
AR, prerequisite, Entry reuse, source amount and all other structural-corruption tests retain
their failure expectations. Complete owner-evidence/RLS/schema/alias regressions remain required.

### Verification and freeze gate

Verification completed: PH2-CLOCK-1 is REMEDIATED LOCALLY — INDEPENDENT VERIFICATION PENDING.
Only new disposable synthetic databases were used. PostgreSQL QA used C-locale UTF-8 and disabled
autovacuum only in the disposable cluster to exclude the separately known synthetic policy-DDL
maintenance deadlock; real application locks and authorization races are unchanged. Full
PostgreSQL/SQLite, targeted integration/authorization, bootstrap/alias/architecture, lint/format,
Django/drift and frontend checks passed before the single local commit. No unexplained failure
remains. PH2-FINAL-DOC-1 stays OPEN / P3 NONBLOCKING; Phase 2 NOT COMPLETE; Phase 3 NOT
AUTHORIZED. No push, PR, merge, tag, main update, earlier-commit amendment or formal closure.

Verification history retained: the initial dedicated PAY-INT run returned 298 passed / 2 failed
in 281.48s. Both failures were fresh PostgreSQL standalone-owner subprocess bootstraps trying
`localhost:5432`: the external QA settings selected the disposable database correctly, but the
subprocesses intentionally load `config.settings.development` and lacked matching POSTGRES_HOST /
USER / PASSWORD environment variables. No application assertion or posting invariant failed in
those two traces. The first full PostgreSQL run was stopped before completion once this harness
misconfiguration was identified; it is not counted as a passing full run. Only the disposable
runner environment was corrected, with the failed logs retained and new database names used.
Repository settings, tests and runtime were not changed to accommodate this harness error.

Completed local verification evidence (all pytest counts below distinguish implementation-run
evidence from the still-required independent combined re-audit):

| Run | Passed | Failed | Skipped | Pytest runtime |
|---|---:|---:|---:|---|
| Final clock-safety file, PostgreSQL | 34 | 0 | 0 | 168.39s |
| Final clock-safety file, SQLite | 34 | 0 | 0 | 71.98s |
| Exact original HTTP case with external 1ms rollback probe, PostgreSQL | 1 | 0 | 0 | 15.73s |
| Exact original HTTP case with external 1ms rollback probe, SQLite | 1 | 0 | 0 | 12.30s |
| Existing three authorization corrective suites, PostgreSQL | 227 | 0 | 0 | 534.33s |
| Fresh standalone-owner and Accounting installation topologies, corrected harness | 26 | 0 | 0 | 175.66s |
| Complete PAY-INT, corrected harness | 300 | 0 | 0 | 300.21s |
| Complete ACC-INT, corrected harness | 1,175 | 0 | 0 | 1,812.90s |
| Full PostgreSQL 17, corrected harness | 3,015 | 0 | 0 | 2,977.23s |
| Full supported SQLite | 1,618 | 0 | 1,397 | 897.82s |

SQLite skip classification from the actual JUnit reasons: 649 real PostgreSQL row-lock/concurrency;
722 PostgreSQL roles/RLS/catalog/FK/CHECK admission; 15 PostgreSQL alias/fresh-bootstrap;
11 exact PostgreSQL numeric/high-precision SQL cases. There are no unexplained SQLite failures.
The exact reproduced HTTP case is
`test_http.py::test_complete_action_rbac[get-allocation-accounting.entry.post]`; the external
probe records binding created_at minus posted_at = -1000us and updated_at minus created_at = 1us
on both backends, validates successfully, and verifies patch restoration.

Runtime: Linux Docker, Python 3.13.16, Django 5.2.17, PostgreSQL 17.11, Ruff 0.16.7,
Node 22.23.3. Source was mounted read-only in every application test runner. The disposable
PostgreSQL cluster used tmpfs storage; final successful test databases were dropped by pytest.
The interrupted run's remaining synthetic test database and all other task-created database
fixtures were destroyed with that verified tmpfs container. All ten `bos-clock4-*` QA containers
and the dedicated network were removed; pre-existing Docker/demo resources were untouched.
External command logs, exit-code JSON and JUnit XML remain in the task's `ph2_clock4_qa`
evidence directory, outside the repository. No customer database or production service was used.

The full PostgreSQL JUnit breakdown includes Core/foundation/database 408; Sales 98;
Procurement 115; Inventory 80; Billing 104; Payments 136; Accounting 304; PAY-INT 300;
ACC-INT 1,175; first/second/third authorization corrective suites 122/60/45; other tests 68.
ACC-INT contains all 225 owner-evidence tests, 442 profile tests, 4 extra PostgreSQL evidence
tests, 228 concurrency tests, 25 atomicity tests and 23 alias/topology tests. Complete owner
RLS/schema/NOT VALID/constraint/identity/default-cursor-trap/two-line/four-line rejection
coverage passed unchanged. ACCINT1-AUD-1 remains resolved; this correction introduces no
weakening of complete-evidence admission. All existing corruption and financial-effect
regressions passed, including the new metadata-versus-structural distinction.

Commands executed (external `qa_settings` only selects each new synthetic PostgreSQL database;
the three installed-integration flags were enabled; bootstrap subprocesses received the same
disposable POSTGRES_HOST/USER/PASSWORD/PORT environment):

```text
python -m pytest -q --ds=qa_settings --tb=short --junitxml=/qa/full-pg-final.xml
python -m pytest -q --ds=config.settings.test --tb=short --junitxml=/qa/full-sqlite.xml
python -m pytest -q --ds=qa_settings businessos/modules/accounting/integrations/tests/test_clock_safety.py
python -m pytest -q --ds=config.settings.test businessos/modules/accounting/integrations/tests/test_clock_safety.py
python -m pytest -q --ds=qa_settings tests/test_final_authorization.py tests/test_authority_batches.py tests/test_permission_upserts.py
python -m pytest -q --ds=qa_settings businessos/modules/payments/integrations/billing/tests
python -m pytest -q --ds=qa_settings businessos/modules/accounting/integrations/tests
ruff check . --no-cache
ruff format --check --no-cache <all six Python files in this corrective diff, explicitly named>
python manage.py migrate --noinput
python manage.py check
python manage.py makemigrations --check --dry-run
git diff --check
git diff --check 669936df432ec1bb12792ed8d31741fbb1b1287a..HEAD
npm ci
node --check static/js/app-navigation.js
node --test tests/js/test_app_navigation.cjs
npm run build:css
```

Fresh complete-topology migrations passed; Django reported zero issues and no migration drift.
All six changed Python files pass explicit formatting; lint and whitespace checks pass. The
frontend commands ran in a disposable copy, not the source checkout: 21 JavaScript tests pass,
generated CSS is byte-identical, and no frontend/dependency file changed. `npm ci` still reports
eight inherited dependency advisories (two moderate, six high); outdated Browserslist data is
also reported. These are retained concerns, not repaired or concealed by this bounded task.
Initial development-focused clock/contract/evidence runs also passed: PostgreSQL 127/0/0 in
262.29s and SQLite 123/0/4 in 110.51s, before ten additional missing/naive-owner cases brought
the final clock file to 34 tests. The final full suites contain all final cases.

Only four Accounting evidence readers, two Accounting integration test files and the two
authorized documents changed. Core Access, all six standalone mutation services, the three
authorization corrective test files, schemas, migrations, settings and frontend are unchanged
from the third corrective. No independent audit was performed in this implementation session.
PH2-FINAL-AUD-1, PH2-AUTH-CORR-1 and PH2-AUTH2-AUD-1 remain remediated locally as their frozen
commits. Canonical clock-sensitivity reproduction is closed by this local correction; the
original historical SQLite failure's cause remains NOT PROVEN. The fourth local commit is
identified by its exact parent `f4925f70fa2efc12a6c0dabad9facc515213efe9` and message
`fix: remove wall-clock causality from accounting evidence`; its resulting SHA is reported in
the handoff, not fabricated inside its own content. STOP for the separately authorized combined
independent re-audit. No publication, main adoption, Phase 2 closure or Phase 3 authorization.

## Phase 2 formal closure for canonical adoption — 2026-10-14

### Authority, canonical baseline and preserved ancestry

The owner explicitly authorized one documentation-only formal Phase 2 closure commit above
the independently approved combined corrective candidate. This records formal acceptance of
the completed Phase 2 architecture/corrective series, not a new implementation or independent
audit performed by this documentation author. **FORMAL PHASE 2 CLOSURE: COMPLETE FOR CANONICAL
ADOPTION. CANONICAL ADOPTION: PENDING. PHASE 2 CANONICALLY CLOSED: NO.**

Canonical starting main remains `669936df432ec1bb12792ed8d31741fbb1b1287a`.
ACC-INT-1 was canonically closed there after acceptance CI #129 and exact-head main
[CI #130 / 38374429372, attempt 2 SUCCESS](https://github.com/sahinkhan/djangobusinessos/actions/runs/38374429372),
with 2,755 PostgreSQL tests. Attempt 1's `CREATE POLICY synthetic_hide` versus autovacuum
deadlock remains historical evidence; the same-SHA failed-job rerun did not change code.

| Order | Exact preserved SHA | Checkpoint |
| --- | --- | --- |
| Canonical base | `669936df432ec1bb12792ed8d31741fbb1b1287a` | ACC-INT-1 canonical freeze |
| First correction | `2fbd4a2ae02eda31c6273456a2599b0a2f90339a` | Late authorization remediation |
| Second correction | `368dc70aa7bdcefd3191661b4569ccfad29f4069` | Authorization batch-cycle remediation |
| Third correction | `f4925f70fa2efc12a6c0dabad9facc515213efe9` | Remaining authorization corrective remediation |
| Fourth correction / audited candidate | `4a2a7ecaa26e1e312a482e405cd763efdc5f2d74` | PH2-CLOCK-1 structural versus clock evidence correction |

No corrective commit is amended, squashed or rewritten. Earlier REVISE results and all
implementation-run evidence above remain historical, including initial harness failures and
the canonical clock-sensitivity investigation. The separate controlled 1ms rollback reproduction
established an inherited product defect; it did **not** establish the cause of the original
historical SQLite failure. That original attribution remains **NOT PROVEN**. PH2-CLOCK-1 removed
independent-clock causal inequalities while preserving required aware metadata, the same-write
Entry `updated_at == posted_at` invariant and complete structural/financial evidence. ADR 0016's
accepted clarification is retained without further technical change.

### Independent audit and hosted corrective-candidate evidence

The owner supplied the fresh combined independent verdict:

**FINAL PASS — PHASE 2 COMBINED CORRECTIVE SERIES APPROVED FOR HOSTED CI AND FORMAL CLOSURE**

Readiness **A**; final exit matrix **13 PASS / 0 FAIL / 0 NOT PROVEN**. This is independent
review evidence supplied to this checkpoint, distinct from the implementation-run PostgreSQL/
SQLite counts recorded above and from hosted CI.

Hosted corrective-candidate [Phase 0 checks #131 / 38537403882](https://github.com/sahinkhan/djangobusinessos/actions/runs/38537403882)
completed **SUCCESS**, attempt 1, event `push`, branch `phase2-final-authorization-remediation`,
exact checkout `4a2a7ecaa26e1e312a482e405cd763efdc5f2d74`. Hosted PostgreSQL:
**3,015 passed / 0 failed / 0 skipped**. Fresh migrations/bootstrap, Ruff, Django system checks,
migration drift, npm installation, Tailwind build and generated CSS reproducibility all passed.
Inherited npm advisories and Actions/Browserslist maintenance warnings remain separate concerns;
this checkpoint does not remediate them or certify production readiness.

### Accepted final Phase 2 exit matrix

| # | Exit criterion | Final accepted result |
| --- | --- | --- |
| 1 | Six standalone accepted architectures | PASS |
| 2 | Company isolation | PASS |
| 3 | ProductVariant consistency | PASS |
| 4 | Inventory ledger authority | PASS |
| 5 | Accounting posted-line authority | PASS |
| 6 | Billing frozen totals/allocation-derived outstanding | PASS |
| 7 | Historical immutability | PASS |
| 8 | Retry/idempotency safety | PASS |
| 9 | Public optional composition/no hard dependency cycle | PASS |
| 10 | Registry gating/exact service RBAC | PASS |
| 11 | Full PostgreSQL/mandatory quality | PASS |
| 12 | No speculative framework | PASS |
| 13 | Complete architecture acceptance | PASS |

**13 PASS / 0 FAIL / 0 NOT PROVEN.** This accepts the reviewed Phase 2 scope, not every
future optional integration, vertical capability or deployment requirement.

### Final finding dispositions and documentation normalization

| Finding / evidence | Final disposition |
| --- | --- |
| PH2-FINAL-AUD-1 | RESOLVED — combined independent re-audit |
| PH2-AUTH-CORR-1 | RESOLVED — combined independent re-audit |
| PH2-AUTH2-AUD-1 | RESOLVED — combined independent re-audit |
| PH2-CLOCK-1 | RESOLVED — combined independent re-audit |
| ACCINT1-AUD-1 | RESOLVED — independent corrective approval retained |
| PH2-FINAL-DOC-1 | RESOLVED — authorized docs-only current-status normalization |
| Original historical SQLite failure attribution | NOT PROVEN — unchanged historical uncertainty |

PH2-FINAL-DOC-1 was P3/nonblocking. Its resolution normalizes stale current-facing summaries
while retaining historical chronology and every accepted technical body:

| Document / location | Normalization |
| --- | --- |
| `docs/ROADMAP.md`, Phase 0H checkpoint, Phase 2 current milestone and gate summary | Historical Gate 3 authorization scoped to its date; ACC-INT-1 closure, four-corrective chain, final audit/CI and Phase 2 formal-versus-canonical distinction |
| `docs/architecture/BASELINE.md`, commercial ownership | PAY-1 canonical closure and exact SHA/CI #105; optional allocation/Accounting implementation, no hard-dependency change |
| `docs/architecture/DEPENDENCY_MAP.md`, Billing and Payments | Implemented optional allocation/outstanding and Accounting composition; standalone Payments still exactly Party/organization/reference/access |
| `docs/architecture/MODULE_BOUNDARIES.md`, Option A commercial boundary | Same stale future-only allocation/PAY-1 summary normalized to implemented optional composition |
| ADR 0010, status/header | Inventory corrective re-audit/adoption closed; historical narrative retained |
| ADR 0011, current context note | Later Payments/Accounting/integration gates distinguished from historical BILL-0/BILL-1 deferrals |
| ADR 0014, current status note | ACC-0/ACC-1/ACC-INT-1 canonical closures distinguished from historical acceptance-stage pending wording |
| ADR 0016, current implementation header and clarification-stage status | ACC-INT-1 canonical closure; later combined corrective approval; clock-safety technical clarification unchanged |
| This plan, top/current status and this closure section | Final audit performed, exit matrix accepted, findings resolved, formal closure complete but canonical adoption pending |

ADRs 0012/0013/0015 were reviewed: their historical foundation/contract/acceptance-stage
records remain evidence of those gates, not new pending Phase 2 findings. No global replacement
of historical pending/REVISE/not-started statements was performed.

### Publication and canonical completion rule

This one docs-only closure commit requires its **own** exact-head hosted branch push CI.
CI #131 verifies its parent corrective candidate and must not be reused as closure-commit CI.
The resulting closure SHA, run number/ID/attempt, tested SHA and actual job/check results are
reported after publication; no future SHA or CI result is fabricated in this commit.

After successful closure CI, status is **FORMALLY CLOSED FOR CANONICAL ADOPTION**, not
canonically closed. A separate authorization must revalidate unchanged main
`669936df432ec1bb12792ed8d31741fbb1b1287a` and straight ancestry, directly fast-forward main
to the closure SHA with a normal push, and verify separate exact-head main push CI. Only then
may Phase 2 be declared canonically closed. **DO NOT CREATE A PR.** No tag is specified or
created; no merge commit, rebase, squash, force push, release or main update is authorized here.

No runtime, test, migration, setting, manifest, frontend or business-semantic change accompanies
this checkpoint. **Phase 3/Phase 4 are NOT AUTHORIZED. Production readiness is NOT CLAIMED;
SaaS activation and production deployment remain NOT AUTHORIZED.** Stop after this closure
commit's hosted CI verification; failed CI requires separate disposition, not automatic repair.
