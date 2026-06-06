# doc-frontmatter-validation Specification

## Purpose

This specification governs the repository validator that enforces doc-frontmatter ownership rules,
fix hints, and rollout scope so maintainers can trust documentation metadata checks locally and in
CI.

## Requirements

### Requirement: Validation Script Implementation

The system SHALL provide a validation script, `scripts/check_doc_frontmatter.py`, that enforces
frontmatter requirements.

#### Scenario: Script execution with valid docs

- **WHEN** `check_doc_frontmatter.py` is executed
- **AND** all tracked docs have valid frontmatter
- **THEN** the script SHALL exit with code `0`
- **AND** output SHALL show a success message

#### Scenario: Script execution with invalid docs

- **WHEN** `check_doc_frontmatter.py` is executed
- **AND** some docs have invalid frontmatter
- **THEN** the script SHALL exit with code `1`
- **AND** output SHALL list all validation failures

### Requirement: Missing Doc Owner Detection

The system SHALL detect documentation files that are missing the `doc_owner` field.

#### Scenario: Missing doc_owner in tracked file

- **WHEN** a tracked Markdown file lacks `doc_owner`
- **THEN** validation SHALL fail
- **AND** the error SHALL specify the missing field

#### Scenario: Valid doc_owner present

- **WHEN** a tracked Markdown file has a valid `doc_owner`
- **THEN** validation SHALL pass for the owner requirement

### Requirement: Owner Resolution Validation

The system SHALL validate that `doc_owner` values resolve to existing paths or known tokens.

#### Scenario: Owner resolves to existing path

- **WHEN** `doc_owner` is a path that exists in the repository
- **THEN** validation SHALL pass for owner resolution

#### Scenario: Owner is valid known token

- **WHEN** `doc_owner` is in `VALID_OWNER_TOKENS`
- **THEN** validation SHALL pass for owner resolution

#### Scenario: Owner cannot be resolved

- **WHEN** `doc_owner` does not resolve to a path or token
- **THEN** validation SHALL fail
- **AND** the error SHALL suggest valid alternatives

### Requirement: Fix Hint Generation

The system SHALL provide helpful fix hints when validation fails.

#### Scenario: Fix hint for missing frontmatter

- **WHEN** validation fails due to missing frontmatter
- **AND** the `--fix-hint` flag is used
- **THEN** output SHALL include a suggested frontmatter template
- **AND** the template SHALL include `doc_owner`, `tracks`, `last_reviewed`, `exempt`, and
  `exempt_reason`

#### Scenario: Fix hint for invalid owner

- **WHEN** validation fails due to an invalid owner
- **AND** the `--fix-hint` flag is used
- **THEN** output SHALL suggest valid owner alternatives

### Requirement: Tracked Files Discovery

The system SHALL discover all Markdown files that should be tracked for frontmatter validation.

#### Scenario: Discover files in docs directory

- **WHEN** the script runs
- **THEN** all `docs/**/*.md` files SHALL be discoverable
- **AND** exempt files SHALL be excluded

#### Scenario: Discover root-level docs

- **WHEN** the script runs
- **THEN** configured root-level docs SHALL be discoverable
- **AND** exempt files SHALL be excluded

#### Scenario: Full-site validation ignores rollout list

- **WHEN** `check_doc_frontmatter.py --all-docs` is executed
- **THEN** the validator SHALL inspect every discovered documentation file
- **AND** it SHALL not require `docs/.doc-frontmatter-enforced` to define the validation scope

### Requirement: Exempt Files Handling

The system SHALL properly handle files marked as exempt.

#### Scenario: Exempt file with valid reason

- **WHEN** a file has `exempt: true` with a valid `exempt_reason`
- **THEN** the file SHALL be excluded from validation

#### Scenario: Non-exempt file validation

- **WHEN** a file has `exempt: false` or no exemption
- **THEN** the file SHALL undergo full validation

**Contract requirements:**

### Requirement: Validation Contracts

The validation module SHALL use `@icontract` decorators on public validation helpers such as
`parse_frontmatter`, `extract_doc_owner`, `resolve_owner`, `validate_glob_patterns`,
`suggest_frontmatter`, `get_all_md_files`, `rg_missing_doc_owner`, and `main`.

#### Scenario: Invalid public helper input

- **WHEN** one of the public validation helpers receives an invalid input
- **THEN** its `@require` or `@ensure` contract SHALL enforce the documented pre/postcondition

### Requirement: Error Handling Contracts

The script SHALL handle file and YAML errors gracefully while preserving validator outcomes.

#### Scenario: File read or YAML parse error

- **WHEN** the script encounters a file read error or YAML parse error
- **THEN** the error SHALL be surfaced in validation output
- **AND** validation SHALL continue for the remaining files

**Performance requirements:**

### Requirement: Efficient File Processing

The validation script SHALL process files efficiently.

#### Scenario: Large documentation set

- **WHEN** the script processes 100 or more documentation files
- **THEN** execution SHALL complete quickly enough for local and CI use

### Requirement: PR Orchestrator Parallel Job Graph

The PR orchestrator workflow SHALL not serialize independent validation jobs behind the Python 3.12
test suite when those jobs do not consume test artifacts.

#### Scenario: Independent jobs start after shared signature gate

- **WHEN** `.github/workflows/pr-orchestrator.yml` defines `compat-py311`, `contract-first-ci`,
  `type-checking`, `linting`, and `cli-validation`
- **THEN** each of those jobs SHALL depend on `changes` and the shared signature gate
- **AND** none of those jobs SHALL list `tests` as a required predecessor unless they consume test
  artifacts from that job

#### Scenario: Coverage-based advisory gate still depends on tests

- **WHEN** `quality-gates` reads the `coverage-reports` artifact
- **THEN** `quality-gates` SHALL keep `tests` as an explicit dependency
- **AND** the workflow SHALL continue to gate that job on unit-coverage availability
