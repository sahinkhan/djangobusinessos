from django.core.management.base import BaseCommand

from businessos.core.reference.models import Country, Currency, Language, UnitOfMeasure


class Command(BaseCommand):
    help = "Create a small, idempotent reference-data starter set."

    def handle(self, *args, **options):
        records = (
            (Currency, "USD", {"name": "US Dollar", "symbol": "$", "decimal_places": 2}),
            (Currency, "BDT", {"name": "Bangladeshi Taka", "symbol": "৳", "decimal_places": 2}),
            (Country, "US", {"name": "United States"}),
            (Country, "BD", {"name": "Bangladesh"}),
            (Language, "EN", {"name": "English"}),
            (Language, "BN", {"name": "Bangla"}),
            (UnitOfMeasure, "EA", {"name": "Each", "symbol": "ea"}),
            (UnitOfMeasure, "KG", {"name": "Kilogram", "symbol": "kg"}),
        )
        created = 0
        for model, code, defaults in records:
            _, was_created = model.objects.update_or_create(code=code, defaults=defaults)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Reference data ready ({created} created)."))
