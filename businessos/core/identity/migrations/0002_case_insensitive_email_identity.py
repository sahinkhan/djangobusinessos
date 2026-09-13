from django.db import migrations, models
from django.db.models.functions import Lower


def normalize_existing_emails(apps, schema_editor):
    user_model = apps.get_model("identity", "User")
    normalized_by_id = {
        user.id: user.email.strip().lower()
        for user in user_model.objects.order_by("id").only("id", "email")
    }
    normalized_values = list(normalized_by_id.values())
    if len(normalized_values) != len(set(normalized_values)):
        raise RuntimeError(
            "Case-insensitive duplicate user emails must be resolved before this migration."
        )
    for user_id, email in normalized_by_id.items():
        user_model.objects.filter(id=user_id).update(email=email)


class Migration(migrations.Migration):
    dependencies = [("identity", "0001_initial")]
    operations = [
        migrations.RunPython(normalize_existing_emails, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                Lower("email"), name="unique_user_email_case_insensitive"
            ),
        ),
    ]
