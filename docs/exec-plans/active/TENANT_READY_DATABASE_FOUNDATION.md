# Tenant-Ready Database Execution Foundation — Single-Database Compatibility Mode

## Status and authorization

IMPLEMENTED LOCAL CANDIDATE — awaiting independent architecture/concurrency audit.
Base `main` and annotated `ui-foundation-v1`:
`65a0e46b51a05aab16de0958e6e0ea5882b3f7fd`.
Branch: `tenant-ready-db-foundation`.
One logical local commit; no publication, tag, main adoption or SaaS activation authorized.

ADR 0012 records the implementation direction and limits. ADR 0011 remains reserved in preserved
Billing Option-A evidence `65600700395d2df923f2cf2b2a5fec5d0c96c8d8`; no Billing WIP restored.

## Outcome

Four small Core Database files provide execution-local alias selection, synchronous call/enter-time
atomic helpers, same-alias nesting, and a namespace-based router. No tenant model or tenant_id;
BusinessContext remains unchanged. Owned models default to the existing database. Technical apps and
migration/relation decisions retain Django defaults. Historical models resolve installed namespace
ownership so immutable registration migrations work inside a selected execution context.

50 decorators + two nested savepoints + 15 model/private transition blocks (67 implicit boundaries)
are adapted without changing lock statements, status checks, mutation/audit bodies or savepoint
extent. Explicit model save/delete aliases (including deprecated positional using) scope their
validation reads too; private transition QuerySets use their resolved `self.db`. Nested cross-alias
switches fail instead of splitting an aggregate transaction.

Organization's two already-resolved explicit transactions and their four `.using(using)` calls remain
byte-for-byte unchanged. Identity's `user.save(using=self._db)` remains unchanged (class E: Django
manager-selected explicit alias or router fallback). No runtime on_commit, raw SQL, raw cursor,
DEFAULT_DB_ALIAS, db_manager or hardcoded `.using("default")` was found.

Reference seeding has no outer implicit transaction: its per-record ORM writes now follow the router;
its existing partial-progress/idempotency semantics are retained. Phase 1 demo's outer atomic is
adapted; it is not turned into a provisioning command.

## Inventory classification

A = already alias safe; B = remediation needed; C = immutable migration/history; D = test-only;
E = justified explicit database/config usage. Line numbers below refer to exact starting SHA, not
post-refactor files. B atomic lines use BusinessOS helpers; B lock statements are unchanged and now
execute inside the alias-aware boundary with owned ORM routing. This covers complete active runtime
under Core, modules and config, not just public service decorators.


### businessos/core/access/services.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 27 | B | `@transaction.atomic` |
| 61 | B | `Company.objects.select_for_update().filter(id=context.company_id, is_active=True).first()` |
| 68 | B | `@transaction.atomic` |
| 85 | B | `@transaction.atomic` |
| 118 | B | `@transaction.atomic` |
| 126 | B | `Branch.objects.select_for_update()` |
| 146 | B | `@transaction.atomic` |
| 166 | B | `@transaction.atomic` |
| 174 | B | `Warehouse.objects.select_for_update()` |
| 194 | B | `@transaction.atomic` |
| 214 | B | `@transaction.atomic` |
| 229 | B | `@transaction.atomic` |
| 236 | B | `Role.objects.select_for_update()` |
| 257 | B | `@transaction.atomic` |
| 278 | B | `@transaction.atomic` |
| 302 | B | `@transaction.atomic` |

### businessos/core/modules/services.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 11 | B | `@transaction.atomic` |

### businessos/core/organization/models.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 191 | A | `using = using or router.db_for_write(type(self), instance=self)` |
| 192 | A | `with transaction.atomic(using=using):` |
| 194 | A | `Company.objects.using(using).select_for_update().filter(pk=self.company_id).first()` |
| 195 | A | `type(self).objects.using(using).select_for_update().filter(pk=self.pk).first()` |
| 236 | A | `using = using or router.db_for_write(type(self), instance=self)` |
| 237 | A | `with transaction.atomic(using=using):` |
| 238 | A | `Company.objects.using(using).select_for_update().filter(pk=self.company_id).first()` |
| 241 | A | `Branch.objects.using(using)` |
| 242 | A | `.select_for_update()` |

### businessos/modules/catalog/services.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 43 | B | `@transaction.atomic` |
| 85 | B | `@transaction.atomic` |
| 124 | B | `@transaction.atomic` |
| 169 | B | `@transaction.atomic` |
| 208 | B | `@transaction.atomic` |
| 232 | B | `@transaction.atomic` |
| 243 | B | `variant = ProductVariant.objects.select_for_update().select_related("product").get(` |
| 259 | B | `@transaction.atomic` |
| 269 | B | `@transaction.atomic` |
| 285 | B | `@transaction.atomic` |
| 291 | B | `variant = ProductVariant.objects.select_for_update().select_related("product").get(` |

