import django.db.models.deletion
from django.db import migrations, models

import businessos.core.organization.models


class Migration(migrations.Migration):
    dependencies = [("organization", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="company",
            name="country",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="companies",
                to="reference.country",
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="default_language",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="default_for_companies",
                to="reference.language",
            ),
        ),
        migrations.AddField(
            model_name="company",
            name="timezone",
            field=models.CharField(
                default="UTC",
                max_length=64,
                validators=[businessos.core.organization.models.validate_iana_timezone],
            ),
        ),
    ]
