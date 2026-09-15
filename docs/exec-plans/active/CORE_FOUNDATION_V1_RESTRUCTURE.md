# Core Foundation v1 Restructure and Canonical Phase Reconstruction

## Status

Core Foundation v1 acceptance was reopened after independent adversarial audit. The prior Gate 2
PASS was withdrawn, ADR 0009 was reopened, and the freeze record at
`5e10ec23ad91a4ba8ef75ea7d29e8b2fb26e2095` became historical evidence. The
`foundation-v1-hardening` evidence branch remains unchanged.

Correctness remediation was implemented on `foundation-v1-correctness-remediation`, based exactly
on that evidence commit. Independent adversarial re-audit gave exact implementation
`f1f7f2f6c917308bedb3c48e51b8113a064d96c2` Gate 2 FINAL PASS on 2026-09-14. ADR 0009 is Accepted
again and Core Foundation v1 is FROZEN at that implementation. Gate 3A reconstruction received
independent FINAL PASS at accepted candidate `780144c5560e1d46cc5d545dc29b33522cd2d1f5`, with hosted
CI #42 successful at the exact SHA. Gate 3B canonical `main` cutover received independent FINAL PASS
at `29d6c12913145bd1b64f572b5bc94c1f53d9987a`; hosted main CI #45 succeeded at that exact SHA.
Gate 3 is closed. Gate 4A Sales and Gate 4B Procurement are accepted, adopted, and closed. Gate
4C Inventory final candidate `8b52270959a2f6623de225e08dc081aea8d1630b` passed exact-head
hosted CI #60 with 410 PostgreSQL tests and independent re-audit returned FINAL PASS.
Documentation-only acceptance checkpoint `eb2f52afc53fd8c36249bc6a1e61c15dba9effe8` passed
branch CI #61, was adopted into canonical `main` by normal fast-forward, and passed exact-head
main CI #62. Gate 4C is accepted, adopted, and closed. Billing, Accounting, integrations, and
deployment remain unauthorized; full Phase 2 is not complete.

Remediation covers the four reproduced findings:

- all 11 scoped Access mutation services lock Company before authorization and mutation;
- Branch/Warehouse ownership, branch consistency and activity cannot bypass validation via bulk APIs;
- audit evidence, reference/permission identities and Company protected fields reject unsafe bulk
  writes/upserts;
- authorization fails closed on malformed cross-company role assignments, and supported assignment
  bulk writes are rejected.

PostgreSQL regressions observe real lock waits for all 11 services against role, permission and
company-access revocation, plus the opposite self-assignment/revocation ordering. Branch retirement
and warehouse activation are tested in both concurrent orderings. Existing tests are retained;
the inactive-branch scope test now uses explicitly corrupt legacy data so its denial assertion
remains covered despite normal model saves preventing that state.

No schema migration, history normalization, Phase 2 adoption or unrelated infrastructure is added.

Accepted remediation verification on 2026-09-14:

- PostgreSQL 17 / Python 3.13: 200 tests passed without teardown warnings;
- 36 new PostgreSQL concurrency cases passed (34 Access authorization/revocation cases and two
  Branch/Warehouse activity orderings); the existing Catalog concurrency case also passed;
- SQLite: 163 passed, 37 expected PostgreSQL-only skips;
- Ruff, Django checks and migration drift passed; no migrations were created or changed;
- fresh PostgreSQL bootstrap and legacy Company upgrade passed (`ZZ` / `UND` / `UTC`, preserved
  currency and active Core permissions); the disposable legacy database was removed;
- Docker build/startup and login HTTP 200 passed;
- demo seeding preserved counts, business identities and attribute mappings on retry (Catalog's
  existing replacement of attribute-assignment join-row UUIDs remains unchanged);
- `npm ci` passed and Tailwind matched the committed output byte-for-byte.

Hosted CI #39 passed at the exact published implementation SHA. The subsequent independent
re-audit closed all four reopened findings and restored Gate 2 FINAL PASS.

## Historical implementation and verification (superseded acceptance)

Implemented outcome:

- Core Access now owns company-scoped minimal RBAC and explicit organizational grant/revoke services.
- module manifests support deterministic, non-destructive permission registration;
- Core Audit records immutable security-action evidence;
- Company now owns country, default language and validated IANA timezone, while base currency is
  immutable through normal model/service mutation;
