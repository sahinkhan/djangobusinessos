from django.contrib import admin

from businessos.core.admin import businessos_admin_site

from .models import BusinessModule


@admin.register(BusinessModule, site=businessos_admin_site)
class BusinessModuleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "version", "is_enabled")
    list_filter = ("is_enabled",)
    search_fields = ("code", "name")
