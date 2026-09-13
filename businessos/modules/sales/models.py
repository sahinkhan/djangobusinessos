from django.core.exceptions import ValidationError
from django.db import models, transaction

from businessos.core.common.models import UUIDTimestampedModel


class SalesOrder(UUIDTimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="sales_orders"
    )
    number = models.CharField(max_length=40)
    customer = models.ForeignKey(
        "party.Party", on_delete=models.PROTECT, related_name="sales_orders"
    )
    order_date = models.DateField()
    currency = models.ForeignKey(
        "reference.Currency", on_delete=models.PROTECT, related_name="sales_orders"
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-order_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"], name="sales_order_company_number_uniq"
            )
        ]
        indexes = [models.Index(fields=["company", "status", "order_date"])]

    def clean(self):
        super().clean()
        self.number = self.number.strip().upper()
        self.notes = self.notes.strip()
        original = None
        if not self._state.adding and self.pk:
            original = type(self).objects.filter(pk=self.pk).values(
                "company_id",
                "number",
                "customer_id",
                "order_date",
                "currency_id",
                "status",
                "notes",
                "confirmed_at",
            ).first()
        if original and original["company_id"] != self.company_id:
            raise ValidationError("Sales Order ownership cannot be reassigned after creation.")
        if original and original["number"] != self.number:
            raise ValidationError({"number": "Sales Order number cannot be changed."})
        if original and original["status"] != self.status:
            raise ValidationError(
                {"status": "Sales Order status may only change through lifecycle services."}
            )
        if not self.number:
            raise ValidationError({"number": "Order number is required."})
        if self._state.adding and self.status != self.Status.DRAFT:
            raise ValidationError({"status": "A new Sales Order must start as draft."})
        if self.customer_id and self.company_id and self.customer.company_id != self.company_id:
            raise ValidationError({"customer": "Customer must belong to the order company."})
        if original is None or original["status"] == self.Status.DRAFT:
            if self.customer_id and (not self.customer.is_active or not self.customer.is_customer):
                raise ValidationError({"customer": "Select an active customer."})
            if self.currency_id and not self.currency.is_active:
                raise ValidationError({"currency": "Select an active currency."})
        if original:
            if original["status"] != self.Status.DRAFT:
                immutable_fields = (
                    "company_id",
                    "number",
                    "customer_id",
                    "order_date",
                    "currency_id",
                    "notes",
                    "confirmed_at",
                )
                if any(original[field] != getattr(self, field) for field in immutable_fields):
                    raise ValidationError(
                        "Confirmed or cancelled Sales Orders are immutable."
                    )
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
        if (
            self.status == self.Status.CONFIRMED
            and not self._state.adding
            and not self.lines.exists()
        ):
            raise ValidationError("A Sales Order requires at least one line before confirmation.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            persisted_status = (
                type(self)
                .objects.select_for_update()
                .filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )
            if persisted_status not in {None, self.Status.DRAFT}:
                raise ValidationError("Confirmed or cancelled Sales Orders cannot be deleted.")
            return super().delete(*args, **kwargs)

    def __str__(self):
        return self.number


class SalesOrderLine(UUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="sales_order_lines"
    )
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name="lines")
    product_variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="sales_order_lines"
    )
    sku_snapshot = models.CharField(max_length=64)
    name_snapshot = models.CharField(max_length=200)
    description_snapshot = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=4)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["sales_order", "position"], name="sales_line_order_position_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="sales_line_quantity_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0), name="sales_line_price_nonnegative"
            ),
            models.CheckConstraint(
                condition=models.Q(position__gt=0), name="sales_line_position_positive"
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
            original = type(self).objects.filter(pk=self.pk).values(
                "company_id",
                "sales_order_id",
                "product_variant_id",
                "sku_snapshot",
                "name_snapshot",
                "description_snapshot",
                "quantity",
                "unit_price",
                "position",
            ).first()
        if original and any(
            original[field] != getattr(self, field)
            for field in ("company_id", "sales_order_id")
        ):
            raise ValidationError("Sales Order Line ownership cannot be reassigned.")
        if self.sales_order_id and self.company_id:
            if self.sales_order.company_id != self.company_id:
                raise ValidationError(
                    {"sales_order": "Sales Order must belong to the line company."}
                )
            persisted_status = SalesOrder.objects.filter(id=self.sales_order_id).values_list(
                "status", flat=True
            ).first()
            if persisted_status != SalesOrder.Status.DRAFT:
                raise ValidationError("Lines may only be changed while the Sales Order is draft.")
        if self.product_variant_id and self.company_id:
            if self.product_variant.company_id != self.company_id:
                raise ValidationError(
                    {"product_variant": "Product variant must belong to the line company."}
                )
            product = self.product_variant.product
            if (
                not self.product_variant.is_active
                or not product.is_active
                or not product.is_sellable
            ):
                raise ValidationError({"product_variant": "Select an active sellable variant."})
        if not self.sku_snapshot:
            raise ValidationError({"sku_snapshot": "SKU snapshot is required."})
        if not self.name_snapshot:
            raise ValidationError({"name_snapshot": "Product name snapshot is required."})
        if self.quantity is not None and self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})
        if self.unit_price is not None and self.unit_price < 0:
            raise ValidationError({"unit_price": "Unit price cannot be negative."})
        if self.position is not None and self.position <= 0:
            raise ValidationError({"position": "Position must be greater than zero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        persisted_status = SalesOrder.objects.filter(id=self.sales_order_id).values_list(
            "status", flat=True
        ).first()
        if persisted_status != SalesOrder.Status.DRAFT:
            raise ValidationError("Lines may only be removed while the Sales Order is draft.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.sales_order.number} · {self.sku_snapshot}"
