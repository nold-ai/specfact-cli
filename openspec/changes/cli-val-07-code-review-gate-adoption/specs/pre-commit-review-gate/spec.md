## MODIFIED Requirements

### Requirement: Repository Pre-Commit Review Gate

The system SHALL integrate `specfact code review run` into this repository's
pre-commit workflow as an `explicit_files` staged-file check using explicit
changed enforcement and bug-hunt timeouts. After C15 adoption, blocking policy
SHALL require the signed schema 1.7 authoritative status/exit contract, replacing
C14's schema 1.6 contract. The hook SHALL validate and return `ci_exit_code`,
reject malformed or contradictory reports, and never derive approval from
finding counts, a legacy verdict, or subprocess success alone. Outside shadow,
`FAIL` and `UNKNOWN` SHALL block; valid `PASS` and `NOT_APPLICABLE` SHALL allow
progress. It SHALL NOT accept protected PR context or claim `range_candidate`
or `pr_range` assurance.

#### Scenario: Pre-commit passes when review verdict is PASS

- **GIVEN** relevant staged files produce a valid schema 1.7 `PASS` with exit zero
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits successfully and reports `explicit_files` assurance.

#### Scenario: Pre-commit passes when review verdict is PASS_WITH_ADVISORY

- **GIVEN** schema 1.7 has authoritative `PASS` or `NOT_APPLICABLE` and exit zero with advisory findings
- **WHEN** the hook presents any legacy `PASS_WITH_ADVISORY` summary
- **THEN** the commit may proceed based on the validated schema 1.7 fields, not that summary.

#### Scenario: Pre-commit blocks commit when review verdict is FAIL

- **GIVEN** non-shadow schema 1.7 reports `FAIL` or `UNKNOWN`, or has contradictory status/exit fields
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits non-zero with actionable diagnostics.

#### Scenario: Review gate only targets relevant staged files

- **GIVEN** a commit contains relevant staged source files and non-code staged files
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the command reviews only the relevant staged source files
- **AND** it passes no protected PR context and cannot emit effective `pr_range`.

#### Scenario: Missing review command surfaces actionable setup guidance

- **GIVEN** the local environment cannot run the review command or supply its valid report
- **WHEN** the repository pre-commit workflow runs the review gate
- **THEN** the hook exits non-zero with actionable setup or report diagnostics.

#### Scenario: Shadow preserves truthful status

- **GIVEN** valid schema 1.7 reports `FAIL` or `UNKNOWN` with an authorized shadow exit of zero
- **WHEN** the hook validates and displays the result
- **THEN** it retains the non-passing assurance status while returning the shadow exit code.

#### Scenario: Schema 1.6 no longer satisfies blocking enforcement

- **GIVEN** a schema 1.6 report after C15 adoption
- **WHEN** local blocking policy requires schema 1.7
- **THEN** the old report cannot satisfy the gate
- **AND** it is readable only in the documented shadow path for one migration release.

#### Scenario: Staged hook consumes a schema 1.6 PASS

- **GIVEN** a schema 1.6 report claims `PASS` after C15 adoption
- **WHEN** the hook reads it during the one-release shadow compatibility window
- **THEN** it identifies the result as legacy shadow evidence
- **AND** the same report cannot satisfy schema 1.7 blocking enforcement.

#### Scenario: Staged hook fails closed on schema 1.6 uncertainty

- **GIVEN** a schema 1.6 report is uncertain or contradictory
- **WHEN** the hook requires schema 1.7 blocking enforcement
- **THEN** it exits non-zero rather than inferring missing fields or a passing status.

#### Scenario: Staged files cannot claim PR authority

- **GIVEN** the local hook receives staged positional files
- **WHEN** it builds and executes the review command
- **THEN** it does not pass protected PR context or range-assurance arguments
- **AND** it cannot emit effective `pr_range`.
