from django.db import migrations


def register_sales(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.update_or_create(
        code="sales",
        defaults={
            "name": "Sales",
            "version": "0.1.0",
            "dependencies": ["party", "catalog", "organization", "reference", "access"],
        },
    )


def unregister_sales(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.filter(code="sales").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0001_initial"),
        ("module_registry", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_sales, unregister_sales)]
