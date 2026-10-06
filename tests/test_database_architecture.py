"""Regression guard, not a sandbox: reviewed explicit aliases remain supported."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


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
        return isinstance(node, ast.Constant) and node.value in (None, "default")

    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = qualified(node.func)
            if name in {"django.db.transaction.atomic", "django.db.transaction.on_commit"}:
                using = next((kw.value for kw in node.keywords if kw.arg == "using"), None)
                # atomic(using, savepoint, durable) / on_commit(func, using, robust).
                position = 0 if name.endswith(".atomic") else 1
                if using is None and len(node.args) > position:
                    using = node.args[position]
                if using is None or unsafe_alias(using):
                    findings.append((node.lineno, "implicit/default transaction alias"))
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"using", "db_manager"}:
                if node.args and unsafe_alias(node.args[0]):
                    findings.append((node.lineno, "hardcoded ORM database alias"))
                if any(kw.arg == "using" and unsafe_alias(kw.value) for kw in node.keywords):
                    findings.append((node.lineno, "hardcoded ORM database alias"))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if qualified(decorator) == "django.db.transaction.atomic":
                    findings.append((decorator.lineno, "implicit atomic decorator"))
        elif isinstance(node, ast.Subscript):
            if qualified(node.value) == "django.db.connections" and unsafe_alias(node.slice):
                findings.append((node.lineno, "hardcoded connection alias"))
        elif isinstance(node, (ast.Name, ast.Attribute)) and isinstance(node.ctx, ast.Load):
            if qualified(node) in {
                "django.db.connection",
                "django.db.DEFAULT_DB_ALIAS",
                "django.db.utils.DEFAULT_DB_ALIAS",
            }:
                findings.append((node.lineno, "implicit default connection"))
    return findings


@pytest.mark.parametrize("source", [
    "from django.db import transaction\n@transaction.atomic\ndef operation(): pass",
    "from django.db import transaction as tx\nwith tx.atomic(): pass",
    "from django.db.transaction import atomic as atom\nwith atom(): pass",
    "import django.db as db\nwith db.transaction.atomic(using=None): pass",
    "from django.db import transaction\nwith transaction.atomic('default'): pass",
    "from django.db import transaction\ntransaction.on_commit(callback)",
    "Model.objects.using('default').all()",
    "Model.objects.db_manager(using='default').all()",
    "from django.db import connections as conns\nconns['default'].cursor()",
    "from django.db import connection as conn\nconn.cursor()",
    "import django.db as db\ndb.connection.cursor()",
    "from django.db.utils import DEFAULT_DB_ALIAS as alias\nModel.objects.using(alias)",
    "from django.db import DEFAULT_DB_ALIAS\nModel.objects.using(DEFAULT_DB_ALIAS)",
])
def test_guard_rejects_implicit_defaults_including_import_aliases(source):
    assert database_assumptions(source)


@pytest.mark.parametrize("source", [
    "from django.db import transaction\nwith transaction.atomic(using=resolved_alias): pass",
    "from django.db import transaction\n@transaction.atomic(using=resolved_alias)\n"
    "def operation(): pass",
    "from django.db import transaction\ntransaction.on_commit(callback, using=alias)",
    "from django.db import connections\nconnections[current_database_alias()].cursor()",
    "Model.objects.using(alias).all()",
    "from businessos.core.database import business_atomic\n@business_atomic\n"
    "def operation(): pass",
])
def test_guard_accepts_explicit_resolved_aliases(source):
    assert not database_assumptions(source)


def test_active_runtime_has_no_unsafe_database_assumptions():
    failures = []
    for directory in (ROOT / "businessos/core", ROOT / "businessos/modules", ROOT / "config"):
        for path in sorted(directory.rglob("*.py")):
            relative = path.relative_to(ROOT)
            if {"migrations", "tests"} & set(relative.parts) or path.is_relative_to(
                ROOT / "businessos/core/database"
            ):
                continue
            for line, finding in database_assumptions(path.read_text(encoding="utf-8")):
                failures.append(f"{relative}:{line}: {finding}")
    assert not failures, "\n".join(failures)
