# BusinessOS Dependency Map

## Goal

Keep module dependencies one-directional and predictable so Codex agents can work in parallel without creating circular coupling.

This document defines **hard dependencies** only: dependencies required for a module to provide its own meaningful core capability.

Cross-capability automation that is useful only when two otherwise-independent modules are enabled is an **optional integration**, not a hard dependency. See ADR 0002.

## Import-direction notation

Every arrow in this document uses one meaning:

```text
consumer -> dependency
```

`sales -> catalog` means Sales may import Catalog's public contracts or call its services. It never means that Catalog imports Sales, nor does it merely describe business-data flow.

## Initial hard-dependency graph

```text
organization -> common, reference
audit -> common, identity, organization
access -> common, identity, organization, audit
module registry -> access

party -> identity, organization, reference, access
catalog -> reference, organization, access

sales -> party, catalog, organization, reference, access
procurement -> party, catalog, organization, reference, access
inventory -> catalog, organization, reference, access
billing -> party, organization, reference, access
accounting -> party, organization, reference, access
hr -> party, organization, reference, access

ecommerce -> catalog, sales, billing
school -> party, hr, billing
hospital -> party, hr, billing
hotel -> party, hr, billing
```

This graph is intentionally conservative. A module may use fewer hard dependencies than shown.

Inventory, Accounting and other capabilities may be composed with these modules through optional integrations without becoming mandatory hard dependencies.

## Core dependencies

Core apps may depend on lower-level shared utilities but must not import business modules.

Core Foundation v1 keeps audit below access: access services may append audit records, while audit
does not import access. The module registry depends on the Access permission identity only to
register manifest declarations deterministically.

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

Owns reusable product/service/category concepts. It must not depend on Sales, Procurement, Inventory, Billing or a vertical module.

Catalog must remain usable for non-stock products and services.

### Sales

Owns sales quotation/order lifecycle and depends on Party/Catalog plus core organizational/reference/access capabilities.

Sales must remain usable for service businesses that do not enable Inventory.

When Inventory is enabled, stock reservation/issue is an optional integration and must use Inventory's public service contract. Sales must never write stock rows directly.

Sales must not own stock balances, invoices/payments or accounting ledgers.

### Procurement

Owns purchase request/order lifecycle and depends on Party/Catalog plus core organizational/reference/access capabilities.

Procurement must remain usable for non-stock purchases and services.

When Inventory is enabled, receiving stock is an optional integration and must use Inventory's public service contract. Procurement must never write stock rows directly.

Procurement must not own stock balances, invoices/payments or accounting ledgers.

### Inventory

Depends on Catalog plus core organization/reference/access capabilities.

It owns stock movement/ledger behavior. Other modules must not directly mutate its authoritative stock ledger.

### Billing

Owns invoices/credit documents/payment orchestration and depends on Party plus core organization/reference/access capabilities.

Billing must be usable independently by Sales, Procurement and vertical products such as School, Hospital and Hotel.

References to upstream business documents should use stable identifiers/contracts rather than hard imports back into Sales/Procurement.

When Accounting is enabled, financial posting is an optional integration that must call Accounting's public service contract. Billing is not the owner of the general ledger.

### Accounting

Owns chart of accounts, journals and journal entries. It depends on Party plus core organization/reference/access capabilities.

Other modules request postings through Accounting services when the optional integration is enabled; they do not directly manipulate ledger rows.

Accounting must remain usable without Billing.

### HR

Owns employee/attendance/leave concepts. Vertical modules may reference HR employee identities instead of reimplementing staff records.

## Vertical rule

Vertical modules are composition layers. They may depend on shared modules, but shared modules must never depend on a vertical.

A vertical should declare only capabilities required for its base workflow. Additional capabilities such as Inventory, Accounting, Documents or Notifications may be enabled through explicit composition/integration when needed.

Not allowed:

```text
billing -> school
inventory -> hospital
party -> hotel
```

## Ecommerce rule

Ecommerce must reuse Catalog, Sales and Billing rather than create separate authoritative copies of products, orders or invoices.

Inventory availability/reservation is an optional integration so Ecommerce can also support non-stock/service/digital scenarios.

## Optional integration examples

These are business flows, not hard dependency declarations:

```text
Sales confirmation -> Inventory reserve/issue
Procurement receipt -> Inventory receive
Billing invoice/payment -> Accounting posting
Ecommerce checkout -> Inventory availability/reservation
Hospital pharmacy -> Inventory issue
```

When implemented, integrations must use owning-module public services/contracts and must not directly write another module's authoritative tables.

Do not introduce a generic event bus, plugin runtime or DI framework merely to implement these integrations. Use the smallest explicit seam justified by the real flow.

## Cross-module writes

When an owning module exposes an established service, call that service instead of writing its tables directly.

Early implementation may be synchronous/in-process. An event bus can be introduced later when there is a real need.

## Circular dependency policy

Circular module imports are prohibited. If two modules appear to require each other:

1. decide whether the relationship is actually an optional integration;
2. identify the authoritative concept owner;
3. move only truly shared primitives downward;
4. use stable identifiers/public services rather than reverse imports;
5. if still necessary, document an architecture decision before coding.

## Parallel Codex ownership

After Phase 0 freezes core contracts, module agents should own only their module directory. Changes to `core/`, shared contracts or this dependency map are integration/architect tasks and must not be made casually by parallel agents.
