# ADR 0012 — Tenant-Ready Database Execution Foundation

Status: Accepted architecture direction by explicit milestone authorization;
implementation candidate awaiting independent architecture/concurrency audit.

Date: 2026-10-07

## Context and boundary

Canonical base is `65a0e46b51a05aab16de0958e6e0ea5882b3f7fd` (`ui-foundation-v1`). This
backend milestone reserves a database execution boundary before more business modules accumulate
implicit-default transaction assumptions. The current runtime remains single-database PostgreSQL.
This decision neither enables SaaS nor changes accepted domain lifecycles or company authorization.

ADR 0011 is reserved by preserved `billing-option-a-reconciliation` evidence at
`65600700395d2df923f2cf2b2a5fec5d0c96c8d8`; it is not restored or overwritten here.

Tenant is an infrastructure database boundary, **not Company**. Company remains a business-domain
scope. BusinessContext stays actor/company/branch/warehouse and does not gain tenant identity.
Future target (not implemented): shared Django application → approved tenant resolver → separate
PostgreSQL database per tenant → existing multi-company/branch/warehouse domain.

## Execution and transaction contract

`businessos.core.database` provides:

- `current_database_alias()`: `default` without an explicit execution scope;
- `database_execution(alias)`: configured-alias ContextVar selection, token restoration on normal
  and exceptional exits, nested scopes, independent threads/async tasks; unknown aliases fail closed;
- `@business_atomic`: synchronous operation boundary, selecting the alias on every call;
- `business_atomic_context()`: selects at context entry, not context construction. Optional
  `using=resolved_alias` aligns explicit model/queryset validation reads and writes.

Transactions retain Django atomic/savepoint behavior and existing lock order. A business transaction
pins its alias: selecting another alias inside it is rejected rather than pretending to offer a
distributed transaction. Async transactions are not added; Django synchronous business operations
must run through a synchronous adapter. Context selection is not authorization. New mutations use
these helpers; existing correct explicit `transaction.atomic(using=resolved_alias)` remains valid.

Audit uses the same execution scope/connection as the aggregate transaction. No event bus, ORM
replacement, repositories, `on_commit` abstraction or raw-SQL layer is introduced.

## Minimal ORM routing

The configured `BusinessDatabaseRouter` resolves owned Core/module models through the active alias.
Ownership follows installed AppConfig namespaces, not a list of app labels. Migration StateApps have
label-only configs, so ownership falls back to the installed namespace using the historical model's
app label. This keeps immutable registration RunPython behavior usable under the selected scope.

In normal single-DB mode, owned reads/writes resolve to `default`; unowned models return no routing
opinion and retain Django behavior. `allow_migrate` and `allow_relation` return no opinion. Django
sessions/admin/auth technical tables, control-plane tables and subscriptions have no new placement
policy. Explicit QuerySet `.using(alias)` bypasses routers by Django design; operators must keep it
aligned with the execution scope. Do not carry cached models/relations across execution scopes or
use explicit aliases to split one business operation. Those are not tenant-isolation APIs.

This is readiness infrastructure, **not a cross-tenant security boundary**. Actual tenancy activation
needs full technical-model routing, request/worker/task lifetimes, explicit-alias/cached-instance
policy, tenant validation and operational isolation review before customer exposure.

## Historical migration and bootstrap contract

No schema or migration changes. Existing migrations, including Core/Party/Catalog/Sales/Procurement/
Inventory registration RunPython declarations, remain immutable. Future provisioning must configure
the alias first and establish **both** the execution context and migration target:

```python
with database_execution(configured_alias):
    call_command("migrate", database=configured_alias)
    call_command("seed_reference_data")
    call_command("seed_phase1_demo")  # Only if explicitly requested for that database.
```

`--database` alone does not scope historical implicit ORM reads/writes in RunPython. This milestone
does not implement a provisioning command. Development migration drift checks remain normal
single-database checks; final SaaS migration/technical-table policy is deferred.

## Guardrails and consequences

AST regressions scan active Core/modules/config (excluding migrations/tests/approved database
infrastructure), rejecting implicit atomic and on-commit usage, default connection imports/literals
and hardcoded `.using("default")`/`db_manager`. Explicit resolved aliases remain allowed. This is a
review/regression guard, not a security sandbox against arbitrary Python metaprogramming.

BusinessContext, authorization, scope, lock order, retry, snapshot, audit, rollback, stock-ledger,
monetary and UI semantics remain unchanged. No models/columns/migrations/tenant identity, middleware,
dynamic DB credentials, cache/jobs/files routing, subscriptions, Redis/Celery or new integrations.
Billing/Payments/Accounting remain stopped. The frozen UI and existing npm advisories are untouched.

Implementation evidence and per-occurrence inventory live in
`docs/exec-plans/active/TENANT_READY_DATABASE_FOUNDATION.md`. Local verification is not independent
acceptance, hosted CI, publication or main adoption. One local candidate commit only, then STOP.

Underlying Django behavior: [multiple databases](https://docs.djangoproject.com/en/5.2/topics/db/multi-db/)
and [atomic transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).
