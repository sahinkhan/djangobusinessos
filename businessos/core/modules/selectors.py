from .models import BusinessModule


class ModuleUnavailable(LookupError):
    pass


def is_module_enabled(code: str) -> bool:
    return BusinessModule.objects.filter(code=code, is_enabled=True).exists()


def require_module_enabled(code: str) -> None:
    if not is_module_enabled(code):
        raise ModuleUnavailable(f"Module {code!r} is not enabled.")


def enabled_module_codes() -> frozenset[str]:
    return frozenset(
        BusinessModule.objects.filter(is_enabled=True).values_list("code", flat=True)
    )
