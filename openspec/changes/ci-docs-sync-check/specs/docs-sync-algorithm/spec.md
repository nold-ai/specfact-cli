# Docs Sync Algorithm Specification

## ADDED Requirements

### Requirement: Change Detection Algorithm
The system SHALL implement an algorithm to detect when source files change but tracked documentation doesn't.

#### Scenario: Source change without doc update
- **WHEN** source files matching `tracks` patterns change
- **AND** corresponding docs are not updated
- **THEN** algorithm SHALL detect stale documentation

#### Scenario: Source and doc both updated
- **WHEN** source files change
- **AND** corresponding docs are also updated
- **THEN** algorithm SHALL not detect stale documentation

### Requirement: Git Diff Integration
The system SHALL integrate with git to detect changed files between commits.

#### Scenario: Git diff between base and head
- **WHEN** algorithm runs on PR
- **THEN** it SHALL use `git diff --name-only <base>...<head>`
- **AND** correctly identify changed files

#### Scenario: Multiple changed files
- **WHEN** multiple files change in PR
- **THEN** algorithm SHALL process all changed files
- **AND** identify all affected documentation

### Requirement: Glob Pattern Matching
The system SHALL support glob pattern matching for tracking relationships.

#### Scenario: Single glob pattern match
- **WHEN** changed file matches single glob pattern in `tracks`
- **THEN** corresponding doc SHALL be marked for sync check

#### Scenario: Multiple glob pattern matches
- **WHEN** changed file matches multiple glob patterns
- **THEN** all corresponding docs SHALL be marked for sync check

### Requirement: Stale Documentation Identification
The system SHALL correctly identify stale documentation.

#### Scenario: Doc not in changed files
- **WHEN** source files change matching doc's `tracks`
- **AND** doc file itself is not in changed files
- **THEN** doc SHALL be marked as stale

#### Scenario: Doc in changed files
- **WHEN** source files change matching doc's `tracks`
- **AND** doc file is in changed files
- **THEN** doc SHALL not be marked as stale

### Requirement: Exempt Documentation Handling
The system SHALL properly handle exempt documentation.

#### Scenario: Exempt doc with source changes
- **WHEN** source files change matching exempt doc's `tracks`
- **THEN** doc SHALL not be marked as stale

#### Scenario: Non-exempt doc processing
- **WHEN** source files change matching non-exempt doc's `tracks`
- **THEN** doc SHALL undergo normal sync check

### Requirement: Error Reporting
The system SHALL provide clear error reporting for stale documentation.

#### Scenario: Single stale document
- **WHEN** one document is stale
- **THEN** error output SHALL list that document clearly

#### Scenario: Multiple stale documents
- **WHEN** multiple documents are stale
- **THEN** error output SHALL list all stale documents
- **AND** format SHALL be clear and readable

## Contract Requirements

### Requirement: Algorithm Contracts
The sync algorithm SHALL use `@icontract` decorators:
- `@require` for input validation
- `@ensure` for result correctness

#### Scenario: Invalid git references
- **WHEN** algorithm receives invalid git references
- **THEN** `@require` contract SHALL raise appropriate exception

### Requirement: Performance Contracts
The algorithm SHALL have performance guarantees.

#### Scenario: Large repository performance
- **WHEN** algorithm processes large repository
- **THEN** execution SHALL complete in reasonable time
- **AND** memory usage SHALL be efficient

## Integration Requirements

### Requirement: GitHub Actions Integration
The algorithm SHALL integrate with GitHub Actions workflow.

#### Scenario: Workflow execution
- **WHEN** workflow runs on PR
- **THEN** algorithm SHALL receive correct base/head references
- **AND** process changes appropriately

### Requirement: Exit Code Contract
The algorithm SHALL use appropriate exit codes.

#### Scenario: No stale documents
- **WHEN** no stale documents found
- **THEN** algorithm SHALL exit with code 0

#### Scenario: Stale documents found
- **WHEN** stale documents found
- **THEN** algorithm SHALL exit with code 1