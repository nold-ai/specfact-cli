# Tasks: icontract AST Scan and TDD Gate Runners

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [ ] 1.1 `git fetch origin`
- [ ] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-04-contract-test-runners -b feature/code-review-04-contract-test-runners origin/dev`
- [ ] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-04-contract-test-runners`
- [ ] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blockers resolved

- [ ] 2.1 Confirm `code-review-01-module-scaffold` is merged (ReviewFinding, ReviewReport)
- [ ] 2.2 Confirm `code-review-02-ruff-radon-runners` and `code-review-03-type-governance-runners` are merged (runner.py needs them)

## 3. Write tests BEFORE implementation (TDD-first)

- [ ] 3.1 Write `tests/unit/specfact_code_review/tools/test_contract_runner.py`
  - [ ] 3.1.1 Test public function without @require → MISSING_ICONTRACT finding
  - [ ] 3.1.2 Test public function with @require + @ensure → no finding
  - [ ] 3.1.3 Test private function (_prefix) → excluded
  - [ ] 3.1.4 Test CrossHair counterexample → contracts/warning finding with tool="crosshair"
  - [ ] 3.1.5 Test CrossHair timeout → skipped, no exception
  - [ ] 3.1.6 Test CrossHair unavailable → tool_error finding, AST scan still runs
- [ ] 3.2 Write `tests/unit/specfact_code_review/run/test_runner.py`
  - [ ] 3.2.1 Test all runners called in order (mock each)
  - [ ] 3.2.2 Test findings merged from all runners
  - [ ] 3.2.3 Test TDD gate: missing test file → TEST_FILE_MISSING finding
  - [ ] 3.2.4 Test --no-tests skips TDD gate
  - [ ] 3.2.5 Test review run returns ReviewReport
- [ ] 3.3 Run tests → expect failure; record in `TDD_EVIDENCE.md`

## 4. Implement runners

- [ ] 4.1 Implement `tools/contract_runner.py`:
  - [ ] 4.1.1 AST scan for missing icontract decorators
  - [ ] 4.1.2 CrossHair fast-pass (2s timeout per path)
  - [ ] 4.1.3 `@require`/`@ensure`/`@beartype` on all public methods
- [ ] 4.2 Implement `run/runner.py`:
  - [ ] 4.2.1 Orchestrate all tool runners in sequence
  - [ ] 4.2.2 Merge findings list
  - [ ] 4.2.3 Invoke scorer to build ReviewReport
  - [ ] 4.2.4 TDD gate logic (test file existence check, coverage check)
- [ ] 4.3 Create AST scan fixture files for tests

## 5. Quality gates

- [ ] 5.1 Run tests → expect passing; record in `TDD_EVIDENCE.md`
- [ ] 5.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`
- [ ] 5.3 Verify crosshair is available in dev environment

## 6. Module signing, docs, version, changelog

- [ ] 6.1 Verify/re-sign module
- [ ] 6.2 Update `docs/modules/code-review.md` with contract and TDD gate details; document crosshair open question
- [ ] 6.3 Bump patch version; update CHANGELOG.md

## 7. Create GitHub issue and PR

- [ ] 7.1 Create issue: `[Change] Add icontract AST scan and TDD gate runners for specfact code review run`
- [ ] 7.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [ ] Remove worktree, delete branch, prune
