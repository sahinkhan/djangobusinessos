from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q

from businessos.core.common.models import UUIDTimestampedModel


class StockMovement(UUIDTimestampedModel):
    class Type(models.TextChoices):
        RECEIPT = "receipt", "Receipt"
        ISSUE = "issue", "Issue"
        TRANSFER = "transfer", "Transfer"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        POSTED = "posted", "Posted"

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="stock_movements"
    )
    number = models.CharField(max_length=40)
    movement_type = models.CharField(max_length=12, choices=Type.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    effective_at = models.DateTimeField()
    reference = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    idempotency_key = models.CharField(max_length=120, blank=True, null=True)  # noqa: DJ001
    source_module = models.CharField(max_length=64, blank=True, null=True)  # noqa: DJ001
    source_type = models.CharField(max_length=64, blank=True, null=True)  # noqa: DJ001
    source_id = models.UUIDField(blank=True, null=True)
    posted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-effective_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"], name="unique_stock_movement_number_per_company"
            ),
            models.UniqueConstraint(
                fields=["company", "idempotency_key"],
                name="unique_stock_movement_idempotency_per_company",
            ),
            models.CheckConstraint(
                condition=(
                    Q(source_module__isnull=True, source_type__isnull=True, source_id__isnull=True)
                    | Q(
                        source_module__isnull=False,
                        source_type__isnull=False,
                        source_id__isnull=False,
                    )
                ),
                name="stock_movement_source_all_or_none",
            ),
        ]
        indexes = [models.Index(fields=["company", "status", "effective_at"])]

    def clean(self):
        super().clean()
        self.number = self.number.strip().upper()
        self.reference = self.reference.strip()
        self.notes = self.notes.strip()
        self.idempotency_key = self.idempotency_key.strip() if self.idempotency_key else None
        self.source_module = self.source_module.strip() if self.source_module else None
        self.source_type = self.source_type.strip() if self.source_type else None
        if not self.number:
            raise ValidationError({"number": "Movement number is required."})
        source_values = (self.source_module, self.source_type, self.source_id)
        if any(value is not None for value in source_values) and not all(
            value is not None for value in source_values
        ):
            raise ValidationError("Source module, type, and ID must be supplied together.")
        if self.status == self.Status.DRAFT and self.posted_at is not None:
            raise ValidationError({"posted_at": "A draft movement cannot have a posted time."})
        if self.status == self.Status.POSTED and self.posted_at is None:
            raise ValidationError({"posted_at": "A posted movement requires a posted time."})

    def save(self, *args, **kwargs):
        self.clean()
        if self._state.adding:
            if self.status != self.Status.DRAFT:
                raise ValidationError("Stock movements must be created as drafts.")
            return super().save(*args, **kwargs)
        with transaction.atomic():
            persisted = type(self).objects.select_for_update().get(pk=self.pk)
            if persisted.status == self.Status.POSTED:
                raise ValidationError("Posted stock movements are immutable.")
            if self.status != persisted.status:
                raise ValidationError("Use the inventory posting service to change status.")
            for field in (
                "company_id",
                "number",
                "idempotency_key",
                "source_module",
                "source_type",
                "source_id",
            ):
                if getattr(self, field) != getattr(persisted, field):
                    raise ValidationError(
                        "Movement number, ownership, and source identity are immutable."
                    )
            if self.movement_type != persisted.movement_type and persisted.lines.exists():
                raise ValidationError("Movement type cannot change after lines are added.")
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            persisted = type(self).objects.select_for_update().get(pk=self.pk)
            if persisted.status == self.Status.POSTED:
                raise ValidationError("Posted stock movements cannot be deleted.")
            return super().delete(*args, **kwargs)

    def __str__(self):
        return self.number


class StockMovementLine(UUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="stock_movement_lines"
    )
    movement = models.ForeignKey(StockMovement, on_delete=models.CASCADE, related_name="lines")
    product_variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="stock_movement_lines"
    )
    sku_snapshot = models.CharField(max_length=64)
    product_name_snapshot = models.CharField(max_length=200)
    uom = models.ForeignKey(
        "reference.UnitOfMeasure", on_delete=models.PROTECT, related_name="stock_movement_lines"
    )
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    source_warehouse = models.ForeignKey(
        "organization.Warehouse",
        on_delete=models.PROTECT,
        related_name="stock_lines_out",
        blank=True,
        null=True,
    )
    destination_warehouse = models.ForeignKey(
        "organization.Warehouse",
        on_delete=models.PROTECT,
        related_name="stock_lines_in",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="stock_line_quantity_positive"
            ),
            models.CheckConstraint(
                condition=(
                    Q(source_warehouse__isnull=True)
                    | Q(destination_warehouse__isnull=True)
                    | ~Q(source_warehouse=models.F("destination_warehouse"))
                ),
                name="stock_line_distinct_warehouses",
            ),
        ]
        indexes = [models.Index(fields=["company", "product_variant"])]

    def clean(self):
        super().clean()
        if self.quantity is None or self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.movement_id and self.company_id != self.movement.company_id:
            raise ValidationError({"movement": "Movement must belong to the line company."})
        if self.product_variant_id and self.company_id != self.product_variant.company_id:
            raise ValidationError({"product_variant": "Variant must belong to the line company."})
        for field in ("source_warehouse", "destination_warehouse"):
            warehouse = getattr(self, field)
            if warehouse and warehouse.company_id != self.company_id:
                raise ValidationError({field: "Warehouse must belong to the line company."})
        if self.source_warehouse_id and self.source_warehouse_id == self.destination_warehouse_id:
            raise ValidationError("Source and destination warehouses must differ.")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            movement = StockMovement.objects.select_for_update().get(pk=self.movement_id)
            if movement.status != StockMovement.Status.DRAFT:
                raise ValidationError("Posted stock movement lines are immutable.")
            if not self._state.adding:
                persisted = type(self).objects.get(pk=self.pk)
                if (
                    persisted.company_id != self.company_id
                    or persisted.movement_id != self.movement_id
                ):
                    raise ValidationError("Stock line ownership is immutable.")
            self.full_clean()
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            persisted = type(self).objects.select_related("movement").get(pk=self.pk)
            movement = StockMovement.objects.select_for_update().get(pk=persisted.movement_id)
            if movement.status != StockMovement.Status.DRAFT:
                raise ValidationError(
                    "Posted stock movement lines are immutable and cannot be deleted."
                )
            return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.movement.number}: {self.sku_snapshot}"
