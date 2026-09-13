# Core Foundation v1 Restructure and Canonical Phase Reconstruction

## Status

Gate 1 implemented on `foundation-v1-hardening`; independent Gate 2 audit pending.

Implemented outcome:

- Core Access now owns company-scoped minimal RBAC and explicit organizational grant/revoke services.
- module manifests support deterministic, non-destructive permission registration;
- Core Audit records immutable security-action evidence;
- Company now owns country, default language and validated IANA timezone, while base currency is
  immutable through normal model/service mutation;
- Reference and permission codes are immutable identities;
- shared company-local datetime/date helpers establish the business-time contract;
- ADR 0009 records the candidate Core Foundation v1 boundary.

No Phase 2 branch was merged, no canonical history was rewritten, and no excluded infrastructure
or capability was introduced. Gate 2, Gate 3 and Phase 2 adoption remain unstarted.

Gate 1 implementation verification on 2026-09-14:

- PostgreSQL 17 / Python 3.13: 86 tests passed without teardown warnings;
- SQLite: 85 tests passed, with the existing PostgreSQL-only Catalog row-lock test skipped;
- Ruff, Django system checks and migration-drift checks passed;
- a zero-state PostgreSQL migration/bootstrap and Docker application startup passed;
- a pre-hardening Company row migrated successfully to explicit `ZZ` / `UND` / `UTC` values;
- module-local test discovery passed;
- the existing Phase 1 demo bootstrap remained idempotent;
- Tailwind output reproduced exactly; no UI files changed.

Known limitations at this gate:

- existing companies receive explicit unknown jurisdiction/language references and require operator
  correction before those values drive business behavior;
- direct raw SQL remains outside normal model/service immutability guarantees;
- Party/Catalog and accepted Phase 2 modules have not yet adopted fine-grained RBAC permissions;
- Core v1 is not frozen until independent Gate 2 review passes.

This plan is intentionally pre-release. Do not rewrite canonical history until the Core Foundation v1 implementation has passed independent review.

## Objective

Restructure BusinessOS so the canonical architecture and repository history represent:

```text
Phase 0
Complete Core Foundation v1

Phase 1
Party + Catalog

Phase 2
Commercial Core development
```

The goal is not to hide defects or fabricate history. The goal is to normalize a pre-release development repository so the final baseline accurately represents the architecture that will be supported going forward.

## Current safety references

Preserve these exact development reference points before any later history normalization:

```text
main
febe5b45941c6956fd98006c04abded16a9ff998

accepted Phase 1
361d832713dcd2325363b4059a4f3b6cac7d3715

Sales
2aeb01c2766da9e78dd04252cfb9d3b221828e6c

Procurement
a99377ca55355a2e4cdebd64ff73cf29fd3eff83

Inventory remediation reference at plan creation
f45afdfea33d3fd03d469e6a0cd63d0e5358f38c
```

Do not lose accepted business behavior from these branches.

---

# Gate 1 — Core Foundation v1 Hardening

Work on a dedicated foundation branch. Do not merge Sales, Procurement, Inventory, Billing or Accounting into this branch merely to implement Core concerns.

Core Foundation v1 must contain the following stable contracts.

## Identity

Preserve the existing UUID User identity and normalized case-insensitive email contract.

Do not redesign User identity during this hardening pass.

## Organization and company business identity

Preserve:

```text
Company
Branch
Warehouse
```

Extend Company with the minimum shared business identity needed by later modules:

```text
country
timezone
default_language
base_currency  # already exists
```

Country and default language must reuse Core Reference Data.

Timezone must be a validated IANA timezone identifier.

Company country, language and timezone may evolve through explicit supported update paths. Company base currency must not be casually changed through ordinary model/form/service mutation after creation. A future functional-currency change requires an explicit migration/business process and separate architectural approval.

Do not implement currency conversion in Core Foundation v1.

## Organizational access lifecycle

Preserve:

```text
UserCompanyAccess
UserBranchAccess
UserWarehouseAccess
```

Add explicit, boring services for organizational grants and revocation.

At minimum support deliberate operations equivalent to:

```text
grant_company_access
revoke_company_access
grant_branch_access
revoke_branch_access
grant_warehouse_access
revoke_warehouse_access
```

Company access revocation must prevent stale subordinate Branch/Warehouse grants from silently becoming effective again if company access is later restored. Use a simple explicit lifecycle; do not create a generic entitlement engine.

## Minimal RBAC

Add a minimal BusinessOS RBAC capability owned by Core Access:

```text
Permission
Role
RolePermission
UserRoleAssignment
```

Permission identity is stable and code-based.

Roles are reusable authorization bundles. User role assignments are company-scoped so the same user may have different roles in different companies.

Cross-company assignments must be rejected.

Provide public authorization contracts equivalent to:

```python
has_permission(context, permission_code)
require_permission(context, permission_code)
```

