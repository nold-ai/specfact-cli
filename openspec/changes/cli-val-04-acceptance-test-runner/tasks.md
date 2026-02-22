# Tasks: cli-val-04-acceptance-test-runner

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for any behavior-changing task. Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last. Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/cli-val-04-acceptance-test-runner -b feature/cli-val-04-acceptance-test-runner origin/dev`
  - [ ] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/cli-val-04-acceptance-test-runner`
  - [ ] 1.1.4 Create a virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify correct branch)
  - [ ] 1.1.6 Verify cli-val-01 and cli-val-03 are merged into dev before starting.

## 2. Spec-first preparation

- [ ] 2.1 Review and finalize `specs/acceptance-test-runner/spec.md` scenarios.
- [ ] 2.2 Verify cli-val-01 scenario files and cli-val-03 anti-patterns are available in the worktree.

## 3. Test-first: runner tests

- [ ] 3.1 Create `tests/unit/tools/test_cli_acceptance_runner.py` with tests for:
  - YAML scenario loading and parsing
  - Fast path (CliRunner) execution and assertion
  - Black-box path (subprocess) execution and assertion
  - Filesystem diff verification
  - Context setup (empty-repo, sample-bundle, initialized-project)
- [ ] 3.2 Run tests and capture failing results in `TDD_EVIDENCE.md`.

## 4. Implementation: dual-path runner

- [ ] 4.1 Create `tools/cli_acceptance_runner.py` — scenario loader, dual-path executor, assertion engine.
- [ ] 4.2 Implement workspace context factory (empty-repo, sample-bundle, initialized-project fixtures).
- [ ] 4.3 Create `tests/e2e/test_cli_acceptance.py` — pytest integration wiring scenarios to test cases.
- [ ] 4.4 Add `@pytest.mark.blackbox` marker to `pyproject.toml` markers list.
- [ ] 4.5 Add hatch scripts: `cli-acceptance-fast` (CliRunner path) and `cli-acceptance-blackbox` (subprocess path).
- [ ] 4.6 Re-run tests until passing; record in `TDD_EVIDENCE.md`.

## 5. Flagship command chain tests

- [ ] 5.1 Create `tests/e2e/test_cli_chain_init.py` — init workflow end-to-end test.
- [ ] 5.2 Create `tests/e2e/test_cli_chain_validate.py` — validate workflow end-to-end test.
- [ ] 5.3 Create `tests/e2e/test_cli_chain_help.py` — help and version end-to-end test.
- [ ] 5.4 Verify all flagship tests pass in both fast and black-box modes.

## 6. Quality gates and documentation

- [ ] 6.1 `hatch run format` — ruff format + autofix.
- [ ] 6.2 `hatch run type-check` — basedpyright strict.
- [ ] 6.3 `hatch run lint` — full lint suite.
- [ ] 6.4 `hatch run contract-test` — contract-first validation.
- [ ] 6.5 `hatch run smart-test` — targeted test run.
- [ ] 6.6 Update `docs/` with acceptance test workflow guide.
- [ ] 6.7 Run `openspec validate cli-val-04-acceptance-test-runner --strict` and resolve all issues.

## 7. Version and changelog

- [ ] 7.1 Bump minor version in `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`.
- [ ] 7.2 Add CHANGELOG.md entry under new version section with `Added` items for acceptance test runner.

## 8. Delivery

- [ ] 8.1 Update `openspec/CHANGE_ORDER.md` with implementation status.
- [ ] 8.2 Stage and commit: `git add . && git commit -m "feat: add CLI acceptance test runner (cli-val-04)"`
- [ ] 8.3 Push: `git push -u origin feature/cli-val-04-acceptance-test-runner`
- [ ] 8.4 Create PR from `feature/cli-val-04-acceptance-test-runner` to `dev` using `gh pr create`.
- [ ] 8.5 Link PR to GitHub issue and project board.

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/cli-val-04-acceptance-test-runner`
- [ ] `git branch -d feature/cli-val-04-acceptance-test-runner`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/cli-val-04-acceptance-test-runner`
