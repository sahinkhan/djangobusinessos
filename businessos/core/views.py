from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from businessos.core.access.context import (
    SESSION_BRANCH_KEY,
    SESSION_COMPANY_KEY,
    SESSION_WAREHOUSE_KEY,
)
from businessos.core.access.forms import CompanyScopeForm
from businessos.core.access.selectors import companies_for_user


@login_required
def home(request):
    return render(request, "core/home.html")


@login_required
def select_company(request):
    companies = companies_for_user(request.user)
    form = CompanyScopeForm(request.POST or None, companies=companies)
    if request.method == "POST" and form.is_valid():
        request.session[SESSION_COMPANY_KEY] = str(form.cleaned_data["company"].id)
        request.session.pop(SESSION_BRANCH_KEY, None)
        request.session.pop(SESSION_WAREHOUSE_KEY, None)
        next_url = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            next_url = "/"
        return redirect(next_url)
    return render(request, "core/select_company.html", {"form": form})
