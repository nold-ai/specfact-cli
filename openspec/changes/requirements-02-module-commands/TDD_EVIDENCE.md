# TDD Evidence: requirements-02-module-commands

## Failing-before

- **Timestamp (Europe/Berlin):** 2026-07-08T20:48:00+02:00
- **Command:** `hatch run pytest tests/unit/requirements/test_context_adapter.py -q`
- **Result:** FAIL, expected
- **Summary:** Pytest failed during collection because the new core requirements
  adapter package did not exist yet.
- **Key error:** `ModuleNotFoundError: No module named 'specfact_cli.requirements'`
- **Sandbox note:** A first unapproved Hatch run failed before pytest while
  creating the worktree virtualenv; the approved rerun captured the behavioral
  missing-package failure above.

## Passing-after

- **Timestamp (Europe/Berlin):** 2026-07-08T20:56:00+02:00
- **Command:** `hatch run pytest tests/unit/requirements/test_context_adapter.py -q`
- **Result:** PASS
- **Summary:** 4 targeted tests passed, covering normalization diagnostics,
  ProjectBundle extension IO, profile-aware validation severity, machine-readable
  coverage summaries.

## Quality Gates

- **Final verification timestamp (Europe/Berlin):**
  2026-07-08T21:26:13+02:00
- `openspec validate requirements-02-module-commands --strict`: PASS
- `hatch run format`: PASS, 637 files left unchanged after final edits.
- `hatch run pytest tests/unit/requirements/test_context_adapter.py -q`: PASS,
  4 passed.
- `hatch run type-check`: PASS, 0 errors; repository baseline warnings remain.
- `hatch run lint`: PASS, pylint 10.00/10.
- `hatch run yaml-lint`: PASS.
- `hatch run contract-test`: PASS, cached changed-file contract result.
- `hatch run smart-test-force`: PASS for test execution, 2,794 tests completed.
  Total repository coverage reported 64.0%, below the 80% policy threshold;
  this result is not recorded as a coverage-gate pass.
  - Test log:
    `logs/tests/test_run_20260708_211857.log`
  - Coverage log:
    `logs/tests/coverage_20260708_211857.log`
  - Coverage disposition: existing repository-wide coverage gap remains;
    changed adapter behavior is covered by targeted tests and code review, but
    total coverage still requires follow-up before the 80% gate can be treated
    as satisfied.
  - Note: `hatch run smart-test` used the cached no-relevant-change shortcut
    after staging and returned nonzero, so the forced full run is the
    authoritative final suite evidence for this change.
- `hatch run check-version-sources`: PASS.
- `hatch run check-pypi-ahead`: PASS, local `0.50.0` ahead of PyPI `0.49.1`.
- `hatch run verify-modules-signature`: PASS, 4 manifests verified.
- `hatch run semgrep-sast --json --output /tmp/specfact-req02-semgrep.json`:
  PASS, 0 findings.
- `hatch run semgrep-sast-gate --results /tmp/specfact-req02-semgrep.json --baseline tools/semgrep/sast-baseline.json`:
  PASS.
- `hatch run bandit-scan`: PASS, no medium/high issues identified.
- `git diff --check`: PASS.
- `hatch run specfact code review run --json --out /tmp/req02-code-review-final.json --scope changed`:
  PASS, no findings on the final code diff.
- `hatch run specfact code review run --json --out /tmp/req02-code-review-final.json --scope full --path src/specfact_cli/requirements/context.py`:
  PASS, no findings after the final docs-only scope cleanup.

## PR Review Fix Verification

- **Timestamp (Europe/Berlin):** 2026-07-08T21:54:30+02:00
- `openspec validate requirements-02-module-commands --strict`: PASS.
- `hatch run format`: PASS, 637 files left unchanged.
- `hatch run pytest tests/unit/requirements/test_context_adapter.py -q`:
  PASS, 5 passed.
- `hatch run type-check`: PASS, 0 errors; repository baseline warnings remain.
- `hatch run lint`: PASS, pylint 10.00/10.
- `hatch run yaml-lint`: PASS.
- `hatch run python -m crosshair check src/specfact_cli/requirements/context.py --per_condition_timeout=5 --analysis_kind=icontract`:
  PASS.
- `hatch run specfact code review run --json --out /tmp/req02-code-review-final.json --scope full --path src/specfact_cli/requirements/context.py`:
  PASS, no findings.
- `git diff --check`: PASS.

## CI Compatibility Fix Verification

- **Timestamp (Europe/Berlin):** 2026-07-08T22:07:05+02:00
- `hatch run pytest tests/unit/registry/test_module_grouping.py tests/unit/requirements/test_context_adapter.py -q`:
  PASS, 14 passed.
- `hatch run python` discovery reproduction against fetched
  `nold-ai/specfact-cli-modules` branch `feature/requirements-02-module-commands`:
  PASS, discovered 7 packages and normalized `nold-ai/specfact-requirements`
  to category/group `requirements`.
- `openspec validate requirements-02-module-commands --strict`: PASS.
- `hatch run type-check`: PASS, 0 errors; repository baseline warnings remain.
- `hatch run lint`: PASS, pylint 10.00/10.
- `hatch run yaml-lint`: PASS.
- `hatch run specfact code review run --json --out /tmp/req02-code-review-final.json --scope changed`:
  PASS, no findings.
- `git diff --check`: PASS.
