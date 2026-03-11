# Tasks: Ruff and Radon Tool Runners

## TDD / SDD order (enforced)

Per `openspec/config.yaml`: tests before code for any behavior-changing task.
Do not implement production code until tests exist and have been run (expecting failure).

---

## 1. Create git worktree for this change

- [ ] 1.1 `git fetch origin`
- [ ] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-02-ruff-radon-runners -b feature/code-review-02-ruff-radon-runners origin/dev`
- [ ] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-02-ruff-radon-runners`
- [ ] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
- [ ] 1.5 `git branch --show-current` (verify branch)

## 2. Verify blocker resolved

- [ ] 2.1 Confirm `code-review-01-module-scaffold` is merged (`ReviewFinding` and `ReviewReport` available)

## 3. Write tests BEFORE implementation (TDD-first)

- [ ] 3.1 Write `tests/unit/specfact_code_review/tools/test_ruff_runner.py`
  - [ ] 3.1.1 Test Bandit S-rule → category=security
  - [ ] 3.1.2 Test C901 → category=clean_code
  - [ ] 3.1.3 Test E501/F401/I001 → category=style
  - [ ] 3.1.4 Test file filter: findings for non-provided files excluded
  - [ ] 3.1.5 Test parse error → tool_error finding
  - [ ] 3.1.6 Test ruff unavailable → tool_error finding, no exception
  - [ ] 3.1.7 Test fixable detection from ruff JSON
- [ ] 3.2 Write `tests/unit/specfact_code_review/tools/test_radon_runner.py`
  - [ ] 3.2.1 Test complexity 13 → severity=warning
  - [ ] 3.2.2 Test complexity 16 → severity=error
  - [ ] 3.2.3 Test complexity 10 → no finding
  - [ ] 3.2.4 Test file filter
  - [ ] 3.2.5 Test parse error → tool_error finding
- [ ] 3.3 Run tests → expect failure
  - [ ] 3.3.1 `hatch test -- tests/unit/specfact_code_review/tools/test_ruff_runner.py tests/unit/specfact_code_review/tools/test_radon_runner.py -v`
  - [ ] 3.3.2 Record failing evidence in `TDD_EVIDENCE.md`

## 4. Implement runners

- [ ] 4.1 Create `tools/__init__.py`
- [ ] 4.2 Implement `tools/ruff_runner.py` with `@require`/`@ensure`/`@beartype`
- [ ] 4.3 Implement `tools/radon_runner.py` with `@require`/`@ensure`/`@beartype`

## 5. Run tests and quality gates

- [ ] 5.1 `hatch test -- tests/unit/specfact_code_review/tools/ -v` → expect passing
- [ ] 5.2 Record passing evidence in `TDD_EVIDENCE.md`
- [ ] 5.3 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`

## 6. Module signing

- [ ] 6.1 Verify module signature; re-sign if needed

## 7. Documentation

- [ ] 7.1 Update `docs/modules/code-review.md`: add tool runner section (ruff rules table, radon thresholds)

## 8. Version and changelog

- [ ] 8.1 Bump patch version; sync version files
- [ ] 8.2 Add CHANGELOG.md entry: `Added: ruff and radon runners for specfact code review run (SP-002)`

## 9. Create GitHub issue and PR

- [ ] 9.1 Create issue: `[Change] Add ruff and radon tool runners for specfact code review run`
- [ ] 9.2 Update proposal.md Source Tracking
- [ ] 9.3 Commit, push, create PR, link to project

## Post-merge cleanup

- [ ] `git worktree remove ../specfact-cli-worktrees/feature/code-review-02-ruff-radon-runners`
- [ ] `git branch -d feature/code-review-02-ruff-radon-runners`
- [ ] `git worktree prune`
