"""
OpenAPI contract extractor.

This module provides utilities for extracting OpenAPI 3.0.3 contracts from
verbose acceptance criteria or existing code using AST analysis.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import os
import re
from pathlib import Path
from threading import Lock
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure, require

from specfact_cli.integrations.specmatic import SpecValidationResult, validate_spec_with_specmatic
from specfact_cli.models.plan import Feature


def _fastapi_decorator_first_path_str(decorator: ast.Call) -> str | None:
    if not decorator.args:
        return None
    path_arg = decorator.args[0]
    if not isinstance(path_arg, ast.Constant):
        return None
    path = path_arg.value
    if not isinstance(path, str):
        return None
    return path


def _fastapi_apply_router_prefix(path: str, decorator: ast.Call, router_prefixes: dict[str, str]) -> str:
    dec_func = decorator.func
    if isinstance(dec_func, ast.Attribute) and isinstance(dec_func.value, ast.Name):
        router_name = dec_func.value.id
        if router_name in router_prefixes:
            return router_prefixes[router_name] + path
    return path


def _fastapi_resolve_route_tags(decorator: ast.Call, router_tags: dict[str, list[str]]) -> list[str]:
    tags: list[str] = []
    dec_func = decorator.func
    if isinstance(dec_func, ast.Attribute) and isinstance(dec_func.value, ast.Name):
        router_name = dec_func.value.id
        if router_name in router_tags:
            tags = router_tags[router_name]
    for kw in decorator.keywords:
        if kw.arg == "tags" and isinstance(kw.value, ast.List):
            tags = [
                str(elt.value) for elt in kw.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            ]
    return tags


def _merge_request_test_example_into_operation(operation: dict[str, Any], example_data: dict[str, Any]) -> None:
    if "request" not in example_data or "requestBody" not in operation:
        return
    request_body_any = example_data["request"]
    if not isinstance(request_body_any, dict):
        return
    request_body = cast(dict[str, Any], request_body_any)
    if "body" not in request_body:
        return
    rb_any = operation.get("requestBody")
    if not isinstance(rb_any, dict):
        return
    request_body_spec = cast(dict[str, Any], rb_any)
    content_any = request_body_spec.get("content", {})
    if not isinstance(content_any, dict):
        return
    content = cast(dict[str, Any], content_any)
    for _content_type, content_schema_any in content.items():
        if not isinstance(content_schema_any, dict):
            continue
        content_schema = cast(dict[str, Any], content_schema_any)
        if "examples" not in content_schema:
            content_schema["examples"] = {}
        content_schema["examples"]["test-example"] = {
            "summary": "Example from test",
            "value": request_body["body"],
        }


def _merge_response_test_example_into_operation(operation: dict[str, Any], example_data: dict[str, Any]) -> None:
    if "response" not in example_data:
        return
    status_code = str(example_data.get("status_code", 200))
    responses_any = operation.get("responses", {})
    if not isinstance(responses_any, dict):
        return
    responses = cast(dict[str, Any], responses_any)
    if status_code not in responses:
        return
    response_any = responses[status_code]
    if not isinstance(response_any, dict):
        return
    response = cast(dict[str, Any], response_any)
    content_any = response.get("content", {})
    if not isinstance(content_any, dict):
        return
    content = cast(dict[str, Any], content_any)
    for _content_type, content_schema_any in content.items():
        if not isinstance(content_schema_any, dict):
            continue
        content_schema = cast(dict[str, Any], content_schema_any)
        if "examples" not in content_schema:
            content_schema["examples"] = {}
        content_schema["examples"]["test-example"] = {
            "summary": "Example from test",
            "value": example_data["response"],
        }


class OpenAPIExtractor:
    """Extractor for generating OpenAPI contracts from features."""

    def __init__(self, repo_path: Path) -> None:
        """
        Initialize extractor with repository path.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path.resolve()
        # Use separate locks to reduce contention:
        # - Cache lock: protects AST cache (shared across all features)
        # - Spec locks: each feature gets its own lock for openapi_spec writes (per-feature isolation)
        self._cache_lock = Lock()  # Thread lock for AST cache (shared resource)
        # Performance optimization: Cache AST trees and file content to avoid redundant parsing
        self._ast_cache: dict[Path, ast.AST] = {}  # File path -> AST tree
        self._file_hash_cache: dict[Path, str] = {}  # File path -> content hash for cache invalidation
        # Pre-compiled regex patterns for early exit optimization
        self._api_patterns = [
            re.compile(r"@(app|router)\.(get|post|put|delete|patch|head|options)", re.IGNORECASE),
            re.compile(r"@app\.route\("),
            re.compile(r"APIRouter\("),
            re.compile(r"FastAPI\("),
        ]

    @beartype
    @require(lambda self, feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @ensure(lambda self, feature, result: isinstance(result, dict), "Must return OpenAPI dict")
    def extract_openapi_from_verbose(self, feature: Feature) -> dict[str, Any]:
        """
        Convert verbose acceptance criteria to OpenAPI contract.

        Args:
            feature: Feature with verbose acceptance criteria

        Returns:
            OpenAPI 3.0.3 specification as dictionary
        """
        # Start with basic OpenAPI structure
        openapi_spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {
                "title": feature.title,
                "version": "1.0.0",
                "description": f"API contract for {feature.title}",
            },
            "paths": {},
            "components": {"schemas": {}},
        }

        # Extract API endpoints from acceptance criteria
        for story in feature.stories:
            for acceptance in story.acceptance:
                # Try to extract HTTP method and path from acceptance criteria
                # Patterns like "POST /api/login", "GET /api/users", etc.
                method_path_match = re.search(
                    r"(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(/[\w/-]+)", acceptance, re.IGNORECASE
                )
                if method_path_match:
                    method = method_path_match.group(1).upper()
                    path = method_path_match.group(2)

                    if path not in openapi_spec["paths"]:
                        openapi_spec["paths"][path] = {}

                    # Create operation
                    operation_id = f"{method.lower()}_{path.replace('/', '_').replace('-', '_').strip('_')}"
                    operation: dict[str, Any] = {
                        "operationId": operation_id,
                        "summary": story.title,
                        "description": acceptance,
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {},
                                        }
                                    }
                                },
                            }
                        },
                    }

                    # Add request body for POST/PUT/PATCH
                    if method in ("POST", "PUT", "PATCH"):
                        operation["requestBody"] = {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {},
                                    }
                                }
                            },
                        }

                    openapi_spec["paths"][path][method.lower()] = operation

        return openapi_spec

    def _collect_py_files_and_init_files(self, repo_path: Path, feature: Feature) -> tuple[list[Path], set[Path]]:
        files_to_process: list[Path] = []
        init_files: set[Path] = set()
        if not feature.source_tracking:
            return files_to_process, init_files
        for impl_file in feature.source_tracking.implementation_files:
            file_path = repo_path / impl_file
            if file_path.exists() and file_path.suffix == ".py":
                files_to_process.append(file_path)
        impl_dirs: set[Path] = set()
        for impl_file in feature.source_tracking.implementation_files:
            file_path = repo_path / impl_file
            if file_path.exists():
                impl_dirs.add(file_path.parent)
        for impl_dir in impl_dirs:
            init_file = impl_dir / "__init__.py"
            if init_file.exists():
                init_files.add(init_file)
        return files_to_process, init_files

    def _run_extract_endpoints_on_files(
        self, all_files: list[Path], openapi_spec: dict[str, Any], *, test_mode: bool
    ) -> None:
        if test_mode or len(all_files) == 0:
            for file_path in all_files:
                self._extract_endpoints_from_file(file_path, openapi_spec)
            return
        for file_path in all_files:
            with contextlib.suppress(Exception):
                self._extract_endpoints_from_file(file_path, openapi_spec)

    @beartype
    @require(lambda self, repo_path: isinstance(repo_path, Path), "Repository path must be Path")
    @require(lambda self, feature: isinstance(feature, Feature), "Feature must be Feature instance")
    @ensure(lambda self, feature, result: isinstance(result, dict), "Must return OpenAPI dict")
    def extract_openapi_from_code(self, repo_path: Path, feature: Feature) -> dict[str, Any]:
        """
        Extract OpenAPI contract from existing code using AST.

        Args:
            repo_path: Path to repository
            feature: Feature to extract contract for

        Returns:
            OpenAPI 3.0.3 specification as dictionary
        """
        # Start with basic OpenAPI structure
        openapi_spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": {
                "title": feature.title,
                "version": "1.0.0",
                "description": f"API contract extracted from code for {feature.title}",
            },
            "paths": {},
            "components": {"schemas": {}},
        }

        files_to_process, init_files = self._collect_py_files_and_init_files(repo_path, feature)
        test_mode = os.environ.get("TEST_MODE") == "true" or os.environ.get("PYTEST_CURRENT_TEST") is not None
        all_files = list(files_to_process) + list(init_files)
        self._run_extract_endpoints_on_files(all_files, openapi_spec, test_mode=test_mode)

        return openapi_spec

    def _has_api_endpoints(self, file_path: Path) -> bool:
        """
        Quick check if file likely has API endpoints before deep AST analysis.

        This optimization allows early exit for non-API files (models, utilities, etc.),
        avoiding expensive AST parsing and traversal.

        Args:
            file_path: Path to Python file

        Returns:
            True if file likely contains API endpoints, False otherwise
        """
        try:
            # Read first 4KB to check for API patterns (most API decorators are near top)
            with file_path.open(encoding="utf-8") as f:
                content_preview = f.read(4096)

            # Quick regex check for common API patterns
            return any(pattern.search(content_preview) for pattern in self._api_patterns)
        except Exception:
            # If we can't read the file, proceed with full analysis (safer)
            return True

    def _get_or_parse_file(self, file_path: Path) -> ast.AST | None:
        """
        Get cached AST or parse and cache file.

        This optimization prevents redundant AST parsing when the same file
        is processed by multiple features.

        Args:
            file_path: Path to Python file

        Returns:
            AST tree or None if parsing fails
        """
        # Check cache first (thread-safe, but minimize lock scope)
        cached_ast = None
        cached_hash = None
        with self._cache_lock:
            if file_path in self._ast_cache:
                cached_ast = self._ast_cache[file_path]
                cached_hash = self._file_hash_cache.get(file_path)

        # Verify file hasn't changed by checking hash (OUTSIDE lock to avoid blocking)
        # OPTIMIZATION: Only read file once, reuse content for parsing if needed
        if cached_ast is not None and cached_hash is not None:
            try:
                # Read file once
                with file_path.open(encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                current_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

                if current_hash == cached_hash:
                    # Cache hit - file unchanged
                    return cached_ast
                # File changed - will re-parse below using the content we just read
            except Exception:
                # If we can't verify, use cached AST (safer than failing)
                if cached_ast is not None:
                    return cached_ast
                # If we can't read, we'll try again below
                content = None
        else:
            # Cache miss - need to read file
            content = None

        # Cache miss or file changed - parse file (OUTSIDE lock)
        # OPTIMIZATION: Reuse content if we already read it for hash check
        try:
            if content is None:
                # Read file if we don't have content yet
                with file_path.open(encoding="utf-8") as f:
                    content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Cache the AST and hash (thread-safe, minimal lock scope)
            with self._cache_lock:
                # Update cache if file changed or not cached
                # Since we removed nested parallelism, we can safely update on hash change
                cached_hash = self._file_hash_cache.get(file_path)
                if cached_hash != file_hash:
                    # File changed or not cached - update cache
                    self._ast_cache[file_path] = tree
                    self._file_hash_cache[file_path] = file_hash
                else:
                    # Use cached version (file unchanged)
                    tree = self._ast_cache.get(file_path, tree)

            return tree
        except Exception:
            return None

    def _is_apirouter_assignment(self, node: ast.AST) -> bool:
        """Return True if node is a module-level ``router = APIRouter(...)`` assignment."""
        return (
            isinstance(node, ast.Assign)
            and bool(node.targets)
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "APIRouter"
        )

    def _parse_apirouter_keywords(self, keywords: list[ast.keyword]) -> tuple[str, list[str]]:
        """
        Parse ``prefix`` and ``tags`` keyword arguments from an APIRouter call.

        Args:
            keywords: Keyword argument list from the AST Call node

        Returns:
            Tuple of (prefix_string, tags_list)
        """
        prefix = ""
        tags_list: list[str] = []
        for kw in keywords:
            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                prefix_value = kw.value.value
                if isinstance(prefix_value, str):
                    prefix = prefix_value
            elif kw.arg == "tags" and isinstance(kw.value, ast.List):
                tags_list = [
                    str(elt.value)
                    for elt in kw.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
        return prefix, tags_list

    def _collect_router_prefixes(self, tree: ast.AST) -> tuple[dict[str, str], dict[str, list[str]]]:
        """
        Collect APIRouter instances and their prefix/tags from module-level assignments.

        Args:
            tree: Parsed AST of the module

        Returns:
            Tuple of (router_prefixes, router_tags) mappings
        """
        router_prefixes: dict[str, str] = {}
        router_tags: dict[str, list[str]] = {}
        for node in ast.iter_child_nodes(tree):
            if not self._is_apirouter_assignment(node):
                continue
            assign_node = cast(ast.Assign, node)
            target0 = assign_node.targets[0]
            if not isinstance(target0, ast.Name):
                continue
            router_name = target0.id
            val = assign_node.value
            if not isinstance(val, ast.Call):
                continue
            prefix, tags_list = self._parse_apirouter_keywords(val.keywords)
            if prefix:
                router_prefixes[router_name] = prefix
            if tags_list:
                router_tags[router_name] = tags_list
        return router_prefixes, router_tags

    def _resolve_fastapi_path_and_tags(
        self,
        decorator: ast.Call,
        router_prefixes: dict[str, str],
        router_tags: dict[str, list[str]],
    ) -> tuple[str, list[str]] | None:
        """
        Resolve the full path and tags for a FastAPI route decorator.

        Returns None if the path cannot be determined (missing or non-string constant arg).

        Args:
            decorator: FastAPI route decorator Call node
            router_prefixes: Known router prefix mappings
            router_tags: Known router tag mappings

        Returns:
            Tuple of (resolved_path, tags) or None
        """
        path_raw = _fastapi_decorator_first_path_str(decorator)
        if path_raw is None:
            return None
        path = _fastapi_apply_router_prefix(path_raw, decorator, router_prefixes)
        tags = _fastapi_resolve_route_tags(decorator, router_tags)
        return path, tags

    def _extract_fastapi_function_endpoint(
        self,
        node: ast.FunctionDef,
        decorator: ast.Call,
        openapi_spec: dict[str, Any],
        router_prefixes: dict[str, str],
        router_tags: dict[str, list[str]],
    ) -> None:
        """
        Extract a FastAPI route decorator endpoint from a function definition.

        Args:
            node: Function AST node
            decorator: Decorator call node (e.g. @app.get("/path"))
            openapi_spec: OpenAPI spec to update
            router_prefixes: Known router prefix mappings
            router_tags: Known router tag mappings
        """
        if not isinstance(decorator.func, ast.Attribute):
            return
        if decorator.func.attr not in ("get", "post", "put", "delete", "patch", "head", "options"):
            return
        method = decorator.func.attr.upper()

        resolved = self._resolve_fastapi_path_and_tags(decorator, router_prefixes, router_tags)
        if resolved is None:
            return
        raw_path, tags = resolved
        path, path_params = self._extract_path_parameters(raw_path)

        status_code = self._extract_status_code_from_decorator(decorator)
        security = self._extract_security_from_decorator(decorator)
        self._add_operation(
            openapi_spec,
            path,
            method,
            node,
            path_params=path_params,
            tags=tags,
            status_code=status_code,
            security=security,
        )

    @staticmethod
    def _flask_route_path_from_decorator(decorator: ast.Call) -> str:
        if decorator.args and isinstance(decorator.args[0], ast.Constant):
            raw = decorator.args[0].value
            return raw if isinstance(raw, str) else ""
        return ""

    @staticmethod
    def _flask_methods_from_decorator(decorator: ast.Call) -> list[str]:
        for kw in decorator.keywords:
            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                return [
                    elt.value.upper()
                    for elt in kw.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
        return ["GET"]

    def _extract_flask_function_endpoint(
        self,
        node: ast.FunctionDef,
        decorator: ast.Call,
        openapi_spec: dict[str, Any],
    ) -> None:
        """
        Extract a Flask @app.route decorator endpoint from a function definition.

        Args:
            node: Function AST node
            decorator: Decorator call node (e.g. @app.route("/path", methods=["GET"]))
            openapi_spec: OpenAPI spec to update
        """
        if not isinstance(decorator.func, ast.Attribute) or decorator.func.attr != "route":
            return
        path = self._flask_route_path_from_decorator(decorator)
        methods = self._flask_methods_from_decorator(decorator)
        if not path:
            return
        path, path_params = self._extract_path_parameters(path, flask_format=True)
        for method in methods:
            self._add_operation(openapi_spec, path, method, node, path_params=path_params)

    def _infer_http_method(self, method_name_lower: str) -> str:
        """
        Infer HTTP method from a Python method name using CRUD verb heuristics.

        Args:
            method_name_lower: Lower-cased method name

        Returns:
            HTTP method string (``"GET"``, ``"POST"``, ``"PUT"``, or ``"DELETE"``)
        """
        if any(verb in method_name_lower for verb in ["create", "add", "new", "post"]):
            return "POST"
        if any(verb in method_name_lower for verb in ["update", "modify", "edit", "put", "patch"]):
            return "PUT"
        if any(verb in method_name_lower for verb in ["delete", "remove", "destroy"]):
            return "DELETE"
        return "GET"

    def _append_id_path_segments(self, base_path: str, args: ast.arguments) -> str:
        """
        Append ``{param}`` segments to a path for ID-like positional arguments.

        Args:
            base_path: Starting path string
            args: Function argument spec

        Returns:
            Extended path with ``{param}`` segments appended
        """
        path = base_path
        for arg in args.args:
            if arg.arg != "self" and arg.arg not in ["cls"] and arg.arg in ["id", "key", "name", "slug", "uuid"]:
                path = f"{path}/{{{arg.arg}}}"
        return path

    def _extract_interface_endpoints(self, node: ast.ClassDef, openapi_spec: dict[str, Any]) -> None:
        """
        Extract endpoints from an abstract interface class (ABC/Protocol).

        Each abstract method becomes a potential endpoint with an inferred HTTP method
        and path derived from the method name.

        Args:
            node: ClassDef node that represents an interface
            openapi_spec: OpenAPI spec to update
        """
        abstract_methods = [
            child
            for child in node.body
            if isinstance(child, ast.FunctionDef)
            and any(isinstance(dec, ast.Name) and dec.id == "abstractmethod" for dec in child.decorator_list)
        ]
        if not abstract_methods:
            return
        base_path = f"/{re.sub(r'(?<!^)(?=[A-Z])', '-', node.name).lower()}"
        for method in abstract_methods:
            method_path = self._append_id_path_segments(base_path, method.args)
            http_method = self._infer_http_method(method.name.lower())
            path, path_params = self._extract_path_parameters(method_path)
            self._add_operation(
                openapi_spec,
                path,
                http_method,
                method,
                path_params=path_params,
                tags=[node.name],
                status_code=None,
                security=None,
            )

    def _collect_class_api_methods(self, node: ast.ClassDef) -> list[ast.FunctionDef]:
        """
        Collect public methods from a class that look like API endpoints.

        Returns an empty list if the class looks like a utility/library class
        (too many methods) or if no CRUD-like methods are found.

        Args:
            node: ClassDef AST node

        Returns:
            List of FunctionDef nodes that are candidate API methods
        """
        skip_method_patterns = [
            "processor",
            "adapter",
            "factory",
            "builder",
            "helper",
            "validator",
            "converter",
            "serializer",
            "deserializer",
            "get_",
            "set_",
            "has_",
            "is_",
            "can_",
            "should_",
            "copy",
            "clone",
            "adapt",
            "coerce",
            "compare",
            "compile",
            "dialect",
            "variant",
            "resolve",
            "literal",
            "bind",
            "result",
        ]
        class_methods: list[ast.FunctionDef] = []
        for child in node.body:
            if not isinstance(child, ast.FunctionDef) or child.name.startswith("_"):
                continue
            method_name_lower = child.name.lower()
            if any(pattern in method_name_lower for pattern in skip_method_patterns):
                continue
            is_crud_like = any(
                verb in method_name_lower
                for verb in ["create", "add", "update", "delete", "remove", "fetch", "list", "save"]
            )
            is_short_api_like = len(method_name_lower.split("_")) <= 2 and method_name_lower not in [
                "copy",
                "clone",
                "adapt",
                "coerce",
            ]
            if is_crud_like or is_short_api_like:
                class_methods.append(child)
        max_methods_per_class = 15
        if len(class_methods) > max_methods_per_class:
            return []
        return class_methods

    def _resolve_method_path_segment(self, method_name_lower: str, base_path: str) -> str:
        """
        Compute the path segment for a class method, stripping common CRUD prefixes.

        Args:
            method_name_lower: Lower-cased method name
            base_path: Base path derived from class name

        Returns:
            Full path string including any sub-resource segment
        """
        canonical_names = {"create", "list", "get", "update", "delete"}
        if method_name_lower in canonical_names:
            return base_path
        method_segment = method_name_lower.replace("_", "-")
        for prefix in ["get_", "create_", "update_", "delete_", "fetch_", "retrieve_"]:
            if method_segment.startswith(prefix):
                method_segment = method_segment[len(prefix) :]
                break
        if method_segment:
            return f"{base_path}/{method_segment}"
        return base_path

    def _extract_class_method_endpoint(
        self,
        node: ast.ClassDef,
        method: ast.FunctionDef,
        base_path: str,
        openapi_spec: dict[str, Any],
    ) -> None:
        """
        Extract a single class method as an API endpoint.

        Args:
            node: Parent ClassDef node (used for tag name)
            method: FunctionDef node to convert to an endpoint
            base_path: Base path derived from class name (e.g. "/user-manager")
            openapi_spec: OpenAPI spec to update
        """
        if method.name.startswith("__") and method.name != "__init__":
            return
        method_name_lower = method.name.lower()
        http_method = self._infer_http_method(method_name_lower)
        method_path = self._resolve_method_path_segment(method_name_lower, base_path)
        method_path = self._append_id_path_segments(method_path, method.args)
        path, path_params = self._extract_path_parameters(method_path)
        self._add_operation(
            openapi_spec,
            path,
            http_method,
            method,
            path_params=path_params,
            tags=[node.name],
            status_code=None,
            security=None,
        )

    def _process_top_level_node_for_endpoints(
        self,
        node: ast.AST,
        openapi_spec: dict[str, Any],
        router_prefixes: dict[str, str],
        router_tags: dict[str, list[str]],
    ) -> None:
        if isinstance(node, ast.ClassDef) and self._is_pydantic_model(node):
            self._extract_pydantic_model_schema(node, openapi_spec)
            return
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if not (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)):
                    continue
                if decorator.func.attr in ("get", "post", "put", "delete", "patch", "head", "options"):
                    self._extract_fastapi_function_endpoint(node, decorator, openapi_spec, router_prefixes, router_tags)
                elif decorator.func.attr == "route":
                    self._extract_flask_function_endpoint(node, decorator, openapi_spec)
            return
        if isinstance(node, ast.ClassDef):
            self._extract_endpoints_from_class(node, openapi_spec)

    def _extract_endpoints_from_file(self, file_path: Path, openapi_spec: dict[str, Any]) -> None:
        """
        Extract API endpoints from a Python file using AST.

        Args:
            file_path: Path to Python file
            openapi_spec: OpenAPI spec dictionary to update
        """
        # Note: Early exit optimization disabled - too aggressive for class-based APIs
        # The extractor also processes class-based APIs and interfaces, not just decorator-based APIs
        # Early exit would skip these valid cases. AST caching provides sufficient performance benefit.

        # Use cached AST or parse and cache
        tree = self._get_or_parse_file(file_path)
        if tree is None:
            return

        try:
            router_prefixes, router_tags = self._collect_router_prefixes(tree)
            for node in ast.iter_child_nodes(tree):
                self._process_top_level_node_for_endpoints(node, openapi_spec, router_prefixes, router_tags)

        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors
            pass

    def _is_interface_class(self, node: ast.ClassDef) -> bool:
        """
        Return True if the class explicitly inherits from ABC, Protocol, AbstractBase, or Interface.

        Args:
            node: ClassDef AST node to inspect
        """
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ["ABC", "Protocol", "AbstractBase", "Interface"]:
                return True
            if isinstance(base, ast.Attribute) and base.attr in ["Protocol", "ABC"]:
                return True
        return False

    def _has_skip_base(self, node: ast.ClassDef) -> bool:
        """
        Return True if any base class name matches patterns that should be skipped.

        Args:
            node: ClassDef AST node to inspect
        """
        skip_base_patterns = ["Protocol", "TypedDict", "Enum", "ABC"]
        for base in node.bases:
            base_name = (
                base.id if isinstance(base, ast.Name) else (base.attr if isinstance(base, ast.Attribute) else "")
            )
            if any(pattern in base_name for pattern in skip_base_patterns):
                return True
        return False

    @staticmethod
    def _should_skip_endpoint_class_name(name: str) -> bool:
        if name.startswith(("_", "Test")):
            return True
        skip_class_patterns = (
            "Protocol",
            "TypedDict",
            "Enum",
            "ABC",
            "AbstractBase",
            "Mixin",
            "Base",
            "Meta",
            "Descriptor",
            "Property",
        )
        return any(pattern in name for pattern in skip_class_patterns)

    def _extract_endpoints_from_class(self, node: ast.ClassDef, openapi_spec: dict[str, Any]) -> None:
        """
        Extract API endpoints from a single class definition (interface or class-based API).

        Args:
            node: ClassDef AST node
            openapi_spec: OpenAPI spec dictionary to update
        """
        if self._should_skip_endpoint_class_name(node.name):
            return

        is_interface = self._is_interface_class(node)
        if not is_interface and self._has_skip_base(node):
            return

        if is_interface:
            self._extract_interface_endpoints(node, openapi_spec)
            return

        class_methods = self._collect_class_api_methods(node)
        if not class_methods:
            return

        base_path = re.sub(r"(?<!^)(?=[A-Z])", "-", node.name).lower()
        base_path = f"/{base_path}"
        for method in class_methods:
            self._extract_class_method_endpoint(node, method, base_path, openapi_spec)

    def _extract_path_parameters(self, path: str, flask_format: bool = False) -> tuple[str, list[dict[str, Any]]]:
        """
        Extract path parameters from route path.

        Args:
            path: Route path (e.g., "/users/{user_id}" or "/users/<int:user_id>")
            flask_format: If True, parse Flask format (<int:user_id>), else FastAPI format ({user_id})

        Returns:
            Tuple of (normalized_path, path_parameters)
        """
        path_params: list[dict[str, Any]] = []
        normalized_path = path

        if flask_format:
            # Flask format: /users/<int:user_id> or /users/<user_id>
            import re

            pattern = r"<(?:(?P<type>\w+):)?(?P<name>\w+)>"
            matches = re.finditer(pattern, path)
            for match in matches:
                param_type = match.group("type") or "string"
                param_name = match.group("name")
                # Convert Flask type to OpenAPI type
                type_map = {"int": "integer", "float": "number", "str": "string", "string": "string"}
                openapi_type = type_map.get(param_type.lower(), "string")
                path_params.append(
                    {"name": param_name, "in": "path", "required": True, "schema": {"type": openapi_type}}
                )
                # Replace with OpenAPI format
                normalized_path = normalized_path.replace(match.group(0), f"{{{param_name}}}")
        else:
            # FastAPI format: /users/{user_id}
            import re

            pattern = r"\{(\w+)\}"
            matches = re.finditer(pattern, path)
            for match in matches:
                param_name = match.group(1)
                path_params.append({"name": param_name, "in": "path", "required": True, "schema": {"type": "string"}})

        return normalized_path, path_params

    def _type_hint_schema_from_name(self, type_node: ast.Name) -> dict[str, Any]:
        type_name = type_node.id
        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "dict": "object",
            "list": "array",
            "Any": "object",
        }
        if type_name in type_map:
            return {"type": type_map[type_name]}
        return {"$ref": f"#/components/schemas/{type_name}"}

    def _type_hint_schema_from_subscript(self, type_node: ast.Subscript) -> dict[str, Any] | None:
        if not isinstance(type_node.value, ast.Name):
            return None
        value_id = type_node.value.id
        if value_id in ("Optional", "Union"):
            if isinstance(type_node.slice, ast.Tuple) and type_node.slice.elts:
                return self._extract_type_hint_schema(type_node.slice.elts[0])
            if isinstance(type_node.slice, ast.Name):
                return self._extract_type_hint_schema(type_node.slice)
            return None
        if value_id == "list":
            if isinstance(type_node.slice, ast.Name):
                item_schema = self._extract_type_hint_schema(type_node.slice)
                return {"type": "array", "items": item_schema}
            if isinstance(type_node.slice, ast.Subscript):
                item_schema = self._extract_type_hint_schema(type_node.slice)
                return {"type": "array", "items": item_schema}
            return None
        if value_id == "dict":
            return {"type": "object", "additionalProperties": True}
        return None

    def _extract_type_hint_schema(self, type_node: ast.expr | None) -> dict[str, Any]:
        """
        Extract OpenAPI schema from AST type hint.

        Args:
            type_node: AST node representing type hint

        Returns:
            OpenAPI schema dictionary
        """
        if type_node is None:
            return {"type": "object"}

        if isinstance(type_node, ast.Name):
            return self._type_hint_schema_from_name(type_node)

        if isinstance(type_node, ast.Subscript):
            sub = self._type_hint_schema_from_subscript(type_node)
            if sub is not None:
                return sub

        if isinstance(type_node, ast.Constant):
            return {"type": "object"}

        return {"type": "object"}

    def _is_pydantic_model(self, class_node: ast.ClassDef) -> bool:
        """
        Check if a class is a Pydantic model (inherits from BaseModel).

        Args:
            class_node: AST ClassDef node

        Returns:
            True if class is a Pydantic model, False otherwise
        """
        for base in class_node.bases:
            # Check for direct BaseModel inheritance: class User(BaseModel)
            if isinstance(base, ast.Name) and base.id == "BaseModel":
                return True
            # Check for pydantic.BaseModel: class User(pydantic.BaseModel)
            if isinstance(base, ast.Attribute):
                if isinstance(base.value, ast.Name) and base.value.id == "pydantic" and base.attr == "BaseModel":
                    return True
                # Check for from pydantic import BaseModel: class User(BaseModel)
                if base.attr == "BaseModel":
                    return True
        return False

    def _pydantic_ann_assign_to_schema(self, item: ast.AnnAssign, schema: dict[str, Any]) -> None:
        if not item.target or not isinstance(item.target, ast.Name):
            return
        field_name = item.target.id
        field_schema = self._extract_type_hint_schema(item.annotation)
        schema["properties"][field_name] = field_schema
        if item.value is None:
            schema["required"].append(field_name)
            return
        default_value = self._extract_default_value(item.value)
        if default_value is not None:
            schema["properties"][field_name]["default"] = default_value

    def _pydantic_assign_to_schema(self, item: ast.Assign, schema: dict[str, Any]) -> None:
        for target in item.targets:
            if not isinstance(target, ast.Name):
                continue
            field_name = target.id
            if not item.value:
                continue
            field_schema = self._infer_schema_from_value(item.value)
            if field_schema:
                schema["properties"][field_name] = field_schema
                default_value = self._extract_default_value(item.value)
                if default_value is not None:
                    schema["properties"][field_name]["default"] = default_value
            else:
                schema["properties"][field_name] = {"type": "object"}

    def _extract_pydantic_model_schema(self, class_node: ast.ClassDef, openapi_spec: dict[str, Any]) -> None:
        """
        Extract OpenAPI schema from a Pydantic model class definition.

        Args:
            class_node: AST ClassDef node representing Pydantic model
            openapi_spec: OpenAPI spec dictionary to update
        """
        schema_name = class_node.name
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        # Extract docstring for description
        docstring = ast.get_docstring(class_node)
        if docstring:
            schema["description"] = docstring

        for item in class_node.body:
            if isinstance(item, ast.AnnAssign):
                self._pydantic_ann_assign_to_schema(item, schema)
            elif isinstance(item, ast.Assign):
                self._pydantic_assign_to_schema(item, schema)

        if "components" not in openapi_spec:
            openapi_spec["components"] = {}
        if "schemas" not in openapi_spec["components"]:
            openapi_spec["components"]["schemas"] = {}

        openapi_spec["components"]["schemas"][schema_name] = schema

    def _extract_default_value(self, value_node: ast.expr) -> Any:
        """
        Extract default value from AST expression.

        Args:
            value_node: AST expression node

        Returns:
            Default value if extractable, None otherwise
        """
        if isinstance(value_node, ast.Constant):
            return value_node.value
        # Python < 3.8 compatibility - suppress deprecation warning
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            # ast.NameConstant is deprecated in Python 3.8+, removed in 3.14
            # Keep for backward compatibility with older Python versions
            if hasattr(ast, "NameConstant") and isinstance(value_node, ast.NameConstant):
                return value_node.value
        if isinstance(value_node, ast.Name) and value_node.id == "None":
            return None
        return None

    def _infer_schema_from_value(self, value_node: ast.expr) -> dict[str, Any] | None:
        """
        Infer OpenAPI schema from AST value node.

        Args:
            value_node: AST expression node

        Returns:
            OpenAPI schema dictionary or None if type can't be inferred
        """
        if isinstance(value_node, ast.Constant):
            value = value_node.value
            if isinstance(value, str):
                return {"type": "string"}
            if isinstance(value, int):
                return {"type": "integer"}
            if isinstance(value, float):
                return {"type": "number"}
            if isinstance(value, bool):
                return {"type": "boolean"}
            if isinstance(value, list):
                return {"type": "array", "items": {"type": "object"}}
            if isinstance(value, dict):
                return {"type": "object"}

        if isinstance(value_node, ast.List):
            return {"type": "array", "items": {"type": "object"}}
        if isinstance(value_node, ast.Dict):
            return {"type": "object"}

        return None

    def _extract_status_code_from_decorator(self, decorator: ast.Call) -> int | None:
        """
        Extract status code from FastAPI decorator.

        Args:
            decorator: AST Call node representing decorator

        Returns:
            Status code if found, None otherwise
        """
        for kw in decorator.keywords:
            if kw.arg == "status_code" and isinstance(kw.value, ast.Constant):
                status_value = kw.value.value
                if isinstance(status_value, int):
                    return status_value
        return None

    def _extract_security_from_decorator(self, decorator: ast.Call) -> list[dict[str, list[str]]] | None:
        """
        Extract security requirements from FastAPI decorator.

        Args:
            decorator: AST Call node representing decorator

        Returns:
            List of security requirements if found, None otherwise
        """
        for kw in decorator.keywords:
            if kw.arg == "dependencies" and isinstance(kw.value, ast.List):
                # Check for security dependencies (simplified detection)
                # In real FastAPI, this would be Depends(Security(...))
                # For now, we'll detect common patterns
                security: list[dict[str, list[str]]] = []
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Call) and isinstance(elt.func, ast.Name) and elt.func.id == "Depends":
                        # This is a simplified detection - in practice, would need deeper AST analysis
                        security.append({"bearerAuth": []})
                if security:
                    return security
        return None

    def _extract_function_parameters(
        self, func_node: ast.FunctionDef, path_param_names: set[str]
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]], dict[str, Any] | None]:
        """
        Extract request body, query parameters, and response schema from function parameters.

        Args:
            func_node: Function AST node
            path_param_names: Set of path parameter names (to exclude from query params)

        Returns:
            Tuple of (request_body_schema, query_parameters, response_schema)
        """
        request_body: dict[str, Any] | None = None
        query_params: list[dict[str, Any]] = []
        response_schema: dict[str, Any] | None = None

        # Extract request body from function parameters
        # FastAPI convention: first parameter without default is request body for POST/PUT/PATCH
        # Parameters with defaults are query parameters
        body_param_found = False
        for i, arg in enumerate(func_node.args.args):
            if arg.arg == "self":
                continue

            # Skip path parameters
            if arg.arg in path_param_names:
                continue

            # Get type hint
            type_hint = None
            if arg.annotation:
                type_hint = arg.annotation

            # Check for default value (indicates query parameter)
            has_default = i >= (len(func_node.args.args) - len(func_node.args.defaults))

            if has_default:
                # Query parameter
                param_schema = self._extract_type_hint_schema(type_hint)

                query_params.append(
                    {
                        "name": arg.arg,
                        "in": "query",
                        "required": False,
                        "schema": param_schema,
                        "description": f"Query parameter: {arg.arg}",
                    }
                )
            elif not body_param_found and type_hint:
                # First non-path parameter without default is likely request body
                # Check if it's a Pydantic model (complex type)
                body_schema = self._extract_type_hint_schema(type_hint)
                request_body = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": body_schema,
                        }
                    },
                }
                body_param_found = True

        # Extract response schema from return type hint
        if func_node.returns:
            response_schema = self._extract_type_hint_schema(func_node.returns)

        return request_body, query_params, response_schema

    @staticmethod
    def _merge_standard_error_responses(operation: dict[str, Any], method: str) -> None:
        responses = operation["responses"]
        if method in ("POST", "PUT", "PATCH"):
            responses["400"] = {"description": "Bad Request"}
            responses["422"] = {"description": "Validation Error"}
        if method in ("GET", "PUT", "PATCH", "DELETE"):
            responses["404"] = {"description": "Not Found"}
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            responses["401"] = {"description": "Unauthorized"}
            responses["403"] = {"description": "Forbidden"}
            responses["500"] = {"description": "Internal Server Error"}

    def _ensure_bearer_security_scheme(
        self, openapi_spec: dict[str, Any], security: list[dict[str, list[str]]] | None
    ) -> None:
        if not security:
            return
        if not any("bearerAuth" in sec_req for sec_req in security):
            return
        openapi_spec.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }

    @staticmethod
    def _attach_operation_request_body(
        operation: dict[str, Any], method: str, request_body: dict[str, Any] | None
    ) -> None:
        if method not in ("POST", "PUT", "PATCH"):
            return
        if request_body:
            operation["requestBody"] = request_body
            return
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {},
                    }
                }
            },
        }

    def _add_operation(
        self,
        openapi_spec: dict[str, Any],
        path: str,
        method: str,
        func_node: ast.FunctionDef,
        path_params: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
        status_code: int | None = None,
        security: list[dict[str, list[str]]] | None = None,
    ) -> None:
        """
        Add operation to OpenAPI spec.

        Args:
            openapi_spec: OpenAPI spec dictionary
            path: API path
            method: HTTP method
            func_node: Function AST node
            path_params: Path parameters (if any)
            tags: Operation tags (if any)
        """
        openapi_spec["paths"].setdefault(path, {})
        path_param_names = {p["name"] for p in (path_params or [])}
        request_body, query_params, response_schema = self._extract_function_parameters(func_node, path_param_names)
        default_status = status_code or 200
        operation: dict[str, Any] = {
            "operationId": func_node.name,
            "summary": func_node.name.replace("_", " ").title(),
            "description": ast.get_docstring(func_node) or "",
            "responses": {
                str(default_status): {
                    "description": "Success" if default_status == 200 else f"Status {default_status}",
                    "content": {
                        "application/json": {
                            "schema": response_schema or {"type": "object"},
                        }
                    },
                }
            },
        }
        self._merge_standard_error_responses(operation, method)
        all_params = list(path_params or [])
        all_params.extend(query_params)
        if all_params:
            operation["parameters"] = all_params
        if tags:
            operation["tags"] = tags
        if security:
            operation["security"] = security
            self._ensure_bearer_security_scheme(openapi_spec, security)
        self._attach_operation_request_body(operation, method, request_body)
        openapi_spec["paths"][path][method.lower()] = operation

    @beartype
    @require(lambda self, contract_path: isinstance(contract_path, Path), "Contract path must be Path")
    @ensure(
        lambda self, contract_path, result: isinstance(result, SpecValidationResult), "Must return SpecValidationResult"
    )
    async def validate_with_specmatic(self, contract_path: Path) -> SpecValidationResult:
        """
        Validate OpenAPI contract using Specmatic.

        Args:
            contract_path: Path to OpenAPI contract file

        Returns:
            SpecValidationResult with validation status
        """
        return await validate_spec_with_specmatic(contract_path)

    @beartype
    @require(lambda self, openapi_spec: isinstance(openapi_spec, dict), "OpenAPI spec must be dict")
    @require(lambda test_examples: isinstance(test_examples, dict), "Test examples must be dict")
    @ensure(lambda result: isinstance(result, dict), "Must return OpenAPI dict")
    def add_test_examples(self, openapi_spec: dict[str, Any], test_examples: dict[str, Any]) -> dict[str, Any]:
        """
        Add test examples to OpenAPI specification.

        Args:
            openapi_spec: OpenAPI specification dictionary
            test_examples: Dictionary mapping operation IDs to example data

        Returns:
            Updated OpenAPI specification with examples
        """
        # Add examples to operations
        paths_raw = openapi_spec.get("paths", {})
        if not isinstance(paths_raw, dict):
            return openapi_spec
        paths_dict: dict[str, Any] = cast(dict[str, Any], paths_raw)
        for _path, path_item_any in paths_dict.items():
            if not isinstance(path_item_any, dict):
                continue
            path_item: dict[str, Any] = cast(dict[str, Any], path_item_any)
            for _method, operation_any in path_item.items():
                if not isinstance(operation_any, dict):
                    continue
                operation: dict[str, Any] = cast(dict[str, Any], operation_any)

                operation_id = operation.get("operationId")
                if not operation_id or operation_id not in test_examples:
                    continue

                example_data_any = test_examples[operation_id]
                if not isinstance(example_data_any, dict):
                    continue
                example_data: dict[str, Any] = cast(dict[str, Any], example_data_any)

                _merge_request_test_example_into_operation(operation, example_data)
                _merge_response_test_example_into_operation(operation, example_data)

        return openapi_spec

    @beartype
    @require(lambda self, openapi_spec: isinstance(openapi_spec, dict), "OpenAPI spec must be dict")
    @require(lambda self, output_path: isinstance(output_path, Path), "Output path must be Path")
    @ensure(lambda result: result is None, "Must return None")
    def save_openapi_contract(self, openapi_spec: dict[str, Any], output_path: Path) -> None:
        """
        Save OpenAPI contract to file.

        Args:
            openapi_spec: OpenAPI specification dictionary
            output_path: Path to save contract file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            yaml.dump(openapi_spec, f, default_flow_style=False, sort_keys=False)
