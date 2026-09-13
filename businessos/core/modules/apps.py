from django.apps import AppConfig


class ModulesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "businessos.core.modules"
    label = "module_registry"
    verbose_name = "Module registry"
