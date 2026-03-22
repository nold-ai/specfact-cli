---
layout: default
title: Ci Pr Orchestrator Log Artifacts
permalink: /plans/ci-pr-orchestrator-log-artifacts/
---

# Plan: PR Orchestrator — Attach Test and Repro Logs to CI Runs

**Repository**: `nold-ai/specfact-cli` (public)

## Purpose

Improve the GitHub Action runner (`.github/workflows/pr-orchestrator.yml`) so that:

1. **Full test output is available on failure** — Today we often copy-paste from the UI, error details are truncated or only snippets, and we must re-run locally to find all issues. The goal is to run `smart-test-full` (or equivalent) so that log files are generated and attached to each CI run so we can download them when a run fails.

2. **Repro test logs are captured and attached** — For the `specfact code repro` step (contract-first-ci job), collect logs and the repro report directory (e.g. `.specfact/reports/enforcement`) and upload them as artifacts so we can download on error.

3. **Shift full execution validation to CI** — By having full logs and repro artifacts attached, we can rely on CI for full validation before merging to `dev` and avoid redundant local full runs.

## Current Shortcomings

- **pr-orchestrator.yml** runs contract-first test layers (contract-test-contracts, contract-test-exploration, contract-test-scenarios, contract-test-e2e) but does **not** use `smart-test-full`; it does not write test output to log files that are then uploaded.
- Only **coverage.xml** is uploaded (in Tests job); no raw test logs or repro logs.
- The **contract-first-ci** job runs `hatch run specfact code repro --verbose --crosshair-required --budget 120` with `|| echo "SpecFact repro found issues"`, so the job does not fail hard and repro stdout/stderr and reports are not uploaded as artifacts.
- Error details in the GitHub Actions UI are limited to step output (snippets); full logs are not downloadable.

## What Changes

- **Tests job**: Switch to (or add) running `hatch run smart-test-full` so that the smart-test script writes logs under `logs/tests/` (e.g. `full_test_run_*.log`, `full_coverage_*.log`). Upload the contents of `logs/tests/` (and existing `logs/tests/coverage/coverage.xml`) as workflow artifacts so they are available for download on every run (or on failure only to save space/retention).
- **Contract-first-ci job (repro)**: After running `specfact code repro`, collect (1) repro stdout/stderr (e.g. by redirecting to a file or using a wrapper that writes to `logs/repro/`), and (2) `.specfact/reports/enforcement/` (repro reports). Upload these as artifacts (e.g. `repro-logs` and `repro-reports`), so on failure we can download full repro output and reports.
- **Artifact upload strategy**: Use `actions/upload-artifact@v4` with a consistent naming scheme (e.g. `test-logs-<job>`, `repro-logs`, `repro-reports`). Optionally use `if: failure()` or `if: always()` so artifacts are retained for failed runs or all runs per project policy.
- **Documentation**: Update docs (e.g. contributing, troubleshooting, or reference) to mention that CI produces downloadable test and repro log artifacts and how to use them.

## Files to Create/Modify

- `.github/workflows/pr-orchestrator.yml` — Add/change test step to use smart-test-full with log output; add artifact upload steps for test logs and repro logs/reports.
- Optionally: a small script under `.github/workflows/scripts/` to run repro and capture logs to a file (if not done inline).
- `docs/` — Add or update a section on CI artifacts (where to find them, what they contain).

## Success Metrics

- Every PR/push run that executes tests produces downloadable artifacts containing full test log files when using smart-test-full.
- Every run that executes `specfact code repro` produces downloadable artifacts containing repro stdout/stderr and repro report files.
- Contributors can diagnose failures from downloaded artifacts without needing to re-run the full suite locally.

## Dependencies

- Existing `tools/smart_test_coverage.py` already writes to `logs/tests/` when running full tests; ensure CI has write access and paths are consistent.
- Existing `specfact.yml` already uploads `.specfact/reports/enforcement/*.yaml` and `.specfact/pr-comment.md`; align naming and behavior with pr-orchestrator for repro artifacts.
