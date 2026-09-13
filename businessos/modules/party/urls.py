from django.urls import path

from . import views

app_name = "party"

urlpatterns = [
    path("", views.party_list, name="list"),
    path("new/", views.party_create, name="create"),
    path("<uuid:party_id>/", views.party_detail_view, name="detail"),
    path("<uuid:party_id>/edit/", views.party_edit, name="edit"),
    path("<uuid:party_id>/contacts/new/", views.contact_create, name="contact_create"),
    path(
        "<uuid:party_id>/contacts/<uuid:contact_id>/edit/",
        views.contact_edit,
        name="contact_edit",
    ),
    path("<uuid:party_id>/addresses/new/", views.address_create, name="address_create"),
    path(
        "<uuid:party_id>/addresses/<uuid:address_id>/edit/",
        views.address_edit,
        name="address_edit",
    ),
]
