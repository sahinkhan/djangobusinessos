from django.urls import path

from . import views

app_name = "accounting"
urlpatterns = [
    path("", views.entry_list, name="list"),
    path("accounts/", views.reference_list, {"kind": "account"}, name="accounts"),
    path("accounts/new/", views.reference_form, {"kind": "account"}, name="account_create"),
    path(
        "accounts/<uuid:reference_id>/edit/",
        views.reference_form,
        {"kind": "account"},
        name="account_edit",
    ),
    path("journals/", views.reference_list, {"kind": "journal"}, name="journals"),
    path("journals/new/", views.reference_form, {"kind": "journal"}, name="journal_create"),
    path(
        "journals/<uuid:reference_id>/edit/",
        views.reference_form,
        {"kind": "journal"},
        name="journal_edit",
    ),
    path("entries/new/", views.entry_form, name="create"),
    path("entries/<uuid:entry_id>/", views.entry_detail, name="detail"),
    path("entries/<uuid:entry_id>/edit/", views.entry_form, name="edit"),
    path("entries/<uuid:entry_id>/lines/new/", views.line_form, name="line_add"),
    path("entries/<uuid:entry_id>/lines/<uuid:line_id>/edit/", views.line_form, name="line_edit"),
    path(
        "entries/<uuid:entry_id>/lines/<uuid:line_id>/remove/",
        views.line_remove,
        name="line_remove",
    ),
    path("entries/<uuid:entry_id>/post/", views.entry_post, name="post"),
    path("reports/general-ledger/", views.report, {"kind": "gl"}, name="gl"),
    path("reports/trial-balance/", views.report, {"kind": "tb"}, name="tb"),
]
