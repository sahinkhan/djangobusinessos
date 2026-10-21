# Phase 3A — HR Foundation

Status: **FORMAL HR-0 CONTRACT ACCEPTANCE COMPLETE; CANONICAL ADOPTION PENDING**.
ADR 0018: **ACCEPTED FOR CANONICAL ADOPTION**. HR-1 NOT AUTHORIZED.
Independent final contract audit: **PASS — Readiness A**; all five findings RESOLVED.

Date: 2026-10-14. Formal acceptance: 2026-10-15 Asia/Dhaka. Branch: `phase3a-hr-contract`.
Canonical base: `6453c8f3202335aabe8a872046fea2e607dac858`.
Technical ADR: [ADR 0018](../../decisions/0018-hr-foundation-technical-contract.md).
Accepted umbrella: [ADR 0017](../../decisions/0017-phase3-people-digital-commerce-boundaries.md)
and [Phase 3 plan](PHASE_3_PEOPLE_DIGITAL_COMMERCE.md).

## 1. Authority, chronology and delivery boundary

The umbrella completion rule is fulfilled at the canonical base: acceptance CI #134 / run
`38570976500` and main CI #135 / run `38576825532` SUCCESS, 3,015 PostgreSQL tests each.
Those inherited results do not execute HR. OD-1–OD-12 remain resolved/frozen; only OD-1–OD-6's
remaining HR technical details are now accepted here. The original internal review's no-conflict
conclusion was subsequently corrected by the supplied independent Readiness B audit below.
Internal review was not independent approval.

Original proposal `5be60f19e3bf654786abcd06b61149bc4a962ea9` is preserved above that canonical parent.
First corrective commit `3ab7aaea019833b9a0f5123f51018f4d516db366` remains preserved.
Finer-grained correction `c99ea988ff7e1a74fed3ed4cb1232cd7db37957a` records owner Option B's
rejection of global EXCLUSIVE authority gates and supplied Result A HR-only protocol. Its final
independent audit now passed with Readiness A, zero P0–P3 and all five findings resolved.
Current authorization permits exactly one docs-only formal acceptance commit above that correction,
normal branch publication/exact-head CI, then direct normal fast-forward main adoption only after
success/unchanged-main checks, separate main CI and only then local main synchronization.
No runtime exists for these six models/services/permissions. No Core/Identity/Access changes,
PR, tag, force-push, rebase, squash, merge commit, amendment, HR-1, ECOM-0/1, Phase 4 or deployment.
Future HR-1 requires completed canonical adoption and separate implementation authorization.
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
P0 0 / P1 0 / P2 4 / P3 0. These historical findings are not erased; the subsequent supplied
independent re-audit reports all four RESOLVED at technical-contract level after the first correction:

| Finding | Original defect | Resolution / review boundary |
| --- | --- | --- |
| HR0-AUD-1 — P2 | HR shared User locks deadlock inherited B→A batch writers; Core actor guard also matters | Original defect independently reported RESOLVED; preserve writer-compatible complete prelock direction, not HR-only blocking row ordering |
| HR0-AUD-2 — P2 | Unsupported 24-hour Attendance ceiling and dependent lookback | RESOLVED: no duration ceiling; complete interval predicate; long-interval/resource-error oracles unchanged |
| HR0-AUD-3 — P2 | Unsupported 366-date Leave ceiling/per-date validation | RESOLVED: no span ceiling; exact transition-driven civil-boundary certification and long-range oracles unchanged |
| HR0-AUD-4 — P2 | Latest/immediate predecessor misses older gaps/corruption | RESOLVED: complete selected-chain aggregate and every-row checks before authority/retry unchanged |

The same re-audit raised NEW **HR0-REAUD-1 — P2**, placing formal acceptance on HOLD because the
EXCLUSIVE replacement gates imposed new database-wide operational contention without owner approval.
Owner Option B rejected that tradeoff. The supplied final independent review of `c99ea988...`
subsequently resolved HR0-REAUD-1; the original HOLD is retained as history, not current status.
Formal contract acceptance is now complete; no HR implementation acceptance PASS is claimed.

### Chronology and present authority

| Checkpoint | Exact evidence / disposition |
| --- | --- |
| 1. Original HR-0 proposal | `5be60f19e3bf654786abcd06b61149bc4a962ea9`, above canonical umbrella `6453c8f...` |
| 2. Initial independent audit | REVISE / Readiness B / four P2 HR0-AUD-1–4 |
| 3. First corrective candidate | `3ab7aaea019833b9a0f5123f51018f4d516db366`; complete history/no temporal caps, but new global EXCLUSIVE authority gates |
| 4. Independent re-audit | Supplied result: original four RESOLVED at technical-contract level; not implementation acceptance |
| 5. New global-contention finding | HR0-REAUD-1 — P2; formal acceptance HOLD; unrelated Company work/login/writers could contend |
| 6. Owner Option B | Explicitly REJECT global EXCLUSIVE authority contention; no owner runtime change authorized |
| 7. Read-only feasibility investigation | Supplied Result **A — HR-ONLY FINER-GRAINED LOCKING FEASIBLE; Core/Identity change NO**; complete row NOWAIT plus relation NOWAIT, unchanged Core; synthetic evidence only |
| 8. Finer-grained corrective candidate | `c99ea988ff7e1a74fed3ed4cb1232cd7db37957a`; section8 replaces global gates, section14 preserves exact T01–T26 future oracles |
| 9. Corrective-stage next gate, historical | Fresh independent audit was PENDING; ADR0018 was PROPOSED and HR-1 unauthorized at that checkpoint |
| 10. Final independent re-audit | Owner-supplied FINAL PASS / Readiness A / zero P0–P3; HR0-REAUD-1 RESOLVED and original four resolutions retained |
| 11. Present formal acceptance | One docs-only acceptance commit; exact reviewed contract frozen; canonical adoption PENDING under the completion rule below; HR-1 NOT AUTHORIZED |

Sections 2–17 retain the reviewed technical requirements verbatim. Their retained drafting labels
such as "proposed" identify the future implementation design, not unresolved choices after this
formal contract acceptance. H01–H18 and T01–T26 still require actual HR-1 evidence.

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
no blocking UUID-sorted reader/writer ordering assumption is retained.

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

### Entry, alias and non-User anchors

Resolve current_database_alias at entry and use unchanged business_atomic_context (or an admitted
nested same-alias business transaction). PostgreSQL READ COMMITTED is the locking-proof basis;
verify it, do not silently override isolation. SQLite has functional validation only, not this proof.

