# Tasks: Project-Specific Semgrep Rules

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [ ] 1.1 `git fetch origin`
- [ ] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-05-semgrep-clean-code-rules -b feature/code-review-05-semgrep-clean-code-rules origin/dev`
- [ ] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-05-semgrep-clean-code-rules`
- [ ] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blocker resolved

- [ ] 2.1 Confirm `code-review-01-module-scaffold` is merged

## 3. Design and write fixture files first

- [ ] 3.1 Write fixture pairs for each of the 5 rules:
  - [ ] 3.1.1 `tests/fixtures/semgrep/bad_get_modify.py` and `good_get_modify.py`
  - [ ] 3.1.2 `tests/fixtures/semgrep/bad_nested_access.py` and `good_nested_access.py`
  - [ ] 3.1.3 `tests/fixtures/semgrep/bad_cross_layer.py` and `good_cross_layer.py`
  - [ ] 3.1.4 `tests/fixtures/semgrep/bad_module_network.py` and `good_module_network.py`
  - [ ] 3.1.5 `tests/fixtures/semgrep/bad_print_in_src.py` and `good_print_in_src.py`

## 4. Write tests BEFORE implementation (TDD-first)

- [ ] 4.1 Write `tests/unit/specfact_code_review/tools/test_semgrep_runner.py`
  - [ ] 4.1.1 Test finding maps to ReviewFinding with correct tool/category
  - [ ] 4.1.2 Test non-provided files filtered out
  - [ ] 4.1.3 Test semgrep unavailable → tool_error, no exception
  - [ ] 4.1.4 Test clean file → empty list
  - [ ] 4.1.5 Test each bad fixture triggers its rule
  - [ ] 4.1.6 Test each good fixture triggers no finding
- [ ] 4.2 Run tests → expect failure; record in `TDD_EVIDENCE.md`

## 5. Implement semgrep runner and rules

- [ ] 5.1 Create `.semgrep/clean_code.yaml` with all 5 rules
- [ ] 5.2 Implement `tools/semgrep_runner.py` with `@require`/`@ensure`/`@beartype`
- [ ] 5.3 Validate rules against fixtures: `semgrep --config .semgrep/clean_code.yaml --json tests/fixtures/semgrep/bad_*.py`

## 6. Quality gates

- [ ] 6.1 Run tests → expect passing; record in `TDD_EVIDENCE.md`
- [ ] 6.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`
- [ ] 6.3 `hatch run scan-all` — verify new semgrep rules don't conflict with existing config

## 7. Module signing, docs, version, changelog

- [ ] 7.1 Verify/re-sign module
- [ ] 7.2 Update `docs/modules/code-review.md` with semgrep rules section (rule descriptions + examples)
- [ ] 7.3 Bump patch version; update CHANGELOG.md

## 8. Create GitHub issue and PR

- [ ] 8.1 Create issue: `[Change] Add project-specific semgrep rules for clean code patterns`
- [ ] 8.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [ ] Remove worktree, delete branch, prune
