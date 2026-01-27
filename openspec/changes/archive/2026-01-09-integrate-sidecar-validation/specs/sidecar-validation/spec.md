# Sidecar Validation Specification

## Purpose

Native CLI integration for sidecar validation workflow, enabling contract-based validation of external codebases without modifying source code. Provides framework-specific route extraction, harness generation, and symbolic execution (CrossHair) analysis.

## ADDED Requirements

### Requirement: Sidecar Validation Command

The system SHALL provide a CLI command to run sidecar validation workflow.

#### Scenario: Run Sidecar Validation

- **GIVEN** a project bundle with contracts
- **WHEN** user runs `specfact validate sidecar --bundle <name>`
- **THEN** system:
  - Detects framework type (Django, FastAPI, DRF, pure-python)
  - Populates contracts with framework-specific routes/schemas
  - Generates CrossHair harness from contracts
  - Runs CrossHair analysis on source code (if decorators present)
  - Runs CrossHair analysis on harness (external contracts)
  - Runs Specmatic validation (if HTTP endpoints available)
  - Generates validation report
- **AND** displays progress using Rich console
- **AND** saves results to `.specfact/projects/<bundle>/reports/sidecar/`

#### Scenario: Initialize Sidecar Workspace

- **GIVEN** a project bundle
- **WHEN** user runs `specfact validate sidecar init --bundle <name>`
- **THEN** system:
  - Creates sidecar workspace directory structure
  - Generates `.env` configuration file
  - Detects Python environment (venv, poetry, uv, pip)
  - Detects framework type
  - Sets up framework-specific configuration
- **AND** workspace is ready for validation

#### Scenario: Framework Auto-Detection

- **GIVEN** a repository path
- **WHEN** sidecar validation runs
- **THEN** system detects framework type via:
  - Django: presence of `manage.py` or `urls.py` files
  - FastAPI: presence of `FastAPI()` or `@app.get()` patterns
  - DRF: presence of `rest_framework` imports
  - Pure Python: no framework detected
- **AND** uses appropriate framework extractor
- **AND** configures environment variables (e.g., `DJANGO_SETTINGS_MODULE`)

### Requirement: Framework-Specific Route Extraction

The system SHALL extract routes and schemas from framework-specific patterns.

#### Scenario: Extract Django Routes

- **GIVEN** a Django application with `urls.py`
- **WHEN** Django extractor runs
- **THEN** system:
  - Parses `urlpatterns` list
  - Extracts `path()` and `re_path()` patterns
  - Resolves view references (function-based and class-based)
  - Determines HTTP methods from view classes
  - Extracts form schemas from Django forms
- **AND** returns list of `RouteInfo` objects with:
  - Path pattern (e.g., `/login/`)
  - HTTP method (e.g., `POST`)
  - View function/class reference
  - Request schema (from forms)
  - Response schema (if available)

#### Scenario: Extract FastAPI Routes

- **GIVEN** a FastAPI application with route decorators
- **WHEN** FastAPI extractor runs
- **THEN** system:
  - Finds `@app.get()`, `@app.post()`, etc. decorators
  - Extracts path patterns and parameters
  - Extracts Pydantic models from route signatures
  - Converts Pydantic models to OpenAPI schemas
  - Handles dependency injection patterns
- **AND** returns list of `RouteInfo` objects with enriched schemas

#### Scenario: Extract DRF Serializers

- **GIVEN** a DRF application with serializers
- **WHEN** DRF extractor runs
- **THEN** system:
  - Finds `serializers.Serializer` and `serializers.ModelSerializer` classes
  - Extracts field definitions
  - Converts DRF fields to OpenAPI schema types
  - Handles nested serializers
- **AND** returns schema definitions compatible with OpenAPI

### Requirement: Contract Population

The system SHALL populate OpenAPI contracts with framework-extracted routes and schemas.

#### Scenario: Populate Django Contracts

