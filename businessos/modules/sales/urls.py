from django.urls import path

from . import views

app_name = "sales"

urlpatterns = [
    path("orders/", views.order_list, name="order_list"),
    path("orders/new/", views.order_create, name="order_create"),
    path("orders/<uuid:order_id>/", views.order_detail_view, name="order_detail"),
    path("orders/<uuid:order_id>/edit/", views.order_edit, name="order_edit"),
    path("orders/<uuid:order_id>/confirm/", views.order_confirm, name="order_confirm"),
    path("orders/<uuid:order_id>/cancel/", views.order_cancel, name="order_cancel"),
    path("orders/<uuid:order_id>/lines/new/", views.line_create, name="line_create"),
    path(
        "orders/<uuid:order_id>/lines/<uuid:line_id>/edit/",
        views.line_edit,
        name="line_edit",
    ),
    path(
        "orders/<uuid:order_id>/lines/<uuid:line_id>/remove/",
        views.line_remove,
        name="line_remove",
    ),
]
