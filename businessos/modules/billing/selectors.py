from django.db.models import Q

from businessos.core.access.policies import require_permission

from .manifest import VIEW_INVOICES
from .models import Invoice


def invoices_for_company(context, *, search="", status=""):
    require_permission(context, VIEW_INVOICES)
    invoices = Invoice.objects.filter(company_id=context.company_id).prefetch_related("lines")
    if search.strip():
        invoices = invoices.filter(
            Q(number__icontains=search.strip())
            | Q(bill_to_display_name_snapshot__icontains=search.strip())
        )
    if status:
        invoices = invoices.filter(status=status)
    return invoices.order_by("-invoice_date", "-created_at", "id")


def invoice_detail(context, invoice_id):
    return invoices_for_company(context).select_related("company").get(pk=invoice_id)


def invoice_total(context, invoice_id):
    return invoice_detail(context, invoice_id).total
