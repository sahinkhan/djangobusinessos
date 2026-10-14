# Phase 3A — HR Foundation

Status: **CORRECTIVE CANDIDATE — RE-AUDIT PENDING**.
ADR 0018: **PROPOSED — NOT ACCEPTED**. HR-1 NOT AUTHORIZED.

Date: 2026-10-14. Local branch: `phase3a-hr-contract`.
Canonical base: `6453c8f3202335aabe8a872046fea2e607dac858`.
Technical ADR: [ADR 0018](../../decisions/0018-hr-foundation-technical-contract.md).
Accepted umbrella: [ADR 0017](../../decisions/0017-phase3-people-digital-commerce-boundaries.md)
and [Phase 3 plan](PHASE_3_PEOPLE_DIGITAL_COMMERCE.md).

## 1. Authority, chronology and delivery boundary

The umbrella completion rule is fulfilled at the canonical base: acceptance CI #134 / run
`38570976500` and main CI #135 / run `38576825532` SUCCESS, 3,015 PostgreSQL tests each.
Those inherited results do not execute HR. OD-1–OD-12 remain resolved/frozen; only OD-1–OD-6's
remaining HR technical details are proposed here. The original internal review's no-conflict
conclusion was subsequently corrected by the supplied independent Readiness B audit below.
Internal review was not independent approval.

Original proposal `5be60f19e3bf654786abcd06b61149bc4a962ea9` is preserved above that canonical parent.
Current authorization permits exactly one local docs-only corrective commit above the proposal,
only after coherent corrections and credible User-lock proof. No amendment or acceptance.
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

### Supplied independent audit — original proposal

Verdict: **REVISE — HR-0 TECHNICAL CONTRACT REQUIRES CORRECTION**; **Readiness B**;
P0 0 / P1 0 / P2 4 / P3 0. These supplied findings are not erased or self-declared resolved:

| Finding | Original defect | Current proposed correction / review boundary |
| --- | --- | --- |
| HR0-AUD-1 — P2 | HR shared User locks deadlock inherited B→A batch writers; Core actor guard also matters | Section 8 three-relation nonwaiting admission, no unnecessary User locks, nested entry rejection; disposable proofs below; independent resolution pending |
| HR0-AUD-2 — P2 | Unsupported 24-hour Attendance ceiling and dependent lookback | No duration ceiling; complete interval predicate; long-interval/resource-error oracles |
| HR0-AUD-3 — P2 | Unsupported 366-date Leave ceiling/per-date validation | No span ceiling; exact transition-driven civil-boundary certification and long-range oracles |
| HR0-AUD-4 — P2 | Latest/immediate predecessor misses older gaps/corruption | Complete selected-chain aggregate and every-row transition checks before authority/retry; corrupt-chain oracles |

All remedies require fresh independent re-audit. No HR implementation test or acceptance PASS.

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
activity after all reference waits. Use section 8 admission on every final-Core path;
no ordered multi-User shared-row protocol is retained.

## 5. Attendance identity and revisions

| Model | Exact additional fields | Immutable / authority |
| --- | --- | --- |
| Attendance | company!, employee! Employee FK, branch? Branch FK, timezone! Char(64), record_request_key! UUID, recorded_by! User FK | All immutable; Company/Employee scope, branch-at-recording and validated IANA timezone-at-recording, original request/actor; no mutable current interval/pointer/status/date total |
| AttendanceRevision | company!, employee! Employee FK, attendance! FK, number! PositiveInteger, expected_revision! Integer, operation! Char(12), effect! Char(16), start_at! aware DateTime, end_at! aware DateTime, local_start_date! Date, local_end_date! Date, reason! Text blank allowed only RECORD, actor! User FK, request_key! UUID | All append-only; scope keys match parent; derived dates match parent timezone; highest number supplies effect |

DB Attendance: unique(company,record_request_key); nonblank timezone; indexes
(company,branch,employee,id), (company,employee,id). Revision: unique(attendance,number),
unique(attendance,request_key); CHECK number>=1, expected_revision=number-1; supported operations
RECORD/CORRECT/VOID/REINSTATE and effects ACTIVE_INTERVAL/VOIDED; number=1 iff operation=RECORD;
VOID iff effect=VOIDED; start<end; local_start_date<=local_end_date; reason nonempty
for number>1. These are same-row facts, not DB enforcement of contiguous history/parent ownership.
Composite indexes (company,employee,start_at,id), (company,employee,end_at,id),
(start_at,id), (end_at,id), (company,start_at,id),
(company,employee,local_start_date,id), (company,employee,local_end_date,id), plus unique parent/ordinal.
There is NO maximum elapsed-duration CHECK, service, widget or domain rule. PostgreSQL/SQLite
migration round-trip tests must prove start<end without restoring a ceiling.

Revision 1: RECORD/ACTIVE_INTERVAL, expected_revision=0, actor=recorded_by, request_key=record key;
original interval and optional recording reason. Correction requires latest ACTIVE, changes interval,
nonblank reason and expected ordinal. VOID requires latest ACTIVE and copies that prior interval/dates
exactly into new VOIDED evidence; no input replacement interval. REINSTATE requires latest VOIDED and
explicit new valid interval (may equal original), nonblank reason. CORRECT with unchanged interval
and a new key rejects as no-effective-change, not an unrecorded successful correction receipt.
VOID→VOID and ACTIVE→REINSTATE also reject; exact prior-key retry is handled first.

