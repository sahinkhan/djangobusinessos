"""HR-local, outer-transaction-bound authority admission (ADR 0018 section 8).

Domain/reference locks remain explicit in HR services.  This adapter is not an
authorization cache: every successful public return uses unchanged Core guards.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from logging import getLogger
from math import ceil
from time import monotonic
from uuid import UUID

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError, connections, transaction

from businessos.core.access.models import Permission, Role, UserRoleAssignment
from businessos.core.access.permissions import validate_permission_code
from businessos.core.access.policies import require_final_permission, require_permission
from businessos.core.database import business_atomic_context, current_database_alias
from businessos.core.organization.models import Company

from .civil_time import ResourceBudgetExceeded

AUTHORITY_WORK_SECONDS = 2.0
PRE_ADMISSION_WORK_SECONDS = 10.0
PRE_ADMISSION_LOCK_MILLISECONDS = 2_000
PRE_ADMISSION_STATEMENT_MILLISECONDS = 5_000
IDLE_TRANSACTION_MILLISECONDS = 5_000
AUTHORITY_CLASS_LIMIT = 1_000
AUTHORITY_TOTAL_LIMIT = 3_000

_CURRENT = ContextVar("hr_authority_admission", default=None)
_LOGGER = getLogger(__name__)
_EXPECTED_RELATIONS = (
    ("public", "identity_user", "r"),
    ("public", "access_role", "r"),
    ("public", "access_permission", "r"),
)
# Fixed canonical deployment identities, not discovered/approved from live rows.
# Early owner/HR reads must not reach a shadow or RLS-filtered partial world.
_EXPECTED_SOURCE_RELATIONS = (
    ("organization.company", "organization_company"),
    ("organization.branch", "organization_branch"),
    ("party.party", "party_party"),
    ("identity.user", "identity_user"),
    ("access.role", "access_role"),
    ("access.permission", "access_permission"),
    ("access.usercompanyaccess", "access_usercompanyaccess"),
    ("access.userbranchaccess", "access_userbranchaccess"),
    ("access.userroleassignment", "access_userroleassignment"),
    ("access.rolepermission", "access_rolepermission"),
    ("hr.department", "hr_department"),
    ("hr.employee", "hr_employee"),
    ("hr.attendance", "hr_attendance"),
    ("hr.attendancerevision", "hr_attendancerevision"),
    ("hr.leavetype", "hr_leavetype"),
    ("hr.leaverequest", "hr_leaverequest"),
)
_DOMAIN_ORDER = {
    label: index
    for index, label in enumerate(
        (
            "hr.employee",
            "hr.department",
            "organization.branch",
            "party.party",
            "hr.leavetype",
            "hr.attendance",
            "hr.leaverequest",
        )
    )
}


class AdmissionError(RuntimeError):
    """Unsupported transaction, missing evidence, or changed lock coverage."""


class AuthorityBusy(RuntimeError):
    """Retryable authority-lock contention, reported ONLY after outer rollback."""


def _sqlstate(error):
    while error is not None:
        code = getattr(error, "sqlstate", None) or getattr(error, "pgcode", None)
        if code:
            return code
        error = error.__cause__
    return None


def _record_failure(state, category, *, sqlstate=None):
    # Operational evidence only, never a success Audit or copied HR/Party PII.
    _LOGGER.warning(
        "HR operation refused: %s on alias %s",
        category,
        state.alias,
        extra={
            "hr_error_category": category,
            "hr_alias": state.alias,
            "hr_permissions": state.permissions,
            "hr_user_count": len(state.user_ids),
            "hr_role_count": len(state.role_ids),
            "hr_permission_count": len(state.permission_ids),
            "hr_domain_anchor_count": len(state.anchors),
            "hr_sqlstate": sqlstate,
        },
    )


def _poison(state, error):
    """An admitted nested refusal cannot be caught to commit prior outer work."""
    state.poisoned = error
    if state.connection.in_atomic_block:
        transaction.set_rollback(True, using=state.alias)


def _uuid_set(values):
    values = frozenset(values)
    if any(not isinstance(value, UUID) for value in values):
        raise AdmissionError("Authority identities must be validated UUIDs.")
    if len(values) > AUTHORITY_CLASS_LIMIT:
        raise ResourceBudgetExceeded("HR authority User set exceeds its resource budget.")
    return values


def _anchor_set(anchors):
    result = set()
    for anchor in anchors:
        if (
            not isinstance(anchor, tuple)
            or len(anchor) != 2
            or not isinstance(anchor[0], str)
            or not isinstance(anchor[1], UUID)
        ):
            raise AdmissionError("Domain anchors require (model label, UUID) identities.")
        result.add(anchor)
    return frozenset(result)


def _permission_set(permissions):
    result = tuple(sorted(set(permissions)))
    if not result:
        raise AdmissionError("HR admission requires explicit compound permissions.")
    for code in result:
        validate_permission_code(code)
        if not code.startswith("hr."):
            raise AdmissionError("HR admission does not authorize cross-owner operations.")
    return result


def _outer_transaction_present(connection):
    # Do not open a connection / issue SQL just to detect an unsupported caller.
    if connection.in_atomic_block:
        return True
    raw = connection.connection
    if raw is None:
        return False
    if not connection.get_autocommit():
        return True
    if connection.vendor == "postgresql":
        return getattr(raw.info.transaction_status, "name", "IDLE") != "IDLE"
    return bool(getattr(raw, "in_transaction", False))


@dataclass
class HRAdmission:
    """Private transaction capability; callers cannot supply an admission bypass."""

    context: object
    permissions: tuple
    alias: str
    connection: object
    anchors: frozenset = field(default_factory=frozenset)
    declared_users: frozenset = field(default_factory=frozenset)
    company: object = None
    admitted: bool = False
    outer: object = None
    raw_connection: object = None
    savepoints: tuple = ()
    started_at: float = field(default_factory=monotonic)
    authority_started_at: float | None = None
    acquiring_authority: bool = False
    authority_conflict: bool = False
    poisoned: Exception | None = None
    user_ids: frozenset = field(default_factory=frozenset)
    role_ids: frozenset = field(default_factory=frozenset)
    permission_ids: frozenset = field(default_factory=frozenset)
    superuser: bool = False
    relations: tuple = ()
    acquired_anchors: frozenset = field(default_factory=frozenset)
    reserved_attendance_ids: frozenset = field(default_factory=frozenset)
    pending_attendance_ids: set = field(default_factory=set)
    finished: bool = False

    def _check_transaction(self):
        if (
            self.finished
            or current_database_alias() != self.alias
            or connections[self.alias] is not self.connection
            or self.connection.connection is not self.raw_connection
            or not self.connection.in_atomic_block
            or self.connection.atomic_blocks[0] is not self.outer
        ):
            raise AdmissionError("HR admission no longer belongs to this outer transaction.")

    def checkpoint(self):
        self._check_transaction()
        if self.poisoned is not None:
            raise self.poisoned
        if self.connection.needs_rollback:
            raise AdmissionError("The HR outer transaction requires rollback.")
        start = (
            self.authority_started_at if self.authority_started_at is not None else self.started_at
        )
        limit = (
            AUTHORITY_WORK_SECONDS
            if self.authority_started_at is not None
            else PRE_ADMISSION_WORK_SECONDS
        )
        remaining = limit - (monotonic() - start)
        if remaining <= 0:
            raise ResourceBudgetExceeded("HR cumulative operation resource budget exhausted.")
        return remaining

    def declare_anchors(self, anchors):
        """Finish bounded authoritative discovery before authority admission."""
        self.checkpoint()
        requested = _anchor_set(anchors)
        if self.admitted or self.authority_started_at is not None:
            if not requested <= self.anchors:
                self._refuse("Domain anchors cannot expand after authority admission.")
            return
        self.anchors = self.anchors | requested

    def _check_domain_boundary(self):
        self.checkpoint()
        if tuple(self.connection.savepoint_ids) != self.savepoints:
            self._refuse("HR acquired-lock evidence cannot cross an unadmitted savepoint.")

    def lock_rows(self, model, identities):
        """Acquire actual scoped locks, never infer protection from declarations.

        Every supported HR domain lock goes through this private adapter. The
        acquired set is populated only AFTER successful selected-transaction SQL.
        After authority starts, rereads use already-held locks and cannot issue
        a new blocking FOR UPDATE. New inserts are recorded separately.
        """
        self._check_domain_boundary()
        label = model._meta.label_lower
        if label not in _DOMAIN_ORDER:
            self._refuse("Unsupported HR domain lock owner.")
        ids = _uuid_set(identities)
        requested = frozenset((label, key) for key in ids)
        self.declare_anchors(requested)
        missing = requested - self.acquired_anchors
        if self.admitted or self.authority_started_at is not None:
            if missing:
                self._refuse("Nested domain anchors are unacquired before authority admission.")
        elif missing:
            # Existing protected identities may be reread after later classes;
            # a newly discovered earlier class cannot be locked in reverse order.
            held_classes = [_DOMAIN_ORDER[name] for name, _ in self.acquired_anchors]
            if held_classes and _DOMAIN_ORDER[label] < max(held_classes):
                self._refuse("HR domain locks cannot acquire an earlier class after later locks.")
        query = (
            model.objects.using(self.alias)
            .filter(company_id=self.context.company_id, pk__in=ids)
            .order_by("pk")
        )
        if label == "party.party":
            query = query.only("id", "company_id", "party_type", "display_name", "is_active")
        if missing:
            query = query.select_for_update(of=("self",))
        rows = list(query)
        if {row.pk for row in rows} != set(ids):
            error = ValidationError("The HR domain lock identity coverage is incomplete.")
            _poison(self, error)
            raise error
        self.acquired_anchors |= requested
        return rows

    def reserve_attendance(self, identity):
        """Reserve a genuinely new identity before authority under the Company mutex."""
        self._check_domain_boundary()
        if self.admitted or self.authority_started_at is not None:
            self._refuse("New Attendance reservation must precede authority admission.")
        identity = next(iter(_uuid_set([identity])))
        if apps.get_model("hr.attendance").objects.using(self.alias).filter(pk=identity).exists():
            self._refuse("A new Attendance reservation cannot name an existing record.")
        self.declare_anchors([("hr.attendance", identity)])
        self.reserved_attendance_ids |= frozenset([identity])

    def register_created_row(self, row):
        self._check_domain_boundary()
        from .persistence import _owns_insert

        if (
            not self.admitted
            or not _owns_insert(self, row=row)
            or row._state.adding
            or row._state.db != self.alias
            or row.company_id != self.context.company_id
            or row._meta.label_lower not in {*_DOMAIN_ORDER, "hr.attendancerevision"}
        ):
            self._refuse(
                "New HR row protection requires this admitted transaction's scoped insert."
            )
        if row._meta.label_lower != "hr.attendancerevision":
            anchor = (row._meta.label_lower, row.pk)
            # An insertion owns its row lock. It cannot pretend an existing
            # declared-but-unheld row was acquired.
            self.anchors |= frozenset([anchor])
            self.acquired_anchors |= frozenset([anchor])

    def register_attendance_creation(self, parent):
        self.checkpoint()
        from .persistence import _owns_insert

        if not _owns_insert(self, row=parent) or parent.pk not in self.reserved_attendance_ids:
            self._refuse("Attendance insertion requires a verified new identity reservation.")
        self.pending_attendance_ids.add(parent.pk)

    def complete_attendance_creation(self, parent_id):
        self.checkpoint()
        from .persistence import _owns_insert

        if (
            not _owns_insert(self, parent_id=parent_id)
            or parent_id not in self.pending_attendance_ids
        ):
            self._refuse("Attendance initial revision has no pending parent insertion.")
        self.pending_attendance_ids.remove(parent_id)

    def declare_permissions(self, permissions):
        """Add a compound discovered from locked state, never after admission."""
        self.checkpoint()
        requested = _permission_set(permissions)
        if self.admitted or self.authority_started_at is not None:
            if not set(requested) <= set(self.permissions):
                self._refuse("Compound permissions cannot expand after admission.")
            return
        for code in requested:
            if code not in self.permissions:
                require_permission(self.context, code)
        self.permissions = tuple(sorted(set(self.permissions) | set(requested)))

    def _refuse(self, message):
        error = AdmissionError(message)
        _poison(self, error)
        raise error

    def _execute(self, execute, sql, params, many, context):
        remaining = self.checkpoint()
        try:
            if self.connection.vendor == "postgresql":
                milliseconds = max(1, ceil(remaining * 1_000))
                statement = min(milliseconds, PRE_ADMISSION_STATEMENT_MILLISECONDS)
                lock = min(milliseconds, PRE_ADMISSION_LOCK_MILLISECONDS)
                # Calling the provided execute directly avoids recursive wrappers.
                # SET LOCAL automatically restores the original settings on outcome.
                execute(
                    "SELECT pg_catalog.set_config('statement_timeout', %s, true), "
                    "pg_catalog.set_config('lock_timeout', %s, true), "
                    "pg_catalog.set_config('idle_in_transaction_session_timeout', %s, true)",
                    [f"{statement}ms", f"{lock}ms", f"{IDLE_TRANSACTION_MILLISECONDS}ms"],
                    False,
                    context,
                )
            result = execute(sql, params, many, context)
        except DatabaseError as exc:
            if self.acquiring_authority and _sqlstate(exc) == "55P03":
                self.authority_conflict = True
            # Django Q.check() deliberately swallows DatabaseError after an
            # internal savepoint. That must never clear this operation's failure
            # or turn missing constraint evidence into a successful HR commit.
            # There is no generic unique-collision-to-receipt recovery path.
            _poison(self, exc)
            raise
        self.checkpoint()
        return result

    def _verified_relations(self, *, source=False):
        if source:
            models = tuple(apps.get_model(label) for label, _ in _EXPECTED_SOURCE_RELATIONS)
            expected = tuple(("public", name, "r") for _, name in _EXPECTED_SOURCE_RELATIONS)
        else:
            models = (get_user_model(), Role, Permission)
            expected = _EXPECTED_RELATIONS
        resolved = []
        with self.connection.cursor() as cursor:
            for model, (schema, name, kind) in zip(models, expected, strict=True):
                if model._meta.db_table != name:
                    raise AdmissionError("Installed HR source relation metadata is unsupported.")
                cursor.execute(
                    "SELECT c.oid, n.nspname, c.relname, c.relkind, "
                    "pg_catalog.to_regclass(%s)::oid, c.relrowsecurity, c.relforcerowsecurity, "
                    "EXISTS(SELECT 1 FROM pg_catalog.pg_policy p WHERE p.polrelid = c.oid) "
                    "FROM pg_catalog.pg_class c "
                    "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = %s AND c.relname = %s",
                    [name, schema, name],
                )
                rows = cursor.fetchall()
                if len(rows) != 1:
                    raise AdmissionError("Canonical HR source relation is missing or ambiguous.")
                oid, actual_schema, actual_name, actual_kind, effective, rls, forced, policy = rows[
                    0
                ]
                if (
                    (actual_schema, actual_name, actual_kind) != (schema, name, kind)
                    or oid != effective
                    or rls
                    or forced
                    or policy
                ):
                    raise AdmissionError(
                        "Unsupported authority relation identity/resolution/policy."
                    )
                resolved.append((oid, schema, name))
        return tuple(resolved)

    def _share_rows(self, model, identities):
        identities = frozenset(identities)
        if len(identities) > AUTHORITY_CLASS_LIMIT:
            raise ResourceBudgetExceeded("HR authority class exceeds its resource budget.")
        if not identities:
            return
        quote = self.connection.ops.quote_name
        lock = " FOR SHARE NOWAIT" if self.connection.vendor == "postgresql" else ""
        table = quote(model._meta.db_table)
        if self.connection.vendor == "postgresql":
            table = f"{quote('public')}.{table}"
        pk = model._meta.pk
        placeholders = ", ".join(["%s"] * len(identities))
        with self.connection.cursor() as cursor:
            cursor.execute(
                f"SELECT {quote(pk.column)} FROM {table} "
                f"WHERE {quote(pk.column)} IN ({placeholders}) "
                f"ORDER BY {quote(pk.column)}{lock}",
                [pk.get_db_prep_value(value, self.connection) for value in sorted(identities)],
            )
            actual = frozenset(UUID(str(row[0])) for row in cursor.fetchall())
        if actual != identities:
            raise AdmissionError("Complete HR authority identity coverage could not be certified.")

    def _admit_source_relations(self):
        """Pin approved identities before unqualified domain/owner ORM reads.

        ACCESS SHARE is the compatible mode ordinary SELECTs themselves need;
        it prevents replacement DDL, not ordinary ROW EXCLUSIVE business DML.
        The three ROW SHARE authority admissions still occur only after domain
        locks.  An early relation conflict has the same whole-rollback outcome.
        """
        self.acquiring_authority = True
        try:
            identities = self._verified_relations(source=True)
            quote = self.connection.ops.quote_name
            with self.connection.cursor() as cursor:
                for _, schema, name in identities:
                    cursor.execute(
                        f"LOCK TABLE {quote(schema)}.{quote(name)} IN ACCESS SHARE MODE NOWAIT"
                    )
            if self._verified_relations(source=True) != identities:
                raise AdmissionError("HR source identities changed during relation admission.")
        finally:
            self.acquiring_authority = False

    def _roles(self):
        rows = list(
            UserRoleAssignment.objects.using(self.alias)
            .filter(
                user_id=self.context.actor_id,
                company_id=self.context.company_id,
                role__company_id=self.context.company_id,
            )
            .order_by("role_id")
            .values_list("role_id", flat=True)
            .distinct()[: AUTHORITY_CLASS_LIMIT + 1]
        )
        if len(rows) > AUTHORITY_CLASS_LIMIT:
            raise ResourceBudgetExceeded("HR complete Role set exceeds its resource budget.")
        return frozenset(rows)

    def _permissions(self):
        query = Permission.objects.using(self.alias)
        if not self.superuser:
            query = query.filter(role_links__role_id__in=self.role_ids)
        rows = list(
            query.order_by("id")
            .values_list("id", flat=True)
            .distinct()[: AUTHORITY_CLASS_LIMIT + 1]
        )
        if len(rows) > AUTHORITY_CLASS_LIMIT:
            raise ResourceBudgetExceeded("HR complete Permission set exceeds its resource budget.")
        return frozenset(rows)

    def _recheck_sets(self):
        if not self.superuser and self._roles() != self.role_ids:
            raise AdmissionError("HR assigned Role membership changed during admission.")
        if self._permissions() != self.permission_ids:
            raise AdmissionError("HR reachable Permission membership changed during admission.")
        actor = get_user_model().objects.using(self.alias).filter(pk=self.context.actor_id).first()
        if actor is None or not actor.is_active or actor.is_superuser != self.superuser:
            raise PermissionDenied("The HR actor changed or is inactive.")

    def authorize(self, *, user_ids=()):
        """Any failed admission poisons the outer unit, even if caller catches it."""
        try:
            return self._authorize(user_ids=user_ids)
        except Exception as exc:
            _poison(self, exc)
            raise

    def _authorize(self, *, user_ids):
        """Freeze the complete discovered union, then run every native final guard."""
        self._check_domain_boundary()
        protected = self.acquired_anchors | frozenset(
            ("hr.attendance", key) for key in self.reserved_attendance_ids
        )
        if not self.anchors <= protected:
            self._refuse("Declared HR domain anchors remain unacquired before authority admission.")
        users = _uuid_set((*user_ids, *self.declared_users, self.context.actor_id))
        self.checkpoint()
        if self.admitted:
            if not users <= self.user_ids:
                self._refuse("A later operation introduced an uncovered authority User.")
            self._final_guards(self.context, self.permissions)
            return
        self.authority_started_at = monotonic()
        self.acquiring_authority = True
        try:
            if self.connection.vendor == "postgresql":
                self.relations = self._verified_relations()
                quote = self.connection.ops.quote_name
                with self.connection.cursor() as cursor:
                    for _, schema, name in self.relations:
                        cursor.execute(
                            f"LOCK TABLE {quote(schema)}.{quote(name)} IN ROW SHARE MODE NOWAIT"
                        )
                if self._verified_relations() != self.relations:
                    raise AdmissionError("Authority identities changed during relation admission.")
            self._share_rows(get_user_model(), users)
            self.user_ids = users
            actor = (
                get_user_model().objects.using(self.alias).filter(pk=self.context.actor_id).first()
            )
            if actor is None or not actor.is_active:
                raise PermissionDenied("The HR actor does not exist or is inactive.")
            self.superuser = actor.is_superuser
            if self.superuser:
                if self.connection.vendor == "postgresql":
                    quote = self.connection.ops.quote_name
                    with self.connection.cursor() as cursor:
                        cursor.execute(
                            f"LOCK TABLE {quote('public')}.{quote('access_permission')} "
                            "IN SHARE MODE NOWAIT"
                        )
            else:
                roles = self._roles()
                self._share_rows(Role, roles)
                self.role_ids = roles
            permissions = self._permissions()
            total = len(users) + len(self.role_ids) + len(permissions)
            if total > AUTHORITY_TOTAL_LIMIT:
                raise ResourceBudgetExceeded("HR aggregate authority resource budget exceeded.")
            self._share_rows(Permission, permissions)
            self.permission_ids = permissions
            self._recheck_sets()
        finally:
            self.acquiring_authority = False
        self.admitted = True
        self._final_guards(self.context, self.permissions)

    def _final_guards(self, context, permissions):
        self.checkpoint()
        self._recheck_sets()
        for code in permissions:
            require_final_permission(context, code)
        self.checkpoint()


@contextmanager
def hr_operation(context, permissions, *, anchors=(), user_ids=()):
    """Own one operation transaction; unknown outer transactions fail before SQL.

    An explicitly nested call is admitted only after its parent's complete union
    is frozen, and cannot add a permission, domain anchor, User or savepoint.
    SQLSTATE 55P03 is translated outside the rolled-back outer boundary only.
    """
    alias = current_database_alias()
    connection = connections[alias]
    parent = _CURRENT.get()
    try:
        permissions = _permission_set(permissions)
        anchors = _anchor_set(anchors)
        users = _uuid_set((*user_ids, context.actor_id))
    except Exception as exc:
        if parent is not None:
            _poison(parent, exc)
        raise
    if parent is not None:
        try:
            parent._check_transaction()
            if (
                not parent.admitted
                or parent.alias != alias
                or parent.connection is not connection
                or parent.context.company_id != context.company_id
                or parent.context.actor_id != context.actor_id
                or context.warehouse_id is not None
                or not set(permissions) <= set(parent.permissions)
                or not anchors <= parent.acquired_anchors
                or not users <= parent.user_ids
                or tuple(connection.savepoint_ids) != parent.savepoints
            ):
                raise AdmissionError(
                    "HR nested work is outside its predeclared complete admission."
                )
            parent._final_guards(context, permissions)
            yield parent
            parent.checkpoint()
        except Exception as exc:
            _poison(parent, exc)
            raise
        return
    if _outer_transaction_present(connection):
        raise AdmissionError("HR operations reject unknown or prelocked outer transactions.")
    if context.warehouse_id is not None:
        raise PermissionDenied("HR operations do not accept Warehouse context.")
    state = HRAdmission(context, permissions, alias, connection, anchors, users)
    try:
        with business_atomic_context(using=alias):
            state.raw_connection = connection.connection
            state.outer = connection.atomic_blocks[0]
            state.savepoints = tuple(connection.savepoint_ids)
            token = _CURRENT.set(state)
            try:
                with connection.execute_wrapper(state._execute):
                    if connection.vendor == "postgresql":
                        with connection.cursor() as cursor:
                            cursor.execute("SHOW transaction_isolation")
                            if cursor.fetchone()[0] != "read committed":
                                raise AdmissionError("HR requires PostgreSQL READ COMMITTED.")
                        state._admit_source_relations()
                    state.company = (
                        Company.objects.using(alias)
                        .select_for_update(of=("self",))
                        .filter(pk=context.company_id, is_active=True)
                        .first()
                    )
                    if state.company is None:
                        raise PermissionDenied(
                            "The selected Company does not exist or is inactive."
                        )
                    for code in permissions:
                        require_permission(context, code)
                    yield state
                    if not state.admitted:
                        raise AdmissionError("HR cannot succeed without complete final admission.")
                    if state.pending_attendance_ids:
                        state._refuse("An Attendance insertion has no complete initial revision.")
                    state.checkpoint()
            finally:
                _CURRENT.reset(token)
                state.finished = True
                state.acquired_anchors = frozenset()
                state.reserved_attendance_ids = frozenset()
                state.pending_attendance_ids.clear()
                state.user_ids = frozenset()
                state.role_ids = frozenset()
                state.permission_ids = frozenset()
    except DatabaseError as exc:
        if state.authority_conflict and _sqlstate(exc) == "55P03":
            _record_failure(state, "AuthorityBusy", sqlstate="55P03")
            raise AuthorityBusy(
                "HR authority is busy; the entire operation was rolled back."
            ) from exc
        if _sqlstate(exc) in {"55P03", "57014"}:
            _record_failure(state, "ResourceBudgetExceeded", sqlstate=_sqlstate(exc))
            raise ResourceBudgetExceeded("HR bounded database execution was exhausted.") from exc
        _record_failure(state, "DatabaseError", sqlstate=_sqlstate(exc))
        raise
    except (PermissionDenied, ValidationError, AdmissionError, ResourceBudgetExceeded) as exc:
        _record_failure(state, type(exc).__name__)
        raise


def require_domain_anchors(anchors):
    """Private guard REQUIRED before any HR domain/reference row-lock SQL.

    Services still own ordered acquisition. Before final admission this records
    the planned complete union; afterward it permits only already protected
    anchors. It never acquires a newly discovered lock after authority admission.
    """
    state = _CURRENT.get()
    if state is None:
        raise AdmissionError("HR domain locking requires an admitted operation boundary.")
    anchors = _anchor_set(anchors)
    state.declare_anchors(anchors)
    if (
        state.admitted or state.authority_started_at is not None
    ) and not anchors <= state.acquired_anchors:
        state._refuse("Nested domain anchors are unacquired before authority admission.")


def require_persistence_scope(company_id, permissions, *, anchors=(), user_ids=()):
    """Named owner primitives require current authority and actual scoped locks."""
    state = _CURRENT.get()
    if state is None:
        raise AdmissionError("HR persistence requires an admitted owning operation.")
    try:
        state._check_domain_boundary()
        if (
            not state.admitted
            or company_id != state.context.company_id
            or permissions
            and not set(_permission_set(permissions)) <= set(state.permissions)
            or not _anchor_set(anchors) <= state.acquired_anchors
            or not _uuid_set(user_ids) <= state.user_ids
        ):
            state._refuse("HR persistence is outside its protected owner operation scope.")
        return state
    except Exception as exc:
        _poison(state, exc)
        raise
