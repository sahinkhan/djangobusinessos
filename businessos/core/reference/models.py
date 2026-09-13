from django.db import models

from businessos.core.common.models import ActiveUUIDTimestampedModel


class CodedReference(ActiveUUIDTimestampedModel):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=120)

    class Meta:
        abstract = True
        ordering = ["code"]

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} — {self.name}"


class Country(CodedReference):
    code = models.CharField(max_length=2, unique=True, help_text="ISO 3166-1 alpha-2 code")

    class Meta(CodedReference.Meta):
        verbose_name_plural = "countries"


class Currency(CodedReference):
    code = models.CharField(max_length=3, unique=True, help_text="ISO 4217 code")
    symbol = models.CharField(max_length=8, blank=True)
    decimal_places = models.PositiveSmallIntegerField(default=2)

    class Meta(CodedReference.Meta):
        verbose_name_plural = "currencies"


class Language(CodedReference):
    code = models.CharField(max_length=10, unique=True, help_text="BCP 47 language tag")


class UnitOfMeasure(CodedReference):
    code = models.CharField(max_length=16, unique=True)
    symbol = models.CharField(max_length=16, blank=True)
