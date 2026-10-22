## Scope rescope — 2026-09-20

Keep the signed C14/C15, profile, policy and exception-authority prerequisites. Optional preflight is not an indirect prerequisite. Use meaningful regression reproduction, current test results and independent review; no immutable RED history or committed test transcripts.

This owner-requested planning amendment supersedes conflicting development-workflow and dependency wording below. Runtime behavior is unchanged. Replacement policy: [core #740](https://github.com/nold-ai/specfact-cli/issues/740) and [modules #481](https://github.com/nold-ai/specfact-cli-modules/issues/481).

## ADDED Requirements

### Requirement: Protected Code Review Uses Approved Signed Evidence

Protected CI SHALL consume only the released, approved schema 1.7 producer and
shall bind the C14 verification envelope, C15 policy profile, and trusted-base
exception authority.

#### Scenario: Feature-branch or unapproved producer cannot enforce

- **GIVEN** a code-review report comes from a feature-branch, unsigned, version-mismatched, or profile-mismatched module
- **WHEN** protected CI evaluates it
- **THEN** the report cannot satisfy required code-review assurance
- **AND** CI fails closed rather than falling back to legacy parsing.