- **GIVEN** OpenAPI contract stubs and Django routes
- **WHEN** contract populator runs
- **THEN** system:
  - Matches routes to contract features (by feature key or path pattern)
  - Populates `paths` section with route operations
  - Merges extracted schemas with existing contract schemas
  - Preserves AI-enriched schemas when merging
  - Updates `operationId` to match view function names
- **AND** contracts are ready for harness generation

#### Scenario: Populate FastAPI Contracts

- **GIVEN** OpenAPI contract stubs and FastAPI routes
- **WHEN** contract populator runs
- **THEN** system:
  - Matches routes to contract features
  - Populates `paths` section with route operations
  - Extracts Pydantic model schemas automatically
  - Merges Pydantic schemas with existing contract schemas
  - Handles `Optional`, `EmailStr`, `UUID` special types
- **AND** contracts have enriched request/response schemas

### Requirement: Harness Generation

The system SHALL generate CrossHair harness files from populated contracts.

#### Scenario: Generate Harness from Contracts

- **GIVEN** populated OpenAPI contracts
- **WHEN** harness generator runs
- **THEN** system:
  - Reads all contracts from contracts directory
  - Generates Python harness file with `@icontract` decorators
  - Creates harness functions for each contract operation
  - Adds `@require` preconditions from request schemas
  - Adds `@ensure` postconditions from response schemas
  - Generates test inputs JSON file
  - Creates bindings YAML file for framework adapters
- **AND** harness file is importable and executable
- **AND** harness functions use framework adapters (e.g., `call_django_view`)

#### Scenario: Handle Schema Types

- **GIVEN** OpenAPI schemas with various types
- **WHEN** harness generator processes schemas
- **THEN** system:
  - Converts OpenAPI types to Python types
  - Handles `nullable` fields
  - Handles `enum` constraints
  - Handles `minLength`/`maxLength` constraints
  - Handles nested objects and arrays
  - Handles `application/x-www-form-urlencoded` (Django forms)
  - Handles `application/json` (FastAPI/DRF)
- **AND** generates valid Python type hints

### Requirement: CrossHair Execution

The system SHALL execute CrossHair symbolic execution on source code and harness.

#### Scenario: Run CrossHair on Source Code

- **GIVEN** source code directory with runtime contracts (icontract/beartype)
- **WHEN** CrossHair runner executes
- **THEN** system:
  - Converts source paths to Python module names
  - Sets up PYTHONPATH correctly
  - Runs `crosshair check` on source modules
  - Filters out test directories
  - Handles framework-specific initialization (e.g., Django setup)
  - Captures output and errors
  - Generates report with confirmed/not-confirmed/violations
- **AND** displays progress during execution
- **AND** saves results to sidecar reports directory

#### Scenario: Run CrossHair on Harness

- **GIVEN** generated harness file
- **WHEN** CrossHair runner executes
- **THEN** system:
  - Sets up PYTHONPATH to include sidecar directory (for `common` imports)
  - Changes to harness directory for valid module name
  - Runs `crosshair check` on harness module
  - Configures timeouts (per-path, per-condition)
  - Captures output and errors
  - Generates report with confirmed/not-confirmed/violations
- **AND** displays progress during execution
- **AND** saves results to sidecar reports directory

#### Scenario: Handle Module Resolution

- **GIVEN** source directory with non-standard structure (e.g., `lib/sqlalchemy`)
- **WHEN** CrossHair runner executes
- **THEN** system:
  - Converts path `lib/sqlalchemy` to module name `sqlalchemy`
  - Adds parent directory `lib/` to PYTHONPATH
  - Ensures module can be imported correctly
  - Handles packages with `__init__.py`
  - Handles subdirectories with packages
- **AND** CrossHair can import and analyze the module

### Requirement: Specmatic Integration

The system SHALL execute Specmatic contract testing when HTTP endpoints are available.

#### Scenario: Run Specmatic Validation

