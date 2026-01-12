"""
Harness generation logic for sidecar validation.

This module generates CrossHair harness files from OpenAPI contracts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from beartype import beartype
from icontract import ensure, require


@beartype
@require(lambda contracts_dir: contracts_dir.exists(), "Contracts directory must exist")
@require(lambda harness_path: isinstance(harness_path, Path), "Harness path must be Path")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def generate_harness(contracts_dir: Path, harness_path: Path, repo_path: Path | None = None) -> bool:
    """
    Generate CrossHair harness from OpenAPI contracts.

    Args:
        contracts_dir: Directory containing OpenAPI contract files
        harness_path: Path to output harness file
        repo_path: Optional path to repository root (for importing application code)

    Returns:
        True if harness was generated successfully
    """
    contract_files = list(contracts_dir.glob("*.yaml")) + list(contracts_dir.glob("*.yml"))
    if not contract_files:
        return False

    operations: list[dict[str, Any]] = []

    for contract_file in contract_files:
        try:
            with contract_file.open(encoding="utf-8") as f:
                contract_data = yaml.safe_load(f) or {}

            ops = extract_operations(contract_data)
            operations.extend(ops)
        except Exception:
            continue

    if not operations:
        return False

    harness_content = render_harness(operations, repo_path)
    harness_path.parent.mkdir(parents=True, exist_ok=True)
    harness_path.write_text(harness_content, encoding="utf-8")

    return True


@beartype
@require(lambda contract_data: isinstance(contract_data, dict), "Contract data must be dict")
@ensure(lambda result: isinstance(result, list), "Must return list")
def extract_operations(contract_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract operations from OpenAPI contract with full schema information.

    Args:
        contract_data: Contract data dictionary

    Returns:
        List of operation dictionaries with parameters, requestBody, and responses
    """
    operations: list[dict[str, Any]] = []

    paths = contract_data.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        # Extract path-level parameters
        path_params = path_item.get("parameters", [])

        for method, operation in path_item.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue

            if not isinstance(operation, dict):
                continue

            op_id = operation.get("operationId") or f"{method}_{path}"

            # Combine path-level and operation-level parameters
            operation_params = operation.get("parameters", [])
            all_params = path_params + operation_params

            # Extract request body schema
            request_body = operation.get("requestBody", {})
            request_schema = _extract_request_schema(request_body)

            # Extract response schemas (prioritize 200, then others)
            responses = operation.get("responses", {})
            response_schema = _extract_response_schema(responses)
            expected_status_codes = _extract_expected_status_codes(responses)

            operations.append(
                {
                    "operation_id": op_id,
                    "path": path,
                    "method": method.upper(),
                    "parameters": all_params,
                    "request_schema": request_schema,
                    "response_schema": response_schema,
                    "expected_status_codes": expected_status_codes,
                }
            )

    return operations


@beartype
def _extract_request_schema(request_body: dict[str, Any]) -> dict[str, Any] | None:
    """Extract schema from requestBody."""
    if not request_body:
        return None

    content = request_body.get("content", {})
    # Prefer application/json, fallback to first content type
    first_content_type = next(iter(content.keys())) if content else None
    json_content = content.get("application/json", content.get(first_content_type) if first_content_type else None)
    if json_content and isinstance(json_content, dict):
        return json_content.get("schema", {})
    return None


@beartype
def _extract_response_schema(responses: dict[str, Any]) -> dict[str, Any] | None:
    """Extract schema from responses (prioritize 200, then first available)."""
    if not responses:
        return None

    # Prioritize 200 response
    success_response = responses.get("200") or responses.get("201") or responses.get("204")
    if success_response and isinstance(success_response, dict):
        content = success_response.get("content", {})
        first_content_type = next(iter(content.keys())) if content else None
        json_content = content.get("application/json", content.get(first_content_type) if first_content_type else None)
        if json_content and isinstance(json_content, dict):
            return json_content.get("schema", {})
    return None


