import ast
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from django.core.exceptions import PermissionDenied

from businessos.core.access.models import Permission, RolePermission
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.services import register_manifest
from businessos.modules.procurement import services
from businessos.modules.procurement.forms import PurchaseOrderForm, PurchaseReceiptForm
from businessos.modules.procurement.manifest import (
    CANCEL_ORDERS,
    CONFIRM_ORDERS,
    CREATE_ORDERS,
    MODULE,
    PROCUREMENT_PERMISSION_DECLARATIONS,
    RECEIVE_ORDERS,
    UPDATE_ORDERS,
    VIEW_ORDERS,
)
from businessos.modules.procurement.models import PurchaseOrder
from businessos.modules.procurement.selectors import purchase_orders_for_company


def _drop(role, code):
    RolePermission.objects.filter(role=role, permission__code=code).delete()


@pytest.mark.django_db
def test_manifest_bootstrap_exact_permissions_and_preserves_enablement():
    expected = [
        VIEW_ORDERS,
        CREATE_ORDERS,
        UPDATE_ORDERS,
        CONFIRM_ORDERS,
        CANCEL_ORDERS,
        RECEIVE_ORDERS,
    ]
    module = BusinessModule.objects.get(code="procurement")
    assert MODULE["permissions"] == expected
    assert module.declared_permissions == sorted(expected)
    assert not module.is_enabled
    assert list(
        Permission.objects.filter(code__startswith="procurement.")
        .order_by("code")
        .values_list("code", "name")
    ) == sorted(PROCUREMENT_PERMISSION_DECLARATIONS)
    module.is_enabled = True
    module.save()
    register_manifest(MODULE)
    module.refresh_from_db()
    assert module.is_enabled


@pytest.mark.django_db
@pytest.mark.parametrize("registry_state", ["disabled", "missing"])
def test_registry_state_does_not_disable_installed_service(
    business_context, supplier, currency, registry_state
):
    if registry_state == "missing":
        BusinessModule.objects.filter(code="procurement").delete()
    else:
        BusinessModule.objects.filter(code="procurement").update(is_enabled=False)
    order = services.create_purchase_order(
        business_context,
        supplier_id=supplier.id,
        order_date=date(2026, 9, 14),
        currency_id=currency.id,
    )
    assert order.company_id == business_context.company_id


@pytest.mark.django_db
@pytest.mark.parametrize(
    "permission,operation",
    [
        (CREATE_ORDERS, "create"),
        (UPDATE_ORDERS, "update"),
        (CONFIRM_ORDERS, "confirm"),
        (CANCEL_ORDERS, "cancel"),
        (RECEIVE_ORDERS, "receive"),
    ],
)
def test_each_mutation_permission_denies_without_audit(
    business_context,
    procurement_permissions,
    supplier,
    currency,
    draft_purchase_order,
    purchasable_variant,
    permission,
    operation,
):
    line = services.add_purchase_order_line(
        business_context,
        order_id=draft_purchase_order.id,
        product_variant_id=purchasable_variant.id,
        quantity=1,
        unit_cost=1,
    )
    if operation in {"cancel", "receive"}:
        services.confirm_purchase_order(business_context, order_id=draft_purchase_order.id)
    _drop(procurement_permissions, permission)
    before = AuditEntry.objects.count()
    actions = {
        "create": lambda: services.create_purchase_order(
            business_context,
            supplier_id=supplier.id,
            order_date=date(2026, 9, 14),
            currency_id=currency.id,
        ),
        "update": lambda: services.update_purchase_order(
            business_context, order_id=draft_purchase_order.id, notes="Denied"
        ),
        "confirm": lambda: services.confirm_purchase_order(
            business_context, order_id=draft_purchase_order.id
        ),
        "cancel": lambda: services.cancel_purchase_order(
            business_context, order_id=draft_purchase_order.id
        ),
        "receive": lambda: services.receive_purchase_order(
            business_context,
            purchase_order_id=draft_purchase_order.id,
            receipt_date=date(2026, 9, 14),
            idempotency_key="denied",
            lines=[{"purchase_order_line_id": line.id, "quantity_received": "1"}],
        ),
    }
    with pytest.raises(PermissionDenied, match=permission):
        actions[operation]()
    assert AuditEntry.objects.count() == before


@pytest.mark.django_db
def test_view_permission_required(business_context, procurement_permissions):
    _drop(procurement_permissions, VIEW_ORDERS)
    with pytest.raises(PermissionDenied, match=VIEW_ORDERS):
        list(purchase_orders_for_company(business_context))


@pytest.mark.django_db
def test_mutation_and_audit_rollback_together(business_context, supplier, currency, monkeypatch):
    def unavailable(**kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(services, "record_audit_entry", unavailable)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        services.create_purchase_order(
            business_context,
            supplier_id=supplier.id,
            order_date=date(2026, 9, 14),
            currency_id=currency.id,
        )
    assert not PurchaseOrder.objects.exists()


@pytest.mark.django_db
def test_forms_use_company_local_date(company, draft_purchase_order, monkeypatch):
    expected = date(2026, 9, 15)
    monkeypatch.setattr(
        "businessos.modules.procurement.forms.company_local_date", lambda _id: expected
    )
    assert PurchaseOrderForm(company_id=company.id).initial["order_date"] == expected
    detail = type(
        "Detail",
        (),
        {"id": draft_purchase_order.id, "sku_snapshot": "SKU", "remaining_quantity": Decimal("1")},
    )()
    assert (
        PurchaseReceiptForm(company_id=company.id, order_lines=[detail]).initial["receipt_date"]
        == expected
    )


def test_procurement_has_no_downstream_imports():
    root = Path(__file__).resolve().parents[1]
    forbidden = (
        "businessos.modules.sales",
        "businessos.modules.inventory",
        "businessos.modules.billing",
        "businessos.modules.accounting",
    )
    imported = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    assert not any(name.startswith(forbidden) for name in imported)
