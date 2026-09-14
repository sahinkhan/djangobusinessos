from collections.abc import Mapping

from businessos.core.common.context import BusinessContext

from .models import AuditEntry


def record_audit_entry(
    *,
    context: BusinessContext,
    action: str,
    object_type: str,
    object_id,
    metadata: Mapping | None = None,
) -> AuditEntry:
    """Append one audit fact; callers validate authorization before recording it."""
    return AuditEntry.objects.create(
        actor_id=context.actor_id,
        company_id=context.company_id,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        metadata=dict(metadata or {}),
    )
