"""Validate Git-bound provenance before forwarding a red proof to reconciliation."""

from __future__ import annotations

import argparse
import ast
import configparser
import functools
import hashlib
import itertools
import json
import re
import shlex
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import cast
from xml.etree import ElementTree

from beartype import beartype
from icontract import ensure


GIT_OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
MAX_TEST_BLOB_BYTES = 10 * 1024 * 1024
GOVERNED_PRODUCTION_PREFIXES = (
    ".github/",
    "ci/",
    "scripts/",
    "src/",
    "tools/",
    "resources/templates/",
    "resources/schemas/",
    "resources/mappings/",
    "resources/keys/",
    "modules/bundle-mapper/",
)
GOVERNED_PRODUCTION_FILES = {"pyproject.toml", "setup.py", "uv.lock", "requirements/ci/locked.txt"}
# Implicit configuration candidates and their tables, mirroring pytest's own discovery order.
PYTEST_CONFIGURATION_FILES = (
    "pytest.toml",
    ".pytest.toml",
    "pytest.ini",
    ".pytest.ini",
    "pyproject.toml",
    "tox.ini",
    "setup.cfg",
)
PYTEST_TOML_TABLES: dict[str, tuple[tuple[str, ...], ...]] = {
    "pytest.toml": (("pytest",),),
    ".pytest.toml": (("pytest",),),
    "pyproject.toml": (("tool", "pytest", "ini_options"), ("tool", "pytest")),
}
PYTEST_INI_SECTIONS = {
    "pytest.ini": "pytest",
    ".pytest.ini": "pytest",
    "tox.ini": "pytest",
    "setup.cfg": "tool:pytest",
}
REPOSITORY_ROOT_MODULE_ROOTS = ("",)
# Plugins the executor early-loads with ``-p`` on every proof run. They are not declared in any
# configuration this gate can read, so they are named here and held to the executor's own command
# shape by a contract test rather than by these two files being edited together.
EXECUTOR_PLUGIN_NAMES = (("scripts", "requirements_proof_pytest_plugin"),)
GIT_TIMEOUT_SECONDS = 30
UNRESOLVED_PLUGIN_VALUE = object()


