from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.common.models import UUIDTimestampedModel

from .permissions import validate_permission_code


class PermissionQuerySet(models.QuerySet):
    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Permission bulk creation/upsert requires validated model saves.")

    def bulk_update(self, objs, fields, batch_size=None):
        if "code" in fields:
            raise ValidationError("Permission identity is immutable.")
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def update(self, **kwargs):
        if "code" in kwargs:
            raise ValidationError("Permission identity is immutable.")
        return super().update(**kwargs)


class Permission(UUIDTimestampedModel):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)

    objects = PermissionQuerySet.as_manager()

    class Meta:
        ordering = ["code"]

    def clean(self):
        super().clean()
        try:
            validate_permission_code(self.code)
        except ValueError as exc:
            raise ValidationError({"code": str(exc)}) from exc
        if not self._state.adding and self.pk:
            original_code = (
                type(self).objects.filter(pk=self.pk).values_list("code", flat=True).first()
            )
            if original_code is not None and original_code != self.code:
                raise ValidationError({"code": "Permission identity is immutable."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class RoleQuerySet(models.QuerySet):
    def update(self, **kwargs):
        if {"company", "company_id"}.intersection(kwargs):
            raise ValidationError("Role company is immutable.")
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if {"company", "company_id"}.intersection(fields):
            raise ValidationError("Role company is immutable.")
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Role bulk creation/upsert requires validated model saves.")


class Role(UUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.CASCADE, related_name="roles"
    )
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)

    objects = RoleQuerySet.as_manager()

    class Meta:
        ordering = ["company__code", "code"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="unique_role_code_company")
        ]

    def clean(self):
        super().clean()
        self.code = self.code.strip().upper()
        if not self._state.adding and self.pk:
            original_company_id = (
                type(self).objects.filter(pk=self.pk).values_list("company_id", flat=True).first()
            )
            if original_company_id is not None and original_company_id != self.company_id:
                raise ValidationError({"company": "Role company is immutable."})

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.code} / {self.code}"


class RolePermission(UUIDTimestampedModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permission_links")
    permission = models.ForeignKey(Permission, on_delete=models.PROTECT, related_name="role_links")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"], name="unique_permission_per_role"
            )
        ]


class UserRoleAssignmentQuerySet(models.QuerySet):
    def _check_bulk_fields(self, fields):
        if {"user", "user_id", "company", "company_id", "role", "role_id"}.intersection(fields):
            raise ValidationError("Role assignment changes require validated model saves.")

    def update(self, **kwargs):
        self._check_bulk_fields(kwargs)
        return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        self._check_bulk_fields(fields)
        return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, *args, **kwargs):
        raise ValidationError(
            "Role assignment bulk creation/upsert requires validated model saves."
        )


class UserRoleAssignment(UUIDTimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="business_role_assignments"
    )
    company = models.ForeignKey(
        "organization.Company", on_delete=models.CASCADE, related_name="user_role_assignments"
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_assignments")

    objects = UserRoleAssignmentQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "company", "role"], name="unique_user_company_role"
            )
        ]

    def clean(self):
        super().clean()
        if self.role_id and self.company_id and self.role.company_id != self.company_id:
            raise ValidationError({"role": "The role must belong to the assigned company."})
        if (
            self.user_id
            and self.company_id
            and not UserCompanyAccess.objects.filter(
                user_id=self.user_id, company_id=self.company_id
            ).exists()
        ):
            raise ValidationError({"user": "Grant company access before assigning a role."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


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
        if (
            self.user_id
            and self.branch_id
            and not UserCompanyAccess.objects.filter(
                user_id=self.user_id, company_id=self.branch.company_id
            ).exists()
        ):
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
        if (
            self.user_id
            and self.warehouse_id
            and not UserCompanyAccess.objects.filter(
                user_id=self.user_id, company_id=self.warehouse.company_id
            ).exists()
        ):
            raise ValidationError({"warehouse": "Grant company access before warehouse access."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
