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
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

import yaml


# Type stubs for template file imports
# These are template files that get copied to sidecar workspace where imports work at runtime
if TYPE_CHECKING:

    def extract_django_urls(repo_path: Path, urls_file: Path | None = None) -> list[dict[str, object]]: ...
    def extract_view_form_schema(repo_path: Path, view_module: str, view_function: str) -> dict[str, object] | None: ...


# Import from same directory (sidecar templates)
# These scripts are run directly, so we need to handle imports differently
# Add current directory to path for direct import when run as script
_script_dir = Path(__file__).parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

# These imports work at runtime when scripts are run directly from sidecar directory
# Type checker uses TYPE_CHECKING stubs above; runtime uses actual imports below
# The sidecar directory has __init__.py, making it a package, so relative imports work at runtime
try:
    # Try explicit relative imports first (preferred for type checking)
    # These work when the sidecar directory is a proper package (has __init__.py)
    from .django_form_extractor import (  # type: ignore[reportMissingImports]
        extract_view_form_schema,
    )
    from .django_url_extractor import extract_django_urls  # type: ignore[reportMissingImports]
except ImportError:
    # Fallback for when run as script (runtime path manipulation case)
    # This happens when the script is executed directly from the sidecar workspace
    # and sys.path manipulation makes absolute imports work
    from django_form_extractor import (  # type: ignore[reportMissingImports]
        extract_view_form_schema,
    )
    from django_url_extractor import (
        extract_django_urls,  # type: ignore[reportImplicitRelativeImport, reportMissingImports]
    )


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
) -> dict[str, object]:
    """
    Create OpenAPI operation from Django URL pattern.

    Args:
        url_pattern: URL pattern dictionary from extractor
        repo_path: Path to Django repository (for form extraction)
        form_schema: Optional pre-extracted form schema

    Returns:
        OpenAPI operation dictionary
    """
    method = str(url_pattern["method"]).lower()
    path = str(url_pattern["path"])
    operation_id = str(url_pattern["operation_id"])
    path_params = url_pattern.get("path_params", [])
    if not isinstance(path_params, list):
        path_params = []
    view_ref = url_pattern.get("view")

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
        # Try to extract form schema from view
        schema: dict[str, object] | None = form_schema
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

        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
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
    contracts_dir: Path, repo_path: Path, urls_file: Path | None = None, extract_forms: bool = True
) -> dict[str, int]:
    """
    Populate OpenAPI contract stubs with Django URL patterns.

    Args:
        contracts_dir: Directory containing *.openapi.yaml files
        repo_path: Path to Django repository
        urls_file: Path to urls.py file (auto-detected if not provided)

    Returns:
        Dictionary with statistics (populated, skipped, errors)
    """
    # Extract Django URL patterns
    url_patterns = extract_django_urls(repo_path, urls_file)

    if not url_patterns:
        return {"populated": 0, "skipped": 0, "errors": 0}

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

                # Extract form schema if enabled
                form_schema: dict[str, object] | None = None
                if extract_forms:
                    view_ref = pattern.get("view")
                    if view_ref:
                        view_str = str(view_ref)
                        if "." in view_str:
                            parts = view_str.split(".")
                            if len(parts) >= 2:
                                view_module = ".".join(parts[:-1])
                                view_function = parts[-1]
                                form_schema = extract_view_form_schema(repo_path, view_module, view_function)

                operation = _create_openapi_operation(pattern, repo_path, form_schema)  # type: ignore[arg-type]
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

    return stats


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


def main() -> int:
    """Main entry point for contract population."""
    parser = argparse.ArgumentParser(
        description="Populate OpenAPI contracts with Django URL patterns or resolve schema references."
    )
    parser.add_argument("--contracts", required=True, help="Contracts directory containing *.openapi.yaml files")
    parser.add_argument("--repo", help="Path to Django repository (required for URL population)")
    parser.add_argument("--urls", help="Path to urls.py file (auto-detected if not provided)")
    parser.add_argument(
        "--resolve-schemas-only", action="store_true", help="Only resolve schema references, don't populate URLs"
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

    # Populate URLs and resolve schemas
    stats = populate_contracts(contracts_dir, repo_path, urls_file)

    # Also resolve schema references after population
    schema_stats = resolve_schema_refs_in_contracts(contracts_dir)
    stats["schema_resolved"] = schema_stats["resolved"]

    print(
        f"Populated: {stats['populated']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}, Schemas resolved: {stats.get('schema_resolved', 0)}"
    )

    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
