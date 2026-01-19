---
layout: default
title: Sidecar Validation Guide
permalink: /guides/sidecar-validation/
---

# Sidecar Validation Guide

Complete guide for using sidecar validation to validate external codebases without modifying source code.

## Overview

Sidecar validation enables contract-based validation of external codebases (libraries, APIs, frameworks) without requiring modifications to the source code. This is particularly useful for:

- **Validating third-party libraries** without forking or modifying them
- **Testing legacy codebases** where direct modifications are risky
- **Contract validation** of APIs where you don't control the implementation
- **Framework validation** (Django, FastAPI, DRF, Flask) using extracted routes and schemas

## Quick Start

### 1. Initialize Sidecar Workspace

```bash
specfact validate sidecar init <bundle-name> <repo-path>
```

**Example:**

```bash
specfact validate sidecar init legacy-api /path/to/django-project
```

This will:

- Detect the framework type (Django, FastAPI, DRF, pure-python)
- Create sidecar workspace directory structure
- Generate configuration files
- Detect Python environment (venv, poetry, uv, pip)
- Set up framework-specific configuration

### 2. Run Validation

```bash
specfact validate sidecar run <bundle-name> <repo-path>
```

**Example:**

```bash
# Run full validation (CrossHair + Specmatic)
specfact validate sidecar run legacy-api /path/to/django-project

# Run only CrossHair analysis
specfact validate sidecar run legacy-api /path/to/django-project --no-run-specmatic

# Run only Specmatic validation
specfact validate sidecar run legacy-api /path/to/django-project --no-run-crosshair
```

## Workflow

### Step 1: Framework Detection

The sidecar validation automatically detects the framework type:

- **Django**: Detects `manage.py` or `urls.py` files
- **FastAPI**: Detects `FastAPI()` or `@app.get()` patterns
- **DRF**: Detects `rest_framework` imports (if Django is also present)
- **Flask**: Detects `Flask()` instantiation or `from flask import Flask` imports
- **Pure Python**: No framework detected

### Step 2: Route Extraction

Framework-specific extractors extract routes and schemas:

- **Django**: Extracts URL patterns from `urls.py` and form schemas
- **FastAPI**: Extracts routes from decorators and Pydantic models
- **DRF**: Extracts serializers and converts to OpenAPI schemas
- **Flask**: Extracts routes from `@app.route()` and `@bp.route()` decorators, converts path parameters (`<int:id>`, `<slug>`, etc.) to OpenAPI format

### Step 3: Contract Population

OpenAPI contracts are populated with extracted routes and schemas:

- Routes are matched to contract features
- Request/response schemas are merged
- Path parameters are extracted and documented
- **Expected status codes** are automatically extracted from OpenAPI `responses` sections
- **Response structure validation** is added based on OpenAPI schemas (required fields, property types, array items)

### Step 4: Harness Generation

CrossHair harness files are generated from populated contracts:

- Creates Python harness with `@icontract` decorators
- Generates test inputs JSON file
- Creates bindings YAML for framework adapters

### Step 5: Validation Execution

Validation tools are executed:

- **CrossHair**: Symbolic execution on source code and harness
- **Specmatic**: Contract testing against API endpoints (if available)

## Supported Frameworks

### Django

**Detection:**

- Looks for `manage.py` or `urls.py` files
- Auto-detects `DJANGO_SETTINGS_MODULE` from `manage.py`

**Extraction:**

- URL patterns from `urlpatterns` in `urls.py`
- Form schemas from Django form classes
- View references (function-based and class-based)

**Example:**

```bash
specfact validate sidecar init django-app /path/to/django-project
specfact validate sidecar run django-app /path/to/django-project
```

### FastAPI

**Detection:**

- Looks for `FastAPI()` or `@app.get()` patterns in `main.py` or `app.py`

**Extraction:**

- Route decorators (`@app.get()`, `@app.post()`, etc.)
- Pydantic models from route signatures
- Path parameters and request/response schemas

**Example:**

```bash
specfact validate sidecar init fastapi-app /path/to/fastapi-project
specfact validate sidecar run fastapi-app /path/to/fastapi-project
```

### Django REST Framework (DRF)

**Detection:**

