from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from businessos.core.common.models import UUIDTimestampedModel

from . import domain

_WRITE_TOKEN = object()
_POST_TOKEN = object()


class AccountingQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Accounting updates require authorized services.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("Accounting bulk updates are forbidden.")

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Accounting bulk creation/upserts are forbidden.")

    def delete(self):
        raise ValidationError("Accounting queryset deletion is forbidden.")


class AccountingModel(UUIDTimestampedModel):
    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT)
    objects = AccountingQuerySet.as_manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        raise ValidationError("Accounting writes require authorized services.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Accounting deletion is unsupported; draft lines use services.")

    def _persist(self, token, *, creating=False):
        if token is not _WRITE_TOKEN:
            raise ValidationError("Unauthorized Accounting persistence.")
        if not creating:
            try:
                original = type(self).objects.select_for_update().get(pk=self.pk)
            except type(self).DoesNotExist as exc:
                raise ValidationError("Accounting record no longer exists.") from exc
            immutable = self._immutable_fields
            if any(getattr(original, field) != getattr(self, field) for field in immutable):
                raise ValidationError("Accounting identity/ownership is immutable.")
            if isinstance(self, JournalEntry) and original.status != JournalEntry.Status.DRAFT:
                raise ValidationError("Posted history is immutable.")
        self.clean()
        self.full_clean(validate_unique=False, validate_constraints=False)
        super().save(force_insert=creating, force_update=not creating)


class Account(AccountingModel):
    class Type(models.TextChoices):
        ASSET = "ASSET", "Asset"
        LIABILITY = "LIABILITY", "Liability"
        EQUITY = "EQUITY", "Equity"
        INCOME = "INCOME", "Income"
        EXPENSE = "EXPENSE", "Expense"

    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    type = models.CharField(max_length=9, choices=Type.choices)
    is_active = models.BooleanField(default=True)
    _immutable_fields = ("company_id", "code", "type", "created_at")

    class Meta:
        ordering = ["code", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"], name="accounting_account_code_uniq"
            ),
            models.CheckConstraint(
                condition=Q(type__in=["ASSET", "LIABILITY", "EQUITY", "INCOME", "EXPENSE"]),
                name="accounting_account_type",
            ),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Journal(AccountingModel):
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)
    _immutable_fields = ("company_id", "code", "created_at")

    class Meta:
        ordering = ["code", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "code"], name="accounting_journal_code_uniq"
            ),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class JournalEntry(AccountingModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        POSTED = "POSTED", "Posted"

    number = models.CharField(max_length=35)
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT)
    entry_date = models.DateField()
    memo = models.TextField(blank=True)
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.DRAFT)
    base_currency_code_snapshot = models.CharField(max_length=3)
    base_currency_precision_snapshot = models.PositiveSmallIntegerField()
    posted_at = models.DateTimeField(null=True, blank=True)
    _immutable_fields = (
        "company_id",
        "number",
        "base_currency_code_snapshot",
        "base_currency_precision_snapshot",
        "created_at",
    )

    class Meta:
        ordering = ["-entry_date", "-created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "number"], name="accounting_entry_number_uniq"
            ),
            models.CheckConstraint(
                condition=Q(status="DRAFT", posted_at__isnull=True)
                | Q(status="POSTED", posted_at__isnull=False),
                name="accounting_entry_lifecycle",
            ),
            models.CheckConstraint(
                condition=Q(base_currency_precision_snapshot__gte=0)
                & Q(base_currency_precision_snapshot__lte=8),
                name="accounting_entry_precision",
            ),
        ]
        indexes = [models.Index(fields=["company", "entry_date", "status"])]

    def clean(self):
        super().clean()
        try:
            domain.precision(self.base_currency_precision_snapshot)
            domain.business_date(self.entry_date)
            domain.text(self.memo)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if self.number != f"JE-{self.pk.hex}":
            raise ValidationError({"number": "Entry number must match its UUID."})
        if self.journal.company_id != self.company_id:
            raise ValidationError({"journal": "Journal is outside the entry company."})

    def _persist(self, token, *, creating=False):
        if self.status != self.Status.DRAFT or self.posted_at is not None:
            raise ValidationError("Only draft entries may be written.")
        return super()._persist(token, creating=creating)

    def _post(self, token, posted_at):
        if (
            token is not _POST_TOKEN
            or self.status != self.Status.DRAFT
            or posted_at is None
            or timezone.is_naive(posted_at)
        ):
            raise ValidationError("Unsupported Accounting transition.")
        changed = models.QuerySet.update(
            type(self).objects.filter(
                pk=self.pk, company_id=self.company_id, status=self.Status.DRAFT
            ),
            status=self.Status.POSTED,
            posted_at=posted_at,
            updated_at=posted_at,
        )
        if changed != 1:
            raise ValidationError("Entry state changed.")
        self.status = self.Status.POSTED
        self.posted_at = self.updated_at = posted_at

    @property
    def totals(self):
        return domain.totals(self.lines.values_list("debit", "credit"))

    @property
    def formatted_debit(self):
        return domain.display(self.totals[0], self.base_currency_precision_snapshot)

    @property
    def formatted_credit(self):
        return domain.display(self.totals[1], self.base_currency_precision_snapshot)

    def __str__(self):
        return self.number


