# BusinessOS Roadmap

## Strategy

BusinessOS follows a staged evolution:

1. ship business value fast;
2. harden what real customers use;
3. extract shared platform capabilities only after repeated needs appear;
4. preserve an eventual path to a protected BusinessOS kernel and optional custom Python runtime.

The roadmap is capability-driven, not date-driven. A later phase should not begin merely because time passed; it begins when earlier exit criteria are met.

---

## Phase 0 — Foundation

Goal: establish the minimum architecture needed to unblock fast module development.

Current correctness status: COMPLETE. Foundation remediation was accepted at
`f1f7f2f6c917308bedb3c48e51b8113a064d96c2`; Core Foundation v1 remains FROZEN by ADR 0009 and is
reconstructed as the canonical Phase 0 checkpoint `4ef16c271dfce235dbcb874fabaa5df0c63edd54`
on canonical `main`.

Deliver:

- Django 5.2 LTS / Python 3.13 project
- PostgreSQL
- custom User model
- Company / Branch / Warehouse
- Country / Currency / Language / UoM references
- basic organizational access
- BusinessContext
- lightweight module manifest/registry
- shared UI shell
- pytest + Ruff
- Docker development baseline

Do not deliver workflow, metadata, event bus, Redis/Celery, React, microservices, tenancy or marketplace.

Exit gate: foundation tests/checks pass and shared contracts are frozen enough for parallel module development.

---

## Phase 0H — Core Foundation v1 Hardening

Status: Complete — FINAL PASS restored. The prior freeze recorded at
`5e10ec23ad91a4ba8ef75ea7d29e8b2fb26e2095` on `foundation-v1-hardening` remains historical
evidence of the acceptance later withdrawn by adversarial audit. Correctness remediation at
`f1f7f2f6c917308bedb3c48e51b8113a064d96c2` passed independent re-audit; ADR 0009 is Accepted and
freezes that implementation as the Core Foundation v1 operational baseline.

Deliver:

- minimal company-scoped BusinessOS RBAC with deny-by-default authorization
- deterministic module permission declarations and registration
- append-only Core audit records for security-sensitive actions
- explicit company/branch/warehouse grant and revoke services
- Company country, default language, IANA timezone and shared business-time helpers
- immutable Company base currency through normal mutation paths
- immutable Country/Currency/Language/UoM and permission identity codes
- a documented boundary between Django technical permissions and BusinessOS authorization

Exit gate: PASSED. Gate 2 received independent FINAL PASS against the accepted remediation SHA.
Gate 3A received independent FINAL PASS at accepted candidate
`780144c5560e1d46cc5d545dc29b33522cd2d1f5`; hosted CI #42 succeeded at that exact SHA. Gate 3B
canonical `main` cutover received independent FINAL PASS at
`29d6c12913145bd1b64f572b5bc94c1f53d9987a`, with hosted main CI #45 successful. Gate 3 is closed;
Phase 2 / Gate 4 adoption remains separately gated and unauthorized.

---

## Phase 1 — Shared Commercial Primitives

Status: COMPLETE. Accepted Party + Catalog behavior is replayed on the canonical Core baseline at
checkpoint `5b95aaa0f13a64a862999e13c6533d1bbb5c81f3`. ADRs 0004 and 0005 remain Accepted.

Deliver:

- Party / Contacts
- Catalog / Products / Categories
- ProductVariant as the concrete sellable/purchasable SKU identity
- minimal Attributes / Attribute Values for real variable products
- simple products represented internally by one default ProductVariant
- reusable document numbering basics only if Phase 1 flows require them
- shared form/list/detail UI patterns

Catalog remains free of stock balances, transactional pricing engines, Sales/Procurement workflow and Accounting.

Do not build an advanced variant configurator, automatic combination generator, pricelists/promotions, Inventory quantities or ecommerce-specific product copies in this phase.

Exit gate: Sales/Procurement/Inventory can consume stable Party/Catalog contracts, and both simple and variable products resolve to stable ProductVariant identities without redesign.

---

## Phase 2 — Commercial Core

