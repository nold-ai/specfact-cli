#!/usr/bin/env python3
"""
Django form schema extractor for sidecar contract population.

Extracts form field schemas from Django form classes and converts them to OpenAPI format.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast


if TYPE_CHECKING:
    from typing import Any
else:
    # Runtime: Allow Any for dynamic schema structures
    Any = object  # type: ignore[assignment, misc]


def _django_field_to_openapi_type(field_class: str) -> dict[str, str | int | float | bool | list[str]]:
    """
    Convert Django form field class to OpenAPI schema type.

    Args:
        field_class: Django field class name (e.g., 'CharField', 'EmailField')

    Returns:
        OpenAPI schema dictionary
    """
    field_lower = field_class.lower()

    # String types
    if "char" in field_lower or "text" in field_lower or "slug" in field_lower or "url" in field_lower:
        return {"type": "string"}
    if "email" in field_lower:
        return {"type": "string", "format": "email"}
    if "password" in field_lower:
        return {"type": "string", "format": "password"}
    if "uuid" in field_lower:
        return {"type": "string", "format": "uuid"}

    # Numeric types
    if "integer" in field_lower or "int" in field_lower:
        return {"type": "integer"}
    if "float" in field_lower or "decimal" in field_lower:
        return {"type": "number", "format": "float"}

    # Boolean
    if "boolean" in field_lower or "bool" in field_lower:
        return {"type": "boolean"}

    # Date/time types
    if "date" in field_lower:
        return {"type": "string", "format": "date"}
    if "time" in field_lower:
        return {"type": "string", "format": "time"}
    if "datetime" in field_lower:
        return {"type": "string", "format": "date-time"}

    # File types
    if "file" in field_lower or "image" in field_lower:
        return {"type": "string", "format": "binary"}

    # Choice/select fields
    if "choice" in field_lower:
        return {"type": "string"}  # enum will be added separately if available

    # Default to string
    return {"type": "string"}


def _extract_field_validators(
    field_node: ast.Assign | ast.AnnAssign,
) -> dict[str, str | int | float | bool | list[str]]:
    """
    Extract validators and constraints from Django form field.

    Args:
        field_node: AST node for field assignment

    Returns:
        Dictionary with validation constraints
    """
    constraints: dict[str, str | int | float | bool | list[str]] = {}

    # Check for field instantiation (e.g., CharField(max_length=100))
    if isinstance(field_node, ast.Assign):
        # ast.Assign has a single 'value' attribute, not 'values'
        value = field_node.value
        if isinstance(value, ast.Call):
            # Check keyword arguments for validators
            for kw in value.keywords:
                if kw.arg == "max_length" and isinstance(kw.value, ast.Constant):
                    max_len = kw.value.value
                    if isinstance(max_len, (int, float)):
                        constraints["maxLength"] = int(max_len)
                elif kw.arg == "min_length" and isinstance(kw.value, ast.Constant):
                    min_len = kw.value.value
                    if isinstance(min_len, (int, float)):
                        constraints["minLength"] = int(min_len)
                elif kw.arg == "required" and isinstance(kw.value, ast.Constant):
                    required_val = kw.value.value
                    if isinstance(required_val, bool) and required_val is False:
                        constraints["nullable"] = True
                elif kw.arg == "choices" and isinstance(kw.value, (ast.List, ast.Tuple)):
                    # Extract enum values if available
                    enum_values: list[str] = []
                    for elt in kw.value.elts if hasattr(kw.value, "elts") else []:
                        if isinstance(elt, (ast.Tuple, ast.List)) and len(elt.elts) >= 1:
                            first_val = elt.elts[0]
                            if isinstance(first_val, ast.Constant):
                                enum_val = first_val.value
                                if isinstance(enum_val, str):
                                    enum_values.append(enum_val)
                    if enum_values:
                        constraints["enum"] = enum_values

    return constraints


def _extract_form_fields_from_ast(form_file: Path, form_class_name: str) -> dict[str, dict[str, object]]:
    """
    Extract form fields from Django form class using AST.

    Args:
        form_file: Path to Python file containing form class
        form_class_name: Name of form class (e.g., 'UserProfileForm')

    Returns:
        Dictionary mapping field names to OpenAPI schema properties
    """
    if not form_file.exists():
        return {}

    try:
        content = form_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(form_file))
    except Exception as e:
        print(f"Warning: Could not parse {form_file}: {e}", file=sys.stderr)
        return {}

    fields: dict[str, dict[str, Any]] = {}

    for node in ast.walk(tree):
        # Find the target form class
        if isinstance(node, ast.ClassDef) and node.name == form_class_name:
            # Check for Meta class (ModelForm)
            for item in node.body:
                if isinstance(item, ast.ClassDef) and item.name == "Meta":
                    # Extract fields from Meta.fields
                    for meta_item in item.body:
                        if isinstance(meta_item, ast.Assign):
                            for target in meta_item.targets:
                                if (
                                    isinstance(target, ast.Name)
                                    and target.id == "fields"
                                    and isinstance(meta_item.value, (ast.Tuple, ast.List))
                                ):
                                    # Extract fields tuple/list
                                    for field_elt in meta_item.value.elts:
                                        if isinstance(field_elt, ast.Constant):
                                            field_elt_value = field_elt.value
                                            if isinstance(field_elt_value, str):
                                                field_name = field_elt_value
                                                # Default schema for ModelForm fields
                                                fields[field_name] = {"type": "string"}  # type: ignore[assignment]
                                        elif hasattr(ast, "Str") and isinstance(field_elt, ast.Str):  # type: ignore[attr-defined, comparison-overlap]
                                            field_elt_value = field_elt.s  # type: ignore[attr-defined, deprecated]
                                            if isinstance(field_elt_value, str):
                                                field_name = field_elt_value
                                                # Default schema for ModelForm fields
                                                fields[field_name] = {"type": "string"}  # type: ignore[assignment]

                    # Extract explicit field definitions (forms.Form style)
            for item in node.body:
                if isinstance(item, ast.Assign):
                    # Check if it's a field assignment
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            field_name = target.id
                            # Check if value is a Django field
                            if isinstance(item.value, ast.Call):
                                if isinstance(item.value.func, ast.Attribute):
                                    field_class = item.value.func.attr
                                elif isinstance(item.value.func, ast.Name):
                                    field_class = item.value.func.id
                                else:
                                    continue

                                # Convert to OpenAPI type
                                schema = _django_field_to_openapi_type(field_class)
                                # Add validators
                                validators = _extract_field_validators(item)
                                schema.update(validators)
                                fields[field_name] = schema  # type: ignore[assignment]

    return fields


def _extract_model_fields_from_meta(form_file: Path, form_class_name: str) -> dict[str, dict[str, object]]:
    """
    Extract fields from Django ModelForm Meta class.

    Args:
        form_file: Path to Python file containing form class
        form_class_name: Name of form class
        model_name: Optional model name to look up

    Returns:
        Dictionary mapping field names to OpenAPI schema properties
    """
    # For ModelForm, we can infer basic types from field names
    # This is a simplified approach - full implementation would parse the model
    fields: dict[str, dict[str, Any]] = {}

    if not form_file.exists():
        return fields

    try:
        content = form_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(form_file))
    except Exception:
        return fields

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == form_class_name:
            for item in node.body:
                if isinstance(item, ast.ClassDef) and item.name == "Meta":
                    for meta_item in item.body:
                        if isinstance(meta_item, ast.Assign):
                            for target in meta_item.targets:
                                if (
                                    isinstance(target, ast.Name)
                                    and target.id == "fields"
                                    and isinstance(meta_item.value, (ast.Tuple, ast.List))
                                ):
                                    for field_elt in meta_item.value.elts:
                                        if isinstance(field_elt, (ast.Constant, ast.Str)):
                                            if isinstance(field_elt, ast.Constant):
                                                field_elt_value = field_elt.value
                                                if isinstance(field_elt_value, str):
                                                    field_name = field_elt_value
                                                    field_name_lower = field_name.lower()
                                                    # Infer type from field name
                                                    if "avatar" in field_name_lower or "image" in field_name_lower:
                                                        fields[field_name] = {"type": "string", "format": "binary"}  # type: ignore[assignment]
                                                    elif "bio" in field_name_lower or "content" in field_name_lower:
                                                        fields[field_name] = {"type": "string"}  # type: ignore[assignment]
                                                    elif "receiver" in field_name_lower or "user" in field_name_lower:
                                                        fields[field_name] = {"type": "integer"}  # type: ignore[assignment]  # Usually a ForeignKey
                                                    else:
                                                        fields[field_name] = {"type": "string"}  # type: ignore[assignment]
                                            elif hasattr(ast, "Str") and isinstance(field_elt, ast.Str):  # type: ignore[attr-defined, comparison-overlap]
                                                field_elt_value = field_elt.s  # type: ignore[attr-defined, deprecated]
                                                if isinstance(field_elt_value, str):
                                                    field_name = field_elt_value
                                                    field_name_lower = field_name.lower()
                                                    # Infer type from field name
                                                    if "avatar" in field_name_lower or "image" in field_name_lower:
                                                        fields[field_name] = {"type": "string", "format": "binary"}  # type: ignore[assignment]
                                                    elif "bio" in field_name_lower or "content" in field_name_lower:
                                                        fields[field_name] = {"type": "string"}  # type: ignore[assignment]
                                                    elif "receiver" in field_name_lower or "user" in field_name_lower:
                                                        fields[field_name] = {"type": "integer"}  # type: ignore[assignment]  # Usually a ForeignKey
                                                    else:
                                                        fields[field_name] = {"type": "string"}  # type: ignore[assignment]

    return fields


def extract_form_schema(repo_path: Path, form_module: str, form_class_name: str) -> dict[str, object]:
    """
    Extract OpenAPI schema from Django form class.

    Args:
        repo_path: Path to Django repository root
        form_module: Module path (e.g., 'authentication.forms')
        form_class_name: Form class name (e.g., 'UserProfileForm')

    Returns:
        OpenAPI schema dictionary with properties and required fields
    """
    # Convert module path to file path
    module_parts = form_module.split(".")
    form_file = repo_path
    for part in module_parts:
        form_file = form_file / part
    form_file = form_file.with_suffix(".py")

    if not form_file.exists():
        # Try alternative locations
        possible_paths = [
            repo_path / form_module.replace(".", "/") / "__init__.py",
            repo_path / form_module.replace(".", "/") / "forms.py",
        ]
        for path in possible_paths:
            if path.exists():
                form_file = path
                break
        else:
            return {"type": "object", "properties": {}, "required": []}

    # Extract fields
    fields = _extract_form_fields_from_ast(form_file, form_class_name)

    # If no fields found, try ModelForm Meta extraction
    if not fields:
        fields = _extract_model_fields_from_meta(form_file, form_class_name)

    # Build OpenAPI schema
    properties: dict[str, dict[str, object]] = {}
    required: list[str] = []

    for field_name, field_schema in fields.items():
        properties[field_name] = cast(dict[str, object], field_schema)
        # Assume all fields are required unless explicitly nullable
        if not field_schema.get("nullable", False):
            required.append(field_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required if required else [],
    }


def extract_view_form_schema(repo_path: Path, view_module: str, view_function: str) -> dict[str, object] | None:
    """
    Extract form schema from Django view function.

    Args:
        repo_path: Path to Django repository root
        view_module: Module path (e.g., 'authentication.views')
        view_function: View function name (e.g., 'sign_up')

    Returns:
        OpenAPI schema dictionary or None if no form found
    """
    # Convert module path to file path
    module_parts = view_module.split(".")
    view_file = repo_path
    for part in module_parts:
        view_file = view_file / part
    view_file = view_file.with_suffix(".py")

    if not view_file.exists():
        return None

    try:
        content = view_file.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(view_file))
    except Exception:
        return None

    # Find the view function
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == view_function:
            # Look for form instantiation (e.g., UserCreationForm(request.POST))
            for item in ast.walk(node):
                if isinstance(item, ast.Call):
                    # Check if it's a form class instantiation
                    if isinstance(item.func, ast.Name):
                        form_class = item.func.id
                        # Check if it ends with 'Form' (common Django pattern)
                        if form_class.endswith("Form"):
                            # Try to find the form module
                            # Look for imports in the file
                            for import_node in ast.walk(tree):
                                if isinstance(import_node, ast.ImportFrom) and import_node.module:
                                    for alias in import_node.names:
                                        if alias.name == form_class:
                                            form_module = import_node.module or ""
                                            if form_module:
                                                return extract_form_schema(repo_path, form_module, form_class)
                    elif isinstance(item.func, ast.Attribute):
                        # Handle cases like forms.UserCreationForm
                        if isinstance(item.func.value, ast.Name):
                            module_name = item.func.value.id
                            form_class = item.func.attr
                            # Common Django form modules
                            if module_name == "forms" and ("Creation" in form_class or "Sign" in form_class):
                                # This is likely django.contrib.auth.forms.UserCreationForm
                                # Return a basic schema for login/signup
                                return {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string", "minLength": 1},
                                        "password1": {"type": "string", "minLength": 1},
                                        "password2": {"type": "string", "minLength": 1},
                                    },
                                    "required": ["username", "password1", "password2"],
                                }

    return None


def main() -> int:
    """Main entry point for Django form extractor."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Extract Django form schemas for contract population.")
    parser.add_argument("--repo", required=True, help="Path to Django repository")
    parser.add_argument("--form-module", help="Form module path (e.g., authentication.forms)")
    parser.add_argument("--form-class", help="Form class name (e.g., UserProfileForm)")
    parser.add_argument("--view-module", help="View module path (e.g., authentication.views)")
    parser.add_argument("--view-function", help="View function name (e.g., sign_up)")
    parser.add_argument("--output", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    repo_path = Path(str(args.repo)).resolve()  # type: ignore[arg-type]

    schema: dict[str, object] | None = None

    if args.form_module and args.form_class:
        schema = extract_form_schema(repo_path, str(args.form_module), str(args.form_class))  # type: ignore[arg-type]
    elif args.view_module and args.view_function:
        schema = extract_view_form_schema(repo_path, str(args.view_module), str(args.view_function))  # type: ignore[arg-type]
    else:
        print("Error: Must provide either --form-module/--form-class or --view-module/--view-function", file=sys.stderr)
        return 1

    if schema is None:
        schema = {"type": "object", "properties": {}, "required": []}

    output_json = json.dumps(schema, indent=2)

    if args.output:
        Path(str(args.output)).write_text(output_json, encoding="utf-8")  # type: ignore[arg-type]
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
