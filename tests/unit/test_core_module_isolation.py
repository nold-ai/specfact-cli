"""Core-module isolation tests."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_DIRS = [
    Path("src/specfact_cli/cli.py"),
    Path("src/specfact_cli/registry"),
    Path("src/specfact_cli/models"),
    Path("src/specfact_cli/utils"),
    Path("src/specfact_cli/contracts"),
]
EXTRACTED_MODULE_PREFIXES = (
    "specfact_cli.modules.",
    "specfact_backlog.",
    "specfact_project.",
    "specfact_codebase.",
    "specfact_spec.",
    "specfact_govern.",
)


def _collect_python_files(dirs: list[Path]) -> list[Path]:
    """Collect Python files from a list of file and directory paths."""
    files: list[Path] = []
    for relative in dirs:
        target = REPO_ROOT / relative
        if target.is_file() and target.suffix == ".py":
            files.append(target)
            continue
        if target.is_dir():
            files.extend(sorted(target.rglob("*.py")))
    return files


def _get_module_name(node: ast.AST) -> str:
    """Extract the imported module name from Import/ImportFrom nodes."""
    if isinstance(node, ast.Import):
        if node.names:
            return node.names[0].name
        return ""
    if isinstance(node, ast.ImportFrom):
        return node.module or ""
    return ""


def _is_type_checking_test(node: ast.AST) -> bool:
    """Return True when an AST expression node checks TYPE_CHECKING."""
    if isinstance(node, ast.Name):
        return node.id == "TYPE_CHECKING"
    if isinstance(node, ast.Attribute):
        return node.attr == "TYPE_CHECKING"
    return False


def _is_in_type_checking_block(node: ast.AST, parent_map: dict[ast.AST, ast.AST]) -> bool:
    """Determine whether a node is nested under an `if TYPE_CHECKING:` block."""
    current: ast.AST | None = node
    while current is not None:
        parent = parent_map.get(current)
        if parent is None:
            return False
        if isinstance(parent, ast.If) and _is_type_checking_test(parent.test):
            return True
        current = parent
    return False


def _format_violation(path: str, line_no: int, module: str) -> str:
    return f"{path}:{line_no} imports {module}"


def _is_extracted_module_import(module_name: str) -> bool:
    """Return True for imports targeting extracted module package namespaces."""
    return module_name.startswith(EXTRACTED_MODULE_PREFIXES)


def _find_core_module_import_violations(files: list[Path]) -> list[str]:
    """Scan Python files and return all direct core->module import violations."""
    violations: list[str] = []
    for file_path in files:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
        parent_map = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}

        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if _is_in_type_checking_block(node, parent_map):
                continue
            module_name = _get_module_name(node)
            if not _is_extracted_module_import(module_name):
                continue
            violations.append(
                _format_violation(
                    str(file_path.relative_to(REPO_ROOT)),
                    getattr(node, "lineno", 0),
                    module_name,
                )
            )
    return violations


def test_core_has_no_module_imports() -> None:
    """Core directories should not import module package code directly."""
    core_files = _collect_python_files(CORE_DIRS)
    violations = _find_core_module_import_violations(core_files)

    assert not violations, "\n".join([f"Found {len(violations)} core-to-module import violations", *violations])


def test_excludes_type_checking_blocks() -> None:
    """Imports in TYPE_CHECKING blocks are allowed by isolation policy."""
    source = ast.parse(
        """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specfact_backlog.backlog import commands
"""
    )
    parent_map = {child: parent for parent in ast.walk(source) for child in ast.iter_child_nodes(parent)}
    imports = [node for node in ast.walk(source) if isinstance(node, (ast.Import, ast.ImportFrom))]
    module_imports = [node for node in imports if _is_extracted_module_import(_get_module_name(node))]

    assert module_imports
    assert all(_is_in_type_checking_block(node, parent_map) for node in module_imports)


def test_multiple_violations_reported_together() -> None:
    """Violation reporting aggregates all issues in a single error payload."""
    violations = [
        _format_violation("src/specfact_cli/cli.py", 10, "specfact_backlog.backlog"),
        _format_violation("src/specfact_cli/models/project.py", 42, "specfact_project.sync"),
    ]
    message = "\n".join([f"Found {len(violations)} core-to-module import violations", *violations])

    assert "Found 2 core-to-module import violations" in message
    assert "src/specfact_cli/cli.py:10" in message
    assert "src/specfact_cli/models/project.py:42" in message


def test_violation_message_format() -> None:
    """Violation messages include file path, line number, and module name."""
    violation = _format_violation("src/specfact_cli/cli.py", 42, "specfact_backlog.backlog.commands")

    assert violation == "src/specfact_cli/cli.py:42 imports specfact_backlog.backlog.commands"
