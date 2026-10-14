# Phase 3A — HR Foundation

Status: **PROPOSED — HR-0; NOT ACCEPTED**. HR-1 NOT AUTHORIZED.

Date: 2026-10-14. Local branch: `phase3a-hr-contract`.
Canonical base: `6453c8f3202335aabe8a872046fea2e607dac858`.
Technical ADR: [ADR 0018](../../decisions/0018-hr-foundation-technical-contract.md).
Accepted umbrella: [ADR 0017](../../decisions/0017-phase3-people-digital-commerce-boundaries.md)
and [Phase 3 plan](PHASE_3_PEOPLE_DIGITAL_COMMERCE.md).

## 1. Authority, chronology and delivery boundary

The umbrella completion rule is fulfilled at the canonical base: acceptance CI #134 / run
`38570976500` and main CI #135 / run `38576825532` SUCCESS, 3,015 PostgreSQL tests each.
Those inherited results do not execute HR. OD-1–OD-12 remain resolved/frozen; only OD-1–OD-6's
remaining HR technical details are proposed here. No owner-policy conflict was found in the internal
design review. This is not the required fresh independent HR-0 audit or acceptance.

This task authorizes exactly one local docs-only proposal commit with that canonical parent.
No runtime exists for these six models/services/permissions. No push, PR, merge, tag, main update,
HR-1, ECOM-0/1, Phase 4 or production deployment. Future implementation requires independent
contract review, explicit acceptance/publication/adoption and separate HR-1 authorization.
The umbrella's earlier NOT STARTED/pending wording records its acceptance checkpoint; this plan
records HR-0's separately authorized start, without editing/backdating that historical evidence.

### Engineering and runtime evidence

Read [AGENTS](../../../AGENTS.md), [baseline](../../architecture/BASELINE.md),
[boundaries](../../architecture/MODULE_BOUNDARIES.md),
[dependencies](../../architecture/DEPENDENCY_MAP.md) and [roadmap](../../ROADMAP.md).
Accepted [ADR 0001](../../decisions/0001-foundation-security-contracts.md),
[0004](../../decisions/0004-phase-1-party-catalog-contract-freeze.md),
[0005](../../decisions/0005-deployment-module-gating-and-simple-variant-lifecycle.md),
[0009](../../decisions/0009-core-foundation-v1-contract.md),
[0012](../../decisions/0012-tenant-ready-database-execution-foundation.md) apply unchanged.

Actual pinned source inspected (these are current owners, not hypothetical HR APIs):

- [Party models](../../../businessos/modules/party/models.py),
  [services](../../../businessos/modules/party/services.py),
  [selectors](../../../businessos/modules/party/selectors.py): Company identity/contact ownership,
  mutable type/activity, company-access CRUD, full-detail prefetch to avoid in HR.
- [Organization models](../../../businessos/core/organization/models.py) and
  [time helpers](../../../businessos/core/organization/time.py): Company/Branch identity and
  activity, immutable Branch ownership, IANA conversion; no employment history.
- [Identity](../../../businessos/core/identity/models.py),
  [BusinessContext](../../../businessos/core/common/context.py),
  [Access policies](../../../businessos/core/access/policies.py),
  [Access services](../../../businessos/core/access/services.py),
  [permission grammar](../../../businessos/core/access/permissions.py).
- [Reference](../../../businessos/core/reference/models.py),
  [Audit model](../../../businessos/core/audit/models.py),
  [Audit service](../../../businessos/core/audit/services.py).
- [Execution](../../../businessos/core/database/execution.py),
  [transactions](../../../businessos/core/database/transactions.py),
  [manifest validation](../../../businessos/core/modules/manifest.py),
  [registration](../../../businessos/core/modules/services.py),
  [HTTP gate](../../../businessos/core/modules/decorators.py).
- [Payments manifest](../../../businessos/modules/payments/manifest.py) and
  [services](../../../businessos/modules/payments/services.py),
  [Sales services](../../../businessos/modules/sales/services.py),
  [Inventory datetime form](../../../businessos/modules/inventory/forms.py): established bounds,
  explicit transaction/audit/numbering conventions and trusted DST-fold preservation pattern.

HR consumes owners; none imports HR. No Party/Core public API change is needed by this proposal.

## 2. Common schema and domain rules

All fields below are the **complete proposed v1 schema**, not examples. No implicit name/contact,
tenant, salary, balance, duration total, position, approval queue or arbitrary JSON field.

Notation: `!` = required/non-null, `?` = nullable reference/date/provenance before its event.
Text is never null: required trimmed/nonblank, optional `""`. IDs are UUID4; `Company!` is
immutable `organization.Company` FK. Every FK, including User/provenance, uses `PROTECT`, not
CASCADE/SET_NULL. All six records have `id!`, `created_at!`, `updated_at!` aware UTC server timestamps;
Attendance/Revision are insert-only, so updated_at remains its insertion value. The two timestamps
need not establish causal order or always be equal. All immutable event timestamps use server time;
no caller-supplied actor/timestamp. Timestamps can move backwards across records without corruption.

`revision`/event ordinal fields use bounded positive integers 1..2,147,483,647; expected prior
revision may be 0 only for Attendance revision 1. Refuse exhaustion before effects, never wrap.
Caller revision must be exact integer, not bool/float/coerced decimal. Canonical UUID objects/strings
are validated without ignoring malformed/duplicate references. Required dates are actual calendar
dates, not datetime strings silently truncated. Reasons ≤2,000, HR-owned setup names ≤160,
code/number ≤32. Party.display_name retains its native ≤200 bound in the projection, untruncated.
Code grammar after trim/uppercase: `[A-Z0-9][A-Z0-9_-]{0,31}`; whitespace/non-ASCII inside rejects.
Boolean fields require actual bool. No automatic name splitting, contact copies or email matching.

Every bounded ordinal has an explicit portable upper/lower CHECK, not just PostgreSQL integer
storage bounds: revision/number/from/result in 1..2,147,483,647; Attendance expected_revision in
0..2,147,483,647 subject to number−1; nullable Leave ordinals are either null or in the positive range.
Increment exhaustion is checked before persistence, including receipt result ordinal.

Public results are bounded HR DTOs/identities/revisions and approved related projections, not lazy
ORM relationships escaping the transaction. Private persistence validates all proposed fields.
No public delete service; code/number/identity retained even for never-used retired setup rows.

## 3. Department and LeaveType

| Model | Exact additional fields | Mutable through owner service | Database facts / indexes |
| --- | --- | --- | --- |
| Department | company!, code! Char(32), name! Char(160), is_active! default true, revision! default 1 | name/activity + revision/updated_at; company/code/id/created_at immutable | unique(company,code); CHECK revision>=1, code/name nonempty; index(company,is_active,code,id) |
| LeaveType | company!, code! Char(32), name! Char(160), is_active! default true, revision! default 1 | name/activity + revision/updated_at; same identity immutability | unique(company,code); same CHECKs; index(company,is_active,code,id) |

Company-wide only; no Branch/hierarchy/parent/job grade/cost center. Rename allowed. Department
retirement takes Company/Department locks and rejects an indexed EXISTS of ACTIVE assigned
Employees until explicit reassignment; ENDED references persist. Reactivation is explicit and audited.
LeaveType retirement never edits leave, is permitted with historical references, but prevents new
submission/approval. Rejection/cancellation and intrinsic existing receipt recovery remain available.
Creating a draft also requires active type. No jurisdictional type seeds, entitlement or balances.