- **GIVEN** OpenAPI contracts and running application
- **WHEN** Specmatic runner executes
- **THEN** system:
  - Detects Specmatic installation (CLI, JAR, npm, Python module)
  - Starts application server (if `SIDECAR_APP_CMD` configured)
  - Starts Specmatic stub server (if auto-stub enabled)
  - Runs `specmatic test` with contracts
  - Validates API responses against contracts
  - Captures test results
  - Generates HTML report
- **AND** displays progress during execution
- **AND** saves results to sidecar reports directory

#### Scenario: Skip Specmatic for Libraries

- **GIVEN** pure Python library (no HTTP endpoints)
- **WHEN** sidecar validation runs
- **THEN** system:
  - Detects no HTTP endpoints available
  - Skips Specmatic validation
  - Logs skip reason
- **AND** continues with CrossHair analysis only

#### Scenario: Auto-Skip Specmatic When No Service Available

- **GIVEN** sidecar configuration without service/client configuration
- **WHEN** sidecar validation runs
- **THEN** system:
  - Detects missing service configuration (no test_base_url, host, port, or app cmd)
  - Automatically sets `run_specmatic = False`
  - Displays clear message: "Skipping Specmatic: No service configuration detected"
  - Continues with CrossHair analysis only
- **AND** manual override still works via `--run-specmatic` flag

#### Scenario: Manual Override for Specmatic

- **GIVEN** sidecar configuration with auto-skip enabled (no service detected)
- **WHEN** user runs `specfact validate sidecar run --run-specmatic`
- **THEN** system:
  - Overrides auto-skip detection
  - Runs Specmatic validation despite missing service configuration
  - Displays warning about missing service configuration
- **AND** Specmatic execution proceeds (may fail if service not available)

### Requirement: Configuration Management

The system SHALL manage sidecar configuration using Pydantic models.

#### Scenario: Load Sidecar Configuration

- **GIVEN** sidecar workspace with `.env` file
- **WHEN** configuration is loaded
- **THEN** system:
  - Reads `.env` file
  - Validates configuration using `SidecarConfig` model
  - Detects missing required fields
  - Provides default values for optional fields
  - Validates paths exist
  - Validates framework type is supported
- **AND** returns validated `SidecarConfig` instance

#### Scenario: Generate Default Configuration

- **GIVEN** project bundle and repository path
- **WHEN** sidecar workspace is initialized
- **THEN** system:
  - Detects Python environment (venv, poetry, uv, pip)
  - Detects framework type
  - Generates default configuration:
    - `RUN_CROSSHAIR=1`
    - `RUN_SPECMATIC=0` (for libraries) or `1` (for apps)
    - `RUN_SEMGREP=0`
    - `RUN_BASEDPYRIGHT=0`
    - Timeout values (60s default)
  - Writes `.env` file
- **AND** configuration is ready for validation

### Requirement: Progress Reporting

The system SHALL display progress using Rich console with terminal capability detection.

#### Scenario: Display Progress for Long Operations

- **GIVEN** sidecar validation workflow
- **WHEN** long-running operations execute (CrossHair, Specmatic)
- **THEN** system:
  - Uses Rich Progress bars (if terminal supports animations)
  - Uses plain text updates (if terminal is basic/CI)
  - Shows current phase (framework detection, contract population, etc.)
  - Shows elapsed time
  - Shows operation status (running, completed, failed)
- **AND** progress is visible in both interactive and CI/CD environments

#### Scenario: Display Validation Results

- **GIVEN** sidecar validation completes
- **WHEN** results are displayed
- **THEN** system:
  - Shows summary table with:
    - CrossHair confirmed count
    - CrossHair not-confirmed count
    - CrossHair violations count
    - Specmatic test results (if applicable)
  - Shows file locations for reports
  - Uses color coding (green for success, red for violations)
  - Respects terminal color capabilities
- **AND** results are clear and actionable

### Requirement: CrossHair Summary Reporting

The system SHALL parse CrossHair output and generate summary statistics.

#### Scenario: Parse CrossHair Output for Summary

