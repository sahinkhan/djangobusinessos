"""Source-level regression guard, not a runtime security boundary.

Python's symbol tables provide lexical locals, parameters, globals and free names;
each AST scope owns its imports. Methods skip class namespaces for closure lookup.
This is not control-flow/interprocedural analysis: conditional/complex reassignment,
global/nonlocal rebinding across calls, dynamic imports, computed attributes/getattr,
monkeypatching, wildcard imports, expanded arguments and runtime values need review.
Advanced type-parameter/annotation scopes aren't modeled. A nonliteral alias isn't
proven safe. Ordinary assignment shadows an import; assigned callable aliases aren't
traced back to their origin. Function/module imports are precollected to cover
forward closure references, not to prove conditional branches/execution order.
Class-body imports bind as encountered; parameters start as injected values.
Only active Python runtime roots are scanned; archived refs and generated frontend
output aren't source inputs. Infrastructure exemptions are path-specific below.
"""

import ast
import symtable
import textwrap
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALIASES = {"django.db.DEFAULT_DB_ALIAS", "django.db.utils.DEFAULT_DB_ALIAS"}


class ScopeImports(ast.NodeVisitor):
    """Collect imports in one body, never in its child lexical scopes."""

    def __init__(self):
        self.bindings = {}

    def visit_Import(self, node):
        for alias in node.names:
            self.bindings[alias.asname or alias.name.split(".")[0]] = (
                alias.name if alias.asname else alias.name.split(".")[0]
            )

    def visit_ImportFrom(self, node):
        for alias in node.names:
            if not node.level and alias.name != "*":
                self.bindings[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    def visit_FunctionDef(self, node):
        pass

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef


class LexicalScope:
    def __init__(self, table, body, parent=None, inlined=False):
        self.table = table
        self.parent = parent
        self.inlined = inlined
        self.kind = "function" if inlined else table.get_type()
        collector = ScopeImports()
        for node in body:
            collector.visit(node)
        # Class bodies execute immediately and use LOAD_NAME fallback until bound;
        # function parameters are initially injected values, not future imports.
        self.bindings = {} if self.kind == "class" else collector.bindings
        if not inlined:
            for symbol in table.get_symbols():
                if symbol.is_parameter():
                    self.bindings[symbol.get_name()] = ""
        self.children = parent.children if inlined else list(table.get_children())

    def resolve(self, name):
        if self.inlined:
            if name in self.bindings:
                return self.bindings[name]
            parent = self.parent
            while parent and parent.kind == "class":
                parent = parent.parent
            return parent.resolve(name) if parent else ""
        try:
            symbol = self.table.lookup(name)
        except KeyError:
            return ""
        if symbol.is_local() or name in self.bindings:
            if self.kind == "class" and name not in self.bindings:
                root = self
                while root.parent:
                    root = root.parent
                return root.bindings.get(name, "")
            return self.bindings.get(name, "")
        parent = self.parent
        if symbol.is_global():
            while parent and parent.parent:
                parent = parent.parent
        else:
            # Class bodies are execution namespaces, not method/nested closures.
            while parent and parent.kind == "class":
                parent = parent.parent
        return parent.resolve(name) if parent else ""


class DatabaseGuard(ast.NodeVisitor):
    def __init__(self, source, tree):
        self.scope = LexicalScope(symtable.symtable(source, "<database-guard>", "exec"), tree.body)
        self.findings = []

    @contextmanager
    def child_scope(self, node, name, body):
        parent = self.scope
        table = next((
            child for child in parent.children
            if child.get_name() == name and child.get_lineno() == node.lineno
        ), None)
        # Python 3.12+ inlines list/set/dict comprehensions in its symbol tables,
        # but their iteration variables still have a separate lexical lifetime.
        inlined = table is None and name in {"listcomp", "setcomp", "dictcomp"}
        if table is None and not inlined:
            raise ValueError(f"Unmodeled lexical scope: {name}:{node.lineno}")
        if table:
            parent.children.remove(table)
        self.scope = LexicalScope(table or parent.table, body, parent, inlined=inlined)
        try:
            yield
        finally:
            self.scope = parent

    def qualified(self, node):
        if isinstance(node, ast.Name):
            return self.scope.resolve(node.id)
        if isinstance(node, ast.Attribute):
            return f"{self.qualified(node.value)}.{node.attr}"
        return ""

    def unsafe_alias(self, node):
        return (
            isinstance(node, ast.Constant) and node.value in (None, "default")
        ) or self.qualified(node) in DEFAULT_ALIASES

    @staticmethod
    def argument(node, keyword, position=0):
        value = next((kw.value for kw in node.keywords if kw.arg == keyword), None)
        if value is None and len(node.args) > position:
            value = node.args[position]
        return value

    def visit_Call(self, node):
        name = self.qualified(node.func)
        if name in {
            "django.db.transaction.atomic",
            "django.db.transaction.on_commit",
            "django.db.transaction.get_connection",
        }:
            # atomic/get_connection(using, ...) versus on_commit(func, using, ...).
            position = 1 if name.endswith(".on_commit") else 0
            using = self.argument(node, "using", position)
            if using is None or self.unsafe_alias(using):
                finding = (
                    "implicit/default get_connection alias"
                    if name.endswith(".get_connection")
                    else "implicit/default transaction alias"
                )
                self.findings.append((node.lineno, finding))
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"using", "db_manager"}:
            keyword = "alias" if node.func.attr == "using" else "using"
            if self.unsafe_alias(self.argument(node, keyword)):
                self.findings.append((node.lineno, "hardcoded ORM database alias"))
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Decorators/defaults/annotations execute outside the new function scope.
        for decorator in node.decorator_list:
            if self.qualified(decorator) == "django.db.transaction.atomic":
                self.findings.append((decorator.lineno, "implicit atomic decorator"))
            self.visit(decorator)
        self.visit(node.args)
        if node.returns:
            self.visit(node.returns)
        self.scope.bindings[node.name] = ""
        with self.child_scope(node, node.name, node.body):
            for statement in node.body:
                self.visit(statement)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        for expression in [*node.decorator_list, *node.bases, *node.keywords]:
            self.visit(expression)
        self.scope.bindings[node.name] = ""
        with self.child_scope(node, node.name, node.body):
            for statement in node.body:
                self.visit(statement)

    def visit_Lambda(self, node):
        self.visit(node.args)
        with self.child_scope(node, "lambda", [node.body]):
            self.visit(node.body)

    def visit_ListComp(self, node):
        # The first iterable executes outside the comprehension's lexical scope.
        self.visit(node.generators[0].iter)
        name = {
            ast.ListComp: "listcomp", ast.SetComp: "setcomp",
            ast.DictComp: "dictcomp", ast.GeneratorExp: "genexpr",
        }[type(node)]
        with self.child_scope(node, name, []):
            for index, generator in enumerate(node.generators):
                if index:
                    self.visit(generator.iter)
                self.visit(generator.target)
                for condition in generator.ifs:
                    self.visit(condition)
            if isinstance(node, ast.DictComp):
                self.visit(node.key)
                self.visit(node.value)
            else:
                self.visit(node.elt)

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_Import(self, node):
        collector = ScopeImports()
        collector.visit(node)
        self.scope.bindings.update(collector.bindings)

    visit_ImportFrom = visit_Import

    def visit_Assign(self, node):
        self.visit(node.value)
        for target in node.targets:
            self.visit(target)

    def visit_NamedExpr(self, node):
        self.visit(node.value)
        self.visit(node.target)

    visit_AugAssign = visit_NamedExpr

    def visit_AnnAssign(self, node):
        self.visit(node.annotation)
        if node.value:
            self.visit(node.value)
            self.visit(node.target)

    def visit_ExceptHandler(self, node):
        if node.type:
            self.visit(node.type)
        if node.name:
            self.scope.bindings[node.name] = ""
        for statement in node.body:
            self.visit(statement)

    def visit_Subscript(self, node):
        if self.qualified(node.value) == "django.db.connections" and self.unsafe_alias(node.slice):
            self.findings.append((node.lineno, "hardcoded connection alias"))
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Del):
            self.scope.bindings.pop(node.id, None)
        elif isinstance(node.ctx, ast.Store):
            self.scope.bindings[node.id] = ""
        elif self.qualified(node) in DEFAULT_ALIASES:
            self.findings.append((node.lineno, "forced default alias constant"))

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load):
            if self.qualified(node) in DEFAULT_ALIASES:
                self.findings.append((node.lineno, "forced default alias constant"))
            if self.qualified(node.value) == "django.db.connection":
                self.findings.append((node.lineno, "implicit default connection access"))
        self.generic_visit(node)


