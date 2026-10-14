# Phase 3 — People and Digital Commerce

Status: **PROPOSED — NOT ACCEPTED / NOT IMPLEMENTED**.

Date: 2026-10-14. Gate: PH3-0 local architecture proposal.

Canonical base: `0d4a14254889ba1ec06cfb16088009177991d8d8`.
Planning branch: `phase3-people-commerce-contract`.
Umbrella: [ADR 0017](../../decisions/0017-phase3-people-digital-commerce-boundaries.md).

## 1. Authority, evidence and current inventory

This document proposes future contracts. It authorizes no model, migration, manifest, permission,
service, UI or runtime implementation. HR and Ecommerce are both NOT STARTED. No owner decision
below is accepted merely because a recommendation is specific. No independent Phase 3 audit has
been performed in this planning task.

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

## 2. Tracks and owner decisions

Phase 3A is reusable People/HR foundation. Phase 3B is a separately gated commerce composition.
Their common constraints are derived from accepted architecture; their business choices below are
**OWNER DECISION REQUIRED**. Recommendations make the proposal reviewable, not accepted.

| ID | Recommended choice for review | Alternative / impact / required gate |
| --- | --- | --- |
| D1 | One Employee per (Company, person Party), immutable Party binding; optional User link is metadata only; no self-service | Multiple employments/rehire history and User self-service need another identity/lifecycle contract; HR-0 must accept cardinality |
| D2 | HR fields restricted by HR permissions, but linked Party names/contacts retain existing company-wide Party visibility; no sensitive medical/payroll data | If employee identity/contact confidentiality is required, HR-1 is blocked pending an explicitly approved Party-owner access extension; do not duplicate contacts or silently change ADR 0004 |
| D3 | Company-wide Department; optional current Employee Branch; HR branch-context filtering, company-wide context retained | Mandatory branch confinement cannot be derived from current Company grants; needs separate Access contract. Department hierarchy/multiple memberships deferred |
| D4 | One completed attendance interval per Employee/local start date; explicit HR-owned append-only revisions and void correction | Multi-session punch clock/open intervals/shift model changes schema and duplicate rules; HR-0 must choose |
| D5 | Full inclusive calendar-day leave, company-defined type labels without balances, staff requests and HR decisions; no self-approval | Half days, work-calendar entitlements and multi-stage approval require a later contract; approval/cancellation authority and overlap policy below need HR-0 acceptance |
| D6 | Authenticated staff-assisted Commerce; Party customer without required User; no public/guest session | A public shop needs a dedicated customer identity/admission contract, not ERP Company access; ECOM-0 must confirm this limited delivery meets its product goal |
| D7 | Explicit persisted staff-entered unit price, no automatic price discovery; separate price permission | Self-service price offers require a small owner-approved Sales price-source contract before exposure; no Catalog pricing engine is assumed |
| D8 | One cart converts to one Sales DRAFT through a new bounded Sales public batch-create API; confirmation stays separate | Automatic confirmation changes compound permissions/retry and validation; Sales-owner API extension and retention of converted carts must be accepted at ECOM-0 |
| D9 | Company-only channel, no Store model/branch/warehouse allocation; optional permissioned Inventory balance display at an explicitly selected warehouse | Branch commerce or Store configuration requires a concrete need and a Sales branch-semantics decision; stock display is never a promise |
| D10 | No invoice, payment, allocation or Accounting effect during checkout | Financial composition is a later independently approved gate using existing owners; no implicit acceptance from Payments being installed |

No runtime work may start with an unresolved decision that affects its schema/API or admission.
HR-0 resolves D1–D5; ECOM-0 resolves D6–D10 and the Sales batch API. Rejected recommendations must
be revised before implementation. PH3-0 review does not itself grant either implementation authority.

## 3. Proposed HR ownership and persistence

All HR records have UUIDs, immutable Company ownership and aware server timestamps. Reference
identities are protected from deletion while referenced. No payroll amount, duplicated personal
name/email/phone/address, tenant field or client-specific branch logic. Proposed string bounds use
existing conventions: codes/numbers 32, names 160, reasons 2,000 characters; required text trimmed
and nonblank, optional reason is empty string, optional references/dates are null. HR-0 must freeze
these bounds along with D1–D5; this table is not a created migration.

