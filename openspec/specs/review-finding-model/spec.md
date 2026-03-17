# review-finding-model Specification

## Purpose
TBD - created by archiving change code-review-01-module-scaffold. Update Purpose after archive.
## Requirements
### Requirement: ReviewFinding Pydantic Model
The system SHALL provide a `ReviewFinding` Pydantic BaseModel with validated `category`, `severity`, `tool`, `rule`, `file`, `line`, `message`, and `fixable` fields.

#### Scenario: Valid ReviewFinding creates successfully
- **GIVEN** a dict with all required fields: category, severity, tool, rule, file, line, message
- **WHEN** `ReviewFinding(**data)` is called
- **THEN** a valid instance is returned with all fields populated
- **AND** `fixable` defaults to `False` if not provided

#### Scenario: Invalid severity is rejected
- **GIVEN** a dict with `severity="critical"` (not in the valid set)
- **WHEN** `ReviewFinding(**data)` is called
- **THEN** a `ValidationError` is raised

#### Scenario: Valid severity and category values accepted
- **GIVEN** severity values `error`, `warning`, `info` and category values `clean_code`, `security`, `type_safety`, `contracts`, `testing`, `style`, `architecture`, `tool_error`
- **WHEN** each is used in a `ReviewFinding`
- **THEN** all are accepted without validation error