## 4. Employee, identity and association

Exact fields beyond common timestamps/UUID:

| Field | Type/null/default | Identity / mutation rule |
| --- | --- | --- |
| company | Company! | Immutable |
| party | Party! | Immutable same-company PERSON at creation |
| employee_number | Char(32)! | Caller supplied normalized code; immutable, never reused |
| user | Identity.User? default null | Explicit optional association; no grant/inference |
| department | Department? default null | One current active same-company setup assignment |
| branch | Branch? default null | One optional current active same-company assignment |
| status | Char(8)! ACTIVE default; ENDED | ACTIVE→ENDED only; no reactivation/rehire |
| joining_date | Date! | Company-calendar eligibility; explicit bounded correction |
| leaving_date | Date? | null ACTIVE; required ENDED, >= joining_date |
| revision | PositiveInteger! default 1 | Every actual update/end/transfer increments once |

DB: unique(company,party), unique(company,employee_number) across ALL states; partial
unique(company,user) WHERE status=ACTIVE AND user IS NOT NULL. CHECK supported status, positive
revision, nonblank number, and ACTIVE/null-end OR ENDED/ordered-end. Indexes
(company,branch,employee_number,id), (company,status,department), (company,joining_date,id).
FKs do not prove same-company/type/activity: owner service validates locked references.

Creation requires ACTIVE Employee, joining_date <= company_local_today, active PERSON, active chosen
Department/Branch. No separate number generator: duplicate normalization/unique collision is explicit
field conflict, never reassignment or implicit success. Company serialization plus DB uniqueness
handles races; after response loss, authorized number/Party lookup is recovery, not create idempotency.

Update accepts only joining_date, nullable user/department (Branch via dedicated transfer) and,
only on ENDED, a corrected leaving_date. ACTIVE status is not an arbitrary field. End requires
leaving_date between joining_date and company-local today. Date correction cannot move joining into
the future or ENDED leaving into the future. Revalidate effective attendance's frozen-zone occupied
dates and SUBMITTED/APPROVED leave dates against proposed eligibility. Indexed outside-range probes
with the work cap in section 7 prevent unbounded history materialization; fail closed on overflow.
Cancelled/rejected leave and void attendance remain historical evidence, not active eligibility
claims. No automatic cancel/void/delete. ENDED→ACTIVE is forbidden; historical correction inside
ended dates remains allowed, but no new attendance session or new Leave creation (including
retrospective requests), submission or approval for ENDED. Existing SUBMITTED requests may only
reject/cancel; intrinsic earlier receipts remain recoverable without reapplying their effects.

Patch inputs distinguish omitted from null: omitted field means unchanged; explicit None clears only
nullable User/Department (or Branch in transfer), never joining_date or ENDED leaving_date. Unknown
fields reject. No unrelated edit silently clears associations. Initial create defaults are explicit.

### Party eligibility and exact projection

HR-bounded selectors over Party use exactly `id, company_id, party_type, display_name, is_active`.
New identity choices filter active PERSON and Company. Historical Employee projections may contain
current non-PERSON/inactive flags to explain ineligibility; no false historical PERSON/name snapshot.
No contacts/addresses/legal_name/customer/supplier flags or `party_detail()` prefetch. Existing Party
screens retain company-wide visibility and company-access CRUD; no privacy redesign or HR write.

If Party later becomes inactive/non-PERSON: historical reads remain authorized; new Employee,
attendance recording, leave draft/edit/submit/approve deny. Employee maintenance may end, correct
dates or clear associations; new non-null association/transfer assignment denies until eligibility
is restored through Party. Existing assignments are not auto-cleared. Historical attendance
correct/void/reinstate and leave reject/cancel may resolve facts with inactive identity, under
employment bounds/conflicts and action permissions. Retry of an existing valid effect validates
intrinsic history, not newly current Party eligibility, and still reauthorizes current actor/scope.

### User and Branch mechanics

Initial/relinked User must exist, be active and have selected Company access, or satisfy existing
superuser grant bypass. No requirement for an HR role just to be associated. Association never
creates User, Company/Branch access or permissions. Optional User can be cleared/relinked explicitly
with expected revision and audit. Partial uniqueness covers ACTIVE Employees; ENDED may retain its
historical association. Later User activity/access loss does not erase association/history or create
self-service. HR User choices expose only Company-eligible UUID/activity, not password/email/admin data.

Company-context `transfer_employee_branch` is the only Branch change operation; optional null
unassigns, otherwise new Branch must be active/same-company. Increment revision once; dedicated
branch_changed audit includes old/new IDs. Snapshot facts stay unchanged. Context Branch is actor
scope, not permission to transfer into another Branch. A new association during a race re-reads
activity after all reference waits. Use shared referenced User locking as section 8 specifies.

## 5. Attendance identity and revisions

| Model | Exact additional fields | Immutable / authority |
| --- | --- | --- |
| Attendance | company!, employee! Employee FK, branch? Branch FK, timezone! Char(64), record_request_key! UUID, recorded_by! User FK | All immutable; Company/Employee scope, branch-at-recording and validated IANA timezone-at-recording, original request/actor; no mutable current interval/pointer/status/date total |
| AttendanceRevision | company!, employee! Employee FK, attendance! FK, number! PositiveInteger, expected_revision! Integer, operation! Char(12), effect! Char(16), start_at! aware DateTime, end_at! aware DateTime, local_start_date! Date, local_end_date! Date, reason! Text blank allowed only RECORD, actor! User FK, request_key! UUID | All append-only; scope keys match parent; derived dates match parent timezone; highest number supplies effect |

DB Attendance: unique(company,record_request_key); nonblank timezone; indexes
(company,branch,employee,id), (company,employee,id). Revision: unique(attendance,number),
unique(attendance,request_key); CHECK number>=1, expected_revision=number-1; supported operations
RECORD/CORRECT/VOID/REINSTATE and effects ACTIVE_INTERVAL/VOIDED; number=1 iff operation=RECORD;
VOID iff effect=VOIDED; start<end; elapsed<=24h; local_start_date<=local_end_date; reason nonempty
for number>1. These are same-row facts, not DB enforcement of contiguous history/parent ownership.
Composite indexes (company,employee,start_at,id), (company,start_at,id),
(company,employee,local_start_date,id), (company,employee,local_end_date,id), plus unique parent/ordinal.
Duration CHECK is represented with backend-supported datetime arithmetic; PostgreSQL/SQLite migration
round-trip tests must prove equivalent semantics, not silently omit SQLite checks.

Revision 1: RECORD/ACTIVE_INTERVAL, expected_revision=0, actor=recorded_by, request_key=record key;
original interval and optional recording reason. Correction requires latest ACTIVE, changes interval,
nonblank reason and expected ordinal. VOID requires latest ACTIVE and copies that prior interval/dates
exactly into new VOIDED evidence; no input replacement interval. REINSTATE requires latest VOIDED and
explicit new valid interval (may equal original), nonblank reason. CORRECT with unchanged interval
and a new key rejects as no-effective-change, not an unrecorded successful correction receipt.
VOID→VOID and ACTIVE→REINSTATE also reject; exact prior-key retry is handled first.

