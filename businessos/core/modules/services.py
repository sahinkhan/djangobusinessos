from collections.abc import Mapping

from businessos.core.access.models import Permission
from businessos.core.database import business_atomic

from .manifest import validate_manifest
from .models import BusinessModule


@business_atomic
def register_manifest(value: Mapping, *, enabled: bool | None = None) -> BusinessModule:
    manifest = validate_manifest(value)
    defaults = {
        "name": manifest.name,
        "version": manifest.version,
        "dependencies": list(manifest.depends),
        "declared_permissions": list(manifest.permissions),
    }
    if enabled is not None:
        defaults["is_enabled"] = enabled
    module, _ = BusinessModule.objects.update_or_create(
        code=manifest.code,
        defaults=defaults,
    )
    for permission_code in manifest.permissions:
        Permission.objects.get_or_create(
            code=permission_code,
            defaults={"name": permission_code, "is_active": True},
        )
    return module
