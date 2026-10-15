"""Private bounded HR projections, input adapters and ordered owner references."""

from dataclasses import dataclass
from types import MappingProxyType
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from businessos.core.access.models import UserCompanyAccess
from businessos.core.audit.services import record_audit_entry
from businessos.core.database import current_database_alias
from businessos.core.organization.models import Branch
from businessos.modules.party.models import Party

from . import domain
from .admission import require_domain_anchors
from .models import Department, Employee, LeaveType


@dataclass(frozen=True, slots=True)
class HRFact:
    """An immutable scalar snapshot, never an ORM instance or deferred relation."""

    id: object
    company_id: object
    kind: str
    values: object

    def __getattr__(self, name):
        try:
            return self.values[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def value(field, normalizer, raw, **kwargs):
    try:
        return normalizer(raw, **kwargs)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError({field: str(exc)}) from exc


def identity(field, raw, *, optional=False):
    return None if optional and raw is None else value(field, domain.identity, raw)


def fact(row, *, related=None, department_visible=False):
    payload = {
        field.attname: getattr(row, field.attname)
        for field in row._meta.concrete_fields
        if field.attname not in {"id", "company_id"}
    }
    if isinstance(row, Employee) and not department_visible:
        payload.pop("department_id", None)
    payload.update(related or {})
    return HRFact(row.pk, row.company_id, row._meta.model_name, MappingProxyType(payload))


def locked(model, context, raw_id):
    row_id = identity("id", raw_id)
    require_domain_anchors([(model._meta.label_lower, row_id)])
    row = (
        model.objects.using(current_database_alias())
        .select_for_update(of=("self",))
        .filter(pk=row_id, company_id=context.company_id)
        .first()
    )
    if row is None:
        raise PermissionDenied("The HR record is unavailable in this scope.")
    return row


def scope(context, branch_id):
    if context.branch_id is not None and branch_id != context.branch_id:
        raise PermissionDenied("The HR record is unavailable in this scope.")


def company_context(context):
    if context.branch_id is not None:
        raise PermissionDenied("This HR operation requires Company-wide context.")


def expected(row, raw_revision):
    revision = value("expected_revision", domain.revision, raw_revision)
    if revision != row.revision:
        raise ValidationError(
            {"expected_revision": "The HR record changed. Reload before editing."}
        )
    return revision


def references(operation, *, department_ids=(), branch_ids=(), party_ids=(), leave_type_ids=()):
    """Acquire complete non-User references in the frozen class/UUID order."""
    result = {}
    for model, identities in (
        (Department, department_ids),
        (Branch, branch_ids),
        (Party, party_ids),
        (LeaveType, leave_type_ids),
    ):
        ids = sorted({identity("reference", key) for key in identities if key is not None})
        require_domain_anchors((model._meta.label_lower, key) for key in ids)
        query = (
            model.objects.using(operation.alias)
            .select_for_update(of=("self",))
            .filter(pk__in=ids, company_id=operation.context.company_id)
            .order_by("pk")
        )
        if model is Party:
            query = query.only("id", "company_id", "party_type", "display_name", "is_active")
        rows = list(query)
        if {row.pk for row in rows} != set(ids):
            raise ValidationError("A related identity is outside the selected Company.")
        operation.declare_anchors((model._meta.label_lower, key) for key in ids)
        result[model] = {row.pk: row for row in rows}
    return result


def person_projection(party):
    return MappingProxyType(
        {
            name: getattr(party, name)
            for name in ("id", "company_id", "party_type", "display_name", "is_active")
        }
    )


def active_person(party):
    if not party.is_active or party.party_type != Party.Type.PERSON:
        raise ValidationError("New HR activity requires an active same-Company PERSON.")


def active_employee(employee):
    if employee.status != Employee.Status.ACTIVE:
        raise ValidationError("New HR activity is unavailable for an ended Employee.")


def association_eligible(user_id, company_id):
    if user_id is None:
        return
    user = get_user_model().objects.using(current_database_alias()).filter(pk=user_id).first()
    if (
        user is None
        or not user.is_active
        or (
            not user.is_superuser
            and not UserCompanyAccess.objects.using(current_database_alias())
            .filter(user_id=user_id, company_id=company_id)
            .exists()
        )
    ):
        raise ValidationError({"user_id": "Select an active Company-eligible User."})


def today(company):
    return timezone.now().astimezone(ZoneInfo(company.timezone)).date()


def employment_dates(employee, first, last):
    if first < employee.joining_date or (
        employee.leaving_date is not None and last > employee.leaving_date
    ):
        raise ValidationError("The requested facts fall outside employment dates.")


def audit(context, row, action, **metadata):
    record_audit_entry(
        context=context,
        action=action,
        object_type=f"hr.{row._meta.object_name}",
        object_id=row.pk,
        metadata=metadata,
    )
