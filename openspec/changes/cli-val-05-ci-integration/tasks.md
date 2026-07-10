# Tasks: cli-val-05-ci-integration

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for any behavior-changing task. Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last. Do not implement workflow or tooling changes until tests exist and have been run expecting failure.

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/cli-val-05-ci-integration -b feature/cli-val-05-ci-integration origin/dev`
  - [ ] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/cli-val-05-ci-integration`
  - [ ] 1.1.4 Bootstrap Hatch environment: `hatch env create`
  - [ ] 1.1.5 Run pre-flight checks: `hatch run smart-test-status`
  - [ ] 1.1.6 Run pre-flight checks: `hatch run contract-test-status`
  - [ ] 1.1.7 `git branch --show-current` (verify correct branch)

## 2. Spec-first preparation

- [x] 2.1 Add spec deltas for CI gates, release parity, package runtime matrix, property tests, and mutation baseline.
- [x] 2.2 Update `cli-val-04-acceptance-test-runner` design/spec to require built-wheel black-box execution.
- [x] 2.3 Update internal wiki source pages for material scope changes and run `wiki_rebuild_graph.py`.
- [x] 2.4 Add a `documentation-accountability` spec delta covering source-of-truth derivation, catalogue completeness, ownership/handoff consistency, and fail-closed local/PR enforcement.

## 3. Test-first: workflow and correctness tests

- [x] 3.1 Add workflow policy tests proving `Quality Gates` is blocking and enforces `fail_under`.
- [x] 3.2 Add workflow policy tests proving independent Semgrep/Bandit job exists and package runtime matrix builds and installs a wheel.
- [x] 3.3 Add workflow policy tests proving release PR fast-path and direct-to-`main` PRs still run strict signature, package validation, version sync, and wheel smoke.
- [x] 3.4 Add Hypothesis property tests for dependency resolver, module installer dependency specs, version satisfaction, malformed manifests, registry identity helpers, and circular-dependency/self-reference surfaces.
- [x] 3.5 Add upgrade/version-detection regression coverage for upgrade path selection, stale launcher repair, and metadata persistence failure handling.
- [x] 3.6 Run focused dependency and upgrade/version tests and record failing-before output in `TDD_EVIDENCE.md`.
- [x] 3.7 Add failing tests proving a requirements-module omission, an incomplete generated command inventory, an incorrect core ownership claim, and an unavailable modules source each fail the accountability contract.
- [x] 3.8 Run the documentation-accountability tests before implementation and record the failing output in `TDD_EVIDENCE.md`.

## 4. Implementation

- [x] 4.1 Update `pr-orchestrator.yml` with blocking coverage, independent static analysis, package runtime matrix, macOS smoke, Windows scheduled/manual smoke, release-safety checks, and mutation baseline.
- [x] 4.2 Update smart-test full-suite threshold handling so full runs enforce coverage threshold.
- [x] 4.3 Add Hatch scripts/config for mutation baseline where needed.
- [x] 4.4 Add or adjust helper code only where required by property tests.
- [x] 4.5 Implement an authoritative official-module inventory loader and documentation-accountability checker; remove the stale five-package command-mount assumptions from generated-command and command-contract validation.
- [x] 4.6 Run the accountability gate from the always-run local pre-commit path and the required PR CI path; make checkout/source-resolution failures blocking.
- [x] 4.7 Correct every identified core catalogue, generated command artifact, and architecture/ownership statement; preserve the current explicit-opt-in requirements profile behavior.

## 5. Passing evidence and quality gates

- [x] 5.1 Re-run focused tests and record passing output in `TDD_EVIDENCE.md`.
- [x] 5.2 Run `openspec validate cli-val-05-ci-integration --strict`.
- [x] 5.3 Run workflow/policy tests for changed CI surfaces.
- [x] 5.4 Run `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, and `hatch run smart-test` as practical for the touched scope.
- [x] 5.5 Run or document `hatch run specfact code review run --json --out .specfact/code-review.json` and resolve findings.
- [x] 5.6 Run the documentation-accountability command directly, through pre-commit, and through focused workflow-policy tests; record passing evidence in `TDD_EVIDENCE.md`.

## 6. Documentation and delivery

- [x] 6.1 Update affected docs/README guidance for required vs advisory CI gates.
- [x] 6.1.1 Update contributor documentation to explain the fail-closed documentation-accountability gate, its modules-repository prerequisite, and the core/modules ownership responsibilities.
- [x] 6.2 Update version/changelog if required by release policy.
- [ ] 6.3 Stage and commit: `git add . && git commit -m "feat: harden PR runtime validation gates"`
- [ ] 6.4 Push and create PR from `feature/cli-val-05-ci-integration` to `dev`.

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/cli-val-05-ci-integration`
- [ ] `git branch -d feature/cli-val-05-ci-integration`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/cli-val-05-ci-integration`
