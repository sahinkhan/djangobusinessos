from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from businessos.core.access.context import SESSION_COMPANY_KEY
from businessos.core.access.models import (
    Permission,
    Role,
    RolePermission,
    UserCompanyAccess,
    UserRoleAssignment,
)
from businessos.core.audit.models import AuditEntry
from businessos.core.modules.models import BusinessModule
from businessos.core.modules.services import register_manifest
from businessos.core.organization.models import Company, Warehouse
from businessos.core.reference.models import UnitOfMeasure
from businessos.modules.catalog.models import Product, ProductVariant
from businessos.modules.catalog.services import create_simple_product, update_product
from businessos.modules.inventory import services
from businessos.modules.inventory.manifest import (
    CREATE_MOVEMENTS,
    INVENTORY_PERMISSION_DECLARATIONS,
    MODULE,
    POST_MOVEMENTS,
    UPDATE_MOVEMENTS,
    VIEW_BALANCES,
    VIEW_MOVEMENTS,
)
from businessos.modules.inventory.models import StockMovement, StockMovementLine
from businessos.modules.inventory.selectors import (
    balances_for_warehouse,
    movement_detail,
    movement_history,
    movements_for_company,
    stock_balance,
)


def add_receipt_line(context, movement, variant, warehouse, quantity="2"):
    return services.add_stock_movement_line(
        context,
        movement_id=movement.id,
        product_variant_id=variant.id,
        quantity=quantity,
        destination_warehouse_id=warehouse.id,
    )


def make_movement(context, movement_type="receipt", **kwargs):
    return services.create_stock_movement(
        context, movement_type=movement_type, effective_at=timezone.now(), **kwargs
    )


def _drop(role, code):
    RolePermission.objects.filter(role=role, permission__code=code).delete()


@pytest.mark.django_db
def test_manifest_permissions_and_enablement_preservation():
    expected = [
        VIEW_MOVEMENTS,
        CREATE_MOVEMENTS,
        UPDATE_MOVEMENTS,
        POST_MOVEMENTS,
        VIEW_BALANCES,
    ]
    module = BusinessModule.objects.get(code="inventory")
    assert MODULE["depends"] == ["catalog", "organization", "reference", "access"]
    assert MODULE["permissions"] == expected
    assert module.declared_permissions == sorted(expected)
    assert not module.is_enabled
    assert list(
        Permission.objects.filter(code__startswith="inventory.")
        .order_by("code")
        .values_list("code", "name")
    ) == sorted(INVENTORY_PERMISSION_DECLARATIONS)
    module.is_enabled = True
    module.save()
    register_manifest(MODULE)
    module.refresh_from_db()
    assert module.is_enabled


@pytest.mark.django_db
@pytest.mark.parametrize("registry_state", ["missing", "disabled"])
def test_registry_state_does_not_disable_python_service(business_context, registry_state):
    if registry_state == "missing":
        BusinessModule.objects.filter(code="inventory").delete()
    else:
        BusinessModule.objects.filter(code="inventory").update(is_enabled=False)
    assert make_movement(business_context).company_id == business_context.company_id


@pytest.mark.django_db
@pytest.mark.parametrize(
    "permission,operation",
    [
        (CREATE_MOVEMENTS, "create"),
        (UPDATE_MOVEMENTS, "update"),
        (UPDATE_MOVEMENTS, "line"),
        (POST_MOVEMENTS, "post"),
    ],
)
def test_each_mutation_permission_denies_without_audit(
    business_context,
    inventory_permissions,
    draft_receipt,
    stockable_variant,
    warehouse,
    permission,
    operation,
):
    line = add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )
    _drop(inventory_permissions, permission)
    before = AuditEntry.objects.count()
    calls = {
        "create": lambda: make_movement(business_context),
        "update": lambda: services.update_stock_movement(
            business_context, movement_id=draft_receipt.id, notes="Denied"
        ),
        "line": lambda: services.update_stock_movement_line(
            business_context,
            movement_id=draft_receipt.id,
            line_id=line.id,
            product_variant_id=stockable_variant.id,
            quantity="3",
            destination_warehouse_id=warehouse.id,
        ),
        "post": lambda: services.post_stock_movement(
            business_context, movement_id=draft_receipt.id
        ),
    }
    with pytest.raises(PermissionDenied, match=permission):
        calls[operation]()
    assert AuditEntry.objects.count() == before


