from django.apps import apps
from django.contrib.auth import views as auth_views
from django.urls import include, path

from businessos.core.admin import businessos_admin_site
from businessos.core.views import home, select_company

billing_urlconf = "businessos.modules.billing.urls"
payments_urlconf = "businessos.modules.payments.urls"
if apps.is_installed("businessos.modules.payments.integrations.billing"):
    from businessos.modules.payments.integrations.billing.urls import (
        billing_urlpatterns,
        payments_urlpatterns,
    )

    billing_urlconf = (billing_urlpatterns, "billing")
    payments_urlconf = (payments_urlpatterns, "payments")

urlpatterns = [
    path("admin/", businessos_admin_site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("scope/company/", select_company, name="select_company"),
    path("parties/", include("businessos.modules.party.urls")),
    path("catalog/", include("businessos.modules.catalog.urls")),
    path("sales/", include("businessos.modules.sales.urls")),
    path("procurement/", include("businessos.modules.procurement.urls")),
    path("inventory/", include("businessos.modules.inventory.urls")),
    path("billing/", include(billing_urlconf)),
    path("payments/", include(payments_urlconf)),
    path("accounting/", include("businessos.modules.accounting.urls")),
    path("", home, name="home"),
]
if apps.is_installed("businessos.modules.payments.integrations.billing"):
    urlpatterns += [
        path(
            "payments/allocations/",
            include("businessos.modules.payments.integrations.billing.urls"),
        )
    ]
