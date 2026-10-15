"""HTTP-only scalar adapters; owning services retain all HR business decisions."""

from datetime import datetime
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from django import forms
from django.utils import timezone

from businessos.core.access.forms import CompanyBoundForm


class HRBoundForm(CompanyBoundForm):
    scope_branch_id = forms.UUIDField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, branch_id=None, choices=None, **kwargs):
        self.rendered_branch_id = branch_id
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["scope_branch_id"] = branch_id
        for name, values in (choices or {}).items():
            if name in self.fields and isinstance(self.fields[name], forms.ChoiceField):
                empty = (
                    [("", "— None —")] if not self.fields[name].required else [("", "— Select —")]
                )
                self.fields[name].choices = empty + [(str(key), label) for key, label in values]

    def clean(self):
        data = super().clean()
        branch = data.pop("scope_branch_id", None)
        if branch != self.rendered_branch_id:
            raise forms.ValidationError("Branch scope changed. Reload this form before continuing.")
        return data


def _choice(label, *, required=True):
    return forms.TypedChoiceField(
        label=label, choices=(), coerce=UUID, empty_value=None, required=required
    )


class SetupForm(HRBoundForm):
    code = forms.CharField(max_length=32)
    name = forms.CharField(max_length=160)
    is_active = forms.TypedChoiceField(
        choices=[("true", "Active"), ("false", "Inactive")], coerce=lambda value: value == "true"
    )
    expected_revision = forms.IntegerField(
        min_value=1, max_value=2_147_483_647, widget=forms.HiddenInput
    )

    def __init__(self, *args, editing=False, **kwargs):
        super().__init__(*args, **kwargs)
        if editing:
            self.fields.pop("code")
        else:
            self.fields.pop("is_active")
            self.fields.pop("expected_revision")


class EmployeeForm(HRBoundForm):
    party_id = _choice("Person")
    employee_number = forms.CharField(max_length=32)
    joining_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    leaving_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    user_id = _choice("User association", required=False)
    department_id = _choice("Department", required=False)
    branch_id = _choice("Current branch", required=False)
    expected_revision = forms.IntegerField(
        min_value=1, max_value=2_147_483_647, widget=forms.HiddenInput
    )

    def __init__(self, *args, editing=False, ended=False, **kwargs):
        super().__init__(*args, **kwargs)
        if editing:
            for field in ("party_id", "employee_number", "branch_id"):
                self.fields.pop(field)
        else:
            self.fields.pop("expected_revision")
        if not ended:
            self.fields.pop("leaving_date")


class RevisionForm(HRBoundForm):
    expected_revision = forms.IntegerField(
        min_value=1, max_value=2_147_483_647, widget=forms.HiddenInput
    )


class EndEmployeeForm(RevisionForm):
    leaving_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class TransferEmployeeForm(RevisionForm):
    branch_id = _choice("New current branch", required=False)


class FrozenDateTimeField(forms.DateTimeField):
    """Preserve an unchanged server-trusted fold/precision before Django parsing."""

    def __init__(self, *, business_timezone, original=None, **kwargs):
        self.business_timezone = business_timezone
        self.original = original
        super().__init__(
            widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            input_formats=["%Y-%m-%dT%H:%M"],
            help_text=(
                f"Timezone: {business_timezone.key}. Unchanged times retain original precision."
            ),
            **kwargs,
        )

    def prepare_value(self, value):
        if isinstance(value, datetime) and timezone.is_aware(value):
            value = timezone.make_naive(value, self.business_timezone)
        return super().prepare_value(value)

    def to_python(self, value):
        if (
            isinstance(value, str)
            and self.original is not None
            and timezone.is_aware(self.original)
        ):
            if value == timezone.localtime(self.original, self.business_timezone).strftime(
                "%Y-%m-%dT%H:%M"
            ):
                return self.original
        with timezone.override(self.business_timezone):
            return super().to_python(value)


class AttendanceForm(RevisionForm):
    employee_id = _choice("Employee")
    request_key = forms.UUIDField(widget=forms.HiddenInput)
    reason = forms.CharField(
        max_length=2000, required=False, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, zone, operation="RECORD", originals=None, **kwargs):
        super().__init__(*args, **kwargs)
        originals = originals or {}
        if operation == "RECORD":
            self.fields.pop("expected_revision")
        else:
            self.fields.pop("employee_id")
            self.fields["reason"].required = True
        if operation != "VOID":
            for name, label in (("start_at", "Start"), ("end_at", "End")):
                self.fields[name] = FrozenDateTimeField(
                    label=label, business_timezone=ZoneInfo(zone), original=originals.get(name)
                )
        if not self.is_bound:
            self.initial.setdefault("request_key", uuid4())


class LeaveForm(RevisionForm):
    employee_id = _choice("Employee")
    create_request_key = forms.UUIDField(widget=forms.HiddenInput)
    leave_type_id = _choice("Leave type")
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    reason = forms.CharField(
        max_length=2000, required=False, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, editing=False, **kwargs):
        super().__init__(*args, **kwargs)
        if editing:
            self.fields.pop("employee_id")
            self.fields.pop("create_request_key")
        else:
            self.fields.pop("expected_revision")
        if not self.is_bound:
            self.initial.setdefault("create_request_key", uuid4())


class LeaveActionForm(RevisionForm):
    request_key = forms.UUIDField(widget=forms.HiddenInput)
    reason = forms.CharField(
        max_length=2000, required=False, widget=forms.Textarea(attrs={"rows": 3})
    )

    def __init__(self, *args, operation, **kwargs):
        super().__init__(*args, **kwargs)
        # A request's original narrative is not a new decision/cancellation reason.
        self.initial.pop("reason", None)
        if operation == "submit_leave":
            self.fields.pop("reason")
        elif operation in {"reject_leave", "cancel_leave"}:
            self.fields["reason"].required = True
        if "reason" in self.fields:
            self.fields["reason"].label = (
                "Cancellation reason" if operation == "cancel_leave" else "Decision reason"
            )
        if not self.is_bound:
            self.initial.setdefault("request_key", uuid4())


class FilterForm(forms.Form):
    q = forms.CharField(max_length=200, required=False, label="Search")
    status = forms.CharField(max_length=16, required=False)
    branch_id = forms.UUIDField(required=False)
    employee_id = forms.UUIDField(required=False)
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    active = forms.ChoiceField(
        required=False, choices=[("", "All"), ("yes", "Active"), ("no", "Inactive")]
    )


class ChoiceFilterForm(forms.Form):
    choices_q = forms.CharField(max_length=200, required=False, label="Shared search (optional)")
    party_q = forms.CharField(max_length=200, required=False, label="Person name")
    user_q = forms.CharField(max_length=200, required=False, label="Exact User UUID")
    department_q = forms.CharField(max_length=200, required=False, label="Department code or name")
    branch_q = forms.CharField(max_length=200, required=False, label="Branch code or name")
    employee_q = forms.CharField(
        max_length=200, required=False, label="Employee number or Person name"
    )
    type_q = forms.CharField(max_length=200, required=False, label="Leave type code or name")
