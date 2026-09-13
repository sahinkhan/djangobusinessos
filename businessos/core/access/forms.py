from django import forms

from businessos.core.organization.models import Company


class CompanyScopeForm(forms.Form):
    company = forms.ModelChoiceField(queryset=Company.objects.none())

    def __init__(self, *args, companies, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = companies
