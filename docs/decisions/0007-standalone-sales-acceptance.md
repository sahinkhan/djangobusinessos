# ADR 0007 — Standalone Sales Acceptance

Status: Accepted for the historical standalone implementation; canonical Gate 4A adoption pending

Date: 2026-09-14

## Context

Batch 2A introduced standalone Sales on the preserved `phase2-sales` branch. Independent technical
and architecture review accepted the implementation after its original audit findings were closed.
Representative desktop/mobile QA then found and closed narrow responsive overflow defects.

The Gate 3 canonical reconstruction deliberately did not adopt Phase 2. Gate 4A now replays the
accepted Sales behavior onto Core Foundation v1. The initial canonical implementation
`28c8028950be1997b4f3d0816b1ec04764222068` and audit head
`fc609bcd81916c13921c2d1cc7b6a59eda1c1e19` were blocked by independent audit pending Sales-local
bulk-write/delete hardening, missing transition concurrency coverage, module-gating contract
reconciliation, and restoration of canonical Phase 2 documentation.

## Historical decision

Standalone Phase 2A Sales remains historically accepted and closed at implementation commit
`a79cb95d031bb38719bcdccfb5b14670cc76cd17`.

The accepted behavior is:

- Sales owns company-scoped `SalesOrder` and `SalesOrderLine` records.
- Customer identity is an active, company-scoped Party with the customer role.
- Each line references an active, sellable ProductVariant and stores historical SKU/name/
  description snapshots.
- The lifecycle is DRAFT -> CONFIRMED -> CANCELLED; confirmed and cancelled content is immutable.
- State-changing use cases accept `BusinessContext` and serialize conflicting draft mutations.
- Totals are line-derived. Currency totals use Currency precision and `ROUND_HALF_UP`; unit prices
  retain four-decimal display precision.
- Confirmation creates no Inventory movement, invoice, payment, or Accounting entry.
- Deployment module gating controls Sales navigation and HTTP access only. It does not disable
  installed non-HTTP Python services, which still require valid context and RBAC permission.

Breaking these contracts requires an explicit architecture decision and compatibility assessment.

## Historical verification basis

- Independent PostgreSQL review at `7e5f5b407415d3b5b32188c94c4e9b4d7dd7a555`: 82 passed.
- Responsive correction and regression assertions:
  `a79cb95d031bb38719bcdccfb5b14670cc76cd17`.
- Hosted CI run 25 passed on that exact implementation.
- Desktop 1280x720 and mobile 390x844 QA covered list, forms, service-variant line creation,
  precision rendering, confirmation, mobile navigation, and local table overflow.

## Canonical Gate 4A status

This ADR does not accept or close the canonical Gate 4A adoption. Remediation implementation
`d62c34e36f0a8b11f59bfdb058143e27f5231c5d` remains isolated on
`gate4a-sales-adoption` and requires exact-head hosted CI plus independent re-audit.

Canonical `main` remains `f2d48c1d1a6f12c7b27c925e2c6f14f922d53beb`. Procurement and
Inventory adoption, Billing, Accounting, optional integrations, and merge to `main` remain
unauthorized.
