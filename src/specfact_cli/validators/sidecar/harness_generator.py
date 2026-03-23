"""
Harness generation logic for sidecar validation.

This module generates CrossHair harness files from OpenAPI contracts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import yaml
from beartype import beartype
from icontract import ensure, require


@beartype
@require(
    lambda contracts_dir: isinstance(contracts_dir, Path) and contracts_dir.exists(),
    "Contracts directory must exist",
)
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
                raw_contract = yaml.safe_load(f)
                contract_data: dict[str, Any] = raw_contract if isinstance(raw_contract, dict) else {}

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


def _openapi_operation_record(
    path: str,
    method: str,
    operation_dict: dict[str, Any],
    path_params: list[Any],
) -> dict[str, Any]:
    op_id = operation_dict.get("operationId") or f"{method}_{path}"
    operation_params_raw = operation_dict.get("parameters", [])
    operation_params: list[Any] = operation_params_raw if isinstance(operation_params_raw, list) else []
    all_params = path_params + operation_params
    request_body_raw = operation_dict.get("requestBody", {})
    request_body: dict[str, Any] = request_body_raw if isinstance(request_body_raw, dict) else {}
    request_schema = _extract_request_schema(request_body)
    responses_raw = operation_dict.get("responses", {})
    responses: dict[str, Any] = responses_raw if isinstance(responses_raw, dict) else {}
    response_schema = _extract_response_schema(responses)
    expected_status_codes = _extract_expected_status_codes(responses)
    response_examples = _extract_examples_from_responses(responses)
    return {
        "operation_id": op_id,
        "path": path,
        "method": method.upper(),
        "parameters": all_params,
        "request_schema": request_schema,
        "response_schema": response_schema,
        "expected_status_codes": expected_status_codes,
        "response_examples": response_examples,
    }


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

    paths_raw = contract_data.get("paths", {})
    paths: dict[str, Any] = paths_raw if isinstance(paths_raw, dict) else {}
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        path_item_dict: dict[str, Any] = path_item

        # Extract path-level parameters
        path_params_raw = path_item_dict.get("parameters", [])
        path_params: list[Any] = path_params_raw if isinstance(path_params_raw, list) else []

        for method_key, operation in path_item_dict.items():
            if not isinstance(method_key, str):
                continue
            if method_key.lower() not in ("get", "post", "put", "patch", "delete"):
                continue

            if not isinstance(operation, dict):
                continue

            operation_dict: dict[str, Any] = operation
            operations.append(_openapi_operation_record(path, method_key, operation_dict, path_params))

    return operations


@beartype
def _extract_request_schema(request_body: dict[str, Any]) -> dict[str, Any] | None:
    """Extract schema from requestBody."""
    if not request_body:
        return None

    content_raw = request_body.get("content", {})
    content: dict[str, Any] = content_raw if isinstance(content_raw, dict) else {}
    # Prefer application/json, fallback to first content type
    first_content_type = next(iter(content.keys())) if content else None
    json_candidate = content.get("application/json")
    if json_candidate is None and first_content_type:
        json_candidate = content.get(first_content_type)
    if isinstance(json_candidate, dict):
        jr: dict[str, Any] = json_candidate
        schema_out = jr.get("schema", {})
        return schema_out if isinstance(schema_out, dict) else {}
    return None


def _json_media_object_from_content(content: dict[str, Any]) -> dict[str, Any] | None:
    if not content:
        return None
    first_key = next(iter(content.keys()))
    json_obj = content.get("application/json")
    if json_obj is None:
        json_obj = content.get(first_key)
    return json_obj if isinstance(json_obj, dict) else None


@beartype
def _extract_response_schema(responses: dict[str, Any]) -> dict[str, Any] | None:
    """Extract schema from responses (prioritize 200, then first available)."""
    if not responses:
        return None

    success_response = responses.get("200") or responses.get("201") or responses.get("204")
    if not (success_response and isinstance(success_response, dict)):
        return None
    sr = cast(dict[str, Any], success_response)
    content_raw = sr.get("content", {})
    content = content_raw if isinstance(content_raw, dict) else {}
    json_candidate = _json_media_object_from_content(cast(dict[str, Any], content))
    if not isinstance(json_candidate, dict):
        return None
    schema_out = json_candidate.get("schema", {})
    return schema_out if isinstance(schema_out, dict) else {}


@beartype
def _extract_expected_status_codes(responses: dict[str, Any]) -> list[int]:
    """Extract expected HTTP status codes from OpenAPI responses."""
    if not responses:
        return [200]  # Default to 200 if no responses defined

    status_codes: list[int] = []
    for status_str, _response_def in responses.items():
        if isinstance(status_str, str) and status_str.isdigit():
            status_codes.append(int(status_str))
        elif isinstance(status_str, int):
            status_codes.append(status_str)

    # If no explicit status codes, default to 200
    if not status_codes:
        status_codes = [200]

    return sorted(status_codes)


def _append_examples_from_schema_dict(schema: dict[str, Any], examples: list[dict[str, Any]]) -> None:
    example = schema.get("example")
    if example is not None and isinstance(example, dict):
        examples.append(example)
    raw_ex = schema.get("examples", {})
    schema_examples = raw_ex if isinstance(raw_ex, dict) else {}
    for ex_val in schema_examples.values():
        if isinstance(ex_val, dict) and "value" in ex_val:
            examples.append(ex_val["value"])


@beartype
def _extract_examples_from_responses(responses: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract example values from OpenAPI responses for constraint inference."""
    examples: list[dict[str, Any]] = []
    for response_def in responses.values():
        if not isinstance(response_def, dict):
            continue
        rd = cast(dict[str, Any], response_def)
        content_raw = rd.get("content", {})
        content = content_raw if isinstance(content_raw, dict) else {}
        json_candidate = _json_media_object_from_content(cast(dict[str, Any], content))
        if not isinstance(json_candidate, dict):
            continue
        schema_raw = json_candidate.get("schema", {})
        schema = schema_raw if isinstance(schema_raw, dict) else {}
        _append_examples_from_schema_dict(schema, examples)
    return examples


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


