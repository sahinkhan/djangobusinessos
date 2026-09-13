from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.common.models import ActiveUUIDTimestampedModel


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


class Company(ActiveUUIDTimestampedModel):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=160)
    base_currency = models.ForeignKey(
        "reference.Currency",
        on_delete=models.PROTECT,
        related_name="companies",
    )

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "companies"

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()

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
