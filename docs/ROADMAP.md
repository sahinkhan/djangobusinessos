# BusinessOS Roadmap

## Strategy

BusinessOS follows a staged evolution:

1. ship business value fast;
2. harden what real customers use;
3. extract shared platform capabilities only after repeated needs appear;
4. preserve an eventual path to a protected BusinessOS kernel and optional custom Python runtime.

The roadmap is capability-driven, not date-driven. A later phase should not begin merely because time passed; it begins when earlier exit criteria are met.

---

## Phase 0 — Foundation

Backend checkpoint for the Option A contract: Gate TDB-1 is canonically closed at
`d65eeee14923910a6b28f11a840a465b1d28ac6f`, tagged `tenant-db-foundation-v1`, after independent
FINAL PASS, candidate CI #88 and main CI #89 (769 PostgreSQL tests). Its original execution-plan
candidate evidence remains historical. ADR 0012's contract applies in single-database mode;
actual SaaS activation remains deferred. `ui-foundation-v1` remains unchanged at `65a0e46b...`.

Goal: establish the minimum architecture needed to unblock fast module development.

Current correctness status: COMPLETE. Foundation remediation was accepted at
`f1f7f2f6c917308bedb3c48e51b8113a064d96c2`; Core Foundation v1 remains FROZEN by ADR 0009 and is
reconstructed as the canonical Phase 0 checkpoint `4ef16c271dfce235dbcb874fabaa5df0c63edd54`
on canonical `main`.

Deliver:

- Django 5.2 LTS / Python 3.13 project
- PostgreSQL
- custom User model
- Company / Branch / Warehouse
- Country / Currency / Language / UoM references
- basic organizational access
- BusinessContext
- lightweight module manifest/registry
- shared UI shell
- pytest + Ruff
- Docker development baseline

Do not deliver workflow, metadata, event bus, Redis/Celery, React, microservices, tenancy or marketplace.

Exit gate: foundation tests/checks pass and shared contracts are frozen enough for parallel module development.

---

## Phase 0H — Core Foundation v1 Hardening

Status: Complete — FINAL PASS restored. The prior freeze recorded at
`5e10ec23ad91a4ba8ef75ea7d29e8b2fb26e2095` on `foundation-v1-hardening` remains historical
evidence of the acceptance later withdrawn by adversarial audit. Correctness remediation at
`f1f7f2f6c917308bedb3c48e51b8113a064d96c2` passed independent re-audit; ADR 0009 is Accepted and
freezes that implementation as the Core Foundation v1 operational baseline.

Deliver:

- minimal company-scoped BusinessOS RBAC with deny-by-default authorization
- deterministic module permission declarations and registration
- append-only Core audit records for security-sensitive actions
- explicit company/branch/warehouse grant and revoke services
- Company country, default language, IANA timezone and shared business-time helpers
- immutable Company base currency through normal mutation paths
- immutable Country/Currency/Language/UoM and permission identity codes
- a documented boundary between Django technical permissions and BusinessOS authorization

Exit gate: PASSED. Gate 2 received independent FINAL PASS against the accepted remediation SHA.
Gate 3A received independent FINAL PASS at accepted candidate
`780144c5560e1d46cc5d545dc29b33522cd2d1f5`; hosted CI #42 succeeded at that exact SHA. Gate 3B
canonical `main` cutover received independent FINAL PASS at
`29d6c12913145bd1b64f572b5bc94c1f53d9987a`, with hosted main CI #45 successful. Gate 3 is closed;
At that historical Gate 3 checkpoint, Phase 2 / Gate 4 adoption remained separately gated and
unauthorized; the subsequently authorized Phase 2 sequence is recorded below.

---

## Phase 1 — Shared Commercial Primitives

Status: COMPLETE. Accepted Party + Catalog behavior is replayed on the canonical Core baseline at
checkpoint `5b95aaa0f13a64a862999e13c6533d1bbb5c81f3`. ADRs 0004 and 0005 remain Accepted.

Deliver:

- Party / Contacts
- Catalog / Products / Categories
- ProductVariant as the concrete sellable/purchasable SKU identity
- minimal Attributes / Attribute Values for real variable products
- simple products represented internally by one default ProductVariant
- reusable document numbering basics only if Phase 1 flows require them
- shared form/list/detail UI patterns

Catalog remains free of stock balances, transactional pricing engines, Sales/Procurement workflow and Accounting.

Do not build an advanced variant configurator, automatic combination generator, pricelists/promotions, Inventory quantities or ecommerce-specific product copies in this phase.

Exit gate: Sales/Procurement/Inventory can consume stable Party/Catalog contracts, and both simple and variable products resolve to stable ProductVariant identities without redesign.

---

## Phase 2 — Commercial Core

Current canonical status: **CANONICALLY CLOSED** at
`0d4a14254889ba1ec06cfb16088009177991d8d8`. Main push CI #133 (run `38549126483`) succeeded
on that exact SHA with 3,015 PostgreSQL tests; final exit matrix: 13 PASS / 0 FAIL / 0 NOT PROVEN.
The acceptance-stage and earlier milestone records below are preserved historical checkpoints;
their then-pending adoption wording does not override this current status.

Current milestone — 2026-10-14: **FORMAL PHASE 2 CLOSURE COMPLETE FOR CANONICAL ADOPTION;
CANONICAL ADOPTION PENDING.** The owner authorizes this documentation-only formal acceptance
of the completed architecture/corrective series, not a main update or Phase 3 work.
Canonical starting `main` remains `669936df432ec1bb12792ed8d31741fbb1b1287a`:
**ACC-INT-1 CANONICALLY CLOSED**, exact-head main CI #130 attempt 2 SUCCESS. Attempt 1's
synthetic-policy/autovacuum deadlock is preserved in the execution-plan history.

Preserved corrective ancestry:

```text
669936df432ec1bb12792ed8d31741fbb1b1287a
→ 2fbd4a2ae02eda31c6273456a2599b0a2f90339a
→ 368dc70aa7bdcefd3191661b4569ccfad29f4069
→ f4925f70fa2efc12a6c0dabad9facc515213efe9
→ 4a2a7ecaa26e1e312a482e405cd763efdc5f2d74
```

The supplied combined independent audit returned **FINAL PASS / Readiness A** with
**13 PASS / 0 FAIL / 0 NOT PROVEN**. Corrective-candidate hosted **Phase 0 checks #131 /
38537403882 SUCCESS** tested exact `4a2a7ec...`: **3,015 PostgreSQL tests passed**, none failed
or skipped; fresh migrations and mandatory quality/frontend checks passed.
PH2-FINAL-AUD-1, PH2-AUTH-CORR-1, PH2-AUTH2-AUD-1, PH2-CLOCK-1 and ACCINT1-AUD-1 are RESOLVED.
This docs-only checkpoint resolves PH2-FINAL-DOC-1 without erasing historical REVISE evidence.
Original historical SQLite failure attribution remains **NOT PROVEN**.

