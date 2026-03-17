# Tasks: basedpyright and pylint Runners

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [x] 1.1 `cd ../specfact-cli-modules && git fetch origin`
- [x] 1.2 `git worktree add ../specfact-cli-modules-worktrees/feature/code-review-03-type-governance-runners -b feature/code-review-03-type-governance-runners origin/dev`
- [x] 1.3 `cd ../specfact-cli-modules-worktrees/feature/code-review-03-type-governance-runners`
- [x] 1.4 `hatch env create && hatch run dev-deps && hatch run smart-test-status && hatch run contract-test-status`

## 2. Verify blocker resolved

- [x] 2.1 Confirm `code-review-01-module-scaffold` is merged

## 3. Write tests BEFORE implementation (TDD-first)

- [x] 3.1 Write `tests/unit/specfact_code_review/tools/test_basedpyright_runner.py`
  - [x] 3.1.1 Test error diagnostic → category=type_safety, severity=error
  - [x] 3.1.2 Test warning diagnostic → severity=warning
  - [x] 3.1.3 Test non-provided files filtered out
  - [x] 3.1.4 Test basedpyright unavailable → tool_error finding
- [x] 3.2 Write `tests/unit/specfact_code_review/tools/test_pylint_runner.py`
  - [x] 3.2.1 Test W0702 → category=architecture
  - [x] 3.2.2 Test W0703 → category=architecture
  - [x] 3.2.3 Test file filter
  - [x] 3.2.4 Test parse error → tool_error
- [x] 3.3 Run tests → expect failure; record in `TDD_EVIDENCE.md`

## 4. Implement runners

- [x] 4.1 Implement `tools/basedpyright_runner.py` with contracts
- [x] 4.2 Implement `tools/pylint_runner.py` with contracts

## 5. Quality gates

- [x] 5.1 Run tests → expect passing; record in `TDD_EVIDENCE.md`
- [x] 5.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`

## 6. Module signing, docs, version, changelog

- [x] 6.1 Verify/re-sign module
- [x] 6.2 Update `docs/modules/code-review.md` with type-safety and governance runner details
- [x] 6.3 Bump patch version; update CHANGELOG.md

## 7. Create GitHub issue and PR

- [x] 7.1 Create issue: `[Change] Add basedpyright and pylint runners for specfact code review run`
  - No matching `specfact-cli` issue was created; implementation was tracked via merged `specfact-cli-modules` PRs `#66` and `#68`.
- [x] 7.2 Update proposal.md Source Tracking; commit, push, create PR
  - `specfact-cli-modules` PR `#66` merged to `dev`; release PR `#68` merged `dev` to `main`.

## Post-merge cleanup

- [x] Remove worktree, delete branch, prune
