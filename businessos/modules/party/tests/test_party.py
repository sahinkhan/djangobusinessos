import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.modules.party.models import ContactMethod, Party
from businessos.modules.party.selectors import (
    active_customers,
    active_suppliers,
    parties_for_company,
)
from businessos.modules.party.services import (
    add_address,
    add_contact_method,
    create_party,
    update_address,
    update_contact_method,
    update_party,
)


@pytest.mark.django_db
def test_person_and_organization_roles(business_context):
    person = create_party(
        business_context,
        party_type=Party.Type.PERSON,
        display_name="Ada Lovelace",
        is_customer=True,
    )
    organization = create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Analytical Engines Ltd",
        legal_name="Analytical Engines Limited",
        is_customer=True,
        is_supplier=True,
    )

    assert person.party_type == Party.Type.PERSON
    assert list(active_customers(business_context)) == [person, organization]
    assert list(active_suppliers(business_context)) == [organization]


@pytest.mark.django_db
def test_contact_and_address_validation(business_context, country):
    party = create_party(
        business_context, party_type=Party.Type.ORGANIZATION, display_name="Supplier One"
    )
    contact = add_contact_method(
        business_context,
        party_id=party.id,
        kind=ContactMethod.Kind.EMAIL,
        value=" SALES@EXAMPLE.COM ",
        is_primary=True,
    )
    address = add_address(
        business_context,
        party_id=party.id,
        country_id=country.id,
        line_1="1 Market Street",
        city="Dhaka",
        is_billing=True,
        is_default=True,
    )

    assert contact.value == "sales@example.com"
    assert address.company_id == party.company_id
    assert address.is_billing is True

    update_contact_method(
        business_context,
        contact_id=contact.id,
        kind=ContactMethod.Kind.PHONE,
        value="+880 1700 000000",
        label="Office",
        is_primary=True,
    )
    update_address(
        business_context,
        address_id=address.id,
        country_id=country.id,
        line_1="2 Market Street",
        city="Dhaka",
        is_shipping=True,
    )
    contact.refresh_from_db()
    address.refresh_from_db()
    assert contact.kind == ContactMethod.Kind.PHONE
    assert address.line_1 == "2 Market Street"

    with pytest.raises(ValidationError):
        add_contact_method(
            business_context,
            party_id=party.id,
            kind=ContactMethod.Kind.EMAIL,
            value="not-an-email",
        )


@pytest.mark.django_db
def test_party_services_and_selectors_reject_cross_company_scope(
    business_context, operator, company, currency
):
    other_company = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=currency,
        country=company.country,
        default_language=company.default_language,
    )
    other_context = BusinessContext(actor_id=operator.id, company_id=other_company.id)
    other_party = Party.objects.create(
        company=other_company,
        party_type=Party.Type.ORGANIZATION,
        display_name="Hidden Supplier",
        is_supplier=True,
    )

    assert list(parties_for_company(business_context)) == []
    with pytest.raises(PermissionDenied, match="outside the selected company"):
        update_party(business_context, party_id=other_party.id, display_name="Leak")
    with pytest.raises(PermissionDenied, match="outside the selected company"):
        add_contact_method(
            business_context,
            party_id=other_party.id,
            kind=ContactMethod.Kind.PHONE,
            value="123",
        )
    with pytest.raises(PermissionDenied, match="access to this company"):
        list(parties_for_company(other_context))


@pytest.mark.django_db
def test_party_company_ownership_is_immutable(business_context, company, currency):
    party = create_party(
        business_context, party_type=Party.Type.PERSON, display_name="Scoped Person"
    )
    other_company = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=currency,
        country=company.country,
        default_language=company.default_language,
    )
    party.company = other_company

    with pytest.raises(ValidationError, match="ownership cannot be reassigned"):
        party.save()
