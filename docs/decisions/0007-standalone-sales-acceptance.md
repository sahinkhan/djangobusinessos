# ADR 0007 — Standalone Sales Acceptance

Status: Accepted — historical closure preserved; post-closure remediation formally accepted

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

Independent re-audit gave Gate 4A FINAL PASS after remediation implementation
`d62c34e36f0a8b11f59bfdb058143e27f5231c5d` closed the initial findings. The formally accepted
candidate is `23338f1cfed11d21d4fa8fd7e92f8de120450977` on `gate4a-sales-adoption`. Hosted CI run #48
succeeded against that exact candidate with fresh PostgreSQL migrations, 283 tests, Ruff, Django
checks, migration-drift checks, `npm ci`, and Tailwind reproducibility all passing.

This decision preserves the initial BLOCKED audit at `fc609bcd81916c13921c2d1cc7b6a59eda1c1e19`
and its remediation history. The accepted candidate was recorded in documentation-only commit
`e0c848f34da0bce9b9c6e010a396026ac5889cf4`, which was then adopted into canonical `main` by a
normal fast-forward. Hosted CI
[run #50](https://github.com/sahinkhan/djangobusinessos/actions/runs/34871467184) succeeded against
that exact adopted checkpoint. Gate 4A is accepted, adopted, and closed.

Procurement and Inventory adoption, Billing, Accounting, and optional integrations remain
unauthorized. This closure changes no reviewed Sales business code, tests, migrations,
configuration, or frontend assets.

## Post-closure corrective status

An independent adversarial audit after the historical Gate 4A closure returned REVISE for four
narrow findings:

- a persisted confirmed/cancelled line could be deleted after substituting a different draft
  parent only on the mutable in-memory instance;
- SKU/name-only snapshot refreshes could change the Sales document without recording the
  canonical `sales.order.updated` audit action;
- a valid unbroken customer name or maximum supported total could overflow the Sales detail
  document;
- non-finite quantity or unit-price Decimal values could escape canonical field-specific
  `ValidationError` handling.

Post-closure corrective implementation `f9092cebe2f27504c0f3dfc772524645e25c1f91` derives line
deletion authority from persisted ownership under the aggregate lock, compares every mutable
business snapshot field for audit purposes, adds Sales-local document containment, and rejects
non-finite quantities/prices before ordering comparisons. The remediation is isolated on
`gate4a-sales-postclosure-remediation`. Final corrective candidate
`b34a98a1f47c7d0c526fa4dbd60207d5123f9fe3` passed exact-head hosted CI
[#74](https://github.com/sahinkhan/djangobusinessos/actions/runs/34961977826) with 437 PostgreSQL
tests, Ruff, Django checks, migration drift, `npm ci`, Tailwind, and CSS reproducibility passing.
Independent Sales corrective re-audit returned FINAL PASS.

The historical standalone and Gate 4A acceptance/adoption/closure records remain valid evidence,
including historical closure `fb9028bbbec5dfc56e7d579c3c351abcde764833` and the later REVISE
finding sequence. The corrective candidate is formally accepted but is not yet adopted into
`main` or re-closed. The current frozen Sales foundation scope is complete. Future Sales
extensions—including quotation, tax, discounts/promotions, shipment/delivery, returns/RMA,
credit notes, commissions, CRM, Inventory reservation, Billing, and POS/E-commerce integration—
remain open and separately governed. Procurement, Billing, Accounting, integrations, and
deployment are outside this corrective execution.
