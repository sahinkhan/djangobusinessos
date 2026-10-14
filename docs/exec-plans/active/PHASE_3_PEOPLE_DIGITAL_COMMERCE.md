# Phase 3 — People and Digital Commerce

Status: **PHASE 3 UMBRELLA CONTRACT FORMALLY ACCEPTED FOR CANONICAL ADOPTION**.
Owner decisions 12/12 RESOLVED; final contract audit PASS / Readiness A; formal acceptance COMPLETE;
canonical adoption PENDING at this acceptance checkpoint. Implementation NOT AUTHORIZED.

Date: 2026-10-14. Gate: PH3-0 formal acceptance/publication/canonical adoption checkpoint.

Canonical base: `0d4a14254889ba1ec06cfb16088009177991d8d8`.
Planning branch: `phase3-people-commerce-contract`.
Umbrella: [ADR 0017](../../decisions/0017-phase3-people-digital-commerce-boundaries.md).

## 1. Authority, evidence and current inventory

This document records twelve explicitly approved owner policies and proposes their remaining
technical contracts. It authorizes no model, migration, manifest, permission, service, UI or runtime
implementation. HR-0, ECOM-0, HR-1 and ECOM-1 are NOT STARTED. The first supplied architecture
audit applies to original proposal `15e68828300f40c84165c86317217024f6b9d66d`; the subsequent final
contract audit passed against resolution `17339a0ae4fdfdb9cf69df74afb98b04c07c9136`.
Section 15 records supplied final evidence, explicit formal acceptance and the conditional canonical
completion rule. This documentation task does not claim to be either independent audit.

Phase 2 is CANONICALLY CLOSED at the base above. Exact-head main push CI #133 / run `38549126483`
passed, including 3,015 PostgreSQL tests (zero failures/skips); the Phase 2 final exit matrix is
13 PASS / 0 FAIL / 0 NOT PROVEN. These are inherited Phase 2 results, not Phase 3 verification.
Earlier blocked audits, corrective history and the NOT PROVEN attribution of the original SQLite
failure remain historical evidence in the [Phase 2 plan](PHASE_2_COMMERCIAL_CORE.md).

### Required architecture and inspected contracts

Read [AGENTS](../../../AGENTS.md), [baseline](../../architecture/BASELINE.md),
[boundaries](../../architecture/MODULE_BOUNDARIES.md),
[dependencies](../../architecture/DEPENDENCY_MAP.md) and [roadmap](../../ROADMAP.md).
ADRs 0001–0009 establish context, hard/optional dependencies, variants, Party, HTTP gating,
standalone commercial lifecycles and Core authorization/audit. ADR 0010 governs Inventory;
0011 Billing ownership, 0012 database execution, 0013 Payments, 0014 Accounting, 0015 allocation,
0016 Accounting outcomes. Their accepted authority is not superseded by this proposal.

All code observations below refer to the exact pinned base, not a speculative API or an external
BusinessOS repository. Paths are repository-relative; named services/selectors were inspected.

| Owner / evidence | Existing reusable contract | Limitation relevant to Phase 3 |
| --- | --- | --- |
| `businessos/modules/party/{models,services,selectors}.py`; ADR 0004 | Company-owned Party(person/organization), ContactMethod, Address; `create_party`, `update_party`, `party_detail`, `active_customers` | No User binding; company-access CRUD, not private HR/customer-portal RBAC; Party type/activity can change |
| `businessos/modules/catalog/{models,services,selectors}.py`; ADR 0003 | Product/Variant, category, attributes, UoM; `active_variants`, `product_detail`, `update_product` | No selling-price source; active selector alone does not require `is_sellable`; mutable product eligibility/UoM |
| `businessos/modules/sales/{models,services,selectors,manifest}.py` | `create_sales_order`, `add_sales_order_line`, `confirm_sales_order`, company list/detail; five order permissions; variant snapshots; Decimal(18,4) quantity/price | No public batch-create or create retry key, no Branch field, no online price offer, no checkout side effects |
| `businessos/modules/inventory/{models,services,selectors}.py`; ADR 0010 | Immutable posted movement facts; `stock_balance`, `balances_for_warehouse`, movement history; mixed-UoM refusal | Balance is not ATP/reservation; scalar balance must not be relabeled with a newly changed Catalog UoM |
| `businessos/modules/billing/{models,services,selectors}.py`; ADR 0011 | Generic Invoice/Line; `create_invoice`, `issue_invoice`, `invoice_total`, `invoice_financial_basis` | No automatic Sales invoice; original total is not outstanding; draft create has no external-key guarantee |
| `businessos/modules/payments/{models,services,selectors}.py`; ADR 0013 | Immutable incoming receipt, method, `record_payment`, `payment_receipt_basis`, keyed retry | Not gateway capture, refund or automatic checkout payment |
| `businessos/modules/payments/integrations/billing/`; ADR 0015 | Explicit Payments-owned optional allocation and validated settlement evidence | Only approved composition derives applied/unapplied/outstanding; no guessed zero-paid value |
| `businessos/modules/accounting/integrations/`; ADR 0016 | Explicit owner-controlled invoice AR/Revenue and allocation Cash/AR outcomes | No implicit Ecommerce or invoice-issue ledger effect; receipt alone is not another AR clearing effect |
| `businessos/core/organization/{models,time}.py` | Company, Branch, Warehouse; protected ownership, IANA timezone; `company_local_date`, `company_local_datetime` | Branch is not a separate tenant; company-time configuration does not freeze past attendance interpretation |
| `businessos/core/access/{policies,services,models}.py` | `validate_business_context`, `require_permission`, `require_final_permission`; Company-first grants and ordered final authority locking | Missing branch in valid context means company-wide access, not branch-only confinement; User link is not authorization |
| `businessos/core/modules/{manifest,services,selectors,decorators}.py` | Deterministic explicit registration, namespace validation, `module_required` | No dynamic installation/resolver; enablement only controls HTTP/navigation |
| `businessos/core/database/{execution,transactions,router}.py` | `database_execution`, `business_atomic`, `business_atomic_context`, call/enter-time alias | No tenant identity/security activation; nested alias switching rejected; no distributed atomicity |

Current module directories are `_example`, Party, Catalog, Sales, Procurement, Inventory, Billing,
Payments and Accounting. Current tracked paths and Python definitions contain no HR, Employee,
Department, Attendance, Leave, Ecommerce, Cart or Checkout implementation. Bounded `git log --all`
inspection of HR/Ecommerce/template paths and employee/attendance/department/checkout/ecommerce
filename patterns found no implementation prototype in locally reachable refs. This is not a claim
about un-fetched/deleted remote history or untracked external backups. No historical code is adopted.

## 2. Tracks, audit chronology and resolved owner decisions

Phase 3A is reusable People/HR foundation. Phase 3B is independently gated staff-assisted Commerce.
Accepted Foundation constraints remain authoritative. The owner resolved all twelve product-policy
choices in the 2026-10-14 resolution instruction. Formal acceptance follows the final audit at
section 15; original policy/audit chronology remains below.

### Preserved proposal and supplied independent audit

Original proposal `15e68828300f40c84165c86317217024f6b9d66d` is one documentation commit above
the canonical Phase 2 base. Its ten D1–D10 recommendations were unresolved at that time. The supplied
fresh independent verdict is **FINAL PASS — PHASE 3 UMBRELLA ARCHITECTURE APPROVED FOR OWNER-DECISION
RESOLUTION**, **Readiness A**, candidate-owned **P0: 0 / P1: 0 / P2: 0 / P3: 0**. That approves
structure for owner resolution; it does not accept the final resolution contract or authorize runtime.

