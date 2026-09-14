from django.db import migrations


CATALOG_MANIFEST = {
    "code": "catalog",
    "name": "Catalog",
    "version": "0.1.0",
    "dependencies": ["reference", "organization", "access"],
    "declared_permissions": [],
}


def register_catalog(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.update_or_create(
        code=CATALOG_MANIFEST["code"],
        defaults={key: value for key, value in CATALOG_MANIFEST.items() if key != "code"},
    )


def unregister_catalog(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.filter(code=CATALOG_MANIFEST["code"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        ("module_registry", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_catalog, unregister_catalog)]
