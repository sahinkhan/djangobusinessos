from django.db import migrations

PERMISSIONS = (
    ("accounting.account.view", "View accounts"),
    ("accounting.account.manage", "Manage accounts"),
    ("accounting.journal.view", "View journals"),
    ("accounting.journal.manage", "Manage journals"),
    ("accounting.entry.view", "View journal entries and reports"),
    ("accounting.entry.create", "Create journal entries"),
    ("accounting.entry.update", "Update draft journal entries"),
    ("accounting.entry.post", "Post journal entries"),
)


def register_accounting(apps, schema_editor):
    alias = schema_editor.connection.alias
    apps.get_model("module_registry", "BusinessModule").objects.using(alias).update_or_create(
        code="accounting", defaults={
            "name": "Accounting & Finance", "version": "0.1.0",
            "dependencies": ["party", "organization", "reference", "access"],
            "declared_permissions": sorted(code for code, _ in PERMISSIONS),
        },
    )
    for code, name in PERMISSIONS:
        apps.get_model("access", "Permission").objects.using(alias).get_or_create(
            code=code, defaults={"name": name, "is_active": True},
        )


def unregister_accounting(apps, schema_editor):
    apps.get_model("module_registry", "BusinessModule").objects.using(
        schema_editor.connection.alias,
    ).filter(code="accounting").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounting", "0001_initial"), ("access", "0003_register_core_permissions"),
        ("module_registry", "0001_initial"),
    ]
    operations = [migrations.RunPython(register_accounting, unregister_accounting)]
