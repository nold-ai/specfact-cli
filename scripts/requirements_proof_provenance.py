"""Validate Git-bound provenance before forwarding a red proof to reconciliation."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast
from xml.parsers import expat

from beartype import beartype
from icontract import ensure


GIT_OBJECT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
MAX_TEST_BLOB_BYTES = 10 * 1024 * 1024
MAX_JUNIT_BYTES = 10 * 1024 * 1024
TOOLCHAIN_PROPERTY_NAMES = {
    "runner": "specfact.runner",
    "python": "specfact.python",
    "pytest": "specfact.pytest",
}
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
    "requirements/",
    "modules/bundle-mapper/",
)
GOVERNED_PRODUCTION_FILES = {"pyproject.toml", "setup.py", "uv.lock"}


@dataclass(frozen=True)
class ParsedJunit:
    """Only the bounded JUnit facts needed by retained-proof validation."""

    cases: tuple[dict[str, tuple[str, ...]], ...]
    has_failure: bool


class _JunitCollector:
    """Reject declarations and collect testcase properties without building a tree."""

    def __init__(self) -> None:
        self.cases: list[dict[str, list[str]]] = []
        self.current_case: dict[str, list[str]] | None = None
        self.has_failure = False

    def _start(self, name: str, attributes: dict[str, str]) -> None:
        if name == "testcase":
            if self.current_case is not None:
                raise ValueError("prior-red-proof-invalid")
            self.current_case = {}
            return
        if self.current_case is None:
            return
        if name in {"failure", "error"}:
            self.has_failure = True
        elif name == "property":
            self._record_property(attributes)

    def _record_property(self, attributes: dict[str, str]) -> None:
        property_name = attributes.get("name")
        value = attributes.get("value")
        if property_name is not None and value is not None and self.current_case is not None:
            self.current_case.setdefault(property_name, []).append(value)

    def _end(self, name: str) -> None:
        if name == "testcase" and self.current_case is not None:
            self.cases.append(self.current_case)
            self.current_case = None

    def _reject_declaration(self, *_arguments: object) -> int:
        raise ValueError("prior-red-proof-invalid")

    def _result(self) -> ParsedJunit:
        if self.current_case is not None:
            raise ValueError("prior-red-proof-invalid")
        cases = tuple({name: tuple(values) for name, values in case.items()} for case in self.cases)
        return ParsedJunit(cases=cases, has_failure=self.has_failure)


def _parse_junit(payload: bytes) -> ParsedJunit:
    """Parse bounded XML while rejecting DTD, entity, and external references."""
    if len(payload) > MAX_JUNIT_BYTES:
        raise ValueError("prior-red-proof-invalid")
    collector = _JunitCollector()
    parser = expat.ParserCreate()
    parser.StartElementHandler = collector._start
    parser.EndElementHandler = collector._end
    parser.StartDoctypeDeclHandler = collector._reject_declaration
    parser.EntityDeclHandler = collector._reject_declaration
    parser.ExternalEntityRefHandler = collector._reject_declaration
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    try:
        parser.Parse(payload, True)
    except (expat.ExpatError, ValueError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    return collector._result()


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
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


def _validated_selectors(execution_proof: dict[str, object]) -> list[object]:
    source_ref = execution_proof.get("source_ref")
    selectors = execution_proof.get("selectors")
    if (
        not isinstance(source_ref, str)
        or GIT_OBJECT_PATTERN.fullmatch(source_ref) is None
        or not isinstance(selectors, list)
        or not selectors
    ):
        raise ValueError("prior-red-proof-invalid")
    return selectors


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
        if not isinstance(selector, str):
            raise ValueError("prior-red-proof-invalid")
        test_path, separator, _ = selector.partition("::")
        path = PurePosixPath(test_path)
        if not separator or path.is_absolute() or ".." in path.parts or not test_path.endswith(".py"):
            raise ValueError("prior-red-proof-invalid")
        paths.add(test_path)
    return source_ref, sorted(paths)


def _applicable_conftest_paths(test_path: str) -> set[str]:
    """Return root and ancestor pytest support files that can affect a selected test."""
    parent = PurePosixPath(test_path).parent
    paths = {"conftest.py"}
    while parent != PurePosixPath("."):
        paths.add((parent / "conftest.py").as_posix())
        parent = parent.parent
    return paths


def _python_module_paths(module_parts: Sequence[str]) -> set[str]:
    """Return possible paths for a repository-local module, including an absent target."""
    if not module_parts:
        return set()
    module_path = PurePosixPath(*module_parts)
    paths = {module_path.with_suffix(".py").as_posix(), (module_path / "__init__.py").as_posix()}
    for parent_depth in range(1, len(module_parts)):
        parent_path = PurePosixPath(*module_parts[:parent_depth])
        paths.add((parent_path / "__init__.py").as_posix())
    return paths


def _definition_expression_children(node: ast.AST) -> list[ast.AST] | None:
    """Return enclosing-scope expressions for one nested definition boundary."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
        return None
    if getattr(node, "name", None) == "pytest_plugins":
        raise ValueError("prior-red-proof-invalid")
    nested_body = {node.body} if isinstance(node, ast.Lambda) else set(node.body)
    return [child for child in ast.iter_child_nodes(node) if child not in nested_body]


