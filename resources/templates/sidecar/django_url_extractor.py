#!/usr/bin/env python3
"""
Django URL pattern extractor for sidecar contract population.

Extracts URL patterns from Django urls.py files and converts them to OpenAPI paths.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def _extract_path_parameters(path: str) -> tuple[str, list[dict[str, object]]]:
    """
    Extract path parameters from Django URL pattern.

    Converts Django format (<int:pk>, <str:name>) to OpenAPI format ({pk}, {name}).

    Args:
        path: Django URL pattern (e.g., 'notes/<int:note_id>/')

    Returns:
        Tuple of (normalized_path, path_params)
    """
    path_params: list[dict[str, Any]] = []
    normalized_path = path

    # Django pattern: <type:name> or <name>
    pattern = r"<(?:(?P<type>\w+):)?(?P<name>\w+)>"
    matches = list(re.finditer(pattern, path))

    for match in matches:
        param_type = match.group("type") or "str"
        param_name = match.group("name")

        # Convert Django type to OpenAPI type
        type_map = {
            "int": "integer",
            "float": "number",
            "str": "string",
            "string": "string",
            "slug": "string",
            "uuid": "string",
            "path": "string",
        }
        openapi_type = type_map.get(param_type.lower(), "string")

        path_params.append(
            {
                "name": param_name,
                "in": "path",
                "required": True,
                "schema": {"type": openapi_type},
            }
        )

        # Replace with OpenAPI format
        normalized_path = normalized_path.replace(match.group(0), f"{{{param_name}}}")

    return normalized_path, path_params


def _resolve_view_reference(view_node: ast.AST, imports: dict[str, str]) -> str | None:
    """
    Resolve Django view reference to a module path.

    Args:
        view_node: AST node representing the view (Name, Attribute, Call)
        imports: Dictionary of import aliases to module paths

    Returns:
        Module path string (e.g., 'authentication.views.sign_up') or None
    """
    if isinstance(view_node, ast.Name):
        # Direct reference: sign_up
        if view_node.id in imports:
            return imports[view_node.id]
        return view_node.id
    if isinstance(view_node, ast.Attribute):
        # Attribute reference: auth_views.sign_up
        if isinstance(view_node.value, ast.Name):
            module_alias = view_node.value.id
            if module_alias in imports:
                module_path = imports[module_alias]
                return f"{module_path}.{view_node.attr}"
            return f"{module_alias}.{view_node.attr}"
    elif isinstance(view_node, ast.Call) and isinstance(view_node.func, ast.Attribute):
        # Class-based view: NoteDetailView.as_view()
        return _resolve_view_reference(view_node.func.value, imports)

    return None


def _infer_http_method(view_name: str, view_path: str | None = None) -> str:
    """
    Infer HTTP method from view name or path.

    Args:
        view_name: Name of the view function
        view_path: URL path pattern (optional)

    Returns:
        HTTP method (default: 'GET')
    """
    view_lower = view_name.lower()

    # Common patterns
    if any(
        keyword in view_lower
        for keyword in ["create", "add", "new", "signup", "sign_up", "login", "log_in", "register"]
    ):
        return "POST"
    if any(keyword in view_lower for keyword in ["update", "edit", "change"]):
        return "PUT"
    if any(keyword in view_lower for keyword in ["delete", "remove"]):
        return "DELETE"
    if any(keyword in view_lower for keyword in ["list", "index", "all"]):
        return "GET"
    if view_path and any(keyword in view_path.lower() for keyword in ["write", "create", "add"]):
        return "POST"

    return "GET"


def extract_django_urls(repo_path: Path, urls_file: Path | None = None) -> list[dict[str, object]]:
    """
    Extract URL patterns from Django urls.py file.

    Args:
        repo_path: Path to Django repository root
        urls_file: Path to urls.py file (default: find automatically)

    Returns:
        List of URL pattern dictionaries with path, method, view, etc.
    """
    if urls_file is None:
        # Try to find main urls.py
        candidates = [
            repo_path / "urls.py",
            repo_path / repo_path.name / "urls.py",  # project/urls.py
        ]
        for candidate in candidates:
            if candidate.exists():
                urls_file = candidate
                break

        if urls_file is None:
            # Search for urls.py files
            urls_files = list(repo_path.rglob("urls.py"))
            if urls_files:
                urls_file = urls_files[0]

    if urls_file is None or not urls_file.exists():
        return []

    with urls_file.open("r", encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content, filename=str(urls_file))
    except SyntaxError:
        return []

    # Extract imports
    imports: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                alias_name = alias.asname or alias.name
                imports[alias_name] = f"{module}.{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                alias_name = alias.asname or alias.name
                imports[alias_name] = alias.name

    # Find urlpatterns
    urlpatterns: Sequence[ast.expr] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "urlpatterns":
                    if isinstance(node.value, ast.List):
                        urlpatterns = node.value.elts
                    break

    results: list[dict[str, object]] = []

    for pattern_node in urlpatterns:
        if not isinstance(pattern_node, ast.Call):
            continue

        # Check if it's path() or re_path()
        if isinstance(pattern_node.func, ast.Name):
            func_name = pattern_node.func.id
        elif isinstance(pattern_node.func, ast.Attribute):
            func_name = pattern_node.func.attr
        else:
            continue

        if func_name not in ("path", "re_path"):
            continue

        # Extract path pattern (first argument)
        if not pattern_node.args:
            continue

        path_arg = pattern_node.args[0]
        if isinstance(path_arg, ast.Constant):
            path_pattern = path_arg.value
        elif hasattr(ast, "Str") and isinstance(path_arg, ast.Str):  # Python < 3.8
            path_pattern = path_arg.s  # type: ignore[attr-defined]
        else:
            continue

        if not isinstance(path_pattern, str):
            continue

        # Extract view (second argument)
        view_ref = None
        if len(pattern_node.args) > 1:
            view_node = pattern_node.args[1]
            view_ref = _resolve_view_reference(view_node, imports)

        # Extract name (keyword argument or third positional)
        pattern_name: str | None = None
        for kw in pattern_node.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                constant_value = kw.value.value
                if isinstance(constant_value, str):
                    pattern_name = constant_value
                break
            if kw.arg == "name" and hasattr(ast, "Str") and isinstance(kw.value, ast.Str):
                str_value = kw.value.s  # type: ignore[attr-defined, deprecated]
                pattern_name = str_value if isinstance(str_value, str) else None
                break

        if not pattern_name and len(pattern_node.args) > 2:
            name_arg = pattern_node.args[2]
            if isinstance(name_arg, ast.Constant):
                constant_value = name_arg.value
                if isinstance(constant_value, str):
                    pattern_name = constant_value
            elif hasattr(ast, "Str") and isinstance(name_arg, ast.Str):
                str_value = name_arg.s  # type: ignore[attr-defined, deprecated]
                pattern_name = str_value if isinstance(str_value, str) else None

        # Normalize path and extract parameters
        normalized_path, path_params = _extract_path_parameters(path_pattern)

        # Infer HTTP method
        view_name_for_inference = view_ref or pattern_name or ""
        if not isinstance(view_name_for_inference, str):
            view_name_for_inference = ""
        method = _infer_http_method(view_name_for_inference, path_pattern)

        # Extract operation_id from view reference or pattern name
        operation_id = pattern_name or (view_ref.split(".")[-1] if view_ref else "unknown")

        results.append(
            {
                "path": normalized_path,
                "method": method,
                "view": view_ref,
                "operation_id": operation_id,
                "path_params": path_params,
                "original_path": path_pattern,
            }
        )

    return results


def main() -> int:
    """Main entry point for Django URL extractor."""
    parser = argparse.ArgumentParser(description="Extract Django URL patterns for contract population.")
    parser.add_argument("--repo", required=True, help="Path to Django repository")
    parser.add_argument("--urls", help="Path to urls.py file (auto-detected if not provided)")
    parser.add_argument("--output", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    repo_path = Path(str(args.repo)).resolve()  # type: ignore[arg-type]
    urls_file = Path(str(args.urls)).resolve() if args.urls else None  # type: ignore[arg-type]

    results = extract_django_urls(repo_path, urls_file)

    output_json = json.dumps(results, indent=2, sort_keys=True)

    if args.output:
        Path(str(args.output)).write_text(output_json, encoding="utf-8")  # type: ignore[arg-type]
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