@beartype
def _extract_expected_status_codes(responses: dict[str, Any]) -> list[int]:
    """Extract expected HTTP status codes from OpenAPI responses."""
    if not responses:
        return [200]  # Default to 200 if no responses defined

    status_codes = []
    for status_str, _response_def in responses.items():
        if isinstance(status_str, str) and status_str.isdigit():
            status_codes.append(int(status_str))
        elif isinstance(status_str, int):
            status_codes.append(status_str)

    # If no explicit status codes, default to 200
    if not status_codes:
        status_codes = [200]

    return sorted(status_codes)


@beartype
@require(lambda operations: isinstance(operations, list), "Operations must be a list")
@ensure(lambda result: isinstance(result, str), "Must return str")
def render_harness(operations: list[dict[str, Any]], repo_path: Path | None = None) -> str:
    """
    Render harness Python code from operations with meaningful contracts.

    Args:
        operations: List of operation dictionaries with parameters and schemas
        repo_path: Optional path to repository root (for importing application code)

    Returns:
        Harness Python code as string
    """
    lines: list[str] = []
    lines.append('"""Generated sidecar harness for CrossHair validation."""')
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("from typing import Any")
    lines.append("")
    lines.append("from beartype import beartype")
    lines.append("from icontract import ensure, require")
    lines.append("")

    # Try to import Flask app if repo_path provided
    app_imported = False
    if repo_path:
        app_imported = _add_flask_app_import(lines, repo_path)

    # Fallback to sidecar_adapters if app not imported
    if not app_imported:
        lines.append("try:")
        lines.append("    from common import adapters as sidecar_adapters")
        lines.append("except ImportError:")
        lines.append("    sidecar_adapters = None")
        lines.append("")

    for op in operations:
        func_code = _render_operation(op, app_imported)
        lines.append(func_code)
        lines.append("")

    return "\n".join(lines)


@beartype
def _add_flask_app_import(lines: list[str], repo_path: Path) -> bool:
    """Add Flask app import and test client setup."""
    # Try to detect Flask app entry point
    app_files = ["microblog.py", "app.py", "main.py", "application.py"]
    app_module = None

    for app_file in app_files:
        if (repo_path / app_file).exists():
            # Try to extract module name from file
            app_module = app_file.replace(".py", "")
            break

    # Also check for app/__init__.py with create_app
    if (repo_path / "app" / "__init__.py").exists():
        app_module = "app"

    if app_module:
        lines.append("# Import Flask application")
        lines.append("import sys")
        lines.append("from pathlib import Path")
        lines.append("")
        lines.append(f"# Add repo to path: {repo_path}")
        lines.append(f"_repo_path = Path(r'{repo_path}')")
        lines.append("if _repo_path.exists():")
        lines.append("    sys.path.insert(0, str(_repo_path))")
        lines.append("")
        lines.append("try:")
        if app_module == "app":
            lines.append("    from app import create_app")
            lines.append("    _flask_app = create_app()")
        elif app_module == "microblog":
            lines.append("    from microblog import app as _flask_app")
        else:
            lines.append(f"    from {app_module} import app as _flask_app")
        lines.append("    _flask_client = _flask_app.test_client()")
        lines.append("    _flask_app_available = True")
        lines.append("except (ImportError, AttributeError, Exception) as e:")
        lines.append("    _flask_app = None")
        lines.append("    _flask_client = None")
        lines.append("    _flask_app_available = False")
        lines.append("")
        return True

    return False