The historical register is reconciled below, rather than rewritten as though policy had always
been settled. OD-5 explicitly supersedes the one-per-day attendance recommendation. OD-10 explicitly
defers the proposed optional Inventory panel. The owner instruction's enumerated decisions govern.

| Historical recommendation | Original proposal position | Current resolution |
| --- | --- | --- |
| D1 | Employee/Party cardinality plus optional non-authorizing User | RESOLVED by OD-1 and OD-2 |
| D2 | Retain Party visibility; additional confidentiality needs another contract | RESOLVED by OD-3, adding mandatory bounded HR PERSON projection |
| D3 | Company-wide Department and optional current Employee Branch | RESOLVED by OD-4 |
| D4 | One completed interval per Employee/local start date | SUPERSEDED and RESOLVED by OD-5: multiple completed sessions per day |
| D5 | Full-day leave; technical approval/retry mechanics proposed | POLICY RESOLVED by OD-6; technical details freeze at HR-0 |
| D6 | Staff-assisted audience without public/guest access | RESOLVED by OD-7 |
| D7 | Explicit authorized staff price entry | RESOLVED by OD-8 |
| D8 | One Cart -> one Sales DRAFT through public batch API | POLICY RESOLVED by OD-9; API details freeze at ECOM-0 |
| D9 | Company-only channel with possible optional stock panel | RESOLVED: company scope retained; OD-10 defers stock display entirely |
| D10 | No checkout financial effects | RESOLVED by OD-11 and OD-12; Accounting boundary reaffirmed |

### Authoritative product-policy register — 12/12 resolved

| ID / state | Owner-approved policy | Technical detail still to freeze |
| --- | --- | --- |
| OD-1 — RESOLVED | One stable Employee per Company + same-company PERSON Party; no duplicated name/contact identity. Company-unique immutable number, no reassignment/reuse, simultaneous duplicate employments or rehire episodes | HR-0: exact Employee fields/number format and generation |
| OD-2 — RESOLVED | Optional User association is authentication linkage only; no inferred identity/grants/self-service. One User cannot ambiguously represent multiple active Employees in one Company | HR-0: exact FK/cardinality mechanics consistent with that rule |
| OD-3 — RESOLVED | Existing company-wide Party visibility retained. HR uses bounded PERSON identity projection and avoids unnecessary contacts/addresses; additional confidentiality needs separate Party-owner access/privacy contract | HR-0: exact identity projection/selector tests, with no Party authorization redesign |
| OD-4 — RESOLVED | Company-wide Department without Branch/hierarchy/position/grade/cost-center engine; one optional current Employee Branch, no concurrent multi-branch memberships; historical scope may be frozen | HR-0: fields and branch transfer mechanics under existing Access rules |
| OD-5 — RESOLVED | Zero/one/multiple completed attendance sessions per local day; aware intervals/cross-midnight, frozen timezone/Branch, overlap denial, immutable revisions and safe retries. No open punch/shift/roster/break/device engine | HR-0: session/request identity, revision schema, exact overlap/timezone/DST/locks |
| OD-6 — RESOLVED | Full calendar-day Leave; bounded draft/submit/approve/reject/cancel lifecycle, overlap/attendance checks, timezone, retries and approval audit. No partial/hourly leave, entitlement/accrual/payroll/workflow | HR-0: exact fields, transitions/retry payloads, self-approval definition |
| OD-7 — RESOLVED | Authenticated internal staff-assisted Commerce; operator has Company and exact Ecommerce/Sales permissions and uses existing same-company customer Party. No public/guest/customer login/registration | ECOM-0: bounded customer projection and precise action admission |
| OD-8 — RESOLVED | Authorized staff-entered Cart price is a commercial instruction; Sales owns converted line snapshots. Browser/client/customer input alone confers no price authority; no generic pricing engine | ECOM-0: exact price permission and Currency/precision policy |
| OD-9 — RESOLVED | Checkout atomically creates one DRAFT SalesOrder and all lines through a new public Sales service; confirmation separate. Cart lock + permanent CheckoutBinding + canonical input/revision + one outer transaction deduplicate conversion | ECOM-0: API signature/snapshots/locks, canonical encoding, equality, uniqueness/collision recovery |
| OD-10 — RESOLVED | Initial ECOM-1 has no Inventory display, projection API, warehouse selection, ATP/reservation/backorder/allocation or stock storage. Inventory remains sole stock authority | Future separately approved bounded Inventory adapter; no current ECOM-0 prerequisite |
| OD-11 — RESOLVED | Billing and Sales-to-Billing integration are not required for minimum Phase 3B; no automatic Invoice | Future separately gated Sales/Ecommerce/Billing composition |
| OD-12 — RESOLVED | Payments collection/gateways/receipt/allocation/payment-status functionality deferred from ECOM-1 | Future separately approved adapter consuming Payments public contracts |

Accounting's no-direct-write rule is derivable accepted architecture: minimum checkout has no
Invoice/Payment/Allocation/Journal effect. No owner policy remains unresolved. Detailed schemas,
wire contracts and permission mechanics below remain technical proposals, not runtime authorization.

### Required detailed contract gates — neither started

**TECHNICAL CONTRACT DETAIL — TO BE FROZEN AT HR-0:** exact Employee fields, number format/generation,
User FK/cardinality, status transitions, Branch transfers, Department and LeaveType fields; Attendance
session/request identity, AttendanceRevision schema, overlap algorithm, timezone/DST rules, retry
keys and reference lock order; LeaveRequest fields, transition matrix, self-approval definition and
Attendance/Leave conflict rules; exact twelve HR permissions, audit vocabulary, HTTP/UI and alias.

**TECHNICAL CONTRACT DETAIL — TO BE FROZEN AT ECOM-0:** Cart fields/status/revision, CartLine fields,
Currency/price permission, Variant eligibility, bounded customer Party projection, CheckoutBinding
fields, canonical encoding/retry equality, one-Cart/one-order uniqueness, locks/final checks,
Sales batch signature/snapshots/rollback/collision behavior, registry/RBAC, selected alias and HTTP/UI.
Inventory display and financial compositions are excluded from initial ECOM-1, not prerequisites.

## 3. Proposed HR ownership and persistence

**TECHNICAL CONTRACT DETAIL — TO BE FROZEN AT HR-0.** Proposed field/bound/mechanical detail below
must implement OD-1–OD-6; it cannot reintroduce one-per-day attendance or reopen approved policy.

All HR records have UUIDs, immutable Company ownership and aware server timestamps. Reference
identities are protected from deletion while referenced. No payroll amount, duplicated personal
name/email/phone/address, tenant field or client-specific branch logic. Proposed string bounds use
existing conventions: codes/numbers 32, names 160, reasons 2,000 characters; required text trimmed
and nonblank, optional reason is empty string, optional references/dates are null. HR-0 must freeze
these technical bounds; this table is not a created migration.

| HR-owned record | Proposed minimum facts and authority |
| --- | --- |
| Department | Company, immutable normalized uppercase code unique per company, name, `is_active`, edit revision; no parent or Branch. One company-wide department may serve multiple branches |
| Employee | Immutable company-unique normalized employee number and required person Party; optional User, Department and Branch; `ACTIVE`/`ENDED`, joining date, nullable leaving date and edit revision. No duplicated Party contact fields |
| Attendance | Stable UUID session identity, immutable Employee/company, Branch-at-recording and IANA timezone snapshot, recording request identity. Multiple sessions per local date; no unique Employee/date constraint and no mutable daily total. Exact identity/field mechanics freeze at HR-0 |
| AttendanceRevision | Attendance/company, unique increasing integer revision, aware check-in/check-out, `RECORDED`/`VOID`, correction reason, actor, request UUID. Revision 1 is original; highest valid revision is current effective interval/void state; earlier revisions immutable and all revisions append-only |
| LeaveType | Company, immutable unique code, name, activity and edit revision only. Labels supplied by authorized HR, no seeded legal entitlement/medical category/paid-day policy |
| LeaveRequest | Company, Employee, Branch-at-request, IANA timezone-at-request, type, inclusive start/end dates, reason, lifecycle, requester actor, optional decision actor/time/reason, cancellation actor/time/reason, request UUID, edit revision |

