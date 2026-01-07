#!/usr/bin/env python3
"""
FastAPI route extractor for sidecar contract population.

Extracts route patterns from FastAPI route files and converts them to OpenAPI paths.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any


def _extract_path_parameters(path: str) -> tuple[str, list[dict[str, object]]]:
    """
    Extract path parameters from FastAPI route path.

    Converts FastAPI format ({id}, {user_id}) to OpenAPI format and extracts parameters.

    Args:
        path: FastAPI route path (e.g., '/items/{id}')

    Returns:
        Tuple of (normalized_path, path_params)
    """
    path_params: list[dict[str, Any]] = []
    normalized_path = path

    # FastAPI path parameter pattern: {param_name} or {param_name:type}
    pattern = r"\{([^}:]+)(?::([^}]+))?\}"
    matches = list(re.finditer(pattern, path))

    for match in matches:
        param_name = match.group(1)
        param_type_hint = match.group(2) if match.group(2) else None

        # Convert type hint to OpenAPI type
        type_map = {
            "int": "integer",
            "float": "number",
            "str": "string",
            "uuid": "string",
            "path": "string",
        }
        openapi_type = type_map.get(param_type_hint.lower() if param_type_hint else "str", "string")

        path_params.append(
            {
                "name": param_name,
                "in": "path",
                "required": True,
                "schema": {"type": openapi_type},
            }
        )

        # Path is already in OpenAPI format, no replacement needed
        # But we track it for completeness

    return normalized_path, path_params


def _resolve_function_reference(func_node: ast.AST, imports: dict[str, str]) -> str | None:
    """
    Resolve FastAPI function reference to a module path.

    Args:
        func_node: AST node representing the function
        imports: Dictionary of import aliases to module paths

    Returns:
        Module path string (e.g., 'app.api.routes.items.read_item') or None
    """
    if isinstance(func_node, ast.Name):
        return func_node.id
    return None


def _infer_http_method(func_name: str, decorator_attr: str | None = None) -> str:
    """
    Infer HTTP method from function name or decorator.

    Args:
        func_name: Name of the function
        decorator_attr: Attribute name from decorator (e.g., 'get', 'post')

    Returns:
        HTTP method (default: 'GET')
    """
    if decorator_attr:
        return decorator_attr.upper()

    func_lower = func_name.lower()

    # Common patterns
    if any(keyword in func_lower for keyword in ["create", "add", "new", "register", "login"]):
        return "POST"
    if any(keyword in func_lower for keyword in ["update", "edit", "change", "patch"]):
        return "PATCH"
    if any(keyword in func_lower for keyword in ["put", "replace"]):
        return "PUT"
    if any(keyword in func_lower for keyword in ["delete", "remove"]):
        return "DELETE"
    if any(keyword in func_lower for keyword in ["list", "read", "get", "fetch"]):
        return "GET"

    return "GET"


def _extract_field_constraints(field_value: ast.expr) -> dict[str, Any]:
    """
    Extract Field constraints from Pydantic Field() call.

    Args:
        field_value: AST node representing Field() call

    Returns:
        Dictionary with constraints (minLength, maxLength, format, etc.)
    """
    constraints: dict[str, Any] = {}

    if isinstance(field_value, ast.Call) and isinstance(field_value.func, ast.Name) and field_value.func.id == "Field":
        # Check if it's a Field() call
        for kw in field_value.keywords:
            if kw.arg == "min_length" and isinstance(kw.value, ast.Constant):
                constraints["minLength"] = kw.value.value
            elif kw.arg == "max_length" and isinstance(kw.value, ast.Constant):
                constraints["maxLength"] = kw.value.value
            elif kw.arg == "format" and isinstance(kw.value, ast.Constant):
                constraints["format"] = kw.value.value
            elif (kw.arg == "default" and isinstance(kw.value, ast.Constant)) or (
                kw.arg == "default" and isinstance(kw.value, ast.NameConstant)
            ):
                constraints["default"] = kw.value.value
            elif kw.arg == "default" and isinstance(kw.value, ast.Name) and kw.value.id == "None":
                constraints["nullable"] = True

    return constraints


def _extract_type_hint_schema(type_node: ast.expr | None) -> dict[str, Any]:
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
        # Check for Pydantic special types first
        if type_name == "EmailStr":
            return {"type": "string", "format": "email"}
        if type_name == "UUID" or type_name == "uuid":
            return {"type": "string", "format": "uuid"}
        # Then check basic types
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
        # Pydantic model reference - will be resolved later
        return {"type": "object", "x-model-name": type_name}

    # Handle Python 3.10+ union syntax: str | None (ast.BinOp with BitOr)
    if isinstance(type_node, ast.BinOp) and isinstance(type_node.op, ast.BitOr):
        # Handle union types like str | None, EmailStr | None
        # Extract the first type (left side) and mark as nullable
        schema = _extract_type_hint_schema(type_node.left)
        schema["nullable"] = True
        return schema

    # Handle Optional/Union types (old syntax)
    if isinstance(type_node, ast.Subscript) and isinstance(type_node.value, ast.Name):
        if type_node.value.id in ("Optional", "Union"):
            # Extract the first type from Optional/Union
            if isinstance(type_node.slice, ast.Tuple) and type_node.slice.elts:
                schema = _extract_type_hint_schema(type_node.slice.elts[0])
                schema["nullable"] = True
                return schema
            if isinstance(type_node.slice, ast.Name):
                schema = _extract_type_hint_schema(type_node.slice)
                schema["nullable"] = True
                return schema
        elif type_node.value.id == "list":
            # Handle List[Type]
            if isinstance(type_node.slice, ast.Name):
                item_schema = _extract_type_hint_schema(type_node.slice)
                return {"type": "array", "items": item_schema}

    # Handle EmailStr, UUID, etc. (from pydantic)
    if isinstance(type_node, ast.Name):
        if type_node.id == "EmailStr":
            return {"type": "string", "format": "email"}
        if type_node.id == "UUID" or type_node.id == "uuid":
            return {"type": "string", "format": "uuid"}

    # Handle Optional[EmailStr] etc.
    if (
        isinstance(type_node, ast.Subscript)
        and isinstance(type_node.value, ast.Name)
        and type_node.value.id in ("Optional", "Union")
    ):
        inner_type = None
        if isinstance(type_node.slice, ast.Tuple) and type_node.slice.elts:
            inner_type = type_node.slice.elts[0]
        elif isinstance(type_node.slice, ast.Name):
            inner_type = type_node.slice
        if inner_type and isinstance(inner_type, ast.Name):
            if inner_type.id == "EmailStr":
                return {"type": "string", "format": "email", "nullable": True}
            if inner_type.id == "UUID" or inner_type.id == "uuid":
                return {"type": "string", "format": "uuid", "nullable": True}

    return {"type": "object"}


def _extract_pydantic_model_schema(repo_path: Path, model_name: str, imports: dict[str, str]) -> dict[str, Any] | None:
    """
    Extract OpenAPI schema from a Pydantic model class definition.

    Args:
        repo_path: Path to repository root
        model_name: Name of the Pydantic model class
        imports: Dictionary of import aliases to module paths

    Returns:
        OpenAPI schema dictionary or None if model not found
    """
    # Try to find the model in common locations
    model_file_candidates = [
        repo_path / "backend" / "app" / "models.py",
        repo_path / "app" / "models.py",
        repo_path / "models.py",
    ]

    # Also check if model is imported from a specific module
    if model_name in imports:
        import_path = imports[model_name]
        module_parts = import_path.split(".")
        model_file = repo_path
        for part in module_parts[:-1]:  # Exclude the class name
            model_file = model_file / part
        model_file = model_file.with_suffix(".py")
        if model_file.exists():
            model_file_candidates.insert(0, model_file)

    for model_file in model_file_candidates:
        if not model_file.exists():
            continue

        try:
            with model_file.open("r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(model_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        # Find the model class
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == model_name:
                # Check if it's a Pydantic model (BaseModel, SQLModel, etc.)
                # Check direct inheritance and also check parent classes recursively
                is_pydantic = False
                bases_to_check = list(node.bases)
                checked_bases = set()

                while bases_to_check:
                    base = bases_to_check.pop(0)

                    # Skip if already checked
                    base_name = None
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        base_name = base.attr

                    if base_name and base_name in checked_bases:
                        continue
                    if base_name:
                        checked_bases.add(base_name)

                    # Check if it's a Pydantic base class
                    if isinstance(base, ast.Name):
                        if base.id in ("BaseModel", "SQLModel"):
                            is_pydantic = True
                            break
                        # Check if parent class exists in the same file
                        for parent_node in ast.walk(tree):
                            if isinstance(parent_node, ast.ClassDef) and parent_node.name == base.id:
                                # Recursively check parent's bases
                                bases_to_check.extend(parent_node.bases)
                                break
                    elif isinstance(base, ast.Attribute):
                        if base.attr in ("BaseModel", "SQLModel"):
                            is_pydantic = True
                            break

                if not is_pydantic:
                    continue

                # Extract schema
                schema: dict[str, Any] = {
                    "type": "object",
                    "properties": {},
                    "required": [],
                }

                # Extract docstring
                docstring = ast.get_docstring(node)
                if docstring:
                    schema["description"] = docstring

                # Extract fields from parent classes first (inheritance)
                parent_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        parent_classes.append(base.id)

                # Extract parent class fields
                for parent_name in parent_classes:
                    for parent_node in ast.walk(tree):
                        if isinstance(parent_node, ast.ClassDef) and parent_node.name == parent_name:
                            # Recursively extract from parent
                            for item in parent_node.body:
                                if (
                                    isinstance(item, ast.AnnAssign)
                                    and item.target
                                    and isinstance(item.target, ast.Name)
                                ):
                                    field_name = item.target.id
                                    # Only add if not already present (child overrides parent)
                                    if field_name not in schema["properties"]:
                                        field_schema = _extract_type_hint_schema(item.annotation)
                                        if item.value:
                                            constraints = _extract_field_constraints(item.value)
                                            field_schema.update(constraints)
                                        schema["properties"][field_name] = field_schema
                                        # Check if required
                                        if item.value is None:
                                            if field_name not in schema["required"]:
                                                schema["required"].append(field_name)
                                        elif (
                                            isinstance(item.value, ast.Name)
                                            and item.value.id == "None"
                                            and "nullable" not in field_schema
                                        ):
                                            field_schema["nullable"] = True
                            break

                # Extract fields from this class (overrides parent)
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and item.target and isinstance(item.target, ast.Name):
                        field_name = item.target.id
                        field_schema = _extract_type_hint_schema(item.annotation)

                        # Extract Field constraints
                        if item.value:
                            constraints = _extract_field_constraints(item.value)
                            field_schema.update(constraints)

                        schema["properties"][field_name] = field_schema

                        # Check if required (no default value)
                        if item.value is None:
                            schema["required"].append(field_name)
                        elif isinstance(item.value, ast.Name) and item.value.id == "None":
                            # Optional field
                            if "nullable" not in field_schema:
                                field_schema["nullable"] = True
                        elif (
                            isinstance(item.value, ast.Call)
                            and "default" not in field_schema
                            and "nullable" not in field_schema
                        ):
                            # Field() call - check for default
                            # No default means required
                            schema["required"].append(field_name)

                return schema

    return None


def _extract_request_body_model(func_node: ast.FunctionDef, imports: dict[str, str]) -> str | None:
    """
    Extract request body model name from FastAPI route function parameters.

    Args:
        func_node: AST FunctionDef node
        imports: Dictionary of import aliases to module paths

    Returns:
        Model name (e.g., 'UserCreate') or None
    """
    # FastAPI convention: first parameter without default is request body for POST/PUT/PATCH
    # Skip special parameters: session, current_user, etc.
    skip_params = {"session", "current_user", "db", "request", "response", "skip", "limit"}

    # Check regular args
    for arg in func_node.args.args:
        if arg.arg in skip_params:
            continue

        # Check if it has a type annotation (Pydantic model)
        if arg.annotation:
            # Extract model name from type annotation
            if isinstance(arg.annotation, ast.Name):
                return arg.annotation.id
            if (
                isinstance(arg.annotation, ast.Subscript)
                and isinstance(arg.annotation.value, ast.Name)
                and arg.annotation.value.id in ("Optional", "Union")
            ):
                # Handle Optional[Model] or Union[Model, None]
                if isinstance(arg.annotation.slice, ast.Tuple) and arg.annotation.slice.elts:
                    first_type = arg.annotation.slice.elts[0]
                    if isinstance(first_type, ast.Name):
                        return first_type.id
                elif isinstance(arg.annotation.slice, ast.Name):
                    return arg.annotation.slice.id

    # Check keyword-only args (FastAPI often uses * to separate path/query params from body)
    for arg in func_node.args.kwonlyargs:
        if arg.arg in skip_params:
            continue

        # Check if it has a type annotation (Pydantic model)
        if arg.annotation:
            # Extract model name from type annotation
            if isinstance(arg.annotation, ast.Name):
                return arg.annotation.id
            if (
                isinstance(arg.annotation, ast.Subscript)
                and isinstance(arg.annotation.value, ast.Name)
                and arg.annotation.value.id in ("Optional", "Union")
            ):
                # Handle Optional[Model] or Union[Model, None]
                if isinstance(arg.annotation.slice, ast.Tuple) and arg.annotation.slice.elts:
                    first_type = arg.annotation.slice.elts[0]
                    if isinstance(first_type, ast.Name):
                        return first_type.id
                elif isinstance(arg.annotation.slice, ast.Name):
                    return arg.annotation.slice.id

    return None


def extract_fastapi_routes(repo_path: Path, routes_dir: Path | None = None) -> list[dict[str, object]]:
    """
    Extract route patterns from FastAPI route files.

    Args:
        repo_path: Path to FastAPI repository root
        routes_dir: Path to routes directory (default: find automatically)

    Returns:
        List of route pattern dictionaries with path, method, function, etc.
    """
    if routes_dir is None:
        # Try to find routes directory
        candidates = [
            repo_path / "backend" / "app" / "api" / "routes",
            repo_path / "app" / "api" / "routes",
            repo_path / "api" / "routes",
            repo_path / "routes",
        ]
        for candidate in candidates:
            if candidate.exists():
                routes_dir = candidate
                break

        if routes_dir is None:
            # Search for route files
            route_files = list(repo_path.rglob("**/routes/*.py"))
            if route_files:
                routes_dir = route_files[0].parent

    if routes_dir is None or not routes_dir.exists():
        return []

    results: list[dict[str, object]] = []

    # Process each route file
    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__init__.py":
            continue

        with route_file.open("r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filename=str(route_file))
        except SyntaxError:
            continue

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

        # Find router variable (usually 'router = APIRouter(...)')
        router_prefix = ""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "router" and isinstance(node.value, ast.Call):
                        # Extract prefix from APIRouter(prefix="...")
                        for kw in node.value.keywords:
                            if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                prefix_value = kw.value.value
                                if isinstance(prefix_value, str):
                                    router_prefix = prefix_value
                                break
                            if kw.arg == "prefix" and hasattr(ast, "Str") and isinstance(kw.value, ast.Str):
                                str_value = kw.value.s  # type: ignore[attr-defined, deprecated]
                                if isinstance(str_value, str):
                                    router_prefix = str_value
                                break

        # Find route decorators (@router.get, @router.post, etc.)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    # Check for @router.METHOD patterns
                    if (
                        isinstance(decorator, ast.Call)
                        and isinstance(decorator.func, ast.Attribute)
                        and isinstance(decorator.func.value, ast.Name)
                        and decorator.func.value.id == "router"
                    ):
                        method = decorator.func.attr.upper()  # get -> GET

                        # Extract path from decorator arguments
                        path = "/"
                        if decorator.args:
                            path_arg = decorator.args[0]
                            if isinstance(path_arg, ast.Constant):
                                path = path_arg.value
                            elif hasattr(ast, "Str") and isinstance(path_arg, ast.Str):
                                path = path_arg.s  # type: ignore[attr-defined, deprecated]

                        if not isinstance(path, str):
                            continue

                        # Combine router prefix with path
                        full_path = (router_prefix + path) if router_prefix and isinstance(router_prefix, str) else path
                        if not full_path.startswith("/"):
                            full_path = "/" + full_path

                        # Normalize path and extract parameters
                        normalized_path, path_params = _extract_path_parameters(full_path)

                        # Extract operation_id from function name
                        operation_id = node.name

                        # Extract response_model if present
                        response_model: str | None = None
                        for kw in decorator.keywords:
                            if kw.arg == "response_model":
                                if isinstance(kw.value, ast.Name):
                                    response_model = kw.value.id
                                elif isinstance(kw.value, ast.Attribute):
                                    response_model = kw.value.attr

                        # Extract request body model from function parameters
                        request_body_model = _extract_request_body_model(node, imports)
                        request_body_schema: dict[str, Any] | None = None
                        if request_body_model:
                            request_body_schema = _extract_pydantic_model_schema(repo_path, request_body_model, imports)

                        # Build function reference
                        module_path = str(route_file.relative_to(repo_path)).replace("/", ".").replace(".py", "")
                        func_ref = f"{module_path}.{node.name}"

                        route_data: dict[str, Any] = {
                            "path": normalized_path,
                            "method": method,
                            "function": func_ref,
                            "operation_id": operation_id,
                            "path_params": path_params,
                            "original_path": full_path,
                            "response_model": response_model,
                        }

                        # Add request body schema if extracted
                        if request_body_schema:
                            route_data["request_body_schema"] = request_body_schema
                            route_data["request_body_model"] = request_body_model

                        results.append(route_data)

    return results


def main() -> int:
    """Main entry point for FastAPI route extractor."""
    parser = argparse.ArgumentParser(description="Extract FastAPI routes for contract population.")
    parser.add_argument("--repo", required=True, help="Path to FastAPI repository")
    parser.add_argument("--routes", help="Path to routes directory (auto-detected if not provided)")
    parser.add_argument("--output", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    repo_path = Path(str(args.repo)).resolve()  # type: ignore[arg-type]
    routes_dir = Path(str(args.routes)).resolve() if args.routes else None  # type: ignore[arg-type]

    results = extract_fastapi_routes(repo_path, routes_dir)

    output_json = json.dumps(results, indent=2, sort_keys=True)

    if args.output:
        Path(str(args.output)).write_text(output_json, encoding="utf-8")  # type: ignore[arg-type]
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
