"""
Django framework extractor for sidecar validation.

This module extracts routes and schemas from Django applications.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.validators.sidecar.frameworks.base import BaseFrameworkExtractor, RouteInfo


class DjangoExtractor(BaseFrameworkExtractor):
    """Django framework extractor."""

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, bool), "Must return bool")
    def detect(self, repo_path: Path) -> bool:
        """
        Detect if Django is used in the repository.

        Args:
            repo_path: Path to repository root

        Returns:
            True if Django is detected
        """
        manage_py = repo_path / "manage.py"
        if manage_py.exists():
            return True

        urls_files = list(repo_path.rglob("urls.py"))
        return len(urls_files) > 0

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
    @ensure(lambda result: isinstance(result, list), "Must return list")
    def extract_routes(self, repo_path: Path) -> list[RouteInfo]:
        """
        Extract routes from Django urls.py files.

        Args:
            repo_path: Path to repository root

        Returns:
            List of RouteInfo objects
        """
        urls_file = self._find_urls_file(repo_path)
        if urls_file is None:
            return []

        return self._extract_urls_from_file(repo_path, urls_file)

    @beartype
    @require(lambda repo_path: repo_path.exists(), "Repository path must exist")
    @require(lambda routes: isinstance(routes, list), "Routes must be a list")
    @ensure(lambda result: isinstance(result, dict), "Must return dict")
    def extract_schemas(self, repo_path: Path, routes: list[RouteInfo]) -> dict[str, dict[str, Any]]:
        """
        Extract schemas from Django forms for routes.

        Args:
            repo_path: Path to repository root
            routes: List of extracted routes

        Returns:
            Dictionary mapping route identifiers to schema dictionaries
        """
        schemas: dict[str, dict[str, Any]] = {}

        for route in routes:
            if route.view:
                form_schema = self._extract_form_schema(repo_path, route.view)
                if form_schema:
                    route_id = f"{route.method}:{route.path}"
                    schemas[route_id] = form_schema

        return schemas

    @beartype
    def _find_urls_file(self, repo_path: Path) -> Path | None:
        """Find the main urls.py file."""
        candidates = [
            repo_path / "urls.py",
            repo_path / repo_path.name / "urls.py",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate

        urls_files = list(repo_path.rglob("urls.py"))
        return urls_files[0] if urls_files else None

    @beartype
    def _extract_urls_from_file(self, repo_path: Path, urls_file: Path) -> list[RouteInfo]:
        """Extract URL patterns from urls.py file."""
        try:
            content = urls_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(urls_file))
        except (SyntaxError, UnicodeDecodeError, PermissionError):
            return []

        imports = self._extract_imports(tree)
        urlpatterns = self._find_urlpatterns(tree)

        results: list[RouteInfo] = []

        for pattern_node in urlpatterns:
            if not isinstance(pattern_node, ast.Call):
                continue

            route_info = self._parse_url_pattern(pattern_node, imports, repo_path)
            if route_info:
                results.append(route_info)

        return results

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
    def _find_urlpatterns(self, tree: ast.AST) -> list[ast.expr]:
        """Find urlpatterns list in AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "urlpatterns":
                        if isinstance(node.value, ast.List):
                            return node.value.elts
                        if (
                            isinstance(node.value, ast.Call)
                            and isinstance(node.value.func, ast.Name)
                            and node.value.func.id == "patterns"
                            and len(node.value.args) > 1
                        ):
                            return node.value.args[1:]
        return []

    @beartype
    def _parse_url_pattern(self, pattern_node: ast.Call, imports: dict[str, str], repo_path: Path) -> RouteInfo | None:
        """Parse a single URL pattern node."""
        func_name = self._get_function_name(pattern_node.func)
        if func_name not in ("path", "re_path", "url"):
            return None

        if len(pattern_node.args) < 2:
            return None

        path_pattern = self._extract_string_literal(pattern_node.args[0])
        if not path_pattern:
            return None

        view_ref = self._resolve_view_reference(pattern_node.args[1], imports)
        pattern_name = self._extract_pattern_name(pattern_node)

        normalized_path, path_params = self._extract_path_parameters(path_pattern)
        method = self._infer_http_method(view_ref or pattern_name or "", path_pattern)
        operation_id = pattern_name or (view_ref.split(".")[-1] if view_ref else "unknown")

        return RouteInfo(
            path=normalized_path,
            method=method,
            operation_id=operation_id,
            view=view_ref,
            path_params=path_params,
        )

    @beartype
    def _get_function_name(self, func_node: ast.AST) -> str:
        """Get function name from AST node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        if isinstance(func_node, ast.Attribute):
            return func_node.attr
        return ""

    @beartype
    def _extract_string_literal(self, node: ast.AST) -> str | None:
        """Extract string literal from AST node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return node.value
        elif hasattr(ast, "Str") and isinstance(node, ast.Str):
            return node.s  # type: ignore[attr-defined, deprecated]
        return None

    @beartype
    def _resolve_view_reference(self, view_node: ast.AST, imports: dict[str, str]) -> str | None:
        """Resolve view reference to module path."""
        if isinstance(view_node, ast.Name):
            if view_node.id in imports:
                return imports[view_node.id]
            return view_node.id
        if isinstance(view_node, ast.Attribute):
            if isinstance(view_node.value, ast.Name):
                module_alias = view_node.value.id
                if module_alias in imports:
                    module_path = imports[module_alias]
                    return f"{module_path}.{view_node.attr}"
                return f"{module_alias}.{view_node.attr}"
        elif isinstance(view_node, ast.Call) and isinstance(view_node.func, ast.Attribute):
            return self._resolve_view_reference(view_node.func.value, imports)
        return None

    @beartype
    def _extract_pattern_name(self, pattern_node: ast.Call) -> str | None:
        """Extract pattern name from URL pattern."""
        for kw in pattern_node.keywords:
            if kw.arg == "name":
                value = self._extract_string_literal(kw.value)
                if value:
                    return value

        if len(pattern_node.args) > 2:
            return self._extract_string_literal(pattern_node.args[2])

        return None

    @beartype
    def _extract_path_parameters(self, path: str) -> tuple[str, list[dict[str, Any]]]:
        """Extract path parameters from Django URL pattern."""
        path_params: list[dict[str, Any]] = []
        normalized_path = path

        # Django 2.0+ pattern: <type:name> or <name>
        django_pattern = r"<(?:(?P<type>\w+):)?(?P<name>\w+)>"
        matches = list(re.finditer(django_pattern, path))

        type_map = {
            "int": "integer",
            "float": "number",
            "str": "string",
            "string": "string",
            "slug": "string",
            "uuid": "string",
            "path": "string",
        }

        for match in matches:
            param_type = match.group("type") or "str"
            param_name = match.group("name")
            openapi_type = type_map.get(param_type.lower(), "string")

            path_params.append(
                {
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": openapi_type},
                }
            )
            normalized_path = normalized_path.replace(match.group(0), f"{{{param_name}}}")

        # Django 1.x regex pattern
        regex_pattern = r"\(\?P<(\w+)>[^)]+\)"
        regex_matches = list(re.finditer(regex_pattern, normalized_path))

        for match in regex_matches:
            param_name = match.group(1)
            path_params.append(
                {
                    "name": param_name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            )
            normalized_path = normalized_path.replace(match.group(0), f"{{{param_name}}}")

        return normalized_path, path_params

    @beartype
    def _infer_http_method(self, view_name: str, view_path: str | None = None) -> str:
        """Infer HTTP method from view name or path."""
        view_lower = view_name.lower()

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

    @beartype
    def _extract_form_schema(self, repo_path: Path, view_ref: str) -> dict[str, Any] | None:
        """Extract form schema from Django view."""
        # Simplified form extraction - full implementation would parse form classes
        # For now, return None to indicate no schema extracted
        # This can be enhanced later with full form extraction logic
        return None