- Detects Django + `rest_framework` imports

**Extraction:**

- Serializers from DRF serializer classes
- OpenAPI schema conversion
- Route patterns from Django URLs

**Example:**

```bash
specfact validate sidecar init drf-api /path/to/drf-project
specfact validate sidecar run drf-api /path/to/drf-project
```

### Flask

**Detection:**

- Looks for `Flask()` instantiation or `from flask import Flask` imports
- Detects Flask route decorators (`@app.route()`, `@bp.route()`)

**Extraction:**

- Route decorators (`@app.route()`, `@bp.route()`)
- **All HTTP methods** are captured (e.g., `methods=['GET','POST']` generates separate routes for each method)
- Path parameters converted to OpenAPI format (`<int:id>` → `{id}` with `type: integer`)
- **Parameter names preserved** for converter-based paths (e.g., `<uuid:user_id>` → `{user_id}`, not `{uuid}`)
- HTTP methods from decorators
- Blueprint routes

**Example:**

```bash
specfact validate sidecar init flask-app /path/to/flask-project
specfact validate sidecar run flask-app /path/to/flask-project
```

**Dependency Installation:**

Flask applications automatically have dependencies installed in an isolated venv (`.specfact/venv/`) to ensure Flask is available for harness execution:

- Framework dependencies: `flask`, `werkzeug`
- Validation tools: `crosshair-tool`
- Harness dependencies: `beartype`, `icontract`
- Project dependencies: Automatically detected and installed from `requirements.txt`, `pyproject.toml`, etc.

**Route Extraction Details:**

- **Multiple HTTP methods**: Routes with `methods=['GET','POST']` generate separate RouteInfo objects for each method
- **Converter-based paths**: Routes like `<uuid:user_id>` correctly extract `{user_id}` as the parameter name
- **Custom converters**: Unknown converters (e.g., `uuid`, custom converters) default to `string` type while preserving parameter names

### Pure Python

**Detection:**

- No framework detected

**Extraction:**

- Basic function extraction (if runtime contracts present)
- Limited schema extraction

**Example:**

```bash
specfact validate sidecar init python-lib /path/to/python-library
specfact validate sidecar run python-lib /path/to/python-library
```

## Configuration

### Sidecar Workspace Structure

After initialization, the sidecar project structure is created at:

```
.specfact/projects/<bundle-name>/
├── contracts/          # OpenAPI contract files
├── harness/            # Generated CrossHair harness files
│   └── harness_contracts.py
├── reports/
│   └── sidecar/        # Validation reports
```

### Environment Variables

Sidecar validation respects the following environment variables:

- `DJANGO_SETTINGS_MODULE`: Django settings module (auto-detected if not set)
- `PYTHONPATH`: Python path for module resolution
- `TEST_MODE`: Set to `true` to disable progress bars (for testing)

## Validation Tools

### CrossHair

**Purpose**: Symbolic execution to verify contracts

**Execution:**

- Runs on source code (if runtime contracts present)
- Runs on generated harness (external contracts)
- **Uses venv Python** (`.specfact/venv/bin/python`) when available to ensure framework dependencies are accessible
- Captures confirmed/not-confirmed/violations

**Configuration:**

- **Overall timeout**: 120 seconds (default) - allows analysis of multiple routes
- **Per-path timeout**: 10 seconds (default) - prevents single route from blocking others
- **Per-condition timeout**: 5 seconds (default) - prevents individual checks from hanging
- Verbose output options
- Module resolution handling

**Timeout Behavior:**

For complex applications, timeouts are expected and indicate normal operation:

- **"Not confirmed"** status means analysis is working but couldn't complete within timeout
- **Partial results** are available in summary files even if overall timeout is reached
- Per-path timeouts ensure progress even if some routes are slow

### Specmatic

**Purpose**: Contract testing against API endpoints

**Execution:**

- Validates API responses against OpenAPI contracts
- Requires running application server (if `SIDECAR_APP_CMD` configured)
- Can use Specmatic stub server for testing

**Auto-Skip Behavior:**

Specmatic is automatically skipped when no service configuration is detected. This prevents unnecessary validation attempts when:

- No `test_base_url` is configured
- No `host` and `port` combination is available
- No application server command and port are configured

