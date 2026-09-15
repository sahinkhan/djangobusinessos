from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q

from businessos.core.common.models import UUIDTimestampedModel

_MOVEMENT_MUTATION_TOKEN = object()
_LINE_MUTATION_TOKEN = object()
_POSTING_TOKEN = object()


class _ProtectedInventoryQuerySet(models.QuerySet):
    record_label = "Inventory record"

    def update(self, **kwargs):
        raise ValidationError(
            f"{self.record_label} bulk updates are unsupported; use validated Inventory services."
        )

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError(
            f"{self.record_label} bulk updates are unsupported; use validated Inventory services."
        )

    def bulk_create(self, *args, **kwargs):
        raise ValidationError(
            f"{self.record_label} bulk creation/upsert is unsupported; "
            "use validated Inventory services."
        )

    def delete(self):
        raise ValidationError(
            f"{self.record_label} queryset deletion is unsupported; "
            "posted history must be preserved."
        )


class StockMovementQuerySet(_ProtectedInventoryQuerySet):
    record_label = "Stock Movement"

    def _post_locked_movement(self, *, movement_id, expected_status, posted_at, token):
        if token is not _POSTING_TOKEN or expected_status != "draft" or posted_at is None:
            raise ValidationError("Unsupported Stock Movement lifecycle transition.")
        with transaction.atomic():
            try:
                movement = self.select_for_update().get(pk=movement_id)
            except self.model.DoesNotExist as exc:
                raise ValidationError("The Stock Movement no longer exists.") from exc
            if movement.status != expected_status:
                raise ValidationError(
                    f"Expected Stock Movement status {expected_status}; found {movement.status}."
                )
            models.QuerySet.update(
                self.filter(pk=movement_id),
                status="posted",
                posted_at=posted_at,
                updated_at=posted_at,
            )
            movement.status = "posted"
            movement.posted_at = posted_at
            movement.updated_at = posted_at
            return movement


