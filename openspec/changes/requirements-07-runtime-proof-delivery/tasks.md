# Tasks: Correct R07 to Current-Run Requirements Evidence

## 0. Planning-only scope reset

- [x] 0.1 Reframe R07 around issue #662 current-run acceptance criteria.
- [x] 0.2 Move historical failing-first chronology to R08.
- [x] 0.3 Record explicit non-goals prohibiting Python/pytest dependency-closure inference.
- [x] 0.4 Create this planning commit without runtime, workflow, fixture, test, or schema implementation changes.

## Implementation-session checklist — before any unchecked implementation task

- [ ] B.1 Create a dedicated implementation worktree and feature branch from current `origin/dev`; do not implement from the primary, `dev`, or `main` checkout.
- [ ] B.2 Run `hatch env create`, then `hatch run smart-test-status` and `hatch run contract-test-status` in the worktree; record and resolve unexpected baseline failures before edits.
- [ ] B.3 Read and apply `openspec/config.yaml` and its artifact rules. If the sibling `specfact-cli-internal` checkout exists, consult the applicable internal-wiki guidance. Record the sources and constraints used in `CHANGE_VALIDATION.md`. Then run exactly `openspec validate requirements-07-runtime-proof-delivery --strict`; require success before tests or source edits and rerun it after every validation-artifact fix. Confirm the accepted specs, dependencies, signed-module prerequisites, and closed file allowlist still match repository reality.
- [ ] B.4 Follow `spec -> tests -> failing evidence -> code -> passing evidence`; in `TDD_EVIDENCE.md`, record separate failing-before and passing-after sections with exact commands, timestamps, actual results, behavioral summaries, environment limitations, and artifact identities. Record passing evidence only after implementation.
- [ ] B.5 Before PR finalization, rerun exactly `openspec validate requirements-07-runtime-proof-delivery --strict` plus the required format, type, lint, YAML, contract, focused/full test, workflow, independent-analysis, signature, and explicit base/head Code Review gates. Update `CHANGE_VALIDATION.md` with validation scope/impact, affected files, exact commands, actual results and test counts, focused/full tests, skipped or unavailable tests/dependencies with reasons, artifact locations/identities, environment limitations, and release hygiene. Keep planning evidence, failing-before evidence, and passing-after evidence separate; rerun affected validation after every artifact fix and resolve every finding or document an approved exception.
- [ ] B.6 After each merge, remove the implementation worktree, delete its local feature branch, run `git worktree prune`, and complete an explicit `AGENTS.md` worktree/policy self-check. Archive only from a dedicated follow-up worktree when the stated release and observation gates are complete.

## 1. Modules dependency — each task at most two hours

- [ ] 1.1 In modules PR #412, add failing model tests separating `current_execution` from `red_green_chronology` using only the companion paths listed below.
- [ ] 1.2 In modules PR #412, update the Requirements reconciliation/report schema so current-run pass/fail can be final without historical proof; version the accepted report shape using only the companion paths listed below.
- [ ] 1.3 In modules PR #412, update the Code Review context adapter and its focused tests so `current_execution` is retained without requiring `proof_basis: "red-junit"`; preserve optional `red_green_chronology` as a separate field that cannot rewrite the review verdict.
- [ ] 1.4 Publish the paired module payloads through the repository release generators. Version module manifests, update `CHANGELOG.md`, `registry/index.json`, generated archives/checksums/signatures, and record immutable commit/tree, package/report-schema versions, manifest integrity, approved signing-key fingerprint or trust-root identity, signer/signature identities, and passing package/signature/registry verification evidence.

## 2. Core failing tests — tests before implementation, each task at most two hours