def _flask_and_fallback_harness_lines(
    method: str,
    path: str,
    path_params: list[dict[str, Any]],
    query_params: list[dict[str, Any]],
    param_names: list[str],
) -> list[str]:
    """Lines for Flask test-client path plus sidecar fallback (used when Flask app is available)."""
    lines: list[str] = [
        "    if _flask_app_available and _flask_client:",
        "        # Call real Flask route using test client",
        "        with _flask_app.app_context():",
        "            try:",
    ]
    flask_path = path
    format_vars: list[str] = []
    for param in path_params:
        param_name = param.get("name", "")
        param_var = param_name.replace("-", "_")
        format_vars.append(param_var)

    query_parts: list[str] = []
    query_format_vars: list[str] = []
    for param in query_params:
        param_name = param.get("name", "")
        param_var = param_name.replace("-", "_")
        if param_var in param_names:
            query_parts.append(f"{param_name}={{{param_var}}}")
            query_format_vars.append(param_var)

    all_format_vars = format_vars + query_format_vars

    if query_parts:
        query_string = "&".join(query_parts)
        full_path = f"'{flask_path}?{query_string}'"
    else:
        full_path = f"'{flask_path}'"

    if all_format_vars:
        format_args = ", ".join(all_format_vars)
        lines.append(f"                response = _flask_client.{method.lower()}({full_path}.format({format_args}))")
    else:
        lines.append(f"                response = _flask_client.{method.lower()}({full_path})")

    lines.extend(
        [
            "                # Extract response data and status code",
            "                response_status = response.status_code",
            "                try:",
            "                    if response.is_json:",
            "                        response_data = response.get_json()",
            "                    else:",
            "                        response_data = response.data.decode('utf-8') if response.data else None",
            "                except Exception:",
            "                    response_data = response.data if response.data else None",
            "                # Return dict with status_code and data for contract validation",
            "                return {'status_code': response_status, 'data': response_data}",
            "            except Exception:",
            "                # If Flask route fails, return error response (violates postcondition if expecting success - this is a bug!)",
            "                return {'status_code': 500, 'data': None}",
            "    ",
            "    # Fallback to sidecar_adapters if Flask app not available",
            "    try:",
            "        from common import adapters as sidecar_adapters",
            "        if sidecar_adapters:",
        ]
    )
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
    lines.extend(
        [
            "    except ImportError:",
            "        pass",
            "    return {'status_code': 503, 'data': None}  # Service unavailable",
        ]
    )
    return lines


