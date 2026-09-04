# TDD Evidence

## Failing Before

- Timestamp: `2026-09-04T20:42:21Z`
- Environment: macOS, Python 3.12.13, pytest 9.1.1
- Workflow baseline: `origin/dev` at
  `1d9491595eb4ba0d6cc55823710d9d2e36a21b16`
- Command:

  ```text
  hatch run python -m pytest -q \
    tests/unit/workflows/test_trustworthy_green_checks.py::test_requirements_final_review_marks_no_python_target_path \
    tests/unit/workflows/test_trustworthy_green_checks.py::test_requirements_final_review_requires_artifact_for_python_targets \
    tests/unit/workflows/test_trustworthy_green_checks.py::test_requirements_final_review_persists_failure_before_enforcement
  ```

- Result: expected failure, `3 failed`.
- Evidence: the review step emits neither fixed output, does not distinguish an
  empty Python diff from a deleted Python path, and uses the unconditional
  `always()` upload rather than an exact required-review check.
- Production workflow remained unchanged while this evidence was captured.
- Formatting and lint controls for the test file passed.
- Mapping acceptance: unedited repository-member issue comment
  <https://github.com/nold-ai/specfact-cli/issues/710#issuecomment-5546332802>
  binds mapping digest
  `sha256:be79411756a4bc65c02d68513b56074b9024876720fbb0f09a9957deb93e57ab`.

## Passing After

Pending implementation.