### businessos/modules/inventory/models.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 44 | B | `with transaction.atomic():` |
| 46 | B | `movement = self.select_for_update().get(pk=movement_id)` |
| 196 | B | `with transaction.atomic():` |
| 198 | B | `type(self).objects.select_for_update().filter(pk=self.pk).exists()` |
| 205 | B | `with transaction.atomic():` |
| 208 | B | `.objects.select_for_update()` |
| 346 | B | `with transaction.atomic():` |
| 348 | B | `StockMovement.objects.select_for_update().filter(pk=self.movement_id).exists()` |
| 357 | B | `with transaction.atomic():` |
| 362 | B | `StockMovement.objects.select_for_update()` |

### businessos/modules/inventory/services.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 27 | B | `Company.objects.select_for_update()` |
| 108 | B | `return StockMovement.objects.select_for_update().get(` |
| 134 | B | `@transaction.atomic` |
| 170 | B | `with transaction.atomic():` |
| 195 | B | `@transaction.atomic` |
| 246 | B | `@transaction.atomic` |
| 267 | B | `@transaction.atomic` |
| 305 | B | `@transaction.atomic` |
| 343 | B | `@transaction.atomic` |

### businessos/modules/party/services.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 25 | B | `@transaction.atomic` |
| 50 | B | `@transaction.atomic` |
| 71 | B | `@transaction.atomic` |
| 95 | B | `@transaction.atomic` |
| 115 | B | `@transaction.atomic` |
| 155 | B | `@transaction.atomic` |

### businessos/modules/procurement/models.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 56 | B | `with transaction.atomic():` |
| 58 | B | `order = self.select_for_update().get(pk=order_id)` |
| 230 | B | `with transaction.atomic():` |
| 232 | B | `type(self).objects.select_for_update().filter(pk=self.pk).exists()` |
| 237 | B | `with transaction.atomic():` |
| 240 | B | `.objects.select_for_update()` |
| 370 | B | `with transaction.atomic():` |
| 372 | B | `PurchaseOrder.objects.select_for_update().filter(pk=self.purchase_order_id).exists()` |
| 377 | B | `with transaction.atomic():` |
| 388 | B | `PurchaseOrder.objects.select_for_update()` |
| 395 | B | `.objects.select_for_update()` |

### businessos/modules/procurement/services.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 40 | B | `Company.objects.select_for_update().filter(id=context.company_id, is_active=True).first()` |
| 84 | B | `return PurchaseOrder.objects.select_for_update().get(` |
| 215 | B | `@transaction.atomic` |
| 244 | B | `@transaction.atomic` |
| 272 | B | `@transaction.atomic` |
| 311 | B | `@transaction.atomic` |
| 354 | B | `@transaction.atomic` |
| 365 | B | `@transaction.atomic` |
| 397 | B | `@transaction.atomic` |
| 422 | B | `@transaction.atomic` |
| 454 | B | `for line in PurchaseOrderLine.objects.select_for_update().filter(` |
| 478 | B | `with transaction.atomic():` |

### businessos/modules/sales/models.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 51 | B | `with transaction.atomic():` |
| 53 | B | `order = self.select_for_update().get(pk=order_id)` |
| 195 | B | `with transaction.atomic():` |
| 197 | B | `type(self).objects.select_for_update().filter(pk=self.pk).exists()` |
| 202 | B | `with transaction.atomic():` |
| 205 | B | `.objects.select_for_update()` |
| 314 | B | `with transaction.atomic():` |
| 316 | B | `SalesOrder.objects.select_for_update().filter(` |
| 323 | B | `with transaction.atomic():` |
| 334 | B | `SalesOrder.objects.select_for_update()` |
| 341 | B | `.objects.select_for_update()` |

### businessos/modules/sales/services.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 23 | B | `Company.objects.select_for_update()` |
| 69 | B | `return SalesOrder.objects.select_for_update().get(` |
| 131 | B | `@transaction.atomic` |
| 160 | B | `@transaction.atomic` |
| 192 | B | `@transaction.atomic` |
| 231 | B | `@transaction.atomic` |
| 275 | B | `@transaction.atomic` |
| 289 | B | `@transaction.atomic` |
| 322 | B | `@transaction.atomic` |

### config/management/commands/seed_phase1_demo.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 145 | B | `@transaction.atomic` |

### config/settings/base.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 69 | E | `DATABASES = {` |

### config/settings/test.py

| Baseline line | Class | Original database boundary/assumption |
| --- | --- | --- |
| 3 | E | `DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}` |


### Additional explicit and historical cases

- E: `businessos/core/identity/managers.py:15`, `user.save(using=self._db)`, retained as above.
- E: `config/settings/base.py` and `test.py` default DATABASES definitions are the intentionally
  supported current single-DB configuration, not a business-operation assumption.
- C: all existing schema migrations under Identity, Reference, Organization, Access, Audit,
  Module Registry, Party, Catalog, Sales, Procurement and Inventory are immutable and unchanged.
