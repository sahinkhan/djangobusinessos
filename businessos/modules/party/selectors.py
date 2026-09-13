from django.db.models import Q

from businessos.core.access.policies import validate_business_context
from businessos.core.common.context import BusinessContext

from .models import Party


def parties_for_company(context: BusinessContext, *, search: str = ""):
    validate_business_context(context)
    queryset = Party.objects.filter(company_id=context.company_id).order_by("display_name")
    if search.strip():
        queryset = queryset.filter(
            Q(display_name__icontains=search.strip()) | Q(legal_name__icontains=search.strip())
        )
    return queryset


def active_customers(context: BusinessContext):
    return parties_for_company(context).filter(is_active=True, is_customer=True)


def active_suppliers(context: BusinessContext):
    return parties_for_company(context).filter(is_active=True, is_supplier=True)


def party_detail(context: BusinessContext, *, party_id) -> Party:
    validate_business_context(context)
    return Party.objects.prefetch_related("contact_methods", "addresses__country").get(
        id=party_id, company_id=context.company_id
    )
