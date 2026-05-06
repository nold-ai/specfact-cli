# Tasks: cli-val-05-ci-integration

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for any behavior-changing task. Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last. Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/cli-val-05-ci-integration -b feature/cli-val-05-ci-integration origin/dev`
  - [ ] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/cli-val-05-ci-integration`
  - [ ] 1.1.4 Create a virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify correct branch)
  - [ ] 1.1.6 Verify cli-val-02 and cli-val-04 are merged into dev before starting.

## 2. Spec-first preparation

- [ ] 2.1 Review and finalize `specs/cli-validation-ci-gates/spec.md` scenarios.
- [ ] 2.2 Review current `pr-orchestrator.yml` job structure for integration points.

## 3. Test-first: CI gate validation

- [ ] 3.1 Create `tests/unit/tools/test_cli_validation_ci.py` with tests for:
  - Contract-test tier extension recognizes CLI behavior contracts
  - Combined CLI validation hatch script runs all tiers
- [ ] 3.2 Run tests and capture failing results in `TDD_EVIDENCE.md`.

## 4. Implementation: CI workflow changes

- [ ] 4.1 Add snapshot validation step to `tests` job in `.github/workflows/pr-orchestrator.yml`:
  - Run `hatch run snapshot-check` (from cli-val-02)
  - Fail on mismatch (hard gate)
- [ ] 4.2 Add anti-pattern safety step to `tests` job:
  - Run `hatch run cli-acceptance-fast` for anti-pattern validation
  - Fail on safety violations (hard gate)
- [ ] 4.3 Add Hypothesis fuzz step to `tests` job:
  - Run Hypothesis tests
  - Continue on error (advisory gate)
  - Post warning annotation
- [ ] 4.4 Add `cli-acceptance` job to `pr-orchestrator.yml`:
  - Build wheel: `hatch build`
  - Install wheel: `pip install dist/*.whl`
  - Run black-box acceptance: `hatch run cli-acceptance-blackbox`
  - Hard gate on failure
- [ ] 4.5 Create `.github/workflows/snapshot-update.yml` — manual workflow_dispatch for updating snapshots.
- [ ] 4.6 Re-run tests until passing; record in `TDD_EVIDENCE.md`.

## 5. Contract-test tier extension

- [ ] 5.1 Extend `tools/contract_first_smart_test.py` to include CLI behavior contracts as a new tier.
- [ ] 5.2 Add `cli-validation` hatch script that runs snapshot check + acceptance fast path + anti-pattern suite.
- [ ] 5.3 Verify `hatch run contract-test` now includes the CLI validation tier.

## 6. Quality gates and documentation

- [ ] 6.1 `hatch run format` — ruff format + autofix.
- [ ] 6.2 `hatch run type-check` — basedpyright strict.
- [ ] 6.3 `hatch run lint` — full lint suite.
- [ ] 6.4 `hatch run contract-test` — contract-first validation.
- [ ] 6.5 `hatch run smart-test` — targeted test run.
- [ ] 6.6 Update `docs/` with CI validation gates documentation and snapshot update guide.
- [ ] 6.7 Run `openspec validate cli-val-05-ci-integration --strict` and resolve all issues.

## 7. Version and changelog

- [ ] 7.1 Bump minor version in `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`.
- [ ] 7.2 Add CHANGELOG.md entry under new version section with `Added` items for CI validation gates.

## 8. Delivery

- [ ] 8.1 Update `openspec/CHANGE_ORDER.md` with implementation status.
- [ ] 8.2 Stage and commit: `git add . && git commit -m "feat: add CLI validation CI gates (cli-val-05)"`
- [ ] 8.3 Push: `git push -u origin feature/cli-val-05-ci-integration`
- [ ] 8.4 Create PR from `feature/cli-val-05-ci-integration` to `dev` using `gh pr create`.
- [ ] 8.5 Link PR to GitHub issue and project board.

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/cli-val-05-ci-integration`
- [ ] `git branch -d feature/cli-val-05-ci-integration`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/cli-val-05-ci-integration`
