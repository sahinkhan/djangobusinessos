# ADR 0004 — Phase 1 Party and Catalog Contract Freeze

Status: Accepted

Date: 2026-09-13

## Context

Phase 1 introduced the Party and variant-first Catalog primitives required by later transactional modules. The initial implementation was independently audited, its five findings were remediated, and commit `18a8cefeed30148ce7847908d7d82e7c570d79f9` received an independent technical PASS with no new blocking defect.

## Decision

Phase 1 is accepted and its public architecture contracts are frozen at audited implementation commit `18a8cefeed30148ce7847908d7d82e7c570d79f9`.

The frozen contracts are:

- Party is the authoritative company-scoped person/organization identity. Customer and supplier are roles on Party, not duplicate authoritative records.
- ContactMethod and Address belong to Party and retain explicit company scope.
- Product is the conceptual catalog identity.
- ProductVariant is the concrete sellable/purchasable SKU identity used by downstream transactional modules.
- A simple Product has exactly one default ProductVariant; a variable Product has one or more explicit ProductVariants.
- SKU uniqueness is scoped to company, and Catalog owns no authoritative stock quantity or transactional pricing workflow.
- New variant attribute assignments require active Attribute and AttributeValue records and serialize replacement per ProductVariant.
- Company-bound forms are an HTTP presentation safeguard. Business services remain framework-neutral and accept validated BusinessContext rather than HttpRequest.
- For Phase 1, validated company access grants operational Party/Catalog CRUD capability. Fine-grained reader/operator/administrator authorization is required before production exposure but is not part of the frozen Phase 1 schema.

Changes that break these contracts require an explicit later architecture decision, compatibility assessment, and migration/versioning plan. Routine backward-compatible fixes remain allowed.

## Verification basis

- PostgreSQL on Python 3.13.15: 56 tests passed.
- SQLite: 55 tests passed with one expected PostgreSQL row-lock skip.
- Ruff, Django system checks, and migration drift checks passed.
- Fresh PostgreSQL migration bootstrap passed and its disposable database was removed.
- Hosted CI run 12 passed for the audited commit.
- Local and remote `phase1-party-catalog` SHA matched during independent review.

## Consequences

Sales, Procurement, and Inventory may design their concrete item references around ProductVariant without reopening the Phase 1 identity model. Phase 2 does not start automatically; it still requires an explicit approved execution plan and instruction.

This acceptance is not production-launch approval. Fine-grained authorization and the previously recorded international deployment, security, recovery, monitoring, localization, and licensing gates remain open.
