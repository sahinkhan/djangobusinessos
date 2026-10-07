from decimal import Decimal

from django import forms

from businessos.core.access.forms import CompanyBoundForm
from businessos.core.organization.time import company_local_date
from businessos.core.reference.models import Currency
from businessos.modules.party.models import Party

from .models import Invoice


class InvoiceForm(CompanyBoundForm):
    bill_to_party = forms.ModelChoiceField(queryset=Party.objects.none(), label="Bill to")
    invoice_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    currency = forms.ModelChoiceField(queryset=Currency.objects.none())
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.fields["bill_to_party"].queryset = Party.objects.filter(
            company_id=company_id, is_active=True
        ).order_by("display_name", "id")
        self.fields["currency"].queryset = Currency.objects.filter(is_active=True).order_by("code")
        if not self.is_bound and not self.initial.get("invoice_date"):
            self.initial["invoice_date"] = company_local_date(company_id)


class InvoiceLineForm(CompanyBoundForm):
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    quantity = forms.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0.0001"))
    unit_price = forms.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal("0"))


class InvoiceFilterForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses"), *Invoice.Status.choices],
        widget=forms.Select(attrs={"aria-label": "Invoice status"}),
    )
