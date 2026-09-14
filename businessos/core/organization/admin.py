from django.contrib import admin

from businessos.core.admin import businessos_admin_site

from .models import Branch, Company, Warehouse


@admin.register(Company, site=businessos_admin_site)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "country",
        "base_currency",
        "timezone",
        "default_language",
        "is_active",
    )
    search_fields = ("code", "name")


@admin.register(Branch, site=businessos_admin_site)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "company", "is_active")
    list_filter = ("company", "is_active")


@admin.register(Warehouse, site=businessos_admin_site)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "company", "branch", "is_active")
    list_filter = ("company", "branch", "is_active")
