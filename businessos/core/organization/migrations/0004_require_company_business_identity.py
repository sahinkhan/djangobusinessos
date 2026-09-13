import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("organization", "0003_populate_company_business_identity")]

    operations = [
        migrations.AlterField(
            model_name="company",
            name="country",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="companies",
                to="reference.country",
            ),
        ),
        migrations.AlterField(
            model_name="company",
            name="default_language",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="default_for_companies",
                to="reference.language",
            ),
        ),
    ]
