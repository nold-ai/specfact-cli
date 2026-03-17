# Tasks: specfact-code-review Module Scaffold

## TDD / SDD order (enforced)

Per `openspec/config.yaml`: tests before code for any behavior-changing task.
Order: (1) Spec deltas, (2) Tests from scenarios (expect failure), (3) Code last.
Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [x] 1.1 Fetch latest and create a worktree with a new branch from `origin/dev`.
  - [x] 1.1.1 `git fetch origin`
  - [x] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-01-module-scaffold -b feature/code-review-01-module-scaffold origin/dev`
  - [x] 1.1.3 Change into the worktree: `cd ../specfact-cli-worktrees/feature/code-review-01-module-scaffold`
  - [x] 1.1.4 Create virtual environment: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [x] 1.1.5 `git branch --show-current` (verify `feature/code-review-01-module-scaffold`)

## 2. Set up specfact-cli-modules worktree and package scaffold

All following tasks run inside the worktree **and** require the `specfact-cli-modules` repository to be accessible.

- [x] 2.1 In `specfact-cli-modules`: create `packages/specfact-code-review/` directory structure
  - [x] 2.1.1 Create all directories per module package structure (see design.md)
  - [x] 2.1.2 Write `packages/specfact-code-review/module-package.yaml` with all required fields

## 3. Write tests BEFORE implementation (TDD-first)

- [x] 3.1 Write `tests/unit/specfact_code_review/run/test_findings.py`
  - [x] 3.1.1 Test `ReviewFinding` field validation (valid/invalid severity, valid/invalid category)
  - [x] 3.1.2 Test `fixable` field defaults to `False`
  - [x] 3.1.3 Test `@require` contract on empty file/message
- [x] 3.2 Write `tests/unit/specfact_code_review/run/test_scorer.py`
  - [x] 3.2.1 Test clean run (zero findings) scores 100, reward_delta=20
  - [x] 3.2.2 Test single blocking error: score=85, reward_delta=5
  - [x] 3.2.3 Test single fixable error: score=95, reward_delta=15
  - [x] 3.2.4 Test warning deductions: 3 warnings → score=94
  - [x] 3.2.5 Test PASS/WARN/BLOCK verdict thresholds
  - [x] 3.2.6 Test all 5 bonus conditions
  - [x] 3.2.7 Test blocking error overrides score to FAIL regardless
  - [x] 3.2.8 Test score is capped at 120
- [x] 3.3 Run tests — expect failure (modules don't exist yet)
  - [x] 3.3.1 `hatch test -- tests/unit/specfact_code_review/run/ -v` → capture failing output
  - [x] 3.3.2 Record failing evidence in `openspec/changes/code-review-01-module-scaffold/TDD_EVIDENCE.md`

## 4. Implement module scaffold

- [x] 4.1 Create `packages/specfact-code-review/src/specfact_code_review/__init__.py`
- [x] 4.2 Create `run/findings.py` — `ReviewFinding` and `ReviewReport` Pydantic models with all governance-01 fields and review extensions; add `@require`/`@ensure`/`@beartype` to all public methods
- [x] 4.3 Create `run/scorer.py` — scoring algorithm; pure function with `@require`/`@ensure`
- [x] 4.4 Create `review/app.py` — Typer extension entrypoint; `module_io_shim` re-exports
- [x] 4.5 Create `review/commands.py` — review subgroup wiring (run/ledger/rules stubs)
- [x] 4.6 Create `run/commands.py` stub

## 5. Run tests and validate

- [x] 5.1 Run tests — expect passing
  - [x] 5.1.1 `hatch test -- tests/unit/specfact_code_review/run/ -v`
  - [x] 5.1.2 Record passing evidence in `TDD_EVIDENCE.md`
- [x] 5.2 `hatch run format` — ruff format + fix
- [x] 5.3 `hatch run type-check` — basedpyright strict
- [x] 5.4 `hatch run contract-test` — validate icontract decorators
- [x] 5.5 `hatch run lint` — full lint suite
- [x] 5.6 Verify `specfact code review --help` shows review subgroup

## 6. Module signing

- [x] 6.1 `hatch run ./scripts/verify-modules-signature.py --require-signature`
- [x] 6.2 If failing: bump module version in `module-package.yaml`, re-sign with signing key
- [x] 6.3 Re-run verification until green

## 7. Documentation

- [x] 7.1 Create `docs/modules/code-review.md` with: install command, command overview, scoring algorithm, JSON output schema, governance-01 alignment note
- [x] 7.2 Update `docs/index.md` and `docs/_layouts/default.html` sidebar to include the new code-review module page
- [x] 7.3 Verify front-matter: `layout`, `title`, `permalink`, `description`

## 8. Version and changelog

- [x] 8.1 Bump minor version (new feature): sync `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`
- [x] 8.2 Add CHANGELOG.md entry: `Added: specfact-code-review module scaffold (SP-001)`

## 9. Create GitHub issue

- [x] 9.1 Create issue in `nold-ai/specfact-cli`:
  - Title: `[Change] specfact-code-review module scaffold with ReviewFinding/ReviewReport models`
  - Labels: `enhancement`, `change-proposal`
  - Body: from proposal.md Why + What Changes sections
  - Footer: `*OpenSpec Change Proposal: code-review-01-module-scaffold*`
- [x] 9.2 Update `proposal.md` Source Tracking with issue number and URL

## 10. Create PR

- [x] 10.1 `git add` changed files (inside worktree)
- [x] 10.2 `git commit -m "feat: add specfact-code-review module scaffold with ReviewFinding/ReviewReport models"`
- [x] 10.3 `git push -u origin feature/code-review-01-module-scaffold`
- [x] 10.4 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/code-review-01-module-scaffold --title "feat: specfact-code-review module scaffold (SP-001)"`
- [x] 10.5 Link PR to project: `gh project item-add 1 --owner nold-ai --url <PR_URL>`

## Post-merge cleanup (after PR is merged)

- [x] Return to primary checkout: `cd .../specfact-cli`
- [x] `git fetch origin`
- [x] `git worktree remove ../specfact-cli-worktrees/feature/code-review-01-module-scaffold`
- [x] `git branch -d feature/code-review-01-module-scaffold`
- [x] `git worktree prune`