def _sidecar_only_harness_lines(
    method: str,
    path: str,
    path_params: list[dict[str, Any]],
    query_params: list[dict[str, Any]],
    param_names: list[str],
) -> list[str]:
    """Lines for sidecar_adapters-only harness (no Flask)."""
    lines: list[str] = []
    if path_params:
        call_args = ", ".join(param_names[: len(path_params)])
        if query_params:
            call_kwargs = ", ".join(f"{name}={name}" for name in param_names[len(path_params) :])
            lines.extend(
                [
                    "    try:",
                    "        from common import adapters as sidecar_adapters",
                    "        if sidecar_adapters:",
                ]
            )
            lines.append(
                f"            return sidecar_adapters.call_endpoint('{method}', '{path}', {call_args}, {call_kwargs})"
            )
            lines.extend(["    except ImportError:", "        pass"])
        else:
            lines.extend(
                [
                    "    try:",
                    "        from common import adapters as sidecar_adapters",
                    "        if sidecar_adapters:",
                ]
            )
            lines.append(f"            return sidecar_adapters.call_endpoint('{method}', '{path}', {call_args})")
            lines.extend(["    except ImportError:", "        pass"])
    else:
        lines.extend(
            [
                "    try:",
                "        from common import adapters as sidecar_adapters",
                "        if sidecar_adapters:",
            ]
        )
        lines.append(f"            return sidecar_adapters.call_endpoint('{method}', '{path}', *args, **kwargs)")
        lines.extend(["    except ImportError:", "        pass"])
    lines.append("    return None")
    return lines


@beartype
def _render_operation(op: dict[str, Any], use_flask_app: bool = False) -> str:
    """Render a single operation as a harness function with meaningful contracts."""
    op_id = op["operation_id"]
    method = op["method"]
    path = op["path"]
    parameters = _normalize_openapi_parameters_list(op.get("parameters", []))
    request_schema = op.get("request_schema")
    response_schema = op.get("response_schema")
    expected_status_codes = op.get("expected_status_codes", [200])

    sanitized_id = re.sub(r"[^a-zA-Z0-9_]", "_", op_id)
    func_name = f"harness_{sanitized_id}"

    path_params = [p for p in parameters if p.get("in") == "path"]
    query_params = [p for p in parameters if p.get("in") == "query"]
    response_examples = op.get("response_examples", [])

    sig_parts, param_names, param_types = _harness_build_signature_parts(path_params, query_params)

    if not sig_parts:
        sig = f"def {func_name}(*args: Any, **kwargs: Any) -> Any:"
    else:
        sig = f"def {func_name}({', '.join(sig_parts)}) -> Any:"

    preconditions = _generate_preconditions(path_params, query_params, request_schema, param_types)
    postconditions = _generate_postconditions(response_schema, expected_status_codes, method, response_examples)

    lines: list[str] = ["@beartype"]
    for precondition in preconditions:
        lines.append(precondition)
    for postcondition in postconditions:
        lines.append(postcondition)

    lines.append(sig)
    lines.append(f'    """Harness for {method} {path}."""')

    path = _harness_substitute_path_parameter_names(path, path_params)

    if use_flask_app:
        lines.extend(_flask_and_fallback_harness_lines(method, path, path_params, query_params, param_names))
    else:
        lines.extend(_sidecar_only_harness_lines(method, path, path_params, query_params, param_names))

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


def _normalize_openapi_parameters_list(parameters_raw: Any) -> list[dict[str, Any]]:
    return [p for p in (parameters_raw if isinstance(parameters_raw, list) else []) if isinstance(p, dict)]


