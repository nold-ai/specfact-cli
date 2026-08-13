# Tasks: Bounded Red-Green Replay

All implementation tasks are intentionally small (target: at most two hours) and name their allowed files. No implementation begins until the paired modules schema is released.

## 0. Planning

- [x] 0.1 Define the bounded B < R < H claim and explicit non-goals.
- [x] 0.2 Define allowed future paths and prohibit extension of static dependency inference.
- [x] 0.3 Record that this planning branch contains no behavior changes.

## 1. Paired modules release

- [ ] 1.1 Implement independent current-execution and chronology states in the paired modules R07/R08 changes.
- [ ] 1.2 Implement the bounded attestation schema and validation contracts.
- [ ] 1.3 Publish a signed module release and record the immutable release SHA.

## 2. Failing tests first

- [ ] 2.1 Create temporary-Git-repository tests for valid B < R < H and invalid ancestry. Allowed path: one new focused unit test module.
- [ ] 2.2 Add failing tests for B..R production changes and R..H undeclared/test/config/harness changes. Allowed path: the same focused unit test module.
- [ ] 2.3 Add failing integration tests proving exact failure at R and exact pass at H under identical selectors. Allowed path: one new integration test module.
- [ ] 2.4 Add failing tests for shallow history, invalid refs, checkout failure, timeout, missing JUnit, selector mismatch, and rename endpoints.
- [ ] 2.5 Add a failing bootstrap test proving verifier/policy self-changes cannot self-attest.
- [ ] 2.6 Record commands and expected failures in `TDD_EVIDENCE.md` before production edits.

## 3. Minimal implementation

- [ ] 3.1 Add an explicit full-SHA red reference to the accepted checkpoint input. Do not auto-discover R.
- [ ] 3.2 Implement ancestry and changed-path-set validation. Do not parse Python AST.
- [ ] 3.3 Implement isolated worktree replay for R and H with identical bounded subprocess arguments.
- [ ] 3.4 Implement attestation construction and module reconciliation handoff.
- [ ] 3.5 Wire the workflow in shadow mode and retain all artifacts before enforcement.
- [ ] 3.6 Remove or bypass obsolete static pytest-input closure from the authoritative path; prefer deletion over parallel complexity.

## 4. Verification and rollout

- [ ] 4.1 Run the #665–#671 benchmark plus seeded invalid-history/path cases.
- [ ] 4.2 Run strict OpenSpec, workflow lint, focused/full tests, contracts, static analysis, and explicit base/head Code Review.
- [ ] 4.3 Establish and document the initial reviewed verifier policy epoch.
- [ ] 4.4 Run shadow, warning, then strict rollout; record rollback instructions.

## Prohibited shortcuts

- Do not cherry-pick PR #671.
- Do not add import, plugin, configuration, data-read, alias, mutation, namespace, symlink, or dynamic-execution inference.
- Do not reuse retained red artifacts in the strongest replay profile.
- Do not allow test/config/harness changes after R; require a new R.
- Do not emit pass/no-impact for missing or unresolved mandatory facts.

## Closed implementation allowlist

Anything not listed here is prohibited unless this OpenSpec change is updated and accepted first.

Production/configuration:

- `scripts/requirements_proof_provenance.py`: replace the existing static/AST closure with the small Git-only B/R/H validator, isolated replay orchestration, and attestation builder. Delete the old import/plugin/config/data-read rules; do not add a parallel provenance script.
- `.github/workflows/requirements-evidence.yml`: pass explicit B/R/H, invoke shadow replay, retain both JUnit artifacts and attestation before enforcement, and enforce verifier-epoch bootstrap.
- `ci/module-fixture.lock.json`: signed R08-capable modules identity only.
- `scripts/requirements_proof_executor.py`: conditional only when replay cannot use its current public seam; permit explicit worktree root/run-stage/output while preserving argv/environment safety.

Tests:

- `tests/unit/scripts/test_requirements_proof_provenance.py`: replace obsolete static-closure cases with ancestry, path-set, missing-history/artifact, rename, attestation, and bootstrap cases.
- New exactly `tests/integration/scripts/test_requirements_red_green_replay.py`: temporary-repository exact fail-at-R/pass-at-H replay, timeout, and selector mismatch.
- `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`: shadow wiring, artifacts-before-enforcement, and epoch bootstrap.
- `tests/unit/scripts/test_requirements_proof_executor.py`: conditional only when the executor changes.
- Temporary repositories live inside the named tests; no fixture directory.

Explicitly forbidden:

- any new general pytest analyzer/provenance production file;
- `scripts/requirements_proof_pytest_plugin.py` unless its existing canonical-selector contract demonstrably fails;
- `scripts/requirements_evidence_delivery_gate.py`, `scripts/pre-commit-quality-checks.sh`, all `src/**`, and `tools/**`;
- security, dependency, safe-write, and smart-coverage paths, `pyproject.toml`, `uv.lock`, and unrelated tests.
