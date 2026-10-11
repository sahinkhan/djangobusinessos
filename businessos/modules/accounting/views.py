from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from businessos.core.access.context import business_context_from_request
from businessos.core.access.forms import CompanyBoundForm
from businessos.core.access.policies import has_permission, require_permission
from businessos.core.modules.decorators import module_required

from . import selectors, services
from .forms import EntryFilterForm, EntryForm, FilterForm, LineForm, ReferenceForm, ReportForm
from .manifest import (
    CREATE_ENTRIES,
    MANAGE_ACCOUNTS,
    MANAGE_JOURNALS,
    POST_ENTRIES,
    UPDATE_ENTRIES,
    VIEW_ENTRIES,
)
from .models import Account, Journal, JournalEntry, JournalEntryLine


def _errors(form, error):
    if hasattr(error, "message_dict"):
        for field, errors in error.message_dict.items():
            for message in errors:
                form.add_error(field if field in form.fields else None, message)
    else:
        form.add_error(None, error)


def _next(context, entry=None):
    if entry is not None and has_permission(context, VIEW_ENTRIES):
        return redirect("accounting:detail", entry_id=entry.pk)
    return redirect("home")


@login_required
@module_required("accounting")
def reference_list(request, kind):
    context = business_context_from_request(request)
    account = kind == "account"
    form = FilterForm(request.GET)
    form.is_valid()
    selector = selectors.accounts_for_company if account else selectors.journals_for_company
    page = Paginator(
        selector(
            context,
            search=form.cleaned_data.get("q", ""),
            active=form.cleaned_data.get("active", ""),
        ),
        50,
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "accounting/reference_list.html",
        {
            "page_obj": page,
            "rows": page.object_list,
            "filter_form": form,
            "kind": kind,
            "heading": "Accounts" if account else "Journals",
            "can_manage": has_permission(context, MANAGE_ACCOUNTS if account else MANAGE_JOURNALS),
            "create_url": "accounting:account_create" if account else "accounting:journal_create",
            "edit_url": "accounting:account_edit" if account else "accounting:journal_edit",
        },
    )


@login_required
@module_required("accounting")
def reference_form(request, kind, reference_id=None):
    context = business_context_from_request(request)
    account = kind == "account"
    require_permission(context, MANAGE_ACCOUNTS if account else MANAGE_JOURNALS)
    model = Account if account else Journal
    row = (
        get_object_or_404(model, pk=reference_id, company_id=context.company_id)
        if reference_id
        else None
    )
    form = ReferenceForm(
        request.POST if request.method == "POST" else None,
        company_id=context.company_id,
        account=account,
        editing=row is not None,
        initial={"name": row.name, "is_active": "true" if row.is_active else "false"}
        if row
        else {},
    )
    if request.method == "POST" and form.is_valid():
        try:
            if row:
                operation = services.update_account if account else services.update_journal
                operation(context, row.pk, **form.cleaned_data)
            else:
                operation = services.create_account if account else services.create_journal
                row = operation(context, **form.cleaned_data)
        except ValidationError as exc:
            _errors(form, exc)
        else:
            return redirect(
                "accounting:account_edit" if account else "accounting:journal_edit",
                reference_id=row.pk,
            )
    return render(
        request,
        "accounting/form.html",
        {"form": form, "heading": f"{'Edit' if row else 'New'} {kind}"},
    )


@login_required
@module_required("accounting")
def entry_list(request):
    context = business_context_from_request(request)
    form = EntryFilterForm(request.GET)
    form.is_valid()
    page = Paginator(
        selectors.journal_entries_for_company(
            context,
            search=form.cleaned_data.get("q", ""),
            status=form.cleaned_data.get("status", ""),
        ),
        50,
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "accounting/entry_list.html",
        {
            "page_obj": page,
            "entries": page.object_list,
            "filter_form": form,
            "can_create": has_permission(context, CREATE_ENTRIES),
        },
    )


@login_required
@module_required("accounting")
def entry_detail(request, entry_id):
    context = business_context_from_request(request)
    try:
        entry = selectors.journal_entry_detail(context, entry_id)
    except JournalEntry.DoesNotExist as exc:
        raise Http404 from exc
    return render(
        request,
        "accounting/entry_detail.html",
        {
            "entry": entry,
            "can_update": has_permission(context, UPDATE_ENTRIES),
            "can_post": has_permission(context, POST_ENTRIES),
            "action_form": CompanyBoundForm(company_id=context.company_id),
        },
    )


