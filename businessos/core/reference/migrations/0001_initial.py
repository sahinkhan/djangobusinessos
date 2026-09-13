import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Country",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("code", models.CharField(help_text="ISO 3166-1 alpha-2 code", max_length=2, unique=True)),
                ("name", models.CharField(max_length=120)),
            ],
            options={"verbose_name_plural": "countries", "ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Currency",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("code", models.CharField(help_text="ISO 4217 code", max_length=3, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("symbol", models.CharField(blank=True, max_length=8)),
                ("decimal_places", models.PositiveSmallIntegerField(default=2)),
            ],
            options={"verbose_name_plural": "currencies", "ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="Language",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("code", models.CharField(help_text="BCP 47 language tag", max_length=10, unique=True)),
                ("name", models.CharField(max_length=120)),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="UnitOfMeasure",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("code", models.CharField(max_length=16, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("symbol", models.CharField(blank=True, max_length=16)),
            ],
            options={"ordering": ["code"]},
        ),
    ]
