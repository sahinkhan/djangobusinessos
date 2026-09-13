# BusinessOS Codex Operating Contract

BusinessOS is developed with a speed-first, future-proof architecture.

## Product direction

BusinessOS starts as a simple modular Django monolith so business modules can be shipped quickly. It must remain evolvable toward a larger enterprise platform and, if justified later, toward a custom Python runtime without rewriting business rules.

## Read before changing code

Before implementing a task, read:

- `docs/architecture/BASELINE.md`
- `docs/architecture/MODULE_BOUNDARIES.md`
- `docs/architecture/DEPENDENCY_MAP.md`
- `docs/ROADMAP.md`
- the active execution plan under `docs/exec-plans/active/`

If a task conflicts with those documents, do not silently expand or change architecture. Follow the baseline unless the task explicitly authorizes an architecture change.

## Non-negotiable rules

1. Do not put business rules in Django views, templates, serializers, admin classes, or form classes.
2. State-changing business operations belong in module `services.py` or `services/`.
3. Pure calculations and domain rules should be framework-neutral Python where practical.
4. Django ORM usage is allowed inside services/selectors in the early product. Do not build repository abstractions without a demonstrated need.
5. Query/read logic that is reused or non-trivial belongs in `selectors.py` or `selectors/`.
6. Client-specific behavior must never be hard-coded into standard modules. Put it under `businessos/extensions/` or promote it to a configurable standard feature.
7. Do not add a generic workflow engine, metadata engine, event bus, command bus, DI container, custom ORM, plugin marketplace, or custom router before the roadmap reaches that capability.
8. Do not add Redis, Celery, React, Kafka/NATS, Elasticsearch, Go services, or additional infrastructure without an actual requirement or an approved execution plan.
9. Every business record that needs organizational isolation must have explicit company/organization scope. Never rely on implicit global state for authorization.
10. Cross-module imports must follow `docs/architecture/DEPENDENCY_MAP.md`. Do not create circular dependencies.
11. Historical released migrations are immutable. Add new migrations instead of editing deployed migration history.
12. Inventory source of truth is movement/ledger based; never make a mutable product stock field the authoritative stock record.
13. Accounting source of truth is balanced journal entries/lines; never maintain authoritative account balances with arbitrary direct updates.
14. Features should remain backward-compatible by default. Breaking behavior requires explicit versioning and migration notes.
15. Keep the core small. New shared platform abstractions are extracted only after repeated real module requirements prove they are useful.
16. Business services must not accept `HttpRequest`. Convert request/user/session state into a framework-neutral `BusinessContext` first.
17. Prefer boring, explicit code over speculative abstractions.
18. Do not fork standard modules for a client.

## Module convention

Standard business modules live under `businessos/modules/<module>/`.

Use the lightest structure that preserves boundaries:

- `models.py` — persistence/schema
- `domain.py` or `domain/` — framework-neutral rules/calculations
- `services.py` or `services/` — state-changing use cases
- `selectors.py` or `selectors/` — reusable/non-trivial reads
- `policies.py` — business authorization when required
- `forms.py`, `views.py`, `urls.py` — Django presentation layer only
- `manifest.py` — module identity/version/dependencies
- `tests/` — module tests

Do not introduce extra layers merely to satisfy a pattern.

## Framework portability rule

Request-specific details must be converted into a framework-neutral business context before they reach business services. Services should accept identifiers/data/context rather than a Django `HttpRequest` object.

Django is the current runtime, not the definition of BusinessOS business logic.

## Client customization rule

A client request must be classified before implementation:

- reusable for multiple clients -> configurable standard module feature
- unique to one client -> `businessos/extensions/<client>/`

Never add checks such as `if company.name == "Client A"` inside standard modules.

## Definition of Done

A task is not complete until all applicable checks pass:

- requirements implemented without unrelated scope expansion
- migrations created and reviewed
- relevant tests added or updated
- `pytest` passes
- `ruff check .` passes
- `python manage.py check` passes
- `python manage.py makemigrations --check` reports no missing migrations
- company/organization scope is verified for affected business records
- permissions are verified for affected actions
- no client-specific hard-coding was introduced
- architecture/docs are updated if a public contract changed

For accounting/inventory state transitions also verify:

- transaction atomicity
- duplicate-posting/idempotency behavior where applicable
- rollback/failure behavior

## Development style

Optimize first for correctness, module delivery speed, maintainability, and future replaceability. Build capabilities late; reserve boundaries early.
