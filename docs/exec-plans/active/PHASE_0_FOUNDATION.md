# Phase 0 — Foundation Execution Plan

## Status

Active

## Objective

Create the smallest production-quality Django foundation that allows business modules to be built quickly and in parallel without locking BusinessOS permanently to Django presentation/runtime details.

This phase is intentionally narrow. Do not implement business modules yet.

## Required reading

Before coding:

- `AGENTS.md`
- `docs/architecture/BASELINE.md`
- `docs/architecture/MODULE_BOUNDARIES.md`
- `docs/architecture/DEPENDENCY_MAP.md`
- `docs/ROADMAP.md`

## Technology contract

- Python 3.13
- Django 5.2 LTS
- PostgreSQL
- pytest + pytest-django
- Ruff
- Django templates
- Tailwind CSS + HTMX + Alpine.js for the shared shell if integration can remain simple
- Docker Compose development environment

Do not add DRF, Redis, Celery, React, message brokers, Elasticsearch, Go services or custom framework components in Phase 0.

## Repository target shape

```text
config/
  settings/
    base.py
    dev.py
    production.py
  urls.py
  asgi.py
  wsgi.py

businessos/
  core/
    identity/
    organization/
    reference/
    access/
    common/
    modules/
  modules/
  extensions/

templates/
static/
tests/
```

Packages may contain additional files needed by Django, but do not create speculative architecture layers.

## Deliverables

### 1. Project bootstrap

Create:

- Django project/config
- environment-driven settings
- PostgreSQL configuration
- `.env.example`
- `pyproject.toml`
- `.gitignore`
- Dockerfile
- `compose.yaml`
- basic developer commands/documentation

No secrets committed.

### 2. Custom User

Create a custom User model from the beginning so later identity changes do not require replacing Django's default user table.

Keep it minimal. Do not build SSO/OAuth/enterprise IAM in this phase.

### 3. Organization

Implement minimum models:

- Company
- Branch
- Warehouse

Requirements:

- stable UUID primary identifiers unless a documented implementation reason argues otherwise
- `created_at` / `updated_at`
- active/inactive state where useful
- Branch belongs to Company
- Warehouse belongs to Company and may optionally relate to Branch
- sensible unique constraints scoped to Company where appropriate

Do not implement business group, region, cost center, profit center or operating unit yet.

### 4. Reference data

Implement minimal reference models:

- Country
- Currency
- Language
- UnitOfMeasure

Keep these generic and small. No advanced UoM conversion engine, tax localization or exchange-rate service yet.

Company should have a base currency and useful locale/reference fields only where needed by the baseline.

### 5. Access foundation

Implement a simple foundation for organizational access:

- roles/permissions may use Django's permission system where practical
- explicit user-company access
- explicit user-branch access if needed for baseline
- explicit user-warehouse access if needed for baseline

Do not build a generic ABAC/policy engine.

The design must support verifying whether an actor may operate in a `BusinessContext`.

### 6. BusinessContext

Implement a framework-neutral Python context object conceptually equivalent to:

```python
@dataclass(frozen=True)
class BusinessContext:
    actor_id: UUID
    company_id: UUID
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None
```

Provide a Django adapter/helper that builds and validates the context from the authenticated request/session, but business services must not accept `HttpRequest`.

Do not add tenant_id in Phase 0.

### 7. Module manifest/registry

Create a lightweight module contract capable of representing:

- module code
- name
- version
- dependencies
- enabled/disabled state where appropriate

This is not a runtime plugin installer. No arbitrary code loading, marketplace, dependency solver or migration orchestrator.

Provide at least one proof/example internal module manifest to demonstrate convention without implementing a business module.

### 8. Common base

Provide only genuinely useful shared primitives, for example:

- UUID/timestamp base model if chosen
- common active-state pattern if justified
- document/sequence abstraction only if it can remain very small; otherwise defer it

Do not create a generic repository, unit-of-work, command bus or event bus.

### 9. Shared UI shell

Implement a clean professional base layout sufficient for module teams to reuse:

- login page
- application shell
- sidebar
- header/top bar
- breadcrumbs/page title pattern
- flash/toast message area
- reusable table/form styling conventions
- responsive behavior

No dashboard builder, page builder or dynamic metadata UI.

### 10. Testing/tooling

Configure:

- pytest
- pytest-django
- factories/fixtures only where useful
- Ruff

Tests must cover at least:

- organization relationships/constraints
- custom user creation
- access scoping basics
- BusinessContext validation/building
- module manifest validation/registry basics

### 11. Documentation

Update/create:

- README setup instructions
- architecture notes only if implementation differs from baseline
- Phase 0 outcome section in this file

## Explicitly forbidden scope

Do not implement any of these in Phase 0:

- Sales
- Procurement
- Inventory
- Billing
- Accounting
- HR
- Ecommerce
- School
- Hospital
- Hotel
- generic workflow engine
- metadata/Studio/dynamic UI
- event bus
- Celery
- Redis
- React
- API platform
- multi-tenancy
- marketplace/plugin runtime
- custom Python framework/runtime
- advanced audit platform
- search/reporting platform
- integrations

If a deliverable seems to require one of these, implement the smallest local solution or document the dependency for a later phase.

## Architecture acceptance tests

The implementation must satisfy these architectural checks:

1. no business rule accepts Django `HttpRequest`;
2. core has no dependency on future business modules;
3. organization/access data is explicit, not hidden global state;
4. no client-specific behavior exists;
5. no speculative framework infrastructure was introduced;
6. a future module agent can create a module without editing core internals except for intentional registration/configuration points.

## Required completion commands

Before declaring Phase 0 complete, run and report:

```bash
pytest
ruff check .
python manage.py check
python manage.py makemigrations --check
```

Also run migrations against PostgreSQL in Docker/dev and verify a clean bootstrap from an empty database.

## Handoff / freeze gate

Phase 0 is complete only after:

- all required checks pass;
- core contracts are documented;
- schema/migrations bootstrap cleanly;
- shared UI shell works;
- organization/access/BusinessContext behavior is tested;
- no forbidden scope was introduced.

After acceptance, freeze Phase 0 shared contracts enough to begin Phase 1 Party/Catalog work. Parallel business-module work must not begin before this gate.

## Outcome

To be filled by the implementing Codex session with:

- commit/PR reference
- delivered items
- deviations/ADRs
- commands/tests run
- known limitations
- next recommended task