@pytest.mark.django_db
@pytest.mark.parametrize(
    "permission,selector",
    [
        (VIEW_MOVEMENTS, lambda c, w, v: list(movements_for_company(c))),
        (VIEW_MOVEMENTS, lambda c, w, v: movement_detail(c, movement_id=uuid4())),
        (
            VIEW_BALANCES,
            lambda c, w, v: stock_balance(
                c, warehouse_id=w.id, product_variant_id=v.id
            ),
        ),
        (VIEW_BALANCES, lambda c, w, v: balances_for_warehouse(c, warehouse_id=w.id)),
        (VIEW_BALANCES, lambda c, w, v: list(movement_history(c))),
    ],
)
def test_selector_permissions(
    business_context,
    inventory_permissions,
    stockable_variant,
    warehouse,
    permission,
    selector,
):
    _drop(inventory_permissions, permission)
    with pytest.raises(PermissionDenied, match=permission):
        selector(business_context, warehouse, stockable_variant)


@pytest.mark.django_db
def test_receipt_issue_transfer_and_negative_ledger(
    business_context, stockable_variant, warehouse, company, branch
):
    second = Warehouse.objects.create(company=company, branch=branch, code="SECOND", name="Second")
    receipt = make_movement(business_context)
    add_receipt_line(business_context, receipt, stockable_variant, warehouse, "10")
    services.post_stock_movement(business_context, movement_id=receipt.id)

    issue = make_movement(business_context, "issue")
    services.add_stock_movement_line(
        business_context,
        movement_id=issue.id,
        product_variant_id=stockable_variant.id,
        quantity="12",
        source_warehouse_id=warehouse.id,
    )
    services.post_stock_movement(business_context, movement_id=issue.id)
    assert stock_balance(
        business_context, warehouse_id=warehouse.id, product_variant_id=stockable_variant.id
    ) == Decimal("-2")

    transfer = make_movement(business_context, "transfer")
    services.add_stock_movement_line(
        business_context,
        movement_id=transfer.id,
        product_variant_id=stockable_variant.id,
        quantity="3.5000",
        source_warehouse_id=warehouse.id,
        destination_warehouse_id=second.id,
    )
    services.post_stock_movement(business_context, movement_id=transfer.id)
    source = stock_balance(
        business_context, warehouse_id=warehouse.id, product_variant_id=stockable_variant.id
    )
    destination = stock_balance(
        business_context, warehouse_id=second.id, product_variant_id=stockable_variant.id
    )
    assert source == Decimal("-5.5")
    assert destination == Decimal("3.5")
    assert source + destination == Decimal("-2")


@pytest.mark.django_db
def test_draft_is_ignored_by_balances(
    business_context, draft_receipt, stockable_variant, warehouse
):
    add_receipt_line(business_context, draft_receipt, stockable_variant, warehouse, "7")
    assert stock_balance(
        business_context, warehouse_id=warehouse.id, product_variant_id=stockable_variant.id
    ) == 0


@pytest.mark.django_db
@pytest.mark.parametrize("movement_type", StockMovement.Type.values)
def test_route_rules(business_context, stockable_variant, warehouse, movement_type):
    movement = make_movement(business_context, movement_type)
    invalid = {
        "receipt": {"source_warehouse_id": warehouse.id},
        "issue": {"destination_warehouse_id": warehouse.id},
        "transfer": {"source_warehouse_id": warehouse.id},
    }[movement_type]
    with pytest.raises(ValidationError):
        services.add_stock_movement_line(
            business_context,
            movement_id=movement.id,
            product_variant_id=stockable_variant.id,
            quantity="1",
            **invalid,
        )


