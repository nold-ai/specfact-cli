# Tasks: cli-val-01-behavior-contract-standard

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for any behavior-changing task. Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last. Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/cli-val-01-behavior-contract-standard -b feature/cli-val-01-behavior-contract-standard origin/dev`
  - [ ] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/cli-val-01-behavior-contract-standard`
  - [ ] 1.1.4 Create a virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify correct branch)

## 2. Spec-first preparation

- [ ] 2.1 Review and finalize `specs/cli-behavior-contracts/spec.md` scenarios.
- [ ] 2.2 Cross-check scenarios against existing CliRunner test patterns in `tests/` for completeness.

## 3. Test-first: schema validation tests

- [ ] 3.1 Create `tests/unit/specfact_cli/test_cli_contract_schema.py` with tests for:
  - Schema validates well-formed YAML
  - Schema rejects missing required fields
  - Schema distinguishes patterns from anti-patterns
  - Validation tool reports errors with file/line context
- [ ] 3.2 Run tests and capture failing results in `TDD_EVIDENCE.md`.

## 4. Implementation: schema and validation tool

- [ ] 4.1 Create `tests/cli-contracts/schema/cli-scenario.schema.yaml` — the JSON Schema for scenario files.
- [ ] 4.2 Create `tools/validate_cli_contracts.py` — validates scenario YAML against schema, reports errors with context.
- [ ] 4.3 Add `validate-cli-contracts` script to `pyproject.toml` hatch scripts.
- [ ] 4.4 Re-run tests until passing; record in `TDD_EVIDENCE.md`.

## 5. Pilot scenario files

- [ ] 5.1 Create `tests/cli-contracts/backlog-ceremony-standup.scenarios.yaml` — command with multiple args, 3+ patterns and 3+ anti-patterns.
- [ ] 5.2 Create `tests/cli-contracts/validate.scenarios.yaml` — command with file I/O, filesystem expectations.
- [ ] 5.3 Create `tests/cli-contracts/root-help.scenarios.yaml` — simple `--help`/`--version` scenarios.
- [ ] 5.4 Run schema validation tool against all pilot files; fix issues.

## 6. Quality gates and documentation

- [ ] 6.1 `hatch run format` — ruff format + autofix.
- [ ] 6.2 `hatch run type-check` — basedpyright strict.
- [ ] 6.3 `hatch run lint` — full lint suite.
- [ ] 6.4 `hatch run contract-test` — contract-first validation.
- [ ] 6.5 `hatch run smart-test` — targeted test run.
- [ ] 6.6 Update `docs/` with a page describing the CLI behavior contract format and authoring guidelines.
- [ ] 6.7 Run `openspec validate cli-val-01-behavior-contract-standard --strict` and resolve all issues.

## 7. Version and changelog

- [ ] 7.1 Bump minor version in `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`.
- [ ] 7.2 Add CHANGELOG.md entry under new version section with `Added` items for CLI behavior contract standard.

## 8. Delivery

- [ ] 8.1 Update `openspec/CHANGE_ORDER.md` with implementation status.
- [ ] 8.2 Stage and commit: `git add . && git commit -m "feat: add CLI behavior contract standard (cli-val-01)"`
- [ ] 8.3 Push: `git push -u origin feature/cli-val-01-behavior-contract-standard`
- [ ] 8.4 Create PR from `feature/cli-val-01-behavior-contract-standard` to `dev` using `gh pr create`.
- [ ] 8.5 Link PR to GitHub issue and project board.

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/cli-val-01-behavior-contract-standard`
- [ ] `git branch -d feature/cli-val-01-behavior-contract-standard`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/cli-val-01-behavior-contract-standard`
