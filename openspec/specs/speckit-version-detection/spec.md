# speckit-version-detection Specification

## Purpose

TBD - created by archiving change speckit-02-v04-adapter-alignment. Update Purpose after archive.

## Requirements

### Requirement: CLI-based version detection

The system SHALL attempt to detect the installed spec-kit version by invoking the `specify` CLI when available on PATH.

#### Scenario: CLI available and returns version

- **GIVEN** the `specify` CLI is installed and available on the system PATH
- **WHEN** `SpecKitAdapter._detect_version_from_cli(repo_path)` is called
- **THEN** the method runs `specify --version` as a subprocess
- **AND** parses the version string from stdout
- **AND** returns the version string (e.g., `"0.4.3"`)
- **AND** sets `ToolCapabilities.detected_version_source` to `"cli"`

#### Scenario: CLI not available

- **GIVEN** the `specify` CLI is not installed or not on PATH
- **WHEN** `SpecKitAdapter._detect_version_from_cli(repo_path)` is called
- **THEN** the method returns `None`
- **AND** does not raise an exception
- **AND** the detection falls through to heuristic detection

#### Scenario: CLI invocation times out

- **GIVEN** the `specify` CLI is on PATH but hangs or takes longer than 5 seconds
- **WHEN** `SpecKitAdapter._detect_version_from_cli(repo_path)` is called
- **THEN** the subprocess is terminated after the timeout
- **AND** the method returns `None`
- **AND** logs a debug-level warning

### Requirement: Heuristic version detection

The system SHALL estimate the spec-kit version from directory structure when CLI detection is unavailable.

#### Scenario: Presets directory implies version >= 0.3.0

- **GIVEN** a repository with `.specify/` and a `presets/` directory
- **AND** CLI-based version detection returned `None`
- **WHEN** `SpecKitAdapter._detect_version_from_heuristics(repo_path)` is called
- **THEN** the method returns `">=0.3.0"`
- **AND** sets `ToolCapabilities.detected_version_source` to `"heuristic"`

#### Scenario: Extensions directory implies version >= 0.2.0

- **GIVEN** a repository with `.specify/` and `extensions/` directory but no `presets/` directory
- **AND** CLI-based version detection returned `None`
- **WHEN** `SpecKitAdapter._detect_version_from_heuristics(repo_path)` is called
- **THEN** the method returns `">=0.2.0"`
- **AND** sets `ToolCapabilities.detected_version_source` to `"heuristic"`

#### Scenario: Only specify directory implies version >= 0.1.0

- **GIVEN** a repository with `.specify/` directory but no `extensions/` or `presets/`
- **AND** CLI-based version detection returned `None`
- **WHEN** `SpecKitAdapter._detect_version_from_heuristics(repo_path)` is called
- **THEN** the method returns `">=0.1.0"`
- **AND** sets `ToolCapabilities.detected_version_source` to `"heuristic"`

#### Scenario: No version detectable

- **GIVEN** a repository with only `specs/` at root (classic layout, no `.specify/`)
- **AND** CLI-based version detection returned `None`
- **WHEN** `SpecKitAdapter._detect_version_from_heuristics(repo_path)` is called
- **THEN** the method returns `None`
- **AND** `ToolCapabilities.detected_version_source` remains `None`

### Requirement: Version detection integration in get_capabilities

The system SHALL integrate version detection into the existing `SpecKitAdapter.get_capabilities()` flow, trying CLI first then heuristics.

#### Scenario: Full version detection flow

- **GIVEN** a spec-kit repository
- **WHEN** `SpecKitAdapter.get_capabilities(repo_path)` is called
- **THEN** the adapter tries CLI detection first
- **AND** if CLI returns `None`, falls back to heuristic detection
- **AND** populates `ToolCapabilities.version` with the result
- **AND** populates `ToolCapabilities.detected_version_source` with the detection method used
