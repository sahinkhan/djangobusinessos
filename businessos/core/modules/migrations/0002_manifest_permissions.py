from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("module_registry", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="businessmodule",
            name="declared_permissions",
            field=models.JSONField(blank=True, default=list),
        )
    ]
