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
- **Framework validation** (Django, FastAPI, DRF) using extracted routes and schemas

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
- **Pure Python**: No framework detected

### Step 2: Route Extraction

Framework-specific extractors extract routes and schemas:

- **Django**: Extracts URL patterns from `urls.py` and form schemas
- **FastAPI**: Extracts routes from decorators and Pydantic models
- **DRF**: Extracts serializers and converts to OpenAPI schemas

### Step 3: Contract Population

OpenAPI contracts are populated with extracted routes and schemas:

- Routes are matched to contract features
- Request/response schemas are merged
- Path parameters are extracted and documented

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

After initialization, the sidecar workspace is created at:

```
.specfact/projects/<bundle-name>/
├── contracts/          # OpenAPI contract files
├── reports/
│   └── sidecar/        # Validation reports
└── sidecar/            # Sidecar workspace (if using templates)
    ├── harness_contracts.py
    ├── inputs.json
    └── bindings.yaml
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
- Captures confirmed/not-confirmed/violations

**Configuration:**

- Timeout settings (per-path, per-condition)
- Verbose output options
- Module resolution handling

### Specmatic

**Purpose**: Contract testing against API endpoints

**Execution:**

- Validates API responses against OpenAPI contracts
- Requires running application server (if `SIDECAR_APP_CMD` configured)
- Can use Specmatic stub server for testing

**Configuration:**

- Base URL for API
- Timeout settings
- Auto-stub server options

## Progress Reporting

Sidecar validation uses Rich console for progress reporting:

- **Interactive terminals**: Full progress bars with animations
- **CI/CD environments**: Plain text updates (no animations)
- **Test mode**: Minimal output (progress bars disabled)

Progress phases:

1. Framework detection
2. Route extraction
3. Contract population
4. Harness generation
5. CrossHair analysis
6. Specmatic validation

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

Specmatic Results:
  ✓ FEATURE-001.openapi.yaml
```

### Report Files

Reports are saved to `.specfact/projects/<bundle>/reports/sidecar/`:

- CrossHair output and analysis results
- Specmatic test results and HTML reports
- Timestamped execution logs

## Backward Compatibility

Sidecar validation maintains backward compatibility with template-based sidecar workspaces:

- Existing workspaces created via `sidecar-init.sh` continue to work
- CLI commands detect existing workspaces automatically
- Template files remain in `resources/templates/sidecar/` for reference

## Troubleshooting

### Framework Not Detected

**Issue**: Framework type shows as `unknown` or `pure-python`

**Solutions:**

- Ensure framework files are present (`manage.py` for Django, `main.py` for FastAPI)
- Check that framework imports are present in source files
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
- Configure `SPECMATIC_CMD` in sidecar workspace `.env` file
- Skip Specmatic if not needed: `--no-run-specmatic`

### Module Resolution Errors

**Issue**: CrossHair fails with import errors

**Solutions:**

- Set `PYTHONPATH` correctly for your project structure
- Ensure source directories are in PYTHONPATH
- Check that `__init__.py` files are present for packages

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

# Run only CrossHair (no HTTP endpoints)
specfact validate sidecar run fastapi-api /path/to/fastapi-api --no-run-specmatic
```

### Example 3: Pure Python Library

```bash
# Initialize
specfact validate sidecar init python-lib /path/to/python-library

# Run validation
specfact validate sidecar run python-lib /path/to/python-library
```

## Related Documentation

- **[Command Reference](../reference/commands.md)** - Complete command documentation
- **[Contract Testing Workflow](contract-testing-workflow.md)** - Contract testing guide
- **[Specmatic Integration](specmatic-integration.md)** - Specmatic integration details

## See Also

- **[Brownfield Engineer Guide](brownfield-engineer.md)** - Modernizing legacy code
- **[Use Cases](use-cases.md)** - Real-world scenarios
