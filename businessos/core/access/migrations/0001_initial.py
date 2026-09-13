import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("organization", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="UserCompanyAccess",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_accesses", to="organization.company")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="company_accesses", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="UserBranchAccess",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_accesses", to="organization.branch")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="branch_accesses", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="UserWarehouseAccess",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="warehouse_accesses", to=settings.AUTH_USER_MODEL)),
                ("warehouse", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_accesses", to="organization.warehouse")),
            ],
        ),
        migrations.AddConstraint(model_name="usercompanyaccess", constraint=models.UniqueConstraint(fields=("user", "company"), name="unique_user_company_access")),
        migrations.AddConstraint(model_name="userbranchaccess", constraint=models.UniqueConstraint(fields=("user", "branch"), name="unique_user_branch_access")),
        migrations.AddConstraint(model_name="userwarehouseaccess", constraint=models.UniqueConstraint(fields=("user", "warehouse"), name="unique_user_warehouse_access")),
    ]
