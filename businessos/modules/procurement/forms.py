from decimal import Decimal
from uuid import UUID

from django import forms

from businessos.core.access.forms import CompanyBoundForm
from businessos.core.organization.time import company_local_date
from businessos.core.reference.models import Currency
from businessos.modules.catalog.models import ProductVariant
from businessos.modules.party.models import Party

from .models import PurchaseOrder


def _display_quantity(value):
    display = format(value, "f")
    return display.rstrip("0").rstrip(".") if "." in display else display


class PurchaseOrderForm(CompanyBoundForm):
    supplier = forms.ModelChoiceField(queryset=Party.objects.none())
    order_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    currency = forms.ModelChoiceField(queryset=Currency.objects.none())
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        if not self.is_bound and not self.initial.get("order_date"):
            self.initial["order_date"] = company_local_date(company_id)
        self.fields["supplier"].queryset = Party.objects.filter(
            company_id=company_id, is_active=True, is_supplier=True
        ).order_by("display_name")
        self.fields["currency"].queryset = Currency.objects.filter(is_active=True).order_by("code")


class PurchaseOrderLineForm(CompanyBoundForm):
    product_variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.none(), label="Product / SKU"
    )
    quantity = forms.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0.0001"))
    unit_cost = forms.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal("0"), label="Unit cost"
    )
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.fields["product_variant"].queryset = (
            ProductVariant.objects.filter(
                company_id=company_id,
                is_active=True,
                product__is_active=True,
                product__is_purchasable=True,
            )
            .select_related("product")
            .order_by("product__name", "sku")
        )


class PurchaseReceiptForm(CompanyBoundForm):
    receipt_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    idempotency_key = forms.CharField(
        max_length=120,
        help_text="Use the same key when safely retrying the exact same receipt.",
    )

    def __init__(self, *args, company_id, order_lines, submitted_line_ids=(), **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        if not self.is_bound and not self.initial.get("receipt_date"):
            self.initial["receipt_date"] = company_local_date(company_id)
        self.order_lines = list(order_lines)
        self.receipt_field_names = []
        for line in self.order_lines:
            field_name = f"line_{line.id}"
            self.receipt_field_names.append(field_name)
            self.fields[field_name] = forms.DecimalField(
                required=False,
                max_digits=18,
                decimal_places=4,
                min_value=Decimal("0.0001"),
                label=(
                    f"{line.sku_snapshot} — remaining {_display_quantity(line.remaining_quantity)}"
                ),
            )
        known = {line.id for line in self.order_lines}
        for line_id in submitted_line_ids:
            if line_id in known:
                continue
            field_name = f"line_{line_id}"
            self.receipt_field_names.append(field_name)
            self.fields[field_name] = forms.DecimalField(
                required=False,
                max_digits=18,
                decimal_places=4,
                min_value=Decimal("0.0001"),
                label="Submitted Purchase Order line",
            )

    def receipt_lines(self):
        return [
            {
                "purchase_order_line_id": UUID(name.removeprefix("line_")),
                "quantity_received": self.cleaned_data[name],
            }
            for name in self.receipt_field_names
            if self.cleaned_data.get(name) is not None
        ]


class PurchaseOrderFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses"), *PurchaseOrder.Status.choices],
        widget=forms.Select(attrs={"aria-label": "Purchase Order status"}),
    )