- **GIVEN** CrossHair execution completes
- **WHEN** summary parser processes output
- **THEN** system:
  - Extracts confirmed over all paths count
  - Extracts not confirmed count
  - Extracts counterexamples/violations count
  - Handles different CrossHair output formats (verbose/non-verbose)
  - Handles edge cases (empty output, malformed output, timeout)
- **AND** summary counts are accurate

#### Scenario: Generate Summary File

- **GIVEN** CrossHair execution completes with parsed summary
- **WHEN** summary file is generated
- **THEN** system:
  - Creates `crosshair-summary.json` in sidecar reports directory
  - Includes confirmed, not confirmed, and violations counts
  - Includes execution metadata (timestamp, timeout, etc.)
  - Uses structured JSON format for machine-readable output
- **AND** summary file is saved to `.specfact/projects/<bundle>/reports/sidecar/crosshair-summary.json`

#### Scenario: Display Summary in Console

- **GIVEN** CrossHair execution completes with parsed summary
- **WHEN** results are displayed
- **THEN** system:
  - Displays summary line: "CrossHair: X confirmed, Y not confirmed, Z violations"
  - Shows summary after CrossHair execution completes
  - Uses color coding (green for confirmed, yellow for not confirmed, red for violations)
  - Respects terminal color capabilities
- **AND** summary is clear and actionable

### Requirement: Backward Compatibility

The system SHALL maintain compatibility with template-based sidecar workspaces.

#### Scenario: Detect Existing Sidecar Workspace

- **GIVEN** existing sidecar workspace (created via `sidecar-init.sh`)
- **WHEN** `specfact validate sidecar` runs
- **THEN** system:
  - Detects existing workspace structure
  - Loads configuration from `.env` file
  - Uses existing harness and bindings
  - Executes validation using existing workspace
- **AND** template-based workspaces continue to work

#### Scenario: Create New Workspace

- **GIVEN** project bundle without sidecar workspace
- **WHEN** `specfact validate sidecar init` runs
- **THEN** system:
  - Creates workspace using CLI-native approach
  - Generates configuration programmatically
  - Does not require template files
  - Creates same directory structure as templates
- **AND** workspace is compatible with template-based tools

### Requirement: Repro Integration

The system SHALL integrate sidecar validation into `specfact repro` workflow for unannotated code validation.

#### Scenario: Run Repro with Sidecar Option

- **GIVEN** a project bundle
- **WHEN** user runs `specfact repro --sidecar --bundle <name> --repo <path>`
- **THEN** system:
  - Detects unannotated code (no icontract/beartype decorators)
  - Generates sidecar harness for unannotated code paths
  - Loads bindings.yaml to map OpenAPI operations to real callables
  - Runs CrossHair against generated harness (not source code)
  - Writes outputs to `.specfact/projects/<bundle>/reports/sidecar/`
- **AND** validation runs without modifying source code

#### Scenario: Detect Unannotated Code

- **GIVEN** source code directory
- **WHEN** repro sidecar mode runs
- **THEN** system:
  - Scans source files for runtime contracts (icontract, beartype decorators)
  - Identifies functions/classes without contracts
  - Generates sidecar harness for unannotated code paths
  - Maps unannotated functions to OpenAPI operations via bindings
- **AND** harness provides external contracts for unannotated code

#### Scenario: Use Deterministic Inputs and Safe Defaults

- **GIVEN** sidecar harness with inputs.json
- **WHEN** repro sidecar mode runs CrossHair
- **THEN** system:
  - Uses deterministic inputs from inputs.json file
  - Applies safe defaults for timeouts (per-path, per-condition limits)
  - Prevents excessive execution time
  - Configures CrossHair with appropriate limits
- **AND** validation completes in reasonable time

#### Scenario: Integrate Sidecar Results into Repro Report

- **GIVEN** repro sidecar validation completes
- **WHEN** repro report is generated
- **THEN** system:
  - Includes sidecar validation results in repro report
  - Shows CrossHair summary counts from sidecar harness
  - Indicates which code paths were validated via sidecar
  - Distinguishes sidecar-validated paths from contract-validated paths
- **AND** repro report provides complete validation coverage
