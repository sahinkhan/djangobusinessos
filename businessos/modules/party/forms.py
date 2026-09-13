from django import forms

from businessos.core.reference.models import Country

from .models import ContactMethod, Party


class PartyForm(forms.Form):
    party_type = forms.ChoiceField(choices=Party.Type.choices)
    display_name = forms.CharField(max_length=200)
    legal_name = forms.CharField(max_length=200, required=False)
    is_customer = forms.BooleanField(required=False)
    is_supplier = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False, initial=True)


class ContactMethodForm(forms.Form):
    kind = forms.ChoiceField(choices=ContactMethod.Kind.choices)
    label = forms.CharField(max_length=60, required=False)
    value = forms.CharField(max_length=254)
    is_primary = forms.BooleanField(required=False)


class AddressForm(forms.Form):
    country = forms.ModelChoiceField(queryset=Country.objects.filter(is_active=True))
    label = forms.CharField(max_length=60, required=False)
    line_1 = forms.CharField(max_length=200)
    line_2 = forms.CharField(max_length=200, required=False)
    city = forms.CharField(max_length=120)
    region = forms.CharField(max_length=120, required=False)
    postal_code = forms.CharField(max_length=32, required=False)
    is_billing = forms.BooleanField(required=False)
    is_shipping = forms.BooleanField(required=False)
    is_default = forms.BooleanField(required=False)
