# Tasks: cli-val-02-output-snapshot-stability

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for any behavior-changing task. Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last. Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/cli-val-02-output-snapshot-stability -b feature/cli-val-02-output-snapshot-stability origin/dev`
  - [ ] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/cli-val-02-output-snapshot-stability`
  - [ ] 1.1.4 Create a virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify correct branch)

## 2. Spec-first preparation

- [ ] 2.1 Review and finalize `specs/output-snapshot-stability/spec.md` scenarios.
- [ ] 2.2 Inventory all existing command groups and their `--help` outputs for snapshot coverage planning.

## 3. Test-first: snapshot test structure

- [ ] 3.1 Add `syrupy` to dev dependencies in `pyproject.toml` (all relevant dependency sections).
- [ ] 3.2 Create `tests/snapshots/test_help_snapshots.py` with parametrized tests for all command `--help` outputs.
- [ ] 3.3 Create `tests/snapshots/test_output_snapshots.py` with tests for structured JSON/YAML outputs.
- [ ] 3.4 Create `tests/snapshots/test_error_snapshots.py` with tests for key error message templates.
- [ ] 3.5 Create normalization helpers for dynamic values (timestamps, paths, versions).
- [ ] 3.6 Run tests to generate initial snapshots; capture results in `TDD_EVIDENCE.md`.

## 4. Configuration and hatch integration

- [ ] 4.1 Add syrupy configuration to `pyproject.toml` (snapshot directory, serializer settings).
- [ ] 4.2 Add `snapshot-update` hatch script: `pytest tests/snapshots/ --snapshot-update`.
- [ ] 4.3 Add `snapshot-check` hatch script: `pytest tests/snapshots/` (fails on mismatch).
- [ ] 4.4 Verify all snapshots pass on clean run; record in `TDD_EVIDENCE.md`.

## 5. Quality gates and documentation

- [ ] 5.1 `hatch run format` — ruff format + autofix.
- [ ] 5.2 `hatch run type-check` — basedpyright strict.
- [ ] 5.3 `hatch run lint` — full lint suite.
- [ ] 5.4 `hatch run contract-test` — contract-first validation.
- [ ] 5.5 `hatch run smart-test` — targeted test run.
- [ ] 5.6 Update `docs/` with snapshot testing workflow guide for contributors.
- [ ] 5.7 Run `openspec validate cli-val-02-output-snapshot-stability --strict` and resolve all issues.

## 6. Version and changelog

- [ ] 6.1 Bump minor version in `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`.
- [ ] 6.2 Add CHANGELOG.md entry under new version section with `Added` items for snapshot testing.

## 7. Delivery

- [ ] 7.1 Update `openspec/CHANGE_ORDER.md` with implementation status.
- [ ] 7.2 Stage and commit: `git add . && git commit -m "feat: add output snapshot stability tests (cli-val-02)"`
- [ ] 7.3 Push: `git push -u origin feature/cli-val-02-output-snapshot-stability`
- [ ] 7.4 Create PR from `feature/cli-val-02-output-snapshot-stability` to `dev` using `gh pr create`.
- [ ] 7.5 Link PR to GitHub issue and project board.

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/cli-val-02-output-snapshot-stability`
- [ ] `git branch -d feature/cli-val-02-output-snapshot-stability`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/cli-val-02-output-snapshot-stability`
