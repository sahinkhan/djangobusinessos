from functools import wraps

from django.core.exceptions import BadRequest, ValidationError


def evidence_errors(view):
    """Translate expected compatibility/input failures at the optional HTTP boundary."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except ValidationError as exc:
            raise BadRequest(
                "Accounting evidence is unavailable or the request is invalid."
            ) from exc

    return wrapped