Authorization must validate BusinessContext first.

Superusers may bypass RBAC grants, but never organizational scope integrity or inactive/missing actor/company checks.

Business authorization is deny-by-default.

Do not add:

```text
ABAC
role inheritance
record-level ACL
field-level ACL
conditional policy DSL
approval engine
```

## Business authorization boundary

Freeze the following architectural rule:

```text
Django auth/model permissions
-> Django technical/admin concerns only

BusinessOS business authorization
-> BusinessContext
-> organizational access
-> BusinessOS RBAC
```

Business modules must not use Django `user.has_perm()` as the authoritative business-action permission system.

Business services must remain request-neutral and use BusinessContext plus Core authorization APIs.

## Permission manifest contract

Extend the module manifest contract so business modules may declare stable permission codes.

Conceptual form:

```python
MODULE = {
    "code": "inventory",
    "name": "Inventory",
    "version": "0.1.0",
    "depends": ["catalog", "organization", "reference", "access"],
    "permissions": [
        "inventory.movement.view",
        "inventory.movement.create",
        "inventory.movement.update",
        "inventory.movement.post",
        "inventory.balance.view",
        "inventory.history.view",
    ],
}
```

Exact permission vocabulary belongs to the owning module and is reviewed with that module.

Validate permission codes deterministically.

Permission registration must be retry-safe.

Manifest re-registration must not silently destroy already-assigned permission relationships merely because a declaration changed. Removal/retirement semantics must be explicit.

Do not turn this into a marketplace/plugin lifecycle.

## Immutable audit foundation

Add a small Core audit capability for security-sensitive and significant business actions.

Audit records must contain at least:

```text
actor identity
company identity where applicable
action
object type
object identity
occurred_at
small structured metadata
```

Audit records are append-only/immutable through normal application paths.

Initial Core audit uses should include security-sensitive operations such as:

```text
organizational access grant/revoke
role assignment/revocation
role-permission changes
other explicitly approved Core security changes
```

Business modules will later record significant transitions through the same audit contract.

Do not implement event sourcing. AuditEntry is not the source of truth for business aggregates.

## Reference identity immutability

Existing reference identities must never be repurposed through ordinary update paths.

At minimum these codes are immutable after creation:

```text
Country.code
Currency.code
Language.code
UnitOfMeasure.code
```

Reference retirement uses `is_active=False`.

A new semantic meaning requires a new reference record.

Historical foreign keys must retain the meaning that existed when business records were created.

## Business time contract

Database timestamps remain timezone-aware UTC.

Provide a small shared company-time API equivalent to:

```python
company_timezone(...)
company_local_datetime(...)
company_local_date(...)
```

Later modules such as Accounting, Payroll, Attendance, POS, Hotel and Scheduling must not each invent independent business-date semantics.

Do not add a generic scheduler or calendar engine in this phase.

## BusinessContext

Preserve the framework-neutral base contract:

```python
actor_id
company_id
branch_id
warehouse_id
```

Do not put Django HttpRequest, Django User objects, ORM model instances, tenant database connections or UI-specific locale objects into BusinessContext.

Future capabilities such as service accounts and tenant resolution must evolve around this boundary rather than making business services request-dependent.

## Module registry

Keep module registration lightweight.

Core Foundation v1 responsibilities are limited to:

```text
module identity
semantic version
dependencies
deployment-wide enablement
permission declarations
```

Do not introduce dynamic installation/uninstallation, marketplace execution, feature-flag engines or dependency orchestration frameworks.

## Region decision

Do not automatically add Region as an authorization scope during Core v1 hardening.

Before a Region model is added, explicitly decide whether Region means only organizational/reporting grouping or an authorization scope. If it becomes an authorization scope, its impact on BusinessContext and access grants requires a separate decision.

## Explicit exclusions

Do not implement now:

```text
MFA
SSO
tenant-per-database runtime
workflow engine
event infrastructure
metadata/Studio
API/service-account system
generic document numbering engine
generic idempotency framework
generic Money framework
UoM conversion
Redis
Celery
Kafka/NATS
Go services
custom Python runtime
```

Reserve compatibility boundaries only.

---

# Gate 2 — Independent Core Foundation Audit

Do not normalize canonical history until this gate receives an independent PASS.

Verify at minimum:

```text
RBAC company isolation
permission deny-by-default behavior
superuser semantics
permission declaration/registration retry safety
organizational grant/revoke lifecycle
stale subordinate grant prevention
audit immutability
reference-code immutability
base-currency immutability
timezone validation
company business-time conversion
BusinessContext authorization
module registry compatibility
existing Phase 0 behavior
Phase 1 compatibility
```

Run at minimum:

```bash
pytest
ruff check .
python manage.py check
python manage.py makemigrations --check
```

Also verify:

