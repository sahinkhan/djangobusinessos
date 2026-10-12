from django.core.exceptions import ValidationError
from django.db import models

from ..bindings import PostingBinding

EFFECT = "billing_invoice_ar_revenue_v1"
_INSERT_TOKEN = object()


class InvoicePosting(PostingBinding):
    invoice = models.ForeignKey("billing.Invoice", on_delete=models.PROTECT)
    revenue_account = models.ForeignKey(
        "accounting.Account", on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "invoice", "effect"], name="invoice_posting_source_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(effect=EFFECT), name="invoice_posting_effect"
            ),
        ]

    def _insert(self, token):
        if token is not _INSERT_TOKEN or not self._state.adding or self.effect != EFFECT:
            raise ValidationError("Unauthorized InvoicePosting persistence.")
        self.full_clean(validate_unique=False, validate_constraints=False)
        return models.Model.save(self, force_insert=True)
