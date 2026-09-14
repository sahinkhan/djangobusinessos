# ADR 0009 — Core Foundation v1 Contract

Status: Proposed — implemented; independent audit pending

Date: 2026-09-14

## Context

Phase 1 and the accepted standalone Phase 2 work exposed shared requirements that the original
minimal foundation deliberately deferred: business permissions, auditable security changes,
explicit access revocation, company jurisdiction/time semantics and stable reference identities.
These must be resolved before Billing and Accounting introduce financially significant workflows.

ADR numbers 0007 and 0008 are reserved by the accepted standalone Sales and Procurement branches.
This Core decision therefore uses 0009 even though those branches are not merged here.

## Decision

### Business authorization

Core Access owns a minimal RBAC model: `Permission`, company-owned `Role`, `RolePermission` and
company-scoped `UserRoleAssignment`. Authorization validates `BusinessContext` and organizational
scope first, then evaluates active roles and permissions. Missing grants deny by default.

Superusers bypass RBAC grants only. They do not bypass actor/company validity or branch/warehouse
ownership integrity, permission-code validation, permission identity existence or permission
retirement. An active registered Permission must exist before any superuser grant bypass applies.

Django groups, Django model permissions and `user.has_perm()` remain technical/admin mechanisms.
They are not authoritative for BusinessOS business actions.

### Permission ownership

Business modules own permission vocabulary in `module.resource.action` form and declare it through
their module manifest. Registration is deterministic and retry-safe. A later manifest that omits a
previous permission does not delete or deactivate its identity or existing role links; retirement
requires an explicit future operation.

Core Access deterministically bootstraps `access.organization.manage` and `access.role.manage` as
active permission identities through a forward data migration. Re-registration preserves an
explicitly retired permission rather than silently reactivating it.

### Organizational grants and roles

Organizational access defines where a user may operate. RBAC defines what the user may do there.
Grant/revoke services are explicit and atomic. Revoking company access removes subordinate branch,
warehouse and role assignments so re-grant cannot resurrect stale authority.

The deployment Django admin exposes Access/RBAC records for inspection only. It cannot add, change
or delete those records; audited Access application services and module permission registration are
the supported mutation paths.

### Audit

Core Audit stores append-only facts with actor, optional company, action, object type/id, timestamp
and small JSON metadata. Normal instance and queryset update/delete paths reject mutation. Audit is
evidence only, not event sourcing and not a source of truth for business state.

The initial audited actions include organizational grants/revocations, role assignment/revocation
and role-permission changes.

### Company identity and time

Company has Country, base Currency, validated IANA timezone and default Language. Normal mutation
cannot change base currency after creation. Database timestamps remain timezone-aware UTC; shared
helpers convert an aware instant to Company-local datetime/date.

The forward migration maps pre-existing companies without these fields to ISO user-assigned
country `ZZ` and BCP 47 undetermined language `UND`. Operators must replace those explicit unknown
references through a supported company update before relying on jurisdiction/language behavior.

### Stable reference identities

`Country.code`, `Currency.code`, `Language.code`, `UnitOfMeasure.code` and BusinessOS permission
codes are immutable after creation through normal model paths. Labels may be corrected and obsolete
references are retired with `is_active=False`.

## Exclusions

This decision does not add ABAC, role inheritance, record/field ACLs, approval workflow, MFA, SSO,
tenancy, event sourcing, event infrastructure, service accounts, scheduling, currency conversion,
Redis/Celery, Go services or a custom framework.

It does not normalize migration or Git history and does not merge Phase 2 branches.

## Gate

The implementation remains a candidate until independent Gate 2 audit passes. Only that audit may
promote this ADR to Accepted and mark Core Foundation v1 FROZEN. Gate 3 history normalization needs
separate explicit authorization after acceptance.
