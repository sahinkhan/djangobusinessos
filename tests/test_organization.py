import pytest
from django.core.exceptions import ValidationError
from django.forms import modelform_factory

from businessos.core.organization.models import Branch, Company, Warehouse


@pytest.mark.django_db
def test_company_uses_base_currency_and_normalizes_code(currency, country, language):
    company = Company.objects.create(
        code=" acme ",
        name="Acme",
        base_currency=currency,
        country=country,
        default_language=language,
    )

    assert company.code == "ACME"
    assert company.base_currency == currency


@pytest.mark.django_db
def test_branch_codes_are_unique_within_company_but_reusable_between_companies(
    currency, country, language
):
    first = Company.objects.create(
        code="ONE", name="One", base_currency=currency, country=country, default_language=language
    )
    second = Company.objects.create(
        code="TWO", name="Two", base_currency=currency, country=country, default_language=language
    )
    Branch.objects.create(company=first, code="HQ", name="First HQ")
    Branch.objects.create(company=second, code="HQ", name="Second HQ")

    with pytest.raises(ValidationError, match="already exists"):
        Branch.objects.create(company=first, code="HQ", name="Duplicate")


@pytest.mark.django_db
def test_warehouse_may_be_company_level(company):
    warehouse = Warehouse.objects.create(company=company, code="TRANSIT", name="Transit")

    assert warehouse.branch is None
    assert warehouse.company == company


@pytest.mark.django_db
def test_warehouse_rejects_branch_from_another_company(currency, company):
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=currency,
        country=company.country,
        default_language=company.default_language,
    )
    other_branch = Branch.objects.create(company=other, code="HQ", name="Other HQ")

    with pytest.raises(ValidationError, match="warehouse company"):
        Warehouse.objects.create(company=company, branch=other_branch, code="BAD", name="Invalid")


@pytest.mark.django_db
def test_branch_company_ownership_is_immutable_through_model_forms(currency, company, branch):
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=currency,
        country=company.country,
        default_language=company.default_language,
    )
    branch_form = modelform_factory(Branch, fields=("company", "code", "name", "is_active"))

    form = branch_form(
        data={"company": other.id, "code": branch.code, "name": branch.name, "is_active": True},
        instance=branch,
    )

    assert not form.is_valid()
    assert "company" in form.errors
    branch.refresh_from_db()
    assert branch.company == company


@pytest.mark.django_db
def test_company_form_normalizes_code_before_uniqueness_validation(company):
    company_form = modelform_factory(
        Company, fields=("code", "name", "base_currency", "is_active")
    )

    form = company_form(
        data={
            "code": "acme",
            "name": "Duplicate",
            "base_currency": company.base_currency_id,
            "is_active": True,
        }
    )

    assert not form.is_valid()
    assert "code" in form.errors


@pytest.mark.django_db
def test_warehouse_company_ownership_is_immutable(currency, warehouse):
    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=currency,
        country=warehouse.company.country,
        default_language=warehouse.company.default_language,
    )
    warehouse.company = other

    with pytest.raises(ValidationError, match="ownership is immutable"):
        warehouse.save()
