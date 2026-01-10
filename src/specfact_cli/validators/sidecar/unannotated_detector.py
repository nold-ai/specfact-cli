"""
Unannotated code detector for sidecar validation.

This module detects functions without icontract/beartype decorators
using AST parsing to enable sidecar validation for unannotated code.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda file_path: file_path.exists(), "File path must exist")
@require(lambda file_path: file_path.suffix == ".py", "File must be Python file")
@ensure(lambda result: isinstance(result, list), "Must return list")
def detect_unannotated_functions(file_path: Path) -> list[dict[str, Any]]:
    """
    Detect functions without icontract/beartype decorators in a Python file.

    Args:
        file_path: Path to Python file to analyze

    Returns:
        List of dictionaries with function information:
        - name: Function name
        - line: Line number
        - has_icontract: Whether function has icontract decorators
        - has_beartype: Whether function has beartype decorator
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    unannotated: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            has_icontract = False
            has_beartype = False

            # Check decorators
            for decorator in node.decorator_list:
                decorator_name = _get_decorator_name(decorator)
                if decorator_name in ("require", "ensure", "invariant"):
                    has_icontract = True
                elif decorator_name == "beartype":
                    has_beartype = True

            # Function is unannotated if it lacks both icontract and beartype
            if not has_icontract and not has_beartype:
                unannotated.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "has_icontract": has_icontract,
                        "has_beartype": has_beartype,
                        "file": str(file_path),
                    }
                )

    return unannotated


@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
@ensure(lambda result: isinstance(result, list), "Must return list")
def detect_unannotated_in_repo(repo_path: Path, source_dirs: list[Path] | None = None) -> list[dict[str, Any]]:
    """
    Detect unannotated functions across a repository.

    Args:
        repo_path: Path to repository root
        source_dirs: Optional list of source directories to scan (defaults to common patterns)

    Returns:
        List of unannotated function dictionaries
    """
    if source_dirs is None:
        # Default source directory patterns
        source_dirs = []
        for pattern in ["src", "lib", "backend/app"]:
            candidate = repo_path / pattern
            if candidate.exists():
                source_dirs.append(candidate)
        if not source_dirs:
            source_dirs = [repo_path]

    unannotated: list[dict[str, Any]] = []

    for source_dir in source_dirs:
        if not source_dir.exists():
            continue

        # Find all Python files
        for py_file in source_dir.rglob("*.py"):
            # Skip test files and sidecar harness files
            if "test" in py_file.parts or "harness" in py_file.name.lower():
                continue

            functions = detect_unannotated_functions(py_file)
            unannotated.extend(functions)

    return unannotated


@beartype
@ensure(lambda result: isinstance(result, str) or result is None, "Must return str or None")
def _get_decorator_name(decorator: ast.expr) -> str | None:
    """
    Extract decorator name from AST node.

    Args:
        decorator: AST decorator node

    Returns:
        Decorator name or None if not a simple name
    """
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        # Handle cases like @icontract.require
        if isinstance(decorator.value, ast.Name):
            return decorator.attr
    elif isinstance(decorator, ast.Call):
        # Handle cases like @require(...)
        if isinstance(decorator.func, ast.Name):
            return decorator.func.id
        if isinstance(decorator.func, ast.Attribute):
            return decorator.func.attr

    return None
