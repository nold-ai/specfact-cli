"""Validate Git-bound provenance before forwarding a red proof to reconciliation."""

from __future__ import annotations

import argparse
import ast
import functools
import hashlib
import json
import re
import subprocess
import sys
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
PYTEST_CONFIGURATION_FILES = ("pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini")
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


def _python_module_target_paths(module_parts: Sequence[str]) -> set[str]:
    """Return the file and package targets for a repository-local module name."""
    if not module_parts:
        return set()
    module_path = PurePosixPath(*module_parts)
    return {module_path.with_suffix(".py").as_posix(), (module_path / "__init__.py").as_posix()}


def _python_module_paths(module_parts: Sequence[str]) -> set[str]:
    """Return possible paths for a repository-local module, including its parent packages."""
    paths = _python_module_target_paths(module_parts)
    for parent_depth in range(1, len(module_parts)):
        parent_path = PurePosixPath(*module_parts[:parent_depth])
        paths.add((parent_path / "__init__.py").as_posix())
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


def _assigned_value_nodes(node: ast.AST, name: str) -> list[ast.expr]:
    """Return every value statically bound to a named variable by one statement."""
    return [value for bound_name, value in _name_bindings(node) if bound_name == name]


def _static_condition(test: ast.AST, type_checking_names: set[str], typing_module_names: set[str]) -> bool | None:
    """Return a known branch condition used during module loading."""
    if isinstance(test, ast.Constant) and isinstance(test.value, bool):
        return test.value
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


def _name_bindings(node: ast.AST) -> list[tuple[str, ast.expr]]:
    """Return every module-level name binding made by one statement."""
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


def _verified_type_checking_bindings(tree: ast.AST) -> tuple[set[str], set[str]]:
    """Return unrebound names imported from the typing module.

    Rebinding is detected across the whole tree because an assignment or an import anywhere
    in the module may replace the guard, while a guard is only trusted when it is imported
    directly at module scope.
    """
    body = tree.body if isinstance(tree, ast.Module) else []
    nodes = list(ast.walk(tree))
    rebound_names = _other_import_names(nodes) | {name for node in nodes for name, _ in _name_bindings(node)}
    return (
        _imported_type_checking_names(body) - rebound_names,
        _imported_typing_module_names(body) - rebound_names,
    )


def _module_scope_nodes(tree: ast.AST, *, include_class_bodies: bool = False) -> list[ast.AST]:
    """Return executable module nodes without entering deferred function scopes."""
    type_checking_names, typing_module_names = _verified_type_checking_bindings(tree)
    pending = list(reversed(list(ast.iter_child_nodes(tree))))
    nodes: list[ast.AST] = []
    while pending:
        node = pending.pop()
        nodes.append(node)
        deferred_scope = isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.Lambda))
        excluded_class_scope = isinstance(node, ast.ClassDef) and not include_class_bodies
        if deferred_scope or excluded_class_scope:
            continue
        if (
            isinstance(node, ast.If)
            and (condition := _static_condition(node.test, type_checking_names, typing_module_names)) is not None
        ):
            pending.extend(reversed(node.body if condition else node.orelse))
            continue
        pending.extend(reversed(list(ast.iter_child_nodes(node))))
    return nodes


def _conditional_assignment_ids(tree: ast.AST) -> set[int]:
    """Return assignments under branches whose runtime outcome is unknown."""
    type_checking_names, typing_module_names = _verified_type_checking_bindings(tree)
    conditional_ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            if _static_condition(node.test, type_checking_names, typing_module_names) is not None:
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


def _pytest_plugin_names(tree: ast.AST) -> list[list[str]]:
    """Return statically declared ``pytest_plugins`` module names.

    Raises ``ValueError('stale-red-proof')`` when an active declaration cannot be resolved,
    because an unverifiable plugin set cannot prove the retained failure is still current.
    """
    plugin_names: list[list[str]] = []
    module_nodes = _module_scope_nodes(tree)
    conditional_assignment_ids = _conditional_assignment_ids(tree)
    constants: dict[str, list[object]] = {}
    for node in module_nodes:
        for value_node in _assigned_value_nodes(node, "pytest_plugins"):
            for value in _resolved_literals(value_node, constants):
                if value is UNRESOLVED_PLUGIN_VALUE:
                    raise ValueError("stale-red-proof")
                plugin_names.extend(_plugin_parts(value))
        for name, assigned_node in _name_bindings(node):
            try:
                value = ast.literal_eval(assigned_node)
            except (ValueError, TypeError):
                value = UNRESOLVED_PLUGIN_VALUE
            extends = id(node) in conditional_assignment_ids or bool(_augmented_assignments(node))
            _record_constant(constants, name, value, extends=extends)
    return plugin_names


def _import_module_names(tree: ast.AST, current_path: str) -> list[list[str]]:
    """Return imported module names, including relative import candidates."""
    current_package = list(PurePosixPath(current_path).parent.parts)
    module_names: list[list[str]] = []
    for node in _module_scope_nodes(tree, include_class_bodies=True):
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
    """
    result = _git_bytes(repo_root, "show", f"{source_ref}:{path}")
    if result.returncode != 0 or len(result.stdout) > MAX_TEST_BLOB_BYTES:
        return None
    try:
        return ast.parse(result.stdout)
    except (SyntaxError, ValueError):
        return None


def _discovered_python_paths(module_names: Sequence[Sequence[str]]) -> set[str]:
    """Return every repository path candidate for discovered module names."""
    return {path for module_parts in module_names for path in _python_module_paths(module_parts)}


def _imported_python_paths(
    repo_root: Path,
    source_ref: str,
    source_paths: Sequence[str],
    *,
    pytest_plugin_source_paths: set[str],
) -> set[str]:
    """Return transitive repository-local Python imports used by pytest inputs."""
    pending = [(path, path in pytest_plugin_source_paths) for path in source_paths]
    traversed_paths: set[tuple[str, bool]] = set()
    imported_paths: set[str] = set()
    while pending:
        current_path, inspect_pytest_plugins = pending.pop()
        traversal = (current_path, inspect_pytest_plugins)
        if traversal in traversed_paths:
            continue
        traversed_paths.add(traversal)
        tree = _python_tree_at_ref(repo_root, source_ref, current_path)
        if tree is None:
            continue
        ordinary_paths = _discovered_python_paths(_import_module_names(tree, current_path))
        plugin_names = _pytest_plugin_names(tree) if inspect_pytest_plugins else []
        plugin_paths = _discovered_python_paths(plugin_names)
        plugin_target_paths = {
            path for module_parts in plugin_names for path in _python_module_target_paths(module_parts)
        }
        imported_paths.update(ordinary_paths, plugin_paths)
        pending.extend(
            (imported_path, False)
            for imported_path in ordinary_paths
            if _test_path_exists_at_ref(repo_root, source_ref, imported_path)
        )
        pending.extend(
            (plugin_path, plugin_path in plugin_target_paths)
            for plugin_path in plugin_paths
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
    traversed once for the whole proof.
    """
    pytest_inputs = {
        path for test_path in selector_paths for path in (test_path, *_ancestor_file_paths(test_path, "conftest.py"))
    }
    initializer_inputs = {
        initializer for path in pytest_inputs for initializer in _ancestor_file_paths(path, "__init__.py")
    }
    traversal_inputs = pytest_inputs | initializer_inputs
    return {
        *traversal_inputs,
        *PYTEST_CONFIGURATION_FILES,
        *_imported_python_paths(
            repo_root,
            source_ref,
            sorted(traversal_inputs),
            pytest_plugin_source_paths=pytest_inputs,
        ),
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
