## MODIFIED Requirements

### Requirement: Resolve pip dependencies across all modules

The system SHALL aggregate pip_dependencies from all installed modules and resolve constraints using pip-compile or fallback resolver. The resolved package set SHALL NOT include packages with GPL-2.0, GPL-3.0, or AGPL-3.0 licenses unless they are documented in the project's license-exception allowlist.

#### Scenario: Dependencies resolved without conflicts

- **WHEN** module installation triggers dependency resolution
- **THEN** system SHALL collect pip_dependencies from all modules
- **AND** SHALL resolve constraints using pip-compile
- **AND** SHALL return list of resolved package versions

#### Scenario: Dependency conflict detected

- **WHEN** new module introduces conflicting pip dependency
- **THEN** system SHALL detect conflict before installation
- **AND** SHALL display error with conflicting packages and versions
- **AND** SHALL suggest resolution options
- **AND** SHALL NOT proceed with installation

#### Scenario: Fallback to basic pip resolver

- **WHEN** pip-tools is not available
- **THEN** system SHALL log warning "pip-tools not found, using basic resolver"
- **AND** SHALL attempt resolution with pip's built-in resolver
- **AND** SHALL proceed if no obvious conflicts

## ADDED Requirements

### Requirement: Wrong-package removal from enhanced-analysis and dev extras

The system SHALL NOT include `syft` (OpenMined ML framework) or `bearer` (SaaS HTTP auth client) in any distributed extra. These packages provide no functional benefit and were included in error.

#### Scenario: enhanced-analysis extra does not install syft or bearer

- **WHEN** `pip install specfact-cli[enhanced-analysis]` is run
- **THEN** the `syft` PyPI package SHALL NOT be installed
- **AND** the `bearer` PyPI package SHALL NOT be installed

#### Scenario: dev extra does not install bearer

- **WHEN** `pip install specfact-cli[dev]` is run
- **THEN** the `bearer` PyPI package SHALL NOT be installed

### Requirement: JSONC read/write via commentjson and stdlib json

The system SHALL read VS Code `settings.json` (JSONC format with `//` comments and trailing commas) using `commentjson.loads()` and SHALL write JSON output using stdlib `json.dumps(indent=4)`. The `json5` package SHALL NOT be used.

#### Scenario: JSONC file with comments is read correctly

- **WHEN** `project_artifact_write` reads a VS Code `settings.json` that contains `//` comments
- **THEN** `commentjson.loads(raw_text)` SHALL strip the comments and parse the JSON successfully
- **AND** the resulting Python dict SHALL match the data in the file (excluding comments)

#### Scenario: JSONC file with trailing commas is read correctly

- **WHEN** `project_artifact_write` reads a `settings.json` containing trailing commas in arrays or objects
- **THEN** `commentjson.loads(raw_text)` SHALL parse it without raising a `JSONDecodeError`

#### Scenario: JSON output is written without trailing commas or unquoted keys

- **WHEN** `project_artifact_write` writes a payload to a JSON file
- **THEN** `json.dumps(payload, indent=4)` SHALL produce valid standard JSON
- **AND** all keys SHALL be quoted
- **AND** there SHALL be no trailing commas
- **AND** the output SHALL be byte-for-byte equivalent to the previous `json5.dumps(..., quote_keys=True, trailing_commas=False)` output for well-formed inputs

### Requirement: bandit available for Python-native security analysis

The system SHALL include `bandit` in the `dev` extra as the Python-native static security analysis tool. A `bandit-scan` hatch script SHALL allow developers to run bandit against `src/`.

#### Scenario: bandit installed in dev environment

- **WHEN** `pip install specfact-cli[dev]` is run
- **THEN** `bandit` SHALL be available on `$PATH`

#### Scenario: bandit scan runs against src/

- **WHEN** `hatch run bandit-scan` is executed
- **THEN** `bandit -r src/ -ll` SHALL run and report findings at medium severity or above
- **AND** the command SHALL exit non-zero if high-severity issues are found