@pytest.mark.django_db
def test_service_product_and_precision_are_rejected(business_context, warehouse, uom):
    product = create_simple_product(
        business_context,
        name="Service",
        sku="SERVICE-001",
        product_type=Product.Type.SERVICE,
        default_uom_id=uom.id,
    )
    movement = make_movement(business_context)
    with pytest.raises(PermissionDenied, match="stockable or consumable"):
        add_receipt_line(business_context, movement, product.variants.get(), warehouse)
    stockable = create_simple_product(
        business_context,
        name="Precise",
        sku="PRECISE-001",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    ).variants.get()
    add_receipt_line(business_context, movement, stockable, warehouse, "0.0001")
    with pytest.raises(ValidationError, match="4 decimal"):
        add_receipt_line(business_context, movement, stockable, warehouse, "0.00001")


@pytest.mark.django_db
def test_post_retry_is_stable_and_audited_once(
    business_context, draft_receipt, stockable_variant, warehouse
):
    line = add_receipt_line(business_context, draft_receipt, stockable_variant, warehouse)
    posted = services.post_stock_movement(business_context, movement_id=draft_receipt.id)
    retry = services.post_stock_movement(business_context, movement_id=draft_receipt.id)
    assert retry.posted_at == posted.posted_at
    assert StockMovementLine.objects.filter(id=line.id).count() == 1
    assert AuditEntry.objects.filter(
        action="inventory.movement.posted", object_id=str(draft_receipt.id)
    ).count() == 1
    audit = AuditEntry.objects.get(
        action="inventory.movement.posted", object_id=str(draft_receipt.id)
    )
    assert audit.metadata == {
        "number": posted.number,
        "movement_type": "receipt",
        "effective_at": posted.effective_at.isoformat(),
        "line_count": 1,
    }


@pytest.mark.django_db
def test_create_update_line_and_post_audit_vocabulary(
    business_context, draft_receipt, stockable_variant, warehouse
):
    services.update_stock_movement(
        business_context, movement_id=draft_receipt.id, notes="Counted"
    )
    line = add_receipt_line(business_context, draft_receipt, stockable_variant, warehouse)
    services.update_stock_movement_line(
        business_context,
        movement_id=draft_receipt.id,
        line_id=line.id,
        product_variant_id=stockable_variant.id,
        quantity="4",
        destination_warehouse_id=warehouse.id,
    )
    services.post_stock_movement(business_context, movement_id=draft_receipt.id)
    assert set(
        AuditEntry.objects.filter(company_id=business_context.company_id).values_list(
            "action", flat=True
        )
    ) == {
        "inventory.movement.created",
        "inventory.movement.updated",
        "inventory.movement.posted",
    }


@pytest.mark.django_db
def test_mutation_and_audit_roll_back(business_context, monkeypatch):
    def unavailable(**kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(services, "record_audit_entry", unavailable)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        make_movement(business_context)
    assert not StockMovement.objects.exists()


@pytest.mark.django_db
def test_update_line_and_post_roll_back_when_audit_fails(
    business_context,
    draft_receipt,
    stockable_variant,
    warehouse,
    monkeypatch,
):
    line = add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )

    def unavailable(**kwargs):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(services, "record_audit_entry", unavailable)
    with pytest.raises(RuntimeError, match="audit unavailable"):
        services.update_stock_movement(
            business_context, movement_id=draft_receipt.id, notes="rolled back"
        )
    draft_receipt.refresh_from_db()
    assert draft_receipt.notes == ""

    before_lines = draft_receipt.lines.count()
    with pytest.raises(RuntimeError, match="audit unavailable"):
        add_receipt_line(
            business_context, draft_receipt, stockable_variant, warehouse, "1"
        )
    assert draft_receipt.lines.count() == before_lines

    with pytest.raises(RuntimeError, match="audit unavailable"):
        services.post_stock_movement(business_context, movement_id=draft_receipt.id)
    draft_receipt.refresh_from_db()
    assert draft_receipt.status == StockMovement.Status.DRAFT
    assert draft_receipt.posted_at is None
    assert StockMovementLine.objects.get(pk=line.pk).quantity == Decimal("2")


