"""HTTP-only, Company-before-registry admission. Domain services do not use this."""

from contextlib import contextmanager

from django.http import Http404

from businessos.core.access.policies import validate_business_context
from businessos.core.database import business_atomic_context, current_database_alias
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company

from .authorization import authorize

CODES = ("billing", "payments", "payments_billing")


@contextmanager
def parent_read_admission(context):
    """Stabilize ordinary parent facts and optional evidence through page rendering.

    This requires no allocation grant: the existing owner view still enforces its
    own permission/module contract. Missing optional authority remains UNAVAILABLE.
    """
    with business_atomic_context():
        Company.objects.using(current_database_alias()).select_for_update().filter(
            pk=context.company_id, is_active=True
        ).first()
        validate_business_context(context)
        yield


@contextmanager
def http_admission(context, permission):
    with business_atomic_context():
        Company.objects.using(current_database_alias()).select_for_update().filter(
            pk=context.company_id, is_active=True
        ).first()
        validate_business_context(context)  # Company before registry; no cached grants.
        modules = tuple(
            BusinessModule.objects.using(current_database_alias())
            .select_for_update()
            .filter(code__in=CODES)
            .order_by("code")
        )
        if tuple(module.code for module in modules) != CODES or not all(
            module.is_enabled for module in modules
        ):
            raise Http404("Payment allocation HTTP capability unavailable.")
        authorize(context, permission)
        yield