@beartype
def _render_operation(op: dict[str, Any], use_flask_app: bool = False) -> str:
    """Render a single operation as a harness function with meaningful contracts."""
    op_id = op["operation_id"]
    method = op["method"]
    path = op["path"]
    parameters = op.get("parameters", [])
    request_schema = op.get("request_schema")
    response_schema = op.get("response_schema")
    expected_status_codes = op.get("expected_status_codes", [200])

    # Sanitize operation_id to create valid Python function name
    sanitized_id = re.sub(r"[^a-zA-Z0-9_]", "_", op_id)
    func_name = f"harness_{sanitized_id}"

    # Extract path parameters for function signature
    path_params = [p for p in parameters if p.get("in") == "path"]
    query_params = [p for p in parameters if p.get("in") == "query"]

    # Generate function signature with typed parameters
    sig_parts = []
    param_names = []
    param_types = {}

    # Add path parameters
    for param in path_params:
        param_name = param.get("name", "").replace("-", "_")
        param_schema = param.get("schema", {})
        param_type = _schema_to_python_type(param_schema)
        sig_parts.append(f"{param_name}: {param_type}")
        param_names.append(param_name)
        param_types[param_name] = param_type

    # Add query parameters (as optional kwargs)
    for param in query_params:
        param_name = param.get("name", "").replace("-", "_")
        param_schema = param.get("schema", {})
        param_type = _schema_to_python_type(param_schema)
        required = param.get("required", False)
        if not required:
            param_type = f"{param_type} | None"
        sig_parts.append(f"{param_name}: {param_type} | None = None")
        param_names.append(param_name)
        param_types[param_name] = param_type

    # If no parameters, use *args, **kwargs
    if not sig_parts:
        sig = f"def {func_name}(*args: Any, **kwargs: Any) -> Any:"
    else:
        sig = f"def {func_name}({', '.join(sig_parts)}) -> Any:"

    # Generate preconditions from parameters and request schema
    preconditions = _generate_preconditions(path_params, query_params, request_schema, param_types)

    # Generate postconditions from response schema and status codes
    postconditions = _generate_postconditions(response_schema, expected_status_codes)

    # Build function code
    lines = []
    lines.append("@beartype")

    # Add preconditions
    for precondition in preconditions:
        lines.append(precondition)

    # Add postconditions
    for postcondition in postconditions:
        lines.append(postcondition)

    lines.append(sig)
    lines.append(f'    """Harness for {method} {path}."""')

    # Build path with parameters substituted
    actual_path = path
    for param in path_params:
        param_name = param.get("name", "")
        param_var = param_name.replace("-", "_")
        # Replace {param} or <param> with actual value
        actual_path = actual_path.replace(f"{{{param_name}}}", f"{{{param_var}}}")
        actual_path = actual_path.replace(f"<{param_name}>", f"{{{param_var}}}")

    # Build call to Flask test client or sidecar_adapters
    if use_flask_app:
        # Use Flask test client to call real routes
        lines.append("    if _flask_app_available and _flask_client:")
        lines.append("        # Call real Flask route using test client")
        lines.append("        with _flask_app.app_context():")
        lines.append("            try:")

        # Build Flask path - Flask uses <param> format in routes, but we have {param} in OpenAPI
        # Convert {param} to <param> for Flask, or use format() with {param}
        flask_path = path
        format_vars = []
        for param in path_params:
            param_name = param.get("name", "")
            param_var = param_name.replace("-", "_")
            # Keep {param} format for .format() call
            format_vars.append(param_var)

        # Build query string from query parameters
        # Use proper format placeholders that will be replaced by .format()
        query_parts = []
        query_format_vars = []
        for param in query_params:
            param_name = param.get("name", "")
            param_var = param_name.replace("-", "_")
            if param_var in param_names:
                # Use single braces for format placeholder, will be formatted with actual value
                query_parts.append(f"{param_name}={{{param_var}}}")
                query_format_vars.append(param_var)

        # Combine all format variables (path params + query params)
        all_format_vars = format_vars + query_format_vars

        # Build the path with query string if needed
        if query_parts:
            query_string = "&".join(query_parts)
            full_path = f"'{flask_path}?{query_string}'"
        else:
            full_path = f"'{flask_path}'"

        # Format the Flask test client call with all variables
        if all_format_vars:
            format_args = ", ".join(all_format_vars)
            lines.append(
                f"                response = _flask_client.{method.lower()}({full_path}.format({format_args}))"
            )
        else:
            lines.append(f"                response = _flask_client.{method.lower()}({full_path})")

        lines.append("                # Extract response data and status code")
        lines.append("                response_status = response.status_code")
        lines.append("                try:")
        lines.append("                    if response.is_json:")
        lines.append("                        response_data = response.get_json()")
        lines.append("                    else:")
        lines.append("                        response_data = response.data.decode('utf-8') if response.data else None")
        lines.append("                except Exception:")
        lines.append("                    response_data = response.data if response.data else None")
        lines.append("                # Return dict with status_code and data for contract validation")
        lines.append("                return {'status_code': response_status, 'data': response_data}")
        lines.append("            except Exception:")
        lines.append(
            "                # If Flask route fails, return error response (violates postcondition if expecting success - this is a bug!)"
        )
        lines.append("                return {'status_code': 500, 'data': None}")
        lines.append("    ")
        lines.append("    # Fallback to sidecar_adapters if Flask app not available")
        lines.append("    try:")
        lines.append("        from common import adapters as sidecar_adapters")
        lines.append("        if sidecar_adapters:")
        if path_params:
            call_args = ", ".join(param_names[: len(path_params)])
            if query_params:
                call_kwargs = ", ".join(f"{name}={name}" for name in param_names[len(path_params) :])
                lines.append(
                    f"            return sidecar_adapters.call_endpoint('{method}', '{path}', {call_args}, {call_kwargs})"
                )
            else:
                lines.append(f"            return sidecar_adapters.call_endpoint('{method}', '{path}', {call_args})")
        else:
            lines.append(f"            return sidecar_adapters.call_endpoint('{method}', '{path}', *args, **kwargs)")
        lines.append("    except ImportError:")
        lines.append("        pass")
        lines.append("    return {'status_code': 503, 'data': None}  # Service unavailable")
    else:
        # Original sidecar_adapters approach
        if path_params:
            call_args = ", ".join(param_names[: len(path_params)])
            if query_params:
                call_kwargs = ", ".join(f"{name}={name}" for name in param_names[len(path_params) :])
                lines.append("    try:")
                lines.append("        from common import adapters as sidecar_adapters")
                lines.append("        if sidecar_adapters:")
                lines.append(
                    f"            return sidecar_adapters.call_endpoint('{method}', '{path}', {call_args}, {call_kwargs})"
                )
                lines.append("    except ImportError:")
                lines.append("        pass")
            else:
                lines.append("    try:")
                lines.append("        from common import adapters as sidecar_adapters")
                lines.append("        if sidecar_adapters:")
                lines.append(f"            return sidecar_adapters.call_endpoint('{method}', '{path}', {call_args})")
                lines.append("    except ImportError:")
                lines.append("        pass")
        else:
            lines.append("    try:")
            lines.append("        from common import adapters as sidecar_adapters")
            lines.append("        if sidecar_adapters:")
            lines.append(f"            return sidecar_adapters.call_endpoint('{method}', '{path}', *args, **kwargs)")
            lines.append("    except ImportError:")
            lines.append("        pass")
        lines.append("    return None")

    return "\n".join(lines)


