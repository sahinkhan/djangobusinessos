from django.db import migrations

SALES_PERMISSION_DECLARATIONS = (
    ("sales.order.view", "View sales orders"),
    ("sales.order.create", "Create sales orders"),
    ("sales.order.update", "Update draft sales orders"),
    ("sales.order.confirm", "Confirm sales orders"),
    ("sales.order.cancel", "Cancel confirmed sales orders"),
)


def register_sales(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    permission = apps.get_model("access", "Permission")
    business_module.objects.update_or_create(
        code="sales",
        defaults={
            "name": "Sales",
            "version": "0.1.0",
            "dependencies": ["party", "catalog", "organization", "reference", "access"],
            "declared_permissions": sorted(
                code for code, _name in SALES_PERMISSION_DECLARATIONS
            ),
        },
    )
    for code, name in SALES_PERMISSION_DECLARATIONS:
        permission.objects.get_or_create(
            code=code,
            defaults={"name": name, "is_active": True},
        )


def unregister_sales(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.filter(code="sales").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0003_register_core_permissions"),
        ("sales", "0001_initial"),
        ("module_registry", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_sales, unregister_sales)]
