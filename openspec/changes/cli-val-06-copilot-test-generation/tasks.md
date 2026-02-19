# Tasks: cli-val-06-copilot-test-generation

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, tests before code for any behavior-changing task. Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last. Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/cli-val-06-copilot-test-generation -b feature/cli-val-06-copilot-test-generation origin/dev`
  - [ ] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/cli-val-06-copilot-test-generation`
  - [ ] 1.1.4 Create a virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.5 `git branch --show-current` (verify correct branch)
  - [ ] 1.1.6 Verify cli-val-01 is merged into dev before starting.

## 2. Spec-first preparation

- [ ] 2.1 Review and finalize `specs/copilot-scenario-generation/spec.md` scenarios.
- [ ] 2.2 Review existing prompt templates in `resources/prompts/` for pattern alignment.

## 3. Test-first: template validation tests

- [ ] 3.1 Create `tests/unit/specfact_cli/test_cli_scenario_prompt.py` with tests for:
  - Prompt template renders valid YAML for a sample command
  - Rendered YAML validates against the cli-val-01 schema
  - Template detects CLI commands by scanning for `@app.command()` patterns
  - Anti-pattern generation covers required categories
- [ ] 3.2 Run tests and capture failing results in `TDD_EVIDENCE.md`.

## 4. Implementation: prompt template and workflow extension

- [ ] 4.1 Create `resources/prompts/cli-scenario-generation.j2` — Jinja2 template generating scenario YAML + anti-patterns + Markdown acceptance test.
- [ ] 4.2 Extend `specfact generate test-prompt` workflow to detect CLI commands and offer scenario template.
- [ ] 4.3 Re-run tests until passing; record in `TDD_EVIDENCE.md`.

## 5. Validation with example commands

- [ ] 5.1 Test template output against `backlog ceremony standup` command — verify generated YAML passes schema validation.
- [ ] 5.2 Test template output against `validate` command — verify file I/O scenarios are generated.
- [ ] 5.3 Test template output against a simple command — verify minimal scenario set is generated.

## 6. Quality gates and documentation

- [ ] 6.1 `hatch run format` — ruff format + autofix.
- [ ] 6.2 `hatch run type-check` — basedpyright strict.
- [ ] 6.3 `hatch run lint` — full lint suite.
- [ ] 6.4 `hatch run contract-test` — contract-first validation.
- [ ] 6.5 `hatch run smart-test` — targeted test run.
- [ ] 6.6 Add `docs/` page on copilot-driven CLI scenario authoring workflow.
- [ ] 6.7 Update contributor guide with convention: CLI command changes require scenario files.
- [ ] 6.8 Run `openspec validate cli-val-06-copilot-test-generation --strict` and resolve all issues.

## 7. Version and changelog

- [ ] 7.1 Bump minor version in `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`.
- [ ] 7.2 Add CHANGELOG.md entry under new version section with `Added` items for copilot scenario generation.

## 8. Delivery

- [ ] 8.1 Update `openspec/CHANGE_ORDER.md` with implementation status.
- [ ] 8.2 Stage and commit: `git add . && git commit -m "feat: add copilot CLI scenario generation (cli-val-06)"`
- [ ] 8.3 Push: `git push -u origin feature/cli-val-06-copilot-test-generation`
- [ ] 8.4 Create PR from `feature/cli-val-06-copilot-test-generation` to `dev` using `gh pr create`.
- [ ] 8.5 Link PR to GitHub issue and project board.

## Post-merge cleanup (after PR is merged)

- [ ] Return to primary checkout: `cd .../specfact-cli`
- [ ] `git fetch origin`
- [ ] `git worktree remove ../specfact-cli-worktrees/feature/cli-val-06-copilot-test-generation`
- [ ] `git branch -d feature/cli-val-06-copilot-test-generation`
- [ ] `git worktree prune`
- [ ] (Optional) `git push origin --delete feature/cli-val-06-copilot-test-generation`
