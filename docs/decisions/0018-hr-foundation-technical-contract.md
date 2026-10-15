# ADR 0018 — HR Foundation Technical Contract

Status: **Accepted — HR-0 Technical Contract**. HR-1 NOT AUTHORIZED.

Independent final contract audit: **PASS — Readiness A**. All five HR-0 findings RESOLVED.
Formal acceptance COMPLETE; canonical adoption PENDING at this acceptance checkpoint.

Date: 2026-10-14. Formal acceptance: 2026-10-15 Asia/Dhaka.

Canonical umbrella base: `6453c8f3202335aabe8a872046fea2e607dac858`.
Acceptance/publication branch: `phase3a-hr-contract`; no PR or tag.

## Authority and evidence

[ADR 0017](0017-phase3-people-digital-commerce-boundaries.md) is canonically accepted at the
base above. Its completion rule was fulfilled: acceptance push CI #134 / `38570976500` and
main push CI #135 / `38576825532` succeeded at that SHA, each with 3,015 PostgreSQL tests.
These are inherited umbrella/Phase 2 regression evidence, not HR runtime tests. The original
proposal, twelve resolved owner decisions and acceptance-stage pending wording remain historical.

Original proposal `5be60f19e3bf654786abcd06b61149bc4a962ea9` received the supplied independent
**REVISE — HR-0 TECHNICAL CONTRACT REQUIRES CORRECTION / Readiness B**, P0 0 / P1 0 / P2 4 / P3 0.
HR0-AUD-1 (User lock cycle), HR0-AUD-2 (unapproved 24-hour attendance ceiling), HR0-AUD-3
(unapproved 366-date leave ceiling) and HR0-AUD-4 (incomplete revision-chain validation) remain
historical findings. First correction `3ab7aaea019833b9a0f5123f51018f4d516db366` received the
subsequently supplied independent re-audit: all four RESOLVED at technical-contract level, but
**HR0-REAUD-1 — P2** placed formal acceptance on HOLD for unacceptable new global table contention.
The owner rejected database-wide EXCLUSIVE authority gates (Option B). The supplied read-only
investigation conclusion is **A — HR-ONLY FINER-GRAINED LOCKING FEASIBLE; Core/Identity change: NO**.
Its synthetic execution evidence is not HR-1 acceptance or this task's independent audit.
The finer-grained correction was recorded at `c99ea988ff7e1a74fed3ed4cb1232cd7db37957a` without
amending history or accepting the ADR at that checkpoint. The owner subsequently supplied
**FINAL PASS — HR-0 FINER-GRAINED TECHNICAL CONTRACT APPROVED FOR FORMAL ACCEPTANCE**,
**Readiness A**, **P0: 0 / P1: 0 / P2: 0 / P3: 0**, resolving HR0-REAUD-1 as well as retaining
the four earlier resolutions. The original HOLD and then-pending correction remain historical.
The present owner authorization accepts this exact technical contract through one docs-only commit,
normal branch publication, exact-head branch CI, direct non-force fast-forward main adoption only
on success/unchanged main, separate exact-head main CI and then local main synchronization.

This ADR and the [detailed HR plan](../exec-plans/active/PHASE_3A_HR_FOUNDATION.md)
jointly specify the accepted technical contract, not an implemented HR runtime. All H01–H18 and
T01–T26 implementation evidence is required in a future separately authorized HR-1, not executed here.
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
| Identity `managers.py`, `models.py`, `admin.py`, `forms.py` | UUID User and normalized email; inherited batch/update/row-lock operations have no common UUID writer order; association is not an HR grant |
| Access `policies.py`, `services.py`, `permissions.py` | `validate_business_context`, `require_permission`, `require_final_permission`; complete final actor/Role/Permission lock protocol and Company-first supported grant writers |
| Reference `models.py` | Stable active/retired codes; no leave-entitlement or payroll authority |
| Audit `models.py`, `services.py` | Append-only `record_audit_entry`, same-alias caller transaction; evidence, not attendance state |
| Database `execution.py`, `transactions.py` | `database_execution`, call/enter-time `business_atomic` / `business_atomic_context`, nested same-alias pinning |
| Modules `manifest.py`, `services.py`, `decorators.py` | Three-part permission namespace, deterministic registration, disabled-by-default/preserved enablement; `module_required` is HTTP-only |
| Payments manifest/services; Sales services; Inventory forms | Existing code/name bounds, explicit audited services, Company-first locks, exact aware-instant preservation before generic DST parsing |

Paths above are under `businessos/core/` or `businessos/modules/`; the plan links exact files.
No public HR API is claimed to exist. No owner is redesigned to serve this proposal.

