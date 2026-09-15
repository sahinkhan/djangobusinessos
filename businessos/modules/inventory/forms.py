from datetime import datetime
from decimal import Decimal

from django import forms
from django.db.models import Q
from django.utils import timezone

from businessos.core.access.forms import CompanyBoundForm
from businessos.core.organization.models import Warehouse
from businessos.core.organization.time import company_local_datetime, company_timezone
from businessos.modules.catalog.models import Product, ProductVariant

from .models import StockMovement


class CompanyDateTimeField(forms.DateTimeField):
    """Interpret and render naive form values in one explicit company timezone."""

    def __init__(self, *args, business_timezone, **kwargs):
        self.business_timezone = business_timezone
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, datetime) and timezone.is_aware(value):
            value = timezone.make_naive(value, self.business_timezone)
        return super().prepare_value(value)

    def to_python(self, value):
        with timezone.override(self.business_timezone):
            return super().to_python(value)


class MovementForm(CompanyBoundForm):
    movement_type = forms.ChoiceField(choices=StockMovement.Type.choices)
    effective_at = forms.DateTimeField()
    reference = forms.CharField(max_length=160, required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, company_id, original_effective_at=None, **kwargs):
        initial = kwargs.get("initial") or {}
        if initial.get("effective_at"):
            initial = initial.copy()
            initial["effective_at"] = company_local_datetime(
                company_id, initial["effective_at"]
            )
            kwargs["initial"] = initial
        super().__init__(*args, company_id=company_id, **kwargs)
        self.company_id = company_id
        self.original_effective_at = original_effective_at
        self.business_timezone = company_timezone(company_id)
        self.fields["effective_at"] = CompanyDateTimeField(
            business_timezone=self.business_timezone,
            widget=forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            input_formats=["%Y-%m-%dT%H:%M"],
        )
        if not self.is_bound and not self.initial.get("effective_at"):
            self.initial["effective_at"] = company_local_datetime(company_id).replace(
                second=0, microsecond=0
            )

    def clean_effective_at(self):
        value = self.cleaned_data["effective_at"]
        original = self.original_effective_at
        if original is None or timezone.is_naive(original):
            return value
        submitted_local = timezone.localtime(value, self.business_timezone)
        original_local = timezone.localtime(original, self.business_timezone)
        displayed_parts = ("year", "month", "day", "hour", "minute")
        if all(
            getattr(submitted_local, part) == getattr(original_local, part)
            for part in displayed_parts
        ):
            return original
        return value


class MovementCreateForm(MovementForm):
    idempotency_key = forms.CharField(max_length=120, required=False)
    source_module = forms.CharField(max_length=64, required=False)
    source_type = forms.CharField(max_length=64, required=False)
    source_id = forms.UUIDField(required=False)


class MovementLineForm(CompanyBoundForm):
    product_variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.none(), label="Product / SKU"
    )
    quantity = forms.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal("0.0001")
    )
    source_warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.none(), required=False)
    destination_warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(), required=False
    )

    def __init__(self, *args, company_id, movement_type, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.fields["product_variant"].queryset = ProductVariant.objects.filter(
            company_id=company_id,
            is_active=True,
            product__is_active=True,
            product__default_uom__is_active=True,
            product__product_type__in=[Product.Type.STOCKABLE, Product.Type.CONSUMABLE],
        ).select_related("product").order_by("product__name", "sku")
        warehouses = Warehouse.objects.filter(company_id=company_id, is_active=True).filter(
            Q(branch__isnull=True) | Q(branch__is_active=True)
        )
        self.fields["source_warehouse"].queryset = warehouses
        self.fields["destination_warehouse"].queryset = warehouses
        if movement_type == StockMovement.Type.RECEIPT:
            self.fields.pop("source_warehouse")
        elif movement_type == StockMovement.Type.ISSUE:
            self.fields.pop("destination_warehouse")


class MovementActionForm(CompanyBoundForm):
    pass


class BalanceFilterForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.none())

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["warehouse"].queryset = Warehouse.objects.filter(company_id=company_id)


class HistoryFilterForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.none(), required=False)
    product_variant = forms.ModelChoiceField(queryset=ProductVariant.objects.none(), required=False)

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["warehouse"].queryset = Warehouse.objects.filter(company_id=company_id)
        self.fields["product_variant"].queryset = ProductVariant.objects.filter(
            company_id=company_id
        ).select_related("product")
