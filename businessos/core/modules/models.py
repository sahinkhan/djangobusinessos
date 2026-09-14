from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.common.models import UUIDTimestampedModel

from .manifest import validate_manifest


class BusinessModule(UUIDTimestampedModel):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=160)
    version = models.CharField(max_length=64)
    dependencies = models.JSONField(default=list, blank=True)
    declared_permissions = models.JSONField(default=list, blank=True)
    is_enabled = models.BooleanField(default=False)

    class Meta:
        ordering = ["code"]

    def clean(self):
        super().clean()
        try:
            validate_manifest(
                {
                    "code": self.code,
                    "name": self.name,
                    "version": self.version,
                    "depends": self.dependencies,
                    "permissions": self.declared_permissions,
                }
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.version})"
