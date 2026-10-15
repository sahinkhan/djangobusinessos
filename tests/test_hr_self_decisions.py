"""Public Leave decision separation is stronger than ordinary/SU RBAC.

A valid retained decision can later acquire a current-beneficiary conflict.
Requester and frozen-beneficiary identities are immutable: no valid historical
self-decision receipt can first be created through the supported public API.
Their fresh attempts are covered independently instead of fabricating receipts.
"""

from datetime import date
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from businessos.core.access.models import UserCompanyAccess, UserRoleAssignment
from businessos.core.access.policies import require_permission
from businessos.core.audit.models import AuditEntry
from businessos.core.common.context import BusinessContext
from businessos.core.database import current_database_alias
from businessos.modules.hr import selectors, services
from businessos.modules.hr.models import Employee, LeaveRequest
from tests import test_hr_services as _fixtures

hr_context = _fixtures.hr_context
hr_person = _fixtures.hr_person
pytestmark = pytest.mark.django_db(transaction=True)


def _decision_actor(context, *, superuser):
    alias = current_database_alias()
    user = (
        get_user_model()
        .objects.db_manager(alias)
        .create_user("hr-self-decision@example.test", "synthetic-only", is_superuser=superuser)
    )
    UserCompanyAccess.objects.using(alias).create(user=user, company_id=context.company_id)
    role_id = UserRoleAssignment.objects.using(alias).get(user_id=context.actor_id).role_id
    UserRoleAssignment.objects.using(alias).create(
        user=user, company_id=context.company_id, role_id=role_id
    )
    return BusinessContext(actor_id=user.pk, company_id=context.company_id)


def _draft(context, person, *, user_id=None):
    employee = services.create_employee(
        context,
        party_id=person.pk,
        employee_number="SELF-DECISION",
        joining_date=date(2020, 1, 1),
        user_id=user_id,
    )
    leave_type = services.create_leave_type(context, code="SELF", name="Synthetic decision leave")
    draft = services.create_leave(
        context,
        employee_id=employee.id,
        create_request_key=uuid4(),
        leave_type_id=leave_type.id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
    )
    services.submit_leave(
        context, leave_id=draft.leave.id, expected_revision=1, request_key=uuid4()
    )
    return employee, draft.leave.id


def _native():
    alias = current_database_alias()
    return tuple(
        tuple(model.objects.using(alias).order_by("pk").values())
        for model in (Employee, LeaveRequest, AuditEntry)
    )


def _rbac_is_valid(context):
    for code in ("hr.leave.approve", "hr.leave.view", "hr.employee.view"):
        assert require_permission(context, code) == context


@pytest.mark.parametrize("decision", ["APPROVED", "REJECTED"])
@pytest.mark.parametrize("superuser", [False, True], ids=["ordinary", "superuser"])
@pytest.mark.parametrize("identity", ["requester", "current_beneficiary", "frozen_beneficiary"])
def test_public_decision_rejects_each_self_identity_despite_valid_compound_rbac(
    hr_context, hr_person, decision, superuser, identity
):
    alias = current_database_alias()
    actor = (
        hr_context if identity == "requester" else _decision_actor(hr_context, superuser=superuser)
    )
    if identity == "requester":
        get_user_model().objects.using(alias).filter(pk=actor.actor_id).update(
            is_superuser=superuser
        )
    employee, leave_id = _draft(
        hr_context,
        hr_person,
        user_id=actor.actor_id if identity == "frozen_beneficiary" else None,
    )
    if identity in {"current_beneficiary", "frozen_beneficiary"}:
        services.update_employee(
            hr_context,
            employee_id=employee.id,
            expected_revision=1,
            user_id=actor.actor_id if identity == "current_beneficiary" else None,
        )
    row = LeaveRequest.objects.using(alias).get(pk=leave_id)
    current = Employee.objects.using(alias).get(pk=employee.id)
    assert (row.requester_id == actor.actor_id) == (identity == "requester")
    assert (current.user_id == actor.actor_id) == (identity == "current_beneficiary")
    assert (row.beneficiary_user_at_submission_id == actor.actor_id) == (
        identity == "frozen_beneficiary"
    )
    _rbac_is_valid(actor)
    before = _native()
    with pytest.raises(ValidationError, match="Requester|beneficiary"):
        services.decide_leave(
            actor,
            leave_id=leave_id,
            expected_revision=2,
            request_key=uuid4(),
            decision=decision,
            reason="Synthetic separation test",
        )
    assert _native() == before
    assert row.status == "SUBMITTED" and row.decision_key is None


@pytest.mark.parametrize("decision", ["APPROVED", "REJECTED"])
@pytest.mark.parametrize("superuser", [False, True], ids=["ordinary", "superuser"])
def test_matching_retained_decision_retry_rechecks_new_current_beneficiary_conflict(
    hr_context, hr_person, decision, superuser
):
    actor = _decision_actor(hr_context, superuser=superuser)
    employee, leave_id = _draft(hr_context, hr_person)
    key = uuid4()
    inputs = dict(
        leave_id=leave_id,
        expected_revision=2,
        request_key=key,
        decision=decision,
        reason="Retained decision reason",
    )
    original = services.decide_leave(actor, **inputs)
    retry = services.decide_leave(actor, **inputs)
    assert retry.historical_retry and retry.receipt_revision == original.receipt_revision == 3
    services.update_employee(
        hr_context, employee_id=employee.id, expected_revision=1, user_id=actor.actor_id
    )
    # A later link does not falsify a previously legal native historical event.
    assert selectors.leave_detail(hr_context, leave_id).decision == decision
    _rbac_is_valid(actor)
    before = _native()
    with pytest.raises(ValidationError, match="Requester|beneficiary"):
        services.decide_leave(actor, **inputs)
    assert _native() == before
    stored = LeaveRequest.objects.using(current_database_alias()).get(pk=leave_id)
    assert stored.decision_key == key and stored.decided_by_id == actor.actor_id
    assert stored.status == decision and stored.revision == 3