An HR-local entry adapter checks the selected connection's outer-transaction state BEFORE entering
its own atomic block or issuing blocking domain SQL. A check inside an already-entered
@business_atomic body cannot distinguish the caller's unknown transaction. Reject unknown/prelocked
outer transactions; do not change Core transaction helpers. Admitted nested work must have the same
alias, connection, outer transaction, Company, actor and predeclared complete domain/authority union.
Private HR admission state is transaction-bound and cleared on success/exception, never a
caller-supplied bypass flag or a new shared coordination/authorization framework.

Order (omit irrelevant classes, never reverse):

```text
entry/nesting admission -> selected-alias business transaction, READ COMMITTED
-> active Company FOR UPDATE -> initial BusinessContext + compound permission recheck
-> Employee (existing target; complete multiple-ID set sorted if needed)
-> Department rows UUID order
-> Branch rows UUID order (context/current/new/frozen anchors where relevant)
-> Party rows UUID order
-> LeaveType rows UUID order
-> bounded Attendance parents UUID order + immutable revision evidence
-> bounded LeaveRequest rows UUID order
-> authoritative state/retry discovery + complete operation-specific User IDs
-> User / Role / Permission ROW SHARE NOWAIT relation admission
-> complete User union FOR SHARE NOWAIT -> stabilized actor/activity/superuser re-read
-> non-SU: ALL assigned same-company Roles FOR SHARE NOWAIT
   -> ALL reachable Permissions FOR SHARE NOWAIT
   SU: existing Permission namespace SHARE NOWAIT -> ALL Permissions FOR SHARE NOWAIT
-> stabilized domain/scope/reference revalidation, no new blocking anchors
-> unchanged complete compound Core final guards
-> precise persistence + Core Audit OR successful historical retry/no-op return
-> outer commit
```

Create Employee reserves identity under Company serialization/uniqueness; Department/Branch/Party
are the non-User references, User discovery is plain UUID projection. Setup locks its Department/
Type after Company and checks membership EXISTS without locking Employee afterward. Leave gathers
Attendance candidates before Leave parent/candidates; Attendance correction locks its parent before
Leave rows. Complete parent/reference unions must be discovered/prelocked before authority admission.
Do not issue pre-admission writes that acquire User FK locks.

Party ordinary writers need not be Company-first: HR's Party row lock stabilizes current PERSON/
activity and is re-read after a wait. Branch supported saves lock Company then Branch. Lock only
explicit owner rows in joined domain queries: use select_for_update(of=("self", ...)) or separate
queries/plain projections. select_related(User) plus unrestricted FOR UPDATE is forbidden before
authority admission. Inspect actual ORM SQL/FK lock behavior, not just helper ordering.

### Why complete fail-fast prelocking, not a writer-order assumption

Identity UserManager inherits unordered update/bulk_update/save/delete/select_for_update paths;
User.save normalizes email only. Canonical bulk_update([B,A],["is_active"],batch_size=1), admin
saves and Django last_login updates remain unchanged. Role/Permission writers also retain their
own supported order; Permission update/upsert acquires ROW EXCLUSIVE write intent. Native Core final
locks actor, ALL assigned same-company Roles and ALL reachable Permissions (including inactive),
or the existing superuser Permission namespace plus all rows. Actor-only operations need the same
complete prelock: User-only NOWAIT followed by blocking Core Role acquisition can still deadlock
a mixed Role-to-User writer.

| Considered approach | Current disposition |
| --- | --- |
| Blocking UUID-sorted HR multi-User rows | Superseded: cannot order unchanged Identity batches; original 40P01 retained |
| No locks / KEY SHARE / optimistic initial activity | Insufficient: non-key is_active can change; KEY SHARE does not stabilize activity |
| User-only row NOWAIT followed by uncovered Core authority | Insufficient: mixed Role/Permission-to-User cycles; later Core locks are not all covered |
| First correction's whole-table EXCLUSIVE gates | Owner REJECTED for HR0-REAUD-1 global contention; historical proof only, NEVER fallback |
| Complete ROW SHARE relation NOWAIT + complete FOR SHARE row NOWAIT | Present HR-only proposed correction, supported by supplied Result A investigation; no owner runtime change |
| Shared Identity/Core writer protocol | Not implemented/assumed/required here; any future owner extension requires separate authorization |

No SKIP LOCKED, partial witness, weaker activity semantics, advisory lock used only by HR,
deadlock-retry-only solution, global writer gate under another name or disabled final guard.

### Verified relation admission before authority row prelocks

On the canonical public-schema deployment, use the selected-alias cursor:

```sql
LOCK TABLE public.identity_user IN ROW SHARE MODE NOWAIT;
LOCK TABLE public.access_role IN ROW SHARE MODE NOWAIT;
LOCK TABLE public.access_permission IN ROW SHARE MODE NOWAIT;
```

Fixed order is User, Role, Permission. Resolve installed owner metadata, verify schema-qualified
identity/OID and ordinary relation kind against the pinned canonical relations, safely quote schema
and relation SEPARATELY, and parameterize UUIDs. Never trust submitted identifiers or quote
"public.identity_user" as one identifier. Missing/unexpected relation or effective search-path
resolution to a different OID fails closed. After admission, reverify the same identities/resolution;
held relation locks protect against incompatible replacement DDL. Native Core/ORM uses unqualified
names, so it must resolve to the same protected relations. No search-path/source normalization.

Pinned expectations are schema/name/kind, not numeric OIDs copied across databases. Resolve and
cross-check each selected alias's own catalog OIDs; never derive approved names/kinds from drift.

