import pytest

from businessos.core.organization.models import Branch, Company, Warehouse
from businessos.core.reference.models import Currency


@pytest.fixture
def currency(db):
    return Currency.objects.create(code="USD", name="US Dollar", symbol="$")


@pytest.fixture
def company(currency):
    return Company.objects.create(code="ACME", name="Acme Corporation", base_currency=currency)


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, code="HQ", name="Head Office")


@pytest.fixture
def warehouse(company, branch):
    return Warehouse.objects.create(
        company=company, branch=branch, code="MAIN", name="Main Warehouse"
    )
