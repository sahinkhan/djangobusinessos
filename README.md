# Django BusinessOS

BusinessOS is a modular business management platform that starts as a simple Django modular monolith and is designed to grow into a broader ERP/industry ecosystem without forcing premature platform complexity.

## Current status

Architecture foundation is defined. Phase 0 implementation has not started yet.

Read before coding:

- `AGENTS.md`
- `docs/architecture/BASELINE.md`
- `docs/architecture/MODULE_BOUNDARIES.md`
- `docs/architecture/DEPENDENCY_MAP.md`
- `docs/ROADMAP.md`
- `docs/exec-plans/active/PHASE_0_FOUNDATION.md`

## Initial product direction

The first product is intentionally simple:

- Django 5.2 LTS / Python 3.13
- PostgreSQL
- multi-company / branch / warehouse foundation
- modular business apps
- Django templates + Tailwind + HTMX + Alpine.js
- client-specific extensions outside standard modules
- business logic separated from Django request/presentation code

Initial business areas after foundation:

- Party / Contacts
- Catalog / Products
- Sales
- Procurement
- Inventory
- Billing
- Accounting
- HR
- Ecommerce
- School
- Hospital/Clinic
- Hotel

## Long-term direction

The architecture preserves a path toward:

- workflow/rules/scheduling
- metadata/Studio/dynamic UI
- documents/notifications/search/reporting/integrations
- enterprise horizontal modules
- industry verticals
- country localizations
- developer platform/marketplace
- self-hosted enterprise operations
- BusinessOS Cloud control plane
- LTS/compatibility/certification/partner ecosystem
- optional custom Python runtime if future evidence justifies replacing parts of Django

## Guiding rule

> Build capabilities late; reserve boundaries early.

BusinessOS prioritizes fast module delivery today without creating unnecessary rewrites tomorrow.