- [ ] 2.1 Add `test_current_run_pass_is_not_labelled_passing_after_red`. Allowed file: `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`.
- [ ] 2.2 Add `test_missing_historical_proof_retains_current_run_observation`. Allowed file: `tests/unit/scripts/test_requirements_evidence_delivery_gate.py`.
- [ ] 2.3 Add `test_unresolved_current_run_cannot_be_pass_or_no_impact`, covering missing scope, missing JUnit, timeout, and tool failure. Allowed file: `tests/unit/scripts/test_requirements_evidence_delivery_gate.py`.
- [ ] 2.4 Add `test_unverified_fixture_identity_fails_before_module_execution`, rejecting mismatched repository, commit, tree, package, report-schema, manifest-integrity, signature, clean-state identity, missing/unknown approved public-key fingerprint, or missing/unknown trust-root reference with field-specific diagnostics before module import. Allowed file: `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`.
- [ ] 2.5 Before any production edit, update `requirements-evidence.yaml` under the paired released mapping schema: convert `R07-CORE-009-S01` from inspection to `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py::test_current_run_pass_is_not_labelled_passing_after_red`, convert `R07-CORE-009-S02` from inspection to `tests/unit/scripts/test_requirements_evidence_delivery_gate.py::test_missing_historical_proof_retains_current_run_observation`, verify both exact selectors collect once, and freeze the accepted mapping and plan digests. Do not invent selectors on this planning-only branch.
- [ ] 2.6 Record the exact failing commands, timestamps, actual results, behavioral summaries, environment limitations, and artifact identities in the failing-before section of `TDD_EVIDENCE.md` before production edits.

## 3. Core implementation — each task at most two hours

- [ ] 3.1 Pin and verify the signed corrected modules repository commit/tree, package version, report-schema version, manifest integrity, signature, clean-state identity, and approved public-key fingerprint or trust-root reference before any module import or execution. Validate the key/trust reference against the repository's configured approved key set and fail closed when it is missing or unknown; retain field-specific mismatch diagnostics. Allowed files: `ci/module-fixture.lock.json` and the exact pre-execution fixture/signature assertion in `.github/workflows/requirements-evidence.yml` only.
- [ ] 3.2 Adapt current-run report handling without implementing chronology. Allowed files: `.github/workflows/requirements-evidence.yml` and `scripts/requirements_evidence_delivery_gate.py`; change `scripts/requirements_proof_executor.py` only when a named failing test proves field incompatibility.
- [ ] 3.3 Remove the R07 legacy-ledger/prior-red requirement from current-run enforcement in `.github/workflows/requirements-evidence.yml` and `scripts/requirements_evidence_delivery_gate.py`. Do not add replacement AST inference.
- [ ] 3.4 In `.github/workflows/requirements-evidence.yml`, keep Requirements and Code Review verdicts independent and publish both available artifacts before terminal enforcement.

## 4. Verification and delivery

- [ ] 4.1 Run focused tests, exactly `openspec validate requirements-07-runtime-proof-delivery --strict`, workflow lint, type/lint/contract checks, and full Code Review with explicit base/head scope; record the exact results under task B.5 and rerun the affected commands after every validation or evidence-artifact fix.
- [ ] 4.2 After implementation, add a separate passing-after section to `TDD_EVIDENCE.md` with timestamps, exact commands, actual results, behavioral summaries, environment limitations, and artifact identities.
- [ ] 4.3 Create or update `docs/guides/requirements-evidence.md` to distinguish current-run evidence from bounded historical proof; update `docs/index.md` and `docs/_layouts/default.html` only when needed to expose the guide, and regenerate `llms.txt` through the existing docs generator rather than hand-editing it.
- [ ] 4.4 Merge the completed implementation to `dev`; do not archive R07 until the correction is released and observed for one delivery cycle.
- [ ] 4.5 Before archiving R07, from the repository root in a disposable verification worktree run exactly `openspec archive requirements-06-evidence-enforcement`, then verify this exact-name `MODIFIED` delta leaves one canonical delivery-gate requirement rather than a duplicate. Do not move an OpenSpec directory manually.
- [ ] 4.6 After the correction is released and observed for one delivery cycle, from the repository root in a dedicated follow-up worktree run exactly `openspec archive requirements-07-runtime-proof-delivery` and verify the canonical delivery-gate requirement remains singular. Do not move a directory into `openspec/changes/archive/` manually.
- [ ] 4.7 Merge checklist follow-up: update `wiki/sources/requirements-07-runtime-proof-delivery.md` (`depends-on`, `blocks`, `external-deps`, `status`, and summary) and run `python3 scripts/wiki_rebuild_graph.py` from the `specfact-cli-internal` repository root.
- [ ] 4.8 After each implementation or archive PR merges, remove its worktree, delete its local feature branch, run `git worktree prune`, and record the worktree-policy self-check.

## Prohibited shortcuts