| HR-owned record | Proposed minimum facts and authority |
| --- | --- |
| Department | Company, immutable normalized uppercase code unique per company, name, `is_active`, edit revision; no parent or Branch. One company-wide department may serve multiple branches |
| Employee | Immutable company-unique normalized employee number and required person Party; optional User, Department and Branch; `ACTIVE`/`ENDED`, joining date, nullable leaving date and edit revision. No duplicated Party contact fields |
| Attendance | Immutable Employee/company, company-local business date, Branch-at-recording and IANA timezone snapshot; unique (company, employee, business_date). Identity container, not mutable worked-hours balance |
| AttendanceRevision | Attendance/company, unique increasing integer revision, aware check-in/check-out, `RECORDED`/`VOID`, correction reason, actor, request UUID. Revision 1 is original; greatest revision is current authority; all revisions append-only |
| LeaveType | Company, immutable unique code, name, activity and edit revision only. Labels supplied by authorized HR, no seeded legal entitlement/medical category/paid-day policy |
| LeaveRequest | Company, Employee, Branch-at-request, IANA timezone-at-request, type, inclusive start/end dates, reason, lifecycle, requester actor, optional decision actor/time/reason, cancellation actor/time/reason, request UUID, edit revision |

AttendanceRevision is justified narrowly: corrections must preserve original business facts under
HR ownership; Core Audit must not reconstruct attendance. LeaveType is justified only to avoid
invented jurisdictional leave categories; it has no accrual, balance, workflow or quota engine.

### Employee, Party and User

Creation requires an active same-company person Party. One Party may be a customer, supplier and
employee in the same Company without identity duplication. A person in another Company has a
separate company-owned Party/Employee; do not infer cross-company identity by name/email.
Optional User is an existing active identity with verified access to this Company on assignment;
at most one Employee per (Company, non-null User). No automatic User creation, email matching,
credential copy, Company grant or role grant. HR permission does not grant Identity administration.

Employee number/company/Party cannot be reassigned. Optional User linkage may be explicitly
changed by employee.manage with audit and uniqueness checks, never used to authorize self-service.
Later User deactivation/access revocation must not delete employment/history. Party remains the
name/contact owner; changes are made through Party's existing services, not HR direct writes.
Later Party inactivity/type change does not rewrite history. New employment/attendance/leave
actions revalidate current person eligibility; historical reads/corrections retain the original
reference and may explain current inactivity. This does not make Party type immutable at rest.

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

Staff-operated `record_attendance` submits a completed positive-duration interval. Both instants
are aware; duration <= 24 elapsed hours; company-local start date equals Attendance business date.
Cross-midnight is allowed; no shift inference or automatic split. The occupied interval is half-open
`[check_in, check_out)`; an exact midnight checkout does not occupy the next day. Its occupied dates
must fall within employment eligibility. One-per-start-date uniqueness is deliberate, not a full punch clock.
Reject overlapping recorded intervals for one Employee even across adjacent dates/branches.

Capture company timezone and branch on first recording; later timezone/branch changes do not
relabel its date. Corrections interpret the original timezone, preserve the date identity and
validate interval overlap. Wrong-date entry is explicitly voided, then recorded under the correct
date; a voided date may be reinstated only by a correction on its existing identity. No hard delete.
Each correction requires expected revision + request UUID + nonblank reason, and appends one
revision. Identical retry returns that revision; same key/different payload conflicts. Record retry
uses Employee/date + request UUID and canonical payload; another distinct recording conflicts.
Sequence, not wall-clock timestamp order, establishes correction order.

Reject new naive/ambiguous/nonexistent local instants unless a separately accepted explicit aware
input resolves them. An unchanged trusted persisted instant on an edit preserves fold, offset,
seconds and microseconds, following the accepted Inventory correction pattern. No comparison of
server created/updated timestamps is proof of causal order. No overtime/payroll duration authority.

### Leave contract

Recommended explicit lifecycle:

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
hierarchy; the requester actor cannot approve their own request, including a superuser. Rejection
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

