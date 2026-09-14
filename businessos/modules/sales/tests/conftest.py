from datetime import date

import pytest

from businessos.core.access.models import Permission, Role, RolePermission, UserRoleAssignment
from businessos.core.modules.services import register_manifest
from businessos.modules.catalog.models import Product
from businessos.modules.catalog.services import create_simple_product
from businessos.modules.party.models import Party
from businessos.modules.party.services import create_party
from businessos.modules.sales.manifest import MODULE
from businessos.modules.sales.services import create_sales_order


@pytest.fixture(autouse=True)
def sales_permissions(operator, company):
    """Keep accepted Sales behavior tests focused while exercising real RBAC grants."""
    register_manifest(MODULE)
    role = Role.objects.create(company=company, code="sales-test", name="Sales test role")
    for permission in Permission.objects.filter(code__in=MODULE["permissions"]):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return role


@pytest.fixture
def customer(business_context):
    return create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Northwind",
        is_customer=True,
    )


@pytest.fixture
def variant(business_context, uom):
    product = create_simple_product(
        business_context,
        name="Consulting",
        sku="CONSULT-001",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
        sales_description="Consulting day",
    )
    return product.variants.get()


@pytest.fixture
def draft_order(business_context, customer, currency):
    return create_sales_order(
        business_context,
        customer_id=customer.id,
        order_date=date(2026, 9, 13),
        currency_id=currency.id,
        notes="Priority customer",
    )
