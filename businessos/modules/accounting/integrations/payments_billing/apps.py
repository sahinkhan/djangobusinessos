from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured


class AccountingPaymentsBillingConfig(AppConfig):
    name = "businessos.modules.accounting.integrations.payments_billing"
    label = "accounting_payments_billing"
    verbose_name = "Allocation Accounting"

    def ready(self):
        for owner in (
            "businessos.modules.accounting",
            "businessos.modules.accounting.integrations.billing",
            "businessos.modules.payments.integrations.billing",
        ):
            if not apps.is_installed(owner):
                raise ImproperlyConfigured(f"accounting_payments_billing requires {owner}.")
