from django.apps import apps

from .execution import current_database_alias


class BusinessDatabaseRouter:
    """Route owned models only; technical/control-plane policy remains undecided."""

    @staticmethod
    def _owned(model):
        config = model._meta.app_config
        prefixes = ("businessos.core.", "businessos.modules.")
        if config is not None and config.name.startswith(prefixes):
            return True
        # Migration StateApps use label-only AppConfig stubs. Resolve ownership
        # from the installed namespace without rewriting historical RunPython.
        try:
            return apps.get_app_config(model._meta.app_label).name.startswith(prefixes)
        except LookupError:
            return False

    def db_for_read(self, model, **hints):
        return current_database_alias() if self._owned(model) else None

    def db_for_write(self, model, **hints):
        return current_database_alias() if self._owned(model) else None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Do not change the migration graph or choose technical table placement.
        return None
