from decimal import Decimal

from django import forms
from django.utils import timezone

from businessos.core.access.forms import CompanyBoundForm
from businessos.core.reference.models import Currency
from businessos.modules.catalog.models import ProductVariant
from businessos.modules.party.models import Party

from .models import PurchaseOrder


def _display_quantity(value):
    display = format(value, "f")
    if "." in display:
        display = display.rstrip("0").rstrip(".")
    return display or "0"


class PurchaseOrderForm(CompanyBoundForm):
    supplier = forms.ModelChoiceField(queryset=Party.objects.none())
    order_date = forms.DateField(
        initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"})
    )
    currency = forms.ModelChoiceField(queryset=Currency.objects.none())
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.fields["supplier"].queryset = Party.objects.filter(
            company_id=company_id, is_active=True, is_supplier=True
        ).order_by("display_name")
        self.fields["currency"].queryset = Currency.objects.filter(is_active=True).order_by(
            "code"
        )


class PurchaseOrderLineForm(CompanyBoundForm):
    product_variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.none(), label="Product / SKU"
    )
    quantity = forms.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal("0.0001")
    )
    unit_cost = forms.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal("0"), label="Unit cost"
    )
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.fields["product_variant"].queryset = ProductVariant.objects.filter(
            company_id=company_id,
            is_active=True,
            product__is_active=True,
            product__is_purchasable=True,
        ).select_related("product").order_by("product__name", "sku")


class PurchaseReceiptForm(CompanyBoundForm):
    receipt_date = forms.DateField(
        initial=timezone.localdate, widget=forms.DateInput(attrs={"type": "date"})
    )
    idempotency_key = forms.CharField(
        max_length=120,
        help_text="Use the same key when safely retrying the exact same receipt.",
    )

    def __init__(self, *args, company_id, order_lines, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.order_lines = list(order_lines)
        for line in self.order_lines:
            self.fields[f"line_{line.id}"] = forms.DecimalField(
                required=False,
                max_digits=18,
                decimal_places=4,
                min_value=Decimal("0.0001"),
                label=(
                    f"{line.sku_snapshot} — remaining "
                    f"{_display_quantity(line.remaining_quantity)}"
                ),
            )

    def receipt_lines(self):
        return [
            {
                "purchase_order_line_id": line.id,
                "quantity_received": self.cleaned_data[f"line_{line.id}"],
            }
            for line in self.order_lines
            if self.cleaned_data.get(f"line_{line.id}") is not None
        ]


class PurchaseOrderFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses"), *PurchaseOrder.Status.choices],
        widget=forms.Select(attrs={"aria-label": "Purchase Order status"}),
    )
