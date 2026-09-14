from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.common.models import ActiveUUIDTimestampedModel


class ImmutableReferenceQuerySet(models.QuerySet):
    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Reference bulk creation/upsert requires validated model saves.")

    def bulk_update(self, objs, fields, batch_size=None):
        if "code" in fields:
            raise ValidationError("Reference identity codes are immutable after creation.")
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def update(self, **kwargs):
        if "code" in kwargs:
            raise ValidationError("Reference identity codes are immutable after creation.")
        return super().update(**kwargs)


class CodedReference(ActiveUUIDTimestampedModel):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=120)

    objects = ImmutableReferenceQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ["code"]

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if not self._state.adding and self.pk:
            original_code = (
                type(self).objects.filter(pk=self.pk).values_list("code", flat=True).first()
            )
            if original_code is not None and original_code != self.code:
                raise ValidationError(
                    {"code": "Reference identity codes are immutable after creation."}
                )

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
