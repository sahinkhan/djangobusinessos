from uuid import uuid4

from django import forms

from businessos.core.access.forms import CompanyBoundForm
from businessos.core.organization.time import company_local_date
from businessos.core.reference.models import Currency
from businessos.modules.party.models import Party

from .models import PaymentMethod


class PaymentMethodForm(CompanyBoundForm):
    code = forms.CharField(max_length=32)
    name = forms.CharField(max_length=160)

    def __init__(self, *args, editing=False, **kwargs):
        super().__init__(*args, **kwargs)
        if editing:
            self.fields.pop("code")


class MethodActivityForm(CompanyBoundForm):
    is_active = forms.TypedChoiceField(
        choices=[("true", "Active"), ("false", "Inactive")], coerce=lambda value: value == "true"
    )


class PaymentForm(CompanyBoundForm):
    payer_party = forms.ModelChoiceField(queryset=Party.objects.none(), label="Payer")
    payment_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    currency = forms.ModelChoiceField(queryset=Currency.objects.none())
    # Domain validation owns exact numeric scale; DecimalField would reject redundant zeros.
    amount = forms.CharField(widget=forms.TextInput(attrs={"inputmode": "decimal"}))
    payment_method = forms.ModelChoiceField(queryset=PaymentMethod.objects.none())
    external_reference = forms.CharField(max_length=128, required=False)
    idempotency_key = forms.CharField(max_length=128, required=False, widget=forms.HiddenInput)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        parties = Party.objects.filter(company_id=company_id)
        methods = PaymentMethod.objects.filter(company_id=company_id)
        currencies = Currency.objects.all()
        # A bound retry may legitimately reference retired identities. Services decide eligibility.
        if not self.is_bound:
            parties = parties.filter(is_active=True)
            methods = methods.filter(is_active=True)
            currencies = currencies.filter(is_active=True)
            self.initial.setdefault("payment_date", company_local_date(company_id))
            self.initial.setdefault("idempotency_key", str(uuid4()))
        self.fields["payer_party"].queryset = parties.order_by("display_name", "id")
        self.fields["payment_method"].queryset = methods.order_by("code", "id")
        self.fields["currency"].queryset = currencies.order_by("code", "id")


class SearchForm(forms.Form):
    q = forms.CharField(required=False)


class MethodFilterForm(SearchForm):
    active = forms.ChoiceField(
        required=False,
        choices=[("", "All methods"), ("yes", "Active"), ("no", "Inactive")],
        widget=forms.Select(attrs={"aria-label": "Method activity"}),
    )
