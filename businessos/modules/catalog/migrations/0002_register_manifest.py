from django.db import migrations


def register_catalog(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.update_or_create(
        code="catalog",
        defaults={
            "name": "Catalog",
            "version": "0.1.0",
            "dependencies": ["reference", "organization", "access"],
        },
    )


def unregister_catalog(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.filter(code="catalog").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        ("module_registry", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_catalog, unregister_catalog)]
