from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BusinessContext:
    """Framework-neutral identity and organizational scope for a business operation."""

    actor_id: UUID
    company_id: UUID
    branch_id: UUID | None = None
    warehouse_id: UUID | None = None

    def __post_init__(self) -> None:
        for field_name in ("actor_id", "company_id"):
            value = getattr(self, field_name)
            if not isinstance(value, UUID):
                raise TypeError(f"{field_name} must be a UUID")
        for field_name in ("branch_id", "warehouse_id"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, UUID):
                raise TypeError(f"{field_name} must be a UUID")