Highest revision of ANY effect is current authority; never highest ACTIVE. Latest structurally
invalid scope/ordinal/interval/date/effect fails closed, never skips to older state. Current ordinal
is indexed MAX/ORDER BY number DESC LIMIT 1; no wall-clock authority and no Audit reconstruction.
Private append validates predecessor number/operation and parent; no generic mutable cache.
On a normal supported path, positive monotone append plus unique keys makes a contiguous chain;
unrestricted SQL/disabled constraints are not a supported mutation API or security sandbox.

## 6. Time semantics and civil-date boundaries

Public attendance API accepts aware datetimes only, preserves microseconds and normalizes to UTC;
aware offset/fold explicitly identifies an instant. Invalid/overflowing dates/offsets or naive data
produce field ValidationError before comparison. `0 < elapsed <= 24 hours` uses UTC instants,
not wall-clock subtraction. Cross-midnight/multiple sessions are valid; no shifts/breaks/daily cap.
Frozen Attendance timezone comes from locked Company on initial creation, not arbitrary client input.
Occupied dates are validated search facts, not independent interval authority. Reuse the civil-day
boundary helper below on a conservative UTC-date envelope (start UTC date−2 through end UTC date+2,
at most seven midnights for <=24h). Reject unsupported boundary/overflow geometry. Positive
intersection of [start,end) with admitted day windows determines occupied dates; prove endpoint
start/end−1 microsecond date equivalence within that admitted geometry before caching first/last
local dates. This avoids silently misclassifying historical date-line retreats. Ordinary New York
fall-back/spring-forward days have unique midnights and remain supported. Employment checks use
these frozen local dates, not naive endpoint assumptions on unsupported calendars.

HTTP datetime-local is a presentation adapter, not business rule authority. New ambiguous/nonexistent
input fails normal Django timezone validation. Corrections render each endpoint in Attendance's frozen
zone. Before generic ambiguous-time conversion, exact raw `%Y-%m-%dT%H:%M` equality with the trusted,
company-scoped persisted endpoint returns that exact original aware datetime. No hidden/query/client
original is trusted. A changed minute follows normal validation and starts at :00.000000. Test both
New York folds, spring gaps, sub-minute precision and changed time, following Inventory's pattern.

Leave day interpretation uses Leave's frozen timezone, not Attendance's or newly current Company zone.
For a requested inclusive 1..366 dates, compute each local midnight through end+1 (<=367 boundaries).
Try fold=0 and fold=1, UTC round-trip back to the exact wall datetime; deduplicate equal UTC instants.
Exactly one valid instant per midnight is required; gap, ambiguity, date overflow, nonincreasing UTC
boundaries or skipped-date geometry rejects with an explicit unsupported-calendar-boundary error.
No silent ZoneInfo attachment/24-hour assumption. The admitted day windows are half-open consecutive
UTC intervals; their union [first boundary,last boundary) is exact admitted full-day coverage.
Very unusual historical date-line/calendar transitions need explicit failing fixtures and must not
be approximated as ordinary DST. HR-1 must demonstrate the admitted geometry before release.

No attendance/leave rule compares unrelated server creation/update/audit clocks to prove order.
Expected revisions, locks and state transitions provide causality; company_local_today is used only
where employment date eligibility explicitly requires it. Timezone snapshots are historical
interpretation, not a second current Company configuration authority.

## 7. Bounded conflict and eligibility queries

Technical constants proposed for v1: maximum attendance elapsed 24h; maximum leave dates 366;
maximum conflict work 1,000 candidates + one sentinel; UTC scanning chunks <=31 days. Exceeding
any bound is a fail-closed ValidationError with no effect/audit, not a truncated successful answer.
No generic indexing/maintenance framework, mutable interval projection or PostgreSQL exclusion extension.

### Effective interval overlap

Under locked Company/Employee and selected alias, for proposed [s,e):

1. Query Revision in that Company/Employee with `start_at >= s−24h AND start_at < e AND end_at > s`.
   Include ALL candidate operations/effects and superseded rows, deterministic start_at,id order;
   fetch at most 1,001 before latest/effect filtering. Clamp datetime underflow safely, never wrap.
2. If >1,000, reject. Extract bounded distinct parent IDs. Resolve latest of ALL effects for each
   through unique(attendance,number) index and scalar newest-row lookup, not loading its whole history.
3. Validate parent/company/employee/timezone and latest same-row/date consistency. For number>1 fetch
   the one indexed immediate predecessor, require expected_revision=number−1 and a legal
   operation/effect transition, and for VOID exact copied interval/dates. Missing or contradictory
   predecessor fails closed, never falls back or scans the chain. When correcting,
   exclude only the authoritative locked parent identity from conflicts, never an unvalidated input FK.
4. If any latest ACTIVE interval has start<e and end>s, reject. VOID does not occupy time. A latest
   interval genuinely overlapping must have its own indexed start in the window by the 24h bound;
   an older candidate moved elsewhere cannot falsely become current. Adjacent end=start is legal.
5. If parent locks are used, lock only this bounded parent set + target in UUID order; revisions are
   immutable and need no rewrite locks. Employee already serializes supported appends. Re-read latest
   after waits, revalidate references, then final authority. No whole-history FOR UPDATE.

This is time-window and work bounded, not a promise that a database index visits exactly N physical
pages. HR-1 must inspect PostgreSQL EXPLAIN with dense synthetic superseded history, confirm indexable
predicates, bounded Python fetch/query counts and cap-before-latest behavior. No unbounded fallback.

Approval applies the same effective-interval query to each <=31-day slice of the validated Leave UTC
window, with one cumulative 1,000-row work budget across slices (deduplicate by revision ID); boundary
overlaps are checked inclusively as intervals, not local-day totals. Attendance's reverse query finds
APPROVED same-Employee Leave with cached validated UTC windows intersecting [s,e), max1,001; validate
each candidate's frozen dates/zone/window before deciding. Never filter conflicts to actor-visible Branch.

Leave submit/approve finds SUBMITTED/APPROVED same-Employee other requests where inclusive date labels
overlap OR frozen UTC windows intersect. Lock bounded candidates UUID ordered. Cap before materializing
results. The extra UTC predicate prevents double coverage from changed Company timezone even if
adjacent raw date labels differ. DRAFT/REJECTED/CANCELLED do not block; historical rows remain.

Employee date/end validation uses indexed outside-range derived local-date candidates plus newest
revision lookups, with the same sentinel/work cap, and indexed EXISTS/limited leave ranges. Verify
derived facts against UTC/zone on candidates. No all-history Python scan; dense unsuitable history
fails closed pending a separately reviewed query improvement. These caps are not daily/entitlement limits.

## 8. Transactions, lock order and final authority

Every mutation uses `@business_atomic` or `business_atomic_context()` on the call/enter-time alias.
PostgreSQL READ COMMITTED is the supported concurrency mode. No arbitrary isolation override.

Global HR order (omit irrelevant classes, never reverse them):

