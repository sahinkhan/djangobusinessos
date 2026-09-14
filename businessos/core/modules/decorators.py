from functools import wraps

from django.http import Http404

from .selectors import ModuleUnavailable, require_module_enabled


def module_required(code: str):
    """Return a request-time deployment module guard for a Django view."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            try:
                require_module_enabled(code)
            except ModuleUnavailable as exc:
                raise Http404("Module unavailable.") from exc
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
