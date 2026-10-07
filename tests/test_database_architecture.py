"""Source-level regression guard, not a runtime security boundary.

Resolve ordinary explicit imports/aliases, not Python's complete scope or data flow.
Dynamic imports, getattr, reassigned aliases, wildcard imports, expanded arguments,
and values computed at runtime require review. A nonliteral alias is not proven safe.
Only active Python runtime roots are scanned; archived refs and generated frontend
output aren't source inputs. Infrastructure exemptions are path-specific below.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALIASES = {"django.db.DEFAULT_DB_ALIAS", "django.db.utils.DEFAULT_DB_ALIAS"}


def database_assumptions(source):
    tree = ast.parse(source)
    imports = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    def qualified(node):
        if isinstance(node, ast.Name):
            return imports.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return f"{qualified(node.value)}.{node.attr}"
        return ""

    def unsafe_alias(node):
        return (
            isinstance(node, ast.Constant) and node.value in (None, "default")
        ) or qualified(node) in DEFAULT_ALIASES

    def argument(node, keyword, position=0):
        value = next((kw.value for kw in node.keywords if kw.arg == keyword), None)
        if value is None and len(node.args) > position:
            value = node.args[position]
        return value

    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = qualified(node.func)
            if name in {
                "django.db.transaction.atomic",
                "django.db.transaction.on_commit",
                "django.db.transaction.get_connection",
            }:
                # atomic(using, savepoint, durable) / on_commit(func, using, robust).
                position = 1 if name.endswith(".on_commit") else 0
                using = argument(node, "using", position)
                if using is None or unsafe_alias(using):
                    finding = (
                        "implicit/default get_connection alias"
                        if name.endswith(".get_connection")
                        else "implicit/default transaction alias"
                    )
                    findings.append((node.lineno, finding))
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"using", "db_manager"}:
                # QuerySet.using(alias=...) versus Manager.db_manager(using=...).
                keyword = "alias" if node.func.attr == "using" else "using"
                if unsafe_alias(argument(node, keyword)):
                    findings.append((node.lineno, "hardcoded ORM database alias"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if qualified(decorator) == "django.db.transaction.atomic":
                    findings.append((decorator.lineno, "implicit atomic decorator"))
        elif isinstance(node, ast.Subscript):
            if qualified(node.value) == "django.db.connections" and unsafe_alias(node.slice):
                findings.append((node.lineno, "hardcoded connection alias"))
        elif isinstance(node, (ast.Name, ast.Attribute)) and isinstance(node.ctx, ast.Load):
            if qualified(node) in DEFAULT_ALIASES:
                findings.append((node.lineno, "forced default alias constant"))
            if isinstance(node, ast.Attribute) and qualified(node.value) == "django.db.connection":
                findings.append((node.lineno, "implicit default connection access"))
    return findings


@pytest.mark.parametrize("source", [
    "from django.db import transaction\n@transaction.atomic\ndef operation(): pass",
    "from django.db import transaction as tx\nwith tx.atomic(): pass",
    "from django.db.transaction import atomic as atom\nwith atom(): pass",
    "import django.db as db\nwith db.transaction.atomic(using=None): pass",
    "from django.db import transaction\nwith transaction.atomic('default'): pass",
    "from django.db import transaction\ntransaction.on_commit(callback)",
    "Model.objects.using('default').all()",
    "Model.objects.using(alias='default').all()",
    "Model.objects.using(alias=None).all()",
    "Model.objects.db_manager('default').all()",
    "Model.objects.db_manager(using='default').all()",
    "Model.objects.db_manager(using=None).all()",
    "from django.db import connections\nconnections['default']",
    "from django.db import connections as conns\nconns['default'].cursor()",
    "from django.db import connection as conn\nconn.cursor()",
    "import django.db as db\ndb.connection.cursor()",
    "from django.db.utils import DEFAULT_DB_ALIAS as alias\nModel.objects.using(alias)",
    "from django.db import DEFAULT_DB_ALIAS\nModel.objects.using(DEFAULT_DB_ALIAS)",
    "from django.db import DEFAULT_DB_ALIAS as DBA\nModel.objects.using(alias=DBA)",
    "from django.db.utils import DEFAULT_DB_ALIAS as DBA\nModel.objects.db_manager(using=DBA)",
    "from django.db import DEFAULT_DB_ALIAS as DBA\nModel.objects.db_manager(DBA)",
    "from django.db import DEFAULT_DB_ALIAS as DBA, connections as conns\nconns[DBA]",
    "import django.db as db\nModel.objects.using(alias=db.DEFAULT_DB_ALIAS)",
    "import django.db.utils as utils\nModel.objects.db_manager(using=utils.DEFAULT_DB_ALIAS)",
    "from django.db import connection\nconnection.cursor()",
    "from django.db import connection as conn\nconn.in_atomic_block",
    "import django.db\ndjango.db.connection.cursor()",
    "from django.db import transaction\n@transaction.atomic()\ndef operation(): pass",
    "from django.db.transaction import atomic as atom\n@atom\ndef operation(): pass",
    "from django.db.transaction import atomic as atom\n@atom()\ndef operation(): pass",
    "from django.db import DEFAULT_DB_ALIAS as DBA, transaction as tx\nwith tx.atomic(DBA): pass",
    "from django.db import DEFAULT_DB_ALIAS as DBA, transaction as tx\n"
    "tx.on_commit(callback, using=DBA)",
    "import django.db.transaction as tx\nwith tx.atomic(): pass",
])
def test_guard_rejects_implicit_defaults_including_import_aliases(source):
    assert database_assumptions(source)


@pytest.mark.parametrize("imports, function", [
    ("from django.db.transaction import get_connection", "get_connection"),
    ("from django.db.transaction import get_connection as gc", "gc"),
    ("from django.db import transaction", "transaction.get_connection"),
    ("from django.db import transaction as tx", "tx.get_connection"),
    ("import django.db.transaction as tx", "tx.get_connection"),
    ("import django.db", "django.db.transaction.get_connection"),
])
@pytest.mark.parametrize("arguments", [
    "", "'default'", "using='default'", "None", "using=None", "DBA", "using=DBA",
])
def test_guard_rejects_get_connection_defaults(imports, function, arguments):
    source = f"from django.db import DEFAULT_DB_ALIAS as DBA\n{imports}\n{function}({arguments})"
    assert (3, "implicit/default get_connection alias") in database_assumptions(source)


@pytest.mark.parametrize("expression, finding", [
    ("Model.objects.using(alias='default')", "hardcoded ORM database alias"),
    ("Model.objects.db_manager(using=DBA)", "hardcoded ORM database alias"),
    ("conns[DBA]", "hardcoded connection alias"),
    ("conn.cursor()", "implicit default connection access"),
])
def test_guard_reports_api_and_source_line(expression, finding):
    source = (
        "from django.db import DEFAULT_DB_ALIAS as DBA, connections as conns, connection as conn\n"
        f"{expression}"
    )
    assert (2, finding) in database_assumptions(source)


@pytest.mark.parametrize("source", [
    "from django.db import transaction\nwith transaction.atomic(using=resolved_alias): pass",
    "from django.db import transaction\n@transaction.atomic(using=resolved_alias)\n"
    "def operation(): pass",
    "from django.db import transaction\ntransaction.on_commit(callback, using=alias)",
    "from django.db import connections\nconnections[current_database_alias()].cursor()",
    "Model.objects.using(alias).all()",
    "Model.objects.using(alias=current_database_alias()).all()",
    "Model.objects.using(current_database_alias()).all()",
    "Model.objects.using(alias=resolved_alias).all()",
    "Model.objects.db_manager(using=resolved_alias).all()",
    "Model.objects.db_manager(current_database_alias()).all()",
    "from django.db import transaction as tx\nwith tx.atomic(using=current_database_alias()): pass",
    "from django.db.transaction import atomic as atom\nwith atom(resolved_alias): pass",
    "from django.db.transaction import get_connection as gc\ngc(using=resolved_alias)",
    "from django.db import transaction as tx\ntx.get_connection(current_database_alias())",
    "from django.db import router\nrouter.db_for_read(Model)\nrouter.db_for_write(Model)",
    "current_database_alias()",
    "from django.db import connection as conn\nreference = conn",
    "# Model.objects.using(alias='default')\nmessage = 'get_connection()'",
    "from businessos.core.database import business_atomic\n@business_atomic\n"
    "def operation(): pass",
    "from businessos.core.database import business_atomic_context\n"
    "with business_atomic_context(): pass",
])
def test_guard_accepts_explicit_resolved_aliases(source):
    assert not database_assumptions(source)


def runtime_database_findings(root):
    failures = []
    for directory in (root / "businessos/core", root / "businessos/modules", root / "config"):
        for path in sorted(directory.rglob("*.py")):
            relative = path.relative_to(root)
            if {"migrations", "tests"} & set(relative.parts) or path.is_relative_to(
                root / "businessos/core/database"
            ):
                continue
            for line, finding in database_assumptions(path.read_text(encoding="utf-8")):
                failures.append(f"{relative}:{line}: {finding}")
    return failures


@pytest.mark.parametrize("relative", [
    "businessos/core/database/transactions.py",
    "businessos/core/access/migrations/0001_initial.py",
    "businessos/modules/catalog/tests/test_example.py",
    "tests/test_example.py",
    "archive/businessos/modules/old/services.py",
    "static/generated/example.py",
])
def test_runtime_scan_excludes_only_approved_source_locations(tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text("from django.db.transaction import get_connection\nget_connection()")
    assert not runtime_database_findings(tmp_path)


@pytest.mark.parametrize("relative", [
    "businessos/core/access/services.py",
    "businessos/modules/example/database/services.py",
    "config/management/commands/example.py",
])
def test_runtime_scan_does_not_exempt_business_database_directories(tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text("Model.objects.using(alias='default')")
    assert runtime_database_findings(tmp_path) == [
        f"{Path(relative)}:1: hardcoded ORM database alias"
    ]


def test_active_runtime_has_no_unsafe_database_assumptions():
    failures = runtime_database_findings(ROOT)
    assert not failures, "\n".join(failures)
