from django.db import migrations

PERMISSIONS = (
    ("payments.method.view", "View payment methods"),
    ("payments.method.manage", "Manage payment methods"),
    ("payments.payment.view", "View payment receipts"),
    ("payments.payment.record", "Record payment receipts"),
)


def register_payments(apps, schema_editor):
    alias = schema_editor.connection.alias
    apps.get_model("module_registry", "BusinessModule").objects.using(alias).update_or_create(
        code="payments",
        defaults={
            "name": "Payments", "version": "0.1.0",
            "dependencies": ["party", "organization", "reference", "access"],
            "declared_permissions": sorted(code for code, _ in PERMISSIONS),
        },
    )
    for code, name in PERMISSIONS:
        apps.get_model("access", "Permission").objects.using(alias).get_or_create(
            code=code, defaults={"name": name, "is_active": True},
        )


def unregister_payments(apps, schema_editor):
    apps.get_model("module_registry", "BusinessModule").objects.using(
        schema_editor.connection.alias
    ).filter(code="payments").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0001_initial"), ("access", "0003_register_core_permissions"),
        ("module_registry", "0001_initial"),
    ]
    operations = [migrations.RunPython(register_payments, unregister_payments)]