AttendanceRevision is justified narrowly: corrections must preserve original business facts under
HR ownership; Core Audit must not reconstruct attendance. LeaveType is justified only to avoid
invented jurisdictional leave categories; it has no accrual, balance, workflow or quota engine.

### Employee, Party and User

Creation requires an active same-company person Party. One Party may be a customer, supplier and
employee in the same Company without identity duplication. A person in another Company has a
separate company-owned Party/Employee; do not infer cross-company identity by name/email.
Optional User is an existing authentication identity; proposed assignment validation verifies activity
and Company access. OD-2 requires unambiguous active Employee association within Company. Exact FK,
uniqueness and inactive-Employee mechanics are HR-0 technical details, not a stronger all-history
cardinality frozen here. No automatic User creation, email matching,
credential copy, Company grant or role grant. HR permission does not grant Identity administration.

Employee number/company/Party cannot be reassigned. Optional User linkage may be explicitly
changed by employee.manage with audit and uniqueness checks, never used to authorize self-service.
Later User deactivation/access revocation must not delete employment/history. Party remains the
name/contact owner; changes are made through Party's existing services, not HR direct writes.
Later Party inactivity/type change does not rewrite history. New employment/attendance/leave
actions revalidate current person eligibility; historical reads/corrections retain the original
reference and may explain current inactivity. This does not make Party type immutable at rest.

Under OD-3, HR screens and selectors must read a bounded PERSON identity projection (scoped Party
UUID/type/display identity and only fields required by the accepted HR screen). They must not
unnecessarily materialize ContactMethod or Address, and `party_detail()` with its contact/address
prefetch is not the HR identity projection. This minimizes HR data loading; existing company-wide
Party screens/CRUD retain their visibility. Additional employee contact confidentiality requires
a separately approved Party-owner contract, never contact copies in HR.

An ACTIVE Employee has no leaving date; proposed joining date cannot be in the future on creation.
Ending employment sets leaving date >= joining date, no later than company-local today. Historical
records remain. Ending must reject if non-cancelled approved leave or recorded attendance lies
outside the proposed employment dates; resolve those facts first through their owning operations.
No automatic cancellation/deletion or rehire transition. Date correction uses employee.manage,
revalidates all affected records and records audit; an ended Employee cannot receive new prospective
leave, but authorized backdated attendance correction remains possible inside employment dates.

### Department and branch

One optional current Department per Employee, no dated membership history or hierarchy. Assign
only active same-company Department/Branch; retiring a Department with active assigned Employees
is rejected until explicit reassignment. Employee branch changes do not rewrite past Attendance
or Leave Branch snapshots. Those snapshots describe recording/request scope, not a reconstructed
historical posting/roster or a fact about where work physically occurred.

HR queries and direct lookups apply Company first. With `context.branch_id`, Employee lists/actions
are restricted to that branch, Attendance/Leave to their immutable branch snapshot; null-branch
records are not included in branch-filtered results. Company-wide Department/LeaveType setup and
Employee branch transfers require company-wide context. With no branch, valid Company grants plus
exact HR permission permit company-wide HR operations, matching Core; do not advertise branch-only
secrecy. A warehouse context is irrelevant and rejected for HR actions rather than repurposed.
Missing/foreign/inactive context scope fails closed; inactive historical branch facts can be read
from an authorized company-wide context. No bypass to activate an inactive selected branch.

### Attendance contract

OD-5 permits zero, one or multiple completed sessions on a local date. Staff-operated
`record_attendance` submits a completed positive-duration interval with aware start/end instants.
Session/request identity, elapsed-duration bounds and exact date derivation are HR-0 technical
details; the original 24-hour duration proposal is not a daily uniqueness rule.
Cross-midnight is allowed; no shift inference or automatic split. The occupied interval is half-open
`[check_in, check_out)`; an exact midnight checkout does not occupy the next day. Its occupied dates
must fall within employment eligibility. No unique Employee/date constraint or one-session-per-day limit.
Reject overlapping recorded intervals for one Employee even across adjacent dates/branches.

Capture company timezone and branch on first recording; later timezone/branch changes do not
reinterpret its frozen timezone/branch. A session's date classification is derived from its effective
revision under that timezone; it is not the session or retry identity. Corrections preserve session
identity and immutable prior revisions while revalidating overlap/employment/leave conflicts. Exact
date-changing correction/void/reinstatement mechanics freeze at HR-0. No hard delete.
Each correction requires expected revision + request UUID + nonblank reason, and appends one
revision. Identical retry returns that revision; same key/different payload conflicts. Record retry
uses session/request identity and canonical payload under HR-0's frozen key contract. A different
non-overlapping session on the same date is allowed; an exact request retry has one effect, reused
key with different canonical input conflicts. No request key is merely Employee/date.
Sequence, not wall-clock timestamp order, establishes correction order.

Reject new naive/ambiguous/nonexistent local instants unless a separately accepted explicit aware
input resolves them. An unchanged trusted persisted instant on an edit preserves fold, offset,
seconds and microseconds, following the accepted Inventory correction pattern. No comparison of
server created/updated timestamps is proof of causal order. No overtime/payroll duration authority.

### Leave contract

OD-6 accepts full-calendar-day leave with the following bounded lifecycle. Exact transition/retry
payloads and self-approval semantics are **TECHNICAL CONTRACT DETAIL — TO BE FROZEN AT HR-0**:

```text
DRAFT -> SUBMITTED -> APPROVED | REJECTED
DRAFT | SUBMITTED | APPROVED -> CANCELLED
REJECTED and CANCELLED are terminal; no hard deletion or implicit reopening.
```

Staff creates/edits on behalf of an Employee; self-service is absent. DRAFT fields may change through
leave.request. Submission freezes Employee/type/dates/reason. Inclusive dates are calendar dates,
not UTC instants; no weekends/holiday deduction, partial days, quotas or salary consequence. Dates
must be ordered and inside employment dates; type must be active at submit/approve. Ended or
inactive identity cannot gain prospective leave. Approval is HR authority, not inferred manager
hierarchy. The original proposed self-approval rule excludes the requester actor, including a
superuser; HR-0 must freeze the precise self-approval definition consistently with the staff-request
contract, rather than treating this preliminary definition as already technically accepted. Rejection
requires decision reason; cancellation requires reason and leave.cancel. Cancelling APPROVED also
requires leave.approve. Terminal retries reauthorize and require the same decision payload; another
decision/reason conflicts, no duplicate success audit or timestamp change.

Leave captures the Company's IANA timezone on request; changing Company timezone does not silently
reinterpret existing leave dates. For attendance conflict, interpret attendance instants in that
Leave's frozen timezone and compare occupied dates with its inclusive leave range. Do not infer
date eligibility from UTC alone or whichever timezone is currently configured.

Draft overlaps may exist. SUBMITTED and APPROVED requests for one Employee must not overlap; lock
Employee before checking ranges so two submissions cannot both succeed. Approved leave cannot
overlap any local calendar date touched by a recorded attendance interval. Attendance record or
correction checks the reverse conflict against approved leave, including cross-midnight intervals.
Both directions serialize on Company/Employee. Submission may precede attendance; approval must
recheck current attendance and fail. Cancellation/void removes only the current conflict, never
historical evidence. Reject/approve/cancel serialize on authoritative request status. A submitted
date/reason change requires cancellation and a new request, not silent historical editing.

