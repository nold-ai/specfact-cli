# doc-frontmatter-schema Specification

## Purpose

This specification defines the authoritative YAML frontmatter schema for repository documentation so
enforced docs carry stable ownership, tracking, and exemption metadata that validators and
contributors must interpret consistently.

## Requirements

### Requirement: YAML Frontmatter Format

The system SHALL support YAML frontmatter in Markdown documentation files with the following schema:

```yaml
---
title: "<Document Title>"
doc_owner: <owner_identifier>  # owning module or known token
tracks:
  - <glob_pattern>  # files/directories this doc tracks
last_reviewed: YYYY-MM-DD
exempt: false  # true for stable/legal docs
exempt_reason: ""  # required if exempt: true
---
```

#### Scenario: Valid frontmatter structure

- **WHEN** a Markdown file contains properly formatted YAML frontmatter
- **THEN** the frontmatter SHALL be parsed successfully
- **AND** all required fields SHALL be present

#### Scenario: Missing required fields

- **WHEN** a Markdown file has frontmatter missing required fields
- **THEN** the validation SHALL fail with clear error message
- **AND** the error SHALL specify which fields are missing

### Requirement: Owner Identifier Resolution

The system SHALL support two types of owner identifiers:

1. Path-like identifiers (for example `src/specfact/parser`)
2. Known tokens (for example `specfact-cli`, `nold-ai`, `openspec`)

#### Scenario: Path-like owner resolution

- **WHEN** `doc_owner` is a path-like identifier
- **THEN** the system SHALL verify the path exists in the repository
- **AND** validation SHALL pass if path exists

#### Scenario: Known token resolution

- **WHEN** `doc_owner` is a known token
- **THEN** the system SHALL verify the token is in `VALID_OWNER_TOKENS`
- **AND** validation SHALL pass if the token is valid

#### Scenario: Invalid owner identifier

- **WHEN** `doc_owner` cannot be resolved
- **THEN** validation SHALL fail with a resolution error
- **AND** the error SHALL suggest valid alternatives

### Requirement: Glob Pattern Tracking

The system SHALL support glob patterns in `tracks` to specify which files or directories the
documentation should stay synchronized with.

#### Scenario: Single glob pattern

- **WHEN** `tracks` contains a single valid glob pattern
- **THEN** the pattern SHALL validate successfully

#### Scenario: Multiple glob patterns

- **WHEN** `tracks` contains multiple glob patterns
- **THEN** all patterns SHALL be validated
- **AND** validation SHALL pass if all patterns are valid

#### Scenario: Invalid glob pattern

- **WHEN** `tracks` contains an invalid glob pattern
- **THEN** validation SHALL fail with a pattern error

### Requirement: Exemption Handling

The system SHALL support document exemptions for stable or legal documentation that does not need
synchronization checks.

#### Scenario: Valid exemption

- **WHEN** `exempt: true` is paired with a non-empty `exempt_reason`
- **THEN** validation SHALL pass
- **AND** the document SHALL be excluded from sync checks

#### Scenario: Exemption without reason

- **WHEN** `exempt: true` is set but `exempt_reason` is empty
- **THEN** validation SHALL fail
- **AND** the error SHALL require an exemption reason

### Requirement: Frontmatter Extraction

The system SHALL provide a function to extract frontmatter from Markdown files.

#### Scenario: Extract from file with frontmatter

- **WHEN** `parse_frontmatter(path)` is called on a file with valid frontmatter
- **THEN** the function SHALL return the parsed frontmatter dictionary
- **AND** the original file content SHALL remain unchanged

#### Scenario: Extract from file without frontmatter

- **WHEN** `parse_frontmatter(path)` is called on a file without frontmatter
- **THEN** the function SHALL return an empty dictionary
- **AND** no error SHALL be raised

## Contract Requirements

### Requirement: Input Validation Contracts

All public functions SHALL use `@icontract` decorators for input validation:

- `@require` for preconditions
- `@ensure` for postconditions

#### Scenario: Invalid input type

- **WHEN** a function receives an invalid input type
- **THEN** the `@require` contract SHALL raise an appropriate exception

### Requirement: Type Safety Contracts

All public functions SHALL use `@beartype` decorators for runtime type checking.

#### Scenario: Type mismatch

- **WHEN** a function receives an argument of the wrong type
- **THEN** `@beartype` SHALL raise a clear `TypeError`
