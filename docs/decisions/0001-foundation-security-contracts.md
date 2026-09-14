# ADR 0001 — Foundation security and ownership contracts

## Status

Accepted for Phase 0 architecture review

## Context

Phase 0 needs predictable identity and organizational isolation before business modules depend on these records. Django model permissions are deployment-wide and do not by themselves enforce company scope.

## Decisions

### Administration boundary

The Django admin is a deployment-wide maintenance surface reserved for active superusers. Staff status and model permissions do not grant access to it. Company-scoped operational administration must use future application views and selectors that validate `BusinessContext`; the Django admin is not that surface.

### Email identity

Login email is one case-insensitive identity. It is stored trimmed and lowercase, normalized by manager, model, and admin form paths, authenticated case-insensitively, and protected by a database constraint over `LOWER(email)`.

### Organizational ownership

The company owner of a Branch or Warehouse is immutable after creation. A correction or transfer requires a deliberate future service and migration design; direct reassignment is rejected. A Warehouse may change its optional Branch only to a Branch in the same company.

Disabling a Branch does not silently mutate its Warehouses. An active Warehouse linked to an inactive Branch is unavailable as a valid business context until the Branch is reactivated or the Warehouse is reassigned/deactivated.

#### Core Foundation v1 compatibility refinement

The preceding activity semantics record the original Phase 0 decision. ADR 0009 later refined the
supported mutation contract: an active Warehouse cannot belong to an inactive Branch, and active
Warehouses must be deactivated or reassigned before their Branch can be deactivated. Legacy or
corrupt inconsistent data remains unavailable and is denied by `BusinessContext` validation. All
other decisions in this ADR remain in effect.

### Context and grants

Every `BusinessContext` requires UUID actor and company identifiers. Optional branch and warehouse identifiers must also be UUIDs when present. Existence, active state, and organizational relationships are validated independently of authorization; superusers bypass grant checks only, never scope-integrity checks.

An omitted Branch means the operation is company-wide, subject to the selected Warehouse and the caller's explicit grants. A company-level Warehouse with no Branch remains valid when a Branch is selected because its ownership is company-wide.

HTTP adapters only parse request/session state. Both HTTP and non-HTTP callers use `validate_business_context(context)` for the same scope and grant checks before protected business services execute.

### Module registry enablement

Manifest registration updates identity, version, and dependencies. Omitting the `enabled` argument preserves existing database enablement; a new module defaults to disabled. Callers must pass `enabled=True` or `False` to change state deliberately.

## Consequences

- Core admin access is intentionally narrower than ordinary Django staff permissions.
- Company ownership changes require a future explicit workflow rather than generic model editing.
- Database migrations must detect pre-existing case-insensitive email collisions before adding the identity constraint.
- Business modules have one reusable non-request access-policy entry point.
