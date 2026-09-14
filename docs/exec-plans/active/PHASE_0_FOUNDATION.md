# Phase 0 — Foundation Execution Plan

## Status

COMPLETE — CORE FOUNDATION V1 FROZEN; INDEPENDENT GATE 2 RE-AUDIT FINAL PASS

The original Phase 0 implementation was accepted, then Foundation correctness was reopened by an
independent adversarial audit that reproduced four authorization, ownership, immutable-evidence and
bulk-mutation findings. Remediation was implemented and independently re-audited. Gate 2 FINAL PASS
was restored, ADR 0009 was re-accepted, and Core Foundation v1 is FROZEN at implementation
`f1f7f2f6c917308bedb3c48e51b8113a064d96c2`. The formal closure checkpoint before this documentation
preflight is `5e824f83ae1c13364f35731d9d00c7ff830b6c54`.

The earlier reopened state remains historical evidence, not the current status. Gate 3 canonical
normalization and Phase 2 continuation have not started and require separate authorization. See
`CORE_FOUNDATION_V1_RESTRUCTURE.md` and ADR 0009 for the complete reopening and remediation record.

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

### Commit / PR

The verified implementation is published from the `phase0-foundation` branch against the existing `origin/main` architecture history. Git history and the Phase 0 pull request are the source of truth for immutable commit and review identifiers.

### Delivered

- Django 5.2 project with split base, development, production, and test settings.
- PostgreSQL-first runtime configuration, Python 3.13 Docker image, and Compose development stack with a PostgreSQL health check.
- Case-insensitive, canonical email-identity custom `User` model with UUID primary key, database enforcement, and Django permissions/admin integration.
- UUID-based `Company`, `Branch`, and `Warehouse` models, including company-scoped codes, base currency, optional warehouse branch, active state, timestamps, and cross-company validation.
- Minimal `Country`, `Currency`, `Language`, and `UnitOfMeasure` reference models plus an idempotent starter-data command.
- Explicit user-to-company, user-to-branch, and user-to-warehouse access grants and a selector that does not expose ungranted companies. Core Django admin is restricted to deployment superusers.
- Immutable, framework-neutral `BusinessContext`, a reusable non-HTTP validation policy, and a Django request/session adapter.
- Small validated semantic-version module manifest contract, database registry, registration service, and a manifest-only convention example.
- Shared responsive template shell with a compiled local Tailwind 3.4 stylesheet, login, sidebar, header, breadcrumbs, page heading, messages, cards, tables, form styles, modal root, pagination, and empty-state components.
- Pytest/pytest-django discovery for both top-level and module-local tests, Ruff configuration, migrations, admin registrations, setup documentation, pinned dependency files, frontend lockfile, and CI workflow.

### Important decisions

- Normal runtime settings are PostgreSQL-only. The dedicated test settings use in-memory SQLite for fast isolated local tests; the same suite was also run successfully against PostgreSQL in Compose.
- Access is represented by explicit grant records rather than a global current-company field. Superusers may access active organizational scope without grant rows; all other users require company access and any selected branch/warehouse grant.
- Django admin is deployment-wide and superuser-only. Future company-scoped administration must use application views that apply `BusinessContext` rather than model-wide admin permissions.
- Branch and Warehouse company ownership is immutable. Warehouse branch changes remain allowed only
  within the same company. Active Warehouses must be deactivated or reassigned before their Branch
  can be deactivated; legacy or corrupt inconsistent scope is still denied by context validation.
- Email is stored trimmed/lowercase, authenticated case-insensitively, and protected by both Django's unique username requirement and a database `LOWER(email)` constraint.
- Scope integrity is checked independently from permission bypasses. The reusable `validate_business_context` policy serves HTTP and non-HTTP callers.
- Module discovery/loading is intentionally absent. Manifest registration preserves enablement unless the caller changes it explicitly.
- Tailwind 3.4 is built into a committed local stylesheet from pinned npm dependencies; HTMX and Alpine remain version-pinned CDN scripts.

### Deviations / ADRs

No baseline deviation was required. `docs/decisions/0001-foundation-security-contracts.md` records the Phase 0 administration, identity, ownership, context, and registry contracts exposed by audit remediation. `docs/architecture/DEPENDENCY_MAP.md` now defines every arrow as `consumer -> dependency` and explicitly permits Sales/Procurement to call Inventory services without reverse imports.

### Verification

Run in the Python 3.13.15 Compose web service:

- `pytest` — 32 passed against PostgreSQL, including audit regressions and module-local discovery.
- `ruff check .` — passed.
- `python manage.py check` — passed with no issues.
- `python manage.py makemigrations --check` — no changes detected.
- `python manage.py check --deploy` with temporary production environment values — passed with no issues.
- Clean PostgreSQL bootstrap — all first-party and Django migrations, including case-insensitive email enforcement, applied successfully to a uniquely named empty disposable database.
- `python manage.py seed_reference_data` — 8 starter records created successfully; the command is idempotent.
- HTTP smoke check — `/login/` returned 200 after startup.
- Visual browser verification — login and authenticated shell passed at 1280×720 and 390×844; correct computed colors, no horizontal overflow, persistent desktop navigation, and functional mobile navigation were confirmed.
- `npm ci` and `npm run build:css` — passed using the frontend lockfile.

### Audit remediation

- Closed P1 admin isolation by making the entire routed core admin site active-superuser-only; regression tests prove a staff user with view/change model permissions cannot edit another company.
- Closed P1 ownership integrity by making Branch and Warehouse company ownership immutable and retaining same-company Warehouse/Branch validation.
- Closed P2 identity inconsistencies across manager, model, admin forms, authentication, migration, and database uniqueness.
- Closed P2 required-context and superuser scope defects, and added one reusable non-request validation policy.
- Closed P2 Tailwind incompatibility with a compiled Tailwind 3.4 asset and desktop/mobile browser verification.
- Closed P2 test discovery by collecting top-level and `businessos/` tests and proving module-local discovery.
- Closed the dependency-map ambiguity and reconciled Inventory/Accounting service-call examples with explicit allowed import direction.
- Closed code-normalization form failures, SemVer prerelease/build validation gaps, and implicit module disabling.

### Remaining Phase 0 concerns

- Hosted CI passed for the published foundation/Phase 1 base, Phase 0 received technical approval, and the foundation security/module contracts were formally frozen before Phase 1 opened.
- Production launch remains blocked on a chosen production process manager/hosting topology, HTTPS and secrets delivery evidence, backup/recovery, monitoring, and login-attempt limiting or an explicitly verified edge control.
- Company/user locale preferences and translation conventions should be decided before broad UI development; country-specific tax/payroll behavior remains correctly deferred to localization phases.
- A project license requires an owner decision and was not invented by this implementation session.

### Next recommended task

Phase 0 implementation and Core Foundation v1 acceptance are complete. Gate 3 pre-release canonical
normalization is the next gated sequence, but it has not started and requires separate explicit
authorization. Do not modify canonical `main`, normalize migrations/history, or continue Phase 2 as
part of this documentation preflight.
