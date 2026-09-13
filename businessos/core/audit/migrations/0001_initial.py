import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organization", "0004_require_company_business_identity"),
    ]
    operations = [
        migrations.CreateModel(
            name="AuditEntry",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("action", models.CharField(max_length=100)),
                ("object_type", models.CharField(max_length=100)),
                ("object_id", models.CharField(max_length=128)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="business_audit_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "company",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="audit_entries",
                        to="organization.company",
                    ),
                ),
            ],
            options={"ordering": ["-occurred_at", "-created_at"]},
        ),
        migrations.AddIndex(
            model_name="auditentry",
            index=models.Index(
                fields=["company", "occurred_at"], name="business_au_company_e21dc8_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="auditentry",
            index=models.Index(
                fields=["object_type", "object_id"], name="business_au_object__9292e8_idx"
            ),
        ),
    ]
