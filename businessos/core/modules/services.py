from collections.abc import Mapping

from .manifest import validate_manifest
from .models import BusinessModule


def register_manifest(value: Mapping, *, enabled: bool | None = None) -> BusinessModule:
    manifest = validate_manifest(value)
    defaults = {
        "name": manifest.name,
        "version": manifest.version,
        "dependencies": list(manifest.depends),
    }
    if enabled is not None:
        defaults["is_enabled"] = enabled
    module, _ = BusinessModule.objects.update_or_create(
        code=manifest.code,
        defaults=defaults,
    )
    return module
