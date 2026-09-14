from django.core.exceptions import ValidationError
from django.db import models, transaction

from businessos.core.common.models import UUIDTimestampedModel

_RECEIPT_INSERTION_TOKEN = object()


class _ProtectedProcurementQuerySet(models.QuerySet):
    record_label = "Procurement record"

    def update(self, **kwargs):
        raise ValidationError(
            f"{self.record_label} bulk updates are unsupported; use validated Procurement services."
        )

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError(
            f"{self.record_label} bulk updates are unsupported; use validated Procurement services."
        )

    def bulk_create(self, *args, **kwargs):
        raise ValidationError(
            f"{self.record_label} bulk creation/upsert is unsupported; "
            "use validated Procurement services."
        )

    def delete(self):
        raise ValidationError(
            f"{self.record_label} queryset deletion is unsupported; "
            "immutable history must be preserved."
        )


class PurchaseOrderQuerySet(_ProtectedProcurementQuerySet):
    record_label = "Purchase Order"

    def _transition_locked_order(
        self,
        *,
        order_id,
        expected_status,
        target_status,
        changed_at,
        confirmed_at=None,
    ):
        allowed = {("draft", "confirmed"), ("confirmed", "cancelled")}
        if (expected_status, target_status) not in allowed:
            raise ValidationError("Unsupported Purchase Order lifecycle transition.")
        if target_status == "confirmed" and confirmed_at is None:
            raise ValidationError("Confirmation time is required when confirming an order.")
        if target_status == "cancelled" and confirmed_at is not None:
            raise ValidationError("Cancellation cannot replace the confirmation time.")
        with transaction.atomic():
            try:
                order = self.select_for_update().get(pk=order_id)
            except self.model.DoesNotExist as exc:
                raise ValidationError("The Purchase Order no longer exists.") from exc
            if order.status != expected_status:
                raise ValidationError(
                    f"Expected Purchase Order status {expected_status}; found {order.status}."
                )
            if target_status == "cancelled" and order.receipts.exists():
                raise ValidationError("A Purchase Order with receipts cannot be cancelled.")
            updates = {"status": target_status, "updated_at": changed_at}
            if target_status == "confirmed":
                updates["confirmed_at"] = confirmed_at
            models.QuerySet.update(self.filter(pk=order_id), **updates)
            order.status = target_status
            order.updated_at = changed_at
            if target_status == "confirmed":
                order.confirmed_at = confirmed_at
            return order


class PurchaseOrderLineQuerySet(_ProtectedProcurementQuerySet):
    record_label = "Purchase Order Line"


class PurchaseReceiptQuerySet(_ProtectedProcurementQuerySet):
    record_label = "Purchase Receipt"

    def _insert_posted_receipt(self, receipt, *, token):
        if token is not _RECEIPT_INSERTION_TOKEN or not receipt._state.adding:
            raise ValidationError("Unsupported Purchase Receipt insertion path.")
        if (
            not receipt.company_id
            or not receipt.purchase_order_id
            or receipt.purchase_order.company_id != receipt.company_id
            or receipt.purchase_order.status != "confirmed"
            or not receipt.number
            or not receipt.idempotency_key
            or receipt.posted_at is None
        ):
            raise ValidationError("A posted Purchase Receipt requires validated immutable fields.")
        models.QuerySet.bulk_create(self, [receipt])
        return receipt


class PurchaseReceiptLineQuerySet(_ProtectedProcurementQuerySet):
    record_label = "Purchase Receipt Line"

    def _insert_posted_lines(self, lines, *, receipt, token):
        lines = list(lines)
        if token is not _RECEIPT_INSERTION_TOKEN or not receipt.pk or not lines:
            raise ValidationError("Unsupported Purchase Receipt Line insertion path.")
        seen = set()
        for line in lines:
            if (
                not line._state.adding
                or line.purchase_receipt_id != receipt.id
                or line.company_id != receipt.company_id
                or line.purchase_order_line.purchase_order_id != receipt.purchase_order_id
                or line.purchase_order_line.company_id != receipt.company_id
                or line.quantity_received is None
                or line.quantity_received <= 0
                or line.purchase_order_line_id in seen
            ):
                raise ValidationError("Purchase Receipt Lines must match the validated receipt.")
            seen.add(line.purchase_order_line_id)
        models.QuerySet.bulk_create(self, lines)
        return lines


