from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from businessos.core.common.models import UUIDTimestampedModel

from .domain import calculate_total, currency_precision, decimal_input, line_amount

_WRITE_TOKEN = object()
_ISSUE_TOKEN = object()


class BillingQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Use authorized Billing services; bulk updates are forbidden.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("Use authorized Billing services; bulk updates are forbidden.")

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Billing bulk creation/upsert is forbidden.")

    def delete(self):
        raise ValidationError("Billing queryset deletion is forbidden.")


class Invoice(UUIDTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"

    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT)
    number = models.CharField(max_length=40)
    bill_to_party = models.ForeignKey("party.Party", on_delete=models.PROTECT)
    bill_to_display_name_snapshot = models.CharField(max_length=200)
    bill_to_legal_name_snapshot = models.CharField(max_length=200, blank=True)
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    currency = models.ForeignKey("reference.Currency", on_delete=models.PROTECT)
    currency_code_snapshot = models.CharField(max_length=3)
    currency_decimal_places_snapshot = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)

    objects = BillingQuerySet.as_manager()

    class Meta:
        ordering = ["-invoice_date", "-created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"], name="billing_company_number_uniq"
            ),
            models.CheckConstraint(
                condition=Q(status="draft", issued_at__isnull=True)
                | Q(status="issued", issued_at__isnull=False),
                name="billing_invoice_lifecycle",
            ),
            models.CheckConstraint(
                condition=Q(currency_decimal_places_snapshot__lte=8),
                name="billing_currency_precision",
            ),
            models.CheckConstraint(
                condition=Q(due_date__isnull=True) | Q(due_date__gte=models.F("invoice_date")),
                name="billing_due_date_order",
            ),
        ]
        indexes = [models.Index(fields=["company", "status", "invoice_date"])]

    def clean(self):
        super().clean()
        if self.bill_to_party_id and self.bill_to_party.company_id != self.company_id:
            raise ValidationError({"bill_to_party": "Party must belong to the invoice company."})
        if self.invoice_date and self.due_date and self.due_date < self.invoice_date:
            raise ValidationError({"due_date": "Due date must not precede invoice date."})
        try:
            currency_precision(self.currency_decimal_places_snapshot)
        except ValueError as exc:
            raise ValidationError({"currency": str(exc)}) from exc

    def save(self, *args, **kwargs):
        raise ValidationError("Invoice writes require authorized Billing services.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Invoice deletion is not supported.")

    def _persist(self, token, *, creating=False):
        if token is not _WRITE_TOKEN:
            raise ValidationError("Unauthorized invoice persistence.")
        if self.status != self.Status.DRAFT or self.issued_at is not None:
            raise ValidationError("Only draft invoices may be written.")
        if not creating:
            original = type(self).objects.select_for_update().get(pk=self.pk)
            if original.status != self.Status.DRAFT or original.company_id != self.company_id:
                raise ValidationError("Invoice history and ownership are immutable.")
            if original.number != self.number:
                raise ValidationError("Invoice number is immutable.")
        # Number uniqueness is enforced by the database inside the service savepoint.
        self.full_clean(validate_constraints=False)
        super().save(force_insert=creating, force_update=not creating)

    def _issue(self, token, issued_at):
        if token is not _ISSUE_TOKEN or self.status != self.Status.DRAFT or issued_at is None:
            raise ValidationError("Unsupported invoice transition.")
        changed = models.QuerySet.update(
            type(self).objects.filter(
                pk=self.pk, company_id=self.company_id, status=self.Status.DRAFT
            ),
            status=self.Status.ISSUED,
            issued_at=issued_at,
            updated_at=issued_at,
        )
        if changed != 1:
            raise ValidationError("Invoice state changed.")
        self.status = self.Status.ISSUED
        self.issued_at = self.updated_at = issued_at

    @property
    def total(self):
        return calculate_total(
            ((line.quantity, line.unit_price) for line in self.lines.all()),
            self.currency_decimal_places_snapshot,
        )

    def __str__(self):
        return self.number


class InvoiceLine(UUIDTimestampedModel):
    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="lines")
    description = models.TextField()
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=4)
    position = models.PositiveIntegerField()

    objects = BillingQuerySet.as_manager()

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="billing_quantity_positive"),
            models.CheckConstraint(
                condition=Q(unit_price__gte=0), name="billing_price_nonnegative"
            ),
            models.CheckConstraint(condition=Q(position__gt=0), name="billing_position_positive"),
            models.UniqueConstraint(
                fields=["invoice", "position"], name="billing_line_position_uniq"
            ),
        ]

    def clean(self):
        super().clean()
        for field, positive in (("quantity", True), ("unit_price", False)):
            try:
                setattr(self, field, decimal_input(getattr(self, field), positive=positive))
            except ValueError as exc:
                raise ValidationError({field: str(exc)}) from exc
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValidationError({"description": "Description is required."})
        self.description = self.description.strip()
        if self.invoice_id and self.invoice.company_id != self.company_id:
            raise ValidationError("Line and invoice must share the same company.")

    def save(self, *args, **kwargs):
        raise ValidationError("Invoice line writes require authorized Billing services.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Invoice line deletion requires authorized Billing services.")

    def _persist(self, token, *, creating=False, remove=False):
        if token is not _WRITE_TOKEN:
            raise ValidationError("Unauthorized line persistence.")
        parent = Invoice.objects.select_for_update().get(pk=self.invoice_id)
        if parent.status != Invoice.Status.DRAFT or parent.company_id != self.company_id:
            raise ValidationError("Only lines of the owning draft invoice may change.")
        if not creating:
            original = type(self).objects.select_for_update().get(pk=self.pk)
            if (original.company_id, original.invoice_id, original.position) != (
                self.company_id,
                self.invoice_id,
                self.position,
            ):
                raise ValidationError("Line ownership and position are immutable.")
        if remove:
            return super().delete()
        self.clean()
        self.full_clean()
        super().save(force_insert=creating, force_update=not creating)

    @property
    def exact_amount(self):
        return line_amount(self.quantity, self.unit_price)

    def __str__(self):
        return f"{self.invoice_id} / {self.position}"
