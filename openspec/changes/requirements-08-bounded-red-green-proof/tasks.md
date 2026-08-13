# Tasks: Bounded Red-Green Replay

All implementation tasks are intentionally small (target: at most two hours) and name their allowed files. No implementation begins until the paired modules schema is released.

## 0. Planning

- [x] 0.1 Define the bounded B < R < H proof claim, delivered-head binding H <= D, and explicit non-goals.
- [x] 0.2 Define allowed future paths and prohibit extension of static dependency inference.
- [x] 0.3 Record that this planning branch contains no behavior changes.

## Implementation-session checklist — before any unchecked implementation task

- [ ] B.1 Create a dedicated implementation worktree and feature branch from current `origin/dev`; do not implement from the primary, `dev`, or `main` checkout.
- [ ] B.2 Run `hatch env create`, then `hatch run smart-test-status` and `hatch run contract-test-status` in the worktree; record and resolve unexpected baseline failures before edits.
- [ ] B.3 Read and apply `openspec/config.yaml` and its artifact rules. If the sibling `specfact-cli-internal` checkout exists, consult the applicable internal-wiki guidance. Record the sources and constraints used in `CHANGE_VALIDATION.md`. Then run exactly `openspec validate requirements-08-bounded-red-green-proof --strict`; require success before tests or source edits and rerun it after every validation-artifact fix. Confirm issue #675 remains open with parent Feature #374, requested User Story type, required labels/project assignment, accepted specs/dependencies, signed-module prerequisites, and both repository-specific closed allowlists. Stop before implementation if project/type metadata cannot be verified.
- [ ] B.4 Follow `spec -> tests -> failing evidence -> code -> passing evidence`; in `TDD_EVIDENCE.md`, record separate failing-before and passing-after sections with exact commands, timestamps, actual results, behavioral summaries, environment limitations, and artifact identities. Record passing evidence only after implementation.
- [ ] B.5 Before PR finalization, rerun exactly `openspec validate requirements-08-bounded-red-green-proof --strict` plus the required format, type, lint, YAML, contract, focused/full test, workflow, independent-analysis, signature, and explicit base/head Code Review gates. Update `CHANGE_VALIDATION.md` with validation scope/impact, affected files, exact commands, actual results and test counts, focused/full tests, skipped or unavailable tests/dependencies with reasons, artifact locations/identities, environment limitations, and release hygiene. Keep planning evidence, failing-before evidence, and H..D passing/implementation evidence separate; rerun affected validation after every artifact fix and resolve every finding or document an approved exception.
- [ ] B.6 After each merge, remove the implementation worktree, delete its local feature branch, run `git worktree prune`, and complete an explicit `AGENTS.md` worktree/policy self-check. Archive only from a dedicated follow-up worktree when the stated dependency, release, and rollout gates are complete.

## 1. Paired modules release

- [ ] 1.1 Implement independent current-execution and chronology states in the paired modules R07/R08 changes.
- [ ] 1.2 Implement the versioned B/R/H/D replay-capsule schema and validation contracts: core supplies Git/execution facts; modules validate schema/hash/transition/outcome facts without running Git or tests.
- [ ] 1.3 In modules PR #412, add `test_code_review_accepts_current_execution_without_tdd_chronology` in `tests/unit/specfact_code_review/run/test_commands.py` and a focused Requirements reconciliation regression proving a valid historical capsule cannot substitute for missing current execution. The adapter may retain both claims, but neither may calculate or rewrite the other claim's status.
- [ ] 1.4 Publish the paired Requirements payload through the modules repository release generators. Version `packages/specfact-requirements/module-package.yaml`, update `CHANGELOG.md` and `registry/index.json`, generate the versioned archive/checksum/signature under `registry/modules/` and `registry/signatures/`, and record immutable commit/tree, package/capsule-schema versions, manifest integrity, approved signing-key fingerprint or trust-root identity, signer/signature identities, and passing package/signature/registry verification evidence.

## 2. Failing tests first

