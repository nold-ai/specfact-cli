# Change Validation: Planning Correction

## Status

`PLANNED — IMPLEMENTATION EVIDENCE NOT YET AVAILABLE`

This branch changes OpenSpec planning artifacts only. It deliberately does not claim that the corrected R07 behavior is implemented or verified.

## Validation evidence

- Evidence class: planning structure and repository integration only.
- Strict planning command: `openspec validate --all --strict`.
- Result: passed for commit `4b12860a70c9e29dd67a01bd5f3cd55dcb86af60` in [SpecFact CLI Validation run 31741879217](https://github.com/nold-ai/specfact-cli/actions/runs/31741879217).
- Execution timestamp: 2026-08-13T20:38:42Z through 2026-08-13T20:40:05Z.
- Required per-change pre-implementation command: `openspec validate requirements-07-runtime-proof-delivery --strict`.
- Affected planning files: `README.md`, `proposal.md`, `design.md`, `tasks.md`, `CHANGE_VALIDATION.md`, `TDD_EVIDENCE.md`, `requirements-evidence.yaml`, and both R07 delta specifications.
- Failing-before implementation artifact: unavailable and not claimed; no corrected behavior has been implemented.
- Passing-after implementation artifact: unavailable and not claimed; current CI proves only planning/schema/repository consistency.
- Excluded or unavailable dependencies: the corrected signed modules release, accepted report-schema identity, internal-wiki checkout, and final R06-to-R07 archive verification.

## Validated planning boundaries

- R07 owns current-run exact-selector planning, execution, JUnit reconciliation, publication, and independent review handoff.
- R08 owns bounded historical red-to-green replay.
- Static inference of complete Python/pytest execution inputs is out of scope.
- The module report must separate `current_execution` from `red_green_chronology` before core implementation begins.
- The signed fixture must bind repository commit/tree, package version, module signature, and accepted report-schema version.
- Code Review must consume current-run evidence without requiring or synthesizing R08 chronology.

## Blockers before implementation can pass

1. The paired modules planning change must be implemented and released as a signed immutable fixture.
2. The module release must expose the accepted current-execution report schema/version and preserve chronology as a separate optional claim.
3. Focused failing tests and their exact commands must be recorded before production changes.
4. Core must consume the signed module report without restoring legacy-ledger or static dependency-closure behavior.
5. Full PR scope and all mandatory tools must resolve; unresolved evidence is not pass.
6. The internal-wiki follow-up and disposable R06-to-R07 archive verification in `tasks.md` remain incomplete.

Historical green reports and the existing TDD ledger predate this correction and are not evidence that the corrected contract is satisfied.
