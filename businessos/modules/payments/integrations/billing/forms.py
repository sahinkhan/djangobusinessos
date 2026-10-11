from django import forms

from businessos.core.access.forms import CompanyBoundForm


class AllocationForm(CompanyBoundForm):
    payment_id = forms.UUIDField(label="Receipt UUID")
    invoice_id = forms.UUIDField(label="Issued invoice UUID")
    amount = forms.CharField(max_length=256, widget=forms.TextInput(attrs={"inputmode": "decimal"}))
    idempotency_key = forms.CharField(max_length=128, label="Request key")
