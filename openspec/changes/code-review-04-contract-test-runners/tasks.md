# Tasks: icontract AST Scan and TDD Gate Runners

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [x] 1.1 `git fetch origin`
- [x] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-04-contract-test-runners -b feature/code-review-04-contract-test-runners origin/dev`
- [x] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-04-contract-test-runners`
- [x] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blockers resolved

- [x] 2.1 Confirm `code-review-01-module-scaffold` is merged (ReviewFinding, ReviewReport)
- [x] 2.2 Confirm `code-review-02-ruff-radon-runners` and `code-review-03-type-governance-runners` are merged (runner.py needs them)

## 3. Write tests BEFORE implementation (TDD-first)

- [x] 3.1 Write `tests/unit/specfact_code_review/tools/test_contract_runner.py`
  - [x] 3.1.1 Test public function without @require → MISSING_ICONTRACT finding
  - [x] 3.1.2 Test public function with @require + @ensure → no finding
  - [x] 3.1.3 Test private function (_prefix) → excluded
  - [x] 3.1.4 Test CrossHair counterexample → contracts/warning finding with tool="crosshair"
  - [x] 3.1.5 Test CrossHair timeout → skipped, no exception
  - [x] 3.1.6 Test CrossHair unavailable → tool_error finding, AST scan still runs
- [x] 3.2 Write `tests/unit/specfact_code_review/run/test_runner.py`
  - [x] 3.2.1 Test all runners called in order (mock each)
  - [x] 3.2.2 Test findings merged from all runners
  - [x] 3.2.3 Test TDD gate: missing test file → TEST_FILE_MISSING finding
  - [x] 3.2.4 Test --no-tests skips TDD gate
  - [x] 3.2.5 Test review run returns ReviewReport
- [x] 3.3 Run tests → expect failure; record in `TDD_EVIDENCE.md`

## 4. Implement runners

- [x] 4.1 Implement `tools/contract_runner.py`:
  - [x] 4.1.1 AST scan for missing icontract decorators
  - [x] 4.1.2 CrossHair fast-pass (2s timeout per path)
  - [x] 4.1.3 `@require`/`@ensure`/`@beartype` on all public methods
- [x] 4.2 Implement `run/runner.py`:
  - [x] 4.2.1 Orchestrate all tool runners in sequence
  - [x] 4.2.2 Merge findings list
  - [x] 4.2.3 Invoke scorer to build ReviewReport
  - [x] 4.2.4 TDD gate logic (test file existence check, coverage check)
- [x] 4.3 Create AST scan fixture files for tests

## 5. Quality gates

- [x] 5.1 Run tests → expect passing; record in `TDD_EVIDENCE.md`
- [x] 5.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`
- [x] 5.3 Verify crosshair is available in dev environment

## 6. Module signing, docs, version, changelog

- [x] 6.1 Verify/re-sign module
- [x] 6.2 Update `docs/modules/code-review.md` with contract and TDD gate details; document crosshair open question
- [x] 6.3 Bump patch version; update CHANGELOG.md

## 7. Create GitHub issue and PR

- [x] 7.1 Create issue: `[Change] Add icontract AST scan and TDD gate runners for specfact code review run`
- [x] 7.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [x] Remove worktree, delete branch, prune
