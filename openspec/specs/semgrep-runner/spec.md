# semgrep-runner Specification

## Purpose

TBD - created by archiving change code-review-05-semgrep-clean-code-rules. Update Purpose after archive.

## Requirements

### Requirement: Project-Specific Semgrep Rule Execution and Finding Extraction

The system SHALL invoke semgrep with the project-specific clean_code ruleset and map findings to `List[ReviewFinding]`, filtered to the provided file list.

#### Scenario: Semgrep finding maps to ReviewFinding

- **GIVEN** semgrep output with a match on the `get-modify-same-method` rule
- **WHEN** `run_semgrep(files=[...])` is called
- **THEN** a `ReviewFinding` is returned with `tool="semgrep"` and `category="clean_code"`

#### Scenario: Non-provided files filtered out

- **GIVEN** semgrep finds matches in `file_a.py` and `file_b.py`, only `file_a.py` provided
- **WHEN** `run_semgrep(files=[file_a.py])` is called
- **THEN** only findings from `file_a.py` are returned

#### Scenario: Semgrep unavailable produces tool_error

- **GIVEN** semgrep binary is unavailable
- **WHEN** `run_semgrep(files=[...])` is called
- **THEN** one `ReviewFinding` with `category="tool_error"` is returned and no exception propagates

#### Scenario: Clean file produces no findings

- **GIVEN** a file that matches none of the 5 custom rules
- **WHEN** `run_semgrep(files=[file])` is called
- **THEN** an empty list is returned
