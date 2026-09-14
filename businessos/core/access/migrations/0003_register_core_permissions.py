from django.db import migrations


CORE_PERMISSION_DECLARATIONS = (
    ("access.organization.manage", "Manage organizational access"),
    ("access.role.manage", "Manage BusinessOS roles"),
)


def register_core_permissions(apps, schema_editor):
    permission_model = apps.get_model("access", "Permission")
    for code, name in CORE_PERMISSION_DECLARATIONS:
        permission, created = permission_model.objects.get_or_create(
            code=code,
            defaults={"name": name, "is_active": True},
        )
        if not created and permission.name != name:
            permission_model.objects.filter(id=permission.id).update(name=name)


class Migration(migrations.Migration):
    dependencies = [("access", "0002_business_rbac")]

    operations = [
        migrations.RunPython(register_core_permissions, migrations.RunPython.noop),
    ]
