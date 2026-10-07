import pytest

from businessos.core.access.models import Permission, Role, RolePermission, UserRoleAssignment
from businessos.core.modules.services import register_manifest
from businessos.modules.party.models import Party
from businessos.modules.payments.manifest import MODULE
from businessos.modules.payments.services import create_payment_method


@pytest.fixture
def payments_role(operator, company):
    register_manifest(MODULE)
    role = Role.objects.create(company=company, code="payments-test", name="Payments test")
    for permission in Permission.objects.filter(code__in=MODULE["permissions"]):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return role


@pytest.fixture
def payer(company):
    return Party.objects.create(company=company, party_type="person", display_name="Payer")


@pytest.fixture
def method(business_context, payments_role):
    return create_payment_method(business_context, code=" cash ", name=" Cash ")


@pytest.fixture
def payload(payer, method, currency):
    return dict(
        payer_party_id=payer.pk,
        payment_method_id=method.pk,
        currency_id=currency.pk,
        amount="12.50",
        payment_date="2026-10-08",
    )
