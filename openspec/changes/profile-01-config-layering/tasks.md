# Tasks: profile-01-config-layering

## 1. Branch and dependency guardrails

- [x] 1.1 Create dedicated worktree branch `feature/profile-01-config-layering-baseline` from `dev` before implementation work.
- [x] 1.2 Verify prerequisite changes are implemented or explicitly accepted as parallel work.
- [x] 1.3 Reconfirm scope against the 2026-02-15 architecture integration plan and this proposal.
- [x] 1.4 Refresh stale February proposal/design/spec wording against the July validation-evidence roadmap before PR preparation.

## 2. Spec-first and test-first preparation

- [x] 2.1 Finalize `specs/` deltas for all listed capabilities and cross-check scenario completeness.
- [x] 2.2 Add/update tests mapped to new and modified scenarios.
- [x] 2.3 Run targeted tests to capture failing-first behavior and record results in `TDD_EVIDENCE.md`.

## 3. Implementation

- [x] 3.1 Implement minimal production code required to satisfy the new scenarios.
- [x] 3.2 Add/update contract decorators and type enforcement on public APIs.
- [x] 3.3 Update command wiring, adapters, and models required by this change scope only.
- [x] 3.4 Map tier profiles to clean-code defaults in the shared resolver so downstream consumers inherit one source of truth for clean-code mode selection.

## 4. Validation and documentation

- [x] 4.1 Re-run tests and quality gates until all changed scenarios pass.
- [x] 4.2 Update user-facing docs and navigation for changed/added commands and workflows.
- [x] 4.3 Run `openspec validate profile-01-config-layering --strict` and resolve all issues.

## 5. Delivery

- [x] 5.1 Confirm `openspec/CHANGE_ORDER.md` did not need status/dependency updates; implementation sequencing stayed unchanged.
- [x] 5.2 Merge PR [#624](https://github.com/nold-ai/specfact-cli/pull/624) to `dev` with spec/test/code/docs evidence; promotion to `main` remains pending release PR #642.