The recommended minimum is an authenticated internal assisted-order channel, not an anonymous
internet shop. All operators have their own active User, Company grants and exact permissions.
The selected customer is an existing active same-company Party with `is_customer=True`, person
or organization; no customer User is required. Customer creation happens explicitly through Party,
not an automatic duplicate match by email/phone. No guest/session/customer-account table, password,
shipping address copy, delivery instruction or Store model in this slice. Those are later contract
choices, not hidden fields inside notes. A company-scoped browse screen is the initial channel.

Company-only commerce requires a company-wide context with branch/warehouse unset. An optional
stock display supplies an explicitly selected warehouse to the Inventory adapter with verified
warehouse scope. The Sales order has no Branch field; a cart must not pretend to retain commercial
branch accounting or fulfillment ownership. Warehouse selection never becomes allocation.

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

Catalog has no approved selling-price authority. Proposed D7 therefore uses explicit **staff**
price entry under `ecommerce.cart.price`, not a public browser-supplied price. Stored price is a draft
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

| Capability | Initial proposal | Unavailable / deferred meaning |
| --- | --- | --- |
| Inventory | Optional read-only balance panel via public `balances_for_warehouse`, preserving posted UoM identity; explicit same-company warehouse and `inventory.balance.view` | Not installed, missing/disabled UI registration, denied or incompatible evidence => unavailable, not zero/in-stock. Negative/zero remains literal ledger balance; no ATP, guarantee or reservation |
| Billing | No checkout invoice; no direct Invoice persistence/import in base Ecommerce | Future Sales-to-Billing integration needs its own idempotency and source-basis contract; standalone Billing create is not that seam |
| Payments | No receipt or allocation at checkout, no external-result ingestion | Future payment-provider/receipt flow separately authorized; never treat order/receipt existence as paid or settled |
| Accounting | No Ecommerce call/write to ledger; no new dependency | Future explicit approved Billing/Payments Accounting outcome services retain control; no duplicated effect |

Inventory's scalar `stock_balance` returns a Decimal, not an availability promise or guaranteed current
Catalog UoM. The optional UI must use owner-returned posted UoM/quantity evidence or report unavailable;
do not relabel a historical balance with a changed Product.default_uom. No cross-company warehouse
enumeration. The current `balances_for_warehouse` materializes warehouse history; it is not a bounded
page API. If that optional panel is included, ECOM-0 must approve a small Inventory-owned bounded
projection (including posted UoM and an explicit no-history result) before implementation, or defer
the panel. Do not load all warehouse history to serve a product page or invent a UoM for no history.
In a Python service, registry state does not override Inventory RBAC; HTTP display
admission checks module availability separately. No stock check is a checkout acceptance precondition.

Future direct manifest graph, subject to ADR 0017 acceptance:

```text
hr (0.1.0)        -> party, organization, reference, access
ecommerce (0.1.0) -> party, catalog, sales, organization, reference, access

existing: sales -> party, catalog, organization, reference, access
optional read: Ecommerce Inventory adapter -> inventory public selectors
deferred: Sales/Billing composition; Ecommerce payment-provider composition
existing optional: payments_billing -> payments, billing
existing optional: accounting_billing -> accounting, billing
existing optional: accounting_payments_billing -> accounting, accounting_billing, payments_billing
```

The stock read adapter is explicitly wired only when installed; no optional FK/migration or eager
Inventory import in base Ecommerce. No generic adapter framework. Base HR and Commerce bootstrap
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
| Employee create | Company -> referenced Department/Branch/Party and optional User in a documented stable order -> final authority; unique company/number, company/Party, non-null company/User. Duplicate create conflicts; authorized lookup by number recovers identity, not a historical-create receipt |
| Employee update/end/association | Company -> Employee -> affected reference set; expected revision rejects stale writes. Recheck attendance/leave before date/end changes; no inferred history rewrite |
| Attendance record | Company -> Employee -> Attendance if present -> revisions. Natural Employee/date uniqueness plus request UUID. Check cross-date overlap/approved leave under Employee lock; full failure rollback |
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

