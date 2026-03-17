# Tasks: Wire All Runners into specfact code review run End-to-End

## TDD / SDD order (enforced)

Tests before code. Do not implement until failing tests exist.

---

## 1. Create git worktree

- [x] 1.1 `git fetch origin`
- [x] 1.2 `git worktree add ../specfact-cli-worktrees/feature/code-review-08-review-run-integration -b feature/code-review-08-review-run-integration origin/dev`
- [x] 1.3 `cd ../specfact-cli-worktrees/feature/code-review-08-review-run-integration`
- [x] 1.4 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

## 2. Verify blockers resolved

- [x] 2.1 Confirm `code-review-02-ruff-radon-runners` merged
- [x] 2.2 Confirm `code-review-03-type-governance-runners` merged
- [x] 2.3 Confirm `code-review-04-contract-test-runners` merged (includes runner.py)
- [x] 2.4 Confirm `code-review-05-semgrep-clean-code-rules` merged

## 3. Create fixture files

- [x] 3.1 Create `tests/fixtures/review/clean_module.py` — well-structured Python file, all contracts present, passing tests at >= 80% coverage, no violations
- [x] 3.2 Create `tests/fixtures/review/dirty_module.py` — file with multiple violations: missing @require, complexity > 12, bare except, no test file → expected BLOCK

## 4. Write tests BEFORE implementation (TDD-first)

- [x] 4.1 Write `tests/e2e/specfact_code_review/test_review_run_e2e.py`
  - [x] 4.1.1 Test clean fixture → PASS, exit 0
  - [x] 4.1.2 Test dirty fixture → FAIL, exit 1
  - [x] 4.1.3 Test `--json` output is valid ReviewReport JSON
  - [x] 4.1.4 Test `--score-only` prints only integer
  - [x] 4.1.5 Test `--fix` applies ruff --fix and re-runs
- [x] 4.2 Write cli-val-01 scenario YAML files:
  - [x] 4.2.1 `tests/cli-contracts/specfact-code-review-run.scenarios.yaml`
  - [x] 4.2.2 `tests/cli-contracts/specfact-code-review-ledger.scenarios.yaml`
  - [x] 4.2.3 `tests/cli-contracts/specfact-code-review-rules.scenarios.yaml`
- [x] 4.3 Run e2e tests → expect failure (command not fully wired yet); record in `TDD_EVIDENCE.md`

## 5. Complete runner.py and commands.py

- [x] 5.1 Complete `run/runner.py` — wire all tool runners, merge findings, invoke scorer, build ReviewReport
- [x] 5.2 Complete `run/commands.py`:
  - [x] 5.2.1 `--json` output mode
  - [x] 5.2.2 `--score-only` mode
  - [x] 5.2.3 `--fix` mode (ruff --fix + isort, then re-run)
  - [x] 5.2.4 `--no-tests` flag
  - [x] 5.2.5 Default: git diff HEAD for file list
  - [x] 5.2.6 Rich table output grouped by category

## 6. Quality gates

- [x] 6.1 Run e2e tests → expect passing; record in `TDD_EVIDENCE.md`
- [x] 6.2 `hatch run format && hatch run type-check && hatch run contract-test && hatch run lint`
- [x] 6.3 Validate scenario YAML files against cli-val-01 schema
- [x] 6.4 Cross-reference e2e fixtures with dogfooding-01-full-chain-e2e-proof requirements

## 7. Module signing, docs, version, changelog

- [x] 7.1 Verify/re-sign module
- [x] 7.2 Complete `docs/modules/code-review.md` — all options, exit codes, output examples, piping examples
- [x] 7.3 Bump minor version; update CHANGELOG.md

## 8. Create GitHub issue and PR

- [x] 8.1 Create issue: `[Change] Wire all tool runners into specfact code review run end-to-end`
- [x] 8.2 Update proposal.md Source Tracking; commit, push, create PR

## Post-merge cleanup

- [x] Remove worktree, delete branch, prune
