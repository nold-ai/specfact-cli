# TDD Evidence

## Failing Before

- Timestamp: `2026-09-04T19:15:33Z`
- Environment: macOS, Python 3.12.13, pytest 9.1.1, inherited
  `GITHUB_BASE_REF=main`
- Command:

  ```text
  python -m pytest -q \
    tests/unit/workflows/test_trustworthy_green_checks.py::test_primary_test_process_does_not_inherit_github_base_ref \
    tests/unit/workflows/test_trustworthy_green_checks.py::test_compatibility_test_process_does_not_inherit_github_base_ref \
    tests/unit/workflows/test_trustworthy_green_checks.py::test_only_test_processes_override_github_base_ref
  ```

- Result: expected failure, `3 failed`.
- Evidence: neither run block unsets the inherited value, the compatibility
  step does not declare Bash explicitly, and the negative control found no
  bounded removals.
- GitHub retained RED proof:
  - Run: `33910361233`
  - Artifact: `9951113546` (`requirements-evidence`)
  - Commit: `597edd1d3c07b3979c03eede1926d75785f8d16e`
  - Tree: `d74d2d7b49556a761e6f3e1ce7ba8819613e68a8`
  - JUnit SHA-256:
    `bfceda1f946b3533649a78547fb37d750088449264fc2c2df6e7e168800ba566`
  - Result: exactly three mapped failures; lifecycle maturity `red` with no
    provenance findings.

## Passing After

- Timestamp: `2026-09-04T19:19:19Z`
- Environment: macOS, Python 3.12.13, pytest 9.1.1; outer process started with
  `GITHUB_BASE_REF=main`, then the same Bash `unset GITHUB_BASE_REF` boundary
  used by CI executed before pytest.
- Scope: the three mapped workflow selectors plus
  `test_check_version_sources_reuses_branch_release_for_dependency_follow_up`
  and
  `test_check_version_sources_rejects_staged_changelog_deletion_during_follow_up`.
- Result: `5 passed in 1.11s`.
- Evidence: both test launchers require the shell-level removal, the negative
  control permits it at exactly those two steps, and both original
  version-source regressions pass without changing their helper or production
  version logic.
