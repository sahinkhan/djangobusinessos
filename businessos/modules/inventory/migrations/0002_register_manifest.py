from django.db import migrations


def register_inventory(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.update_or_create(
        code="inventory",
        defaults={
            "name": "Inventory",
            "version": "0.1.0",
            "dependencies": ["catalog", "organization", "access"],
        },
    )


def unregister_inventory(apps, schema_editor):
    apps.get_model("module_registry", "BusinessModule").objects.filter(
        code="inventory"
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0001_initial"),
        ("module_registry", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_inventory, unregister_inventory)]