## 4. Proposed HR permission and audit contracts

**TECHNICAL CONTRACT DETAIL — TO BE FROZEN AT HR-0:** exact twelve codes, action/response mapping
and audit vocabulary below. No permission is registered by owner-policy resolution.

Future module code/version: `hr`, `0.1.0`. Exact proposed permission vocabulary:

| Permission | Authorized surface |
| --- | --- |
| `hr.employee.view` | Scoped Employee list/detail and identity projection |
| `hr.employee.manage` | Create, permitted updates, end employment and User/Department/Branch association |
| `hr.department.view` | Company Department list/detail |
| `hr.department.manage` | Department create/name/activity |
| `hr.attendance.view` | Current attendance and revision history |
| `hr.attendance.record` | Initial completed interval |
| `hr.attendance.correct` | Append correction/void/reinstatement |
| `hr.leave.view` | Leave list/detail and type choices |
| `hr.leave.request` | Draft create/update and submission on behalf of an Employee |
| `hr.leave.approve` | Approve/reject; also required to cancel approved leave |
| `hr.leave.cancel` | Explicit cancel with additional approval permission where specified |
| `hr.leave_type.manage` | Company leave-type create/name/activity |

No permission is installed here. Future HTTP action form GET and POST require the action code;
displaying existing data also requires its view code. Related Employee selection requires
employee.view, Department selection department.view; type choice requires leave.view. Services
that return business data recheck corresponding view permission as well as action permission;
there is no create response leaking an otherwise forbidden record. Identical retries require the
same compound permission set. Core Company access alone is insufficient for HR-owned fields.

Audit through Core: `hr.employee.created`, `.updated`, `.ended`; `hr.department.created`, `.updated`;
`hr.attendance.recorded`, `.corrected`; `hr.leave_type.created`, `.updated`;
`hr.leave.created`, `.updated`, `.submitted`, `.approved`, `.rejected`, `.cancelled`.
Every actual persisted business change, including association changes, is covered. Include actor,
company, aggregate/revision IDs, changed field names and transition/reason classification; avoid
duplicating personal contact data or unrestricted leave narrative in general audit metadata. Full
attendance corrections remain in HR revisions, leave decision narrative in its scoped record.
No audit on every read, true no-op or successful retry. Audit failure rolls back business effects.

## 5. Proposed Ecommerce ownership, customer and pricing

OD-7 accepts the authenticated internal staff-assisted channel. Public/guest/customer self-login and
registration are outside initial ECOM-1. All operators have their own active User, Company grants and exact permissions.
The selected customer is an existing active same-company Party with `is_customer=True`, person
or organization; no customer User is required. Customer creation happens explicitly through Party,
not an automatic duplicate match by email/phone. No guest/session/customer-account table, password,
shipping address copy, delivery instruction or Store model in this slice. Those are later contract
choices, not hidden fields inside notes. A company-scoped browse screen is the initial channel.

Company-only commerce uses the existing Company boundary; the proposed HTTP/service context has
branch/warehouse unset, with exact admission mechanics frozen at ECOM-0. OD-10 excludes warehouse
selection and all Inventory display from this slice. The Sales order has no Branch field; a cart
must not pretend to retain commercial branch accounting or fulfillment ownership.

**TECHNICAL CONTRACT DETAIL — TO BE FROZEN AT ECOM-0:** exact Cart/Line/Binding schema, bounds,
Currency and projection/permission mechanics below, under resolved OD-7–OD-12.

| Proposed Ecommerce record | Why owned here / lifecycle / retention |
| --- | --- |
| Cart | Company, customer Party, Currency, creator actor, UUID, timestamps, revision, `OPEN`/`CONVERTED`/`ABANDONED`; optional draft order date and notes; immutable versioned initial-request evidence for create retry. Mutable interaction before conversion, not an order or receivable. Explicit abandon, no automatic expiry job |
| CartLine | Company, immutable Cart parent, ProductVariant, quantity, staff-proposed unit price, optional description, stable position. Unique (cart, variant), one currency from parent; no stock/paid/GL balance |
| CheckoutBinding | Immutable company/cart/SalesOrder protected references, submitted cart revision, versioned canonical payload fingerprint and resolved order date, actor and timestamp. Unique cart and unique SalesOrder; permanent conversion/retry identity, not another commercial document |

All three use UUIDs; converted Cart/Lines are frozen evidence for the binding, not mirrors of current
Sales state. Retain converted carts/bindings; no purge is authorized. OPEN/ABANDONED cart retention
and eventual deletion require a later retention policy; initial scope supports abandon only. No
CheckoutSession or second customer-order projection table is necessary; status is a bounded read
through the Sales public selector plus the immutable binding.

Catalog has no approved selling-price authority. OD-8 accepts explicit authorized **staff** price
entry; the proposed narrow `ecommerce.cart.price` permission freezes at ECOM-0. Staff UI input is
validated/authorized and persisted by the service; a raw browser or customer value is never itself
price authority. Stored price is a draft
commercial instruction; Sales owns the resulting order price/snapshot. Cart change permissions do
not grant price change. Never default a missing price to zero or derive it from stock/UoM. Zero
explicitly entered under price permission is allowed if Sales allows it. Quantity/price use the
Sales Decimal(18,4) finite bounds; reject malformed, binary-float, nonfinite, excessive precision
or overflow inputs without rounding. Display all supported unit-price precision; cart totals are
non-authoritative previews using the Sales amount policy, never a competing pricing engine.

Changing customer or currency invalidates price acknowledgement: require price permission and
explicit reapproval of every line. Checkout submits expected Cart revision; no silent conversion
of stale prices, line edits or a different displayed customer. Catalog rename/reconfiguration is
revalidated during conversion. Catalog labels remain current display data, not another Cart name/SKU
authority; Sales captures its own snapshots. An explicit Cart description must not be silently
changed. Price changes require explicit cart review, never a hidden refresh. A public self-service
offer remains a genuine gap.

## 6. Checkout to Sales: proposed public seam and retry

OD-9 requires the new atomic public Sales owner operation and a permanent CheckoutBinding.
**TECHNICAL CONTRACT DETAIL — TO BE FROZEN AT ECOM-0:** exact signature, batch fields/snapshots,
canonical encoding/revision equality, uniqueness, locks, final checks and rollback/collision rules.

Existing `create_sales_order` and `add_sales_order_line` perform owner validation, snapshots and
audits, but repeatedly calling them without a reviewed all-reference lock plan is not sufficient
evidence for a new multi-line composition. Proposed **Sales-owned** addition at ECOM-0:

`create_sales_order_with_lines(context, *, customer_id, currency_id, order_date, notes, lines)`

Typed input is ordinary explicit data: bounded 1..100 lines, each ProductVariant UUID, finite
quantity/unit price, optional description, deterministic position. Result is the SalesOrder identity
and owner snapshot/line identities. No HttpRequest, Cart model, privileged actor, callback, registry
or import of Ecommerce. Sales validates and obtains the full Party/Currency/Product/Variant reference
lock set through its own implementation, takes the complete final authority set, and creates one
DRAFT plus its lines atomically. It preserves existing single-order services and financial/identity
semantics. This is a proposed API, not an assertion that one exists; its exact additive contract and
lock compatibility with existing owner writers must pass ECOM-0 before implementation.

Outer Ecommerce operation:

1. Enter selected-alias business transaction; lock active Company; recheck context and compound
   permissions. Lock Cart, validate company/authoritative ownership and expected revision.
2. If binding exists, reauthorize, compare exact stored conversion input/revision, validate binding
   company/cart/order identities and obtain its current Sales projection through the public owner
   selector. Apply the complete final compound permission checks before returning. Do not create again.
