## Scope rescope — 2026-09-20

Keep the signed C14/C15, profile, policy and exception-authority prerequisites. Optional preflight is not an indirect prerequisite. Use meaningful regression reproduction, current test results and independent review; no immutable RED history or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## MODIFIED Requirements

### Requirement: Protected Code Review green SHALL require a verified C14 envelope

A protected Code Review required check SHALL report success only when the
core-owned verifier envelope binds the approved signed schema 1.7 producer
report, verifies the applicable C15 policy/exception identities, and records
effective `pr_range` with authoritative PASS. Producer status alone SHALL NOT
constitute protected-range authority. After C15 adoption this replaces the
C14 producer-version acceptance rule while preserving C14 range verification
and trusted-context provenance. Required local and protected checks SHALL use
their authoritative schema contract and fail closed when required evidence is
unavailable or invalid.

#### Scenario: Producer passes but protected verification is unknown

- **GIVEN** a producer report records PASS with `range_candidate`
- **AND** the core verifier records an omitted or mismatched required identity
- **WHEN** the protected Code Review check runs in enforce mode
- **THEN** the emitted check fails
- **AND** it reports `UNKNOWN` rather than a green PR-range result.

#### Scenario: Verified C14 envelope passes

- **GIVEN** the approved schema 1.7 producer report and core verifier envelope are complete,
  signed, mutually consistent, and bind the protected workflow context
- **AND** the envelope records effective `pr_range` with PASS
- **WHEN** the protected check completes in enforce mode
- **THEN** the check reports success
- **AND** retains the producer report and verifier envelope as distinct
  artifacts.

#### Scenario: Score and finding recount cannot manufacture green

- **GIVEN** the authoritative report is failing, unknown, missing, or invalid
- **WHEN** a required check evaluates code-review evidence
- **THEN** a local score threshold, raw severity recount, or nested process zero cannot produce green
- **AND** the required check exits non-zero outside shadow mode.
