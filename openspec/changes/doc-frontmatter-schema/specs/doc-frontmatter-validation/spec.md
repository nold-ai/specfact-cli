# Doc Frontmatter Validation Specification

## ADDED Requirements

### Requirement: Validation Script Implementation
The system SHALL provide a validation script `scripts/check_doc_frontmatter.py` that enforces frontmatter requirements.

#### Scenario: Script execution with valid docs

- **WHEN** `check_doc_frontmatter.py` is executed
- **AND** all tracked docs have valid frontmatter
- **THEN** script SHALL exit with code 0
- **AND** output SHALL show success message

#### Scenario: Script execution with invalid docs

- **WHEN** `check_doc_frontmatter.py` is executed
- **AND** some docs have invalid frontmatter
- **THEN** script SHALL exit with code 1
- **AND** output SHALL list all validation failures

### Requirement: Missing Doc Owner Detection
The system SHALL detect documentation files that are missing the `doc_owner` field.

#### Scenario: Missing doc_owner in tracked file

- **WHEN** a tracked Markdown file lacks `doc_owner` field
- **THEN** validation SHALL fail
- **AND** error SHALL specify missing field

#### Scenario: Valid doc_owner present

- **WHEN** a tracked Markdown file has valid `doc_owner`
- **THEN** validation SHALL pass for owner requirement

### Requirement: Owner Resolution Validation
The system SHALL validate that `doc_owner` values resolve to existing paths or known tokens.

#### Scenario: Owner resolves to existing path

- **WHEN** `doc_owner` is a path that exists in repository
- **THEN** validation SHALL pass for owner resolution

#### Scenario: Owner is valid known token

- **WHEN** `doc_owner` is in `VALID_OWNER_TOKENS`
- **THEN** validation SHALL pass for owner resolution

#### Scenario: Owner cannot be resolved

- **WHEN** `doc_owner` doesn't resolve to path or token
- **THEN** validation SHALL fail
- **AND** error SHALL suggest valid alternatives

### Requirement: Fix Hint Generation
The system SHALL provide helpful fix hints when validation fails.

#### Scenario: Fix hint for missing frontmatter

- **WHEN** validation fails due to missing frontmatter
- **AND** `--fix-hint` flag is used
- **THEN** output SHALL include suggested frontmatter template

#### Scenario: Fix hint for invalid owner

- **WHEN** validation fails due to invalid owner
- **AND** `--fix-hint` flag is used
- **THEN** output SHALL suggest valid owner alternatives

### Requirement: Tracked Files Discovery
The system SHALL discover all Markdown files that should be tracked for frontmatter validation.

#### Scenario: Discover files in docs directory

- **WHEN** script runs
- **THEN** all `docs/**/*.md` files SHALL be discovered
- **AND** exempt files SHALL be excluded

#### Scenario: Discover root-level docs

- **WHEN** script runs
- **THEN** configured root-level docs SHALL be discovered
- **AND** exempt files SHALL be excluded

### Requirement: Exempt Files Handling
The system SHALL properly handle files marked as exempt.

#### Scenario: Exempt file with valid reason

- **WHEN** file has `exempt: true` with valid reason
- **THEN** file SHALL be excluded from validation

#### Scenario: Non-exempt file validation

- **WHEN** file has `exempt: false` or no exempt field
- **THEN** file SHALL undergo full validation

## Contract Requirements

### Requirement: Validation Contracts
The validation script SHALL use `@icontract` decorators for validation logic:
- `@require` for input validation
- `@ensure` for validation results

#### Scenario: Invalid file path input

- **WHEN** script receives invalid file path
- **THEN** `@require` contract SHALL raise appropriate exception

### Requirement: Error Handling Contracts
The script SHALL handle errors gracefully with appropriate contracts.

#### Scenario: File read error

- **WHEN** script encounters file read error
- **THEN** error SHALL be caught and handled
- **AND** script SHALL continue with other files

## Performance Requirements

### Requirement: Efficient File Processing
The validation script SHALL process files efficiently.

#### Scenario: Large documentation set

- **WHEN** script processes 100+ documentation files
- **THEN** execution SHALL complete in < 2 seconds

### Requirement: Memory Efficiency
The script SHALL be memory efficient.

#### Scenario: Memory usage with many files

- **WHEN** script processes large number of files
- **THEN** memory usage SHALL remain under 100MB