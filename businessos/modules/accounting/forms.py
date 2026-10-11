from django import forms

from businessos.core.access.forms import CompanyBoundForm
from businessos.core.organization.time import company_local_date
from businessos.modules.party.models import Party

from .models import Account, Journal, JournalEntry


class ReferenceForm(CompanyBoundForm):
    # Domain validates length AFTER code normalization (Unicode may expand).
    code = forms.CharField()
    name = forms.CharField()
    is_active = forms.TypedChoiceField(
        choices=[("true", "Active"), ("false", "Inactive")],
        coerce=lambda value: value == "true",
    )

    def __init__(self, *args, account=False, editing=False, **kwargs):
        super().__init__(*args, **kwargs)
        if account and not editing:
            self.fields["type"] = forms.ChoiceField(choices=Account.Type.choices)
        if editing:
            self.fields.pop("code")
        self.initial.setdefault("is_active", "true")


class EntryForm(CompanyBoundForm):
    journal = forms.ModelChoiceField(queryset=Journal.objects.none())
    entry_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    memo = forms.CharField(required=False, strip=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.fields["journal"].queryset = (
            Journal.objects.filter(
                company_id=company_id,
                is_active=True,
            )
            .only("id", "code", "name")
            .order_by("code", "id")
        )
        if not self.is_bound:
            self.initial.setdefault("entry_date", company_local_date(company_id))


class LineForm(CompanyBoundForm):
    account = forms.ModelChoiceField(queryset=Account.objects.none())
    party = forms.ModelChoiceField(queryset=Party.objects.none(), required=False)
    description = forms.CharField(
        required=False, strip=False, widget=forms.Textarea(attrs={"rows": 3})
    )
    debit = forms.CharField(initial="0", widget=forms.TextInput(attrs={"inputmode": "decimal"}))
    credit = forms.CharField(initial="0", widget=forms.TextInput(attrs={"inputmode": "decimal"}))

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, company_id=company_id, **kwargs)
        self.fields["account"].queryset = (
            Account.objects.filter(
                company_id=company_id,
                is_active=True,
            )
            .only("id", "code", "name")
            .order_by("code", "id")
        )
        self.fields["party"].queryset = (
            Party.objects.filter(
                company_id=company_id,
                is_active=True,
            )
            .only("id", "display_name")
            .order_by("display_name", "id")
        )


class FilterForm(forms.Form):
    q = forms.CharField(required=False)
    active = forms.ChoiceField(
        required=False, choices=[("", "All"), ("yes", "Active"), ("no", "Inactive")]
    )


class EntryFilterForm(forms.Form):
    q = forms.CharField(required=False)
    status = forms.ChoiceField(
        required=False, choices=[("", "All states"), *JournalEntry.Status.choices]
    )


class ReportForm(forms.Form):
    from_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    to_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    account = forms.ModelChoiceField(queryset=Account.objects.none(), required=False)

    def __init__(self, *args, company_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["account"].queryset = (
            Account.objects.filter(
                company_id=company_id,
            )
            .only("id", "code", "name")
            .order_by("code", "id")
        )