@login_required
@module_required("accounting")
def entry_form(request, entry_id=None):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_ENTRIES if entry_id else CREATE_ENTRIES)
    entry = (
        get_object_or_404(JournalEntry, pk=entry_id, company_id=context.company_id)
        if entry_id
        else None
    )
    form = EntryForm(
        request.POST if request.method == "POST" else None,
        company_id=context.company_id,
        initial={"journal": entry.journal_id, "entry_date": entry.entry_date, "memo": entry.memo}
        if entry
        else {},
    )
    if request.method == "POST" and form.is_valid():
        data = dict(form.cleaned_data)
        data["journal_id"] = data.pop("journal").pk
        try:
            if entry:
                entry = services.update_journal_entry(context, entry.pk, **data)
            else:
                entry = services.create_journal_entry(context, **data)
        except ValidationError as exc:
            _errors(form, exc)
        else:
            return _next(context, entry)
    return render(
        request,
        "accounting/form.html",
        {"form": form, "heading": "Edit draft entry" if entry else "New journal entry"},
    )


@login_required
@module_required("accounting")
def line_form(request, entry_id, line_id=None):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_ENTRIES)
    entry = get_object_or_404(JournalEntry, pk=entry_id, company_id=context.company_id)
    line = (
        get_object_or_404(
            JournalEntryLine, pk=line_id, journal_entry=entry, company_id=context.company_id
        )
        if line_id
        else None
    )
    initial = {f: getattr(line, f) for f in ("description", "debit", "credit")} if line else {}
    if line:
        initial.update(account=line.account_id, party=line.party_id)
    form = LineForm(
        request.POST if request.method == "POST" else None,
        company_id=context.company_id,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        data = dict(form.cleaned_data)
        data["account_id"] = data.pop("account").pk
        party = data.pop("party")
        data["party_id"] = party.pk if party else None
        try:
            if line:
                services.update_journal_entry_line(context, entry.pk, line.pk, **data)
            else:
                services.add_journal_entry_line(context, entry.pk, **data)
        except ValidationError as exc:
            _errors(form, exc)
        else:
            return _next(context, entry)
    return render(
        request,
        "accounting/form.html",
        {"form": form, "heading": "Edit draft line" if line else "Add draft line"},
    )


@login_required
@module_required("accounting")
@require_POST
def line_remove(request, entry_id, line_id):
    context = business_context_from_request(request)
    require_permission(context, UPDATE_ENTRIES)
    entry = get_object_or_404(JournalEntry, pk=entry_id, company_id=context.company_id)
    form = CompanyBoundForm(request.POST, company_id=context.company_id)
    if form.is_valid():
        try:
            services.remove_journal_entry_line(context, entry_id, line_id)
        except ValidationError as exc:
            _errors(form, exc)
        else:
            return _next(context, entry)
    return render(
        request, "accounting/form.html", {"form": form, "heading": "Remove line"}, status=400
    )


@login_required
@module_required("accounting")
def entry_post(request, entry_id):
    context = business_context_from_request(request)
    require_permission(context, POST_ENTRIES)
    entry = get_object_or_404(JournalEntry, pk=entry_id, company_id=context.company_id)
    form = CompanyBoundForm(
        request.POST if request.method == "POST" else None, company_id=context.company_id
    )
    if request.method == "POST" and form.is_valid():
        try:
            services.post_journal_entry(context, entry_id)
        except ValidationError as exc:
            _errors(form, exc)
        else:
            messages.success(request, "Journal entry posted.")
            return _next(context, entry)
    return render(request, "accounting/form.html", {"form": form, "heading": "Post journal entry"})


@login_required
@module_required("accounting")
def report(request, kind):
    context = business_context_from_request(request)
    require_permission(context, VIEW_ENTRIES)
    form = ReportForm(request.GET, company_id=context.company_id)
    rows = []
    if form.is_valid():
        data = dict(form.cleaned_data)
        account = data.pop("account")
        try:
            rows = (selectors.general_ledger if kind == "gl" else selectors.trial_balance)(
                context,
                account_id=account.pk if account else None,
                **data,
            )
        except ValidationError as exc:
            _errors(form, exc)
    page = Paginator(rows, 50).get_page(request.GET.get("page"))
    return render(
        request,
        "accounting/report.html",
        {
            "kind": kind,
            "page_obj": page,
            "rows": page.object_list,
            "filter_form": form,
            "heading": "General Ledger" if kind == "gl" else "Trial Balance",
        },
    )
