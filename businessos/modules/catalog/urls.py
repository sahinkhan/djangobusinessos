from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<uuid:product_id>/", views.product_detail_view, name="product_detail"),
    path("products/<uuid:product_id>/edit/", views.product_edit, name="product_edit"),
    path("products/<uuid:product_id>/variants/new/", views.variant_create, name="variant_create"),
    path(
        "products/<uuid:product_id>/variants/<uuid:variant_id>/edit/",
        views.variant_edit,
        name="variant_edit",
    ),
    path(
        "products/<uuid:product_id>/variants/<uuid:variant_id>/attributes/",
        views.variant_attributes,
        name="variant_attributes",
    ),
    path("categories/", views.category_list, name="categories"),
    path("attributes/", views.attribute_list, name="attributes"),
    path(
        "attributes/<uuid:attribute_id>/values/new/",
        views.attribute_value_create,
        name="attribute_value_create",
    ),
]