@beartype
def _schema_to_python_type(schema: dict[str, Any]) -> str:
    """Convert OpenAPI schema to Python type hint."""
    if not schema:
        return "Any"

    schema_type = schema.get("type")
    if schema_type == "string":
        return "str"
    if schema_type == "integer":
        return "int"
    if schema_type == "number":
        return "float"
    if schema_type == "boolean":
        return "bool"
    if schema_type == "array":
        items_schema = schema.get("items", {})
        item_type = _schema_to_python_type(items_schema)
        return f"list[{item_type}]"
    if schema_type == "object":
        return "dict[str, Any]"

    # Handle format
    format_type = schema.get("format")
    if format_type == "int32" or format_type == "int64":
        return "int"
    if format_type == "float" or format_type == "double":
        return "float"

    return "Any"


@beartype
def _generate_preconditions(
    path_params: list[dict[str, Any]],
    query_params: list[dict[str, Any]],
    request_schema: dict[str, Any] | None,
    param_types: dict[str, str],
) -> list[str]:
    """Generate @require preconditions from parameters and request schema."""
    preconditions = []

    # Preconditions for path parameters (always required)
    for param in path_params:
        param_name = param.get("name", "").replace("-", "_")
        param_schema = param.get("schema", {})
        param_type = param_types.get(param_name, "Any")

        # Type check precondition
        if param_type != "Any":
            preconditions.append(
                f"@require(lambda {param_name}: isinstance({param_name}, {param_type.split('[')[0]}), '{param_name} must be {param_type}')"
            )

        # String length/format constraints
        if param_schema.get("type") == "string":
            min_length = param_schema.get("minLength")
            max_length = param_schema.get("maxLength")
            if min_length is not None:
                preconditions.append(
                    f"@require(lambda {param_name}: len({param_name}) >= {min_length}, '{param_name} length must be >= {min_length}')"
                )
            if max_length is not None:
                preconditions.append(
                    f"@require(lambda {param_name}: len({param_name}) <= {max_length}, '{param_name} length must be <= {max_length}')"
                )

        # Integer range constraints
        if param_schema.get("type") == "integer":
            minimum = param_schema.get("minimum")
            maximum = param_schema.get("maximum")
            if minimum is not None:
                preconditions.append(
                    f"@require(lambda {param_name}: {param_name} >= {minimum}, '{param_name} must be >= {minimum}')"
                )
            if maximum is not None:
                preconditions.append(
                    f"@require(lambda {param_name}: {param_name} <= {maximum}, '{param_name} must be <= {maximum}')"
                )

    # Preconditions for required query parameters
    for param in query_params:
        if param.get("required", False):
            param_name = param.get("name", "").replace("-", "_")
            preconditions.append(f"@require(lambda {param_name}: {param_name} is not None, '{param_name} is required')")

    # Preconditions for request body schema
    if request_schema and request_schema.get("type") == "object":
        preconditions.append(
            "@require(lambda request_body: isinstance(request_body, dict), 'request_body must be a dict')"
        )

        # Check required properties
        required_props = request_schema.get("required", [])
        for prop in required_props:
            preconditions.append(
                f"@require(lambda request_body: '{prop}' in request_body, 'request_body must contain {prop}')"
            )

    # If no meaningful preconditions, add a minimal one
    if not preconditions:
        preconditions.append("@require(lambda *args, **kwargs: True, 'Precondition')")

    return preconditions