Status: Gate 4A Sales is accepted, adopted, and closed. Gate 4B Procurement implementation
candidate `395da2ad874fc2efb72219da71316b9a6d8f73bf` replays the historically accepted standalone
contract onto Core Foundation v1. Candidate head `12d1a1f90689979048cdf3b4f59836b026dd153f`
passed hosted CI #53 but completion review BLOCKED on missing authorization-revocation and
confirmation-versus-mutation PostgreSQL coverage. Narrow test remediation
`b8c49e1fb5b62f9169038b59e35b6d4e7adfb8e0` closes those gaps without production changes and is
published at final candidate `1eabb0e9806342cc2ba71f1468eb18af120cddb9`. Hosted CI #54 passed
with 342 PostgreSQL tests, and independent re-audit returned FINAL PASS. Documentation-only
acceptance commit `e4ea1791f0b2c7d1209ea574de3689970e1fc398` passed branch CI #55, was
adopted into canonical `main` by normal fast-forward, and passed exact-head main CI #56. Gate 4B
is accepted, adopted, and closed.

Gate 4C Inventory is now implemented only as an isolated canonical adoption candidate on
`gate4c-inventory-adoption`, reconstructed from canonical `main` at
`8d5a41f83c3f796fa31e7d3f8598c54f7dfc5b95`. Historical `phase2-inventory` at
`f45afdfea33d3fd03d469e6a0cd63d0e5358f38c` remains remediation/reference evidence only and was
not merged or cherry-picked. The candidate implements the posted movement ledger, Foundation v1
RBAC/audit/company-lock contracts, derived balances, and HTTP-only module gating. Initial
candidate head `01037fc7f87e546382931a081750bf367bb78232` passed hosted CI #59 with 406
PostgreSQL tests, but independent audit BLOCKED acceptance on mixed-UoM balance safety, HTTP
mutation-form RBAC, stale-company HTTP evidence, and a missing ProductVariant stock-field
assertion. Narrow remediation `78ba3ae92366da9b2136b260cc9a380e22587e08` closed those findings at
final candidate `8b52270959a2f6623de225e08dc081aea8d1630b`. Hosted CI #60 passed that exact
head with 410 PostgreSQL tests, and independent re-audit returned FINAL PASS. Documentation-only
acceptance checkpoint `eb2f52afc53fd8c36249bc6a1e61c15dba9effe8` passed branch CI #61, was
adopted into canonical `main` by normal fast-forward, and passed exact-head main
[CI #62](https://github.com/sahinkhan/djangobusinessos/actions/runs/34931069346). Gate 4C is
accepted, adopted, and closed. Billing, Accounting, integrations, and
Procurement/Sales-to-Inventory automation remain unauthorized; full Phase 2 is not complete and
production deployment is not approved.

The closure at `60f879a036e0fd21eada1375fa695f32adc7dc91` remains historical administrative
evidence. A post-closure correctness audit subsequently returned REVISE for four narrow
Inventory findings covering company-local datetime/DST handling, same-line combined history
filters, snapshot/UoM update auditing, and initial balance/history page RBAC. Corrective
implementation `343c413bff7f7e520a5a031f92f461a8058db3cc` was published through candidate
`23a12ae544be2e611ac3fd5bfa90d62299599648`. Independent corrective re-audit returned REVISE for
one residual timestamp-precision issue: an unchanged minute-granular edit could truncate the
trusted persisted seconds and microseconds. Narrow remediation
`b33e6faaf931777575292a42af775a1c11986984` preserves the original aware instant when the submitted
company-local minute is unchanged, while a changed minute remains normalized to the submitted
minute. Candidate head `d7fc63c2af77e210cdbae8a72837c1497200f251` passed CI #68, but independent
re-audit returned REVISE because a trusted persisted DST fall-back-fold minute was rejected during
generic parsing before preservation. Final narrow remediation
`145c9d51a3507aa1df8d6548659e16e506940d1e` performs the trusted raw-minute match before generic
DST conversion while retaining ambiguity/gap rejection for other input. It is isolated on
`gate4c-inventory-postclosure-remediation` at final corrective candidate
`09794e9293da78117e5873ebbff9f4b98fa5e1b7`. CI #69 passed that exact head with 422 PostgreSQL
tests, and independent final corrective re-audit returned FINAL PASS. The correction is formally
accepted at checkpoint `35663e4f6b4112903838e0a8069f47885c83f7ce`, adopted into canonical `main`
by normal fast-forward, and passed exact-head main CI #71
([run 34957834165](https://github.com/sahinkhan/djangobusinessos/actions/runs/34957834165)). The Gate
4C post-closure corrective audit cycle is FINAL PASS, formally accepted, adopted, and closed; the
original historical closure remains preserved.

An independent Sales post-closure audit returned REVISE for four narrow findings: mutable
in-memory parent substitution could bypass historical line deletion protection; SKU/name-only
snapshot refreshes could persist without `sales.order.updated` evidence; long customer names and
maximum supported totals could overflow the order document; and non-finite Decimal inputs could
escape canonical validation. Sales-local remediation is implemented at
`f9092cebe2f27504c0f3dfc772524645e25c1f91` on
`gate4a-sales-postclosure-remediation`. Final corrective candidate
`b34a98a1f47c7d0c526fa4dbd60207d5123f9fe3` passed exact-head hosted CI
[#74](https://github.com/sahinkhan/djangobusinessos/actions/runs/34961977826) with 437 PostgreSQL
tests and all required checks, and independent corrective re-audit returned FINAL PASS. The
historical Gate 4A closure remains preserved. Documentation-only corrective acceptance checkpoint
`5ccada2bdb8f28bbc031e25aae72a88f7f454e09` was adopted into canonical `main` by normal
fast-forward and passed exact-head main
[#76](https://github.com/sahinkhan/djangobusinessos/actions/runs/34966070313). Corrective
acceptance and canonical adoption are complete; this documentation closes the post-closure
corrective cycle. The current frozen Sales foundation scope is canonically complete. Future Sales
extensions remain open and separately governed. Billing, Accounting, and integrations remain
unauthorized.

An independent Procurement post-closure audit subsequently returned REVISE for five narrow
findings: mutable in-memory parent substitution could bypass historical line deletion protection;
noncanonical or duplicate receipt-field UUID representations could be discarded before partial
HTTP processing; SKU/name-only snapshot refreshes could persist without
`procurement.order.updated` evidence; supported boundary values could overflow Procurement
documents; and non-finite line Decimals could escape canonical validation. Procurement-local
remediation is implemented at `1ccaf0bc74816b11035cb33f24e172ff8f902329` on
`gate4b-procurement-postclosure-remediation`. The historical Gate 4B closure remains preserved.
This corrective candidate is AWAITING INDEPENDENT PROCUREMENT CORRECTIVE RE-AUDIT and is not
accepted, adopted, merged, or re-closed. Billing, Accounting, integrations, and deployment remain
unauthorized.

The first Procurement corrective re-audit returned REVISE for one residual P3: invalid numeric
strings on `PurchaseOrderLine.quantity` or `unit_cost` could escape model validation as an
uncontrolled `TypeError`. Residual remediation `c34daec0d3ad876612c15536f8c94148f7f4664c`
uses Django DecimalField conversion semantics before finite/business comparisons and adds public
service plus direct-model regressions. Final candidate
`ad03000deeae72a1703f6935dd9d4cde46ede5cc` passed exact-head hosted CI
[#80](https://github.com/sahinkhan/djangobusinessos/actions/runs/34987503229). The second independent
corrective re-audit returned FINAL PASS after 493 PostgreSQL tests, 115 Procurement-local tests,
27 real-lock concurrency tests, focused adversarial probes, SQLite verification, and desktop/mobile
boundary QA. The corrective remediation is ACCEPTED FOR CONTROLLED ADOPTION; historical findings
remain recorded, while corrective adoption and re-closure are not yet complete.

Gate 4C original implementation candidate: `e1e94307bd96b2834f677eb02b91d27b87843f21`.

Historical Gate 4A record: independent audit BLOCKED the initial Sales adoption implementation
`28c8028950be1997b4f3d0816b1ec04764222068` at audit head
`fc609bcd81916c13921c2d1cc7b6a59eda1c1e19`. Remediation at
`d62c34e36f0a8b11f59bfdb058143e27f5231c5d` closed the findings, and independent re-audit gave
FINAL PASS to candidate `23338f1cfed11d21d4fa8fd7e92f8de120450977`; exact-head hosted CI #48
also passed. Documentation-only acceptance commit `e0c848f34da0bce9b9c6e010a396026ac5889cf4`
was adopted into canonical `main` by normal fast-forward, and exact-head main CI #50 passed. Gate
4A Sales is accepted, adopted, and closed. Gate 4B Procurement is also accepted, adopted, and
closed. Inventory adoption, Billing, Accounting, integrations, and any Procurement-to-Inventory
write remain unauthorized. Preserved historical branches remain unchanged.

Standalone modules are parallelizable after the Phase 1 contract freeze. Optional cross-module integrations are implemented only after the standalone module contracts pass review.

Deliver:

- Sales
- Procurement
- Inventory
- basic Billing
- basic Accounting

Golden flows:

- Customer -> Sales Order -> Confirm
- Supplier -> Purchase Order -> Receive
- Stock Receive / Issue / Transfer
- Invoice/Payment basics
- Journal Entry + Trial Balance basics

Concrete transactional item references use Catalog ProductVariant where an item/SKU is required.

Accounting and Inventory require transactional tests and duplicate-posting protection where relevant.

---

## Phase 3 — People and Digital Commerce

Deliver:

- HR basics: Employee, Department, Attendance, Leave
- Ecommerce composition using Catalog + Sales + Inventory + Billing

Do not create duplicate ecommerce product/variant/order/stock sources of truth.

---

## Phase 4 — Marketing Vertical MVPs

Deliver thin, polished, demo-ready verticals with one complete workflow each.

### School

Student -> Enrollment -> Attendance -> Fee -> Payment

### Hospital/Clinic

Patient -> Appointment -> Visit -> Bill -> Payment

### Hotel

Guest -> Room/Reservation -> Check-in -> Bill -> Check-out

These are marketing/pilot MVPs, not claims of full clinical/school/hospitality compliance.

---

## Phase 5 — Product Hardening

Driven by pilot clients.

Deliver as demanded:

- stronger authorization/data scope
- audit logs
- documents/attachments
- notifications
- imports/exports
- PDF/document outputs
- API surface
- backup/restore
- operational monitoring
- security hardening
- performance baselines

Exit gate: production client deployments can be upgraded/recovered safely.

---

## Phase 6 — Shared Platform Services

Extract only from repeated real requirements:

- Party/Geography/UoM/Reference Data maturity
- workflow/approval engine
- rules engine
- resource/scheduling
- documents/collaboration/notifications
- search/reporting/import/export platform
- integration platform

These are extracted platform capabilities, not speculative rewrites.

---

## Phase 7 — Enterprise Horizontal Suite

Expand/harden:

- Catalog/Pricing/Tax
- CRM/Sales
- Procurement
- Inventory/Warehouse/Logistics
- Billing/Payments
- Accounting/Finance
- Assets/Expenses/Treasury
- HR/Payroll
- Project/Helpdesk/Field Service
- Manufacturing/Maintenance/Quality
- POS
- Ecommerce

---

## Phase 8 — Industry Verticals

Build verticals primarily by composing horizontal/shared capabilities:

- Healthcare/Hospital/Clinic/Pharmacy
- Education/School
- Salon/Spa/Gym
- Restaurant
- Hotel/Hospitality
- Garments/Apparel
- Construction/Real Estate
- Fleet/Logistics
- Microfinance/Financial Services
- Legal
- Travel/Air Ticketing

---

## Phase 9 — Internationalization and Localization

Deliver localization packs rather than contaminating generic modules with country-specific rules.

Potential structure:

```text
businessos/localizations/
  bd/
  us/
  ca/
  uk/
  ae/
```

Localization may include taxes, payroll rules, fiscal reports, chart templates, document formats and legal fields.

---

## Phase 10 — Metadata / Studio / Dynamic UI

Only after stable business patterns are known:

- metadata definitions
- dynamic forms/lists
- configurable dashboards
- Studio customization
- visual workflow/rule designers where justified

React may be introduced selectively for complex designers.

---

## Phase 11 — Developer Platform and Marketplace

Deliver:

- stable extension/module SDK
- compatibility contracts
- package signing/trust policy
- certification process
- partner/developer documentation
- marketplace

Third-party code trust/isolation must be treated as a security architecture problem, not merely a packaging problem.

---

## Phase 12 — Enterprise Operations / Cloud

Deliver when customer scale justifies it:

- self-hosted enterprise operations tooling
- BusinessOS Cloud control plane
- deployment orchestration
- fleet/version visibility
- upgrade waves
- backup/restore automation
- performance certification
- security/compliance maturity
- LTS policy
- compatibility guarantees
- partner ecosystem operations

---

## Optional Runtime Evolution

Django remains the default runtime unless there is measured justification to replace parts of it.

If a custom Python runtime is later justified:

1. keep business/domain services framework-neutral;
2. extract reusable BusinessOS kernel contracts;
3. add custom runtime adapters for new endpoints/modules;
4. allow Django and custom runtime to coexist;
5. migrate selectively;
6. remove Django only if benefits clearly exceed migration/maintenance cost.

Do not schedule a rewrite merely because a custom framework is technically possible.

---

## Permanent rule

**Build capabilities late; reserve boundaries early.**
