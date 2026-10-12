from contextlib import contextmanager

from django.core.exceptions import PermissionDenied
from django.http import Http404

from businessos.core.access.policies import require_permission
from businessos.core.database import business_atomic_context
from businessos.core.modules.models import BusinessModule
from businessos.core.organization.models import Company

from .compatibility import admit_profile

ACCOUNTING_CREATE = (
    "accounting.account.view",
    "accounting.journal.view",
    "accounting.entry.create",
    "accounting.entry.update",
    "accounting.entry.post",
)


def permissions(*, allocation=False, create=False):
    code = "accounting_payments_billing" if allocation else "accounting_billing"
    grants = [
        f"{code}.posting.{'create' if create else 'view'}",
        "billing.invoice.view",
        "accounting.entry.view",
    ]
    if allocation:
        grants += [
            "accounting_billing.posting.view",
            "payments_billing.allocation.view",
            "payments.payment.view",
        ]
    if create:
        grants += list(ACCOUNTING_CREATE)
    return tuple(grants)


def authorize(context, *, allocation=False, create=False):
    company = (
        Company.objects.select_for_update().filter(pk=context.company_id, is_active=True).first()
    )
    if company is None:
        raise PermissionDenied("Active company context required.")
    for permission in permissions(allocation=allocation, create=create):
        require_permission(context, permission)
    return company


@contextmanager
def admission(context, *, allocation=False, create=False, http=False):
    with business_atomic_context():
        # Reject invisible/misdirected authorization relations BEFORE checking any grants.
        admit_profile(allocation=allocation, http=http)
        company = authorize(context, allocation=allocation, create=create)
        if http:
            codes = ["accounting", "accounting_billing", "billing"]
            if allocation:
                codes += ["accounting_payments_billing", "payments", "payments_billing"]
            rows = list(
                BusinessModule.objects.select_for_update()
                .filter(code__in=codes)
                .order_by("code")
                .values_list("code", "is_enabled")
            )
            if len(rows) != len(codes) or not all(enabled for _, enabled in rows):
                raise Http404("Accounting integration is unavailable.")
            authorize(context, allocation=allocation, create=create)
        yield company
