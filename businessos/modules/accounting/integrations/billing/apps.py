from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured


class AccountingBillingConfig(AppConfig):
    name = "businessos.modules.accounting.integrations.billing"
    label = "accounting_billing"
    verbose_name = "Invoice Accounting"

    def ready(self):
        for owner in ("accounting", "billing"):
            if not apps.is_installed(f"businessos.modules.{owner}"):
                raise ImproperlyConfigured(f"accounting_billing requires {owner}.")
