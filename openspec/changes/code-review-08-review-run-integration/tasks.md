# Tasks: Wire All Runners into specfact code review run End-to-End

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [ ] 1.1 `git fetch origin`
- [ ] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-08-review-run-integration -b feature/code-review-08-review-run-integration origin/dev`
- [ ] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-08-review-run-integration`
- [ ] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blockers resolved

- [ ] 2.1 Confirm `code-review-02-ruff-radon-runners` merged
- [ ] 2.2 Confirm `code-review-03-type-governance-runners` merged
- [ ] 2.3 Confirm `code-review-04-contract-test-runners` merged (includes runner.py)
- [ ] 2.4 Confirm `code-review-05-semgrep-clean-code-rules` merged

## 3. Create fixture files

- [ ] 3.1 Create `tests/fixtures/review/clean_module.py` — well-structured Python file, all contracts present, passing tests at >= 80% coverage, no violations
- [ ] 3.2 Create `tests/fixtures/review/dirty_module.py` — file with multiple violations: missing @require, complexity > 12, bare except, no test file → expected BLOCK

## 4. Write tests BEFORE implementation (TDD-first)

- [ ] 4.1 Write `tests/e2e/specfact_code_review/test_review_run_e2e.py`
  - [ ] 4.1.1 Test clean fixture → PASS, exit 0
  - [ ] 4.1.2 Test dirty fixture → FAIL, exit 1
  - [ ] 4.1.3 Test `--json` output is valid ReviewReport JSON
  - [ ] 4.1.4 Test `--score-only` prints only integer
  - [ ] 4.1.5 Test `--fix` applies ruff --fix and re-runs
- [ ] 4.2 Write cli-val-01 scenario YAML files:
  - [ ] 4.2.1 `tests/cli-contracts/specfact-code-review-run.scenarios.yaml`
  - [ ] 4.2.2 `tests/cli-contracts/specfact-code-review-ledger.scenarios.yaml`
  - [ ] 4.2.3 `tests/cli-contracts/specfact-code-review-rules.scenarios.yaml`
- [ ] 4.3 Run e2e tests → expect failure (command not fully wired yet); record in `TDD_EVIDENCE.md`

## 5. Complete runner.py and commands.py

- [ ] 5.1 Complete `run/runner.py` — wire all tool runners, merge findings, invoke scorer, build ReviewReport
- [ ] 5.2 Complete `run/commands.py`:
  - [ ] 5.2.1 `--json` output mode
  - [ ] 5.2.2 `--score-only` mode
  - [ ] 5.2.3 `--fix` mode (ruff --fix + isort, then re-run)
  - [ ] 5.2.4 `--no-tests` flag
  - [ ] 5.2.5 Default: git diff HEAD for file list
  - [ ] 5.2.6 Rich table output grouped by category

## 6. Quality gates

- [ ] 6.1 Run e2e tests → expect passing; record in `TDD_EVIDENCE.md`
- [ ] 6.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`
- [ ] 6.3 Validate scenario YAML files against cli-val-01 schema
- [ ] 6.4 Cross-reference e2e fixtures with dogfooding-01-full-chain-e2e-proof requirements

## 7. Module signing, docs, version, changelog

- [ ] 7.1 Verify/re-sign module
- [ ] 7.2 Complete `docs/modules/code-review.md` — all options, exit codes, output examples, piping examples
- [ ] 7.3 Bump minor version; update CHANGELOG.md

## 8. Create GitHub issue and PR

- [ ] 8.1 Create issue: `[Change] Wire all tool runners into specfact code review run end-to-end`
- [ ] 8.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [ ] Remove worktree, delete branch, prune
