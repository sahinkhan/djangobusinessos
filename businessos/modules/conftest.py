import pytest
from django.contrib.auth import get_user_model

from businessos.core.access.models import UserCompanyAccess
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Company
from businessos.core.reference.models import Country, Currency, UnitOfMeasure


@pytest.fixture
def currency(db):
    return Currency.objects.create(code="USD", name="US Dollar", symbol="$")


@pytest.fixture
def company(currency):
    return Company.objects.create(code="ACME", name="Acme Corporation", base_currency=currency)


@pytest.fixture
def country(db):
    return Country.objects.create(code="US", name="United States")


@pytest.fixture
def uom(db):
    return UnitOfMeasure.objects.create(code="EA", name="Each", symbol="ea")


@pytest.fixture
def operator(db, company):
    user = get_user_model().objects.create_user("phase1@example.com", "password")
    UserCompanyAccess.objects.create(user=user, company=company)
    return user


@pytest.fixture
def business_context(operator, company):
    return BusinessContext(actor_id=operator.id, company_id=company.id)
