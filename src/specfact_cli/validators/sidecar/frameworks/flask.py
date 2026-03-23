"""
Flask framework extractor for sidecar validation.

This module extracts routes and schemas from Flask applications.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.validators.sidecar.frameworks.base import BaseFrameworkExtractor, RouteInfo


def _flask_markers_in_content(content: str) -> bool:
    return "from flask import Flask" in content or ("import flask" in content and "Flask(" in content)


def _read_flask_markers(file_path: Path) -> bool:
    try:
        return _flask_markers_in_content(file_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, PermissionError):
        return False


def _flask_or_blueprint_constructor(call: ast.Call) -> tuple[bool, bool]:
    is_flask = (isinstance(call.func, ast.Name) and call.func.id == "Flask") or (
        isinstance(call.func, ast.Attribute) and call.func.attr == "Flask"
    )
    is_blueprint = (isinstance(call.func, ast.Name) and call.func.id == "Blueprint") or (
        isinstance(call.func, ast.Attribute) and call.func.attr == "Blueprint"
    )
    return is_flask, is_blueprint


class FlaskExtractor(BaseFrameworkExtractor):
    """Flask framework extractor."""

    @beartype
    @require(
        lambda repo_path: isinstance(repo_path, Path) and repo_path.exists(),
        "Repository path must exist",
    )
    @require(
        lambda repo_path: isinstance(repo_path, Path) and repo_path.is_dir(),
        "Repository path must be a directory",
    )
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def detect(self, repo_path: Path) -> bool:
        """
        Detect if Flask is used in the repository.

        Args:
            repo_path: Path to repository root

        Returns:
            True if Flask is detected
        """
        for candidate_file in ["app.py", "main.py", "__init__.py"]:
            file_path = repo_path / candidate_file
            if file_path.exists() and _read_flask_markers(file_path):
                return True

        # Check in common locations
        for search_path in [repo_path, repo_path / "src", repo_path / "app", repo_path / "backend" / "app"]:
            if not search_path.exists():
                continue
            for py_file in search_path.rglob("*.py"):
                if py_file.name in ["app.py", "main.py", "__init__.py"] and _read_flask_markers(py_file):
                    return True

        return False

    @beartype
    @require(
        lambda repo_path: isinstance(repo_path, Path) and repo_path.exists(),
        "Repository path must exist",
    )
    @require(
        lambda repo_path: isinstance(repo_path, Path) and repo_path.is_dir(),
        "Repository path must be a directory",
    )
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def extract_routes(self, repo_path: Path) -> list[RouteInfo]:
        """
        Extract routes from Flask route files.

        Args:
            repo_path: Path to repository root

        Returns:
            List of RouteInfo objects
        """
        results: list[RouteInfo] = []

        # Find Flask app files
        for search_path in [repo_path, repo_path / "src", repo_path / "app", repo_path / "backend" / "app"]:
            if not search_path.exists():
                continue
            for py_file in search_path.rglob("*.py"):
                try:
                    routes = self._extract_routes_from_file(py_file)
                    results.extend(routes)
                except (SyntaxError, UnicodeDecodeError, PermissionError):
                    continue

        return results

    @beartype
    @require(
        lambda repo_path: isinstance(repo_path, Path) and repo_path.exists(),
        "Repository path must exist",
    )
    @require(lambda routes: isinstance(routes, list), "Routes must be a list")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_schemas(self, repo_path: Path, routes: list[RouteInfo]) -> dict[str, dict[str, Any]]:
        """
        Extract schemas from Flask routes.

        Args:
            repo_path: Path to repository root
            routes: List of extracted routes

        Returns:
            Dictionary mapping route identifiers to schema dictionaries
        """
        # Schema extraction can be enhanced later
        # For now, return empty dict
        return {}

    @beartype
    def _extract_routes_from_file(self, py_file: Path) -> list[RouteInfo]:
        """Extract routes from a Python file."""
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError, PermissionError):
            return []

        imports = self._extract_imports(tree)
        results: list[RouteInfo] = []

        app_names, bp_names = self._collect_flask_app_and_blueprint_names(tree)

        # Second pass: Extract routes from functions with decorators
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                route_infos = self._extract_route_from_function(node, imports, py_file, app_names, bp_names)
                if route_infos:
                    results.extend(route_infos)

        return results

    def _collect_flask_app_and_blueprint_names(self, tree: ast.AST) -> tuple[set[str], set[str]]:
        app_names: set[str] = set()
        bp_names: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if not isinstance(node.value, ast.Call):
                    continue
                call = node.value
                is_flask, is_blueprint = _flask_or_blueprint_constructor(call)
                if is_flask:
                    app_names.add(target.id)
                elif is_blueprint:
                    bp_names.add(target.id)
        return app_names, bp_names

    @beartype
    def _extract_imports(self, tree: ast.AST) -> dict[str, str]:
        """Extract import statements from AST."""
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
        return imports

    @beartype
    def _extract_route_from_function(
        self,
        func_node: ast.FunctionDef,
        imports: dict[str, str],
        py_file: Path,
        app_names: set[str],
        bp_names: set[str],
    ) -> list[RouteInfo]:
        """Extract route information from a function with Flask decorators."""
        path = None
        methods = ["GET"]  # Default method

        # Check decorators for route information
        for decorator in func_node.decorator_list:
            # @app.route('/path', methods=['GET', 'POST'])
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "route"
            ):
                # Extract path from first argument
                if decorator.args:
                    path_arg = self._extract_string_literal(decorator.args[0])
                    if path_arg:
                        path = path_arg

                # Extract methods from keyword arguments
                for keyword in decorator.keywords:
                    if keyword.arg == "methods":
                        methods = self._extract_methods_list(keyword.value)

        if path is None:
            return []

        # Convert Flask path parameters to OpenAPI format
        normalized_path, path_params = self._extract_path_parameters(path)

        # Return one RouteInfo per method to capture all HTTP methods
        results: list[RouteInfo] = []
        for method in methods:
            results.append(
                RouteInfo(
                    path=normalized_path,
                    method=method,
                    operation_id=func_node.name,
                    function=func_node.name,
                    path_params=path_params,
                )
            )

        return results

    @beartype
    def _extract_string_literal(self, node: ast.AST) -> str | None:
        """Extract string literal from AST node (Python 3.8+ uses ast.Constant)."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    @beartype
    def _extract_methods_list(self, node: ast.AST) -> list[str]:
        """Extract HTTP methods from AST list node."""
        methods: list[str] = []
        if isinstance(node, ast.List):
            for elt in node.elts:
                method = self._extract_string_literal(elt)
                if method:
                    methods.append(method.upper())
        return methods if methods else ["GET"]

    @beartype
    def _extract_path_parameters(self, path: str) -> tuple[str, list[dict[str, Any]]]:
        """Extract path parameters from Flask route path and convert to OpenAPI format."""
        path_params: list[dict[str, Any]] = []
        normalized_path = path

        # Flask path parameter patterns:
        # <int:id> -> {id} with type: integer
        # <float:value> -> {value} with type: number
        # <path:path> -> {path} with type: string
        # <slug> -> {slug} with type: string (default)

        # Pattern: <type:name> or <name>
        pattern = r"<([^:>]+)(?::([^>]+))?>"
        matches = list(re.finditer(pattern, path))

        type_map = {
            "int": "integer",
            "float": "number",
            "path": "string",
            "str": "string",
            "string": "string",
        }

        for match in matches:
            param_type = match.group(1)  # type or name
            param_name_from_group2 = match.group(2)  # name (if present)

            # If second group exists, it's the parameter name (converter:name format)
            # If not, first group is the parameter name (<name> format)
            if param_name_from_group2:
                # Format: <converter:name> or <type:name>
                param_name = param_name_from_group2
                # Use known converter type or default to string for unknown converters
                openapi_type = type_map.get(param_type, "string")
            else:
                # Format: <slug> or <id> (no converter)
                param_name = param_type
                openapi_type = "string"

            path_params.append(
                {
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": openapi_type},
                }
            )

            # Replace Flask format with OpenAPI format
            # Reconstruct the original Flask pattern for replacement
            flask_pattern = f"<{param_type}:{param_name_from_group2}>" if param_name_from_group2 else f"<{param_type}>"
            normalized_path = normalized_path.replace(flask_pattern, f"{{{param_name}}}")

        return normalized_path, path_params
