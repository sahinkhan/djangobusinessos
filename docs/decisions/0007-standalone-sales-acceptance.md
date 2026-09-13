# ADR 0007 — Standalone Sales Acceptance

Status: Accepted

Date: 2026-09-14

## Context

Batch 2A introduced standalone Sales on `phase2-sales`. Independent technical and architecture
review accepted commit `7e5f5b407415d3b5b32188c94c4e9b4d7dd7a555` after the audit findings were
closed. The remaining completion gates were representative desktop/mobile visual QA and a
repository acceptance record.

Completion QA exercised the real customer -> draft order -> service ProductVariant line ->
confirmation workflow. Desktop behavior passed. Mobile QA found that a long generated order
number and the order-lines grid could widen the page beyond the viewport. Commit
`a79cb95d031bb38719bcdccfb5b14670cc76cd17` contains the responsive correction and regression
assertions without changing Sales domain or service contracts.

## Decision

Standalone Phase 2A Sales is accepted and closed at implementation commit
`a79cb95d031bb38719bcdccfb5b14670cc76cd17`.

The accepted contract is:

- Sales owns company-scoped `SalesOrder` and `SalesOrderLine` records.
- Customer identity is an active, company-scoped Party with the customer role.
- Each line references a concrete, active, sellable ProductVariant and stores historical item
  snapshots.
- The lifecycle is DRAFT -> CONFIRMED -> CANCELLED; confirmed content is immutable.
- State-changing use cases accept BusinessContext and serialize conflicting draft mutations with
  the persisted order row.
- Totals are derived from lines. Currency amounts follow Currency precision and `ROUND_HALF_UP`;
  unit prices retain four-decimal display precision.
- Sales confirmation creates no Inventory movement, invoice, payment, or Accounting entry.
- Deployment module gating controls Sales navigation and direct HTTP access.

Breaking these contracts requires a later explicit architecture decision and compatibility
assessment. Routine backward-compatible corrections remain allowed.

## Verification basis

- Independent PostgreSQL review at `7e5f5b407415d3b5b32188c94c4e9b4d7dd7a555`: 82 tests passed
  without the earlier connection-cleanup warning.
- Local post-QA-fix suite: 78 passed with four expected PostgreSQL-only concurrency skips; the
  focused Sales UI suite passed 5 tests.
- Ruff, Django system checks, and migration drift checks passed. The migration drift command
  reported no changes while warning that the local default PostgreSQL credentials were not
  available; schema verification remains covered by the independent PostgreSQL run and hosted CI.
- Tailwind CSS was rebuilt from source after the responsive template change.
- Hosted CI run 25 passed on exact commit
  `a79cb95d031bb38719bcdccfb5b14670cc76cd17`.
- Desktop QA at 1280x720 verified list, draft creation, service line creation, precision rendering,
  and confirmation.
- Mobile QA at 390x844 verified the navigation drawer, list, form, and confirmed detail. The final
  document scroll width matched its client width; the order-lines table remained locally
  scrollable where needed.
- The disposable QA database, user, and configuration were removed after verification.

## Consequences

The future `phase2-commercial-core` integration branch may consume the accepted standalone Sales
module without reopening its Batch 2A contract. Sales stays outside `main` until that planned
integration gate is executed.

This decision does not accept Procurement, Inventory, Billing, Accounting, optional integrations,
the full Phase 2 exit, or production launch readiness.