Row NOWAIT does NOT make the SELECT's implicit relation lock nonwaiting. PostgreSQL FOR SHARE
NOWAIT and ORM select_for_update(nowait=True) can wait for ROW SHARE against maintenance EXCLUSIVE/
ACCESS EXCLUSIVE. Explicit relation NOWAIT closes that acquisition gap. ROW SHARE is compatible
with ordinary ROW EXCLUSIVE DML and other ROW SHARE readers; it is NOT table-wide exclusive writer
serialization. Preliminary metadata/permission/domain SELECTs before admission can still wait on
implicit ACCESS SHARE against maintenance ACCESS EXCLUSIVE: apply bounded lock/statement resource
controls from entry and fail closed. Do not claim the whole operation is nonblocking.
Reference: [PostgreSQL 17 explicit locking](https://www.postgresql.org/docs/17/explicit-locking.html).

### Complete User, Role and Permission sets

1. From locked authoritative domain/retry facts derive distinct validated User UUIDs. ALWAYS include
   context.actor_id, plus actual new/relinked association targets, genuinely required stable-current
   User facts, new persisted User FK targets and declared nested work. Table below is exhaustive.
2. Lock that complete set with parameterized selected-alias SQL, before native final guards:

```sql
SELECT id
FROM public.identity_user
WHERE id IN (:validated_distinct_user_ids)
ORDER BY id
FOR SHARE NOWAIT;
```

   Require exact ID coverage, not merely a nonempty result/count of available rows. Missing actor/
   reference fails explicitly, never successful partial prelocking. Re-read current actor activity
   and is_superuser UNDER protection before choosing authority coverage. Validate active/current
   Company eligibility only for a genuinely new Employee association/current-eligibility projection.
   A new historical beneficiary snapshot protects existence/identity even when inactive; it does
   not introduce a current activity/grant requirement.
3. Non-superuser: enumerate ALL current UserRoleAssignment.role_id where BOTH assignment Company
   and Role Company equal context.company_id, with NO active filter. UUID-sort/deduplicate and lock
   EVERY Role FOR SHARE NOWAIT; require exact coverage. Then enumerate ALL Permissions reachable
   through those Roles, including inactive rows; lock the complete set FOR SHARE NOWAIT and require
   exact coverage. Do not use only requested codes, active rows or a successful grant witness.
   No Roles/Permissions are inferred from linked/beneficiary Users.
4. The held active Company mutex stabilizes supported Company-first Access grant/assignment/
   RolePermission membership writers (ADR0009). Role/Permission activity/deletion is protected by
   the complete row prelocks. Re-read complete membership/sets under locks and require equality
   before final guards; an uncovered/missing anchor is an evidence/admission failure, NOT a reason
   to append another lock set. This is not a guarantee for raw SQL or unsupported direct grant
   mutations bypassing accepted Access services.
5. Superuser: after protected actor state, BEFORE namespace enumeration/native final, acquire:

```sql
LOCK TABLE public.access_permission IN SHARE MODE NOWAIT;
```

   Then enumerate EVERY current Permission, inactive included, and prelock ALL FOR SHARE NOWAIT.
   Exact coverage is mandatory. This preserves Core's EXISTING namespace protection, not a new
   HR-only EXCLUSIVE gate. Core's later ordinary SHARE request is already covered. Superuser still
   requires active registered codes/current Company and obeys domain/self-approval rules.
6. Revalidate protected scope/activity/domain facts, then invoke unchanged require_final_permission
   for EVERY declared compound code in deterministic code order immediately before effects/Audit/
   successful return. Native Core's actor/Role/Permission rows and any superuser namespace request
   must be a compatible SUBSET of held locks. HR-1 SQL-capture tests must prove this, including
   inactive authority rows, repeated compound guards and nested calls. No Core private helper import,
   copied grant policy, actor substitution, cache or new shared final-authorization API.

### Public-operation authority coverage

All rows below use the SAME complete non-SU/SU authority procedure above; compound codes are section10
verbatim. A = current actor, including every new Audit actor. N = actual new non-null Employee User
link. B = locked Employee.user captured by a NEW submit. No other User's Roles grant HR authority.

| Public operation / declared compound codes | User union and exact FK/current-fact treatment |
| --- | --- |
| department_page/detail — DV | A only |
| create/update_department — DM+DV | A only; new Audit.actor=A |
| leave_type_page/detail/choices — LV | A only |
| create/update_leave_type — LM+LV | A only |
| employee_page/detail; PERSON choices — EV | A only; existing association UUID is not a current-activity certification |
| User association choices — EM+EV | A plus EVERY bounded returned User whose current activity/Company eligibility is certified; include before materialization/return |
| create_employee — EM+EV; DV if Department used | A plus N if non-null; new Employee.user=N; require active/Company-eligible N |
| update_employee — EM+EV; DV if Department read/assigned | A plus N only for actual new/relinked non-null User; omitted/unchanged same UUID/clearing old link adds none |
| transfer_employee_branch / end_employee — EM+EV | A only; do not rewrite unchanged Employee.user |
| attendance_page/detail/revision_page — AV+EV | A only; historical recorder/actors remain intrinsic provenance, not reactivated |
| record_attendance — AR+AV+EV | A only; new Attendance.recorded_by and Revision.actor=A; existing-key retry adds no historical actors |
| revise_attendance — AC+AV+EV | A only; new Revision.actor=A; earlier actors unchanged |
| leave_page/detail — LV+EV | A only |
| create_leave — LR+LV+EV | A only; requester=A |
| update_leave — LR+LV+EV | A only; requester/snapshots unchanged |
| submit_leave, NEW effect — LR+LV+EV | A plus non-null B for new beneficiary_user_at_submission FK; existence/identity, NOT new B activity/grant eligibility |
| submit_leave, matching historical retry — LR+LV+EV | A only; stored B is not newly persisted or replaced by current Employee.user |
| decide_leave — LA+LV+EV | A only; new decided_by=A; requester/current/frozen beneficiary are negative self-comparison IDs only |
| cancel_leave — LC+LV+EV, also LA if originally APPROVED | A only; new cancelled_by=A; exact retry preserves original compound requirement after cancellation |

The actor is not assumed equal to a link. Removed old links, unchanged historical provenance and IDs
used only for negative self-approval comparisons are not extra activity anchors. If another actual
operation-specific current fact or new FK genuinely requires a User, declare it BEFORE admission
and protect it; do not silently expand the table or add a new eligibility rule. Use precise validated
update_fields/private column sets so immutable historical FKs are not needlessly rewritten and do
not create uncovered key-lock acquisition later. Successful no-ops/retries still prelock current A.

EVERY listed public selector materializes under this complete final-Core protocol, including action
form choices; there is no actor-only/public-read exemption. Nonlocking initial checks/internal scalar
discovery helpers do not return an externally certified DTO or replace public final authorization.
Optional related sections/codes and all Users genuinely required by declared nested work belong to
the predeclared union, not dynamic post-admission discovery.

### Failure, nesting, historical receipts and resource controls

Any relation/row/namespace NOWAIT SQLSTATE55P03 propagates through COMPLETE outer-operation rollback.
Release Company/domain/partial-authority locks; no partial authoritative effect, success Audit,
idempotency receipt or successful retry/no-op return. Subsequent SQL in an aborted PostgreSQL
transaction can fail25P02; do not continue. An inner savepoint can mechanically clear a database
error, but HR MUST NOT swallow it and commit outer work. Translate outside the rolled-back boundary
to explicit retryable AuthorityBusy. A fresh request independently revalidates all state/permissions;
no automatic unbounded retry. Missing/corrupt evidence, authorization denial and resource exhaustion
are distinct fail-closed errors, not all AuthorityBusy. Observability records error category,
operation/alias and non-sensitive counts; never creates a false success Audit/receipt or logs PII.

Admitted nested calls reuse the already declared/prelocked complete set on the exact same alias,
connection, outer transaction, Company and actor. Reject expansion/unknown scope BEFORE new SQL;
no earlier domain lock, new authority anchor, Identity/Access write, callback or cross-owner operation
may be added after admission. Do not change global helpers or impose a writer-order rule on owners.

For matching historical retries first discover/validate canonical retained receipt under proper
Company/domain locks, then prelock CURRENT actor authority and run the original required compound
Core guards. Return original effect/receipt separately from current validated owner state; never
reapply, duplicate Audit, replace snapshots from new configuration or certify old receipt as current.
A revoked actor cannot recover a receipt. Existing historical FK identity/intrinsic validity remains
required, but previous actor/beneficiary activity is not renewed.

Proposed execution resources, not product/admission policy: at most 1,000 distinct Users, 1,000 Roles
and 1,000 Permissions per admitted operation (including nested union), aggregate maximum3,000.
Use SQL DISTINCT BEFORE LIMIT1001 for Role/Permission ID discovery, and deduplicate the complete
validated operation User union before its sentinel check. Discover each set with one overflow
sentinel before materializing/locking; never deduplicate a truncated prefix and call it complete. No truncated
set may authorize; overflow returns ResourceBudgetExceeded with whole rollback, not denial or a
maximum Attendance duration/Leave span. Query/parameter exhaustion also fails closed, no fallback.

Retain a proposed 2s monotonic admitted-work budget from before first relation admission, checked
before/after every discovery/lock/SQL/bounded pure phase/effect/return/outer commit; each SQL timeout
uses remaining budget, with separately bounded pre-admission waits and idle transactions. Complete
SQL iteration of many small steps cannot silently reset this total budget. Scope/restore settings
safely on success/rollback. This is cooperative execution control, NOT a hard two-second server or
end-to-end wall-clock guarantee; stalled process/session termination is an operational concern.
No network/UI/long-calendar/chain preparation under authority locks. No production latency claim.

### Remaining contention and bounded guarantee

ROW SHARE admits ordinary DML table intents, and FOR SHARE readers are compatible even on shared
User/Role/Permission rows. Disjoint Companies/Users must progress concurrently; shared read-only
Permission identities are not a reason for AuthorityBusy. HR-first blocks an actual conflicting
same-row writer until commit; writer-first causes safe NOWAIT refusal/rollback. Remaining contention:
same User writers (including that User's last_login), shared Role/Permission modifications, the
existing Company mutex, maintenance and existing Core superuser Permission namespace SHARE.
There is NO new table-wide EXCLUSIVE serialization or globally conflicting ordinary-DML gate.
Role SHARE/SHARE compatibility is a lock-primitive property, not a claim that same-Company public
operations bypass their Company mutex; a Company-owned Role is not cross-Company authority.

Fairness/starvation freedom, production throughput and universal deadlock freedom for arbitrary
transactions are NOT PROVEN. The claim is limited to the tested supported writer/admitted-nesting
surface with complete anchors and no new blocking locks after final authorization. T01–T26 are
mandatory future HR-1 implementation oracles, not inherited synthetic PASS.

Supported unique-collision recovery remains unchanged: positively identify an HR unique constraint
inside a same-alias savepoint, roll it back, re-read locked canonical evidence and equality, then
reauthorize before recovery. Unclassified IntegrityError propagates/rolls back. Audit/validation/crash
before commit leaves no effect; response loss after commit recovers only the specific receipt/lookup.
No independent inner commit or generic collision-to-success conversion.

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
rows/related projections, section8 relation/complete authority prelocks, then unchanged final current
guard immediately before return after any wait. User-choice certified UUIDs belong to the predeclared
User union; historical IDs alone do not create new activity requirements. No lazy
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
| Same active User association/create | Company→Employee/non-User refs→ROW SHARE relation admission→complete row prelocks→Core; first claims partial key, second uniqueness/resource conflict | One active association, losing revision/audit absent |
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
| Canonical B→A User batch vs A/B HR association, both winners | Company/non-User anchors→ROW SHARE NOWAIT relation admission→complete User/Role/Permission FOR SHARE NOWAIT; writer-first HR row-busy rollback, HR-first conflicting writer ROW wait | No new 40P01, no partial effect; no table-wide writer barrier |
| Single deactivation, old User unlink/relink, actor==target or distinct | Actor always prelocked; actual new User/FK union complete; no removed-old/historical activity lock or joined implicit lock | Deactivation-first new link denied, link-first history retained; unrelated old-link writer does not force table-busy unlink |
| Mixed Role/Permission prelock→User batch and nested calls | Relation admission compatible with ordinary DML; ANY relevant authority row conflict refuses NOWAIT before native Core; unknown outer rejected, admitted nested set fixed | Whole outer rollback on partial row/namespace failure; no partial witness/default access or owner-order assumption |
| Two Companies / disjoint or shared read-only authority | Compatible relation/row SHARE readers coexist, including shared User/Permission rows; disjoint DML need not wait | Both progress without new whole-table EXCLUSIVE admission; same-row writers and existing SU namespace contention remain |
| Employment date correction vs approved leave/attendance | Company→Employee then bounded facts; prior valid effect cannot be moved outside eligibility by stale edit | No silent cancellation/void; date edit audit only if valid |

Add read-path revocation before materialization/after Company or reference wait; delayed selector
results must not escape current view guards. Test Company/Branch switch HTTP matrix for all mutation
families, not just create. Two Companies sharing actor/Permission/User must preserve global authority
order and nested audit rollback. No mutable timestamp as race winner evidence.

### T01–T26 — exact investigation IDs, future HR-1 PostgreSQL requirements

ALL rows are **REQUIRED — NOT EXECUTED AS HR-1**. The supplied investigation's synthetic successes
are not inherited HR runtime PASS. Use real wait detection/Events/Barriers, bounded safety timeouts,
fresh synthetic data and finally-closed worker connections; SQLite explicitly skips lock assertions.
For every row record actual locks, blockers, SQLSTATE, outer rollback, absence of stale effects/
Audit/partial receipts and unrelated-Company progress. Test both winner orders where applicable.

| ID | Frozen investigation case | Required future implementation oracle |
| --- | --- | --- |
| T01 | Original B→A writer / A→B reader | Isolated negative control reproduces old blocking 40P01; current HR never uses that protocol |
| T02 | Corrected HR-first winner | Complete compatible prelocks; relevant User writer visibly waits at ROW lock, not a new table writer gate; HR commits then writer completes |
| T03 | Corrected writer-first winner | Actual User.bulk_update([B,A],is_active,batch_size=1) causes55P03 at relevant row; whole HR rollback; fresh retry rechecks activity |
| T04 | Actor equals Employee link | Deduplicated actor/link once, exact coverage, current guard and FK effects safe |
| T05 | Actor differs from link | Complete A+new-link/FK union; both activity/reference rules, no authority from beneficiary |
| T06 | Relink versus deactivation | New target protected; inactive removed old User does not block unlink/relink by eligibility; new inactive link denies, later history retained |
| T07 | Mixed Role→User writer | Negative User-only control may deadlock; complete Role-inclusive NOWAIT refuses safely; reverse order writer waits on held relevant row |
| T08 | Permission mutation | Include Permission.update/update_or_create→User batch, retirement and both orders; relevant conflict fail-fast, unrelated writes compatible |
| T09 | Company-access revocation | Company mutex determines winner; revocation-first denies after wait, HR-first valid effect then revoke; no receipt recovery on stale authority |
| T10 | Role revocation | Supported assignment/RolePermission revoke and Role activity change; complete current membership after Company wait, inactive rows covered |
| T11 | Actor deactivation after domain wait | Initial check may pass, but protected current actor recheck/native Core deny after real later wait; zero effects/Audit |
| T12 | Independent Companies / disjoint Users | Different Companies/actors/links/Roles, shared read-only Permissions allowed; simultaneous compatible locks and BOTH progress, not historical EXCLUSIVE busy |
| T13 | Two HR operations share one User | Compatible FOR SHARE readers coexist; a relevant writer still waits or causes explicit busy |
| T14 | Concurrent HR with disjoint Users | No new global writer/reader gate; verify pg_locks and actual simultaneous progress |
| T15 | Superuser final authority | Stabilized SU flag→existing Permission namespace SHARE NOWAIT→ALL rows incl inactive; conflict55P03/full rollback; native namespace subset, no domain/self-approval bypass |
| T16 | Nested transactions | Same alias/connection/outer transaction/Company/actor/fixed union works; unknown outer and anchor expansion reject before blocking/new SQL |
| T17 | Non-default selected alias | Company/domain/admission/prelocks/Core/persistence/Audit/recovery all use selected alias; poison default cursor; nested switch rejects |
| T18 | Authority conflict after domain locks | Partial User/Role/Permission acquisition fails55P03; after whole rollback another worker can acquire released Company/domain/authority locks |
| T19 | Business effect and Audit rollback | Inject NOWAIT/validation/Audit failures, including nested savepoint; no authoritative row, revision, receipt or success Audit survives |
| T20 | Historical idempotent retry/current RBAC | Exact retained input/identity recovered separately from current native state; no reapplication/duplicate Audit; current revocation denies; old inactive provenance not reactivated |
| T21 | Repeated contention/explicit failure | Repeated hot-row refusals are bounded observable AuthorityBusy, no busy loop or starvation-free claim; later independent request revalidates |
| T22 | Reader/read concurrency | Same/disjoint global Users and shared Permissions permit cross-Company SHARE progress; Role SHARE/SHARE primitive compatibility does not bypass the same-Company mutex; no unnecessary FOR UPDATE/NO KEY UPDATE |
| T23 | Reversed User batch order | Canonical A→B as well as B→A, batch_size1, save/update/email/last_login/prelock/delete cases; no owner writer-order assumption |
| T24 | Reversed Permission/Role update order | Complete inactive-inclusive sets; adversarial ordering/mixed writes safely refuse, never later Core uncovered wait |
| T25 | Existing module final guard | Actual Sales public service and HR operation both winner orders across Companies; complete shared authority reads coexist, no new table-wide stall |
| T26 | Implicit ORM relation locks | Negative raw FOR SHARE NOWAIT / ORM select_for_update(nowait=True) can wait on implicit ROW SHARE; explicit three-relation ROW SHARE NOWAIT refuses before row locks; disjoint ROW EXCLUSIVE DML remains compatible |

Also require executed native Core SQL lock-target subset evidence, missing-row refusal, per-class
LIMIT1001 overflow/no truncated success, precise FK update fields, per-alias relation identity/search-
path mismatch rejection and monotonic/SQL-budget cleanup. These refine H07/H12/H13/H14; all original
H01–H18 requirements remain future implementation gates, not replaced by this lock-only matrix.

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
| H12 | All section14 domain race winners plus exact T01–T26 future PostgreSQL matrix: canonical B→A/A→B batch, mixed Role/Permission-upsert→User, actor/link variants, revocations, fixed nesting, retry and alias; compatible cross-Company/shared-reader progress and actual Sales guard; no unexpected 40P01, stale authority or partial effect/Audit |
| H13 | Complete non-User anchors→verified ROW SHARE NOWAIT relation admission→complete operation User union/ALL inactive-inclusive actor Roles/reachable Permissions FOR SHARE NOWAIT; existing SU namespace SHARE NOWAIT + all Permissions; native guard SQL subset proof, implicit relation negative control, full rollback/budgets/cleanup; NO whole-table EXCLUSIVE fallback or unnecessary historical activity checks |
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

### Historical first-correction investigation and proof record — 2026-10-15 Asia/Dhaka

This section records superseded `3ab7aaea...` EXCLUSIVE-gate design/probes only. Its P01–P22
winner/busy outcomes are NOT current finer-grained acceptance oracles. The later independent
re-audit resolved the original four defects but held formal acceptance for HR0-REAUD-1; the owner
then rejected global contention. Current authority acquisition is section8; it has no EXCLUSIVE
gate fallback. Preserve these historical results rather than reword them as new-protocol evidence.

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

At that first-correction checkpoint all H01–H18 were future implementation obligations and original
findings awaited independent re-audit. The later supplied re-audit resolved those four at contract
level and raised HR0-REAUD-1. At the subsequent finer-grained corrective checkpoint, status was
corrective candidate, not accepted/closed or HR-1 authority; the new correction awaited re-audit.

### Finer-grained correction evidence — 2026-10-15 Asia/Dhaka

Resume integrity: phase3a-hr-contract at exact first correction `3ab7aaea...`, then parent
`5be60f19...` and canonical umbrella `6453c8f...`; main/origin-main/live main unchanged, remote HR
branch absent. The only pending changes were the two authorized documentation paths, preserved
across the owner-requested wait for Docker. No extra candidate commit had been created.

The owner's instruction supplies Result **A — HR-ONLY FINER-GRAINED LOCKING FEASIBLE; Core/Identity
change NO**. The retrieved read-only investigation trace contains completed synthetic PART1–PART6
probe outputs, but no final-verdict message in that retrieved turn; attribute Result A to the supplied
owner record, not a newly manufactured independent acceptance. Its recorded evidence includes old
40P01 controls, full-set55P03 rollback, concurrent compatible readers, actual Sales guard interaction,
inactive provenance, selected alias and ordinary NOSUPERUSER/NOBYPASSRLS execution-role checks.
Row-lock NOWAIT alone still waited on an implicit relation lock; explicit ROW SHARE NOWAIT refused.
These observations support this proposed contract; none is HR-1 implementation acceptance.

Canonical-source inspection reconfirmed unchanged UserManager/save, Access policies/models/services,
Company-first supported assignment/link writers, Audit and selected-alias transaction helpers. No
Identity/Access/Core owner contract or runtime extension is secretly assumed. Internal consistency
review is not the separately required independent re-audit. Exact T01–T26 names remain section14.

#### Fresh focused PostgreSQL contract probes

New isolated container `hr0-fine-contract-proof-20261015-3ab7aae`, exact ID
`f5c659e8b291a3a4742a113db361bad0022b698a925daef31e04a7ac3caa6e45`, used PostgreSQL **17.11**,
network none, no ports/persistent mounts, tmpfs PGDATA and new synthetic hr0_fine_proof DB. Source
was mounted read-only; temporary Python stdin harnesses were not written/committed to the repository.
Existing migrations bootstrapped unchanged. Fake Users/Companies/Roles/Permissions/Party and the
harmless hr_fine_effect SQL table are not an HR implementation. The only Sales document was a
synthetic fixture in this disposable DB, created by its actual existing public service.

The fresh runner was Python **3.13.16**, Django **5.2.18**, psycopg **3.3.6**; these satisfy the
repository's existing dependency ranges. The earlier investigation used Django5.2.17. No source
dependency/settings change was made. Fresh DB execution used postgres; non-superuser below means
BusinessContext actor, not a new least-privilege database-role certification. Prior investigation's
ordinary DB-reader evidence remains separately attributed.

All fresh workers used hr_fine selected alias with a poisoned default cursor, finally-closed
connections, explicit Events and pg_stat_activity/pg_blocking_pids wait detection, 9s statement/7s
lock SAFETY timeouts. No arbitrary race sleeps. Fixed public table identities/kinds and per-alias
resolved OIDs were checked before/after ROW SHARE admission. No unexpected40P01 or safety timeout.

| Fresh probe | Actual observation, NOT future HR-1 PASS |
| --- | --- |
| F01 canonical B→A writer first | Real User.bulk_update(batch_size1) held B; reader55P03 at User ROW, writer committed, zero dummy effects |
| F02 HR-first | Writer visibly blocked by HR at conflicting User row; native complete Core guards succeeded, then both committed |
| F03 mixed Role→User | RoleQuerySet.update held Role before User batch; complete prelock refused55P03 at Role, whole reader rollback, writer committed |
| F04 Permission-upsert→User | Actual Permission.update_or_create held existing Permission; reader55P03 at that Permission, writer committed, zero effects |
| F05 disjoint Companies/Users | First reader held locks while second reader with shared global Permissions committed; both committed, two effects |
| F06 shared User across Companies | Same global actor/shared Permissions, distinct Company-owned Roles; second reader committed before first released; both committed |
| F07 full effect/Audit rollback | Injected failure after synthetic effect and ACTUAL record_audit_entry; whole outer rollback, zero dummy effect and no added matching Audit |
| F08 implicit relation negative control | Raw FOR SHARE NOWAIT visibly WAITED at relation admission against maintenance EXCLUSIVE; completed after release |
| F09 explicit relation admission | Same maintenance holder; explicit ROW SHARE NOWAIT failed55P03 before rows, no effect |
| F10 unrelated canonical DML | User.update + Role.update + Permission.update on disjoint rows all committed while HR locks remained held; HR then committed |
| F11 superuser | Existing Permission namespace SHARE NOWAIT + all38 current Permissions protected; native Core requests were subsets; committed |
| F12 actual Sales service | create_sales_order in another Company committed while HR-like transaction remained open; HR then committed, no new table-wide stall |

Captured real Core compound guards requested only prelocked targets: ordinary actor1 / assigned
Roles2 (including inactive) / Permissions3 (including inactive), twice; the other Company used its
own Role and shared Permissions. Superuser requested actor1/all38 Permissions twice. This is a
subset/equality coverage proof for these fixtures, not universal safety for unsupported transactions.
The retrieved investigation covered additional cases/both Sales winner orders; those are not
misreported as freshly rerun here. General HR-1 models/services, all T01–T26 and H01–H18 remain future.

#### Quality, interruptions and cleanup

| Check / exact command | Actual result |
| --- | --- |
| python manage.py check | PASS, zero issues |
| python manage.py makemigrations --check --dry-run | PASS, no changes detected |
| ruff check . --no-cache | PASS, Ruff0.17.0; no source formatting/writes |
| pytest tests/test_database_architecture.py tests/test_modules.py tests/test_database_foundation.py -q -p no:cacheprovider | **248 passed in13.25s**, existing architecture/registry/alias/bootstrap guards only |
| Fresh unchanged migration bootstrap | PASS on new PostgreSQL17.11 DB, hr_fine alias; not a customer/demo database |

Quality commands ran in a task-only Python3.13 Docker image built from the declared dependency
ranges via stdin, ephemeral --rm runner, network none, read-only source, PYTHONDONTWRITEBYTECODE=1,
config.settings.test/in-memory SQLite and all three existing financial-integration install flags.
No full PostgreSQL application suite/browser/hosted HR CI was required or claimed for these docs.

| Final pre-commit documentation / integrity check | Actual result |
| --- | --- |
| Markdown relative links and heading anchors | PASS: 49 file links and one heading anchor resolve |
| Fences, final newlines, trailing whitespace and git diff --check | PASS |
| Acceptance enumeration | H01–H18 and T01–T26 each present exactly once in their matrices; future HR-1 tests are not marked PASS |
| Current locking requirements | Three ROW SHARE NOWAIT admissions; existing superuser Permission SHARE NOWAIT retained; no current EXCLUSIVE gate/fallback |
| Protected contract comparison with first correction | Sections 2–3, 5–7 and 9–12 unchanged; no Attendance/Leave cap, lifecycle, permissions or Audit change |
| Candidate scope | Exactly the two authorized Markdown files; empty index and no untracked candidate files before staging |
| Local refs / ancestry | All 48 recorded local branch/tag refs unchanged before commit; HEAD 3ab7aaea → 5be60f19 → 6453c8f |
| Main / publication | Local main, origin/main and live remote main remain 6453c8f3202335aabe8a872046fea2e607dac858; live remote HR branch absent |

The ref comparator covers the recorded local heads/tags, not additional remote-tracking refs;
live publication identities were checked separately with git ls-remote. No fetch/ref update was
needed. The subsequent single local correction commit may move only phase3a-hr-contract.

Interruption history retained: the first optional Docker startup failed with engine/WSL errors and
returned no container ID; the owner requested a wait, then authorized continuation after opening
Docker. An attempted local fallback was Python3.12.14, outside baseline: check/drift/lint passed,
guard run emitted errors and was interrupted. It was not diagnosed as a source defect, counted as
passing evidence or used to certify this candidate. Docker's previous QA images were unavailable
after restart; a disposable Python3.13 runner was built instead. The complete canonical-version
quality run above passed. No unrelated environment/runtime remediation was attempted.

After proof completion verified exact task container identity, network/tmpfs/no mounts/ports and
zero remaining worker DB sessions. Removed ONLY that container and task QA image
hr0-fine-contract-qa:20261015-3ab7aae (verified image ID
`sha256:d083c34021137c4d90547751b94cd4690bcba822bb99a9ddaf178ffe65a496b4`); filtered inventories
confirmed both absent. Tmpfs synthetic DB/fixtures were removed and are not recoverable. Downloaded
Python/PostgreSQL base images were retained; no broad Docker cleanup or preexisting resource deletion.

All original domain/history corrections remain intact. At that finer-grained corrective checkpoint,
HR0-REAUD-1 status was **CORRECTION
PROPOSED — INDEPENDENT AUDIT PENDING**. ADR0018 was PROPOSED — NOT ACCEPTED; HR-1/ECOM-0,
push/PR/merge/tag/main update were unauthorized. The then-current STOP was after one local correction for a
fresh independent technical-contract re-audit, not formal acceptance or runtime implementation.
That historical pending boundary is superseded by the supplied final audit and authorization below.

### Final independent re-audit and formal acceptance — 2026-10-15 Asia/Dhaka

Exact reviewed candidate: `c99ea988ff7e1a74fed3ed4cb1232cd7db37957a`.
The owner supplied **FINAL PASS — HR-0 FINER-GRAINED TECHNICAL CONTRACT APPROVED FOR FORMAL
ACCEPTANCE**, **Readiness A**, **P0: 0 / P1: 0 / P2: 0 / P3: 0**. HR0-AUD-1–4 and HR0-REAUD-1
are all **RESOLVED at technical-contract level**. This task records the supplied independent review,
not a new self-issued audit. Original REVISE results, first-correction HOLD, rejected global gates,
Option B/Result A, interruptions and all previous verification evidence remain historical above.

Supplied independent evidence includes PostgreSQL T01–T26, original 40P01 reproduction and no
corrected deadlock in tested supported probes, complete authority sets, cross-company simultaneous
progress, current authorization/revocation, selected alias, atomic rollback, historical retry and
retained temporal/history corrections. It also reports 248 existing architecture tests passed.
The earlier 248-test and twelve fresh-probe execution records remain separately attributed; none
certifies implemented HR. H01–H18 and T01–T26 remain future HR-1 implementation obligations.

**INDEPENDENT FINAL CONTRACT AUDIT: PASS / READINESS A. FORMAL ACCEPTANCE: COMPLETE.**
**CANONICAL ADOPTION: PENDING AT THIS ACCEPTANCE CHECKPOINT. ADR 0018: ACCEPTED FOR CANONICAL
ADOPTION. HR-1: NOT AUTHORIZED. ECOM-0: NOT STARTED. PHASE 3: NOT COMPLETE.**

No policy/technical requirement changed: verified qualified relation admission, complete actor/new-FK
User union and inactive-inclusive Role/Permission NOWAIT sets, existing SU namespace, unchanged
final Core guards, fixed alias/nesting, whole rollback/AuthorityBusy and historical receipts are
frozen. The domain schema, twelve codes, Company/Branch, optional non-authorizing User, multiple
sessions, complete append-only chains, no duration/span caps, full-day Leave, HTTP-only enablement
and atomic Audit are retained. No runtime, migration, test, settings, manifest or frontend changes.

#### Formal-acceptance local verification

The following checks were actually rerun for this docs-only acceptance, separately from supplied
independent review and earlier corrective execution evidence. A disposable --rm Python3.13 container
mounted source read-only, installed unchanged requirements/development.lock, set
PYTHONDONTWRITEBYTECODE=1 and config.settings.test, and enabled the three existing financial
integration install flags. Python3.13.16, Django5.2.17 and Ruff0.16.7 were observed. Database state
was in-memory SQLite only; no customer/demo database or existing container was used. Network was
used for the base-image/locked-package downloads, not customer data. No full application suite or
new PostgreSQL contract probes were required/claimed by this acceptance task.

| Exact check | Actual acceptance-stage local result |
| --- | --- |
| python manage.py check | PASS, zero issues |
| python manage.py makemigrations --check --dry-run | PASS, no changes detected |
| ruff check . --no-cache | PASS |
| pytest tests/test_database_architecture.py tests/test_modules.py tests/test_database_foundation.py -q -p no:cacheprovider | **248 passed in 36.44s**, existing guards, not HR-1 tests |
| Markdown and scope checks | PASS: 49 relative links, one heading anchor, balanced fences, H01–H18/T01–T26 exact; only two authorized Markdown paths |
| Reviewed contract preservation | PASS: technical sections 2–17 verbatim unchanged from c99ea988; ADR acceptance/status prose only, no policy change |
| git diff --check | PASS |

Documentation/whitespace/scope/ancestry are rechecked before this single acceptance commit. Hosted
branch CI, main CI, run identifiers and test counts remain unclaimed until actually observed.

#### Acceptance publication and canonical completion rule

Required chain, exactly four commits above canonical umbrella:

```text
6453c8f3202335aabe8a872046fea2e607dac858
-> 5be60f19e3bf654786abcd06b61149bc4a962ea9
-> 3ab7aaea019833b9a0f5123f51018f4d516db366
-> c99ea988ff7e1a74fed3ed4cb1232cd7db37957a
-> this ONE formal acceptance commit
```

Publish `phase3a-hr-contract` normally only after unchanged live main/absent remote branch checks.
Require `Phase 0 checks`, event push, exact branch and acceptance SHA, SUCCESS with actual mandatory
PostgreSQL/bootstrap/lint/Django/drift/npm/Tailwind/CSS evidence. Then reverify live main still
`6453c8f3202335aabe8a872046fea2e607dac858` and the exact fast-forward chain. Normally push the
same exact acceptance SHA directly to main (no PR), require a SEPARATE successful main push CI at
that SHA, then and only then switch local main and pull --ff-only. Preserve the HR branch.

Only after that complete chain does this acceptance SHA become the **CANONICAL HR-0 CONTRACT
FREEZE**, with HR-0/ADR0018 CANONICALLY ACCEPTED. The pending statement is acceptance-stage history
superseded by verified completion; no second commit or future CI result is assumed. Report actual
run numbers/IDs/attempts/counts after observation, not before. Any failure/rejected push/unexpected
state stops without automatic remediation, amendment, revert or another commit.

After success HR-1 is ELIGIBLE FOR SEPARATE AUTHORIZATION, NOT STARTED; ECOM-0 remains separately
eligible and NOT STARTED BY THIS TASK. HR-1/ECOM-1, Phase 4 and production deployment remain
unauthorized. Phase 3 is NOT COMPLETE; production readiness is NOT CLAIMED. No PR, tag, force-push,
rebase, squash, merge commit, branch deletion, runtime change or automatic next milestone.

## HR-1 formal implementation acceptance — 2026-10-21

This later acceptance section supersedes historical HR-1 authorization/status statements only.
All earlier text, including the accepted HR-0 technical contract and original failures, remains
unchanged. HR-0/ADR 0018 are ACCEPTED at canonical base
`b36cdba91654e6a583735d67f7f6cf27a835003e`; ADR 0017 and the accepted Phase 3 owner decisions
are unchanged. This is implementation acceptance, not a new architecture decision.

The exact accepted linear candidate history is:

- HR-0 canonical base: `b36cdba91654e6a583735d67f7f6cf27a835003e`.
- Original HR-1: `e6b72896e10471463b8b6b280fbccfc524d7cc42`.
- Independently approved corrective implementation: `c49a1291ce979093f1219dea41d5fdcd743239b7`.
- Independently approved CI-only coverage delta: `a867a8c240627f4161ec4ef23564a320d4cf6b49`.
- This documentation-only acceptance commit has that CI-only SHA as its immediate parent.

The original independent HR-1 audit was REVISE / Readiness B / four P2. HR1-AUD-001,
HR1-AUD-002, HR1-AUD-003 and HR1-AUD-004 are independently RESOLVED. The fresh corrective
re-audit and separate CI-delta audit both returned FINAL PASS / Readiness A, with no new
blocking P0/P1/P2. [CI #138](https://github.com/sahinkhan/djangobusinessos/actions/runs/39543423762)
succeeded on the corrective SHA with 4,326 PostgreSQL tests but lacked hosted JavaScript tests.
[CI #139](https://github.com/sahinkhan/djangobusinessos/actions/runs/39567787163) succeeded on
the CI-only SHA with 4,326 PostgreSQL and 21 JavaScript tests. The
[evidence checkpoint](HR_1_IMPLEMENTATION_EVIDENCE.md#formal-acceptance-checkpoint--2026-10-21)
records the actual logs, audit identities and limitations; local evidence is not represented as
hosted execution.

HR-1 runtime implementation is **FORMALLY ACCEPTED FOR CANONICAL ADOPTION at this documentation
checkpoint**. Accepted scope is HR Foundation v1: Employee, Department, Attendance,
AttendanceRevision, LeaveType and LeaveRequest. It is not Full Enterprise HR, Payroll,
recruitment, shifts or biometric attendance. No production readiness, SaaS/tenant activation or
deployment approval is claimed.

This acceptance does not change the six model ownership rules, twelve permission identities,
Employee/Department lifecycle, Attendance revision/history authority, frozen timezone semantics,
Leave lifecycle, ROW SHARE NOWAIT admission, complete User/Role/Permission locking, existing
Core final guards, selected execution-alias rules, nested transaction/whole-outer rollback policy,
historical retry/immutable receipt semantics, or H01–H18 and T01–T26. All preexisting contract
sections remain byte-for-byte unchanged in the committed document.

### Conditional canonical completion rule

Canonical HR-1 adoption is **PENDING** at this documentation checkpoint. The owner authorizes
only this sequence, with no amendment or further acceptance commit:

1. Publish this exact acceptance commit normally to the existing HR-1 branch and require a NEW
   successful exact-head `Phase 0 checks` push run, including actual PostgreSQL terminal results,
   21 JavaScript passes/zero failures/zero skips, migrations, Ruff, Django checks, migration
   drift, Node/npm and Tailwind/generated-CSS checks.
2. Reverify remote main is still `b36cdba91654e6a583735d67f7f6cf27a835003e`, HR-1 equals this
   acceptance commit, exact linear ancestry and preserved user edits; only then normally
   fast-forward that same acceptance SHA to main. If a security reviewer requires direct owner
   approval of the concrete SHA, stop and request it. No force, merge commit, PR or tag.
3. Require a SEPARATE successful exact-head `Phase 0 checks` push run on main, with all configured
   gates and actual fresh PostgreSQL/JavaScript results. Branch CI alone does not prove main CI.
4. Only after those gates succeed does this acceptance commit become the **CANONICAL HR-1
   FREEZE**, and HR-1 implementation become CANONICALLY ACCEPTED. Record the actual SHA, run
   IDs/numbers/attempts/counts and fulfillment externally without another commit. Safe local-main
   synchronization follows only where no user worktree/index can be disturbed; otherwise report
   it deferred. Preserve the original dirty worktree and local acceptance branch.

No future run ID, count, main update or main CI success is asserted here. Failure, rejection,
drift or incomplete CI stops progression without automatic repair, retry, revert or new commit.
The historical unexpected native SQLSTATE 57014 cause and unexpected ResourceBudgetExceeded
cause remain separately NOT PROVEN; the interrupted run and bounded infrastructure diagnosis
are retained, not recast as pytest success/failure. Eight inherited npm advisories (two moderate,
six high) remain disclosed and unfixed by this task.

Phase 3 is **NOT COMPLETE**. ECOM-0 is separately governed and NOT STARTED BY THIS TASK; ECOM-1
is NOT STARTED. Ecommerce work and the final combined Phase 3 audit/closure remain future gates.
Phase 4 Education/Healthcare stays **ON HOLD** at
`735e1bea13bc58fa71d430163422139d5c0f2363`; ADRs 0019–0021 remain PROPOSED. No next phase,
dependency remediation or owner-decision resolution is authorized.
