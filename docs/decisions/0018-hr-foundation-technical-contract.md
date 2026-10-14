# ADR 0018 — HR Foundation Technical Contract

Status: **PROPOSED — HR-0**. Not Accepted. HR-1 NOT AUTHORIZED.

Date: 2026-10-14.

Canonical umbrella base: `6453c8f3202335aabe8a872046fea2e607dac858`.
Local proposal branch: `phase3a-hr-contract`; no publication authorized.

## Authority and evidence

[ADR 0017](0017-phase3-people-digital-commerce-boundaries.md) is canonically accepted at the
base above. Its completion rule was fulfilled: acceptance push CI #134 / `38570976500` and
main push CI #135 / `38576825532` succeeded at that SHA, each with 3,015 PostgreSQL tests.
These are inherited umbrella/Phase 2 regression evidence, not HR runtime tests. The original
proposal, twelve resolved owner decisions and acceptance-stage pending wording remain historical.

The owner now authorizes HR-0 technical planning and exactly one local documentation proposal
commit. This ADR and the [detailed HR plan](../exec-plans/active/PHASE_3A_HR_FOUNDATION.md)
jointly specify a proposed implementation contract. Neither is accepted by this task. All
H01–H18 evidence is required in a future separately authorized HR-1, not executed here.
No runtime, schema, manifest, permission, test, frontend or existing owner implementation changes.

Required engineering reading: [operating contract](../../AGENTS.md),
[baseline](../architecture/BASELINE.md), [boundaries](../architecture/MODULE_BOUNDARIES.md),
[dependency map](../architecture/DEPENDENCY_MAP.md), [roadmap](../ROADMAP.md) and
[umbrella plan](../exec-plans/active/PHASE_3_PEOPLE_DIGITAL_COMMERCE.md).
Existing accepted ADRs [0001](0001-foundation-security-contracts.md),
[0004](0004-phase-1-party-catalog-contract-freeze.md),
[0005](0005-deployment-module-gating-and-simple-variant-lifecycle.md),
[0009](0009-core-foundation-v1-contract.md) and
[0012](0012-tenant-ready-database-execution-foundation.md) remain authoritative.

## Existing owners inspected at the pinned base

| Owner / actual implementation | Reused contract / relevant limit |
| --- | --- |
| Party `models.py`, `services.py`, `selectors.py` | Company-owned PERSON/ORGANIZATION, mutable activity/type, immutable Company; `party_detail` prefetches contacts/addresses and is unsuitable for HR identity choices |
| Organization `models.py`, `time.py` | Company, same-company Branch, active context, IANA timezone, aware company-local helpers; no employment/roster ownership |
| Identity `models.py` | UUID User, normalized email, activity and technical authentication; User association is not an HR grant |
| Access `policies.py`, `services.py`, `permissions.py` | `validate_business_context`, `require_permission`, `require_final_permission`; complete final actor/Role/Permission lock protocol and Company-first supported grant writers |
| Reference `models.py` | Stable active/retired codes; no leave-entitlement or payroll authority |
| Audit `models.py`, `services.py` | Append-only `record_audit_entry`, same-alias caller transaction; evidence, not attendance state |
| Database `execution.py`, `transactions.py` | `database_execution`, call/enter-time `business_atomic` / `business_atomic_context`, nested same-alias pinning |
| Modules `manifest.py`, `services.py`, `decorators.py` | Three-part permission namespace, deterministic registration, disabled-by-default/preserved enablement; `module_required` is HTTP-only |
| Payments manifest/services; Sales services; Inventory forms | Existing code/name bounds, explicit audited services, Company-first locks, exact aware-instant preservation before generic DST parsing |

Paths above are under `businessos/core/` or `businessos/modules/`; the plan links exact files.
No public HR API is claimed to exist. No owner is redesigned to serve this proposal.

## Proposed decisions within frozen OD-1–OD-6

### 1. Six HR-owned entities, no competing identity or balance

The plan freezes exact fields, nulls, keys, CHECKs, indexes and supported writes for
Department, Employee, Attendance, AttendanceRevision, LeaveType and LeaveRequest.
All have UUID identity and immutable explicit Company scope. References use `PROTECT`.
No hard-delete API exists in v1, including setup rows; retirement/end/cancellation/void preserve
identities and prevent employee-number/code reuse. No copied Party names, contacts or addresses.

Department and LeaveType use immutable trimmed uppercase ASCII codes (1..32), names (1..160),
activity and positive edit revision. Department is Company-wide, without Branch/hierarchy;
retirement rejects any assigned ACTIVE Employee. LeaveType retirement preserves historical leave;
new submit/approve requires active type. No quotas/accrual/paid-day classification.

Employee has immutable Company, PERSON Party and caller-supplied normalized employee number
(1..32, same code grammar), optional User/Department/current Branch, ACTIVE/ENDED, joining date,
nullable leaving date and edit revision. Company+Party and Company+number remain unique across
all history. This follows the explicit setup-code convention rather than truncating the existing
36-character `PAY-<uuid>` pattern into a 32-character field. Duplicate creation conflicts;
authorized lookup recovers identity after response loss, not an invented create receipt.
No generation framework, automatic renumbering, ENDED→ACTIVE or rehire episode.

