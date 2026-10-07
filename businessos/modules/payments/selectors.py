from django.db.models import Q

from businessos.core.access.policies import require_permission

from .manifest import VIEW_METHODS, VIEW_PAYMENTS
from .models import Payment, PaymentMethod


def payment_methods_for_company(context, *, search="", active=""):
    require_permission(context, VIEW_METHODS)
    methods = PaymentMethod.objects.filter(company_id=context.company_id)
    if search.strip():
        methods = methods.filter(
            Q(code__icontains=search.strip()) | Q(name__icontains=search.strip())
        )
    if active in {"yes", "no"}:
        methods = methods.filter(is_active=active == "yes")
    return methods.order_by("code", "id")


def payments_for_company(context, *, search=""):
    require_permission(context, VIEW_PAYMENTS)
    payments = Payment.objects.filter(company_id=context.company_id)
    if search.strip():
        payments = payments.filter(
            Q(number__icontains=search.strip())
            | Q(payer_display_name_snapshot__icontains=search.strip())
            | Q(external_reference__icontains=search.strip())
        )
    return payments.order_by("-payment_date", "-recorded_at", "id")


def payment_detail(context, payment_id):
    return payments_for_company(context).select_related("company").get(pk=payment_id)
