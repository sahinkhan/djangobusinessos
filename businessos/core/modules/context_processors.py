from .selectors import enabled_module_codes


def module_navigation(request):
    codes = enabled_module_codes() if request.user.is_authenticated else frozenset()
    return {"enabled_module_codes": codes}
