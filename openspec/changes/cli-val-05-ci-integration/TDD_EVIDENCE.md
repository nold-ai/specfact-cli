# TDD Evidence: cli-val-05-ci-integration

## Pre-Implementation Failing Run

- Timestamp (UTC): 2026-02-26T00:23:59Z
- Command:
  - `python -m pytest tests/unit/specfact_cli/registry/test_signing_artifacts.py -k virtualenv_below_21 -q`
- Result: FAILED
- Failure summary:
  - `test_pr_orchestrator_pins_virtualenv_below_21_for_hatch_jobs`
  - Assertion error: missing `virtualenv<21` pin in workflow install command (`pip install hatch coverage`).

## Post-Implementation Passing Run

- Timestamp (UTC): 2026-02-26T00:24:14Z
- Command:
  - `python -m pytest tests/unit/specfact_cli/registry/test_signing_artifacts.py -k virtualenv_below_21 -q`
- Result: PASSED
- Summary:
  - Workflow install commands that include `hatch` now also include `virtualenv<21`.
