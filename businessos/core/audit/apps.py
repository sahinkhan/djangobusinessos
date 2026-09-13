from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "businessos.core.audit"
    label = "business_audit"
    verbose_name = "Business audit"
