# BusinessOS Architecture Baseline

## Objective

Ship useful business modules quickly using Django while preserving clear seams for future enterprise capabilities and an optional custom Python runtime.

## Initial stack

- Python 3.13
- Django 5.2 LTS
- PostgreSQL
- Django Templates + Tailwind CSS + HTMX + Alpine.js
- pytest + pytest-django
- Ruff
- Docker Compose for development/deployment baseline

Redis, Celery, React, search engines, message brokers, Go services and custom framework components are not baseline dependencies. Add them only when justified by a concrete requirement.

## Architectural shape

```text
Django Runtime
    |
BusinessOS Core (small)
    |
Business Modules
    |
Client Extensions
    |
PostgreSQL
```

Django is an implementation runtime. Business rules must not depend on Django request/response objects.

## Core scope

The initial core contains only capabilities needed by many modules immediately:

- identity/authentication
- organization: company, branch, warehouse
- basic access control and organizational scope
- reference data: country, currency, language, unit of measure
- common utilities/base models
- lightweight module registry/manifests
- framework-neutral `BusinessContext`

Not part of the initial core:

- generic workflow engine
- metadata engine / Studio
- event bus
- dynamic plugin marketplace
- custom DI/container/router/ORM
- distributed messaging
- cloud control plane
- multi-tenant SaaS runtime

## Framework-neutral BusinessContext

Business services receive explicit context instead of `HttpRequest`.

Conceptual shape:

```python
@dataclass(frozen=True)
class BusinessContext:
    actor_id: UUID
    company_id: UUID
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None
```

The context may evolve later (for example tenant or locale information), but request-specific framework objects must not leak into business services.

## Module internal pattern

Use a lightweight pattern:

```text
module/
  models.py
  domain.py
  services.py
  selectors.py
  policies.py
  forms.py
  views.py
  urls.py
  manifest.py
  tests/
```

Split files into packages only after size/complexity justifies it.

### models

Persistence and relational schema. Models may contain small invariant helpers, but orchestration across aggregates/modules belongs in services.

### domain

Pure calculations, value rules and reusable framework-neutral invariants.

### services

State-changing use cases and transactional orchestration. Examples: confirm order, receive purchase, post invoice, check in guest.

### selectors

Reusable/non-trivial query logic and read models.

### policies

Business authorization beyond basic Django permissions.

### presentation

Views/forms/templates translate HTTP/user input to application calls and render output. They do not implement business workflows.

## Organization scope

BusinessOS initially uses separate deployment per customer, not SaaS multi-tenancy. Within a deployment it can support multiple companies, branches and warehouses.

Any record whose meaning is company-specific must have explicit company scope. Branch/warehouse scope is explicit where appropriate.

Do not use global mutable "current company" as the sole security mechanism. Authorization/query filtering must be based on allowed scope.

The concrete Phase 0 identity, administration, organizational-ownership, and context-validation contracts are recorded in `docs/decisions/0001-foundation-security-contracts.md`.

## Inventory invariant

Inventory source of truth is a stock movement/ledger model. Product stock is never the authoritative mutable source.

Examples:

- purchase receipt +quantity
- sale issue -quantity
- customer return +quantity
- supplier return -quantity
- transfer out/in
- adjustment

Derived balances may later be cached/materialized.

## Accounting invariant

Accounting source of truth is journal entry + journal lines. Posted entries must balance debits and credits. Account balances are derived, not arbitrarily mutated.

## Client customization

Standard module code remains product-owned and upgradeable.

```text
businessos/modules/...       # standard product
businessos/extensions/...    # client-specific customization
```

Reusable client requests should be promoted to configurable standard functionality. Unique requests remain extensions.

## Versioning

Each module has a manifest containing at least:

- code
- name
- semantic version
- dependencies

Module contracts should evolve backward-compatibly where practical. Client extensions may declare compatible module version ranges later.

## Future extraction path

The platform may evolve in this order:

1. Django modular ERP
2. shared platform services extracted from repeated needs
3. enterprise core: workflow/rules/audit/documents/integration
4. metadata/dynamic UI/Studio
5. developer SDK/marketplace/localizations
6. cloud control plane and ecosystem capabilities
7. optional custom Python runtime

A custom runtime migration, if ever justified, should replace adapters incrementally while retaining business services/domain rules.

## Guiding principle

**Build capabilities late; reserve boundaries early.**
