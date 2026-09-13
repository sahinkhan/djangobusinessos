from django.db import migrations


def register_procurement(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.update_or_create(
        code="procurement",
        defaults={
            "name": "Procurement",
            "version": "0.1.0",
            "dependencies": ["party", "catalog", "organization", "reference", "access"],
            "is_enabled": False,
        },
    )


def unregister_procurement(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.filter(code="procurement").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("procurement", "0001_initial"),
        ("module_registry", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_procurement, unregister_procurement)]
