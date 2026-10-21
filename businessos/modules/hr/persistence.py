"""Private, operation-specific persistence.  These are not authorization APIs.

Owning services enter the admitted transaction, lock the complete reference set,
validate domain rules and obtain final Core authorization before invoking these
small primitives. Ordinary managers never provide a writable escape hatch.
"""

from contextvars import ContextVar
from datetime import UTC, datetime
from functools import wraps
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connections, models
from django.utils import timezone

from businessos.core.access.models import UserCompanyAccess
from businessos.core.database import current_database_alias
from businessos.core.organization.models import Branch, Company
from businessos.modules.party.models import Party

from . import domain
from .civil_time import leave_window, occupied_dates
from .models import Attendance, AttendanceRevision, Department, Employee, LeaveRequest, LeaveType

# Fixed owner operations, not caller-selected model/field capabilities. The
# ContextVar exists only while one named primitive is executing and is always
# checked against the live, transaction-bound HR admission before a write.
_OWNER_WRITE = ContextVar("hr_owner_write", default=None)
_INSERTED_ROW = ContextVar("hr_just_inserted_row", default=None)
_WRITE_SPECS = {
    "_create_department": (Department, ("hr.department.manage", "hr.department.view"), None, ()),
    "_update_department": (
        Department,
        ("hr.department.manage", "hr.department.view"),
        "department_id",
        ("name", "is_active"),
    ),
    "_create_leave_type": (LeaveType, ("hr.leave_type.manage", "hr.leave.view"), None, ()),
    "_update_leave_type": (
        LeaveType,
        ("hr.leave_type.manage", "hr.leave.view"),
        "leave_type_id",
        ("name", "is_active"),
    ),
    "_create_employee": (Employee, ("hr.employee.manage", "hr.employee.view"), None, ()),
    "_update_employee": (
        Employee,
        ("hr.employee.manage", "hr.employee.view"),
        "employee_id",
        ("joining_date", "user_id", "department_id", "leaving_date"),
    ),
    "_end_employee": (
        Employee,
        ("hr.employee.manage", "hr.employee.view"),
        "employee_id",
        ("status", "leaving_date"),
    ),
    "_transfer_employee_branch": (
        Employee,
        ("hr.employee.manage", "hr.employee.view"),
        "employee_id",
        ("branch_id",),
    ),
    "_create_attendance": (
        Attendance,
        ("hr.attendance.record", "hr.attendance.view", "hr.employee.view"),
        None,
        (),
    ),
    "_append_attendance_revision": (
        AttendanceRevision,
        ("hr.attendance.view", "hr.employee.view"),
        "attendance_id",
        (),
    ),
    "_create_leave": (
        LeaveRequest,
        ("hr.leave.request", "hr.leave.view", "hr.employee.view"),
        None,
        (),
    ),
    "_update_leave": (
        LeaveRequest,
        ("hr.leave.request", "hr.leave.view", "hr.employee.view"),
        "leave_id",
        ("leave_type_id", "start_date", "end_date", "window_start_at", "window_end_at", "reason"),
    ),
    "_submit_leave": (
        LeaveRequest,
        ("hr.leave.request", "hr.leave.view", "hr.employee.view"),
        "leave_id",
        (
            "status",
            "submit_key",
            "submitted_by_id",
            "submitted_at",
            "submit_from_revision",
            "submit_revision",
            "beneficiary_user_at_submission_id",
        ),
    ),
    "_decide_leave": (
        LeaveRequest,
        ("hr.leave.approve", "hr.leave.view", "hr.employee.view"),
        "leave_id",
        (
            "status",
            "decision",
            "decision_key",
            "decided_by_id",
            "decided_at",
            "decision_from_revision",
            "decision_revision",
            "decision_reason",
        ),
    ),
    "_cancel_leave": (
        LeaveRequest,
        ("hr.leave.cancel", "hr.leave.view", "hr.employee.view"),
        "leave_id",
        (
            "status",
            "cancel_key",
            "cancelled_by_id",
            "cancelled_at",
            "cancel_from_revision",
            "cancel_revision",
            "cancel_reason",
        ),
    ),
}


def _authority(company_id, permissions=(), *, anchors=(), user_ids=()):
    from .admission import AdmissionError, require_persistence_scope

    try:
        return require_persistence_scope(
            company_id, permissions, anchors=anchors, user_ids=user_ids
        )
    except AdmissionError as exc:
        raise ValidationError(str(exc)) from exc


