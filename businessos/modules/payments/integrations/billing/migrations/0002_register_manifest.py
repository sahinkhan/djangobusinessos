from django.db import migrations

PERMISSIONS = (
    ("payments_billing.allocation.view", "View payment allocation evidence"),
    ("payments_billing.allocation.create", "Create payment allocations"),
)


def register(apps, schema_editor):
    alias = schema_editor.connection.alias
    apps.get_model("module_registry", "BusinessModule").objects.using(alias).update_or_create(
        code="payments_billing",
        defaults={
            "name": "Payment allocations",
            "version": "0.1.0",
            "dependencies": ["billing", "payments"],
            "declared_permissions": sorted(code for code, _ in PERMISSIONS),
        },
    )
    for code, name in PERMISSIONS:
        apps.get_model("access", "Permission").objects.using(alias).get_or_create(
            code=code,
            defaults={"name": name, "is_active": True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("payments_billing", "0001_initial"),
        ("access", "0003_register_core_permissions"),
        ("module_registry", "0001_initial"),
    ]
    operations = [migrations.RunPython(register, migrations.RunPython.noop)]
