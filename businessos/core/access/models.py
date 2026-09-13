from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.common.models import UUIDTimestampedModel


class UserCompanyAccess(UUIDTimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_accesses"
    )
    company = models.ForeignKey(
        "organization.Company", on_delete=models.CASCADE, related_name="user_accesses"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "company"], name="unique_user_company_access")
        ]

    def __str__(self):
        return f"{self.user} -> {self.company}"


class UserBranchAccess(UUIDTimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="branch_accesses"
    )
    branch = models.ForeignKey(
        "organization.Branch", on_delete=models.CASCADE, related_name="user_accesses"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "branch"], name="unique_user_branch_access")
        ]

    def clean(self):
        super().clean()
        if self.user_id and self.branch_id and not UserCompanyAccess.objects.filter(
            user_id=self.user_id, company_id=self.branch.company_id
        ).exists():
            raise ValidationError({"branch": "Grant company access before branch access."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class UserWarehouseAccess(UUIDTimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="warehouse_accesses"
    )
    warehouse = models.ForeignKey(
        "organization.Warehouse", on_delete=models.CASCADE, related_name="user_accesses"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "warehouse"], name="unique_user_warehouse_access"
            )
        ]

    def clean(self):
        super().clean()
        if self.user_id and self.warehouse_id and not UserCompanyAccess.objects.filter(
            user_id=self.user_id, company_id=self.warehouse.company_id
        ).exists():
            raise ValidationError({"warehouse": "Grant company access before warehouse access."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