def _owner_primitive(function):
    """Bind a named primitive to its exact fixed model, action and target."""
    name = function.__name__
    model, permissions, target_key, allowed = _WRITE_SPECS[name]

    @wraps(function)
    def execute(**kwargs):
        company_id = _identity("company", kwargs["company_id"])
        target = _identity("id", kwargs[target_key]) if target_key is not None else None
        target_model = Attendance if model is AttendanceRevision else model
        anchors = () if target is None else ((target_model._meta.label_lower, target),)
        codes = list(permissions)
        if name == "_append_attendance_revision":
            codes.append(
                "hr.attendance.record"
                if kwargs["expected_revision"] == 0
                else "hr.attendance.correct"
            )
        if (
            name in {"_create_employee", "_update_employee"}
            and kwargs.get("department_id") is not None
        ):
            codes.append("hr.department.view")
        operation = _authority(company_id, codes, anchors=anchors)
        if _OWNER_WRITE.get() is not None:
            raise ValidationError("HR owner primitives cannot recursively substitute write scope.")
        binding = (name, model, company_id, target, frozenset(allowed), operation)
        token = _OWNER_WRITE.set(binding)
        try:
            if (
                name
                in {
                    "_create_department",
                    "_update_department",
                    "_create_leave_type",
                    "_update_leave_type",
                    "_create_employee",
                    "_transfer_employee_branch",
                }
                and operation.context.branch_id is not None
            ):
                raise ValidationError("This HR owner operation requires Company-wide context.")
            result = function(**kwargs)
            operation.checkpoint()
            return result
        except Exception as exc:
            from .admission import _poison

            _poison(operation, exc)
            raise
        finally:
            _OWNER_WRITE.reset(token)

    return execute


def _binding(row):
    binding = _OWNER_WRITE.get()
    if binding is None or type(row) is not binding[1] or row.company_id != binding[2]:
        from .admission import _CURRENT, _poison

        error = ValidationError("HR writes require their exact named owner primitive and Company.")
        if (operation := _CURRENT.get()) is not None:
            _poison(operation, error)
        raise error
    _authority(binding[2])
    if binding[3] is not None and not isinstance(row, AttendanceRevision) and row.pk != binding[3]:
        raise ValidationError("HR persistence target differs from its protected owner identity.")
    return binding


def _owns_insert(operation, *, row=None, parent_id=None):
    """Attest only the exact row just INSERTed by the currently bound primitive.

    Admission cannot promote a caller's loaded existing row to acquired lock
    evidence or clear an orphan-parent obligation. This proof is live only
    across the immediate post-INSERT registration calls below, never returned.
    """
    binding = _OWNER_WRITE.get()
    inserted = _INSERTED_ROW.get()
    if (
        binding is None
        or inserted is None
        or binding[5] is not operation
        or inserted[0] is not operation
    ):
        return False
    saved = inserted[1]
    if type(saved) is not binding[1] or saved.company_id != binding[2]:
        return False
    if saved._state.adding or saved._state.db != operation.alias:
        return False
    if row is not None:
        return row is saved and parent_id is None
    return (
        parent_id is not None
        and isinstance(saved, AttendanceRevision)
        and saved.number == 1
        and saved.expected_revision == 0
        and saved.attendance_id == parent_id == binding[3]
    )


def _value(field, normalizer, value, **kwargs):
    try:
        return normalizer(value, **kwargs)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError({field: str(exc)}) from exc


def _identity(field, value, *, optional=False):
    if optional and value is None:
        return None
    return _value(field, domain.identity, value)


def _alias():
    alias = current_database_alias()
    if not connections[alias].in_atomic_block:
        raise ValidationError("HR private persistence requires an owning transaction.")
    return alias


def _locked(model, identity, company_id):
    identity = _identity("id", identity)
    operation = _authority(company_id, anchors=[(model._meta.label_lower, identity)])
    rows = operation.lock_rows(model, [identity])
    if len(rows) != 1:
        raise ValidationError("The HR record is unavailable in the selected company.")
    row = rows[0]
    if (
        model in {Employee, Attendance, LeaveRequest}
        and operation.context.branch_id is not None
        and row.branch_id != operation.context.branch_id
    ):
        raise ValidationError("The protected HR record is outside the selected Branch.")
    return row


