"""Actual public HR nesting may never introduce an uncovered domain lock."""

import inspect
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext

from businessos.core.access.models import Permission, Role, RolePermission, UserRoleAssignment
from businessos.core.audit.models import AuditEntry
from businessos.core.audit.services import record_audit_entry
from businessos.core.common.context import BusinessContext
from businessos.modules.hr import selectors, services
from businessos.modules.hr.admission import AdmissionError, hr_operation
from businessos.modules.hr.models import Department

pytestmark = pytest.mark.django_db(transaction=True)
VIEW = "hr.department.view"
MANAGE = "hr.department.manage"


@pytest.fixture
def nested_world(company, operator):
    role = Role.objects.create(company=company, code="NESTED-HR", name="Synthetic HR nesting")
    for code in (VIEW, MANAGE):
        permission, _ = Permission.objects.get_or_create(code=code, defaults={"name": code})
        RolePermission.objects.create(role=role, permission=permission)
    UserRoleAssignment.objects.create(company=company, user=operator, role=role)
    context = BusinessContext(actor_id=operator.pk, company_id=company.pk)
    covered = services.create_department(context, code="COVERED", name="Covered")
    uncovered = services.create_department(context, code="UNCOVERED", name="Uncovered")
    return context, covered, uncovered


def _prelock(operation, target):
    return (
        Department.objects.using(operation.alias)
        .select_for_update()
        .get(pk=target.id, company_id=operation.context.company_id)
    )


@pytest.mark.parametrize("public_call", ["mutation", "selector"])
def test_nested_public_uncovered_target_rejects_before_its_domain_sql(nested_world, public_call):
    context, covered, uncovered = nested_world
    statements = []

    def capture(execute, sql, params, many, execution_context):
        statements.append(sql)
        return execute(sql, params, many, execution_context)

    with pytest.raises(AdmissionError):
        with hr_operation(
            context, [VIEW, MANAGE], anchors=[("hr.department", covered.id)]
        ) as outer:
            _prelock(outer, covered)
            outer.authorize()
            with connection.execute_wrapper(capture):
                if public_call == "mutation":
                    services.update_department(
                        context,
                        department_id=uncovered.id,
                        expected_revision=1,
                        name="Must not reach persistence",
                        is_active=True,
                    )
                else:
                    selectors.department_detail(context, uncovered.id)
    # Entry may reauthorize its already-covered User/Role/Permission set. It
    # must not issue even a functional SQLite read of the unknown Department,
    # and on PostgreSQL must not attempt the corresponding FOR UPDATE lock.
    assert not any('"hr_department"' in sql for sql in statements)
    assert Department.objects.get(pk=uncovered.id).name == "Uncovered"
    assert not AuditEntry.objects.filter(action="hr.department.updated").exists()


def test_public_covered_nested_update_and_noop_share_one_outer_transaction(nested_world):
    context, covered, _ = nested_world
    with hr_operation(context, [VIEW, MANAGE], anchors=[("hr.department", covered.id)]) as outer:
        _prelock(outer, covered)
        outer.authorize()
        original_outer = connection.atomic_blocks[0]
        original_savepoints = tuple(connection.savepoint_ids)
        atomic_callers = []
        original_atomic = transaction.atomic

        def traced_atomic(*args, **kwargs):
            caller = inspect.currentframe().f_back
            atomic_callers.append((caller.f_code.co_filename, caller.f_code.co_name))
            return original_atomic(*args, **kwargs)

        with (
            CaptureQueriesContext(connection) as captured,
            patch("django.db.transaction.atomic", new=traced_atomic),
            patch(
                "businessos.modules.hr.admission.business_atomic_context",
                side_effect=AssertionError("Nested HR entry must reuse its outer transaction"),
            ),
        ):
            changed = services.update_department(
                context,
                department_id=covered.id,
                expected_revision=1,
                name="Updated",
                is_active=True,
            )
            same = services.update_department(
                context,
                department_id=covered.id,
                expected_revision=2,
                name="Updated",
                is_active=True,
            )
        assert changed.revision == same.revision == 2
        assert connection.atomic_blocks[0] is original_outer
        assert tuple(connection.savepoint_ids) == original_savepoints
        # Django Q.check/full_clean uses same-alias read-validation savepoints.
        # Those are not independent HR operation transactions or commits.
        assert atomic_callers and all(
            name == "check" and path.endswith("query_utils.py") for path, name in atomic_callers
        )
        assert not any(
            query["sql"].strip().upper() in {"BEGIN", "COMMIT", "ROLLBACK"} for query in captured
        )
    assert Department.objects.get(pk=covered.id).revision == 2
    assert AuditEntry.objects.filter(action="hr.department.updated").count() == 1


def test_catching_uncovered_public_nested_error_cannot_commit_prior_outer_evidence(nested_world):
    context, covered, uncovered = nested_world
    marker = uuid4()
    with pytest.raises(AdmissionError):
        with hr_operation(
            context, [VIEW, MANAGE], anchors=[("hr.department", covered.id)]
        ) as outer:
            _prelock(outer, covered)
            outer.authorize()
            record_audit_entry(
                context=context,
                action="hr.department.updated",
                object_type="hr.Department",
                object_id=marker,
            )
            try:
                services.update_department(
                    context,
                    department_id=uncovered.id,
                    expected_revision=1,
                    name="Uncovered",
                    is_active=True,
                )
            except AdmissionError:
                pass
    assert not AuditEntry.objects.filter(object_id=str(marker)).exists()
    assert Department.objects.get(pk=covered.id).revision == 1


def test_caught_nested_audit_failure_rolls_back_all_outer_updates(nested_world):
    context, covered, _ = nested_world
    with pytest.raises(RuntimeError, match="Synthetic nested Audit failure"):
        with hr_operation(
            context, [VIEW, MANAGE], anchors=[("hr.department", covered.id)]
        ) as outer:
            _prelock(outer, covered)
            outer.authorize()
            services.update_department(
                context, department_id=covered.id, expected_revision=1, name="First", is_active=True
            )
            try:
                with patch(
                    "businessos.modules.hr.services.audit",
                    side_effect=RuntimeError("Synthetic nested Audit failure"),
                ):
                    services.update_department(
                        context,
                        department_id=covered.id,
                        expected_revision=2,
                        name="Must roll back",
                        is_active=True,
                    )
            except RuntimeError:
                pass
    row = Department.objects.get(pk=covered.id)
    assert row.name == "Covered" and row.revision == 1
    assert not AuditEntry.objects.filter(action="hr.department.updated").exists()