3. Otherwise require OPEN/nonempty Cart and full prices. Resolve omitted order date once through
   company-local date. Call the Sales-owned public batch API. It validates active customer,
   active/sellable Product and Variant, active Currency and all line bounds, obtains the complete
   reference lock set, then takes final Sales create/update authority and creates the DRAFT/lines.
4. Before persisting the binding or returning, apply final Ecommerce checkout/view and Sales view
   checks. This reuses the same complete authority set already held by Sales, not new partial locks.
   Do not acquire final Ecommerce authority before the batch API has acquired its domain/reference
   locks. No private token, unscoped owner write or synthetic admin context is permitted.
5. Persist binding, freeze cart and append `ecommerce.checkout.converted` in the same outer
   transaction. Nested Sales savepoints are not commits. A denied final Ecommerce/view check or
   any line/audit/binding error rolls back the entire Sales/cart/audit set. No owner result escapes
   before outer success. Owner audits remain owner audits.

Retry identity is immutable Cart UUID in Company scope plus submitted revision and canonical
payload (ordered lines, customer, currency, original optional date and notes). Store resolved date
separately so an identical omitted-date retry across midnight recovers the same order. Canonical
encoding/version and Decimal string normalization must be frozen at ECOM-0; fingerprint is a
comparison aid, not permission or a substitute for retained input. Same cart/different input after
conversion is a conflict. Lock and DB uniqueness enforce one binding/order; an unexpected unique
collision is recovered only after a savepoint rollback and full equality/provenance validation,
never a generic IntegrityError-to-success conversion. Crash before outer commit leaves no effect;
crash after commit/response loss returns the existing identity on authorized retry.

Sales may subsequently edit its DRAFT or confirm/cancel through existing services. Retry reports
conversion identity plus **current Sales state**; it does not certify that current order lines still
equal the frozen cart, overwrite legitimate Sales edits or create a replacement order. Missing or
foreign/corrupt binding target fails closed. A protected binding prevents draft-order deletion while
referenced; this additive retention effect on Sales must be accepted/tested at ECOM-0.

Checkout never confirms automatically. Normal `sales.order.confirm` is a separate explicitly
authorized Sales action, with its own validation, race handling and audit. No stock or invoice follows.

## 7. Optional capabilities, authority and admission

| Capability | Owner-resolved initial ECOM-1 scope | Future separately gated relationship |
| --- | --- | --- |
| Inventory | OD-10: display/projection/warehouse selection entirely deferred; no Inventory calls or stock quantity storage in base Ecommerce | Future adapter -> bounded Inventory public projection after separate approval; no ATP/reservation promise |
| Billing | OD-11: no invoice or Sales-to-Billing integration required for initial completion; no direct Invoice persistence/import | Future integration -> public Sales source + Billing creation contract with its own idempotency/source basis |
| Payments | OD-12: receipt/allocation/collection/payment status/providers deferred | Future payment-provider adapter -> Payments public receipt/payment contract under separate approval |
| Accounting | No Ecommerce call/write to ledger; no new dependency | Future explicit approved Billing/Payments Accounting outcome services retain control; no duplicated effect |

Inventory remains the sole posted stock authority. Its scalar `stock_balance` is not an availability
promise, and current `balances_for_warehouse` is not a bounded page API. These observations justify
OD-10's deferral; they create no API or panel prerequisite for ECOM-0/ECOM-1. A future separately
approved adapter must preserve posted UoM, complete evidence and explicit unavailable semantics,
without inventing stock or availability. Initial checkout makes no stock assertion or stock check.

Accepted umbrella direct manifest policy; future technical contracts and runtime manifests remain pending:

```text
hr (0.1.0)        -> party, organization, reference, access
ecommerce (0.1.0) -> party, catalog, sales, organization, reference, access

existing: sales -> party, catalog, organization, reference, access
future deferred: Ecommerce Inventory adapter -> Inventory bounded owner projection
future deferred: Sales/Ecommerce Billing integration -> Sales source + Billing creation contracts
future deferred: payment-provider adapter -> Payments public receipt/payment contract
future deferred: attendance-device adapter -> HR public attendance service
existing optional: payments_billing -> payments, billing
existing optional: accounting_billing -> accounting, billing
existing optional: accounting_payments_billing -> accounting, accounting_billing, payments_billing
```

No Inventory adapter, optional FK/migration, warehouse control or eager Inventory import belongs
to initial ECOM-1. Future adapters require separate approval; no generic adapter framework. Base HR and Commerce bootstrap
without Inventory/Billing/Payments/Accounting or each other. Existing owners bootstrap without both.
Core common/identity/audit/time/database/registry are allowed infrastructure, not new business manifest
dependencies. No reverse owner import, cycle, dynamic plugin installer or auto dependency enablement.

Future registration freezes historical permission declarations, starts disabled and preserves existing
enablement. HTTP/navigation hides disabled/missing modules and denies direct URLs with 404. Service
APIs remain installed and independently authorize context/RBAC. Hard dependency UI admission is
explicit, not implied by the current decorator: Commerce browse requires Ecommerce/Catalog/Party
availability; cart/checkout and order status additionally require Sales. No registry gate in services.

Proposed Ecommerce permissions: `ecommerce.cart.view`, `ecommerce.cart.manage`,
`ecommerce.cart.price`, `ecommerce.checkout.convert`. Browse uses cart.view; draft create/edit/line
add/remove/abandon uses manage; setting/changing price also requires price. Detail/action responses
and existing-record forms require view. Conversion requires cart.view + checkout.convert +
sales.order.create + sales.order.update + sales.order.view. It does not require confirm. Price is
approved during persisted cart mutations; conversion cannot supply a new client price. Status reads
require cart.view + sales.order.view; denied owner reads are unavailable/denied, not cached disclosure.
No arbitrary public shopper receives these internal ERP permissions.

## 8. Transactions, races and history protection

Every proposed mutation below uses one selected-alias business transaction, active Company lock,
current permission recheck after waiting, then authoritative domain/reference locks and final
permission checks immediately before effect/authorized retry. Actor, all assigned same-company
Roles and all reachable Permissions use the existing complete ordered set, including inactive rows;
superuser namespace handling remains Core-owned. Do not copy an older pre-final-guard Phase 2 pattern.

| Mutation family | Authoritative serialization and retry identity |
| --- | --- |
| Department / LeaveType create/update/activity | Company -> existing setup row if any; company/code DB uniqueness. Duplicate create conflicts; response-loss recovery is an authorized lookup, not certification of unchanged original values. Update uses expected revision; no-op no audit |
| Employee create | Company -> referenced Department/Branch/Party and optional User in HR-0's stable order -> final authority; unique company/number and company/Party, with User mechanics implementing OD-2. Duplicate create conflicts; authorized lookup recovers identity, not a historical-create receipt |
| Employee update/end/association | Company -> Employee -> affected reference set; expected revision rejects stale writes. Recheck attendance/leave before date/end changes; no inferred history rewrite |
| Attendance record | Company -> Employee -> session/request identity if present -> revisions. HR-0 freezes request uniqueness/canonical comparison; no Employee/date uniqueness. Same-day non-overlapping sessions allowed; check overlap/approved leave under Employee lock; full failure rollback |
| Attendance correction | Company -> Employee -> persisted Attendance -> latest revision; expected revision and unique request UUID. Append exactly once; reject stale/reused-different input and in-memory parent substitution |
| Leave create/edit/submit | Company -> Employee -> existing Leave -> type; unique company/request UUID for create. Duplicate create returns conflict with authorized identity lookup, not an unchanged-history receipt. Expected revision for edit/submit. Range conflicts checked across company/Employee regardless branch, not only visible list |
| Leave approve/reject/cancel | Company -> Employee -> authoritative Leave/type -> final authority; exact request/status/decision payload retry. Recheck overlap, attendance, employment and self-approval rule after waits |
| Cart create | Company -> Party/Currency -> final authority; client-generated request UUID scoped to Company is Cart identity. Same exact create request recovers, changed request conflicts |
| Cart update/price/line/abandon | Company -> Cart -> relevant owner references through reviewed public contracts; expected revision; stable line identity/position under Cart lock. Same complete replacement/no-op returns without audit, stale revision conflicts |
| Checkout conversion/retry | Company -> Cart -> complete Sales-owned reference lock set -> complete final authority -> owner batch-create/binding/audits. Cart unique binding is permanent retry identity; row/status checks repeated after waits |