def _expected(row, expected_revision):
    expected = _value("expected_revision", domain.revision, expected_revision)
    if row.revision != expected:
        raise ValidationError({"expected_revision": "The HR record revision has changed."})


def _insert(row):
    name, _, company_id, _, _, operation = _binding(row)
    if not name.startswith("_create_") and name != "_append_attendance_revision":
        raise ValidationError("This HR owner primitive cannot insert records.")
    alias = _alias()
    if not row._state.adding or row._state.db not in (None, alias):
        raise ValidationError("Private HR insertion requires a new selected-alias instance.")
    row._state.db = alias
    if hasattr(row, "revision") and row.revision != 1:
        raise ValidationError("New editable HR records must start at revision one.")
    if isinstance(row, Employee) and (
        row.status != Employee.Status.ACTIVE or row.leaving_date is not None
    ):
        raise ValidationError("New Employee lifecycle must be ACTIVE without a leaving date.")
    if isinstance(row, LeaveRequest) and (
        row.status != LeaveRequest.Status.DRAFT
        or any(
            getattr(row, f"{event}_key") is not None for event in ("submit", "decision", "cancel")
        )
    ):
        raise ValidationError("New Leave must be DRAFT without lifecycle receipts.")
    if isinstance(row, Attendance):
        if row.pk not in operation.reserved_attendance_ids:
            raise ValidationError("Attendance creation needs a pre-authority identity reservation.")
    if isinstance(row, (Attendance, LeaveRequest)) and operation.context.branch_id is not None:
        if row.branch_id != operation.context.branch_id:
            raise ValidationError("New HR snapshots must remain inside the selected Branch.")
    if isinstance(row, AttendanceRevision):
        if row.attendance_id != _OWNER_WRITE.get()[3]:
            raise ValidationError("Revision insertion cannot replace its protected Attendance.")
        parent = Attendance.objects.using(alias).get(pk=row.attendance_id, company_id=company_id)
        if (row.employee_id, row.company_id) != (parent.employee_id, parent.company_id):
            raise ValidationError("Revision scope must match its persisted Attendance parent.")
    row.full_clean()
    # Deliberately call the base implementation: public save/save_base stay closed.
    # No mutable enable flag or publicly usable generic persistence method exists.
    models.Model.save_base(row, using=alias, force_insert=True)
    proof = _INSERTED_ROW.set((operation, row))
    try:
        operation.register_created_row(row)
        if isinstance(row, Attendance):
            operation.register_attendance_creation(row)
        elif isinstance(row, AttendanceRevision) and row.number == 1:
            operation.complete_attendance_creation(row.attendance_id)
    finally:
        _INSERTED_ROW.reset(proof)
    return row


def _write_changed(row, fields):
    name, _, company_id, target_id, allowed, _ = _binding(row)
    if not allowed or not fields or len(set(fields)) != len(fields) or not set(fields) <= allowed:
        raise ValidationError("This HR owner operation does not permit the requested columns.")
    alias = _alias()
    if row._state.adding or row._state.db != alias:
        raise ValidationError("Private HR update requires a persisted selected-alias instance.")
    persisted = type(row).objects.using(alias).filter(pk=target_id, company_id=company_id).first()
    if persisted is None or row.revision != persisted.revision:
        raise ValidationError("The protected HR persistence revision has changed.")
    differences = {
        field.attname
        for field in row._meta.concrete_fields
        if getattr(row, field.attname) != getattr(persisted, field.attname)
    }
    if not differences or not differences <= set(fields):
        raise ValidationError(
            "HR identity, omitted fields and frozen evidence cannot be rewritten."
        )
    _transition(name, persisted, row)
    row.revision = _value("revision", domain.next_revision, persisted.revision)
    row.updated_at = timezone.now()
    row.full_clean()
    models.Model.save_base(
        row,
        using=alias,
        force_update=True,
        update_fields=frozenset([*fields, "revision", "updated_at"]),
    )
    return row


