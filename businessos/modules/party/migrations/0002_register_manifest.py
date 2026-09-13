from django.db import migrations


def register_party(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.update_or_create(
        code="party",
        defaults={
            "name": "Party",
            "version": "0.1.0",
            "dependencies": ["identity", "organization", "reference", "access"],
        },
    )


def unregister_party(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.filter(code="party").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("module_registry", "0001_initial"),
        ("party", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_party, unregister_party)]
