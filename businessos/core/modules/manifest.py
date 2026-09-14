import re
from collections.abc import Mapping
from dataclasses import dataclass

from businessos.core.access.permissions import validate_permission_code

MODULE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
SEMANTIC_VERSION_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@dataclass(frozen=True, slots=True)
class ModuleManifest:
    code: str
    name: str
    version: str
    depends: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()


def validate_manifest(value: Mapping) -> ModuleManifest:
    required = {"code", "name", "version", "depends"}
    allowed = required | {"permissions"}
    missing = required - value.keys()
    unknown = value.keys() - allowed
    if missing:
        raise ValueError(f"Missing manifest fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"Unknown manifest fields: {', '.join(sorted(unknown))}")

    code = value["code"]
    name = value["name"]
    version = value["version"]
    depends = value["depends"]
    permissions = value.get("permissions", ())
    if not isinstance(code, str) or not MODULE_CODE_PATTERN.fullmatch(code):
        raise ValueError("Module code must be lowercase letters, numbers, or underscores.")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Module name is required.")
    if not isinstance(version, str) or not SEMANTIC_VERSION_PATTERN.fullmatch(version):
        raise ValueError("Module version must use semantic versioning.")
    if not isinstance(depends, (list, tuple)) or any(
        not isinstance(item, str) or not MODULE_CODE_PATTERN.fullmatch(item) for item in depends
    ):
        raise ValueError("Module dependencies must be valid module codes.")
    if code in depends:
        raise ValueError("A module cannot depend on itself.")
    if len(depends) != len(set(depends)):
        raise ValueError("Module dependencies must be unique.")
    if not isinstance(permissions, (list, tuple)):
        raise ValueError("Module permissions must be a list or tuple.")
    for permission_code in permissions:
        validate_permission_code(permission_code)
    if any(not item.startswith(f"{code}.") for item in permissions):
        raise ValueError("A module may declare only permission codes in its own namespace.")
    if len(permissions) != len(set(permissions)):
        raise ValueError("Module permissions must be unique.")
    return ModuleManifest(
        code=code,
        name=name.strip(),
        version=version,
        depends=tuple(depends),
        permissions=tuple(sorted(permissions)),
    )