HR: Employee list/detail/create/edit/end; Department list/manage; daily attendance list/record and
correction history; Leave list/detail/draft/request/submit/approve/reject/cancel and type setup.
Commerce: authenticated company catalog browse, cart and staff price entry, checkout review, bound
Sales confirmation/status screen. No public customer portal is promised by this recommended slice.
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
No automatic Invoice/Payment/Allocation/Journal or stock mutation. Guest/public checkout is deferred
under the recommended D6, not silently implemented. No new Redis/Celery/event bus/metadata engine,
custom runtime, tenancy activation, Phase 4 vertical or production deployment.

## 10. Future acceptance matrix — HR

These are required future tests/evidence, **not executed or passing in PH3-0**.

| ID | Objective acceptance evidence |
| --- | --- |
| H01 | Two companies; direct/list/search/choice/history and every mutation reject foreign IDs, mixed parents and stale company form submissions |
| H02 | Branch context filters current Employees and historical branch snapshots exactly; null/foreign/inactive branch denied; company-wide semantics explicit; transfers preserve past scope |
| H03 | Person Party reuse, company/Party and company/User cardinality, immutable IDs/number, inactive/type-changed Party and revoked User access behavior; no contact duplication or implicit grants |
| H04 | Duplicate Employee/Department/type codes under real PostgreSQL contention: one fact, explicit conflict/recovery; Department retirement/reassignment rules |
| H05 | Every HR code and compound read/action permission; non-superuser happy path; no self-approval; active-registered permission required for superusers |
| H06 | Missing/disabled registry hides navigation/404; installed service remains callable with valid RBAC; deterministic migration registration preserves enablement |
| H07 | Selected non-default alias with default-cursor trap for reads/mutations/audit/registration; rollback and unknown/nested alias refusal |
| H08 | Attendance same-day duplicate race, adjacent-day overlap, different-branch same-Employee conflict; one original plus ordered revisions only |
| H09 | Midnight, company-time changes, DST folds/gaps, exact unchanged precision, 24h elapsed boundary and employment date limits; clock rollback not mistaken for causal corruption |
| H10 | Correction/void/reinstate retry, stale revision, altered key payload, immutable prior facts and wrong-parent save/delete/bulk paths |
| H11 | Full leave transition matrix; ordered/inclusive dates, inactive type, employment eligibility, reason/actor fields and terminal retries |
| H12 | Concurrent overlapping submit, approve versus cancel, approve versus attendance and reverse winner orders; no phantom overlap or partial history |
| H13 | Role/access/actor/Permission revocation while waiting: post-wait and final authorization deny; supported batch writers and both winner orders tested |
| H14 | Audit on every actual significant change, no-op/retry no duplicate, injected audit failure rolls back identity/revision/lifecycle |
| H15 | HTTP GET/action permission, CSRF POST-only, stale company, hostile text, bounded pagination/query preservation and non-JS fallback |
| H16 | Actual browser 390/768/1280, overflow/focus/keyboard/errors, approved shell and navigation unchanged |
| H17 | Fresh PostgreSQL bootstrap and module-local discovery; HR alone with required owners; no Ecommerce/financial hard dependency |
| H18 | Full PostgreSQL and supported SQLite suites with explicit PostgreSQL-only skips; Ruff/changed-file formatting including migrations, Django/drift, JS/Tailwind reproducibility and docs/scope checks |

## 11. Future acceptance matrix — Ecommerce

