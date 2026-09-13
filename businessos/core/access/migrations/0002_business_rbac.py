import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0001_initial"),
        ("business_audit", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Permission",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=100, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=64)),
                ("name", models.CharField(max_length=160)),
                ("is_active", models.BooleanField(default=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="roles", to="organization.company")),
            ],
            options={"ordering": ["company__code", "code"]},
        ),
        migrations.CreateModel(
            name="RolePermission",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("permission", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="role_links", to="access.permission")),
                ("role", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="permission_links", to="access.role")),
            ],
        ),
        migrations.CreateModel(
            name="UserRoleAssignment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_role_assignments", to="organization.company")),
                ("role", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_assignments", to="access.role")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="business_role_assignments", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name="role", constraint=models.UniqueConstraint(fields=("company", "code"), name="unique_role_code_company")),
        migrations.AddConstraint(model_name="rolepermission", constraint=models.UniqueConstraint(fields=("role", "permission"), name="unique_permission_per_role")),
        migrations.AddConstraint(model_name="userroleassignment", constraint=models.UniqueConstraint(fields=("user", "company", "role"), name="unique_user_company_role")),
    ]
