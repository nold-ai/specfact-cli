# Change Validation: Planning Correction

## Status

`PLANNED — IMPLEMENTATION EVIDENCE NOT YET AVAILABLE`

This branch changes OpenSpec planning artifacts only. It deliberately does not claim that the corrected R07 behavior is implemented or verified.

## Current delivery-tree validation contract

- Planning command: `openspec validate --all --strict`.
- Required per-change command before and after implementation: `openspec validate requirements-07-runtime-proof-delivery --strict`.
- The authoritative planning result is the final successful SpecFact CLI Validation check on PR #674 whose recorded `head_sha` equals the PR delivery head.
- The exact final head SHA, workflow run URL, status, and result belong in the PR/check-suite delivery record after the last content commit. They are intentionally not hard-coded here: adding a commit's own SHA to this file would change that SHA and create an impossible self-reference.
- The earlier run for `4b12860a70c9e29dd67a01bd5f3cd55dcb86af60` is historical planning evidence only and is not evidence for the final PR tree.
- No implementation validation result, focused-test count, failing-before artifact, or passing-after artifact exists yet.

## Planning sources and constraints

- Applied sources: `AGENTS.md`, `openspec/config.yaml`, and `docs/agent-rules/40-openspec-and-tdd.md`, `50-github-project-management.md`, and `70-release-commit-and-docs.md`.
- Internal wiki: unavailable in this workspace; `tasks.md` requires the exact post-merge source-page and graph-rebuild follow-up.
- Affected planning files: `README.md`, `proposal.md`, `design.md`, `tasks.md`, `CHANGE_VALIDATION.md`, `TDD_EVIDENCE.md`, `requirements-evidence.yaml`, and both R07 delta specifications.
- Excluded or unavailable dependencies: corrected signed modules release, accepted report-schema identity, approved signing-key/trust-root identity, internal-wiki checkout, and final R06-to-R07 archive verification.

## Required implementation evidence

At implementation finalization this file SHALL record validation scope and impact, affected files, exact commands, actual outcomes and test counts, focused and full tests, skipped or unavailable tests/dependencies with reasons, artifact locations and identities, environment limitations, approved signer/trust-root verification, and release hygiene. Planning evidence, failing-before evidence, and passing-after evidence remain separate.

## Validated planning boundaries

- R07 owns current-run exact-selector planning, execution, JUnit reconciliation, publication, and independent review handoff.
- R08 owns bounded historical red-to-green replay.
- Static inference of complete Python/pytest execution inputs is out of scope.
- The module report must separate `current_execution` from `red_green_chronology` before core implementation begins.
- The signed fixture must bind repository commit/tree, package and report-schema versions, manifest integrity, approved signing-key fingerprint or trust-root, and signature.
- Code Review must consume current-run evidence without requiring or synthesizing R08 chronology.

## Blockers before implementation can pass

1. The paired modules planning change must be implemented and released as a signed immutable fixture.
2. The module release must expose the accepted current-execution report schema/version and preserve chronology as a separate optional claim.
3. Focused failing tests, exact selectors, and failing-before evidence must be recorded before production changes.
4. Core must consume the signed module report without restoring legacy-ledger or static dependency-closure behavior.
5. Full PR scope and all mandatory tools must resolve; unresolved evidence is not pass.
6. Issue/project/type metadata, internal-wiki follow-up, and disposable R06-to-R07 archive verification remain incomplete.

Historical green reports and the existing TDD ledger predate this correction and are not evidence that the corrected contract is satisfied.
