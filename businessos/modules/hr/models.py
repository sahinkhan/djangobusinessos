"""HR-owned schema and closed ordinary-ORM mutation boundary.

Private operation-specific writes are in persistence.py.  A model instance is never
an authorization capability, including one loaded through the base manager.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q

from businessos.core.common.models import UUIDTimestampedModel

MAX_ORDINAL = 2_147_483_647
ORDINAL_VALIDATORS = [MinValueValidator(1), MaxValueValidator(MAX_ORDINAL)]


class HRQuerySet(models.QuerySet):
    def create(self, **kwargs):
        raise ValidationError("HR creation requires an authorized owning service.")

    def update(self, **kwargs):
        raise ValidationError("HR updates require an authorized owning service.")

    def delete(self):
        raise ValidationError("HR identities and history cannot be deleted.")

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("HR bulk creation and conflict upserts are unsupported.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("HR bulk updates are unsupported.")

    def get_or_create(self, *args, **kwargs):
        raise ValidationError("HR get_or_create is not an authorized mutation path.")

    def update_or_create(self, *args, **kwargs):
        raise ValidationError("HR update_or_create is not an authorized mutation path.")


class HROwnedModel(UUIDTimestampedModel):
    company = models.ForeignKey("organization.Company", on_delete=models.PROTECT)
    objects = HRQuerySet.as_manager()

    class Meta:
        abstract = True
        base_manager_name = "objects"
        default_manager_name = "objects"

    def save(self, *args, **kwargs):
        raise ValidationError("HR persistence requires an authorized owning service.")

    def save_base(self, *args, **kwargs):
        raise ValidationError("HR raw/save_base persistence is unsupported.")

    def delete(self, *args, **kwargs):
        raise ValidationError("HR identities and history cannot be deleted.")


def _ordinal_check(field):
    return Q(**{f"{field}__gte": 1, f"{field}__lte": MAX_ORDINAL})


def _nullable_ordinal_check(field):
    return Q(**{f"{field}__isnull": True}) | _ordinal_check(field)


class Department(HROwnedModel):
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1, validators=ORDINAL_VALIDATORS)

    class Meta(HROwnedModel.Meta):
        ordering = ["code", "id"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="hr_department_code_uniq"),
            models.CheckConstraint(condition=_ordinal_check("revision"), name="hr_department_rev"),
            models.CheckConstraint(condition=~Q(code=""), name="hr_department_code_nonempty"),
            models.CheckConstraint(condition=~Q(name=""), name="hr_department_name_nonempty"),
        ]
        indexes = [
            models.Index(fields=["company", "is_active", "code", "id"], name="hr_dept_active_code")
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class LeaveType(HROwnedModel):
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=True)
    revision = models.PositiveIntegerField(default=1, validators=ORDINAL_VALIDATORS)

    class Meta(HROwnedModel.Meta):
        ordering = ["code", "id"]
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="hr_leave_type_code_uniq"),
            models.CheckConstraint(condition=_ordinal_check("revision"), name="hr_leave_type_rev"),
            models.CheckConstraint(condition=~Q(code=""), name="hr_leave_type_code_nonempty"),
            models.CheckConstraint(condition=~Q(name=""), name="hr_leave_type_name_nonempty"),
        ]
        indexes = [
            models.Index(fields=["company", "is_active", "code", "id"], name="hr_type_active_code")
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Employee(HROwnedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ENDED = "ENDED", "Ended"

    party = models.ForeignKey("party.Party", on_delete=models.PROTECT)
    employee_number = models.CharField(max_length=32)
    user = models.ForeignKey("identity.User", null=True, blank=True, on_delete=models.PROTECT)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.PROTECT)
    branch = models.ForeignKey(
        "organization.Branch", null=True, blank=True, on_delete=models.PROTECT
    )
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    joining_date = models.DateField()
    leaving_date = models.DateField(null=True, blank=True)
    revision = models.PositiveIntegerField(default=1, validators=ORDINAL_VALIDATORS)

    class Meta(HROwnedModel.Meta):
        ordering = ["employee_number", "id"]
        constraints = [
            models.UniqueConstraint(fields=["company", "party"], name="hr_employee_party_uniq"),
            models.UniqueConstraint(
                fields=["company", "employee_number"], name="hr_employee_number_uniq"
            ),
            models.UniqueConstraint(
                fields=["company", "user"],
                condition=Q(status="ACTIVE", user__isnull=False),
                name="hr_employee_active_user_uniq",
            ),
            models.CheckConstraint(condition=_ordinal_check("revision"), name="hr_employee_rev"),
            models.CheckConstraint(
                condition=Q(status__in=["ACTIVE", "ENDED"]), name="hr_employee_status"
            ),
            models.CheckConstraint(
                condition=~Q(employee_number=""), name="hr_employee_number_nonempty"
            ),
            models.CheckConstraint(
                condition=Q(status="ACTIVE", leaving_date__isnull=True)
                | Q(
                    status="ENDED", leaving_date__isnull=False, leaving_date__gte=F("joining_date")
                ),
                name="hr_employee_end_dates",
            ),
        ]
        indexes = [
            models.Index(
                fields=["company", "branch", "employee_number", "id"], name="hr_employee_branch_num"
            ),
            models.Index(
                fields=["company", "status", "department"], name="hr_employee_status_dept"
            ),
            models.Index(fields=["company", "joining_date", "id"], name="hr_employee_joined"),
        ]

    def __str__(self):
        return self.employee_number


class Attendance(HROwnedModel):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    branch = models.ForeignKey(
        "organization.Branch", null=True, blank=True, on_delete=models.PROTECT
    )
    timezone = models.CharField(max_length=64)
    record_request_key = models.UUIDField()
    recorded_by = models.ForeignKey("identity.User", on_delete=models.PROTECT)

    class Meta(HROwnedModel.Meta):
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "record_request_key"], name="hr_attendance_record_key_uniq"
            ),
            models.CheckConstraint(condition=~Q(timezone=""), name="hr_attendance_zone_nonempty"),
        ]
        indexes = [
            models.Index(
                fields=["company", "branch", "employee", "id"], name="hr_attendance_branch"
            ),
            models.Index(fields=["company", "employee", "id"], name="hr_attendance_employee"),
        ]

    def __str__(self):
        return str(self.id)


class AttendanceRevision(HROwnedModel):
    class Operation(models.TextChoices):
        RECORD = "RECORD", "Record"
        CORRECT = "CORRECT", "Correct"
        VOID = "VOID", "Void"
        REINSTATE = "REINSTATE", "Reinstate"

    class Effect(models.TextChoices):
        ACTIVE_INTERVAL = "ACTIVE_INTERVAL", "Active interval"
        VOIDED = "VOIDED", "Voided"

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    attendance = models.ForeignKey(Attendance, on_delete=models.PROTECT, related_name="revisions")
    number = models.PositiveIntegerField(validators=ORDINAL_VALIDATORS)
    expected_revision = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(MAX_ORDINAL)]
    )
    operation = models.CharField(max_length=12, choices=Operation.choices)
    effect = models.CharField(max_length=16, choices=Effect.choices)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    local_start_date = models.DateField()
    local_end_date = models.DateField()
    reason = models.TextField(max_length=2000, blank=True)
    actor = models.ForeignKey("identity.User", on_delete=models.PROTECT)
    request_key = models.UUIDField()

    class Meta(HROwnedModel.Meta):
        ordering = ["-number", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["attendance", "number"], name="hr_revision_number_uniq"
            ),
            models.UniqueConstraint(
                fields=["attendance", "request_key"], name="hr_revision_request_uniq"
            ),
            models.CheckConstraint(condition=_ordinal_check("number"), name="hr_revision_number"),
            models.CheckConstraint(
                condition=Q(expected_revision__gte=0, expected_revision__lte=MAX_ORDINAL)
                & Q(expected_revision=F("number") - 1),
                name="hr_revision_expected",
            ),
            models.CheckConstraint(
                condition=Q(operation__in=["RECORD", "CORRECT", "VOID", "REINSTATE"]),
                name="hr_revision_operation",
            ),
            models.CheckConstraint(
                condition=Q(effect__in=["ACTIVE_INTERVAL", "VOIDED"]), name="hr_revision_effect"
            ),
            models.CheckConstraint(
                condition=Q(number=1, operation="RECORD") | (~Q(number=1) & ~Q(operation="RECORD")),
                name="hr_revision_initial",
            ),
            models.CheckConstraint(
                condition=Q(operation="VOID", effect="VOIDED")
                | (~Q(operation="VOID") & Q(effect="ACTIVE_INTERVAL")),
                name="hr_revision_void_effect",
            ),
            models.CheckConstraint(
                condition=Q(start_at__lt=F("end_at")), name="hr_revision_interval"
            ),
            models.CheckConstraint(
                condition=Q(local_start_date__lte=F("local_end_date")), name="hr_revision_dates"
            ),
            models.CheckConstraint(
                condition=Q(number=1) | ~Q(reason=""), name="hr_revision_reason"
            ),
        ]
        indexes = [
            models.Index(fields=["company", "employee", "start_at", "id"], name="hr_rev_emp_start"),
            models.Index(fields=["company", "employee", "end_at", "id"], name="hr_rev_emp_end"),
            models.Index(fields=["start_at", "id"], name="hr_rev_start"),
            models.Index(fields=["end_at", "id"], name="hr_rev_end"),
            models.Index(fields=["company", "start_at", "id"], name="hr_rev_company_start"),
            models.Index(
                fields=["company", "employee", "local_start_date", "id"],
                name="hr_rev_emp_local_start",
            ),
            models.Index(
                fields=["company", "employee", "local_end_date", "id"], name="hr_rev_emp_local_end"
            ),
        ]

    def __str__(self):
        return f"{self.attendance_id} / {self.number}"


class LeaveRequest(HROwnedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    class Decision(models.TextChoices):
        APPROVED = "APPROVED", "Approve"
        REJECTED = "REJECTED", "Reject"

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT)
    branch = models.ForeignKey(
        "organization.Branch", null=True, blank=True, on_delete=models.PROTECT
    )
    timezone = models.CharField(max_length=64)
    create_request_key = models.UUIDField()
    requester = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, related_name="hr_requested_leave"
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(max_length=2000, blank=True)
    window_start_at = models.DateTimeField()
    window_end_at = models.DateTimeField()
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.DRAFT)
    revision = models.PositiveIntegerField(default=1, validators=ORDINAL_VALIDATORS)
    submit_key = models.UUIDField(null=True, blank=True)
    submitted_by = models.ForeignKey(
        "identity.User",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="hr_submitted_leave",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    submit_from_revision = models.PositiveIntegerField(
        null=True, blank=True, validators=ORDINAL_VALIDATORS
    )
    submit_revision = models.PositiveIntegerField(
        null=True, blank=True, validators=ORDINAL_VALIDATORS
    )
    beneficiary_user_at_submission = models.ForeignKey(
        "identity.User",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="hr_beneficiary_leave",
    )
    decision_key = models.UUIDField(null=True, blank=True)
    decided_by = models.ForeignKey(
        "identity.User",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="hr_decided_leave",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_from_revision = models.PositiveIntegerField(
        null=True, blank=True, validators=ORDINAL_VALIDATORS
    )
    decision_revision = models.PositiveIntegerField(
        null=True, blank=True, validators=ORDINAL_VALIDATORS
    )
    decision = models.CharField(max_length=8, choices=Decision.choices, null=True, blank=True)  # noqa: DJ001
    decision_reason = models.TextField(max_length=2000, blank=True, default="")
    cancel_key = models.UUIDField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        "identity.User",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="hr_cancelled_leave",
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_from_revision = models.PositiveIntegerField(
        null=True, blank=True, validators=ORDINAL_VALIDATORS
    )
    cancel_revision = models.PositiveIntegerField(
        null=True, blank=True, validators=ORDINAL_VALIDATORS
    )
    cancel_reason = models.TextField(max_length=2000, blank=True, default="")

    class Meta(HROwnedModel.Meta):
        ordering = ["-start_date", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "create_request_key"], name="hr_leave_create_key_uniq"
            ),
            *[
                models.UniqueConstraint(
                    fields=["company", f"{event}_key"],
                    condition=Q(**{f"{event}_key__isnull": False}),
                    name=f"hr_leave_{event}_key_uniq",
                )
                for event in ("submit", "decision", "cancel")
            ],
            models.CheckConstraint(condition=_ordinal_check("revision"), name="hr_leave_revision"),
            *[
                models.CheckConstraint(
                    condition=_nullable_ordinal_check(f"{event}_{suffix}"),
                    name=f"hr_leave_{event}_{suffix}_bounds",
                )
                for event in ("submit", "decision", "cancel")
                for suffix in ("from_revision", "revision")
            ],
            models.CheckConstraint(
                condition=Q(status__in=["DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "CANCELLED"]),
                name="hr_leave_status",
            ),
            models.CheckConstraint(condition=~Q(timezone=""), name="hr_leave_zone_nonempty"),
            models.CheckConstraint(
                condition=Q(start_date__lte=F("end_date")), name="hr_leave_dates"
            ),
            models.CheckConstraint(
                condition=Q(window_start_at__lt=F("window_end_at")), name="hr_leave_window"
            ),
            models.CheckConstraint(
                condition=Q(decision__isnull=True) | Q(decision__in=["APPROVED", "REJECTED"]),
                name="hr_leave_decision",
            ),
            models.CheckConstraint(
                condition=Q(
                    submit_key__isnull=True,
                    submitted_by__isnull=True,
                    submitted_at__isnull=True,
                    submit_from_revision__isnull=True,
                    submit_revision__isnull=True,
                    beneficiary_user_at_submission__isnull=True,
                )
                | Q(
                    submit_key__isnull=False,
                    submitted_by__isnull=False,
                    submitted_at__isnull=False,
                    submit_from_revision__isnull=False,
                    submit_revision__isnull=False,
                    submit_revision=F("submit_from_revision") + 1,
                ),
                name="hr_leave_submit_receipt",
            ),
            models.CheckConstraint(
                condition=Q(
                    decision_key__isnull=True,
                    decided_by__isnull=True,
                    decided_at__isnull=True,
                    decision_from_revision__isnull=True,
                    decision_revision__isnull=True,
                    decision__isnull=True,
                    decision_reason="",
                )
                | Q(
                    decision_key__isnull=False,
                    decided_by__isnull=False,
                    decided_at__isnull=False,
                    decision_from_revision__isnull=False,
                    decision_revision__isnull=False,
                    decision__isnull=False,
                    submit_revision__isnull=False,
                    decision_revision=F("decision_from_revision") + 1,
                    decision_from_revision=F("submit_revision"),
                ),
                name="hr_leave_decision_receipt",
            ),
            models.CheckConstraint(
                condition=Q(
                    cancel_key__isnull=True,
                    cancelled_by__isnull=True,
                    cancelled_at__isnull=True,
                    cancel_from_revision__isnull=True,
                    cancel_revision__isnull=True,
                    cancel_reason="",
                )
                | (
                    Q(
                        cancel_key__isnull=False,
                        cancelled_by__isnull=False,
                        cancelled_at__isnull=False,
                        cancel_from_revision__isnull=False,
                        cancel_revision__isnull=False,
                        cancel_revision=F("cancel_from_revision") + 1,
                    )
                    & ~Q(cancel_reason="")
                ),
                name="hr_leave_cancel_receipt",
            ),
            models.CheckConstraint(
                condition=Q(cancel_key__isnull=True)
                | Q(decision_revision__isnull=False, cancel_from_revision=F("decision_revision"))
                | Q(
                    decision_revision__isnull=True,
                    submit_revision__isnull=False,
                    cancel_from_revision=F("submit_revision"),
                )
                | Q(decision_revision__isnull=True, submit_revision__isnull=True),
                name="hr_leave_cancel_source",
            ),
            models.CheckConstraint(
                condition=Q(
                    status="DRAFT",
                    submit_key__isnull=True,
                    decision_key__isnull=True,
                    cancel_key__isnull=True,
                )
                | Q(
                    status="SUBMITTED",
                    submit_key__isnull=False,
                    decision_key__isnull=True,
                    cancel_key__isnull=True,
                    revision=F("submit_revision"),
                )
                | Q(
                    status="APPROVED",
                    submit_key__isnull=False,
                    decision="APPROVED",
                    decision_key__isnull=False,
                    cancel_key__isnull=True,
                    revision=F("decision_revision"),
                )
                | Q(
                    status="REJECTED",
                    submit_key__isnull=False,
                    decision="REJECTED",
                    decision_key__isnull=False,
                    cancel_key__isnull=True,
                    revision=F("decision_revision"),
                )
                | (
                    Q(status="CANCELLED", cancel_key__isnull=False, revision=F("cancel_revision"))
                    & (Q(decision__isnull=True) | Q(decision="APPROVED"))
                ),
                name="hr_leave_status_receipts",
            ),
            models.CheckConstraint(
                condition=(
                    Q(submit_key__isnull=True)
                    | Q(decision_key__isnull=True)
                    | ~Q(submit_key=F("decision_key"))
                )
                & (
                    Q(submit_key__isnull=True)
                    | Q(cancel_key__isnull=True)
                    | ~Q(submit_key=F("cancel_key"))
                )
                & (
                    Q(decision_key__isnull=True)
                    | Q(cancel_key__isnull=True)
                    | ~Q(decision_key=F("cancel_key"))
                ),
                name="hr_leave_distinct_event_keys",
            ),
            models.CheckConstraint(
                condition=Q(decision__isnull=True)
                | ~Q(decision="REJECTED")
                | ~Q(decision_reason=""),
                name="hr_leave_rejection_reason",
            ),
        ]
        indexes = [
            models.Index(
                fields=["company", "employee", "status", "start_date", "end_date"],
                name="hr_leave_employee_dates",
            ),
            models.Index(
                fields=["company", "employee", "status", "window_start_at"],
                name="hr_leave_employee_window",
            ),
            models.Index(
                fields=["company", "branch", "start_date", "id"], name="hr_leave_branch_dates"
            ),
            models.Index(
                fields=["company", "status", "start_date", "id"], name="hr_leave_status_dates"
            ),
        ]

    def __str__(self):
        return str(self.id)
