from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render

from businessos.core.access.context import business_context_from_request

from .forms import AddressForm, ContactMethodForm, PartyForm
from .models import Address, ContactMethod, Party
from .selectors import parties_for_company, party_detail
from .services import (
    add_address,
    add_contact_method,
    create_party,
    update_address,
    update_contact_method,
    update_party,
)


def _add_service_error(form, error):
    if hasattr(error, "message_dict"):
        for field, errors in error.message_dict.items():
            target = field if field in form.fields else None
            for message in errors:
                form.add_error(target, message)
    else:
        form.add_error(None, error)


@login_required
def party_list(request):
    context = business_context_from_request(request)
    search = request.GET.get("q", "")
    return render(
        request,
        "party/party_list.html",
        {"parties": parties_for_company(context, search=search), "search": search},
    )


@login_required
def party_create(request):
    context = business_context_from_request(request)
    form = PartyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            party = create_party(context, **form.cleaned_data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Party created.")
            return redirect("party:detail", party_id=party.id)
    return render(request, "party/party_form.html", {"form": form, "heading": "Create party"})


@login_required
def party_edit(request, party_id):
    context = business_context_from_request(request)
    try:
        party = party_detail(context, party_id=party_id)
    except Party.DoesNotExist as exc:
        raise Http404 from exc
    initial = {
        "party_type": party.party_type,
        "display_name": party.display_name,
        "legal_name": party.legal_name,
        "is_customer": party.is_customer,
        "is_supplier": party.is_supplier,
        "is_active": party.is_active,
    }
    form = PartyForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            update_party(context, party_id=party.id, **form.cleaned_data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Party updated.")
            return redirect("party:detail", party_id=party.id)
    return render(request, "party/party_form.html", {"form": form, "heading": "Edit party"})


@login_required
def party_detail_view(request, party_id):
    context = business_context_from_request(request)
    try:
        party = party_detail(context, party_id=party_id)
    except Party.DoesNotExist as exc:
        raise Http404 from exc
    return render(request, "party/party_detail.html", {"party": party})


@login_required
def contact_create(request, party_id):
    context = business_context_from_request(request)
    form = ContactMethodForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            add_contact_method(context, party_id=party_id, **form.cleaned_data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Contact method added.")
            return redirect("party:detail", party_id=party_id)
    return render(request, "party/related_form.html", {"form": form, "heading": "Add contact"})


@login_required
def contact_edit(request, party_id, contact_id):
    context = business_context_from_request(request)
    try:
        contact = ContactMethod.objects.get(
            id=contact_id, party_id=party_id, company_id=context.company_id
        )
    except ContactMethod.DoesNotExist as exc:
        raise Http404 from exc
    form = ContactMethodForm(
        request.POST or None,
        initial={
            "kind": contact.kind,
            "label": contact.label,
            "value": contact.value,
            "is_primary": contact.is_primary,
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_contact_method(context, contact_id=contact.id, **form.cleaned_data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Contact method updated.")
            return redirect("party:detail", party_id=party_id)
    return render(request, "party/related_form.html", {"form": form, "heading": "Edit contact"})


@login_required
def address_create(request, party_id):
    context = business_context_from_request(request)
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        data["country_id"] = data.pop("country").id
        try:
            add_address(context, party_id=party_id, **data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Address added.")
            return redirect("party:detail", party_id=party_id)
    return render(request, "party/related_form.html", {"form": form, "heading": "Add address"})


@login_required
def address_edit(request, party_id, address_id):
    context = business_context_from_request(request)
    try:
        address = Address.objects.get(
            id=address_id, party_id=party_id, company_id=context.company_id
        )
    except Address.DoesNotExist as exc:
        raise Http404 from exc
    initial = {
        "country": address.country_id,
        "label": address.label,
        "line_1": address.line_1,
        "line_2": address.line_2,
        "city": address.city,
        "region": address.region,
        "postal_code": address.postal_code,
        "is_billing": address.is_billing,
        "is_shipping": address.is_shipping,
        "is_default": address.is_default,
    }
    form = AddressForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        data["country_id"] = data.pop("country").id
        try:
            update_address(context, address_id=address.id, **data)
        except ValidationError as error:
            _add_service_error(form, error)
        else:
            messages.success(request, "Address updated.")
            return redirect("party:detail", party_id=party_id)
    return render(request, "party/related_form.html", {"form": form, "heading": "Edit address"})
