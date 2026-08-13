# Tasks: Correct R07 to Current-Run Requirements Evidence

## 0. Planning-only scope reset

- [x] 0.1 Reframe R07 around issue #662 current-run acceptance criteria.
- [x] 0.2 Move historical failing-first chronology to R08.
- [x] 0.3 Record explicit non-goals prohibiting Python/pytest dependency-closure inference.
- [x] 0.4 Create this planning commit without runtime, workflow, fixture, test, or schema implementation changes.

## 1. Modules dependency — each task at most two hours

- [ ] 1.1 In the paired modules branch, add failing model tests separating `current_execution` from `red_green_chronology`. Allowed files: the Requirements lifecycle model and its focused tests.
- [ ] 1.2 Update the module reconciliation schema so current-run pass/fail can be final without historical proof. Allowed files: Requirements report/reconciliation models and focused tests.
- [ ] 1.3 Update Code Review context validation to accept finalized current-run evidence without requiring a historical proof basis. Allowed files: review context adapter and focused tests.
- [ ] 1.4 Publish a signed modules release and record its immutable commit and package versions.

## 2. Core failing tests — tests before implementation, each task at most two hours

- [ ] 2.1 Add `test_current_run_pass_is_not_labelled_passing_after_red`. Allowed file: `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`.
- [ ] 2.2 Add `test_missing_historical_proof_retains_current_run_observation`. Allowed file: `tests/unit/scripts/test_requirements_evidence_delivery_gate.py`.
- [ ] 2.3 Add `test_unresolved_current_run_cannot_be_pass_or_no_impact`, covering missing scope, missing JUnit, timeout, and tool failure. Allowed file: `tests/unit/scripts/test_requirements_evidence_delivery_gate.py`.
- [ ] 2.4 Record the exact failing commands and expected failures in `TDD_EVIDENCE.md` before production edits.

## 3. Core implementation — each task at most two hours

- [ ] 3.1 Pin the signed corrected modules release. Allowed file: `ci/module-fixture.lock.json` and its exact fixture assertion only.
- [ ] 3.2 Adapt current-run report handling without implementing chronology. Allowed files: `.github/workflows/requirements-evidence.yml` and one existing small delivery adapter if necessary.
- [ ] 3.3 Remove the R07 legacy-ledger/prior-red requirement from current-run enforcement. Do not add replacement AST inference.
- [ ] 3.4 Keep Requirements and Code Review verdicts independent and publish both artifacts before enforcement.

## 4. Verification and delivery

- [ ] 4.1 Run focused tests, strict OpenSpec validation, workflow lint, type/lint/contract checks, and full Code Review with explicit base/head scope.
- [ ] 4.2 Update `TDD_EVIDENCE.md` with passing commands and artifact identities.
- [ ] 4.3 Update user documentation to distinguish current-run evidence from bounded historical proof.
- [ ] 4.4 Merge the completed implementation to `dev`; do not archive R07 until the correction is released and observed for one delivery cycle.
- [ ] 4.5 Before archiving R07, archive `requirements-06-evidence-enforcement` with the OpenSpec CLI in a disposable verification checkout, then verify this exact-name `MODIFIED` delta leaves one canonical delivery-gate requirement rather than a duplicate.
- [ ] 4.6 Merge checklist follow-up: update `wiki/sources/requirements-07-runtime-proof-delivery.md` (`depends-on`, `blocks`, `external-deps`, `status`, and summary) and run `python3 scripts/wiki_rebuild_graph.py` from the `specfact-cli-internal` repository root.

## Prohibited shortcuts

- Do not cherry-pick or merge PR #671.
- Do not add AST rules for imports, plugins, configuration, data files, aliases, mutations, namespaces, symlinks, or dynamic execution.
- Do not mark a skipped, failed, unresolved, or missing tool result as pass/no-impact.
- Do not modify unrelated security, dependency-trust, safe-write, or smart-coverage tooling.

## Closed implementation allowlist

Anything not listed here is prohibited unless this OpenSpec change is updated and accepted first.

Production/configuration:

- `ci/module-fixture.lock.json`: signed modules repository/commit/tree/package identities only.
- `scripts/requirements_evidence_delivery_gate.py`: adapt request/report fields for independent `current_execution`; no chronology or Git-history logic.
- `.github/workflows/requirements-evidence.yml`: remove retained-run discovery/download and legacy-ledger/prior-red branches; consume, publish, and enforce current-run evidence plus explicit PR review paths.
- `scripts/requirements_proof_executor.py`: conditional only when a named failing test proves schema incompatibility; plan/result field adaptation only.

Tests:

- `tests/unit/workflows/test_requirements_evidence_delivery_workflow.py`.
- `tests/unit/scripts/test_requirements_evidence_delivery_gate.py`.
- `tests/unit/scripts/test_requirements_proof_executor.py`: conditional only when the executor changes.
- No new R07 test module.

Explicitly forbidden:

- `scripts/requirements_proof_provenance.py`, `scripts/requirements_proof_pytest_plugin.py`, and `scripts/pre-commit-quality-checks.sh`;
- all `src/**`, `tools/**`, security, dependency, safe-write, and smart-coverage paths;
- `pyproject.toml`, `uv.lock`, and unrelated tests.