def _transition(name, persisted, row):
    """Persisted state, not mutable input status, selects legal field transitions."""
    if name == "_end_employee":
        if persisted.status != Employee.Status.ACTIVE or row.status != Employee.Status.ENDED:
            raise ValidationError("Employee ending must retain the ACTIVE to ENDED transition.")
    elif name == "_update_employee":
        if row.status != persisted.status or (
            persisted.status == Employee.Status.ACTIVE and row.leaving_date is not None
        ):
            raise ValidationError("Employee edit cannot change its persisted lifecycle.")
    elif name == "_update_leave":
        if persisted.status != LeaveRequest.Status.DRAFT or row.status != LeaveRequest.Status.DRAFT:
            raise ValidationError("Submitted Leave content is frozen.")
    elif name in {"_submit_leave", "_decide_leave", "_cancel_leave"}:
        event, required, result = {
            "_submit_leave": (
                "submit",
                {LeaveRequest.Status.DRAFT},
                {LeaveRequest.Status.SUBMITTED},
            ),
            "_decide_leave": (
                "decision",
                {LeaveRequest.Status.SUBMITTED},
                {LeaveRequest.Status.APPROVED, LeaveRequest.Status.REJECTED},
            ),
            "_cancel_leave": (
                "cancel",
                {
                    LeaveRequest.Status.DRAFT,
                    LeaveRequest.Status.SUBMITTED,
                    LeaveRequest.Status.APPROVED,
                },
                {LeaveRequest.Status.CANCELLED},
            ),
        }[name]
        if (
            persisted.status not in required
            or row.status not in result
            or getattr(persisted, f"{event}_key") is not None
            or getattr(row, f"{event}_from_revision") != persisted.revision
            or getattr(row, f"{event}_revision") != domain.next_revision(persisted.revision)
        ):
            raise ValidationError(
                "The Leave receipt does not describe the exact protected transition."
            )
        if name == "_cancel_leave" and persisted.status == LeaveRequest.Status.APPROVED:
            _authority(row.company_id, ["hr.leave.approve"])


def _scoped_reference(model, identity, company_id, field, *, active=False):
    if identity is None:
        return None
    identity = _identity(field, identity)
    _authority(company_id, anchors=[(model._meta.label_lower, identity)])
    query = model.objects.using(_alias()).filter(pk=identity, company_id=company_id)
    if active:
        query = query.filter(is_active=True)
    row = query.first()
    if row is None:
        raise ValidationError({field: "The reference is outside the company or unavailable."})
    return row


def _new_user(user_id):
    if user_id is None:
        return None
    identity = _identity("user", user_id)
    binding = _OWNER_WRITE.get()
    if binding is None:
        raise ValidationError("User association writes require a named HR owner primitive.")
    _authority(binding[2], user_ids=[identity])
    user = get_user_model().objects.using(_alias()).filter(pk=identity, is_active=True).first()
    if user is None:
        raise ValidationError({"user": "The association User must exist and be active."})
    if (
        not user.is_superuser
        and not UserCompanyAccess.objects.using(_alias())
        .filter(user_id=identity, company_id=binding[2])
        .exists()
    ):
        raise ValidationError({"user": "The association User must have selected Company access."})
    return identity


@_owner_primitive
def _create_department(*, company_id, code, name):
    return _insert(
        Department(
            company_id=_identity("company", company_id),
            code=_value("code", domain.code, code),
            name=_value("name", domain.text, name, maximum=160, required=True),
        )
    )


@_owner_primitive
def _update_department(*, company_id, department_id, expected_revision, name, is_active):
    row = _locked(Department, department_id, company_id)
    _expected(row, expected_revision)
    values = {
        "name": _value("name", domain.text, name, maximum=160, required=True),
        "is_active": _value("is_active", domain.boolean, is_active),
    }
    if (
        not values["is_active"]
        and Employee.objects.using(_alias())
        .filter(company_id=row.company_id, department_id=row.pk, status=Employee.Status.ACTIVE)
        .exists()
    ):
        raise ValidationError(
            {"is_active": "Reassign active Employees before retiring a Department."}
        )
    changed = [field for field, value in values.items() if getattr(row, field) != value]
    for field in changed:
        setattr(row, field, values[field])
    return _write_changed(row, changed) if changed else row


@_owner_primitive
def _create_leave_type(*, company_id, code, name):
    return _insert(
        LeaveType(
            company_id=_identity("company", company_id),
            code=_value("code", domain.code, code),
            name=_value("name", domain.text, name, maximum=160, required=True),
        )
    )


@_owner_primitive
def _update_leave_type(*, company_id, leave_type_id, expected_revision, name, is_active):
    row = _locked(LeaveType, leave_type_id, company_id)
    _expected(row, expected_revision)
    values = {
        "name": _value("name", domain.text, name, maximum=160, required=True),
        "is_active": _value("is_active", domain.boolean, is_active),
    }
    changed = [field for field, value in values.items() if getattr(row, field) != value]
    for field in changed:
        setattr(row, field, values[field])
    return _write_changed(row, changed) if changed else row