**When Specmatic is Auto-Skipped:**

```bash
⚠ Skipping Specmatic: No service configuration detected (use --run-specmatic to override)
```

**Manual Override:**

You can force Specmatic to run even without service configuration using the `--run-specmatic` flag:

```bash
# Force Specmatic to run (may fail if no service available)
specfact validate sidecar run legacy-api /path/to/repo --run-specmatic
```

**Configuration:**

- Base URL for API (`test_base_url`)
- Host and port (`host`, `port`)
- Application server command and port (`cmd`, `port` in app config)
- Timeout settings
- Auto-stub server options

## Progress Reporting

Sidecar validation uses Rich console for progress reporting:

- **Interactive terminals**: Full progress bars with animations
- **CI/CD environments**: Plain text updates (no animations)
- **Test mode**: Minimal output (progress bars disabled)

Progress phases:

1. Framework detection
2. Dependency installation (isolated venv creation and package installation)
3. Route extraction
4. Contract population (with expected status codes and response structure validation)
5. Harness generation
6. CrossHair analysis (using venv Python)
7. Specmatic validation

## Output and Reports

### Console Output

Validation results are displayed in the console:

```
Validation Results:
  Framework: django
  Routes extracted: 15
  Contracts populated: 3
  Harness generated: True

CrossHair Results:
  ✓ harness
  CrossHair: 5 confirmed, 2 not confirmed, 1 violations
  Summary file: .specfact/projects/legacy-api/reports/sidecar/crosshair-summary-20240109T120000Z.json

Specmatic Results:
  ✓ FEATURE-001.openapi.yaml
```

**Note**: If Specmatic is auto-skipped, you'll see:

```
⚠ Specmatic skipped: No service configuration detected
```

Instead of the Specmatic Results section.

### Report Files

Reports are saved to `.specfact/projects/<bundle>/reports/sidecar/`:

- CrossHair output and analysis results
- Specmatic test results and HTML reports
- Timestamped execution logs

## Troubleshooting

### Framework Not Detected

**Issue**: Framework type shows as `unknown` or `pure-python`

**Solutions:**

- Ensure framework files are present (`manage.py` for Django, `main.py` for FastAPI, `app.py` for Flask)
- Check that framework imports are present in source files
- For Flask: Ensure `from flask import Flask` or `import flask` with `Flask()` instantiation
- Verify repository path is correct

### CrossHair Not Found

**Issue**: Error message "CrossHair not found in PATH"

**Solutions:**

- Install CrossHair: `pip install crosshair-tool`
- Ensure CrossHair is in PATH
- Use virtual environment with CrossHair installed

### Specmatic Not Found

**Issue**: Error message "Specmatic not found in PATH"

**Solutions:**

- Install Specmatic (CLI, JAR, npm, or Python module)
- Ensure `specmatic` is available on PATH
- Skip Specmatic if not needed: `--no-run-specmatic`

### Specmatic Auto-Skipped

**Issue**: Specmatic is automatically skipped with message "No service configuration detected"

**Explanation:**
Specmatic requires a service endpoint to test against. If no service configuration is detected, Specmatic is automatically skipped to avoid unnecessary validation attempts.

**When This Happens:**

- No `test_base_url` configured in SpecmaticConfig
- No `host` and `port` combination available
- No application server command and port configured

**Solutions:**

1. **Ensure Specmatic is installed and on PATH**
2. **Make sure your Specmatic configuration/service is available** (e.g., config file in the repo or a running service)
3. **Re-run with Specmatic enabled**:

   ```bash
   specfact validate sidecar run legacy-api /path/to/repo --run-specmatic
   ```

4. **Skip Specmatic explicitly** (if you only need CrossHair):

   ```bash
   specfact validate sidecar run legacy-api /path/to/repo --no-run-specmatic
   ```

### Module Resolution Errors

**Issue**: CrossHair fails with import errors

**Solutions:**

- **Automatic**: Sidecar validation automatically sets PYTHONPATH to include venv site-packages
- **Venv Python**: CrossHair uses venv Python (`.specfact/venv/bin/python`) when available, ensuring framework dependencies are accessible
- Set `PYTHONPATH` correctly for your project structure (if manual override needed)
- Ensure source directories are in PYTHONPATH
- Check that `__init__.py` files are present for packages

