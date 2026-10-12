from django.core.exceptions import ValidationError
from django.db import models

from ..bindings import PostingBinding

EFFECT = "payment_allocation_cash_ar_v1"
_INSERT_TOKEN = object()


class AllocationPosting(PostingBinding):
    allocation = models.ForeignKey("payments_billing.PaymentAllocation", on_delete=models.PROTECT)
    cash_account = models.ForeignKey(
        "accounting.Account", on_delete=models.PROTECT, related_name="+"
    )
    invoice_posting = models.ForeignKey(
        "accounting_billing.InvoicePosting", on_delete=models.PROTECT
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "allocation", "effect"], name="allocation_posting_source_uniq"
            ),
            models.CheckConstraint(
                condition=models.Q(effect=EFFECT), name="allocation_posting_effect"
            ),
        ]

    def _insert(self, token):
        if token is not _INSERT_TOKEN or not self._state.adding or self.effect != EFFECT:
            raise ValidationError("Unauthorized AllocationPosting persistence.")
        self.full_clean(validate_unique=False, validate_constraints=False)
        return models.Model.save(self, force_insert=True)
