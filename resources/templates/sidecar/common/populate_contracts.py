#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportImplicitRelativeImport=false
"""
Populate OpenAPI contract stubs with Django URL patterns.

Reads Django URL patterns and populates existing OpenAPI contract files.

Note: This is a template file that gets copied to the sidecar workspace.
The imports work at runtime when the file is in the sidecar directory.
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

import yaml


# Type stubs for template file imports
# These are template files that get copied to sidecar workspace where imports work at runtime
if TYPE_CHECKING:

    def extract_django_urls(repo_path: Path, urls_file: Path | None = None) -> list[dict[str, object]]: ...
    def extract_view_form_schema(repo_path: Path, view_module: str, view_function: str) -> dict[str, object] | None: ...
    def extract_fastapi_routes(repo_path: Path, routes_dir: Path | None = None) -> list[dict[str, object]]: ...
    def extract_serializer_schema(
        repo_path: Path, serializer_module: str, serializer_class: str
    ) -> dict[str, object]: ...


# Import from framework-specific modules
# These scripts are run directly, so we need to handle imports differently
# Add parent directory to path for framework imports when run as script
_script_dir = Path(__file__).parent
_parent_dir = _script_dir.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

# These imports work at runtime when scripts are run directly from sidecar directory
# Type checker uses TYPE_CHECKING stubs above; runtime uses actual imports below
# The sidecar directory has __init__.py, making it a package, so relative imports work at runtime
try:
    # Try explicit relative imports first (preferred for type checking)
    # These work when the sidecar directory is a proper package (has __init__.py)
    from frameworks.django.django_form_extractor import (  # type: ignore[reportMissingImports]
        extract_view_form_schema,
    )
    from frameworks.django.django_url_extractor import extract_django_urls  # type: ignore[reportMissingImports]
    from frameworks.drf.drf_serializer_extractor import extract_serializer_schema  # type: ignore[reportMissingImports]
    from frameworks.fastapi.fastapi_route_extractor import extract_fastapi_routes  # type: ignore[reportMissingImports]
except ImportError:
    # Fallback for when run as script (runtime path manipulation case)
    # This happens when the script is executed directly from the sidecar workspace
    # and sys.path manipulation makes absolute imports work
    from frameworks.django.django_form_extractor import (  # type: ignore[reportMissingImports]
        extract_view_form_schema,
    )
    from frameworks.django.django_url_extractor import (
        extract_django_urls,  # type: ignore[reportImplicitRelativeImport, reportMissingImports]
    )

    try:
        from frameworks.fastapi.fastapi_route_extractor import (
            extract_fastapi_routes,  # type: ignore[reportMissingImports]
        )
    except ImportError:
        # FastAPI extractor not available
        def extract_fastapi_routes(repo_path: Path, routes_dir: Path | None = None) -> list[dict[str, object]]:  # type: ignore[misc]
            return []

    try:
        from frameworks.drf.drf_serializer_extractor import (
            extract_serializer_schema,  # type: ignore[reportMissingImports]
        )
    except ImportError:
        # DRF serializer extractor not available
        def extract_serializer_schema(
            repo_path: Path, serializer_module: str, serializer_class: str
        ) -> dict[str, object]:  # type: ignore[misc]
            return {"type": "object", "properties": {}, "required": []}


def _match_url_to_feature(url_pattern: dict[str, object], feature_key: str) -> bool:
    """
    Match URL pattern to feature by operation_id or view name.

    Args:
        url_pattern: URL pattern dictionary from extractor
        feature_key: Feature key (e.g., 'FEATURE-USER-AUTHENTICATION')

    Returns:
        True if pattern matches feature
    """
    operation_id = str(url_pattern.get("operation_id", "")).lower()
    view = str(url_pattern.get("view", "")).lower()
    feature_lower = feature_key.lower().replace("feature-", "").replace("-", "_")

    # Check if operation_id or view contains feature keywords
    keywords = feature_lower.split("_")
    return any(keyword and (keyword in operation_id or keyword in view) for keyword in keywords)


def _create_openapi_operation(
    url_pattern: dict[str, object],
    repo_path: Path,
    form_schema: dict[str, object] | None = None,
    framework: str = "django",
) -> dict[str, object]:
    """
    Create OpenAPI operation from framework URL pattern (Django or FastAPI).

    Args:
        url_pattern: URL pattern dictionary from extractor
        repo_path: Path to repository (for form extraction, Django only)
        form_schema: Optional pre-extracted form schema (Django only)
        framework: Framework type ("django" or "fastapi")

    Returns:
        OpenAPI operation dictionary
    """
    method = str(url_pattern["method"]).lower()
    path = str(url_pattern["path"])
    operation_id = str(url_pattern.get("operation_id", ""))
    path_params = url_pattern.get("path_params", [])
    if not isinstance(path_params, list):
        path_params = []
    view_ref = url_pattern.get("view") or url_pattern.get("function")

    operation: dict[str, object] = {
        "operationId": operation_id,
        "summary": f"{method.upper()} {path}",
        "responses": {
            "200": {"description": "Success"},
            "400": {"description": "Bad request"},
            "500": {"description": "Internal server error"},
        },
    }

    # Add path parameters
    if path_params:
        operation["parameters"] = path_params

    # Add request body for POST/PUT/PATCH
    if method in ("post", "put", "patch"):
        # For FastAPI: try to use extracted Pydantic model schema
        schema: dict[str, object] | None = None
        if framework == "fastapi":
            request_body_schema = url_pattern.get("request_body_schema")
            if request_body_schema and isinstance(request_body_schema, dict):
                schema = request_body_schema

        # For Django: try to extract form schema from view
        if schema is None and framework == "django":
            schema = form_schema
            if schema is None and view_ref:
                # Try to extract from view function
                view_str = str(view_ref)
                if "." in view_str:
                    parts = view_str.split(".")
                    if len(parts) >= 2:
                        view_module = ".".join(parts[:-1])
                        view_function = parts[-1]
                        schema = extract_view_form_schema(repo_path, view_module, view_function)

        # Special case: login view doesn't use a form
        if schema is None and "login" in operation_id.lower():
            schema = {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "minLength": 1},
                    "password": {"type": "string", "minLength": 1},
                },
                "required": ["username", "password"],
            }

        # Use extracted schema or default empty schema
        if schema is None:
            schema = {"type": "object", "properties": {}, "required": []}

        # FastAPI uses application/json, Django uses application/x-www-form-urlencoded
        content_type = "application/json" if framework == "fastapi" else "application/x-www-form-urlencoded"

        operation["requestBody"] = {
            "required": True,
            "content": {
                content_type: {
                    "schema": schema,
                }
            },
        }

    return operation  # type: ignore[return-value]


def _get_common_schemas() -> dict[str, dict[str, object]]:
    """
    Get common schema definitions for OpenAPI contracts.

    Returns:
        Dictionary of schema name to schema definition
    """
    return {
        "Path": {
            "type": "string",
            "description": "File system path",
            "example": "/path/to/file.py",
        },
        "PlanBundle": {
            "type": "object",
            "description": "Plan bundle containing features, stories, and product definition",
            "properties": {
                "version": {"type": "string", "example": "1.0"},
                "idea": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "narrative": {"type": "string"},
                    },
                },
                "product": {
                    "type": "object",
                    "properties": {
                        "themes": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "features": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "title": {"type": "string"},
                            "stories": {"type": "array", "items": {"type": "object"}},
                        },
                    },
                },
            },
        },
        "FileSystemEvent": {
            "type": "object",
            "description": "File system event (created, modified, deleted)",
            "properties": {
                "path": {"type": "string"},
                "event_type": {"type": "string", "enum": ["created", "modified", "deleted"]},
                "timestamp": {"type": "string", "format": "date-time"},
            },
        },
        "SyncResult": {
            "type": "object",
            "description": "Synchronization result",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "changes": {"type": "array", "items": {"type": "object"}},
            },
        },
        "RepositorySyncResult": {
            "type": "object",
            "description": "Repository synchronization result",
            "properties": {
                "success": {"type": "boolean"},
                "synced_files": {"type": "array", "items": {"type": "string"}},
                "conflicts": {"type": "array", "items": {"type": "object"}},
            },
        },
    }


def _resolve_schema_refs(contract: dict[str, object]) -> dict[str, object]:
    """
    Resolve schema references and add missing schema definitions.

    Args:
        contract: OpenAPI contract dictionary

    Returns:
        Updated contract with resolved schemas
    """
    # Get common schemas
    common_schemas = _get_common_schemas()

    # Ensure components.schemas exists
    components = contract.get("components", {})
    if not isinstance(components, dict):
        components = {}
        contract["components"] = components

    schemas = components.get("schemas", {})
    if not isinstance(schemas, dict):
        schemas = {}
        components["schemas"] = schemas

    # Find all $ref references in the contract
    def find_refs(obj: object, refs: set[str]) -> None:
        """Recursively find all $ref references."""
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = str(obj["$ref"])
                if ref.startswith("#/components/schemas/"):
                    schema_name = ref.split("/")[-1]
                    refs.add(schema_name)
            for value in obj.values():
                find_refs(value, refs)
        elif isinstance(obj, list):
            for item in obj:
                find_refs(item, refs)

    refs: set[str] = set()
    find_refs(contract, refs)

    # Add missing schema definitions
    for ref in refs:
        if ref not in schemas and ref in common_schemas:
            schemas[ref] = common_schemas[ref]
        elif ref in schemas and ref in common_schemas:
            # Fix incorrect schema definitions (hotpatch for PlanBundle schema bug)
            # If schema exists but has incorrect structure, replace with correct one
            existing_schema = schemas[ref]
            correct_schema = common_schemas[ref]

            # Special case: Fix PlanBundle.themes schema bug (array of objects -> array of strings)
            if ref == "PlanBundle" and isinstance(existing_schema, dict) and isinstance(correct_schema, dict):
                existing_props = existing_schema.get("properties", {})
                if not isinstance(existing_props, dict):
                    existing_props = {}
                correct_props = correct_schema.get("properties", {})
                if not isinstance(correct_props, dict):
                    correct_props = {}

                # Check if themes schema is incorrect
                existing_product = existing_props.get("product", {})
                if not isinstance(existing_product, dict):
                    existing_product = {}
                existing_product_props = existing_product.get("properties", {})
                if not isinstance(existing_product_props, dict):
                    existing_product_props = {}
                existing_themes = existing_product_props.get("themes", {})

                correct_product = correct_props.get("product", {})
                if not isinstance(correct_product, dict):
                    correct_product = {}
                correct_product_props = correct_product.get("properties", {})
                if not isinstance(correct_product_props, dict):
                    correct_product_props = {}
                correct_themes = correct_product_props.get("themes", {})

                if (
                    isinstance(existing_themes, dict)
                    and isinstance(correct_themes, dict)
                    and existing_themes.get("items", {}).get("type") == "object"
                    and correct_themes.get("items", {}).get("type") == "string"
                ):
                    # Fix the themes schema
                    if "product" not in existing_props:
                        existing_props["product"] = {}
                    if "properties" not in existing_props["product"]:
                        existing_props["product"]["properties"] = {}
                    existing_props["product"]["properties"]["themes"] = correct_themes

    return contract


def populate_contracts(
    contracts_dir: Path,
    repo_path: Path,
    urls_file: Path | None = None,
    extract_forms: bool = True,
    url_patterns: list[dict[str, object]] | None = None,
    framework: str = "django",
) -> tuple[dict[str, int], list[dict[str, object]]]:
    """
    Populate OpenAPI contract stubs with framework URL patterns (Django or FastAPI).

    Args:
        contracts_dir: Directory containing *.openapi.yaml files
        repo_path: Path to repository
        urls_file: Path to urls.py file (Django only, auto-detected if not provided)
        extract_forms: Whether to extract form schemas from views (Django only)
        url_patterns: Pre-extracted URL patterns (if None, will extract)
        framework: Framework type ("django" or "fastapi")

    Returns:
        Tuple of (statistics dict, url_patterns list)
    """
    # Extract URL patterns if not provided
    if url_patterns is None:
        if framework == "fastapi":
            url_patterns = extract_fastapi_routes(repo_path)
        else:
            url_patterns = extract_django_urls(repo_path, urls_file)

    if not url_patterns:
        return {"populated": 0, "skipped": 0, "errors": 0}, []

    # Find all contract files
    contract_files = list(contracts_dir.glob("*.openapi.yaml"))

    stats = {"populated": 0, "skipped": 0, "errors": 0}

    for contract_file in contract_files:
        try:
            # Load contract
            with contract_file.open("r", encoding="utf-8") as f:
                contract_data = yaml.safe_load(f)  # type: ignore[assignment]
                if not isinstance(contract_data, dict):
                    contract_data = {}
                contract = cast(dict[str, object], contract_data)

            if "paths" not in contract:
                contract["paths"] = {}

            # Extract feature key from filename
            feature_key = contract_file.stem.replace(".openapi", "").upper()

            # Find matching URL patterns
            matching_patterns = [p for p in url_patterns if _match_url_to_feature(p, feature_key)]

            if not matching_patterns:
                stats["skipped"] += 1
                continue

            # Populate paths
            for pattern in matching_patterns:
                path = str(pattern["path"])
                method = str(pattern["method"]).lower()

                paths_dict = contract.get("paths", {})
                if not isinstance(paths_dict, dict):
                    paths_dict = {}
                    contract["paths"] = paths_dict
                if path not in paths_dict:
                    paths_dict[path] = {}  # type: ignore[assignment]

                # Check if operation already exists (may have enriched schemas)
                existing_operation: dict[str, object] | None = None
                if isinstance(paths_dict, dict) and isinstance(paths_dict.get(path), dict):
                    existing_operation = paths_dict[path].get(method)  # type: ignore[index]
                    if not isinstance(existing_operation, dict):
                        existing_operation = None

                # Extract form schema if enabled (Django only)
                form_schema: dict[str, object] | None = None
                if extract_forms and framework == "django":
                    view_ref = pattern.get("view")
                    if view_ref:
                        view_str = str(view_ref)
                        if "." in view_str:
                            parts = view_str.split(".")
                            if len(parts) >= 2:
                                view_module = ".".join(parts[:-1])
                                view_function = parts[-1]
                                form_schema = extract_view_form_schema(repo_path, view_module, view_function)

                operation = _create_openapi_operation(pattern, repo_path, form_schema, framework)  # type: ignore[arg-type]

                # Merge with existing operation, preserving enriched schemas
                if existing_operation:
                    # Preserve enriched requestBody if it exists
                    existing_request_body = existing_operation.get("requestBody")
                    if existing_request_body and isinstance(existing_request_body, dict):
                        existing_content = existing_request_body.get("content", {})
                        if isinstance(existing_content, dict):
                            # Check if ANY content type has enriched schema (has properties with proper types, not just 'object')
                            # This handles cases where enriched contract uses application/json but
                            # existing contract might have application/x-www-form-urlencoded
                            has_enriched_schema = False
                            for _content_type, content_schema in existing_content.items():
                                if isinstance(content_schema, dict):
                                    schema = content_schema.get("schema", {})
                                    if isinstance(schema, dict):
                                        properties = schema.get("properties", {})
                                        required = schema.get("required", [])
                                        # Consider enriched if it has properties with proper types (not just 'object')
                                        if isinstance(properties, dict) and properties:
                                            # Check if at least one property has a proper type (not 'object')
                                            for prop in properties.values():
                                                if isinstance(prop, dict):
                                                    prop_type = prop.get("type", "")
                                                    if prop_type and prop_type != "object":
                                                        has_enriched_schema = True
                                                        break
                                            if has_enriched_schema:
                                                break
                                        # Also consider enriched if it has required fields (even with weak types)
                                        elif isinstance(required, list) and required:
                                            has_enriched_schema = True
                                            break

                            if has_enriched_schema:
                                # Has enriched schema - merge individual properties, preserving enriched ones and replacing weak ones
                                # This allows us to update weak properties (type: 'object') while preserving enriched ones
                                new_request_body = operation.get("requestBody")
                                if new_request_body and isinstance(new_request_body, dict):
                                    new_content = new_request_body.get("content", {})
                                    if isinstance(new_content, dict):
                                        # Merge: keep existing content types, but replace weak properties with extracted ones
                                        merged_content = copy.deepcopy(existing_content)
                                        for content_type, content_schema in new_content.items():
                                            if content_type not in merged_content:
                                                # New content type - add it
                                                merged_content[content_type] = content_schema
                                            else:
                                                # Content type exists - merge individual properties
                                                existing_schema = merged_content[content_type]
                                                if isinstance(existing_schema, dict) and isinstance(
                                                    content_schema, dict
                                                ):
                                                    existing_schema_obj = existing_schema.get("schema", {})
                                                    new_schema_obj = content_schema.get("schema", {})
                                                    if isinstance(existing_schema_obj, dict) and isinstance(
                                                        new_schema_obj, dict
                                                    ):
                                                        existing_props = existing_schema_obj.get("properties", {})
                                                        new_props = new_schema_obj.get("properties", {})
                                                        if isinstance(existing_props, dict) and isinstance(
                                                            new_props, dict
                                                        ):
                                                            # Merge properties: replace weak ones (type: 'object') with extracted ones
                                                            merged_props = dict(existing_props)
                                                            for prop_name, new_prop in new_props.items():
                                                                existing_prop = merged_props.get(prop_name, {})
                                                                if isinstance(new_prop, dict) and isinstance(
                                                                    existing_prop, dict
                                                                ):
                                                                    new_type = new_prop.get("type", "")
                                                                    existing_type = existing_prop.get("type", "")
                                                                    new_has_proper_type = (
                                                                        new_type and new_type != "object"
                                                                    )
                                                                    existing_has_weak_type = (
                                                                        not existing_type or existing_type == "object"
                                                                    )

                                                                    # Replace weak properties with extracted ones, preserve enriched ones
                                                                    if new_has_proper_type and existing_has_weak_type:
                                                                        merged_props[prop_name] = new_prop
                                                                    elif (
                                                                        new_has_proper_type
                                                                        and existing_type == new_type
                                                                    ):
                                                                        # Both have same type - prefer new if it has more constraints
                                                                        new_constraints = sum(
                                                                            1
                                                                            for k in new_prop
                                                                            if k
                                                                            in [
                                                                                "minLength",
                                                                                "maxLength",
                                                                                "format",
                                                                                "nullable",
                                                                                "default",
                                                                            ]
                                                                        )
                                                                        existing_constraints = sum(
                                                                            1
                                                                            for k in existing_prop
                                                                            if k
                                                                            in [
                                                                                "minLength",
                                                                                "maxLength",
                                                                                "format",
                                                                                "nullable",
                                                                                "default",
                                                                            ]
                                                                        )
                                                                        if new_constraints > existing_constraints:
                                                                            merged_props[prop_name] = new_prop
                                                                    elif not existing_prop:
                                                                        # New property - add it
                                                                        merged_props[prop_name] = new_prop
                                                            # Update the schema with merged properties
                                                            existing_schema_obj["properties"] = merged_props
                                                            # Also merge required fields
                                                            existing_required = existing_schema_obj.get("required", [])
                                                            new_required = new_schema_obj.get("required", [])
                                                            if isinstance(existing_required, list) and isinstance(
                                                                new_required, list
                                                            ):
                                                                merged_required = list(
                                                                    set(existing_required + new_required)
                                                                )
                                                                existing_schema_obj["required"] = merged_required
                                        # Update the operation's requestBody with merged content
                                        request_body = operation.get("requestBody")
                                        if isinstance(request_body, dict):
                                            request_body["content"] = merged_content
                            elif "requestBody" in operation:
                                # If no enriched schema found, but new operation has requestBody, merge content types
                                # This allows both application/json (FastAPI) and application/x-www-form-urlencoded (Django) to coexist
                                new_request_body = operation.get("requestBody")
                                if new_request_body and isinstance(new_request_body, dict):
                                    new_content = new_request_body.get("content", {})
                                    if isinstance(new_content, dict):
                                        # Merge: keep existing content types, but replace empty ones with extracted schemas
                                        # Use deep copy to ensure nested modifications are preserved
                                        merged_content = copy.deepcopy(existing_content)
                                        for content_type, content_schema in new_content.items():
                                            if content_type not in merged_content:
                                                # New content type - add it
                                                merged_content[content_type] = content_schema
                                            else:
                                                # Content type exists - check if we should replace weak schema with extracted one
                                                existing_schema = merged_content[content_type]
                                                if isinstance(existing_schema, dict) and isinstance(
                                                    content_schema, dict
                                                ):
                                                    existing_schema_obj = existing_schema.get("schema", {})
                                                    new_schema_obj = content_schema.get("schema", {})
                                                    if isinstance(existing_schema_obj, dict) and isinstance(
                                                        new_schema_obj, dict
                                                    ):
                                                        existing_props = existing_schema_obj.get("properties", {})
                                                        new_props = new_schema_obj.get("properties", {})
                                                        if isinstance(existing_props, dict) and isinstance(
                                                            new_props, dict
                                                        ):
                                                            # Check if existing schema is weak (all properties have type 'object' or no type)
                                                            existing_is_weak = True
                                                            if existing_props:
                                                                for prop in existing_props.values():
                                                                    if isinstance(prop, dict):
                                                                        prop_type = prop.get("type", "")
                                                                        if prop_type and prop_type != "object":
                                                                            existing_is_weak = False
                                                                            break
                                                            else:
                                                                existing_is_weak = True  # Empty properties = weak

                                                            # Check if new schema has proper types
                                                            new_has_proper_types = False
                                                            if new_props:
                                                                for prop in new_props.values():
                                                                    if isinstance(prop, dict):
                                                                        prop_type = prop.get("type", "")
                                                                        if prop_type and prop_type != "object":
                                                                            new_has_proper_types = True
                                                                            break

                                                            # If existing is weak and new has proper types, replace entire schema
                                                            if existing_is_weak and new_has_proper_types:
                                                                # Replace the entire content schema with the extracted one
                                                                merged_content[content_type] = content_schema
                                                            else:
                                                                # Merge individual properties: use new if it has more information
                                                                merged_props = dict(existing_props)
                                                                for prop_name, new_prop in new_props.items():
                                                                    existing_prop = merged_props.get(prop_name, {})
                                                                    if isinstance(new_prop, dict) and isinstance(
                                                                        existing_prop, dict
                                                                    ):
                                                                        new_type = new_prop.get("type", "")
                                                                        existing_type = existing_prop.get("type", "")
                                                                        new_has_proper_type = (
                                                                            new_type and new_type != "object"
                                                                        )
                                                                        existing_has_weak_type = (
                                                                            not existing_type
                                                                            or existing_type == "object"
                                                                        )

                                                                        if (
                                                                            new_has_proper_type
                                                                            and existing_has_weak_type
                                                                        ):
                                                                            merged_props[prop_name] = new_prop
                                                                        elif (
                                                                            new_has_proper_type
                                                                            and existing_type == new_type
                                                                        ):
                                                                            # Both have same type - prefer new if it has more constraints
                                                                            new_constraints = sum(
                                                                                1
                                                                                for k in new_prop
                                                                                if k
                                                                                in [
                                                                                    "minLength",
                                                                                    "maxLength",
                                                                                    "format",
                                                                                    "nullable",
                                                                                    "default",
                                                                                ]
                                                                            )
                                                                            existing_constraints = sum(
                                                                                1
                                                                                for k in existing_prop
                                                                                if k
                                                                                in [
                                                                                    "minLength",
                                                                                    "maxLength",
                                                                                    "format",
                                                                                    "nullable",
                                                                                    "default",
                                                                                ]
                                                                            )
                                                                            if new_constraints > existing_constraints:
                                                                                merged_props[prop_name] = new_prop
                                                                        elif not existing_prop:
                                                                            merged_props[prop_name] = new_prop
                                                                # Update the schema with merged properties
                                                                existing_schema_obj["properties"] = merged_props
                                                                # Also merge required fields
                                                                existing_required = existing_schema_obj.get(
                                                                    "required", []
                                                                )
                                                                new_required = new_schema_obj.get("required", [])
                                                                if isinstance(existing_required, list) and isinstance(
                                                                    new_required, list
                                                                ):
                                                                    merged_required = list(
                                                                        set(existing_required + new_required)
                                                                    )
                                                                    existing_schema_obj["required"] = merged_required
                                        # Update the operation's requestBody with merged content
                                        request_body = operation.get("requestBody")
                                        if isinstance(request_body, dict):
                                            request_body["content"] = merged_content
                            else:
                                # If new operation has requestBody, merge content types
                                new_request_body = operation.get("requestBody")
                                if new_request_body and isinstance(new_request_body, dict):
                                    new_content = new_request_body.get("content", {})
                                    if isinstance(new_content, dict):
                                        # Merge: keep existing content types, add new ones
                                        merged_content = dict(existing_content)
                                        for content_type, content_schema in new_content.items():
                                            if content_type not in merged_content:
                                                merged_content[content_type] = content_schema
                                        # Type check to ensure requestBody is a dict before setting content
                                        request_body = operation.get("requestBody")
                                        if isinstance(request_body, dict):
                                            request_body["content"] = merged_content

                    # Preserve enriched responses if they exist
                    existing_responses = existing_operation.get("responses")
                    if existing_responses and isinstance(existing_responses, dict):
                        # Check if any response has enriched schema
                        has_enriched_response = False
                        for _status_code, response in existing_responses.items():
                            if isinstance(response, dict):
                                content = response.get("content", {})
                                if isinstance(content, dict):
                                    for _content_type, content_schema in content.items():
                                        if isinstance(content_schema, dict):
                                            schema = content_schema.get("schema", {})
                                            if isinstance(schema, dict):
                                                properties = schema.get("properties", {})
                                                if isinstance(properties, dict) and properties:
                                                    has_enriched_response = True
                                                    break
                        if has_enriched_response:
                            # Merge responses, preserving enriched ones
                            merged_responses = dict(existing_responses)
                            new_responses = operation.get("responses", {})
                            if isinstance(new_responses, dict):
                                for status_code, response in new_responses.items():
                                    if status_code not in merged_responses:
                                        merged_responses[status_code] = response
                                    elif isinstance(merged_responses[status_code], dict) and isinstance(response, dict):
                                        # Preserve enriched content if it exists
                                        existing_content = merged_responses[status_code].get("content", {})
                                        new_content = response.get("content", {})
                                        if isinstance(existing_content, dict) and isinstance(new_content, dict):
                                            # Keep existing enriched content
                                            for content_type, content_schema in existing_content.items():
                                                if content_type not in new_content:
                                                    new_content[content_type] = content_schema
                                            merged_responses[status_code]["content"] = existing_content
                            operation["responses"] = merged_responses

                    # Preserve other enriched fields (parameters, etc.)
                    if "parameters" in existing_operation:
                        operation["parameters"] = existing_operation["parameters"]

                if isinstance(paths_dict, dict) and isinstance(paths_dict.get(path), dict):
                    paths_dict[path][method] = operation  # type: ignore[assignment, index]

            # Resolve schema references and add missing schemas
            contract = _resolve_schema_refs(contract)

            # Save updated contract
            with contract_file.open("w", encoding="utf-8") as f:
                yaml.dump(contract, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            stats["populated"] += 1

        except Exception as e:
            print(f"Error processing {contract_file}: {e}")
            stats["errors"] += 1

    return stats, url_patterns


def resolve_schema_refs_in_contracts(contracts_dir: Path) -> dict[str, int]:
    """
    Resolve schema references in all OpenAPI contracts.

    This function adds missing schema definitions for common types like Path, PlanBundle, etc.
    It can be used for any project type (not just Django).

    Args:
        contracts_dir: Directory containing *.openapi.yaml files

    Returns:
        Dictionary with statistics (resolved, skipped, errors)
    """
    contract_files = list(contracts_dir.glob("*.openapi.yaml"))
    stats = {"resolved": 0, "skipped": 0, "errors": 0}

    for contract_file in contract_files:
        try:
            # Load contract
            with contract_file.open("r", encoding="utf-8") as f:
                contract_data = yaml.safe_load(f)  # type: ignore[assignment]
                if not isinstance(contract_data, dict):
                    contract_data = {}
                contract = cast(dict[str, object], contract_data)

            # Resolve schema references
            # Get original schemas BEFORE resolving (make a copy since _resolve_schema_refs modifies in place)
            import json

            components = contract.get("components")
            original_schemas: dict[str, object] = {}
            original_schemas_str = ""
            if isinstance(components, dict):
                schemas = components.get("schemas")
                if isinstance(schemas, dict):
                    original_schemas = schemas.copy()  # Make a copy to avoid reference issues
                    # Also serialize to string for comparison (to detect schema fixes, not just additions)
                    original_schemas_str = json.dumps(original_schemas, sort_keys=True)

            contract = _resolve_schema_refs(contract)

            new_schemas: dict[str, object] = {}
            components_after = contract.get("components")
            if isinstance(components_after, dict):
                schemas_after = components_after.get("schemas")
                if isinstance(schemas_after, dict):
                    new_schemas = schemas_after

            # Check if schemas were added OR fixed (hotpatch for PlanBundle schema bug)
            schemas_changed = False
            if len(new_schemas) > len(original_schemas):
                schemas_changed = True
            elif len(new_schemas) == len(original_schemas) and len(original_schemas) > 0 and original_schemas_str:
                # Check if any schemas were modified (e.g., PlanBundle.themes fix)
                new_schemas_str = json.dumps(new_schemas, sort_keys=True)
                if new_schemas_str != original_schemas_str:
                    schemas_changed = True

            if schemas_changed:
                # Save updated contract
                with contract_file.open("w", encoding="utf-8") as f:
                    yaml.dump(contract, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                stats["resolved"] += 1
            else:
                stats["skipped"] += 1

        except Exception as e:
            print(f"Error processing {contract_file}: {e}")
            stats["errors"] += 1

    return stats


def generate_bindings(url_patterns: list[dict[str, object]], bindings_path: Path) -> dict[str, int]:
    """
    Generate bindings.yaml from Django URL patterns.

    Args:
        url_patterns: List of URL pattern dictionaries from extractor
        bindings_path: Path to bindings.yaml file to create/update

    Returns:
        Dictionary with statistics (generated, skipped, errors)
    """
    if not url_patterns:
        return {"generated": 0, "skipped": 0, "errors": 0}

    bindings: list[dict[str, object]] = []

    for pattern in url_patterns:
        operation_id = pattern.get("operation_id")
        # FastAPI uses "function", Django uses "view"
        view = pattern.get("view") or pattern.get("function")
        path = str(pattern.get("path", ""))

        if not operation_id or not view:
            continue

        # Convert view/function reference to target format (taskManager.views.index -> taskManager.views:index)
        # For FastAPI: backend.app.api.routes.login.login_access_token -> backend.app.api.routes.login:login_access_token
        if "." in str(view):
            parts = str(view).rsplit(".", 1)
            target = f"{parts[0]}:{parts[1]}"
        else:
            target = str(view)

        # Ensure path starts with /
        if path and not path.startswith("/"):
            path = f"/{path}"

        # Determine adapter based on function path
        # FastAPI functions are in backend.app.api.routes.* or *.routes.*, Django views are typically in *.views.*
        adapter = "call_fastapi_route" if ("api.routes" in str(view) or ".routes." in str(view)) else "call_django_view"

        binding = {
            "operation_id": operation_id,
            "adapter": adapter,
            "target": target,
            "path": path if path else "/",
        }
        bindings.append(binding)

    # Load existing bindings if file exists
    existing_bindings: list[dict[str, object]] = []
    if bindings_path.exists():
        try:
            with bindings_path.open("r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f) or {}
                existing_bindings = existing_data.get("bindings", []) or []
        except Exception:
            existing_bindings = []

    # Merge: keep existing bindings, add new ones (don't duplicate)
    existing_ops = {b.get("operation_id") for b in existing_bindings if isinstance(b, dict)}
    new_bindings = [b for b in bindings if b.get("operation_id") not in existing_ops]
    merged_bindings = existing_bindings + new_bindings

    # Write bindings.yaml
    try:
        bindings_data = {"bindings": merged_bindings}
        with bindings_path.open("w", encoding="utf-8") as f:
            yaml.dump(bindings_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        return {"generated": len(new_bindings), "skipped": len(existing_bindings), "errors": 0}
    except Exception as e:
        print(f"Error writing bindings: {e}")
        return {"generated": 0, "skipped": 0, "errors": 1}


def main() -> int:
    """Main entry point for contract population."""
    parser = argparse.ArgumentParser(
        description="Populate OpenAPI contracts with Django URL patterns or resolve schema references."
    )
    parser.add_argument("--contracts", required=True, help="Contracts directory containing *.openapi.yaml files")
    parser.add_argument("--repo", help="Path to repository (required for URL population)")
    parser.add_argument("--urls", help="Path to urls.py file (Django only, auto-detected if not provided)")
    parser.add_argument(
        "--resolve-schemas-only", action="store_true", help="Only resolve schema references, don't populate URLs"
    )
    parser.add_argument("--bindings", help="Path to bindings.yaml file to generate (auto-generated if not provided)")
    parser.add_argument(
        "--framework", choices=["django", "fastapi"], default="django", help="Framework type (default: django)"
    )
    args = parser.parse_args()

    contracts_dir = Path(str(args.contracts)).resolve()  # type: ignore[arg-type]

    if not contracts_dir.exists():
        print(f"Error: Contracts directory not found: {contracts_dir}")
        return 1

    # If --resolve-schemas-only, just resolve schema references
    if args.resolve_schemas_only:
        stats = resolve_schema_refs_in_contracts(contracts_dir)
        print(f"Resolved: {stats['resolved']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")
        return 0 if stats["errors"] == 0 else 1

    # Otherwise, do Django URL population (requires --repo)
    if not args.repo:
        print("Error: --repo is required for URL population (or use --resolve-schemas-only)")
        return 1

    repo_path = Path(str(args.repo)).resolve()  # type: ignore[arg-type]
    urls_file = Path(str(args.urls)).resolve() if args.urls else None  # type: ignore[arg-type]

    if not repo_path.exists():
        print(f"Error: Repository path not found: {repo_path}")
        return 1

    # Populate URLs and resolve schemas (returns stats and url_patterns)
    stats, url_patterns = populate_contracts(contracts_dir, repo_path, urls_file, framework=args.framework)

    # Also resolve schema references after population
    schema_stats = resolve_schema_refs_in_contracts(contracts_dir)
    stats["schema_resolved"] = schema_stats["resolved"]

    # Generate bindings.yaml if requested
    if args.bindings or url_patterns:
        bindings_path = Path(str(args.bindings)) if args.bindings else Path("bindings.yaml")
        bindings_stats = generate_bindings(url_patterns, bindings_path)
        stats["bindings_generated"] = bindings_stats["generated"]
        stats["bindings_skipped"] = bindings_stats["skipped"]
        stats["bindings_errors"] = bindings_stats["errors"]

    print(
        f"Populated: {stats['populated']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}, Schemas resolved: {stats.get('schema_resolved', 0)}"
    )
    if "bindings_generated" in stats:
        print(
            f"Bindings: Generated: {stats['bindings_generated']}, Skipped: {stats['bindings_skipped']}, Errors: {stats['bindings_errors']}"
        )

    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
