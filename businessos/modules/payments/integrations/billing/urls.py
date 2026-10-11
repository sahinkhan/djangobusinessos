from django.urls import path

from businessos.modules.billing.urls import urlpatterns as billing_patterns
from businessos.modules.payments.urls import urlpatterns as payments_patterns

from . import views

app_name = "payments_billing"
urlpatterns = [path("new/", views.allocation_create, name="create")]

# Explicit optional presentation composition, not owner imports of this app.
# All other owner routes and their ordinary permission contracts stay intact.
billing_urlpatterns = [
    path("invoices/<uuid:invoice_id>/", views.invoice_parent_detail, name="detail"),
    *(pattern for pattern in billing_patterns if pattern.name != "detail"),
]
payments_urlpatterns = [
    path("receipts/<uuid:payment_id>/", views.payment_parent_detail, name="detail"),
    *(pattern for pattern in payments_patterns if pattern.name != "detail"),
]
