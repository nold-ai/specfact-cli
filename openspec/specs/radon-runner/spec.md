# radon-runner Specification

## Purpose

TBD - created by archiving change code-review-02-ruff-radon-runners. Update Purpose after archive.

## Requirements

### Requirement: Radon Cyclomatic Complexity Extraction

The system SHALL invoke `radon cc -j` on provided files and produce severity-tiered findings for functions exceeding complexity thresholds (12-15 → warning, >15 → error).

#### Scenario: Function with complexity 13 produces warning

- **GIVEN** radon output shows a function with cyclomatic complexity 13
- **WHEN** `run_radon(files=[...])` is called
- **THEN** a `ReviewFinding` is returned with `severity="warning"` and `category="clean_code"`

#### Scenario: Function with complexity 16 produces error

- **GIVEN** radon output shows a function with cyclomatic complexity 16
- **WHEN** `run_radon(files=[...])` is called
- **THEN** a `ReviewFinding` is returned with `severity="error"` and `category="clean_code"`

#### Scenario: Function with complexity 12 or below produces no finding

- **GIVEN** all functions have complexity <= 12
- **WHEN** `run_radon(files=[...])` is called
- **THEN** no findings are returned

#### Scenario: Radon parse error produces tool_error finding

- **GIVEN** radon returns unparseable output
- **WHEN** `run_radon(files=[...])` is called
- **THEN** one `ReviewFinding` with `category="tool_error"` is returned
