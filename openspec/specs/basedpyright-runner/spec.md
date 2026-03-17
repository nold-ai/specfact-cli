# basedpyright-runner Specification

## Purpose
TBD - created by archiving change code-review-03-type-governance-runners. Update Purpose after archive.
## Requirements
### Requirement: basedpyright Type-Safety Finding Extraction
The system SHALL parse `basedpyright --outputjson` output and map all diagnostics to `category="type_safety"`, filtered to the provided changed files only.

#### Scenario: Type error maps to type_safety finding
- **GIVEN** basedpyright JSON output with a type error in `file_a.py`
- **WHEN** `run_basedpyright(files=[file_a.py])` is called
- **THEN** a `ReviewFinding` is returned with `category="type_safety"`, `tool="basedpyright"`, `severity="error"`
- **AND** `file` and `line` are correctly populated

#### Scenario: Only changed files are reported
- **GIVEN** basedpyright errors in multiple files but only `file_a.py` is in the provided list
- **WHEN** `run_basedpyright(files=[file_a.py])` is called
- **THEN** only findings from `file_a.py` are returned

#### Scenario: basedpyright unavailable produces tool_error
- **GIVEN** basedpyright binary is unavailable
- **WHEN** `run_basedpyright(files=[...])` is called
- **THEN** one `ReviewFinding` with `category="tool_error"` is returned