```text
active Company FOR UPDATE
-> Employee (existing target; multiple IDs sorted if ever necessary)
-> Department rows UUID order
-> Branch rows UUID order
-> Party rows UUID order
-> LeaveType rows UUID order
-> referenced User union including actor, UUID order, FOR SHARE
-> bounded Attendance parents UUID order + immutable newest revision reads
-> bounded LeaveRequest rows UUID order
-> final Core authority: actor / complete Roles / complete Permissions
-> operation-specific persistence + Core Audit -> outer commit
```

Create Employee has no Employee row yet: Company serialization and uniqueness reserve its identity;
take Department/Branch/Party/User references before final authority. Setup-only operation locks its
Department/Type after Company, uses indexed membership EXISTS, never locks Employee after setup.
Leave operations gather attendance candidates BEFORE locking Leave parent/candidates; correction
locks its Attendance parent before any Leave row. Company/Employee already serialize same-scope
writers; this fixed order also prevents future nested order inversion. References are ID/scalar
discoveries only until locked; persisted Company/parent IDs are authoritative and revalidated.

Department/Branch/Party/LeaveType use owner rows locked FOR UPDATE when eligibility matters.
Party ordinary writers do not use Company-first locks but their SQL updates conflict with HR's
Party row lock; re-read active PERSON after waiting. Branch supported saves start Company→Branch.
No HR reference write or owner-private helper import. Global User references use HR-local selected-
alias quoted `FOR SHARE`, sorted union of actor/linked/provenance inputs, never FOR UPDATE. SQLite
retains value validation, not a row-lock claim. Compatible reader locks prevent swapped actors/linked
Users across Companies from forming an exclusive-upgrade cycle; include this exact race test.
Historical actor/provenance Users need identity preservation only, not renewed activity/grants:
deactivated prior requesters/recorders do not make valid history corrupt. Current actor and new
association alone need their current activity/access checks.

Immediately after Company wait, validate BusinessContext and all compound initial permissions.
After ALL domain/reference waits, refresh their relevant activity/ownership facts, then invoke
`require_final_permission` for each required code in deterministic code order. Core's first call
locks actor, ALL assigned same-company Roles and ALL reachable Permissions (including inactive rows),
UUID ordered; later compound calls reuse the complete set, not add an earlier authority anchor.
Superuser namespace stabilization remains Core-owned. Do not lock a partial permission witness,
copy Core private locking helpers, cache authority or preauthorize before reference waits.

Final guard is immediately before first authoritative effect and before a successful exact retry/
no-op return. No later new domain/reference lock after final authority. All result materialization
stays within transaction/authority lifetime. Revoked actor/Company/Branch access/Role/Permission
fails closed even if the form or earlier check succeeded. No special HR bypass for superuser domain
invariants or self-approval. Expected revision/status always re-read after waits.

Persistence collision: supported Company/Employee locks prevent ordinary same-source races. DB
uniqueness remains backstop. Catch only positively identified HR unique constraints inside a nested
same-alias savepoint; after rollback re-read immutable keyed evidence and compare full input before
authorized recovery. Identity duplicates/conflicting requests return explicit ValidationError;
unclassified IntegrityError propagates/rolls back, never generic success. Outer audit failure,
validation failure or process crash before commit leaves no effect; response loss after commit
recovers only as the specific retry/lookup rules allow. No independent inner commits.

## 9. LeaveRequest exact schema and lifecycle

Beyond common UUID/timestamps, proposed fields:

| Fields | Type/null | Mutability / meaning |
| --- | --- | --- |
| company, employee | Company!, Employee! | Immutable; Employee cannot change even in DRAFT |
| branch, timezone | Branch?, Char(64)! | Immutable current Employee Branch + Company zone at creation |
| create_request_key, requester | UUID!, User! | Immutable explicit create identity/actor, no create-history receipt |
| leave_type, start_date, end_date, reason | LeaveType!, Date!, Date!, Text! | DRAFT only; full inclusive dates, reason may be empty |
| window_start_at, window_end_at | aware DateTime! | Verified derivatives of frozen zone/date boundaries; updated only with DRAFT dates, not independent authority |
| status, revision | Char(9)! DRAFT default, PositiveInteger! 1 | Owner transitions/edits only |
| submit_key, submitted_by, submitted_at | UUID?, User?, DateTime? | Immutable once submitted |
| submit_from_revision, submit_revision | PositiveInteger?, PositiveInteger? | Original expected and resulting revision |
| beneficiary_user_at_submission | User? | Frozen nullable association, no grant |
| decision_key, decided_by, decided_at | UUID?, User?, DateTime? | One immutable decision receipt |
| decision_from_revision, decision_revision, decision | PositiveInteger?, PositiveInteger?, Char(8)? | APPROVED/REJECTED, preserved after cancellation |
| decision_reason | Text! default empty | Required rejection; optional approval, frozen once decided |
| cancel_key, cancelled_by, cancelled_at | UUID?, User?, DateTime? | One immutable cancellation receipt |
| cancel_from_revision, cancel_revision | PositiveInteger?, PositiveInteger? | Expected/resulting revision; original state inferable from receipt/status history |
| cancel_reason | Text! default empty | Required on cancellation, immutable afterward |

The nullable beneficiary snapshot is valid even after submit if there was no linked User; it is not
included in event all-or-none checks. Reasons max2,000. Event result=from+1; each present event has
all key/actor/time/from/result fields, except optional beneficiary snapshot. Decision field required
with decision receipt, absent otherwise. DB CHECKs: allowed status, positive revisions, dates ordered,
1..366 date length, window_start<window_end, supported decision, receipt all-or-none and from/result
relationships; decision_from_revision=submit_revision; cancel_from_revision equals retained decision
revision if decided, else submit revision if submitted, else the current pre-cancel draft revision;
current revision equals the latest retained event revision outside DRAFT. Require status-compatible
receipt presence (e.g. APPROVED requires submit+APPROVED decision;
REJECTED requires submit+REJECTED decision; SUBMITTED requires submit/no decision/cancel; DRAFT none;
CANCELLED requires cancel and may retain submit and approved decision but never rejected decision).
No DB CHECK claims to enforce timezone conversion, actor eligibility or cross-row conflicts.

DB unique(company,create_request_key); unique(company,submit_key), unique(company,decision_key),
unique(company,cancel_key) when non-null. Scope of event keys is Company+event family; submit/decision/
cancel keys must also be distinct within one request (service and same-row CHECK). Do not silently
reuse another request's event key. Event audit/equality includes actor, action, original expected
revision and reason; submission content remains in the frozen row. No generic receipt/history table.
Indexes (company,employee,status,start_date,end_date), (company,employee,status,window_start_at),
(company,branch,start_date,id), (company,status,start_date,id).

### Public lifecycle and domain eligibility

| Operation / from | To | Required validation under locks | Historical/retry treatment |
| --- | --- | --- | --- |
| create | DRAFT | ACTIVE Employee/active PERSON/type, dates inside employment, validated frozen window | Duplicate create key conflicts; authorized lookup only |
| update DRAFT | DRAFT | expected revision; type/dates/reason only; same eligibility and window | True unchanged values return current revision after final guard; stale edit conflicts |
| submit DRAFT | SUBMITTED | expected revision, active identities/type, no SUBMITTED/APPROVED date OR window overlap; capture linked User | Freeze payload and one submit receipt |
| approve SUBMITTED | APPROVED | expected revision, active Employee/PERSON/type, no leave overlap, no effective attendance window, self-approval rule | One decision receipt; source is_active not a workflow state |
| reject SUBMITTED | REJECTED | expected revision, nonblank reason, self-approval rule | Inactive identity/type may be resolved; one decision receipt |
| cancel DRAFT/SUBMITTED/APPROVED | CANCELLED | expected revision, nonblank reason; APPROVED needs approve as well as cancel permission | Inactive references allowed; one cancel receipt; no implicit reopening |

