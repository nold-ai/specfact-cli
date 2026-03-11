## ADDED Requirements

### Requirement: Ruff Finding Extraction Mapped to ReviewFinding
The system SHALL invoke `ruff check --output-format json` on provided files and map rule prefixes to categories: `S*` → security, `C9*` → clean_code, `E/F/I*` → style.

#### Scenario: Bandit S-rules map to security category
- **GIVEN** ruff output contains a finding with rule `S603`
- **WHEN** `run_ruff(files=[...])` is called
- **THEN** the returned `ReviewFinding` has `category="security"` and `tool="ruff"`

#### Scenario: C90 complexity rules map to clean_code
- **GIVEN** ruff output contains a finding with rule `C901`
- **WHEN** `run_ruff(files=[...])` is called
- **THEN** the finding has `category="clean_code"`

#### Scenario: Only provided files are scanned
- **GIVEN** a file list `[file_a.py]`
- **WHEN** `run_ruff(files=[file_a.py])` is called
- **THEN** ruff is invoked with only `file_a.py` and no other files appear in findings

#### Scenario: Ruff parse error or unavailability produces tool_error finding
- **GIVEN** ruff returns unparseable output or is not installed
- **WHEN** `run_ruff(files=[...])` is called
- **THEN** one `ReviewFinding` with `category="tool_error"` is returned and no exception propagates