Highest revision of ANY effect is current authority only AFTER complete chain certification in
section 7, never highest ACTIVE or fallback past bad history. Private append checks the complete
persisted chain as well as the new transition; normal append correctness alone is insufficient.
No wall-clock authority, Audit reconstruction or generic event-sourcing system. Corrupt earlier
history fails closed when certifying authority, even though arbitrary SQL remains unsupported.
Contiguity and every earlier intrinsic transition both matter.

## 6. Time semantics and civil-date boundaries

Public attendance API accepts aware datetimes only, preserves microseconds and normalizes to UTC;
aware offset/fold explicitly identifies an instant. Invalid/overflowing dates/offsets or naive data
produce field ValidationError before comparison. `start_at < end_at` uses UTC instants, not
wall-clock subtraction. NO elapsed-duration ceiling: valid 25h, >48h and longer completed intervals
are admitted subject to employment/overlap/calendar rules, not another numeric duration cap.
Cross-midnight/multiple sessions are valid; no shifts/breaks/daily cap.
Frozen Attendance timezone comes from locked Company on initial creation, not arbitrary client input.
Occupied dates are validated search facts, not independent interval authority. The transition-driven
helper below certifies civil-midnight geometry across the whole interval without iterating each day;
then start and end−1 microsecond local dates give the occupied inclusive range. Unsupported date-line
retreat/midnight ambiguity/gap geometry fails closed, not approximates intermediate dates. Ordinary
New York DST remains supported, including a 25h fall-back calendar day. Employment checks use the
certified frozen-zone dates. No fixed lookback/envelope length follows from the removed duration
bound; arithmetic overflow is an explicit boundary error.

HTTP datetime-local is a presentation adapter, not business rule authority. New ambiguous/nonexistent
input fails normal Django timezone validation. Corrections render each endpoint in Attendance's frozen
zone. Before generic ambiguous-time conversion, exact raw `%Y-%m-%dT%H:%M` equality with the trusted,
company-scoped persisted endpoint returns that exact original aware datetime. No hidden/query/client
original is trusted. A changed minute follows normal validation and starts at :00.000000. Test both
New York folds, spring gaps, sub-minute precision and changed time, following Inventory's pattern.

Leave day interpretation uses Leave's frozen timezone, not Attendance's or newly current Company zone.
Validate start_date<=end_date and employment containment with Date comparisons. Inclusive count is
`(end_date-start_date).days+1`, never elapsed-hour division; it has NO admission maximum.
Compute only start midnight and exclusive `end_date+1` midnight by both-fold UTC round-trip,
deduplicate equal instants and require one valid instant each. Overflow at date.max is an explicit
unrepresentable-exclusive-boundary error, not a span ceiling. Interior safety needs the following
exact transition algorithm, not endpoint-only guesswork or a loop per requested date.

HR-local framework-neutral rule analysis (future HR-1, not new Core infrastructure):

1. Resolve the zone from the same configured ZoneInfo TZPATH/available tzdata source. Read exact
   TZif bytes once; instantiate ZoneInfo.from_file from those bytes. Parse reviewed TZif v2/v3/v4
   explicit UTC transitions, pre-first-transition offset and POSIX footer recurring rules (time
   basis and signed/extended transition hours included); handle fixed-offset tails explicitly.
   No private ZoneInfo internals, guessed modern rules or coarse sampling.
2. Generate applicable offset transitions for the representable requested year range using annual
   footer rules plus explicit records and sufficient boundary halo. Work is proportional to actual
   transitions/years, not each requested date. The native Date/datetime domain is finite; no shorter
   duration/span admission ceiling is added.
3. For transition UTC t, old/new offsets give its local skipped/repeated wall interval. Arithmetic
   ceiling-to-midnight and interval intersection detects ANY midnight from start_date through
   end_date+1 in that gap/fold; reject if present. Validate strict increasing endpoint UTC order and
   no unsupported date-line/skipped-date geometry. Ordinary 02:00 DST transitions remain valid.
4. With exact covered rules and no invalid intervening midnight, full-day occupancy is
   `[B(start_date),B(end_date+1))`. Use that UTC interval for bidirectional conflicts and local dates
   for employment/leave overlap. UTC boundaries are verified derivatives, never separate facts.
5. Unverified TZif/footer/version/offset coverage, conversion parity mismatch or unsupported boundary
   returns UnsupportedCalendarBoundary, never guessed coverage or a shorter span cap. CPU/statement
   timeout returns ResourceBudgetExceeded with no effect, never claims no conflict.

Full-chain date validation first obtains selected-chain UTC min/max scalars, then compiles that
same zone's exact UTC offset segments and invalid-boundary intervals to finite selected-alias SQL
parameters. EVERY historical revision must satisfy admitted geometry and cached-date conversion:
exactly one segment covers each start/end-minus-one-microsecond instant; derive the local date from
the UTC value plus that verified integer offset, not PostgreSQL's separately installed named-zone
rules. UTC conversion only is fixed; no guessed cross-platform tzdata parity. Require complete
nonoverlapping segment coverage and overflow checks; parameter/work overflow fails closed. SQLite's
functional oracle uses exact integer microseconds/offsets, not float epoch arithmetic. A current-offset
database timezone catalog does not substitute for historical transitions.

