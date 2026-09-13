from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.common.models import ActiveUUIDTimestampedModel, UUIDTimestampedModel


def _validate_immutable_ownership(instance, *field_names):
    if instance._state.adding or not instance.pk:
        return
    original = type(instance).objects.filter(pk=instance.pk).values(*field_names).first()
    if original and any(original[name] != getattr(instance, name) for name in field_names):
        raise ValidationError("Catalog ownership cannot be reassigned after creation.")


class ProductCategory(ActiveUUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="product_categories"
    )
    name = models.CharField(max_length=160)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="children",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"], name="unique_category_name_per_company"
            )
        ]
        verbose_name_plural = "product categories"

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        _validate_immutable_ownership(self, "company_id")
        if not self.name:
            raise ValidationError({"name": "Category name is required."})
        if self.parent_id:
            if self.parent_id == self.id:
                raise ValidationError({"parent": "A category cannot be its own parent."})
            if self.parent.company_id != self.company_id:
                raise ValidationError(
                    {"parent": "Parent category must belong to the same company."}
                )
            ancestor = self.parent
            while ancestor is not None:
                if ancestor.id == self.id:
                    raise ValidationError({"parent": "Category hierarchy cannot contain a cycle."})
                ancestor = ancestor.parent

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(ActiveUUIDTimestampedModel):
    class Type(models.TextChoices):
        STOCKABLE = "stockable", "Stockable"
        CONSUMABLE = "consumable", "Consumable"
        SERVICE = "service", "Service"

    class Structure(models.TextChoices):
        SIMPLE = "simple", "Simple"
        VARIABLE = "variable", "Variable"

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="products"
    )
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
        blank=True,
        null=True,
    )
    product_type = models.CharField(max_length=16, choices=Type.choices)
    structure = models.CharField(max_length=12, choices=Structure.choices)
    default_uom = models.ForeignKey(
        "reference.UnitOfMeasure", on_delete=models.PROTECT, related_name="products"
    )
    sales_description = models.TextField(blank=True)
    purchase_description = models.TextField(blank=True)
    is_sellable = models.BooleanField(default=True)
    is_purchasable = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]
        indexes = [models.Index(fields=["company", "product_type", "is_active"])]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        self.sales_description = self.sales_description.strip()
        self.purchase_description = self.purchase_description.strip()
        _validate_immutable_ownership(self, "company_id", "structure")
        if not self.name:
            raise ValidationError({"name": "Product name is required."})
        if self.category_id and self.category.company_id != self.company_id:
            raise ValidationError({"category": "Category must belong to the product company."})
        if not self._state.adding and (self.is_sellable or self.is_purchasable):
            variants = self.variants.all()
            if not variants.exists():
                raise ValidationError(
                    "A sellable or purchasable Product requires a ProductVariant."
                )
            if self.structure == self.Structure.SIMPLE and (
                variants.count() != 1 or not variants.filter(is_default=True).exists()
            ):
                raise ValidationError(
                    "A simple Product requires exactly one default ProductVariant."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductVariant(ActiveUUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="product_variants"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["product", "sku"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "sku"], name="unique_variant_sku_per_company"
            ),
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_default=True),
                name="one_default_variant_per_product",
            ),
        ]
        indexes = [models.Index(fields=["company", "is_active"])]

    def clean(self):
        super().clean()
        self.sku = self.sku.strip().upper()
        _validate_immutable_ownership(self, "company_id", "product_id")
        if not self.sku:
            raise ValidationError({"sku": "SKU is required."})
        if self.product_id and self.product.company_id != self.company_id:
            raise ValidationError({"product": "Product must belong to the variant company."})
        if self.product_id and self.product.structure == Product.Structure.SIMPLE:
            other_variants = ProductVariant.objects.filter(product_id=self.product_id).exclude(
                pk=self.pk
            )
            if other_variants.exists():
                raise ValidationError("A simple Product can have only one ProductVariant.")
            if not self.is_default:
                raise ValidationError({"is_default": "A simple Product variant must be default."})
            if self.is_active != self.product.is_active:
                raise ValidationError(
                    {"is_active": "A simple Product variant must match its Product activity."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.product.structure == Product.Structure.SIMPLE:
            raise ValidationError("The default variant of a simple Product cannot be deleted.")
        if (
            self.product.is_sellable or self.product.is_purchasable
        ) and not ProductVariant.objects.filter(product=self.product).exclude(pk=self.pk).exists():
            raise ValidationError(
                "The last variant of a sellable or purchasable Product cannot be deleted."
            )
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.sku} — {self.product.name}"


class Attribute(ActiveUUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="product_attributes"
    )
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"], name="unique_attribute_name_per_company"
            )
        ]

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        _validate_immutable_ownership(self, "company_id")
        if not self.name:
            raise ValidationError({"name": "Attribute name is required."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AttributeValue(ActiveUUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="product_attribute_values"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=120)

    class Meta:
        ordering = ["attribute", "value", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "value"], name="unique_value_per_attribute"
            )
        ]

    def clean(self):
        super().clean()
        self.value = self.value.strip()
        _validate_immutable_ownership(self, "company_id", "attribute_id")
        if self.attribute_id and self.attribute.company_id != self.company_id:
            raise ValidationError({"attribute": "Attribute must belong to the value company."})
        if not self.value:
            raise ValidationError({"value": "Attribute value is required."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class VariantAttributeValue(UUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="variant_attribute_values"
    )
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name="attribute_assignments"
    )
    attribute = models.ForeignKey(
        Attribute, on_delete=models.PROTECT, related_name="variant_assignments"
    )
    attribute_value = models.ForeignKey(
        AttributeValue, on_delete=models.PROTECT, related_name="variant_assignments"
    )

    class Meta:
        ordering = ["variant", "attribute", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["variant", "attribute"], name="one_value_per_variant_attribute"
            ),
            models.UniqueConstraint(
                fields=["variant", "attribute_value"],
                name="unique_value_assignment_per_variant",
            ),
        ]

    def clean(self):
        super().clean()
        _validate_immutable_ownership(
            self, "company_id", "variant_id", "attribute_id", "attribute_value_id"
        )
        if self.variant_id and self.variant.company_id != self.company_id:
            raise ValidationError({"variant": "Variant must belong to the assignment company."})
        if self.attribute_id and self.attribute.company_id != self.company_id:
            raise ValidationError({"attribute": "Attribute must belong to the assignment company."})
        if self.attribute_value_id:
            if self.attribute_value.company_id != self.company_id:
                raise ValidationError(
                    {"attribute_value": "Attribute value must belong to the assignment company."}
                )
            if self.attribute_id and self.attribute_value.attribute_id != self.attribute_id:
                raise ValidationError(
                    {
                        "attribute_value": (
                            "Attribute value does not belong to the selected attribute."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
