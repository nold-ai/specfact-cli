# Design: CI Log Artifacts for PR Orchestrator

## Overview

This change updates `.github/workflows/pr-orchestrator.yml` so that (1) the Tests job runs `hatch run smart-test-full` and uploads generated logs under `logs/tests/` as artifacts, and (2) the contract-first-ci job captures `specfact repro` output to a log file and uploads repro logs and `.specfact/reports/enforcement/` as artifacts. No new external systems; only workflow YAML and optional helper scripts.

## Current State

- **Tests job**: Runs contract-test layers (contract-test-contracts, contract-test-exploration, contract-test-scenarios, contract-test-e2e) and unit tests with coverage via `hatch -e hatch-test.py3.12 run run-cov` / `hatch -e hatch-test.py3.12 run xml`. Uploads only `logs/tests/coverage/coverage.xml` as `coverage-reports`. No full test stdout/stderr log files are produced or uploaded.
- **contract-first-ci job**: Runs `hatch run specfact repro --verbose --crosshair-required --budget 120` with `|| echo "SpecFact repro found issues"`. No log file capture; no artifact upload for repro output or reports.
- **smart_test_coverage.py**: When run with `--level full`, writes to `logs/tests/` (e.g. `full_test_run_<timestamp>.log`, `full_coverage_<timestamp>.log`). Used locally; not yet used in pr-orchestrator.

## Target State

- **Tests job**: Add or replace a step to run `hatch run smart-test-full` so that logs are written to `logs/tests/`. Keep or align with existing coverage XML generation so quality-gates job still receives coverage. Add an upload-artifact step that uploads `logs/tests/` (and `logs/tests/coverage/` if separate) with a name like `test-logs`. Use `if: always()` so logs are available for both success and failure.
- **contract-first-ci job**: Before or as part of the repro step, ensure `logs/repro/` exists. Run repro with stdout/stderr redirected to a file (e.g. `logs/repro/repro_$(date +%Y%m%d_%H%M%S).log`). After the repro step, add an upload-artifact step that uploads `logs/repro/` and `.specfact/reports/enforcement/` (if present) with names like `repro-logs` and `repro-reports`, with `if: always()`.
- **Artifact retention**: Rely on GitHub Actions default retention; no change to workflow-level retention unless required by org policy.

## Integration Points

- **smart_test_coverage.py**: Already creates `logs/tests/` and writes timestamped log files when running full tests. CI must run in an environment where `hatch run smart-test-full` is available (Python 3.12, hatch, dependencies). Timeout: existing step may use SMART_TEST_TIMEOUT_SECONDS (e.g. 1800); ensure sufficient for full run.
- **specfact repro**: Writes reports to `.specfact/reports/enforcement/` (existing). Repro does not write its own stdout to a file; workflow must redirect (e.g. `tee` or `script -q -c "..." repro.log`).
- **specfact.yml**: Already uploads `.specfact/reports/enforcement/*.yaml` and `.specfact/pr-comment.md` as `specfact-report`. We keep pr-orchestrator artifact names distinct (e.g. `repro-reports`) so both workflows remain consistent and downloadable.

## Edge Cases

- **dev→main skip**: When `skip_tests_dev_to_main` is true, Tests and contract-first-ci are skipped; no new artifact steps run. No change.
- **No report directory**: If `specfact repro` never creates `.specfact/reports/enforcement/`, upload with `if-no-files-found: ignore` so the step does not fail.
- **Log directory missing**: Create `logs/repro/` in the contract-first-ci job before running repro so the redirect target exists.

## Contract Enforcement

- No new Python public APIs; only workflow and docs. No new @icontract/@beartype. Existing tools (smart_test_coverage.py, specfact repro) are unchanged except how they are invoked from CI.