def _git_bytes(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    """Run Git for payloads that are not required to be valid text."""
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            capture_output=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(["git", *arguments], returncode=1, stdout=b"", stderr=b"")


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run Git for textual output, treating a timeout as an ordinary command failure."""
    result = _git_bytes(repo_root, *arguments)
    return subprocess.CompletedProcess(
        result.args,
        returncode=result.returncode,
        stdout=result.stdout.decode("utf-8", errors="surrogateescape"),
        stderr=result.stderr.decode("utf-8", errors="surrogateescape"),
    )


def _read_red_proof(red_proof_path: Path) -> dict[str, object]:
    try:
        report = json.loads(red_proof_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    if not isinstance(report, dict):
        raise ValueError("prior-red-proof-invalid")
    return cast(dict[str, object], report)


def _validated_execution_proof(report: dict[str, object]) -> dict[str, object]:
    """Return the red-stage execution record only when its required fields are valid."""
    execution_proof = report.get("execution_proof")
    if not isinstance(execution_proof, dict):
        raise ValueError("prior-red-proof-invalid")
    return cast(dict[str, object], execution_proof)


def _validated_selectors(execution_proof: dict[str, object]) -> list[str]:
    """Return selector strings only when the red source and every selector entry are well formed."""
    source_ref = execution_proof.get("source_ref")
    selectors = execution_proof.get("selectors")
    if (
        not isinstance(source_ref, str)
        or GIT_OBJECT_PATTERN.fullmatch(source_ref) is None
        or not isinstance(selectors, list)
        or not selectors
        or not all(isinstance(selector, str) for selector in cast(list[object], selectors))
    ):
        raise ValueError("prior-red-proof-invalid")
    return cast(list[str], selectors)


def _selector_paths(report: dict[str, object]) -> tuple[str, list[str]]:
    """Validate the released red-report shape and extract unique selector file paths."""
    execution_proof = _validated_execution_proof(report)
    if report.get("gate_decision") != "pass" or report.get("observed_maturity") != "red":
        raise ValueError("prior-red-proof-invalid")
    if execution_proof.get("run_stage") != "red":
        raise ValueError("prior-red-proof-invalid")
    selectors = _validated_selectors(execution_proof)
    source_ref = execution_proof["source_ref"]
    assert isinstance(source_ref, str)
    paths: set[str] = set()
    for selector in selectors:
        test_path, separator, _ = selector.partition("::")
        path = PurePosixPath(test_path)
        if not separator or path.is_absolute() or ".." in path.parts or not test_path.endswith(".py"):
            raise ValueError("prior-red-proof-invalid")
        paths.add(test_path)
    return source_ref, sorted(paths)


def _ancestor_file_paths(path: str, filename: str) -> set[str]:
    """Return a root file candidate and the same file beneath every ancestor."""
    parent = PurePosixPath(path).parent
    paths = {filename}
    while parent != PurePosixPath("."):
        paths.add((parent / filename).as_posix())
        parent = parent.parent
    return paths


def _pythonpath_entries(value: object) -> list[str]:
    """Return the individual roots of a pytest ``pythonpath`` setting.

    A string form is split with ``shlex`` because pytest parses ``paths`` ini values that
    way, so a quoted entry containing spaces stays one path.
    """
    if isinstance(value, str):
        try:
            return shlex.split(value)
        except ValueError:
            return []
    if isinstance(value, list):
        return [entry for entry in cast(list[object], value) if isinstance(entry, str)]
    return []


def _toml_option_value(text: str, table_paths: Sequence[Sequence[str]], option: str) -> object | None:
    """Return one option from the first TOML table that declares it."""
    try:
        document: object = tomllib.loads(text)
    except (tomllib.TOMLDecodeError, ValueError):
        return None
    for table_path in table_paths:
        node = document
        for key in (*table_path, option):
            if not isinstance(node, dict):
                node = None
                break
            node = cast(dict[str, object], node).get(key)
        if node is not None:
            return node
    return None


def _pytest_ini_option(text: str, configuration_path: str, option: str) -> object | None:
    """Return one pytest configuration option from a TOML or ini-style source."""
    table_paths = PYTEST_TOML_TABLES.get(configuration_path)
    if table_paths is not None:
        return _toml_option_value(text, table_paths, option)
    section = PYTEST_INI_SECTIONS.get(configuration_path)
    if section is None:
        return None
    # Interpolation is disabled because pytest accepts literal percent signs in option values.
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(text)
        return parser.get(section, option, fallback=None)
    except configparser.Error:
        return None


def _configuration_candidate_paths(directories: Sequence[str]) -> set[str]:
    """Return every configuration path pytest may read for these directories.

    The returned set is bound as proof input, so adding or changing a nested candidate after
    the red source invalidates the proof exactly as a root-level one does.
    """
    return {
        f"{directory}/{name}" if directory else name for directory in directories for name in PYTEST_CONFIGURATION_FILES
    }


def _configuration_directories(selector_paths: Sequence[str]) -> tuple[str, ...]:
    """Return the repository root and every selector ancestor pytest may take configuration from.

    Pytest searches upward from the arguments' common ancestor, so a nested ``tests/pytest.ini``
    decides collection for a selector beneath it.
    """
    directories = {""}
    for path in selector_paths:
        parent = PurePosixPath(path).parent
        while parent != PurePosixPath("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return tuple(sorted(directories))


@functools.cache
def _pytest_configuration_sources(
    repo_root: Path, source_ref: str, directories: tuple[str, ...] = ("",)
) -> tuple[tuple[str, str], ...]:
    """Return the readable pytest configuration candidates committed at the red source.

    Raises ``ValueError('stale-red-proof')`` when a candidate exists but cannot be read,
    whether because it is oversized, symlinked, or its Git read failed, because an unread
    configuration could declare plugins or roots this gate must bind. An absent candidate is
    distinguished from an unreadable one so a timeout is never mistaken for absence.
    """
    sources: list[tuple[str, str]] = []
    for directory in directories:
        for name in PYTEST_CONFIGURATION_FILES:
            path = f"{directory}/{name}" if directory else name
            result = _git_bytes(repo_root, "show", f"{source_ref}:{path}")
            if result.returncode != 0:
                if _test_path_exists_at_ref(repo_root, source_ref, path):
                    raise ValueError("stale-red-proof")
                continue
            if len(result.stdout) > MAX_TEST_BLOB_BYTES or not _test_path_is_regular_at_ref(
                repo_root, source_ref, path
            ):
                raise ValueError("stale-red-proof")
            sources.append((path, result.stdout.decode("utf-8", errors="surrogateescape")))
    return tuple(sources)


def _addopts_plugin_names(value: object) -> list[list[str]]:
    """Return module names early-loaded through ``-p`` in a configured ``addopts`` setting."""
    if isinstance(value, str):
        try:
            tokens = shlex.split(value)
        except ValueError:
            return []
    elif isinstance(value, list):
        tokens = [token for token in cast(list[object], value) if isinstance(token, str)]
    else:
        return []
    names: list[str] = []
    expecting_name = False
    for token in tokens:
        if expecting_name:
            names.append(token)
            expecting_name = False
        elif token == "-p":
            expecting_name = True
        elif token.startswith("-p") and len(token) > 2:
            names.append(token.removeprefix("-p"))
    return [name.split(".") for name in names if name and not name.startswith("no:")]


@functools.cache
def _addopts_plugin_module_names(
    repo_root: Path, source_ref: str, directories: tuple[str, ...] = ("",)
) -> tuple[tuple[str, ...], ...]:
    """Return plugin module names early-loaded by configured ``addopts`` at the red source.

    ``-p name`` loads a plugin module regardless of autoload settings, so a repository-local
    module named there decides collection exactly as a declared ``pytest_plugins`` entry does.
    """
    names: set[tuple[str, ...]] = set()
    for path, text in _pytest_configuration_sources(repo_root, source_ref, directories):
        for parts in _addopts_plugin_names(_pytest_ini_option(text, PurePosixPath(path).name, "addopts")):
            names.add(tuple(parts))
    return tuple(sorted(names))


def _root_name(expression: ast.expr) -> str | None:
    """Return the base name an attribute, subscript, or call chain is rooted at.

    Every check that asks "which name does this touch" resolves through this helper, so a
    wrapped form such as ``typing.__dict__["TYPE_CHECKING"]`` cannot evade a rule that its
    unwrapped equivalent triggers.
    """
    node: ast.expr = expression
    while True:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, (ast.Attribute, ast.Subscript)):
            node = node.value
            continue
        if isinstance(node, ast.Call):
            node = node.func
            continue
        return None


@functools.cache
def _symlink_paths_at_ref(repo_root: Path, source_ref: str) -> frozenset[str]:
    """Return every symlinked path committed at the red source.

    Collected in one traversal so any candidate path can be tested for a symlinked ancestor
    without another Git call per lookup.
    """
    result = _git(repo_root, "ls-tree", "-r", "--full-tree", source_ref)
    if result.returncode != 0:
        return frozenset()
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        metadata, _, path = line.partition("\t")
        if metadata.startswith("120000 "):
            paths.add(path.strip('"'))
    return frozenset(paths)


def _has_symlinked_ancestor(repo_root: Path, source_ref: str, path: str) -> bool:
    """Return whether a directory link stands between the repository root and this path."""
    symlinks = _symlink_paths_at_ref(repo_root, source_ref)
    if not symlinks:
        return False
    parent = PurePosixPath(path).parent
    while parent != PurePosixPath("."):
        if parent.as_posix() in symlinks:
            return True
        parent = parent.parent
    return False


def _safe_module_root(root: str, repo_root: Path) -> str | None:
    """Return a repository-relative module root, normalizing traversal within the repository.

    Pytest resolves the configured entry against the rootdir, so ``a/../b`` names the root
    ``b`` and must bind the plugins reachable through it. An absolute entry is resolved the
    same way and kept when it lands inside the checkout. Only an entry naming a tree outside
    the repository yields no root, because no Git ref can bind its files.
    """
    path = PurePosixPath(root)
    if path.is_absolute():
        try:
            contained = Path(root).resolve().relative_to(repo_root.resolve())
        except (OSError, ValueError):
            return None
        return "" if contained == Path() else contained.as_posix()
    parts: list[str] = []
    for part in path.parts:
        if part == ".":
            continue
        if part != "..":
            parts.append(part)
        elif parts:
            parts.pop()
        else:
            return None
    return "/".join(parts)


@functools.cache
def _pythonpath_roots(repo_root: Path, source_ref: str, directories: tuple[str, ...] = ("",)) -> tuple[str, ...]:
    """Return module roots configured through pytest ``pythonpath`` at the red source.

    Every configuration candidate is read rather than replicating pytest's inifile
    precedence, because binding a root pytest did not use only widens the proof inputs.
    """
    roots: set[str] = set()
    for path, text in _pytest_configuration_sources(repo_root, source_ref, directories):
        entries = _pythonpath_entries(_pytest_ini_option(text, PurePosixPath(path).name, "pythonpath"))
        # Pytest joins a relative entry to the declaring file's directory, so a nested
        # configuration names a root beneath itself rather than beneath the repository root.
        declaring_directory = PurePosixPath(path).parent
        roots.update(
            root
            for entry in entries
            if (root := _safe_module_root((declaring_directory / entry).as_posix(), repo_root)) is not None
        )
    return (*REPOSITORY_ROOT_MODULE_ROOTS, *sorted(roots - set(REPOSITORY_ROOT_MODULE_ROOTS)))


def _rooted_path(root: str, relative: str) -> str:
    """Return a repository-relative path beneath one module root."""
    return f"{root}/{relative}" if root else relative


def _python_module_target_paths(module_parts: Sequence[str], module_roots: Sequence[str]) -> set[str]:
    """Return the file and package targets for a repository-local module name under each root."""
    if not module_parts:
        return set()
    module_path = PurePosixPath(*module_parts)
    relatives = (module_path.with_suffix(".py").as_posix(), (module_path / "__init__.py").as_posix())
    return {_rooted_path(root, relative) for root in module_roots for relative in relatives}


def _python_module_paths(module_parts: Sequence[str], module_roots: Sequence[str]) -> set[str]:
    """Return possible paths for a repository-local module, including its parent packages."""
    paths = _python_module_target_paths(module_parts, module_roots)
    for parent_depth in range(1, len(module_parts)):
        parent_path = PurePosixPath(*module_parts[:parent_depth])
        paths.update(_rooted_path(root, (parent_path / "__init__.py").as_posix()) for root in module_roots)
    return paths


def _destructured_targets(target: ast.expr, value: ast.expr) -> list[tuple[str, ast.expr]]:
    """Return the names bound by one assignment target, unpacking literal sequences."""
    if isinstance(target, ast.Name):
        return [(target.id, value)]
    if (
        isinstance(target, (ast.List, ast.Tuple))
        and isinstance(value, (ast.List, ast.Tuple))
        and len(target.elts) == len(value.elts)
    ):
        return [
            binding
            for element, element_value in zip(target.elts, value.elts, strict=True)
            for binding in _destructured_targets(element, element_value)
        ]
    return []


def _static_condition(test: ast.AST, type_checking_names: set[str], typing_module_names: set[str]) -> bool | None:
    """Return a known branch condition used during module loading."""
    try:
        # Any literal has known truthiness, so `if 0:`, `if None:`, and `if ():` are as
        # static as `if False:`. A dynamic expression raises and stays runtime-unknown.
        return bool(ast.literal_eval(test))
    except (ValueError, TypeError):
        pass
    if isinstance(test, ast.Name) and test.id in type_checking_names:
        return False
    if (
        isinstance(test, ast.Attribute)
        and test.attr == "TYPE_CHECKING"
        and isinstance(test.value, ast.Name)
        and test.value.id in typing_module_names
    ):
        return False
    return None


def _simple_assignments(node: ast.AST) -> list[tuple[str, ast.expr]]:
    """Return name assignments that replace any previous binding."""
    if isinstance(node, ast.Assign):
        return [binding for target in node.targets for binding in _destructured_targets(target, node.value)]
    if isinstance(node, ast.AnnAssign) and node.value is not None:
        return _destructured_targets(node.target, node.value)
    return []


def _augmented_assignments(node: ast.AST) -> list[tuple[str, ast.expr]]:
    """Return name assignments that extend rather than replace a previous binding."""
    if isinstance(node, ast.AugAssign):
        return _destructured_targets(node.target, node.value)
    return []


def _target_names(target: ast.expr) -> list[str]:
    """Return every name bound by an assignment-like target expression."""
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.List, ast.Tuple)):
        return [name for element in target.elts for name in _target_names(element)]
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    return []


def _compound_binding_names(node: ast.AST) -> list[str]:
    """Return names bound by a compound statement target, whose value is not statically known.

    Loop, context-manager, exception, and match targets rebind a module constant without an
    evaluable right-hand side, so their names must be recorded rather than left stale.
    """
    if isinstance(node, (ast.AsyncFor, ast.For)):
        return _target_names(node.target)
    if isinstance(node, (ast.AsyncWith, ast.With)):
        return [
            name for item in node.items if item.optional_vars is not None for name in _target_names(item.optional_vars)
        ]
    if isinstance(node, ast.ExceptHandler):
        return [node.name] if node.name else []
    if isinstance(node, (ast.MatchAs, ast.MatchStar)):
        return [node.name] if node.name else []
    if isinstance(node, ast.MatchMapping):
        return [node.rest] if node.rest else []
    return []


def _name_bindings(node: ast.AST) -> list[tuple[str, ast.expr]]:
    """Return every module-level name binding made by one statement."""
    if isinstance(node, ast.NamedExpr):
        return _destructured_targets(node.target, node.value)
    return [*_simple_assignments(node), *_augmented_assignments(node)]


def _imported_type_checking_names(body: Sequence[ast.stmt]) -> set[str]:
    """Return names imported from ``typing.TYPE_CHECKING``."""
    return {
        alias.asname or alias.name
        for node in body
        if isinstance(node, ast.ImportFrom) and node.module == "typing"
        for alias in node.names
        if alias.name == "TYPE_CHECKING"
    }


def _imported_typing_module_names(body: Sequence[ast.stmt]) -> set[str]:
    """Return local names bound to the ``typing`` module."""
    return {
        alias.asname or "typing"
        for node in body
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "typing"
    }


def _other_import_names(nodes: Sequence[ast.AST]) -> set[str]:
    """Return local names bound by imports other than typing guards."""
    direct_imports = {
        alias.asname or alias.name.split(".")[0]
        for node in nodes
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name != "typing"
    }
    from_imports = {
        alias.asname or alias.name
        for node in nodes
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
        if node.module != "typing" or alias.name != "TYPE_CHECKING"
    }
    return direct_imports | from_imports


def _scope_header_nodes(node: ast.AST) -> list[ast.AST]:
    """Return the parts of a scope-defining statement that execute where the statement appears.

    Decorators, argument defaults, annotations, and base-class expressions run in the
    enclosing scope even though the body does not, so a walrus in a default can rebind a
    module name.
    """
    body = getattr(node, "body", [])
    body_nodes = body if isinstance(body, list) else [body]
    body_ids = {id(child) for child in cast(list[object], body_nodes)}
    return [child for child in ast.iter_child_nodes(node) if id(child) not in body_ids]


def _executable_scope_nodes(tree: ast.AST, *, include_class_bodies: bool = False) -> list[ast.AST]:
    """Return nodes that run at module load, without entering deferred scopes.

    Function and lambda bodies do not run where they appear, and a class body binds class
    attributes rather than module names, so neither counts as rebinding the typing guard.
    Their headers still execute in the enclosing scope and are traversed. A class body is
    included when the caller looks for module mutations rather than name bindings, because
    the body does execute during import.
    """
    deferred = (
        (ast.AsyncFunctionDef, ast.FunctionDef, ast.Lambda)
        if include_class_bodies
        else (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Lambda)
    )
    pending = list(ast.iter_child_nodes(tree))
    nodes: list[ast.AST] = []
    while pending:
        node = pending.pop()
        nodes.append(node)
        if isinstance(node, deferred):
            pending.extend(_scope_header_nodes(node))
            continue
        pending.extend(ast.iter_child_nodes(node))
    return nodes


def _guard_attribute_targets(node: ast.AST) -> list[str]:
    """Return module names whose ``TYPE_CHECKING`` attribute this statement writes."""
    targets: list[ast.expr] = []
    if isinstance(node, ast.Assign):
        targets = list(node.targets)
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        targets = [node.target]
    guarded: list[ast.expr] = [
        target for target in targets if isinstance(target, ast.Attribute) and target.attr == "TYPE_CHECKING"
    ]
    # A write through the module mapping reaches the same attribute the guard reads. The key
    # is matched so an ordinary `mapping[key] = value` does not read as a guard write, which
    # would make almost every module unverifiable.
    guarded.extend(
        target
        for target in targets
        if isinstance(target, ast.Subscript)
        and isinstance(target.slice, ast.Constant)
        and target.slice.value == "TYPE_CHECKING"
    )
    return [name for target in guarded for name in (_root_name(target.value),) if name is not None]


def _call_argument_names(node: ast.AST) -> list[str]:
    """Return module names handed to a call, which can rewrite any attribute they expose.

    ``setattr(typing, "TYPE_CHECKING", True)`` and ``vars(typing)["TYPE_CHECKING"] = True``
    both rewrite the guard without an attribute-assignment target, and resolving which calls
    do so would need the callee's body, so passing the module at all drops the guard.
    """
    if not isinstance(node, ast.Call):
        return []
    arguments = [*node.args, *(keyword.value for keyword in node.keywords)]
    # Nested expressions still hand the module over: `setattr([typing][0], ...)` reaches it.
    return [child.id for argument in arguments for child in ast.walk(argument) if isinstance(child, ast.Name)]


def _second_reference_names(nodes: Sequence[ast.AST]) -> set[str]:
    """Return names copied into another binding, through which a later write is invisible.

    ``alias = typing`` binds the same module object, so ``alias.TYPE_CHECKING = True``
    rewrites the guard that ``typing`` also names while recording only ``alias``.
    """
    return {value.id for node in nodes for _, value in _name_bindings(node) if isinstance(value, ast.Name)}


def _rewrites_attributes(nodes: Sequence[ast.AST]) -> bool:
    """Return whether these nodes rewrite an attribute through the ``setattr`` builtin."""
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setattr" for node in nodes
    )


def _globally_rebound_in(nodes: Sequence[ast.AST]) -> set[str]:
    """Return names both declared ``global`` and bound among the given nodes."""
    declared = {name for node in nodes if isinstance(node, ast.Global) for name in node.names}
    bound = {name for node in nodes for name, _ in _name_bindings(node)} | {
        name for node in nodes for name in _compound_binding_names(node)
    }
    return declared & bound


def _module_state_mutating_functions(tree: ast.AST) -> list[ast.AST]:
    """Return function definitions whose body can change module state this gate depends on.

    A ``global`` rebinding, a ``TYPE_CHECKING`` attribute write, a ``setattr`` rewrite, a
    call handed the typing module, or a ``pytest_plugins`` assignment inside a function all
    alter what pytest sees once that function runs. The guard is tracked by the name it is
    passed under rather than by the callee's name, because an aliased or wrapped rewriter
    defeats any match on ``setattr`` alone.
    """
    guard_names = _imported_typing_module_names(tree.body if isinstance(tree, ast.Module) else [])
    definitions: list[ast.AST] = []
    for node in ast.walk(tree):
        # A lambda body runs when it is called, exactly as a function body does.
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.Lambda)):
            continue
        body_nodes = list(ast.walk(node))
        mutates = (
            _globally_rebound_in(body_nodes)
            or any(_guard_attribute_targets(child) for child in body_nodes)
            or _rewrites_attributes(body_nodes)
            or any(name in guard_names for child in body_nodes for name in _call_argument_names(child))
            or any(name == "pytest_plugins" for child in body_nodes for name, _ in _name_bindings(child))
        )
        if mutates:
            definitions.append(node)
    return definitions


def _calls_during_module_load(tree: ast.AST) -> bool:
    """Return whether the module invokes anything while it loads.

    Applying a decorator invokes it during import even when the decorator expression is a
    bare name, which produces no ``ast.Call`` node of its own.
    """
    nodes = _executable_scope_nodes(tree, include_class_bodies=True)
    return any(isinstance(node, ast.Call) for node in nodes) or any(
        getattr(node, "decorator_list", ()) for node in nodes
    )


def _writes_module_namespace(tree: ast.AST) -> bool:
    """Return whether the module rewrites its own namespace mapping while loading.

    ``globals()["pytest_plugins"] = [...]`` creates exactly the attribute pytest reads, but
    through a subscript whose base is a call rather than a name, so no binding is recorded.
    """
    return any(
        isinstance(target, ast.Subscript)
        and isinstance(target.value, ast.Call)
        and isinstance(target.value.func, ast.Name)
        and target.value.func.id in {"globals", "vars"}
        for node in _executable_scope_nodes(tree, include_class_bodies=True)
        for target in _write_targets(node)
    )


def _unverifiable_module_state(tree: ast.AST) -> bool:
    """Return whether an invoked function could change module state before pytest reads it.

    Resolving which function a module-load call reaches would require following aliases,
    wrappers, decorators, and transitive calls, and any partial resolution silently accepts
    the shapes it cannot follow. When a module both defines a state-mutating function and
    calls anything while loading, the resulting state is therefore treated as unknown. A
    module that writes its own namespace mapping is unverifiable on the same grounds.
    """
    if _writes_module_namespace(tree):
        return True
    return bool(_module_state_mutating_functions(tree)) and _calls_during_module_load(tree)


def _global_rebound_names(tree: ast.AST) -> set[str]:
    """Return names a ``global`` declaration rebinds while the module loads.

    A class body executes during import, so a ``global`` binding there always applies.
    Bindings inside function bodies are covered by ``_unverifiable_module_state`` instead,
    because whether such a body runs cannot be decided by inspecting call names.
    """
    return _globally_rebound_in(_executable_scope_nodes(tree, include_class_bodies=True))


def _nodes_before(nodes: Sequence[ast.AST], before_line: int | None) -> list[ast.AST]:
    """Return the nodes that appear before a source line, or all of them when unbounded."""
    if before_line is None:
        return list(nodes)
    return [node for node in nodes if getattr(node, "lineno", 0) < before_line]


def _verified_type_checking_bindings(tree: ast.AST, before_line: int | None = None) -> tuple[set[str], set[str]]:
    """Return unrebound names imported from the typing module.

    A rebinding only invalidates a guard used after it, so ``before_line`` bounds the scan to
    statements that already ran; an unbounded call sees the whole module.

    Rebinding is detected across every node that executes at module load, including loop,
    context-manager, exception, and match targets, so a nested but reachable rebinding
    replaces the guard while a name bound only inside a function, lambda, or class body
    does not — unless a ``global`` declaration makes that binding module-scoped. A module
    guard is also dropped when its ``TYPE_CHECKING`` attribute is written directly or when the
    module itself is handed to a call that could rewrite it, and no guard is trusted at all
    when an invoked function could change module state. A guard is trusted only when imported
    directly at module scope.
    """
    body = tree.body if isinstance(tree, ast.Module) else []
    if _unverifiable_module_state(tree):
        return set(), set()
    nodes = _nodes_before(_executable_scope_nodes(tree), before_line)
    executing_nodes = _nodes_before(_executable_scope_nodes(tree, include_class_bodies=True), before_line)
    rebound_names = (
        _other_import_names(nodes)
        | {name for node in nodes for name, _ in _name_bindings(node)}
        | {name for node in nodes for name in _compound_binding_names(node)}
        | _globally_rebound_in(executing_nodes)
    )
    mutated_guard_names = (
        {name for node in executing_nodes for name in _guard_attribute_targets(node)}
        | {name for node in executing_nodes for name in _call_argument_names(node)}
        | _second_reference_names(executing_nodes)
    )
    return (
        _imported_type_checking_names(body) - rebound_names,
        _imported_typing_module_names(body) - rebound_names - mutated_guard_names,
    )


def _module_scope_nodes(
    tree: ast.AST, *, include_class_bodies: bool = False, include_deferred_scopes: bool = False
) -> list[ast.AST]:
    """Return executable module nodes without entering deferred function scopes.

    A caller collecting imports enters them anyway: a function invoked while the module
    loads executes its imports at import time, and one invoked from a fixture executes them
    while the selected test runs, so either way the imported file decides the outcome.
    Static branch pruning still applies inside those bodies, so a guarded type-only import
    stays unbound.
    """
    pending = list(reversed(list(ast.iter_child_nodes(tree))))
    nodes: list[ast.AST] = []
    while pending:
        node = pending.pop()
        nodes.append(node)
        deferred_scope = (
            isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.Lambda)) and not include_deferred_scopes
        )
        excluded_class_scope = isinstance(node, ast.ClassDef) and not include_class_bodies
        if deferred_scope or excluded_class_scope:
            # The body does not run here, but decorators, defaults, and bases do.
            pending.extend(reversed(_scope_header_nodes(node)))
            continue
        if (
            isinstance(node, ast.If)
            and (condition := _static_condition(node.test, *_verified_type_checking_bindings(tree, node.lineno)))
            is not None
        ):
            pending.extend(reversed(node.body if condition else node.orelse))
            continue
        pending.extend(reversed(list(ast.iter_child_nodes(node))))
    return nodes


def _conditional_assignment_ids(tree: ast.AST) -> set[int]:
    """Return assignments under branches whose runtime outcome is unknown."""
    conditional_ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            if _static_condition(node.test, *_verified_type_checking_bindings(tree, node.lineno)) is not None:
                continue
            branch_nodes: tuple[ast.stmt, ...] = (*node.body, *node.orelse)
        elif isinstance(
            node, (ast.AsyncFor, ast.AsyncWith, ast.For, ast.Match, ast.Try, ast.TryStar, ast.While, ast.With)
        ):
            branch_nodes = tuple(child for child in ast.iter_child_nodes(node) if isinstance(child, ast.stmt))
        else:
            continue
        conditional_ids.update(
            id(descendant)
            for branch_node in branch_nodes
            for descendant in ast.walk(branch_node)
            if _name_bindings(descendant)
        )
    return conditional_ids


def _resolved_literals(value_node: ast.expr, constants: dict[str, list[object]]) -> list[object]:
    """Resolve a literal expression or all possible values of a bound name.

    An expression that cannot be evaluated yields the unresolved marker so callers fail
    closed instead of silently treating an active declaration as absent.
    """
    if isinstance(value_node, ast.Name):
        return constants.get(value_node.id, [UNRESOLVED_PLUGIN_VALUE])
    try:
        return [ast.literal_eval(value_node)]
    except (ValueError, TypeError):
        return [UNRESOLVED_PLUGIN_VALUE]


def _plugin_parts(value: object) -> list[list[str]]:
    """Return normalized module parts from a supported plugin declaration value."""
    declarations = [value] if isinstance(value, str) else value
    if not isinstance(declarations, (list, tuple)):
        return []
    return [
        plugin_name.strip().split(".")
        for declaration in declarations
        if isinstance(declaration, str)
        for plugin_name in declaration.split(",")
        if plugin_name.strip()
    ]


def _record_constant(constants: dict[str, list[object]], name: str, value: object, *, extends: bool) -> None:
    """Record one possible value of a module constant, keeping earlier possibilities when they survive."""
    if extends:
        constants.setdefault(name, []).append(value)
    else:
        constants[name] = [value]


def _import_binding_names(node: ast.AST) -> list[str]:
    """Return names bound by one import statement, whose values are not statically known."""
    if isinstance(node, ast.Import):
        return [alias.asname or alias.name.split(".")[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        return [alias.asname or alias.name for alias in node.names if alias.name != "*"]
    return []


def _mutation_target_names(target: ast.expr) -> list[str]:
    """Return the name a subscript or attribute write changes in place.

    The base is resolved through wrapper chains, so ``typing.__dict__["TYPE_CHECKING"]``
    reports ``typing`` exactly as a direct attribute write does.
    """
    if isinstance(target, (ast.Attribute, ast.Subscript)):
        return [name for name in (_root_name(target.value),) if name is not None]
    return []


def _write_targets(node: ast.AST) -> list[ast.expr]:
    """Return the targets of one assignment or deletion statement."""
    if isinstance(node, (ast.Assign, ast.Delete)):
        return list(node.targets)
    if isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        return [node.target]
    return []


def _mutated_name_targets(node: ast.AST) -> list[str]:
    """Return names this statement mutates in place, whose resulting value is unknown.

    A method call, a subscript or attribute write, and a deletion all change the object a
    name is bound to without rebinding the name itself, so a binding copied from it earlier
    still observes the change.
    """
    names: list[str] = []
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and isinstance(child.func.value, ast.Name)
        ):
            names.append(child.func.value.id)
        if isinstance(child, ast.AugAssign) and isinstance(child.target, ast.Name):
            # `x += [...]` extends a list in place, so every alias observes it.
            names.append(child.target.id)
        names.extend(name for target in _write_targets(child) for name in _mutation_target_names(target))
    return names


def _aliased_names(constants: dict[str, list[object]], name: str) -> set[str]:
    """Return every name recorded as the same mutable object as this one.

    Assigning one name to another copies the reference, so mutating either changes both.
    Only mutable containers are compared by identity, because equal immutable values may be
    interned and share identity without sharing a binding.
    """
    mutated = [value for value in constants.get(name, []) if isinstance(value, (dict, list, set))]
    return {
        other for other, values in constants.items() if any(value is target for value in values for target in mutated)
    }


def _received_call_argument_names(node: ast.AST) -> list[str]:
    """Return names handed to any call within this statement.

    An unbound-method form such as ``list.append(P, ...)`` mutates the argument rather than
    the receiver, so a declaration reached this way is no more knowable than one mutated
    through its own method.
    """
    return [name for child in ast.walk(node) for name in _call_argument_names(child)]


def _has_star_import(node: ast.AST) -> bool:
    """Return whether one statement imports an unknown set of names."""
    return isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names)


def _pytest_plugin_names(tree: ast.AST) -> list[list[str]]:
    """Return statically declared ``pytest_plugins`` module names.

    Only the final possible binding is reported, because pytest reads the attribute after
    the module is imported, so an assignment that a later one overwrites never loads.
    Raises ``ValueError('stale-red-proof')`` when that binding cannot be resolved, because
    an unverifiable plugin set cannot prove the retained failure is still current. An
    imported binding, including one a star import may supply, is treated as unresolved
    since its value lives in another module.
    """
    if _unverifiable_module_state(tree):
        raise ValueError("stale-red-proof")
    if "pytest_plugins" in _global_rebound_names(tree):
        # An executing class body created the module attribute pytest reads, outside the
        # module-scope traversal that resolves values.
        raise ValueError("stale-red-proof")
    conditional_assignment_ids = _conditional_assignment_ids(tree)
    constants: dict[str, list[object]] = {}
    # Chained targets share one right-hand side node and therefore one runtime object, so the
    # evaluation is memoized per node to keep alias identity intact.
    evaluated: dict[int, list[object]] = {}
    for node in _module_scope_nodes(tree):
        for name, assigned_node in _name_bindings(node):
            extends = id(node) in conditional_assignment_ids or bool(_augmented_assignments(node))
            if id(assigned_node) not in evaluated:
                evaluated[id(assigned_node)] = _resolved_literals(assigned_node, constants)
            for value in evaluated[id(assigned_node)]:
                _record_constant(constants, name, value, extends=extends)
                extends = True
        for name in _compound_binding_names(node):
            _record_constant(constants, name, UNRESOLVED_PLUGIN_VALUE, extends=True)
        for name in _import_binding_names(node):
            _record_constant(constants, name, UNRESOLVED_PLUGIN_VALUE, extends=False)
        for name in (*_mutated_name_targets(node), *_received_call_argument_names(node)):
            for aliased in _aliased_names(constants, name):
                _record_constant(constants, aliased, UNRESOLVED_PLUGIN_VALUE, extends=True)
        if _has_star_import(node):
            _record_constant(constants, "pytest_plugins", UNRESOLVED_PLUGIN_VALUE, extends=True)
    plugin_names: list[list[str]] = []
    for value in constants.get("pytest_plugins", []):
        if value is UNRESOLVED_PLUGIN_VALUE:
            raise ValueError("stale-red-proof")
        plugin_names.extend(_plugin_parts(value))
    return plugin_names


def _deferred_scopes_are_reachable(tree: ast.AST, current_path: str) -> bool:
    """Report whether a module's deferred bodies run during the pytest session.

    Pytest invokes test and fixture bodies during the run, so their imports always execute.
    Only a package initializer needs an import-time call to reach one of its own functions.
    """
    is_package_initializer = PurePosixPath(current_path).name == "__init__.py"
    return not is_package_initializer or _calls_during_module_load(tree)


def _literal_module_candidates(tree: ast.AST, current_path: str) -> list[list[str]]:
    """Return module names spelled as string literals in a reachable body.

    A dynamic import names its target in data rather than in the callee, so the mechanism is
    not what identifies it: ``importlib.import_module``, ``__import__``, an alias, a wrapper, or
    a name read out of a list all execute the same module. Resolving the literal itself covers
    every such spelling without matching a mechanism by name — the matching that aliasing and
    indirection defeat.

    Two positions narrow the literals worth reading as names. It must be handed to a call,
    because a string merely written down is not loaded by anyone — a ``pytest_plugins`` value in
    a scope pytest ignores names a module that is never imported. And it must be dotted, because
    a bare word is ordinary prose, the directory component in ``Path("src")``; reading those as
    imports binds unrelated files and fails valid proofs with no legible cause. The cost is that
    a single-part dynamic target resting directly on an import root stays unbound; that gap is
    bounded, while prose is not. Because even a handed-over dotted literal may be prose, the
    caller keeps only the names whose module exists at the red source.
    """
    names: list[list[str]] = []
    reachable_bodies = _deferred_scopes_are_reachable(tree, current_path)
    for node in _module_scope_nodes(tree, include_class_bodies=True, include_deferred_scopes=reachable_bodies):
        handed_over = _handed_over_expressions(node)
        for value in itertools.chain.from_iterable(_literal_strings(argument) for argument in handed_over):
            parts = value.split(".")
            if len(parts) > 1 and all(part.isidentifier() for part in parts):
                names.append(parts)
    return names


def _handed_over_expressions(node: ast.AST) -> list[ast.expr]:
    """Return the expressions a statement hands to something that consumes them.

    A call receives its arguments and a loop or comprehension receives what it iterates. A value
    in either position is used, unlike one that is only bound to a name, so this is the position
    that separates a literal naming something the run reads from a literal written down.
    """
    if isinstance(node, ast.Call):
        return [*node.args, *(keyword.value for keyword in node.keywords)]
    if isinstance(node, (ast.AsyncFor, ast.For)):
        return [node.iter]
    if isinstance(node, ast.comprehension):
        return [node.iter]
    return []


def _literal_strings(expression: ast.expr) -> list[str]:
    """Return the string literals an expression hands over, including through a literal group.

    A loader is as often given a collection of names as a single one, and the elements of a
    literal sequence are handed over just as directly as a bare argument is.
    """
    if isinstance(expression, ast.Constant):
        return [expression.value] if isinstance(expression.value, str) else []
    if isinstance(expression, (ast.List, ast.Tuple, ast.Set)):
        return [value for element in expression.elts for value in _literal_strings(element)]
    if isinstance(expression, ast.Dict):
        return [value for element in expression.values for value in _literal_strings(element)]
    return []


def _import_module_names(tree: ast.AST, current_path: str) -> list[list[str]]:
    """Return imported module names, including relative import candidates."""
    current_package = list(PurePosixPath(current_path).parent.parts)
    module_names: list[list[str]] = []
    reachable_bodies = _deferred_scopes_are_reachable(tree, current_path)
    for node in _module_scope_nodes(tree, include_class_bodies=True, include_deferred_scopes=reachable_bodies):
        if isinstance(node, ast.Import):
            module_names.extend(alias.name.split(".") for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            parent_parts = current_package[: max(len(current_package) - node.level + 1, 0)] if node.level else []
            base_parts = parent_parts + (node.module.split(".") if node.module else [])
            module_names.append(base_parts)
            module_names.extend(base_parts + alias.name.split(".") for alias in node.names if alias.name != "*")
    return module_names


@functools.cache
def _python_tree_at_ref(repo_root: Path, source_ref: str, path: str) -> ast.AST | None:
    """Parse committed Python source without consulting mutable worktree bytes.

    Source is parsed as bytes so a PEP 263 encoding declaration is honoured rather than
    forcing a UTF-8 decode that would abort the gate on legally encoded modules. Results are
    cached because the content of a path at an immutable ref cannot change during one run.

    The Git mode is checked independently of parsing, because a link text such as
    ``real_conftest.py`` is itself valid Python and would otherwise parse as an attribute
    expression while pytest executes the target instead.
    """
    result = _git_bytes(repo_root, "show", f"{source_ref}:{path}")
    if result.returncode != 0 or len(result.stdout) > MAX_TEST_BLOB_BYTES:
        return None
    if not _test_path_is_regular_at_ref(repo_root, source_ref, path):
        return None
    try:
        return ast.parse(result.stdout)
    except (SyntaxError, ValueError):
        return None


def _discovered_rooted_paths(
    module_names: Sequence[Sequence[str]], module_roots: Sequence[str]
) -> set[tuple[str, str]]:
    """Return every (module root, repository path) candidate for discovered module names."""
    return {
        (root, path)
        for module_parts in module_names
        for root in module_roots
        for path in _python_module_paths(module_parts, (root,))
    }


def _joined_path_literal(expression: ast.expr) -> str | None:
    """Return the repository-relative path a chain of ``/`` joins spells, if it is fully literal.

    ``REPO_ROOT / "tests" / "data" / "case.json"`` names a file as directly as a single string
    does; the root the chain starts from is dropped because a path built inside the checkout is
    only bindable relative to it.
    """
    parts: list[str] = []
    node: ast.expr = expression
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        if not isinstance(node.right, ast.Constant) or not isinstance(node.right.value, str):
            return None
        parts.insert(0, node.right.value)
        node = node.left
    return "/".join(parts) if parts else None


def _literal_path_candidates(tree: ast.AST, current_path: str) -> list[str]:
    """Return repository-relative paths a reachable body names as literals.

    A harness reads a data file the same way it names a module: by handing a literal to a call,
    or by joining literals onto a path root. Both are resolved, and nothing else is, because a
    path assembled at runtime — ``tmp_path / name`` — cannot be bound to a committed file and
    failing closed on it would reject every proof in a repository that uses temporary
    directories, which is every repository.
    """
    candidates: list[str] = []
    reachable_bodies = _deferred_scopes_are_reachable(tree, current_path)
    for node in _module_scope_nodes(tree, include_class_bodies=True, include_deferred_scopes=reachable_bodies):
        handed_over = _handed_over_expressions(node)
        candidates.extend(itertools.chain.from_iterable(_literal_strings(argument) for argument in handed_over))
        if isinstance(node, ast.BinOp) and (joined := _joined_path_literal(node)) is not None:
            candidates.append(joined)
    return [candidate.strip("/") for candidate in candidates if candidate.strip("/")]


def _harness_directories(selector_paths: Sequence[str]) -> tuple[str, ...]:
    """Return the top-level directories the selected tests live in.

    Data beneath them belongs to the harness, so a red-to-green change may not edit it. Anything
    outside is what the change is expected to edit — production source, documentation, packaging
    — which is why ordinary imports already stop at the repository root rather than following
    into it. A selector sitting at the repository root contributes no directory, so it widens
    nothing.
    """
    return tuple(sorted({parts[0] for path in selector_paths if (parts := PurePosixPath(path).parts[:-1])}))


def _is_harness_path(path: str, harness_directories: Sequence[str]) -> bool:
    """Return whether a path names harness data rather than something the fix may change."""
    if path in GOVERNED_PRODUCTION_FILES or path.startswith(GOVERNED_PRODUCTION_PREFIXES):
        return False
    return any(path.startswith(f"{directory}/") for directory in harness_directories)


def _referenced_data_paths(
    repo_root: Path, source_ref: str, python_paths: Sequence[str], selector_paths: Sequence[str]
) -> set[str]:
    """Return committed harness data the resolved Python proof inputs read by literal path.

    Data files import nothing, so this pass runs once over the already-resolved Python inputs
    rather than participating in their traversal.
    """
    harness_directories = _harness_directories(selector_paths)
    if not harness_directories:
        return set()
    return {
        candidate
        for path in python_paths
        if (tree := _python_tree_at_ref(repo_root, source_ref, path)) is not None
        for candidate in _literal_path_candidates(tree, path)
        if _is_harness_path(candidate, harness_directories)
        and _test_path_exists_at_ref(repo_root, source_ref, candidate)
        and _test_path_is_regular_at_ref(repo_root, source_ref, candidate)
    }


def _committed_module_names(
    module_names: Sequence[Sequence[str]], module_roots: Sequence[str], repo_root: Path, source_ref: str
) -> list[list[str]]:
    """Return the module names whose own file is committed at the red source.

    An ordinary ``import`` statement is proof that its target is imported, so its absent
    candidates are bound as absent and a later addition invalidates the proof. A name merely
    guessed from a string literal carries no such proof, so a name is kept only once the module
    it points at exists. The test is the module's own file rather than any of the candidate
    paths, because a parent package's ``__init__.py`` can exist while the named module does not.
    """
    return [
        list(module_parts)
        for module_parts in module_names
        if any(
            _test_path_exists_at_ref(repo_root, source_ref, path)
            for path in _python_module_target_paths(module_parts, module_roots)
        )
    ]


def _module_relative_path(path: str, module_root: str) -> str:
    """Return a path relative to the module root it was discovered under."""
    prefix = f"{module_root}/"
    return path.removeprefix(prefix) if module_root and path.startswith(prefix) else path


def _import_roots(module_root: str) -> tuple[str, ...]:
    """Return the roots an import inside a module discovered under one root may resolve against."""
    return ("",) if not module_root else ("", module_root)


def _imported_python_paths(
    repo_root: Path,
    source_ref: str,
    seeds: Sequence[tuple[str, bool, str]],
    *,
    plugin_module_roots: Sequence[str],
) -> set[str]:
    """Return transitive repository-local Python imports used by pytest inputs.

    Each traversal entry carries the module root it was discovered under, so a plugin loaded
    from a configured ``pythonpath`` root resolves its own imports against that root as
    pytest does. An input discovered at the repository root keeps repository-root resolution,
    because resolving ordinary test imports through a root such as ``src`` would bind
    governed production modules that a red-to-green change is expected to edit.
    """
    pending = list(seeds)
    traversed_paths: set[tuple[str, bool, str]] = set()
    imported_paths: set[str] = set()
    while pending:
        traversal = pending.pop()
        if traversal in traversed_paths:
            continue
        traversed_paths.add(traversal)
        current_path, inspect_pytest_plugins, module_root = traversal
        tree = _python_tree_at_ref(repo_root, source_ref, current_path)
        if tree is None:
            # An existing input that is neither parseable nor a plain absent candidate cannot
            # be verified: a symlink executes bytes this gate never inspected.
            if _test_path_exists_at_ref(repo_root, source_ref, current_path):
                raise ValueError("stale-red-proof")
            continue
        import_roots = _import_roots(module_root)
        relative_path = _module_relative_path(current_path, module_root)
        ordinary_rooted = _discovered_rooted_paths(_import_module_names(tree, relative_path), import_roots)
        ordinary_rooted |= _discovered_rooted_paths(
            _committed_module_names(
                _literal_module_candidates(tree, relative_path), import_roots, repo_root, source_ref
            ),
            import_roots,
        )
        plugin_names = _pytest_plugin_names(tree) if inspect_pytest_plugins else []
        plugin_rooted = _discovered_rooted_paths(plugin_names, plugin_module_roots)
        plugin_targets = {
            (root, path)
            for module_parts in plugin_names
            for root in plugin_module_roots
            for path in _python_module_target_paths(module_parts, (root,))
        }
        for _, candidate in sorted(ordinary_rooted | plugin_rooted):
            if not _test_path_exists_at_ref(repo_root, source_ref, candidate) and _has_symlinked_ancestor(
                repo_root, source_ref, candidate
            ):
                # Python follows the directory link; Git records the link, not the target tree.
                raise ValueError("stale-red-proof")
        imported_paths.update(path for _, path in ordinary_rooted | plugin_rooted)
        pending.extend(
            (imported_path, False, root)
            for root, imported_path in ordinary_rooted
            if _test_path_exists_at_ref(repo_root, source_ref, imported_path)
        )
        pending.extend(
            (plugin_path, (root, plugin_path) in plugin_targets, root)
            for root, plugin_path in plugin_rooted
            if _test_path_exists_at_ref(repo_root, source_ref, plugin_path)
        )
    return imported_paths


def _validate_retained_red_junit(red_proof_path: Path, report: dict[str, object]) -> None:
    """Bind the released report to a retained failing JUnit artifact."""
    execution_proof = _validated_execution_proof(report)
    expected_digest = execution_proof.get("junit_digest")
    junit_path = red_proof_path.with_suffix(".xml")
    try:
        payload = junit_path.read_bytes()
        root = ElementTree.fromstring(payload)
    except (OSError, ElementTree.ParseError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    actual_digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    if expected_digest != actual_digest or (root.find(".//failure") is None and root.find(".//error") is None):
        raise ValueError("prior-red-proof-invalid")
    junit_selectors = {
        str(property_node.get("value"))
        for property_node in root.findall(".//property[@name='specfact.selector']")
        if property_node.get("value") is not None
    }
    if junit_selectors != set(_validated_selectors(execution_proof)):
        raise ValueError("prior-red-proof-invalid")


def _artifact_is_tracked(repo_root: Path, artifact_path: Path) -> bool:
    """Return whether an artifact is controlled by the pull-request Git tree."""
    try:
        relative_path = artifact_path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    return _git(repo_root, "ls-files", "--error-unmatch", "--", relative_path.as_posix()).returncode == 0


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    return _git(repo_root, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def _parse_name_status_records(payload: bytes) -> list[str] | None:
    """Return every path from a NUL-delimited Git name-status stream."""
    records = payload.split(b"\0")
    if records.pop() != b"":
        return None
    paths: list[str] = []
    record_index = 0
    while record_index < len(records):
        status = records[record_index]
        record_index += 1
        if record_index >= len(records):
            return None
        paths.append(records[record_index].decode("utf-8", errors="surrogateescape"))
        record_index += 1
        if status.startswith((b"R", b"C")):
            if record_index >= len(records):
                return None
            paths.append(records[record_index].decode("utf-8", errors="surrogateescape"))
            record_index += 1
    return paths


def _changed_paths_in_history(
    repo_root: Path, start_ref: str, end_ref: str, *, merge_parent: int = 2
) -> list[str] | None:
    """Return paths touched by every commit, including changes later restored."""
    revisions = _git(repo_root, "rev-list", "--reverse", f"{start_ref}..{end_ref}")
    if revisions.returncode:
        return None
    paths: list[str] = []
    for revision in revisions.stdout.splitlines():
        parents = _git(repo_root, "rev-list", "--parents", "-n", "1", revision).stdout.split()
        comparison_ref = f"{revision}^{merge_parent}" if len(parents) > 2 else f"{revision}^"
        result = _git_bytes(repo_root, "diff", "--name-status", "-z", "--find-renames", comparison_ref, revision)
        commit_paths = _parse_name_status_records(result.stdout) if result.returncode == 0 else None
        if commit_paths is None:
            return None
        paths.extend(commit_paths)
    return paths


def _red_source_precedes_final(repo_root: Path, base_ref: str, source_ref: str, final_ref: str) -> bool:
    """Require the current base, red source, and final source to form one strict chain."""
    resolved_base = _git(repo_root, "rev-parse", base_ref)
    return (
        GIT_OBJECT_PATTERN.fullmatch(final_ref) is not None
        and resolved_base.returncode == 0
        and source_ref != resolved_base.stdout.strip()
        and source_ref != final_ref
        and _is_ancestor(repo_root, base_ref, source_ref)
        and _is_ancestor(repo_root, source_ref, final_ref)
    )


def _has_governed_production_path(paths: Sequence[str]) -> bool:
    return any(path in GOVERNED_PRODUCTION_FILES or path.startswith(GOVERNED_PRODUCTION_PREFIXES) for path in paths)


@functools.cache
def _test_path_exists_at_ref(repo_root: Path, source_ref: str, test_path: str) -> bool:
    """Return whether a path exists at an immutable ref, caching the answer for the run."""
    return _git(repo_root, "cat-file", "-e", f"{source_ref}:{test_path}").returncode == 0


@functools.cache
def _test_path_is_regular_at_ref(repo_root: Path, source_ref: str, test_path: str) -> bool:
    """Reject symlink selectors because pytest follows bytes not bound by their Git blob."""
    result = _git(repo_root, "ls-tree", source_ref, "--", test_path)
    return result.returncode == 0 and result.stdout.startswith(("100644 blob ", "100755 blob "))


def _blob_digest_at_ref(repo_root: Path, source_ref: str, test_path: str) -> str | None:
    """Return the digest of committed test bytes without consulting the worktree."""
    size_result = _git(repo_root, "cat-file", "-s", f"{source_ref}:{test_path}")
    try:
        blob_size = int(size_result.stdout.strip())
    except ValueError:
        return None
    if size_result.returncode != 0 or blob_size > MAX_TEST_BLOB_BYTES:
        return None
    result = _git_bytes(repo_root, "show", f"{source_ref}:{test_path}")
    return f"sha256:{hashlib.sha256(result.stdout).hexdigest()}" if result.returncode == 0 else None


def _valid_report_digests(report: dict[str, object]) -> bool:
    """Return whether the report binds both governed input digests."""
    return all(
        isinstance(report.get(field), str) and DIGEST_PATTERN.fullmatch(cast(str, report[field])) is not None
        for field in ("mapping_digest", "plan_digest")
    )


def _validated_toolchain_identity(value: object) -> None:
    """Reject an incomplete toolchain identity."""
    if not isinstance(value, dict):
        raise ValueError("prior-red-proof-invalid")
    identity = cast(dict[str, object], value)
    if set(identity) != {"runner", "python", "pytest"} or not all(
        isinstance(item, str) and item for item in identity.values()
    ):
        raise ValueError("prior-red-proof-invalid")


def _validated_test_file_digests(value: object, selector_paths: Sequence[str]) -> dict[str, object]:
    """Return selector-complete test digests or reject the proof."""
    if not isinstance(value, dict):
        raise ValueError("prior-red-proof-invalid")
    digests = cast(dict[str, object], value)
    if set(digests) != set(selector_paths):
        raise ValueError("prior-red-proof-invalid")
    return digests


def _validate_execution_bindings(
    report: dict[str, object], repo_root: Path, base_ref: str, source_ref: str, selector_paths: Sequence[str]
) -> None:
    """Verify every source, test, plan, and toolchain binding required by the red-proof contract."""
    execution_proof = _validated_execution_proof(report)
    source_tree = execution_proof.get("source_tree")
    merge_base = execution_proof.get("merge_base")
    test_file_digests = _validated_test_file_digests(execution_proof.get("test_file_digests"), selector_paths)
    _validated_toolchain_identity(execution_proof.get("toolchain_identity"))
    actual_tree = _git(repo_root, "rev-parse", f"{source_ref}^{{tree}}").stdout.strip()
    actual_merge_base = _git(repo_root, "merge-base", base_ref, source_ref).stdout.strip()
    if not _valid_report_digests(report) or source_tree != actual_tree or merge_base != actual_merge_base:
        raise ValueError("prior-red-proof-invalid")
    for test_path in selector_paths:
        recorded_digest = test_file_digests.get(test_path)
        if not isinstance(recorded_digest, str) or recorded_digest != _blob_digest_at_ref(
            repo_root, source_ref, test_path
        ):
            raise ValueError("prior-red-proof-invalid")


def _proof_inputs(repo_root: Path, source_ref: str, selector_paths: Sequence[str]) -> set[str]:
    """Return every committed path whose change after the red source would invalidate the proof.

    Selectors are resolved together so their shared conftest, initializer, and import graph is
    traversed once for the whole proof. Plugins early-loaded through ``-p`` are seeded alongside
    them, because pytest loads those modules too, whether the option comes from configured
    ``addopts`` or from the command the executor builds for every run.
    """
    pytest_inputs = {
        path for test_path in selector_paths for path in (test_path, *_ancestor_file_paths(test_path, "conftest.py"))
    }
    initializer_inputs = {
        initializer for path in pytest_inputs for initializer in _ancestor_file_paths(path, "__init__.py")
    }
    traversal_inputs = pytest_inputs | initializer_inputs
    configuration_directories = _configuration_directories(selector_paths)
    plugin_module_roots = _pythonpath_roots(repo_root, source_ref, configuration_directories)
    addopts_names = (
        *_addopts_plugin_module_names(repo_root, source_ref, configuration_directories),
        *EXECUTOR_PLUGIN_NAMES,
    )
    addopts_rooted = _discovered_rooted_paths(addopts_names, plugin_module_roots)
    addopts_targets = {
        (root, path)
        for module_parts in addopts_names
        for root in plugin_module_roots
        for path in _python_module_target_paths(module_parts, (root,))
    }
    seeds = [(path, path in pytest_inputs, "") for path in sorted(traversal_inputs)]
    seeds += [(path, (root, path) in addopts_targets, root) for root, path in sorted(addopts_rooted)]
    python_inputs = {
        *traversal_inputs,
        *(path for _, path in addopts_rooted),
        *_imported_python_paths(repo_root, source_ref, seeds, plugin_module_roots=plugin_module_roots),
    }
    return {
        *python_inputs,
        *_configuration_candidate_paths(configuration_directories),
        *_referenced_data_paths(repo_root, source_ref, sorted(python_inputs), selector_paths),
    }


@beartype
@ensure(
    lambda result: all(
        finding in {"tdd-order-unproven", "stale-red-proof", "prior-red-proof-invalid"} for finding in result
    )
)
def validate_prior_red_proof(red_proof_path: Path, repo_root: Path, *, base_ref: str, final_ref: str) -> list[str]:
    """Return deterministic findings when a red report cannot prove failing-first order."""
    if _artifact_is_tracked(repo_root, red_proof_path) or _artifact_is_tracked(
        repo_root, red_proof_path.with_suffix(".xml")
    ):
        return ["prior-red-proof-invalid"]
    try:
        report = _read_red_proof(red_proof_path)
        _validate_retained_red_junit(red_proof_path, report)
        source_ref, selector_paths = _selector_paths(report)
    except ValueError as error:
        return [str(error)]
    if not _red_source_precedes_final(repo_root, base_ref, source_ref, final_ref):
        return ["tdd-order-unproven"]
    try:
        _validate_execution_bindings(report, repo_root, base_ref, source_ref, selector_paths)
    except ValueError as error:
        return [str(error)]
    paths_before_red = _changed_paths_in_history(repo_root, base_ref, source_ref)
    if paths_before_red is None:
        return ["tdd-order-unproven"]
    if _has_governed_production_path(paths_before_red):
        return ["tdd-order-unproven"]
    paths_after_red = _changed_paths_in_history(repo_root, source_ref, final_ref, merge_parent=1)
    if paths_after_red is None:
        return ["tdd-order-unproven"]
    for test_path in selector_paths:
        if not _test_path_exists_at_ref(repo_root, source_ref, test_path) or not _test_path_is_regular_at_ref(
            repo_root, source_ref, test_path
        ):
            return ["prior-red-proof-invalid"]
    try:
        proof_inputs = _proof_inputs(repo_root, source_ref, selector_paths)
    except ValueError as error:
        return [str(error)]
    if not proof_inputs.isdisjoint(paths_after_red):
        return ["stale-red-proof"]
    return []


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prior-red-proof", type=Path, required=True, help="Runner-produced red reconciliation report."
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository containing both Git sources.")
    parser.add_argument(
        "--base-ref", required=True, help="Pull-request base ref used to detect pre-red production changes."
    )
    parser.add_argument("--final-ref", required=True, help="Final source commit under reconciliation.")
    return parser


@beartype
@ensure(lambda result: result in {0, 1})
def main(argv: Sequence[str] | None = None) -> int:
    """Print provenance findings for the workflow's retained diagnostic report."""
    arguments = _build_parser().parse_args(argv)
    findings = validate_prior_red_proof(
        arguments.prior_red_proof,
        arguments.repo_root.resolve(),
        base_ref=arguments.base_ref,
        final_ref=arguments.final_ref,
    )
    if findings:
        sys.stderr.write(f"{','.join(findings)}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
