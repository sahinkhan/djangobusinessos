from django.db import migrations


def populate_company_identity(apps, schema_editor):
    country_model = apps.get_model("reference", "Country")
    language_model = apps.get_model("reference", "Language")
    company_model = apps.get_model("organization", "Company")
    country, _ = country_model.objects.get_or_create(
        code="ZZ", defaults={"name": "Unspecified country", "is_active": True}
    )
    language, _ = language_model.objects.get_or_create(
        code="UND", defaults={"name": "Undetermined language", "is_active": True}
    )
    company_model.objects.filter(country__isnull=True).update(country=country)
    company_model.objects.filter(default_language__isnull=True).update(default_language=language)


class Migration(migrations.Migration):
    dependencies = [("organization", "0002_company_business_identity")]

    operations = [migrations.RunPython(populate_company_identity, migrations.RunPython.noop)]
