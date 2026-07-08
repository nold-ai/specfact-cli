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

## 0.50.2 Root Command Mount Regression

- **Timestamp (Europe/Berlin):** 2026-07-08T23:55:00+02:00
- **Regression:** The `0.50.1` release discovered
  `nold-ai/specfact-requirements` but did not mount the installed native
  `requirements` group at the root CLI. End users could install the marketplace
  module and still fail `specfact requirements --help`.
- **Failing-before command:** `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py::test_requirements_bundle_mounts_native_requirements_root_group tests/unit/cli/test_lean_help_output.py::test_root_group_unknown_requirements_shows_specfact_requirements_module tests/unit/cli/test_lean_help_output.py::test_installed_requirements_module_makes_root_cli_help_callable -q`
- **Failing-before result:** FAIL, expected; 3 failed.
  - `CommandRegistry.get_typer("requirements")` raised
    `ValueError: Command 'requirements' not found`.
  - Missing `requirements` guidance fell through to raw Click
    `No such command 'requirements'`.
  - `specfact requirements --help` exited 2 instead of resolving through the
    installed module app.
- **Production fix:** Added `requirements` to root missing-bundle guidance and
  mapped `specfact-requirements` to the root `requirements` group so the native
  module app is mounted when the bundle is installed.
- **Passing-after command:** `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py::test_requirements_bundle_mounts_native_requirements_root_group tests/unit/cli/test_lean_help_output.py::test_root_group_unknown_requirements_shows_specfact_requirements_module tests/unit/cli/test_lean_help_output.py::test_installed_requirements_module_makes_root_cli_help_callable -q`
- **Passing-after result:** PASS, 3 passed.
- **Focused suite:** `hatch run pytest tests/unit/cli/test_lean_help_output.py tests/unit/specfact_cli/registry/test_module_packages.py tests/unit/registry/test_module_grouping.py tests/unit/requirements/test_context_adapter.py -q`: PASS, 80 passed, 1 skipped.
- **Quality gates:** `hatch run type-check`: PASS, 0 errors; `hatch run lint`: PASS, pylint 10.00/10; `hatch run yaml-lint`: PASS; `git diff --check`: PASS.
- **OpenSpec gate:** `openspec validate requirements-02-module-commands --strict`: PASS.
- **Release gates:** `hatch run python scripts/check_version_sources.py --changed-vs origin/main`: PASS; `SPECFACT_PYPI_VERSION_CHECK_LENIENT_NETWORK=1 hatch run python scripts/check_local_version_ahead_of_pypi.py`: PASS, local `0.50.2` is ahead of PyPI latest `0.50.1`; `hatch build`: PASS, produced `dist/specfact_cli-0.50.2.tar.gz` and `dist/specfact_cli-0.50.2-py3-none-any.whl`.
- **SpecFact code review:** `SEMGREP_SEND_METRICS=off hatch run specfact code review run --json --out /tmp/req02-0502-code-review-rerun.json --scope changed`: PASS_WITH_ADVISORY, no blocking findings on changed lines. Advisory contents are pre-existing unchanged-line findings plus local semgrep CA-store and sandbox pylint tool errors; standalone lint passed outside the sandbox.
- **PR #635 review follow-up:** Codex review noted that root help advertised `specfact init` for requirements, while `specfact init --install requirements` was still rejected and `--install all` omitted `specfact-requirements`.
  - Failing-before command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py::test_install_requirements_alias_resolves_to_requirements_bundle tests/unit/modules/init/test_first_run_selection.py::test_install_all_resolves_to_all_workflow_bundles -q`
  - Failing-before result: FAIL, expected; `requirements` raised `Unknown bundle`, and `all` omitted `specfact-requirements`.
  - Passing-after command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py tests/unit/modules/init/test_mandatory_bundle_selection.py tests/unit/specfact_cli/registry/test_profile_presets.py -q`: PASS, 46 passed.
