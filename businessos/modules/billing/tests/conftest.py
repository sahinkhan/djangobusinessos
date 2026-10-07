import pytest

from businessos.core.access.models import Permission, Role, RolePermission, UserRoleAssignment
from businessos.core.modules.services import register_manifest
from businessos.modules.billing.manifest import MODULE
from businessos.modules.billing.services import add_invoice_line, create_invoice
from businessos.modules.party.models import Party


@pytest.fixture
def billing_role(operator, company):
    register_manifest(MODULE)
    role = Role.objects.create(company=company, code="billing-test", name="Billing test")
    for permission in Permission.objects.filter(code__in=MODULE["permissions"]):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return role


@pytest.fixture
def party(company):
    return Party.objects.create(company=company, party_type="person", display_name="Generic client")


@pytest.fixture
def invoice(business_context, billing_role, party, currency):
    return create_invoice(business_context, bill_to_party_id=party.pk, currency_id=currency.pk)


@pytest.fixture
def line(business_context, invoice):
    return add_invoice_line(
        business_context, invoice.pk, description="Consulting", quantity="2", unit_price="0.0050"
    )