class PurchaseOrder(UUIDTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="purchase_orders"
    )
    number = models.CharField(max_length=40)
    supplier = models.ForeignKey(
        "party.Party", on_delete=models.PROTECT, related_name="purchase_orders"
    )
    order_date = models.DateField()
    currency = models.ForeignKey(
        "reference.Currency", on_delete=models.PROTECT, related_name="purchase_orders"
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)

    objects = PurchaseOrderQuerySet.as_manager()

    class Meta:
        ordering = ["-order_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"], name="procurement_po_company_number_uniq"
            )
        ]
        indexes = [models.Index(fields=["company", "status", "order_date"])]

    def clean(self):
        super().clean()
        self.number = self.number.strip().upper()
        self.notes = self.notes.strip()
        original = None
        if not self._state.adding and self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "company_id",
                    "number",
                    "supplier_id",
                    "order_date",
                    "currency_id",
                    "status",
                    "notes",
                    "confirmed_at",
                )
                .first()
            )
        if original and original["company_id"] != self.company_id:
            raise ValidationError("Purchase Order ownership cannot be reassigned after creation.")
        if original and original["number"] != self.number:
            raise ValidationError({"number": "Purchase Order number cannot be changed."})
        if original and original["status"] != self.status:
            raise ValidationError(
                {"status": "Purchase Order status may only change through lifecycle services."}
            )
        if not self.number:
            raise ValidationError({"number": "Order number is required."})
        if self._state.adding and self.status != self.Status.DRAFT:
            raise ValidationError({"status": "A new Purchase Order must start as draft."})
        if self.supplier_id and self.company_id:
            if self.supplier.company_id != self.company_id:
                raise ValidationError({"supplier": "Supplier must belong to the order company."})
            if (original is None or original["status"] == self.Status.DRAFT) and (
                not self.supplier.is_active or not self.supplier.is_supplier
            ):
                raise ValidationError({"supplier": "Select an active supplier."})
        if (
            self.currency_id
            and (original is None or original["status"] == self.Status.DRAFT)
            and not self.currency.is_active
        ):
            raise ValidationError({"currency": "Select an active currency."})
        if original and original["status"] != self.Status.DRAFT:
            immutable = (
                "company_id",
                "number",
                "supplier_id",
                "order_date",
                "currency_id",
                "notes",
                "confirmed_at",
            )
            if any(original[field] != getattr(self, field) for field in immutable):
                raise ValidationError("Confirmed or cancelled Purchase Orders are immutable.")
        if self.status == self.Status.DRAFT and self.confirmed_at is not None:
            raise ValidationError(
                {"confirmed_at": "A draft order cannot have a confirmation time."}
            )
        if (
            self.status in {self.Status.CONFIRMED, self.Status.CANCELLED}
            and self.confirmed_at is None
        ):
            raise ValidationError(
                {"confirmed_at": "A confirmed order requires a confirmation time."}
            )

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self._state.adding and self.pk:
                type(self).objects.select_for_update().filter(pk=self.pk).exists()
            self.full_clean()
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            persisted = (
                type(self)
                .objects.select_for_update()
                .filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )
            if persisted not in {None, self.Status.DRAFT}:
                raise ValidationError("Confirmed or cancelled Purchase Orders cannot be deleted.")
            return super().delete(*args, **kwargs)

    def __str__(self):
        return self.number


