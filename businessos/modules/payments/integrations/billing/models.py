from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Length, Trim
from django.db.models.lookups import GreaterThan, LessThanOrEqual

from businessos.core.common.models import UUIDTimestampedModel
from businessos.core.database import current_database_alias

from . import domain

_INSERT_TOKEN = object()


class AllocationQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Allocation facts are immutable; use authorized creation.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("Allocation bulk updates are forbidden.")

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Allocation bulk creation/upsert is forbidden.")

    def delete(self):
        raise ValidationError("Allocation history cannot be deleted.")


class PaymentAllocation(UUIDTimestampedModel):
    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT)
    payment = models.ForeignKey("payments.Payment", on_delete=models.PROTECT)
    invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=38, decimal_places=8)
    idempotency_key = models.CharField(max_length=128)

    objects = AllocationQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "idempotency_key"], name="allocation_company_key_uniq"
            ),
            models.CheckConstraint(condition=Q(amount__gt=0), name="allocation_amount_positive"),
            models.CheckConstraint(
                condition=Q(amount__lt=domain.AMOUNT_LIMIT), name="allocation_amount_range"
            ),
            models.CheckConstraint(
                condition=GreaterThan(Length(Trim("idempotency_key")), 0)
                & LessThanOrEqual(Length("idempotency_key"), 128)
                & Q(idempotency_key__regex=r"\S"),
                name="allocation_key_bounds",
            ),
        ]
        indexes = [
            models.Index(
                fields=["company", "payment", "created_at", "id"], name="allocation_payment_history"
            ),
            models.Index(
                fields=["company", "invoice", "created_at", "id"], name="allocation_invoice_history"
            ),
        ]

    def save(self, *args, **kwargs):
        raise ValidationError("Allocation creation requires its authorized service.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Allocation history cannot be deleted.")

    def _insert(self, token):
        if token is not _INSERT_TOKEN or not self._state.adding:
            raise ValidationError("Allocation persistence permits validated insertion only.")
        alias = current_database_alias()
        if self._state.db not in (None, alias):
            raise ValidationError("Cross-alias allocation objects are forbidden.")
        # The service supplies IDs only, after the locked owner basis and capacity checks.
        self.full_clean(validate_unique=False, validate_constraints=False)
        super().save(using=alias, force_insert=True)
