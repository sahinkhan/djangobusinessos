# ADR 0017 — Phase 3 People and Digital Commerce Boundaries

Status: **PROPOSED — FINAL ACCEPTANCE PENDING**. Owner decisions resolved locally;
implementation not authorized.

Date: 2026-10-14

Canonical Phase 2 base: `0d4a14254889ba1ec06cfb16088009177991d8d8`.

## Authority and gate boundary

The original checkpoint authorized planning, inspection and one local documentation commit.
The subsequent owner-decision checkpoint authorizes one further local documentation commit.
Publication, final umbrella acceptance, runtime work and production deployment remain separately
gated. ADRs 0001–0016 remain authoritative.
The decisions directory was inspected: 0016 was the highest allocated number; 0017 was unused.
No historical ADR is superseded by this proposal before explicit acceptance.

Phase 2 is canonically closed at the base above, with exact-head main CI #133, run
`38549126483`, SUCCESS, 3,015 PostgreSQL tests and the accepted 13/13 exit matrix. Those are
Phase 2 evidence, not executed Phase 3 tests. Historical acceptance-stage records remain intact.

The concrete proposed contract attachment is the
[Phase 3 execution plan](../exec-plans/active/PHASE_3_PEOPLE_DIGITAL_COMMERCE.md).
Its owner-decision register, mutation tables and acceptance matrices are part of this proposal,
not optional implementation guidance. All twelve owner policies below are resolved; detailed
HR-0/ECOM-0 technical contracts and final umbrella acceptance remain pending.

## Context: existing capabilities and gaps

The pinned repository contains Party, Catalog, Sales, Procurement, Inventory, Billing, Payments,
Accounting and the explicitly installed financial integrations. No HR or Ecommerce implementation
was found in the current tree or the bounded local reachable-history inspection recorded in the
plan. Roadmap names and the initial dependency graph are not implemented capabilities.

Party supplies company-owned person/organization identity, contacts and addresses. It does not
supply a private employee directory or a User-to-customer portal authorization boundary. Catalog
supplies ProductVariant identity, not a selling-price authority. Sales supplies company-owned
orders and explicit line prices, but no checkout retry binding, Branch field or public batch
creation operation. Inventory balance is not available-to-promise. Billing issue, payment recording,
allocation and Accounting posting are independent owner-controlled actions, not checkout side effects.

## Owner-resolved split and ownership — final contract acceptance pending

1. **Phase 3A / HR:** employment, departments, manually recorded attendance and explicit leave
   lifecycle. Party remains human/contact identity; User remains authentication identity. No payroll.
2. **Phase 3B / Ecommerce:** channel interaction state and durable cart-to-Sales conversion identity.
   Catalog owns items; Party owns customers; Sales owns commercial orders; Inventory owns posted
   stock; Billing owns invoices; Payments owns receipts/allocations; Accounting owns journal facts.

OD-7 resolves the first Commerce audience to authenticated **staff-assisted / internal**
browse/cart/checkout. Public anonymous storefront, guest checkout, customer self-login and
registration are excluded. Future customer/guest commerce requires a separate identity/admission
contract; ordinary Company access must never be handed to a shopper to make existing selectors work.

OD-1–OD-6 resolve HR to one stable Employee per Company/person Party, optional non-authorizing User
association, company-wide Department and optional current Employee Branch. Attendance supports
multiple completed sessions per local day with HR-owned append-only revisions; no daily record limit
or mutable daily summary authority. Leave is full calendar days with explicit submit/approve/reject/
cancel. HR uses a bounded PERSON projection without unnecessary contacts/addresses; existing Party
company-wide visibility is retained. No employment-episode, self-service, payroll or workflow engine.

## Owner-resolved dependency direction — final contract acceptance pending

Direct future manifest dependencies:

```text
hr        -> party, organization, reference, access
ecommerce -> party, catalog, sales, organization, reference, access
```

