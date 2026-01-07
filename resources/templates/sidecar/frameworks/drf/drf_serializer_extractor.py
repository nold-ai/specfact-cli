#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportImplicitRelativeImport=false, reportArgumentType=false
"""
Django REST Framework serializer extractor for sidecar contract population.

Extracts serializer field schemas from DRF serializer classes and converts them to OpenAPI format.
Similar to Pydantic model extraction but for DRF serializers.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from typing import Any
else:
    # Runtime: Allow Any for dynamic schema structures
    Any = object  # type: ignore[assignment, misc]


def _drf_field_to_openapi_type(field_class: str) -> dict[str, Any]:
    """
    Convert DRF serializer field class to OpenAPI schema type.

    Args:
        field_class: DRF field class name (e.g., 'CharField', 'EmailField', 'IntegerField')

    Returns:
        OpenAPI schema dictionary
    """
    field_lower = field_class.lower()

    # String types
    if "char" in field_lower or "slug" in field_lower or "url" in field_lower:
        return {"type": "string"}
    if "email" in field_lower:
        return {"type": "string", "format": "email"}
    if "uuid" in field_lower:
        return {"type": "string", "format": "uuid"}
    if "ipaddress" in field_lower:
        return {"type": "string", "format": "ipv4"}
    if "filepath" in field_lower:
        return {"type": "string", "format": "uri"}
    if "file" in field_lower or "image" in field_lower:
        return {"type": "string", "format": "binary"}

    # Numeric types
    if "integer" in field_lower or "int" in field_lower:
        return {"type": "integer"}
    if "biginteger" in field_lower:
        return {"type": "integer", "format": "int64"}
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
    if "duration" in field_lower:
        return {"type": "string", "format": "duration"}

    # Complex types
    if "json" in field_lower:
        return {"type": "object"}  # JSON object
    if "dict" in field_lower:
        return {"type": "object"}
    if "list" in field_lower:
        return {"type": "array", "items": {"type": "string"}}  # Default to string items

    # Choice/select fields
    if "choice" in field_lower:
        return {"type": "string"}  # enum will be added separately if available

    # Default to string
    return {"type": "string"}


def _extract_field_constraints(field_node: ast.Call) -> dict[str, Any]:
    """
    Extract validators and constraints from DRF serializer field.

    Args:
        field_node: AST Call node for field instantiation (e.g., CharField(max_length=100))

    Returns:
        Dictionary with validation constraints
    """
    constraints: dict[str, Any] = {}

    # Check keyword arguments for validators
    for kw in field_node.keywords:
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
        elif kw.arg == "allow_null" and isinstance(kw.value, ast.Constant):
            allow_null_val = kw.value.value
            if isinstance(allow_null_val, bool) and allow_null_val is True:
                constraints["nullable"] = True
        elif kw.arg == "allow_blank" and isinstance(kw.value, ast.Constant):
            allow_blank_val = kw.value.value
            if isinstance(allow_blank_val, bool) and allow_blank_val is True:
                # Blank strings are allowed, but still required if required=True
                pass
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
        elif kw.arg == "min_value" and isinstance(kw.value, ast.Constant):
            min_val = kw.value.value
            if isinstance(min_val, (int, float)):
                constraints["minimum"] = min_val
        elif kw.arg == "max_value" and isinstance(kw.value, ast.Constant):
            max_val = kw.value.value
            if isinstance(max_val, (int, float)):
                constraints["maximum"] = max_val

    return constraints


def _is_drf_serializer(node: ast.ClassDef, tree: ast.AST) -> bool:
    """
    Check if a class is a DRF serializer (BaseSerializer, Serializer, ModelSerializer, etc.).

    Args:
        node: AST ClassDef node
        tree: Full AST tree for checking parent classes

    Returns:
        True if the class is a DRF serializer
    """
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

        # Check if it's a DRF serializer base class
        if isinstance(base, ast.Name):
            if base.id in ("BaseSerializer", "Serializer", "ModelSerializer"):
                return True
            # Check if parent class exists in the same file
            for parent_node in ast.walk(tree):
                if isinstance(parent_node, ast.ClassDef) and parent_node.name == base.id:
                    # Recursively check parent's bases
                    bases_to_check.extend(parent_node.bases)
                    break
        elif isinstance(base, ast.Attribute):
            if base.attr in ("BaseSerializer", "Serializer", "ModelSerializer"):
                return True

    return False


def _extract_serializer_fields_from_ast(serializer_file: Path, serializer_class_name: str) -> dict[str, dict[str, Any]]:
    """
    Extract serializer fields from AST.

    Args:
        serializer_file: Path to serializer file
        serializer_class_name: Name of serializer class

    Returns:
        Dictionary mapping field names to OpenAPI schemas
    """
    fields: dict[str, dict[str, Any]] = {}

    try:
        with serializer_file.open("r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=str(serializer_file))
    except (SyntaxError, UnicodeDecodeError):
        return fields

    # Find the serializer class
    serializer_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == serializer_class_name and _is_drf_serializer(node, tree):
            serializer_node = node
            break

    if not serializer_node:
        return fields

    # Extract fields from parent classes first (inheritance)
    parent_classes = []
    for base in serializer_node.bases:
        if isinstance(base, ast.Name):
            parent_classes.append(base.id)

    # Extract parent class fields
    for parent_name in parent_classes:
        for parent_node in ast.walk(tree):
            if isinstance(parent_node, ast.ClassDef) and parent_node.name == parent_name:
                # Recursively extract from parent
                for item in parent_node.body:
                    if isinstance(item, ast.Assign):
                        # Field assignment: field_name = CharField(...) or serializers.CharField(...)
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                field_name = target.id
                                # Only add if not already present (child overrides parent)
                                if field_name not in fields and isinstance(item.value, ast.Call):
                                    # Extract field type from call
                                    field_class = None
                                    if isinstance(item.value.func, ast.Name):
                                        # Direct: CharField(...)
                                        field_class = item.value.func.id
                                    elif isinstance(item.value.func, ast.Attribute):
                                        # Attribute: serializers.CharField(...)
                                        field_class = item.value.func.attr

                                    if field_class:
                                        field_schema = _drf_field_to_openapi_type(field_class)
                                        constraints = _extract_field_constraints(item.value)
                                        field_schema.update(constraints)
                                        fields[field_name] = field_schema
                break

    # Extract fields from this class (overrides parent)
    for item in serializer_node.body:
        if isinstance(item, ast.Assign):
            # Field assignment: field_name = CharField(...) or serializers.CharField(...)
            for target in item.targets:
                if isinstance(target, ast.Name):
                    field_name = target.id
                    if isinstance(item.value, ast.Call):
                        # Extract field type from call
                        field_class = None
                        if isinstance(item.value.func, ast.Name):
                            # Direct: CharField(...)
                            field_class = item.value.func.id
                        elif isinstance(item.value.func, ast.Attribute):
                            # Attribute: serializers.CharField(...)
                            field_class = item.value.func.attr

                        if field_class:
                            field_schema = _drf_field_to_openapi_type(field_class)
                            constraints = _extract_field_constraints(item.value)
                            field_schema.update(constraints)
                            fields[field_name] = field_schema
                    elif isinstance(item.value, ast.Attribute):
                        # Nested serializer: field_name = AnotherSerializer()
                        # For now, treat as object
                        fields[field_name] = {"type": "object"}

    return fields


def extract_serializer_schema(repo_path: Path, serializer_module: str, serializer_class_name: str) -> dict[str, Any]:
    """
    Extract OpenAPI schema from DRF serializer class.

    Args:
        repo_path: Path to Django repository root
        serializer_module: Module path (e.g., 'api.serializers')
        serializer_class_name: Serializer class name (e.g., 'UserSerializer')

    Returns:
        OpenAPI schema dictionary with properties and required fields
    """
    # Convert module path to file path
    module_parts = serializer_module.split(".")
    serializer_file = repo_path
    for part in module_parts:
        serializer_file = serializer_file / part
    serializer_file = serializer_file.with_suffix(".py")

    if not serializer_file.exists():
        # Try alternative locations
        possible_paths = [
            repo_path / serializer_module.replace(".", "/") / "__init__.py",
            repo_path / serializer_module.replace(".", "/") / "serializers.py",
        ]
        for path in possible_paths:
            if path.exists():
                serializer_file = path
                break
        else:
            return {"type": "object", "properties": {}, "required": []}

    # Extract fields
    fields = _extract_serializer_fields_from_ast(serializer_file, serializer_class_name)

    # Build OpenAPI schema
    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []

    for field_name, field_schema in fields.items():
        properties[field_name] = field_schema
        # Assume all fields are required unless explicitly nullable or has default
        if not field_schema.get("nullable", False) and "default" not in field_schema:
            required.append(field_name)

    return {
        "type": "object",
        "properties": properties,
        "required": required if required else [],
    }


def main() -> int:
    """Main entry point for DRF serializer extractor."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Extract DRF serializer schemas for contract population.")
    _ = parser.add_argument("--repo", required=True, help="Path to Django repository")
    _ = parser.add_argument("--serializer-module", required=True, help="Serializer module path (e.g., api.serializers)")
    _ = parser.add_argument("--serializer-class", required=True, help="Serializer class name (e.g., UserSerializer)")
    _ = parser.add_argument("--output", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    # Use vars() to get dictionary for type checker
    args_dict = vars(args)
    repo_path = Path(str(args_dict["repo"])).resolve()

    schema = extract_serializer_schema(
        repo_path, str(args_dict["serializer_module"]), str(args_dict["serializer_class"])
    )

    output_json = json.dumps(schema, indent=2)

    output_path = args_dict.get("output")
    if output_path:
        _ = Path(str(output_path)).write_text(output_json, encoding="utf-8")
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
