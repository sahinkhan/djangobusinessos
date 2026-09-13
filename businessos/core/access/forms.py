from django import forms

from businessos.core.organization.models import Company


class CompanyScopeForm(forms.Form):
    company = forms.ModelChoiceField(queryset=Company.objects.none())

    def __init__(self, *args, companies, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company"].queryset = companies


class CompanyBoundForm(forms.Form):
    """Bind a state-changing form to the company selected when it was rendered."""

    scope_company_id = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, company_id, **kwargs):
        self.scope_company_id = company_id
        self.scope_company = Company.objects.only("id", "code", "name").get(id=company_id)
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["scope_company_id"] = company_id

    def clean(self):
        cleaned_data = super().clean()
        submitted_company_id = cleaned_data.pop("scope_company_id", None)
        if submitted_company_id != self.scope_company_id:
            raise forms.ValidationError(
                "Company scope changed after this form was opened. Reload the page and try again."
            )
        return cleaned_data