## Accepted decisions within frozen OD-1–OD-6

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
Company/Branch/role grants or self-service. Identity's inherited B→A batches cannot be made A→B
by an HR-only sorting rule: blocking ordered multi-User locks are superseded, not revived.
The first correction's EXCLUSIVE authority-table gates are owner-rejected history, never a fallback.
Every public HR mutation, successful retry/no-op and locking selector follows the plan's sequence:
Company/all non-User anchors, then verified User/Role/Permission relations in ROW SHARE NOWAIT,
then the complete operation-specific User union FOR SHARE NOWAIT (always actor). Re-read stabilized
actor activity/superuser state; for non-superusers prelock ALL assigned same-company Roles and ALL
reachable Permissions, including inactive rows, FOR SHARE NOWAIT. For superusers first obtain Core's
existing Permission namespace SHARE NOWAIT, then every Permission row FOR SHARE NOWAIT.
Only then invoke every unchanged compound Core final guard immediately before effects/Audit/return.
Exact row coverage is mandatory; no later guard/nested call may introduce an uncovered anchor.
New beneficiary snapshot FKs require existence protection, not invented activity/grant eligibility;
unchanged historical/removed links and negative self-comparison IDs need no extra User locks.
Any admission conflict aborts the WHOLE outer operation; AuthorityBusy is mapped after rollback,
with no effect, success Audit, partial receipt or successful retry. Unknown outer transactions are
rejected before blocking SQL; admitted nesting reuses one alias/connection/outer transaction,
Company/actor and predeclared complete anchors. No Core/Identity/Access runtime change is required.

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
highest revision of a completely certified chain is authoritative. Any corrupt earlier/latest
evidence is an error, not
permission to fall back to a previous ACTIVE revision. Core Audit never reconstructs the interval.
Prior revisions and session identity cannot be rewritten/deleted by supported ORM callers.

Non-void sessions have `start_at < end_at`, with **no elapsed-duration admission ceiling**.
Valid 25-hour and >48-hour completed intervals are supported. Cross-midnight and multiple
sessions per day are allowed. `[start_at,end_at)` intervals cannot overlap for one Employee,
even across Branch/date snapshots; adjacent intervals are allowed. Local dates use the frozen
timezone and `end_at - 1 microsecond`, not UTC date or today's Company timezone. Aware API instants
resolve folds explicitly; new ambiguous/nonexistent wall input is rejected. Unchanged minute-form
input preserves the trusted server-side original instant before normal DST conversion, including
both folds, seconds and microseconds. No created/updated timestamp ordering proves causality.

Company→Employee serialization precedes parent/reference locks, overlap/leave queries and final
Core authorization. Overlap uses the complete indexed predicate `existing.start < proposed.end
AND existing.end > proposed.start`, with no lookback shortcut. At most 1,000 candidate revision
rows plus one sentinel are materialized, followed by database-side complete-chain certification
and newest-any-effect lookups for their bounded session IDs.
It never locks/materializes an Employee's entire history. Exceeding the cap fails closed, not
truncates evidence. Full-chain count/distinct/min/max and every-row predecessor/transition checks
detect `1,3,4` and malformed earlier facts. Scalar/indexed checks may scan the selected chains in
the database but never materialize all history; operational timeout is a resource error, not a
revision-count/duration limit. No exclusion extension or mutable authoritative projection is added.

Record retry compares original explicit inputs under the stored Branch/timezone, not newly current
Company/Employee configuration. Correction keys are scoped to Attendance; exact authorized retry
returns the immutable matched revision plus separately labelled current effect. Later corrections
do not turn the old receipt into proof of current state. Same key/different input conflicts.

### 3. Full-day Leave with bounded explicit lifecycle

LeaveRequest binds immutable Company/Employee/requester/create UUID and Branch/timezone at creation.
Only type, inclusive dates and reason are DRAFT-editable. No hours/quantity/balance and **no maximum
calendar-date span**. Ordered dates and employment containment use date arithmetic, not elapsed-hour
division. Unique start and exclusive-end midnight conversion plus exact IANA transition analysis
certifies interior midnight geometry without a Python loop per requested date. The HR-local helper
must use the exact TZif/ZoneInfo rule bytes, including recurring future rules; unsupported/ambiguous
boundaries or unverified rule coverage fail closed. No 366-day CHECK, service or hidden UI ceiling.

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

Exactly twelve contract manifest permissions (not registered by this acceptance):

```text
hr.employee.view       hr.employee.manage
hr.department.view     hr.department.manage
hr.attendance.view     hr.attendance.record     hr.attendance.correct
hr.leave.view          hr.leave.request         hr.leave.approve     hr.leave.cancel
hr.leave_type.manage
```

The plan specifies compound permissions for every public service, selector, related choice and
HTTP GET/POST. Company access alone does not authorize HR. Django permissions are not business RBAC.
After Company wait, recheck context/actions; take domain/reference locks and the complete
fail-fast authority prelocks in the plan; invoke existing
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

