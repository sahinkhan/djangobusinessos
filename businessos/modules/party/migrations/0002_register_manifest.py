from django.db import migrations


PARTY_MANIFEST = {
    "code": "party",
    "name": "Party",
    "version": "0.1.0",
    "dependencies": ["identity", "organization", "reference", "access"],
    "declared_permissions": [],
}


def register_party(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.update_or_create(
        code=PARTY_MANIFEST["code"],
        defaults={key: value for key, value in PARTY_MANIFEST.items() if key != "code"},
    )


def unregister_party(apps, schema_editor):
    business_module = apps.get_model("module_registry", "BusinessModule")
    business_module.objects.filter(code=PARTY_MANIFEST["code"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("module_registry", "0001_initial"),
        ("party", "0001_initial"),
    ]

    operations = [migrations.RunPython(register_party, unregister_party)]
