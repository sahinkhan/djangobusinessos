from decimal import Decimal

from django import forms

from businessos.core.access.forms import CompanyBoundForm
from businessos.core.organization.models import Warehouse
from businessos.modules.catalog.models import Product, ProductVariant

from .models import StockMovement


class MovementCreateForm(CompanyBoundForm):
    movement_type = forms.ChoiceField(choices=StockMovement.Type.choices)
    effective_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    reference = forms.CharField(max_length=160, required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea)
    idempotency_key = forms.CharField(max_length=120, required=False)
    source_module = forms.CharField(max_length=64, required=False)
    source_type = forms.CharField(max_length=64, required=False)
    source_id = forms.UUIDField(required=False)


class MovementEditForm(CompanyBoundForm):
    movement_type = forms.ChoiceField(choices=StockMovement.Type.choices)
    effective_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    reference = forms.CharField(max_length=160, required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea)


class MovementLineForm(CompanyBoundForm):
    product_variant = forms.ModelChoiceField(queryset=ProductVariant.objects.none())
    quantity = forms.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0.0001"))
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
        ).select_related("product")
        warehouses = Warehouse.objects.filter(company_id=company_id, is_active=True)
        self.fields["source_warehouse"].queryset = warehouses
        self.fields["destination_warehouse"].queryset = warehouses
        if movement_type == StockMovement.Type.RECEIPT:
            self.fields.pop("source_warehouse")
        elif movement_type == StockMovement.Type.ISSUE:
            self.fields.pop("destination_warehouse")


class BalanceFilterForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.none())

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["warehouse"].queryset = Warehouse.objects.filter(
            company_id=company_id, is_active=True
        )


class HistoryFilterForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.none(), required=False)
    product_variant = forms.ModelChoiceField(queryset=ProductVariant.objects.none(), required=False)

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["warehouse"].queryset = Warehouse.objects.filter(company_id=company_id)
        self.fields["product_variant"].queryset = ProductVariant.objects.filter(
            company_id=company_id
        ).select_related("product")
