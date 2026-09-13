from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError

from businessos.core.access.context import (
    SESSION_BRANCH_KEY,
    SESSION_COMPANY_KEY,
    SESSION_WAREHOUSE_KEY,
    business_context_from_request,
)
from businessos.core.access.models import UserBranchAccess, UserCompanyAccess, UserWarehouseAccess
from businessos.core.access.policies import validate_business_context
from businessos.core.access.selectors import companies_for_user
from businessos.core.common.context import BusinessContext
from businessos.core.organization.models import Branch, Company
from businessos.core.reference.models import Currency


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user("operator@example.com", "password")


@pytest.mark.django_db
def test_company_selector_returns_only_explicitly_allowed_companies(user, company):
    other_currency = Currency.objects.create(code="EUR", name="Euro", symbol="€")
    Company.objects.create(code="OTHER", name="Other", base_currency=other_currency)
    UserCompanyAccess.objects.create(user=user, company=company)

    assert list(companies_for_user(user)) == [company]


@pytest.mark.django_db
def test_branch_access_requires_company_access(user, branch):
    with pytest.raises(ValidationError, match="Grant company access"):
        UserBranchAccess.objects.create(user=user, branch=branch)


@pytest.mark.django_db
def test_context_adapter_builds_immutable_validated_context(user, company, branch, warehouse):
    UserCompanyAccess.objects.create(user=user, company=company)
    UserBranchAccess.objects.create(user=user, branch=branch)
    UserWarehouseAccess.objects.create(user=user, warehouse=warehouse)
    request = SimpleNamespace(
        user=user,
        session={
            SESSION_COMPANY_KEY: str(company.id),
            SESSION_BRANCH_KEY: str(branch.id),
            SESSION_WAREHOUSE_KEY: str(warehouse.id),
        },
    )

    context = business_context_from_request(request)

    assert context.actor_id == user.id
    assert context.company_id == company.id
    assert context.branch_id == branch.id
    assert context.warehouse_id == warehouse.id
    with pytest.raises(AttributeError):
        context.company_id = company.id


@pytest.mark.django_db
def test_context_adapter_rejects_cross_company_branch(user, company, currency):
    other = Company.objects.create(code="OTHER", name="Other", base_currency=currency)
    other_branch = Branch.objects.create(company=other, code="HQ", name="Other HQ")
    UserCompanyAccess.objects.create(user=user, company=company)
    request = SimpleNamespace(
        user=user,
        session={SESSION_COMPANY_KEY: str(company.id), SESSION_BRANCH_KEY: str(other_branch.id)},
    )

    with pytest.raises(PermissionDenied, match="outside the selected company"):
        business_context_from_request(request)


def test_business_context_rejects_missing_required_identifiers():
    with pytest.raises(TypeError, match="actor_id"):
        BusinessContext(actor_id=None, company_id=None)


@pytest.mark.django_db
def test_superuser_context_still_requires_an_active_existing_company():
    superuser = get_user_model().objects.create_superuser("admin@example.com", "password")
    request = SimpleNamespace(
        user=superuser,
        session={SESSION_COMPANY_KEY: str(uuid4())},
    )

    with pytest.raises(PermissionDenied, match="does not exist or is inactive"):
        business_context_from_request(request)


@pytest.mark.django_db
def test_superuser_context_rejects_inactive_company(company):
    superuser = get_user_model().objects.create_superuser("admin@example.com", "password")
    company.is_active = False
    company.save()
    request = SimpleNamespace(user=superuser, session={SESSION_COMPANY_KEY: str(company.id)})

    with pytest.raises(PermissionDenied, match="does not exist or is inactive"):
        business_context_from_request(request)


@pytest.mark.django_db
def test_non_http_policy_validates_context(user, company):
    UserCompanyAccess.objects.create(user=user, company=company)
    context = BusinessContext(actor_id=user.id, company_id=company.id)

    assert validate_business_context(context) is context


@pytest.mark.django_db
def test_warehouse_on_inactive_branch_is_not_valid_scope(user, company, branch, warehouse):
    UserCompanyAccess.objects.create(user=user, company=company)
    UserWarehouseAccess.objects.create(user=user, warehouse=warehouse)
    branch.is_active = False
    branch.save()
    context = BusinessContext(actor_id=user.id, company_id=company.id, warehouse_id=warehouse.id)

    with pytest.raises(PermissionDenied, match="branch is inactive"):
        validate_business_context(context)