@_owner_primitive
def _create_employee(
    *,
    company_id,
    party_id,
    employee_number,
    joining_date,
    user_id=None,
    department_id=None,
    branch_id=None,
):
    company_id = _identity("company", company_id)
    party = _scoped_reference(Party, party_id, company_id, "party", active=True)
    if party is None or party.party_type != Party.Type.PERSON:
        raise ValidationError({"party": "An active same-company PERSON is required."})
    _scoped_reference(Department, department_id, company_id, "department", active=True)
    _scoped_reference(Branch, branch_id, company_id, "branch", active=True)
    return _insert(
        Employee(
            company_id=company_id,
            party_id=party.pk,
            employee_number=_value("employee_number", domain.code, employee_number),
            joining_date=_value("joining_date", domain.calendar_date, joining_date),
            user_id=_new_user(user_id),
            department_id=_identity("department", department_id, optional=True),
            branch_id=_identity("branch", branch_id, optional=True),
        )
    )


@_owner_primitive
def _update_employee(
    *,
    company_id,
    employee_id,
    expected_revision,
    joining_date,
    user_id,
    department_id,
    leaving_date,
):
    row = _locked(Employee, employee_id, company_id)
    _expected(row, expected_revision)
    if row.department_id is not None or department_id is not None:
        _authority(row.company_id, ["hr.department.view"])
    new_user = _identity("user", user_id, optional=True)
    new_department = _identity("department", department_id, optional=True)
    if new_user != row.user_id:
        _new_user(new_user)
    if new_department != row.department_id:
        _scoped_reference(Department, new_department, row.company_id, "department", active=True)
    if row.status == Employee.Status.ACTIVE and leaving_date is not None:
        raise ValidationError({"leaving_date": "Use end_employee to end an active Employee."})
    values = {
        "joining_date": _value("joining_date", domain.calendar_date, joining_date),
        "user_id": new_user,
        "department_id": new_department,
        "leaving_date": None
        if leaving_date is None
        else _value("leaving_date", domain.calendar_date, leaving_date),
    }
    changed = [field for field, value in values.items() if getattr(row, field) != value]
    for field in changed:
        setattr(row, field, values[field])
    # Exact column sets intentionally do not rewrite an unchanged historical User FK.
    return _write_changed(row, changed) if changed else row


@_owner_primitive
def _end_employee(*, company_id, employee_id, expected_revision, leaving_date):
    row = _locked(Employee, employee_id, company_id)
    _expected(row, expected_revision)
    leaving_date = _value("leaving_date", domain.calendar_date, leaving_date)
    if row.status == Employee.Status.ENDED:
        if row.leaving_date != leaving_date:
            raise ValidationError({"leaving_date": "Use an explicit date correction after ending."})
        return row
    if row.status != Employee.Status.ACTIVE:
        raise ValidationError({"status": "Unsupported persisted Employee lifecycle."})
    row.status = Employee.Status.ENDED
    row.leaving_date = leaving_date
    return _write_changed(row, ["status", "leaving_date"])


@_owner_primitive
def _transfer_employee_branch(*, company_id, employee_id, expected_revision, branch_id):
    row = _locked(Employee, employee_id, company_id)
    _expected(row, expected_revision)
    branch_id = _identity("branch", branch_id, optional=True)
    if row.branch_id == branch_id:
        return row
    _scoped_reference(Branch, branch_id, row.company_id, "branch", active=True)
    row.branch_id = branch_id
    return _write_changed(row, ["branch_id"])


def _zone(value):
    if not isinstance(value, str) or not value or len(value) > 64:
        raise ValidationError({"timezone": "Use an IANA timezone identity."})
    try:
        ZoneInfo(value)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ValidationError({"timezone": "Use a known IANA timezone identity."}) from exc
    return value


def _new_snapshot_zone(company_id, timezone_name):
    value = _zone(timezone_name)
    if (
        not Company.objects.using(_alias())
        .filter(pk=company_id, is_active=True, timezone=value)
        .exists()
    ):
        raise ValidationError({"timezone": "New snapshots use the active Company's current zone."})
    return value


