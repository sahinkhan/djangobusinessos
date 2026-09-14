from django.contrib import admin

from businessos.core.admin import businessos_admin_site

from .models import AuditEntry


@admin.register(AuditEntry, site=businessos_admin_site)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "action", "actor", "company", "object_type", "object_id")
    list_filter = ("action", "company")
    search_fields = ("action", "object_type", "object_id", "actor__email")
    readonly_fields = tuple(field.name for field in AuditEntry._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
