"""Accounting-owned immutable binding mechanics; no public persistence bypass."""

from django.core.exceptions import ValidationError
from django.db import models

from businessos.core.common.models import UUIDTimestampedModel


class BindingQuerySet(models.QuerySet):
    def create(self, **kwargs):
        raise ValidationError("Posting binding creation requires authorized services.")

    def get_or_create(self, **kwargs):
        raise ValidationError("Posting binding convenience creation is forbidden.")

    def update_or_create(self, **kwargs):
        raise ValidationError("Posting binding convenience upserts are forbidden.")

    def update(self, **kwargs):
        raise ValidationError("Posting bindings are immutable; use authorized posting services.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("Posting binding bulk updates are forbidden.")

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Posting binding bulk creation/upsert is forbidden.")

    def delete(self):
        raise ValidationError("Posting binding deletion is forbidden.")


class PostingBinding(UUIDTimestampedModel):
    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT)
    effect = models.CharField(max_length=40)
    journal_entry = models.OneToOneField("accounting.JournalEntry", on_delete=models.PROTECT)
    journal = models.ForeignKey("accounting.Journal", on_delete=models.PROTECT)
    ar_account = models.ForeignKey("accounting.Account", on_delete=models.PROTECT, related_name="+")
    objects = BindingQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        raise ValidationError("Posting bindings require an authorized atomic service.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Posting bindings are immutable.")
