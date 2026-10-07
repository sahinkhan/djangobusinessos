from django.urls import path

from . import views

app_name = "billing"
urlpatterns = [
    path("invoices/", views.invoice_list, name="list"),
    path("invoices/new/", views.invoice_create, name="create"),
    path("invoices/<uuid:invoice_id>/", views.invoice_detail_view, name="detail"),
    path("invoices/<uuid:invoice_id>/edit/", views.invoice_edit, name="edit"),
    path("invoices/<uuid:invoice_id>/issue/", views.invoice_issue, name="issue"),
    path("invoices/<uuid:invoice_id>/lines/new/", views.line_form, name="line_create"),
    path(
        "invoices/<uuid:invoice_id>/lines/<uuid:line_id>/edit/", views.line_form, name="line_edit"
    ),
    path(
        "invoices/<uuid:invoice_id>/lines/<uuid:line_id>/remove/",
        views.line_remove,
        name="line_remove",
    ),
]
