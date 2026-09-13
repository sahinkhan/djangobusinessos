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

## Phase 1 — Shared Commercial Primitives

Deliver:

- Party / Contacts
- Catalog / Products / Categories
- reusable document numbering basics
- shared form/list/detail UI patterns

Exit gate: Sales/Procurement/Inventory can consume stable Party/Catalog contracts.

---

## Phase 2 — Commercial Core

Parallelizable after Phase 1 contract freeze.

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

Accounting and Inventory require transactional tests and duplicate-posting protection where relevant.

---

## Phase 3 — People and Digital Commerce

Deliver:

- HR basics: Employee, Department, Attendance, Leave
- Ecommerce composition using Catalog + Sales + Inventory + Billing

Do not create duplicate ecommerce product/order/stock sources of truth.

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
