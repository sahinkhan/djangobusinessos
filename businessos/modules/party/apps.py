from django.apps import AppConfig


class PartyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "businessos.modules.party"
    label = "party"
    verbose_name = "Party"