class PurchaseOrderLine(UUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="purchase_order_lines"
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="lines"
    )
    product_variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="purchase_order_lines"
    )
    sku_snapshot = models.CharField(max_length=64)
    name_snapshot = models.CharField(max_length=200)
    description_snapshot = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4)
    position = models.PositiveIntegerField()

    objects = PurchaseOrderLineQuerySet.as_manager()

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["purchase_order", "position"], name="procurement_po_line_position_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="procurement_po_line_quantity_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(unit_cost__gte=0), name="procurement_po_line_cost_nonnegative"
            ),
            models.CheckConstraint(
                condition=models.Q(position__gt=0), name="procurement_po_line_position_positive"
            ),
        ]
        indexes = [models.Index(fields=["company", "product_variant"])]

    def clean(self):
        super().clean()
        self.sku_snapshot = self.sku_snapshot.strip().upper()
        self.name_snapshot = self.name_snapshot.strip()
        self.description_snapshot = self.description_snapshot.strip()
        original = None
        if not self._state.adding and self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "company_id",
                    "purchase_order_id",
                    "product_variant_id",
                    "sku_snapshot",
                    "name_snapshot",
                    "description_snapshot",
                    "quantity",
                    "unit_cost",
                    "position",
                )
                .first()
            )
        if original and any(
            original[field] != getattr(self, field) for field in ("company_id", "purchase_order_id")
        ):
            raise ValidationError("Purchase Order Line ownership cannot be reassigned.")
        if self.purchase_order_id and self.company_id:
            if self.purchase_order.company_id != self.company_id:
                raise ValidationError(
                    {"purchase_order": "Purchase Order must belong to the line company."}
                )
            status = (
                PurchaseOrder.objects.filter(id=self.purchase_order_id)
                .values_list("status", flat=True)
                .first()
            )
            if status != PurchaseOrder.Status.DRAFT:
                raise ValidationError(
                    "Lines may only be changed while the Purchase Order is draft."
                )
        if self.product_variant_id and self.company_id:
            if self.product_variant.company_id != self.company_id:
                raise ValidationError(
                    {"product_variant": "Product variant must belong to the line company."}
                )
            product = self.product_variant.product
            if (
                not self.product_variant.is_active
                or not product.is_active
                or not product.is_purchasable
            ):
                raise ValidationError({"product_variant": "Select an active purchasable variant."})
        if not self.sku_snapshot:
            raise ValidationError({"sku_snapshot": "SKU snapshot is required."})
        if not self.name_snapshot:
            raise ValidationError({"name_snapshot": "Product name snapshot is required."})
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.unit_cost is not None and self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})
        if self.position is not None and self.position <= 0:
            raise ValidationError({"position": "Position must be greater than zero."})

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.purchase_order_id:
                PurchaseOrder.objects.select_for_update().filter(pk=self.purchase_order_id).exists()
            self.full_clean()
            return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            status = (
                PurchaseOrder.objects.select_for_update()
                .filter(id=self.purchase_order_id)
                .values_list("status", flat=True)
                .first()
            )
            if status != PurchaseOrder.Status.DRAFT:
                raise ValidationError(
                    "Lines may only be removed while the Purchase Order is draft."
                )
            return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.purchase_order.number} · {self.sku_snapshot}"


class PurchaseReceipt(UUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="purchase_receipts"
    )
    number = models.CharField(max_length=40)
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.PROTECT, related_name="receipts"
    )
    receipt_date = models.DateField()
    idempotency_key = models.CharField(max_length=120)
    posted_at = models.DateTimeField()

    objects = PurchaseReceiptQuerySet.as_manager()

    class Meta:
        ordering = ["-receipt_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"], name="procurement_receipt_company_number_uniq"
            ),
            models.UniqueConstraint(
                fields=["company", "idempotency_key"], name="procurement_receipt_company_key_uniq"
            ),
        ]
        indexes = [models.Index(fields=["company", "purchase_order", "receipt_date"])]

    def clean(self):
        super().clean()
        self.number = self.number.strip().upper()
        self.idempotency_key = self.idempotency_key.strip()
        original = None
        if not self._state.adding and self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "company_id",
                    "number",
                    "purchase_order_id",
                    "receipt_date",
                    "idempotency_key",
                    "posted_at",
                )
                .first()
            )
        if self._state.adding:
            raise ValidationError("Purchase Receipts must be created through the receive service.")
        if original and any(original[field] != getattr(self, field) for field in original):
            raise ValidationError("Posted Purchase Receipts are immutable.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Posted Purchase Receipts cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.number


class PurchaseReceiptLine(UUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="purchase_receipt_lines"
    )
    purchase_receipt = models.ForeignKey(
        PurchaseReceipt, on_delete=models.CASCADE, related_name="lines"
    )
    purchase_order_line = models.ForeignKey(
        PurchaseOrderLine, on_delete=models.PROTECT, related_name="receipt_lines"
    )
    quantity_received = models.DecimalField(max_digits=18, decimal_places=4)

    objects = PurchaseReceiptLineQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["purchase_receipt", "purchase_order_line"],
                name="procurement_receipt_line_uniq",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_received__gt=0),
                name="procurement_receipt_quantity_positive",
            ),
        ]
        indexes = [models.Index(fields=["company", "purchase_order_line"])]

    def clean(self):
        super().clean()
        original = None
        if not self._state.adding and self.pk:
            original = (
                type(self)
                .objects.filter(pk=self.pk)
                .values(
                    "company_id",
                    "purchase_receipt_id",
                    "purchase_order_line_id",
                    "quantity_received",
                )
                .first()
            )
        if self._state.adding:
            raise ValidationError(
                "Purchase Receipt Lines must be created through the receive service."
            )
        if original and any(original[field] != getattr(self, field) for field in original):
            raise ValidationError("Posted Purchase Receipt Lines are immutable.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Posted Purchase Receipt Lines cannot be deleted.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.purchase_receipt.number} · {self.purchase_order_line.sku_snapshot}"