def database_assumptions(source):
    tree = ast.parse(source)
    guard = DatabaseGuard(source, tree)
    guard.visit(tree)
    return guard.findings


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


@pytest.mark.parametrize("api, unsafe_import, safe_import, unsafe_call, safe_call, finding", [
    (
        "get_connection", "from django.db.transaction import get_connection as gc",
        "from math import gcd as gc", "gc()", "gc(6, 4)",
        "implicit/default get_connection alias",
    ),
    (
        "atomic", "from django.db import transaction as tx",
        "from helpers import transaction as tx", "tx.atomic()", "tx.atomic()",
        "implicit/default transaction alias",
    ),
])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("methods", [False, True])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_sibling_import_scopes_are_independent(
    api, unsafe_import, safe_import, unsafe_call, safe_call, finding,
    reverse, methods, asynchronous,
):
    prefix = "async " if asynchronous else ""
    arguments = "self" if methods else ""
    unsafe = f"{prefix}def unsafe({arguments}):\n    {unsafe_import}\n    return {unsafe_call}"
    safe = f"{prefix}def safe({arguments}):\n    {safe_import}\n    return {safe_call}"
    source = "\n\n".join([safe, unsafe] if reverse else [unsafe, safe])
    line = 7 if reverse else 3
    if methods:
        source = "class Example:\n" + textwrap.indent(source, "    ")
        line += 1
    assert database_assumptions(source) == [(line, finding)], api


