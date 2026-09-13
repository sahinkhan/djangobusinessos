# Phase 1 — Shared Commercial Primitives

Status: READY AFTER PHASE 0 MERGE

## Goal

Create the smallest stable Party and Catalog capabilities needed to unblock Sales, Procurement, Inventory, Billing, HR, Ecommerce and vertical modules.

Phase 1 must remain business-focused and fast. Do not introduce platform abstractions that are not required by Party/Catalog.

## Required reading

Before implementation, read:

- `AGENTS.md`
- `docs/architecture/BASELINE.md`
- `docs/architecture/MODULE_BOUNDARIES.md`
- `docs/architecture/DEPENDENCY_MAP.md`
- `docs/decisions/0002-hard-dependencies-and-optional-integrations.md`
- `docs/ROADMAP.md`

## Deliverables

### 1. Party module

Create `businessos/modules/party/`.

Party owns reusable external/internal business-party identity concepts used across modules.

Minimum models/capabilities:

- Party
  - UUID id
  - company scope where appropriate
  - party type: person / organization
  - display/legal name
  - active status
  - created/updated timestamps
- ContactMethod
  - email / phone (minimum useful set)
- Address
  - link to Party
  - country
  - structured address fields kept intentionally simple
  - billing/shipping/default semantics only if needed by real flows
- business roles/flags sufficient to express customer and supplier use without creating separate authoritative Customer/Supplier copies

Do not implement CRM pipeline, customer credit control, loyalty, marketing automation, complex KYC, or arbitrary party graph/network concepts.

Party must not depend on Sales, Procurement, Inventory, Billing, Accounting, HR, Ecommerce or verticals.

### 2. Catalog module

Create `businessos/modules/catalog/`.

Catalog owns reusable sellable/purchasable item/service identity.

Minimum models/capabilities:

- Product
  - UUID id
  - company scope if product ownership is company-specific; document the chosen rule
  - code/SKU
  - name
  - product type at minimum: stockable / consumable / service (or equivalent minimal design)
  - default UoM
  - active status
- ProductCategory
  - minimal hierarchy if genuinely useful
- basic sales/purchase description/flags only when required to unblock later modules

Catalog must NOT own:

- authoritative stock quantity
- warehouse balances
- sales order pricing engine
- purchasing workflow
- accounting balances
- ecommerce-only duplicated product records

Do not implement variants/attributes, pricelists, promotions, tax engine, BOM, manufacturing, complex UoM conversions, barcode platform, media library or product bundles in Phase 1 unless required to preserve a correct minimal contract.

### 3. Framework-neutral services

State-changing use cases belong in services.

Provide only useful services, for example:

- create/update party
- add/update party contact/address
- create/update product/category

Business services must accept `BusinessContext` where organization scope/authorization is relevant and must not accept Django `HttpRequest`.

### 4. Selectors/read APIs

Create selectors for reusable/non-trivial reads needed by later modules, such as:

- active customers/suppliers accessible in company scope
- active products/categories accessible in company scope

Keep selectors simple and explicit.

### 5. Authorization/data scope

All company-owned Party/Catalog data must be scoped explicitly.

Use the existing `BusinessContext` and organizational access policies rather than inventing a new authorization engine.

Prevent cross-company reads/writes in service paths and test this explicitly.

### 6. Module manifests

Party and Catalog must provide valid manifests.

Expected hard dependency direction:

```text
party -> identity, organization, reference, access
catalog -> reference, organization, access
```

If Catalog genuinely requires Party for a concrete Phase 1 rule, document the decision before adding that dependency. Do not add it speculatively.

Register module manifests using the existing registry convention.

### 7. UI

Create polished reusable screens using existing BusinessOS UI patterns:

Party:
- party list
- create/edit
- detail
- search/filter minimum

Catalog:
- product list
- create/edit
- detail
- category management minimum
- search/filter minimum

Do not create a metadata-driven UI engine.

### 8. Demo/seed data

Add idempotent demo/reference setup only where useful for local development.

Do not couple production startup to demo data.

### 9. Tests

Minimum architectural test coverage:

Party:
- person and organization creation
- customer/supplier role representation
- company scope enforcement
- cross-company write/read rejection through business services/selectors
- contact/address validation

Catalog:
- product/category creation
- SKU/code uniqueness rule according to documented scope
- service products work without Inventory
- no authoritative stock field/source of truth is introduced
- company scope enforcement

Shared:
- manifests validate/register correctly
- services accept BusinessContext rather than HttpRequest
- no reverse imports into core or unrelated modules

## Explicitly forbidden in Phase 1

Do NOT implement:

- Sales
- Procurement
- Inventory ledger
- Billing
- Accounting
- HR workflows
- Ecommerce
- School/Hospital/Hotel
- workflow engine
- rules engine
- event bus
- metadata/studio
- React
- Celery/Redis unless a Phase 1 requirement proves it necessary
- generic repository/unit-of-work/command-bus abstractions
- dynamic plugin installer
- client-specific extensions

## Quality gates

Before Phase 1 can PASS:

```bash
pytest
ruff check .
python manage.py check
python manage.py makemigrations --check
```

Also verify:

- fresh PostgreSQL migration bootstrap
- module-local tests are discovered
- representative desktop/mobile UI smoke test
- no cross-company leakage in tested service/selectors

## Publication workflow

Work on a dedicated branch such as:

```text
phase1-party-catalog
```

Do not commit directly to `main`.

Do not begin Phase 2 automatically after Phase 1 implementation.

## Exit criteria

Phase 1 is complete only when:

1. Party and Catalog are stable enough for Sales/Procurement/Inventory to consume without redesign;
2. company-scope behavior is explicit and tested;
3. service products are supported without requiring Inventory;
4. Catalog does not own stock or transaction pricing workflow;
5. no speculative platform framework was introduced;
6. tests/checks pass;
7. implementation is published for architecture review.

## Architect intent

The main purpose of Phase 1 is not feature depth. It is to freeze the first reusable business contracts that many later modules will depend on. Keep the models small, explicit and easy to evolve.
