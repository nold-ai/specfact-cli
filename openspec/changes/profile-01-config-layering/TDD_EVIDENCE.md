# TDD Evidence: profile-01-config-layering

## Stale-change refresh

- Timestamp: 2026-07-06 23:18 CEST
- Result: Refreshed February 2026 OpenSpec artifacts before PR preparation.
- Evidence:
  - `proposal.md` now records the 2026-07-06 implementation refresh and PR-candidate status.
  - `design.md` no longer describes the change as proposal-stage only or non-code.
  - `specs/init-module-state/spec.md` now uses validation-support module language instead of stale ceremony positioning.
  - `CHANGE_VALIDATION.md` now records the current strict validation result.

## Failing-before run

- Timestamp: 2026-07-06 22:02 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py -q`
- Result: Failed as expected before production implementation.
- Evidence:
  - `test_validation_tier_profiles_resolve_clean_code_defaults` failed because `first_run_selection.resolve_profile_config` did not exist.
  - `test_profile_config_layering_records_winning_sources` failed because `first_run_selection.resolve_profile_config` did not exist.
  - `test_init_startup_profile_writes_layered_config_and_enables_startup_modules` failed because `startup` was rejected as an unknown profile.

## Passing-after runs

- Timestamp: 2026-07-06 22:04 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py -q`
- Result: Passed, 24 passed.

- Timestamp: 2026-07-06 22:08 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py -q`
- Result: Passed, 24 passed.

- Timestamp: 2026-07-06 22:08 CEST
- Command: `hatch run pytest tests/e2e/test_first_run_init.py -q`
- Result: Passed, 2 passed.

## Quality and OpenSpec gates

- Timestamp: 2026-07-06 22:07 CEST
- Command: `hatch run format`
- Result: Passed.

- Timestamp: 2026-07-06 22:07 CEST
- Command: `hatch run type-check`
- Result: Passed with existing repository warnings; touched resolver warning removed.

- Timestamp: 2026-07-06 22:08 CEST
- Command: `openspec validate profile-01-config-layering --strict`
- Result: Passed.

- Timestamp: 2026-07-06 22:09 CEST
- Command: `hatch run yaml-lint`
- Result: Passed.

- Timestamp: 2026-07-06 22:09 CEST
- Command: `hatch run lint`
- Result: Passed.

- Timestamp: 2026-07-06 23:02 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py -q`
- Result: Passed, 24 passed.

- Timestamp: 2026-07-06 23:02 CEST
- Command: `hatch run pytest tests/e2e/test_first_run_init.py -q`
- Result: Passed, 2 passed.

- Timestamp: 2026-07-06 23:02 CEST
- Command: `openspec validate profile-01-config-layering --strict`
- Result: Passed.

- Timestamp: 2026-07-06 23:03 CEST
- Command: `hatch run format`
- Result: Passed.

- Timestamp: 2026-07-06 23:03 CEST
- Command: `hatch run type-check`
- Result: Passed with existing repository warnings; 0 errors.

- Timestamp: 2026-07-06 23:03 CEST
- Command: `hatch run yaml-lint`
- Result: Passed.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run lint`
- Result: Passed. Initial sandbox run failed in pylint process-pool system-limit detection; rerun outside sandbox passed with 10.00/10.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run contract-test`
- Result: Passed with cached changed-scope result: no modified files detected.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run specfact code review run --scope changed --json --out .specfact/code-review.json`
- Result: Passed with advisory, CI exit code 0, score 96, 9 advisory findings, 0 blocking findings.
- Advisory disposition: not fixed in this PR. Findings are legacy clean-code/KISS/YAGNI advisories around existing `commands.py` helpers and `init_ide` size/shape, not regressions introduced by profile config layering. Changing them here would expand scope beyond the OpenSpec story.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run bandit-scan`
- Result: Passed. No medium/high issues identified.

- Timestamp: 2026-07-06 23:08 CEST
- Command: `SEMGREP_ENABLE_VERSION_CHECK=0 hatch run semgrep-sast --json --output logs/static-analysis/semgrep.json`
- Result: Passed, 0 findings.

- Timestamp: 2026-07-06 23:08 CEST
- Command: `hatch run semgrep-sast-gate --results logs/static-analysis/semgrep.json --baseline tools/semgrep/sast-baseline.json`
- Result: Passed, 0 current findings and 0 accepted baseline findings.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run smart-test`
- Result: Inconclusive. The tool had no incremental baseline, expanded to a full 2,783-test suite, and was stopped after unrelated broad-suite failures appeared outside the changed scope. Targeted unit/e2e tests above provide changed-scope coverage for this PR.