def _harness_build_signature_parts(
    path_params: list[dict[str, Any]],
    query_params: list[dict[str, Any]],
) -> tuple[list[str], list[str], dict[str, str]]:
    sig_parts: list[str] = []
    param_names: list[str] = []
    param_types: dict[str, str] = {}
    for param in path_params:
        param_name = param.get("name", "").replace("-", "_")
        param_schema = param.get("schema", {})
        param_type = _schema_to_python_type(param_schema)
        sig_parts.append(f"{param_name}: {param_type}")
        param_names.append(param_name)
        param_types[param_name] = param_type
    for param in query_params:
        param_name = param.get("name", "").replace("-", "_")
        param_schema = param.get("schema", {})
        param_type = _schema_to_python_type(param_schema)
        if not param.get("required", False):
            param_type = f"{param_type} | None"
        sig_parts.append(f"{param_name}: {param_type} | None = None")
        param_names.append(param_name)
        param_types[param_name] = param_type
    return sig_parts, param_names, param_types


def _harness_substitute_path_parameter_names(path: str, path_params: list[dict[str, Any]]) -> str:
    out = path
    for param in path_params:
        param_name = param.get("name", "")
        param_var = param_name.replace("-", "_")
        out = out.replace(f"{{{param_name}}}", f"{{{param_var}}}")
        out = out.replace(f"<{param_name}>", f"{{{param_var}}}")
    return out


def _path_param_string_preconditions(param_name: str, param_schema: dict[str, Any]) -> list[str]:
    out: list[str] = []
    min_length = param_schema.get("minLength")
    max_length = param_schema.get("maxLength")
    if min_length is not None:
        out.append(
            f"@require(lambda {param_name}: len({param_name}) >= {min_length}, '{param_name} length must be >= {min_length}')"
        )
    if max_length is not None:
        out.append(
            f"@require(lambda {param_name}: len({param_name}) <= {max_length}, '{param_name} length must be <= {max_length}')"
        )
    if param_schema.get("minLength") is None and param_name in ("username", "slug", "token", "name"):
        out.append(f"@require(lambda {param_name}: len({param_name}) >= 1, '{param_name} must be non-empty')")
    return out


def _path_param_integer_preconditions(param_name: str, param_schema: dict[str, Any]) -> list[str]:
    out: list[str] = []
    minimum = param_schema.get("minimum")
    maximum = param_schema.get("maximum")
    if minimum is None and param_name == "id":
        minimum = 1
    if minimum is not None:
        out.append(f"@require(lambda {param_name}: {param_name} >= {minimum}, '{param_name} must be >= {minimum}')")
    if maximum is not None:
        out.append(f"@require(lambda {param_name}: {param_name} <= {maximum}, '{param_name} must be <= {maximum}')")
    return out


def _preconditions_for_path_param(param: dict[str, Any], param_types: dict[str, str]) -> list[str]:
    """Build @require lines for one path parameter."""
    out: list[str] = []
    param_name = param.get("name", "").replace("-", "_")
    param_schema = param.get("schema", {})
    param_type = param_types.get(param_name, "Any")

    if param_type != "Any":
        out.append(
            f"@require(lambda {param_name}: isinstance({param_name}, {param_type.split('[')[0]}), '{param_name} must be {param_type}')"
        )

    if param_schema.get("type") == "string":
        out.extend(_path_param_string_preconditions(param_name, param_schema))

    if param_schema.get("type") == "integer":
        out.extend(_path_param_integer_preconditions(param_name, param_schema))

    enum_vals = param_schema.get("enum")
    if enum_vals and isinstance(enum_vals, (list, tuple)):
        enum_str = ", ".join(repr(v) for v in enum_vals)
        out.append(
            f"@require(lambda {param_name}: {param_name} in ({enum_str}), '{param_name} must be one of {enum_vals}')"
        )

    return out


def _preconditions_for_request_object(request_schema: dict[str, Any]) -> list[str]:
    """Build @require lines for request body object schema."""
    out: list[str] = [
        "@require(lambda request_body: isinstance(request_body, dict), 'request_body must be a dict')",
    ]
    for prop in request_schema.get("required", []):
        out.append(f"@require(lambda request_body: '{prop}' in request_body, 'request_body must contain {prop}')")
    return out


