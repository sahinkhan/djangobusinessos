# Phase 1 — Shared Commercial Primitives

Status: IMPLEMENTED — AWAITING ARCHITECTURE REVIEW

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
- `docs/decisions/0003-catalog-variant-contract.md`
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

Catalog owns reusable product/service/category identity and the concrete sellable/purchasable SKU identity.

The variant contract is mandatory in Phase 1. Follow ADR 0003.

Minimum models/capabilities:

#### Product

- UUID id
- company scope if product ownership is company-specific; document the chosen rule
- name
- category
- product type at minimum: stockable / consumable / service (or equivalent minimal design)
- default UoM
- active status
- basic sales/purchase description/flags only when required to unblock later modules

`Product` is the conceptual/catalog identity. Do not make Product the transactional SKU identity.

#### ProductVariant

- UUID id
- Product foreign key
- SKU/code
- `is_default`
- active status
- created/updated timestamps
- minimal fields required for stable downstream identification only

`ProductVariant` is the concrete sellable/purchasable identity used later by Sales, Procurement, Inventory, POS and Ecommerce.

Every sellable/purchasable Product must have at least one ProductVariant.

A Product must have at most one default variant.

For a simple Product, services must create/maintain exactly one default variant unless the Product is intentionally transitioned to a variable-product state according to explicit service rules.

The UI may hide variant complexity for simple Products.

#### ProductCategory

- minimal hierarchy if genuinely useful
- company/global scope rule must be explicit

#### Attribute

Minimum reusable product option definition, for example:

```text
Color
Size
```

Do not create a generic metadata engine.

#### AttributeValue

Belongs to an Attribute, for example:

```text
Color -> Black
Color -> White
Size -> M
Size -> L
```

#### VariantAttributeValue

Associates a concrete ProductVariant with AttributeValue records.

Enforce enough constraints to prevent duplicate/contradictory assignments for the same variant/attribute.

### 3. Variant invariants

The following are Phase 1 architecture invariants and require tests:

1. every sellable/purchasable Product has at least one ProductVariant;
2. a Product has at most one default ProductVariant;
3. simple product creation produces one default ProductVariant automatically through the business service path;
4. a simple Product can exist without attribute assignments;
5. variable Products can have multiple variants with attribute-value assignments;
6. SKU uniqueness scope is explicit and documented;
7. downstream contracts should be designed around ProductVariant as the transactional item identity;
8. service Products also receive a default ProductVariant and must work without Inventory;
9. Catalog does not introduce stock quantities or warehouse balances.

Do not rely only on UI/form behavior for these invariants. Enforce them appropriately at service/model/database levels according to what PostgreSQL/Django can safely guarantee.

### 4. Catalog must NOT own

- authoritative stock quantity
- warehouse balances
- sales order pricing engine
- purchase workflow
- accounting balances
- ecommerce-only duplicate Product/Variant records
- advanced pricelists/promotions

Phase 1 intentionally does NOT implement:

- automatic combinatorial variant generator
- advanced product configurator
- pricelist/variant pricing engine
- promotions/campaign pricing
- tax engine
- BOM/manufacturing
- complex UoM conversions
- barcode platform
- media library
- product bundles/kits

### 5. Framework-neutral services

State-changing use cases belong in services.

Provide only useful services, for example:

Party:

- create/update party
- add/update party contact/address

Catalog:

- create/update category
- create simple Product with default ProductVariant
- create/update ProductVariant
- create/update Attribute/AttributeValue
- assign variant attribute values
- transition/manage simple vs variable representation only if required by the implemented UI/workflow

Do not put variant lifecycle rules directly in Django views/forms/admin.

Business services must accept `BusinessContext` where organization scope/authorization is relevant and must not accept Django `HttpRequest`.

### 6. Selectors/read APIs

Create selectors for reusable/non-trivial reads needed by later modules, such as:

- active customers/suppliers accessible in company scope
- active products/categories accessible in company scope
- active ProductVariants accessible in company scope
- default variant resolution for a Product
- variant lookup by SKU according to documented uniqueness scope

Keep selectors simple and explicit.

### 7. Authorization/data scope

All company-owned Party/Catalog data must be scoped explicitly.

Use the existing `BusinessContext` and organizational access policies rather than inventing a new authorization engine.

Prevent cross-company reads/writes in service paths and test this explicitly.

Product/Variant/Category/Attribute scope rules must not allow cross-company composition accidentally.

### 8. Module manifests

Party and Catalog must provide valid manifests.

Expected hard dependency direction:

```text
party -> identity, organization, reference, access
catalog -> reference, organization, access
```

If Catalog genuinely requires Party for a concrete Phase 1 rule, document the decision before adding that dependency. Do not add it speculatively.

Register module manifests using the existing registry convention.

### 9. UI

Create polished reusable screens using existing BusinessOS UI patterns.

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
- simple-product UX that does not expose unnecessary variant complexity
- variable-product variant management
- attribute/value management sufficient to create real variants
- search/filter minimum

Do not create a metadata-driven UI engine or advanced variant matrix/configurator.

### 10. Demo/seed data

Add idempotent demo/reference setup only where useful for local development.

Include at least representative examples of:

- one simple product with one default variant
- one variable product with multiple variants/attribute values
- one service product with a default variant and no Inventory dependency

Do not couple production startup to demo data.

### 11. Tests

Minimum architectural test coverage:

Party:

- person and organization creation
- customer/supplier role representation
- company scope enforcement
- cross-company write/read rejection through business services/selectors
- contact/address validation

Catalog:

- product/category creation
- simple Product automatically gets exactly one default ProductVariant through service path
- service Product gets default ProductVariant and works without Inventory
- variable Product supports multiple variants
- attribute/value assignment works
- duplicate/contradictory variant attribute assignment is rejected
- no Product has more than one default variant
- SKU/code uniqueness follows documented scope
- company scope enforcement for Product/Variant/Category/Attribute data
- no authoritative stock field/source of truth is introduced

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
- automatic variant combination generation
- advanced variant configurator
- pricelist/promotion/tax engine
- stock quantities

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
- simple and variable Product flows both work through the service layer
- downstream item identity is ProductVariant-ready

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
3. every sellable/purchasable Product has a ProductVariant identity;
4. simple Products use one default ProductVariant without unnecessary UI complexity;
5. variable Products can use attributes/values without an advanced configurator;
6. service Products work without requiring Inventory;
7. Catalog does not own stock or transaction pricing workflow;
8. no speculative platform framework was introduced;
9. tests/checks pass;
10. implementation is published for architecture review.

## Architect intent

The main purpose of Phase 1 is not feature depth. It is to freeze the first reusable business contracts that many later modules will depend on.

`Product` is catalog identity; `ProductVariant` is transactional SKU identity. Establish this contract now so Sales, Procurement, Inventory, POS and Ecommerce do not require a later variant retrofit.

## Implementation outcome

### Delivered

- Company-owned Party, ContactMethod, and Address records with person/organization identity, customer/supplier roles, email/phone contacts, structured addresses, service APIs, scoped selectors, and operational screens.
- Company-owned Product, ProductVariant, ProductCategory, Attribute, AttributeValue, and VariantAttributeValue records with service APIs, scoped selectors, manifests, migrations, and operational screens.
- Explicit company selection for the existing HTTP-to-BusinessContext adapter so normal UI workflows do not rely on implicit global scope.
- Search/filter lists, Party and Product create/edit/detail screens, category and attribute/value management, and explicit variable-variant management.

### Product and variant decisions