All states are staff-operated, not requester/self-service ownership ACL. No automatic manager hierarchy.
Draft dates inside employment and eligible Employee enforced; request may be retrospective while
Employee still ACTIVE. No weekend/holiday deductions, accrual or payroll effects. Approval rechecks
all conditions after waiting, not trusts submission. Reject/cancel never erase frozen evidence.

Self-approval AND self-rejection deny if actor equals immutable requester, current beneficiary
Employee.user, or beneficiary_user_at_submission. Apply to superusers too. Association is a negative
separation check, never positive authority or email-derived human identity. Unlink/relink cannot
erase submission snapshot; a later link is also checked. Ordinary unlink cannot alter frozen receipt.

## 10. Public API, permissions and scope matrix

All service inputs are IDs/context/scalars, never HttpRequest/ORM objects from another alias.
Proposed signatures below are exhaustive operation families; implementation may split Python files
without adding services/policies. `expected_revision` is required for existing-row changes.

Permission abbreviations expand EXACTLY to:

```text
EV=hr.employee.view       EM=hr.employee.manage
DV=hr.department.view     DM=hr.department.manage
AV=hr.attendance.view     AR=hr.attendance.record     AC=hr.attendance.correct
LV=hr.leave.view          LR=hr.leave.request         LA=hr.leave.approve
LC=hr.leave.cancel        LM=hr.leave_type.manage
```

No extra leave_type.view permission: ordinary type choices require LV; setup management requires
LM+LV. All are valid three-part Core names; none is registered by HR-0.

| Service / selector / corresponding HTTP action | Exact compound codes | Context and inputs/result |
| --- | --- | --- |
| department_page/detail | DV | Company-wide setup read; Company or Branch context |
| create_department(code,name), update_department(id,expected_revision,name,is_active) | DM+DV | Company context only; bounded setup DTO |
| leave_type_page/detail/choices | LV | Company-wide read; include activity/history as authorized |
| create_leave_type(code,name), update_leave_type(id,expected_revision,name,is_active) | LM+LV | Company context only |
| employee_page/detail; HR PERSON choices | EV | Company, optional current-Branch confinement; new Party choices active PERSON |
| User association choices | EM+EV | Valid Company or Branch context, bounded Company-eligible UUID/activity only; User has no Branch ownership and choice grants no access |
| create_employee(party_id,employee_number,joining_date,user_id?,department_id?,branch_id?) | EM+EV; DV additionally if Department used | Company context only, new Employee DTO |
| update_employee(id,expected_revision,joining_date,user_id?,department_id?,leaving_date?) | EM+EV; DV if Department read/assigned | Current Employee Branch confinement; no Party/number/status/Branch reassignment |
| transfer_employee_branch(id,expected_revision,branch_id?) | EM+EV | Company context only; current/new Branch IDs validated |
| end_employee(id,expected_revision,leaving_date) | EM+EV | Current Employee Branch confinement |
| attendance_page/detail/revision_page | AV+EV | Frozen Attendance Branch; live minimal identity, bounded current/history DTOs |
| record_attendance(employee_id,request_key,start_at,end_at,reason="") | AR+AV+EV | New record: current Employee Branch; existing-key retry: persisted Attendance frozen Branch; returns original/current classifications |
| revise_attendance(id,expected_revision,request_key,operation,start_at?,end_at?,reason) | AC+AV+EV | Frozen Attendance Branch; CORRECT/VOID/REINSTATE only; Employee current Branch need not match historical snapshot |
| leave_page/detail | LV+EV | Frozen Leave Branch, not current Employee Branch |
| create_leave(employee_id,create_request_key,leave_type_id,start_date,end_date,reason="") | LR+LV+EV | Current Employee Branch confinement; frozen Branch/zone; Employee immutable |
| update_leave(id,expected_revision,leave_type_id,start_date,end_date,reason) | LR+LV+EV | Frozen Leave Branch; DRAFT only |
| submit_leave(id,expected_revision,request_key) | LR+LV+EV | Frozen Leave Branch; creates submit receipt |
| decide_leave(id,expected_revision,request_key,decision,reason="") | LA+LV+EV | Frozen Leave Branch; APPROVED/REJECTED and domain separation |
| cancel_leave(id,expected_revision,request_key,reason) | LC+LV+EV; LA also if originally APPROVED | Frozen Leave Branch; retry retains original compound requirement after cancellation |

Related Employee/Department selection requires EV/DV respectively; attendance/leave action forms
showing existing history use AV/LV. Permission requirements apply to Python and HTTP alike, including
GET mutation forms, results and retries. No permission inferred from linked User or Django groups.
Employee detail never automatically emits Attendance/Leave without AV/LV; Department identity/name
requires DV, otherwise omit that related projection without weakening mutation checks. Attendance/
Leave can project beneficiary identity under EV using the historical record's frozen Branch, even
after transfer; this does not authorize unrelated current Employee details in another Branch.

Scope for every row/reference: explicit `company_id=context.company_id`. Employee→Party/Department/
Branch, Revision→Attendance/Employee, Leave→Employee/Type have matching Company on locked facts;
wrong/malformed IDs fail closed, no informative foreign lookup. With context.branch_id, Employee
uses current Branch; Attendance/Leave use frozen Branch; null snapshots excluded. Internal overlap/
eligibility checks cover ALL Employee facts across Branches but return generic conflict, not hidden
record IDs/narrative. Company-wide Department/Type remain available as choices. Warehouse context
rejects all HR operations. No-Branch Company grants mean company-wide, not implicit branch-only ACL.
Inactive historical Branch reads/corrections can occur in valid Company context; inactive selected
context Branch never gains a bypass. Attendance create/Leave create need active assigned Branch;
historical correction/leave transitions preserve snapshots, with active context required.

## 11. Retry and persistence boundary matrix

Canonical attendance equality: validated UTC ISO instant with full microseconds, Employee UUID,
request UUID, operation, original expected revision (0 for record), actor and normalized reason.
VOID has no new interval inputs; stored interval must equal preceding revision. Stored branch/zone
belong to original effect, never substituted from later current configuration. Record key scope is
Company; correction key scope is Attendance (revision1 also reserves its key). Original revision
and parent consistency must be validated on recoverable retry. New recording checks current Employee
Branch; existing-key retry checks persisted Attendance frozen Branch before returning its minimal
Employee identity/current effect, not Employee's newly assigned Branch. Former Branch A can recover
its A snapshot after transfer to B; Branch B cannot recover A history merely because Employee now
belongs to B. Company-wide valid context remains permitted. Compound current permissions still apply.
Discover existing key before applying new-record eligibility, lock its authoritative Employee/parent
and compare submitted identity; old receipt never authorizes a different snapshot or new record.

