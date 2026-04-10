# pre-commit-review-gate Specification

## Purpose

TBD - created by archiving change code-review-09-f4-automation-upgrade. Update Purpose after archive.

## Requirements

### Requirement: Repository Pre-Commit Review Gate

The system SHALL integrate `specfact code review run` into this repository's
pre-commit workflow so commits are blocked when the review verdict is `FAIL`
and allowed to proceed when the verdict is `PASS` or `PASS_WITH_ADVISORY`.

#### Scenario: Pre-commit passes when review verdict is PASS

- **GIVEN** staged repository files produce a `PASS` verdict
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits successfully and the commit may proceed

#### Scenario: Pre-commit passes when review verdict is PASS_WITH_ADVISORY

- **GIVEN** staged repository files produce a `PASS_WITH_ADVISORY` verdict
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits successfully and the commit may proceed

#### Scenario: Pre-commit blocks commit when review verdict is FAIL

- **GIVEN** staged repository files produce a `FAIL` verdict
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits non-zero and the commit is blocked

#### Scenario: Review gate only targets relevant staged files

- **GIVEN** a commit contains staged files and non-code staged files
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the command reviews only the relevant staged source files instead of the full repository

#### Scenario: Missing review command surfaces actionable setup guidance

- **GIVEN** the local environment cannot run `specfact code review run`
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits non-zero with setup guidance instead of failing silently