- [ ] 2.1 In `tests/unit/scripts/test_requirements_proof_provenance.py`, replace obsolete static-closure cases with temporary-Git-repository tests for valid B < R < H <= D, exact D delivery binding, and invalid ancestry/identity.
- [ ] 2.2 In `tests/unit/scripts/test_requirements_proof_provenance.py`, add failing tests that reject every undeclared/disallowed B..R path or rename endpoint, every R..H non-implementation change, and every H..D path except exact mapped `TDD_EVIDENCE.md`/`CHANGE_VALIDATION.md` delivery evidence.
- [ ] 2.3 In exactly `tests/integration/scripts/test_requirements_red_green_replay.py`, add failing integration tests proving exact failure at R, exact pass at H, and retained exact pass at a distinct D under identical selectors.
- [ ] 2.4 In `tests/unit/scripts/test_requirements_proof_provenance.py`, add shallow-history, invalid-ref, checkout-failure, missing-artifact, and rename-endpoint cases; execution timeout and selector-mismatch cases may additionally use `tests/integration/scripts/test_requirements_red_green_replay.py`.
- [ ] 2.5 In `tests/unit/scripts/test_requirements_proof_provenance.py`, add a failing bootstrap test proving verifier/policy self-changes cannot self-attest.
- [ ] 2.6 In `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`, add `test_replay_capsule_requires_trusted_module_and_epoch`, rejecting an unreleased/mismatched signed-module identity, capsule schema, verifier epoch, missing/unknown approved public-key fingerprint, or missing/unknown trust-root reference before module import or chronology enforcement.
- [ ] 2.7 In `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`, add `test_current_run_pass_remains_valid_without_red_green_chronology` and `test_historical_capsule_cannot_substitute_for_missing_current_execution`. The first must pass with no chronology claim; the second must remain unresolved/non-pass when the current-run JUnit observation is absent even if chronology is valid.
- [ ] 2.8 In exactly `tests/integration/scripts/test_requirements_red_green_replay.py`, add `test_historical_replay_does_not_synthesize_current_execution`, proving successful B/R/H/D replay emits chronology facts only and cannot manufacture the independent delivered-head current-execution observation.
- [ ] 2.9 Before accepting R, update `requirements-evidence.yaml` under the paired released mapping schema: replace applicable planning-only inspection cases with exact executable test selectors, including the independence regressions in tasks 2.7 and 2.8; declare complete `red_setup_touchpoints`, implementation touchpoints, and exact delivery-evidence touchpoints; include this mapping and the governed `TDD_EVIDENCE.md` failing-before record in red setup; then freeze mapping, plan, selector, and path-set digests at R.
- [ ] 2.10 Before production edits and before accepting R, add the actual failing-before section to `TDD_EVIDENCE.md` with timestamps, exact commands/results, behavioral summary, environment limitations, and artifact identities. This file is an explicitly mapped B..R `failing_tdd_evidence` touchpoint and is frozen from R through H.

## 3. Minimal implementation

- [ ] 3.1 In `scripts/requirements_proof_provenance.py`, require explicit full-SHA B/R/H/D inputs plus complete declared `red_setup_touchpoints`, implementation touchpoints, and exact `delivery_evidence_touchpoints`. Validate D equals the current delivery head, H is its ancestor or equal, and every identity is full length; do not auto-discover R or substitute another green/delivery endpoint.
- [ ] 3.2 In `scripts/requirements_proof_provenance.py`, implement ancestry and all three closed B..R, R..H, and H..D changed-path/rename-endpoint validators. Do not parse Python AST.
- [ ] 3.3 In `scripts/requirements_proof_provenance.py`, implement isolated worktree replay for R, H, and distinct D with identical bounded subprocess arguments and enforced network-isolation evidence; reuse H as D only when the SHAs are equal. Change `scripts/requirements_proof_executor.py` only if the existing seam demonstrably cannot support explicit worktree/output inputs.
- [ ] 3.4 In `scripts/requirements_proof_provenance.py`, produce and schema-validate the versioned capsule before handing it to the signed Requirements module. Mandatory fields: B/R/H/D commit and tree identities; B..R, R..H, and H..D path/rename manifests and digests; mapping and plan digests; exact selector list; red, green-checkpoint, and delivery JUnit digests; runner, toolchain, dependency, environment, plugin, and network-policy identities/results; policy/verifier identities and epoch; timestamps and resource bounds; and signed module repository, commit, tree, package, manifest-integrity, approved signing-key fingerprint or trust-root, signer, and signature identities. Add focused tests that delete or alter each mandatory field and require `unproven`.
- [ ] 3.5 In `.github/workflows/requirements-evidence.yml` and `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`, validate the fixture's signing-key fingerprint or trust-root reference against the configured approved key set before module import and fail closed when missing/unknown; pass explicit B/R/H/D, bind D to the current delivery SHA, wire shadow mode, make unavailable network isolation unproven, and retain all artifacts before enforcement.
- [ ] 3.6 In `scripts/requirements_proof_provenance.py`, remove or bypass obsolete static pytest-input closure from the authoritative path; prefer deletion over parallel complexity.