def _import_binds_pytest_plugins(node: ast.AST) -> bool:
    """Return whether an import can create the active module global."""
    if isinstance(node, ast.Import):
        bound_names = {alias.asname or alias.name.split(".", maxsplit=1)[0] for alias in node.names}
        return "pytest_plugins" in bound_names
    if isinstance(node, ast.ImportFrom):
        bound_names = {alias.asname or alias.name for alias in node.names}
        return "pytest_plugins" in bound_names or "*" in bound_names
    return False


def _is_namespace_plugin_subscript(node: ast.AST) -> bool:
    """Return whether a direct module-namespace write targets ``pytest_plugins``."""
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.ctx, (ast.Store, ast.Del))
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == "pytest_plugins"
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id in {"globals", "locals", "vars"}
        and not node.value.args
        and not node.value.keywords
    )


def _is_indirect_plugin_binding(node: ast.AST) -> bool:
    """Return whether an unresolved enclosing-scope operation binds the plugin global."""
    pattern_binding = (isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name == "pytest_plugins") or (
        isinstance(node, ast.MatchMapping) and node.rest == "pytest_plugins"
    )
    name_binding = (
        isinstance(node, ast.Name) and node.id == "pytest_plugins" and isinstance(node.ctx, (ast.Store, ast.Del))
    )
    return pattern_binding or name_binding or _is_namespace_plugin_subscript(node)


def _plugin_assignment(node: ast.AST) -> tuple[ast.Name | None, ast.AST | None]:
    """Return one direct plugin target and its value, when present."""
    if isinstance(node, ast.Assign):
        target = next(
            (
                candidate
                for candidate in node.targets
                if isinstance(candidate, ast.Name) and candidate.id == "pytest_plugins"
            ),
            None,
        )
        return target, node.value if target is not None else None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "pytest_plugins":
        return node.target, node.value
    return None, None


def _enclosing_scope_children(node: ast.AST, plugin_target: ast.Name | None) -> list[ast.AST]:
    """Return children evaluated in the same scope, excluding local comprehension targets."""
    if isinstance(node, ast.comprehension):
        return [node.iter, *node.ifs]
    return [child for child in ast.iter_child_nodes(node) if child is not plugin_target]