Company lock already serializes same-company operations; do not add a generic lock coordinator or
redundant reservation subsystem. HR-0/ECOM-0 must finalize exact reference order against supported
owner writers, especially shared Currency/User and Sales reference locking before nested owner
mutations. An approved public owner lock/batch seam is required where existing APIs cannot enforce
that sequence; direct private helper imports are forbidden. Fixed lock-set tests must include
different companies sharing actor/Permission/Currency and nested savepoint rollback, not just one
successful same-company race. Raw SQL by an unrestricted operator is not a claimed security sandbox.

HR/Commerce public model and bulk ORM paths must not bypass immutable identity/history/lifecycle;
queryset update/bulk update/create/conflict-upsert/delete are rejected or validated with equivalent
invariants. Persisted parent is authoritative for stale save/delete, never mutable in-memory FK.
No generic framework or copied financial ledger machinery merely for simple setup rows. New module
history protection must not weaken existing owners or edit released migrations.

Reads require current context/RBAC and company/branch predicates before materialization; no cached
authorization or unbounded cross-company projections. Paginate lists at the existing 50-row pattern
with stable UUID tie-breakers. Delayed/lazy reads and post-wait revocation need explicit regression
coverage. Do not claim a one-time view check protects later unrelated queries indefinitely.

`database_execution` chooses infrastructure connection, not business identity. Everything including
audit, uniqueness recovery, raw lock queries and registration/bootstrap uses the selected alias;
unknown alias or nested switch fails closed. Non-default tests trap default cursor access. No
HttpRequest enters business services, and no new tenant resolver or distributed transaction exists.

Commerce audit actions: `ecommerce.cart.created`, `.updated`, `.abandoned`,
`ecommerce.checkout.converted`. Price changes are included in updated metadata (field/line IDs),
not omitted by a partial comparison tuple. One meaningful success per changed aggregate operation;
existing Sales create/update audits remain independently owner-attributed in the same outer commit.
No success event on conflict, validation/RBAC failure, rollback or exact retry.

## 9. UI and explicit exclusions

HR: Employee list/detail/create/edit/end; Department list/manage; completed-session attendance list/record and
correction history; Leave list/detail/draft/request/submit/approve/reject/cancel and type setup.
Commerce: authenticated company catalog browse, cart and staff price entry, checkout review, bound
Sales conversion-confirmation/status screen (conversion confirmation does not mean SalesOrder
confirmation). OD-7 excludes public/customer/guest admission; no Inventory panel or warehouse choice.
Existing Django templates/Tailwind/HTMX/Alpine shell remains. GET-only safe navigation, bounded
list-results swaps, query-preserving 50-row pagination, full-page/no-JS fallback; mutations remain
normal CSRF-protected POST. Action forms/buttons require exact permissions and stale company forms
are rejected. No global-shell redesign, React, SPA or default privileged client actor.

Real browser verification is required at 390/768/1280: no page-level overflow with long names,
maximum numeric values or error text; table scroll local; labels/focus/Tab/Enter/validation accessible;
deep-link/refresh/Back/Forward and HTMX security retained. Server error presentation must not leak
foreign-company identities or permit stale scope resubmission.

HR exclusions: Payroll, salary, tax, benefits, recruitment, appraisal, job grades, cost centers,
org-chart engine, shift scheduling, roster optimization, biometric integration, expenses, timesheets,
entitlement accrual and generic approvals/workflow. No employee self-service or manager hierarchy.

Commerce exclusions: pricing/pricelist/promotions/coupons/tax engines, shipping rates or courier
integration, multi-vendor marketplace, returns/exchanges, refunds, subscriptions, loyalty,
recommendations, search infrastructure, reservation/ATP/backorders/multi-warehouse allocation,
fraud engine, bKash/Stripe/SSLCommerz/card adapters or authorization/capture, CMS/page builder/SEO.
No automatic Invoice/Payment/Allocation/Journal or stock mutation/display. Guest/public checkout is
deferred by OD-7. No new Redis/Celery/event bus/metadata engine,
custom runtime, tenancy activation, Phase 4 vertical or production deployment.

## 10. Future acceptance matrix — HR

These are required future tests/evidence, **not executed or passing in PH3-0**.

| ID | Objective acceptance evidence |
| --- | --- |
| H01 | Two companies; direct/list/search/choice/history and every mutation reject foreign IDs, mixed parents and stale company form submissions |
| H02 | OD-4 company-wide Department and one optional current Employee Branch; HR-0 transfer/snapshot rules under existing Access; branch-filtered direct/list/mutation scope, company-wide semantics and past scope preserved |
| H03 | OD-1 stable Company/PERSON Party identity/immutable number and OD-2 unambiguous active User association under HR-0 FK mechanics; OD-3 bounded PERSON projection without unnecessary contacts/addresses; existing Party visibility retained, no contact copies or implicit grants |
| H04 | Duplicate Employee/Department/type codes under real PostgreSQL contention: one fact, explicit conflict/recovery; Department retirement/reassignment rules |
| H05 | Exact twelve HR-0 codes and compound read/action permissions; non-superuser happy path; HR-0 frozen self-approval semantics; active-registered permission required for superusers |
| H06 | Missing/disabled registry hides navigation/404; installed service remains callable with valid RBAC; deterministic migration registration preserves enablement |
| H07 | Selected non-default alias with default-cursor trap for reads/mutations/audit/registration; rollback and unknown/nested alias refusal |
| H08 | OD-5 multiple same-day non-overlapping completed sessions succeed; HR-0 request-key retry/conflict and same-day/cross-date/branch overlap races reject safely; one original revision per session plus immutable corrections, no mutable daily authority |
| H09 | HR-0 frozen timezone/DST/date/duration rules: midnight, timezone changes, folds/gaps, preserved precision and employment limits; cross-midnight sessions supported; clock rollback not mistaken for causal corruption |
| H10 | Correction/void/reinstate retry, stale revision, altered key payload, immutable prior facts and wrong-parent save/delete/bulk paths |
| H11 | OD-6 full-calendar-day Leave only; HR-0 exact transition/retry/self-approval contract, ordered/inclusive dates, inactive type, employment eligibility, reason/actor fields; no entitlement/payroll/workflow |
| H12 | Concurrent overlapping submit, approve versus cancel, approve versus attendance and reverse winner orders; no phantom overlap or partial history |
| H13 | HR-0 freezes exact reference/final-authority lock protocol; real PostgreSQL Role/access/actor/Permission revocation waits deny after recheck; supported batch writers and both winner orders tested |
| H14 | Audit on every actual significant change, no-op/retry no duplicate, injected audit failure rolls back identity/revision/lifecycle |
| H15 | HTTP GET/action permission, CSRF POST-only, stale company, hostile text, bounded pagination/query preservation and non-JS fallback |
| H16 | Actual browser 390/768/1280, overflow/focus/keyboard/errors, approved shell and navigation unchanged |
| H17 | Fresh PostgreSQL bootstrap and module-local discovery; HR alone with required owners; no Ecommerce/financial hard dependency |
| H18 | Full PostgreSQL and supported SQLite suites with explicit PostgreSQL-only skips; Ruff/changed-file formatting including migrations, Django/drift, JS/Tailwind reproducibility and docs/scope checks |

