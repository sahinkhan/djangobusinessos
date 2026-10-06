from contextlib import contextmanager
from contextvars import ContextVar

from django.db import connections
from django.utils.connection import ConnectionDoesNotExist

_database_alias = ContextVar("businessos_database_alias", default="default")
_atomic_alias = ContextVar("businessos_atomic_alias", default=None)


def current_database_alias() -> str:
    return _database_alias.get()


@contextmanager
def database_execution(alias: str):
    """Select a configured alias for this execution only; never fall back on error.

    This does not resolve tenants, open connections, or authorize a business action.
    Switching databases during a business transaction is deliberately unsupported.
    """
    if not isinstance(alias, str) or not alias:
        raise ValueError("A non-empty database alias is required.")
    if alias not in connections:
        raise ConnectionDoesNotExist(f"The connection {alias!r} doesn't exist.")
    pinned = _atomic_alias.get()
    if pinned is not None and pinned != alias:
        raise ValueError("Cannot switch databases inside a business transaction.")
    token = _database_alias.set(alias)
    try:
        yield
    finally:
        _database_alias.reset(token)
