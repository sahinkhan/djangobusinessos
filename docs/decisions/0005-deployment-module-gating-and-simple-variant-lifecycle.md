# ADR 0005 — Deployment Module Gating and Simple Variant Lifecycle

Status: Accepted

Date: 2026-09-13

## Context

The Phase 1 freeze left two operational contracts incomplete. `BusinessModule.is_enabled` was persisted but did not affect the user-facing application, and the generic ProductVariant update service could edit the sole variant of a simple Product independently of its Product lifecycle.

## Decision

### Deployment module state

`BusinessModule.is_enabled` controls whether an installed module is available on this BusinessOS deployment's user-facing application surface.

- A missing registry row is disabled.
- A registry row with `is_enabled=False` is disabled.
- A registry row with `is_enabled=True` is enabled.
- Disabled Party and Catalog modules are omitted from shared navigation and their direct HTTP views return 404 at request time.
- Django applications and URL patterns remain installed and statically configured. No database query occurs while importing the root URL configuration.

This flag does not install or uninstall code, load or unload Django applications, reverse migrations, resolve dependencies, grant per-company licenses, or implement marketplace behavior.

### Simple Product variant lifecycle

The Product-level service owns the SKU and activity lifecycle of the sole variant of a simple Product.

- Product service updates synchronize Product activity with the default variant.
- The generic ProductVariant update service rejects variants belonging to simple Products.
- Normal ProductVariant model saves require a simple variant to remain default and to match its Product activity.
- Variable Product variants remain editable through ProductVariant services.

No signal or hidden workflow orchestration is introduced.

## Consequences

Deployment operators may expose or hide installed Party and Catalog surfaces through explicit registry state without claiming dynamic plugin lifecycle support. Non-HTTP business services remain installed Python APIs; callers continue to enforce their existing BusinessContext and authorization contracts.

Simple Product callers have one unambiguous lifecycle entry point, while downstream modules continue to reference ProductVariant as the transactional SKU identity.

The explicit `seed_phase1_demo` command creates representative Phase 1 data in a deterministic DEMO company and enables Party and Catalog for that deliberately requested demo setup. It is not invoked by migrations or production startup.

Phase 2 remains outside this decision.