## 11. Future acceptance matrix — Ecommerce

| ID | Objective acceptance evidence |
| --- | --- |
| E01 | ProductVariant identity for simple/variable/service products; inactive/unsellable/foreign variants rejected; no duplicate catalog/order/stock authority |
| E02 | OD-7 authenticated staff-assisted audience and ECOM-0 bounded same-company customer Party projection/eligibility; no email match/implicit grants or public/guest/customer login/registration |
| E03 | OD-8 authorized staff-entered prices with ECOM-0 exact price permission/Currency policy; finite Sales-compatible values, missing/client-authoritative price denied, repricing acknowledgement and stale revision rejection |
| E04 | OD-9 new public Sales batch service, ECOM-0 signature/snapshots/position/alias/RBAC/rollback frozen; one atomic DRAFT and all lines, no automatic confirm or private/direct persistence |
| E05 | ECOM-0 canonical checkout/revision encoding/equality frozen; concurrent same-cart conversion has one binding/order, response-loss/midnight retry recovers, changed input conflicts and no duplicate audit |
| E06 | Binding/owner references protected, foreign/orphan/corrupt provenance fails; later legitimate Sales edit/confirm/cancel returns current state without resetting or falsely certifying original content |
| E07 | Inject every line/binding/audit failure: no partial order/cart transition or success event; known uniqueness collision recovery after savepoint rollback only |
| E08 | Checkout versus cart edit/price/abandon both winner orders; shared actor/Currency cross-company contention and owner-reference changes; real PostgreSQL lock blocking, no timing sleeps |
| E09 | Exact compound Ecommerce/Sales RBAC and final guards; Role/access/actor/Permission revocation and supported batch writer races; no privileged context substitution |
| E10 | Company-only scope explicitly enforced, foreign Cart/Party/Variant/order denied, branch/warehouse context rejected for base checkout, stale company HTTP matrix |
| E11 | OD-10: ECOM-1 has no Inventory import/call/display/projection requirement, warehouse selection, stock storage/assertion/mutation or ATP/reservation; works with Inventory absent or installed; stock authority retained |
| E12 | OD-11: Billing/Sales-to-Billing not required for Phase 3B exit; absent/present gives no invoice generation or eager dependency; no outstanding inference |
| E13 | OD-12: Payments/allocation/providers/payment status deferred; absent/present gives no checkout receipt/allocation/collection or fabricated paid/unpaid state |
| E14 | Accounting absent/present: no direct journal write or implicit outcome posting; existing explicit integrations unchanged |
| E15 | Manifest dependency/permission vocabulary, fresh bootstrap with only hard owners and with all optional owners; disabled/missing HTTP/navigation gating, authorized Python service independence |
| E16 | Selected alias including nested Sales/audit/unique recovery; default-cursor trap, no alias switch or cached cross-database models |
| E17 | Cart/binding immutability and guarded bulk ORM, stale parent/delete attacks, explicit retained conversion evidence and no authoritative cached total/balance |
| E18 | HTTP CSRF/POST, exact action GET permissions, list limits/stable order, query preservation, safe HTMX, non-JS and history/deep-link behavior |
| E19 | Actual browser 390/768/1280 cart/review/status/errors with max prices/long labels; local table overflow only, keyboard/focus intact |
| E20 | Full PostgreSQL and supported SQLite with classified skips, module-local discovery, fresh bootstrap, Ruff/changed-file format, Django/drift, JS/Tailwind/CSS/docs; Phase 0–2 regressions preserved |

## 12. Delivery gates and bounded final exit

| Gate | Required output / stop boundary |
| --- | --- |
| PH3-0 (current checkpoint) | Both supplied independent audits PASS / A; OD-1–OD-12 resolved; formally accepted for canonical adoption, pending successful branch/main CI and direct fast-forward; no runtime |
| HR-0 | NOT STARTED; freeze HR technical details listed in section 2 under resolved OD-1–OD-6, including exact twelve permissions, then detailed contract acceptance; implementation separately authorized |
| HR-1 | Bounded HR runtime only after authorization; H01–H18 evidence, independent audit, then separately authorized publication/acceptance/adoption |
| ECOM-0 | NOT STARTED; freeze Commerce/Sales technical details listed in section 2 under resolved OD-7–OD-12, including price permission, canonical retry/locks/public batch API; no Inventory or finance prerequisites |
| ECOM-1 | Bounded Commerce and accepted additive Sales API only after authorization; E01–E20 evidence and independent audit before separate publication/adoption |
| PH3-FINAL | Combined canonical regression and independent final Phase 3 exit audit, formal closure and exact-head CI under separate authorization |

HR-1 and ECOM-1 can be developed independently after both relevant contracts are accepted and
authorization identifies non-overlapping file ownership. HR must not edit the shared shell/Core or
the Sales batch seam. Canonical adoption remains sequential; later candidate must be verified
against the then-current canonical base by an explicitly authorized method. Parallel work is not
permission to rebase/merge/rewrite, introduce a runtime framework, or combine unreviewed contracts.

Thirteen finite exit criteria, all currently **NOT STARTED**:

| Exit | Required PASS evidence |
| --- | --- |
| X01 | Resolved OD-1–OD-6 implemented under accepted HR-0; HR-1 independently accepted with H01–H18 complete, including multiple completed sessions and bounded PERSON projection |
| X02 | Resolved OD-7–OD-12 implemented under accepted ECOM-0; ECOM-1 independently accepted with E01–E20 complete: staff-assisted Cart/Checkout -> one DRAFT SalesOrder and lines |
| X03 | One authority each for Party/ProductVariant/Order/stock/Invoice/Payment/allocation/GL; architecture and runtime regressions prove no duplicate writes |
| X04 | Company/branch isolation across direct reads, lists, mutations and stale forms verified on two companies |
| X05 | Exact registered active permissions and post-wait/final authorization verified, including revocation and HR-0 frozen self-approval rules |
| X06 | Non-default execution and default trap pass for all new reads/mutations/audit/bootstrap; no tenant identity introduced |
| X07 | Real PostgreSQL races, retries, response loss, nested rollback, immutable history and uniqueness protections pass |
| X08 | Initial Phase 3B completes without Inventory display/projection/warehouse selection, Billing, Payments, Accounting or public/guest storefront; absence/presence tests prove no stock/financial effects or fabricated availability/payment state |
| X09 | HTTP/module admission, CSRF, Python service independence, list bounds and HTMX/no-JS security verified |
| X10 | Minimum accepted HR and Commerce flows demonstrated at 390/768/1280 with accessible keyboard/errors and no page overflow |
| X11 | Combined full PostgreSQL, classified SQLite, fresh migrations, lint/format/Django/drift/JS/Tailwind and exact-head hosted CI pass |
| X12 | Scope/dependency review confirms no Payroll, gateway, speculative framework, reverse imports, historical migration rewrite or Phase 4 work |
| X13 | Fresh independent final Phase 3 audit plus explicit formal acceptance/canonical closure; no self-approval or production-readiness inference |

## 13. Historical local proposal checks — 2026-10-14

Before the one local proposal commit: documentation-only diff; Markdown relative links and anchors;
whitespace; internal consistency against accepted owners; Django system check and migration drift.
No business tests are introduced and no Phase 3 runtime test result is claimed. Unchanged full
regression suites are not substitutes for independent architecture review.