class JournalEntryLine(AccountingModel):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    party = models.ForeignKey("party.Party", on_delete=models.PROTECT, null=True, blank=True)
    description = models.TextField(blank=True)
    debit = models.DecimalField(max_digits=38, decimal_places=8)
    credit = models.DecimalField(max_digits=38, decimal_places=8)
    position = models.PositiveIntegerField()
    _immutable_fields = ("company_id", "journal_entry_id", "position", "created_at")

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["journal_entry", "position"], name="accounting_line_position_uniq"
            ),
            models.CheckConstraint(
                condition=Q(position__gt=0, position__lte=domain.MAX_POSITION),
                name="accounting_line_position",
            ),
            models.CheckConstraint(
                condition=Q(
                    debit__gte=0,
                    credit__gte=0,
                    debit__lt=domain.AMOUNT_LIMIT,
                    credit__lt=domain.AMOUNT_LIMIT,
                ),
                name="accounting_line_amount_range",
            ),
            models.CheckConstraint(
                condition=Q(debit__gt=0, credit=0) | Q(credit__gt=0, debit=0),
                name="accounting_line_sides",
            ),
        ]

    def clean(self):
        super().clean()
        for field in ("debit", "credit"):
            try:
                setattr(
                    self,
                    field,
                    domain.amount(
                        getattr(self, field),
                        self.journal_entry.base_currency_precision_snapshot,
                    ),
                )
            except ValueError as exc:
                raise ValidationError({field: str(exc)}) from exc
        try:
            domain.sides(
                self.debit, self.credit, self.journal_entry.base_currency_precision_snapshot
            )
            domain.position(self.position)
            domain.text(self.description)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if (
            self.journal_entry.company_id != self.company_id
            or self.account.company_id != self.company_id
            or (self.party_id and self.party.company_id != self.company_id)
        ):
            raise ValidationError("Line relationships must share the owning company.")

    def _persist(self, token, *, creating=False, remove=False):
        if token is not _WRITE_TOKEN:
            raise ValidationError("Unauthorized Accounting line persistence.")
        # Resolve persisted ownership BEFORE trusting the mutable in-memory parent.
        original = None
        if not creating:
            original = type(self).objects.filter(pk=self.pk).first()
            if original is None:
                raise ValidationError("Line no longer exists.")
        parent_id = original.journal_entry_id if original else self.journal_entry_id
        parent = JournalEntry.objects.select_for_update().get(pk=parent_id)
        if parent.status != JournalEntry.Status.DRAFT or parent.company_id != self.company_id:
            raise ValidationError("Only the owning draft's lines may change.")
        if original:
            original = type(self).objects.select_for_update().get(pk=self.pk)
            if any(getattr(original, f) != getattr(self, f) for f in self._immutable_fields):
                raise ValidationError("Line ownership and position are immutable.")
        if remove:
            return models.Model.delete(self)
        return super()._persist(token, creating=creating)

    @property
    def formatted_debit(self):
        return domain.display(self.debit, self.journal_entry.base_currency_precision_snapshot)

    @property
    def formatted_credit(self):
        return domain.display(self.credit, self.journal_entry.base_currency_precision_snapshot)

    def __str__(self):
        return f"{self.journal_entry_id} / {self.position}"