- Reference and permission codes are immutable identities;
- shared company-local datetime/date helpers establish the business-time contract;
- ADR 0009 recorded the former acceptance, now withdrawn pending independent re-audit.

Gate 2 remediation after the audit of `62d6931e22127cc9c42ba59fe6b80a7f664f8c1d`:

- Core Access management permissions now bootstrap deterministically through a forward migration;
- authorization requires an active registered permission before superuser role-grant bypass;
- all Access/RBAC deployment-admin models are inspection-only so lifecycle/audit services cannot be
  bypassed there;
- Company queryset timezone mutation is rejected in favor of validated model mutation;
- permission re-registration preserves explicit retirement state.

Remediation verification on 2026-09-14:

- PostgreSQL 17 / Python 3.13: 89 tests passed without warnings;
- focused Core Foundation/Admin suite: 30 tests passed on PostgreSQL;
- SQLite: 88 tests passed with one expected PostgreSQL-only Catalog concurrency skip;
- fresh PostgreSQL bootstrap created both active Core management permissions automatically;
- the legacy-Company upgrade still produced explicit `ZZ` / `UND` / `UTC` values and the active
  Core permissions;
- delegated non-superuser management, superuser fail-closed semantics, read-only security admin,
  stale-authority cleanup and queryset-timezone rejection regressions passed;
- Ruff, Django checks, migration drift, Docker startup, demo idempotency and Tailwind
  reproducibility passed.

No Phase 2 branch was merged, no canonical history was rewritten, and no excluded infrastructure
or capability was introduced. That earlier Gate 2 acceptance has since been reopened; Gate 3 and
Phase 2 adoption remain unstarted.

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
- Gate 3 canonical normalization has not started and requires separate explicit authorization.

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

## Gate 3A reconstruction outcome

Gate 3A preserves the pre-reconstruction heads under annotated `archive/pre-gate3/*` tags and builds
only on `gate3-canonical-reconstruction`. No existing branch or tag is moved.

Canonical checkpoints:

```text
Phase 0 / Core Foundation v1
4ef16c271dfce235dbcb874fabaa5df0c63edd54

Phase 1 Party + Catalog
5b95aaa0f13a64a862999e13c6533d1bbb5c81f3
```

Core migration inventory is normalized from 13 development schema/data files to nine supported
files: one initial each for Identity, Reference, Organization, and Module Registry; two initials
each for Access and Core Audit where Django resolves cross-app foreign-key dependencies; and one
frozen Access permission data migration. The final email constraint, Company business identity,
reference identity rules, RBAC, audit schema, and module permission field are present directly in
that canonical graph.

Party and Catalog each retain one final initial schema migration and one deterministic manifest data
migration. The data migrations keep their declarations locally and preserve existing deployment
enablement on retry.

Local candidate evidence:

- fresh PostgreSQL 17 zero-state migration completed without manual intervention;
- PostgreSQL full suite: 200 passed, including Foundation adversarial concurrency and Catalog row-lock tests;
- SQLite: 163 passed, 37 expected PostgreSQL-only skips;
- core permission bootstrap produced exactly the two frozen Core v1 identities;
- reference seed retry reported 8 created then 0 created;
- Phase 1 demo retry reported 14 created then 0 created, with final Party/Product/Variant/Attribute/
  Value/Assignment counts `2/3/5/2/4/6`;
- Ruff, Django system checks, and migration drift checks passed;
- `npm ci` reported no vulnerabilities and Tailwind rebuilt byte-for-byte;
- a clean Docker Compose build applied the canonical graph and served `/login/` with HTTP 200;
- semantic PostgreSQL comparison against accepted pre-normalization checkpoint `130c44bf...`
  matched 519 sorted facts covering tables, columns, types, nullability, defaults, primary/foreign/
  unique/check constraints, and indexes. Raw dump differences were only column ordering and dump nonce.

Independent Gate 3A audit gave FINAL PASS to candidate
`780144c5560e1d46cc5d545dc29b33522cd2d1f5`. Hosted CI run #42 succeeded against that exact SHA.
The accepted canonical checkpoints are:

```text
Canonical Phase 0 candidate   4ef16c271dfce235dbcb874fabaa5df0c63edd54
Canonical Phase 1 candidate   5b95aaa0f13a64a862999e13c6533d1bbb5c81f3
Accepted Gate 3A candidate    780144c5560e1d46cc5d545dc29b33522cd2d1f5
```

Gate 3A is closed with FINAL PASS.

## Gate 3B canonical cutover outcome

