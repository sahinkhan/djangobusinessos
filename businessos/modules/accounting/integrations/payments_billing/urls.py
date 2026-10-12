from django.urls import path

from . import views

app_name = "accounting_payments_billing"
urlpatterns = [
    path("allocations/<uuid:allocation_id>/", views.allocation_detail, name="detail"),
    path("allocations/<uuid:allocation_id>/post/", views.allocation_post, name="post"),
]
