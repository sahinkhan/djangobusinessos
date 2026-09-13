from django.urls import path

from . import views

app_name = "inventory"
urlpatterns = [
    path("movements/", views.movement_list, name="list"),
    path("movements/new/", views.movement_create, name="create"),
    path("movements/<uuid:movement_id>/", views.movement_detail_view, name="detail"),
    path("movements/<uuid:movement_id>/edit/", views.movement_edit, name="edit"),
    path("movements/<uuid:movement_id>/post/", views.movement_post, name="post"),
    path("movements/<uuid:movement_id>/lines/new/", views.line_create, name="line_create"),
    path(
        "movements/<uuid:movement_id>/lines/<uuid:line_id>/edit/", views.line_edit, name="line_edit"
    ),
    path(
        "movements/<uuid:movement_id>/lines/<uuid:line_id>/remove/",
        views.line_remove,
        name="line_remove",
    ),
    path("balances/", views.balances, name="balances"),
    path("history/", views.history, name="history"),
]