| Mutation | Matching retry / no-op | Conflict / historical state / audit |
| --- | --- | --- |
| Department/Type create | No create receipt; authorized code lookup | Duplicate conflicts, never overwrites; one created audit |
| Department/Type update/activity | Same values + current expected revision => final-authorized no-op | Stale expected revision conflicts even if response was lost; changed values increments/audits once |
| Employee create | No generated external receipt; authorized Party/number lookup | Duplicate number/Party/active-User conflicts, no second employment |
| Employee update/transfer/end | Same state/values + current expected revision => guarded no-op; already-ended matching date requires that current revision too | Response-loss stale revision conflicts/authorized lookup, not hidden end idempotency; different ended date requires explicit versioned date correction, never re-end/rehire; actual change one audit |
| Attendance record | Existing Company key + exact immutable original input => matched revision1 and separately current effect | Different input/actor/Employee conflicts; later Branch/zone/revision changes do not recreate or falsify original receipt |
| Attendance revision | Existing parent key + exact operation/expected/reason/interval => matched revision and current effect | Different key payload conflicts; later ordinal does not invalidate intrinsic original receipt or certify it current; new stale correction fails |
| Leave create | Duplicate create identity => conflict + permitted lookup | No assertion original draft still identical after edit |
| Leave draft edit | True unchanged/current version => no-op | Stale conflicts; after submit fields frozen |
| Leave submit | Existing submit key + same actor/from-revision and frozen submitted input => original submit revision + current status | After approve/reject/cancel, receipt remains historical; never re-submit; changed actor/key use/payload conflicts |
| Leave approve/reject | Same decision key/from-revision/actor/outcome/reason => original decision revision + current status | After APPROVED→CANCELLED, retry is historical approval only; other decision/reason conflicts; current self-approval check still applies |
| Leave cancel | Same cancel key/from-revision/actor/reason and original required permission set => original cancel revision | Changed payload conflicts; retains prior decision/submission; no reopen |

For submit, retain the input through immutable frozen row fields; exact retry does not silently use
new date/type/Company zone. Decision/cancel persist from/result ordinals and effect input; no need to
compare unordered server timestamps. Missing/corrupt event provenance fails closed. Final authority
is required before every successful recovery/no-op, even if no insertion will occur. No duplicate
success audit and no refreshed occurrence time. A new key cannot turn a stale transition into success.

All six HR aggregates are service-owned: public save/create/delete, QuerySet.update/delete,
bulk_update, bulk_create (including ignore/conflict upsert), get_or_create creation, update_or_create
creation/update reject bypass. Ordinary reads remain possible to internal selectors. Module-local
operation tokens/private methods expose only validated create/setup edit/Employee edit/append/Leave
transition field sets; no caller `_allow_*` flags or public generic bypass. Historical Attendance/
Revision cannot update any fields. Leave submitted content and each receipt are immutable; lifecycle
changes use a narrowly guarded persisted-state transition primitive. No blind shared guard framework
for setup rows. Persisted parent/Company is authoritative before stale-object save/delete checks;
in-memory FK substitution cannot erase history. No supported hard deletion of any HR identity.

Protected manager/base-manager/default-manager paths must be covered, including refresh/update_fields,
cached objects, cascade attempts and bulk variants. Raw SQL by an unrestricted DB operator is outside
the ordinary API threat model; FK/CHECK/unique still protect their genuine single-row facts.

## 12. Audit, module and alias contracts

Exact actions:

```text
hr.department.created  hr.department.updated
hr.employee.created    hr.employee.updated    hr.employee.ended    hr.employee.branch_changed
hr.attendance.recorded hr.attendance.corrected hr.attendance.voided hr.attendance.reinstated
hr.leave_type.created  hr.leave_type.updated
hr.leave.created       hr.leave.updated       hr.leave.submitted
hr.leave.approved      hr.leave.rejected      hr.leave.cancelled
```

One meaningful action per public actual change: employee branch transfer uses branch_changed rather
than duplicate updated; setup retirement uses updated with activity field. Core Audit same transaction/
alias, actor from context, Company/aggregate/revision IDs and bounded changed-field/effect metadata.
No reasons/contact payload in general audit; scoped HR keeps narratives. Full before/after mutable
business comparison includes all actual fields, not a partial tuple. Injected Audit failure rolls
back business row, appended revision/receipts and revision counter. Reads/no-ops/retries do not audit.

Future manifest: `hr`, `Human Resources`, `0.1.0`, hard dependencies exactly
`party, organization, reference, access`, permissions exactly the twelve codes in section 10.
Core identity/common/audit/database/time/registry are infrastructure. No owner→HR, HR→finance/
commercial/Ecommerce or HR/Ecommerce reverse pair. Historical registration migration freezes strings
locally; new row disabled; existing explicit enablement/permission retirement preserved. No dynamic
installer, automatic dependencies/license or migration history rewrite.

HTTP/nav uses `module_required("hr")`: missing/disabled -> hidden + 404 at request time, no import-time
database work. Installed Python services remain available with valid context/RBAC/schema independent
of registry. No unconditional Party HTTP decorator prerequisite when rendering only HR's bounded
projection; Party page itself remains separately gated. This does not install/uninstall owners.

ADR 0012: all ORM/raw query/lock/audit/unique recovery goes through current selected alias. No default
cursor/transaction/using literal, cached cross-alias model or tenant field. Bootstrap scopes both
database_execution(alias) and migrate --database alias, then registration/seeds only when requested.
Unknown alias/nested switch fails closed; no distributed atomicity or tenant-security claim.

## 13. HTTP, selectors, pagination and browser requirements

Minimum routes/screens under future `/hr/`: Employee list/detail/create/edit/end/transfer;
Department list/manage; completed Attendance list/detail/record/correct/void/reinstate/revision
history; Leave list/detail/create/edit/submit/approve/reject/cancel; LeaveType manage. No new shell.
Django Templates + Tailwind + HTMX + Alpine only. Views/forms translate input/context and display
service errors; no lifecycle/overlap/authorization business rules in presentation/admin/signals.
GET mutation forms require the action's full compound set before materializing fields/choices.
POST only for actions, CSRF mandatory; stale CompanyBoundForm on EVERY mutation, expected revision
and immutable request UUID hidden as untrusted submitted data. Branch changes also revalidate current
scope, not only a client hidden company. Inputs never select actor or trusted original timestamps.

Selectors are materialized bounded Page/DTO calls inside selected-alias business transactions:
lock Company using established convention, validate current scope/view permissions, evaluate bounded
rows/related projections, final current guard immediately before return after any wait. No lazy
QuerySet or deferred relationship access bypasses late authorization. Repeated requests reauthorize;
no claim that an old response can be revoked from the user's memory.

| Selector family | Bounds / stable ordering / data |
| --- | --- |
| Employee list/choices | 50 rows/page; employee_number,id; search<=200, status/Branch preserved; one Party scalar projection per result, no contacts/addresses |
| Department/LeaveType lists/choices | 50/page; code,id; activity/search query preserved; no unbounded choice dropdown |
| Attendance current list | Default last31 local dates; explicit range<=366; convert bounded search window, candidate sentinel before latest; order effective start_at DESC, Attendance UUID; 50/page; VOID included only explicit filter |
| Attendance revisions | One scoped session, 50/page, number DESC,id; no full revision collection |
| Leave list | Default date window today−31..today+31; explicit range<=366, status/Employee/Branch/search preserved; start_date DESC,id; 50/page; current effect + permitted receipt labels |
| Details/related sections | One validated aggregate; history is separate bounded page; Department name gated DV, Attendance/Leave sections gated AV/LV |

