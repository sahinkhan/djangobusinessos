from businessos.core.admin import businessos_admin_site

from .models import UserBranchAccess, UserCompanyAccess, UserWarehouseAccess

businessos_admin_site.register(UserCompanyAccess)
businessos_admin_site.register(UserBranchAccess)
businessos_admin_site.register(UserWarehouseAccess)