@pytest.mark.django_db
def test_post_validation_failure_leaves_draft(business_context, draft_receipt):
    with pytest.raises(ValidationError, match="at least one line"):
        services.post_stock_movement(business_context, movement_id=draft_receipt.id)
    draft_receipt.refresh_from_db()
    assert draft_receipt.status == StockMovement.Status.DRAFT
    assert draft_receipt.posted_at is None
    assert not AuditEntry.objects.filter(action="inventory.movement.posted").exists()


@pytest.mark.django_db
def test_uom_snapshot_history_and_inactive_rules(
    business_context, draft_receipt, stockable_variant, warehouse, uom
):
    line = add_receipt_line(business_context, draft_receipt, stockable_variant, warehouse)
    assert line.uom_id == uom.id
    services.post_stock_movement(business_context, movement_id=draft_receipt.id)
    uom.is_active = False
    uom.save()
    assert stock_balance(
        business_context, warehouse_id=warehouse.id, product_variant_id=stockable_variant.id
    ) == Decimal("2")
    later = make_movement(business_context)
    with pytest.raises(PermissionDenied, match="active UoM"):
        add_receipt_line(business_context, later, stockable_variant, warehouse)


@pytest.mark.django_db
def test_post_rejects_new_uom_when_variant_has_posted_history(
    business_context, draft_receipt, stockable_variant, warehouse, uom
):
    add_receipt_line(business_context, draft_receipt, stockable_variant, warehouse, "10")
    services.post_stock_movement(business_context, movement_id=draft_receipt.id)

    kilograms = UnitOfMeasure.objects.create(code="KG", name="Kilogram", symbol="kg")
    update_product(
        business_context,
        product_id=stockable_variant.product_id,
        default_uom_id=kilograms.id,
    )
    conflicting = make_movement(business_context)
    add_receipt_line(business_context, conflicting, stockable_variant, warehouse, "5")

    with pytest.raises(ValidationError, match="posted stock history"):
        services.post_stock_movement(business_context, movement_id=conflicting.id)

    conflicting.refresh_from_db()
    assert conflicting.status == StockMovement.Status.DRAFT
    assert stock_balance(
        business_context,
        warehouse_id=warehouse.id,
        product_variant_id=stockable_variant.id,
    ) == Decimal("10")


@pytest.mark.django_db
def test_balance_selectors_fail_closed_for_mixed_uom_history(
    business_context, stockable_variant, warehouse
):
    first = make_movement(business_context)
    add_receipt_line(business_context, first, stockable_variant, warehouse, "10")
    services.post_stock_movement(business_context, movement_id=first.id)
    second = make_movement(business_context)
    second_line = add_receipt_line(
        business_context, second, stockable_variant, warehouse, "5"
    )
    services.post_stock_movement(business_context, movement_id=second.id)
    kilograms = UnitOfMeasure.objects.create(code="KG", name="Kilogram", symbol="kg")
    models.QuerySet.update(
        StockMovementLine.objects.filter(pk=second_line.pk), uom_id=kilograms.id
    )

    with pytest.raises(ValidationError, match="incompatible units"):
        stock_balance(
            business_context,
            warehouse_id=warehouse.id,
            product_variant_id=stockable_variant.id,
        )
    with pytest.raises(ValidationError, match="incompatible units"):
        balances_for_warehouse(business_context, warehouse_id=warehouse.id)


@pytest.mark.django_db
def test_idempotency_source_and_number_contract(business_context):
    source_id = uuid4()
    first = make_movement(
        business_context,
        idempotency_key=" key ",
        source_module="external",
        source_type="receipt",
        source_id=source_id,
    )
    assert first.idempotency_key == "key"
    assert first.number.startswith("SM-") and len(first.number) == 35
    with pytest.raises(ValidationError, match="already in use"):
        make_movement(business_context, idempotency_key="key")
    with pytest.raises(ValidationError, match="supplied together"):
        make_movement(business_context, source_module="procurement")
    with pytest.raises(ValidationError, match="Unsupported Stock Movement fields"):
        services.update_stock_movement(
            business_context, movement_id=first.id, number="CALLER-NUMBER"
        )


