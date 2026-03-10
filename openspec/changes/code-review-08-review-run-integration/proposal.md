# Change: Wire All Tool Runners into specfact code review run End-to-End

## Why

SP-002 through SP-005 deliver individual runners; this change wires them together into a fully functional `specfact code review run` command. It also adds the CLI contracts scenario YAML files required for cli-val-01..06 integration, and e2e test fixtures that serve double duty as dogfooding-01 evidence.

Without this change, the module has no working entry point — all runner SPs are internal building blocks.

## What Changes

- **COMPLETE**: `runner.py` — orchestrates all tool runners in sequence (ruff → radon → basedpyright → pylint → contract → semgrep → test TDD gate), merges findings, invokes scorer, returns `ReviewReport` (governance-01 envelope)
- **COMPLETE**: `run/commands.py` — Typer command with `--json`, `--score-only`, `--fix`, `--no-tests`, `--rules` options
- **NEW**: `--fix` applies `ruff --fix` + isort on auto-fixable findings, then re-runs review
- **NEW**: `--score-only` prints only the `reward_delta` integer (CI integration)
- **NEW**: Human-readable output uses Rich tables grouped by category
- **NEW**: e2e test: runs `specfact code review run` on a fixture directory (clean → PASS, dirty → BLOCK)
- **NEW**: `tests/fixtures/review/clean_module.py` — expected `overall_verdict=PASS`
- **NEW**: `tests/fixtures/review/dirty_module.py` — expected `overall_verdict=FAIL`
- **NEW**: `tests/cli-contracts/specfact-code-review-run.scenarios.yaml` (cli-val-01 format)
- **NEW**: `tests/cli-contracts/specfact-code-review-ledger.scenarios.yaml` (cli-val-01 format)
- **NEW**: `tests/cli-contracts/specfact-code-review-rules.scenarios.yaml` (cli-val-01 format)

**Exit code semantics (cli-val-05 aligned):**
- `ci_exit_code=0` → PASS or WARN (advisory)
- `ci_exit_code=1` → BLOCK (hard gate)

## Capabilities

### New Capabilities

- `review-run-command`: End-to-end `specfact code review run` with all options, Rich output, and correct exit codes
- `review-cli-contracts`: cli-val-01 scenario YAML files for all 3 command groups (run, ledger, rules)
- `review-e2e-fixtures`: Clean/dirty module fixtures for e2e testing and dogfooding-01 evidence

### Modified Capabilities

- `review-runner`: `runner.py` wired end-to-end with all tool runners
- `review-run-command`: `commands.py` completed with all options

---

## Impact

- Depends on `code-review-02-ruff-radon-runners`, `code-review-03-type-governance-runners`, `code-review-04-contract-test-runners`, `code-review-05-semgrep-clean-code-rules`
- cli-val-01 scenario files feed directly into cli-val-04 acceptance runner and cli-val-05 CI gates when those changes land
- e2e fixture also serves as dogfooding-01 evidence — cross-reference with dogfooding-01-full-chain-e2e-proof
- **Documentation**: Complete `docs/modules/code-review.md` with all options, exit codes, output examples

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: TBD
- **Issue URL**: TBD
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