The lease-guarded canonical cutover moved only `refs/heads/main` from
`febe5b45941c6956fd98006c04abded16a9ff998` to Gate 3A closure
`29d6c12913145bd1b64f572b5bc94c1f53d9987a`. Recovery tag `archive/pre-gate3b/main` preserves the
old main commit. All pre-Gate-3 archive tags and historical Phase 0, Phase 1, Sales, Procurement,
and Inventory branches remain preserved.

Independent verification gave Gate 3B FINAL PASS. Hosted main CI run #45 succeeded against exact
head `29d6c12913145bd1b64f572b5bc94c1f53d9987a`, including fresh PostgreSQL migration, 200 tests,
Ruff, Django system checks, migration drift, `npm ci`, and Tailwind reproducibility.

Canonical `main` now contains:

```text
Phase 0  Complete Core Foundation v1
Phase 1  Party + Catalog
Phase 2  Not yet adopted
```

Gate 3A and Gate 3B are closed. The exceptional pre-release canonical migration-normalization
window is also closed. From this baseline forward, committed supported migrations are append-only;
future schema evolution uses normal additive Django migrations. Any exceptional migration-history
rewrite requires a separately approved architecture gate.

Future canonical development starts from normalized `main`. Accepted standalone Phase 2 inputs
remain preserved at Sales `2aeb01c2766da9e78dd04252cfb9d3b221828e6c`, Procurement
`a99377ca55355a2e4cdebd64ff73cf29fd3eff83`, and Inventory remediation
`f45afdfea33d3fd03d469e6a0cd63d0e5358f38c`. This closure does not authorize Gate 4, adopt those
modules, or begin Billing, Accounting, or integrations.

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

## Gate 4A Sales adoption candidate

Gate 4A replays the accepted standalone Sales behavior onto canonical Core Foundation v1 without
merging or cherry-picking the historical Sales branch. The code-bearing candidate is:

```text
Branch              gate4a-sales-adoption
Canonical base      f2d48c1d1a6f12c7b27c925e2c6f14f922d53beb
Historical evidence 2aeb01c2766da9e78dd04252cfb9d3b221828e6c
Implementation      28c8028950be1997b4f3d0816b1ec04764222068
Initial audit        BLOCKED at fc609bcd81916c13921c2d1cc7b6a59eda1c1e19
Remediation          d62c34e36f0a8b11f59bfdb058143e27f5231c5d
Accepted candidate   23338f1cfed11d21d4fa8fd7e92f8de120450977
Independent re-audit FINAL PASS
Hosted CI            run #48 SUCCESS at the accepted candidate
Adoption checkpoint  e0c848f34da0bce9b9c6e010a396026ac5889cf4
Main CI              run #50 SUCCESS at the adoption checkpoint
Status               accepted, adopted, and closed
```

Preserved Sales semantics:

```text
SalesOrder / SalesOrderLine
DRAFT -> CONFIRMED -> CANCELLED
ProductVariant is the transactional item identity
confirmed and cancelled documents are immutable
totals are derived from lines
confirmation does not change stock or create billing/accounting records
```

The final Gate 4A permission vocabulary is:

```text
sales.order.view
sales.order.create
sales.order.update
sales.order.confirm
sales.order.cancel
```

State-changing services accept `BusinessContext`, lock the active Company before authorization and
mutation, and re-check the action permission inside the same transaction. Significant immutable
audit actions are `sales.order.created`, `sales.order.updated`, `sales.order.confirmed`, and
`sales.order.cancelled`. Successful retries and no-op updates do not duplicate audit records.

Candidate evidence:

- fresh PostgreSQL 17 zero-state migration and Sales permission/module bootstrap passed;
- PostgreSQL full suite: 238 passed, including Sales concurrency, stale mutation, revocation, audit
  rollback, and retry coverage;
- SQLite: 197 passed with 41 expected PostgreSQL-only skips;
- Ruff, Django checks, migration drift, module-local discovery, Docker startup, and repeatable demo
  seed passed;
- `npm ci` completed and Tailwind rebuilt byte-for-byte on the second clean build;
- representative service/simple and variable-ProductVariant order workflows passed desktop and
  390px mobile browser QA, including monetary precision and long-identity overflow checks.

