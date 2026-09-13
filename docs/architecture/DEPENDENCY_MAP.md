# BusinessOS Dependency Map

## Goal

Keep module dependencies one-directional and predictable so Codex agents can work in parallel without creating circular coupling.

## Initial dependency graph

```text
identity   organization   reference   access
    \          |             |         /
     \_________|_____________|________/
                 |
               party
                 |
               catalog
        _________|____________
       |         |            |
     sales   procurement   inventory
       |         |            |
       |_________|____________|
                 |
               billing
                 |
             accounting

hr -------------------------------> vertical modules

catalog + sales + inventory + billing ---> ecommerce
party + hr + billing + accounting ------> school
party + hr + billing + inventory -------> hospital
party + hr + billing + inventory -------> hotel
```

This graph is intentionally conservative. A module may use fewer dependencies than shown.

## Core dependencies

Core apps may depend on lower-level shared utilities but must not import business modules.

Allowed direction:

```text
common/reference -> organization/access -> business modules
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

May depend on Party, Catalog, Organization, Reference and Access.

It must not own stock balances or accounting ledgers.

### Procurement

May depend on Party, Catalog, Organization, Reference and Access.

It must not own stock balances or accounting ledgers.

### Inventory

May depend on Catalog, Organization, Reference and Access.

It owns stock movement/ledger behavior.

### Billing

Owns customer/supplier billing and payment orchestration. It may depend on Party, Reference, Organization and relevant commercial documents through stable identifiers/service contracts. Avoid making Billing the owner of general ledger accounting.

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
Sales confirm -> Inventory service to issue/reserve stock
Billing post -> Accounting service to create ledger posting
```

Early implementation may be synchronous/in-process. An event bus can be introduced later when there is a real need.

## Circular dependency policy

Circular module imports are prohibited. If two modules appear to require each other:

1. identify the concept owner;
2. move truly shared primitives downward;
3. use identifiers/services rather than reverse imports;
4. if still necessary, document an architecture decision before coding.

## Parallel Codex ownership

After Phase 0 freezes core contracts, module agents should own only their module directory. Changes to `core/`, shared contracts or this dependency map are integration/architect tasks and must not be made casually by parallel agents.