New Employee/attendance/leave require active same-company PERSON. Historical reads and bounded
corrections/rejection/cancellation remain possible after Party inactivity/type change. Current
eligibility is shown, never reconstructed from copied contact identity. HR never writes Party.
The exact HR projection is `id, company_id, party_type, display_name, is_active`, through an
HR-bounded selector over accepted Party fields, not `party_detail()` or a new Party API.

New/relinked User must be active and have Company access (or valid superuser grant bypass), with
partial unique Company+User for ACTIVE Employees. Unlink/relink is explicit, versioned and audited;
later User inactivity/revocation does not erase history. No matching by email/phone, identity creation,
Company/Branch/role grants or self-service. Cross-company User reference stabilization uses
compatible UUID-ordered PostgreSQL `FOR SHARE`, never swapped exclusive actor/reference locks.

Employee branch transfer is a separate company-context operation, with expected revision and
`hr.employee.branch_changed` audit. It changes only current assignment, not physical-work history.
Attendance/Leave retain immutable Branch/timezone snapshots. Date/end changes validate existing
effective attendance and SUBMITTED/APPROVED leave; no silent historical repair.

### 2. Attendance session plus append-only revision authority

Attendance is stable session identity with Company/Employee, nullable Branch snapshot, frozen
IANA timezone, Company-scoped record request UUID and recording actor. No date uniqueness, current
mutable interval, daily total or daily balance. AttendanceRevision contains immutable scoped keys,
parent, increasing revision, operation, effect, aware UTC interval (retained on VOID), derived
local-date search facts, reason, actor, request UUID and expected previous revision.

Revision 1 records the original. Later CORRECT/VOID/REINSTATE appends exactly one revision; the
highest structurally valid revision is authoritative. Invalid latest evidence is an error, not
permission to fall back to a previous ACTIVE revision. Core Audit never reconstructs the interval.
Prior revisions and session identity cannot be rewritten/deleted by supported ORM callers.

Non-void sessions have `0 < end_at - start_at <= 24 hours` elapsed UTC. Cross-midnight and multiple
sessions per day are allowed. `[start_at,end_at)` intervals cannot overlap for one Employee,
even across Branch/date snapshots; adjacent intervals are allowed. Local dates use the frozen
timezone and `end_at - 1 microsecond`, not UTC date or today's Company timezone. Aware API instants
resolve folds explicitly; new ambiguous/nonexistent wall input is rejected. Unchanged minute-form
input preserves the trusted server-side original instant before normal DST conversion, including
both folds, seconds and microseconds. No created/updated timestamp ordering proves causality.

Company→Employee serialization precedes parent/reference locks, overlap/leave queries and final
Core authorization. Overlap uses an indexed finite UTC window and at most 1,000 candidate revision
rows plus one overflow sentinel, followed by indexed latest lookups for bounded session IDs.
It never locks/materializes an Employee's entire history. Exceeding the cap fails closed, not
truncates evidence. The plan specifies query predicates, indexes, correction exclusion and
date-window chunking. No exclusion extension or mutable authoritative search projection is added.

Record retry compares original explicit inputs under the stored Branch/timezone, not newly current
Company/Employee configuration. Correction keys are scoped to Attendance; exact authorized retry
returns the immutable matched revision plus separately labelled current effect. Later corrections
do not turn the old receipt into proof of current state. Same key/different input conflicts.

### 3. Full-day Leave with bounded explicit lifecycle

LeaveRequest binds immutable Company/Employee/requester/create UUID and Branch/timezone at creation.
Only type, inclusive dates and reason are DRAFT-editable. No hours/quantity/balance. Request length
is 1..366 inclusive calendar dates as a technical work bound, not entitlement. Every frozen-zone
midnight from first day through day-after-last is validated by round-trip, ambiguity/gap and increasing
UTC-boundary checks. Unsupported boundaries fail closed; no assumed 24-hour civil day.

Legal transitions:

```text
DRAFT -> SUBMITTED -> APPROVED | REJECTED
DRAFT | SUBMITTED | APPROVED -> CANCELLED
REJECTED and CANCELLED are terminal.
```

Submission freezes content and beneficiary User snapshot; per-event UUID, actor, from/result
revision and timestamp preserve submit/decision/cancel receipts in the same row. No generic history
or workflow table. Matching retry reauthorizes and returns historical event plus current status;
changed payload/key scope conflicts. Type/Party retirement or later cancellation does not erase
an intrinsic valid earlier receipt; retry does not perform its effect again.

Approve **and reject** deny if actor is requester, current beneficiary User or frozen beneficiary
User at submission. Superusers do not bypass this separation. It is a precise association-based
domain rule, not a claim to infer a human identity without an association. Link never gives authority.
APPROVED cancellation requires leave.cancel + leave.approve; other cancellation requires leave.cancel,
with compound read permissions throughout. Rejection/cancellation may resolve inactive references.

