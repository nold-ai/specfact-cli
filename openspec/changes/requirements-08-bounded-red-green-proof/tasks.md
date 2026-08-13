# Tasks: Bounded Red-Green Replay

All implementation tasks are intentionally small (target: at most two hours) and name their allowed files. No implementation begins until the paired modules schema is released.

## 0. Planning

- [x] 0.1 Define the bounded B < R < H claim and explicit non-goals.
- [x] 0.2 Define allowed future paths and prohibit extension of static dependency inference.
- [x] 0.3 Record that this planning branch contains no behavior changes.

## Implementation-session checklist — before any unchecked implementation task

- [ ] B.1 Create a dedicated implementation worktree and feature branch from current `origin/dev`; do not implement from the primary, `dev`, or `main` checkout.
- [ ] B.2 Run `hatch env create`, then `hatch run smart-test-status` and `hatch run contract-test-status` in the worktree; record and resolve unexpected baseline failures before edits.
- [ ] B.3 Run the change-specific strict OpenSpec command and confirm the accepted specs, dependencies, signed-module prerequisites, and closed file allowlist still match repository reality.
- [ ] B.4 Follow `spec -> tests -> failing evidence -> code -> passing evidence`; record exact failing-before and passing-after commands, timestamps, and artifact identities in `TDD_EVIDENCE.md`.
- [ ] B.5 Before PR finalization, run the required format, type, lint, YAML, contract, focused/full test, workflow, independent-analysis, signature, and explicit base/head Code Review gates; resolve every finding or document an approved exception.
- [ ] B.6 After merge and only when the change is complete, archive with the OpenSpec CLI, update the internal-wiki mirror, remove the worktree, prune it, and complete an explicit `AGENTS.md` worktree/policy self-check.

## 1. Paired modules release

- [ ] 1.1 Implement independent current-execution and chronology states in the paired modules R07/R08 changes.
- [ ] 1.2 Implement the versioned replay-capsule schema and validation contracts: core supplies Git/execution facts; modules validate schema/hash/transition/outcome facts without running Git or tests.
- [ ] 1.3 Publish a signed module release and record its immutable repository commit/tree, package version, capsule-schema version, manifest integrity, and signature identities.

## 2. Failing tests first

- [ ] 2.1 In `tests/unit/scripts/test_requirements_proof_provenance.py`, replace obsolete static-closure cases with temporary-Git-repository tests for valid B < R < H and invalid ancestry.
- [ ] 2.2 In `tests/unit/scripts/test_requirements_proof_provenance.py`, add failing tests that reject every undeclared/disallowed B..R path or rename endpoint and every R..H undeclared/test/config/harness change.
- [ ] 2.3 In exactly `tests/integration/scripts/test_requirements_red_green_replay.py`, add failing integration tests proving exact failure at R and exact pass at H under identical selectors.
- [ ] 2.4 In `tests/unit/scripts/test_requirements_proof_provenance.py`, add shallow-history, invalid-ref, checkout-failure, missing-artifact, and rename-endpoint cases; execution timeout and selector-mismatch cases may additionally use `tests/integration/scripts/test_requirements_red_green_replay.py`.
- [ ] 2.5 In `tests/unit/scripts/test_requirements_proof_provenance.py`, add a failing bootstrap test proving verifier/policy self-changes cannot self-attest.
- [ ] 2.6 Record commands and expected failures in `TDD_EVIDENCE.md` before production edits.

## 3. Minimal implementation

- [ ] 3.1 In `scripts/requirements_proof_provenance.py`, add explicit full-SHA B/R/H inputs plus complete declared `red_setup_touchpoints` and implementation-touchpoint sets. Do not auto-discover R.
- [ ] 3.2 In `scripts/requirements_proof_provenance.py`, implement ancestry and both closed changed-path/rename-endpoint validators. Do not parse Python AST.
- [ ] 3.3 In `scripts/requirements_proof_provenance.py`, implement isolated worktree replay for R and H with identical bounded subprocess arguments and enforced network-isolation evidence; change `scripts/requirements_proof_executor.py` only if the existing seam demonstrably cannot support explicit worktree/output inputs.
- [ ] 3.4 In `scripts/requirements_proof_provenance.py`, produce the versioned capsule and hand it to the signed Requirements module; bind the accepted capsule schema, module identity/signature, network policy, and verifier epoch.
- [ ] 3.5 In `.github/workflows/requirements-evidence.yml` and `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`, wire shadow mode, make unavailable network isolation unproven, and retain all artifacts before enforcement.
- [ ] 3.6 In `scripts/requirements_proof_provenance.py`, remove or bypass obsolete static pytest-input closure from the authoritative path; prefer deletion over parallel complexity.

## 4. Verification and rollout

- [ ] 4.1 Run the #665–#671 benchmark plus seeded invalid-history/path cases.
- [ ] 4.2 Run strict OpenSpec, workflow lint, focused/full tests, contracts, static analysis, and explicit base/head Code Review.
- [ ] 4.3 Establish and document the initial reviewed verifier policy epoch.
- [ ] 4.4 Run shadow, warning, then strict rollout; record rollback instructions.
- [ ] 4.5 Merge checklist follow-up: create or update `wiki/sources/requirements-08-bounded-red-green-proof.md` (`depends-on`, `blocks`, `external-deps`, `status`, and summary) and run `python3 scripts/wiki_rebuild_graph.py` from the `specfact-cli-internal` repository root.

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
