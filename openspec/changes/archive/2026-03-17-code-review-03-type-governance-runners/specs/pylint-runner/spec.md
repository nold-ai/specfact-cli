## ADDED Requirements

### Requirement: pylint Architecture Smell Extraction

The system SHALL invoke pylint on provided files and map message IDs to violation categories: `W0702`, `W0703` → architecture (bare-except, broad-except).

#### Scenario: Bare except maps to architecture category

- **GIVEN** pylint output with message id `W0702`
- **WHEN** `run_pylint(files=[...])` is called
- **THEN** a `ReviewFinding` is returned with `category="architecture"` and `tool="pylint"`

#### Scenario: W0703 broad-except maps to architecture

- **GIVEN** pylint output with message id `W0703`
- **WHEN** `run_pylint(files=[...])` is called
- **THEN** finding has `category="architecture"`

#### Scenario: Only changed files are filtered

- **GIVEN** a file list `[file_a.py]`
- **WHEN** `run_pylint(files=[file_a.py])` is called
- **THEN** only findings for `file_a.py` are returned

#### Scenario: pylint parse error produces tool_error

- **GIVEN** pylint returns unparseable output
- **WHEN** `run_pylint(files=[...])` is called
- **THEN** one `ReviewFinding` with `category="tool_error"` is returned
