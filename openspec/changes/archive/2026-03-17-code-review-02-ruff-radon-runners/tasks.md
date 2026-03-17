# Tasks: Ruff and Radon Tool Runners

## TDD / SDD order (enforced)

Per `openspec/config.yaml`: tests before code for any behavior-changing task.
Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [x] 1.1 `git fetch origin`
- [x] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-02-ruff-radon-runners -b feature/code-review-02-ruff-radon-runners origin/dev`
- [x] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-02-ruff-radon-runners`
- [x] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
- [x] 1.5 `git branch --show-current` (verify branch)

## 2. Verify blocker resolved

- [x] 2.1 Confirm `code-review-01-module-scaffold` is merged (`ReviewFinding` and `ReviewReport` available)

## 3. Write tests BEFORE implementation (TDD-first)

- [x] 3.1 Write `tests/unit/specfact_code_review/tools/test_ruff_runner.py`
  - [x] 3.1.1 Test Bandit S-rule → category=security
  - [x] 3.1.2 Test C901 → category=clean_code
  - [x] 3.1.3 Test E501/F401/I001 → category=style
  - [x] 3.1.4 Test file filter: findings for non-provided files excluded
  - [x] 3.1.5 Test parse error → tool_error finding
  - [x] 3.1.6 Test ruff unavailable → tool_error finding, no exception
  - [x] 3.1.7 Test fixable detection from ruff JSON
- [x] 3.2 Write `tests/unit/specfact_code_review/tools/test_radon_runner.py`
  - [x] 3.2.1 Test complexity 13 → severity=warning
  - [x] 3.2.2 Test complexity 16 → severity=error
  - [x] 3.2.3 Test complexity 10 → no finding
  - [x] 3.2.4 Test file filter
  - [x] 3.2.5 Test parse error → tool_error finding
- [x] 3.3 Run tests → expect failure
  - [x] 3.3.1 `hatch test -- tests/unit/specfact_code_review/tools/test_ruff_runner.py tests/unit/specfact_code_review/tools/test_radon_runner.py -v`
  - [x] 3.3.2 Record failing evidence in `TDD_EVIDENCE.md`

## 4. Implement runners

- [x] 4.1 Create `tools/__init__.py`
- [x] 4.2 Implement `tools/ruff_runner.py` with `@require`/`@ensure`/`@beartype`
- [x] 4.3 Implement `tools/radon_runner.py` with `@require`/`@ensure`/`@beartype`

## 5. Run tests and quality gates

- [x] 5.1 `hatch test -- tests/unit/specfact_code_review/tools/ -v` → expect passing
- [x] 5.2 Record passing evidence in `TDD_EVIDENCE.md`
- [x] 5.3 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`

## 6. Module signing

- [x] 6.1 Verify module signature; re-sign if needed

## 7. Documentation

- [x] 7.1 Update `docs/modules/code-review.md`: add tool runner section (ruff rules table, radon thresholds)

## 8. Version and changelog

- [x] 8.1 Bump patch version; sync version files
- [x] 8.2 Add CHANGELOG.md entry: `Added: ruff and radon runners for specfact code review run (SP-002)`

## 9. Create GitHub issue and PR

- [x] 9.1 Create issue: `[Change] Add ruff and radon tool runners for specfact code review run`
- [x] 9.2 Update proposal.md Source Tracking
- [x] 9.3 Commit, push, create PR, link to project

## Post-merge cleanup

- [x] `git worktree remove ../specfact-cli-worktrees/feature/code-review-02-ruff-radon-runners`
- [x] `git branch -d feature/code-review-02-ruff-radon-runners`
- [x] `git worktree prune`