Format reference: [TZif RFC 9636](https://www.rfc-editor.org/rfc/rfc9636.html);
data sources: [Python ZoneInfo](https://docs.python.org/3.13/library/zoneinfo.html).
HR-1 must prove parser/footer/SQL-offset equivalence/extreme-year handling. Focused probes below cover explicit-rule
fixture ranges, not complete POSIX-tail/parser implementation certification.

No attendance/leave rule compares unrelated server creation/update/audit clocks to prove order.
Expected revisions, locks and state transitions provide causality; company_local_today is used only
where employment date eligibility explicitly requires it. Timezone snapshots are historical
interpretation, not a second current Company configuration authority.

## 7. Bounded conflict and eligibility queries

Operational materialization budget: 1,000 interval/range candidates + one sentinel. There is NO
Attendance duration, Leave span or revision-count admission ceiling. A budget/statement timeout
returns explicit ResourceBudgetExceeded and rolls back, never a truncated success or "no overlap".
Statement budgets bound execution resource/lifetime, not the input's elapsed/calendar duration.
No generic indexing/maintenance framework, mutable interval projection or PostgreSQL exclusion extension.

### Effective interval overlap

Under locked Company/Employee and selected alias, for proposed [s,e):

1. Query Revision JOIN authoritative Attendance parent by parent ID, scoped on the PARENT's Company/
   Employee, with `r.start_at < e AND r.end_at > s`. NO lower start/lookback predicate. Include ALL
   effects and superseded rows, ordered start_at,id, LIMIT 1001 before current/effect filtering.
   Duplicated revision scope keys are optimization hints, never the inclusion authority.
2. If >1,000, resource error. Extract bounded distinct parent IDs; certify their COMPLETE chains
   below, then resolve newest of ALL effects through parent/ordinal index. No Python history load.
3. Validate locked parent identity and the certified latest facts. For correction exclude only the
   persisted validated target parent, never a caller's mutable FK. Any earlier chain error rejects.
4. If any certified latest ACTIVE interval has start<e and end>s, reject; VOID occupies no time.
   Every genuinely overlapping latest row is itself an interval candidate, irrespective of how
   long ago it began. An older row corrected elsewhere cannot become current. Adjacent end=start
   remains legal; Branch/date differences never permit overlap.
5. If parent locks are used, lock only this bounded parent set + target in UUID order; revisions are
   immutable and need no rewrite locks. Employee already serializes supported appends. Re-read latest
   after waits, revalidate references, then final authority. No whole-history FOR UPDATE.

This is a complete database-side range predicate with bounded materialization, not a promise that
an index visits only N physical pages. Use Attendance(company,employee,id), Revision(start_at,id),
Revision(end_at,id) and parent/ordinal indexes; EXPLAIN long earlier sessions/dense superseded history.
Operational timeout may fail closed, but no old lower-start bound or maximum duration can be restored.

Approval applies ONE complete interval query to the validated Leave UTC window; no per-date or
fixed-day chunk loop. Conflicts are half-open instants, not daily totals. Attendance's reverse query finds
APPROVED same-Employee Leave with cached validated UTC windows intersecting [s,e), max1,001; validate
each candidate's frozen dates/zone/window before deciding. Never filter conflicts to actor-visible Branch.

Leave submit/approve finds SUBMITTED/APPROVED same-Employee other requests where inclusive date labels
overlap OR frozen UTC windows intersect. Lock bounded candidates UUID ordered. Cap before materializing
results. The extra UTC predicate prevents double coverage from changed Company timezone even if
adjacent raw date labels differ. DRAFT/REJECTED/CANCELLED do not block; historical rows remain.

Employee date/end validation uses indexed outside-range derived local-date candidates plus newest
revision lookups, with the same sentinel/work cap, and indexed EXISTS/limited leave ranges. Verify
derived facts against UTC/zone on candidates. No all-history Python scan; dense unsuitable history
returns ResourceBudgetExceeded pending a separately reviewed query improvement. No temporal/entitlement
limit is inferred from materialization/statement budgets.

### Complete selected-chain certification — HR0-AUD-4

Every detail/current-effect read, record-key/revision retry, append, overlap/eligibility certification
must verify the entire relevant persisted Attendance chain before reporting authority or auditing.
Under held Company/Employee and bounded parent locks, return scalar database evidence per parent:

```sql
SELECT attendance_id, COUNT(*), COUNT(DISTINCT number), MIN(number), MAX(number)
FROM hr_attendancerevision
WHERE attendance_id IN (:bounded_validated_parent_ids)
GROUP BY attendance_id;
```

Require revision1 exists, min=1, all ordinals in the portable positive range, and
`count = count_distinct = max`. The DISTINCT proof also detects duplicate+gap corruption without
assuming uniqueness was never bypassed. Parent/ordinal unique constraint remains required and
duplicates must be rejected normally. `1,3,4` fails count=3/max=4 even though latest/predecessor match.

Contiguity alone is insufficient. A selected-chain SQL NOT EXISTS bad-row check LEFT JOINs EVERY
revision r to its same-parent predecessor p(number=r.number−1), plus authoritative Attendance and
Employee. Null-safe violation predicates (`IS DISTINCT FROM`, never NULL-skipping equality) cover:

- exact parent/Company/Employee identity, actor/request existence, allowed enums/ordinal ranges,
  expected_revision=number−1, positive ordered aware UTC interval, validated cached dates/frozen zone;
- revision1 RECORD/ACTIVE_INTERVAL, actor=recorded_by, request_key=record_request_key, expected=0;
- every later predecessor exists; CORRECT ACTIVE→ACTIVE with changed interval/nonblank reason;
  VOID ACTIVE→VOIDED with EXACT prior interval/dates; REINSTATE VOIDED→ACTIVE with explicit valid
  interval/nonblank reason; no later RECORD, no VOID→VOID or ACTIVE→REINSTATE;
- every earlier intrinsic date/interval/operation/reference fact, not only the latest. Zone geometry
  and SQL offset conversion use section6's exact rule basis. No renewed activity requirement on
  historical actors/Party/Branch; no wall-clock ordering checks.

This scans indexed SELECTED chains inside the database, returns aggregate/boolean/newest scalars,
and never materializes an Employee's full history. Query timeout produces an explicit resource
failure, not a chain-length admission ceiling. HR-1 must inspect plans and query bounds. Supported
SQLite uses equivalent correlated predecessor/aggregate expressions with null-safe comparisons;
PostgreSQL supplies native SQL oracles/concurrency proof. No generic event-sourcing framework.

Only a certified chain can supply newest-any-effect authority or accept the next revision. An
existing-key historical retry first certifies the COMPLETE current chain, then finds the immutable
matched prior event and labels current effect separately. Legitimate later corrections do not
invalidate old receipt equality; corrupt earlier/later evidence never gets a success Audit receipt.

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
-> bounded Attendance parents UUID order + immutable newest revision reads
-> bounded LeaveRequest rows UUID order
-> nonwaiting authority-relation admission for EVERY final-Core path (below)
-> final Core authority: actor / complete Roles / complete Permissions
-> operation-specific persistence + Core Audit -> outer commit
```

Create Employee has no Employee row yet: Company serialization and uniqueness reserve its identity;
take Department/Branch/Party references before final authority; discover User IDs without row locks.
Setup-only operation locks its
Department/Type after Company, uses indexed membership EXISTS, never locks Employee after setup.
Leave operations gather attendance candidates BEFORE locking Leave parent/candidates; correction
locks its Attendance parent before any Leave row. Company/Employee already serialize same-scope
writers; this fixed order also prevents future nested order inversion. References are ID/scalar
discoveries only until locked; persisted Company/parent IDs are authoritative and revalidated.

Department/Branch/Party/LeaveType use owner rows locked FOR UPDATE when eligibility matters.
Party ordinary writers do not use Company-first locks but their SQL updates conflict with HR's
Party row lock; re-read active PERSON after waiting. Branch supported saves start Company→Branch.
No HR reference write or owner-private helper import. The original sorted multi-User FOR SHARE
proposal was disproved and is withdrawn. Identity UserManager has no get_queryset/batch override;
User.save normalizes email only. Inherited update/bulk_update([B,A],batch_size=1), save/delete and
select_for_update paths impose no shared reader/writer order. Admin forms/save and Django last_login
updates use those ordinary Identity paths; the demo command creates Users, not a new lock protocol.
All relevant tracked production call sites and inherited paths were considered, not just explicit
deactivation functions. Access target-user lookups are plain reads; Core final locks actor itself.

Historical/unlinked User IDs and negative self-approval comparisons need no renewed activity/grants
or extra row locking. EVERY mutation, successful no-op/retry and read invoking locking Core final
authorization needs the admission below. Actor-only/actor-equals-new-User paths are not exceptions:
a Role-first writer followed by User B→A can deadlock Core's actor-A→Role guard without a second HR
User reference. Employee creation/relink and Leave submission also introduce FK locking points.
Existing unchanged User columns must not be needlessly rewritten. Ordinary require_permission-only
reads remain nonlocking and ungated; they cannot claim commit-stable final authority. Pre-gate
FOR UPDATE queries must lock owner rows only, with explicit of=('self',) if joins exist; never
implicitly lock a joined User/Role/Permission. H13 inspects executed SQL/FK effects, not helper names.

### HR0-AUD-1 alternatives and proposed writer-compatible admission

| Alternative | Evaluation |
| --- | --- |
| A: no additional User locks, or only KEY SHARE | Avoiding historical/unlinked locks is correct, but new distinct activity/reference is not protected by KEY SHARE against non-key is_active updates; FK/key locks can still interact with actor and key-changing/deleting batches. Not sufficient for stable new association |
| B: User SHARE barrier alone | SHARE excludes UPDATE's ROW EXCLUSIVE but permits select_for_update ROW SHARE; User-only barriers also miss mixed Role/Permission→User transactions. Core-final-first/User-gate-second can deadlock before reaching the gate. Rejected |
| B: complete authority relation gates before ALL final-Core paths, all NOWAIT | Proposed below; automatically conflicts with existing canonical writers regardless row order, no writer participation change. Global manual-v1 contention tradeoff; association-only gating was disproved by the actor-only mixed writer |
| C: Identity-owner common writer/reader protocol | Possible later finer-grained owner extension covering batches, prelocks, actor/reference and mixed authority order; requires separate authorization/ADR/runtime audit. Not a prerequisite secretly assumed by this candidate |

For EVERY HR final-Core path, including mutations/retries/no-ops and locking reads, after Company
and ALL relevant non-User domain/reference anchors, BEFORE any explicit/implicit
User/Role/Permission row lock, new User FK persistence or Core final call:

```sql
LOCK TABLE public.identity_user IN EXCLUSIVE MODE NOWAIT;
LOCK TABLE public.access_role IN EXCLUSIVE MODE NOWAIT;
LOCK TABLE public.access_permission IN EXCLUSIVE MODE NOWAIT;
```

Use verified installed owner table identity, selected-alias cursor and safe identifier quoting, not
default cursor or a redirected unqualified relation. Runtime table names are the pinned public
owner relations; unsupported identity/search-path mismatch fails closed. No source normalization.
All three gates are NOWAIT in fixed order. Any SQLSTATE 55P03 escapes the COMPLETE outer HR operation
and rolls it back, releasing earlier gates/Company/domain locks; translate outside that boundary to
retryable AuthorityBusy with no success/no-op receipt/audit. No inner-savepoint-only recovery,
partial success, fallback to row sorting/advisory locks or automatic unbounded retry.

EXCLUSIVE conflicts with ROW SHARE as well as ROW EXCLUSIVE; SHARE does not. Once all gates succeed,
no other transaction can acquire User/Role/Permission row-lock or DML relation intent, so unchanged
Core final cannot wait on a mixed authority writer. If a writer holds Role/Permission first, its
gate makes HR fail immediately instead of waiting while holding User. If HR wins, canonical writers
wait at relation admission before taking conflicting rows. Ordinary SELECT/ACCESS SHARE continues.
Lock semantics: [PostgreSQL 17 explicit locking](https://www.postgresql.org/docs/17/explicit-locking.html).

After admission, run every unchanged Core compound final guard, plain-read/revalidate new User
activity/Company eligibility, refresh locked domain facts without acquiring NEW blocking anchors,
then repeat final guards immediately before effects/audit/return. Gate is NOT authorization; no
new Core helper, privileged context, incomplete Role/Permission witness or duplicated RBAC policy.
Old/inactive provenance remains valid. PostgreSQL fixtures exercised non-superuser actor, selected
non-default alias and a NOSUPERUSER/NOBYPASSRLS execution role with ordinary DML grants. Lack of
required relation-lock privileges fails closed; production privilege certification is not claimed.

Entry/nesting is enforceable HR-local scope: public outer entry must begin without an unknown
surrounding atomic transaction; reject unknown/prelocked outer transaction BEFORE any blocking
Company/domain acquisition. Allow nested same-alias/Company/actor calls only inside an HR-owned
admitted outer operation whose complete reference/authority anchor union is predeclared/prelocked.
After gates, no new Company/domain/reference lock or Identity/authority write may be added by nested
callbacks/cross-owner calls. Scope must be private, alias/connection/outer-transaction bound, cleaned
on success/exception; not a generic coordinator or caller-supplied bypass flag. Same alias alone is
insufficient. If a caller needs broader composition, reject and require a separately reviewed lock
plan; do not silently impose an ordering restriction on existing Identity writers.

Cost/why proposed for bounded v1: three gates serialize global authority DML/locking readers in this
database, including unrelated login last_login, admin batches, Role/Permission maintenance and other
modules' final guards. Ordinary Attendance, Leave decisions/cancel, setup, exact retries and locking
reads ALL incur this cost; there is no false low-frequency association-only exemption. Concurrent
gated HR operations, even across Companies, have one winner and a 55P03/AuthorityBusy loser; a later
separate retry may succeed, but fairness/retry is not guaranteed. Ordinary SELECT/nonlocking reads
continue. The proposal favors complete correctness without changing accepted writers for manual
completed-session/admin v1, which excludes device/open-punch/self-service traffic. It is unsuitable
as an unreviewed high-throughput HR policy: owner acceptance/re-audit must assess this disclosed
tradeoff; no production-capacity claim. Finer-grained scaling is a separate owner extension.

Finish long-chain/timezone/result preparation before admission; no network/UI/callback/owner-write
work while gated. Proposed resource control: a 2s monotonic TOTAL admitted deadline starting before
the first gate; check before/after bounded pure work and every SQL/effect/return/outer commit,
set each SQL lock/statement timeout to its remaining budget, and bound idle-in-transaction separately.
Expiry rolls back the whole outer operation with ResourceBudgetExceeded. Per-statement/lock/idle
timeouts alone do NOT bound accumulated gate residence; a stalled application/process requires DB
session watchdog/termination controls, not a claim of a proven hard 2s server guarantee. HR-1 must
prove deadline, rollback-safe setting restoration and contention, including multiple short SQL calls.
This is an execution budget, not a business duration/date cap. No such runtime is implemented here.
SQLite has functional validation only, not these locking/concurrency guarantees.

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
window_start<window_end, supported decision, receipt all-or-none and from/result
relationships; decision_from_revision=submit_revision; cancel_from_revision equals retained decision
revision if decided, else submit revision if submitted, else the current pre-cancel draft revision;
current revision equals the latest retained event revision outside DRAFT. Require status-compatible
receipt presence (e.g. APPROVED requires submit+APPROVED decision;
REJECTED requires submit+REJECTED decision; SUBMITTED requires submit/no decision/cancel; DRAFT none;
CANCELLED requires cancel and may retain submit and approved decision but never rejected decision).
No DB CHECK claims to enforce timezone conversion, actor eligibility or cross-row conflicts.
NO maximum Leave span CHECK/service/UI rule; 365/366/367 and longer valid ranges are not special
admission categories. Unsupported exclusive-boundary arithmetic is a distinct explicit error.

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
| Attendance current list | Default last31 local dates; explicit ordered date range has no span ceiling; complete interval predicate/candidate sentinel before chain/latest; order effective start_at DESC, Attendance UUID; 50/page; VOID included only explicit filter |
| Attendance revisions | One scoped session, 50/page, number DESC,id; no full revision collection |
| Leave list | Default date window today−31..today+31; explicit ordered range has no span ceiling; status/Employee/Branch/search preserved; start_date DESC,id; 50/page; current effect + permitted receipt labels |
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
| Same active User association/create | Company→Employee/non-User refs→three gates→Core; first claims partial key, second uniqueness/resource conflict | One active association, losing revision/audit absent |
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
| Canonical B→A User batch vs A/B HR association, both winners | Company/non-User anchors then all three EXCLUSIVE NOWAIT gates before Core; writer-first HR resource abort, HR-first writer relation wait | No 40P01, no partial effect; current new-User/actor checks after contention |
| Single deactivation, old User unlink/relink, actor==target or distinct | All final-Core paths gated; no unnecessary old/historical row locks; actor-equal also admitted before Core actor lock | Deactivation-first new link denied, link-first history retained; unlink can be busy but does not demand old activity |
| Mixed Role/Permission prelock→User batch and nested calls | Three gates exclude preexisting ROW SHARE/ROW EXCLUSIVE on any authority table; unknown outer rejected before blocking; admitted nested reuses fixed anchors | Whole outer rollback on partial gate failure; no default access, writer-order assumption or silent nested expansion |
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
| H08 | Multiple same-day, valid 25h/>48h/longer intervals, cross-midnight/Branch and adjacency; long earlier session found, long correction/create and create/create both winners, VOID excluded/reinstate rechecked; exact retry after transfer/zone change with historical A/new B scope; candidate overflow ResourceBudgetExceeded, no temporal ceiling/lookback/current balance |
| H09 | Aware UTC/precision/both DST folds/gaps and trusted minute preservation; New York 25h fall-back day, exact midnight, long intervals/leap/frozen-zone changes/extreme dates; NO duration or Leave-span maximum in DB/service/UI; TZif explicit/footer/ZoneInfo/SQL-offset equivalence and unsupported midnight geometry; clock rollback not causal corruption |
| H10 | Valid chains 1;1,2;1,2,3;1,2,3,4 and VOID/reinstate; invalid 3;1,3;1,3,4;1,2,4;2,3,4, duplicate+gap, missing initial/wrong parent/malformed earlier/invalid latest reject; every-row transition/date checks, attempted append after corruption denied/no Audit, stale ordinal, historical retry after valid later correction; all direct/bulk attacks |
| H11 | Full-day Leave for 1/365/366/367 and longer valid ranges, leap/DST/zone changes/inclusive overlap/employment/extreme exclusive-boundary arithmetic; no 366 CHECK/service/widget/filter limit; exact receipts/DRAFT edits/lifecycle/active type vs historical recovery/self-approval, no entitlement/workflow |
| H12 | All section14 overlap/approval/cancel/record/correction winners; canonical User.bulk_update([B,A],is_active,batch_size=1) vs HR both orders, select_for_update prelocks, mixed Role/Permission→User batches, unlink/relink/deactivation, actor equal/distinct, concurrent readers and admitted nested/unknown-outer cases; no new 40P01 or partial effect/audit |
| H13 | Complete non-User anchors then User/Role/Permission EXCLUSIVE NOWAIT gates on EVERY final-Core path BEFORE explicit/implicit authority row locks/FK effects; inspect joined FOR UPDATE SQL; unchanged Core compound guard; partial-gate failure rolls back WHOLE outer transaction; actor/access/Role/Permission revoke after waits, SU namespace, non-default trap, two Companies, total deadline/settings cleanup and global contention; no unnecessary historical User locks |
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

### Preserved original proposal checks — 2026-10-14

The following checks describe original `5be60f19...`, not independent approval or future H01–H18
execution. Its internal no-conflict conclusion did not close the four later independent findings.

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

At that original checkpoint the local proposal was ready for independent audit, not accepted. The
subsequent supplied REVISE/B/4-P2 result and current proposed corrections are recorded above.

### Corrective investigation and proof record — 2026-10-15 Asia/Dhaka

Pre-edit: clean phase3a-hr-contract/HEAD `5be60f19e3bf654786abcd06b61149bc4a962ea9`, parent/local main/
origin-main/live main exact canonical base; remote HR branch absent. Only ADR0018/this plan may change.

Disposable infrastructure: existing postgres:17-alpine image, actual PostgreSQL **17.11**, isolated
task container `hr0-corrective-proof-pg-20261014-5be60f`, `--network none`, no ports, tmpfs PGDATA,
new synthetic `hr0_proof` database. Existing QA image ran ephemeral `--rm -i` Python **3.13.16** /
Django **5.2.17** via stdin, source bind mounted read-only/PYTHONDONTWRITEBYTECODE=1 and
`--network container:hr0-corrective-proof-pg-20261014-5be60f`. No test/probe script committed or
runtime edited. Existing source migrations bootstrapped this new DB unchanged. Fake Users/Company/
roles plus harmless hr0_effect/hr0_domain/chain-proof tables are not HR implementation/schema.

Exact canonical writer executed: `User.objects.bulk_update([user_b,user_a], ["is_active"],
batch_size=1)` under business_atomic_context. execute_wrapper observed first UPDATE of UUID B and
paused AFTER it executed; threading Events/Barriers and pg_stat_activity/pg_blocking_pids established
real blocking, no timing sleeps. Each worker closed its database connection in finally. Safety
timeouts were 8s statement/6s lock; no corrected probe hit a timeout or 40P01.

Original multi-row protocol: User B batch UPDATE held B; reader `SELECT ... A FOR SHARE`, then
`SELECT ... B FOR SHARE`; writer continued A. PostgreSQL **40P01 deadlock detected**, reader chosen
victim, writer completed. Reproduced twice. Sorting HR alone was conclusively insufficient.

| Corrective lock proof | Observed outcome (contract harness, NOT HR implementation) |
| --- | --- |
| P01 canonical B→A writer first | Three-gate reader failed 55P03 on User relation; whole operation rolled back; writer completed |
| P02 gate first / opposite order | pg_locks showed ExclusiveLock on all three relations; writer visibly waited at relation before first User row update; both completed after release |
| P03 single deactivation committed first | New linked B inactive -> actual PermissionDenied, no dummy linkage |
| P04 linkage first | B deactivation waited, then completed; valid association history retained after inactivity |
| P05 relink from inactive old B | New active C accepted; no renewed activity requirement on old B |
| P06 unlink vs old-B deactivation | All-path gate returned 55P03 while deactivation held the relation; separate unlink retry succeeded after release without old-User activity requirement |
| P07 actor deactivation during later domain wait | Initial permission passed; real domain lock wait; A deactivated; unchanged final Core denied after wait |
| P08 actor equals linked User | All-path gate preceded Core actor FOR SHARE; deactivation waited until valid effect committed |
| P09 actor distinct from linked User | Non-superuser A, active Company grant/Role and both hr.employee.manage/view checks succeeded through actual Core guards |
| P10 concurrent authorized locking readers | Different Companies: one admitted, one 55P03, separate post-release retry succeeded; no claim both locking reads are admitted concurrently |
| P11 declared fixed-anchor nested call | Same-alias nested savepoint/Core recheck completed, with complete anchors acquired before gates |
| P12 mixed canonical Role→User writer first | RoleQuerySet.update then User batch is an existing callable composition; reader's second gate failed 55P03 on Role, releasing earlier User gate; writer completed |
| P13 gate first / mixed writer opposite order | Role→User writer waited at relation; reader's unchanged Core final completed, then writer completed |
| P14 inherited User.select_for_update before UPDATE | ROW SHARE prelock caused EXCLUSIVE NOWAIT refusal (55P03), not a SHARE-mode upgrade cycle |
| P15 KEY SHARE rejected alternative | B.is_active update completed while KEY SHARE held; reader saw false—KEY SHARE does not stabilize activity |
| P16 unknown prelocked outer transaction | Before-blocking admission check rejected without issuing Company SQL while another worker actually held Company; no wait cycle |
| P17 failed gate inside nested savepoint | Propagated 55P03 rolled back WHOLE outer transaction, including dummy marker; remaining marker count0 |
| P18 execution-role/alias proof | NOSUPERUSER/NOBYPASSRLS hr0_app with ordinary DML grants, hr0_nondefault alias and default-cursor trap: three gates/actual Core guards/FK effect completed, no default query |
| P19 actor-only mixed writer first | Canonical Role.update then User B→A batch; all-path reader failed 55P03 on Role, writer completed, zero dummy effects |
| P20 actor-only gate first | Canonical mixed writer visibly waited before Role row acquisition; actual Core completed and writer then completed |
| P21 concurrent locking-reader retry | Different Companies: first gate winner; second 55P03/no authority receipt; separate post-release retry succeeded |
| P22 ordinary authorized nonlocking read | Actual require_permission read in another Company succeeded while first reader held all gates; ordinary SELECT stays available |

Further alternatives tested: User-only EXCLUSIVE after Core worked for pure batch/row-prelock fixtures,
but mixed Role/Permission prelocks can deadlock BEFORE that gate. A first association-only triple-gate
draft was also rejected: actual actor-only Core actor-A FOR SHARE→Role wait versus canonical
Role.update→User.bulk_update([B,A],batch_size=1) reproduced another **40P01** with real wait detection.
Therefore no actor-only/equal/no-op exemption survives. P01–P15 were rerun under all-path gating:
unlink and concurrent locking-reader resource outcomes above replace the narrower exploratory
success claims. P19–P22 prove the residual cycle's correction and disclosed contention. Initial
ungated compatible-reader success remains exploratory history, not the final protocol's oracle.
Two extra mixed-order exploratory runs passed; do not inflate any probes into independent audit.
No Identity/Core runtime extension is required by this proposed bounded protocol. No universal
arbitrary-outer-transaction, fairness, production load or future HR implementation proof is claimed.

Transient harness failures preserved: first exploratory run had an unsynchronized worker-PID lookup
KeyError after the old deadlock/direct-writer proofs; fixed Event-before-read coordination and reran
successfully. First P18 attempt created a synthetic NOLOGIN role and failed connection; enabled LOGIN
on that task-created role only, then the alias/trap proof passed. Neither changed source or justified
ignoring a failing candidate test.

Other actual focused contract probes:

- PostgreSQL scalar chain aggregate/every-row predecessor query accepted `1`, `1,2`, `1,2,3`,
  `1,2,3,4`; rejected `3`, `1,3`, `1,3,4`, `1,2,4`, `2,3,4`, wrong earlier scope, malformed earlier
  VOID and invalid latest interval. Valid RECORD→VOID→REINSTATE certified. Unique ordinal rejected
  duplicate with 23505; deliberately weakened synthetic uniqueness still rejected duplicate+gap
  `1,2,2,4` via COUNT(DISTINCT). All fixture schema/corruption is confined to the disposable DB.
- SQL interval `[0,61h)` versus `[60h,62h)` was included by the complete predicate and omitted by
  the old lower-start lookback; adjacent `[61h,62h)` did not overlap. No duration admission ceiling.
- In-memory same-file TZif explicit-record/ZoneInfo probes: one UTC day; New York 365,366,367,1461
  inclusive dates; and 2026-11-01 New York one calendar day occupying **25 UTC hours**, all valid.
  Transition scan examined 236 rule records, not every requested date. Interior Apia skipped-date
  boundary rejected, date.max exclusive-end arithmetic failed explicitly, both New York fold
  instants retained UTC/fold identity. General POSIX-tail/parser/SQL-offset/extreme-year certification
  is **NOT PROVEN here** and remains an explicit HR-1 acceptance obligation; no guessed coverage.

Corrective documentation/quality checks on this two-file working candidate:

| Exact check / environment | Actual result |
| --- | --- |
| `python manage.py check` | PASS, zero issues |
| `python manage.py makemigrations --check --dry-run` | PASS, no changes detected |
| `ruff check . --no-cache` | PASS, no source writes |
| `pytest tests/test_database_architecture.py tests/test_modules.py tests/test_database_foundation.py -q -p no:cacheprovider` | **248 passed in 15.11s**; existing architecture/registry/alias/bootstrap guards, NOT HR runtime tests |
| Read-only PowerShell documentation validator | PASS: 49 relative file links, one heading anchor, balanced fences/final newlines/no trailing whitespace; H01–H18 exactly once in the matrix |
| `git diff --check` / authorized path comparison | PASS; exactly ADR0018/this plan; no protected runtime/schema/migration/ADR0017 change |
| Live `git ls-remote origin refs/heads/main refs/heads/phase3a-hr-contract` | main exact `6453c8f3202335aabe8a872046fea2e607dac858`; HR branch absent |
| Local heads/tags comparison with captured pre-proposal refs | All 47 existing refs unchanged; only the local HR proposal branch added |

Checks used existing `ui-gate1-qa-web:latest`, ephemeral `docker run --rm -i --network none`,
read-only source bind, PYTHONDONTWRITEBYTECODE=1, config.settings.test/in-memory SQLite and all
three existing financial-integration install flags. No full application suite/browser/hosted HR CI
was required or claimed. Contract probes and internal consistency review are implementation-task
evidence, not fresh independent re-audit or production load certification.

Cleanup verified the exact task container ID
`ef3b079e79bef40a37cc46a889333085b6fd1e1599f70ad8fe725552042e45b9`, network none, no published
ports/persistent mounts, tmpfs PGDATA and zero remaining worker DB sessions. Removed ONLY
`hr0-corrective-proof-pg-20261014-5be60f` with docker rm -f; subsequent filtered inventory was empty.
Its disposable synthetic database/roles/fixtures disappeared with tmpfs and are not recoverable.
All preexisting containers, demos/source databases and source files were left untouched.

All H01–H18 remain future implementation obligations. Original findings are independently unresolved
until re-audit; current status is corrective candidate, not accepted/closed or HR-1 authority.
