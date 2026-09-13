from .base import *  # noqa: F403

# Worker-thread database connections must close immediately so PostgreSQL test
# databases can be removed deterministically after concurrency tests.
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405
ALLOWED_HOSTS = ALLOWED_HOSTS or ["localhost", "127.0.0.1"]  # noqa: F405
