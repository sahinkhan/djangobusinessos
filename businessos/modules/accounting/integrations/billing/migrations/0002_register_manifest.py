from django.db import migrations

PERMISSIONS = (
    ("accounting_billing.posting.view", "View invoice Accounting outcomes"),
    ("accounting_billing.posting.create", "Post invoice Accounting outcomes"),
)


def register(apps, schema_editor):
    alias = schema_editor.connection.alias
    apps.get_model("module_registry", "BusinessModule").objects.using(alias).update_or_create(
        code="accounting_billing",
        defaults={
            "name": "Invoice Accounting",
            "version": "0.1.0",
            "dependencies": ["accounting", "billing"],
            "declared_permissions": [code for code, _ in PERMISSIONS],
        },
    )
    for code, name in PERMISSIONS:
        apps.get_model("access", "Permission").objects.using(alias).get_or_create(
            code=code, defaults={"name": name, "is_active": True}
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounting_billing", "0001_initial"),
        ("module_registry", "0001_initial"),
        ("access", "0003_register_core_permissions"),
    ]
    operations = [migrations.RunPython(register, migrations.RunPython.noop)]
