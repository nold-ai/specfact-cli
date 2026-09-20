## Scope rescope — 2026-09-20

Keep the signed C14/C15, profile, policy and exception-authority prerequisites. Optional preflight is not an indirect prerequisite. Use meaningful regression reproduction, current test results and independent review; no immutable RED history or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## ADDED Requirements

### Requirement: Authoritative Schema 1.7 Local Consumer

The core pre-commit helper SHALL invoke explicit changed enforcement with
bug-hunt timeouts, validate the schema 1.7 status/exit contract, and return the
report's authoritative exit code.

#### Scenario: Valid schema 1.7 result controls the hook

- **GIVEN** the review command writes a valid schema 1.7 report
- **WHEN** the pre-commit helper consumes it
- **THEN** the helper returns the report ci_exit_code
- **AND** it does not recompute authority from finding counts, score, fixable, or subprocess status.

#### Scenario: Contradictory report fails closed

- **GIVEN** schema 1.7 reports FAIL or UNKNOWN with a non-shadow zero exit, or PASS/NOT_APPLICABLE with exit one
- **WHEN** the helper validates the report
- **THEN** the report is rejected and the hook exits non-zero.

#### Scenario: Shadow preserves truthful status

- **GIVEN** schema 1.7 reports FAIL or UNKNOWN under shadow mode with exit zero
- **WHEN** the helper validates it
- **THEN** the report is accepted as shadow evidence
- **AND** the printed summary retains the non-passing assurance status.

#### Scenario: Legacy schema is shadow-only

- **GIVEN** a schema 1.6 report
- **WHEN** protected or local blocking enforcement requires schema 1.7
- **THEN** the older report cannot satisfy the gate
- **AND** it may be read only through the documented shadow compatibility path.

### Requirement: Protected Schema 1.7 Waiver Verification

Protected CI SHALL independently verify the approved module, profile, C14
envelope, and trusted-base exception evidence before accepting a waived error.

#### Scenario: Trusted approved waiver is accepted

- **GIVEN** the report and C14 envelope match approved signed identities
- **AND** a retained directive matches an active trusted-base exception for the same canonical rule, path, and symbol
- **WHEN** protected verification runs
- **THEN** the waiver is accepted and retained as advisory evidence.

#### Scenario: Candidate self-approval is rejected

- **GIVEN** the candidate adds or changes the exception that would authorize its own error suppression
- **WHEN** protected verification runs
- **THEN** the candidate exception is not approval authority
- **AND** the error remains blocking.

#### Scenario: Identity or expiry mismatch fails closed

- **GIVEN** the module/profile digest, C14 envelope, rule/scope, approval, or expiry evidence is missing or mismatched
- **WHEN** protected verification runs
- **THEN** effective assurance is UNKNOWN or FAIL as applicable
- **AND** protected CI exits non-zero.
