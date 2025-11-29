"""
OpenAPI contract extractor.

This module provides utilities for extracting OpenAPI 3.0.3 contracts from
verbose acceptance criteria or existing code using AST analysis.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure, require

from specfact_cli.integrations.specmatic import SpecValidationResult, validate_spec_with_specmatic
from specfact_cli.models.plan import Feature


class OpenAPIExtractor:
    """Extractor for generating OpenAPI contracts from features."""

    def __init__(self, repo_path: Path) -> None:
        """
        Initialize extractor with repository path.

        Args:
            repo_path: Path to repository root
        """
        self.repo_path = repo_path.resolve()

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

        # Use source tracking to find implementation files
        if feature.source_tracking:
            for impl_file in feature.source_tracking.implementation_files:
                file_path = repo_path / impl_file
                if file_path.exists() and file_path.suffix == ".py":
                    self._extract_endpoints_from_file(file_path, openapi_spec)

        # Also check __init__.py files in the same directory for module-level interfaces
        if feature.source_tracking:
            # Get unique directories from implementation files
            impl_dirs = set()
            for impl_file in feature.source_tracking.implementation_files:
                file_path = repo_path / impl_file
                if file_path.exists():
                    impl_dirs.add(file_path.parent)

            # Check __init__.py in each directory for module-level exports/interfaces
            for impl_dir in impl_dirs:
                init_file = impl_dir / "__init__.py"
                if init_file.exists():
                    self._extract_endpoints_from_file(init_file, openapi_spec)

        return openapi_spec

    def _extract_endpoints_from_file(self, file_path: Path, openapi_spec: dict[str, Any]) -> None:
        """
        Extract API endpoints from a Python file using AST.

        Args:
            file_path: Path to Python file
            openapi_spec: OpenAPI spec dictionary to update
        """
        try:
            with file_path.open(encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            # Track router instances and their prefixes
            router_prefixes: dict[str, str] = {}  # router_name -> prefix
            router_tags: dict[str, list[str]] = {}  # router_name -> tags

            # First pass: Find router instances and their prefixes (use iter_child_nodes for efficiency)
            for node in ast.iter_child_nodes(tree):
                if (
                    isinstance(node, ast.Assign)
                    and node.targets
                    and isinstance(node.targets[0], ast.Name)
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "APIRouter"
                ):
                    # Check for APIRouter instantiation: router = APIRouter(prefix="/api")
                    router_name = node.targets[0].id
                    prefix = ""
                    router_tags_list: list[str] = []
                    # Extract prefix from keyword arguments
                    for kw in node.value.keywords:
                        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                            prefix_value = kw.value.value
                            if isinstance(prefix_value, str):
                                prefix = prefix_value
                        elif kw.arg == "tags" and isinstance(kw.value, ast.List):
                            router_tags_list = [
                                str(elt.value)
                                for elt in kw.value.elts
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                            ]
                    if prefix:
                        router_prefixes[router_name] = prefix
                    if router_tags_list:
                        router_tags[router_name] = router_tags_list

            # Second pass: Extract endpoints from functions and class methods (use iter_child_nodes for efficiency)
            # Note: We need to walk recursively for nested classes, but we'll do it more efficiently
            def extract_from_node(node: ast.AST) -> None:
                """Recursively extract endpoints from AST node."""
                if isinstance(node, ast.Module):
                    # Start from module level
                    for child in node.body:
                        extract_from_node(child)
                elif isinstance(node, ast.ClassDef):
                    # Process class and its methods
                    for child in node.body:
                        extract_from_node(child)
                elif isinstance(node, ast.FunctionDef):
                    # Process function
                    pass  # Will be handled below

            # Use more efficient iteration - only walk what we need
            for node in ast.iter_child_nodes(tree):
                # Extract from function definitions (module-level or class methods)
                if isinstance(node, ast.FunctionDef):
                    # Check for decorators that indicate HTTP routes
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            # FastAPI: @app.get("/path") or @router.get("/path")
                            if decorator.func.attr in ("get", "post", "put", "delete", "patch", "head", "options"):
                                method = decorator.func.attr.upper()
                                # Extract path from first argument
                                if decorator.args:
                                    path_arg = decorator.args[0]
                                    if isinstance(path_arg, ast.Constant):
                                        path = path_arg.value
                                        if isinstance(path, str):
                                            # Check if this is a router method (router.get vs app.get)
                                            if isinstance(decorator.func.value, ast.Name):
                                                router_name = decorator.func.value.id
                                                if router_name in router_prefixes:
                                                    path = router_prefixes[router_name] + path
                                            # Extract path parameters
                                            path, path_params = self._extract_path_parameters(path)
                                            # Extract tags if router has them
                                            tags: list[str] = []
                                            if isinstance(decorator.func.value, ast.Name):
                                                router_name = decorator.func.value.id
                                                if router_name in router_tags:
                                                    tags = router_tags[router_name]
                                            # Extract tags from decorator kwargs
                                            for kw in decorator.keywords:
                                                if kw.arg == "tags" and isinstance(kw.value, ast.List):
                                                    tags = [
                                                        str(elt.value)
                                                        for elt in kw.value.elts
                                                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                                                    ]
                                            # Extract status code
                                            status_code = self._extract_status_code_from_decorator(decorator)
                                            # Extract security
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
                            # Flask: @app.route("/path", methods=["GET"])
                            elif decorator.func.attr == "route":
                                # Extract path from first argument
                                path = ""
                                methods: list[str] = ["GET"]  # Default to GET
                                if decorator.args:
                                    path_arg = decorator.args[0]
                                    if isinstance(path_arg, ast.Constant):
                                        path = path_arg.value
                                # Extract methods from keyword arguments
                                for kw in decorator.keywords:
                                    if kw.arg == "methods" and isinstance(kw.value, ast.List):
                                        methods = [
                                            elt.value.upper()
                                            for elt in kw.value.elts
                                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                                        ]
                                if path and isinstance(path, str):
                                    # Extract path parameters (Flask: /users/<int:user_id>)
                                    path, path_params = self._extract_path_parameters(path, flask_format=True)
                                    for method in methods:
                                        self._add_operation(openapi_spec, path, method, node, path_params=path_params)

                # Extract from class definitions (class-based APIs)
                # Pattern: Classes represent APIs, methods represent endpoints
                elif isinstance(node, ast.ClassDef):
                    # Skip private classes and test classes
                    if node.name.startswith("_") or node.name.startswith("Test"):
                        continue

                    # Check if class is an abstract base class or protocol (interface)
                    is_interface = False
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id in ["ABC", "Protocol", "AbstractBase", "Interface"]:
                            # Check for ABC, Protocol, or abstract base classes
                            is_interface = True
                            break
                        if isinstance(base, ast.Attribute) and base.attr in ["Protocol", "ABC"]:
                            # Check for typing.Protocol, abc.ABC, etc.
                            is_interface = True
                            break

                    # For interfaces, extract abstract methods as potential endpoints
                    if is_interface:
                        abstract_methods = [
                            child
                            for child in node.body
                            if isinstance(child, ast.FunctionDef)
                            and any(
                                isinstance(dec, ast.Name) and dec.id == "abstractmethod" for dec in child.decorator_list
                            )
                        ]
                        if abstract_methods:
                            # Generate base path from interface name
                            base_path = re.sub(r"(?<!^)(?=[A-Z])", "-", node.name).lower()
                            base_path = f"/{base_path}"

                            for method in abstract_methods:
                                # Generate path from method name
                                method_name_lower = method.name.lower()
                                method_path = base_path

                                # Determine HTTP method from method name
                                http_method = "GET"
                                if any(verb in method_name_lower for verb in ["create", "add", "new", "post"]):
                                    http_method = "POST"
                                elif any(
                                    verb in method_name_lower for verb in ["update", "modify", "edit", "put", "patch"]
                                ):
                                    http_method = "PUT"
                                elif any(verb in method_name_lower for verb in ["delete", "remove", "destroy"]):
                                    http_method = "DELETE"

                                # Extract path parameters
                                path_param_names = set()
                                for arg in method.args.args:
                                    if (
                                        arg.arg != "self"
                                        and arg.arg not in ["cls"]
                                        and arg.arg in ["id", "key", "name", "slug", "uuid"]
                                    ):
                                        path_param_names.add(arg.arg)
                                        method_path = f"{method_path}/{{{arg.arg}}}"

                                path, path_params = self._extract_path_parameters(method_path)

                                # Use interface name as tag
                                tags = [node.name]

                                # Add operation
                                self._add_operation(
                                    openapi_spec,
                                    path,
                                    http_method,
                                    method,
                                    path_params=path_params,
                                    tags=tags,
                                    status_code=None,
                                    security=None,
                                )
                        continue  # Skip regular class processing for interfaces

                    # Check if class has methods that could be API endpoints
                    # Look for public methods (not starting with _)
                    class_methods = [
                        child
                        for child in node.body
                        if isinstance(child, ast.FunctionDef) and not child.name.startswith("_")
                    ]

                    if class_methods:
                        # Generate base path from class name (e.g., UserManager -> /users)
                        # Convert CamelCase to kebab-case for path
                        base_path = re.sub(r"(?<!^)(?=[A-Z])", "-", node.name).lower()
                        base_path = f"/{base_path}"

                        # Extract endpoints from class methods
                        for method in class_methods:
                            # Skip special methods except __init__
                            if method.name.startswith("__") and method.name != "__init__":
                                continue

                            # Generate path from method name
                            # Pattern: get_user -> GET /users/user, create_user -> POST /users
                            method_name_lower = method.name.lower()
                            method_path = base_path

                            # Determine HTTP method from method name
                            http_method = "GET"  # Default
                            if any(verb in method_name_lower for verb in ["create", "add", "new", "post"]):
                                http_method = "POST"
                            elif any(
                                verb in method_name_lower for verb in ["update", "modify", "edit", "put", "patch"]
                            ):
                                http_method = "PUT"
                            elif any(verb in method_name_lower for verb in ["delete", "remove", "destroy"]):
                                http_method = "DELETE"
                            elif any(
                                verb in method_name_lower for verb in ["get", "fetch", "retrieve", "read", "list"]
                            ):
                                http_method = "GET"

                            # Add method-specific path segment for non-CRUD operations
                            if method_name_lower not in ["create", "list", "get", "update", "delete"]:
                                # Extract resource name from method (e.g., get_user_by_id -> user-by-id)
                                method_segment = method_name_lower.replace("_", "-")
                                # Remove common prefixes
                                for prefix in ["get_", "create_", "update_", "delete_", "fetch_", "retrieve_"]:
                                    if method_segment.startswith(prefix):
                                        method_segment = method_segment[len(prefix) :]
                                        break
                                if method_segment:
                                    method_path = f"{base_path}/{method_segment}"

                            # Extract path parameters from method signature
                            path_param_names = set()
                            for arg in method.args.args:
                                if (
                                    arg.arg != "self"
                                    and arg.arg not in ["cls"]
                                    and arg.arg in ["id", "key", "name", "slug", "uuid"]
                                ):
                                    # Check if it's a path parameter (common patterns: id, key, name)
                                    path_param_names.add(arg.arg)
                                    method_path = f"{method_path}/{{{arg.arg}}}"

                            # Extract path parameters
                            path, path_params = self._extract_path_parameters(method_path)

                            # Use class name as tag
                            tags = [node.name]

                            # Add operation
                            self._add_operation(
                                openapi_spec,
                                path,
                                http_method,
                                method,
                                path_params=path_params,
                                tags=tags,
                                status_code=None,
                                security=None,
                            )

        except (SyntaxError, UnicodeDecodeError):
            # Skip files with syntax errors
            pass

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

        # Handle basic types
        if isinstance(type_node, ast.Name):
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
            # Check if it's a Pydantic model (BaseModel subclass)
            # We'll detect this by checking if it's imported from pydantic
            return {"$ref": f"#/components/schemas/{type_name}"}

        # Handle Optional/Union types
        if isinstance(type_node, ast.Subscript) and isinstance(type_node.value, ast.Name):
            if type_node.value.id in ("Optional", "Union"):
                # Extract the first type from Optional/Union
                if isinstance(type_node.slice, ast.Tuple) and type_node.slice.elts:
                    return self._extract_type_hint_schema(type_node.slice.elts[0])
                if isinstance(type_node.slice, ast.Name):
                    return self._extract_type_hint_schema(type_node.slice)
            elif type_node.value.id == "list":
                # Handle List[Type]
                if isinstance(type_node.slice, ast.Name):
                    item_schema = self._extract_type_hint_schema(type_node.slice)
                    return {"type": "array", "items": item_schema}
                if isinstance(type_node.slice, ast.Subscript):
                    # Handle List[Optional[Type]] or nested types
                    item_schema = self._extract_type_hint_schema(type_node.slice)
                    return {"type": "array", "items": item_schema}
            elif type_node.value.id == "dict":
                # Handle Dict[K, V] - simplified to object
                return {"type": "object", "additionalProperties": True}

        # Handle generic types
        if isinstance(type_node, ast.Constant):
            # This shouldn't happen for type hints, but handle it
            return {"type": "object"}

        return {"type": "object"}

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
        if path not in openapi_spec["paths"]:
            openapi_spec["paths"][path] = {}

        # Extract path parameter names
        path_param_names = {p["name"] for p in (path_params or [])}

        # Extract request body, query parameters, and response schema
        request_body, query_params, response_schema = self._extract_function_parameters(func_node, path_param_names)

        operation_id = func_node.name
        # Use extracted status code or default to 200
        default_status = status_code or 200
        operation: dict[str, Any] = {
            "operationId": operation_id,
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

        # Add additional common status codes for error cases
        if method in ("POST", "PUT", "PATCH"):
            operation["responses"]["400"] = {"description": "Bad Request"}
            operation["responses"]["422"] = {"description": "Validation Error"}
        if method in ("GET", "PUT", "PATCH", "DELETE"):
            operation["responses"]["404"] = {"description": "Not Found"}
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            operation["responses"]["401"] = {"description": "Unauthorized"}
            operation["responses"]["403"] = {"description": "Forbidden"}
        if method in ("POST", "PUT", "PATCH", "DELETE"):
            operation["responses"]["500"] = {"description": "Internal Server Error"}

        # Add path parameters
        all_params = list(path_params or [])
        # Add query parameters
        all_params.extend(query_params)
        if all_params:
            operation["parameters"] = all_params

        # Add tags
        if tags:
            operation["tags"] = tags

        # Add security requirements
        if security:
            operation["security"] = security
            # Ensure security schemes are defined in components
            if "components" not in openapi_spec:
                openapi_spec["components"] = {}
            if "securitySchemes" not in openapi_spec["components"]:
                openapi_spec["components"]["securitySchemes"] = {}
            # Add bearerAuth scheme if used
            for sec_req in security:
                if "bearerAuth" in sec_req:
                    openapi_spec["components"]["securitySchemes"]["bearerAuth"] = {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }

        # Add request body for POST/PUT/PATCH if found
        if method in ("POST", "PUT", "PATCH") and request_body:
            operation["requestBody"] = request_body
        elif method in ("POST", "PUT", "PATCH") and not request_body:
            # Fallback: create empty request body
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
        for _path, path_item in openapi_spec.get("paths", {}).items():
            for _method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue

                operation_id = operation.get("operationId")
                if not operation_id or operation_id not in test_examples:
                    continue

                example_data = test_examples[operation_id]

                # Add request example
                if "request" in example_data and "requestBody" in operation:
                    request_body = example_data["request"]
                    if "body" in request_body:
                        # Add example to request body
                        content = operation["requestBody"].get("content", {})
                        for _content_type, content_schema in content.items():
                            if "examples" not in content_schema:
                                content_schema["examples"] = {}
                            content_schema["examples"]["test-example"] = {
                                "summary": "Example from test",
                                "value": request_body["body"],
                            }

                # Add response example
                if "response" in example_data:
                    status_code = str(example_data.get("status_code", 200))
                    if status_code in operation.get("responses", {}):
                        response = operation["responses"][status_code]
                        content = response.get("content", {})
                        for _content_type, content_schema in content.items():
                            if "examples" not in content_schema:
                                content_schema["examples"] = {}
                            content_schema["examples"]["test-example"] = {
                                "summary": "Example from test",
                                "value": example_data["response"],
                            }

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
