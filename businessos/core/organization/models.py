from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.common.models import ActiveUUIDTimestampedModel


def validate_iana_timezone(value):
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        raise ValidationError("Enter a valid IANA timezone identifier.") from exc


def _validate_immutable_company(instance):
    if instance._state.adding or not instance.pk:
        return
    original_company_id = (
        type(instance).objects.filter(pk=instance.pk).values_list("company_id", flat=True).first()
    )
    if original_company_id is not None and original_company_id != instance.company_id:
        raise ValidationError(
            {"company": "Company ownership is immutable after this record is created."}
        )


class CompanyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        if "base_currency" in kwargs or "base_currency_id" in kwargs:
            raise ValidationError("Base currency is immutable after company creation.")
        return super().update(**kwargs)


class Company(ActiveUUIDTimestampedModel):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=160)
    base_currency = models.ForeignKey(
        "reference.Currency",
        on_delete=models.PROTECT,
        related_name="companies",
    )
    country = models.ForeignKey(
        "reference.Country",
        on_delete=models.PROTECT,
        related_name="companies",
    )
    timezone = models.CharField(max_length=64, default="UTC", validators=[validate_iana_timezone])
    default_language = models.ForeignKey(
        "reference.Language",
        on_delete=models.PROTECT,
        related_name="default_for_companies",
    )

    objects = CompanyQuerySet.as_manager()

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "companies"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        self.timezone = self.timezone.strip()
        original = None
        if not self._state.adding and self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("base_currency_id", "country_id", "default_language_id")
                .first()
            )
            if original and original["base_currency_id"] != self.base_currency_id:
                raise ValidationError(
                    {"base_currency": "Base currency is immutable after company creation."}
                )
        active_reference_checks = (
            (
                "base_currency",
                self.base_currency_id,
                "reference.Currency",
                None if original is None else original["base_currency_id"],
            ),
            (
                "country",
                self.country_id,
                "reference.Country",
                None if original is None else original["country_id"],
            ),
            (
                "default_language",
                self.default_language_id,
                "reference.Language",
                None if original is None else original["default_language_id"],
            ),
        )
        for field_name, reference_id, model_label, original_id in active_reference_checks:
            if reference_id and (self._state.adding or reference_id != original_id):
                reference_model = self._meta.apps.get_model(model_label)
                if not reference_model.objects.filter(id=reference_id, is_active=True).exists():
                    raise ValidationError(
                        {field_name: "A new company identity requires an active reference."}
                    )

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} — {self.name}"


class Branch(ActiveUUIDTimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="branches")
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)

    class Meta:
        ordering = ["company__code", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"], name="unique_branch_code_per_company"
            )
        ]

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        _validate_immutable_company(self)

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.code} / {self.code} — {self.name}"


class Warehouse(ActiveUUIDTimestampedModel):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="warehouses")
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="warehouses",
        blank=True,
        null=True,
    )
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)

    class Meta:
        ordering = ["company__code", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"], name="unique_warehouse_code_per_company"
            )
        ]

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        _validate_immutable_company(self)
        if self.branch_id and self.company_id and self.branch.company_id != self.company_id:
            raise ValidationError({"branch": "The branch must belong to the warehouse company."})
        if self.is_active and self.branch_id and not self.branch.is_active:
            raise ValidationError({"branch": "An active warehouse requires an active branch."})

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.code} / {self.code} — {self.name}"
