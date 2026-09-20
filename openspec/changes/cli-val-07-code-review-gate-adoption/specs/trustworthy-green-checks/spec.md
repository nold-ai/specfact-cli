## Scope rescope — 2026-09-20

Keep the signed C14/C15, profile, policy and exception-authority prerequisites. Optional preflight is not an indirect prerequisite. Use meaningful regression reproduction, current test results and independent review; no immutable RED history or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## ADDED Requirements

### Requirement: Code Review Green Status Is Evidence-Derived

Required local and protected code-review checks SHALL use the authoritative
schema contract and SHALL fail closed when that evidence is unavailable or
invalid.

#### Scenario: Score and finding recount cannot manufacture green

- **GIVEN** the authoritative report is failing, unknown, missing, or invalid
- **WHEN** a required check evaluates code-review evidence
- **THEN** a local score threshold, raw severity recount, or nested process zero cannot produce green
- **AND** the required check exits non-zero outside shadow mode.
