import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("reference", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("code", models.CharField(max_length=32, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("base_currency", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="companies", to="reference.currency")),
            ],
            options={"verbose_name_plural": "companies", "ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Branch",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("code", models.CharField(max_length=32)),
                ("name", models.CharField(max_length=160)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="branches", to="organization.company")),
            ],
            options={"ordering": ["company__code", "code"]},
        ),
        migrations.CreateModel(
            name="Warehouse",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("code", models.CharField(max_length=32)),
                ("name", models.CharField(max_length=160)),
                ("branch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="warehouses", to="organization.branch")),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="warehouses", to="organization.company")),
            ],
            options={"ordering": ["company__code", "code"]},
        ),
        migrations.AddConstraint(model_name="branch", constraint=models.UniqueConstraint(fields=("company", "code"), name="unique_branch_code_per_company")),
        migrations.AddConstraint(model_name="warehouse", constraint=models.UniqueConstraint(fields=("company", "code"), name="unique_warehouse_code_per_company")),
    ]
