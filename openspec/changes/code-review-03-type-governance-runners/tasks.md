# Tasks: basedpyright and pylint Runners

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [ ] 1.1 `git fetch origin`
- [ ] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-03-type-governance-runners -b feature/code-review-03-type-governance-runners origin/dev`
- [ ] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-03-type-governance-runners`
- [ ] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blocker resolved

- [ ] 2.1 Confirm `code-review-01-module-scaffold` is merged

## 3. Write tests BEFORE implementation (TDD-first)

- [ ] 3.1 Write `tests/unit/specfact_code_review/tools/test_basedpyright_runner.py`
  - [ ] 3.1.1 Test error diagnostic → category=type_safety, severity=error
  - [ ] 3.1.2 Test warning diagnostic → severity=warning
  - [ ] 3.1.3 Test non-provided files filtered out
  - [ ] 3.1.4 Test basedpyright unavailable → tool_error finding
- [ ] 3.2 Write `tests/unit/specfact_code_review/tools/test_pylint_runner.py`
  - [ ] 3.2.1 Test W0702 → category=architecture
  - [ ] 3.2.2 Test W0703 → category=architecture
  - [ ] 3.2.3 Test file filter
  - [ ] 3.2.4 Test parse error → tool_error
- [ ] 3.3 Run tests → expect failure; record in `TDD_EVIDENCE.md`

## 4. Implement runners

- [ ] 4.1 Implement `tools/basedpyright_runner.py` with contracts
- [ ] 4.2 Implement `tools/pylint_runner.py` with contracts

## 5. Quality gates

- [ ] 5.1 Run tests → expect passing; record in `TDD_EVIDENCE.md`
- [ ] 5.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`

## 6. Module signing, docs, version, changelog

- [ ] 6.1 Verify/re-sign module
- [ ] 6.2 Update `docs/modules/code-review.md` with type-safety and governance runner details
- [ ] 6.3 Bump patch version; update CHANGELOG.md

## 7. Create GitHub issue and PR

- [ ] 7.1 Create issue: `[Change] Add basedpyright and pylint runners for specfact code review run`
- [ ] 7.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [ ] Remove worktree, delete branch, prune