@beartype
def _generate_preconditions(
    path_params: list[dict[str, Any]],
    query_params: list[dict[str, Any]],
    request_schema: dict[str, Any] | None,
    param_types: dict[str, str],
) -> list[str]:
    """Generate @require preconditions from parameters and request schema."""
    preconditions: list[str] = []
    for param in path_params:
        preconditions.extend(_preconditions_for_path_param(param, param_types))

    for param in query_params:
        if param.get("required", False):
            param_name = param.get("name", "").replace("-", "_")
            preconditions.append(f"@require(lambda {param_name}: {param_name} is not None, '{param_name} is required')")

    if request_schema and request_schema.get("type") == "object":
        preconditions.extend(_preconditions_for_request_object(request_schema))

    if not preconditions:
        preconditions.append("@require(lambda *args, **kwargs: True, 'Precondition')")

    return preconditions


def _postconditions_status_code_lines(expected_status_codes: list[int] | None) -> list[str]:
    """Build @ensure lines for HTTP status codes."""
    out: list[str] = []
    if expected_status_codes:
        expanded_codes = set(expected_status_codes)
        expanded_codes.update([200, 201, 204])
        expanded_codes.update([302, 404])
        expanded_codes.discard(500)
        status_codes_str = ", ".join(map(str, sorted(expanded_codes)))
        if len(expanded_codes) == 1:
            single_code = next(iter(expanded_codes))
            out.append(
                f"@ensure(lambda result: result.get('status_code') == {single_code}, 'Response status code must be {single_code}')"
            )
        else:
            out.append(
                f"@ensure(lambda result: result.get('status_code') in [{status_codes_str}], 'Response status code must be one of [{status_codes_str}]')"
            )
    else:
        out.append(
            "@ensure(lambda result: result.get('status_code') in [200, 201, 204, 302, 404], 'Response status code must be valid (200, 201, 204, 302, or 404)')"
        )
        out.append(
            "@ensure(lambda result: result.get('status_code') != 500, 'Response status code must not be 500 (server error)')"
        )
    return out


def _postconditions_top_level_data_type(schema_type: str | None) -> list[str]:
    """@ensure lines for result['data'] top-level JSON type."""
    if schema_type == "object":
        return ["@ensure(lambda result: isinstance(result.get('data'), dict), 'Response data must be a dict')"]
    if schema_type == "array":
        return ["@ensure(lambda result: isinstance(result.get('data'), list), 'Response data must be a list')"]
    if schema_type == "string":
        return ["@ensure(lambda result: isinstance(result.get('data'), str), 'Response data must be a string')"]
    if schema_type == "integer":
        return ["@ensure(lambda result: isinstance(result.get('data'), int), 'Response data must be an integer')"]
    if schema_type == "number":
        return [
            "@ensure(lambda result: isinstance(result.get('data'), (int, float)), 'Response data must be a number')"
        ]
    if schema_type == "boolean":
        return ["@ensure(lambda result: isinstance(result.get('data'), bool), 'Response data must be a boolean')"]
    return []


def _scalar_object_property_ensure_line(prop_name: str, prop_type: Any) -> str | None:
    if prop_type == "string":
        return f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), str) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be a string')"
    if prop_type == "integer":
        return f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), int) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be an integer')"
    if prop_type == "number":
        return f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), (int, float)) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be a number')"
    if prop_type == "boolean":
        return f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), bool) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be a boolean')"
    if prop_type == "array":
        return f"@ensure(lambda result: isinstance(result.get('data', {{}}).get('{prop_name}'), list) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be an array')"
    return None


def _id_property_minimum_ensure_lines(prop_name: str, prop_type: Any, ps: dict[str, Any]) -> list[str]:
    if prop_name != "id" or prop_type != "integer":
        return []
    min_val = ps.get("minimum", 1)
    return [
        f"@ensure(lambda result: result.get('data', {{}}).get('{prop_name}', 0) >= {min_val} if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) and result.get('status_code') in [200, 201, 204] else True, 'Response data.{prop_name} must be valid ID (>= {min_val})')"
    ]


def _enum_property_ensure_line(prop_name: str, ps: dict[str, Any]) -> str | None:
    enum_vals = ps.get("enum")
    if not enum_vals or not isinstance(enum_vals, (list, tuple)):
        return None
    enum_str = ", ".join(repr(v) for v in enum_vals)
    return f"@ensure(lambda result: result.get('data', {{}}).get('{prop_name}') in ({enum_str}) if isinstance(result.get('data'), dict) and '{prop_name}' in result.get('data', {{}}) else True, 'Response data.{prop_name} must be one of {list(enum_vals)}')"


