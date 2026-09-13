# BusinessOS Module Boundaries

## Purpose

BusinessOS must ship modules quickly without becoming one tightly coupled Django application. Boundaries are deliberately lightweight: enough discipline for future growth, not enough ceremony to slow delivery.

## Core vs business modules

### Core

Core contains only capabilities that are truly shared infrastructure:

- identity
- organization
- access
- reference data
- common utilities
- module registry

Core must not contain Sales, Inventory, Accounting, HR, School, Hospital, Hotel or other business-specific workflows.

### Shared business modules

Reusable business capabilities live under `businessos/modules/`.

Initial shared modules:

- party
- catalog
- sales
- procurement
- inventory
- billing
- accounting
- hr
- ecommerce

### Vertical modules

Vertical modules compose/reuse shared modules rather than reimplementing them.

Initial verticals:

- school
- hospital
- hotel

Future examples:

- restaurant
- salon
- manufacturing
- garments
- construction
- fleet
- legal
- travel

## Ownership rule

A concept has one authoritative owning module.

Examples:

- customer/supplier/person/organization identity -> Party
- product/service/category -> Catalog
- sales order lifecycle -> Sales
- purchase order lifecycle -> Procurement
- stock movement -> Inventory
- invoice/payment orchestration -> Billing
- journal entries/chart of accounts -> Accounting
- employee/leave/attendance -> HR

Other modules reference the owning concept; they do not create competing copies.

## Integration rule

Early BusinessOS may use direct Python service calls between allowed dependencies. Do not introduce an event bus just to decouple code cosmetically.

When repeated cross-module integration becomes difficult, extract explicit contracts/events later.

## Business logic rule

Business workflows belong in services, not in views/templates/admin/forms/signals.

Django signals must not become hidden workflow orchestration. Use signals only for truly local technical concerns where explicit service calls would add no value.

## Client extension rule

Client-specific behavior belongs under:

```text
businessos/extensions/<client_code>/
```

Standard modules expose intentional extension seams only as repeated needs emerge. Avoid speculative hook frameworks.

## UI rule

Normal ERP screens use Django templates + HTMX/Alpine where useful. React is reserved for UI that genuinely benefits from complex client-side state, such as a future workflow designer, Studio, page builder or advanced spreadsheet-like interface.

## Reporting rule

Operational reports may initially use Django ORM/SQL/selectors. Do not force transactional models to serve every future analytics need. Read models, materialized views or a warehouse can be introduced later.

## Data isolation rule

Company scope is explicit on company-owned business records. A module must not expose data from companies/branches/warehouses outside the actor's allowed scope.

## Avoid these anti-patterns

- client-name conditionals in standard modules
- duplicate Customer/Product/Payment concepts in vertical modules
- business logic in views
- circular imports between business apps
- authoritative mutable `product.stock`
- authoritative mutable accounting balances
- one giant `utils.py` containing business behavior
- premature generic workflow/event/plugin frameworks
- cross-module database writes that bypass the owning module's service contract when an established service exists
