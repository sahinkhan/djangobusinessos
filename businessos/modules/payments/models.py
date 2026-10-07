from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from businessos.core.common.models import UUIDTimestampedModel

from .domain import AMOUNT_LIMIT, format_amount, receipt_amount

_METHOD_WRITE_TOKEN = object()
_RECEIPT_INSERT_TOKEN = object()


class PaymentsQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Use authorized Payments services; public updates are forbidden.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("Payments bulk updates are forbidden.")

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Payments bulk creation/upsert is forbidden.")

    def delete(self):
        raise ValidationError("Payments deletion is forbidden.")


class PaymentMethod(UUIDTimestampedModel):
    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT)
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)

    objects = PaymentsQuerySet.as_manager()

    class Meta:
        ordering = ["code", "id"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="payments_method_code_uniq"),
        ]

    def save(self, *args, **kwargs):
        raise ValidationError("PaymentMethod writes require authorized Payments services.")

    def delete(self, *args, **kwargs):
        raise ValidationError("PaymentMethod deletion is forbidden; deactivate through services.")

    def _persist(self, token, *, creating=False):
        if token is not _METHOD_WRITE_TOKEN:
            raise ValidationError("Unauthorized payment method persistence.")
        if not creating:
            original = type(self).objects.select_for_update().get(pk=self.pk)
            if (original.company_id, original.code) != (self.company_id, self.code):
                raise ValidationError("Payment method company and code are immutable.")
        self.full_clean(validate_constraints=False)
        super().save(force_insert=creating, force_update=not creating)

    def __str__(self):
        return f"{self.code} — {self.name}"


class Payment(UUIDTimestampedModel):
    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT)
    number = models.CharField(max_length=40)
    payer_party = models.ForeignKey("party.Party", on_delete=models.PROTECT)
    payer_display_name_snapshot = models.CharField(max_length=200)
    payer_legal_name_snapshot = models.CharField(max_length=200, blank=True)
    payment_date = models.DateField()
    currency = models.ForeignKey("reference.Currency", on_delete=models.PROTECT)
    currency_code_snapshot = models.CharField(max_length=3)
    currency_decimal_places_snapshot = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=38, decimal_places=8)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    payment_method_code_snapshot = models.CharField(max_length=32)
    payment_method_name_snapshot = models.CharField(max_length=160)
    external_reference = models.CharField(max_length=128, blank=True)
    # NULL represents an unkeyed request; only non-NULL company keys are unique.
    idempotency_key = models.CharField(max_length=128, blank=True, null=True)  # noqa: DJ001
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField()

    objects = PaymentsQuerySet.as_manager()

    class Meta:
        ordering = ["-payment_date", "-recorded_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"], name="payments_company_number_uniq"
            ),
            models.UniqueConstraint(
                fields=["company", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="payments_company_key_uniq",
            ),
            models.CheckConstraint(condition=Q(amount__gt=0), name="payments_amount_positive"),
            models.CheckConstraint(
                condition=Q(amount__lt=AMOUNT_LIMIT), name="payments_amount_range"
            ),
            models.CheckConstraint(
                condition=Q(currency_decimal_places_snapshot__gte=0)
                & Q(currency_decimal_places_snapshot__lte=8),
                name="payments_currency_precision",
            ),
        ]
        indexes = [models.Index(fields=["company", "payment_date"])]

    def clean(self):
        super().clean()
        try:
            self.amount = receipt_amount(self.amount, self.currency_decimal_places_snapshot)
        except ValueError as exc:
            raise ValidationError({"amount": str(exc)}) from exc
        if self.payer_party_id and self.payer_party.company_id != self.company_id:
            raise ValidationError({"payer_party": "Payer must belong to the receipt company."})
        if self.payment_method_id and self.payment_method.company_id != self.company_id:
            raise ValidationError({"payment_method": "Method must belong to the receipt company."})

    def save(self, *args, **kwargs):
        raise ValidationError("Payment writes require authorized receipt recording.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Recorded receipts cannot be deleted.")

    def _insert(self, token):
        if token is not _RECEIPT_INSERT_TOKEN or not self._state.adding:
            raise ValidationError("Receipt persistence permits validated insertion only.")
        # Normalize redundant zeros before Django's representation-based DecimalField validation.
        self.clean()
        self.full_clean(validate_constraints=False)
        super().save(force_insert=True)

    @property
    def formatted_amount(self):
        return format_amount(self.amount, self.currency_decimal_places_snapshot)

    def __str__(self):
        return self.number