def _postconditions_object_properties(response_schema: dict[str, Any]) -> list[str]:
    """@ensure lines for object properties and nested constraints."""
    out: list[str] = []
    required_raw = response_schema.get("required", [])
    required_props: list[Any] = required_raw if isinstance(required_raw, list) else []
    for prop in required_props:
        out.append(
            f"@ensure(lambda result: '{prop}' in result.get('data', {{}}) if isinstance(result.get('data'), dict) else True, 'Response data must contain {prop}')"
        )

    properties_raw = response_schema.get("properties", {})
    properties: dict[str, Any] = properties_raw if isinstance(properties_raw, dict) else {}
    for prop_name, prop_schema in properties.items():
        if not isinstance(prop_schema, dict):
            continue
        ps: dict[str, Any] = prop_schema
        prop_type = ps.get("type")
        scalar = _scalar_object_property_ensure_line(prop_name, prop_type)
        if scalar:
            out.append(scalar)
        out.extend(_id_property_minimum_ensure_lines(prop_name, prop_type, ps))
        enum_line = _enum_property_ensure_line(prop_name, ps)
        if enum_line:
            out.append(enum_line)
    return out


def _postconditions_array_items(response_schema: dict[str, Any]) -> list[str]:
    """@ensure lines for array item typing."""
    out: list[str] = []
    items_schema_raw = response_schema.get("items", {})
    if not isinstance(items_schema_raw, dict):
        return out
    items_schema: dict[str, Any] = items_schema_raw
    item_type = items_schema.get("type")
    if item_type == "object":
        out.append(
            "@ensure(lambda result: all(isinstance(item, dict) for item in result.get('data', [])) if isinstance(result.get('data'), list) else True, 'Response data array items must be objects')"
        )
    elif item_type == "string":
        out.append(
            "@ensure(lambda result: all(isinstance(item, str) for item in result.get('data', [])) if isinstance(result.get('data'), list) else True, 'Response data array items must be strings')"
        )
    return out


def _postconditions_from_response_schema(
    response_schema: dict[str, Any],
    response_examples: list[dict[str, Any]] | None,
) -> list[str]:
    """Build schema-driven @ensure lines."""
    out: list[str] = []
    schema_type = response_schema.get("type")
    out.extend(_postconditions_top_level_data_type(schema_type))

    if schema_type == "object":
        out.extend(_postconditions_object_properties(response_schema))
        props_chk = response_schema.get("properties")
        props_for_id: dict[str, Any] = props_chk if isinstance(props_chk, dict) else {}
        if response_examples and not props_for_id.get("id"):
            for ex in response_examples:
                if isinstance(ex, dict) and "id" in ex and isinstance(ex["id"], (int, float)) and ex["id"] >= 1:
                    out.append(
                        "@ensure(lambda result: (not isinstance(result.get('data'), dict)) or ('id' not in result.get('data', {})) or result.get('data', {}).get('id', 0) >= 1, 'Response id must be valid (>= 1) when present')"
                    )
                    break
    elif schema_type == "array":
        out.extend(_postconditions_array_items(response_schema))

    return out


@beartype
def _generate_postconditions(
    response_schema: dict[str, Any] | None,
    expected_status_codes: list[int] | None = None,
    method: str = "GET",
    response_examples: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Generate @ensure postconditions from response schema, status codes, and business rules."""
    postconditions: list[str] = [
        "@ensure(lambda result: isinstance(result, dict) and 'status_code' in result and 'data' in result, 'Response must be dict with status_code and data')",
    ]
    postconditions.extend(_postconditions_status_code_lines(expected_status_codes))

    if response_schema:
        postconditions.extend(_postconditions_from_response_schema(response_schema, response_examples))

    success_codes = expected_status_codes or [200]
    success_codes_str = ", ".join(map(str, success_codes))
    postconditions.append(
        f"@ensure(lambda result: result.get('data') is not None if result.get('status_code') in [{success_codes_str}] else True, 'Response data must not be None for success status codes')"
    )

    return postconditions
