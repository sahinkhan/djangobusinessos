from django.core.exceptions import PermissionDenied

from businessos.core.access.policies import require_permission
from businessos.core.database import current_database_alias
from businessos.core.organization.models import Company
from businessos.modules.billing.manifest import VIEW_INVOICES
from businessos.modules.payments.manifest import VIEW_PAYMENTS


def authorize(context, permission):
    if (
        not Company.objects.using(current_database_alias())
        .select_for_update()
        .filter(pk=context.company_id, is_active=True)
        .exists()
    ):
        raise PermissionDenied("The selected company is unavailable.")
    for grant in (permission, VIEW_PAYMENTS, VIEW_INVOICES):
        require_permission(context, grant)
