from businessos.core.admin import businessos_admin_site

from .models import Country, Currency, Language, UnitOfMeasure

for model in (Country, Currency, Language, UnitOfMeasure):
    businessos_admin_site.register(model)
