# BusinessOS Dependency Map

## Goal

Keep module dependencies one-directional and predictable so Codex agents can work in parallel without creating circular coupling.

## Import-direction notation

Every arrow in this document uses one meaning:

```text
consumer -> dependency
```

`sales -> catalog` means Sales may import Catalog's public contracts or call its services. It never means that Catalog imports Sales, nor does it merely describe business-data flow.

## Initial dependency graph

```text
organization -> common, reference
access -> common, identity, organization

party -> identity, organization, reference, access
catalog -> party, reference
inventory -> catalog, organization, reference, access
sales -> party, catalog, inventory, organization, reference, access
procurement -> party, catalog, inventory, organization, reference, access
accounting -> party, organization, reference, access
billing -> party, sales, procurement, accounting, organization, reference, access
hr -> party, organization, reference, access

ecommerce -> catalog, sales, inventory, billing
school -> party, hr, billing, accounting
hospital -> party, hr, billing, inventory
hotel -> party, hr, billing, inventory
```

This graph is intentionally conservative. A module may use fewer dependencies than shown.

## Core dependencies

Core apps may depend on lower-level shared utilities but must not import business modules.

Examples of allowed imports:

```text
organization -> common/reference
access -> common/identity/organization
business modules -> core
```

Not allowed:

```text
core -> sales
core -> accounting
core -> school
```

## Business module rules

### Party

Owns shared person/organization/contact concepts. Must not depend on Sales, Inventory, Accounting or verticals.

### Catalog

Owns reusable product/service/category concepts. May depend on reference data and Party only where ownership/business rules justify it. It must not depend on Sales/Inventory.

### Sales

May depend on Party, Catalog, Inventory, Organization, Reference and Access. Any Inventory interaction must use Inventory's public service contract; Sales must not write stock rows directly.

It must not own stock balances or accounting ledgers.

### Procurement

May depend on Party, Catalog, Inventory, Organization, Reference and Access. Any receipt interaction must use Inventory's public service contract; Procurement must not write stock rows directly.

It must not own stock balances or accounting ledgers.

### Inventory

May depend on Catalog, Organization, Reference and Access.

It owns stock movement/ledger behavior.

### Billing

Owns customer/supplier billing and payment orchestration. It may depend on Party, Reference, Organization, Accounting, and relevant Sales/Procurement documents through stable identifiers or public service contracts. Billing is not the owner of general ledger accounting.

### Accounting

Owns chart of accounts, journals and journal entries. Other modules request postings through Accounting services; they do not directly manipulate ledger rows.

### HR

Owns employee/attendance/leave concepts. Vertical modules may reference HR employee identities instead of reimplementing staff records.

## Vertical rule

Vertical modules are composition layers. They may depend on shared modules, but shared modules must never depend on a vertical.

Not allowed:

```text
billing -> school
inventory -> hospital
party -> hotel
```

## Ecommerce rule

Ecommerce must reuse Catalog, Sales, Inventory and Billing rather than create separate authoritative copies of products, orders, stock or invoices.

## Cross-module writes

When an owning module exposes an established service, call that service instead of writing its tables directly.

Example:

```text
Sales service -> Inventory service to issue/reserve stock
Procurement service -> Inventory service to receive stock
Billing service -> Accounting service to create ledger posting
```

These examples follow the same `consumer -> dependency` import direction defined above. Inventory never imports Sales or Procurement, and Accounting never imports Billing.

Early implementation may be synchronous/in-process. An event bus can be introduced later when there is a real need.

## Circular dependency policy

Circular module imports are prohibited. If two modules appear to require each other:

1. identify the concept owner;
2. move truly shared primitives downward;
3. use identifiers/services rather than reverse imports;
4. if still necessary, document an architecture decision before coding.

## Parallel Codex ownership

After Phase 0 freezes core contracts, module agents should own only their module directory. Changes to `core/`, shared contracts or this dependency map are integration/architect tasks and must not be made casually by parallel agents.
