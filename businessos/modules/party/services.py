from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from businessos.core.access.policies import validate_business_context
from businessos.core.common.context import BusinessContext
from businessos.core.reference.models import Country

from .models import Address, ContactMethod, Party


def _party_in_scope(context: BusinessContext, party_id) -> Party:
    try:
        return Party.objects.get(id=party_id, company_id=context.company_id)
    except Party.DoesNotExist as exc:
        raise PermissionDenied("The party is outside the selected company.") from exc


def _related_in_scope(model, context: BusinessContext, object_id, label: str):
    try:
        return model.objects.get(id=object_id, company_id=context.company_id)
    except model.DoesNotExist as exc:
        raise PermissionDenied(f"The {label} is outside the selected company.") from exc


@transaction.atomic
def create_party(
    context: BusinessContext,
    *,
    party_type: str,
    display_name: str,
    legal_name: str = "",
    is_customer: bool = False,
    is_supplier: bool = False,
    is_active: bool = True,
) -> Party:
    validate_business_context(context)
    party = Party(
        company_id=context.company_id,
        party_type=party_type,
        display_name=display_name,
        legal_name=legal_name,
        is_customer=is_customer,
        is_supplier=is_supplier,
        is_active=is_active,
    )
    party.save()
    return party


@transaction.atomic
def update_party(context: BusinessContext, *, party_id, **changes) -> Party:
    validate_business_context(context)
    party = _party_in_scope(context, party_id)
    allowed = {
        "party_type",
        "display_name",
        "legal_name",
        "is_customer",
        "is_supplier",
        "is_active",
    }
    unknown = changes.keys() - allowed
    if unknown:
        raise ValidationError(f"Unsupported Party fields: {', '.join(sorted(unknown))}")
    for field_name, value in changes.items():
        setattr(party, field_name, value)
    party.save()
    return party


@transaction.atomic
def add_contact_method(
    context: BusinessContext,
    *,
    party_id,
    kind: str,
    value: str,
    label: str = "",
    is_primary: bool = False,
) -> ContactMethod:
    validate_business_context(context)
    party = _party_in_scope(context, party_id)
    contact = ContactMethod(
        company_id=context.company_id,
        party=party,
        kind=kind,
        value=value,
        label=label,
        is_primary=is_primary,
    )
    contact.save()
    return contact


@transaction.atomic
def update_contact_method(
    context: BusinessContext,
    *,
    contact_id,
    kind: str,
    value: str,
    label: str = "",
    is_primary: bool = False,
) -> ContactMethod:
    validate_business_context(context)
    contact = _related_in_scope(ContactMethod, context, contact_id, "contact method")
    contact.kind = kind
    contact.value = value
    contact.label = label
    contact.is_primary = is_primary
    contact.save()
    return contact


@transaction.atomic
def add_address(
    context: BusinessContext,
    *,
    party_id,
    country_id,
    label: str = "",
    line_1: str,
    line_2: str = "",
    city: str,
    region: str = "",
    postal_code: str = "",
    is_billing: bool = False,
    is_shipping: bool = False,
    is_default: bool = False,
) -> Address:
    validate_business_context(context)
    party = _party_in_scope(context, party_id)
    try:
        country = Country.objects.get(id=country_id, is_active=True)
    except Country.DoesNotExist as exc:
        raise ValidationError({"country": "Select an active country."}) from exc
    address = Address(
        company_id=context.company_id,
        party=party,
        country=country,
        label=label,
        line_1=line_1,
        line_2=line_2,
        city=city,
        region=region,
        postal_code=postal_code,
        is_billing=is_billing,
        is_shipping=is_shipping,
        is_default=is_default,
    )
    address.save()
    return address


@transaction.atomic
def update_address(
    context: BusinessContext,
    *,
    address_id,
    country_id,
    label: str = "",
    line_1: str,
    line_2: str = "",
    city: str,
    region: str = "",
    postal_code: str = "",
    is_billing: bool = False,
    is_shipping: bool = False,
    is_default: bool = False,
) -> Address:
    validate_business_context(context)
    address = _related_in_scope(Address, context, address_id, "address")
    try:
        country = Country.objects.get(id=country_id, is_active=True)
    except Country.DoesNotExist as exc:
        raise ValidationError({"country": "Select an active country."}) from exc
    address.country = country
    address.label = label
    address.line_1 = line_1
    address.line_2 = line_2
    address.city = city
    address.region = region
    address.postal_code = postal_code
    address.is_billing = is_billing
    address.is_shipping = is_shipping
    address.is_default = is_default
    address.save()
    return address