| ID | Objective acceptance evidence |
| --- | --- |
| E01 | ProductVariant identity for simple/variable/service products; inactive/unsellable/foreign variants rejected; no duplicate catalog/order/stock authority |
| E02 | Explicit Party customer ownership/role/activity; no email/name merge or User/Company grant; no guest/public access without a separately accepted contract |
| E03 | Finite exact Sales-compatible quantities/prices, missing price denial, dedicated price permission, currency/customer repricing acknowledgement and stale revision rejection |
| E04 | Sales public batch API only; one DRAFT, correct owner snapshots/date/lines and no private persistence token/direct Sales table write |
| E05 | Concurrent same-cart checkout: one binding/order; response-loss and midnight retry recover; differing revision/payload conflicts; no duplicate audit |
| E06 | Binding/owner references protected, foreign/orphan/corrupt provenance fails; later legitimate Sales edit/confirm/cancel returns current state without resetting or falsely certifying original content |
| E07 | Inject every line/binding/audit failure: no partial order/cart transition or success event; known uniqueness collision recovery after savepoint rollback only |
| E08 | Checkout versus cart edit/price/abandon both winner orders; shared actor/Currency cross-company contention and owner-reference changes; real PostgreSQL lock blocking, no timing sleeps |
| E09 | Exact compound Ecommerce/Sales RBAC and final guards; Role/access/actor/Permission revocation and supported batch writer races; no privileged context substitution |
| E10 | Company-only scope explicitly enforced, foreign Cart/Party/Variant/order denied, branch/warehouse context rejected for base checkout, stale company HTTP matrix |
| E11 | Optional Inventory absent/disabled/denied/incompatible -> unavailable; posted UoM preserved, negative/zero exact; no reservation/ATP or stock write; service product without Inventory |
| E12 | Billing absent/present: no invoice generation; original invoice total never mislabeled as outstanding; no eager optional import |
| E13 | Payments/allocation absent/present: no checkout receipt/allocation/provider request and no fabricated paid/unpaid state |
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
| PH3-0 (this task) | Local umbrella proposal, inspection evidence, decision register and matrices; independent architecture audit next; no acceptance/publication/runtime |
| HR-0 | Explicit D1–D5 decisions, final fields/bounds/retry payloads/reference lock order and HR contract acceptance; implementation separately authorized |
| HR-1 | Bounded HR runtime only after authorization; H01–H18 evidence, independent audit, then separately authorized publication/acceptance/adoption |
| ECOM-0 | Explicit D6–D10 decisions, price/customer admission, Sales batch API and exact fingerprint/lock contract, optional display topology; no implied owner API permission |
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
| X01 | HR ownership/identity/privacy/attendance/leave choices explicitly accepted; H01–H18 complete |
| X02 | Ecommerce audience/price/conversion/dependencies accepted; E01–E20 complete; no unresolved public-shop expectation |
| X03 | One authority each for Party/ProductVariant/Order/stock/Invoice/Payment/allocation/GL; architecture and runtime regressions prove no duplicate writes |
| X04 | Company/branch isolation across direct reads, lists, mutations and stale forms verified on two companies |
| X05 | Exact registered active permissions and post-wait/final authorization verified, including revocation and forbidden self-approval |
| X06 | Non-default execution and default trap pass for all new reads/mutations/audit/bootstrap; no tenant identity introduced |
| X07 | Real PostgreSQL races, retries, response loss, nested rollback, immutable history and uniqueness protections pass |
| X08 | Optional Inventory/financial absence and explicit unavailable semantics pass; no unintended checkout financial/stock effect |
| X09 | HTTP/module admission, CSRF, Python service independence, list bounds and HTMX/no-JS security verified |
| X10 | Minimum accepted HR and Commerce flows demonstrated at 390/768/1280 with accessible keyboard/errors and no page overflow |
| X11 | Combined full PostgreSQL, classified SQLite, fresh migrations, lint/format/Django/drift/JS/Tailwind and exact-head hosted CI pass |
| X12 | Scope/dependency review confirms no Payroll, gateway, speculative framework, reverse imports, historical migration rewrite or Phase 4 work |
| X13 | Fresh independent final Phase 3 audit plus explicit formal acceptance/canonical closure; no self-approval or production-readiness inference |

## 13. Local proposal checks and next action

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

Smallest next action is a fresh independent PH3-0 architecture audit, followed by explicit owner
choices, not implementation. Remaining material ambiguities are D1–D10, exact public Sales batch
lock/validation API, optional bounded Inventory display API and final HR-0/ECOM-0 wire bounds/canonical
retry encodings. No unknown current
price/customer-portal API is treated as implemented. Phase 3 remains PROPOSED; HR and Ecommerce
NOT STARTED; no publication, acceptance, Phase 4 or deployment authorization is implied.
