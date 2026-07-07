# TDD Evidence: requirements-01-data-model

## Failing-before

- **Timestamp (Europe/Berlin):** 2026-07-07T22:24:00+02:00
- **Command:** `hatch run pytest tests/unit/models/test_requirements.py tests/unit/models/test_schema_extensions.py -q`
- **Result:** FAIL, expected
- **Summary:** Pytest collected zero tests and failed during collection because
  `specfact_cli.models.requirements` does not exist yet.
- **Key error:** `ModuleNotFoundError: No module named 'specfact_cli.models.requirements'`

## Passing-after

- **Timestamp (Europe/Berlin):** 2026-07-07T22:39:00+02:00
- **Command:** `hatch run pytest tests/unit/models/test_requirements.py tests/unit/models/test_schema_extensions.py -q`
- **Result:** PASS
- **Summary:** 20 targeted unit tests passed, covering requirement input
  serialization, missing `schema_version`, required source references, advisory
  completeness findings, ProjectBundle extension payload round-tripping, and
  contract-boundary rejection of invalid extension payloads.

## Quality Gates

- **Timestamp (Europe/Berlin):** 2026-07-07T22:43:00+02:00
- **Result:** PASS for changed scope and required metadata gates.
- **Commands:**
  - `openspec validate requirements-01-data-model --strict`
  - `hatch run pytest tests/unit/models/test_requirements.py tests/unit/models/test_schema_extensions.py -q`
  - `hatch run type-check`
  - `hatch run lint`
  - `hatch run contract-test`
  - `hatch run check-version-sources`
  - `hatch run check-pypi-ahead`
  - `hatch run verify-modules-signature`
  - `hatch run semgrep-sast`
  - `hatch run semgrep-sast-gate --results /tmp/specfact-requirements-01-semgrep.json --baseline tools/semgrep/sast-baseline.json`
  - `hatch run bandit-scan`
  - `hatch run smart-test`
  - `hatch run specfact code review run --json --out /tmp/req01-code-review-final.json --scope changed`
- **Review summary:** SpecFact code review returned `overall_verdict: PASS`,
  `ci_exit_code: 0`, `score: 120`, and zero findings after the contract-boundary
  remediation.

## Full Suite Remediation

- **Timestamp (Europe/Berlin):** 2026-07-07T23:27:13+02:00
- **Command:** `hatch run smart-test`
- **Result:** PASS.
- **Summary:** 2785 tests passed, 11 skipped, and 2 third-party deprecation
  warnings remained. The earlier 9 baseline failures were fixed by resolving
  analyzer entry-point paths before repository containment checks, tolerating Rich
  output wrapping in the module init assertion, and preventing ambient
  project-scoped modules from leaking into explicitly scoped discovery tests.
  The analyzer integration and E2E tests intentionally keep raw
  `TemporaryDirectory()` paths, and
  `TestCodeAnalyzer::test_resolve_entry_point_accepts_canonical_path_alias`
  covers symlink/canonical-path aliases without hard-coded `/var` or
  `/private/var` assumptions.
- **Log:** `logs/tests/test_run_20260707_232713.log`.

## Final Review Notes

- **Timestamp (Europe/Berlin):** 2026-07-07T23:32:17+02:00
- **Command:** `SPECFACT_MODULES_ROOTS=/Users/dom/git/nold-ai/specfact-cli-modules/packages hatch run specfact code review run --json --out /tmp/req01-code-review-final3.json --scope changed`
- **Result:** PASS_WITH_ADVISORY, `ci_exit_code: 0`, `score: 95`.
- **Summary:** Changed-line enforcement found no blocking findings. The remaining
  advisories are pre-existing whole-file KISS/AI-bloat findings in
  `src/specfact_cli/analyzers/code_analyzer.py`; the production path-resolution
  fix was retained to avoid masking OS-specific path alias failures in tests.