@pytest.mark.django_db
def test_company_isolation_for_movement_variant_and_warehouse(
    business_context, stockable_variant, warehouse, company, currency, country, language
):
    from businessos.core.access.models import UserCompanyAccess
    from businessos.core.common.context import BusinessContext
    from businessos.core.organization.models import Company

    other = Company.objects.create(
        code="OTHER",
        name="Other",
        base_currency=currency,
        country=country,
        default_language=language,
    )
    other_warehouse = Warehouse.objects.create(company=other, code="OTHER", name="Other")
    movement = make_movement(business_context)
    with pytest.raises(PermissionDenied, match="selected company"):
        services.add_stock_movement_line(
            business_context,
            movement_id=movement.id,
            product_variant_id=stockable_variant.id,
            quantity="1",
            destination_warehouse_id=other_warehouse.id,
        )
    unauthorized = BusinessContext(actor_id=business_context.actor_id, company_id=other.id)
    with pytest.raises(PermissionDenied, match="access to this company"):
        list(movements_for_company(unauthorized))
    UserCompanyAccess.objects.create(user_id=business_context.actor_id, company=other)
    with pytest.raises(PermissionDenied, match=VIEW_MOVEMENTS):
        list(movements_for_company(unauthorized))


@pytest.mark.django_db
def test_module_gating_and_stale_company_forms(client, operator, company):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    module = BusinessModule.objects.get(code="inventory")
    assert client.get(reverse("inventory:list")).status_code == 404
    assert b'href="/inventory/movements/"' not in client.get(reverse("home")).content
    module.is_enabled = True
    module.save()
    assert client.get(reverse("inventory:list")).status_code == 200
    assert b'href="/inventory/movements/"' in client.get(reverse("home")).content
    response = client.post(
        reverse("inventory:create"),
        {
            "scope_company_id": uuid4(),
            "movement_type": "receipt",
            "effective_at": (timezone.now() - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M"),
        },
    )
    assert response.status_code == 200
    assert b"Company scope changed" in response.content


@pytest.mark.django_db
def test_http_mutation_forms_require_their_action_permissions(
    client,
    operator,
    company,
    business_context,
    inventory_permissions,
    draft_receipt,
    stockable_variant,
    warehouse,
):
    register_manifest(MODULE, enabled=True)
    line = add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    RolePermission.objects.filter(role=inventory_permissions).exclude(
        permission__code=VIEW_MOVEMENTS
    ).delete()

    movement_list = client.get(reverse("inventory:list"))
    detail = client.get(reverse("inventory:detail", args=[draft_receipt.id]))
    assert movement_list.status_code == 200
    assert b"Create movement" not in movement_list.content
    assert detail.status_code == 200
    assert b">Edit<" not in detail.content
    assert b">Add line<" not in detail.content
    assert b">Post movement<" not in detail.content
    assert client.get(reverse("inventory:create")).status_code == 403
    assert client.get(reverse("inventory:edit", args=[draft_receipt.id])).status_code == 403
    assert (
        client.get(reverse("inventory:line_create", args=[draft_receipt.id])).status_code
        == 403
    )
    assert (
        client.get(
            reverse("inventory:line_edit", args=[draft_receipt.id, line.id])
        ).status_code
        == 403
    )
    assert (
        client.post(
            reverse("inventory:line_remove", args=[draft_receipt.id, line.id]),
            {"scope_company_id": company.id},
        ).status_code
        == 403
    )
    assert (
        client.post(
            reverse("inventory:post", args=[draft_receipt.id]),
            {"scope_company_id": company.id},
        ).status_code
        == 403
    )


@pytest.mark.django_db
def test_stale_company_http_matrix_preserves_movement_and_line(
    client,
    operator,
    company,
    currency,
    country,
    language,
    business_context,
    draft_receipt,
    stockable_variant,
    warehouse,
):
    register_manifest(MODULE, enabled=True)
    line = add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    assert client.get(reverse("inventory:create")).status_code == 200
    assert client.get(reverse("inventory:edit", args=[draft_receipt.id])).status_code == 200
    assert (
        client.get(reverse("inventory:line_create", args=[draft_receipt.id])).status_code
        == 200
    )
    assert (
        client.get(
            reverse("inventory:line_edit", args=[draft_receipt.id, line.id])
        ).status_code
        == 200
    )

    switched = Company.objects.create(
        code="SWITCHED",
        name="Switched Company",
        base_currency=currency,
        country=country,
        default_language=language,
    )
    UserCompanyAccess.objects.create(user=operator, company=switched)
    switched_role = Role.objects.create(
        company=switched, code="INVENTORY", name="Inventory"
    )
    for permission in Permission.objects.filter(code__in=MODULE["permissions"]):
        RolePermission.objects.create(role=switched_role, permission=permission)
    UserRoleAssignment.objects.create(
        user=operator, company=switched, role=switched_role
    )
    session = client.session
    session[SESSION_COMPANY_KEY] = str(switched.id)
    session.save()

    stale_scope = str(company.id)
    create_response = client.post(
        reverse("inventory:create"),
        {
            "scope_company_id": stale_scope,
            "movement_type": StockMovement.Type.RECEIPT,
            "effective_at": (timezone.now() - timedelta(minutes=1)).strftime(
                "%Y-%m-%dT%H:%M"
            ),
        },
    )
    assert create_response.status_code == 200
    assert b"Company scope changed" in create_response.content
    assert (
        client.post(
            reverse("inventory:edit", args=[draft_receipt.id]),
            {"scope_company_id": stale_scope},
        ).status_code
        == 404
    )
    assert (
        client.post(
            reverse("inventory:line_create", args=[draft_receipt.id]),
            {"scope_company_id": stale_scope},
        ).status_code
        == 404
    )
    assert (
        client.post(
            reverse("inventory:line_edit", args=[draft_receipt.id, line.id]),
            {"scope_company_id": stale_scope},
        ).status_code
        == 404
    )
    assert (
        client.post(
            reverse("inventory:line_remove", args=[draft_receipt.id, line.id]),
            {"scope_company_id": stale_scope},
        ).status_code
        == 302
    )
    assert (
        client.post(
            reverse("inventory:post", args=[draft_receipt.id]),
            {"scope_company_id": stale_scope},
        ).status_code
        == 302
    )
    draft_receipt.refresh_from_db()
    line.refresh_from_db()
    assert draft_receipt.status == StockMovement.Status.DRAFT
    assert draft_receipt.notes == ""
    assert line.quantity == Decimal("2")


@pytest.mark.django_db
def test_missing_module_registry_blocks_navigation_and_http(client, operator, company):
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()
    BusinessModule.objects.filter(code="inventory").delete()
    assert client.get(reverse("inventory:list")).status_code == 404
    assert b'href="/inventory/movements/"' not in client.get(reverse("home")).content


@pytest.mark.django_db
@pytest.mark.parametrize("revocation", ["role", "permission", "company_access"])
def test_inactive_or_revoked_foundation_authority_fails_closed(
    business_context,
    inventory_permissions,
    revocation,
):
    if revocation == "role":
        inventory_permissions.is_active = False
        inventory_permissions.save()
    elif revocation == "permission":
        permission = Permission.objects.get(code=CREATE_MOVEMENTS)
        permission.is_active = False
        permission.save()
    else:
        UserCompanyAccess.objects.filter(
            user_id=business_context.actor_id,
            company_id=business_context.company_id,
        ).delete()
    with pytest.raises(PermissionDenied):
        make_movement(business_context)


@pytest.mark.django_db
def test_default_deny_module_enablement_and_superuser_contract(
    business_context,
    inventory_permissions,
    company,
    django_user_model,
):
    UserRoleAssignment.objects.filter(role=inventory_permissions).delete()
    BusinessModule.objects.filter(code="inventory").update(is_enabled=True)
    with pytest.raises(PermissionDenied, match=CREATE_MOVEMENTS):
        make_movement(business_context)

    root = django_user_model.objects.create_superuser("inventory-root@example.com", "password")
    root_context = type(business_context)(actor_id=root.id, company_id=company.id)
    assert make_movement(root_context).company_id == company.id


@pytest.mark.django_db
def test_malformed_cross_company_role_assignment_cannot_authorize(
    business_context,
    inventory_permissions,
    company,
    currency,
    country,
    language,
):
    from django.db import models

    other = type(company).objects.create(
        code="ROLE-OTHER",
        name="Role other",
        base_currency=currency,
        country=country,
        default_language=language,
    )
    other_role = Role.objects.create(company=other, code="INVENTORY", name="Other role")
    for permission in Permission.objects.filter(code__in=MODULE["permissions"]):
        RolePermission.objects.create(role=other_role, permission=permission)
    assignment = UserRoleAssignment.objects.get(role=inventory_permissions)
    models.QuerySet.update(
        UserRoleAssignment.objects.filter(pk=assignment.pk), role_id=other_role.id
    )
    with pytest.raises(PermissionDenied, match=CREATE_MOVEMENTS):
        make_movement(business_context)


@pytest.mark.django_db
def test_no_authoritative_stock_field():
    for model in (Product, ProductVariant, StockMovement, StockMovementLine, Warehouse):
        assert "stock" not in {field.name for field in model._meta.fields}


@pytest.mark.django_db
def test_movement_form_interprets_effective_time_in_company_timezone(company):
    from businessos.modules.inventory.forms import MovementForm

    company.timezone = "Asia/Dhaka"
    company.save()
    form = MovementForm(
        {
            "scope_company_id": company.id,
            "movement_type": "receipt",
            "effective_at": "2026-09-15T08:30",
            "reference": "",
            "notes": "",
        },
        company_id=company.id,
    )
    assert form.is_valid(), form.errors
    effective_at = form.cleaned_data["effective_at"]
    assert effective_at.utcoffset() == timedelta(hours=6)
    assert effective_at.hour == 8


@pytest.mark.django_db
def test_movement_edit_renders_and_preserves_company_local_effective_time(
    client, operator, company, business_context
):
    company.timezone = "Asia/Dhaka"
    company.save()
    register_manifest(MODULE, enabled=True)
    instant = datetime(2026, 9, 15, 2, 30, tzinfo=UTC)
    movement = services.create_stock_movement(
        business_context,
        movement_type=StockMovement.Type.RECEIPT,
        effective_at=instant,
    )
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()

    url = reverse("inventory:edit", args=[movement.id])
    response = client.get(url)
    assert response.status_code == 200
    assert b'value="2026-09-15T08:30"' in response.content

    response = client.post(
        url,
        {
            "scope_company_id": company.id,
            "movement_type": StockMovement.Type.RECEIPT,
            "effective_at": "2026-09-15T08:30",
            "reference": "",
            "notes": "",
        },
    )
    assert response.status_code == 302
    movement.refresh_from_db()
    assert movement.effective_at == instant


@pytest.mark.django_db
@pytest.mark.parametrize("wall_time", ["2026-03-08T02:30", "2026-11-01T01:30"])
def test_movement_form_rejects_nonexistent_and_ambiguous_company_times(
    company, wall_time
):
    from businessos.modules.inventory.forms import MovementForm

    company.timezone = "America/New_York"
    company.save()
    form = MovementForm(
        {
            "scope_company_id": company.id,
            "movement_type": StockMovement.Type.RECEIPT,
            "effective_at": wall_time,
            "reference": "",
            "notes": "",
        },
        company_id=company.id,
    )
    assert not form.is_valid()
    assert "effective_at" in form.errors
    assert "ambiguous or it may not exist" in form.errors["effective_at"][0]


@pytest.mark.django_db
def test_movement_form_accepts_ordinary_new_york_company_time(company):
    from businessos.modules.inventory.forms import MovementForm

    company.timezone = "America/New_York"
    company.save()
    form = MovementForm(
        {
            "scope_company_id": company.id,
            "movement_type": StockMovement.Type.RECEIPT,
            "effective_at": "2026-03-08T03:30",
            "reference": "",
            "notes": "",
        },
        company_id=company.id,
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["effective_at"].astimezone(UTC) == datetime(
        2026, 3, 8, 7, 30, tzinfo=UTC
    )


@pytest.mark.django_db
def test_combined_history_filters_require_one_matching_line(
    business_context, stockable_variant, warehouse, company, branch, uom
):
    other_warehouse = Warehouse.objects.create(
        company=company, branch=branch, code="SECOND", name="Second warehouse"
    )
    other_variant = create_simple_product(
        business_context,
        name="Other tracked item",
        sku="STOCK-002",
        product_type=Product.Type.STOCKABLE,
        default_uom_id=uom.id,
    ).variants.get()

    split_match = make_movement(business_context)
    add_receipt_line(
        business_context, split_match, stockable_variant, other_warehouse
    )
    add_receipt_line(business_context, split_match, other_variant, warehouse)
    services.post_stock_movement(business_context, movement_id=split_match.id)

    exact_match = make_movement(business_context)
    add_receipt_line(business_context, exact_match, stockable_variant, warehouse)
    services.post_stock_movement(business_context, movement_id=exact_match.id)

    result_ids = set(
        movement_history(
            business_context,
            warehouse_id=warehouse.id,
            product_variant_id=stockable_variant.id,
        ).values_list("id", flat=True)
    )
    assert exact_match.id in result_ids
    assert split_match.id not in result_ids


@pytest.mark.django_db
def test_line_snapshot_and_uom_refresh_is_audited_but_true_noop_is_not(
    business_context, draft_receipt, stockable_variant, warehouse
):
    line = add_receipt_line(
        business_context, draft_receipt, stockable_variant, warehouse
    )
    kilograms = UnitOfMeasure.objects.create(code="KGS", name="Kilograms", symbol="kg")
    update_product(
        business_context,
        product_id=stockable_variant.product_id,
        name="Renamed tracked item",
        sku="STOCK-RENAMED",
        default_uom_id=kilograms.id,
    )

    services.update_stock_movement_line(
        business_context,
        movement_id=draft_receipt.id,
        line_id=line.id,
        product_variant_id=stockable_variant.id,
        quantity=line.quantity,
        destination_warehouse_id=warehouse.id,
    )
    line.refresh_from_db()
    updates = [
        entry
        for entry in AuditEntry.objects.filter(
            action="inventory.movement.updated", object_id=str(draft_receipt.id)
        )
        if entry.metadata.get("change") == "line_updated"
    ]
    assert len(updates) == 1
    assert updates[0].metadata["fields"] == [
        "product_name_snapshot",
        "sku_snapshot",
        "uom_id",
    ]
    assert line.product_name_snapshot == "Renamed tracked item"
    assert line.sku_snapshot == "STOCK-RENAMED"
    assert line.uom_id == kilograms.id

    services.update_stock_movement_line(
        business_context,
        movement_id=draft_receipt.id,
        line_id=line.id,
        product_variant_id=stockable_variant.id,
        quantity=line.quantity,
        destination_warehouse_id=warehouse.id,
    )
    assert len(
        [
            entry
            for entry in AuditEntry.objects.filter(
                action="inventory.movement.updated", object_id=str(draft_receipt.id)
            )
            if entry.metadata.get("change") == "line_updated"
        ]
    ) == 1


@pytest.mark.django_db
def test_balance_http_permission_is_checked_before_form_construction(
    client, operator, company, inventory_permissions, monkeypatch
):
    from businessos.modules.inventory import views

    register_manifest(MODULE, enabled=True)
    _drop(inventory_permissions, VIEW_BALANCES)
    client.force_login(operator)
    session = client.session
    session[SESSION_COMPANY_KEY] = str(company.id)
    session.save()

    def unexpected_form_construction(*args, **kwargs):
        raise AssertionError("The filter form was constructed before balance authorization.")

    monkeypatch.setattr(views, "BalanceFilterForm", unexpected_form_construction)
    monkeypatch.setattr(views, "HistoryFilterForm", unexpected_form_construction)
    assert client.get(reverse("inventory:balances")).status_code == 403
    assert client.get(reverse("inventory:history")).status_code == 403