@beartype
def _generate_postconditions(
    response_schema: dict[str, Any] | None, expected_status_codes: list[int] | None = None
) -> list[str]:
    """Generate @ensure postconditions from response schema and expected status codes."""
    postconditions = []

    # Always check that result is a dict with status_code and data
    postconditions.append(
        "@ensure(lambda result: isinstance(result, dict) and 'status_code' in result and 'data' in result, 'Response must be dict with status_code and data')"
    )

    # Check status code matches expected codes
    # For GET requests, also allow 302 (redirects) and 404 (not found) as they're common in Flask
    # For POST/PUT/PATCH, allow 201 (created) and 204 (no content)
    if expected_status_codes:
        # Expand expected codes based on HTTP method context
        # Note: We don't have method here, so we'll use all expected codes plus common ones
        expanded_codes = set(expected_status_codes)
        # Always allow 200, 201, 204 for success
        expanded_codes.update([200, 201, 204])
        # For GET requests, also allow 302 (redirect) and 404 (not found) - these are common
        # We'll be permissive to avoid false positives, but still catch 500 errors
        expanded_codes.update([302, 404])  # Add 302 and 404 as they're common Flask responses
        expanded_codes.discard(500)  # Remove 500 from valid codes - that's a real error

        status_codes_str = ", ".join(map(str, sorted(expanded_codes)))
        if len(expanded_codes) == 1:
            single_code = next(iter(expanded_codes))
            postconditions.append(
                f"@ensure(lambda result: result.get('status_code') == {single_code}, 'Response status code must be {single_code}')"
            )
        else:
            postconditions.append(
                f"@ensure(lambda result: result.get('status_code') in [{status_codes_str}], 'Response status code must be one of [{status_codes_str}]')"
            )
    else:
        # Default: expect 200, 201, 204, 302, 404 (common Flask responses)
        # But NOT 500 (server error) - that's a real bug
        postconditions.append(
            "@ensure(lambda result: result.get('status_code') in [200, 201, 204, 302, 404], 'Response status code must be valid (200, 201, 204, 302, or 404)')"
        )
        postconditions.append(
            "@ensure(lambda result: result.get('status_code') != 500, 'Response status code must not be 500 (server error)')"
        )

    # Check response data structure based on schema
    if response_schema:
        schema_type = response_schema.get("type")
        if schema_type == "object":
            postconditions.append(
                "@ensure(lambda result: isinstance(result.get('data'), dict), 'Response data must be a dict')"
            )
        elif schema_type == "array":
            postconditions.append(
                "@ensure(lambda result: isinstance(result.get('data'), list), 'Response data must be a list')"
            )
        elif schema_type == "string":
            postconditions.append(
                "@ensure(lambda result: isinstance(result.get('data'), str), 'Response data must be a string')"
            )
        elif schema_type == "integer":
            postconditions.append(
                "@ensure(lambda result: isinstance(result.get('data'), int), 'Response data must be an integer')"
            )
        elif schema_type == "number":
            postconditions.append(
                "@ensure(lambda result: isinstance(result.get('data'), (int, float)), 'Response data must be a number')"
            )
        elif schema_type == "boolean":
            postconditions.append(
                "@ensure(lambda result: isinstance(result.get('data'), bool), 'Response data must be a boolean')"
            )

        # Check required properties in response data
        if schema_type == "object":
            required_props = response_schema.get("required", [])
            for prop in required_props:
                postconditions.append(
                    f"@ensure(lambda result: '{prop}' in result.get('data', {{}}) if isinstance(result.get('data'), dict) else True, 'Response data must contain {prop}')"
                )

            # Check property types if properties are defined
            properties = response_schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if isinstance(prop_schema, dict):
                    prop_type = prop_schema.get("type")
                    if prop_type:
                        if prop_type == "string":
                            postconditions.append(
                                f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), str) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be a string')"
                            )
                        elif prop_type == "integer":
                            postconditions.append(
                                f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), int) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be an integer')"
                            )
                        elif prop_type == "number":
                            postconditions.append(
                                f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), (int, float)) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be a number')"
                            )
                        elif prop_type == "boolean":
                            postconditions.append(
                                f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), bool) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be a boolean')"
                            )
                        elif prop_type == "array":
                            postconditions.append(
                                f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), list) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be an array')"
                            )

        # Check array item types
        elif schema_type == "array":
            items_schema = response_schema.get("items", {})
            if isinstance(items_schema, dict):
                item_type = items_schema.get("type")
                if item_type == "object":
                    postconditions.append(
                        "@ensure(lambda result: all(isinstance(item, dict) for item in result.get('data', [])) if isinstance(result.get('data'), list) else True, 'Response data array items must be objects')"
                    )
                elif item_type == "string":
                    postconditions.append(
                        "@ensure(lambda result: all(isinstance(item, str) for item in result.get('data', [])) if isinstance(result.get('data'), list) else True, 'Response data array items must be strings')"
                    )

    # Ensure data is not None when status is success
    success_codes = expected_status_codes or [200]
    success_codes_str = ", ".join(map(str, success_codes))
    postconditions.append(
        f"@ensure(lambda result: result.get('data') is not None if result.get('status_code') in [{success_codes_str}] else True, 'Response data must not be None for success status codes')"
    )

    return postconditions