Count/page SQL stays scoped, not full Python materialization. Attendance search bounds are widened
conservatively for UTC/timezone offsets then validated under frozen zones; never drop cross-midnight
rows at local date boundaries. On work cap, return explicit bounded-query error requiring narrower
filters, not partial count/results. Pagination validates page positive integer, missing page default1,
out-of-range existing convention; all ordering ends in UUID. No cap can hide conflicts in mutations.

Preserve existing 50-row/query-string pattern and `#list-results` HTMX swaps. GET-only safe navigation,
redirect/full refresh/deep-link, Back/Forward, active nav, persistent shell, local table scroll and
non-JS full-page fallback. Mutations remain normal Django POST, not HTMX history GET side effects.
Hostile/long text escaped, errors bound/wrap, no foreign-ID error leaks. Future actual browser QA at
390/768/1280: max labels/reasons/numbers, local overflow only, focus/Tab/Enter, errors, contrast/labels,
CSRF rejection, non-JS and stale Company/Branch forms. Do not claim browser PASS in HR-0.

## 14. Concurrency matrix

Every PostgreSQL case uses real lock wait detection/barriers (pg_stat_activity/pg_locks or equivalent),
not arbitrary sleeps. Clean worker connections/finally-close, isolated synthetic DB. Test both winner
orders; SQLite explicitly skips lock-specific assertions. Each loser must have no partial effect/audit.

| Race | Ordered locks / winner behavior | Retry/audit oracle |
| --- | --- | --- |
| Duplicate number; same Company/Party create | Company→complete references; first persists, second explicit unique conflict even different number/Party input | One Employee/created audit; no number reuse |
| Same active User association/create | Company→Employee/ref User SHARE; first claims partial key, second conflict | One active association, losing revision/audit absent |
| Employee end vs record | Company→Employee→refs; end-first new record denies; record-first end rechecks frozen eligibility and succeeds only if interval fits proposed end | No deletion; one record audit and valid end or no end audit |
| Branch transfer vs record/leave create | Company→Employee→Branch; transfer-first new snapshot uses new Branch; record-first old snapshot immutable | Stale branch context denies after wait; explicit retry uses original snapshot |
| Overlap record/record incl cross-midnight/Branch | Company→Employee→bounded sessions; first interval persists, second overlap rejects; adjacent both succeed | One per key; multiple non-overlapping same-day sessions accepted |
| Correction/correction | Company→Employee→Attendance latest; first appends, new stale expected ordinal rejects | Same exact key returns same revision; distinct different intent no second audit |
| Correction/void/reinstate vs approval | Company→Employee→bounded Attendance→Leave; first effect changes conflict decision; approval-first conflicting correction/reinstate denies, correction-first conflicting approval denies | VOID can remove current conflict only; no erased revisions |
| Overlap submit/submit | Company→Employee→Attendance→Leave; first submits, second overlapping date/window fails | One submit receipt/audit; drafts intact |
| Approve vs approve/reject | Same ordered Employee/Leave; first decision wins; other different request/outcome stale/conflict | Exact same event retry one receipt/audit; no opposite decision |
| Approve vs cancel | Same order; cancel-first approve denies; approve-first cancel requires approve+cancel and current revision | Distinct authorized transitions retained; stale loser no audit |
| Approve vs attendance record, both orders | Same Company/Employee; attendance-first approval rejects; approval-first conflicting record rejects | No simultaneous current conflict; no partially created session/receipt |
| Actor/Role/Permission retirement or supported batch rewrite at later reference waits | HR Company/domain wait then complete final Core authority; revocation-first deny; HR final locks-first writer waits until commit | No old authority reuse; cover all compound actions, SU namespace, inactive roles/permissions |
| Company/Branch access revoke while waiting | Company-first Access writer; revocation-first current validation denies, HR-first valid commit then revoke | Retry reauthorizes; no resurrection via User association |
| Party type/activity, Department/type/Branch retirement | Company/row lock matches supported owner; retirement-first new use denies; use-first valid commit, later history retained (Department retirement still rejects ACTIVE assignments) | No stale reference acceptance or implicit owner write |
| User deactivate + swapped actor/reference Users across Companies | Compatible ordered User SHARE; deactivate-first new link denies, link-first identity writer waits; no exclusive upgrade cycle | No grant; no deadlock, correct final actor check |
| Employment date correction vs approved leave/attendance | Company→Employee then bounded facts; prior valid effect cannot be moved outside eligibility by stale edit | No silent cancellation/void; date edit audit only if valid |

Add read-path revocation before materialization/after Company or reference wait; delayed selector
results must not escape current view guards. Test Company/Branch switch HTTP matrix for all mutation
families, not just create. Two Companies sharing actor/Permission/User must preserve global authority
order and nested audit rollback. No mutable timestamp as race winner evidence.

## 15. Database guarantees and SQLite policy

DB directly enforces UUID PK/FKs, normalized persisted code uniqueness, Employee Company+Party/
number/active-User keys, Attendance record key, revision parent ordinal/key, Leave create/event keys,
supported enums/null groups/date/interval/ordinal CHECKs. PostgreSQL CHECK cannot enforce same-company
FK pairs, active PERSON/Type, append-only history, highest revision, scope/RBAC, self-approval or
cross-row overlap. Those are service/protected-ORM/lock invariants and require adversarial tests.
No overlap exclusion constraint selected: would add revision-effective projection/extension and
SQLite complexity without need under Company→Employee serialization. Honest constraint review,
fresh bootstrap and drift must verify actual migration semantics in HR-1.

SQLite functional: field bounds/normalization, states/retries, append-only managers, projection,
single-thread overlap/conflict, audits/rollback, dates/DST, scope/HTTP/pages and supported alias reads.
PostgreSQL-only: real row locks, FOR SHARE/order/blocking, simultaneous races/revocation, query-plan
evidence/catalog-specific probes and any backend-specific migration inspection. Label each skip with
reason; no unexplained skips, deadlock warnings or claim SQLite certifies production concurrency.

## 16. Final future HR-1 acceptance matrix

ALL H01–H18: **REQUIRED — NOT EXECUTED IN HR-0**. Evidence must cite exact implementation SHA,
test paths/results and browser/run records, not a checklist self-approval.