- Do not cherry-pick or merge PR #671.
- Do not add AST rules for imports, plugins, configuration, data files, aliases, mutations, namespaces, symlinks, or dynamic execution.
- Do not mark a skipped, failed, unresolved, or missing tool result as pass/no-impact.
- Do not modify unrelated security, dependency-trust, safe-write, or smart-coverage tooling.
- Do not manually move directories into `openspec/changes/archive/`; use the exact repository-root `openspec archive <change-id>` commands above.

## Closed implementation allowlist

Anything not listed here is prohibited unless this OpenSpec change is updated and accepted first.

OpenSpec mapping and evidence records:

- `openspec/changes/requirements-07-runtime-proof-delivery/requirements-evidence.yaml`: before production edits only, convert `R07-CORE-009-S01` and `R07-CORE-009-S02` to the exact selectors named in task 2.5 and freeze the accepted mapping/plan digests.
- `openspec/changes/requirements-07-runtime-proof-delivery/TDD_EVIDENCE.md`: add failing-before evidence after the named tests fail and before production edits; add a separate passing-after section only after implementation passes.
- `openspec/changes/requirements-07-runtime-proof-delivery/CHANGE_VALIDATION.md`: final corrected implementation validation only after the implementation and all required gates complete.

Production/configuration:

- `ci/module-fixture.lock.json`: signed modules repository/commit/tree/package/report-schema identities plus the approved public-key fingerprint or trust-root reference only.
- `scripts/requirements_evidence_delivery_gate.py`: adapt request/report fields for independent `current_execution`; no chronology or Git-history logic.
- `.github/workflows/requirements-evidence.yml`: remove retained-run discovery/download and legacy-ledger/prior-red branches; verify the fixture's approved signing-key/trust-root reference before module import; consume, publish, and enforce current-run evidence plus explicit PR review paths.
- `scripts/requirements_proof_executor.py`: conditional only when a named failing test proves schema incompatibility; plan/result field adaptation only.

Tests:

- `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`.
- `tests/unit/scripts/test_requirements_evidence_delivery_gate.py`.
- `tests/unit/scripts/test_requirements_proof_executor.py`: conditional only when the executor changes.
- No new R07 test module.

Adoption documentation:

- `docs/guides/requirements-evidence.md`: canonical current-execution versus chronology guide; create if absent.
- `docs/index.md` and `docs/_layouts/default.html`: link/navigation only when the new guide is otherwise undiscoverable.
- `llms.txt`: generated from accepted docs only through the existing generator; never hand-edit.

Paired modules dependency allowlist — separate repository `nold-ai/specfact-cli-modules`, implemented and reviewed in PR #412 rather than on this core branch:

- Requirements sources: `packages/specfact-requirements/src/specfact_requirements/requirements/lifecycle.py`, `evidence.py`, `commands.py`, new `replay_proof.py`, and `__init__.py` only for intentional exports.
- Code Review handoff sources: `packages/specfact-code-review/src/specfact_code_review/run/commands.py` and `findings.py` only.
- Focused tests: `tests/unit/specfact_requirements/test_requirements_lifecycle.py`, new `test_requirements_replay_proof.py`, `test_requirements_evidence.py`, `tests/integration/specfact_requirements/test_command_apps.py`, `tests/unit/specfact_code_review/run/test_commands.py`, and `test_findings.py`.
- Release/docs sources: `docs/bundles/requirements/overview.md`, `packages/specfact-requirements/module-package.yaml`, and `packages/specfact-code-review/module-package.yaml` only when its proof-context payload changes.
- Generated publication outputs, only through existing generators after behavior passes: `registry/index.json`, `registry/modules/specfact-requirements-<version>.tar.gz`, its `.sha256`, `registry/signatures/specfact-requirements-<version>.tar.sig`, and equivalent Code Review artifacts when that payload changes; include `CHANGELOG.md` and generated command docs required by module policy.
- No core implementation file is authorized by this companion allowlist, and no companion file is authorized by the core allowlist above.

Explicitly forbidden:

- `scripts/requirements_proof_provenance.py`, `scripts/requirements_proof_pytest_plugin.py`, and `scripts/pre-commit-quality-checks.sh`;
- all `src/**`, `tools/**`, security, dependency, safe-write, and smart-coverage paths;
- `pyproject.toml`, `uv.lock`, and unrelated tests.