The [formal closure record and exit matrix](exec-plans/active/PHASE_2_COMMERCIAL_CORE.md#phase-2-formal-closure-for-canonical-adoption--2026-10-14)
distinguishes independent audit, implementation runs and hosted evidence. This closure commit
requires its own exact-head branch CI; later separately authorized unchanged-main/ancestry
verification, direct fast-forward adoption and exact-head main CI are still required. Phase 2
is **not yet canonically closed**. No PR, tag, production readiness, deployment, SaaS activation
or Phase 3 authorization is granted by this checkpoint.

### Historical milestone chronology

The following dated acceptance-stage statements retain their original scope and baselines;
the current status above and current gate summary below supersede their pending/not-started wording.

Milestone — 2026-10-12: **PAY-INT-1 CANONICALLY CLOSED** at
`a1079985a2ef5645dfed338e3e58af54f5242e1a` after normal fast-forward adoption and successful
exact-head main CI. Original implementation `4b8a072da4426a48988d4605641bf1fc846c06ee`,
corrective implementation `bef50fe8b20f97aaeefb8c610a46d412e9a05402` and the original independent
REVISE / readiness C history are preserved. Corrective independent FINAL PASS / readiness A closed
**PAYINT1-R1, PAYINT1-R2, PAYINT1-R3 and PAYINT1-R4: RESOLVED**.
Hosted Phase 0 checks
[implementation #118 / 38162359131](https://github.com/sahinkhan/djangobusinessos/actions/runs/38162359131),
[acceptance #119 / 38163571737](https://github.com/sahinkhan/djangobusinessos/actions/runs/38163571737)
and [main #120 / 38164395135](https://github.com/sahinkhan/djangobusinessos/actions/runs/38164395135)
all succeeded with **1,613 PostgreSQL tests each**, fresh migrations and all mandatory checks.
#118 tested the corrective SHA; #119/#120 tested the canonical freeze. No PAY-INT-1 tag is claimed.
Earlier adoption-pending statements below describe their historical acceptance stage.

**ACC-INT-0 — Billing / Payments Outcomes -> Accounting Posting Contract: FORMALLY ACCEPTED**,
2026-10-12, documentation only on `accint0-accounting-outcomes-contract`, from that exact main.
[ADR 0016](decisions/0016-accounting-commercial-outcomes-integration-contract.md) is
**Accepted — Gate ACC-INT-0** after supplied independent **FINAL PASS — ACC-INT-0 CONTRACT
APPROVED FOR FORMAL ACCEPTANCE**, readiness **A**, no candidate-owned P0–P3, and hosted
**Phase 0 checks #125 / 38203841663 — SUCCESS**
([run](https://github.com/sahinkhan/djangobusinessos/actions/runs/38203841663)) at exact audited
proposal `207c78096f419b4d924326df256355a356a3f3d7`: **1,613 PostgreSQL tests**, fresh migrations
and all mandatory checks passed. **Formal acceptance COMPLETE; canonical adoption PENDING
at this acceptance checkpoint**, requiring acceptance CI, direct fast-forward and separate main CI.
The unchanged contract defines two
Accounting-owned opt-in apps: invoice AR/Revenue independently of Payments, and allocation Cash/AR
after a valid invoice Accounting posting. Explicit Journal/Account IDs, immutable source/effect
bindings, owner financial bases, complete evidence and atomic public-service composition are
accepted, not implemented. Original proposal/verification history remains in the ADR and plan.
Inherited non-blocking ACCINT0-DOC-1 remains unmodified; npm/Actions/Browserslist maintenance
is not remediated. No runtime, permission, migration or UI change is authorized by acceptance.
That acceptance-stage authorization statement is historical. The ACC-INT-1 starting canonical base was
`4419bdc4f0210894065400923741dd5449ffd158`; **ACC-INT-0 CANONICALLY CLOSED**.
**ACC-INT-1: FORMALLY ACCEPTED FOR CANONICAL ADOPTION** on `accint1-accounting-outcomes`.
**Formal acceptance COMPLETE; canonical adoption PENDING at this acceptance checkpoint.**
Original candidate `5bfc055b1fb6c2b806a4f4bbf04fc749cc9020fe` and its independent
**REVISE — Readiness B / ACCINT1-AUD-1 — P2** result remain historical evidence.
Corrective candidate `2c7c8109f875909b34cc089698cb6d7dde572266` received the supplied independent
**FINAL PASS — ACC-INT-1 CORRECTIVE IMPLEMENTATION APPROVED FOR HOSTED CI / Readiness A**;
**ACCINT1-AUD-1 independently RESOLVED; no new actionable candidate-owned P0–P3 findings**.
Exact-head hosted **Phase 0 checks #128 / 38365702656 SUCCESS** passed **2,755 PostgreSQL tests**
and all configured mandatory checks. Accepted ADR 0016 technical semantics are unchanged.
See the [formal implementation acceptance and completion rule](exec-plans/active/PHASE_2_COMMERCIAL_CORE.md#acc-int-1-independent-corrective-approval-and-formal-implementation-acceptance--2026-10-13).
This same docs-only acceptance commit becomes the canonical freeze only after its own exact-head
branch CI, unchanged-main/ancestry verification, direct fast-forward normal push and separate
exact-head main CI succeed. Earlier local-remediation/pending wording is historical.
At that historical acceptance checkpoint, **Phase 2 was NOT COMPLETE; final completion audit
was NOT YET PERFORMED. Phase 3 was NOT AUTHORIZED.** The current final audit/closure is above.
Production readiness is not claimed; SaaS activation and production deployment remain unauthorized.
This is the accepted contract for the final currently scoped Accounting composition gate before
a later Phase 2 completion review, not runtime or Phase 2 exit approval. Other optional integrations
remain separately governed; SaaS activation and production deployment are not authorized.
No exact ACC-INT-0 checkpoint tag name is specified: **NO TAG CREATED**.

Accepted ownership contract: **Option A — separate horizontal modules**, selected by the owner.
[ADR 0011](decisions/0011-modular-billing-payments-accounting-boundary.md) is **Accepted — Gate BILL-0**
as of 2026-10-07. Independent audit FINAL PASS and hosted Phase 0 checks #91 SUCCESS
([run 37579298801](https://github.com/sahinkhan/djangobusinessos/actions/runs/37579298801))
cover exact contract candidate `24d73be43cc09ef66f4405453a210d8f07fcca7f`.
BILL-0 OPTION A CONTRACT CANONICALLY CLOSED at `b9dd8b185a301dca5b76ec7b6604c42805021174`,
checkpoint `billing-option-a-contract-v1`; main CI #93 SUCCESS (run `37581371586`).
Separately authorized BILL-1 implementation `6f1b5f719fe0848e37774b3247a7bd4300a006a6` on
`bill1-billing-invoicing` is **CANONICALLY CLOSED**, 2026-10-07.
Independent implementation correctness audit passed; preservation re-audit under the clarified
authoritative-ref policy returned **FINAL PASS — BILL-1 APPROVED FOR HOSTED CI** after the initial
procedural capture-ref block. The candidate tree/content remained unchanged. Hosted **Phase 0
checks #95 — SUCCESS** ([run 37639810038](https://github.com/sahinkhan/djangobusinessos/actions/runs/37639810038))
tested that exact SHA: **873 PostgreSQL tests passed**, fresh migrations and all mandatory checks
passed. Formal acceptance checkpoint `409e45eaa32fae1cf9c77042a762e57026d0349f`
was adopted by normal fast-forward and passed exact-head main
**CI #97 — SUCCESS** ([run 37645584246](https://github.com/sahinkhan/djangobusinessos/actions/runs/37645584246)):
873 PostgreSQL tests and fresh migrations/all mandatory checks. Canonical `main` and checkpoint
`billing-invoicing-v1` are at that accepted SHA. Earlier candidate/acceptance chronology is retained.

**Gate PAY-0 — standalone Payments contract: FORMALLY ACCEPTED**, 2026-10-07, on
`pay0-payments-contract`, from canonical `409e45eaa32fae1cf9c77042a762e57026d0349f`.
[ADR 0013](decisions/0013-standalone-payments-contract.md) is **Accepted — Gate PAY-0**.
Accepted candidate `9ffb5eae09da680354776872a601bedd58163ab1` has independent
**FINAL PASS — PAY-0 CONTRACT APPROVED**, readiness **A — precise enough for PAY-1 implementation**,
and exact-head hosted **Phase 0 checks #99 — SUCCESS**, run ID `37656399267`
([run evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/37656399267)):
**873 PostgreSQL tests**, fresh migrations and all mandatory checks passed.
Formal acceptance and canonical adoption are **COMPLETE** at
`d12f3e8c3a955dd90f1e03f35a30fde789441764`, checkpoint `payments-contract-v1`.
Exact-head main CI #101 / `37662202308` succeeded with 873 PostgreSQL tests.
It specifies PAY-1 as PaymentMethod and immutable incoming
Payment/Receipt only. PaymentAllocation remains Payments-owned but deferred to a separately
approved optional integration, as are applied/unapplied/outstanding amounts, settlement/refunds
and Accounting effects. At the historical formal-acceptance checkpoint, separately authorized
PAY-1 implementation on `pay1-payments` was
**FORMALLY ACCEPTED FOR CANONICAL ADOPTION**, 2026-10-11, at implementation
`86e15f9f0aea29a07694c251d511e4b60fc6d2ad`. Independent audit returned
**FINAL PASS — PAY-1 APPROVED FOR HOSTED CI**. Hosted implementation **Phase 0 checks #103 — SUCCESS**,
run ID `38076354718`
([run evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38076354718)),
checked out that exact SHA and passed 1,009 PostgreSQL tests, fresh migrations and all mandatory
checks. The detailed independent evidence is recorded in ADR 0013, separately from historical
implementation verification. Formal acceptance is **COMPLETE**; canonical adoption is **PENDING**.
The documentation-only acceptance commit requires its own exact-head hosted CI. Canonical `main`
remains `d12f3e8c3a955dd90f1e03f35a30fde789441764`; PAY-1 is not canonically closed or tagged.
At that historical acceptance stage PAY-INT-1 and ACC-1 were **NOT STARTED**; integrations and
actual SaaS activation were unauthorized. Current Accounting closure is recorded below.
This is not production approval.

**Current PAY-1 status: PAY-1 STANDALONE PAYMENTS — CANONICALLY CLOSED**, 2026-10-11.
The preceding adoption-pending statements describe the formal-acceptance stage, not current state.
Documentation-only acceptance `9ac3f0944fff65f013efd9c3a3e9b841022ce87f` passed acceptance
CI #104 / `38077428416`, was adopted into canonical `main` by normal fast-forward, and passed
exact-head main **Phase 0 checks #105 — SUCCESS**, run ID `38078381136`
([run evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38078381136)):
**1,009 PostgreSQL tests**, fresh migrations and all mandatory checks passed.
Annotated checkpoint `payments-v1` has tag object `05dcb375d0b05ad6ee9f819faa2c4e57dbfd3a34`
and peels to that accepted canonical SHA. No implementation changed during acceptance/adoption.
Earlier implementation, independent audit and candidate/acceptance evidence remain preserved.

**Gate ACC-0 — Standalone Accounting & Finance Contract: FORMALLY ACCEPTED**, 2026-10-11, on
`acc0-accounting-contract`, from canonical `9ac3f0944fff65f013efd9c3a3e9b841022ce87f`.
[ADR 0014](decisions/0014-standalone-accounting-finance-contract.md) is **Accepted — Gate ACC-0**:
Account, Journal, DRAFT -> POSTED JournalEntry/lines, exact base-currency Decimal(38,8), frozen
precision, balanced immutable postings, derived GL/TB, eight RBAC permissions and seven audit
actions. Dependencies are exactly Party/organization/reference/access; no Billing/Payments or
other commercial/vertical dependency. Same-entry post retry is safe; a generic external-header
idempotency key is not an ACC-1 field. Complete external-source posting idempotency remains a
separately approved integration requirement. Older Accounting notes remain historical evidence.

Original candidate `c9f676349a72c585d16a6d3a467cdd676ee2db1d` passed CI #107 / `38109947735`
with 1,009 PostgreSQL tests, then received independent **REVISE** for F1/F2, two P2s concerning
text/identity bounds and position range/exhaustion. That history is preserved. Accepted remediated
contract head `217b7a8f39b628571f616034a7d9d02b436ec03d` passed exact-head **Phase 0 checks #108 —
SUCCESS**, run ID `38112122913`
([evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38112122913)), with 1,009
PostgreSQL tests, fresh migrations and all mandatory checks. The owner-supplied independent
corrective verdict is **FINAL PASS — ACC-0 CONTRACT APPROVED FOR FORMAL ACCEPTANCE**, readiness
**A**; F1/F2 resolved, no new P0/P1/P2/P3. This is contract acceptance, not ACC-1 runtime evidence.

At the historical ACC-0 acceptance stage, formal acceptance was **COMPLETE** and canonical
adoption was **PENDING**; that documentation-only commit required its own exact-head hosted CI.
At that stage `main` remained `9ac3f0944fff65f013efd9c3a3e9b841022ce87f` and
`accounting-contract-v1` had not been created. This chronology is retained.

**Historical ACC-1 implementation/remediation checkpoint — 2026-10-11:** ACC-0 was canonically adopted at
`d5030e0e807334fdc358a1aa3affce704ef4a0f0`. The existing annotated `accounting-contract-v1`
tag object `7369a26d526e10e9a128b44cf79efca9cf353e89` peels to that baseline. Separately
authorized standalone Accounting was implemented locally on `acc1-accounting`. Original candidate
`8eaa084aee58cc7c09e6ce74fe663b1f47c7d9f3` received **REVISE — ACC-1 IMPLEMENTATION REQUIRES
REMEDIATION**, readiness **C**, with one blocking **ACC1-R1 — P2** report-retrieval finding and
no reported P0/P1. At that checkpoint narrow local remediation awaited independent corrective audit.
Account/Journal, service-only draft editing, immutable balanced posted
JournalEntry/lines, eight permissions, seven atomic audit actions, and derived GL/TB are included.
Original implementation-run verification: **1,282 PostgreSQL tests passed** (Accounting 273, including 56 real-lock
concurrency cases); **1,084 SQLite tests passed, 198 expected skips**. See the
[ACC-1 verification record](exec-plans/active/PHASE_2_COMMERCIAL_CORE.md#acc-1-local-implementation-verification--2026-10-11).
See the [ACC1-R1 remediation record](exec-plans/active/PHASE_2_COMMERCIAL_CORE.md#acc1-r1-report-retrieval-remediation--2026-10-11)
for reproduced failures, SQL-bounded retrieval and subsequent verification. These are
implementation-run records, not independent corrective approval or hosted candidate CI.
Remediation verification: **1,313 PostgreSQL tests passed** (Accounting **304**, including
**56** concurrency cases), **31** focused new report cases, **1,114 SQLite tests passed / 199
expected skips**, and **222** database architecture guards. Fresh bootstrap, quality/frontend
checks and real-browser report verification at 390/768/1280px passed.
At that historical checkpoint `main` remained at the baseline; no ACC-1 publication, acceptance,
adoption or `accounting-v1` tag was authorized. Subsequent closure is recorded below, without
rewriting the original audit or implementation-run evidence.

**Current ACC-1 status: ACC-1 STANDALONE ACCOUNTING — CANONICALLY CLOSED**, 2026-10-11.
Canonical freeze: `00e18a75e27bfe962ea290ab01f0cb0520f4427e`.
ACC1-R1 substantive report-retrieval finding is **RESOLVED** at
`0aa759cbbc881ce8c3488f2a98c2095e8c9d2797`; ACC1-R2 P3 changed-file formatting is **RESOLVED**
at the frozen head. Independent final reconciliation returned
**PASS — ACC-1 IMPLEMENTATION APPROVED FOR PUBLICATION**. Candidate push
**Phase 0 checks #112 / 38127289623 — SUCCESS**
([candidate evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38127289623))
tested the exact frozen SHA. Normal fast-forward adoption passed exact-head main
**Phase 0 checks #114 / 38127960676 — SUCCESS**
([main evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38127960676)):
**1,313 PostgreSQL tests**, fresh migrations and all mandatory checks passed. PR #1 was closed
**without merging**; it was not the adoption route. No `accounting-v1` tag exists or is claimed.
These are publication/closure results, not new runtime tests performed by PAY-INT-0.
Standalone closure is not production Accounting readiness or full Phase 2 completion.

**Historical acceptance-stage milestone: PAY-INT-1 — FORMALLY ACCEPTED FOR CANONICAL ADOPTION,
2026-10-12. Formal acceptance: COMPLETE. Canonical adoption: PENDING at this acceptance checkpoint.**

Separately authorized implementation starts from canonical PAY-INT-0 freeze
`9ee4e0bd77350ddeef1e928e2a73b676b4cbb1ee`, on `payint1-billing-payments-allocation`.
Acceptance CI #116 / `38134694017` and main CI #117 / `38135373053` succeeded against that
same exact freeze, with 1,313 PostgreSQL tests each. Those hosted results close PAY-INT-0;
they are **not** PAY-INT-1 hosted implementation evidence. Main is unchanged.

The explicit opt-in Payments-owned `payments_billing` app depends on Billing and Payments,
without adding reverse owner dependencies. It implements immutable keyed partial allocations,
compound RBAC, Company -> Payment -> Invoice locking, atomic creation/audit, exact owner-owned
financial bases and bounded complete-evidence summaries/history. HTTP additionally locks and
checks all three module registrations; installed Python services do not use UI enablement.
Only new optional-app migrations are added. No mutable balances, Accounting automation, reversal,
bank reconciliation, SaaS activation or deployment is implemented. Existing standalone contracts
and ADR 0015's technical semantics remain intact. Actual local verification and limitations are
recorded in the [PAY-INT-1 execution record](exec-plans/active/PHASE_2_COMMERCIAL_CORE.md#pay-int-1-local-implementation-and-verification--2026-10-11).
The supplied independent audit of original candidate
`4b8a072da4426a48988d4605641bf1fc846c06ee` returned **REVISE / Readiness C**:
PAYINT1-R1 P1 (RLS-hidden evidence), PAYINT1-R2 P1 (unvalidated FK/orphan history),
PAYINT1-R3 P2 (requested-parent retry ordering), PAYINT1-R4 P2 (intrinsically impossible retry).
At the historical corrective checkpoint, the correction was local only; developer tests did not
close those findings.
Its [corrective evidence](exec-plans/active/PHASE_2_COMMERCIAL_CORE.md#pay-int-1-local-corrective-remediation--2026-10-11)
records selected-alias catalog checks, raw orphan probes and stored-parent intrinsic retry
validation without changing accepted ADR 0015 or migrations. The owner-supplied independent
corrective verdict for `bef50fe8b20f97aaeefb8c610a46d412e9a05402` is **FINAL PASS — PAY-INT-1
CORRECTIVE IMPLEMENTATION APPROVED FOR HOSTED CI**, readiness **A**. PAYINT1-R1 P1, R2 P1,
R3 P2 and R4 P2 are **RESOLVED**, with no new actionable candidate-owned P0–P3 finding.
Normal publication preserved that exact candidate. **Phase 0 checks #118 / 38162359131 — SUCCESS**
([implementation CI](https://github.com/sahinkhan/djangobusinessos/actions/runs/38162359131))
checked out the exact corrective SHA and passed **1,613 PostgreSQL tests**, fresh migrations,
Ruff, Django checks, no migration drift, npm/Tailwind and generated CSS reproducibility.
The [formal acceptance record](exec-plans/active/PHASE_2_COMMERCIAL_CORE.md#pay-int-1-independent-corrective-approval-and-formal-acceptance--2026-10-12)
separates supplied independent evidence, historical developer runs and hosted CI. This docs-only
acceptance commit must pass its own exact-head branch CI before normal fast-forward adoption;
separate exact-head main CI must then succeed. Only then is the same acceptance commit the
**PAY-INT-1 canonical freeze / CANONICALLY CLOSED** checkpoint. Pending wording remains historical
acceptance-stage evidence; no future run or result is claimed here. **Production readiness is
NOT CLAIMED. Accounting automation is NOT STARTED / NOT AUTHORIZED. SaaS activation and production
deployment are NOT AUTHORIZED.** No exact PAY-INT-1 tag is specified; no tag or release is created.

**Historical acceptance checkpoint: PAY-INT-0 — Billing/Payments Allocation Integration Contract.**
[ADR 0015](decisions/0015-billing-payments-allocation-integration-contract.md) is
**Accepted — Gate PAY-INT-0**. The original proposal remains intact at audited
`9d4fa5d3b7a12d4eb0ee2046d6e4ff306957e228`, from the ACC-1 canonical freeze above.
Owner-supplied independent verdict: **FINAL PASS — PAY-INT-0 CONTRACT APPROVED FOR FORMAL
ACCEPTANCE**, readiness **A**, no actionable candidate-owned P0–P3. Normal candidate publication
passed exact-head **Phase 0 checks #115 / 38133793295 — SUCCESS**
([candidate evidence](https://github.com/sahinkhan/djangobusinessos/actions/runs/38133793295)):
**1,313 PostgreSQL tests**, fresh migrations and all mandatory checks passed. This is hosted
existing-runtime regression evidence, not executed allocation implementation tests.

**Formal acceptance: COMPLETE. Canonical adoption: PENDING at this acceptance checkpoint.**
The acceptance metadata commit must pass its own exact-head branch CI before normal fast-forward
adoption, followed by separate exact-head main CI. Once that authorized sequence succeeds, the
same acceptance commit is the **PAY-INT-0 canonical freeze / CANONICALLY CLOSED** checkpoint;
the pending statement remains historical acceptance-stage evidence. See ADR 0015's
[completion rule](decisions/0015-billing-payments-allocation-integration-contract.md#formal-acceptance-and-canonical-completion-rule--2026-10-11).
No future CI result is claimed here. The reviewed Payments-owned optional component, immutable
partial allocations, explicit RBAC/audit, same-alias locking/retry and complete-evidence derived
balances are unchanged. **PAY-INT-1: NOT STARTED / NOT AUTHORIZED**.
Accounting integrations, other integrations, actual SaaS activation and production deployment
remain **NOT STARTED / NOT AUTHORIZED**. No runtime work or full Phase 2 completion is authorized.
This publication/adoption flow uses no PR or force push. No exact PAY-INT-0 tag is specified;
no tag or release is created. The earlier local-only proposal/preparation stage remains historical.

PAY-1 acceptance preserves PaymentMethod and immutable incoming Payment/Receipt only, their
exact amount/snapshot/authorization/idempotency and omitted-date midnight-retry semantics.
At that standalone PAY-1 checkpoint PaymentAllocation remained absent; no Billing dependency/effect,
Accounting or Inventory effect was introduced. Known PAY-1 maintenance follow-ups remain inherited ADR status wording (only
necessary acceptance lines normalized), favicon 404, eight npm advisories (two moderate, six high),
Actions runtime warnings and stale Browserslist data; no runtime maintenance is authorized here.

Inherited nonblocking PAY-0 P3: checkpoint-era ADR 0011/Billing authorization wording in ADR 0006
and `CORE_FOUNDATION_V1_RESTRUCTURE.md` remains a documentation-maintenance follow-up. Those files
are unchanged by this acceptance and the follow-up does not change PAY-0 semantics.

Known nonblocking BILL-1 P3: the "Issued" badge may wrap in one extreme boundary-length list row
at 1280px; retain it for separately authorized UI maintenance. Existing eight npm advisories
(two moderate, six high) and GitHub Actions runtime deprecation warnings remain separate
security-maintenance follow-ups. No accepted ownership or implementation is changed by acceptance.

### Current gate summary

| Gate | Ownership / accepted implementation | Standalone exclusions / remaining boundaries |
| --- | --- | --- |
| BILL-1 — Billing & Invoicing | Invoice/InvoiceLine, generic lines, snapshots, numbering, DRAFT -> ISSUED, derived original totals | No payment-aware outstanding; no void/credit, Sales automation or journals |
| PAY-1 — Payments (canonically closed; payments-v1) | PaymentMethod, immutable incoming Payment/Receipt, snapshots, numbering and receipt idempotency | Allocations/applied/unapplied/outstanding supplied only by optional PAY-INT-1; journals only by optional ACC-INT-1; refunds/reversals/bank settlement remain deferred |
| ACC-0 / ACC-1 canonically closed | Account, Journal, balanced immutable base-currency postings, derived GL/trial balance; accepted ADR 0014; freeze `00e18a75...` | Historical REVISE retained; ACC1-R1/R2 resolved; external-source idempotency, Billing/Payments automation and other finance capabilities separately governed |
| PAY-INT-0 canonically closed at `9ee4e0bd...` | Payments retains allocation ownership; Billing retains invoice facts; accepted ADR 0015 freezes opt-in composition | Historical acceptance-stage pending wording retained above; allocation implementation is separately governed; no Accounting automation |
| PAY-INT-1 canonically closed at `a1079985...` | Opt-in `payments_billing`; immutable allocations, complete-evidence profile and intrinsic stored-parent retries; original REVISE / C preserved; corrective FINAL PASS / A; R1-R4 RESOLVED; CI #118/#119/#120 SUCCESS | No Accounting effect, reversal/refund, FX, bank settlement or other automatic posting; earlier acceptance-stage pending chronology retained |
| ACC-INT-0 / ACC-INT-1 canonically closed | ADR 0016; ACC-INT-1 freeze `669936df432ec1bb12792ed8d31741fbb1b1287a`; ACCINT1-AUD-1 RESOLVED; main CI #130 attempt 2 SUCCESS / 2,755 PostgreSQL tests; original REVISE and attempt-1 deadlock preserved | Invoice AR/Revenue and Allocation Cash/AR remain optional public-service composition, not standalone hard dependencies |
| Phase 2 combined corrective series / formal closure | Candidate `4a2a7ec...`; supplied independent FINAL PASS / A / 13 of 13 PASS; candidate CI #131 SUCCESS / 3,015 PostgreSQL tests; all six findings RESOLVED including docs-only PH2-FINAL-DOC-1 | FORMAL CLOSURE COMPLETE FOR CANONICAL ADOPTION; adoption PENDING, requiring closure branch CI and separately authorized fast-forward/main CI; Phase 3 NOT AUTHORIZED |

This is implementation sequence, not a hard-dependency chain. Billing requires Party plus Core;
generic Payments and Accounting work without Billing. Settlement-adjusted outstanding in the accepted
optional integration is a derived composition of invoice state and valid Payments allocations; absence of integration must
not display an invoice as fully unpaid. No duplicate mutable financial balance is introduced.

Historical audit/adoption records below are retained as evidence of their respective checkpoints.
The future delivery list and accepted ADRs 0011/0013 govern the Payments contract; accepted ADR 0014
is the detailed Accounting contract, not implementation authorization. These contracts do not
reopen accepted Sales, Procurement, Inventory, UI or Core behavior.

Status: Gate 4A Sales is accepted, adopted, and closed. Gate 4B Procurement implementation
candidate `395da2ad874fc2efb72219da71316b9a6d8f73bf` replays the historically accepted standalone
contract onto Core Foundation v1. Candidate head `12d1a1f90689979048cdf3b4f59836b026dd153f`
passed hosted CI #53 but completion review BLOCKED on missing authorization-revocation and
confirmation-versus-mutation PostgreSQL coverage. Narrow test remediation
`b8c49e1fb5b62f9169038b59e35b6d4e7adfb8e0` closes those gaps without production changes and is
published at final candidate `1eabb0e9806342cc2ba71f1468eb18af120cddb9`. Hosted CI #54 passed
with 342 PostgreSQL tests, and independent re-audit returned FINAL PASS. Documentation-only
acceptance commit `e4ea1791f0b2c7d1209ea574de3689970e1fc398` passed branch CI #55, was
adopted into canonical `main` by normal fast-forward, and passed exact-head main CI #56. Gate 4B
is accepted, adopted, and closed.

Gate 4C Inventory is now implemented only as an isolated canonical adoption candidate on
`gate4c-inventory-adoption`, reconstructed from canonical `main` at
`8d5a41f83c3f796fa31e7d3f8598c54f7dfc5b95`. Historical `phase2-inventory` at
`f45afdfea33d3fd03d469e6a0cd63d0e5358f38c` remains remediation/reference evidence only and was
not merged or cherry-picked. The candidate implements the posted movement ledger, Foundation v1
RBAC/audit/company-lock contracts, derived balances, and HTTP-only module gating. Initial
candidate head `01037fc7f87e546382931a081750bf367bb78232` passed hosted CI #59 with 406
PostgreSQL tests, but independent audit BLOCKED acceptance on mixed-UoM balance safety, HTTP
mutation-form RBAC, stale-company HTTP evidence, and a missing ProductVariant stock-field
assertion. Narrow remediation `78ba3ae92366da9b2136b260cc9a380e22587e08` closed those findings at
final candidate `8b52270959a2f6623de225e08dc081aea8d1630b`. Hosted CI #60 passed that exact
head with 410 PostgreSQL tests, and independent re-audit returned FINAL PASS. Documentation-only
acceptance checkpoint `eb2f52afc53fd8c36249bc6a1e61c15dba9effe8` passed branch CI #61, was
adopted into canonical `main` by normal fast-forward, and passed exact-head main
[CI #62](https://github.com/sahinkhan/djangobusinessos/actions/runs/34931069346). Gate 4C is
accepted, adopted, and closed. Billing, Accounting, integrations, and
Procurement/Sales-to-Inventory automation remain unauthorized; full Phase 2 is not complete and
production deployment is not approved.

The closure at `60f879a036e0fd21eada1375fa695f32adc7dc91` remains historical administrative
evidence. A post-closure correctness audit subsequently returned REVISE for four narrow
Inventory findings covering company-local datetime/DST handling, same-line combined history
filters, snapshot/UoM update auditing, and initial balance/history page RBAC. Corrective
implementation `343c413bff7f7e520a5a031f92f461a8058db3cc` was published through candidate
`23a12ae544be2e611ac3fd5bfa90d62299599648`. Independent corrective re-audit returned REVISE for
one residual timestamp-precision issue: an unchanged minute-granular edit could truncate the
trusted persisted seconds and microseconds. Narrow remediation
`b33e6faaf931777575292a42af775a1c11986984` preserves the original aware instant when the submitted
company-local minute is unchanged, while a changed minute remains normalized to the submitted
minute. Candidate head `d7fc63c2af77e210cdbae8a72837c1497200f251` passed CI #68, but independent
re-audit returned REVISE because a trusted persisted DST fall-back-fold minute was rejected during
generic parsing before preservation. Final narrow remediation
`145c9d51a3507aa1df8d6548659e16e506940d1e` performs the trusted raw-minute match before generic
DST conversion while retaining ambiguity/gap rejection for other input. It is isolated on
`gate4c-inventory-postclosure-remediation` at final corrective candidate
`09794e9293da78117e5873ebbff9f4b98fa5e1b7`. CI #69 passed that exact head with 422 PostgreSQL
tests, and independent final corrective re-audit returned FINAL PASS. The correction is formally
accepted at checkpoint `35663e4f6b4112903838e0a8069f47885c83f7ce`, adopted into canonical `main`
by normal fast-forward, and passed exact-head main CI #71
([run 34957834165](https://github.com/sahinkhan/djangobusinessos/actions/runs/34957834165)). The Gate
4C post-closure corrective audit cycle is FINAL PASS, formally accepted, adopted, and closed; the
original historical closure remains preserved.

An independent Sales post-closure audit returned REVISE for four narrow findings: mutable
in-memory parent substitution could bypass historical line deletion protection; SKU/name-only
snapshot refreshes could persist without `sales.order.updated` evidence; long customer names and
maximum supported totals could overflow the order document; and non-finite Decimal inputs could
escape canonical validation. Sales-local remediation is implemented at
`f9092cebe2f27504c0f3dfc772524645e25c1f91` on
`gate4a-sales-postclosure-remediation`. Final corrective candidate
`b34a98a1f47c7d0c526fa4dbd60207d5123f9fe3` passed exact-head hosted CI
[#74](https://github.com/sahinkhan/djangobusinessos/actions/runs/34961977826) with 437 PostgreSQL
tests and all required checks, and independent corrective re-audit returned FINAL PASS. The
historical Gate 4A closure remains preserved. Documentation-only corrective acceptance checkpoint
`5ccada2bdb8f28bbc031e25aae72a88f7f454e09` was adopted into canonical `main` by normal
fast-forward and passed exact-head main
[#76](https://github.com/sahinkhan/djangobusinessos/actions/runs/34966070313). Corrective
acceptance and canonical adoption are complete; this documentation closes the post-closure
corrective cycle. The current frozen Sales foundation scope is canonically complete. Future Sales
extensions remain open and separately governed. Billing, Accounting, and integrations remain
unauthorized.

An independent Procurement post-closure audit subsequently returned REVISE for five narrow
findings: mutable in-memory parent substitution could bypass historical line deletion protection;
noncanonical or duplicate receipt-field UUID representations could be discarded before partial
HTTP processing; SKU/name-only snapshot refreshes could persist without
`procurement.order.updated` evidence; supported boundary values could overflow Procurement
documents; and non-finite line Decimals could escape canonical validation. Procurement-local
remediation is implemented at `1ccaf0bc74816b11035cb33f24e172ff8f902329` on
`gate4b-procurement-postclosure-remediation`. The historical Gate 4B closure remains preserved.
This corrective candidate is AWAITING INDEPENDENT PROCUREMENT CORRECTIVE RE-AUDIT and is not
accepted, adopted, merged, or re-closed. Billing, Accounting, integrations, and deployment remain
unauthorized.

The first Procurement corrective re-audit returned REVISE for one residual P3: invalid numeric
strings on `PurchaseOrderLine.quantity` or `unit_cost` could escape model validation as an
uncontrolled `TypeError`. Residual remediation `c34daec0d3ad876612c15536f8c94148f7f4664c`
uses Django DecimalField conversion semantics before finite/business comparisons and adds public
service plus direct-model regressions. Final candidate
`ad03000deeae72a1703f6935dd9d4cde46ede5cc` passed exact-head hosted CI
[#80](https://github.com/sahinkhan/djangobusinessos/actions/runs/34987503229). The second independent
corrective re-audit returned FINAL PASS after 493 PostgreSQL tests, 115 Procurement-local tests,
27 real-lock concurrency tests, focused adversarial probes, SQLite verification, and desktop/mobile
boundary QA. The corrective remediation is ACCEPTED FOR CONTROLLED ADOPTION; historical findings
remain recorded. Documentation-only acceptance checkpoint
`49052c0efd3a63ec55c409e0d38082425ce116c3` passed exact-head branch
[#81](https://github.com/sahinkhan/djangobusinessos/actions/runs/34992015192), was adopted into
canonical `main` by normal fast-forward, and passed exact-head main
[#82](https://github.com/sahinkhan/djangobusinessos/actions/runs/34993306285). Corrective
acceptance and canonical adoption are complete; this documentation closes the Procurement
post-closure corrective cycle. The current frozen Procurement foundation scope is canonically
complete. Future Procurement extensions remain open and separately governed. Billing,
Accounting, integrations, and deployment remain unauthorized.

Gate 4C original implementation candidate: `e1e94307bd96b2834f677eb02b91d27b87843f21`.

Historical Gate 4A record: independent audit BLOCKED the initial Sales adoption implementation
`28c8028950be1997b4f3d0816b1ec04764222068` at audit head
`fc609bcd81916c13921c2d1cc7b6a59eda1c1e19`. Remediation at
`d62c34e36f0a8b11f59bfdb058143e27f5231c5d` closed the findings, and independent re-audit gave
FINAL PASS to candidate `23338f1cfed11d21d4fa8fd7e92f8de120450977`; exact-head hosted CI #48
also passed. Documentation-only acceptance commit `e0c848f34da0bce9b9c6e010a396026ac5889cf4`
was adopted into canonical `main` by normal fast-forward, and exact-head main CI #50 passed. Gate
4A Sales is accepted, adopted, and closed. Gate 4B Procurement is also accepted, adopted, and
closed. Inventory adoption, Billing, Accounting, integrations, and any Procurement-to-Inventory
write remain unauthorized. Preserved historical branches remain unchanged.

Standalone modules are parallelizable after the Phase 1 contract freeze. Optional cross-module integrations are implemented only after the standalone module contracts pass review.

Deliver:

- Sales
- Procurement
- Inventory
- Gate BILL-1: standalone Billing & Invoicing
- Gate PAY-1: standalone Payments, with invoice allocation separately governed
- Gate ACC-1: independent Accounting & Finance Core

Golden flows:

- Customer -> Sales Order -> Confirm
- Supplier -> Purchase Order -> Receive
- Stock Receive / Issue / Transfer
- Generic Invoice -> Issue (Billing); standalone payment receipts (Payments)
- Invoice allocation/outstanding only through a separately approved Payments/Billing integration
- Journal Entry + Trial Balance basics

Concrete transactional item references use Catalog ProductVariant where an item/SKU is required.

Accounting and Inventory require transactional tests and duplicate-posting protection where relevant.

---

## Phase 3 — People and Digital Commerce

Status: **PHASE 3 UMBRELLA CONTRACT FORMALLY ACCEPTED FOR CANONICAL ADOPTION**.
ADR 0017 is **Accepted — Phase 3 Umbrella Contract**. Canonical adoption PENDING at this acceptance
checkpoint. Phase 2 remains CANONICALLY CLOSED; implementation NOT AUTHORIZED.

Review [accepted ADR 0017](decisions/0017-phase3-people-digital-commerce-boundaries.md) and the
[Phase 3 execution plan](exec-plans/active/PHASE_3_PEOPLE_DIGITAL_COMMERCE.md). Original proposal
`15e68828300f40c84165c86317217024f6b9d66d` received the supplied independent structural audit
FINAL PASS / Readiness A for owner-decision resolution, with zero candidate-owned P0–P3 findings.
On 2026-10-14 the owner explicitly resolved OD-1–OD-12 at
`17339a0ae4fdfdb9cf69df74afb98b04c07c9136`. The supplied fresh final verdict against that resolution
is **FINAL PASS — PHASE 3 UMBRELLA CONTRACT APPROVED FOR FORMAL ACCEPTANCE**, Readiness A,
zero candidate-owned P0–P3. Owner authorization now records formal acceptance and permits normal
publication/CI followed on success by direct fast-forward/main CI. Original chronology remains.

Owner-approved initial product scope:

- Phase 3A: stable Company/PERSON Employee, company-wide Department, optional current Employee
  Branch, multiple completed attendance sessions with immutable revisions, full-calendar-day Leave.
  Optional User association grants no authority; bounded HR PERSON projection retains Party ownership
  and existing company-wide Party visibility. Self-service, rehire episodes and Payroll are deferred.
- Phase 3B minimum: authenticated staff-assisted Cart/Checkout -> one atomic DRAFT SalesOrder and
  all lines through a new public Sales owner service; explicit authorized staff-entered price.
  Catalog + Sales composition retains Party/Core boundaries; Sales confirmation stays separate.
- Deferred optional Commerce scope: Inventory display/projection/warehouse selection, Billing,
  Payments and Accounting effects, public/guest/customer storefront admission. None is required for
  initial Phase 3B completion. Future compositions require their own approved owner contracts.

The owner explicitly clarifies the previous roadmap wording: Billing is not mandatory for minimum
Phase 3B. No duplicate product/variant/order/stock/invoice/payment/ledger authority. Thirteen bounded
exit criteria require both HR and minimum Ecommerce implementations accepted. HR-0 and ECOM-0 must
freeze detailed technical contracts after final umbrella acceptance; HR-0/ECOM-0/HR-1/ECOM-1 are
NOT STARTED. This one acceptance commit becomes the canonical umbrella freeze only after successful
branch push CI, unchanged-main/three-commit ancestry verification, normal direct fast-forward push,
separate successful main push CI and local main synchronization; see the plan's completion rule.
Canonical acceptance does not complete Phase 3 or authorize runtime. HR-0/ECOM-0 then become
eligible for separate authorization; HR-1/ECOM-1 and Phase 4 remain unauthorized. No PR or tag.

---

## Phase 4 — Marketing Vertical MVPs

Deliver thin, polished, demo-ready verticals with one complete workflow each.

### School

Student -> Enrollment -> Attendance -> Fee -> Payment

### Hospital/Clinic

Patient -> Appointment -> Visit -> Bill -> Payment

### Hotel

Guest -> Room/Reservation -> Check-in -> Bill -> Check-out

These are marketing/pilot MVPs, not claims of full clinical/school/hospitality compliance.

---

## Phase 5 — Product Hardening

Driven by pilot clients.

Deliver as demanded:

- stronger authorization/data scope
- audit logs
- documents/attachments
- notifications
- imports/exports
- PDF/document outputs
- API surface
- backup/restore
- operational monitoring
- security hardening
- performance baselines

Exit gate: production client deployments can be upgraded/recovered safely.

---

## Phase 6 — Shared Platform Services

Extract only from repeated real requirements:

- Party/Geography/UoM/Reference Data maturity
- workflow/approval engine
- rules engine
- resource/scheduling
- documents/collaboration/notifications
- search/reporting/import/export platform
- integration platform

These are extracted platform capabilities, not speculative rewrites.

---

## Phase 7 — Enterprise Horizontal Suite

Expand/harden:

- Catalog/Pricing/Tax
- CRM/Sales
- Procurement
- Inventory/Warehouse/Logistics
- Billing & Invoicing
- Payments
- Accounting & Finance
- Assets/Expenses/Treasury
- HR/Payroll
- Project/Helpdesk/Field Service
- Manufacturing/Maintenance/Quality
- POS
- Ecommerce

---

## Phase 8 — Industry Verticals

Build verticals primarily by composing horizontal/shared capabilities:

- Healthcare/Hospital/Clinic/Pharmacy
- Education/School
- Salon/Spa/Gym
- Restaurant
- Hotel/Hospitality
- Garments/Apparel
- Construction/Real Estate
- Fleet/Logistics
- Microfinance/Financial Services
- Legal
- Travel/Air Ticketing

---

## Phase 9 — Internationalization and Localization

Deliver localization packs rather than contaminating generic modules with country-specific rules.

Potential structure:

```text
businessos/localizations/
  bd/
  us/
  ca/
  uk/
  ae/
```

Localization may include taxes, payroll rules, fiscal reports, chart templates, document formats and legal fields.

---

## Phase 10 — Metadata / Studio / Dynamic UI

Only after stable business patterns are known:

- metadata definitions
- dynamic forms/lists
- configurable dashboards
- Studio customization
- visual workflow/rule designers where justified

React may be introduced selectively for complex designers.

---

## Phase 11 — Developer Platform and Marketplace

Deliver:

- stable extension/module SDK
- compatibility contracts
- package signing/trust policy
- certification process
- partner/developer documentation
- marketplace

Third-party code trust/isolation must be treated as a security architecture problem, not merely a packaging problem.

---

## Phase 12 — Enterprise Operations / Cloud

Deliver when customer scale justifies it:

- self-hosted enterprise operations tooling
- BusinessOS Cloud control plane
- deployment orchestration
- fleet/version visibility
- upgrade waves
- backup/restore automation
- performance certification
- security/compliance maturity
- LTS policy
- compatibility guarantees
- partner ecosystem operations

---

## Optional Runtime Evolution

Django remains the default runtime unless there is measured justification to replace parts of it.

If a custom Python runtime is later justified:

1. keep business/domain services framework-neutral;
2. extract reusable BusinessOS kernel contracts;
3. add custom runtime adapters for new endpoints/modules;
4. allow Django and custom runtime to coexist;
5. migrate selectively;
6. remove Django only if benefits clearly exceed migration/maintenance cost.

Do not schedule a rewrite merely because a custom framework is technically possible.

---

## Permanent rule

**Build capabilities late; reserve boundaries early.**

## Current HR-1 formal acceptance checkpoint — 2026-10-21

This later checkpoint supersedes only the historical HR-1 status statements above; it does not
erase or backdate earlier authorizations, failures or accepted owner decisions.

HR-0 and ADR 0018 remain canonically accepted at
`b36cdba91654e6a583735d67f7f6cf27a835003e`. HR-1 runtime implementation is **FORMALLY ACCEPTED FOR
CANONICAL ADOPTION at this documentation checkpoint**, following the independently approved
corrective implementation and JavaScript CI-coverage delta. The accepted scope is HR Foundation
v1: Employee, Department, Attendance, AttendanceRevision, LeaveType and LeaveRequest, not a Full
Enterprise HR Suite.

Canonical adoption is **PENDING** until this acceptance commit receives successful exact-head
branch CI, is normally fast-forwarded to unchanged canonical main, and receives separate
successful exact-head main CI. Only verified fulfillment of all three gates makes this acceptance
commit the canonical HR-1 freeze; this record does not claim those future results. See the
[acceptance record and completion rule](exec-plans/active/PHASE_3A_HR_FOUNDATION.md#hr-1-formal-implementation-acceptance--2026-10-21)
and [implementation evidence](exec-plans/active/HR_1_IMPLEMENTATION_EVIDENCE.md#formal-acceptance-checkpoint--2026-10-21).

Phase 3 is **NOT COMPLETE**. ECOM-0 remains separately governed and is NOT STARTED BY THIS TASK;
ECOM-1 is NOT STARTED. The final combined Phase 3 audit and closure remain future gates. Payroll,
recruitment, shifts, biometric attendance, SaaS/tenant activation and production deployment are
outside this acceptance; production readiness is NOT CLAIMED. Phase 4 Education/Healthcare and
the unchanged local proposal at `735e1bea13bc58fa71d430163422139d5c0f2363` remain **ON HOLD**;
ADRs 0019–0021 remain PROPOSED. No next milestone is authorized by this checkpoint.
