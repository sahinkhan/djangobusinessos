from django.urls import path

from . import views

app_name = "accounting_billing"
urlpatterns = [path("invoices/<uuid:invoice_id>/post/", views.invoice_post, name="post")]
