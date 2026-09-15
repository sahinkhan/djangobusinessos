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
head with 410 PostgreSQL tests, and independent re-audit returned FINAL PASS. Gate 4C is formally
accepted at that candidate; canonical adoption and closure are pending this controlled execution.
Billing, Accounting, integrations, and Procurement/Sales-to-Inventory automation remain
unauthorized.

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