def _instant(field, value):
    if not isinstance(value, datetime):
        raise ValidationError({field: "Use an aware datetime instant."})
    try:
        if timezone.is_naive(value):
            raise ValidationError({field: "Use an aware datetime instant."})
        return value.astimezone(UTC)
    except (ValueError, OverflowError) as exc:
        raise ValidationError(
            {field: "The instant is outside the supported representation."}
        ) from exc


def _actor(value):
    value = _identity("actor", value)
    binding = _OWNER_WRITE.get()
    if binding is None or value != binding[5].context.actor_id:
        raise ValidationError("New HR provenance must retain the admitted operation actor.")
    _authority(binding[2], user_ids=[value])
    if not get_user_model().objects.using(_alias()).filter(pk=value).exists():
        raise ValidationError({"actor": "The actor identity does not exist."})
    return value


@_owner_primitive
def _create_attendance(
    *,
    company_id,
    employee_id,
    branch_id,
    timezone_name,
    record_request_key,
    recorded_by_id,
    attendance_id=None,
):
    company_id = _identity("company", company_id)
    employee = _scoped_reference(Employee, employee_id, company_id, "employee")
    if employee is None or employee.status != Employee.Status.ACTIVE:
        raise ValidationError({"employee": "New Attendance requires an active Employee."})
    branch_id = _identity("branch", branch_id, optional=True)
    if employee.branch_id != branch_id:
        raise ValidationError({"branch": "The new Attendance snapshot must match the Employee."})
    _scoped_reference(Branch, branch_id, company_id, "branch", active=True)
    row = Attendance(
        company_id=company_id,
        employee_id=employee.pk,
        branch_id=branch_id,
        timezone=_new_snapshot_zone(company_id, timezone_name),
        record_request_key=_identity("record_request_key", record_request_key),
        recorded_by_id=_actor(recorded_by_id),
    )
    if attendance_id is not None:
        row.pk = _identity("attendance_id", attendance_id)
    return _insert(row)


@_owner_primitive
def _append_attendance_revision(
    *,
    company_id,
    attendance_id,
    expected_revision,
    operation,
    start_at,
    end_at,
    local_start_date,
    local_end_date,
    reason,
    actor_id,
    request_key,
):
    parent = _locked(Attendance, attendance_id, company_id)
    expected = _value("expected_revision", domain.revision, expected_revision, allow_zero=True)
    actor_id = _actor(actor_id)
    request_key = _identity("request_key", request_key)
    reason = _value("reason", domain.text, reason)
    start_at, end_at = _instant("start_at", start_at), _instant("end_at", end_at)
    local_start_date = _value("local_start_date", domain.calendar_date, local_start_date)
    local_end_date = _value("local_end_date", domain.calendar_date, local_end_date)
    if expected == 0:
        if AttendanceRevision.objects.using(_alias()).filter(attendance_id=parent.pk).exists():
            raise ValidationError({"expected_revision": "The Attendance already has history."})
        if (
            operation != AttendanceRevision.Operation.RECORD
            or actor_id != parent.recorded_by_id
            or request_key != parent.record_request_key
        ):
            raise ValidationError(
                "The original revision must retain the Attendance recording identity."
            )
    else:
        # This owner helper certifies EVERY persisted predecessor and historical
        # geometry in the selected chain; latest-only validation is not sufficient.
        from .history import certify_attendance

        latest = certify_attendance(parent)
        if latest.number != expected:
            raise ValidationError({"expected_revision": "The Attendance revision has changed."})
        if not reason:
            raise ValidationError({"reason": "A correction reason is required."})
        if operation == AttendanceRevision.Operation.CORRECT:
            if latest.effect != AttendanceRevision.Effect.ACTIVE_INTERVAL:
                raise ValidationError("Only an active interval can be corrected.")
            if (latest.start_at, latest.end_at) == (start_at, end_at):
                raise ValidationError("A correction must change the effective interval.")
        elif operation == AttendanceRevision.Operation.VOID:
            if latest.effect != AttendanceRevision.Effect.ACTIVE_INTERVAL:
                raise ValidationError("Only an active interval can be voided.")
            if (start_at, end_at, local_start_date, local_end_date) != (
                latest.start_at,
                latest.end_at,
                latest.local_start_date,
                latest.local_end_date,
            ):
                raise ValidationError("A void retains the complete preceding interval and dates.")
        elif operation == AttendanceRevision.Operation.REINSTATE:
            if latest.effect != AttendanceRevision.Effect.VOIDED:
                raise ValidationError("Only a voided interval can be reinstated.")
        else:
            raise ValidationError({"operation": "Unsupported Attendance transition."})
    if start_at >= end_at:
        raise ValidationError({"end_at": "The completed interval must end after its start."})
    try:
        dates = occupied_dates(start_at, end_at, parent.timezone)
    except (ValueError, OverflowError) as exc:
        raise ValidationError({"start_at": str(exc)}) from exc
    if dates != (local_start_date, local_end_date):
        raise ValidationError("Attendance search dates do not match the frozen-zone interval.")
    return _insert(
        AttendanceRevision(
            company_id=parent.company_id,
            employee_id=parent.employee_id,
            attendance_id=parent.pk,
            number=_value("number", domain.next_revision, expected) if expected else 1,
            expected_revision=expected,
            operation=operation,
            effect=AttendanceRevision.Effect.VOIDED
            if operation == AttendanceRevision.Operation.VOID
            else AttendanceRevision.Effect.ACTIVE_INTERVAL,
            start_at=start_at,
            end_at=end_at,
            local_start_date=local_start_date,
            local_end_date=local_end_date,
            reason=reason,
            actor_id=actor_id,
            request_key=request_key,
        )
    )


