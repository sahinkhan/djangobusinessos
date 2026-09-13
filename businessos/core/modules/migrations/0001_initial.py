import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="BusinessModule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("version", models.CharField(max_length=64)),
                ("dependencies", models.JSONField(blank=True, default=list)),
                ("is_enabled", models.BooleanField(default=False)),
            ],
            options={"ordering": ["code"]},
        )
    ]
