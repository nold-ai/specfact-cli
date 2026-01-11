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
def generate_harness(contracts_dir: Path, harness_path: Path) -> bool:
    """
    Generate CrossHair harness from OpenAPI contracts.

    Args:
        contracts_dir: Directory containing OpenAPI contract files
        harness_path: Path to output harness file

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

    harness_content = render_harness(operations)
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

            operations.append(
                {
                    "operation_id": op_id,
                    "path": path,
                    "method": method.upper(),
                    "parameters": all_params,
                    "request_schema": request_schema,
                    "response_schema": response_schema,
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
@require(lambda operations: isinstance(operations, list), "Operations must be a list")
@ensure(lambda result: isinstance(result, str), "Must return str")
def render_harness(operations: list[dict[str, Any]]) -> str:
    """
    Render harness Python code from operations with meaningful contracts.

    Args:
        operations: List of operation dictionaries with parameters and schemas

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
    lines.append("try:")
    lines.append("    from common import adapters as sidecar_adapters")
    lines.append("except ImportError:")
    lines.append("    sidecar_adapters = None")
    lines.append("")

    for op in operations:
        func_code = _render_operation(op)
        lines.append(func_code)
        lines.append("")

    return "\n".join(lines)


@beartype
def _render_operation(op: dict[str, Any]) -> str:
    """Render a single operation as a harness function with meaningful contracts."""
    op_id = op["operation_id"]
    method = op["method"]
    path = op["path"]
    parameters = op.get("parameters", [])
    request_schema = op.get("request_schema")
    response_schema = op.get("response_schema")

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

    # Generate postconditions from response schema
    postconditions = _generate_postconditions(response_schema)

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

    # Build call arguments
    if path_params:
        # For path params, we need to pass them in order
        call_args = ", ".join(param_names[: len(path_params)])
        if query_params:
            call_kwargs = ", ".join(f"{name}={name}" for name in param_names[len(path_params) :])
            lines.append("    if sidecar_adapters:")
            lines.append(
                f"        return sidecar_adapters.call_endpoint('{method}', '{path}', {call_args}, {call_kwargs})"
            )
        else:
            lines.append("    if sidecar_adapters:")
            lines.append(f"        return sidecar_adapters.call_endpoint('{method}', '{path}', {call_args})")
    else:
        # Fallback to *args, **kwargs
        lines.append("    if sidecar_adapters:")
        lines.append(f"        return sidecar_adapters.call_endpoint('{method}', '{path}', *args, **kwargs)")

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
def _generate_postconditions(response_schema: dict[str, Any] | None) -> list[str]:
    """Generate @ensure postconditions from response schema."""
    postconditions = []

    if response_schema:
        schema_type = response_schema.get("type")
        if schema_type == "object":
            postconditions.append("@ensure(lambda result: isinstance(result, dict), 'Response must be a dict')")
        elif schema_type == "array":
            postconditions.append("@ensure(lambda result: isinstance(result, list), 'Response must be a list')")
        elif schema_type == "string":
            postconditions.append("@ensure(lambda result: isinstance(result, str), 'Response must be a string')")
        elif schema_type == "integer":
            postconditions.append("@ensure(lambda result: isinstance(result, int), 'Response must be an integer')")
        elif schema_type == "number":
            postconditions.append(
                "@ensure(lambda result: isinstance(result, (int, float)), 'Response must be a number')"
            )
        elif schema_type == "boolean":
            postconditions.append("@ensure(lambda result: isinstance(result, bool), 'Response must be a boolean')")

        # Check required properties in response
        if schema_type == "object":
            required_props = response_schema.get("required", [])
            for prop in required_props:
                postconditions.append(
                    f"@ensure(lambda result: '{prop}' in result if isinstance(result, dict) else True, 'Response must contain {prop}')"
                )

    # Always ensure result is not None (unless sidecar_adapters unavailable)
    if not postconditions:
        postconditions.append(
            "@ensure(lambda result: result is not None or sidecar_adapters is None, 'Response must not be None when adapters available')"
        )

    return postconditions
