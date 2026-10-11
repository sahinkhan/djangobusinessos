from django.apps import AppConfig, apps
from django.core.exceptions import ImproperlyConfigured


class PaymentsBillingConfig(AppConfig):
    name = "businessos.modules.payments.integrations.billing"
    label = "payments_billing"
    verbose_name = "Payments / Billing allocations"

    def ready(self):
        if not all(
            apps.is_installed(f"businessos.modules.{owner}") for owner in ("billing", "payments")
        ):
            raise ImproperlyConfigured(
                "payments_billing requires installed Billing and Payments owners."
            )
