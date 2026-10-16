## Scope rescope — 2026-09-20

Optional preflight, approval seals and development checkpoints are not prerequisites. Keep independent protected-range verification, complete scope, authenticated runtime and signed producer compatibility. Use focused regression reproduction and current-run results; do not require immutable RED history, frozen selector inventories or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## ADDED Requirements

### Requirement: Protected Code Review green SHALL require a verified C14 envelope

A protected Code Review required check SHALL report success only when the
core-owned verifier envelope binds the signed C14 producer report and records
effective `pr_range` with authoritative PASS. Producer status alone SHALL NOT
constitute protected-range authority.

#### Scenario: Producer passes but protected verification is unknown

- **GIVEN** a producer report records PASS with `range_candidate`
- **AND** the core verifier records an omitted or mismatched required identity
- **WHEN** the protected Code Review check runs in enforce mode
- **THEN** the emitted check fails
- **AND** it reports `UNKNOWN` rather than a green PR-range result.

#### Scenario: Verified C14 envelope passes

- **GIVEN** the producer report and core verifier envelope are complete,
  signed, mutually consistent, and bind the protected workflow context
- **AND** the envelope records effective `pr_range` with PASS
- **WHEN** the protected check completes in enforce mode
- **THEN** the check reports success
- **AND** retains the producer report and verifier envelope as distinct
  artifacts.