@pytest.mark.parametrize("name, import_source, expression", [
    ("gc", "from django.db.transaction import get_connection as gc", "gc()"),
    ("tx", "from django.db import transaction as tx", "tx.atomic()"),
])
@pytest.mark.parametrize("parameters", ["{name}", "{name}=None", "{name}, /", "*, {name}"])
def test_parameters_shadow_module_imports(name, import_source, expression, parameters):
    source = (
        f"{import_source}\ndef callback({parameters.format(name=name)}):\n"
        f"    return {expression}"
    )
    assert database_assumptions(source) == []


@pytest.mark.parametrize("source, expected", [
    ("""
        from django.db.transaction import get_connection as gc
        def unsafe():
            return gc()
        def safe():
            from math import gcd as gc
            return gc(6, 4)
    """, [(3, "implicit/default get_connection alias")]),
    ("""
        from django.db import transaction as tx
        def safe():
            from helpers import transaction as tx
            return tx.atomic()
        def unsafe():
            return tx.atomic()
    """, [(6, "implicit/default transaction alias")]),
    ("""
        def outer():
            from django.db.transaction import get_connection as gc
            def inner():
                return gc()
            return inner()
    """, [(4, "implicit/default get_connection alias")]),
    ("""
        def outer():
            def inner():
                return gc()
            from django.db.transaction import get_connection as gc
            return inner()
    """, [(3, "implicit/default get_connection alias")]),
    ("""
        def outer():
            from django.db.transaction import get_connection as gc
            def inner(gc):
                return gc()
            return inner(callback)
    """, []),
    ("""
        from django.db.transaction import get_connection as gc
        def outer(gc):
            def inner():
                return gc()
            return inner()
    """, []),
    ("""
        def outer():
            from django.db.transaction import get_connection as gc
            def inner():
                from math import gcd as gc
                return gc(6, 4)
            return gc()
    """, [(6, "implicit/default get_connection alias")]),
    ("""
        from django.db.transaction import get_connection as gc
        class Example:
            gc = injected_callback
            def unsafe(self):
                return gc()
    """, [(5, "implicit/default get_connection alias")]),
    ("""
        from math import gcd as gc
        class Example:
            from django.db.transaction import get_connection as gc
            def safe(self):
                return gc(6, 4)
    """, []),
    ("""
        def outer():
            from django.db.transaction import get_connection as gc
            class Example:
                gc = injected_callback
                def unsafe(self):
                    return gc()
            return Example
    """, [(6, "implicit/default get_connection alias")]),
    ("""
        class Unsafe:
            def operation(self):
                from django.db import transaction as tx
                return tx.atomic()
        class Safe:
            def operation(self):
                from helpers import transaction as tx
                return tx.atomic()
    """, [(4, "implicit/default transaction alias")]),
    ("""
        from django.db.transaction import get_connection as gc
        def callback():
            gc = injected_callback
            return gc()
    """, []),
    ("""
        from django.db.transaction import get_connection as gc
        def callback():
            value = gc()
            gc = injected_callback
            return value
    """, []),
    ("""
        from django.db.transaction import get_connection as gc
        def callback():
            def gc():
                return 1
            return gc()
    """, []),
    ("""
        from django.db.transaction import get_connection as gc
        def gc():
            return 1
        gc()
    """, []),
    ("""
        def callback():
            from django.db.transaction import get_connection as gc
            gc = injected_callback
            return gc()
    """, []),
    ("""
        def callback():
            from django.db.transaction import get_connection as gc
            gc = gc()
            return gc
    """, [(3, "implicit/default get_connection alias")]),
    ("""
        from django.db.transaction import get_connection as gc
        def callback(gc=gc()):
            return gc()
    """, [(2, "implicit/default get_connection alias")]),
    ("""
        from django.db import transaction as tx
        @tx.atomic
        def callback(tx):
            return tx.atomic()
    """, [(2, "implicit atomic decorator")]),
    ("""
        from django.db.transaction import get_connection as gc
        callback = lambda gc: gc()
        unsafe = lambda: gc()
    """, [(3, "implicit/default get_connection alias")]),
    ("""
        from django.db.transaction import get_connection as gc
        def callback():
            global gc
            return gc()
    """, [(4, "implicit/default get_connection alias")]),
    ("""
        def outer():
            from django.db.transaction import get_connection as gc
            def inner():
                nonlocal gc
                return gc()
    """, [(5, "implicit/default get_connection alias")]),
    ("""
        from django.db import transaction as tx
        def one(tx):
            return tx.atomic()
        def two():
            import helpers as tx
            return tx.atomic()
        def three():
            return tx.atomic()
    """, [(8, "implicit/default transaction alias")]),
    ("""
        from django.db.transaction import get_connection as gc
        value = (gc := gc())
    """, [(2, "implicit/default get_connection alias")]),
    ("""
        from django.db.transaction import get_connection as gc
        def callback():
            from django.db.transaction import get_connection as gc
            try:
                operation()
            except Exception as gc:
                return gc()
    """, []),
    ("""
        from django.db import transaction as tx
        class Example:
            from django.db import transaction as tx
            @tx.atomic
            def callback(self, tx):
                return tx.atomic()
    """, [(4, "implicit atomic decorator")]),
    ("""
        from django.db.transaction import get_connection as gc
        class Example:
            value = gc()
            gc = injected_callback
            safe_value = gc()
    """, [(3, "implicit/default get_connection alias")]),
    ("""
        from django.db.transaction import get_connection as gc
        class Example:
            value = gc()
            from math import gcd as gc
            safe_value = gc(6, 4)
    """, [(3, "implicit/default get_connection alias")]),
    ("""
        def outer():
            from django.db.transaction import get_connection as gc
            class Example:
                value = gc()
                gc = injected_callback
            return Example
    """, []),
    ("""
        def callback(gc):
            gc()
            from django.db.transaction import get_connection as gc
            gc()
    """, [(4, "implicit/default get_connection alias")]),
    ("""
        def callback(tx):
            tx.atomic()
            from django.db import transaction as tx
            tx.atomic()
    """, [(4, "implicit/default transaction alias")]),
    ("""
        from django.db.transaction import get_connection as gc
        class Example:
            gc = lambda: 1
            safe_value = gc()
            del gc
            unsafe_value = gc()
    """, [(6, "implicit/default get_connection alias")]),
])
def test_lexical_resolution_and_shadowing(source, expected):
    assert database_assumptions(textwrap.dedent(source).strip()) == expected


