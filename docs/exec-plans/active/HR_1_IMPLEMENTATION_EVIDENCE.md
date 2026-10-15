# HR-1 local implementation evidence

Canonical base: `b36cdba91654e6a583735d67f7f6cf27a835003e`.
This is an implementation-run record, not an independent audit or acceptance.
The accepted [HR-0 contract](PHASE_3A_HR_FOUNDATION.md) remains unchanged.

**Latest local status:** all required implementation-run verification completed;
see [Completed local verification](#completed-local-verification). Earlier
pending statements and failed attempts below are retained chronological evidence,
not the current gate status. Independent audit and hosted CI are not performed;
acceptance, canonical adoption and production deployment are not authorized.

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
