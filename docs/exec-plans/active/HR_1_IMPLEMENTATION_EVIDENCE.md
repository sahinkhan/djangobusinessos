# HR-1 local implementation evidence

Canonical base: `b36cdba91654e6a583735d67f7f6cf27a835003e`.
This is an implementation-run record, not an independent audit or acceptance.
The accepted [HR-0 contract](PHASE_3A_HR_FOUNDATION.md) remains unchanged.

**Latest local status: HR1-AUD-1 corrective implementation is INCOMPLETE / NOT
AUDIT-READY.** Latest [pending-Attendance budget diagnosis](#hr1-aud-1-pending-attendance-budget-diagnosis)
passes its bounded fresh safety checks, but the earlier budget-consumption cause
remains NOT PROVEN. The [owner-authorized final-verification attempt](#hr1-aud-1-owner-authorized-final-verification--stopped)
failed its fresh focused prerequisite and remains historical. The owner
authorized a limited exception to the historical root-cause prerequisite;
historical 57014 causation remains NOT PROVEN. Earlier
[two-oracle diagnostics](#hr1-aud-1-two-oracle-diagnostics), the
[prior resumption](#hr1-aud-1-resumed-verification) and all failures remain
historical evidence, not substitutes for the failed current gate.
[Completed local verification](#completed-local-verification) records the
original implementation checkpoint, not corrective approval. The subsequent
independent REVISE and every failed/intermediate run below remain historical
evidence. No corrective commit, independent corrective re-audit, acceptance,
hosted publication, canonical adoption or production approval has occurred.

## Concurrency and authority verification

Evidence date: 2026-10-15 Asia/Dhaka. Runs use the locked disposable
`hr1-local-qa:b36cdba` image (Python 3.13 / Django 5.2.17 / Ruff 0.16.7).
PostgreSQL runs use the task-created, network-isolated, tmpfs-backed PostgreSQL
17 fixture `hr1-implementation-proof-pg-b36cdba`, not an existing demo database.
Pytest creates and tears down its synthetic application test database. Worker
connections are independent and explicitly closed. Race assertions inspect the
actual PostgreSQL lock graph; short polling waits are not ordering evidence.

Actual completed focused runs, preserved as chronology:

- Initial admission SQLite: **17 passed, 9 PostgreSQL-only skips**, 36.10s.
- Initial admission PostgreSQL: **28 passed**, 51.29s.
- Expanded public-service run: **34 passed, 4 failed**, 74.27s. Failures were
  fixture setup (one duplicate registered HR permission and three absent Core
  revoker permissions after flush), not accepted runtime behavior. Fixtures were
  corrected explicitly; no test or required permission was removed.
- Expanded admission PostgreSQL including fixed source identities: **55 passed**,
  93.66s.
- Final expanded admission and domain-race PostgreSQL run: **66 passed**, 170.08s.
  This executed the isolated old-protocol negative control, exact native SQL UUID
  subset oracle (both superuser/non-superuser), actual two-order batch UPDATE
  writers and all nine public domain races described below.
- Corresponding supported SQLite run: **19 passed, 47 explicitly PostgreSQL-only
  skips**, 76.65s. No SQLite result is offered as PostgreSQL concurrency proof.
- Subsequent bounded additions (non-PII failure observability, repeated hot-Role
  refusal, second-worker anchor-release assertion) passed their targeted actual
  PostgreSQL run: **4 passed, 55 deselected**, 19.32s. This selection runs the two
  strengthened batch orders and the two new tests, not another full suite.
- Final exact-three-file Ruff lint passed. Format checking uses `--no-cache`
  because the source mount is read-only; an initial cache-write refusal is a
  runner invocation issue, not source formatting evidence.
- The remaining mixed/reversed authority, User-writer, relink, current-retry
  and ORM-relation cases passed their focused PostgreSQL selection: **40 passed,
  70 deselected in 78.71s**. No unexpected SQLSTATE 40P01 was accepted.
- The subsequent complete admission/concurrency run returned **112 passed,
  1 failed in 260.51s**. The writer-first `User.update` case's five-second test
  coordination watchdog expired while other heavy verification runners were
  active; PostgreSQL also terminated the HR connection with
  `IdleInTransactionSessionTimeout`. This was a refused operation, not successful
  stale authorization. Host scheduling pressure is a plausible explanation,
  not a separately instrumented root-cause proof. The test-only coordination
  watchdog is now fifteen
  seconds; HR's production cumulative/statement/lock/idle deadlines remain
  unchanged. The focused green case is not substituted for the required final
  complete PostgreSQL rerun, which remains pending in this subsection.

Source namespace admission pins sixteen fixed `public` ordinary-table identities
with compatible **ACCESS SHARE NOWAIT**, before Company/data reads, then rechecks
OID, kind, effective unqualified resolution, RLS flags and even disabled policies.
This stabilizes identities against replacement DDL, not ordinary DML writers.
The distinct final authority protocol remains precisely three **ROW SHARE
NOWAIT** relations, complete **FOR SHARE NOWAIT** rows, and the existing Core
superuser Permission **SHARE NOWAIT** namespace. There is no EXCLUSIVE fallback.

### T01–T26 implementation traceability

`A` denotes [test_hr_admission.py](../../../tests/test_hr_admission.py); `C` denotes
[test_hr_concurrency.py](../../../tests/test_hr_concurrency.py). A passed related
test is not automatically a complete matrix PASS. The table names actual
case-specific oracles rather than inheriting HR-0 investigation probe results.
The final lead-run PostgreSQL regression and the disclosed coordination-failure
rerun remain gates; the table does not turn those pending runs into PASS.

| ID | Actual implementation oracle / pending requirement |
| --- | --- |
| T01 | A `test_original_blocking_user_order_deadlock_is_an_isolated_negative_control`: executed explicit rejected old protocol; one expected isolated 40P01, not a current HR protocol failure. |
| T02 | A `test_public_employee_hr_first_writer_wait_is_row_not_global_gate`: actual Employee create, actor=link and actor!=link, observed User writer row wait and one effect/Audit. |
| T03 | A `test_public_employee_writer_first_unordered_user_batches_fail_closed`: executed both actual batch orders with batch_size=1, first UPDATE held, HR55P03 and no effect/Audit. |
| T04 | Actor=link case in T02 verifies actual association, current native authority and FK effect; fixed User union deduplicates. |
| T05 | Actor!=link cases in T02/T03 protect both identities without deriving actor permission from beneficiary. |
| T06 | C `test_inactive_removed_user_lock_does_not_block_public_unlink_or_relink` executes clear/relink with the inactive old User row independently held. `test_public_relink_writer_first_deactivation_is_busy_then_currently_ineligible` refuses actual target-row contention then current inactivity; `test_public_relink_hr_first_deactivation_waits_then_retains_identity` observes the deactivator's row wait and preserves the committed association/history. All four cases passed the focused 40-case and complete 113-case attempts. |
| T07 | A `test_original_user_only_reader_mixed_role_writer_deadlock_negative_control` reproduces the rejected User-only mixed Role-to-User cycle, with exactly one expected isolated 40P01. `test_actual_mixed_authority_then_user_batch_both_winner_orders` executes Role mutation/retirement followed by actual `User.bulk_update(batch_size=1)`: writer-first complete-set admission refuses 55P03; HR-first writer waits on the held relevant Role. |
| T08 | The same mixed-authority test executes Permission.update, Permission.update_or_create and Permission retirement followed by User batch, both winner orders. `test_unrelated_permission_update_or_create_and_user_writer_remain_compatible` executes unrelated Permission upsert and User mutation in both orders without a global gate. |
| T09 | A `test_public_hr_waiter_rechecks_committed_company_revocation[company_access]`: actual observed Company wait, owning Access revoke then denial/no HR effect. C `test_hr_first_company_access_revoker_waits_until_valid_effect_commits` observes the revoker waiting on Company, then one valid HR effect before actual owner revocation and subsequent denial. |
| T10 | Same test role_assignment/role_permission cases plus `test_public_hr_rechecks_actor_and_authority_after_domain_wait[role]`: supported revocation and inactivity observed; complete inactive sets have separate oracle. |
| T11 | A `test_public_hr_rechecks_actor_and_authority_after_domain_wait[actor]`: initial authorization, observed Department wait, committed actor deactivation, final denial and unchanged Department/Audit. |
| T12 | A `test_public_hr_independent_companies_share_read_only_authority_without_global_gate`: actual nested public creates, distinct Companies, shared/disjoint actors, shared permissions, both admitted concurrently. |
| T13 | Shared-actor T12 plus T02 writer-wait oracle; separate primitive does not bypass a Company's serialization mutex. |
| T14 | Disjoint-actor T12; no new global writer gate. |
| T15 | A `test_existing_superuser_namespace_is_not_a_new_ordinary_dml_gate`: existing namespace refuses conflicting ROW EXCLUSIVE writer only for SU, ordinary caller progresses. All inactive namespace rows and native subsets separately checked. |
| T16 | A `test_admitted_nested_subset_reuses_outer_and_rechecks_guards`, `test_nested_expansion_rejected_before_sql`, unknown atomic/manual-transaction and caught-nested-failure tests, strengthened by actual public nested services below. Domain locks remain service-owned, not a public bypass token. |
| T17 | A `test_actual_public_hr_service_nondefault_postgresql_alias_and_default_cursor_trap`: actual Company/admission/persistence/Audit under selected PostgreSQL alias; separate fresh SQLite alias bootstrap. `test_actual_hr_admission_rejects_nested_alias_switch_before_sql` rejects a configured alias switch before target SQL and retains the original execution alias. |
| T18 | A `test_postgresql_nowait_conflict_rolls_back_before_authority_busy`: executed User/Role/Permission cases, outside-transaction error, no marker/Audit and released transaction locks. Strengthened T03 also executed another worker reacquiring the actual Company/Party/free-User anchors while the original writer still holds its first updated User row. |
| T19 | Whole rollback after authority NOWAIT, validation and caught nested failures is covered in A and the actual public nesting suite. `test_real_django_constraint_check_swallowed_timeout_cannot_commit_hr_effect` proves even Django's swallowed 57014 cannot retain native/Audit work. The separate adversarial file injects Audit failure for every Attendance effect and eight Leave effect/status families, with complete native/receipt/Audit readback; its 22-case SQLite run passed and PostgreSQL execution remains a lead full-suite gate. |
| T20 | C `test_historical_correction_retry_ignores_inactive_provenance_but_rechecks_current_revocation` executes a matching CORRECT retry after current VOID, while the old inactive provenance User row is held. It recovers revision 2 separately from current revision 3 without reapplication/Audit. Both actual company-access and permission revokers then win the observed Company wait; the retry denies current authority. |
| T21 | Executed `test_repeated_hot_role_refusals_are_bounded_then_fresh_request_succeeds`: three independent hot-row refusals with complete rollback/no success Audit, then a fresh successful request after contention ends. No retry loop or starvation-freedom claim. |
| T22 | T12 actual compatible cross-Company readers and T02 conflicting writer; namespace test proves ordinary ROW EXCLUSIVE intent compatibility. `test_role_share_readers_are_compatible_without_bypassing_company_serialization` holds the same Role FOR SHARE NOWAIT concurrently on two clean connections; it is explicitly a compatibility primitive, not a bypass of the existing Company mutex. |
| T23 | T03 executes both actual User batch orders with batch_size=1. `test_supported_identity_writer_forms_both_winner_orders` executes actual save/activity update/email save/Django update_last_login/prelock/delete forms, both winner orders; HR-first delete is rejected by retained-history protection after a valid HR effect. All twelve passed the focused selection; one writer-first update hit the disclosed full-run coordination timeout, requiring the pending final rerun. |
| T24 | A `test_reversed_active_inactive_authority_multirow_writers` executes Role and Permission active-first/inactive-first mutations, both winner orders. An inactive assigned Role and its inactive reachable Permission are included even when not needed by the requested compound. Relevant contention refuses 55P03 or the writer waits on the exact preheld row; no later uncovered Core wait is accepted. Mixed writer families are exercised under T07/T08. |
| T25 | A `test_native_sales_public_service_can_progress_while_hr_holds_shared_authority` and `test_native_sales_first_shared_authority_does_not_block_public_hr`: actual native Sales/HR public services, both winner orders, shared compatible authority. |
| T26 | A `test_implicit_for_share_nowait_still_waits_on_relation_negative_control` and `test_actual_orm_nowait_can_wait_for_implicit_relation_lock_negative_control` both observe actual implicit relation waiting, even with row NOWAIT. `test_explicit_relation_admission_refuses_before_implicit_row_acquisition` proves explicit relation admission fails before row SQL; ordinary unrelated DML remains compatible under T08/T15. |

Additional actual domain-race oracles in C: end versus record in both orders;
Branch transfer versus record in both orders with immutable winning snapshot;
two overlapping record attempts; two expected-revision corrections in both
orders; Leave approval versus Attendance in both orders. Each holds a real
winner effect/Audit before commit and observes the loser's actual lock wait.
All nine executed successfully in the 66-test PostgreSQL run above and the later
113-case attempt; corresponding SQLite cases explicitly skip because they
require real PostgreSQL row locks. The seven later relink/revocation/retry cases
also passed the focused 40-case and complete 113-case attempts.

At this checkpoint the complete T01–T26 matrix is **NOT PROVEN**. Focused green
admission tests do not independently establish every H01–H18 or T01–T26 oracle,
browser verification, full regression or fresh independent audit.

### Internal-review nested-domain and swallowed-SQL correction

Internal implementation review identified a genuine boundary gap: a public
nested service could enter with an empty anchor declaration and issue a domain
FOR UPDATE before its later declaration refused expansion. This was not an
HR-0 contract change. HR helpers now call private `require_domain_anchors`
**before** domain/reference lock SQL; admitted nesting can only reuse a complete
predeclared, prelocked set. Covered anchor/permission redeclarations are no-ops;
expansion poisons the entire outer transaction, including when caught by caller.
Invalid nested entry itself also poisons the outer operation.

Actual public-service tests live in
[test_hr_nested_services.py](../../../tests/test_hr_nested_services.py).
The first focused PostgreSQL attempt produced **12 passed, 1 failed**, 31.80s:
the single failure was an over-strong test forbidding every savepoint. Django's
unchanged intrinsic `Q.check` uses same-alias validation savepoints. The corrected
oracle proves no new HR adapter transaction while classifying those intrinsic
validation savepoints and preserving the same outer transaction.

A second internal gap concerned Django `Q.check` swallowing `DatabaseError` and
returning true after its internal savepoint. HR's execution wrapper now retains
and poisons **every** database error, including errors in scoped timeout setup;
an intrinsic savepoint cannot clear the operation's failure. There is no generic
SQLSTATE 23505-to-success exception or guessed receipt. Supported same-key
requests resolve through Company-serialized locked lookup; unclassified SQL
collisions propagate and roll back rather than pretending to recover a receipt.

Final targeted actual PostgreSQL result: **15 passed, 51 deselected**, 33.55s,
covering adapter declaration/nesting, all five actual public nested cases, and
`test_real_django_constraint_check_swallowed_timeout_cannot_commit_hr_effect`.
The last test executes real PostgreSQL `pg_sleep(3)` inside actual Django
`Q.check`, receives SQLSTATE **57014**, proves Django returned its true fallback,
and nevertheless verifies complete rollback of a real nested public Department
creation and its successful Audit, with `ResourceBudgetExceeded` only after the
outer boundary. The corrected admission-only SQLite selection also passed:
**9 passed, 51 deselected**, 22.27s. No Core/Identity/Access owner implementation
was changed.

## Schema/HTTP/topology verification

Implementation-run evidence on 2026-10-15 Asia/Dhaka; not independent review,
hosted CI, canonical acceptance or production readiness. These checks used the
same locked `hr1-local-qa:b36cdba` image, read-only repository mount,
`PYTHONDONTWRITEBYTECODE=1`, `docker run --rm`, no published ports, and new
in-memory synthetic SQLite databases. No customer/demo data or target repository
was accessed. All worker containers exited and were automatically removed.

### Six-model schema and private persistence

The exact Department, Employee, Attendance, AttendanceRevision, LeaveType and
LeaveRequest fields, protected foreign keys, ordinal bounds, uniqueness, receipt
groups and indexes are represented by additive HR migrations only. Public
instance save/save_base/delete and ordinary create/update/delete/bulk/upsert/
get_or_create/update_or_create paths reject for default and base managers.
Private operation-specific persistence uses persisted identities, precise changed
columns, complete Attendance-chain certification, exact civil geometry and
server event timestamps. Unchanged historical User foreign keys are not rewritten.

`tests/test_hr_models.py` contains **164** focused schema/persistence cases.
The initial run produced **159 passed, 1 failed**: a new test incorrectly
compared a 366-day exclusive difference against 366 instead of its 367-day
inclusive Leave span. Its oracle was corrected; no duration/span ceiling was
added. A subsequent focused run passed **164 tests in 17.37s**.

The first combined PostgreSQL implementation run, recorded by the lead runner,
reported **381 passed, 1 failed**: the new raw upper-bound test expected only
`IntegrityError`, but PostgreSQL int4 rejects 2,147,483,648 with `DataError` /
SQLSTATE **22003** before evaluating CHECK. The corrected test expects 22003 for
that storage overflow and **23514** for zero, and independently inspects actual
constraint definitions for explicit `revision >= 1` and `revision <= 2147483647`.
No field type, CHECK, migration or accepted semantics was changed for that oracle.

### HTTP adapters and current-scope evidence

`tests/test_hr_http.py` contains **126** focused cases. Actual public owner
services create all synthetic HR fixtures for request-path tests. Eighteen
mutation routes are each exercised with stale submitted Company/Branch scope,
and with actual authorized session switches to another Company or Branch.
The oracle compares every native field of all six HR tables plus the Audit
count: no rejected request changes either business state or successful evidence.

Other executed cases cover complete creation-form GET permission admission,
disabled-surface behavior, navigation visibility, CSRF, no GET mutation,
escaped maximum-length identity text, stable 50-row pagination, malformed
filters, bounded independent related-choice searches and retained current
inactive Branch selection without an implicit clear. Normal GET/POST forms
remain usable without JavaScript; no new HTMX mutation behavior is introduced.
Static adapters are not offered as actual browser Back/Forward/pixel evidence.

Both New York DST folds were exercised through real HTTP corrections after the
Company timezone changed: the unchanged trusted local start minute preserves
the original UTC instant, fold and `45.123456` precision; a changed unambiguous
end becomes the new whole-minute instant. Posted fake original timestamps are
ignored. Generic new ambiguous/nonexistent local inputs still reject. Decision
and cancellation reason fields do not reuse the original Leave request narrative.

Final complete owned-suite command:

```text
pytest tests/test_hr_models.py tests/test_hr_http.py -q -p no:cacheprovider
```

**290 passed in 94.88s**: 164 model/schema + 126 HTTP/forms tests. Prior green
runs and the corrected failing oracles above remain implementation chronology,
not extra independent test counts. Exact owned-path Ruff checks, explicit
format checks of twelve related Python files including both new HR migrations,
and `git diff --check` passed. HR migration drift check returned
**No changes detected**.

### Actual minimal topology bootstrap

A separate `docker run --rm -i --network none` process mounted source read-only
and configured only the existing Django technical apps, required Core apps,
Party and HR before `django.setup()`. It filtered commercial-only template
context processors and selected a temporary in-memory HR-only URL configuration.
These were process-local test settings; no repository settings, migrations or
manifest was edited by the probe. SQLite database identity was exactly
`:memory:`. Catalog, Sales, Procurement, Inventory, Billing, Payments, Accounting,
Ecommerce and their integration apps and tables were all absent.

Actual commands in that process:

```text
call_command("migrate", verbosity=0, interactive=False)
call_command("check", verbosity=1)
call_command("makemigrations", "--check", "--dry-run", verbosity=1)
```

Fresh migration bootstrap succeeded, Django reported **zero issues**, and drift
reported **No changes detected**. App discovery and catalog inspection found
exactly the six HR models/tables. The migration leaf was
`hr.0002_register_manifest`; exactly **12** HR Permission identities were present
and the HR registry remained **disabled**. Actual public services created one
Department, LeaveType, Employee, Attendance with its initial Revision, and Leave
draft while HR stayed disabled, producing exactly **five** successful HR Audits.
No commercial module import/effect was required for those services.

The first minimal-topology probe above proved SQLite only. The subsequently
executed PostgreSQL probe below closes that backend-specific topology gap; it
does not substitute for full regression suites or independent review.

### Minimal PostgreSQL topology follow-up

The separate `hr1_minimal_topology` database was created only after verifying
that this exact name did not exist in the task-created
`hr1-implementation-proof-pg-b36cdba` PostgreSQL 17 container. Its database
comment identified this HR-1 synthetic task and baseline. The QA runner used
read-only source and process-local settings with the same minimal installed
app set as the SQLite probe; no source settings, URLs, manifest or migration
were edited. A temporary HR/Core/Auth URL configuration permitted real HTTP
checks without importing commercial modules.

Actual commands in that fresh database were `migrate`, `check` and
`makemigrations --check --dry-run`. All **passed**: zero Django issues, no
migration drift, exactly six HR tables/models, exactly twelve registered HR
Permission identities and migration leaf `hr.0002_register_manifest`. Catalog,
Sales, Procurement, Inventory, Billing, Payments, Accounting, Ecommerce and
their integration apps/tables were absent.

Real public services, while the HR registry stayed disabled, created one
Department, LeaveType, Employee, Attendance, initial AttendanceRevision and
LeaveRequest, producing exactly five HR success Audits. An authenticated real
Django Client received **404** for disabled `/hr/`; after an explicit synthetic
registry enable, both `/hr/` and `/hr/employees/new/` returned **200**. This
confirms installed Python service availability and separate HTTP enablement
under the minimal topology, not authorization for operational deployment.

All Django connections were closed. Before cleanup, the exact synthetic custody
comment and zero remaining sessions were verified; only this new database was
dropped and its absence rechecked. The ephemeral QA container was automatically
removed. The shared proof PostgreSQL server, existing demos and all other
databases were untouched.

### Demonstrated bounded UI layout corrections

Implementation browser inspection identified two HR-local presentation defects:
max-content Employee identity compressed state text, and the expanded related
choice-search form inherited the compact header-tools width at 768px. State and
revision cells/headers now retain unbroken labels within the existing local
scroll container. The choice-search GET form now occupies the full content
width below the header and before, rather than inside, the normal POST form.
No shared styles or navigation JavaScript changed. A response regression checks
the independent form placement. Final real-browser responsive measurements
remain the lead task's separate evidence, not an assertion of this subsection.

After both demonstrated layout fixes, the bounded command
`pytest tests/test_hr_http.py -q -p no:cacheprovider -k
'header_and_bounded_related_choice_search or employee_lists_pagination or
inactive_current_branch'` passed **3 tests**, with **123 deselected**, in
**27.99s** against a new ephemeral SQLite database. Owned-file Ruff lint passed,
explicit Ruff format checks passed for all **13** owned Python paths (including
both migration modules and package markers), and `git diff --check` passed.
The branch remained `phase3a-hr1-implementation` at unchanged baseline HEAD
`b36cdba91654e6a583735d67f7f6cf27a835003e`; these are uncommitted working-candidate
results, not an approved artifact.

## Functional adversarial verification

These are local implementation-run results on the uncommitted HR-1 working
candidate, not independent acceptance or a frozen implementation SHA. The
accepted source base remains `b36cdba91654e6a583735d67f7f6cf27a835003e`.

The focused commands used `hr1-local-qa:b36cdba`, Python 3.13 and unchanged
locked dependencies, read-only `/app` source, `PYTHONDONTWRITEBYTECODE=1` and
`pytest -q -p no:cacheprovider`. SQLite runners used `--rm --network none`,
`config.settings.test` and new in-memory databases. PostgreSQL runners used
the already task-created isolated `hr1-implementation-proof-pg-b36cdba`
network namespace and synthetic application/test databases, never a demo or
customer database. Pytest test databases and ephemeral runners were removed
at normal completion; the shared disposable proof server remains under the
lead task's final cleanup responsibility.

| Actual command / result | Bounded evidence and traceability |
| --- | --- |
| `pytest tests/test_hr_civil_time.py tests/test_hr_history.py -q -p no:cacheprovider` — PostgreSQL **117 passed in 23.09s** | H09/H10 portions: exact TZif/ZoneInfo and SQL integer-offset proofs; microsecond/fold/extreme-year cases; complete-chain sequence/predecessor/cached-date checks; 1,001-revision chain with only scalar/violation/latest materialization; ordinary-reader RLS, disabled policy, relocation and shadow rejection |
| Earlier SQLite civil/history run — **110 passed, 5 PostgreSQL-only skips in 19.54s** | Same functional families at that checkpoint; five catalog/RLS proofs explicitly skipped. Two additional portable path-identity cases were added afterward and are included in the PostgreSQL 117 above; this earlier run is not represented as the final candidate-wide SQLite result |
| `pytest tests/test_hr_nested_services.py -q -p no:cacheprovider` — SQLite **5 passed in 13.85s** | H07/H13/H14 portions: actual covered public update/no-op reuses one outer transaction; unknown public mutation/selector anchor rejected before target SQL; caught failures cannot commit earlier outer Audit or business effects |
| Admission agent's combined PostgreSQL critical regression run — **15 passed, 51 deselected in 33.55s** | Includes those five actual public nested cases; attributed combined-run evidence, not another independent review or 15 additional unique test cases |
| `pytest tests/test_hr_adversarial.py -q -p no:cacheprovider` — SQLite **22 passed in 30.08s** | H01/H03/H08/H10/H11/H14/H15 portions detailed below; PostgreSQL execution of this newly added file remains part of the lead's final full-suite gate |
| `ruff check tests/test_hr_adversarial.py --no-cache`; `ruff format --check tests/test_hr_adversarial.py`; `git diff --check` | PASS, no formatting or whitespace issue in the bounded addition |

The 22-case adversarial addition verifies actual owner service effects and
independent native ORM readback, rather than constructing expected state from
the implementation's output serializer:

- RECORD/CORRECT/VOID/REINSTATE each fail at the Audit boundary after the
  attempted persistence; all native Attendance/Revision fields, revision
  counters, request identities and existing Audit rows remain exactly as before.
- Leave create, draft update, submit, approve, reject and cancellation from
  DRAFT/SUBMITTED/APPROVED each roll back all native fields and event receipts
  together with Audit on injected failure. There is no partially retained key,
  actor, timestamp, state or revision.
- Explicit VOIDED selection returns only VOIDED latest facts, default selection
  returns ACTIVE_INTERVAL only, and an unknown effect filter rejects. A
  revision whose cached dates are moved outside the requested range is still
  discovered by UTC bounds and rejected by complete-chain certification.
- Fifty-one actual sessions include equal effective starts across two Employees.
  Two pages retain exact effective-start/UUID ordering, count 51, sizes 50 and 1,
  and materialized tuples. Captured SQL contains scoped COUNT, LIMIT 50 and
  OFFSET 50; Python list slicing is not accepted as backend-pagination evidence.
- PERSON choices omit inactive/non-PERSON/foreign-Company records and expose
  exactly the five permitted Party fields without contact/address queries.
  Removing employee.manage does not revoke PERSON choices under employee.view,
  but does deny the independent User-association choice surface.
- A deterministic interleaving performs a real validated Party retirement
  between candidate discovery and reference locking. PERSON, Employee-create
  and Attendance-record action choices all recheck current eligibility and
  reject; this is a functional interleaving, not PostgreSQL row-wait evidence.
- Retained decisions forged to name the immutable requester or frozen
  beneficiary fail intrinsic readback validation. Conversely, a legitimate
  decision remains historical evidence after its actor is subsequently linked
  as the current beneficiary; a matching decision retry still applies the
  separately required current self-decision restriction.

Historical verification failures remain disclosed. The first PostgreSQL
civil/history run returned **115 passed, 2 failed** because fixture RLS DDL ran
with deferred FK trigger events pending. The fixture now executes
`SET CONSTRAINTS ALL IMMEDIATE` before its synthetic DDL; no runtime rule or
assertion was weakened, and the complete 117-case rerun above passed. The first
public-nesting SQLite run returned **3 passed, 1 failed** on an overly broad
"no SAVEPOINT SQL whatsoever" oracle. Actual stack tracing identified Django
`Q.check` constraint-validation savepoints. The corrected test forbids a new
HR `business_atomic_context` entry, proves the same outer transaction and final
savepoint state, classifies all transient atomic callers as `Q.check`, and
separately proves full outer rollback after caught nested failures.

TZif limitations remain explicit: unsupported leap-second/truncated coverage,
native-parser rejection and any POSIX/ZoneInfo parity mismatch fail closed.
The synthetic bare-ordinal POSIX discrepancy observed in Python 3.13 is not
silently imitated. A separate read-only probe successfully compiled a 2050
annual basis for all **486** zones available in the Linux QA image; that is
not a claim of universal platform/tzdata certification. No calendar duration
or Leave-span admission ceiling was added.

This subsection does **not** mark H01–H18 or T01–T26 collectively PASS.
Full final candidate PostgreSQL/SQLite results, all missing-code/domain-race
coverage, non-default alias/topology evidence, real browser checks, final
quality/protected-diff checks and independent code/security review remain
separate gates. No hosted publication, canonical adoption, HR-1 acceptance,
Phase 3 completion or production readiness follows from these focused runs.

## Final local verification checkpoint

The owner authorized HR-1 local implementation after HR-0 acceptance. All work
remains on `phase3a-hr1-implementation`, directly above canonical
`b36cdba91654e6a583735d67f7f6cf27a835003e`. There is no runtime candidate commit
at this pending-verification checkpoint. The local held Phase 4 proposal remains
`735e1bea13bc58fa71d430163422139d5c0f2363`, untouched. A later read-only live
`git ls-remote --heads` succeeded and independently confirmed remote `main` and
`phase3a-hr-contract` at the canonical HR-0 SHA; the initial unavailable network
check is not represented as a successful check.

### Final test-set freeze and outstanding gates

The expanded complete test collection contains **4,108 cases**, including the
existing commercial integrations. Full PostgreSQL and SQLite runs of this
collection are pending. Earlier focused green runs are not substitutes for
those final results. Forty-eight candidate code/test/template/build files were
SHA-256 fingerprinted at this freeze; only this evidence document is excluded
from that comparison. No source change is permitted to be described as tested
by an earlier run that did not include it.

The first complete SQLite run (before the final coverage expansion and scoped
Employee-admission defensive rechecks) actually completed **2,079 passed,
1,451 explicitly classified skips in 1,466.76s**. Skips are PostgreSQL locking,
catalog/RLS/DDL/topology, exact monetary arithmetic and other already classified
backend-specific cases. This is preserved historical implementation-run evidence,
not the expanded collection's final result.

Additional root-owned cases exercise actual Company-serialized Employee Party,
number and active-User uniqueness winners; setup-code races; Department retirement
versus new active assignment; a real 1,000+1 revision-candidate sentinel;
actual candidate query EXPLAIN; and wall-clock rollback without revision-causality
assumptions. Their final database execution is pending with the complete runs.

Self-review added current protected Employee Branch/ACTIVE rechecks to action
admission and choices. Supported HR transfers/end operations are already serialized
by the Company mutex. The additional raw persisted-state interleaving regressions
are deliberately classified as functional defensive tests, not claims that a
supported HR writer bypasses that Company mutex.

### Actual browser and frontend evidence

Browser work used the computer-use skill and the real in-app Chromium browser,
only against task-created localhost fixtures. The primary fixture uses a fresh
SQLite database in container tmpfs, with synthetic Companies, accounts, persons,
maximum-length names/codes, a 49-hour session and a 2,000-character Leave reason.
Neither existing demo data nor customer data was accessed. The runner was
recreated after code/template corrections; uncached template loading is confined
to the fixture process, not source settings.

- Final primary navigation traversed **27 observed HR routes at each actual
  390, 768 and 1,280 pixel viewport**: Employee/setup lists, details and forms;
  Attendance record/correct/void/reinstate/history; and Leave draft/edit/submit/
  cancel screens. Every measurement had document scroll width at or below the
  viewport. Wide tables scroll locally (760px table inside the 380px mobile
  container), not at page level.
- Two demonstrated local presentation defects were corrected and rechecked:
  maximum-content state/revision columns now remain unbroken; expanded related
  choice searches now occupy full-width HR content rather than a narrow header
  tool. All five Employee-create search inputs were actually usable at the
  tablet breakpoint; the mobile screenshot shows full-width stacked fields.
- Keyboard Tab moved focus to the next field with a visible plum focus ring;
  Enter submitted a whitespace-only name and server-rendered the field-required
  error. A real normal CSRF-protected Leave-submit POST returned SUBMITTED native
  readback. Additional final history/pagination/decision-form checks remain pending.
- A separate disposable fixture strips application script elements from rendered
  responses without changing repository files. Browser DOM inspection confirmed
  **zero scripts** on login, HR filtering and successful Department-create native
  readback. Login, Company selection, normal links, GET query parameters and an
  Enter-submitted POST all worked without HTMX/Alpine. This is a script-free HTML
  fallback fixture, not a claim that browser developer tools disabled JavaScript.
- `npm ci` succeeded using unchanged lockfiles; actual local Node was 24.20.0.
  It reported **8 vulnerabilities (2 moderate, 6 high)**. No dependency fix,
  lockfile update or security-advisory dismissal was performed. The existing
  Browserslist stale-data warning remains disclosed.
- `node --check static/js/app-navigation.js` passed. All **21** existing
  `node --test tests/js/test_app_navigation.cjs` cases passed. Navigation JavaScript
  is unchanged.
- Two consecutive builds after template freeze produced identical Tailwind output:
  SHA-256 `a7c650044ad3e2b11df25f8c84e749a2c3f0fd3d1a55edff6f974f7061219cae`.
  An earlier hash comparison during active template editing differed and is not
  recorded as a frozen-source reproducibility failure or PASS. Generated CSS
  adds detected utilities only; shared CSS source/configuration is unchanged.

All **37 changed Python paths**, including both new HR migrations, passed explicit
`ruff format --check --no-cache`; canonical `ruff check . --no-cache` and
`git diff --check` passed. Fresh full-topology PostgreSQL migration bootstrap,
Django system checks and `makemigrations --check --dry-run` passed. The exact
frozen HR-0 ADR, HR-plan sections and Phase 3 umbrella files remain unmodified.

**Current status: verification pending, not independently audited, not accepted,
not published, not canonically adopted.** Full H01–H18/T01–T26 closure and the
single local candidate commit remain conditional on all mandatory results.

### Finite compound-permission and Company-scope completion

`tests/test_hr_permissions.py` adds a fixed, independently written section-10
permission table; expected codes are not copied from runtime `_ACTIONS`.
Its final collected set contains **377** cases. It covers 41 valid public
service/selector variants, each individually missing compound code, all twelve
superuser absent/retired namespace identities, corresponding non-superuser
HTTP read/action GETs, independent POST action admission before form parsing,
conditional Department reads and retained Attendance/Leave transition retries.
Duplicate Leave creation is explicitly a conflict, not an invented successful
create-retry receipt.

Each valid public family is parameterized for the default execution and a new
selected connection to the same disposable synthetic application test database.
The selected call runs with the default connection cursor poisoned, receives
only scalar IDs/context, and closes/removes its task-created alias afterward.
This is SQLite alias evidence until the final PostgreSQL run executes the same
cases; PostgreSQL-only raw locking cannot be certified from SQLite.

The finite Company matrix grants the actor access and HR permissions in **both**
Companies, then proves context confinement rather than relying on lack of the
other Company grant. It includes all six direct/detail/history selector
families; seven payload list/search/choice families; every public mutation
family with foreign parents/references; foreign Branch assignment/transfer;
all ten existing-target action-admission families; a User eligible only in the
other Company; and ten raw malformed Employee/Attendance/Revision/Leave Company
relationship cases through both detail and list. Native rows and Audit are
compared before/after refusals. Employee detail with a real Department omits
both Department identity and related data when DV is absent.

Five persisted interleavings change Employee Branch or ACTIVE eligibility
between candidate discovery and its protected read. New Attendance/Leave
choices and Employee action targets recheck the actually locked row and reject.
The injected raw fixture change also rolls back. These are deterministic
functional interleavings, **not** supported-writer PostgreSQL lock-race evidence.

Actual split SQLite verification, all using the same read-only QA image and
flags described above:

- Initial expanded run: **201 passed, 1 fixture failure in 137.19s**, stopping
  before HTTP setup because transactional flush removed the registry row.
  The fixture now uses the same explicit `get_or_create` pattern as the existing
  HR HTTP fixtures. Those 201 include all 41 default and 41 selected-alias valid
  calls, individual service/selector compound denials and all namespace cases.
- HTTP/Company subset (`-k "corresponding or foreign or raw_malformed or
  user_choices or action_choices or detail_omits or duplicate"`): **121 passed,
  1 test-oracle failure, 208 deselected in 114.90s**. The oracle incorrectly
  demanded PermissionDenied for a foreign reference input; the public contract
  uses a generic ValidationError for invalid relationship ownership. Expected
  exception types are now explicit by operation: unavailable target IDs versus
  invalid reference inputs. Runtime behavior was not modified.
- Final finite remaining subset (`-k "all_mutation or existing_target or
  user_choices or action_choices or raw_malformed or
  action_admission_rechecks"`): **50 passed, 327 deselected in 44.50s**.
- Earlier fixture-development attempts also remain disclosed: **31 passed,
  1 failed in 46.43s** on the invalid Leave-create-retry assumption; **35 passed,
  1 failed in 36.58s** on a rejection fixture missing its required reason.
  Correcting these tests did not change the frozen lifecycle contract.

These split observations are **not** summed or labelled as one complete final
377-case run; the final full PostgreSQL/SQLite collection remains separately
required. In particular, no claim is made that every PostgreSQL RLS attack was
individually run against all sixteen fixed relations merely because the runtime
check enumerates them. Representative executed attacks and the fixed shared
catalog-check algorithm are different evidence categories.

Two final `tests/test_hr_adversarial.py` cases exercise the public
`revise_attendance` call after corrupting an earlier reason or removing an
interior revision (chain 1,3). They require no new revision and no Audit, comparing
all native parent/revision/Audit fields. They were added before final full-suite
collection and are **pending** that run, not covered by the earlier 22-case
adversarial result. Ruff, changed-file format and whitespace checks pass for
both test files. No runtime, schema, migration or authorization-policy change
was made in this bounded test-completion step.

### Subsequent service-placement correction and restart

The first expanded 4,108-case PostgreSQL/SQLite attempts were deliberately
interrupted by the lead before completion. They are **not full-suite PASS**
evidence. A final engineering-instruction review found that the Attendance and
Leave use-case bodies were in sibling files, while AGENTS.md explicitly requires
state-changing use cases in `services.py` or `services/`. Merely re-exporting
those bodies did not satisfy that rule.

The three service implementation files were mechanically organized under
`businessos/modules/hr/services/` (`__init__.py`, `attendance.py`, `leave.py`).
Public `businessos.modules.hr.services` call signatures and business bodies are
unchanged. Relative imports and two test module/patch targets were adjusted;
no contract, model, schema, migration or owner dependency changed. One import
ordering error was reported by Ruff immediately after relocation and corrected
before testing. A new run of flows, adversarial rollback/corruption, actual
nested services and resource-boundary cases then passed **44 tests in 42.56s**
on fresh disposable SQLite. These 44 passes are post-placement evidence,
not a replacement for full final PostgreSQL/SQLite verification.

The final browser session additionally exercised all **29** route families
(the original 27 plus approve/reject) at the three required widths. A real
51-Employee synthetic filtered dataset produced page sizes **50 and 1**,
stable PAGING001–PAGING051 order, preserved `q=PAGING` and status parameters,
working Next/Back/Forward, and identical page-2 results after direct refresh.
Final browser logs at that read-path checkpoint contained no warnings/errors.
Keyboard Tab visibly focused `id_name`; Enter on whitespace-only name produced
the expected server-required error without an HR effect, with no page overflow
at 390px. One browser inspection timed out after this POST; a subsequent fresh
accessibility read independently confirmed that the validation response had
completed. This timeout is not represented as a failed or repeated mutation.

The service relocation follows those visual measurements, so final post-layout
runtime/bootstrap/browser smoke and complete regressions are still required.
No old in-memory browser process is represented as running the relocated source.

### Post-placement verification and final matrix review

The complete post-placement focused PostgreSQL command was:

```text
pytest tests/test_hr_admission.py tests/test_hr_concurrency.py
  tests/test_hr_identity_races.py tests/test_hr_adversarial.py
  tests/test_hr_resource_boundaries.py --tb=short
```

It completed **151 passed in 453.38s**, including the previously disclosed
coordination-watchdog case, all current admission/domain races, the two public
corrupt-chain append refusals, sentinel overflow and clock-rollback cases.
This closes that focused rerun, not the complete H12/full-regression gates.
The frozen contract distinguishes cooperative budgets from stalled-process or
session termination; the earlier SQLSTATE 25P03 is retained as fail-closed
operational session loss, not relabelled successful admission or AuthorityBusy.
There is no production timeout or error-classification change for that event.

Fresh post-placement minimal SQLite and PostgreSQL probes both passed: migrations,
Django checks and drift; all six HR model facts, twelve permissions and five
successful HR audits; no commercial applications/tables; installed services with
HR disabled; HTTP 404 while disabled and 200 after enablement, including Employee
creation. The PostgreSQL database was uniquely named
`hr1_minimal_topology_postlayout`, custody/session checked, dropped and its absence
rechecked. An earlier probe's terminal stdout was unavailable after its session
expired; that attempt is not asserted PASS. The named evidence rerun exited zero
and its actual terminal logs were retrieved. Public services resolve through the
new `hr.services` package.

Canonical Ruff lint and explicit formatting of all **37 changed Python paths**
passed again after placement. Existing JavaScript syntax and all **21** navigation
tests passed. Two further Tailwind builds retained the exact previously recorded
SHA-256. A browser-fixture invocation initially used Docker network-none with a
published localhost port, making it unreachable; only that disposable runner was
recreated with the prior localhost-only binding. The refreshed actual runtime
then completed browser login and Company selection. This was runner configuration,
not a source change or application test PASS for the unreachable attempt.

The final internal traceability review found additional required evidence gaps:
section-14 transfer/Leave, Attendance-revision/approval, overlapping submissions,
competing decisions/cancellation and employment-date races; delayed selector
revocation; and the complete approve/reject self-decision identity matrix.
These are missing mandatory oracles, not independently confirmed runtime defects.
They are being completed in HR-local test files before the final test-set freeze.
The current 4,108-case SQLite run started before these additions; it cannot be
represented as a complete run of the subsequently expanded collection. The full
PostgreSQL run and final expanded SQLite verification remain required. No
candidate commit, independent acceptance, publication or canonical adoption has
occurred.

### Remaining matrix completion: actual failed run and test-oracle corrections

Five HR-local files added 89 cases for the remaining domain/reference races,
delayed selector authorization, self-decision identities, installed API admission
and retired Party eligibility. Collection confirmed **89 tests**. This is
implementation verification, not an independent acceptance review.

The first PostgreSQL command ran only the domain-race, read-authorization and
self-decision files (50 cases). Its actual result was **13 failed, 37 passed in
278.49s**. All sixteen self-decision cases passed. Twelve delayed-selector cases
failed in the test controller's statement-observation oracle: PostgreSQL retained
an earlier `pg_stat_activity` statistics snapshot within the long-lived controller
transaction, while the current blocker function already reported the real lock.
The controller now explicitly calls `pg_stat_clear_snapshot()` on every poll and
requires the expected relation, `FOR UPDATE`, the actual controller blocker and
`Lock` together. Earlier/mismatched SQL is never accepted as a successful oracle.

One domain-race case failed before its winning worker reached Audit; runtime
logs reported `ResourceBudgetExceeded`. Concurrent heavy SQLite verification was
running, but scheduling pressure is only a possible explanation, not an
established root cause. The new test file now propagates completed worker
exceptions instead of hiding them behind an Event assertion. Its coordination
watchdog is fifteen seconds; the genuine PostgreSQL blocker observation and all
production two-second admission/runtime budgets remain unchanged. There is no
retry loop or weakened success condition. Both test-only helper corrections
passed locked Ruff lint/format; their PostgreSQL execution remains pending.

The temporary scheduled continuation was paused when that failed run completed;
no automatic commit is permitted on those results. The active owner-requested
completion work retains the failure evidence and requires successful verification
of the final test set before any local candidate commit.

The refreshed post-placement browser runtime completed Employee, Attendance and
Leave lists plus Employee creation at 390, 768 and 1280px. Every measured document
width was at or below its viewport (mobile lists 380/390, tablet lists 758/768,
desktop lists 1270/1280; creation 380/390, 768/768, 1280/1280). Actual application
warning/error logs were empty. The browser-control tool separately reported
external telemetry HTTP 403s; these were not localhost application console
errors. Temporary viewport overrides were reset. These twelve smoke checks
complement, rather than replace, the earlier 29-route responsive and mutation
evidence on the unchanged HR presentation files.

The complete earlier 4,108-case post-placement SQLite run finished **1 failed,
2,602 passed, 1,505 classified PostgreSQL-only skips in 1,809.86s**. Its single
failure was the new Company list-isolation test's `isinstance(row, dict)` oracle:
`person_choices` intentionally returns immutable `MappingProxyType` projections,
so the assertion attempted `.id` on a mapping. The test now uses the standard
`collections.abc.Mapping` interface. No selector or other runtime change was
needed; exact foreign-ID exclusion and the search assertions are retained.
This failed historical run is not represented as full-suite PASS. Final expanded
PostgreSQL and SQLite suites remain mandatory.

The same final matrix review identified missing H02/H08 current-versus-frozen
Branch evidence. Eight new `test_hr_branch_scope.py` cases use null snapshots,
Branch A facts, then Employee transfer to Branch B. They cover current Employee
scope, frozen Attendance/Leave/history/list scope, null exclusion, original
Attendance retry/correction after Company timezone change, Leave edit/submit/
cancel/receipt scope and inactive historical Branch behavior through a valid
Company context. All denied calls compare six HR models and Audit unchanged.
Collection (eight cases), locked Ruff/format and whitespace passed; actual
functional execution is still pending. The six additional test files total
97 cases beyond the earlier collection, and the corrected Company-isolation
oracle does not change the case count.

### Final local traceability and immutable verification input

After the test-controller corrections, the exact same initial 89-case focused
selection completed on disposable PostgreSQL: **89 passed in 304.96s**. This
includes all twelve delayed-selector authority cases and the earlier resource-
budget domain failure, without changing production budgets or retrying inside
tests. The retained named runner `hr1-final-gap-recheck-pg-b36cdba` exited zero.
The later sixteen additional cases and corrected fourteen-case Company-list
oracle are a separate pending thirty-case selection, not included in those 89.

That separate selection then completed **30 passed in 101.70s** on PostgreSQL:
eight current/frozen Branch cases, six native-effect/Audit rollback cases, two
long create/create winners and fourteen Company list/search/choice cases. Actual
final whole-project collection is **4,213 tests** (15.52s collection), not the
earlier 4,108. The final full PostgreSQL run now uses the uniquely created,
custody-marked `hr1_final_regression` database in the same isolated task server;
pytest creates its distinct synthetic test database. The retained runner is
`hr1-final-full-pg-4213-b36cdba`, with fresh migration, full pytest, Ruff, Django
check and drift in one fail-on-first-error command chain. No competing full
SQLite runner remains active. Final full-suite results are still pending.
After those focused failures were resolved and both selections were green, the
lead resumed the owner's previously authorized temporary ten-minute follow-up.
It may finish the remaining sequential local verification and create the one
authorized local candidate commit only after every gate passes. It must stop
on a new failure or completion; publication and `main` movement remain forbidden.

Two long create/create race cases (73-hour interval versus an inner one-hour
interval, both winner orders) and six Employee/LeaveType native-effect Audit
failure cases close the final literal H08/H14 proof gaps. The latter inspect
the persisted effect inside the failing transaction, then compare all six HR
models and Audit after complete rollback. They change only HR-local tests.
Canonical Ruff and explicit formatting of all **44 changed Python files**,
including both new migrations, passed. Final test execution remains pending.

The following table is coverage traceability, **not a collective PASS**. `tests/`
is the prefix for the named test files. Actual final suite results are recorded
separately; independent audit and hosted candidate CI remain later gates.

| ID | Concrete local implementation oracle |
| --- | --- |
| H01 | `test_hr_permissions.py`: every foreign direct/list/search/choice/mutation/action family and malformed native relationships; `test_hr_http.py`: stale Company/Branch POSTs without native/Audit effects. |
| H02 | `test_hr_branch_scope.py`: current Employee B versus frozen Attendance/Leave A, null/inactive history, Company-wide setup and scoped receipts; transfer races in concurrency/domain tests. |
| H03 | Model/identity-race tests: retained Party/number/User identity; adversarial exact five-field Party projection with no contacts/addresses; installation tests distinguish current ineligible Party from historical resolution. |
| H04 | Services/models: normalization, bounds, no reuse and ordinals; identity/reference races: actual unique winners, owner Party/Department/LeaveType/Branch retirement in both orders. |
| H05 | Independent finite compound table in permission tests, each missing code, non-superuser happy paths and GET/POST, superuser absent/retired identities; self-decision suite covers requester/current/frozen beneficiary and retry. |
| H06 | Model registration preserves enablement/retirement and fixed twelve migration strings; HTTP and installation tests prove missing/disabled HTTP 404 while installed APIs still require RBAC. |
| H07 | Permission valid-call matrix on selected alias with default cursor poisoned; admission PostgreSQL alias/bootstrap and switch refusal; nested services prove same outer transaction and rollback. |
| H08 | Flows, long domain races, Branch receipts, actual 1,000+1 sentinel and EXPLAIN; history/adversarial VOID/reinstate; no temporal lookback/duration ceiling. |
| H09 | Civil-time TZif/ZoneInfo/SQL integer-offset parity, both folds/gaps, 25/23-hour days, midnight geometry, footer rules and extreme boundaries; HTTP trusted originals; noncausal clock rollback. |
| H10 | History legal/invalid full chains, malformed earlier facts and bounded materialization; public append after corruption refuses; model guards reject direct/bulk/upsert/delete/history rewrite. |
| H11 | Flows/civil-time: inclusive 1/365/366/367/longer Leave, frozen windows, leap/DST/extreme boundaries, lifecycle and historical receipts; self-decision and retired-reference rules. |
| H12 | T01–T26 mapping above plus actual identity/reference/domain races; delayed public selector revocation in read-authorization tests. Expected isolated negative controls are not current-protocol deadlocks. |
| H13 | Admission tests: complete inactive-inclusive authority, exact relation modes/native SQL subset, NOWAIT rollback, superuser namespace, overflow/budgets/cleanup and implicit relation negative controls; fixed nested anchors. |
| H14 | Exact field/transition actions and no-op/retry counts; all Attendance/Leave effect Audit failures; six Employee/LeaveType rollback cases; caught nested failure poisons the complete outer operation. |
| H15 | HTTP/permission tests: exact GET/POST admission, CSRF, stale forms, escaped text/trusted originals, independent bounded choices and query preservation; real pagination/Back/Forward/refresh and script-free fallback evidence. |
| H16 | Actual 29-route 390/768/1280 maximum-content browser record, local table scrolling, layout corrections, focus/Tab/Enter/errors and normal CSRF submission; refreshed post-placement twelve-surface smoke. |
| H17 | Fresh full PostgreSQL bootstrap plus actual minimal Core/Party/HR SQLite/PostgreSQL installations, six facts/twelve permissions/five Audits, missing commercial owners and disabled/enabled HTTP; task databases removed. |
| H18 | Final full PostgreSQL/SQLite and classified skips remain required; Ruff/all-changed-file formatting, Django/drift/architecture, JavaScript 21 tests, npm/Tailwind/CSS, protected diff/docs/fingerprints. Independent audit and hosted CI are not performed by this local task. |

Frozen verification inventory: **55 code/test/template/build files**, excluding
only this implementation evidence document. These hashes identify the exact
input for the final expanded verification, not an approved operational artifact.
The prior 48-file freeze differs only in the disclosed Mapping test-oracle
correction; seven bounded HR test files are additional. No runtime file changed
between those two freezes.

```text
029237c4b764f5fe7d07fe19d72f3bbd5f43d6ed6b14d10b33ff5e2058756919  businessos/modules/hr/__init__.py
482046270fb97fefffe8a07a3bf2205e8c8d1c6598531772171eff3c71de1547  businessos/modules/hr/admission.py
b2654ecded6f79c5e9c42778a2e9cb44cf24090acf25237ce0846cfeebefba6b  businessos/modules/hr/apps.py
693fdc16926803dd671c8792c41340e063cdf8db93ff3d8a958f22c10ca3f1c6  businessos/modules/hr/civil_time.py
ecb9df9a332ef03700659060e08a29acab14b86d9e991169576afce715f4b471  businessos/modules/hr/conflicts.py
e7e221a7a4f7ad28d614a72ef622eb62aa39ef78b4c0643cc7d71fadf89f4f84  businessos/modules/hr/domain.py
5a9588c5553de07eacfeb23498a9a2e38b742361d3905867eabecedc9dc515bb  businessos/modules/hr/forms.py
cb1ee11c9748d71cf0734abdb98971f0de03aae61c570f84f1067df2bc7ba691  businessos/modules/hr/history.py
71dbdd47d589cda99093418400d82255bda33579889360a4cea3aa2517442647  businessos/modules/hr/manifest.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  businessos/modules/hr/migrations/__init__.py
2de582ba9d1d2c598fa3b3d5f047d751d9e1397614e29343695448b9a12b648f  businessos/modules/hr/migrations/0001_initial.py
e0087a18ec74214d5d40be727d4ae00f171203f6ea643db88709901976b3a63b  businessos/modules/hr/migrations/0002_register_manifest.py
e037a789d76903d02cec9d9c033fa026accc8e068b1ebdad397badce129b7f00  businessos/modules/hr/models.py
875c8a01440b4cd23f5b2b9dc3c1a26d94d95a1e517cb6ff9908fe83d28fe7fe  businessos/modules/hr/persistence.py
e907c9c1fc6e77b8b74f9f236fca3b59f4d5a833e69485833942a3ef68d80449  businessos/modules/hr/selectors.py
7d5669a33ae24bfb44b051a419f74c484e8b2a6451776ad652124c8453538815  businessos/modules/hr/services/__init__.py
863e8f921f51b415f1ad3ce820387942c180929d2f84ea849ccbf7b8142deffe  businessos/modules/hr/services/attendance.py
9e222b3c12c67bb1c21f19870b2e1ad70e469fa260e47ed4f5b311e44862015a  businessos/modules/hr/services/leave.py
0cfdb01050aa658929cbdf7e4ada6e5122d1e9bbfa466d64901c167536cc4785  businessos/modules/hr/support.py
7571bd0ec3bdfd92e708c1b3624a3eed30b3d290cfda23d89a66df111c6fefba  businessos/modules/hr/urls.py
243d2f3132f55dd0f68ef71b5c72edfdfe122b5bdc360c1845d112c42018109c  businessos/modules/hr/views.py
7542df586219cdfcceb496c50a9c9a3e49e4d951653e2b0f2107514e1adcbf72  config/settings/base.py
d11769617ed3eb6d2ace3b0cf499e7175ae89ca02758ff9e618f42d29b23c185  config/urls.py
a7c650044ad3e2b11df25f8c84e749a2c3f0fd3d1a55edff6f974f7061219cae  static/css/tailwind.css
082f69f44d123bf736b63175beb3c611e0da9c6c3ee905805ee1ba7ccd57b303  templates/components/header.html
92ae30232b4577f428da0418a3d84ba5529e305cc8e7cd29c5b225199151c2a4  templates/components/sidebar.html
ef2ed05f3c9d4df622a4b4e7a8c6e4517725658660973ccbcb8201be725b72a4  templates/core/home.html
7450c0cc9e80390f3e588e7bd2fdfb34122c8f6a89bb068e0ecd31f9eff76fa6  templates/hr/detail.html
6da7e5dc5c6b07a11bc02638052f63d548172b51582373690cd85d43f9bd1534  templates/hr/error.html
f593ecdb1690edd5b5ba6744e78cd9efd4b9525e98634d1507ff38e99f393390  templates/hr/form.html
91bb65d0b40023902924c2992658721099209a31f89e9bbe5ff1d48a2c386a49  templates/hr/list.html
425de6402f1892f37a7d4939dcfb3e8b8110dda1039074ef393c5f40d54b5ca6  templates/hr/menu.html
753d24d9685e4b6975554dfcf71552d9b79185e3ecf05473e17f47a58f0c9f94  templates/hr/navigation.html
c3a0ddb2213a0eeb30dece2e24eb0ff0950388c72fe14fa81c279abc6ce7ecbc  templates/hr/revisions.html
35b7457e301ddbee6ecc4edd618bab49842127355faeff7c8ee58d09cce77aff  tests/test_database_foundation.py
73f176471763dda18aa4e4090f16344846dcb7f4d3e366b82a6dd6af232e6d10  tests/test_hr_admission.py
a1a0123311dd13787c910dc840ba046ddc6f4b6f352e9b7a2fb65a20797f4089  tests/test_hr_adversarial.py
3d42ee3bfa6a7cd906903f34289eea838c44f9f249741738f4370572b5f7c328  tests/test_hr_branch_scope.py
085a268b2c3b3e8cf94a22c5026b834452a563761de7b3e90d2810f34e0c675a  tests/test_hr_civil_time.py
bb190b1fd969f4ca55b9a8c5715d5090baa4b21e022dee5ebb33773225a5b6cc  tests/test_hr_concurrency.py
253adadb399634074462650f56149133fc21e10a34ddde91e7cbcaf017ab5972  tests/test_hr_domain_races.py
d0a5f2c2c9845374b2f7784867fbbf77d73e83c91ef362a75df18cdd770f873d  tests/test_hr_flows.py
4784da7e7a5b3e82ba6a19e50bb144ef0476dcdc7efef00fa7991429daec2e11  tests/test_hr_history.py
549eb44e11074ce1661be1ee85c55e93723df2928499ae7a781f8aa32d81d6cc  tests/test_hr_http.py
b5bb1f8aed0b5a3c671e0e0e30d7bf7b19680c92145b734c0ec5b9500c7a9379  tests/test_hr_identity_races.py
5363f19619ced314e05fac666db12ea24e911eff61bdfd339dc2f140ebb23062  tests/test_hr_installation_contract.py
243bc190879bf054c88bed689b3cef7f0805246c79f39d0bced0e8203ce044c9  tests/test_hr_models.py
a64859f9ce6a7386972d243b5f8e09b6115d5adc35867ac25b04e53fc7139067  tests/test_hr_nested_services.py
f9a558608d5c16144e310319bff20ad1c67daec37949bea4dbc2b2875cabbcc9  tests/test_hr_permissions.py
f2424a9cac5ee7bd4b3c1816411df32427ef6f486a392eba7adb7d4311d5e9ed  tests/test_hr_read_authorization.py
f9dcfb349f2c14ef3debbbfa3de5d190afcfe1a2d9b1a45a3f771ea7cc6b1ad4  tests/test_hr_reference_races.py
89128d1a25eb8359399ba49e04cf9ce336a89f9d9ad72eda86d242ffa2521f25  tests/test_hr_resource_boundaries.py
1559e5afece27117c60c5b4d647f5964e15e6e4feb5bcd42f99dc163886ee71f  tests/test_hr_self_decisions.py
767bca9a6699aaff32212845d1fbf2d41bb67713b3293729449a00db52e78f3a  tests/test_hr_services.py
fb18067d41b1e1042fd9e6d39d72ea0453c5803c0fd5c2e335b15d3b0127d0d3  tests/test_hr_setup_rollback.py
```

## Completed local verification

This supersedes the earlier pending local-verification statements, not their
historical failure evidence. Date: 2026-10-15. All 55 frozen implementation,
test, template and generated-build fingerprints above remained unchanged during
the final complete suites and final checks. Only this evidence document was
updated afterward. The candidate remains a local implementation checkpoint for
fresh independent audit, not an accepted or operational artifact.

### Actual final full-suite results

| Gate | Actual result |
| --- | --- |
| Full PostgreSQL 17 regression | **4,213 passed, zero skips, 4,688.17s**; runner exited **0** |
| Supported SQLite regression | **2,652 passed, 1,561 classified skips, 1,056.11s**; runner exited **0**; all 4,213 collected cases accounted for |
| Fresh full-topology PostgreSQL migration bootstrap | All migrations, including additive HR `0001_initial` and `0002_register_manifest`, applied successfully before full pytest |
| Canonical Ruff | `ruff check . --no-cache`: **PASS**, including after the PostgreSQL suite and final source-frozen verification |
| Explicit changed-Python formatting | `ruff format --check --no-cache` with all **44** explicit changed Python paths, including both HR migrations: **44 files already formatted** |
| Django system check | **Zero issues** after full PostgreSQL regression |
| Migration drift | `python manage.py makemigrations --check --dry-run`: **No changes detected** |
| JavaScript syntax | `node --check static/js/app-navigation.js`: **PASS** |
| Existing navigation JavaScript suite | `node --test tests/js/test_app_navigation.cjs`: **21 passed**, no skips/failures |
| Final Tailwind reproducibility | Two further `npm run build:css` executions: **PASS**; both retained exact CSS SHA-256 recorded above |
| Protected diff, fingerprints and whitespace | All 55 hashes match; exactly 56 authorized candidate paths; protected owners/contracts/existing migrations unchanged; `git diff --check`: **PASS** |

The PostgreSQL runner was `hr1-final-full-pg-4213-b36cdba`, immutable container
identity `383320a022382b53a1372373e00f67bc532b7637ae36ca3c241436b459b374e2`.
Its source was read-only, with locked Python **3.13.16**, Django **5.2.17**,
Ruff **0.16.7** and all three existing opt-in commercial integration apps enabled.
It used the new custody-marked `hr1_final_regression` application database and
separate pytest database in the task-only isolated PostgreSQL server. The exact
successful command chain was:

```text
python manage.py migrate --noinput
pytest --maxfail=1 --tb=short -rs -p no:cacheprovider
ruff check . --no-cache
python manage.py check
python manage.py makemigrations --check --dry-run
```

The SQLite runner was `hr1-final-full-sqlite-4213-b36cdba`, immutable identity
`8d37bd5beaabe6213f956021f394049c5375784cdb2b631fcf47e7b9041745f5`.
It used `config.settings.test`, read-only source, network-none, the same locked
image and integration opt-ins, and the same pytest command above. These are
complete final-collection results, not sums of the earlier focused selections.

Every SQLite skip was read from the actual `-rs` report and classified; no skip
was used as PostgreSQL proof:

| Backend-specific skip classification | Count |
| --- | ---: |
| PostgreSQL catalog/schema/RLS/admission | 808 |
| PostgreSQL real concurrency/lock observations | 733 |
| Fresh PostgreSQL topology/bootstrap | 13 |
| PostgreSQL-exact financial arithmetic | 7 |
| Total | **1,561** |

All H01-H18 **local implementation evidence** is now executed as mapped above,
including responsive browser and minimum-topology probes. All T01-T26 actual
PostgreSQL implementation oracles passed in the complete run. The deliberately
isolated rejected-protocol deadlock negative controls remain expected test
outcomes; no unexpected supported-surface deadlock is accepted. The missing
Branch-scope, long create/create, delayed selector revocation, self-decision and
Employee/setup rollback oracles are included in the final complete collection.
H18's independent audit and separate exact-head hosted CI are **future gates**,
not a claim made by these local results.

### Final integrity, custody and remaining boundaries

The exact HR-0 base, local `main`, `origin/main` and HR-0 contract branch remained
`b36cdba91654e6a583735d67f7f6cf27a835003e`. A final read-only live
`git ls-remote --heads` independently returned that same SHA for remote `main`
and `phase3a-hr-contract`. The held local Phase 4 proposal remained exactly
`735e1bea13bc58fa71d430163422139d5c0f2363`; it was not published or adopted.
All accepted HR-0 contracts, Core, other business owners, source lockfiles and
existing migrations are unchanged. The only final post-freeze edit is this
implementation-run evidence record.

After final logs were read, nine exact task-created container identities,
images and host mounts were checked. Only the known HR proof/focused/final
runners, two synthetic browser fixtures and tmpfs-backed isolated HR PostgreSQL
server were stopped where necessary and removed. The server inventory before
cleanup contained only the two task application databases and PostgreSQL
technical databases, with **zero other client sessions**. Final pytest test
databases were already absent. A final inventory confirmed no `hr1-` task
container remains. Existing demos, other projects' containers and repositories
were not modified. Removed disposable databases/output are not a retained
operational artifact; the locked QA image was not deleted.

Limitations remain explicit: this is local implementation evidence, not fresh
independent review, hosted CI, acceptance, canonical adoption, Phase 3 completion
or production readiness. Browser evidence is the actual recorded 29-route
responsive run plus post-placement smoke, not a newly invented rerun. The
script-free fixture is not a claim of browser-wide JavaScript disabling.
Timezone support remains fail-closed for unsupported TZif/geometry/parity; the
486-zone probe is not universal platform certification. Test deadlines do not
establish production latency or starvation guarantees. Local frontend tooling
was Node **24.20.0** / npm **11.19.0**; CI's configured Node version was not
changed. Existing npm findings (**8: 2 moderate, 6 high**) and Browserslist's
stale-data warning remain disclosed and unmodified.

All required local gates permit creation of the owner's **one** local candidate
commit, `feat(hr): implement Phase 3A HR foundation`, containing exactly the
55 frozen files plus this record. Its actual Git SHA is reported by the task;
the document does not invent or self-reference its containing commit hash.
Fresh independent audit and later publication/adoption require separate gates.
No push, PR, merge, tag, `main` update or next-milestone work is authorized.
## HR1-AUD-1 targeted corrective record — 2026-10-16

This is the current corrective checkpoint; the completed original implementation
record above remains historical. Original candidate
`e6b72896e10471463b8b6b280fbccfc524d7cc42` remains immutable above canonical
HR-0 `b36cdba91654e6a583735d67f7f6cf27a835003e`. The supplied fresh independent
HR1-AUD-1 verdict is **REVISE / Readiness B**, P0 0 / P1 0 / **P2 4** / P3 0.
The complete external report, sections A–AJ, was read before correction and
is preserved unchanged. Its four exact findings are HR1-AUD-001–004 below.
Original 4,213-test results are implementation-run evidence, not independent
approval. This corrective work does not manufacture independent re-audit.

### Integrity and bounded authority

Initial working tree was clean on `phase3a-hr1-implementation`, HEAD exactly
the original candidate and parent/main/origin-main exactly the HR-0 base.
Read-only live `git ls-remote --heads origin main phase3a-hr1-implementation`
subsequently succeeded: main equals HR-0 and remote HR-1 is absent. The first
sandbox network failure (`getaddrinfo() thread failed to start`) is retained
as an unavailable attempt, not implementation evidence. No fetch/ref mutation
was necessary. Held Phase 4 remains
`735e1bea13bc58fa71d430163422139d5c0f2363`, on
`phase4-domain-foundations-architecture`; no Phase 4 files or decisions changed.

Only HR-local runtime corrections, their focused regressions/fixture adapters,
and this appended evidence are authorized. No schema/migration, Core, other
owner, settings, manifest, frozen ADR 0017/0018, accepted HR-plan section,
frontend/template or ordinary CRUD change is introduced by this correction.

### Actual pre-fix reproductions

All runs used unchanged pinned `hr1-local-qa:b36cdba`, read-only source,
`config.settings.test`, network-none, new disposable synthetic SQLite
fixtures and all three existing commercial-integration opt-ins. New tests
were executed before the corresponding production fixes; assertions were not
changed to accept defective behavior.

| Finding | Exact executed red command suffix and result |
| --- | --- |
| HR1-AUD-001 — P2 | `pytest tests/test_hr_audit_history.py -q --tb=short -p no:cacheprovider`: **35 failed / 2 passed, 21.45s**. Both extreme retained-boundary certificates, public reads/retries, earlier-row appends and eligibility lacked the required rejection. Current corrupt VOID/conflict paths sometimes failed only later on a different validation, which did not establish complete-chain certification; the expected retained-fact rejection assertion failed. Two adjacent-valid controls passed. |
| HR1-AUD-002 — P2 | `pytest tests/test_hr_audit_persistence.py -q --tb=short -p no:cacheprovider`: **6 failed, 15.73s**, all DID NOT RAISE. Employee number/Party/Company, retired setup code, submitted Leave content/receipt and cross-Company orphan Attendance bypasses reproduced. |
| HR1-AUD-003 — P2 | New declared-but-unacquired target case DID NOT RAISE before nested mutation. It ran together with the validation file below: **29 failed / 16 passed, 29.55s**, one failure belonging to this anchor case. |
| HR1-AUD-004 — P2 | The same command, `pytest tests/test_hr_audit_acquired.py tests/test_hr_audit_validation.py -q --tb=short -p no:cacheprovider`, had **28 validation-file failures / 16 passes**: caught early errors committed prior work, including selected-alias and combined Leave/Department cases. Direct failures and already-inside-boundary controls passed. |

These are fresh corrective implementation executions, not a rerun or alteration
of the external independent audit. PostgreSQL fail-closed and actual-lock
regressions are separate post-fix gates below; no PostgreSQL red result is
invented.

### Implemented correction and interaction boundaries

- **HR1-AUD-001:** every-row SQL now counts exact representable first and
  exclusive-final midnight candidates over segments compiled from the SAME
  verified TZif/ZoneInfo bytes. Exactly one candidate is required, and the
  exclusive Date must be constructible. A mathematically sufficient three-day
  UTC candidate halo includes offsets strictly below one day plus boundary
  displacement; it is rule coverage, not a duration/lookback limit. Both native
  extreme cases, earlier corrupt rows and a synthetic second midnight beyond
  the former halo have independent regressions. Scalar/correlated complete-chain
  checks stay bounded in materialization; no fallback to older ACTIVE history.
- **HR1-AUD-002:** fixed named owner primitives bind model, Company, target,
  permissions, alias and actual protected references to the active transaction.
  Generic insert/write helpers reject absent bindings. Before an update, every
  concrete field is compared with persisted identity/revision; only the exact
  operation-specific mutable columns may differ. Persisted lifecycle validates
  new Leave receipt families; existing content/receipts cannot be rewritten.
  New User FKs require the protected set; original actors equal the admitted
  actor. Supported edits/end/transfer/draft/lifecycle behavior remains legal.
- **HR1-AUD-003:** declarations, actual domain acquisition, new Attendance
  reservations and complete authority admission are distinct. A single HR-local
  acquisition helper performs scoped ordered SQL, recording locks only after
  successful exact coverage. Authorization rejects unacquired declarations.
  After authority, nested reads reuse held protection without a new FOR UPDATE.
  Unknown savepoint/transaction/connection/alias and completed state reject.
  User/Role/Permission acquired sets are recorded only after successful locks;
  any caught admission failure poisons the outer operation. Final native Core
  guards remain unchanged. No global EXCLUSIVE gate is introduced.
- New-row registration is not a claimed-lock bypass: it requires exact-object,
  immediate post-INSERT attestation inside the active named primitive. Existing
  loaded rows cannot be promoted. A new Attendance must complete revision 1
  inside the same outer unit; caller-forged completion cannot clear that duty.
- **HR1-AUD-004:** existing Attendance normalizers and Employee unknown-field
  rejection now execute inside their existing `hr_operation` boundary. A caught
  nested error poisons all prior effects/Audits/receipts. No global transaction
  helper or Leave lifecycle redesign was needed.

The exact corrections span `admission.py`, `civil_time.py`, `conflicts.py`,
`history.py`, `persistence.py`, `selectors.py`, `services/__init__.py`,
`services/attendance.py`, and `support.py`, all under the HR module.
Four new `test_hr_audit_*.py` files independently reproduce/guard the findings.
Existing `test_hr_admission.py` and `test_hr_nested_services.py` positive
nesting fixtures now acquire real rows, rather than treating fake/declared UUIDs
as locks. `test_hr_history.py` explicitly uses fixture-only base insertion for
corrupt-history/catalog proofs. `test_hr_models.py` intrinsic tests enter real
owner admission where necessary, retaining raw CHECK and ordinary ORM-guard
oracles. No original acceptance case was deleted.

An internal cross-finding diff review identified and closed the false-created-row
and savepoint-proof gaps before final verification. This was implementation
self-review, NOT independent approval.

### Intermediate post-fix results and retained interruptions

- The first combined history run stopped at an existing history fixture calling
  a private create helper in plain atomic scope: **1 setup error, 18.79s**.
  That fixture was explicitly adapted as described above.
- A combined legitimate-behavior run then reached **214 passed / 1 failed,
  56.51s**. Over-broad transaction test marking had flushed the registry row
  assumed by an unchanged manifest assertion. Only tests requiring real owner
  admission retain transaction marking; ordinary registry/raw-CHECK tests keep
  their original marking. No registration assertion was weakened.
- Initial PostgreSQL critical run: **327 passed, 384.85s**. Subsequent final
  admission-state/insert-attestation regressions require a fresh run; this
  intermediate result is not substituted for final frozen-source evidence.
- Combined SQLite functional run: **539 passed / 6 classified skips, 79.05s**:
  five PostgreSQL catalog/RLS/identity proofs and one real held-row lock proof.
  Later authority failure-state strengthening is not claimed covered by that
  earlier process.
- Canonical Ruff initially reported two import-layout issues. Those were fixed
  nonsemantically; the subsequent canonical check passed. No unrelated file
  was mass-formatted.

### Final frozen-input verification gates — FAILED / STOPPED

Final focused PostgreSQL runner: `hr1-aud1-final-focused-pg`,
ID `bfb2c046056555b6bf6151fcc61f1a0d14df8a5163438c655d91b3b999af7030`.
It covers all four new regression files plus admission, nested services, history,
civil-time, models, services and flows. Final full PostgreSQL, supported SQLite,
H01–H18/T01–T26 revalidation, bootstrap/drift, explicit changed-Python formatting,
frontend reproducibility and targeted browser verification remain mandatory.
No corrective commit is permitted until every required gate passes.

The task-only PostgreSQL server is `hr1-aud1-corrective-pg-e6b7289`,
ID `08830823c9c53f97b77bd41b773a50747573cf5d4ca498ba6fcd8c81b0182065`,
PostgreSQL17-alpine, network-none/tmpfs PGDATA/no ports/no data mounts. Its new
`hr1_aud1_corrective` application database has an explicit synthetic custody
comment. Pytest uses a separate disposable test database; workers close their
connections. No demo/customer database or unrelated Ecommerce container is used.

The owner separately authorized a temporary ten-minute scheduled continuation
for this corrective verification and the one conditional local commit. It
must stop on failure/completion, with no push or main change. Status at launch:
**CORRECTIVE VERIFICATION PENDING / NOT AUDIT-READY**. Independent corrective
re-audit, formal acceptance, hosted CI and adoption have NOT occurred.

### Corrective verification input SHA-256

These are actual filesystem bytes of all 59 code/test/template/build inputs:
the original 55 plus four new test files. The prior 55-value inventory remains
historical above. This evolving evidence document is excluded from self-hashing.
Any further source/test change invalidates the frozen-run attribution until
fresh verification. Fingerprints are integrity evidence, not correctness proof.

```text
029237c4b764f5fe7d07fe19d72f3bbd5f43d6ed6b14d10b33ff5e2058756919  businessos/modules/hr/__init__.py
78bc17826f2dadabec1de9ef8c52a64ebf3056945fc094923152fba2a01b2f1f  businessos/modules/hr/admission.py
b2654ecded6f79c5e9c42778a2e9cb44cf24090acf25237ce0846cfeebefba6b  businessos/modules/hr/apps.py
f29a74c79d8fba13f2f413ffc593661500055c6162a816dabab69e0317f8d1c1  businessos/modules/hr/civil_time.py
37ce3ce0b956345c7aca1d214ecbba296328d8819a81104ea356b115a8bfc8f1  businessos/modules/hr/conflicts.py
e7e221a7a4f7ad28d614a72ef622eb62aa39ef78b4c0643cc7d71fadf89f4f84  businessos/modules/hr/domain.py
5a9588c5553de07eacfeb23498a9a2e38b742361d3905867eabecedc9dc515bb  businessos/modules/hr/forms.py
a0285e935e08dc91f7daaee85156ea8623d5c5733d2f44ab35c2bb5d68f611b2  businessos/modules/hr/history.py
71dbdd47d589cda99093418400d82255bda33579889360a4cea3aa2517442647  businessos/modules/hr/manifest.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  businessos/modules/hr/migrations/__init__.py
2de582ba9d1d2c598fa3b3d5f047d751d9e1397614e29343695448b9a12b648f  businessos/modules/hr/migrations/0001_initial.py
e0087a18ec74214d5d40be727d4ae00f171203f6ea643db88709901976b3a63b  businessos/modules/hr/migrations/0002_register_manifest.py
e037a789d76903d02cec9d9c033fa026accc8e068b1ebdad397badce129b7f00  businessos/modules/hr/models.py
4095f53d6e63d5a2f0ba67f76bb86667b1fe4dddc71f8612fb9e482d08753ba7  businessos/modules/hr/persistence.py
b101a75d1229ecb42bbe85570c46a3e0bda76dfdaf8673f564cee32508ee88db  businessos/modules/hr/selectors.py
6b20c89a82251aa14f9ca9ab9a1695ed09bfd8294295f2e2a31b8dd775802ba3  businessos/modules/hr/services/__init__.py
c37622f7fa866d36f247347d5c580abb25d35158fde78fb36e82f336ae864d41  businessos/modules/hr/services/attendance.py
9e222b3c12c67bb1c21f19870b2e1ad70e469fa260e47ed4f5b311e44862015a  businessos/modules/hr/services/leave.py
d69f9fb11f48e756ee2d427611d8a42e235585b2fcafa72daad1a4a959a850a6  businessos/modules/hr/support.py
7571bd0ec3bdfd92e708c1b3624a3eed30b3d290cfda23d89a66df111c6fefba  businessos/modules/hr/urls.py
243d2f3132f55dd0f68ef71b5c72edfdfe122b5bdc360c1845d112c42018109c  businessos/modules/hr/views.py
7542df586219cdfcceb496c50a9c9a3e49e4d951653e2b0f2107514e1adcbf72  config/settings/base.py
d11769617ed3eb6d2ace3b0cf499e7175ae89ca02758ff9e618f42d29b23c185  config/urls.py
a7c650044ad3e2b11df25f8c84e749a2c3f0fd3d1a55edff6f974f7061219cae  static/css/tailwind.css
082f69f44d123bf736b63175beb3c611e0da9c6c3ee905805ee1ba7ccd57b303  templates/components/header.html
92ae30232b4577f428da0418a3d84ba5529e305cc8e7cd29c5b225199151c2a4  templates/components/sidebar.html
ef2ed05f3c9d4df622a4b4e7a8c6e4517725658660973ccbcb8201be725b72a4  templates/core/home.html
7450c0cc9e80390f3e588e7bd2fdfb34122c8f6a89bb068e0ecd31f9eff76fa6  templates/hr/detail.html
6da7e5dc5c6b07a11bc02638052f63d548172b51582373690cd85d43f9bd1534  templates/hr/error.html
f593ecdb1690edd5b5ba6744e78cd9efd4b9525e98634d1507ff38e99f393390  templates/hr/form.html
91bb65d0b40023902924c2992658721099209a31f89e9bbe5ff1d48a2c386a49  templates/hr/list.html
425de6402f1892f37a7d4939dcfb3e8b8110dda1039074ef393c5f40d54b5ca6  templates/hr/menu.html
753d24d9685e4b6975554dfcf71552d9b79185e3ecf05473e17f47a58f0c9f94  templates/hr/navigation.html
c3a0ddb2213a0eeb30dece2e24eb0ff0950388c72fe14fa81c279abc6ce7ecbc  templates/hr/revisions.html
35b7457e301ddbee6ecc4edd618bab49842127355faeff7c8ee58d09cce77aff  tests/test_database_foundation.py
420c74d6edf38deba726c5f9bd8f4f61bfd2222fdd6f25d54c13cf67ac1e3267  tests/test_hr_admission.py
a1a0123311dd13787c910dc840ba046ddc6f4b6f352e9b7a2fb65a20797f4089  tests/test_hr_adversarial.py
e9659c5e208a02a0125f8cd5d549e83b1cf1fb9fef1e84f4848798290d718a85  tests/test_hr_audit_acquired.py
874a3c98c5f0b0ab3194252cd4d04a5bb4f9bbaacec9ef131b4882ae8194bfcf  tests/test_hr_audit_history.py
1a02903c4fe1f711591e6a361b7a7e03ff4065785dc4caed41c58e94a6dcce96  tests/test_hr_audit_persistence.py
023cbdc7824c8b88e9004d377088e7b55b4bc4d29f66d5aaa7e92c940561025d  tests/test_hr_audit_validation.py
3d42ee3bfa6a7cd906903f34289eea838c44f9f249741738f4370572b5f7c328  tests/test_hr_branch_scope.py
085a268b2c3b3e8cf94a22c5026b834452a563761de7b3e90d2810f34e0c675a  tests/test_hr_civil_time.py
bb190b1fd969f4ca55b9a8c5715d5090baa4b21e022dee5ebb33773225a5b6cc  tests/test_hr_concurrency.py
253adadb399634074462650f56149133fc21e10a34ddde91e7cbcaf017ab5972  tests/test_hr_domain_races.py
d0a5f2c2c9845374b2f7784867fbbf77d73e83c91ef362a75df18cdd770f873d  tests/test_hr_flows.py
5404679b199c5b4423893413065e9e81cb0a884fc352eaacdb44ff91dffee91d  tests/test_hr_history.py
549eb44e11074ce1661be1ee85c55e93723df2928499ae7a781f8aa32d81d6cc  tests/test_hr_http.py
b5bb1f8aed0b5a3c671e0e0e30d7bf7b19680c92145b734c0ec5b9500c7a9379  tests/test_hr_identity_races.py
5363f19619ced314e05fac666db12ea24e911eff61bdfd339dc2f140ebb23062  tests/test_hr_installation_contract.py
617e12748e931f53bd57a71c481b90b95808ee3eda2774284961bca6ec697041  tests/test_hr_models.py
672f4e4b1becad911bc21cadd905acca2f863ebd8e285d31bc1a52973d079d70  tests/test_hr_nested_services.py
f9a558608d5c16144e310319bff20ad1c67daec37949bea4dbc2b2875cabbcc9  tests/test_hr_permissions.py
f2424a9cac5ee7bd4b3c1816411df32427ef6f486a392eba7adb7d4311d5e9ed  tests/test_hr_read_authorization.py
f9dcfb349f2c14ef3debbbfa3de5d190afcfe1a2d9b1a45a3f771ea7cc6b1ad4  tests/test_hr_reference_races.py
89128d1a25eb8359399ba49e04cf9ce336a89f9d9ad72eda86d242ffa2521f25  tests/test_hr_resource_boundaries.py
1559e5afece27117c60c5b4d647f5964e15e6e4feb5bcd42f99dc163886ee71f  tests/test_hr_self_decisions.py
767bca9a6699aaff32212845d1fbf2d41bb67713b3293729449a00db52e78f3a  tests/test_hr_services.py
fb18067d41b1e1042fd9e6d39d72ea0453c5803c0fd5c2e335b15d3b0127d0d3  tests/test_hr_setup_rollback.py
```

### Corrective stop checkpoint — failed final focused verification

The final focused PostgreSQL runner above exited **1**:
**194 passed / 1 failed in 215.75s**. Exact failing case:

```text
tests/test_hr_audit_validation.py::test_caught_early_public_validation_rolls_back_prior_effect_and_audit[selected-alias-record_employee_uuid]
```

The intended malformed-Attendance assertion was NOT reached. During the prior
nested `services.create_department()` operation, its duplicate-code `exists()`
query was cancelled by PostgreSQL statement timeout, SQLSTATE **57014**;
the outer boundary raised `ResourceBudgetExceeded`, not the expected validation
error. This is a real failed verification gate, not a green fail-closed test or
proof that this particular validation regression is resolved on final input.
No automatic rerun, production-budget change or test weakening was performed.

A disposable browser fixture was starting concurrently. An actual subsequent
`docker stats --no-stream` observation recorded its CPU at **99.17%** (the
PostgreSQL container was **2.52%**). This establishes overlapping load, NOT the
timeout's root cause. The browser controller's first discovery timed out; its
retry succeeded, but the new localhost tab returned `net::ERR_EMPTY_RESPONSE`
while the fixture was still starting. No responsive, CSRF, keyboard or non-JS
browser PASS is claimed for this corrective candidate.

Full PostgreSQL and full supported SQLite suites were **NOT STARTED** after
this failed prerequisite. H01–H18 and T01–T26 are collectively **NOT PROVEN**
on the final corrective input. The original independent H03/H04/H07/H09–H14
failures and H16/H18 evidence limits remain historical; this implementation
does not self-close them. Earlier focused green executions remain attributed
only to their actual intermediate inputs. Canonical Ruff passed after final
source edits. Complete baseline-to-corrective changed-file formatting,
Django/drift/bootstrap, frontend reproducibility and targeted browser gates
remain incomplete, not silently inherited from the original candidate.

Actual complete logs for all nine execution/fixture runners were saved outside
the repository before teardown:

```text
C:\Users\HP\.codex\visualizations\2026\09\13\01a09a3b-7a01-72e3-86bc-21a752d748fc\HR1-AUD-1-corrective-execution-logs.txt
```

Cleanup verified all ten exact task-created container IDs/images/source mounts.
Only the new HR corrective runners, tmpfs browser fixture and tmpfs PostgreSQL
server were stopped/removed. The server contained only the custody-commented
task database and PostgreSQL technical databases, with zero other client
sessions. The temporary browser-fixture source helper was also removed. These
disposable synthetic databases are not recoverable; actual execution logs are
retained. The unrelated `ecom-local-db-1` and pinned QA image remain untouched.

**CURRENT STATUS: HR1-AUD-1 CORRECTIVE IMPLEMENTATION — INCOMPLETE / NOT
AUDIT-READY.** Four targeted corrections and 113 new regression cases exist,
but mandatory final verification failed. No corrective commit was created:
HEAD remains the original `e6b72896e10471463b8b6b280fbccfc524d7cc42`; changes
remain intentionally uncommitted. Main/origin-main remain the HR-0 base;
Phase 4 remains held at its exact preserved SHA. No push, PR, merge or tag.

The owner authorized temporary scheduled continuation, but the final focused
gate failed before any such automation was activated. No corrective follow-up
was created and no rerun is scheduled. Safe continuation requires review of
the timeout evidence, then explicitly resumed, serial frozen-input verification
with no competing fixture startup; if successful, all remaining full-suite,
quality/browser/integrity gates still precede the one conditional local commit.
Do not weaken accepted production deadlines or manufacture an independent
corrective audit, acceptance, adoption or production-readiness claim. **STOP.**

#### Exact uncommitted corrective path inventory

Fourteen tracked modifications and four new, untracked regression files;
nothing staged. Ordinary `git diff --stat` does not include the untracked four.

```text
businessos/modules/hr/admission.py
businessos/modules/hr/civil_time.py
businessos/modules/hr/conflicts.py
businessos/modules/hr/history.py
businessos/modules/hr/persistence.py
businessos/modules/hr/selectors.py
businessos/modules/hr/services/__init__.py
businessos/modules/hr/services/attendance.py
businessos/modules/hr/support.py
docs/exec-plans/active/HR_1_IMPLEMENTATION_EVIDENCE.md
tests/test_hr_admission.py
tests/test_hr_history.py
tests/test_hr_models.py
tests/test_hr_nested_services.py
tests/test_hr_audit_acquired.py
tests/test_hr_audit_history.py
tests/test_hr_audit_persistence.py
tests/test_hr_audit_validation.py
```

#### A–W corrective handoff summary

| Report requirement | Actual stop-checkpoint disposition |
| --- | --- |
| A / T — integrity and ancestry | Clean required starting candidate verified; final HEAD remains e6b72896, parent/local main/origin-main/live main b36cdba9. Working tree intentionally dirty, 18 paths above; no commit. |
| B / C — audit | Complete A–AJ report read, preserved; HR1-AUD-001/002/003/004 are exactly four P2s, original REVISE/B retained. |
| D — reproduction | Actual SQLite red failures for all four, separately recorded above; no invented PostgreSQL red. |
| E — historical certification | Same-rule finite SQL exact midnight candidate proof and extreme/earlier-row regressions implemented; final full acceptance pending. |
| F — persistence | Named exact write boundaries, persisted immutable/receipt comparisons, operation/actor/scope binding and orphan protection implemented. |
| G — acquisition | Declared versus acquired versus new reservation separated, actual central lock acquisition, no late FOR UPDATE, non-reusable transaction/savepoint evidence and complete current guards. |
| H — nested validation | Early Attendance and Employee validation moved inside existing boundary; no global transaction change. |
| I — interaction | Retry/history, legitimate lifecycle, caught failures, alias and combined Leave/Department tests added; internal review closed insert-attestation/savepoint gaps; final revalidation incomplete. |
| J / K — files/tests | Exact 18-path inventory; 113 new cases across four files, old acceptance cases retained with bounded fixture adaptations. |
| L / M — H/T | H01–H18 and T01–T26 collectively NOT PROVEN on final input; earlier independent and implementation results not reused as fresh PASS. |
| N / O — database suites | Intermediate PG327 PASS; final focused PG194 PASS/1FAIL; intermediate SQLite539 PASS/6 classified skips. Final full suites not started. |
| P — transaction/alias | New default/selected-alias cursor-trap and whole-rollback cases exist; failed final selected-alias validation case did not reach its intended oracle. No blanket alias PASS. |
| Q — quality/bootstrap | Canonical Ruff PASS; corrected-file formatting performed; all 59 hashes match. Final documentation links/fences/whitespace pass. Full changed-set formatting/bootstrap/drift/frontend gates incomplete. |
| R — browser | Synthetic fixture/controller attempt failed to reach a working page; 390/768/1280, CSRF and non-JS are NOT PROVEN for this correction. No UI redesign. |
| S — evidence | Original chronology/fingerprints retained; separate corrective record, real logs and refreshed 59-input inventory added. |
| U — Phase 4 | Held branch remains 735e1bea13bc58fa71d430163422139d5c0f2363, untouched. |
| V / W — limits/verdict | INCOMPLETE / NOT AUDIT-READY; exact timeout blocker and safe serial continuation above. No independent re-audit, acceptance, adoption, push, PR, merge, tag or next milestone. |

## HR1-AUD-1 resumed verification

Evidence date: **2026-10-16 Asia/Dhaka**. This is an implementation-run
investigation under the owner's separate resumption authorization, not an
independent corrective audit. The preceding failed checkpoint and its complete
execution log remain unchanged. The misleading introductory "Latest" status
has been corrected without relabeling the original completed implementation.

### Integrity and bounded environment

Starting and final HEAD: `e6b72896e10471463b8b6b280fbccfc524d7cc42`;
branch `phase3a-hr1-implementation`. Parent/local main/origin-main:
`b36cdba91654e6a583735d67f7f6cf27a835003e`. All **59** frozen code/test/
template/build fingerprints above matched before execution and remain unchanged.
The exact **18** dirty paths above were preserved, with nothing staged. This
resumption changes only this already-dirty evidence document inside the
repository; there is no new runtime or test correction.

The isolated server `hr1-aud1-resume-pg-e6b7289` had exact container ID
`4fea137851ef207507a6bfa4216e1ad2bc6004241f3ebbefc9760f78104197f0`,
PostgreSQL 17-alpine, network-none, tmpfs PGDATA, no host data mounts or ports.
The new `hr1_aud1_resume` database carried the explicit synthetic-only custody
comment. Each PostgreSQL pytest invocation created/destroyed its own disposable
`test_hr1_aud1_resume`; SQLite used a separate network-none test container and
the supported in-memory settings. No existing demo/customer database was used.
Application source and external probes were mounted read-only. The pinned QA
image remained `hr1-local-qa:b36cdba` (Python 3.13.16, Django 5.2.17,
Ruff 0.16.7); all three optional commercial-install flags were enabled.

Execution was **serial**, without browser-fixture startup or another heavy
verification job alongside a test runner. The observed Docker platform was
Linux/x86_64, 12 CPUs, 3,742,158,848 bytes reported memory. These are current
platform observations, not measurements of the earlier failure's conditions.

### Historical failure versus newly captured SQL

The historical failed case remains:

```text
tests/test_hr_audit_validation.py::test_caught_early_public_validation_rolls_back_prior_effect_and_audit[selected-alias-record_employee_uuid]
```

Its traceback identifies the **preceding Department duplicate-code EXISTS**:
`services.create_department()` -> `_setup_create()` -> `.exists()` ->
`HRAdmission._execute()` -> psycopg statement cancellation, SQLSTATE **57014**.
The outer boundary maps that database failure to `ResourceBudgetExceeded`
after rollback. The intended invalid Attendance call had not run. The selected
alias was `hr_audit_validation_selected`. Historical exact SQL bytes/parameters,
PID, effective timeout, remaining budget, duration and lock graph were **not
recorded**. They cannot be retroactively manufactured from this traceback.

Fresh read-only instrumentation captured this actual SQL shape, with parameter
types `Int4`, `str`, `UUID`; bound synthetic identities are not copied here:

```sql
SELECT %s AS "a" FROM "hr_department"
WHERE ("hr_department"."code" = %s AND "hr_department"."company_id" = %s)
LIMIT 1
```

This is newly observed SQL at the same identified source stage, not a claim
to have recovered the missing historical SQL/parameters or backend state.

| Fresh context | Selected backend PID | Remaining admitted budget before EXISTS | Actual local statement/lock/idle settings | EXISTS client duration |
| --- | --- | --- | --- | --- |
| Isolated instrumented exact case | 96 | 1,749.387 ms | 1,750 ms / 1,750 ms / 5 s | 1.422 ms |
| Neighboring rollback/admission group | 126 | 1,822.337 ms | 1,823 ms / 1,823 ms / 5 s | 1.046 ms |
| Reconstructed original eleven-file scope | 475 | 1,791.466 ms | 1,792 ms / 1,792 ms / 5 s | 1.669 ms |

Each instrumented operation traversed 515 application SQL-wrapper calls,
including the unchanged all-12-permission union. The minimum recorded remaining
admitted allowance was respectively 1,549.521, 1,635.060 and 1,551.866 ms.
These timings include diagnostic overhead; they are not performance guarantees.
The external helper delegates to the real `_execute`, observes its existing
`set_config` result, and samples `pg_stat_activity`, `pg_blocking_pids` and
`pg_locks` through a separate read-only connection at 50 ms intervals. It does
not reset clocks, change budgets/GUC policy, add production logging or suppress
exceptions. Sampling can miss brief waits: no observed blockers/ungranted locks
does not prove that no wait of any duration occurred.

The sampled selected connections were inside their actual outer transaction.
Before fixture closure after rollback they were `IDLE`, autocommit true,
outside atomic blocks, with `needs_rollback` false and all three timeout settings
restored to `0`; isolation was `read committed`. The admission ContextVar was
cleared, the capability marked finished, and the selected connection then
closed/deleted. The existing default-alias success/rollback timeout-restoration
and alias-switch/default-cursor-trap regressions also passed. No timeout-state
leak was observed in these runs; this is not proof about missing historical
session measurements.

After rollback and outside the admitted budget, a read-only EXPLAIN ANALYZE in
the neighbor probe used an Index Scan on `hr_department_company_id_4857ee51`
plus the code filter, with 0.056 ms reported execution time and three shared
buffer hits. This disproves an expensive plan in that fresh probe, not every
possible historical plan or scheduling condition.

### Actual reproduction sequence and rollback evidence

All processes exited **0**, in this order, with new disposable database state:

| Runner | Actual result | Time |
| --- | --- | --- |
| `hr1-aud1-resume-exact-01` — exact case alone, no instrumentation | 1 passed | 15.51 s |
| `hr1-aud1-resume-exact-02` — exact case alone, read-only instrumentation | 1 passed | 11.68 s |
| `hr1-aud1-resume-exact-03` — exact case alone, no instrumentation | 1 passed | 10.15 s |
| `hr1-aud1-resume-neighbors` — validation, nested services, acquired locks, admission | 160 passed, zero skipped | 153.55 s |
| `hr1-aud1-resume-focused-pg` — documented original eleven-file set | 648 passed, zero skipped | 260.49 s |
| `hr1-aud1-resume-focused-sqlite` — same focused set, supported SQLite | 567 passed, 81 classified skips | 64.23 s |

The exact case therefore passed five times: three isolated invocations and
once in each PostgreSQL group. The original failed runner did not preserve
its ordered argv. The eleven-file **set** is documented, but this fresh argv
ordering is a reconstruction, not an exact historical ordered replay.

The actual focused command, using PostgreSQL development settings and then
SQLite test settings, was:

```text
pytest tests/test_hr_audit_acquired.py tests/test_hr_audit_history.py tests/test_hr_audit_persistence.py tests/test_hr_audit_validation.py tests/test_hr_admission.py tests/test_hr_nested_services.py tests/test_hr_history.py tests/test_hr_civil_time.py tests/test_hr_models.py tests/test_hr_services.py tests/test_hr_flows.py -vv --maxfail=1 --tb=long
```

Both disabled the cache provider; PostgreSQL additionally used `-s` and
`-p hr1_timeout_probe`, SQLite used `-rs`. Exact container IDs, executed command
arrays, times, exit states, source mounts and network modes are retained in the
sanitized container record below. No test selection or expected exception was
changed to accept the historical timeout.

The neighbor/focused diagnostic traces prove successful preceding native
Department and success Audit INSERTs on the **same selected PID**, followed by
the intended `_invalid_call` and field-specific `ValidationError` for
`employee_id`. The original test's complete before/after native comparison
passed for Department, Employee, Attendance, AttendanceRevision, LeaveType,
LeaveRequest and AuditEntry, including when the caller caught the nested
validation error. Thus the intended whole-outer rollback actually occurred in
these observed runs, with no surviving prior effect, revision, receipt or Audit.
The permanent test still has a broad outer `raises(ValidationError)` assertion;
explicit reached-stage/exception-identity assertions would strengthen its
future standalone oracle. No such test edit is misrepresented as completed.

SQLite's 81 skips are exactly: 75 PostgreSQL relation/row-lock/catalog admission
proofs; four history catalog/RLS/relation proofs; one history shadow-identity
proof; one independently held domain-row lock proof. There are no other skips.
All four finding-specific regression files ran in the fresh PostgreSQL group;
all supported counterparts ran in SQLite. This is focused implementation
evidence, not independent re-audit closure or complete H/T acceptance.

The retained PostgreSQL log also contains expected adversarial errors: two
intentional `pg_sleep(3)`/Django `Q.check` statement timeouts, four deliberate
old-protocol negative-control deadlocks across the two groups, NOWAIT lock
refusals, raw revision/range constraint attacks, and two Identity-delete
Audit-FK refusals accepted by the writer-race oracle. These are not recurrences
of the Department EXISTS failure; none occurred on selected PIDs 96/126/475.

### Root-cause disposition and enforced stop

**Historical root cause remains materially UNPROVEN.** The exact historical
57014 did not recur. The known concurrent browser startup is temporal overlap,
not causal proof. The all-12 permission union is allowed by the accepted
contract, not a demonstrated fixture defect. Current measurements leave ample
budget and show scoped cleanup, so neither shrinking that union nor changing
timeouts is justified by this evidence. Cumulative-budget pressure, backend/
host scheduling contention or an unrecorded historical wait remain hypotheses,
not established explanations. No additional code/test correction was applied.

Per resumption section 10, this blocks the long full PostgreSQL/SQLite suites
and the conditional corrective commit even though focused verification passed.
They were **not started**. H01-H18 and T01-T26 remain collectively **NOT PROVEN
on the corrective candidate**; earlier original full-suite/audit results are
not substituted. Final canonical Ruff/all-changed-file formatting, application
bootstrap/Django/drift, frontend and 390/768/1280 browser gates were not advanced
past this stop. Fresh pytest databases did apply source migrations successfully;
that is not a claim to have executed every remaining bootstrap/topology gate.
Only documentation/link/fence/whitespace and integrity checks accompany this
handoff. No temporary follow-up was created or left running.

Safe continuation: preserve these 18 paths and 59 fingerprints; review the
retained historical and fresh traces; obtain a causally faithful instrumented
failure or other material evidence before choosing a correction. Preserve the
two-second cumulative budget and whole-outer rollback; do not substitute green
reruns for root-cause proof. Strengthen the stage-specific rollback oracle when
continuing that bounded work. Only after that gate is genuinely satisfied may
fresh complete regression/quality/browser verification precede the one
authorized additive commit above `e6b72896...`.

### Retained diagnostic evidence and cleanup

Actual logs and the read-only helper are retained outside the repository under:

```text
C:\Users\HP\.codex\visualizations\2026\09\13\01a09a3b-7a01-72e3-86bc-21a752d748fc
```

They do not replace the previous `HR1-AUD-1-corrective-execution-logs.txt`.
SHA-256 of the new retained records:

```text
bfc099ac7229c924bf396294b4f0b1b57f659d2cbe4f86138fb4b8697efc5947  hr1_timeout_probe.py
793e06cac371a16002ab26a5e41ad0e9ca0d0c7da42bdc42172e570fbe558ef5  hr1-aud1-resume-exact-01.log
089b9588beba179e9afa248b4f18865da763f02183f418c3096364201c86d9eb  hr1-aud1-resume-exact-02.log
5624c6d9d772d2593cddceed76f0206e54e404556c53b4163c4b83eff58181b2  hr1-aud1-resume-exact-03.log
047d32db005f73e9637b07f34e69cfe4bd061288f259486b8d84fb11a4154bc6  hr1-aud1-resume-neighbors.log
a2a2bf5b12bb5c6d56e781395ad17621d14fa445bce3f1659a117556d8d3303b  hr1-aud1-resume-focused-pg.log
941ff63365171536d3d873dc78551f567944a56f06dd61f2f60c4374594a36e6  hr1-aud1-resume-focused-sqlite.log
18e56242cc3b6462936f04dad4c50224fdbedde800fb81df161e76458edd4b87  hr1-aud1-resume-pg-server.log
c4fb086ef88b7778688e7a7b6d21fed22dca3fb5d8eae231f6002d5a24bb78de  hr1-aud1-resume-container-evidence.json
```

All seven exact task-created container IDs/images/mounts were verified before
teardown. Immediately before cleanup, the server contained only the custody-
commented synthetic application database and PostgreSQL technical databases,
with zero other client sessions. Its tmpfs server and six exited runners were
stopped/removed, deleting only these disposable synthetic databases; they are
not recoverable. Complete logs remain above. The pinned image and unrelated
`ecom-local-db-1` were preserved. No prune or unrelated deletion occurred.

Final local main/origin-main and live main remain `b36cdba91654e6a583735d67f7f6cf27a835003e`;
the local held Phase 4 branch remains `735e1bea13bc58fa71d430163422139d5c0f2363`.
The live read returned no remote HR-1 or Phase 4 branch. Protected Core, other
modules, accepted migrations/contracts and the frozen HR plan remain unchanged.
No new commit, staged change, push, PR, merge, tag, adoption or next milestone.

**HR1-AUD-1 CORRECTIVE IMPLEMENTATION: INCOMPLETE / NOT AUDIT-READY.**
Corrective HEAD is still the original `e6b72896...`; no new corrective SHA
exists. Independent corrective re-audit is not performed, canonical adoption
is not authorized, Phase 4 remains ON HOLD. **STOP.**

## HR1-AUD-1 two-oracle diagnostics

Date: **2026-10-16 Asia/Dhaka**. This bounded continuation follows the owner's
`563eb5cb-ad00-4b1d-82a8-ce00b72da58e` authorization. It explicitly prohibits
full regression suites and commits, independently of the earlier conditional
commit authorization. This is implementation-run safety evidence, not an
independent corrective audit, owner acceptance or waiver of the root-cause gate.

### Preserved inputs and exact diagnostic changes

Starting/final branch is `phase3a-hr1-implementation`, HEAD
`e6b72896e10471463b8b6b280fbccfc524d7cc42`; parent/main/origin-main remain
`b36cdba91654e6a583735d67f7f6cf27a835003e`. All 18 dirty paths above were
preserved, with zero staged paths. All 59 original corrective fingerprints
matched before editing. The only repository paths changed in this batch are:

- `tests/test_hr_audit_validation.py`: strengthen the existing normal-failure
  oracle, add one PostgreSQL-only Department-stage timeout negative control,
  and record bounded non-PII state facts. Real services, admission, transactions,
  native persistence and Audit are not mocked or replaced.
- This evidence document: append actual results/disposition and update its
  current-status pointer. All original findings, failures and verification
  records remain intact.

No production correction was demonstrated necessary or applied. The other
58 frozen inputs remain byte-identical, including all four original production
fixes and their other regressions. Accepted ADR 0018, frozen HR plan, Core,
other owners, schemas, settings/manifests/migrations and frontend remain unchanged.
No contract inconsistency requiring an ADR change was found.

The historical 59-path fingerprint inventory remains unchanged above. Its exact
overlay identifying the final diagnostic input is:

| Path | Historical SHA-256 | Current SHA-256 |
| --- | --- | --- |
| `tests/test_hr_audit_validation.py` | `023cbdc7824c8b88e9004d377088e7b55b4bc4d29f66d5aaa7e92c940561025d` | `5f818b4b160d7cd7b6670f6af4623cb27692bf434f4cd11152a7c8d2a715f923` |

The other 58 values apply verbatim. Original nine retained diagnostic records
also retain their exact previously recorded hashes. New logs do not overwrite
them. Initial standalone probes preceded the final bounded JSON-output/message
assertion enhancement; the subsequent neighbor/focused/quality runs all used
the final test hash above. The normal business-test assertions were not weakened.

### Oracle A: intended domain validation and whole-outer rollback

The original parametrized test and all fourteen invalid-input families remain.
It now requires a successfully returned real Department, native scoped row and
exact `hr.department.created` Audit **before** calling the invalid nested
operation. For the target selected-alias case, the real public Attendance
service must produce the field-specific `employee_id` ValidationError. A prior
Department failure can no longer satisfy the broad outer exception oracle.

The test captures the inner error, requires the identical error at outer exit,
and proves `outer.poisoned` identity plus `needs_rollback` and same-alias
`transaction.get_rollback()` immediately after the caller catches it. No SQL is
attempted inside that poisoned scope. Complete native before/after comparison
includes all fields of the six HR models and Audit. It proves no earlier
Department/Audit, Attendance, revision or receipt survives.

After exit, assertions require no current admission, finished capability,
autocommit, no atomic/savepoint/rollback state, PostgreSQL IDLE and restored
session settings on the same selected PID before alias closure. The default
cursor remains trapped. Two necessary native readbacks occur before failure;
diagnostic settings/readback queries otherwise run outside the admitted budget.

In the final PostgreSQL group the target normal operation used selected PID
**280**, READ COMMITTED, and 517 observed application SQL-wrapper calls. Its
preceding Department EXISTS took **1.122 ms**, with **1,814.408 ms** remaining
and actual local statement/lock/idle settings **1,815 ms / 1,815 ms / 5 s**.
The explicit `HR1_NORMAL_ORACLE` record confirms prior native/Audit visibility,
only `employee_id` in the domain error, identical inner/outer error, rollback-
only state, complete restored native baseline and finished capability. No
natural 57014 occurred in the normal-validation runs.

### Oracle B: deliberate real Department-stage 57014

The separate new test is
`test_selected_department_statement_timeout_rolls_back_and_does_not_poison_fresh_request`.
It creates a real preceding Department and Audit within a real admitted outer
scope, verifies both natively, then targets only the next Department duplicate-
code EXISTS using a test-only execute wrapper. The deliberately augmented SQL is:

```sql
SELECT (
    SELECT %s AS "a" FROM "hr_department"
    WHERE ("hr_department"."code" = %s AND "hr_department"."company_id" = %s)
    LIMIT 1
) AS hr_test_exists, pg_catalog.pg_sleep(3)
```

The original parameterized EXISTS remains inside this controlled statement.
The extra three-second work is a **negative-control injection**, not a fix,
ordinary application SQL or historical root-cause reproduction. Existing
production remaining-budget timeouts cause actual PostgreSQL 57014; no timeout,
two-second monotonic budget, clock, error or service return is mocked/reset.

The caller catches the real nested OperationalError. Assertions require its
psycopg cause to be 57014 with the statement-timeout diagnostic, exact poisoned
error identity and whole-outer rollback-only state. Outside rollback, the outer
contract must classify that same database error as ResourceBudgetExceeded.
Native baseline and original timeout/isolation/PID settings must be restored.
With injection removed, a **fresh independent real create** on that same
selected connection must commit exactly one new Department and Audit, leaving
all other native HR tables unchanged. This proves more than an exception type
or merely opening another clean connection.

| Controlled run | Selected PID | Remaining at injected statement | Actual statement / lock / idle | Statement duration |
| --- | --- | --- | --- | --- |
| Neighbor group | 159 | 1,016.315 ms | 1,017 ms / 1,017 ms / 5 s | 1,018.916 ms |
| Final focused group | 310 | 1,635.656 ms | 1,636 ms / 1,636 ms / 5 s | 1,637.257 ms |

Both records show INTRANS, one outer atomic block, no savepoint, real 57014,
rollback-only at catch, restored native baseline and successful same-session
fresh request. Original/post-outcome settings were `0 / 0 / 0`, READ COMMITTED,
with the same PID. The independent read-only observer saw **32 PgSleep samples**
in the final controlled case. It observed no blocking PID/ungranted lock there;
periodic sampling does not exclude every brief wait. Server logs contain exactly
four statement-timeout errors: three deliberately augmented Department queries
(standalone/neighbor/focused), and the existing deliberate Django Q.check
`pg_sleep(3)` negative control. No unclassified/natural timeout was observed.

The external trace and permanent negative-control test both observe the otherwise
unused `set_config` result. During injection the test consumes that result first,
so the outer trace's duplicate configuration observation is null. The explicit
`HR1_CONTROLLED_57014` test record captures the actual first-read values shown
above; null is not interpreted as absent/reset server configuration. No extra
per-statement settings query was introduced into the admitted work.

### Bounded serial executions and quality

Each PostgreSQL invocation created/destroyed a new disposable test database;
the repeated runner invoked pytest exactly twice, sequentially. There was no
parallel verification or browser-fixture startup. Every retained runner exited 0.

| Execution | Actual terminal result |
| --- | --- |
| Target A alone, instrumented preliminary | 1 passed, 13.06 s |
| Target A repetition 2, no instrumentation | 1 passed, 11.39 s |
| Target A repetition 3, no instrumentation | 1 passed, 12.22 s |
| Standalone preliminary controlled B | 1 passed, 21.93 s |
| Neighboring validation + nested services, final test input | 50 passed, zero skipped, 72.82 s |
| Bounded four-finding PostgreSQL group, final test input | 124 passed, zero skipped, 136.19 s |
| Supported bounded SQLite counterpart | 119 passed, 5 classified skips, 36.33 s |
| Canonical Ruff / explicit changed-Python formatting | PASS / 48 files already formatted, including migrations |
| Django check / migration drift, disposable SQLite settings | Zero issues / No changes detected |

The PostgreSQL group contains the four audit files, five existing real nested-
service cases, and six precise admission tests: timeout restoration, cumulative
budget, actual swallowed Q.check timeout, actual non-default PostgreSQL alias,
alias-switch rejection and admitted nested-subset guards. Actual collection is
124: current audit files contribute 14 acquired + 38 history + 16 persistence +
45 validation cases. All earlier cases are retained; B is one additional case.
This concrete collection, rather than an inherited narrative count, identifies
the bounded evidence. It is not the previous 648-test-scope run or a full suite.

Actual pytest path arguments (plus `-vv --maxfail=1 --tb=long`, cache provider
disabled; PostgreSQL `-s -p hr1_oracle_probe`, SQLite `-rs`) were:

```text
tests/test_hr_audit_acquired.py
tests/test_hr_audit_history.py
tests/test_hr_audit_persistence.py
tests/test_hr_audit_validation.py
tests/test_hr_nested_services.py
tests/test_hr_admission.py::test_postgresql_timeout_settings_restore_after_outcome
tests/test_hr_admission.py::test_cumulative_budget_is_not_reset_by_small_queries
tests/test_hr_admission.py::test_real_django_constraint_check_swallowed_timeout_cannot_commit_hr_effect
tests/test_hr_admission.py::test_actual_public_hr_service_nondefault_postgresql_alias_and_default_cursor_trap
tests/test_hr_admission.py::test_actual_hr_admission_rejects_nested_alias_switch_before_sql
tests/test_hr_admission.py::test_admitted_nested_subset_reuses_outer_and_rechecks_guards
```

SQLite skips are one real acquired-row lock, one new real PostgreSQL Department-
timeout/session proof, and three PostgreSQL-only admission/catalog proofs. The
other cases, including the functional alias/nesting/budget tests, passed. No
SQLite result is represented as PostgreSQL concurrency/timeout proof.

The locked read-only quality runner executed `ruff check . --no-cache`, explicit
`ruff format --check --no-cache` for all 48 baseline-to-working-candidate Python
paths, `python manage.py check`, and `python manage.py makemigrations --check
--dry-run`. No formatter write mode or migration generation was used. Fresh
PostgreSQL pytest bootstrap applied accepted migrations successfully. Full
PostgreSQL/SQLite suites, browser/frontend revalidation and complete H/T closure
were **not run/claimed** in this diagnostic-only batch. No commit is authorized
by these results.

### Separate conclusions and proposed owner disposition

**HISTORICAL TIMEOUT ROOT CAUSE: NOT PROVEN.** The original unmodified Department
EXISTS incident still lacks historical PID, actual remaining timeout/budget,
statement duration and backend wait/lock evidence. Its traceback/stage/alias and
57014 remain established; concurrent browser startup remains only temporal
overlap. All bounded ordinary target executions reached the intended domain
error. Artificially augmented queries do not recover the missing incident facts.

**CORRECTIVE SAFETY STATUS: PASS — bounded diagnostic scope.** Real normal
validation, caller-caught whole-outer rollback, deliberate native 57014,
selected-session restoration/fresh request and four original correction
regressions passed. No new production defect was demonstrated. This is neither
independent corrective approval nor complete-candidate regression readiness.

Accepted ADR/plan analysis: nested operations intentionally inherit the one
outer two-second admitted-work clock, with no reset and the same selected alias/
connection/transaction. The all-twelve-permission union remains unchanged.
Current normal observations do not show insufficient remaining budget; current
success/rollback/timeout tests show no leaked session setting. These observations
do not prove the missing historical mechanism. External scheduling/load, an
unobserved wait or historical cumulative pressure remain hypotheses. The
cooperative policy permits explicit resource refusal and does not promise hard
two-second wall-clock latency. No budget increase, permission-union reduction,
Core redesign or global authority gate is justified or introduced.

**Recommendation for OWNER REVIEW, not acceptance:** retain the historical
incident as an unexplained verification failure, not a resolved environmental
defect. The owner may explicitly decide that the proven safety oracles plus
bounded serial reliability justify advancing to a separately authorized,
serial frozen-input full-verification gate despite the unrecoverable historical
metrics. That decision should retain NOT PROVEN attribution, prohibit competing
heavy fixture startup, and require immediate stop/capture on any new unexpected
timeout. No timeout relaxation, automatic retry or broader readiness claim is
recommended. This task does **not** independently waive the previous stop gate.

Remaining risks: the original cause may recur; these finite probes cannot
certify every scheduling/lock/cancellation point or production latency. The
instrumentation has measurement overhead. Complete final regressions, H01-H18/
T01-T26, browser/other remaining gates and fresh independent re-audit are still
required for the corrective candidate. Owner disposition is **PENDING**.

### Retained records, cleanup and final state

New records share the external directory recorded above. The neighbor/focused
PG logs were captured in bounded chunks with Docker timestamps and deterministic
line ordering after an unchunked tool response exceeded capacity. Docker inserts
timestamps at partial-record boundaries too; decoded JSON removes only these
`YYYY-MM-DDTHH:MM:SS.<fraction>Z ` transport prefixes. Captures were reassembled
and hash-verified before teardown. Parsing failure before that transport-prefix
decoding was a diagnostic-reader limitation, not a failed test or altered
application result. Complete timestamped records remain available for review.

```text
a9bd873c8189829ccdd7b3a41ee93467ea635fc4a91043a9b0e59d07b5b97fcf  hr1_oracle_probe.py
1c72f29224dd035db574722f30a3f1a265410d50acf6d845c76342180c391355  hr1-aud1-oracles-container-evidence.json
19c87c1a4ca5669e4e7c9a15f2cdb0024d0c25b759aff3ddbed86098bc950526  hr1-aud1-oracles-exact-01.log
b1c304b375c8ecd3be7db1055db277bde8bd131bb260ba2cece016a39ed529c1  hr1-aud1-oracles-focused-pg.log
67f760ca814a26f57f94e01399bebd5dac21594f8e0b32af612127cde28572f3  hr1-aud1-oracles-focused-sqlite.log
95a998fa674f49c89dce0b7057abac3fd1580dc36f8c8db6375640e766481844  hr1-aud1-oracles-neighbors.log
181b2b8d9119a7f354fbf72381f4708759c3b35ef992bdbd4ea0277adbf9d253  hr1-aud1-oracles-pg-server.log
687133830bd79511aa08e7d1fdbba3dbfd92bd0b2bf8ef77889fe36dc42581ab  hr1-aud1-oracles-quality.log
01689f981c4d2b4df5ec07f4fc37eed9150238c9b7f1140296a2bf5bc4be482f  hr1-aud1-oracles-repeat-02-03.log
7199997a9336194385048a259746bbcf9b080216a90874a18e4b82a551a3b77f  hr1-aud1-oracles-timeout.log
```

New PostgreSQL server `hr1-aud1-oracles-pg-e6b7289`, exact ID
`8e1bdfd8d63e968d8e9c183e837baeb41681f23c6719e9d8cb5a549fdfc48a7d`,
used network-none/tmpfs PGDATA/no ports/no host data mounts. Its new
`hr1_aud1_oracles` database had an explicit synthetic custody comment. QA used
the unchanged locked image, read-only source/probe mounts, all three existing
commercial-install flags and isolated test databases, not customer/demo data.
Before cleanup, only that synthetic application database and PostgreSQL
technical databases remained, with zero other client sessions. All eight retained
task container IDs/images/mounts were verified, then the server and seven
exited runners were removed. Disposable synthetic databases are not recoverable;
complete evidence logs remain. The pinned image, unrelated Ecommerce container,
demos, other repositories and all preserved source histories were untouched.

Final HEAD remains `e6b72896e10471463b8b6b280fbccfc524d7cc42`, with the same
18 intentionally uncommitted paths. Main/origin-main remain
`b36cdba91654e6a583735d67f7f6cf27a835003e`; held local Phase 4 remains
`735e1bea13bc58fa71d430163422139d5c0f2363`. No commit, push, PR, main update,
tag, new milestone or scheduled continuation. Phase 4 remains **ON HOLD**.

**Historical root cause: NOT PROVEN. Bounded corrective safety: PASS.
Owner disposition: PENDING. Overall corrective implementation: INCOMPLETE /
NOT AUDIT-READY. NO COMMIT. STOP.**

## HR1-AUD-1 owner-authorized final verification — STOPPED

Date: **2026-10-18 Asia/Dhaka**. Authority: the owner's complete attachment
`b1144d48-b646-4252-9872-142fbedb8c2c/Pasted text.txt`. This is a local
implementation verification attempt, not an independent re-audit. The original
**REVISE / Readiness B / four P2** audit remains unchanged and independently
unclosed. No new runtime or test correction is authorized by this failed run.

### Limited owner disposition and frozen preflight

The owner explicitly permitted serial final verification despite the original
57014 cause remaining **NOT PROVEN**, based on the separately recorded normal
validation/whole-outer rollback and controlled native timeout/session-safety
evidence. This supersedes the earlier *owner disposition pending* status only;
it does not prove historical causation, accept the corrections, waive any
production correctness rule, relax the two-second budget or permit automatic
reruns. Any fresh focused failure must stop full-suite progression and commit.

Verified starting branch/HEAD: `phase3a-hr1-implementation` /
`e6b72896e10471463b8b6b280fbccfc524d7cc42`. Parent, local main, origin/main
and HR-0 contract branch equal `b36cdba91654e6a583735d67f7f6cf27a835003e`.
The exact 18 corrective paths listed above remain dirty, with zero staged files
and no corrective commit. Held local Phase 4 remains
`735e1bea13bc58fa71d430163422139d5c0f2363`.

All **59** actual code/test/template/build fingerprints were recomputed:
**58 unchanged values plus the exact recorded validation-test overlay match**.
The current validation-test hash remains
`5f818b4b160d7cd7b6670f6af4623cb27692bf434f4cd11152a7c8d2a715f923`.
The original nine and subsequent ten diagnostic records also match all **19**
recorded hashes. No production/test/accepted-contract/migration/frontend input
was edited during this attempt. Only this already-dirty evidence document is
updated afterward. Protected tracked-owner diffs remain empty.

The sandboxed live Git read failed with `getaddrinfo() thread failed to start`;
the read-only escalated retry succeeded, returning remote main at the exact
HR-0 base and no remote HR-1 or Phase 4 branch. No fetch/ref update was needed.
Initial sandbox Docker access was denied; the authorized isolated Docker
commands subsequently ran with escalation, not against an existing demo DB.

### Fresh focused prerequisite: actual FAIL

The new server `hr1-aud1-owner-final-pg-e6b7289` had exact ID
`8fc8b019fe15fe75acca6d1fc8e5782e4de8e434c686b1da0cf29e307373c1f2`.
It used PostgreSQL **17.11**, Linux/x86_64, network-none, tmpfs PGDATA, no host
data mounts or published ports. The new `hr1_owner_final` database had an
explicit synthetic-only task/teardown custody comment. Pytest created the
separate `test_hr1_owner_final` and destroyed it on failure exit.

Runner `hr1-aud1-owner-focused-pg`, exact ID
`0284313c32ab6608add6bb8cd762166c09212d2430a000fc2699ab50e88a6e91`,
used the pinned `hr1-local-qa:b36cdba` image
`sha256:a7a3476a1883cddc11d7c9bcf7d7674c5c9396211f2b654337a58a1c9936637f`:
Python **3.13.16**, Django **5.2.17**, pytest **8.4.2**. Source/probes were
mounted read-only, bytecode/cache writes disabled, all three existing optional
commercial-install flags enabled and development PostgreSQL settings selected.
Execution was the default alias with server default **READ COMMITTED**; the
failed operation itself also reports the default alias. No second heavy
verification or browser startup was launched by this task.

The exact pytest path arguments were the twelve arguments in the preceding
bounded 124-case command block, in the same order. The exact options were:

```text
-vv --maxfail=1 --tb=long -s -p no:cacheprovider -p hr1_oracle_probe
```

The runner's complete command array is retained in its container evidence.
All fresh test-database migrations applied, including both unchanged HR
migrations. Collection was **124**. Actual terminal result:
**13 passed / 1 failed / zero skips in 211.62s**, container exit **1**.
Container start/finish were `2026-10-18T03:33:06.463958975Z` and
`2026-10-18T03:36:50.352358833Z` (09:33–09:36 Asia/Dhaka).

Exact failing case:

```text
tests/test_hr_audit_acquired.py::test_pending_attendance_cannot_be_completed_without_actual_initial_revision_insert
```

This test expected `AdmissionError` from attempting to complete a newly
reserved Attendance without a real initial revision. Instead it failed earlier:
after `op.authorize()` and the returned nested `create_department`, the private
`_create_attendance` entered `_insert` and `row.full_clean()`. Django validated
the `recorded_by` foreign key through this actual SQL template:

```sql
SELECT %s AS "a" FROM "identity_user" WHERE "identity_user"."id" = %s LIMIT 1
```

`HRAdmission._execute()` reached its **post-SQL** `self.checkpoint()` at
`admission.py:384`; the cumulative monotonic budget check at line 227 raised
`ResourceBudgetExceeded: HR cumulative operation resource budget exhausted.`
The source call is `test_hr_audit_acquired.py:395`. The Attendance INSERT and
the intended `complete_attendance_creation` refusal/assertions were not reached.
The test's final native/Audit rollback assertions were likewise not reached;
destroying the test DB is **not** evidence that those assertions passed.

This is **not a reported native SQLSTATE 57014 recurrence**: the error is the
cooperative post-SQL budget check, not a psycopg statement cancellation. The
complete fresh server log has no statement-timeout or deadlock ERROR. The
budget-consumption cause is **NOT PROVEN**. There is no contemporaneous failing
PID, exact remaining-time trace, operation-duration breakdown or failing-stage
lock graph. A separate earlier read-only activity snapshot is not such proof.
The existing diagnostic plugin observes only the two validation/timeout oracles,
neither of which was reached before this failure. No observer result is invented.
Host load, scheduling and cumulative SQL/validation work remain hypotheses.
No claim of an environmental cause, partial commit or proven production defect
is inferred solely from this verification failure.

### Four findings and remaining H/T gates

| Original finding | Current-attempt evidence / disposition |
| --- | --- |
| HR1-AUD-001 — P2 | Existing implementation/fingerprints retained; history family not reached. Final revalidation NOT PROVEN. |
| HR1-AUD-002 — P2 | Existing private-field guards retained; persistence family not reached. Failed pending-Attendance interaction precedes its intended assertion. Final revalidation NOT PROVEN. |
| HR1-AUD-003 — P2 | Thirteen acquired-lock/nesting cases passed, including a real held target and selected-alias trap; fourteenth case failed as above. Complete corrective gate FAIL. |
| HR1-AUD-004 — P2 | Existing boundary correction and strengthened test retained; normal and controlled-57014 validation cases not reached. Fresh revalidation NOT PROVEN. |

No earlier green family is substituted for the failed fresh prerequisite.
The focused SQLite counterpart, full PostgreSQL and full SQLite suites were
**NOT STARTED**. No rerun, budget change, expected-exception broadening or
permission-union reduction was performed.

| H ID | Local current-attempt status / evidence | External obligation |
| --- | --- | --- |
| H01 | NOT PROVEN; complete scope suite not run | Independent re-audit pending |
| H02 | NOT PROVEN; Branch suite not run | Independent re-audit pending |
| H03 | NOT PROVEN; identity/persistence suite not run | Independent re-audit pending |
| H04 | NOT PROVEN; lifecycle/unique races not run | Independent re-audit pending |
| H05 | NOT PROVEN; compound permission matrix not run | Independent re-audit pending |
| H06 | NOT PROVEN; registration migrations applied, full admission matrix not run | Independent re-audit pending |
| H07 | PARTIAL / NOT PROVEN; acquired-file selected-alias and connection cases pass, complete matrix not run | Independent re-audit pending |
| H08 | NOT PROVEN; interval/conflict suite not run | Independent re-audit pending |
| H09 | NOT PROVEN; civil/history suite not run | Independent re-audit pending |
| H10 | NOT PROVEN; complete history suite not run | Independent re-audit pending |
| H11 | NOT PROVEN; Leave suite not run | Independent re-audit pending |
| H12 | NOT PROVEN; all T oracles not run | Independent re-audit pending |
| H13 | PARTIAL / NOT PROVEN; acquired guards exercised, prerequisite failed | Independent re-audit pending |
| H14 | NOT PROVEN; failing test's final native/Audit assertions not reached | Independent re-audit pending |
| H15 | NOT PROVEN; HTTP/frontend suite not run | Independent re-audit pending |
| H16 | NOT PROVEN; no fresh browser run; prior evidence remains historical | Independent re-audit pending |
| H17 | PARTIAL / NOT PROVEN; fresh full test-schema migrations applied, minimal topology not rerun | Independent re-audit pending |
| H18 | FAIL local prerequisite; final quality/full suites not advanced | Independent re-audit/hosted CI/canonical gates pending and not executed |

| T ID | Current-attempt actual result |
| --- | --- |
| T01 | NOT RUN; isolated negative-control deadlock not executed |
| T02 | NOT RUN |
| T03 | NOT RUN |
| T04 | NOT RUN |
| T05 | NOT RUN |
| T06 | NOT RUN |
| T07 | NOT RUN |
| T08 | NOT RUN |
| T09 | NOT RUN |
| T10 | NOT RUN |
| T11 | NOT RUN |
| T12 | NOT RUN |
| T13 | NOT RUN |
| T14 | NOT RUN |
| T15 | NOT RUN |
| T16 | PARTIAL; thirteen acquired-file cases pass, but final pending-Attendance interaction fails before intended oracle; NOT PROVEN complete |
| T17 | PARTIAL; acquired-file selected alias/default trap passes, complete PostgreSQL alias oracle not reached |
| T18 | NOT RUN as complete User/Role/Permission release matrix |
| T19 | PARTIAL; acquired-file caught-refusal rollback passes; normal/controlled timeout and complete effect/Audit matrix not reached |
| T20 | NOT RUN |
| T21 | NOT RUN |
| T22 | NOT RUN |
| T23 | NOT RUN |
| T24 | NOT RUN |
| T25 | NOT RUN |
| T26 | NOT RUN |

Fresh Ruff/format, Django/drift, standalone bootstrap/registry/architecture,
JavaScript, npm/Tailwind/CSS and 390/768/1280 browser gates were **not advanced**
after failure. Earlier PASS records retain their original run attribution.
Only documentation/integrity/whitespace checks accompany this stop record.
No new UI or production code change was made.

### Evidence custody, cleanup and safe continuation

Complete fresh timestamped logs were saved through `apply_patch` outside the
repository in the same retained evidence root above, without truncation:

```text
4bb48bf18f9059baaa490bcd1947d9bd038bd78f9e3c966eb65bed627626fe32  hr1-aud1-owner-final-focused-pg.log
3b285263f8060da7fa0bd420627ab2fed8adb1cd5961b259c69414db320e1173  hr1-aud1-owner-final-pg-server.log
9a13db1779774be21c8a19fc366fcffdcd837d21a6df3e86bbfb43f5d141015e  hr1-aud1-owner-final-container-evidence.json
bf0c966bc6bf1d15345b470822577e74acd8bac0918df74d7cbca08b36bed268  hr1-aud1-owner-final-pg-shutdown.log
```

The initial combined tool display was truncated; the complete separate log
captures above were verified non-truncated before saving. Original audit/logs
and all previous 19 diagnostic artifacts were not overwritten. A proposed
external full-suite-only observer helper was never executed and was removed;
it supplies no evidence and changed no repository input.

Before teardown, exact IDs/images/read-only mounts/network/tmpfs/ports were
verified. Only `hr1_owner_final` and PostgreSQL technical databases remained,
with **zero other client sessions**; the failed pytest DB was already absent.
The exact task server was stopped, shutdown logged, then it and the one exited
runner were removed. Only disposable synthetic databases disappeared; they are
not recoverable. Logs and the pinned image remain. Unrelated Ecommerce
containers, demos and other repositories were untouched; no Docker prune.
No temporary continuation was created or left active for this attempt: failure
was observed before scheduling. No automatic retry or later gate may proceed.

Safe next checkpoint requires **separate owner direction** for bounded diagnosis
of this exact failed case on the same frozen inputs, measuring cumulative
admission stages/SQL latency and native/Audit rollback without altering budgets
or weakening the expected `AdmissionError`. Diagnose whether this was resource
refusal or another material defect before choosing any correction or subsequent
full-verification run. Do not label a green rerun causal proof or silently extend
the owner's exception to another unexplained failure.

Final integrity: original HEAD, parent/main/origin-main and held Phase 4 hashes
above remain unchanged; same 18 dirty corrective paths, zero staged files.
This attempt changes only the evidence document. No corrective commit/SHA,
push, PR, merge, tag, acceptance, canonical adoption or next milestone.
The final read-only remote check again returned only main at the HR-0 base.
Documentation validation passed: four relative file links, four heading links,
21 balanced fence pairs, final newline and no trailing whitespace. All 59
frozen inputs still match, the exact 18-path set matches and `git diff --check`
passes. Existing LF/CRLF normalization warnings are not formatter/source edits.

**HR1-AUD-1 CORRECTIVE IMPLEMENTATION: INCOMPLETE / NOT AUDIT-READY.**
**No corrective commit. Historical 57014 root cause: NOT PROVEN.**
**Fresh focused prerequisite: FAIL — 13 passed / 1 failed.**
**Full PostgreSQL/SQLite: NOT STARTED. Independent corrective re-audit: PENDING.**
**Hosted CI/canonical adoption: NOT AUTHORIZED. Phase 4: ON HOLD. STOP.**

## HR1-AUD-1 pending Attendance budget diagnosis

Date: **2026-10-20 Asia/Dhaka**. The owner's latest direct instruction authorizes
bounded root-cause diagnosis only of
`test_pending_attendance_cannot_be_completed_without_actual_initial_revision_insert`.
No production fix, test-expectation change, full regression, commit or publication
is authorized. The four P2 corrections and all preceding failures remain intact.
This record does not turn the earlier failed final-verification gate into PASS.

### Integrity and exact scope

Verified branch/HEAD: `phase3a-hr1-implementation` /
`e6b72896e10471463b8b6b280fbccfc524d7cc42`. Parent/main/origin-main remain
`b36cdba91654e6a583735d67f7f6cf27a835003e`; held local Phase 4 remains
`735e1bea13bc58fa71d430163422139d5c0f2363`. The same **18** corrective paths
listed in the exact inventory above remain dirty, with nothing staged. All
**59** code/test/template/build inputs match the earlier 58-value inventory plus
the recorded validation-test overlay. No production, test, schema, migration,
Core, frontend, accepted ADR 0018 or frozen HR-plan input changed in this batch.
Only this already-dirty evidence document changes inside the repository.

The complete retained failure log was inspected and its exact SHA-256 verified:
`4bb48bf18f9059baaa490bcd1947d9bd038bd78f9e3c966eb65bed627626fe32`.
The historical traceback proves a post-SQL cumulative checkpoint refusal during
`recorded_by` FK validation. It does not record that operation's budget timeline,
PID, SQL duration, effective GUCs or lock graph. Traceback-print timestamps are
not query-execution timestamps and cannot supply those missing measurements.

### Actual call stack and clock/protection semantics

The real target follows this path, without mocked services or returned effects:

```text
create_employee (separate completed setup operation)
-> explicit hr_operation(all twelve HR permissions)
-> Employee and Party actual lock_rows; new Attendance reservation
-> authorize -> _authorize -> first authority_started_at = monotonic()
-> verified authority relations / ROW SHARE NOWAIT / complete row prelocks
-> complete native final guards
-> nested create_department -> nested entry final guards (two action codes)
-> _setup_create -> op.authorize (existing outer twelve-code union)
-> Department validation/INSERT + success Audit within the outer transaction
-> private _create_attendance -> _insert -> Attendance.full_clean
-> ForeignKey(recorded_by).validate -> identity_user EXISTS
-> _execute post-SQL checkpoint -> Attendance INSERT/registration when admitted
-> complete_attendance_creation without an actual inserted Revision 1
-> AdmissionError / poison / whole outer rollback
```

The two-second clock begins in `_authorize()` immediately before the final
authority relation identity/prelock phase, not at the FK query or nested call.
Earlier source-identity pinning, Company/domain acquisition and initial checks
use the separate existing ten-second pre-admission allowance. A nested operation
reuses the identical state, alias, raw connection, outer transaction and
`authority_started_at`; it never starts a fresh two-second allowance.
The prior Employee setup has its own transaction/clock and is not work that the
failing subsequent outer unit should undo.

Before authorization the target has three declarations: Employee, Party and a
new Attendance UUID. Only Employee/Party are acquired existing-row locks; the
Attendance is a distinct new-row reservation. After successful actual INSERT,
Department and Attendance are registered as acquired rows. No declaration alone
is promoted to protection; no post-authority domain `FOR UPDATE` occurred in
either traced target run. The unauthorized completion call has no current
Revision-1 insertion attestation, so `_owns_insert` refuses it even if its
AdmissionError is caught. Poison and rollback-only remain set until outer exit.

### Instrumentation and fixed bounded execution

External `hr1_pending_budget_probe.py` delegates the original context manager,
stage functions, `ForeignKey.validate`, model validation and `_execute`. It
records real monotonic instants, the original authority-start value, remaining
budget, SQL/configuration durations, transaction/anchor states and outcomes.
It does not patch clocks, constants, Core authorization, expected exceptions,
native persistence or SQL return values. The only consumed cursor result is the
otherwise-unused existing `set_config` result specifically during Attendance's
`recorded_by` validation, to record actual effective local timeouts; no extra
settings query occurs inside the admitted work. The controlled Department-timeout
test's own settings observation is left untouched.

A separate read-only psycopg connection samples activity, blocking PIDs and
locks every 50ms. Sampling can miss brief waits. Independent complete native
snapshots of all six HR tables plus Audit run outside each outer admitted
operation, before entry and after outcome. Full field equality, not just counts,
is compared; record hashes/counts are retained. No recovery SQL is attempted in
the poisoned outer transaction. Instrumentation adds overhead; these timings
are diagnostic observations, not baseline performance/latency certification.

Both invocations were serial and used new disposable PostgreSQL test databases:

| Run | Actual result / immutable runner ID |
| --- | --- |
| Exact failing test alone, instrumented | **1 passed in 16.29s**, exit 0; `cb790d34793bc2d54d24ed509b09f7e7d3573bc00d5e6baccda848765846c756` |
| Fixed related set, instrumented | **8 passed in 30.92s**, exit 0; `3359d3b53f32202cdd94c30425575452fce97f963ce568753cd674cd6cb3c750` |

The related set includes the target again: nine total executions, **eight unique
tests**, not nine new unique cases. Exact options for each invocation:

```text
-vv -s --maxfail=1 --tb=long -p no:cacheprovider -p hr1_pending_budget_probe
```

The fixed eight node IDs use these existing unchanged tests:

```text
tests/test_hr_audit_acquired.py::test_pending_attendance_cannot_be_completed_without_actual_initial_revision_insert
tests/test_hr_audit_acquired.py::test_plain_existing_row_cannot_be_registered_as_freshly_inserted
tests/test_hr_audit_acquired.py::test_caught_new_target_refusal_rolls_back_prior_registered_insert
tests/test_hr_audit_acquired.py::test_new_attendance_reservation_is_not_an_acquired_existing_anchor
tests/test_hr_nested_services.py::test_catching_uncovered_public_nested_error_cannot_commit_prior_outer_evidence
tests/test_hr_nested_services.py::test_caught_nested_audit_failure_rolls_back_all_outer_updates
tests/test_hr_audit_validation.py::test_caught_early_public_validation_rolls_back_prior_effect_and_audit[selected-alias-record_employee_uuid]
tests/test_hr_audit_validation.py::test_selected_department_statement_timeout_rolls_back_and_does_not_poison_fresh_request
```

The locked QA image, Python **3.13.16**, Django **5.2.17**, pytest **8.4.2**,
PostgreSQL **17.11**, READ COMMITTED, read-only source/probe mounts and all three
existing commercial-install flags were used. No competing heavy verification or
browser-fixture startup was launched by this task. The observed new server was
`hr1-pending-diag-pg-e6b7289`, ID
`36123ec4c1ba8b881b5e76d2c04035d1eeea3a633714406cd7f9a5caa28a98b9`:
network none, tmpfs PGDATA, no ports or host data mounts. The new
`hr1_pending_diag` database had an explicit synthetic custody comment; each pytest
invocation created/destroyed `test_hr1_pending_diag`. Existing demos were not used.

### Measured monotonic timeline and FK/lock evidence

Time zero is the actual original `authority_started_at`: **387.864393114**
for the isolated target and **459.439444779** for the target in the related set.
Each run retained exactly one unchanged start value for this entire outer unit.
All numbers below are milliseconds after that origin, not wall-clock timestamps:

| Stage | Exact alone | Target in related set |
| --- | ---: | ---: |
| Two-second authority clock starts | 0.000 | 0.000 |
| Initial authorization returns | 227.13 | 198.50 |
| Nested entry's two-code final guards complete | 271.39 | 230.40 |
| Nested setup's complete twelve-code reauthorization returns | 474.08 | 633.90 |
| Department + success Audit return | 485.90 | 646.94 |
| Attendance.recorded_by validation begins | 492.40 | 655.29 |
| Attendance.recorded_by validation ends | 493.87 | 656.20 |
| Actual Attendance INSERT/registration returns | 500.05 | 661.58 |
| Intended completion AdmissionError raised | 501.27 | 662.74 |

At the intended refusal, **1,498.73ms / 1,337.26ms** remained respectively.
The isolated target's three native final-guard phases took approximately
210.49ms + 44.15ms + 200.92ms; the related target took
177.83ms + 31.79ms + 402.34ms. Those phases dominate these fresh operations.
The complete main outer unit made 492 instrumented application-SQL calls,
of which **367** were after the two-second clock began, in each run. Their
measured admitted SQL/configuration times were respectively
**183.27ms / 99.53ms** and **165.23ms / 84.91ms**. These components do not sum
to total wall time: Python/ORM work, gaps, scheduling and instrumentation also
consume the same cumulative clock. Inclusive nested stage times must not be
summed twice. Complete current guards and their fixed union were not reduced.

The actual FK SQL in both runs is the same template as the retained failure:

```sql
SELECT %s AS "a" FROM "identity_user" WHERE "identity_user"."id" = %s LIMIT 1
```

| Fresh FK observation | Exact alone | Related target |
| --- | --- | --- |
| Selected alias / PID | default / 78 | default / 85 |
| Native transaction state | INTRANS | INTRANS |
| Remaining before query wrapper | 1,507.24ms | 1,344.39ms |
| Actual local statement / lock / idle timeout result | 1508ms / 1508ms / 5s | 1345ms / 1345ms / 5s |
| Configuration round trip | 0.731ms | 0.220ms |
| Actual FK SQL duration | **0.285ms** | **0.268ms** |
| Remaining after wrapper | 1,506.17ms | 1,343.85ms |

No fresh unexpected budget/statement failure occurred. The isolated observer
captured 14 samples, zero observer errors and no observed blocking PID or
ungranted lock. User/Role/Permission relations had granted AccessShareLock and
RowShareLock modes; actual SQL contains their ordered complete FOR SHARE NOWAIT
prelocks. Lack of an uncontended tuple-lock row in `pg_locks` would not disprove
a held row lock. These sampled fresh observations do not recover a historical
wait graph or exclude every transient wait.

### Native rollback and timeout/session controls

Each target run observed one actual Department INSERT, one success Audit INSERT
and one Attendance INSERT, **zero** AttendanceRevision INSERTs, followed by the
required AdmissionError. At the caught refusal the same outer state was
INTRANS, atomic depth 1, no savepoint, `poison=AdmissionError` and rollback-only.
After exit the exact complete native baseline was restored across all six HR
tables and Audit: no prior Department, orphan Attendance, revision, Leave receipt
or added success Audit committed. The separately completed Employee setup and
its original Audit remained unchanged; their existence is not a partial commit
of the failed later unit. Connections were IDLE/autocommit, depth 0,
`needs_rollback=False`, admission cleared and settings restored to **0 / 0 / 0**
under READ COMMITTED on the same PID.

All **seven** failed outer operations in the eight-case related set independently
matched their full native baselines: four AdmissionError paths, one caught
ValidationError, one injected Audit RuntimeError and the controlled native timeout.
The reservation-only case is a non-effect success, not an eighth failed unit.
The tests' original own native/assertion oracles also passed unchanged.

The existing controlled test produced one deliberate 57014 on selected PID **104**:
actual remaining allowance **1.558618s**, statement/lock **1560ms / 1560ms**,
deliberate statement duration **1.565899s**. Its `pg_sleep(3)` augmentation, not
ordinary Attendance FK SQL, is the sole new server timeout ERROR. It proved
whole rollback, restored settings and a successful fresh real request on the
**same** selected session. This is deliberately induced error-path safety, not
reproduction of either unexplained historical incident.

### Causal assessment and smallest next proposal

**EXACT HISTORICAL BUDGET-CONSUMPTION CAUSE: NOT PROVEN.** The previous run
mechanically exhausted the accepted cumulative clock at a post-SQL checkpoint;
that mechanism is established. Why it crossed the threshold is not established.
The earlier unexpected native 57014 likewise remains NOT PROVEN. Neither new
target execution reproduced the resource failure, and green diagnostic runs
cannot retroactively prove host contention, slow FK SQL or historical GUC leakage.

| Classification | Evidence-based conclusion |
| --- | --- |
| Implementation defect | Not demonstrated by this investigation; real reservation/attestation refusal and complete rollback work in both fresh target runs. |
| Test/fixture defect | Not demonstrated; the unchanged strict AdmissionError expectation and original assertions pass. The broad twelve-permission composition is allowed, not an invalid fixture merely because it is costlier. |
| Legitimate resource exhaustion | The historical checkpoint enforced its real deadline and refused work; the underlying consumption source/operational conditions remain NOT PROVEN. This does not waive the failed verification gate. |
| Database contention | No supporting fresh blocker evidence; historical query timing/locks are unavailable. Not established and not excluded historically. |
| Budget reset, leaked setting or declaration-as-lock reuse | No such behavior observed; source and fresh state/timing/SQL evidence support one shared clock, scoped settings and actual acquisition. |

**Smallest recommended next correction is evidence/test-only, subject to owner
authorization:** strengthen this exact pending-creation test with explicit
reached-stage facts and full native/Audit readback in an outside-transaction
`finally` path, so an unexpected exception retains rollback evidence while the
test still fails unless the intended AdmissionError was reached. Retain the
strict exception, prior real Department/Audit effect and complete anchor/authority
union. Keep compact stage/SQL timing available for another unexpected deadline
event. This improves future diagnosis; it is not a claimed cure of the historical
failure. No behavior-changing production correction is justified by these data.
Do not weaken complete guards, shrink permissions merely for a green run, bypass
FK validation, reset the clock, increase timeouts or change the expected error.
Any later full verification requires separate owner direction after this review.

### Retained diagnostic artifacts and final custody

The following **15** new external records are under the previously recorded
visualizations root, not in the repository candidate. Complete JSON traces retain
all stage events, every instrumented SQL/configuration timing and observer samples.
Runtime-generated JSON was copied from each exited container before teardown;
complete timestamped stdout/server logs were saved without truncation.

```text
17ea55cdc4c65128e98384034523d955f33d4b25e8edc91f58fe7bdcd03a1cfc  hr1_pending_budget_probe.py
4cc671eca8173b15f548089d1f5e43b327185f2a951d00d2ea9601877234f281  hr1-pending-exact.json
b5ccf7f6275412b74dc4a8557d89756e43d5570d6a8f1b53543644023ebe0da4  hr1-pending-exact.log
53d07ffa3baffa25de13fe7447a4f0d549e9d2880a340d8c17d9566f5bdb25dc  hr1-pending-related.log
2e0628e85741a28578c7831486a4930969ef313b8a8f4de2e4a8f1243db32f76  hr1-pending-server.log
a44130afe04687c63fad45cd244b2e5ef88610b0eca950c82c7e4909f2ffd75a  hr1-pending-container-evidence.json
09063230e4a288b8bec008882fa2aa9a75b80a2bee53f8c374cdc34cb3b6c586  hr1-pending-shutdown.log
99056aff2bb4633fb8f02106b0ee18729d1ec4b59c1edf14d0cf6397ff1e799a  hr1-pending-related-records/18edb195b42220ca.json
297390db405ca71d69859fd4c1d75421fbebe157c83cc4ec1f0d332a0f604ffc  hr1-pending-related-records/2e87793bd16257c8.json
ac2249f99375c7163a2a676b126189672d726e2ec22fa686b8a8f20c8200feca  hr1-pending-related-records/5a1c3db06bffe0f0.json
d71805461a038578833398f2c27e0138df1ed65f96d706512c200ae99c34176e  hr1-pending-related-records/919dab86df725b06.json
86f8ea79b84dcc73f5b3c44519fafb52798631a7e93b0b965a7eed2b9cadd7e8  hr1-pending-related-records/9700bc2dcc8ddfee.json
883f3151dde4507fd1deba29adca8c85f6148bed39aad37ed81115adc8d5b3cd  hr1-pending-related-records/b1d1283f39ef22bf.json
cb8a2408e66576e12ce20e7bfd50f9199c4a26a805819c5b0f63febe9cfbe0bc  hr1-pending-related-records/bd964c9c707d9228.json
89fd660b1802b95132aa49c6235696af76feb8ba2f141dff2f8bc33464db76bd  hr1-pending-related-records/c4d8de9b8c3faf29.json
```

The first PowerShell summary-reader invocation had a pipeline parse error;
correcting that read-only summary command did not rerun or change a test.
All eight JSON records were then parsed, and raw results/rollback summaries
cross-checked. Prior audit/failure/diagnostic records were not overwritten.

Before cleanup, exact three container IDs/images/mounts/network/ports were
verified. Only the custody-commented synthetic application DB and PostgreSQL
technical DBs remained, with zero other client sessions. The task server was
stopped, shutdown logged and only those three containers removed. Their synthetic
databases are not recoverable; logs/traces and the pinned image remain. Existing
demos, unrelated Ecommerce containers, PAY-1, target repository and Phase 4 were
not modified. No broad Docker cleanup, full suite, browser run or automation.

Final branch/HEAD/main/origin-main/Phase 4 identities above remain unchanged;
the same 18 dirty corrective paths remain, with zero staged files. Only this
evidence document changed in-repository; no code or test fingerprint changed.
No reset, clean, stash, rebase, commit, push, PR, merge or tag occurred.
Final live read-only verification returned main at the same HR-0 base and no
remote HR-1/Phase 4 branch. All 59 input and 15 new artifact hashes match.
Documentation checks pass: four relative file links, five heading links,
26 balanced fence pairs, final newline/no trailing whitespace, and
`git diff --check`. No unchanged full regression or application quality suite
was rerun for this diagnostic-only documentation update.

**BOUNDED DIAGNOSIS COMPLETE. Historical consumption cause: NOT PROVEN.**
**Fresh target refusal/whole-outer rollback: PASS. Full corrective readiness:
INCOMPLETE / NOT AUDIT-READY. Independent re-audit: PENDING.**
**No production fix applied. No corrective commit. Phase 4: ON HOLD. STOP.**

## HR1-AUD-1 frozen verification interruption and safe continuation checkpoint

Date: **2026-10-20 Asia/Dhaka**. This is an append-only implementation-run
record, not an independent re-audit or approval. It supersedes no historical
failure evidence. The owner's verification-continuation authorization allowed
one bounded test hardening, serial focused gates and conditional full suites.
The owner's latest instruction authorizes completing this interrupted evidence
record only: **no test rerun, code change, commit, push or main update yet**.

### A-B / R: preserved candidate and Phase 4 identities

Verified before progression, throughout scheduled checks and after interruption:

- Branch: `phase3a-hr1-implementation`.
- HEAD: `e6b72896e10471463b8b6b280fbccfc524d7cc42`.
- HEAD parent, local `main`, `origin/main` and `phase3a-hr-contract`:
  `b36cdba91654e6a583735d67f7f6cf27a835003e`.
- Held local Phase 4:
  `735e1bea13bc58fa71d430163422139d5c0f2363`, **ON HOLD**.
- Same **18** preserved dirty paths below; **zero staged**; no corrective commit.
- Read-only live `git ls-remote` returned the same main/HR-0 heads and no
  remote HR-1 or Phase 4 head. No fetch/ref update was needed.
- Sandbox Git once reported “must be run in a work tree”; an explicitly
  read-only escalated check resolved the actual checkout and verified its state.
  This command/environment issue was not a source or ref change.

No Core, Identity, Access, other owner, accepted migration, settings, manifest,
frontend, ADR 0018, frozen HR plan, PAY-1, demo or target-repository change was
made during this hardening/verification batch. The nine existing production
corrective paths remain byte-identical to the pre-hardening freeze.

### C-D: authorized test-only hardening and input freeze

Only `tests/test_hr_audit_acquired.py` changed in this continuation before
verification; only the exact pending-Attendance test and necessary local imports
were hardened. The real service, native transaction, twelve-permission union,
foreign-key validation and accepted two-second cooperative budget remain intact.

The test now proves a real prior Department and its exact success Audit exist
only inside the outer transaction; a genuine private Attendance parent insert
has reached the post-parent/pre-completion stage; and no genuine Revision 1 was
inserted. It catches the real completion refusal
(`Attendance initial revision has no pending parent insertion.`), verifies the
same operation is poisoned and rollback-only, and performs no recovery SQL in
that poisoned scope. Outer exit independently refuses the incomplete insertion
(`An Attendance insertion has no complete initial revision.`). These are
distinct production AdmissionError instances; exception-object identity is not
fabricated as an oracle.

An outside-outer-transaction `finally` reads every concrete field of all six HR
models and Audit using the selected alias. Exact baseline equality proves no
orphan parent, revision, receipt, added success Audit or prior Department effect
survives. The separately committed setup Employee and its original Audit remain
unchanged. The same raw connection, selected alias, cleared admission,
autocommit, empty atomic/savepoint state, no rollback flag, PostgreSQL IDLE and
original statement/lock/idle/isolation settings are verified after rollback.

The acquired-test fingerprint changed from
`e9659c5e208a02a0125f8cd5d549e83b1cf1fb9fef1e84f4848798290d718a85`
to
`c39b5c1c409c3ead9df676c43372a5de2b51b973b40ddb8d9eced0288b4ed298`.
The earlier validation overlay remains
`5f818b4b160d7cd7b6670f6af4623cb27692bf434f4cd11152a7c8d2a715f923`;
its preceding historical fingerprints remain above. All other 57 inputs are
unchanged. The only formatter write was the authorized acquired-test file,
before freezing; its local Ruff check passed. No implementation/test input was
edited during or after the following verification.

The exact **59-input** external manifest is
`hr1-hardening-frozen-inputs.sha256`, SHA-256
`9415b9cf5b4e6df60b786c8e1662fcbcdd2ed17cb746ce96bd34e2517b9e1a29`.
It was verified before each progression and again for this evidence-only update.
The final current inventory is reproduced below without rewriting old records.

### E-H / K / N: actual executions and separate limitations

All runs were serial, without task-owned competing heavy verification or browser
startup. Source and external probe mounts were read-only. The locked QA image
`hr1-local-qa:b36cdba` is
`sha256:a7a3476a1883cddc11d7c9bcf7d7674c5c9396211f2b654337a58a1c9936637f`:
Python **3.13.16**, Django **5.2.17**, pytest **8.4.2**, Ruff **0.16.7**.
The actual isolated server was PostgreSQL **17.11**, Linux Docker, network none,
tmpfs PGDATA, no host database mounts or published ports. No customer/demo data.

| Gate | Actual result / immutable runner identity |
| --- | --- |
| Exact hardened pending-Attendance test | **1 passed in 24.13s**, exit 0; `hr1-hardening-exact-pg`, `721eaab7a17cd91e55039664daa4360bcea189900af86e0e102226112a7c222e` |
| Focused PostgreSQL | **649 passed in 397.64s**, exit 0, no skips; `hr1-hardening-focused-pg`, `9d6befb60a4205ed34687b9c410fe792b843bdeadb1271c81c63f01e6202a9db` |
| Focused SQLite | **567 passed, 82 skipped in 118.76s**, exit 0; `hr1-hardening-focused-sqlite`, `fee59e6fbf41a3aec5e315891dcddae14ca39227c4c67e1ed98285e01a310aa2` |
| Full PostgreSQL | **INTERRUPTED / NOT PASS**, exit **255**, 4,326 collected, **4,313 explicit PASS markers**, no terminal pytest summary; `hr1-hardening-full-pg`, `550449680d38073129c99d2296c76a4776ab4e934d933b6f72a47ae02bb61be0` |
| Full SQLite | **NOT STARTED**: required full PostgreSQL success unavailable |

The 82 focused SQLite skips are all explicit PostgreSQL-only requirements:
two RLS/catalog, two relation identities, one shadow relation, one genuine
57014/session-restoration control, one independently held domain-row lock and
75 PostgreSQL relation/row-lock/catalog admission cases. They are not missing
portable functionality or evidence of PostgreSQL concurrency from SQLite.

The exact test used the already retained bounded
`hr1_pending_budget_probe.py` only for that invocation. Its fresh trace reaches
the intended completion AdmissionError at approximately **722.94ms**, with
approximately **1,277.06ms remaining**; the same outer native baseline and
settings are restored. The earlier **501ms / 663ms** observations and their
**0.285ms / 0.268ms** FK durations remain historical measurements, not new
numbers for this run or proof of an old cause.

Focused/full PostgreSQL used external `hr1_corrective_watch.py`: bounded recent
SQL/configuration parameters/durations, alias/PID, transaction/budget state,
call stacks and read-only sampled activity/blocking PID/ungranted-lock evidence.
It delegates actual production checkpoint and execution without changing clocks,
budgets, SQL or outcomes; it fails the session for an unapproved resource event.
Sampling/instrumentation has overhead and can miss short waits. Requested GUC
parameters in this watcher must not be misrepresented as a separate session
settings query. The exact-test probe and controlled timeout test separately
capture actual effective settings.

Each PostgreSQL run retained seven watcher records, all belonging to three
predeclared controls: artificial cumulative-clock exhaustion, real Django
constraint-check 57014 swallowing and selected-alias genuine 57014 cleanup.
Multiple records can describe the same exception propagating through layers,
not seven independent incidents. The selected-alias control proves rollback,
settings restoration and a fresh successful request on that same session.
The server's two deadlocks per focused/full run correspond by timestamp to the
two explicit rejected-old-protocol negative controls, whose tests passed.
No unexpected HR budget/native-timeout/deadlock event was recorded before the
interruption; this is not proof about an unobserved final process state.

**Both earlier historical causes remain separately NOT PROVEN:** the original
unexpected native 57014 and the later cumulative ResourceBudgetExceeded. Owner
authorization permitted progression without reconstructing those past causes;
it waived no current requirement. This new exit-255 interruption is a third,
distinct event, not an established reproduction of either earlier incident.

Focused argv, preserving its actual file order (pytest may reorder execution):

```text
pytest tests/test_hr_audit_validation.py tests/test_hr_audit_history.py tests/test_hr_audit_persistence.py tests/test_hr_audit_acquired.py tests/test_hr_admission.py tests/test_hr_nested_services.py tests/test_hr_history.py tests/test_hr_civil_time.py tests/test_hr_models.py tests/test_hr_services.py tests/test_hr_flows.py -vv -s --maxfail=1 --tb=long -rs -p no:cacheprovider -p hr1_corrective_watch
```

Exact-test argv adds only its node ID, `-vv -s --maxfail=1 --tb=long`,
`-p no:cacheprovider -p hr1_pending_budget_probe`. Focused SQLite uses the same
eleven files/options without the PostgreSQL watcher and with
`DJANGO_SETTINGS_MODULE=config.settings.test`, network none and a fresh
in-memory application test database.

PostgreSQL uses actual supported `config.settings.development` with all three
existing commercial-install flags set to 1, host `127.0.0.1:5432` in the task
server's isolated network namespace. The fresh custody-commented application
databases were `hr1_hardening` and subsequently `hr1_hardening_full`, with new
pytest databases, synthetic-only operator and no customer-derived records.
Actual full-run command, with pipefail preserving nonzero outcomes:

```sh
bash -o pipefail -c '(python manage.py migrate --noinput && pytest -vv --maxfail=1 --tb=long -rs -p no:cacheprovider -p hr1_corrective_watch) 2>&1 | tee /tmp/hr1-hardening-full-pg.log'
```

### Interrupted full-gate facts: cause NOT PROVEN

The full runner started at **14:31:32.039566712 Asia/Dhaka** and its metadata
records finish **16:13:58.711694055**, exit 255, `OOMKilled=false`,
empty Docker State.Error. The task PostgreSQL server
`85842223c6d646a2419cfa80fd4afba407c505988fe4fb8bca05179f08f8df55`
records finish **16:13:58.708567333**, exit 255, `OOMKilled=false`,
empty State.Error: approximately **3.13ms** apart. These are container lifecycle
timestamps, not pytest duration or query timing.

The last retained PASS is
`test_installation_topology[postgresql-unsupported-1-1-0]` at
**16:11:41.117784572 Asia/Dhaka**. No pytest failure traceback, completion
summary or successful test-database teardown followed. Thirteen collected cases
have no observed PASS result. The last server lines are ordinary checkpoint
completion; no shutdown/PANIC/FATAL at the exit is recorded. A bounded Docker
events query over the observed exit interval returned no retained events.
Current Docker reports 29.8.2 / Docker Desktop / WSL2; that does not establish
a historical daemon restart, Windows action, OOM, deadlock or actor responsible.

**Immediate blocker:** the full verification process and isolated database both
ended without a successful terminal result. **Underlying cause: NOT PROVEN.**
It would be inaccurate to call this a demonstrated HR implementation defect,
a proved Docker restart, or a successful 4,326-test run. No replay/rerun was
attempted. The lost tmpfs database prevents new native readback of that final
interruption; final transaction/Audit/session state for that event is NOT PROVEN.
The successful exact/focused rollback oracles are retained, not substituted.

### I-J: executed matrix evidence, not collective gate approval

The interrupted full log contains **1,311 HR PASS-result lines** across 24 HR
test files. Entries below are checked against that log and the already named
case-specific implementation oracles above; no inherited PASS is promoted to
a completed regression gate. PASS here means the stated executable local
oracles ran; independent review remains pending for every requirement.

| H ID | Current actual local evidence / status |
| --- | --- |
| H01 | Executed scope/RBAC/HTTP oracles PASS: permissions 377, HTTP 126. |
| H02 | Executed Branch scope and domain-race oracles PASS: Branch 8, concurrency 16, domain races 24. |
| H03 | Executed Party/identity/immutable-model oracles PASS: identity races 12, models 284, adversarial 24. |
| H04 | Executed setup/lifecycle/unique/reference race oracles PASS: services 20, reference races 20, identity races 12. |
| H05 | Executed exact compound/self-decision oracles PASS: permissions 377, self decisions 16. |
| H06 | Executed registration/module/HTTP oracles PASS: models, installation contract 19, HTTP 126. |
| H07 | Executed selected-alias/default-trap/nested oracles PASS: admission, acquired, validation and permissions. |
| H08 | Executed interval/conflict/resource oracles PASS: flows 13, domain races 24, resource boundaries 2, history 36. |
| H09 | Executed civil/fold/boundary oracles PASS: civil time 81, corrective history 38, HTTP and history. |
| H10 | Executed complete-chain/private-persistence oracles PASS: history 36, corrective history 38, persistence 16, models 284. |
| H11 | Executed Leave/receipt/lifecycle oracles PASS: flows, services, self decisions, adversarial and civil time. |
| H12 | Executed T oracles below and read-path revocation PASS: read authorization 12 plus domain/reference/identity races. |
| H13 | Executed admission/budget/namespace/protection oracles PASS: admission 97, acquired 14. |
| H14 | Executed native/Audit/outer rollback oracles PASS: nested services 5, setup rollback 6, adversarial 24, validation 45, acquired 14. |
| H15 | Executed HTTP/form/permission oracles PASS; fresh real-browser/frontend validation is still NOT RUN. |
| H16 | NOT RUN for this corrective freeze; previous original browser evidence is historical only. |
| H17 | PARTIAL: initial full-topology migration/bootstrap and installation test oracles ran; post-full-suite standalone verification not advanced. |
| H18 | BLOCKED: no terminal full PostgreSQL PASS; full SQLite and final quality/browser gates NOT RUN. External re-audit/CI/acceptance/adoption pending. |

T case names resolve to `tests/test_hr_admission.py` (A) or
`tests/test_hr_concurrency.py` (C), with full names in the original traceability
table above. The following counts are actual full-log PASS matches where stated.

| T ID | Actual executed oracle / current result |
| --- | --- |
| T01 | A original blocking-User-order negative control PASS (one deliberate 40P01). |
| T02 | A public Employee HR-first User writer wait, two cases PASS. |
| T03 | A writer-first unordered User batches, two cases PASS. |
| T04 | Actor=link member of T02 PASS. |
| T05 | Actor!=link members of T02/T03 PASS. |
| T06 | C inactive removed-User lock, two cases PASS; relink winner-order cases PASS. |
| T07 | A original User-only mixed-authority negative control PASS; actual mixed-authority batch winners PASS. |
| T08 | A mixed Role/Permission writer forms, ten cases PASS, plus unrelated authority compatibility. |
| T09 | A Company-wait revocation matrix, three cases PASS; C HR-first revoker oracle PASS. |
| T10 | A post-domain-wait authority matrix, three cases PASS, plus permission/assignment revocation. |
| T11 | Actor member of post-domain-wait matrix PASS. |
| T12 | A compatible independent Companies, two cases PASS. |
| T13 | Shared-actor member of T12 PASS. |
| T14 | Disjoint-actor member of T12 PASS. |
| T15 | A existing-superuser namespace, two cases PASS. |
| T16 | A admitted nested subset PASS; acquired 14, nested service 5 and corrective validation oracles PASS. |
| T17 | A actual nondefault PostgreSQL alias/default-cursor trap PASS; nested alias-switch refusal PASS. |
| T18 | A User/Role/Permission NOWAIT rollback, three cases PASS. |
| T19 | Real constraint-check 57014 control PASS; full-outer validation/Audit/receipt rollback oracles PASS. |
| T20 | C historical correction retry with current revocation, two cases PASS. |
| T21 | A repeated hot-Role refusals then fresh request PASS. |
| T22 | A Role share-read compatibility PASS; T12 compatible Companies PASS. |
| T23 | A supported Identity writer forms, twelve cases PASS; T03 both User batches PASS. |
| T24 | A active/inactive Role/Permission reversed writers, eight cases PASS. |
| T25 | A native Sales/HR compatibility, both winner-order tests PASS. |
| T26 | A implicit relation-lock negative controls and explicit relation admission, three tests PASS. |

These executed results do not satisfy the interrupted full-suite, H16/H18 or
independent audit obligations. **Overall local corrective readiness remains
INCOMPLETE / NOT AUDIT-READY.** The four original P2 regression families passed
their focused and observed full-run cases; their independent closure is not
granted by this record.

### L-M / O-P: checks, scope and retained evidence

After the interruption, no application regression, Ruff suite, format write,
Django check, drift command, new bootstrap or browser fixture was launched.
The post-full-suite quality/frontend/browser gates remain pending. Original
browser results, earlier Ruff/Django/drift and historical full suites remain
dated historical evidence only. Documentation integrity, exact hash/path/ref
checks and Git whitespace checks are the only current completion checks.

Exactly the following 18 corrective paths remain preserved; the current
evidence-completion instruction changes only this already-dirty document:

```text
businessos/modules/hr/admission.py
businessos/modules/hr/civil_time.py
businessos/modules/hr/conflicts.py
businessos/modules/hr/history.py
businessos/modules/hr/persistence.py
businessos/modules/hr/selectors.py
businessos/modules/hr/services/__init__.py
businessos/modules/hr/services/attendance.py
businessos/modules/hr/support.py
docs/exec-plans/active/HR_1_IMPLEMENTATION_EVIDENCE.md
tests/test_hr_admission.py
tests/test_hr_history.py
tests/test_hr_models.py
tests/test_hr_nested_services.py
tests/test_hr_audit_acquired.py
tests/test_hr_audit_history.py
tests/test_hr_audit_persistence.py
tests/test_hr_audit_validation.py
```

All artifacts below are retained outside the repository under
`C:\Users\HP\.codex\visualizations\2026\09\13\01a09a3b-7a01-72e3-86bc-21a752d748fc`.
Complete timestamped runner/server logs were retrieved in bounded windows to
avoid tool-output truncation; raw tee output and all fourteen control JSON
records are also retained. A first overlarge read window was truncated and was
discarded, then smaller read-only windows captured the full logs; no tests were
rerun. A Docker inspect template initially referenced an absent runner Tmpfs
key; structured inspect then retained all five actual records successfully.
These are evidence-retrieval issues, not application failures or new tests.

The external artifact manifest `hr1-hardening-artifacts.sha256` has SHA-256
`cb32f4ba4968e863908b0802bae98619d2b5727c6a60d7dbeb8c67d91ce287f0`.
It records the following immutable files (excluding itself):

```text
776b4ac224a02f4ccb9920b8ef86213e946352079f663dcc5dc0781c30aa9069  hr1_corrective_watch.py
17ea55cdc4c65128e98384034523d955f33d4b25e8edc91f58fe7bdcd03a1cfc  hr1_pending_budget_probe.py
31602d1557e476b3260dc99fe1001f22b80b37d5ae17a9aec1f908541445a388  hr1-hardening-container-evidence.json
1c72053a2a70b01bca82e3ad9fcdccc594fb93f0ed51de0aae1f1b18ccbfd211  hr1-hardening-exact.json
9c763803b6a7719898011c147f4d1f232d3ef298d496c463a90845e95f8318c0  hr1-hardening-exact.log
b472f2fd44e85dc4205255b21b5a017b59483d381f6d2a0bddd6bb77c7f57207  hr1-hardening-focused-pg-watch/2e87793bd16257c8-1.json
2051686c5bb712c4fb7b45560ca23173f08edb4148cc3c8e98d0f9fe76ca4a60  hr1-hardening-focused-pg-watch/2e87793bd16257c8-2.json
21c3748b7ab4e46023f45059b59522680061438bfcf6a3979f2a63b6d367ff33  hr1-hardening-focused-pg-watch/6116d0798cd92431-4.json
6ef1cc901b6b43ab1b51b3667a16c52dd80724b62774b7b24200ab98ac8df03d  hr1-hardening-focused-pg-watch/6116d0798cd92431-5.json
edf2a521accd2a638ef9a6d1d822ed4dc5cbc9cc652b9b6161c8fd556eedfbc0  hr1-hardening-focused-pg-watch/6116d0798cd92431-6.json
6dc4204d88ca174db25b723919cea45daecfdb8c500ab0f1322198fe55552ef4  hr1-hardening-focused-pg-watch/6116d0798cd92431-7.json
ea76d6ba95c7672fffc5e3c341ec121187e2193a4675065fda6522cd16f0f866  hr1-hardening-focused-pg-watch/c45074df55216ca6-3.json
3fe4ac7a01e83f1a2408635a1cb49bcab8d1b26a90f701eaf54d12164edf45db  hr1-hardening-focused-pg.log
5e719429e21ce19f0b88d1f78f526ad484b3c60d26c2271434b277a71f5dd58e  hr1-hardening-focused-sqlite.log
9415b9cf5b4e6df60b786c8e1662fcbcdd2ed17cb746ce96bd34e2517b9e1a29  hr1-hardening-frozen-inputs.sha256
f7ab750da6b989eb35e4f2663254a1a47b17343ad607d37a5e65f99cfb98e27d  hr1-hardening-full-pg-exit-tail.log
d45516bc7812db1c2432c8c7e8c39e64485adc5f5677bf1ef263633899396e46  hr1-hardening-full-pg-timestamped.log
b26d5d9b5a4161ddf11229cd141f7caa9111363359eeb4364e12bf1ed8889450  hr1-hardening-full-pg-watch/2e87793bd16257c8-6.json
b648e5dc5a3fca8aa7fa5c6aebad9b9475ff85fd84869b4a7cb17d4f5d0f5dbc  hr1-hardening-full-pg-watch/2e87793bd16257c8-7.json
8d1f8905e7d47ad9b06969f717246a79a03a78dde472219679fca1de02ea063b  hr1-hardening-full-pg-watch/6116d0798cd92431-2.json
1d2953857525f7e45e4f3608e5c678452abd93b32f6e54bab556296141948d00  hr1-hardening-full-pg-watch/6116d0798cd92431-3.json
189282b12429e2434ea3fdba10dd4e7c54fb3da917d75f71b9aad3a2a51f600d  hr1-hardening-full-pg-watch/6116d0798cd92431-4.json
33558a85badb0620a37adc4e7797faec1ade27af2b69346ec0bece7ab969e452  hr1-hardening-full-pg-watch/6116d0798cd92431-5.json
6b2e468137344e7182563001cf0c68e83a06e02613921460f7477e660c029746  hr1-hardening-full-pg-watch/c45074df55216ca6-1.json
76fd901156faed01495764080678f468d020f927af8ef6b062ee9269f4ef747e  hr1-hardening-full-pg.log
7079c14a1657534946c21559bcf7003cda8170e3df28b9f89892b5c8255d61ab  hr1-hardening-server-exit-tail.log
2f6ed7f511696b2fb6ec01814c50a412200e4968711ece800ac12cc3ebde3589  hr1-hardening-server.log
```

### Custody, automation and safe stop

Before cleanup, all five exact IDs, pinned images, read-only runner mounts,
server tmpfs/isolation and stopped/PID-0 states were verified. Only these
task-created containers were removed with ordinary `docker rm`; no force,
Docker prune, image deletion or unrelated-resource cleanup. The synthetic
tmpfs database state is no longer recoverable; complete retained evidence and
the locked QA image remain. Existing demos, unrelated Ecommerce resources,
customer-migration work and target repository were not touched.

The explicitly authorized temporary ten-minute heartbeat was deleted after
the blocked result; its automation configuration is absent. There is no
scheduled rerun. The OpenAI Docs skill was used for scheduling management only,
not as implementation or correctness evidence.

### Exact safe continuation plan — proposed, NOT authorized by this record

1. Obtain a new explicit owner instruction to resume after this exit-255
   interruption. Do not treat historical authorization or a heartbeat as an
   automatic retry. The owner may first request a bounded read-only Docker/host
   interruption investigation; current evidence does not prove its cause.
2. Reverify branch/HEAD/parent/main/origin-main/live remote, the exact 18 paths,
   zero staged, the held Phase 4 SHA and every one of the 59 frozen input hashes.
   Preserve the separate historical failures and the current interrupted log.
   Any code/test change needs separate authority and invalidates affected gates.
3. Verify the QA image identity, Docker availability and isolated-resource
   configuration. Create a **new** restricted, custody-commented synthetic tmpfs
   PostgreSQL fixture with new container/database names. Do not restart/reuse the
   lost fixture or an existing demo/customer database.
4. Only if expressly reauthorized, run the complete PostgreSQL gate **once**
   from fresh migration/bootstrap, serially, against these unchanged inputs:
   `python manage.py migrate --noinput`, then the recorded full pytest command
   with maxfail=1 and bounded causal observation. Require actual terminal exit 0,
   all 4,326 collected cases accounted for and no unexpected error/skip.
   The 4,313 markers cannot replace this gate. Do not run only the last 13 cases.
   Retain the focused PASS evidence as a prerequisite only while hashes/profile
   match; rerun focused gates only if newly authorized or their inputs change.
5. Only after full PostgreSQL PASS, run full supported SQLite once, recording
   actual passes and explicit skip classifications. Do not extrapolate its
   result from the 567-case focused run or old full-suite counts.
6. Only after both full suites PASS, finish the already specified Ruff,
   explicit baseline-to-candidate changed-Python formatting checks (including
   migrations), Django/drift, fresh schema/registration/architecture/security,
   frontend/JS/Tailwind reproducibility and affected real-browser workflows at
   390/768/1280. Reconcile final H01-H18/T01-T26 evidence and fingerprints.
7. Stop immediately on any unexpected timeout/budget/deadlock/material failure;
   preserve causal evidence and do not loop until green. Keep the two-second
   budget, all guards, the four P2 corrections and Phase 4 HOLD unchanged.
8. **No commit is authorized by the latest evidence-only instruction.** After
   every gate passes, request explicit owner direction for the one additive
   local corrective checkpoint before staging. A later authorized commit would
   have parent `e6b72896e10471463b8b6b280fbccfc524d7cc42`, the exact 18 paths
   and message `fix(hr): remediate HR1-AUD-1 correctness findings`.
   Fresh independent corrective re-audit follows that checkpoint. Hosted CI,
   acceptance and canonical adoption remain separate gates; no push/main update.

### Current 59 frozen input fingerprints

```text
029237c4b764f5fe7d07fe19d72f3bbd5f43d6ed6b14d10b33ff5e2058756919  businessos/modules/hr/__init__.py
78bc17826f2dadabec1de9ef8c52a64ebf3056945fc094923152fba2a01b2f1f  businessos/modules/hr/admission.py
b2654ecded6f79c5e9c42778a2e9cb44cf24090acf25237ce0846cfeebefba6b  businessos/modules/hr/apps.py
f29a74c79d8fba13f2f413ffc593661500055c6162a816dabab69e0317f8d1c1  businessos/modules/hr/civil_time.py
37ce3ce0b956345c7aca1d214ecbba296328d8819a81104ea356b115a8bfc8f1  businessos/modules/hr/conflicts.py
e7e221a7a4f7ad28d614a72ef622eb62aa39ef78b4c0643cc7d71fadf89f4f84  businessos/modules/hr/domain.py
5a9588c5553de07eacfeb23498a9a2e38b742361d3905867eabecedc9dc515bb  businessos/modules/hr/forms.py
a0285e935e08dc91f7daaee85156ea8623d5c5733d2f44ab35c2bb5d68f611b2  businessos/modules/hr/history.py
71dbdd47d589cda99093418400d82255bda33579889360a4cea3aa2517442647  businessos/modules/hr/manifest.py
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  businessos/modules/hr/migrations/__init__.py
2de582ba9d1d2c598fa3b3d5f047d751d9e1397614e29343695448b9a12b648f  businessos/modules/hr/migrations/0001_initial.py
e0087a18ec74214d5d40be727d4ae00f171203f6ea643db88709901976b3a63b  businessos/modules/hr/migrations/0002_register_manifest.py
e037a789d76903d02cec9d9c033fa026accc8e068b1ebdad397badce129b7f00  businessos/modules/hr/models.py
4095f53d6e63d5a2f0ba67f76bb86667b1fe4dddc71f8612fb9e482d08753ba7  businessos/modules/hr/persistence.py
b101a75d1229ecb42bbe85570c46a3e0bda76dfdaf8673f564cee32508ee88db  businessos/modules/hr/selectors.py
6b20c89a82251aa14f9ca9ab9a1695ed09bfd8294295f2e2a31b8dd775802ba3  businessos/modules/hr/services/__init__.py
c37622f7fa866d36f247347d5c580abb25d35158fde78fb36e82f336ae864d41  businessos/modules/hr/services/attendance.py
9e222b3c12c67bb1c21f19870b2e1ad70e469fa260e47ed4f5b311e44862015a  businessos/modules/hr/services/leave.py
d69f9fb11f48e756ee2d427611d8a42e235585b2fcafa72daad1a4a959a850a6  businessos/modules/hr/support.py
7571bd0ec3bdfd92e708c1b3624a3eed30b3d290cfda23d89a66df111c6fefba  businessos/modules/hr/urls.py
243d2f3132f55dd0f68ef71b5c72edfdfe122b5bdc360c1845d112c42018109c  businessos/modules/hr/views.py
7542df586219cdfcceb496c50a9c9a3e49e4d951653e2b0f2107514e1adcbf72  config/settings/base.py
d11769617ed3eb6d2ace3b0cf499e7175ae89ca02758ff9e618f42d29b23c185  config/urls.py
a7c650044ad3e2b11df25f8c84e749a2c3f0fd3d1a55edff6f974f7061219cae  static/css/tailwind.css
082f69f44d123bf736b63175beb3c611e0da9c6c3ee905805ee1ba7ccd57b303  templates/components/header.html
92ae30232b4577f428da0418a3d84ba5529e305cc8e7cd29c5b225199151c2a4  templates/components/sidebar.html
ef2ed05f3c9d4df622a4b4e7a8c6e4517725658660973ccbcb8201be725b72a4  templates/core/home.html
7450c0cc9e80390f3e588e7bd2fdfb34122c8f6a89bb068e0ecd31f9eff76fa6  templates/hr/detail.html
6da7e5dc5c6b07a11bc02638052f63d548172b51582373690cd85d43f9bd1534  templates/hr/error.html
f593ecdb1690edd5b5ba6744e78cd9efd4b9525e98634d1507ff38e99f393390  templates/hr/form.html
91bb65d0b40023902924c2992658721099209a31f89e9bbe5ff1d48a2c386a49  templates/hr/list.html
425de6402f1892f37a7d4939dcfb3e8b8110dda1039074ef393c5f40d54b5ca6  templates/hr/menu.html
753d24d9685e4b6975554dfcf71552d9b79185e3ecf05473e17f47a58f0c9f94  templates/hr/navigation.html
c3a0ddb2213a0eeb30dece2e24eb0ff0950388c72fe14fa81c279abc6ce7ecbc  templates/hr/revisions.html
35b7457e301ddbee6ecc4edd618bab49842127355faeff7c8ee58d09cce77aff  tests/test_database_foundation.py
420c74d6edf38deba726c5f9bd8f4f61bfd2222fdd6f25d54c13cf67ac1e3267  tests/test_hr_admission.py
a1a0123311dd13787c910dc840ba046ddc6f4b6f352e9b7a2fb65a20797f4089  tests/test_hr_adversarial.py
c39b5c1c409c3ead9df676c43372a5de2b51b973b40ddb8d9eced0288b4ed298  tests/test_hr_audit_acquired.py
874a3c98c5f0b0ab3194252cd4d04a5bb4f9bbaacec9ef131b4882ae8194bfcf  tests/test_hr_audit_history.py
1a02903c4fe1f711591e6a361b7a7e03ff4065785dc4caed41c58e94a6dcce96  tests/test_hr_audit_persistence.py
5f818b4b160d7cd7b6670f6af4623cb27692bf434f4cd11152a7c8d2a715f923  tests/test_hr_audit_validation.py
3d42ee3bfa6a7cd906903f34289eea838c44f9f249741738f4370572b5f7c328  tests/test_hr_branch_scope.py
085a268b2c3b3e8cf94a22c5026b834452a563761de7b3e90d2810f34e0c675a  tests/test_hr_civil_time.py
bb190b1fd969f4ca55b9a8c5715d5090baa4b21e022dee5ebb33773225a5b6cc  tests/test_hr_concurrency.py
253adadb399634074462650f56149133fc21e10a34ddde91e7cbcaf017ab5972  tests/test_hr_domain_races.py
d0a5f2c2c9845374b2f7784867fbbf77d73e83c91ef362a75df18cdd770f873d  tests/test_hr_flows.py
5404679b199c5b4423893413065e9e81cb0a884fc352eaacdb44ff91dffee91d  tests/test_hr_history.py
549eb44e11074ce1661be1ee85c55e93723df2928499ae7a781f8aa32d81d6cc  tests/test_hr_http.py
b5bb1f8aed0b5a3c671e0e0e30d7bf7b19680c92145b734c0ec5b9500c7a9379  tests/test_hr_identity_races.py
5363f19619ced314e05fac666db12ea24e911eff61bdfd339dc2f140ebb23062  tests/test_hr_installation_contract.py
617e12748e931f53bd57a71c481b90b95808ee3eda2774284961bca6ec697041  tests/test_hr_models.py
672f4e4b1becad911bc21cadd905acca2f863ebd8e285d31bc1a52973d079d70  tests/test_hr_nested_services.py
f9a558608d5c16144e310319bff20ad1c67daec37949bea4dbc2b2875cabbcc9  tests/test_hr_permissions.py
f2424a9cac5ee7bd4b3c1816411df32427ef6f486a392eba7adb7d4311d5e9ed  tests/test_hr_read_authorization.py
f9dcfb349f2c14ef3debbbfa3de5d190afcfe1a2d9b1a45a3f771ea7cc6b1ad4  tests/test_hr_reference_races.py
89128d1a25eb8359399ba49e04cf9ce336a89f9d9ad72eda86d242ffa2521f25  tests/test_hr_resource_boundaries.py
1559e5afece27117c60c5b4d647f5964e15e6e4feb5bcd42f99dc163886ee71f  tests/test_hr_self_decisions.py
767bca9a6699aaff32212845d1fbf2d41bb67713b3293729449a00db52e78f3a  tests/test_hr_services.py
fb18067d41b1e1042fd9e6d39d72ea0453c5803c0fd5c2e335b15d3b0127d0d3  tests/test_hr_setup_rollback.py
```

Final evidence-only checks passed: **4 relative file links, 5 heading anchors,
32 balanced fence pairs**, final newline/no trailing whitespace and
`git diff --check`. The preceding **159,982-byte** historical document prefix
still hashes to
`8daefa42210817fcf1c14d9328e21d284732aa778af4b4ffac300c0f72bb5be0`:
it is byte-for-byte unchanged. All **59** input hashes and **27** retained
artifact hashes match their ledgers. No application test or quality suite was
rerun for this final documentation-only completion.

### Q / S: current disposition

```text
HR1-AUD-1 CORRECTIVE IMPLEMENTATION:
INCOMPLETE / NOT AUDIT-READY

NO CORRECTIVE COMMIT.
HEAD: e6b72896e10471463b8b6b280fbccfc524d7cc42
MAIN: b36cdba91654e6a583735d67f7f6cf27a835003e

FOCUSED POSTGRESQL: 649 PASSED
FOCUSED SQLITE: 567 PASSED / 82 CLASSIFIED SKIPS
FULL POSTGRESQL: INTERRUPTED, EXIT 255; NOT PASS
FULL SQLITE / FINAL QUALITY / CORRECTIVE BROWSER: NOT RUN

HISTORICAL TIMEOUT CAUSES: SEPARATELY NOT PROVEN
NEW CONTAINER-EXIT CAUSE: NOT PROVEN
FRESH INDEPENDENT CORRECTIVE RE-AUDIT: NOT YET PERFORMED
HOSTED CI / FORMAL ACCEPTANCE / CANONICAL ADOPTION: NOT AUTHORIZED
PHASE 4: ON HOLD — UNCHANGED
AUTOMATION: DELETED / NO SCHEDULED RETRY
PUSH / PR / TAG: NONE
STOP.
```

## HR1-AUD-1 interrupted full verification recovery — in progress

Date: **2026-10-20 Asia/Dhaka**. Authority: the owner's complete attachment
`f2d7e168-10f7-49b3-a80b-06a78d47221a/Pasted text.txt`, followed by explicit
authorization of a new temporary ten-minute continuation in this chat. This
supersedes the preceding evidence-only stop solely for the bounded investigation
and one fresh complete verification attempt. **No staging or commit is permitted,
even if every local gate passes.** No push, main update, PR, tag, owner-system
remediation, runtime/test change or next phase is authorized.

### A-B / N-P: preserved integrity

Read the complete evidence/handoff, accepted ADR 0018 and HR plan, architecture
baseline/boundaries/dependency map and roadmap. Recomputed both immutable ledgers:
all **59 frozen inputs** and all **27 retained artifacts** match. Their manifest
hashes remain `9415b9cf5b4e6df60b786c8e1662fcbcdd2ed17cb746ce96bd34e2517b9e1a29`
and `cb32f4ba4968e863908b0802bae98619d2b5727c6a60d7dbeb8c67d91ce287f0`.
The exact 18-path inventory above is unchanged, with zero staged paths.

Branch/HEAD remain `phase3a-hr1-implementation` /
`e6b72896e10471463b8b6b280fbccfc524d7cc42`. Parent, local main, origin/main
and HR-0 branch remain `b36cdba91654e6a583735d67f7f6cf27a835003e`.
Independent read-only `git ls-remote` returned main/HR-0 at that SHA and no
remote HR-1 or Phase 4 branch; no fetch occurred. Held local Phase 4 remains
`735e1bea13bc58fa71d430163422139d5c0f2363`, **ON HOLD**. The four P2
corrections, both test-hardening overlays and all protected files are unchanged.
This continuation appends only this evidence document inside the repository.

### C-D: bounded original-exit investigation and disposition

Complete retained raw/timestamped runner and server logs were inspected and
parsed, including all recorded result markers and all fourteen watcher JSON
records. There are **4,313 PASSED tokens**, 4,326 collected cases, no observed
FAILED/ERROR/SKIPPED test-result marker, no traceback and no terminal pytest
summary. Twenty-three PASS records lack percentage suffixes; a percentage-only
parser counts 4,290 and is not the complete result-marker count. This does not
promote the incomplete execution to PASS.

The last completed test remains
`businessos/modules/accounting/integrations/tests/test_alias_topology.py::test_installation_topology[postgresql-unsupported-1-1-0]`.
Importantly, the **final unterminated raw-log line identifies the active node**:
`businessos/modules/accounting/integrations/tests/test_alias_topology.py::test_selected_alias_complete_posting_and_proof`.
Its exact internal stage was not logged. Source inspection shows a fresh selected
alias migration/bootstrap and Accounting composition proof. The preceding
topology subprocesses have a 100-second subprocess safety timeout; that timeout
does not govern this active test. No pytest timeout plugin/global test watchdog
is configured in the inspected project configuration. A lost tool session alone
is not treated as process-termination evidence.

New retained Windows/Docker host evidence, previously not inspected:

| UTC timestamp | Actual retained record |
| --- | --- |
| 10:11:31.2219069 | Windows System event 2004, Resource-Exhaustion-Detector: low virtual memory; reported leading consumers include vmmemWSL 3,046,301,696 bytes, ChatGPT 1,292,828,672 bytes and mysqld 1,290,686,464 bytes. These are observations, not permission to terminate unrelated programs. |
| 10:11:40.5477587 | Docker backend: `monitor exited: exit status 2`. |
| 10:11:40.7742067 | Docker backend: `extracted panic from services output: monitor: fatal error: out of memory`. |
| 10:11:46.1774858 | Docker Desktop: backend process exited. |
| 10:13:24.9100524 / 10:13:41.6372371 | Backend launched again, then exited. |
| 10:13:44.2434799 / 10:13:56.4276405 | Another backend launch, followed by WSL VM-start record. |
| 10:13:58.708567333 / 10:13:58.711694055 | Previously retained server/runner finish metadata: exit 255, approximately 3.13ms apart. |
| 10:17:26.0812351 | A second Windows low-virtual-memory event, after the interruption. |

**Disposition A — PROVEN INFRASTRUCTURE INTERRUPTION.** The host component's
out-of-memory panic, backend exits and VM restart are directly recorded.
Inference, clearly bounded: these lifecycle events support infrastructure loss
as the explanation for the paired container interruption, rather than a pytest
assertion failure. The precise allocating process/call, ultimate memory-pressure
cause and complete per-container termination chain remain NOT PROVEN. In
particular, do not call this a Linux container OOM kill: both retained container
records say `OOMKilled=false`. The later low-memory event is not backdated to
prove earlier state. No test/runtime implementation defect was demonstrated.

Original containers are already removed; their runtime/cgroup/DB evidence is
unavailable. Original PostgreSQL logs finish with ordinary checkpoints, without
shutdown/PANIC/FATAL at the interruption. Their expected timeout/deadlock controls
remain classified separately. Historical per-container CPU/memory limits were
not retained in the sanitized inspect record; current limits cannot replace them.
No historical disk-full/filesystem-error evidence was found in the bounded logs;
current disk headroom is not a historical disk measurement. Both earlier HR
timeout causes remain **separately NOT PROVEN**. This new infrastructure evidence
does not explain the earlier Department 57014 or Attendance budget refusal.

### E-F: single fresh complete PostgreSQL attempt

New server `hr1-recovery-proof-pg-e6b7289`, immutable ID
`d241c45d0b8669da2fea45c9f1118657fbfb28f545586c9a4dcae2260da0e5ef`,
started **13:05:11.225449659 UTC**. Exact image digest/ID:
`sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24`.
Actual PostgreSQL **17.11**, READ COMMITTED, initial statement/lock timeout 0;
network none, tmpfs PGDATA, no ports or host database mounts. New application DB
`hr1_recovery_full` has explicit synthetic-only recovery/24-hour-teardown custody;
pytest uses fresh `test_hr1_recovery_full`. No demo/customer database is involved.

One new runner `hr1-recovery-full-pg`, immutable ID
`4ebc9fd79f0aa8cbbc4915dcec072912f18ccca3f0147ef2191c5c861e41eeb0`,
started **13:05:53.356313027 UTC**. Exact QA image remains
`sha256:a7a3476a1883cddc11d7c9bcf7d7674c5c9396211f2b654337a58a1c9936637f`;
Python 3.13.16 / Django 5.2.17 / pytest 8.4.2 / Ruff 0.16.7. Source `/app`
and external probes `/probes` are read-only; bytecode/cache writes disabled,
development PostgreSQL settings, default execution alias and all three existing
commercial-install flags enabled. Only the task server's network is shared.

```sh
bash -o pipefail -c '(python manage.py migrate --noinput && pytest -vv --maxfail=1 --tb=long -rs -p no:cacheprovider -p hr1_corrective_watch --junitxml=/tmp/hr1-recovery-full-pg.xml) 2>&1 | tee /tmp/hr1-recovery-full-pg.log'
```

Fresh migrations succeeded. Actual collection at **13:06:26 UTC: 4,326**.
Current checkpoint: **RUNNING / NO TERMINAL VERDICT**. The old partial run is not
combined with this attempt. JUnit output is additional reporting, not a changed
test input or skip policy. Existing causal watcher and accepted two-second
cumulative budget are unchanged. No competing heavy task/browser was started.

Current resource observations: Docker 12 CPUs / 3,742,158,848 bytes reported
memory; no additional per-container CPU/memory ceiling. Windows preflight:
24,324,124,672 committed bytes / 27,984,510,976 commit limit, 768MiB available
physical memory; C approximately 27.1GB and D 61.4GB free. These are limited
headroom observations, not a performance/stability guarantee. No host setting,
memory limit or unrelated process was changed. A later initial monitor sample
recorded runner 91.25MiB and server 104.7MiB; live samples retain subsequent load.

Improved passive monitoring is **outside** HR critical transactions: hidden
host PowerShell PID 6924, independent runner/server timestamped log streams,
filtered Docker lifecycle events, and approximately 30-second host commit/CPU/
disk plus container state/resource/progress samples. Bounded CLI timeout terminates
only its own observer CLI, never a container. The monitor stops on terminal state
or unavailable daemon; logs persist on the host across a Docker failure. No HR
clock, SQL, expected exception or persistence result is changed. Actual samples
and stream liveness were checked; sandbox process discovery required the
read-only escalated check to see these processes.

New immutable records, retained under the same external artifact root:

```text
52b209d97d3de77541ecda1a1349e47fe73b16bf87d445fd1816d24a92028477  hr1-recovery-historical-host-excerpt.log
450e2bb9cba5d363fdc6b9730235cfb10ec9e44230e21954cd4b063885368893  hr1-recovery-historical-memory-events.json
dbf00098544cee490e3d6a16d2cf48a74372897ad630925683f52db916631bcb  hr1-recovery-container-start.json
1d04b32af6426da7e084c58e6464898e5ef1fb6ee86d1f949323592de27084ac  hr1-recovery-host-monitor.ps1
```

Live `hr1-recovery-*-live.log`, corresponding stderr streams,
`hr1-recovery-events.jsonl` and `hr1-recovery-metrics.jsonl` are append-only
runtime outputs, not final-hashed completed artifacts yet. Full tee/JUnit/watcher
records must be retained and reconciled before verified task-only teardown.
All original 27 retained records remain untouched.

### G-M / Q-R: remaining gates and enforced checkpoint

Full SQLite, final quality/bootstrap/frontend/browser and fresh final H/T
reconciliation are **NOT STARTED / PENDING**, conditional on terminal full PG
success. No original or partially executed H/T result is promoted to fresh
complete gate evidence. Prior H/T tables retain their dated status; H16/H18 and
all external independent review/CI/acceptance/adoption obligations remain open.

The owner-authorized temporary heartbeat
`recover-hr1-aud-1-full-local-verification` checks this same attempt every ten
minutes, stays quiet while healthy/pending, and must be deleted on failure or
completion. It does not authorize another PostgreSQL attempt, code/test changes,
staging or a commit. Any unexpected resource/native timeout/deadlock, failed test,
interruption, partial effect, frozen drift or missing mandatory evidence stops
progression: retain original evidence, no automatic retry, then report the exact
blocker. Only a complete successful PG process permits one full supported SQLite
run; both must pass before quality/browser/H01-H18/T01-T26 completion.

**RECOVERY IN PROGRESS — no full-suite PASS yet. NO STAGING / NO COMMIT.**
**Phase 4 ON HOLD. Push / PR / tag / main update: NONE.**

### Recovery gate completion — PostgreSQL PASS, SQLite running

Checkpoint: **2026-10-20 20:22 Asia/Dhaka**. The one fresh PostgreSQL runner
`4ebc9fd79f0aa8cbbc4915dcec072912f18ccca3f0147ef2191c5c861e41eeb0`
exited **0** at **2026-10-20T14:12:47.757010165Z**. Actual pytest terminal result:
**4,326 passed in 3,993.41s (1:06:33), zero skips/failures/errors**.
Copied JUnit independently accounts for exactly 4,326 testcase elements,
errors=0/failures=0/skipped=0; its suite duration is 3,993.452s. The previously
unfinished selected-alias/topology cases have actual fresh results. The old
partial attempt remains INTERRUPTED; its markers contribute none of this count.

Seven complete causal watcher records correspond only to the three predeclared
deliberate controls. Two server statement-timeout messages timestamp-match the
constraint-check and selected-Department controls; two deadlocks timestamp-match
the two rejected-old-protocol negative controls. All four control tests PASS;
no unexpected watcher event occurred. All four P2 regression families and the
hardened pending-Attendance rollback case are included in this complete run.
Final H/T reconciliation and independent finding closure are not yet claimed.

The host monitor intentionally finished after terminal PG, closing only its own
observer CLI children. A later Get-Process error for absent PID 6924 is expected
monitor completion, not a test failure. Its 121 retained samples show physical
memory availability 13–993MiB, committed memory 23,526,539,264–27,167,789,056 bytes,
against the recorded 27,984,510,976-byte commit limit. Tight headroom remains a
limitation, not production capacity certification. No system tuning occurred.

Complete copied artifacts under the same external root:

```text
311bad8003292b60ca05f7707a9b9e7ab16011ad2d71efb8d3d6d5a252ab9f6b  hr1-recovery-full-pg.log
e4cc81c6f5805334ae791a89dd96c0a0e71081bd2dc12bf74d3a2a0ba6623117  hr1-recovery-full-pg.xml
55bfed18b91163dcc0459ddf1edf093d740519482f191e413ccc0cf39202cad4  hr1-recovery-server-after-pg.log
98bf5b480b90d8b1398c2a40ec812f2f019b0445504fc13c0b8a4630d41bf0cf  hr1-recovery-pg-terminal-inspect.json
d0c75e3d9fa80ad91dc077e519b76a7b105490e53dd736715b6bc548e6064ffb  hr1-recovery-metrics.jsonl
189a201137b8291aa39215b48b5fd3d157df2d3926dbf56f770832ef3e596a6b  hr1-recovery-events.jsonl
```

All seven causal JSON records are copied in `hr1-recovery-full-pg-watch/`.
Original 27 artifacts remain untouched. Task PostgreSQL remains isolated/running
for later authorized gates; no teardown/unrelated-resource change occurred.

After terminal success/log/JUnit/control and frozen-state checks, launched the
one full SQLite runner `hr1-recovery-full-sqlite`, immutable ID
`17224555143c4e642ac266ef56c16c3ab6db345c678c0cf78defabe981dfba8c`.
Actual start **2026-10-20T14:19:25.818835068Z**. Exact QA image unchanged,
source `/app` read-only, network none, `config.settings.test`, all three existing
commercial-install flags enabled, bytecode/cache writes disabled. Actual command:

```sh
bash -o pipefail -c 'pytest -vv --maxfail=1 --tb=long -rs -p no:cacheprovider --junitxml=/tmp/hr1-recovery-full-sqlite.xml 2>&1 | tee /tmp/hr1-recovery-full-sqlite.log'
```

SQLite is RUNNING / NO TERMINAL RESULT; no final count/skip total is assumed.
No competing heavy checks/browser were started. Quality/bootstrap/frontend/
browser and H01-H18/T01-T26 reconciliation remain conditional on SQLite success.
The same temporary heartbeat was updated, not duplicated, with the completed PG
and pending SQLite identities. OpenAI Docs influenced scheduling management only.
An initial Windows batch-wrapper patch invocation rejected its argument before
editing; the evidence hash remained unchanged. It was a documentation-command
transport issue, not a test failure or an implementation change.

**Fresh full PostgreSQL PASS. Full SQLite PENDING. Overall local gates INCOMPLETE.**
**NO STAGING / NO COMMIT. Phase 4 ON HOLD. Push / PR / tag / main update NONE.**

## HR1-AUD-1 recovery stop — complete suites PASS, minimal-fixture failure

Date: **2026-10-20 Asia/Dhaka**. Same recovery authorization; no permission to
stage or commit. Preserve the preceding original failures and interrupted run.
The new stop is a **disposable verification-fixture configuration error**, not a
demonstrated defect in the frozen implementation. No automatic correction or
rerun was attempted. Overall mandatory local verification remains incomplete.

### A-R final recovery report

| Item | Exact result at this stop |
| --- | --- |
| A — Starting integrity | Required branch/HEAD/parent/main/origin-main/HR-0/held Phase 4 verified; exact 18 dirty paths, zero staged. |
| B — Frozen hashes | All 59 inputs and original 27 artifacts match their immutable manifests. Completed PG's 24-record ledger also matches. No frozen source/test/template/build input changed. |
| C — Exit-255 diagnosis | Retained host monitor out-of-memory panic, backend exits and WSL restart are recorded above. Old 4,313 markers are not a completed suite. |
| D — Classification | A: infrastructure interruption established at host-component/lifecycle level; exact allocation and per-container termination chain NOT PROVEN. Not a pytest assertion failure or established container OOM kill. |
| E — Fresh environment | Exact pinned QA/PostgreSQL images, new custody-commented tmpfs databases, read-only source, selected default alias, READ COMMITTED, all three commercial flags. Full details/IDs above and in retained inspect records. |
| F — Full PostgreSQL | 4,326 passed / 0 failed / 0 skipped, 3,993.41s, exit 0. Complete raw log and JUnit agree. |
| G — Full SQLite | 2,763 passed / 1,563 explicitly classified skips / 0 failed, 939.25s, exit 0; all 4,326 cases accounted for. |
| H — H01-H18 | Fresh executed test evidence below; H16 NOT RUN, H17 minimal-topology proof blocked by invalid fixture, H18 incomplete. No collective acceptance. |
| I — T01-T26 | Fresh PostgreSQL executed oracle matches below, all PASS. Exact node IDs/counts retained in the matrix JSON; overlapping IDs are not extra unique tests. Independent review remains pending. |
| J — Migration/quality | Fresh full PG migrations PASS; canonical Ruff PASS; explicit 48-Python-path format PASS; Django zero issues; no drift; 248 architecture/registry/database guards PASS. Full-topology standalone bootstrap PASS; minimal fixture fails as below. |
| K — Frontend/browser | Fresh node syntax/21 JS tests/npm/Tailwind and 390/768/1280 browser gates NOT RUN after the stop. Browser skill/controller initialized only; no fresh page interaction, responsive, CSRF, stale-scope, keyboard or non-JS PASS. |
| L — Historical limits | Original Department native 57014 and Attendance cumulative-budget consumption causes remain separately NOT PROVEN. Fresh successes do not retroactively explain them; two-second budget unchanged. |
| M — Evidence | This append only; previous history/fingerprints retained; complete new logs/JUnit/trace/inspect/matrix/fixture and cleanup records retained externally. |
| N — File inventory | Same exact 18 dirty paths reproduced below; in-repository changes in this recovery are evidence-only. No frozen code/test edit. External disposable fixture/helper files are not candidate implementation files. |
| O — Git/worktree | HEAD e6b72896e10471463b8b6b280fbccfc524d7cc42, main/origin-main/HR-0 b36cdba91654e6a583735d67f7f6cf27a835003e; no staging/commit/push/main update. Final checks below. |
| P — Phase 4 | Local phase4-domain-foundations-architecture remains 735e1bea13bc58fa71d430163422139d5c0f2363, ON HOLD. |
| Q — Blocker | Required minimal-topology rendering proof failed in a misconfigured external fixture; minimal SQLite, frontend/browser and final H16/H17/H18 closure not completed. |
| R — Recommendation | Separate bounded authorization to correct only the disposable fixture configuration and resume the remaining gates. Retain completed full-suite evidence while all 59 inputs/profile match. No default full-suite rerun or production correction. |

### SQLite and quality execution evidence

SQLite runner `17224555143c4e642ac266ef56c16c3ab6db345c678c0cf78defabe981dfba8c`
finished **2026-10-20T14:35:09.870878805Z**, exit **0**. Its actual terminal result
is **2,763 passed, 1,563 skipped in 939.25s (0:15:39)**. JUnit: tests=4326,
failures=0/errors=0/skipped=1563; reported suite time 939.148s. Reporting precision
differences are not test-count differences. Every skip has one of 36 explicit
backend reasons, grouped with exact counts in `hr1-recovery-executed-matrix.json`.
The groups sum to 1,563: PostgreSQL catalog/DDL/RLS/schema/role/FK proofs, real
independent locks/concurrency/revocation, PostgreSQL bootstrap/alias proofs and
exact numeric storage/arithmetic that SQLite cannot certify. No unexplained skip
was accepted and no SQLite lock/concurrency certification is claimed.

Quality runner `hr1-recovery-quality`, immutable ID
`243715f7515132a4ec630bb2d66c29cb81ba889acd2434cc9769b29252a7bab9`,
started 14:40:37.743302141Z, finished 14:41:14.225396240Z, exit 0. It used the
same pinned QA image, network none, source read-only, test settings and all three
commercial-install flags. Actual serial command chain:

```text
ruff check . --no-cache
ruff format --check --no-cache [all 48 explicit paths in hr1-recovery-quality-python-paths.txt]
python manage.py check
python manage.py makemigrations --check --dry-run
pytest tests/test_database_architecture.py tests/test_modules.py tests/test_database_foundation.py -q --maxfail=1 --tb=long -p no:cacheprovider
```

Actual output: All checks passed; 48 files already formatted; system check zero
issues; no changes detected; **248 passed in 21.47s**. The Python path set was
derived from baseline b36cdba-to-working-tree plus untracked Python paths and
compared to all 48 frozen Python inputs, including both HR migrations and four
audit regression files. No formatter write mode ran. Known historical eight npm
alerts (two moderate/six high) remain unmodified, not newly rechecked here.

### Exact new failure and causal boundary

The new external `hr1-recovery-fixture.py` runs three serial probe modes: fresh
full-topology PostgreSQL, minimal Core/Party/HR PostgreSQL, then minimal SQLite.
New app databases `hr1_recovery_bootstrap` and `hr1_recovery_minimal` were absent
before creation and explicitly custody-commented synthetic-only/task tmpfs.
No demo/customer database was used. Its read-only source/probe runner was
`hr1-recovery-bootstrap`, immutable ID
`d08921fc349a5d422f60bbedaf80224ea560700603d525b5e1be9190035ab2ce`,
started 14:44:06.749837770Z, finished 14:44:28.792254344Z, exit **1**.

The full-topology mode printed `HR1_RECOVERY_BOOTSTRAP_PASS` at
**14:44:21.501716678Z**: six native HR model counts exactly one each,
12 active HR permissions, five actual success Audits, disabled HR HTTP 404 and
enabled HTTP 200. Existing migrations were applied on the fresh schema.

The second mode filtered `settings.INSTALLED_APPS` to Core/Party/HR **after**
settings had been loaded with all three commercial integration flags set to 1.
It did not correspondingly remove the optional financial template context
processors or configure the minimal installation before loading settings.
On `/probes/hr1-recovery-fixture.py:99`, `client.get('/hr/')` reached enabled-page
rendering. Django imported the retained
`businessos.modules.payments.integrations.billing.presentation.parent_evidence`,
which imports its selectors and then `businessos.modules.billing.models.Invoice`.
Billing had been removed from INSTALLED_APPS, producing this actual exception:

```text
RuntimeError: Model class businessos.modules.billing.models.Invoice doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS.
```

The complete traceback and frozen settings source establish the fixture's
inconsistent app/context-processor configuration. This is not a new unexpected
HR deadline/deadlock and not evidence that a supported coherently configured
minimal deployment fails. Nor is it a minimal-topology PASS: its required HTTP
proof did not complete. The script's earlier native/permission/disabled-HTTP
assertions ran, but complete minimal PostgreSQL verification is **NOT PROVEN**.
The `&&` chain did not start minimal SQLite. No fixture correction or retry,
production/settings modification, frontend execution or browser startup followed.
There was no failed HR mutation to which a new rollback claim is attributed;
the synthetic setup operations intentionally committed within the disposable DB.

Smallest proposed next correction, **not applied**: configure the external
minimal fixture coherently before Django setup, including optional install flags
and template context processors for absent owners. Preserve this failed helper
and log; version any replacement externally. Do not change repository settings,
frozen implementation/tests, accepted contracts, permissions or resource budget.
Owner authorization is required to resume that probe and the remaining frontend/
browser gates. The passed full suites do not need automatic repetition if their
59 inputs, image/profile and relevant evidence remain unchanged.

### H01-H18: fresh executed tests versus incomplete local gates

Paths in this table are under `tests/`. Counts are fresh PostgreSQL JUnit cases,
not inherited results or a sum of independent requirements. All 1,311 HR cases
across 24 files passed. Every row still requires fresh independent corrective
re-audit; no original finding is self-closed.

| ID | Fresh actual evidence / status |
| --- | --- |
| H01 | PASS executed oracles: test_hr_permissions.py 377, test_hr_http.py 126, scoped foreign-ID/mutation tests. |
| H02 | PASS executed oracles: test_hr_branch_scope.py 8, test_hr_concurrency.py 16, test_hr_domain_races.py 24. |
| H03 | PASS executed oracles: test_hr_models.py 284, test_hr_identity_races.py 12, test_hr_adversarial.py 24. |
| H04 | PASS executed oracles: test_hr_services.py 20, identity races 12, reference races 20; keys/lifecycle/retirement. |
| H05 | PASS executed compound/SU/negative-self-decision oracles: permissions 377, test_hr_self_decisions.py 16. |
| H06 | PASS executed registry/HTTP/install oracles: test_hr_installation_contract.py 19, HTTP 126, models 284. |
| H07 | PASS executed alias/default-trap/nesting oracles: admission 97, acquired 14, validation 45, nested services 5. |
| H08 | PASS executed interval/conflict/resource oracles: flows 13, history 36, domain races 24, resource boundaries 2. |
| H09 | PASS executed civil/fold/historical-boundary oracles: civil time 81, corrective history 38, history 36, HTTP 126. |
| H10 | PASS executed complete-chain/immutability oracles: history 36, corrective history 38, persistence 16, models 284. |
| H11 | PASS executed Leave lifecycle/receipt/date/self-decision oracles: flows, services, civil time, self decisions, adversarial. |
| H12 | PASS executed PostgreSQL T matrix below, domain/reference/identity races and read authorization 12. |
| H13 | PASS executed authority/admission/budget/lock coverage oracles: admission 97 and acquired 14. |
| H14 | PASS executed native/Audit/whole-outer rollback: validation 45, acquired 14, nested services 5, setup rollback 6, adversarial 24. |
| H15 | PASS executed HTTP/form/CSRF/stale-scope/pagination oracles in HTTP 126 and permissions 377; fresh interactive browser still pending under H16. |
| H16 | NOT PROVEN / NOT RUN: no fresh 390/768/1280 screenshots or interaction/fallback proof. Prior original browser record remains historical. |
| H17 | NOT PROVEN complete: full-suite installation cases and fresh full-topology bootstrap PASS; required minimal standalone probe failed from invalid fixture configuration. |
| H18 | NOT PROVEN complete: full suites/lint/48-file format/Django/drift/248 guards PASS; frontend/browser/minimal gates outstanding. Independent re-audit/hosted CI/acceptance/adoption remain separate pending gates. |

### T01-T26: actual full PostgreSQL oracle reconciliation

`A` = `tests/test_hr_admission.py`; `C` = `tests/test_hr_concurrency.py`.
Exact full node IDs, parameter variants and counts are in the retained matrix
JSON, matched directly to fresh JUnit. Counts intentionally overlap IDs; they
must not be added as new unique tests. Local executed oracles PASS, not universal
deadlock/fairness/production proof or independent acceptance.

| ID | Fresh executed oracle / PASS matches |
| --- | --- |
| T01 | A original_blocking_user_order_deadlock isolated negative control — 1. |
| T02 | A public_employee_hr_first_writer_wait_is_row_not_global_gate — 2. |
| T03 | A public_employee_writer_first_unordered_user_batches_fail_closed — 2. |
| T04 | Actor/link variants of the T02 test — 2; exact variants retained. |
| T05 | Actor/link variants in T02/T03 — 4. |
| T06 | C inactive_removed_user_lock and public_relink writer/HR-first tests — 4. |
| T07 | A original_user_only_reader mixed-writer negative control plus actual_mixed_authority_then_user_batch — 11. |
| T08 | A actual_mixed_authority_then_user_batch and unrelated_permission_update_or_create — 12. |
| T09 | A Company-wait revocation matrix and C HR-first company-access revoker — 4. |
| T10 | A rechecks_actor_and_authority_after_domain_wait matrix — 3. |
| T11 | Actor variant of that domain-wait matrix — retained within the same 3. |
| T12 | A independent_companies_share_read_only_authority_without_global_gate — 2. |
| T13 | Shared-actor variant within the same 2. |
| T14 | Disjoint-actor variant within the same 2. |
| T15 | A superuser inactive namespace, existing namespace/DML and complete final SQL tests — 5 matched cases. |
| T16 | A admitted_nested_subset, nested_expansion and unknown outer/manual transaction tests — 8; acquired/nested/validation families additionally PASS. |
| T17 | A actual nondefault PG alias/default trap, alias bootstrap and nested alias switch — 3. |
| T18 | A nowait_conflict_rolls_back_before_authority_busy User/Role/Permission — 3. |
| T19 | A caught nested outer-Audit rollback and genuine constraint-check timeout — 2; full corrective native rollback files additionally PASS. |
| T20 | C historical_correction_retry_ignores_inactive_provenance_but_rechecks_current_revocation — 2. |
| T21 | A repeated_hot_role_refusals_are_bounded_then_fresh_request_succeeds — 1. |
| T22 | A role_share_readers and independent-Company reader tests — 3. |
| T23 | A supported_identity_writer_forms and both unordered User batch orders — 14. |
| T24 | A reversed_active_inactive_authority_multirow_writers — 8. |
| T25 | A native Sales public service/HR compatibility, both orders — 2. |
| T26 | A implicit raw/ORM relation negative controls and explicit relation admission — 3. |

### Custody, exact scope and safe continuation

The exact 18 preserved dirty paths remain:

```text
businessos/modules/hr/admission.py
businessos/modules/hr/civil_time.py
businessos/modules/hr/conflicts.py
businessos/modules/hr/history.py
businessos/modules/hr/persistence.py
businessos/modules/hr/selectors.py
businessos/modules/hr/services/__init__.py
businessos/modules/hr/services/attendance.py
businessos/modules/hr/support.py
docs/exec-plans/active/HR_1_IMPLEMENTATION_EVIDENCE.md
tests/test_hr_admission.py
tests/test_hr_history.py
tests/test_hr_models.py
tests/test_hr_nested_services.py
tests/test_hr_audit_acquired.py
tests/test_hr_audit_history.py
tests/test_hr_audit_persistence.py
tests/test_hr_audit_validation.py
```

New immutable retained records include:

```text
f297b3d6e5565d845863896e98a6335346b3d73e0ab8f11338a580c45245aa17  hr1-recovery-full-sqlite.log
d8a8c5b13190bcc19a7dc7e639abb01e2dd2cfdc88cc89c719f14bea1e82c384  hr1-recovery-full-sqlite.xml
c8ee8306873bd0d60658a66da1a2a6a274d9c65e85597c364ea4747a49fc9191  hr1-recovery-sqlite-terminal-inspect.json
56158a65c1dfe8a147a3f067325f1c4209d81a401f47a8313a3e3282da1dcf03  hr1-recovery-quality.log
1bc7948d1fe26a1365e0e733068eede649335bccf19fbc78cf12ba7031066469  hr1-recovery-quality-python-paths.txt
cfb0316a34424bc6eb3acdf27d4cfa0266433ba8e106d60205dce54ed2c14836  hr1-recovery-fixture.py
6e56f28a216ba0df52585f04ba06407b59fd533476811accea9ef1f47924dfb8  hr1-recovery-bootstrap.log
767a42f243a6b374e85553778fcc2f745d867b48d017d767aa0cad682087ac99  hr1-recovery-bootstrap-terminal-inspect.json
d59ff01c819c4e1b751ecf671f0c004013f2f0f4b7cb9535fcc5505a9cbfe798  hr1-recovery-executed-matrix.json
```

The complete **38-record** new stop manifest is
`hr1-recovery-stop-artifacts.sha256`, SHA-256
`f57ec2902cc92c82268ee85cc8462acf95d969feb831182cbd0999e0e2bcff46`.
It includes complete PG/SQLite outputs, all seven causal JSON records, lifecycle/
resource/host evidence, helper, quality/bootstrap traces, pre-cleanup inspect,
server final/shutdown logs and shutdown state. Earlier 27-record and completed
24-record PG manifests are preserved, not overwritten.

Before cleanup, verified all five exact IDs/images/mounts and only the three
custody-commented task application databases plus PostgreSQL technical databases,
with zero other client sessions. Stopped the exact task PostgreSQL server,
retained clean shutdown evidence, then normally removed that server and the four
exited runners. No force/prune/image removal/unrelated container mutation.
These disposable synthetic databases are no longer recoverable; full logs,
matrix and pinned images remain. No browser fixture was started or removed.

The temporary `recover-hr1-aud-1-full-local-verification` heartbeat was **deleted**
under the stop rule; its configuration is absent. OpenAI Docs was used only for
scheduling management. Computer-use guidance was read and the browser inventory
initialized, but no fresh app-page/browser PASS is claimed after the failed gate.

Safe continuation requires new owner direction: retain both completed suites
and this exact freeze; correct only the disposable minimal-fixture configuration,
rerun that bounded PostgreSQL/SQLite topology proof, then complete the unrun
frontend/browser and documentation/final-integrity gates. Do not rerun complete
suites merely because this external helper failed. No staging or commit is
permitted under the present authorization, even after those remaining gates pass.

```text
HR1-AUD-1 CORRECTIVE VERIFICATION:
INCOMPLETE / NOT AUDIT-READY

NO COMMIT.

FULL POSTGRESQL: 4326 PASSED, EXIT 0
FULL SQLITE: 2763 PASSED / 1563 CLASSIFIED SKIPS, EXIT 0
QUALITY: PASS; 48 PYTHON FILES / 248 GUARD TESTS
MINIMAL TOPOLOGY: BLOCKED BY EXTERNAL FIXTURE CONFIGURATION ERROR
FRONTEND / FRESH BROWSER: NOT RUN
INDEPENDENT CORRECTIVE RE-AUDIT: NOT YET PERFORMED
CANONICAL ADOPTION: NOT AUTHORIZED
PHASE 4: ON HOLD — UNCHANGED
AUTOMATION: DELETED
PUSH / PR / TAG / MAIN UPDATE: NONE
STOP.
```

## HR1-AUD-1 final-local authorization — minimal PASS, environment-blocked remainder

Date: **2026-10-20 Asia/Dhaka**. Governing owner attachment:
`62436d1b-d5c3-4d9a-b577-4c4075cce8b9/Pasted text.txt`, read completely.
This authorization permits external-probe correction, bounded topology/frontend/
real-browser verification and factual evidence append only. **No staging or commit**,
including on success. No production/test/settings/schema/UI correction was made.
All preceding history is retained verbatim; this section supersedes only the
then-unrun minimal/JavaScript gates, not previous failure attribution or acceptance.

### Integrity and reusable regression evidence

At start and before this append, all **59** frozen inputs matched
`hr1-hardening-frozen-inputs.sha256`, manifest SHA-256
`9415b9cf5b4e6df60b786c8e1662fcbcdd2ed17cb746ce96bd34e2517b9e1a29`.
The original 27 artifacts, completed-PG 24-record manifest and recovery-stop
38-record manifest also matched every recorded artifact hash. No later frozen
implementation/test correction occurred. The previous whole evidence file is
retained externally as `hr1-final-evidence-before.md`, SHA-256
`8bb5ec4834e6cff7561dbf37fe02f8a853f15618b761b53ebd84a9dd0b29eea5`.
The append must preserve that entire byte prefix, not merely its earlier 192,788
bytes. The candidate remains the same nine changed production paths/four P2
families; their independent resolution is NOT claimed.

Re-read terminal raw logs and parsed both retained JUnit files: PostgreSQL
**4326 cases / 4326 passed / 0 skipped / 0 errors / 0 failures**, exit 0,
3993.41s; SQLite **4326 cases / 2763 passed / 1563 classified skips / 0 errors /
0 failures**, exit 0, 939.25s. The same pinned QA image/profile/command records
and all 36 SQLite backend-specific skip groups remain valid. These full suites
were **not rerun**. Prior Ruff/48-file formatting/Django/drift/248 guard tests
and full-topology bootstrap evidence remains applicable to unchanged inputs.
The earlier exit-255 run remains INTERRUPTED, not a substituted PASS. Historical
Department native 57014 and Attendance cumulative-budget causes remain separately
**NOT PROVEN**; the accepted two-second budget is unchanged.

### Corrected external topology and actual minimal proofs

The malformed original `hr1-recovery-fixture.py` and its failed log/hash were
preserved unchanged. Its actual traceback imported Payments/Billing's retained
template context processor, then Billing.Invoice after Billing was removed from
INSTALLED_APPS. This was investigated as an incoherent external configuration,
not a blanket exemption for missing imports.

New external `hr1-final-settings.py` configures a **fresh process before
django.setup()** using the existing Django settings-module seam. All three
commercial integration environment flags are absent/default 0 (asserted not 1
before loading base settings). It retains required Django infrastructure,
config/Core Identity/Reference/Organization/Audit/Access/Modules, Party and HR;
no populated app registry is mutated. It filters context processors whose owner
module is absent, including base Accounting navigation. Actual effective processors:

```text
django.template.context_processors.request
django.contrib.auth.context_processors.auth
django.contrib.messages.context_processors.messages
businessos.core.modules.context_processors.module_navigation
```

Normal security/session/common/CSRF/auth/messages/clickjacking middleware and
the BusinessDatabaseRouter remain. HR manifest hard dependencies are exactly
Party/Organization/Reference/Access. The external URL configuration uses native
Core/auth/Party/HR routes. No production setting, hook, manifest or URL was edited.
Effective full apps/processors/middleware/router/dependencies are printed in each
complete minimal log, followed by assertions on actual installed apps, imported
module namespaces and actual schema tables.

Pinned QA image: `sha256:a7a3476a1883cddc11d7c9bcf7d7674c5c9396211f2b654337a58a1c9936637f`
(`hr1-local-qa:b36cdba`, Python 3.13.16 / Django 5.2.17 / pytest 8.4.2 /
Ruff 0.16.7). Source `/app` and probes `/probes` were read-only bind mounts;
PYTHONDONTWRITEBYTECODE=1, PYTHONUNBUFFERED=1, PYTHONPATH=/probes:/app.

| Proof | Actual runner / execution / result |
| --- | --- |
| Minimal PostgreSQL | `hr1-final-minimal-pg`, ID `3e10918c57d91a63114ce6eb51699f45d58d08bfadb28a39ba4bf03251e43cd3`; 15:23:44.102808462Z–15:23:59.454993391Z, approximately 15.35s, **exit 0 / HR1_FINAL_MINIMAL_PASS**. |
| Minimal SQLite | `hr1-final-minimal-sqlite`, ID `5d0df601a1adcbc18e8e260023c691581d992dc87c9e2a9574e9793a1c440005`; 15:24:11.770848263Z–15:24:20.449039880Z, approximately 8.68s, **exit 0 / HR1_FINAL_MINIMAL_PASS**. |

Both run exactly `python /probes/hr1-final-minimal.py` under bash pipefail and
tee their respective `/tmp/hr1-final-minimal-{pg,sqlite}.log`. PostgreSQL settings:
DJANGO_SETTINGS_MODULE=hr1-final-settings; POSTGRES_HOST=127.0.0.1,
POSTGRES_DB=hr1_final_minimal, POSTGRES_USER=hr1_final,
POSTGRES_PASSWORD=synthetic-final-only. The sole new PostgreSQL server
`hr1-final-proof-pg-e6b7289`, ID
`a47c4002abbc055d022f43fbcf67f02c70c9990525ac282496e4e5b9b15659e2`,
uses pinned Postgres image
`sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24`,
network none, tmpfs PGDATA, no ports or host DB mounts. The application DB was
newly created and explicitly custody-commented synthetic-only/task teardown;
the PG runner shares only this server's network. SQLite uses HR1_BACKEND=sqlite,
its independent fresh process/in-memory schema, network none. No optional flags
were enabled, no competing heavy regression ran, no production DB was used.

Both actually verified:

- Django system check/setup and all fresh installed migrations succeed.
- Exact twelve active HR permission identities equal the native manifest codes;
  fresh HR defaults disabled. Re-registration preserves explicit HR enablement
  and existing Party enablement, using native register_manifest.
- Disabled `/hr/` returns 404. Ten enabled/authorized native screens return 200:
  Employee list/create/detail, Departments, Attendance list/detail/revisions,
  Leave list/detail and LeaveTypes. `/hr/` no longer imports Billing.
- Native Department/Employee/Attendance/initial revision/LeaveType/Leave creation
  succeeds with six counts one each and exactly five success Audit rows.
- Authorized Attendance retry returns historical_retry with full seven-model
  field equality (all six HR models plus Audit), no duplicate effect.
- RBAC-denied Department raises PermissionDenied; missing context raises
  AttributeError before any effect (not claimed as a new typed API error
  contract); foreign-Company Party raises ValidationError. Every refusal compares
  complete seven-model snapshots and verifies autocommit/no remaining atomic
  block. No committed Department/revision/receipt/Audit effect leaks.
- Foreign Party's secret marker is absent from all ten rendered screens.
- No Catalog/Sales/Procurement/Inventory/Billing/Payments/Accounting/Ecommerce
  namespace is imported and no corresponding financial/business table exists.
  No accidental financial effect or hidden optional startup dependency is found.

These are bounded functional/transaction/isolation proofs, not new concurrency
tests. There are no skipped assertions in either script. SQLite does **not**
certify PostgreSQL NOWAIT, lock ordering, race outcomes or production concurrency.

### Frontend command outcome and exact environment blockers

At **21:24:34 +06:00** a serial PowerShell command used existing Node
**v24.20.0**, npm **11.19.0**, explicit `C:\Program Files\nodejs` PATH:

```text
node --check static/js/app-navigation.js
node --test tests/js/test_app_navigation.cjs
npm ci
npm ls --depth=0                         # NOT REACHED
npm run build:css                       # NOT REACHED, first build
SHA256 generated CSS equals frozen hash # NOT REACHED
npm run build:css                       # NOT REACHED, second build
SHA256 generated CSS equals frozen hash # NOT REACHED
git diff --exit-code HEAD -- package.json package-lock.json # checked separately later
```

Syntax returned exit 0. All **21 JavaScript tests passed**, 0 failed/skipped,
actual TAP duration **156.1825ms**. `npm ci` then failed; the serial shell returned
**exit 1** after this actual native result:

```text
npm error code ENOTFOUND
npm error syscall getaddrinfo
npm error network request to https://registry.npmjs.org/yaml/-/yaml-2.9.1.tgz failed,
reason: getaddrinfo ENOTFOUND registry.npmjs.org
```

This establishes sandbox registry/DNS unavailability, not a frozen application
test assertion or a demonstrated dependency vulnerability. npm's exact elapsed
duration was not separately measured; no fabricated duration is supplied. No
automatic npm retry, dependency upgrade/fix, alternate registry, clock/budget
change or lockfile edit followed. npm ci may have cleared/partially repopulated
the ignored node_modules directory: dependency installation is **incomplete**.
No CSS build ran, and frozen generated CSS remains exactly
`a7c650044ad3e2b11df25f8c84e749a2c3f0fd3d1a55edff6f974f7061219cae`.
Prior eight npm advisories (two moderate/six high) remain historical, not newly
audited. Node 24 was actually used, not falsely represented as CI's Node 22.

A separate coherent minimal browser fixture reached READY with 51 Employees,
long-field synthetic data, Department, two Attendance revisions, draft/submitted/
approved Leave, two Companies and Branch state. It reused the preserved helper
through the new external fresh-process `hr1-final-browser.py` wrapper and coherent
settings. Browser runner ID:
`6e27b7c9d6d932eeebd19fc9a7f4735c029a621aa0393005f20120343153c7db`.
It used an exclusive **internal** Docker bridge `hr1-final-browser-net`, network ID
`f369bfc793e05fba52f48ddab2204e800c28a7813e01f6eee290a0f47d73e561`,
and requested 127.0.0.1-only ephemeral ports for 8000/8001. Actual NetworkSettings
Ports contained empty arrays; `docker port` returned no published host port.
No localhost URL was available for the browser under this network configuration.

The proposed `docker network connect bridge <exact browser ID>` was **rejected
before execution by auto-review**, because it would broaden isolation to outbound
and other-container traffic. It was not bypassed. Read-only inspection proved
the container stayed attached only to the internal network; no default bridge
connection or security/network change was applied. This is a tooling/environment
blocker, not a browser/application PASS or a new HR production defect.

Computer-use skill and its safety guidance were used to initialize browser
inventory/control and read responsive viewport/local-development documentation.
**No app page, login, form, screenshot, viewport override or live DOM QA was
performed**. Thus 390/768/1280, Employee/Department/Attendance/Leave workflows,
validation/stale Company/Branch, real CSRF, search/pagination/history, keyboard,
HTMX/non-JavaScript, responsive overflow and console/runtime gates remain **NOT
PROVEN**. Fixture readiness and server-side Client checks do not substitute for
them. Browser tabs belonging to the user were not changed.

The owner stop rule was observed: no retries until green, no new regression,
no production repair or broader network change. No new unexpected HR resource
expiry/57014/deadlock/data-integrity failure was observed in these bounded runs.

### H01-H18 current local matrix

Full-regression oracle paths/counts and exact JUnit cases in the preceding
recovery H/T tables and `hr1-recovery-executed-matrix.json` remain the unchanged
executed basis. PASS here means bounded local evidence, never independent closure.

| ID | Requirement / evidence | Actual result |
| --- | --- | --- |
| H01 | Two-Company isolation, foreign IDs/choice/history/services; test_hr_permissions/http plus new foreign-Party and ten-screen secret-marker probes | PASS local executed oracles. |
| H02 | Current/frozen Branch and stale scope; branch_scope/concurrency/domain_races | PASS executed tests; fresh interactive stale-Branch QA NOT PROVEN under H16. |
| H03 | Employee/Party/number/User identity and minimal projection; models/identity_races/adversarial | PASS local executed oracles. |
| H04 | Normalization, keys, races and retirement; services/reference_races/identity_races | PASS local executed oracles. |
| H05 | Exact twelve/compound RBAC/self-decisions; permissions/self_decisions plus new exact-identity/RBAC refusal probes | PASS local executed oracles. |
| H06 | Registration/enablement/missing/disabled HTTP; installation_contract/http/models plus new default404/enabled200/re-registration | PASS local executed oracles. |
| H07 | Selected alias, default traps, nesting; admission/acquired/validation/nested_services | PASS retained full PostgreSQL cases; no new alias/concurrency claim from minimal SQLite. |
| H08 | Intervals/conflicts/resources/retries; flows/history/domain_races/resource_boundaries | PASS local executed oracles, plus minimal native Attendance/retry. |
| H09 | Civil/fold/gap/historical/extreme arithmetic; civil_time/audit_history/history/http | PASS local executed oracles. |
| H10 | Complete immutable revision chain/history/receipts; history/audit_history/audit_persistence/models | PASS local executed oracles, plus minimal initial revision/no-duplicate retry. |
| H11 | Leave lifecycle/date/self-decision/receipts; flows/services/civil_time/self_decisions/adversarial | PASS local executed oracles, plus minimal native draft. |
| H12 | T matrix/native races and current read authorization | PASS retained executed PostgreSQL oracles; see all26 rows below. |
| H13 | Admission/authority/budget/work caps; admission/acquired | PASS retained executed PostgreSQL cases; no budget change. |
| H14 | Atomic native/revision/receipt/Audit failure rollback; validation/acquired/nested/setup_rollback/adversarial plus new seven-model refusal/retry comparisons | PASS local executed oracles. |
| H15 | HTTP/forms/CSRF/stale scope/pagination; http/permissions | PASS executed tests; real interactive counterparts still NOT PROVEN under H16. |
| H16 | Fresh responsive/keyboard/history/HTMX/non-JS browser matrix | NOT PROVEN: no host-published fixture port; isolation expansion rejected. |
| H17 | Fresh full/minimal supported installation and dependency independence | PASS local bounded proofs: full bootstrap retained; new minimal PostgreSQL and SQLite exit0 with explicit apps/processors/schema/import/permission/service/HTTP assertions. |
| H18 | All local quality, frontend, browser and external acceptance stages | INCOMPLETE / NOT PROVEN: JS21/syntax pass; npm installation blocked, builds/static/template final gates and browser incomplete. Independent re-audit/hosted exact-head CI/formal acceptance/adoption remain pending. |

### T01-T26 retained actual PostgreSQL matrix

Every row below is supported by actual completed full-PG JUnit, not a new run,
old partial markers or SQLite. A = tests/test_hr_admission.py;
C = tests/test_hr_concurrency.py. Exact IDs/parameter variants/counts are retained
in `hr1-recovery-executed-matrix.json`. Rows overlap; do not sum them as new cases.

| ID | Actual executed PostgreSQL oracle / result |
| --- | --- |
| T01 | A original blocking User-order negative control reproduced old deadlock only: PASS (1). |
| T02 | A public Employee HR-first writer waits at row, not global table gate: PASS (2). |
| T03 | A writer-first unordered User batches fail closed: PASS (2). |
| T04 | Actor/link-equal variants of T02: PASS (retained within 2). |
| T05 | Distinct actor/link variants T02/T03: PASS (4). |
| T06 | C inactive removed User and public relink winner orders: PASS (4). |
| T07 | A old User-only mixed-writer negative control and complete mixed-authority admission: PASS (11). |
| T08 | A Permission mixed-authority/unrelated update_or_create compatibility: PASS (12). |
| T09 | A Company-wait revocation and C HR-first company-access revoker: PASS (4). |
| T10 | A current actor/authority recheck after domain wait: PASS (3). |
| T11 | Actor deactivation variant after domain wait: PASS (within same 3). |
| T12 | A independent Companies share read-only authority without global gate: PASS (2). |
| T13 | Shared-actor variant of independent Companies: PASS (within same 2). |
| T14 | Disjoint-actor variant of independent Companies: PASS (within same 2). |
| T15 | A SU inactive namespace/existing DML/complete final SQL coverage: PASS (5). |
| T16 | A admitted subset/expansion/unknown outer/manual transaction: PASS (8), acquired/nested/validation also pass. |
| T17 | A selected nondefault actual alias/default trap/bootstrap/nested switch: PASS (3). |
| T18 | A NOWAIT authority User/Role/Permission conflict whole rollback: PASS (3). |
| T19 | A caught nested outer-Audit and real constraint-check timeout rollback: PASS (2), corrective native rollback families also pass. |
| T20 | C historical retry ignores inactive provenance but rechecks current revocation: PASS (2). |
| T21 | A repeated bounded hot-role refusal then independent fresh success: PASS (1). |
| T22 | A Role share readers/independent-Company compatible reads: PASS (3). |
| T23 | A supported identity writer forms and both unordered User batch orders: PASS (14). |
| T24 | A reversed active/inactive authority multirow writers: PASS (8). |
| T25 | A native Sales service and HR compatibility in both orders: PASS (2). |
| T26 | A raw/ORM implicit-relation negative controls and explicit admission: PASS (3). |

No universal deadlock-freedom, fairness, production readiness or independent
corrective acceptance is inferred. Seven full-PG watcher records remain exactly
the three declared controls; server cancellations/two raw old-protocol negative
controls remain classified in the preceding immutable evidence.

### Artifact custody, final inventory and next authorization

New external **15-record** manifest `hr1-final-artifacts.sha256`, SHA-256
`45cb6782d539e766e9f458d00a3a2851338a004f729729bc408bcf0a125b581c`,
records settings/probe/wrapper, both complete minimal logs, full frontend output,
browser readiness/facts/network/terminal logs, server/shutdown logs, both full
container inspect snapshots, and the complete prior evidence copy. Key hashes:

```text
9abaaad37f40630bf81da6f8c642481ddb058553d7ed2168405e828638416fd5  hr1-final-settings.py
4de4bb69ad79651beaad6243885ac2d673149787a817363670fe294833ec132c  hr1-final-minimal.py
b975c771882f8f665e5cc8349a410f39c74f0516009b9c8619c5e6c1f6d93b94  hr1-final-minimal-pg.log
249989a5fdcffbe79ab536b15a2b21dbaac180d681b0a975cc7dc441406176f3  hr1-final-minimal-sqlite.log
3024bb400d20c46d2ab641d492debff83ffc420c627757e21464fe7724e91779  hr1-final-frontend.log
56e5d3f5056c0bfd1ecf133022ee9500dc88e9a55ebcece5b600190fd5abffeb  hr1-final-browser.py
```

After retaining results/inspect/logs, verified the four exact task IDs, pinned
images and read-only host mounts. Only the custody-commented hr1_final_minimal
DB plus PostgreSQL technical DBs existed, with zero other client sessions.
Normally stopped/removed these four containers and the exact now-empty internal
network; no force/prune/image removal or unrelated container operation. Their
synthetic databases, including browser SQLite, are unrecoverable; all logs and
pinned images remain. Existing djangobusinessos demo containers and ecom-local-db-1
were untouched. No recurring automation was created or reactivated.

Exact preserved dirty paths (zero staged) remain:

```text
businessos/modules/hr/admission.py
businessos/modules/hr/civil_time.py
businessos/modules/hr/conflicts.py
businessos/modules/hr/history.py
businessos/modules/hr/persistence.py
businessos/modules/hr/selectors.py
businessos/modules/hr/services/__init__.py
businessos/modules/hr/services/attendance.py
businessos/modules/hr/support.py
docs/exec-plans/active/HR_1_IMPLEMENTATION_EVIDENCE.md
tests/test_hr_admission.py
tests/test_hr_history.py
tests/test_hr_models.py
tests/test_hr_nested_services.py
tests/test_hr_audit_acquired.py
tests/test_hr_audit_history.py
tests/test_hr_audit_persistence.py
tests/test_hr_audit_validation.py
```

Branch phase3a-hr1-implementation and HEAD
`e6b72896e10471463b8b6b280fbccfc524d7cc42` unchanged. Parent/local main/
origin-main/local HR-0 remain `b36cdba91654e6a583735d67f7f6cf27a835003e`.
Read-only live ls-remote also returned main/HR-0 at b36, HR1/Phase4 remote absent;
no fetch. Held local Phase4 remains
`735e1bea13bc58fa71d430163422139d5c0f2363`, ON HOLD. No ADR/plan history,
Core/other-module, lockfile or frozen candidate changes; this repository edit is
append-only evidence. Final hash/path/whitespace checks accompany the handoff.

Required next disposition: approve registry access for the normal locked npm ci
verification, and approve a **task-exclusive localhost-published browser network**
with the specified isolation boundary (not an unapproved default-bridge connection).
Then restore/verify dependency installation, execute both CSS builds/static/
template checks and real browser matrix. No full Python suite or minimal proof
needs repetition solely for these environment blocks while all59 hashes and
retained execution profiles remain unchanged. No staging/commit authorization is
requested or inferred. A production fix still requires separate owner direction
if any genuine app defect is later demonstrated.

```text
HR1-AUD-1 CORRECTIVE VERIFICATION:
INCOMPLETE / NOT AUDIT-READY

NO COMMIT.

FULL POSTGRESQL: 4326 PASSED, EXIT 0 — RETAINED, NOT RERUN
FULL SQLITE: 2763 PASSED / 1563 CLASSIFIED SKIPS, EXIT 0 — RETAINED, NOT RERUN
MINIMAL POSTGRESQL / SQLITE: PASS, BOTH EXIT 0
JAVASCRIPT: SYNTAX PASS / 21 TESTS PASS
FRONTEND DEPENDENCIES: BLOCKED — NPM REGISTRY DNS ENOTFOUND
CSS REPRODUCIBILITY / FRESH BROWSER: NOT PROVEN
FOUR P2 CORRECTIONS: PENDING FRESH INDEPENDENT RE-AUDIT
LOCAL CORRECTIVE COMMIT: NOT AUTHORIZED
HISTORICAL TIMEOUT ATTRIBUTION: NOT PROVEN
PHASE 4: ON HOLD — UNCHANGED
PUSH / PR / TAG / MAIN UPDATE: NONE
AUTOMATION: NONE CREATED
STOP.
```

## HR1-AUD-1 frontend/browser completion — all local gates complete

Date: **2026-10-20 Asia/Dhaka**. The owner's direct continuation explicitly
authorized HTTPS registry access for locked npm ci and a task-exclusive disposable
Docker network with HTTP bound only to 127.0.0.1. The later instruction to
"complete incomplete task" continued the same scope; it did not authorize code,
staging, commit, push, PR, tag, main adoption, Ecommerce or Phase 4. No earlier
security-review rejection was bypassed. The newly authorized operation was
submitted to review and allowed; it did not attach to the default Docker bridge.

**All remaining mandatory LOCAL gates are complete.** This is an implementation
verification record, NOT fresh independent corrective re-audit, hosted exact-head
CI, formal acceptance, canonical HR-1 adoption or production approval. The four
P2 corrections remain pending fresh independent re-audit, not self-closed.

### Unchanged candidate and retained completed suites

Before progression and after the executed gates, all **59 frozen input hashes**
matched manifest `hr1-hardening-frozen-inputs.sha256`, SHA-256
`9415b9cf5b4e6df60b786c8e1662fcbcdd2ed17cb746ce96bd34e2517b9e1a29`.
No production/test contract correction occurred. Both complete regression logs,
JUnit, immutable execution profiles and prior quality/minimal evidence remain
applicable, not stale and **not rerun**:

| Retained gate | Actual completed result |
| --- | --- |
| Full PostgreSQL | 4326 passed / zero failures, errors or skips; 3993.41s; exit0; 4326 JUnit cases. |
| Full SQLite | 2763 passed / 1563 explicitly classified backend-specific skips / zero failures or errors; 939.25s; exit0; all4326 JUnit cases accounted for. |
| Python quality | Canonical Ruff, explicit48-file formatting, Django check and migration drift PASS; 248 architecture/registry/database guard tests PASS. |
| Bootstrap/topology | Fresh full-topology bootstrap PASS; independently configured minimal PostgreSQL and SQLite both exit0 with ten HTTP screens, exact twelve permissions, native services/denials/idempotency and no financial imports/tables. |

The preceding interrupted/failed histories remain verbatim. The entire
pre-append evidence file is retained as `hr1-ui-final-evidence-before.md`, SHA-256
`78eee4eb978ff4c14c2c70bacc524c0aaf4071e11c27eeb74f4e04aa18a0fafd`.
No passed run retroactively proves the two historical HR timeout root causes;
their attribution remains separately NOT PROVEN and the two-second budget is
unchanged. The earlier host-memory/Docker interruption remains its separately
established infrastructure incident, not an assertion failure or replaced PASS.

### Frontend and static/template execution

Actual authorized serial frontend run: **21:44:30.8462816–21:44:50.9612739 +06:00**,
**20.1154401s**, shell **exit0**, Node **v24.20.0**, npm **11.19.0**. Commands:

```text
npm ci --registry=https://registry.npmjs.org
npm ls --depth=0
node --check static/js/app-navigation.js
node --test tests/js/test_app_navigation.cjs
npm run build:css
SHA256(static/css/tailwind.css) == frozen hash
npm run build:css
SHA256(static/css/tailwind.css) == frozen hash
git diff --exit-code HEAD -- package.json package-lock.json
```

Actual results: locked install added73 packages/audited74; installed top-level
dependency tailwindcss **3.4.17**; all **21 JS tests PASS**, zero failed/skipped,
TAP duration **171.5536ms**. Syntax PASS. Tailwind build1 reported1879ms and
build2 845ms; both produced exactly
`a7c650044ad3e2b11df25f8c84e749a2c3f0fd3d1a55edff6f974f7061219cae`.
The existing package/lockfile were unchanged. A final bounded syntax check also
passed the complete local set: app-navigation.js, test_app_navigation.cjs and
tailwind.config.js. No npm fix/upgrade, alternate registry or dependency contract
change was made. The prior incomplete ignored node_modules installation is now
replaced by a successful locked install.

Actual npm output retains **eight advisories: two moderate/six high**, matching
the inherited count; not a claim that advisories are fixed or independently
triaged. Both builds retain the caniuse-lite/Browserslist-age warning. These are
disclosed inherited maintenance limits, not newly introduced HR changes. Actual
Node24 is not represented as hosted CI's Node22 or exact-head hosted evidence.

In the coherent disposable minimal environment, command
`python /probes/hr1-ui-final-control.py quality` returned **exit0**, native Django
check zero issues, and compiled all **seven** HR templates: detail, error, form,
list, menu, navigation and revisions. Native static finders resolved
`/app/static/css/tailwind.css` and `/app/static/js/app-navigation.js`.
All rendered screens below exercised the actual shared shell/templates. DOM
inspection additionally observed loaded local Tailwind CSS176 rules and
businessos.css493 rules, the local app-navigation script and pinned Alpine3.14.9 /
HTMX2.0.6 script URLs. Successful static GETs are retained in the server log.

### Disposable browser environment and custody

New fixture `hr1-ui-final-browser`, immutable ID
`df661cda58d3ff5c21d31eeb6401053da89f9274324af1d15383b9bd6b7ade93`,
uses the existing pinned QA image
`sha256:a7a3476a1883cddc11d7c9bcf7d7674c5c9396211f2b654337a58a1c9936637f`.
It starts the unchanged external `hr1-final-browser.py` wrapper / preserved
`hr1-recovery-fixture.py` under coherent `hr1-final-settings.py` in a fresh process.
App and probes are read-only binds; root filesystem read-only, tmpfs `/tmp`,
all capabilities dropped, no-new-privileges; bytecode disabled. Synthetic SQLite
is inside task tmpfs only. No customer/demo/production database was accessed.

Exclusive bridge `hr1-ui-final-browser-net`, ID
`ce77a29aafa7a4a99d0a8da37f40cf1a7eedee7548d17f43f2675eb09fff4758`,
has container-to-container communication disabled and only this container.
Actual bindings: **127.0.0.1:51145 -> 8000** (normal scripts) and
**127.0.0.1:51146 -> 8001** (script-stripped fallback). No wildcard/LAN binding,
default-bridge attachment or Docker/host security-setting change. This bridge
is not claimed to be an egress firewall; it is the separately approved
task-exclusive network, with loopback-only published HTTP.

Actual command: bash pipefail with
`python /probes/hr1-final-browser.py 2>&1 | tee /tmp/hr1-ui-final-browser.log`.
Server lifecycle: **15:45:14.822572833Z–16:27:44.563104091Z**
(21:45:14–22:27:44 Asia/Dhaka). It was deliberately stopped only after proofs
were retained. Its final server state is **exit137 / OOMKilled=false following
the requested docker stop**, not a successful finite-run exit0, unexpected pytest
failure, or proof of OOM. The finite frontend, template/static and read-only
native-check gates independently returned exit0. No new unexpected HR timeout,
AuthorityBusy/deadlock, 5xx or data-integrity failure was found in the server log.

### Actual real-browser execution

Computer-use skill/safety guidance selected the supported in-app browser and
real DOM, screenshot, navigation, locator and keyboard APIs. Source inspection
was not substituted for execution. The run retained **126 browser records and
126 PNG screenshots**, including **90 route/width** samples: the actual30 native
HR routes at **390px, 768px and 1280px**,30 at each width. These include both
Employee list aliases, every six-model list/detail/create/edit surface, Employee
end/transfer, Attendance correct/void/reinstate/history and all Leave action forms.
The extra list alias accounts for30 rather than the earlier historical29.

All90 samples had real HR headings and **no page-level horizontal overflow**.
Long data includes32-character codes,160-character setup names,200-character
Party projection and2000-character reasons; no truncation/rewritten CSS was used.
Wide tables retained local overflow:auto (mobile example380px scroll area /
760px table). Actual ArrowRight focus/scroll reached the table container,
scrollLeft5.333px while page scrollX remained0; right-hand columns are local
table content, not a document overflow. Representative mobile/tablet/desktop
screenshots were visually inspected in addition to the retained full sweep and
live geometry. Responsive error pages were separately rendered at all3 widths,
retaining input and visible role=alert content without page overflow.

| Browser gate | Actual observed result |
| --- | --- |
| Login/Company | Native synthetic login, dashboard and Company selection work; no real-user credentials/data. |
| Employee | Bounded Person-name lookup finds unassigned PERSON; future joining date gives expected field alert with retained values. Create BROWSER-1 -> ACTIVE revision1; edit joining date -> revision2; explicit end -> ENDED revision3. Detail/list and transfer form inspected at all widths; no extra transfer POST claimed. |
| Department | Native CSRF-protected create UI-DEPT revision1, rename/retire -> inactive revision2. Historical/long and management screens all widths. |
| LeaveType | Native create UI-TYPE revision1 and rename revision2; actual selected labels and detail reflect new name; all management screens/widths. |
| Attendance | Native record -> revision1, correction -> revision2/end11:00, void -> revision3, reinstate -> ACTIVE_INTERVAL revision4. Revision history actually displays RECORD/CORRECT/VOID/REINSTATE without deletion. Original long-reason history also rendered all widths. |
| Leave | Native draft creation/edit/submit/cancel reached CANCELLED; separately requested fixture Leave approved by different actor -> APPROVED; another draft submitted by operator and rejected by other actor -> REJECTED with mandatory reason. An additional2000-character draft retained for layout. Actions/detail/history meanings preserved. |
| 50+1 pagination | Status ACTIVE yields exactly51 active Employees after the newly created Employee was ended; page1 has50 rows and page2 exactly1 (QA-050). q/status parameters preserved in Next/Previous links. |
| Search/history | Search QA- with ACTIVE yields50 rows. Keyboard Enter submits the native filter. Actual Back, Forward and refresh retain q/status/page and50+1 position; normal HTMX navigation/fragment updates observed. |
| Keyboard | Enter opens mobile launcher and focuses Search apps; Shift+Tab wraps to Dashboards, Tab wraps back to Search apps, Escape closes/restores Open apps. Error-date input remains keyboard focusable; native date segments may retain focus within the same input on Tab, not falsely claimed to jump immediately to the next field. |
| Stale Company | Two real tabs: Department form rendered under Primary, fixture scope switched to Second, POST -> HTTP400 with explicit Company-scope-changed alert; no silent target switch. Foreign Primary Employee under Second -> access-required403, no Employee projection leaked. |
| Stale Branch | Attendance form rendered Company-wide, session switched to Branch A, POST -> access-required403 because actor lacks that new Branch grant. Fail-closed before mutation. This is NOT mislabeled as a freshly demonstrated granted-Branch field-level alert; the full regression retains that broader matrix. |
| CSRF | Explicit synthetic missing-token Department POST ->403, native "CSRF token missing" message. Normal Employee/Department/Attendance/Leave POSTs used genuine form CSRF and succeeded. |
| Native/Audit negative effects | Read-only full-field hashes of all six HR tables plus Audit are identical before/after stale Company, foreign-record, stale Branch and missing-CSRF controls. Forbidden Department codes absent. |
| Disabled module | Task-only registry disabled through native register_manifest while preserving Party flag; real browser /hr/ ->404 and dashboard has zero HR links. Native registry enable restored HR only; no production deployment/config changed. |
| Non-JavaScript | Separate script-stripped server actually has document.scripts.length=0. Native logout/login, Company selection, HR navigation, Enter GET filter (QA-050 -> one row), and CSRF-protected Department POST create NOJS-OK succeeded. This is zero-script fallback, not a claim the browser's global JavaScript setting was changed. |
| Runtime/assets | No console warnings/errors observed in inspected browser logs; retained console record is []. Native server has no unexpected HR budget/lock/5xx errors. Browser-generated optional /favicon.ico404 is retained, not a failed HR static asset or hidden application exception. |

Finally, a separate **read-only SQLite native check, exit0**, verified actual
BROWSER-1 ENDED/revision3/dates, Attendance ordinals1–4 with exact operations,
Leave CANCELLED/APPROVED/REJECTED/DRAFT identities, Department inactive/revision2,
LeaveType rename/revision2, one NOJS-OK row, zero STALE-COMP/CSRF-ATTACK rows and
81 total fixture/native Audit rows. After the single no-script Department create
and another rejected future-date correction, the remaining five HR table field
hashes were unchanged; no accidental Employee/Attendance/Leave rewrite.

### Tool limitations retained, not application failures

Two early wait probes assumed the wrong instantaneous DOM/field label (history
table before settled navigation, generic Reason versus actual Cancellation
reason). Fresh DOM inspection corrected the locator, without changing app code,
test expectations or server outcomes; the native settled history/label and
operations were actually verified. Early transient navigation/filter snapshots
are retained alongside later URL-and-result checks, not falsely counted as
completed outcomes. A later owner continuation cleaned temporary browser tabs;
the new tab reopened retained data, without rerunning the90-surface sweep.

The browser's read-only DOM sandbox does not expose performance.getEntriesByType;
that instrumentation probe errored before any app interaction. Static evidence
instead uses actual loaded stylesheets/script DOM and server GET logs. Docker cp
reported missing files on the tmpfs path although docker exec ls/read proved
them present; complete tee/facts bytes were exported through read-only exec/base64
instead. The Docker stdout log independently retains the full server stream.
These transport/locator limitations are disclosed; they are not security-review
bypasses, hidden mandatory test failures, a retry-until-green production fix or
new HR budget/deadlock incidents. No security operation was denied in this newly
authorized batch. Earlier registry/network denial history remains intact.

### Final H01-H18 and T01-T26 local reconciliation

The retained full JUnit and `hr1-recovery-executed-matrix.json` remain the exact
test-path/parameter evidence for every row; all1311 HR cases across24 files passed
within the4326 full PG cases. Browser does not certify PostgreSQL locks/races.

| ID | Requirement / actual local evidence | Local disposition |
| --- | --- | --- |
| H01 | Two-Company isolation; permissions/http/foreign-ID tests plus actual stale Company/foreign Employee refusal and identical seven-table snapshots | PASS. |
| H02 | Current/frozen Branch, transfer/history scope; branch_scope/concurrency/domain_races plus all-width transfer form and actual new-Branch denial | PASS bounded executed evidence; granted-Branch field alert not newly claimed. |
| H03 | Employee/Party/number/User identity and minimal projection; models/identity_races/adversarial plus long projection UI | PASS. |
| H04 | Bounds/normalization/identity keys/races/retirement; services/reference/identity races plus actual Department/LeaveType management | PASS. |
| H05 | Exact twelve/compound RBAC/self-decisions; permissions/self_decisions plus native minimal identity/denial and distinct-actor browser decisions | PASS. |
| H06 | Registry/default-disabled/enablement/HTTP gating; installation_contract/http/models, minimal proofs and actual browser404/no HR links/restoration | PASS. |
| H07 | Execution alias/default trap/nesting; admission/acquired/validation/nested_services completed PG cases | PASS retained actual oracles. |
| H08 | Intervals/conflicts/resources/retry; flows/history/domain_races/resource_boundaries plus actual browser Attendance lifecycle | PASS. |
| H09 | Civil/fold/gap/long/extreme/historical arithmetic; civil_time/audit_history/history/http plus precise rendered interval UI | PASS retained executed oracles. |
| H10 | Full immutable chain/receipt/history; history/audit_history/audit_persistence/models plus browser1–4 revisions/native check | PASS. |
| H11 | Leave dates/lifecycle/receipts/self-decisions; flows/services/civil_time/self_decisions/adversarial plus actual create/edit/submit/approve/reject/cancel | PASS. |
| H12 | Exact PostgreSQL lock/race/read-authorization matrix | PASS T01–T26 retained below. |
| H13 | Admission/authority/budget/work bounds; admission/acquired | PASS retained actual PG oracles; budget unchanged. |
| H14 | Outer/native/revision/receipt/Audit rollback; validation/acquired/nested/setup/adversarial plus seven-table browser-negative equality | PASS. |
| H15 | HTTP/forms/CSRF/scope/search/pagination; http/permissions plus actual native/HTMX/browser/fallback results above | PASS. |
| H16 | Real responsive/action/error/keyboard/navigation/non-JS/console QA | PASS bounded local run:90 route/width observations, workflows and controls above; not a universal accessibility certification. |
| H17 | Supported independent installation/minimal topology/migrations/registry/bootstrap/security | PASS retained full and both minimal fresh-process proofs; all59 inputs unchanged. |
| H18 | Mandatory LOCAL quality/frontend/browser/docs integrity, distinct from external acceptance | LOCAL PASS; fresh independent re-audit, hosted exact-head CI, formal acceptance and canonical adoption remain PENDING. |

T01–T26 each retain **PASS** against actual full PostgreSQL node IDs/variants and
counts in the preceding complete T table and matrix JSON; no inherited partial
run, new SQLite concurrency assertion or new test execution is substituted:

| IDs | Actual retained PostgreSQL oracle families / local result |
| --- | --- |
| T01 | Original blocking User-order isolated negative control — PASS1. |
| T02 / T03 | HR-first row wait / writer-first unordered batch refusal — PASS2 / PASS2. |
| T04 / T05 | Equal actor/link and distinct union variants — PASS within2 / PASS4. |
| T06 | Inactive removed User / relink winner orders — PASS4. |
| T07 / T08 | Mixed Role/User negative/current admission / Permission compatibility — PASS11 / PASS12. |
| T09 / T10 / T11 | Company-access revoke / authority-after-domain-wait / actor variant — PASS4 / PASS3 / PASS within3. |
| T12 / T13 / T14 | Independent Companies / shared actor / disjoint actor — PASS2 with variants retained. |
| T15 | SU inactive namespace, DML and final SQL coverage — PASS5. |
| T16 / T17 | Nested subset/expansion/unknown outer / selected alias/default trap — PASS8 / PASS3. |
| T18 / T19 | NOWAIT partial authority rollback / nested native-Audit timeout rollback — PASS3 / PASS2 plus corrective files. |
| T20 / T21 / T22 | Historical retry/current revoke / hot-role bound / compatible readers — PASS2 / PASS1 / PASS3. |
| T23 / T24 | Supported/reversed User writers / reversed active/inactive Role/Permission batches — PASS14 / PASS8. |
| T25 / T26 | Actual Sales/HR compatibility / implicit-relation negative and explicit admission — PASS2 / PASS3. |

Counts overlap and are not new unique tests. Original raw old-protocol deadlocks
and three declared timeout controls retain their explicit classifications; no
new current-protocol event was accepted or dismissed as flakiness.

### Retained artifacts, cleanup and unchanged refs

External root remains
`C:\Users\HP\.codex\visualizations\2026\09\13\01a09a3b-7a01-72e3-86bc-21a752d748fc`.
New **148-record** manifest `hr1-ui-final-artifacts.sha256`, SHA-256
`1b894a967993b806a7503879b1c710256b2e412664090fb00911b71caded66d7`,
includes126 PNGs,126-record browser JSON, frontend log, template/static transcript,
seven-table before/after/native snapshots/checks, fixture/control helper sources,
network/lifecycle/log/facts records, finishing DOM/console/asset evidence and the
whole pre-append evidence copy. Key hashes:

```text
bb821f98f21f629ca7d7d366b619284ed363f9001453f979002f8fd5b3824413  hr1-ui-final-frontend.log
1f413743b73ec33074f7a0745705606400cb113d0bf8f98543cdf9133bced020  hr1-ui-final-browser-records.json
02d3e8dfeab3fb04d28179848af038acaf7ff1d03f224e76ae850d46a8106624  hr1-ui-final-browser.log
7f361912c5f841ac12ff00ade3024f9c96e947e81015044eb1303e3067d35bbf  hr1-ui-final-native-check.log
141d2e3fb541b04f5768b921ca8085c405e56e0222454deaac8a18149c41e987  hr1-ui-final-negatives-before.json
141d2e3fb541b04f5768b921ca8085c405e56e0222454deaac8a18149c41e987  hr1-ui-final-negatives-after.json
deadad2ff4942e5652fe7005595a99b6dfe4c3351af7d7a615da549f917dc036  hr1-ui-final-template-static.log
c9a52025345ced88bf5f5055fec96c232828785e88fd8dbd5a0e5477bfdda370  hr1-ui-final-network.json
8bb59c8a889338c0383dd717a24fc2c6d0f9a74df8d776db06a03e70056c015c  hr1-ui-final-terminal-inspect.json
```

After complete retention, reverified exact container/image/read-only mounts,
loopback bindings and exclusive network. Normally stopped/removed only the named
task container and the now-empty exact network; no prune/force/image removal.
The task's synthetic tmpfs database is no longer recoverable; logs, screenshots,
helpers and pinned image remain. Other running demo/ecom containers were not
stopped, changed or incorporated into the proof. Temporary QA tabs were closed
and viewport override reset; user tabs untouched. No automation was created or
reactivated. No outstanding worker or browser fixture is intentionally retained.

The exact18 corrective dirty paths remain, zero staged:

```text
businessos/modules/hr/admission.py
businessos/modules/hr/civil_time.py
businessos/modules/hr/conflicts.py
businessos/modules/hr/history.py
businessos/modules/hr/persistence.py
businessos/modules/hr/selectors.py
businessos/modules/hr/services/__init__.py
businessos/modules/hr/services/attendance.py
businessos/modules/hr/support.py
docs/exec-plans/active/HR_1_IMPLEMENTATION_EVIDENCE.md
tests/test_hr_admission.py
tests/test_hr_history.py
tests/test_hr_models.py
tests/test_hr_nested_services.py
tests/test_hr_audit_acquired.py
tests/test_hr_audit_history.py
tests/test_hr_audit_persistence.py
tests/test_hr_audit_validation.py
```

Branch **phase3a-hr1-implementation**, HEAD
`e6b72896e10471463b8b6b280fbccfc524d7cc42`, unchanged. Parent/local main/
origin-main/HR-0 remain `b36cdba91654e6a583735d67f7f6cf27a835003e`.
Held local Phase4 remains `735e1bea13bc58fa71d430163422139d5c0f2363`.
No staging, corrective commit, push, PR, tag, merge, rebase, reset, stash, main
update, accepted-contract edit or new milestone. This batch's only in-repository
content change is this factual evidence append; generated CSS content stayed
identical. Final prefix/hash/inventory/document/whitespace/ref checks accompany
the handoff. Any future local corrective commit requires separate owner
authorization; independent audit/CI/acceptance/adoption are not inferred.

```text
HR1-AUD-1 CORRECTIVE VERIFICATION:
ALL LOCAL GATES COMPLETE

FULL POSTGRESQL:
4,326 PASSED

FULL SQLITE:
2,763 PASSED / 1,563 CLASSIFIED SKIPS

MINIMAL TOPOLOGY:
POSTGRESQL PASS / SQLITE PASS — RETAINED, INPUTS UNCHANGED

FRONTEND:
LOCKED NPM CI / JS SYNTAX / 21 TESTS / TWO IDENTICAL CSS BUILDS / TEMPLATES / STATIC PASS

BROWSER:
390PX / 768PX / 1280PX — 90 ROUTE-WIDTH CHECKS AND BOUNDED INTERACTION MATRIX PASS

H01-H18:
LOCAL EXECUTED GATES COMPLETE; H18 EXTERNAL STAGES PENDING

T01-T26:
PASS — RETAINED ACTUAL FULL POSTGRESQL ORACLES

FOUR P2 CORRECTIONS:
PENDING FRESH INDEPENDENT RE-AUDIT

LOCAL CORRECTIVE COMMIT:
PENDING OWNER AUTHORIZATION

HISTORICAL TIMEOUT ATTRIBUTION:
NOT PROVEN

PHASE 4:
ON HOLD

PUSH:
NONE

PR:
NONE

STOP.
```

## Formal acceptance checkpoint — 2026-10-21

This is a later current-status checkpoint, not a rewrite of the preceding execution record.
Earlier INCOMPLETE, audit-pending, commit-pending and PUSH NONE statements describe their own
historical checkpoints. The original failures, diagnostic measurements, partial executions and
their limitations remain preserved. The owner now authorizes one documentation-only acceptance
commit and conditional canonical adoption; no runtime/test/contract change is part of this task.

### Accepted candidate and independent review

HR-0/ADR 0018 remain canonically ACCEPTED at
`b36cdba91654e6a583735d67f7f6cf27a835003e`. Exact linear ancestry for this record is:

1. Original HR-1 implementation: `e6b72896e10471463b8b6b280fbccfc524d7cc42`.
2. Corrective implementation: `c49a1291ce979093f1219dea41d5fdcd743239b7`.
3. CI-only JavaScript coverage delta: `a867a8c240627f4161ec4ef23564a320d4cf6b49`.
4. This documentation-only acceptance commit, immediately above the CI-only SHA.

The original independent audit was **REVISE / Readiness B / four P2**. The separate fresh
implementation re-auditor returned **FINAL PASS / Readiness A**, independently resolving
HR1-AUD-001, HR1-AUD-002, HR1-AUD-003 and HR1-AUD-004. No new blocking P0/P1/P2 was reported.
Authority is the separate chat `01a15c72-5238-71e2-9852-28d968f49a8d`, titled
`Audit HR-1 corrective implementation`, not this implementation chat. Full report:
`HR1-AUD-1-corrective-re-audit-report.txt`, SHA-256
`018a3411d0f455239bd6dba4da909c7085d2bbada6c6d96b0aaddfc11d198821`.

The CI-only delta received a second separate **FINAL PASS / Readiness A**, with no P0–P3,
from chat `01a15d4d-5591-7190-a7c2-14c7858ab69f`, titled `Audit CI corrective commit`.
It independently executed Linux Node 22.23.3 JavaScript tests: 21 passed, zero failed/skipped;
strict YAML validation also passed. Full retained final report:
`hr1-ci-publication-independent-delta-audit.txt`, SHA-256
`260e2b5968f46704423053594b2595aa1f611b1e6e151b0074bf1e811ce4113e`.
Both report fingerprints were reverified for this acceptance checkpoint. The CI delta changes
only `.github/workflows/ci.yml`, adding two lines after npm ci and before the CSS build; it
does not alter HR implementation or tests.

### Actual hosted evidence reviewed before acceptance

[CI #138](https://github.com/sahinkhan/djangobusinessos/actions/runs/39543423762), run
`39543423762`, succeeded on `c49a1291ce979093f1219dea41d5fdcd743239b7`: 4,326 PostgreSQL
tests passed. It did **not** execute JavaScript unit tests. That coverage gap and the historical
publication/monitoring blocker remain recorded, not silently converted into JavaScript success.

[CI #139](https://github.com/sahinkhan/djangobusinessos/actions/runs/39567787163), workflow
`Phase 0 checks` (`357068273`), run `39567787163`, attempt 1, event `push`, branch
`phase3a-hr1-implementation`, exact head `a867a8c240627f4161ec4ef23564a320d4cf6b49`,
is **completed / SUCCESS**. Actual decoded checkout logs match that full SHA. Job `test`
(`119114168145`) completed at `2026-10-21T09:27:05Z`; the run update is
`2026-10-21T09:27:06Z` (15:27:06 Asia/Dhaka). All 20 recorded job steps succeeded.

- PostgreSQL 17.11, development PostgreSQL settings and all three optional commercial install
  flags enabled; Python 3.13.16, Django 5.2.17, pytest 8.4.2, Ruff 0.16.7.
- Fresh migrations succeeded; actual pytest collection 4,326 and terminal result **4,326 passed
  in 4305.60s (1:11:45)**, with no failures, errors or skips.
- Ruff: all checks passed. Django: zero issues. Migration drift: no changes detected.
- Node 22.23.3 / npm 10.9.9; locked npm ci succeeded. The named JavaScript unit-test step ran
  `node --test tests/js/*.cjs`: **21 tests, 21 passed, zero failed/cancelled/skipped/todo**,
  duration 97.484671ms, successful step conclusion.
- Tailwind build succeeded (690ms); `git diff --exit-code -- static/css/tailwind.css`
  succeeded. This is one hosted build/diff check, not two hosted reproducibility builds.
- npm reported **eight advisories: two moderate, six high**. No dependency fix was attempted.
  Other runtime/deprecation/Browserslist warnings remain in the complete logs. Neither warning
  disclosure nor a green workflow is a production-readiness claim.

GitHub access was restored and these actual metadata/logs were recovered and verified for this
checkpoint. The earlier access-blocked report is retained as history, not used as terminal CI
evidence. New external artifacts under the task artifact root are:

- `hr1-acceptance-ci139-run.json`, SHA-256
  `d17d84152edc264e8be4c43799f4fa3ec8e733694d3eb72c6a4accbba5a26a7b`.
- `hr1-acceptance-ci139-jobs.json`, SHA-256
  `698c4145c1b578602d599251bcd4f0b864b0d7ffd66d0463970d1a8af02558a4`.
- `hr1-acceptance-ci139-job.log`, complete decoded log, SHA-256
  `ac9f9380ee5b798350b459a975192b41fb3a5c9e03d8c9fd4e541054f80a79ec`.

No fresh hosted SQLite/browser execution is claimed by #139. Earlier successful local
PostgreSQL/SQLite/frontend/browser evidence retains its recorded profile and limitations;
unchanged implementation/test/build Git objects permit reuse rather than unnecessary full-suite
repetition. H01–H18 and T01–T26 retain the accepted technical requirements and their recorded
local/oracle results; the independent implementation report supplies the separate re-audit
disposition. Hosted evidence is now specifically #139, not inherited local JavaScript results.
This docs-only checkpoint does not invent new oracle runs, counts or an additional self-audit.

### Formal acceptance, scope and conditional adoption

HR-1 runtime implementation is **FORMALLY ACCEPTED FOR CANONICAL ADOPTION at this documentation
checkpoint**. Scope is HR Foundation v1: Employee, Department, Attendance, AttendanceRevision,
LeaveType and LeaveRequest. HR-0/ADR 0018 remain the accepted technical contract. Six ownership
rules, twelve permission identities, lifecycle/history/timezone semantics, ROW SHARE NOWAIT,
complete User/Role/Permission locks, Core final guards, selected alias, whole-outer nested
rollback, immutable receipts/historical retries and H01–H18/T01–T26 are unchanged.

Canonical adoption remains **PENDING** until the
[conditional completion rule](PHASE_3A_HR_FOUNDATION.md#conditional-canonical-completion-rule)
is actually fulfilled: new exact-head acceptance-branch CI succeeds; unchanged main is normally
fast-forwarded to that exact acceptance SHA; separate exact-head main CI succeeds. The actual
acceptance SHA and future observed run metadata/results must be recorded externally without
another commit. This section asserts no future main push, CI count/success or canonical closure.

Historical unexpected native SQLSTATE 57014 causal attribution remains **NOT PROVEN**;
historical unexpected ResourceBudgetExceeded causal attribution remains separately **NOT
PROVEN**. The older partial full run (4,326 collected / 4,313 PASS tokens / no terminal summary)
remains INTERRUPTED, not PASS and not 13 presumed test failures. Retained host evidence proves
an infrastructure interruption and component-level Docker monitor memory failure; the exact
allocation/termination chain and container OOM remain NOT PROVEN. These are not correctness
waivers and do not change the independently RESOLVED four P2 dispositions.

The original worktree remains on local HR-1 at `c49a1291ce979093f1219dea41d5fdcd743239b7`,
with its four uncommitted policy files and index preserved. Acceptance work uses the new clean
isolated `hr1-formal-acceptance` checkout at the exact CI-only base; no uncommitted policy is
copied into this release. The four permitted documents are append-only. Source, tests,
migrations, manifests, frontend, packages, CI and accepted ADR Git identities must remain exact.
Non-mutating docs-only quality checks use the pinned QA image
`sha256:a7a3476a1883cddc11d7c9bcf7d7674c5c9396211f2b654337a58a1c9936637f`, read-only source,
network none, in-memory SQLite test settings and all three install flags: Django check reports
zero issues; makemigrations `--check --dry-run` reports no changes; `ruff check . --no-cache`
passes (Python 3.13.16 / Django 5.2.17 / Ruff 0.16.7, exit 0). No local full suite was rerun
for prose-only acceptance. Prefix, link/anchor, fence, whitespace and exact-object checks are
mandatory before committing; their actual results and publication sequence are external records.

Phase 3 remains **NOT COMPLETE**. ECOM-0 is separately governed and NOT STARTED BY THIS TASK;
ECOM-1 is NOT STARTED. Ecommerce and the final combined Phase 3 audit/closure remain future
gates. This is not Full Enterprise HR, Payroll, recruitment, shifts, biometrics, SaaS/tenant
activation or production readiness. Phase 4 Education/Healthcare remains **ON HOLD** at
`735e1bea13bc58fa71d430163422139d5c0f2363`; ADRs 0019–0021 remain PROPOSED and untouched.
No automatic remediation, new phase, PR, tag or force push is authorized.
