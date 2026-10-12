from django import forms

from businessos.core.access.forms import CompanyBoundForm
from businessos.modules.accounting.models import Account, Journal
from businessos.modules.accounting.selectors import accounts_for_company, journals_for_company


class PostingForm(CompanyBoundForm):
    journal_id = forms.ModelChoiceField(queryset=Journal.objects.none(), label="Journal")
    ar_account_id = forms.ModelChoiceField(queryset=Account.objects.none(), label="AR")

    def __init__(self, *args, context, allocation=False, **kwargs):
        super().__init__(*args, company_id=context.company_id, **kwargs)
        # NEW activity is authoritative in services; retired original choices must
        # remain representable for an authorized historical POST retry.
        self.fields["journal_id"].queryset = journals_for_company(context)
        accounts = accounts_for_company(context)
        self.fields["ar_account_id"].queryset = accounts.filter(type="ASSET")
        self.fields["cash_account_id" if allocation else "revenue_account_id"] = (
            forms.ModelChoiceField(
                queryset=accounts.filter(type="ASSET" if allocation else "INCOME"),
                label="Cash/Bank" if allocation else "Revenue",
            )
        )


def identifiers(data):
    return {name: instance.pk for name, instance in data.items()}