Local planning verification on 2026-10-14:

| Check | Actual result / limitation |
| --- | --- |
| Starting integrity | Clean main/HEAD/origin-main/live remote at exact canonical base; new local planning branch from that base |
| Current/history inventory | Current path/definition scan and bounded locally reachable history scan found no HR/Ecommerce implementation; not an exhaustive remote-backup audit |
| Internal architecture review | No reverse dependency, duplicated commercial authority, tenant field, private owner write, Payroll/gateway/vertical work or speculative framework; D1–D10 remain unaccepted |
| Markdown links / fences | 26 local relative links resolve across the four candidate documents; fenced blocks balanced; no repository link-check tool found |
| `git diff --check` | PASS; documentation-only paths, also checked staged before commit |
| `python manage.py check` | PASS, zero issues |
| `python manage.py makemigrations --check --dry-run` | PASS, no changes detected |
| `ruff check . --no-cache` | PASS; no source formatting/writes |
| `pytest tests/test_database_architecture.py -q -p no:cacheprovider` | 222 passed in 3.37s; existing architecture regressions only, not new HR/Ecommerce tests |

Runtime checks used the existing `ui-gate1-qa-web:latest` QA image (Python 3.13.16), read-only
repository bind mount, `--network none`, `PYTHONDONTWRITEBYTECODE=1`, in-memory SQLite test settings,
and all three existing financial integration install flags enabled. Containers used `--rm`.
No customer/demo database, generated CSS, migration or runtime file was modified. No full
PostgreSQL/SQLite suite, browser test or hosted CI is claimed for this documentation-only task.
Those remain required for future separately authorized implementation candidates.

At original proposal `15e68828300f40c84165c86317217024f6b9d66d`, the next action was an independent
structure audit and owner resolution. D1–D10 were unaccepted at that checkpoint. Those original
checks/history remain above; the subsequent supplied audit and twelve owner resolutions are in
section 2. The current checkpoint supersedes pending owner-policy wording, not historical evidence.

## 14. Historical resolution checkpoint — 17339a0 — 2026-10-14

The following boundary and checks describe the completed resolution task, before the final audit
and present acceptance. Its then-pending authorization wording is historical; current status is section 15.

**12/12 owner policies are RESOLVED.** No remaining owner-policy ambiguity is claimed. Technical
details are explicitly labelled for HR-0/ECOM-0 in section 2; neither gate has started. Inventory
display API and financial integrations are future separately approved work, not initial blockers.
The minimum Phase 3 exit requires accepted HR-1 **and** accepted ECOM-1; the latter is staff-assisted
Cart/Checkout -> DRAFT SalesOrder. The thirteen exit criteria remain future requirements, not PASS
results or evidence of completed implementation.

This task creates one local documentation resolution commit above the original proposal, retaining
canonical Phase 2 main. ADR 0017 stays **PROPOSED — FINAL ACCEPTANCE PENDING**. Next action is a
fresh independent final umbrella-contract audit of this resolution checkpoint. Formal acceptance,
publication, HR-0, ECOM-0, HR-1, ECOM-1, Phase 4 and deployment remain unauthorized in this task.

Local owner-resolution checks on 2026-10-14, separate from the supplied independent audit:

| Check | Actual result |
| --- | --- |
| Pre-edit integrity | Clean planning branch at `15e68828300f40c84165c86317217024f6b9d66d`, parent and local/remote main at canonical base; remote planning branch absent |
| Scope and policy review | Four authorized Markdown files only; OD-1–OD-12 resolved; technical detail separately labelled; no runtime or Phase 2 historical-record changes |
| Documentation | 26 relative links and 8 heading anchors resolve; balanced fences; whitespace checks PASS |
| Matrix preservation | 18 HR criteria, 20 Ecommerce criteria and 13 exits retained as future requirements; none reported as executed PASS |
| `python manage.py check` | PASS, zero issues |
| `python manage.py makemigrations --check --dry-run` | PASS, no changes detected |
| `ruff check . --no-cache` | PASS |
| `pytest tests/test_database_architecture.py -q -p no:cacheprovider` | 222 passed in 3.32s |

Checks used the existing QA image with Python 3.13.16, a read-only source mount, no network,
in-memory SQLite settings and all three existing financial integration flags enabled, as in the
historical proposal check. No full runtime suite or hosted CI is claimed. These local documentation
checks and internal consistency review are not the required fresh final independent umbrella audit.

## 15. Final independent audit and formal acceptance — 2026-10-14

Original proposal `15e68828300f40c84165c86317217024f6b9d66d` received supplied independent
**FINAL PASS — PHASE 3 UMBRELLA ARCHITECTURE APPROVED FOR OWNER-DECISION RESOLUTION**, Readiness A,
zero candidate-owned P0–P3. Owner resolution `17339a0ae4fdfdb9cf69df74afb98b04c07c9136` then
recorded twelve authoritative owner decisions without runtime changes. The subsequent supplied
fresh final verdict against that resolution is **FINAL PASS — PHASE 3 UMBRELLA CONTRACT APPROVED
FOR FORMAL ACCEPTANCE**, **Readiness A**, **P0: 0 / P1: 0 / P2: 0 / P3: 0**.

The owner authorizes this one documentation acceptance commit, its normal publication and CI,
followed only on success by direct normal fast-forward main adoption and separate CI. ADR 0017 is
**Accepted — Phase 3 Umbrella Contract**; OD-1–OD-12 and hard dependency sets are frozen as recorded.
Formal acceptance is COMPLETE; canonical adoption is PENDING at this acceptance checkpoint.
The original Proposed and owner-resolution history remains, rather than backdating acceptance.

The final audit confirms owner boundaries/privacy, session/revision attendance authority, bounded
Leave, staff-assisted Commerce and pricing, public Sales batch direction, deferred Inventory/
Billing/Payments, no duplicated authority or cycles, bounded HR-0/ECOM-0 deferrals, eighteen HR
requirements, twenty Commerce requirements and thirteen future exit criteria. This is supplied
contract review evidence, not new runtime test evidence. No policy or detailed technical design is
changed by acceptance; HR-0 and ECOM-0 still must freeze all items listed in section 2.

The accepted minimum requires both HR-1 and ECOM-1 accepted implementations, with initial Commerce
Cart/Checkout -> one atomic DRAFT SalesOrder + lines. Neither exists. No Inventory display,
Billing, Payments, Accounting or public/guest storefront is required for minimum Phase 3B.

### Publication and canonical completion rule

Required chain: canonical base `0d4a14254889ba1ec06cfb16088009177991d8d8` -> proposal
`15e68828300f40c84165c86317217024f6b9d66d` -> resolution
`17339a0ae4fdfdb9cf69df74afb98b04c07c9136` -> this one acceptance commit. No extra commit.
Publish only `phase3-people-commerce-contract` normally, require successful `Phase 0 checks`
push CI at this exact SHA, then verify unchanged remote main, ancestry and three commits above base.
Push this same SHA normally to main, require a separate successful main push CI at that exact SHA,
then fast-forward local main. Keep the planning branch as evidence; no PR or tag is specified.

Only after all gates pass does this acceptance SHA become the canonical umbrella freeze and
ADR 0017/Phase 3 umbrella become CANONICALLY ACCEPTED. Pending wording is this acceptance-stage
record; verified fulfillment of this rule supersedes it. No future run number, ID, test count or
success is claimed before observation. Failure or unexpected state stops without automatic correction.

HR-0 and ECOM-0 become eligible for separate authorization after canonical acceptance but remain
NOT STARTED in this task. HR-1/ECOM-1/runtime, Phase 4 and deployment are NOT AUTHORIZED.
Phase 3 is not complete and no production readiness is claimed.
