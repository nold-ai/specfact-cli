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

## Passing After

Pending implementation.