## 4. Verification and rollout

- [ ] 4.1 Run the #665–#671 benchmark plus seeded invalid-history/path cases.
- [ ] 4.2 Run exactly `openspec validate requirements-08-bounded-red-green-proof --strict`, workflow lint, focused/full tests, contracts, static analysis, and explicit base/head Code Review; record the exact results under task B.5 and rerun the affected commands after every validation or evidence-artifact fix.
- [ ] 4.3 After implementation, add a separate passing-after section to `TDD_EVIDENCE.md` with timestamps, exact commands, actual results, behavioral summaries, environment limitations, and artifact identities.
- [ ] 4.4 Create or update `docs/guides/requirements-evidence.md` to distinguish `current_execution`, bounded `tdd_chronology`, `unproven`, bootstrap/shadow status, and remediation. Update `docs/index.md` and `docs/_layouts/default.html` only when needed to expose the guide, and regenerate `llms.txt` through the existing docs generator rather than hand-editing it.
- [ ] 4.5 Establish and document the initial reviewed verifier policy epoch.
- [ ] 4.6 Run shadow, warning, then strict rollout; record rollback instructions.
- [ ] 4.7 Merge the completed implementation to `dev` only after the paired signed module release is pinned and all gates pass.
- [ ] 4.8 After R07 is archived and the R08 strict rollout is accepted, from the repository root in a dedicated follow-up worktree run exactly `openspec archive requirements-08-bounded-red-green-proof` and verify the canonical bounded-replay specification. Do not move a directory into `openspec/changes/archive/` manually.
- [ ] 4.9 Merge checklist follow-up: create or update `wiki/sources/requirements-08-bounded-red-green-proof.md` (`depends-on`, `blocks`, `external-deps`, `status`, and summary) and run `python3 scripts/wiki_rebuild_graph.py` from the `specfact-cli-internal` repository root.
- [ ] 4.10 After each implementation or archive PR merges, remove its worktree, delete its local feature branch, run `git worktree prune`, and record the worktree-policy self-check.

## Prohibited shortcuts

- Do not cherry-pick PR #671.
- Do not add import, plugin, configuration, data-read, alias, mutation, namespace, symlink, or dynamic-execution inference.
- Do not reuse retained red artifacts in the strongest replay profile.
- Do not allow test/config/harness changes after R; require a new R.
- Do not emit pass/no-impact for missing or unresolved mandatory facts.
- Do not manually move directories into `openspec/changes/archive/`; use the exact repository-root archive command above.

## Closed implementation allowlist

Anything not listed here is prohibited unless this OpenSpec change is updated and accepted first.

Pre-red mapping and evidence records:

- `openspec/changes/requirements-08-bounded-red-green-proof/requirements-evidence.yaml`: before R only, add schema-accepted exact selectors plus complete red-setup, implementation, and delivery-evidence declarations; freeze its digest at R.
- `openspec/changes/requirements-08-bounded-red-green-proof/TDD_EVIDENCE.md`: failing-before section in B..R; frozen R..H; passing-after section only in H..D.
- `openspec/changes/requirements-08-bounded-red-green-proof/CHANGE_VALIDATION.md`: final implementation validation record only in H..D.

