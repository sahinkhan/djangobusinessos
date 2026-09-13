from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group


class BusinessOSAdminSite(AdminSite):
    """Deployment-wide administration reserved for trusted superusers."""

    site_header = "BusinessOS administration"
    site_title = "BusinessOS admin"
    index_title = "Deployment administration"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser


businessos_admin_site = BusinessOSAdminSite(name="businessos_admin")
businessos_admin_site.register(Group)