### Dependency Installation Issues

**Issue**: Dependencies not installed or venv broken

**Solutions:**

- **Automatic recreation**: The system automatically detects and recreates broken venvs
- **Check venv**: Verify `.specfact/venv/` exists and contains installed packages
- **Re-run validation**: Delete `.specfact/venv/` and re-run validation to trigger fresh installation
- **Manual installation**: If automatic installation fails, manually install dependencies:

  ```bash
  cd /path/to/repo
  python3 -m venv .specfact/venv --copies
  .specfact/venv/bin/pip install flask werkzeug crosshair-tool beartype icontract
  .specfact/venv/bin/pip install -r requirements.txt
  ```

## Examples

### Example 1: Django Application

```bash
# Initialize
specfact validate sidecar init django-blog /path/to/django-blog

# Run validation
specfact validate sidecar run django-blog /path/to/django-blog
```

### Example 2: FastAPI API

```bash
# Initialize
specfact validate sidecar init fastapi-api /path/to/fastapi-api

# Run only CrossHair (no HTTP endpoints - Specmatic auto-skipped)
specfact validate sidecar run fastapi-api /path/to/fastapi-api --no-run-specmatic

# Or let auto-skip handle it (Specmatic will be skipped automatically)
specfact validate sidecar run fastapi-api /path/to/fastapi-api
```

**Note**: In this example, Specmatic is automatically skipped because no service configuration is provided. The validation will focus on CrossHair analysis only.

### Example 3: Flask Application

```bash
# Initialize
specfact validate sidecar init flask-app /path/to/flask-project

# Run validation (dependencies automatically installed in isolated venv)
specfact validate sidecar run flask-app /path/to/flask-project --no-run-specmatic
```

**Note**: Flask applications automatically have dependencies installed in `.specfact/venv/` during initialization. All HTTP methods are captured (e.g., routes with `methods=['GET','POST']` generate separate routes for each method).

### Example 4: Pure Python Library

```bash
# Initialize
specfact validate sidecar init python-lib /path/to/python-library

# Run validation
specfact validate sidecar run python-lib /path/to/python-library
```

## Repro Integration

Sidecar validation can be integrated into the `specfact repro` command for validating unannotated code as part of the reproducibility suite.

### Using Sidecar with Repro

```bash
# Run repro with sidecar validation for unannotated code
specfact repro --sidecar --sidecar-bundle legacy-api --repo /path/to/repo
```

**What it does:**

1. Detects unannotated functions (no icontract/beartype decorators) using AST parsing
2. Generates sidecar harness for unannotated code paths
3. Runs CrossHair against the generated harness (not source code)
4. Applies safe defaults (shorter timeouts, per-path limits) to prevent excessive execution time
5. Uses deterministic inputs when available

**Safe Defaults for Repro Mode:**

When used with `specfact repro --sidecar`, sidecar validation automatically applies safe defaults:

- **CrossHair timeout**: 30 seconds (vs 60 default)
- **Per-path timeout**: 5 seconds
- **Per-condition timeout**: 2 seconds
- **Deterministic inputs**: Enabled (uses inputs.json from harness)

**Example:**

```bash
# Initialize sidecar workspace first
specfact validate sidecar init legacy-api /path/to/repo

# Then run repro with sidecar validation
specfact repro --sidecar --sidecar-bundle legacy-api --repo /path/to/repo --verbose
```

**Output:**

```
Running sidecar validation for unannotated code...
Found 12 unannotated functions
[sidecar validation runs...]
Sidecar CrossHair: 8 confirmed, 3 not confirmed, 1 violations
```

## Related Documentation

- **[Command Reference](../reference/commands.md)** - Complete command documentation
- **[Contract Testing Workflow](contract-testing-workflow.md)** - Contract testing guide
- **[Specmatic Integration](specmatic-integration.md)** - Specmatic integration details

## See Also

- **[Brownfield Engineer Guide](brownfield-engineer.md)** - Modernizing legacy code
- **[Use Cases](use-cases.md)** - Real-world scenarios