Production/configuration:

- `scripts/requirements_proof_provenance.py`: replace the existing static/AST closure with the small Git-only B/R/H/D validator, isolated replay orchestration, and attestation builder. Delete the old import/plugin/config/data-read rules; do not add a parallel provenance script.
- `.github/workflows/requirements-evidence.yml`: verify the fixture's approved signing-key/trust-root reference before module import; pass explicit B/R/H/D, bind D to the current delivery SHA, invoke shadow replay, retain red/green/delivery JUnit artifacts and attestation before enforcement, and enforce verifier-epoch bootstrap.
- `ci/module-fixture.lock.json`: signed R08-capable modules identity plus approved public-key fingerprint or trust-root reference only.
- `scripts/requirements_proof_executor.py`: conditional only when replay cannot use its current public seam; permit explicit worktree root/run-stage/output while preserving argv/environment safety.

Tests:

- `tests/unit/scripts/test_requirements_proof_provenance.py`: replace obsolete static-closure cases with B/R/H/D ancestry/delivery identity, three path-set, missing-history/artifact, rename, attestation, and bootstrap cases.
- New exactly `tests/integration/scripts/test_requirements_red_green_replay.py`: temporary-repository exact fail-at-R/pass-at-H/remain-pass-at-distinct-D replay, timeout, and selector mismatch.
- `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`: shadow wiring, artifacts-before-enforcement, and epoch bootstrap.
- `tests/unit/scripts/test_requirements_proof_executor.py`: conditional only when the executor changes.
- Temporary repositories live inside the named tests; no fixture directory.

Adoption documentation:

- `docs/guides/requirements-evidence.md`: canonical current-execution versus bounded-chronology guide; create if absent.
- `docs/index.md` and `docs/_layouts/default.html`: link/navigation only when the guide is otherwise undiscoverable.
- `llms.txt`: generated from accepted docs only through the existing generator; never hand-edit.

Paired modules dependency allowlist — separate repository `nold-ai/specfact-cli-modules`, implemented and reviewed in PR #412 rather than on this core branch:

- Requirements sources: new `packages/specfact-requirements/src/specfact_requirements/requirements/replay_proof.py`; `lifecycle.py`, `evidence.py`, and `commands.py`; `app.py`/`__init__.py` only for required command/export wiring.
- Focused tests: new `tests/unit/specfact_requirements/test_requirements_replay_proof.py`; `test_requirements_lifecycle.py`, `test_requirements_evidence.py`, and `tests/integration/specfact_requirements/test_command_apps.py`.
- Code Review provenance handoff, only if the capsule context changes: `packages/specfact-code-review/src/specfact_code_review/run/commands.py`, `findings.py`, and their focused `test_commands.py`/`test_findings.py` tests.
- Release/docs sources: `docs/bundles/requirements/overview.md`, `packages/specfact-requirements/module-package.yaml`, and `packages/specfact-code-review/module-package.yaml` only when its payload changes.
- Generated publication outputs, only through existing generators after behavior passes: `registry/index.json`, `registry/modules/specfact-requirements-<version>.tar.gz`, its `.sha256`, `registry/signatures/specfact-requirements-<version>.tar.sig`, `CHANGELOG.md`, and generated command/docs outputs required by module policy.
- The module validator must not run Git, pytest, subprocesses, or infer Python/pytest dependencies. No core file is authorized by this companion allowlist.

Explicitly forbidden:

- any new general pytest analyzer/provenance production file;
- `scripts/requirements_proof_pytest_plugin.py` unless its existing canonical-selector contract demonstrably fails;
- `scripts/requirements_evidence_delivery_gate.py`, `scripts/pre-commit-quality-checks.sh`, all `src/**`, and `tools/**`;
- security, dependency, safe-write, and smart-coverage paths, `pyproject.toml`, `uv.lock`, and unrelated tests.
