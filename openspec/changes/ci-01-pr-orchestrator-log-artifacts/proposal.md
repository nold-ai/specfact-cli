# Change: CI — Attach Test and Repro Log Artifacts to PR Orchestrator Runs

## Why

The current GitHub Action runner (`.github/workflows/pr-orchestrator.yml`) forces us to copy-paste from the UI when debugging; error details are often truncated or only snippets are visible, so we must re-run the full suite locally to find all issues before fixing them. Repro test output and reports are not attached to the run, so failures in `specfact repro` are hard to diagnose from CI alone. The goal is to use `smart-test-full` to generate log files, attach those logs (and repro logs/reports) as workflow artifacts so we can download them on failure, and shift full execution validation from local runs to CI before merging to `dev`.

## What Changes

- **Tests job**: Use `hatch run smart-test-full` so that the smart-test script writes full test and coverage logs under `logs/tests/`. Upload `logs/tests/` (and existing coverage XML) as workflow artifacts so every run (or every failed run) has downloadable full logs.
- **Contract-first-ci job (repro)**: After running `specfact repro`, capture repro stdout/stderr to a file under `logs/repro/` and upload `.specfact/reports/enforcement/` and the repro log file as artifacts so we can download them when the job fails.
- **Artifact upload**: Add `actions/upload-artifact@v4` steps for test logs and repro logs/reports with consistent names (e.g. `test-logs`, `repro-logs`, `repro-reports`). Use `if: always()` or `if: failure()` per project policy so artifacts are available for debugging.
- **Documentation**: Update contributing or troubleshooting docs to describe CI log artifacts and how to download and use them.

## Capabilities

- **ci-log-artifacts**: PR orchestrator runs produce downloadable test logs (from smart-test-full) and repro logs/reports so failures can be diagnosed from CI without local re-runs.

## Impact

- **CI**: Longer test step when using smart-test-full (writes logs); additional artifact upload steps; slightly more storage/retention for artifacts. No change to test semantics beyond ensuring full logs are generated and uploaded.
- **Developers**: Can download full test and repro logs from the Actions run when a job fails, reducing need to re-run locally.
- **Docs**: One new or updated section on CI artifacts (where to find them, what they contain).

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #260
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/260>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
