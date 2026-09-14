from datetime import date

import pytest

from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserRoleAssignment,
)
from businessos.core.modules.services import register_manifest
from businessos.modules.catalog.models import Product
from businessos.modules.catalog.services import create_simple_product
from businessos.modules.party.models import Party
from businessos.modules.party.services import create_party
from businessos.modules.procurement.manifest import MODULE
from businessos.modules.procurement.services import create_purchase_order


@pytest.fixture(autouse=True)
def procurement_permissions(operator, company):
    register_manifest(MODULE)
    role = Role.objects.create(
        company=company, code="procurement-test", name="Procurement test role"
    )
    for permission in Permission.objects.filter(code__in=MODULE["permissions"]):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return role


@pytest.fixture
def supplier(business_context):
    return create_party(
        business_context,
        party_type=Party.Type.ORGANIZATION,
        display_name="Northwind Supplier",
        is_supplier=True,
    )


@pytest.fixture
def purchasable_variant(business_context, uom):
    product = create_simple_product(
        business_context,
        name="Purchased consulting",
        sku="BUY-001",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
        purchase_description="Supplier service day",
    )
    return product.variants.get()


@pytest.fixture
def draft_purchase_order(business_context, supplier, currency):
    return create_purchase_order(
        business_context,
        supplier_id=supplier.id,
        order_date=date(2026, 9, 14),
        currency_id=currency.id,
        notes="Priority supplier",
    )