Core identity/common/audit/database/time/registry utilities remain infrastructure. No owner imports
HR or Ecommerce. HR and Ecommerce do not depend on one another. The proposed Ecommerce graph
refines the conservative future `ecommerce -> catalog, sales, billing` allowance: Billing is not
required for minimum Phase 3B completion under OD-11. Owner approval resolves this product-policy
distinction; the umbrella ADR itself still requires final acceptance.
See the owner-resolution section in the [dependency map](../architecture/DEPENDENCY_MAP.md).

OD-10 defers Inventory display and its bounded projection API entirely from initial ECOM-1.
OD-11/OD-12 exclude Billing and Payments from minimum Phase 3B completion. Accounting has no
checkout effect by existing owner architecture. Later approved
compositions must retain their owner APIs, dependency direction and distinct authorities. No eager
optional imports, direct cross-owner writes or automatic installation/enablement are permitted.

## Proposed Foundation and composition contract

- Framework-neutral BusinessContext, explicit Company scope, existing branch semantics and the
  selected execution alias; no tenant identity or SaaS activation.
- State changes and audit share `business_atomic` / `business_atomic_context()` on one alias.
  Lock active Company, check current RBAC, obtain domain/reference locks, then invoke the existing
  final permission guard immediately before effects and successful retries. Preserve Phase 2's
  complete ordered authority set; do not invent per-action authority caches or partial witness locks.
- HR owns its history and invariant enforcement; Core Audit records meaningful transitions and
  corrections, not the authoritative attendance ledger or every read.
- Registry enablement remains HTTP/navigation-only. Installed Python services still require
  context/RBAC, even with missing/disabled registry state; they do not require UI enablement.
- Cart conversion is one outer transaction, one immutable binding and one Sales DRAFT. A proposed
  bounded Sales public batch-create API validates/prelocks the complete order input before final
  authority acquisition. It does not exist at this base and must be accepted explicitly at ECOM-0;
  Ecommerce must not reach into private Sales persistence or reference-lock helpers.
- No automatic confirmation, stock deduction, invoice, receipt, allocation or journal. A retry
  recovers the existing order identity, never recreates or resets an order subsequently edited by Sales.
- Existing Django/Tailwind/HTMX/Alpine presentation and security conventions remain; no shell redesign.

## Owner-decision resolution checkpoint — 2026-10-14

Original proposal: `15e68828300f40c84165c86317217024f6b9d66d`, directly above the canonical base.
Its ten D1–D10 recommendations were unresolved at that checkpoint. The owner supplied the subsequent
independent audit result: **FINAL PASS — PHASE 3 UMBRELLA ARCHITECTURE APPROVED FOR OWNER-DECISION
RESOLUTION**, **Readiness A**, candidate-owned findings **P0: 0 / P1: 0 / P2: 0 / P3: 0**.
This records the supplied audit; this documentation task does not perform or manufacture that audit.

The owner explicitly authorized the following twelve authoritative product-policy decisions in the
resolution instruction. OD-5 supersedes D4's original one-interval-per-day recommendation; OD-10
defers the original optional Inventory display. The original proposal commit and plan chronology
retain the previous recommendations. Decisions were not settled retroactively.

