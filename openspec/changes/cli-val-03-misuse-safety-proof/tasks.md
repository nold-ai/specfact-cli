# Tasks: cli-val-03-misuse-safety-proof

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for any behavior-changing task. Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last. Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/cli-val-03-misuse-safety-proof -b feature/cli-val-03-misuse-safety-proof origin/dev`
  - [ ] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/cli-val-03-misuse-safety-proof`
  - [ ] 1.1.4 Create a virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify correct branch)
  - [ ] 1.1.6 Verify cli-val-01 is merged into dev before starting.

## 2. Spec-first preparation

- [ ] 2.1 Review and finalize `specs/misuse-safety-proof/spec.md` scenarios.
- [ ] 2.2 Inventory all Wave 1 command groups and their argument signatures for anti-pattern coverage.

## 3. Anti-pattern catalog creation

- [ ] 3.1 Create anti-pattern YAML scenarios for each Wave 1 command group in `tests/cli-contracts/`:
  - `backlog-ceremony-standup.scenarios.yaml` (extend with anti-patterns)
  - `validate.scenarios.yaml` (extend with anti-patterns)
  - Additional command groups as identified in 2.2
- [ ] 3.2 Ensure each command group has at least 3 anti-pattern scenarios covering: missing args, invalid flags, bad paths.

## 4. Test-first: safety assertion suite

- [ ] 4.1 Create `tests/unit/specfact_cli/test_cli_misuse_safety.py` with:
  - Reusable three-property assertion helper (exit code, error message, filesystem)
  - Parametrized tests loading anti-patterns from YAML scenario files
  - Traceback-absence assertion for non-debug mode
- [ ] 4.2 Create `tests/unit/specfact_cli/test_cli_hypothesis_fuzz.py` with:
  - Hypothesis strategies for invalid enum values
  - Hypothesis strategies for path edge cases (Unicode, spaces, empty, deeply nested)
  - Bounded settings (`max_examples=50`, `deadline=30s`)
- [ ] 4.3 Run tests and capture results in `TDD_EVIDENCE.md` (expect some failures from discovered bugs).

## 5. Bug triage and documentation

- [ ] 5.1 Document any production bugs discovered during anti-pattern testing as separate GitHub issues.
- [ ] 5.2 For each discovered bug, add a `# Known issue: #NNN` comment in the anti-pattern scenario.

## 6. Quality gates and documentation

- [ ] 6.1 `hatch run format` — ruff format + autofix.
- [ ] 6.2 `hatch run type-check` — basedpyright strict.
- [ ] 6.3 `hatch run lint` — full lint suite.
- [ ] 6.4 `hatch run contract-test` — contract-first validation.
- [ ] 6.5 `hatch run smart-test` — targeted test run.
- [ ] 6.6 Update `docs/` with anti-pattern authoring guide for contributors.
- [ ] 6.7 Run `openspec validate cli-val-03-misuse-safety-proof --strict` and resolve all issues.

## 7. Version and changelog

- [ ] 7.1 Bump minor version in `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`.
- [ ] 7.2 Add CHANGELOG.md entry under new version section with `Added` items for misuse safety proof.

## 8. Delivery

- [ ] 8.1 Update `openspec/CHANGE_ORDER.md` with implementation status.
- [ ] 8.2 Stage and commit: `git add . && git commit -m "feat: add misuse safety proof tests (cli-val-03)"`
- [ ] 8.3 Push: `git push -u origin feature/cli-val-03-misuse-safety-proof`
- [ ] 8.4 Create PR from `feature/cli-val-03-misuse-safety-proof` to `dev` using `gh pr create`.
- [ ] 8.5 Link PR to GitHub issue and project board.

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/cli-val-03-misuse-safety-proof`
- [ ] `git branch -d feature/cli-val-03-misuse-safety-proof`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/cli-val-03-misuse-safety-proof`
