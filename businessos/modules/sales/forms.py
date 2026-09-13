from django import forms
from django.utils import timezone

from businessos.core.access.forms import CompanyBoundForm
from businessos.core.reference.models import Currency
from businessos.modules.catalog.models import ProductVariant
from businessos.modules.party.models import Party

from .models import SalesOrder


class SalesOrderForm(CompanyBoundForm):
    customer = forms.ModelChoiceField(queryset=Party.objects.none())
    order_date = forms.DateField(
        initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"})
    )
    currency = forms.ModelChoiceField(queryset=Currency.objects.none())
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.fields["customer"].queryset = Party.objects.filter(
            company_id=company_id, is_active=True, is_customer=True
        ).order_by("display_name")
        self.fields["currency"].queryset = Currency.objects.filter(is_active=True).order_by(
            "code"
        )


class SalesOrderLineForm(CompanyBoundForm):
    product_variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.none(), label="Product / SKU"
    )
    quantity = forms.DecimalField(max_digits=18, decimal_places=4, min_value=0.0001)
    unit_price = forms.DecimalField(
        max_digits=18, decimal_places=4, min_value=0, label="Unit price"
    )
    description = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    position = forms.IntegerField(min_value=1, required=False)

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.fields["product_variant"].queryset = ProductVariant.objects.filter(
            company_id=company_id,
            is_active=True,
            product__is_active=True,
            product__is_sellable=True,
        ).select_related("product").order_by("product__name", "sku")


class SalesOrderFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses"), *SalesOrder.Status.choices],
        widget=forms.Select(attrs={"aria-label": "Sales Order status"}),
    )