def _leave_window(start_date, end_date, window_start_at, window_end_at, zone):
    start_date = _value("start_date", domain.calendar_date, start_date)
    end_date = _value("end_date", domain.calendar_date, end_date)
    start_at = _instant("window_start_at", window_start_at)
    end_at = _instant("window_end_at", window_end_at)
    if start_date > end_date or start_at >= end_at:
        raise ValidationError("Leave dates/window are not ordered.")
    try:
        expected_window = leave_window(start_date, end_date, zone)
    except (ValueError, OverflowError) as exc:
        raise ValidationError({"start_date": str(exc)}) from exc
    if (start_at, end_at) != expected_window:
        raise ValidationError(
            "Leave window does not match the exact frozen-zone calendar boundaries."
        )
    return start_date, end_date, start_at, end_at


@_owner_primitive
def _create_leave(
    *,
    company_id,
    employee_id,
    branch_id,
    timezone_name,
    create_request_key,
    requester_id,
    leave_type_id,
    start_date,
    end_date,
    window_start_at,
    window_end_at,
    reason="",
):
    company_id = _identity("company", company_id)
    employee = _scoped_reference(Employee, employee_id, company_id, "employee")
    if employee is None or employee.status != Employee.Status.ACTIVE:
        raise ValidationError({"employee": "New Leave requires an active Employee."})
    branch_id = _identity("branch", branch_id, optional=True)
    if branch_id != employee.branch_id:
        raise ValidationError({"branch": "The new Leave snapshot must match the Employee."})
    _scoped_reference(Branch, branch_id, company_id, "branch", active=True)
    leave_type = _scoped_reference(LeaveType, leave_type_id, company_id, "leave_type", active=True)
    if leave_type is None:
        raise ValidationError({"leave_type": "A LeaveType is required."})
    snapshot_zone = _new_snapshot_zone(company_id, timezone_name)
    start_date, end_date, window_start_at, window_end_at = _leave_window(
        start_date, end_date, window_start_at, window_end_at, snapshot_zone
    )
    return _insert(
        LeaveRequest(
            company_id=company_id,
            employee_id=employee.pk,
            branch_id=branch_id,
            timezone=snapshot_zone,
            create_request_key=_identity("create_request_key", create_request_key),
            requester_id=_actor(requester_id),
            leave_type_id=leave_type.pk,
            start_date=start_date,
            end_date=end_date,
            reason=_value("reason", domain.text, reason),
            window_start_at=window_start_at,
            window_end_at=window_end_at,
        )
    )


@_owner_primitive
def _update_leave(
    *,
    company_id,
    leave_id,
    expected_revision,
    leave_type_id,
    start_date,
    end_date,
    window_start_at,
    window_end_at,
    reason,
):
    row = _locked(LeaveRequest, leave_id, company_id)
    _expected(row, expected_revision)
    if row.status != LeaveRequest.Status.DRAFT:
        raise ValidationError("Only a DRAFT LeaveRequest can be edited.")
    leave_type = _scoped_reference(
        LeaveType, leave_type_id, row.company_id, "leave_type", active=True
    )
    if leave_type is None:
        raise ValidationError({"leave_type": "A LeaveType is required."})
    start_date, end_date, window_start_at, window_end_at = _leave_window(
        start_date, end_date, window_start_at, window_end_at, row.timezone
    )
    values = {
        "leave_type_id": leave_type.pk,
        "start_date": start_date,
        "end_date": end_date,
        "window_start_at": window_start_at,
        "window_end_at": window_end_at,
        "reason": _value("reason", domain.text, reason),
    }
    changed = [field for field, value in values.items() if getattr(row, field) != value]
    for field in changed:
        setattr(row, field, values[field])
    return _write_changed(row, changed) if changed else row