@pytest.mark.parametrize("declaration, expression, expected", [
    (
        "connections as conns", "conns['default']",
        ["hardcoded connection alias"],
    ),
    (
        "connection as conn", "conn.cursor()",
        ["implicit default connection access"],
    ),
    (
        "DEFAULT_DB_ALIAS as DBA", "Model.objects.using(alias=DBA)",
        ["hardcoded ORM database alias", "forced default alias constant"],
    ),
    (
        "transaction as tx", "tx.on_commit(callback)",
        ["implicit/default transaction alias"],
    ),
])
@pytest.mark.parametrize("reverse", [False, True])
def test_other_database_import_aliases_remain_scope_local(
    declaration, expression, expected, reverse,
):
    unsafe = f"def unsafe():\n    from django.db import {declaration}\n    {expression}"
    safe = f"def safe():\n    from helpers import {declaration}\n    {expression}"
    source = "\n\n".join([safe, unsafe] if reverse else [unsafe, safe])
    line = 7 if reverse else 3
    assert database_assumptions(source) == [(line, finding) for finding in expected]


@pytest.mark.parametrize("declaration, parameter, expression", [
    ("connections as conns", "conns", "conns['default']"),
    ("connection as conn", "conn", "conn.cursor()"),
    ("DEFAULT_DB_ALIAS as DBA", "DBA", "Model.objects.using(alias=DBA)"),
    ("transaction as tx", "tx", "tx.on_commit(callback)"),
])
def test_other_database_alias_parameters_shadow_imports(declaration, parameter, expression):
    source = f"from django.db import {declaration}\ndef safe({parameter}):\n    {expression}"
    assert database_assumptions(source) == []


@pytest.mark.parametrize("expression", [
    "[gc() for gc in callbacks]",
    "{gc() for gc in callbacks}",
    "{index: gc() for index, gc in callbacks}",
    "(gc() for gc in callbacks)",
])
def test_comprehension_binding_does_not_leak(expression):
    source = f"from django.db.transaction import get_connection as gc\nvalue = {expression}\ngc()"
    assert database_assumptions(source) == [(3, "implicit/default get_connection alias")]


def test_comprehension_first_iterable_uses_enclosing_scope():
    source = (
        "from django.db.transaction import get_connection as gc\n"
        "value = [gc() for gc in gc()]"
    )
    assert database_assumptions(source) == [(2, "implicit/default get_connection alias")]


def test_comprehension_skips_class_namespace():
    source = (
        "from django.db.transaction import get_connection as gc\n"
        "class Example:\n"
        "    gc = injected_callback\n"
        "    value = [gc() for item in values]"
    )
    assert database_assumptions(source) == [(4, "implicit/default get_connection alias")]


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
