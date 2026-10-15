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

if apps.is_installed("businessos.modules.accounting.integrations.billing"):
    from businessos.modules.accounting.integrations.billing.views import invoice_detail
    from businessos.modules.billing.urls import urlpatterns as invoice_patterns

    billing_urlconf = (
        [
            path("invoices/<uuid:invoice_id>/", invoice_detail, name="detail"),
            *(pattern for pattern in invoice_patterns if pattern.name != "detail"),
        ],
        "billing",
    )
if apps.is_installed("businessos.modules.accounting.integrations.payments_billing"):
    from businessos.modules.accounting.integrations.payments_billing.views import payment_detail
    from businessos.modules.payments.urls import urlpatterns as receipt_patterns

    payments_urlconf = (
        [
            path("receipts/<uuid:payment_id>/", payment_detail, name="detail"),
            *(pattern for pattern in receipt_patterns if pattern.name != "detail"),
        ],
        "payments",
    )

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
    path("hr/", include("businessos.modules.hr.urls")),
    path("", home, name="home"),
]
if apps.is_installed("businessos.modules.payments.integrations.billing"):
    urlpatterns += [
        path(
            "payments/allocations/",
            include("businessos.modules.payments.integrations.billing.urls"),
        )
    ]
if apps.is_installed("businessos.modules.accounting.integrations.billing"):
    urlpatterns += [
        path(
            "accounting/invoice-outcomes/",
            include("businessos.modules.accounting.integrations.billing.urls"),
        )
    ]
if apps.is_installed("businessos.modules.accounting.integrations.payments_billing"):
    urlpatterns += [
        path(
            "accounting/allocation-outcomes/",
            include("businessos.modules.accounting.integrations.payments_billing.urls"),
        )
    ]
