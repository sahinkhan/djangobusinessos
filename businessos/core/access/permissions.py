import re

PERMISSION_CODE_PATTERN = re.compile(
    r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$"
)

CORE_PERMISSION_DECLARATIONS = (
    ("access.organization.manage", "Manage organizational access"),
    ("access.role.manage", "Manage BusinessOS roles"),
)


def validate_permission_code(code: str) -> None:
    if not isinstance(code, str) or not PERMISSION_CODE_PATTERN.fullmatch(code):
        raise ValueError("Permission codes must use the lowercase module.resource.action format.")
