from django.contrib import admin

from businessos.core.admin import businessos_admin_site

from .models import (
    Permission,
    Role,
    RolePermission,
    UserBranchAccess,
    UserCompanyAccess,
    UserRoleAssignment,
    UserWarehouseAccess,
)


class ReadOnlySecurityRecordAdmin(admin.ModelAdmin):
    """Inspection-only surface; security mutations use audited application services."""

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


for security_model in (
    UserCompanyAccess,
    UserBranchAccess,
    UserWarehouseAccess,
    Permission,
    Role,
    RolePermission,
    UserRoleAssignment,
):
    businessos_admin_site.register(security_model, ReadOnlySecurityRecordAdmin)
