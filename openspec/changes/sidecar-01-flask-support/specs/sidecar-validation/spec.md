# Sidecar Validation - Flask Framework Support

## ADDED Requirements

### Requirement: Flask Framework Detection

The sidecar validation system SHALL detect Flask applications and return the appropriate framework type.

**Rationale**: Flask applications are currently detected but incorrectly classified as `PURE_PYTHON`, preventing route extraction and contract population.

#### Scenario: Detect Flask Application

**Given**: A repository contains Flask application code with `from flask import Flask` or `Flask()` instantiation

**When**: The framework detector analyzes the repository

**Then**: The detector returns `FrameworkType.FLASK` (not `PURE_PYTHON`)

**Acceptance Criteria**:

- Flask detection logic identifies Flask imports correctly
- Framework detector returns `FrameworkType.FLASK` for Flask applications
- Framework detector returns `PURE_PYTHON` only when no framework is detected

---

### Requirement: Flask Route Extraction

The sidecar validation system SHALL extract routes from Flask applications using AST parsing.

**Rationale**: Flask applications use decorator-based routing (`@app.route()`, `@bp.route()`) that requires AST parsing to extract route information.

#### Scenario: Extract Routes from Flask App Decorators

**Given**: A Flask application file contains `@app.route('/path', methods=['GET', 'POST'])` decorators

**When**: The Flask extractor processes the file

**Then**: The extractor returns `RouteInfo` objects with:

- Path: `/path`
- Method: `GET` or `POST` (from decorator)
- Operation ID: Function name
- Path parameters: Extracted from Flask path syntax

**Acceptance Criteria**:

- Routes extracted from `@app.route()` decorators
- Routes extracted from `@bp.route()` decorators (Blueprints)
- HTTP methods extracted from `methods` parameter
- Path parameters converted from Flask syntax (`<int:id>`) to OpenAPI format (`{id}`)

#### Scenario: Extract Blueprint Routes

**Given**: A Flask application uses Blueprints with `@bp.route('/api/users')` decorators

**When**: The Flask extractor processes Blueprint files

**Then**: The extractor extracts routes from Blueprint decorators and includes Blueprint prefix in paths

**Acceptance Criteria**:

- Blueprint routes are detected and extracted
- Blueprint prefix is included in route paths
- Blueprint registration is tracked for route resolution

#### Scenario: Convert Flask Path Parameters to OpenAPI Format

**Given**: A Flask route contains path parameters like `/user/<int:id>` or `/post/<slug>`

**When**: The Flask extractor processes the route

**Then**: The extractor converts Flask path parameters to OpenAPI format:

- `<int:id>` → `{id}` with `type: integer`
- `<float:value>` → `{value}` with `type: number`
- `<path:path>` → `{path}` with `type: string`
- `<slug>` → `{slug}` with `type: string` (default)

**Acceptance Criteria**:

- All Flask path parameter types are converted correctly
- OpenAPI path parameter format is used in RouteInfo
- Type information is preserved in schema

---

### Requirement: FlaskExtractor Implementation

A new `FlaskExtractor` class SHALL be implemented following the same pattern as `FastAPIExtractor` and `DjangoExtractor`.

**Rationale**: Framework-specific extractors provide consistent interface for route and schema extraction across different frameworks.

#### Scenario: FlaskExtractor Implements BaseFrameworkExtractor Interface

**Given**: The `FlaskExtractor` class is created

**When**: The extractor is instantiated and used

**Then**: The extractor implements all required methods:

- `detect()`: Returns `True` for Flask applications
- `extract_routes()`: Returns list of `RouteInfo` objects
- `extract_schemas()`: Returns dictionary of schemas (can be empty initially)

**Acceptance Criteria**:

- `FlaskExtractor` extends `BaseFrameworkExtractor`
- All abstract methods are implemented
- Methods have proper type hints and contracts (`@beartype`, `@icontract`)
- Code follows same patterns as `FastAPIExtractor`

---

### Requirement: Flask Extractor Integration

The Flask extractor SHALL be integrated into the sidecar validation orchestrator.

**Rationale**: The orchestrator needs to return the Flask extractor when Flask framework is detected.

#### Scenario: Orchestrator Returns FlaskExtractor for Flask Framework

**Given**: Framework detector returns `FrameworkType.FLASK`

**When**: The orchestrator calls `get_extractor()`

**Then**: The orchestrator returns a `FlaskExtractor` instance

**Acceptance Criteria**:

- `get_extractor()` includes `FlaskExtractor` in return type
- `get_extractor()` returns `FlaskExtractor()` for `FrameworkType.FLASK`
- `FlaskExtractor` is exported from `frameworks/__init__.py`

---

### Requirement: Flask Extractor Unit Tests

Comprehensive unit tests SHALL be created for Flask extractor functionality.

**Rationale**: Unit tests ensure Flask route extraction works correctly and maintains quality standards.

#### Scenario: Unit Tests Cover Flask Route Extraction

**Given**: Unit test file `test_flask.py` is created

**When**: Tests are executed

**Then**: Tests cover:

- Framework detection (positive and negative cases)
- Route extraction from `@app.route()` decorators
- Route extraction from `@bp.route()` decorators
- Path parameter conversion (all types)
- HTTP method extraction
- Schema extraction (returns empty dict)

**Acceptance Criteria**:

- Test coverage ≥80% for Flask extractor code
- All test cases pass
- Tests follow existing test patterns

---

### Requirement: Flask Application Validation

The sidecar validation SHALL work end-to-end with Flask applications.

**Rationale**: Flask support is only complete when real Flask applications can be validated.

#### Scenario: Validate Microblog Flask Application

**Given**: Microblog Flask application is available

**When**: Sidecar validation is run on Microblog

**Then**: Validation completes successfully:

- Framework detected as `FLASK` (not `PURE_PYTHON`)
- Routes extracted (> 0 routes)
- Contracts populated with routes
- Harness generated from contracts

**Acceptance Criteria**:

- Microblog validation Phase B can proceed
- Routes are extracted correctly
- Contracts are populated
- Harness is generated