@_owner_primitive
def _submit_leave(*, company_id, leave_id, expected_revision, request_key, actor_id):
    row = _locked(LeaveRequest, leave_id, company_id)
    _expected(row, expected_revision)
    if row.status != LeaveRequest.Status.DRAFT:
        raise ValidationError("Only a DRAFT LeaveRequest can be submitted.")
    employee = _scoped_reference(Employee, row.employee_id, row.company_id, "employee")
    if employee is None:
        raise ValidationError("The Leave Employee is unavailable.")
    row.status = LeaveRequest.Status.SUBMITTED
    row.submit_key = _identity("request_key", request_key)
    row.submitted_by_id = _actor(actor_id)
    row.submitted_at = timezone.now()
    row.submit_from_revision = row.revision
    row.submit_revision = _value("submit_revision", domain.next_revision, row.revision)
    row.beneficiary_user_at_submission_id = employee.user_id
    if employee.user_id is not None:
        _authority(row.company_id, user_ids=[employee.user_id])
    return _write_changed(
        row,
        [
            "status",
            "submit_key",
            "submitted_by_id",
            "submitted_at",
            "submit_from_revision",
            "submit_revision",
            "beneficiary_user_at_submission_id",
        ],
    )


@_owner_primitive
def _decide_leave(
    *,
    company_id,
    leave_id,
    expected_revision,
    request_key,
    actor_id,
    decision,
    reason="",
):
    row = _locked(LeaveRequest, leave_id, company_id)
    _expected(row, expected_revision)
    if row.status != LeaveRequest.Status.SUBMITTED:
        raise ValidationError("Only a SUBMITTED LeaveRequest can be decided.")
    actor_id = _actor(actor_id)
    employee = _scoped_reference(Employee, row.employee_id, row.company_id, "employee")
    if employee is None or actor_id in {
        row.requester_id,
        employee.user_id,
        row.beneficiary_user_at_submission_id,
    }:
        raise ValidationError("The requester or beneficiary association cannot decide this Leave.")
    if decision not in LeaveRequest.Decision.values:
        raise ValidationError({"decision": "Use APPROVED or REJECTED."})
    row.decision_reason = _value(
        "reason", domain.text, reason, required=decision == LeaveRequest.Decision.REJECTED
    )
    row.status = decision
    row.decision = decision
    row.decision_key = _identity("request_key", request_key)
    row.decided_by_id = actor_id
    row.decided_at = timezone.now()
    row.decision_from_revision = row.revision
    row.decision_revision = _value("decision_revision", domain.next_revision, row.revision)
    return _write_changed(
        row,
        [
            "status",
            "decision",
            "decision_key",
            "decided_by_id",
            "decided_at",
            "decision_from_revision",
            "decision_revision",
            "decision_reason",
        ],
    )


@_owner_primitive
def _cancel_leave(*, company_id, leave_id, expected_revision, request_key, actor_id, reason):
    row = _locked(LeaveRequest, leave_id, company_id)
    _expected(row, expected_revision)
    if row.status not in {
        LeaveRequest.Status.DRAFT,
        LeaveRequest.Status.SUBMITTED,
        LeaveRequest.Status.APPROVED,
    }:
        raise ValidationError("This LeaveRequest cannot be cancelled.")
    row.cancel_reason = _value("reason", domain.text, reason, required=True)
    row.status = LeaveRequest.Status.CANCELLED
    row.cancel_key = _identity("request_key", request_key)
    row.cancelled_by_id = _actor(actor_id)
    row.cancelled_at = timezone.now()
    row.cancel_from_revision = row.revision
    row.cancel_revision = _value("cancel_revision", domain.next_revision, row.revision)
    return _write_changed(
        row,
        [
            "status",
            "cancel_key",
            "cancelled_by_id",
            "cancelled_at",
            "cancel_from_revision",
            "cancel_revision",
            "cancel_reason",
        ],
    )