Candidate/statement budgets may refuse dense evidence with an explicit resource error; they do not
limit interval duration, leave span or revision count. Unsupported civil boundaries fail explicitly,
never approximate. ROW SHARE relation admission is compatible with ordinary ROW EXCLUSIVE DML;
compatible FOR SHARE readers can coexist, including shared authority rows across Companies. No new
whole-table EXCLUSIVE serialization or replacement writer gate is permitted. Hot User/Role/Permission
writers, the existing Company mutex, maintenance and Core's existing superuser Permission SHARE
namespace lock still contend; NOWAIT refusal is explicit and observable, not permission denial.
Preliminary SQL may wait under bounded resource controls; row NOWAIT alone does not make implicit
relation acquisition NOWAIT. Complete sets/deadlines fail closed, with no truncation or hard two-second
wall-clock guarantee. HR-1 must prove T01–T26, whole rollback, actual FK/ORM lock coverage and compatible
cross-company progress. Fairness, starvation freedom, throughput and arbitrary-transaction deadlock
freedom are not claimed. No request/network/UI work under authority locks. Canonical adoption remains
pending under the completion rule below; formal contract acceptance is complete.
One identity and one attendance authority remain; history lives in HR, not Audit.

## Review and next gate

The [plan's local verification record](../exec-plans/active/PHASE_3A_HR_FOUNDATION.md#local-hr-0-verification)
separates actual documentation checks from future implementation requirements.
The supplied final independent audit and owner-authorized formal acceptance are complete. Next is
the currently authorized publication/CI/canonical-adoption sequence below, not further remediation.
HR-1 remains NOT AUTHORIZED; no policy or runtime change is introduced by acceptance.

## Final independent audit and formal acceptance — 2026-10-15

Reviewed finer-grained candidate: `c99ea988ff7e1a74fed3ed4cb1232cd7db37957a`, directly above
`3ab7aaea019833b9a0f5123f51018f4d516db366`, original proposal
`5be60f19e3bf654786abcd06b61149bc4a962ea9` and canonical umbrella base above.
The owner supplied final independent **PASS / Readiness A**, with zero P0–P3 findings and
**HR0-AUD-1, HR0-AUD-2, HR0-AUD-3, HR0-AUD-4 and HR0-REAUD-1: RESOLVED** at technical-contract
level. This acceptance task records that supplied review; it does not manufacture another audit.

Supplied evidence includes the PostgreSQL T01–T26 corrective matrix, original 40P01 reproduction,
no corrected deadlock in tested supported paths, complete authority coverage, simultaneous
cross-company progress, final authorization/revocation, selected alias, rollback, historical retry
and retained Attendance/Leave/history corrections; 248 existing architecture tests passed.
Those are contract-review/synthetic/existing-runtime evidence, not implemented HR-1 acceptance.

Acceptance freezes the finer-grained protocol and domain rules above unchanged: verified relation
identities, ROW SHARE NOWAIT admission, complete inactive-inclusive FOR SHARE NOWAIT authority sets,
existing superuser namespace, unchanged Core final guards, fixed nesting/alias, whole rollback and
historical receipts. Rejected EXCLUSIVE gates remain rejected. H01–H18 and T01–T26 remain mandatory
future HR-1 implementation gates. No HR models, services, permissions or migrations are installed.

### Canonical completion rule

This one acceptance commit becomes the **CANONICAL HR-0 CONTRACT FREEZE** only after:

1. normal publication of `phase3a-hr-contract` and successful `Phase 0 checks` for event `push`,
   branch `phase3a-hr-contract`, testing this exact acceptance SHA;
2. remote main still `6453c8f3202335aabe8a872046fea2e607dac858`, proven fast-forward ancestry and
   exactly four commits above it: proposal, first correction, finer-grained correction, acceptance;
3. direct normal non-force fast-forward push of that same verified SHA to `refs/heads/main`;
4. a separate successful `Phase 0 checks` push run on `main` at that same SHA, followed only then
   by `git switch main` and `git pull --ff-only origin main` with a clean working tree.

Only then are HR-0 and ADR 0018 CANONICALLY ACCEPTED. Adoption-pending wording records this
acceptance checkpoint and is superseded by verified completion, without another commit or invented
future CI evidence. Failure, rejected push or unexpected state stops without automatic correction.
No PR, tag, force-push, rebase, squash, merge commit, amendment or runtime work is authorized.
HR-1 then becomes eligible for separate authorization but is NOT STARTED. ECOM-0 is not started
by this task; ECOM-1, Phase 4 and deployment remain unauthorized. Phase 3 is NOT COMPLETE;
production readiness is NOT CLAIMED.
