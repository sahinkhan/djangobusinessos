from django.db import migrations

PROCUREMENT_PERMISSION_DECLARATIONS = (
    ("procurement.order.view", "View purchase orders and purchase receipts"),
    ("procurement.order.create", "Create purchase orders"),
    ("procurement.order.update", "Update draft purchase orders"),
    ("procurement.order.confirm", "Confirm purchase orders"),
    ("procurement.order.cancel", "Cancel confirmed purchase orders"),
    ("procurement.receipt.receive", "Post purchase receipts"),
)


def register_procurement(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    permission = apps.get_model("access", "Permission")
    business_module.objects.update_or_create(
        code="procurement",
        defaults={
            "name": "Procurement",
            "version": "0.1.0",
            "dependencies": [
                "party",
                "catalog",
                "organization",
                "reference",
                "access",
            ],
            "declared_permissions": sorted(
                code for code, _name in PROCUREMENT_PERMISSION_DECLARATIONS
            ),
        },
    )
    for code, name in PROCUREMENT_PERMISSION_DECLARATIONS:
        permission.objects.get_or_create(
            code=code, defaults={"name": name, "is_active": True}
        )


def unregister_procurement(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.filter(code="procurement").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0003_register_core_permissions"),
        ("procurement", "0001_initial"),
        ("module_registry", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_procurement, unregister_procurement)]