class StockMovementLineQuerySet(_ProtectedInventoryQuerySet):
    record_label = "Stock Movement Line"


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

    objects = StockMovementQuerySet.as_manager()

    class Meta:
        ordering = ["-effective_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"], name="inventory_movement_company_number_uniq"
            ),
            models.UniqueConstraint(
                fields=["company", "idempotency_key"],
                name="inventory_movement_company_key_uniq",
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
                name="inventory_movement_source_all_or_none",
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
        original = None
        if not self._state.adding and self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "company_id",
                    "number",
                    "movement_type",
                    "status",
                    "effective_at",
                    "reference",
                    "notes",
                    "idempotency_key",
                    "source_module",
                    "source_type",
                    "source_id",
                    "posted_at",
                )
                .first()
            )
        if not self.number:
            raise ValidationError({"number": "Movement number is required."})
        source_values = (self.source_module, self.source_type, self.source_id)
        if any(value is not None for value in source_values) and not all(
            value is not None for value in source_values
        ):
            raise ValidationError("Source module, type, and ID must be supplied together.")
        if self._state.adding and self.status != self.Status.DRAFT:
            raise ValidationError({"status": "A Stock Movement must start as draft."})
        if original:
            if any(
                original[field] != getattr(self, field)
                for field in (
                    "company_id",
                    "number",
                    "idempotency_key",
                    "source_module",
                    "source_type",
                    "source_id",
                )
            ):
                raise ValidationError(
                    "Movement ownership, number, and source identity are immutable."
                )
            if original["status"] != self.status:
                raise ValidationError({"status": "Use the Inventory posting service."})
            if original["status"] == self.Status.POSTED and any(
                original[field] != getattr(self, field)
                for field in (
                    "movement_type",
                    "effective_at",
                    "reference",
                    "notes",
                    "posted_at",
                )
            ):
                raise ValidationError("Posted Stock Movements are immutable.")
            if original["movement_type"] != self.movement_type and self.lines.exists():
                raise ValidationError("Movement type cannot change after lines are added.")
        if self.status == self.Status.DRAFT and self.posted_at is not None:
            raise ValidationError({"posted_at": "A draft movement cannot have a posted time."})
        if self.status == self.Status.POSTED and self.posted_at is None:
            raise ValidationError({"posted_at": "A posted movement requires a posted time."})

    def save(self, *args, _inventory_token=None, **kwargs):
        if _inventory_token is not _MOVEMENT_MUTATION_TOKEN:
            raise ValidationError("Stock Movements must be changed through Inventory services.")
        with transaction.atomic():
            if not self._state.adding and self.pk:
                type(self).objects.select_for_update().filter(pk=self.pk).exists()
            self.full_clean()
            return super().save(*args, **kwargs)

    def delete(self, *args, _inventory_token=None, **kwargs):
        if _inventory_token is not _MOVEMENT_MUTATION_TOKEN:
            raise ValidationError("Stock Movements must be deleted through Inventory services.")
        with transaction.atomic():
            persisted = (
                type(self)
                .objects.select_for_update()
                .filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )
            if persisted not in {None, self.Status.DRAFT}:
                raise ValidationError("Posted Stock Movements cannot be deleted.")
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

    objects = StockMovementLineQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="inventory_line_quantity_positive"
            ),
            models.CheckConstraint(
                condition=(
                    Q(source_warehouse__isnull=True)
                    | Q(destination_warehouse__isnull=True)
                    | ~Q(source_warehouse=models.F("destination_warehouse"))
                ),
                name="inventory_line_distinct_warehouses",
            ),
        ]
        indexes = [models.Index(fields=["company", "product_variant"])]

    def clean(self):
        super().clean()
        original = None
        if not self._state.adding and self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("company_id", "movement_id")
                .first()
            )
        if original and any(
            original[field] != getattr(self, field) for field in ("company_id", "movement_id")
        ):
            raise ValidationError("Stock Movement Line ownership is immutable.")
        if self.movement_id and self.company_id:
            if self.movement.company_id != self.company_id:
                raise ValidationError({"movement": "Movement must belong to the line company."})
            status = (
                StockMovement.objects.filter(pk=self.movement_id)
                .values_list("status", flat=True)
                .first()
            )
            if status != StockMovement.Status.DRAFT:
                raise ValidationError("Lines may only change while the Stock Movement is draft.")
        if self.product_variant_id and self.product_variant.company_id != self.company_id:
            raise ValidationError({"product_variant": "Variant must belong to the line company."})
        if self.product_variant_id:
            product = self.product_variant.product
            if (
                not self.product_variant.is_active
                or not product.is_active
                or product.product_type not in {"stockable", "consumable"}
            ):
                raise ValidationError(
                    {"product_variant": "Select an active stockable or consumable variant."}
                )
            if self.uom_id != product.default_uom_id or not self.uom.is_active:
                raise ValidationError({"uom": "Use the active current Product UoM."})
            if self.sku_snapshot != self.product_variant.sku:
                raise ValidationError({"sku_snapshot": "SKU snapshot must match the variant."})
            if self.product_name_snapshot != product.name:
                raise ValidationError(
                    {"product_name_snapshot": "Product snapshot must match the Product."}
                )
        for field in ("source_warehouse", "destination_warehouse"):
            warehouse = getattr(self, field)
            if warehouse and warehouse.company_id != self.company_id:
                raise ValidationError({field: "Warehouse must belong to the line company."})
            if warehouse and (
                not warehouse.is_active or (warehouse.branch_id and not warehouse.branch.is_active)
            ):
                raise ValidationError({field: "Select an active Warehouse."})
        if self.quantity is None or self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.source_warehouse_id and self.source_warehouse_id == self.destination_warehouse_id:
            raise ValidationError("Source and destination warehouses must differ.")
        if self.movement_id:
            source = self.source_warehouse_id is not None
            destination = self.destination_warehouse_id is not None
            if self.movement.movement_type == StockMovement.Type.RECEIPT and (
                source or not destination
            ):
                raise ValidationError("A receipt requires only a destination warehouse.")
            if self.movement.movement_type == StockMovement.Type.ISSUE and (
                not source or destination
            ):
                raise ValidationError("An issue requires only a source warehouse.")
            if self.movement.movement_type == StockMovement.Type.TRANSFER and (
                not source or not destination
            ):
                raise ValidationError("A transfer requires source and destination warehouses.")

    def save(self, *args, _inventory_token=None, **kwargs):
        if _inventory_token is not _LINE_MUTATION_TOKEN:
            raise ValidationError(
                "Stock Movement Lines must be changed through Inventory services."
            )
        with transaction.atomic():
            if self.movement_id:
                StockMovement.objects.select_for_update().filter(pk=self.movement_id).exists()
            self.full_clean()
            return super().save(*args, **kwargs)

    def delete(self, *args, _inventory_token=None, **kwargs):
        if _inventory_token is not _LINE_MUTATION_TOKEN:
            raise ValidationError(
                "Stock Movement Lines must be deleted through Inventory services."
            )
        with transaction.atomic():
            persisted = type(self).objects.filter(pk=self.pk).values("movement_id").first()
            if persisted is None:
                return super().delete(*args, **kwargs)
            status = (
                StockMovement.objects.select_for_update()
                .filter(pk=persisted["movement_id"])
                .values_list("status", flat=True)
                .first()
            )
            if status != StockMovement.Status.DRAFT:
                raise ValidationError("Posted Stock Movement Lines cannot be deleted.")
            return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.movement.number} · {self.sku_snapshot}"
