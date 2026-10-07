from django.urls import path

from . import views

app_name = "payments"
urlpatterns = [
    path("receipts/", views.payment_list, name="list"),
    path("receipts/new/", views.payment_record, name="record"),
    path("receipts/<uuid:payment_id>/", views.payment_detail, name="detail"),
    path("methods/", views.method_list, name="methods"),
    path("methods/new/", views.method_form, name="method_create"),
    path("methods/<uuid:method_id>/edit/", views.method_form, name="method_edit"),
    path("methods/<uuid:method_id>/activity/", views.method_activity, name="method_activity"),
]
