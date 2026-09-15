import pytest

from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserRoleAssignment,
)
from businessos.core.modules.services import register_manifest
from businessos.core.organization.models import Branch, Warehouse
from businessos.modules.catalog.models import Product
from businessos.modules.catalog.services import create_simple_product
from businessos.modules.inventory.manifest import MODULE
from businessos.modules.inventory.services import create_stock_movement


@pytest.fixture(autouse=True)
def inventory_permissions(operator, company):
    register_manifest(MODULE)
    role = Role.objects.create(company=company, code="inventory-test", name="Inventory test role")
    for permission in Permission.objects.filter(code__in=MODULE["permissions"]):
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(user=operator, company=company, role=role)
    return role


@pytest.fixture
def stockable_variant(business_context, uom):
    product = create_simple_product(
        business_context,
        name="Tracked item",
        sku="STOCK-001",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    )
    return product.variants.get()


@pytest.fixture
def draft_receipt(business_context):
    from django.utils import timezone

    return create_stock_movement(
        business_context,
        movement_type="receipt",
        effective_at=timezone.now(),
        reference="Opening receipt",
    )


@pytest.fixture
def branch(company):
    return Branch.objects.create(company=company, code="MAIN", name="Main branch")


@pytest.fixture
def warehouse(company, branch):
    return Warehouse.objects.create(
        company=company,
        branch=branch,
        code="MAIN",
        name="Main warehouse",
    )