def _literal_plugin_names(value_node: ast.AST) -> list[list[str]]:
    """Parse one literal plugin declaration or reject ambiguous runtime data."""
    try:
        value = ast.literal_eval(value_node)
    except (ValueError, TypeError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    declared_plugins = [value] if isinstance(value, str) else value
    if not isinstance(declared_plugins, (list, tuple)):
        raise ValueError("prior-red-proof-invalid")
    string_plugins = [plugin for plugin in declared_plugins if isinstance(plugin, str)]
    if len(string_plugins) != len(declared_plugins):
        raise ValueError("prior-red-proof-invalid")
    return [plugin.split(".") for plugin in string_plugins]


def _pytest_plugin_names(tree: ast.AST) -> list[list[str]]:
    """Return literal module-scope plugins or reject an unresolved declaration."""
    plugin_names: list[list[str]] = []
    scope_nodes: list[ast.AST] = list(reversed(tree.body)) if isinstance(tree, ast.Module) else []
    while scope_nodes:
        node = scope_nodes.pop()
        definition_children = _definition_expression_children(node)
        if definition_children is not None:
            scope_nodes.extend(reversed(definition_children))
            continue
        if _import_binds_pytest_plugins(node) or _is_indirect_plugin_binding(node):
            raise ValueError("prior-red-proof-invalid")
        plugin_target, value_node = _plugin_assignment(node)
        scope_nodes.extend(reversed(_enclosing_scope_children(node, plugin_target)))
        if value_node is not None:
            plugin_names.extend(_literal_plugin_names(value_node))
    return plugin_names


def _import_module_names(tree: ast.AST, current_path: str) -> list[list[str]]:
    """Return imported module names, including relative import candidates."""
    current_package = list(PurePosixPath(current_path).parent.parts)
    module_names = _pytest_plugin_names(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            module_names.extend(alias.name.split(".") for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            parent_parts = current_package[: max(len(current_package) - node.level + 1, 0)] if node.level else []
            base_parts = parent_parts + (node.module.split(".") if node.module else [])
            module_names.append(base_parts)
            module_names.extend(base_parts + alias.name.split(".") for alias in node.names if alias.name != "*")
    return module_names


def _python_tree_at_ref(repo_root: Path, source_ref: str, path: str) -> ast.AST | None:
    """Parse committed Python source without consulting mutable worktree bytes."""
    result = _git(repo_root, "show", f"{source_ref}:{path}")
    try:
        return ast.parse(result.stdout) if result.returncode == 0 else None
    except SyntaxError:
        return None


def _imported_python_paths(repo_root: Path, source_ref: str, source_paths: Sequence[str]) -> set[str]:
    """Return transitive repository-local Python imports used by pytest inputs."""
    pending = list(source_paths)
    imported_paths: set[str] = set()
    while pending:
        current_path = pending.pop()
        tree = _python_tree_at_ref(repo_root, source_ref, current_path)
        if tree is None:
            continue
        discovered_paths = {
            imported_path
            for module_parts in _import_module_names(tree, current_path)
            for imported_path in _python_module_paths(module_parts)
        }
        for imported_path in discovered_paths - imported_paths:
            imported_paths.add(imported_path)
            if _test_path_exists_at_ref(repo_root, source_ref, imported_path):
                pending.append(imported_path)
    return imported_paths


def _validate_retained_red_junit(
    red_proof_path: Path, report: dict[str, object], *, junit_path: Path | None = None
) -> ParsedJunit:
    """Bind the released report to a retained failing JUnit artifact."""
    execution_proof = _validated_execution_proof(report)
    expected_digest = execution_proof.get("junit_digest")
    retained_junit_path = junit_path or red_proof_path.with_suffix(".xml")
    try:
        if retained_junit_path.stat().st_size > MAX_JUNIT_BYTES:
            raise ValueError("prior-red-proof-invalid")
        payload = retained_junit_path.read_bytes()
        parsed_junit = _parse_junit(payload)
    except (OSError, ValueError) as error:
        raise ValueError("prior-red-proof-invalid") from error
    actual_digest = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    if expected_digest != actual_digest or not parsed_junit.has_failure:
        raise ValueError("prior-red-proof-invalid")
    junit_selectors = {selector for case in parsed_junit.cases for selector in case.get("specfact.selector", ())}
    if junit_selectors != set(_validated_selectors(execution_proof)):
        raise ValueError("prior-red-proof-invalid")
    return parsed_junit


def _case_property(properties: dict[str, tuple[str, ...]], name: str) -> str:
    """Return one non-empty JUnit case property or reject ambiguous producer evidence."""
    values = properties.get(name, ())
    if len(values) != 1 or not values[0]:
        raise ValueError("prior-red-proof-invalid")
    return values[0]


def _toolchain_identity_from_junit(junit: ParsedJunit, selectors: Sequence[object]) -> dict[str, str]:
    """Return one consistent toolchain identity emitted by every selected pytest case."""
    expected_selectors = {selector for selector in selectors if isinstance(selector, str)}
    identities: dict[str, tuple[str, str, str]] = {}
    for properties in junit.cases:
        selector = _case_property(properties, "specfact.selector")
        if selector not in expected_selectors or selector in identities:
            raise ValueError("prior-red-proof-invalid")
        identities[selector] = (
            _case_property(properties, TOOLCHAIN_PROPERTY_NAMES["runner"]),
            _case_property(properties, TOOLCHAIN_PROPERTY_NAMES["python"]),
            _case_property(properties, TOOLCHAIN_PROPERTY_NAMES["pytest"]),
        )
    if set(identities) != expected_selectors or len(set(identities.values())) != 1:
        raise ValueError("prior-red-proof-invalid")
    identity = next(iter(identities.values()))
    return dict(zip(TOOLCHAIN_PROPERTY_NAMES, identity, strict=True))


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
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "-z",
                "--find-renames",
                comparison_ref,
                revision,
            ],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
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


def _test_path_exists_at_ref(repo_root: Path, source_ref: str, test_path: str) -> bool:
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
    result = subprocess.run(
        ["git", "show", f"{source_ref}:{test_path}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
        timeout=30,
    )
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


def _write_report_atomically(red_proof_path: Path, report: dict[str, object]) -> None:
    """Replace the report only after every producer binding has validated."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=red_proof_path.parent, prefix=f".{red_proof_path.name}.", delete=False
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_path, red_proof_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _validate_binding_artifact_paths(red_proof_path: Path, junit_path: Path, repo_root: Path) -> None:
    """Reject mutable source-controlled or link-indirected producer artifacts."""
    paths = (red_proof_path, junit_path)
    if any(path.is_symlink() or _artifact_is_tracked(repo_root, path) for path in paths):
        raise ValueError("prior-red-proof-invalid")


def _red_source_identities(repo_root: Path, base_ref: str, source_ref: str) -> tuple[str, str]:
    """Return a committed source tree and merge base for one test-only red source."""
    if not _is_ancestor(repo_root, base_ref, source_ref):
        raise ValueError("prior-red-proof-invalid")
    changed_paths = _changed_paths_in_history(repo_root, base_ref, source_ref)
    if changed_paths is None or _has_governed_production_path(changed_paths):
        raise ValueError("prior-red-proof-invalid")
    source_tree_result = _git(repo_root, "rev-parse", f"{source_ref}^{{tree}}")
    merge_base_result = _git(repo_root, "merge-base", base_ref, source_ref)
    identities = (source_tree_result.stdout.strip(), merge_base_result.stdout.strip())
    if (
        source_tree_result.returncode
        or merge_base_result.returncode
        or any(GIT_OBJECT_PATTERN.fullmatch(identity) is None for identity in identities)
    ):
        raise ValueError("prior-red-proof-invalid")
    return identities


def _selected_test_digests(repo_root: Path, source_ref: str, selector_paths: Sequence[str]) -> dict[str, str]:
    """Bind every selected regular test to its immutable source-commit blob."""
    digests: dict[str, str] = {}
    for test_path in selector_paths:
        digest = _blob_digest_at_ref(repo_root, source_ref, test_path)
        if digest is None or not _test_path_is_regular_at_ref(repo_root, source_ref, test_path):
            raise ValueError("prior-red-proof-invalid")
        digests[test_path] = digest
    return digests


def _merge_execution_bindings(execution_proof: dict[str, object], bindings: dict[str, object]) -> None:
    """Add absent bindings while rejecting any producer-supplied contradiction."""
    conflicts = {
        field for field, value in bindings.items() if field in execution_proof and execution_proof[field] != value
    }
    if conflicts:
        raise ValueError("prior-red-proof-invalid")
    execution_proof.update(bindings)


@beartype
@ensure(lambda result: result is None)
def bind_red_proof(red_proof_path: Path, repo_root: Path, *, base_ref: str, junit_path: Path | None = None) -> None:
    """Add immutable core-owned provenance to one freshly reconciled red report."""
    retained_junit_path = junit_path or red_proof_path.with_suffix(".xml")
    _validate_binding_artifact_paths(red_proof_path, retained_junit_path, repo_root)
    report = _read_red_proof(red_proof_path)
    root = _validate_retained_red_junit(red_proof_path, report, junit_path=retained_junit_path)
    source_ref, selector_paths = _selector_paths(report)
    if not _valid_report_digests(report):
        raise ValueError("prior-red-proof-invalid")
    source_tree, merge_base = _red_source_identities(repo_root, base_ref, source_ref)
    execution_proof = _validated_execution_proof(report)
    bindings: dict[str, object] = {
        "source_tree": source_tree,
        "merge_base": merge_base,
        "test_file_digests": _selected_test_digests(repo_root, source_ref, selector_paths),
        "toolchain_identity": _toolchain_identity_from_junit(root, _validated_selectors(execution_proof)),
    }
    _merge_execution_bindings(execution_proof, bindings)
    _validate_execution_bindings(report, repo_root, base_ref, junit_root=root)
    _write_report_atomically(red_proof_path, report)


def _validated_test_file_digests(value: object, selector_paths: Sequence[str]) -> dict[str, object]:
    """Return selector-complete test digests or reject the proof."""
    if not isinstance(value, dict):
        raise ValueError("prior-red-proof-invalid")
    digests = cast(dict[str, object], value)
    if set(digests) != set(selector_paths):
        raise ValueError("prior-red-proof-invalid")
    return digests


def _validate_execution_bindings(
    report: dict[str, object],
    repo_root: Path,
    base_ref: str,
    *,
    junit_root: ParsedJunit,
) -> None:
    """Verify every source, test, plan, and toolchain binding required by the red-proof contract."""
    source_ref, selector_paths = _selector_paths(report)
    execution_proof = _validated_execution_proof(report)
    source_tree = execution_proof.get("source_tree")
    merge_base = execution_proof.get("merge_base")
    test_file_digests = _validated_test_file_digests(execution_proof.get("test_file_digests"), selector_paths)
    toolchain_identity = execution_proof.get("toolchain_identity")
    _validated_toolchain_identity(toolchain_identity)
    if toolchain_identity != _toolchain_identity_from_junit(junit_root, _validated_selectors(execution_proof)):
        raise ValueError("prior-red-proof-invalid")
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
        junit_root = _validate_retained_red_junit(red_proof_path, report)
        source_ref, _ = _selector_paths(report)
    except ValueError as error:
        return [str(error)]
    if not _red_source_precedes_final(repo_root, base_ref, source_ref, final_ref):
        return ["tdd-order-unproven"]
    try:
        _validate_execution_bindings(report, repo_root, base_ref, junit_root=junit_root)
    except ValueError as error:
        return [str(error)]
    return _validate_red_history_freshness(report, repo_root, base_ref, source_ref, final_ref)


def _validate_red_history_freshness(
    report: dict[str, object], repo_root: Path, base_ref: str, source_ref: str, final_ref: str
) -> list[str]:
    """Reject production-before-red and changed proof inputs after the red source."""
    _, selector_paths = _selector_paths(report)
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
        pytest_inputs = {test_path, *_applicable_conftest_paths(test_path)}
        try:
            proof_inputs = {
                *pytest_inputs,
                *_imported_python_paths(repo_root, source_ref, sorted(pytest_inputs)),
            }
        except ValueError as error:
            if str(error) == "prior-red-proof-invalid":
                return [str(error)]
            raise
        if not proof_inputs.isdisjoint(paths_after_red):
            return ["stale-red-proof"]
    return []


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    proof_mode = parser.add_mutually_exclusive_group(required=True)
    proof_mode.add_argument("--prior-red-proof", type=Path, help="Runner-produced red reconciliation report.")
    proof_mode.add_argument("--bind-red-proof", type=Path, help="Fresh red report to bind before artifact upload.")
    parser.add_argument("--junit", type=Path, help="JUnit artifact written beside a fresh bind-mode report.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository containing both Git sources.")
    parser.add_argument(
        "--base-ref", required=True, help="Pull-request base ref used to detect pre-red production changes."
    )
    parser.add_argument("--final-ref", help="Final source commit under reconciliation.")
    return parser


@beartype
@ensure(lambda result: result in {0, 1})
def main(argv: Sequence[str] | None = None) -> int:
    """Print provenance findings for the workflow's retained diagnostic report."""
    arguments = _build_parser().parse_args(argv)
    if arguments.bind_red_proof is not None:
        if arguments.junit is None:
            sys.stderr.write("prior-red-proof-invalid\n")
            return 1
        try:
            bind_red_proof(
                arguments.bind_red_proof,
                arguments.repo_root.resolve(),
                base_ref=arguments.base_ref,
                junit_path=arguments.junit,
            )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            sys.stderr.write(f"{error}\n")
            return 1
        return 0
    if arguments.prior_red_proof is None or arguments.final_ref is None:
        sys.stderr.write("prior-red-proof-invalid\n")
        return 1
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