The independent audit required explicit reconciliation of the module-gating contract, ORM bulk
immutability protection, missing transition-vs-edit/delete concurrency coverage, and restoration
of canonical Phase 2 documentation. Remediation preserves ADR 0005's HTTP-only module gate;
installed Python services remain governed by BusinessContext and RBAC. Sales-local QuerySets now
reject public bulk update/create/upsert/delete paths, while lifecycle services use one private,
row-locked transition primitive limited to DRAFT -> CONFIRMED and CONFIRMED -> CANCELLED.
PostgreSQL regressions cover both edit/confirmation orderings and confirmation winning over stale
order/line deletion.

Independent re-audit gave the remediated candidate
`23338f1cfed11d21d4fa8fd7e92f8de120450977` FINAL PASS, and hosted CI run #48 succeeded against
that exact SHA with 283 PostgreSQL tests and all required quality checks passing. The
documentation-only acceptance commit `e0c848f34da0bce9b9c6e010a396026ac5889cf4` was then adopted
into canonical `main` by normal fast-forward; exact-head main CI run #50 succeeded. Gate 4A is
accepted, adopted, and closed. Gate 4B Procurement, Gate 4C Inventory, Billing, Accounting, and
integrations remain unauthorized.

## Gate 4B Procurement adoption closure

Gate 4B starts from canonical `main` at
`fb9028bbbec5dfc56e7d579c3c351abcde764833` and uses historical Procurement closure
`a99377ca55355a2e4cdebd64ff73cf29fd3eff83` only as read-only evidence. Candidate implementation
`395da2ad874fc2efb72219da71316b9a6d8f73bf` preserves Purchase Order and immutable receipt
semantics while adopting Foundation v1 RBAC, Company locking, audit, business time, and the
canonical HTTP-only module-gating contract.

The candidate remains isolated on `gate4b-procurement-adoption`; candidate head
`12d1a1f90689979048cdf3b4f59836b026dd153f` passed hosted CI #53.
Completion review then BLOCKED acceptance on missing authorization-revocation and
confirmation-versus-mutation PostgreSQL coverage. Narrow test-only remediation
`b8c49e1fb5b62f9169038b59e35b6d4e7adfb8e0` closes those gaps at final candidate
`1eabb0e9806342cc2ba71f1468eb18af120cddb9`. Hosted CI #54 passed that exact head with 342
PostgreSQL tests, and independent Gate 4B re-audit returned FINAL PASS. Documentation-only
acceptance commit `e4ea1791f0b2c7d1209ea574de3689970e1fc398` passed exact-head branch CI #55,
was adopted into canonical `main` by normal fast-forward, and passed exact-head main CI #56. Gate
4B is accepted, adopted, and closed. Procurement creates no Inventory, Billing, or Accounting
effects. At that checkpoint Gate 4C and later work remained unauthorized; Gate 4C subsequently
received candidate-only authorization recorded below.

## Gate 4C Inventory adoption candidate

Gate 4C is implemented in isolation from canonical `main` at
`8d5a41f83c3f796fa31e7d3f8598c54f7dfc5b95`. Historical Inventory remediation
`f45afdfea33d3fd03d469e6a0cd63d0e5358f38c` remains read-only reference evidence and is not an
accepted or merged baseline. The candidate adopts Foundation v1 BusinessContext, RBAC,
Company-lock ordering, atomic audit, HTTP-only module gating, and Inventory-local ORM hardening
while preserving a standalone posted movement ledger and no cross-module effects.

Original implementation `e1e94307bd96b2834f677eb02b91d27b87843f21` was published at initial
candidate `01037fc7f87e546382931a081750bf367bb78232`; CI #59 passed with 406 PostgreSQL
tests, but independent audit BLOCKED acceptance on mixed-UoM balance safety, HTTP mutation-form
RBAC, stale-company HTTP evidence, and a missing ProductVariant stock-field assertion. Narrow
remediation `78ba3ae92366da9b2136b260cc9a380e22587e08` closed those findings at final
candidate `8b52270959a2f6623de225e08dc081aea8d1630b`. Exact-head CI #60 passed with 410
PostgreSQL tests and independent re-audit returned FINAL PASS. Documentation-only acceptance
checkpoint `eb2f52afc53fd8c36249bc6a1e61c15dba9effe8` passed branch CI #61, was adopted into
canonical `main` by normal fast-forward, and passed exact-head main CI #62. Gate 4C is accepted,
adopted, and closed. Billing, Accounting, Procurement-to-Inventory, Sales-to-Inventory, and other
integrations remain unauthorized; full Phase 2 is not complete and production deployment is not
approved.

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
