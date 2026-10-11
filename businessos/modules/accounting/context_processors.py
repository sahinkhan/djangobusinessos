from django.core.exceptions import PermissionDenied

from businessos.core.access.context import business_context_from_request
from businessos.core.access.policies import has_permission

from .manifest import (
    CREATE_ENTRIES,
    MANAGE_ACCOUNTS,
    MANAGE_JOURNALS,
    VIEW_ACCOUNTS,
    VIEW_ENTRIES,
    VIEW_JOURNALS,
)


def accounting_navigation(request):
    result = {"accounting_navigation_url": None}
    if not request.user.is_authenticated:
        return result
    try:
        context = business_context_from_request(request)
        result.update(
            {
                "accounting_can_view_entries": has_permission(context, VIEW_ENTRIES),
                "accounting_can_view_accounts": has_permission(context, VIEW_ACCOUNTS),
                "accounting_can_view_journals": has_permission(context, VIEW_JOURNALS),
                "accounting_can_manage_accounts": has_permission(context, MANAGE_ACCOUNTS),
                "accounting_can_manage_journals": has_permission(context, MANAGE_JOURNALS),
            }
        )
        for permission, url in (
            (VIEW_ENTRIES, "accounting:list"),
            (VIEW_ACCOUNTS, "accounting:accounts"),
            (VIEW_JOURNALS, "accounting:journals"),
            (CREATE_ENTRIES, "accounting:create"),
            (MANAGE_ACCOUNTS, "accounting:account_create"),
            (MANAGE_JOURNALS, "accounting:journal_create"),
        ):
            if has_permission(context, permission):
                result["accounting_navigation_url"] = url
                break
    except PermissionDenied:
        pass
    return result
