# Flask-Specific Sidecar Validation Guide

**Date**: 2026-01-12  
**Status**: ✅ **COMPLETE**  
**Purpose**: Flask-specific documentation for sidecar validation

---

## Overview

Flask applications are fully supported by SpecFact CLI sidecar validation. The system automatically detects Flask applications, extracts routes, and generates contracts for validation.

## Flask Detection

Flask applications are automatically detected by looking for:

- Flask imports: `from flask import Flask` or `import flask`
- Flask app instantiation: `app = Flask(__name__)` or `Flask(__name__)`
- Flask route decorators: `@app.route()` or `@bp.route()`

**Detection Priority**: Flask is detected before Django if both are present (Flask has higher priority).

## Route Extraction

### Supported Patterns

Flask route extraction supports:

1. **Application Routes**:
   ```python
   @app.route('/users/<int:id>', methods=['GET'])
   def get_user(id):
       return jsonify({'id': id})
   ```

2. **Blueprint Routes**:
   ```python
   bp = Blueprint('api', __name__)
   
   @bp.route('/posts/<slug>', methods=['GET'])
   def get_post(slug):
       return jsonify({'slug': slug})
   ```

3. **Path Parameters**:
   - `<int:id>` → `{id}` with `type: integer`
   - `<float:value>` → `{value}` with `type: number`
   - `<path:path>` → `{path}` with `type: string`
   - `<slug>` → `{slug}` with `type: string` (default)

### Extraction Process

1. **AST Parsing**: Parses Python files to find route decorators
2. **Route Information**: Extracts path, methods, and function names
3. **Parameter Conversion**: Converts Flask path parameters to OpenAPI format
4. **Contract Generation**: Creates OpenAPI operations for each route

## Contract Validation

### Status Code Validation

Flask routes are validated against expected status codes extracted from OpenAPI contracts:

- **Allowed Status Codes**: `[200, 201, 204, 302, 404]` (common Flask responses)
- **Rejected Status Codes**: `500` (server errors indicate bugs)
- **Validation**: CrossHair checks that responses match expected status codes

### Response Structure Validation

Contracts validate response structure based on OpenAPI schemas:

- **Required Fields**: Validates that required fields are present in responses
- **Type Validation**: Checks that response data types match OpenAPI spec
- **Nested Objects**: Validates nested object properties
- **Arrays**: Validates array item types

### Example Contract

```yaml
paths:
  /users/{id}:
    get:
      operationId: get_user
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                type: object
                required: [id, email]
                properties:
                  id:
                    type: integer
                  email:
                    type: string
                    format: email
        '404':
          description: User not found
```

## Dependency Installation

### Automatic Installation

Sidecar validation automatically:

1. **Creates Isolated Venv**: Creates `.specfact/venv/` for dependency isolation
2. **Installs Framework Dependencies**: Installs Flask, Werkzeug, and CrossHair
3. **Installs Project Dependencies**: Detects and installs from:
   - `requirements.txt` (pip)
   - `pyproject.toml` (hatch, poetry, uv)
   - `poetry.lock` (poetry)
4. **Installs Harness Dependencies**: Installs `beartype` and `icontract` for harness execution

### Manual Installation

If automatic installation fails, you can manually install dependencies:

```bash
cd /path/to/flask-app
python3 -m venv .specfact/venv
.specfact/venv/bin/pip install flask werkzeug crosshair-tool beartype icontract
.specfact/venv/bin/pip install -r requirements.txt
```

## Harness Generation

### Flask App Integration

The generated harness automatically:

1. **Imports Flask App**: Attempts to import Flask app from repository
2. **Creates Test Client**: Uses Flask test client for route execution
3. **Calls Real Routes**: Executes actual Flask routes during validation
4. **Extracts Responses**: Captures response status codes and data

### Harness Structure

```python
# Flask app import (automatic)
try:
    from app import create_app as _create_flask_app
    _flask_app = _create_flask_app()
    _flask_client = _flask_app.test_client()
    _flask_app_available = True
except Exception:
    _flask_app = None
    _flask_client = None
    _flask_app_available = False

# Harness function
@beartype
@require(lambda *args, **kwargs: True, 'Precondition')
@ensure(lambda result: result.get('status_code') in [200, 201, 204, 302, 404], 'Valid status code')
def harness_get_user(*args: Any, **kwargs: Any) -> Any:
    """Harness for GET /users/{id}."""
    if _flask_app_available and _flask_client:
        with _flask_app.app_context():
            response = _flask_client.get(f'/users/{kwargs.get("id")}')
            return {
                'status_code': response.status_code,
                'data': response.get_json() if response.is_json else response.data
            }
    return {'status_code': 503, 'data': None}  # Fallback
```

