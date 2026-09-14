from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.common.models import UUIDTimestampedModel


class ImmutableAuditQuerySet(models.QuerySet):
    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Audit entries are immutable.")

    def bulk_create(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
    ):
        if update_conflicts:
            raise ValidationError("Audit entries are immutable; conflict updates are forbidden.")
        return super().bulk_create(
            objs,
            batch_size=batch_size,
            ignore_conflicts=ignore_conflicts,
            update_conflicts=update_conflicts,
            update_fields=update_fields,
            unique_fields=unique_fields,
        )

    def update(self, **kwargs):
        raise ValidationError("Audit entries are immutable.")

    def delete(self):
        raise ValidationError("Audit entries are immutable.")


class AuditEntry(UUIDTimestampedModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="business_audit_entries",
    )
    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.PROTECT,
        related_name="audit_entries",
        blank=True,
        null=True,
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=128)
    occurred_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    objects = ImmutableAuditQuerySet.as_manager()

    class Meta:
        ordering = ["-occurred_at", "-created_at"]
        indexes = [
            models.Index(fields=["company", "occurred_at"], name="business_au_company_e21dc8_idx"),
            models.Index(
                fields=["object_type", "object_id"], name="business_au_object__9292e8_idx"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Audit entries are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit entries are immutable.")

    def __str__(self):
        return f"{self.action}: {self.object_type}/{self.object_id}"