| Decision | Resolved owner policy |
| --- | --- |
| OD-1 | One stable Employee per Company + same-company PERSON Party; Party owns names/contacts. Company-unique immutable employee number; no reassignment/reuse, simultaneous employment duplicates or rehire episodes |
| OD-2 | Optional unambiguous Company-local User association; no inferred identity or authority/access grants. No multiple active Employee identities represented ambiguously by one User; no self-service |
| OD-3 | Retain existing company-wide Party visibility; HR uses bounded PERSON identity projection and avoids unnecessary contact/address loading. Additional confidentiality requires separate Party-owner contract |
| OD-4 | Company-wide Department without branch/hierarchy/position/grade/cost-center engine; Employee has at most one optional current Branch; historical scope may be frozen |
| OD-5 | Zero/one/multiple completed sessions per local day, aware intervals/cross-midnight, frozen timezone/branch, overlap prevention and immutable retry-safe revisions. No open punch/shift/roster/break/device engine |
| OD-6 | Full calendar-day Leave only, bounded explicit lifecycle/cancellation, overlap/attendance conflict checks, timezone, retries and approval audit; no entitlement/payroll/workflow engine |
| OD-7 | Authenticated internal staff-assisted Commerce using existing Company/customer Party and exact permissions; no public/guest/customer login or registration |
| OD-8 | Authorized staff-entered Cart prices become Sales-owned line snapshots; no customer/client price authority or pricing/pricelist/promotion/coupon engine |
| OD-9 | One atomic DRAFT SalesOrder and all lines through a new public Sales-owned batch service; separate Sales confirmation; permanent unique Cart/CheckoutBinding retry identity |
| OD-10 | Inventory display, projection API, warehouse selection, ATP/reservation/backorder/allocation deferred from initial ECOM-1; Inventory remains sole stock authority |
| OD-11 | Billing and Sales-to-Billing integration not required for initial Phase 3B exit; no automatic Invoice; future integration separately gated |
| OD-12 | Payments collection, gateways, receipt/allocation creation and checkout payment status deferred; future adapters use Payments public contracts under separate approval |

**12/12 OWNER DECISIONS RESOLVED.** This records policy approval, not final ADR acceptance or
implementation authorization. A fresh independent final umbrella-contract acceptance audit must
review the resulting resolution commit. ADR 0017 remains Proposed.

### Technical contracts still to freeze

**TECHNICAL CONTRACT DETAIL — TO BE FROZEN AT HR-0:** exact Employee/Department/LeaveType fields,
number generation, User FK/cardinality mechanics, status and branch transfers, attendance session
and request identities/revision schema/overlap/locks/timezone/DST, leave fields/transition retry and
self-approval definition, twelve exact permission codes, audit, HTTP/UI and selected-alias rules.

**TECHNICAL CONTRACT DETAIL — TO BE FROZEN AT ECOM-0:** Cart/Line/Binding fields and revisions,
Currency policy, price permission, Variant/customer projections, canonical retry encoding/equality,
uniqueness/collision recovery, exact locks/final checks, public Sales batch signature/snapshots/
rollback, registry/RBAC and selected-alias HTTP/UI. The API is required by owner policy but is not
implemented or technically frozen here. Inventory display is not an ECOM-0 prerequisite.

## Delivery and acceptance

The original PH3-0 architecture review approved structure for owner-decision resolution. A fresh
final umbrella audit and separately authorized acceptance must follow this resolution checkpoint.
HR-0 and ECOM-0 then freeze their detailed contracts and permission vocabulary before separately authorized
HR-1 and ECOM-1 implementation. They may proceed in parallel only after the dependency/public-API
decisions are accepted and file ownership is isolated; canonical adoption remains sequential and
separately authorized. Do not merge competing histories or rebase under assumed authority.

Each implementation requires its own independent audit, exact-head hosted CI, acceptance and
canonical-adoption authorization. The plan defines H01–H18, E01–E20 and thirteen bounded Phase 3
exit criteria. No matrix is marked passed here. A final independent Phase 3 audit and formal closure
are separate gates; Phase 4 and production launch remain unauthorized.

## Consequences

The resolved policies reuse existing owners: multiple completed attendance sessions, no leave
entitlement calculation, no employee/customer self-service and authorized staff-entered prices.
Initial Commerce completes Cart/Checkout -> DRAFT SalesOrder without Inventory display or financial
effects. Phase 3 completion still requires both HR and minimum Ecommerce implementations to be
accepted; neither has started. Final independent umbrella acceptance remains pending.
No runtime, migration, manifest, permission registration or business test is changed by this ADR.