```text
fresh PostgreSQL bootstrap
SQLite compatibility where supported
Docker application startup
Tailwind reproducibility
representative authentication/company switching
fresh module registration
```

Review migration operations for destructive behavior, unsafe defaults and accidental table rewrites.

When the independent audit passes, document:

```text
Core Foundation v1 — FROZEN
```

Freeze means foundational contracts cannot be casually redesigned. Future capabilities may be additive and must use explicit ADRs when they change a frozen public contract.

---

# Gate 3 — Pre-release Canonical Normalization

This is a separate operation from implementation. Do not execute it merely because Gate 1 code exists.

Only begin after Gate 2 has passed and explicit authorization is given.

## Safety first

Preserve durable backup references for the pre-normalization development heads, including:

```text
main
accepted Phase 1
Sales
Procurement
latest Inventory
```

Never rely solely on local reflogs.

## Canonical target

Construct a clean pre-release canonical history representing:

```text
Phase 0 — Complete Core Foundation v1
Phase 1 — Party + Catalog
Phase 2 — Commercial Core development
```

Because BusinessOS is still pre-release, development migration history may be normalized so fresh installations see Core Foundation v1 as the Phase-0 baseline.

Do not retain unnecessary amendment migrations solely to preserve development-time chronology.

However, canonical normalization must preserve every accepted schema invariant and business contract.

## Migration normalization rules

After normalization:

- Core migration history represents the final Core Foundation v1 schema cleanly.
- Phase 1 migrations sit cleanly on the final Core baseline.
- Phase 2 standalone module migrations sit cleanly on Phase 1/Core.
- migration dependencies are deterministic;
- a brand-new PostgreSQL database migrates from zero without manual intervention;
- `makemigrations --check` reports no drift;
- fresh seed/demo commands remain retry-safe where applicable.

Do not fake or backdate timestamps.

Do not claim old GitHub objects never existed. The objective is a clean canonical supported history, not forensic erasure.

## Publication rule

Do not replace canonical `main` until the complete normalized candidate passes the full CI/test/bootstrap suite.

No partial force-update of `main` during reconstruction.

---

# Gate 4 — Phase 2 Foundation Adoption

After Core Foundation v1 and Phase 1 have been reconstructed on the canonical baseline, replay/rebase the accepted standalone Phase-2 work onto that baseline.

Preserve accepted business behavior from:

```text
Sales
Procurement
Inventory
```

Do not redevelop their domain lifecycles merely because Core authorization changed.

Adopt the new Core contracts:

```text
validate_business_context
RBAC permission enforcement
module permission declarations
immutable audit for significant transitions
company business-time helpers where business dates are relevant
```

Example Phase-2 permission vocabulary may include:

```text
sales.order.view
sales.order.create
sales.order.update
sales.order.confirm
sales.order.cancel

procurement.order.view
procurement.order.create
procurement.order.update
procurement.order.confirm
procurement.order.cancel
procurement.receipt.create

inventory.movement.view
inventory.movement.create
inventory.movement.update
inventory.movement.post
inventory.balance.view
inventory.history.view
```

The owning module must freeze the final vocabulary through review.

RBAC integration must not change Sales, Procurement or Inventory business semantics.

After Sales/Procurement/Inventory adoption passes review, continue new work:

```text
Billing
Accounting
```

These modules must use Core Foundation v1 contracts from their first implementation.

Optional integrations remain deferred until standalone module acceptance.

---

# Final Canonical Product State

The supported repository and documentation should eventually communicate:

```text
Phase 0
✅ Complete Core Foundation v1

Phase 1
✅ Party + Catalog

Phase 2
🔄 Commercial Core
   ✅ Sales standalone
   ✅ Procurement standalone
   ✅ Inventory standalone
   ⏳ Billing
   ⏳ Accounting
   ⛔ integrations pending standalone completion
```

Do not mark Phase 2 fully complete until Billing, Accounting, approved integrations, independent audits and final Phase-2 acceptance all pass.

---

# Permanent architecture rules

- Build capabilities late; reserve boundaries early.
- Business rules do not live in views/templates/forms/admin classes.
- Business services accept BusinessContext, never HttpRequest.
- Cross-module writes use owning-module public services.
- Inventory remains movement-ledger authoritative.
- Accounting remains balanced-journal authoritative.
- Historical released migrations become immutable once the product is released; this pre-release normalization window is exceptional and must close after canonicalization.
- Future Django replacement remains optional. BusinessOS domain/application contracts must not be defined by Django request/response objects.
- No force-push/history normalization before explicit Gate-3 authorization.

# Gate reporting

After each gate, report:

1. branch
2. exact SHA
3. files/schema changed
4. migrations
5. tests and database used
6. security/concurrency results where applicable
7. fresh bootstrap result
8. hosted exact-head CI
9. limitations
10. PASS/BLOCKED recommendation

Stop after each gate for independent review.