| ID | Concrete acceptance oracle / relevant contract |
| --- | --- |
| H01 | Two Company fixtures: every six-model direct/list/search/choice/history/service path rejects foreign/malformed parents; stale-company POST for create/edit/end/transfer/record/revision/all leave/setup actions; no foreign data/audit |
| H02 | Department company-wide/no Branch; Employee current Branch vs frozen Attendance/Leave after transfer; null/inactive snapshots and company-context access; transfer revision/audit; branch switch and hidden conflict behavior |
| H03 | One Party/Employee all-history identity and number, active-User partial uniqueness; exact five-field Party projection/no contact/address queries; inactive/non-PERSON historical vs new behavior; link never writes grants/credentials; no rehire |
| H04 | Code/number normalization/max/duplicates and DB uniqueness; real Company/Party/number/User races, Department retirement with ACTIVE assignments, type retirement/references; no key reuse on retirement/end |
| H05 | Exact twelve registered active codes; all section10 compound services/GET/POST/results/retries with non-superuser happy path and each missing code; SU missing/retired code deny; requester/current/snapshot beneficiary self-approve/reject deny |
| H06 | Disabled/missing HR navigation/URL 404; enabled route works; installed Python record/setup works with registry absent but RBAC required; registration preserves enablement/retired permission and frozen migration strings |
| H07 | Non-default selected alias, poisoned default cursor for all services/pages/raw locks/audit/registration/bootstrap; nested same-alias rollback, unknown/switch reject; no cached cross-alias object |
| H08 | Two+ same-day sessions, cross-midnight/Branch/date conflict and adjacent intervals; record response-loss retry after transfer/zone change, former-A scoped recovery and new-B denial of A history; different payload/key conflicts; 24h limits/cap/indexed query evidence; no date unique/current balance |
| H09 | Aware UTC/microseconds/DST both folds/gaps, trusted unchanged inputs and changed-minute behavior; exact-midnight end, leap/cross-midnight/zone change, 366-date/civil boundary admission, employment limits and wall-clock rollback |
| H10 | Append sequence/CORRECT/VOID/REINSTATE states, stale ordinal/exhaustion, same-key prior-effect retry after later revision, intrinsic corrupt latest reject; wrong in-memory parent/delete/public/bulk/upsert/manager attacks leave historical rows intact |
| H11 | Exact Leave schema/receipt null groups, DRAFT-only edits, full inclusive dates/no hours, active type/Employee rules vs historical retry, precise legal transitions and separate cancellation permissions; no entitlement/workflow |
| H12 | All section14 overlap/approval/reject/cancel/record/correction races both winners with pg lock evidence; raw-date+UTC-window cross-zone overlap; no current approved-leave/attendance conflict, loser no partial receipt/audit |
| H13 | Exact section8 lock set including global shared Users; Company wait and every later reference wait: actor/Role/Permission/Company+Branch access revoke, multi-role/compound/batch/SU cases; materialized-read late revoke and two-Company order tests |
| H14 | Every section12 meaningful field/snapshot/association/transition audit, one action per change; no-op/key retry none; injected failure at each append/receipt/audit rolls back entire selected-alias outer transaction |
| H15 | Exact action form GET/POST admission, CSRF and POST-only, CompanyBoundForm all actions, hostile text, trusted original from server, search/filter/page query preservation and 50-row stable UUID ordering; no-JS/deep links/HTMX security |
| H16 | Actual real-browser 390/768/1280 Employee/setup/Attendance/revision/Leave/errors with maximum fields, local table scroll/no page overflow, focus/Tab/Enter/labels/validation, safe GET Back/Forward/refresh; approved global shell unchanged |
| H17 | Fresh PostgreSQL zero-state schema + module-local discovery; HR with only Party/Core hard owners, and all commercial owners absent/present; no dependency cycle/eager financial/Ecommerce import or side effects; migration constraints reviewed |
| H18 | Full PostgreSQL + supported SQLite with classified skips; Ruff and EVERY changed-Python format including migrations; Django/drift, database architecture guards, node syntax/JS tests/npm/Tailwind/CSS reproducibility, docs/whitespace/protected diff; independent audit and separate exact-head hosted CI gates |

## 17. Bounded future delivery and exclusions

After accepted HR-0 and explicit HR-1: first module/schema/private persistence + deterministic
manifest migration; then pure domain bounds/dates, scoped selectors and services under the lock/
final-guard contract; then attendance/leave/race/alias oracles; then minimal existing-shell UI and
real browser verification; final full regression/independent audit. Commit/publication/adoption is
separately authorized. No future migration/history edit, shared Core extraction or speculative layer.

Exclude Payroll, salary, tax, benefits, recruitment, performance appraisal, positions/job grades,
cost centers, org charts, shift scheduling/rosters/open punches/break/device/biometric engines,
expenses/timesheets, leave entitlement/accrual, self-service, rehire/multiple employment episodes,
generic workflow/event bus/metadata/DI/plugin framework, Ecommerce and Phase 4 verticals. No extra
infrastructure, target custom BusinessOS work, SaaS activation or production deployment.
Internal authority checklist: Party identity; Employee employment; Attendance+revisions time facts;
no mutable daily summary or leave balance; Core Access current permission; Core Audit evidence only.

## Local HR-0 verification

Actual results will be recorded here before the one local proposal commit. This section is local
documentation-gate evidence only, not independent HR-0 approval or future H01–H18 execution.

Starting integrity: clean main/HEAD/origin-main/live main at exact `6453c8f...`; live HR-0 branch absent;
ADR0018 unused; new local branch created exactly from canonical base. Existing branch/tag targets
captured for final comparison. Only ADR0018 and this HR plan are needed: accepted dependency graph/
umbrella policy is unchanged, so no shared roadmap/dependency/history edit is necessary.

Actual local checks on 2026-10-14 (not independent acceptance):

| Check | Result |
| --- | --- |
| Internal contract review | Party/Employee/Attendance authority, finite schema/lock/retry/race matrices and all H01–H18 checked; no owner-policy conflict identified; clarified predecessor/receipt chains, historical Branch retry, null semantics and native Party name bound |
| Documentation validator | 49 relative file links and one heading anchor resolve; fenced blocks balanced; no trailing whitespace, final newlines present; H01–H18 exactly once in the implementation matrix |
| Documentation-only diff / `git diff --check` | Only the two new authorized Markdown paths; whitespace PASS; staged check required again before commit |
| `python manage.py check` | PASS, zero issues |
| `python manage.py makemigrations --check --dry-run` | PASS, no changes detected |
| `ruff check . --no-cache` | PASS, no source writes |
| `pytest tests/test_database_architecture.py -q -p no:cacheprovider` | 222 passed in 4.61s; existing source-level architecture guards, not HR runtime tests |
| `pytest tests/test_modules.py tests/test_database_foundation.py -q -p no:cacheprovider` | 26 passed in 14.58s; existing registry/alias/savepoint/non-default in-memory bootstrap guards |

Runtime commands used existing `ui-gate1-qa-web:latest` (Python 3.13.16), `docker run --rm
--network none`, read-only source bind mount, PYTHONDONTWRITEBYTECODE=1, config.settings.test
in-memory SQLite and all three existing financial-integration install flags enabled. No demo/customer
DB, generated assets, migrations or source file changed. No full PostgreSQL/SQLite suite, new
runtime test, browser QA or hosted HR-0 CI is claimed or required for this documentation-only gate.
Future H01–H18 still require full implementation evidence; these checks cannot substitute for it.

Final gate: **HR-0 TECHNICAL CONTRACT PROPOSAL READY FOR INDEPENDENT AUDIT** only after those checks
and the one local docs-only commit. ADR0018/HR-0 remain PROPOSED — NOT ACCEPTED. HR-1 NOT AUTHORIZED.
ECOM-0 not started by this task. Phase 3 NOT COMPLETE. PUSH NONE; PR NONE; no tag/main update. STOP.