SUBMITTED/APPROVED inclusive date ranges or their frozen-zone UTC windows cannot overlap for one
Employee; the latter prevents double coverage after a timezone change. Approved Leave's frozen-zone
day windows must not intersect any effective attendance. Attendance record/correct/reinstate checks
the same rule in reverse, including intervals crossing midnight or a later Company timezone change.
Company→Employee lock order makes both winner cases deterministic. Void/cancel removes current
conflict only; existing history persists.

### 4. Authorization, scope, persistence and audit

Exactly twelve proposed manifest permissions:

```text
hr.employee.view       hr.employee.manage
hr.department.view     hr.department.manage
hr.attendance.view     hr.attendance.record     hr.attendance.correct
hr.leave.view          hr.leave.request         hr.leave.approve     hr.leave.cancel
hr.leave_type.manage
```

The plan specifies compound permissions for every public service, selector, related choice and
HTTP GET/POST. Company access alone does not authorize HR. Django permissions are not business RBAC.
After Company wait, recheck context/actions; take domain/reference locks; invoke existing
`require_final_permission` for the complete compound set immediately before effects/audit and
successful retry/no-op. Its actor/all assigned Roles/all reachable Permissions protocol, including
inactive rows and superuser namespace stabilization, remains Core-owned. No HR authority cache.

Every service rejects warehouse context. Company-wide setup/branch transfer requires no Branch;
Employee branch-context scope uses current Branch; Attendance/Leave uses frozen Branch. Null-Branch
facts do not enter branch-filtered results. Conflicts check all same-company Employee facts regardless
of Branch, without disclosing hidden identities. Current Company grants with no Branch remain
company-wide, not a new branch-only secrecy model. Foreign IDs and malformed ownership deny.

All reads/writes/locks/savepoints/audits use the selected alias; HR models/ORM results cannot cross
execution scopes. Private HR persistence paths are operation-specific and validate exact allowed
changes. Ordinary direct save/create/delete, update/bulk/upsert/update_or_create bypasses are rejected
for all six entities. This is module-local, not a new shared persistence framework or raw-SQL sandbox.

Core Audit accompanies each meaningful operation in the same transaction. Exact actions include
employee/setup changes, branch transfer, record/correct/void/reinstate, and leave create/update/
submit/approve/reject/cancel. Reasons remain in scoped HR records; audit contains bounded identifiers,
revision/effect and changed-field metadata, not copied PII narratives. Failure rolls back everything;
true no-op/exact retry emits no duplicate success audit.

### 5. Manifest, UI, bounded reads and verification

Future manifest: code `hr`, name `Human Resources`, version `0.1.0`, exact hard dependencies
`party, organization, reference, access`. Core infrastructure is not an additional manifest module.
No Finance, Inventory, Sales, Ecommerce or reverse owner import. Registration migration freezes
permission strings locally, starts disabled and preserves pre-existing enablement.
Missing/disabled HR hides navigation and returns HTTP 404; installed Python services continue with
scope/RBAC/schema independent of registry enablement.

Minimum UI: Employee, Department, completed Attendance/revision history, Leave and type setup.
Existing Django/Tailwind/HTMX/Alpine shell only; safe GET navigation, CSRF normal POST, stale-company
binding, exact action forms and non-JS fallback. Materialized selectors use stable 50-row pages,
UUID tie-breakers, bounded choices/history/date filters and current authorization before return.
Future real-browser 390/768/1280 evidence is mandatory, not provided by this docs-only gate.

The detailed plan freezes every race/retry, database-vs-service invariant and H01–H18 test oracle.
SQLite covers functional rules with explicitly classified PostgreSQL-only lock/catalog skips;
it cannot certify production concurrency. Full future PostgreSQL/SQLite/alias/bootstrap/quality/
browser and independent audit gates are distinct from these existing-runtime documentation checks.

## Exclusions and consequences

No Payroll, salary, tax, benefits, recruitment, appraisal, positions/grades/cost centers, hierarchy,
shifts/rosters/open punches/breaks/devices, expenses/timesheets, entitlements/accrual, self-service,
rehire, generic workflow, Ecommerce or Phase 4 vertical. No generic event/DI/plugin/metadata framework,
new infrastructure, target custom-runtime work, SaaS activation or production deployment.

Bounded candidate caps may refuse dense histories; unsupported civil-midnight boundaries are explicit
validation failures. These are proposed v1 technical limits with no partial acceptance/approximation.
Changing them later needs reviewed algorithm/index and compatibility notes, not silent fallback.
One identity and one attendance authority remain; history lives in HR, not Audit.

## Review and next gate

The [plan's local verification record](../exec-plans/active/PHASE_3A_HR_FOUNDATION.md#local-hr-0-verification)
separates actual documentation checks from future implementation requirements.
Next: fresh independent HR-0 technical-contract audit, then separately authorized acceptance and
publication/adoption. HR-1 remains NOT AUTHORIZED. No policy reopening or self-acceptance.
