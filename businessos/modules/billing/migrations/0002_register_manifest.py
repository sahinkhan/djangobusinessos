from django.db import migrations

PERMISSIONS = (
    ("billing.invoice.view", "View invoices"),
    ("billing.invoice.create", "Create draft invoices"),
    ("billing.invoice.update", "Update draft invoices and lines"),
    ("billing.invoice.issue", "Issue invoices"),
)


def register_billing(apps, schema_editor):
    module = apps.get_model("module_registry", "BusinessModule")
    permission = apps.get_model("access", "Permission")
    module.objects.update_or_create(
        code="billing",
        defaults={
            "name": "Billing & Invoicing", "version": "0.1.0",
            "dependencies": ["party", "organization", "reference", "access"],
            "declared_permissions": sorted(code for code, _ in PERMISSIONS),
        },
    )
    for code, name in PERMISSIONS:
        permission.objects.get_or_create(code=code, defaults={"name": name, "is_active": True})


def unregister_billing(apps, schema_editor):
    apps.get_model("module_registry", "BusinessModule").objects.filter(code="billing").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"), ("access", "0003_register_core_permissions"),
        ("module_registry", "0001_initial"),
    ]
    operations = [migrations.RunPython(register_billing, unregister_billing)]
