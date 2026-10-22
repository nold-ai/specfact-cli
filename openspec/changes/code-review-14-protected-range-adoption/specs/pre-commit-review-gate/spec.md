## Scope rescope — 2026-09-20

Optional preflight, approval seals and development checkpoints are not prerequisites. Keep independent protected-range verification, complete scope, authenticated runtime and signed producer compatibility. Use focused regression reproduction and current-run results; do not require immutable RED history, frozen selector inventories or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## MODIFIED Requirements

### Requirement: Repository Pre-Commit Review Gate

The system SHALL integrate `specfact code review run` into this repository's
pre-commit workflow as an `explicit_files` staged-file check. It SHALL consume
schema 1.6 authoritative `assurance_status` and exit semantics, block any
authoritative `FAIL` or `UNKNOWN`, and allow an authoritative `PASS` or
`NOT_APPLICABLE` according to the signed report contract. It SHALL NOT accept
protected PR context or claim `range_candidate` or `pr_range` assurance.

#### Scenario: Staged hook consumes a schema 1.6 PASS

- **GIVEN** the staged explicit-file review emits a valid schema 1.6 report
  with authoritative `assurance_status=PASS`
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits successfully
- **AND** its summary identifies the assurance as `explicit_files`.

#### Scenario: Staged hook fails closed on schema 1.6 uncertainty

- **GIVEN** the staged explicit-file review emits authoritative
  `assurance_status=UNKNOWN` or inconsistent status/exit evidence
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits non-zero with actionable diagnostics
- **AND** it does not reinterpret uncertainty through legacy finding severity.

#### Scenario: Staged files cannot claim PR authority

- **GIVEN** the local hook receives staged positional files
- **WHEN** it builds and executes the review command
- **THEN** it does not pass protected PR context or range-assurance arguments
- **AND** it cannot emit effective `pr_range`.

#### Scenario: Pre-commit passes when review verdict is PASS

- **GIVEN** staged repository files produce a valid schema 1.6 authoritative `PASS` with consistent legacy verdict and exit code
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits successfully and the commit may proceed

#### Scenario: Pre-commit passes when review verdict is PASS_WITH_ADVISORY

- **GIVEN** staged repository files produce a valid schema 1.6 report with authoritative `PASS` or `NOT_APPLICABLE` and a consistent `PASS_WITH_ADVISORY` projection
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits successfully and the commit may proceed

#### Scenario: Pre-commit blocks commit when review verdict is FAIL

- **GIVEN** staged repository files produce authoritative `FAIL` or `UNKNOWN` with a conservative legacy `FAIL` projection
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