- `Product` owns conceptual identity, type, structure, category, default UoM, descriptions, sell/purchase flags, activity, and company scope. It has no SKU or stock fields.
- `ProductVariant` owns the company-scoped SKU, Product relationship, default marker, activity, and timestamps. `(company, sku)` is unique and SKU values are stored uppercase.
- Product structure is immutable after creation. A simple Product is created atomically with exactly one default ProductVariant; its UI exposes only the SKU and does not expose variant management.
- A variable Product is created atomically with one or more caller-supplied variants. Additional variants and attribute-value assignments are explicit; no combinations are generated.
- PostgreSQL enforces at most one default variant per Product. Model/service validation also prevents additional or non-default variants on a simple Product.
- VariantAttributeValue stores the explicit Attribute alongside AttributeValue so PostgreSQL can enforce at most one value for each `(variant, attribute)` pair. Services validate that all composed records share one company.
- Service Products follow the same default-variant contract and do not import or require Inventory.

### Party decisions

- Party uses one person/organization identity with reusable customer and supplier flags rather than separate Customer/Supplier tables.
- Party, ContactMethod, and Address carry explicit company scope. Company/owner reassignment is rejected through model save paths.
- Email contacts are normalized to lowercase and validated. At most one primary contact of each kind and one default address per Party are database-enforced.

### Service and selector boundaries

- All company-scoped state-changing functions accept framework-neutral BusinessContext and validate existing organization grants before resolving or writing records.
- Cross-company relationship identifiers are rejected in service paths. Reusable reads validate BusinessContext and filter explicitly by company.
- Party and Catalog manifests validate and register through the existing module registry convention. Catalog has no Party, Inventory, Sales, Procurement, Billing, or vertical dependency.
- Core contains no reverse imports into Party or Catalog. The only core change is the small company-scope HTTP form/view that adapts session selection to the existing BusinessContext contract.

### Migrations

- `party.0001_initial` creates Party, ContactMethod, Address, their company indexes, and primary/default uniqueness constraints; `party.0002_register_manifest` registers the disabled-by-default Party manifest without overwriting future enablement.
- `catalog.0001_initial` creates Product, ProductVariant, ProductCategory, Attribute, AttributeValue, VariantAttributeValue, company indexes, SKU/default-variant constraints, and assignment-integrity constraints; `catalog.0002_register_manifest` registers the disabled-by-default Catalog manifest without overwriting future enablement.
- A fresh empty PostgreSQL database successfully applied the complete Phase 0 and Phase 1 migration history and was removed after verification.

### Verification

- `pytest` — 51 passed on Python 3.13/PostgreSQL, including module-local Party and Catalog tests.
- `ruff check .` — passed.
- `python manage.py check` — passed with no issues.
- `python manage.py makemigrations --check` — no changes detected.
- `npm ci` — passed with no vulnerabilities; `npm run build:css` reproduced the committed Tailwind asset.
- Docker Compose rebuilt and started with healthy PostgreSQL and the web service available on port 8000.
- Desktop 1280×720 and mobile 390×844 browser checks passed for Party, Catalog, simple Product, variable Product, responsive layout, and mobile navigation.
- Service and UI tests prove simple-product default-variant creation, service-product independence, explicit multiple variants, SKU uniqueness, attribute integrity, company isolation, and absence of authoritative stock fields.

### Remaining concerns and deliberate limits

- The mandatory child-existence rule cannot be represented as a normal portable Django database constraint. Product creation/update is therefore an atomic service contract, reinforced by Product/ProductVariant model validation and database constraints for the enforceable uniqueness portions. Bulk ORM updates or raw SQL must not bypass these contracts.
- Product structure transition is intentionally absent; simple-to-variable conversion requires a future explicit service and migration policy rather than direct field editing.
- Variant combinations, advanced configurators, pricing, stock, barcode infrastructure, media, tax, workflows, events, and Phase 2 modules remain deliberately absent.

### Next task

Review and freeze the published Party and Catalog contracts. Do not begin Phase 2 until architecture review accepts Phase 1.
