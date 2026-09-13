from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models

from businessos.core.common.models import ActiveUUIDTimestampedModel, UUIDTimestampedModel


def _validate_immutable_ownership(instance, *field_names):
    if instance._state.adding or not instance.pk:
        return
    original = type(instance).objects.filter(pk=instance.pk).values(*field_names).first()
    if original and any(original[name] != getattr(instance, name) for name in field_names):
        raise ValidationError("Party ownership cannot be reassigned after creation.")


class Party(ActiveUUIDTimestampedModel):
    class Type(models.TextChoices):
        PERSON = "person", "Person"
        ORGANIZATION = "organization", "Organization"

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="parties"
    )
    party_type = models.CharField(max_length=16, choices=Type.choices)
    display_name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    is_customer = models.BooleanField(default=False)
    is_supplier = models.BooleanField(default=False)

    class Meta:
        ordering = ["display_name", "id"]
        indexes = [models.Index(fields=["company", "party_type", "is_active"])]
        verbose_name_plural = "parties"

    def clean(self):
        super().clean()
        self.display_name = self.display_name.strip()
        self.legal_name = self.legal_name.strip()
        _validate_immutable_ownership(self, "company_id")
        if not self.display_name:
            raise ValidationError({"display_name": "Display name is required."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name


class ContactMethod(ActiveUUIDTimestampedModel):
    class Kind(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"

    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="party_contacts"
    )
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="contact_methods")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    label = models.CharField(max_length=60, blank=True)
    value = models.CharField(max_length=254)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["party", "kind", "value"]
        constraints = [
            models.UniqueConstraint(
                fields=["party", "kind", "value"], name="unique_party_contact_method"
            ),
            models.UniqueConstraint(
                fields=["party", "kind"],
                condition=models.Q(is_primary=True),
                name="one_primary_contact_per_kind",
            ),
        ]

    def clean(self):
        super().clean()
        self.label = self.label.strip()
        self.value = self.value.strip()
        _validate_immutable_ownership(self, "company_id", "party_id")
        if self.party_id and self.company_id and self.party.company_id != self.company_id:
            raise ValidationError({"party": "The party must belong to the selected company."})
        if not self.value:
            raise ValidationError({"value": "Contact value is required."})
        if self.kind == self.Kind.EMAIL:
            self.value = self.value.lower()
            validate_email(self.value)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_kind_display()}: {self.value}"


class Address(UUIDTimestampedModel):
    company = models.ForeignKey(
        "organization.Company", on_delete=models.PROTECT, related_name="party_addresses"
    )
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="addresses")
    country = models.ForeignKey(
        "reference.Country", on_delete=models.PROTECT, related_name="party_addresses"
    )
    label = models.CharField(max_length=60, blank=True)
    line_1 = models.CharField(max_length=200)
    line_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    is_billing = models.BooleanField(default=False)
    is_shipping = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["party", "-is_default", "label", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["party"],
                condition=models.Q(is_default=True),
                name="one_default_address_per_party",
            )
        ]

    def clean(self):
        super().clean()
        for field_name in ("label", "line_1", "line_2", "city", "region", "postal_code"):
            setattr(self, field_name, getattr(self, field_name).strip())
        _validate_immutable_ownership(self, "company_id", "party_id")
        if self.party_id and self.company_id and self.party.company_id != self.company_id:
            raise ValidationError({"party": "The party must belong to the selected company."})
        if not self.line_1:
            raise ValidationError({"line_1": "Address line 1 is required."})
        if not self.city:
            raise ValidationError({"city": "City is required."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.line_1}, {self.city}"
