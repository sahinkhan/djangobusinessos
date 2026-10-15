"""Frozen HR v1 vocabulary; runtime declarations may evolve independently."""

from django.db import migrations

PERMISSIONS = (
    ("hr.employee.view", "View employees"),
    ("hr.employee.manage", "Manage employees"),
    ("hr.department.view", "View departments"),
    ("hr.department.manage", "Manage departments"),
    ("hr.attendance.view", "View attendance"),
    ("hr.attendance.record", "Record attendance"),
    ("hr.attendance.correct", "Correct attendance"),
    ("hr.leave.view", "View leave"),
    ("hr.leave.request", "Request leave"),
    ("hr.leave.approve", "Approve or reject leave"),
    ("hr.leave.cancel", "Cancel leave"),
    ("hr.leave_type.manage", "Manage leave types"),
)


def register_hr(apps, schema_editor):
    alias = schema_editor.connection.alias
    apps.get_model("module_registry", "BusinessModule").objects.using(alias).update_or_create(
        code="hr",
        defaults={
            "name": "Human Resources",
            "version": "0.1.0",
            "dependencies": ["party", "organization", "reference", "access"],
            "declared_permissions": sorted(code for code, _ in PERMISSIONS),
        },
    )
    for code, name in PERMISSIONS:
        apps.get_model("access", "Permission").objects.using(alias).get_or_create(
            code=code, defaults={"name": name, "is_active": True}
        )


def unregister_hr(apps, schema_editor):
    # Historical permissions/grants are never silently retired or removed.
    apps.get_model("module_registry", "BusinessModule").objects.using(
        schema_editor.connection.alias
    ).filter(code="hr").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("hr", "0001_initial"),
        ("access", "0003_register_core_permissions"),
        ("module_registry", "0001_initial"),
    ]
    operations = [migrations.RunPython(register_hr, unregister_hr)]
