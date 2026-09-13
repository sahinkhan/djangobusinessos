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

businessos_admin_site.register(UserCompanyAccess)
businessos_admin_site.register(UserBranchAccess)
businessos_admin_site.register(UserWarehouseAccess)
businessos_admin_site.register(Permission)
businessos_admin_site.register(Role)
businessos_admin_site.register(RolePermission)
businessos_admin_site.register(UserRoleAssignment)