- C: `access/0003_register_core_permissions.py` and each business module's
  `0002_register_manifest.py` retain frozen historical declarations. Their implicit historical ORM
  requires both selected execution context and explicit migration database target; see ADR 0012.
- C: Django's contributed migrations/technical tables are not rewritten or repartitioned.
- D: existing PostgreSQL test workers deliberately use default `connection`/atomic/cursors,
  `connections["default"]`, blocking PID probes and clean connection cleanup. These exercise the
  canonical single-DB contract; 96 PostgreSQL-only cases retain explicit SQLite skips.
- D: new alias-selection tests mock configured aliases; isolated in-memory SQLite tests exercise
  nondefault rollback and historical bootstrap/business flows with default cursor access forbidden.
- E: new database infrastructure alone owns the default fallback and explicit
  `transaction.atomic(using=alias)`. Static guard exempts this exact package, not every directory
  named database.
- No other active runtime raw SQL/on_commit/db_manager/default-connection assumptions were found.

## Verification record

Final local verification is recorded below before the one candidate commit. Hosted CI is not run:
publication is unauthorized. Independent architecture acceptance remains pending.

- Focused execution/router/AST tests: 37 passed, including import-alias guard regressions.
- Full PostgreSQL 17 / Python 3.13.16: 567 passed; no skips or teardown warnings.
- Full SQLite / Python 3.13.16: 471 passed, 96 expected PostgreSQL-only skips.
  The local Python 3.12.14 compatibility run also passed 471 with the same 96 skips.
- Concurrency: all 96 PostgreSQL-only cases passed in the full suite. Separate Foundation,
  Catalog, Sales lifecycle/foundation, Procurement concurrency and Inventory concurrency rerun:
  229 passed, including existing non-concurrency regressions in those files.
- Fresh PostgreSQL: zero-state migrate passed on PostgreSQL 17 / Python 3.13.16.
- Reference seed: 8 created then 0; demo: 14 created then 0 (18 already existed).
- Separate disposable PostgreSQL selected-alias probe migrated and seeded from zero, confirmed
  Sales, received Procurement with identical retry recovery, posted Inventory with repeat recovery
  and derived balance, and proved aggregate/audit rollback. Default target was deliberately
  unavailable; no default connection was opened. The auxiliary drift probe against unavailable
  default reported an expected connection warning; authoritative drift checks use the supported
  default configuration and must pass without warnings.
- No frontend rebuild required: frozen UI/assets/dependencies are untouched.
- Ruff passed on local and authoritative Python containers. Django checks reported zero issues;
  supported PostgreSQL and SQLite migration drift checks reported no changes. git diff --check
  passed. All 25 changed files were reviewed/classified below. Existing migration, UI, dependency,
  BusinessContext, Organization, Identity, Reference and Audit files are unchanged.
- Disposable PostgreSQL databases/containers/network are removed after final verification. Only
  task-created QA resources are removed; pre-existing Docker images and all preserved refs remain.

## Complete diff classification

| Category | Files |
| --- | --- |
| Database execution infrastructure | `businessos/core/database/__init__.py`, `execution.py`, `transactions.py`, `router.py` |
| Runtime boundary adapters | Core Access and Module Registry `services.py`; Party/Catalog/Sales/Procurement/Inventory `services.py`; Sales/Procurement/Inventory `models.py`; `config/management/commands/seed_phase1_demo.py` |
| Router activation | `config/settings/base.py` (one DATABASE_ROUTERS declaration only) |
| Regression tests | `tests/test_database_foundation.py`, `tests/test_database_architecture.py` |
| Architecture/status documentation | `docs/architecture/BASELINE.md`, `MODULE_BOUNDARIES.md`, `DEPENDENCY_MAP.md`; `docs/ROADMAP.md`; ADR 0012; this plan |
| Developer guidance | `AGENTS.md` |

Model files change transaction execution only, not schema/fields or domain checks. Existing tests
remain unchanged. No migration, UI, frontend build/dependency, Billing/Payment/Accounting or
BusinessContext file belongs to this diff.

## Deferred work and stop condition

No tenant registry/resolver/middleware/provisioning, DB credentials, control plane, subscriptions,
cross-tenant admin, per-tenant backup, cache/files/jobs policy or operational SaaS machinery.
Future activation must review Django technical-app placement, explicit aliases and cached objects,
worker context propagation, full migration/post-migrate policy and real tenant isolation.
ContextVar child tasks inherit their parent's context by Python semantics; infrastructure adapters
must delimit future request/task lifetimes, not spawn DB transactions into unrelated tasks.

Current single-DB compatibility is the acceptance target; no claim of production SaaS readiness.
Existing 8 npm advisories (2 moderate, 6 high) remain a separate production-security follow-up.
No dependency upgrades. Billing/Payments/Accounting remain stopped.

After local verification, exactly one local commit:
`refactor: add tenant-ready database execution foundation`.
STOP for independent audit. No push, merge, tag or main update.
