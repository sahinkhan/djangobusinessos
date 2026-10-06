from contextlib import contextmanager
from functools import wraps
from inspect import iscoroutinefunction

from django.db import transaction

from .execution import _atomic_alias, current_database_alias, database_execution


@contextmanager
def business_atomic_context(*, using=None):
    """Resolve at ENTER time, preserving Django's normal savepoint semantics.

    Explicit model/queryset aliases also scope validation/related reads. Nested
    operations must use the same alias; this is not a distributed transaction.
    """
    alias = current_database_alias() if using is None else using
    with database_execution(alias):
        token = _atomic_alias.set(alias)
        try:
            with transaction.atomic(using=alias):
                yield
        finally:
            _atomic_alias.reset(token)


def business_atomic(function):
    """Decorate synchronous business operations; resolve the alias on every call."""
    if iscoroutinefunction(function):
        raise TypeError("Business transactions require a synchronous execution boundary.")

    @wraps(function)
    def wrapped(*args, **kwargs):
        with business_atomic_context():
            return function(*args, **kwargs)

    return wrapped
