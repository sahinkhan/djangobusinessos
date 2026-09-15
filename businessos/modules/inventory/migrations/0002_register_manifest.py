from django.db import migrations

INVENTORY_PERMISSION_DECLARATIONS = (
    ("inventory.movement.view", "View stock movements"),
    ("inventory.movement.create", "Create draft stock movements"),
    (
        "inventory.movement.update",
        "Update draft stock movements and movement lines",
    ),
    ("inventory.movement.post", "Post stock movements"),
    ("inventory.balance.view", "View derived stock balances and stock history"),
)


def register_inventory(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    permission = apps.get_model("access", "Permission")
    business_module.objects.update_or_create(
        code="inventory",
        defaults={
            "name": "Inventory",
            "version": "0.1.0",
            "dependencies": ["catalog", "organization", "reference", "access"],
            "declared_permissions": sorted(
                code for code, _name in INVENTORY_PERMISSION_DECLARATIONS
            ),
        },
    )
    for code, name in INVENTORY_PERMISSION_DECLARATIONS:
        permission.objects.get_or_create(
            code=code, defaults={"name": name, "is_active": True}
        )


def unregister_inventory(apps, schema_editor):
    apps.get_model("module_registry", "BusinessModule").objects.filter(
        code="inventory"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0003_register_core_permissions"),
        ("inventory", "0001_initial"),
        ("module_registry", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_inventory, unregister_inventory)]
