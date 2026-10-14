# ADR 0017 — Phase 3 People and Digital Commerce Boundaries

Status: **PROPOSED — NOT ACCEPTED**. Local architecture proposal only.

Date: 2026-10-14

Canonical Phase 2 base: `0d4a14254889ba1ec06cfb16088009177991d8d8`.

## Authority and gate boundary

The owner authorized planning, inspection and one local documentation commit, not runtime work,
publication, contract acceptance or production deployment. ADRs 0001–0016 remain authoritative.
The decisions directory was inspected: 0016 was the highest allocated number; 0017 was unused.
No historical ADR is superseded by this proposal before explicit acceptance.

Phase 2 is canonically closed at the base above, with exact-head main CI #133, run
`38549126483`, SUCCESS, 3,015 PostgreSQL tests and the accepted 13/13 exit matrix. Those are
Phase 2 evidence, not executed Phase 3 tests. Historical acceptance-stage records remain intact.

The concrete proposed contract attachment is the
[Phase 3 execution plan](../exec-plans/active/PHASE_3_PEOPLE_DIGITAL_COMMERCE.md).
Its owner-decision register, mutation tables and acceptance matrices are part of this proposal,
not optional implementation guidance. Unresolved choices block their respective implementation gate.

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

## Proposed split and ownership

1. **Phase 3A / HR:** employment, departments, manually recorded attendance and explicit leave
   lifecycle. Party remains human/contact identity; User remains authentication identity. No payroll.
2. **Phase 3B / Ecommerce:** channel interaction state and durable cart-to-Sales conversion identity.
   Catalog owns items; Party owns customers; Sales owns commercial orders; Inventory owns posted
   stock; Billing owns invoices; Payments owns receipts/allocations; Accounting owns journal facts.

The recommended first Commerce slice is authenticated **staff-assisted** browse/cart/checkout,
not a public self-service shop. This is a material owner decision, not a claim that an internal
screen satisfies an unapproved public-commerce requirement. If public/guest checkout is required,
ECOM-0 must first specify a customer identity/admission and price-offer contract; ordinary Company
access must never be handed to a shopper to make existing selectors work.

Recommended HR semantics, subject to decisions D1–D5: one Employee per Company/Party, required
person Party, optional non-authorizing User link; company-wide Department; one completed attendance
interval per company-local start date with HR-owned append-only revisions; full-day LeaveRequest
with explicit submit/approve/reject/cancel, no quotas or approval engine. Party-visible contact data
is not made confidential by adding HR RBAC.

## Proposed dependency refinement

Direct future manifest dependencies:

```text
hr        -> party, organization, reference, access
ecommerce -> party, catalog, sales, organization, reference, access
```

Core identity/common/audit/database/time/registry utilities remain infrastructure. No owner imports
HR or Ecommerce. HR and Ecommerce do not depend on one another. The proposed Ecommerce graph
refines the conservative future `ecommerce -> catalog, sales, billing` allowance: Billing is not
required to place a draft Sales order. This change requires acceptance, not silent graph substitution.
See the proposed section in the [dependency map](../architecture/DEPENDENCY_MAP.md).

Inventory availability display is an optional read-only composition, separately enabled and
authorized. Billing/Payments/Accounting have **no initial checkout effect**. Later approved
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

## Decisions and alternatives requiring owner acceptance

The plan's D1–D10 register explicitly covers identity/cardinality/privacy, Department and branch
scope, attendance granularity/history, leave policy, assisted versus public customer access, explicit
staff price entry, conversion/batch API, optional stock display and deferred financial effects.
Recommendations are concrete so they can be reviewed, but **none is recorded as owner-accepted**.

Rejected as this proposal's default: duplicate employee/customer identity; public customers with ERP
Company access; Product-owned pricing engine; a second Ecommerce Order; automatic financial/stock
effects; Payroll; generic workflow/events; a new tenancy/runtime framework. These alternatives would
need a separate bounded contract rather than implementation improvisation.

## Delivery and acceptance

PH3-0 independent architecture review precedes explicit umbrella acceptance. HR-0 and ECOM-0 then
resolve/freeze their respective contracts and permission vocabulary before separately authorized
HR-1 and ECOM-1 implementation. They may proceed in parallel only after the dependency/public-API
decisions are accepted and file ownership is isolated; canonical adoption remains sequential and
separately authorized. Do not merge competing histories or rebase under assumed authority.

Each implementation requires its own independent audit, exact-head hosted CI, acceptance and
canonical-adoption authorization. The plan defines H01–H18, E01–E20 and thirteen bounded Phase 3
exit criteria. No matrix is marked passed here. A final independent Phase 3 audit and formal closure
are separate gates; Phase 4 and production launch remain unauthorized.

## Consequences

The proposal reuses existing owners and avoids unsupported storefront security or finance promises.
Its deliberate limits are one daily attendance interval, no leave entitlement calculation, no
employee/customer self-service and no authoritative online price/stock offer. Those limits need
product-owner agreement before implementation; rejecting them reopens the relevant contract only.
No runtime, migration, manifest, permission registration or business test is changed by this ADR.