## CrossHair Execution

### Execution Environment

CrossHair runs in the sidecar venv to ensure Flask is available:

- **Venv Python**: Uses `.specfact/venv/bin/python` when available
- **System Fallback**: Falls back to system CrossHair if venv unavailable
- **PYTHONPATH**: Automatically set to include venv site-packages

### Timeout Configuration

Default timeout settings for Flask applications:

- **Overall Timeout**: 120 seconds (allows analysis of multiple routes)
- **Per-Path Timeout**: 10 seconds (prevents single route from blocking)
- **Per-Condition Timeout**: 5 seconds (prevents individual checks from hanging)

### Expected Behavior

For complex Flask applications:

- **Timeouts Are Expected**: Symbolic execution of Flask routes is computationally expensive
- **Partial Results**: Per-path timeouts ensure partial results are available even if overall timeout is reached
- **Status**: "Not confirmed" indicates analysis is working but couldn't complete within timeout

## Example Workflow

### Step 1: Initialize Sidecar Workspace

```bash
specfact validate sidecar init microblog /path/to/microblog
```

**Output**:
```
✓ Sidecar workspace initialized successfully
  Framework detected: FrameworkType.FLASK
```

### Step 2: Run Validation

```bash
specfact validate sidecar run microblog /path/to/microblog --no-run-specmatic
```

**Output**:
```
Validation Results:
  Framework: FrameworkType.FLASK
  Routes extracted: 52
  Contracts populated: 23
  Harness generated: True

CrossHair Results:
  ✗ harness
    Error: CrossHair analysis timed out. This is expected for complex applications with 
many routes. Some routes were analyzed before timeout. Check the summary file 
for partial results.
  CrossHair: 1 not confirmed
  Summary file: .specfact/projects/microblog/reports/sidecar/crosshair-summary-*.json
```

### Step 3: Review Results

Check the summary file for detailed analysis results:

```bash
cat .specfact/projects/microblog/reports/sidecar/crosshair-summary-*.json | jq
```

## Troubleshooting

### Flask Not Detected

**Issue**: Framework detected as `PURE_PYTHON` instead of `FLASK`

**Solutions**:
- Ensure Flask imports are present: `from flask import Flask`
- Check that Flask app is instantiated: `app = Flask(__name__)`
- Verify repository path is correct

### Routes Not Extracted

**Issue**: `Routes extracted: 0`

**Solutions**:
- Check that route decorators use `@app.route()` or `@bp.route()`
- Verify routes are in Python files (not templates)
- Check for syntax errors in route files

### Dependencies Not Installed

**Issue**: `ModuleNotFoundError: No module named 'flask'`

**Solutions**:
- Check that sidecar venv was created: `.specfact/venv/` exists
- Verify dependencies were installed: Check `.specfact/venv/lib/python*/site-packages/`
- Recreate venv if broken: Delete `.specfact/venv/` and run validation again

### CrossHair Timeout

**Issue**: CrossHair analysis times out

**Explanation**: This is expected for complex Flask applications. Timeouts occur because:
- Symbolic execution of Flask routes is computationally expensive
- Database dependencies, sessions, and external services add complexity
- Multiple routes need to be analyzed

**Solutions**:
- Check summary file for partial results
- Increase timeout if needed (modify `TimeoutConfig` in code)
- Focus on specific routes by generating smaller harness files

## Best Practices

### Contract Design

1. **Extract Expected Status Codes**: Include all possible response codes in OpenAPI contracts
2. **Define Response Schemas**: Specify response structure in OpenAPI schemas
3. **Use Type Constraints**: Add type, format, and validation constraints

### Route Organization

1. **Use Blueprints**: Organize routes into blueprints for better extraction
2. **Consistent Naming**: Use consistent route and function naming
3. **Document Routes**: Add docstrings to route functions

### Validation Strategy

1. **Start Simple**: Begin with simple routes before complex ones
2. **Incremental Validation**: Validate routes incrementally
3. **Review Partial Results**: Check summary files even if timeout occurs

## Related Documentation

- [Sidecar Validation Guide](../../../../specfact-cli/docs/guides/sidecar-validation.md) - General sidecar guide
- [Sidecar Execution Guide](./SIDECAR-EXECUTION-GUIDE.md) - Execution workflow
- [Investigation Report](./INVESTIGATION.md) - CrossHair execution investigation

---

**Rulesets Applied**: SpecFact CLI rules, Python GitHub rules, Clean Code principles  
**AI Provider**: Claude (Sonnet 4.5)
