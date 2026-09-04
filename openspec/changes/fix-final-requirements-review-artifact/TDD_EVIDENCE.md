# TDD Evidence

## Failing Before

- Timestamp: `2026-09-04T21:06:28Z`
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
- Evidence: the review step emits neither fixed output, and the upload condition
  is the unconditional `always()` rather than an exact required-review check.
- Production workflow remained unchanged while this evidence was captured.
- Formatting and lint controls for the test file passed.
- Mapping acceptance: unedited repository-member issue comment
  <https://github.com/nold-ai/specfact-cli/issues/710#issuecomment-5545980847>
  binds mapping digest
  `sha256:e7354c1071e98cab25b4990b410a40d68865fb57911371b02046d62b50c2c0c1`.
- GitHub retained RED proof:
  - Run: `33919608690`
  - Artifact: `9954495445` (`requirements-evidence`)
  - Artifact service digest:
    `sha256:d527b0af614e93d36e00c891fe812026974f8c0526e11206c3eef5012f3ba871`
  - Commit: `b9c5d110e72f98a2b2f7e92848930270988b0330`
  - Tree: `0483b892202d12922ce563db1de59095a2afb4f5`
  - Merge base: `1d9491595eb4ba0d6cc55823710d9d2e36a21b16`
  - JUnit SHA-256:
    `0401f12d28155d2a716a0dde3795c2f03f34f3a96489245f7740047aefe1b701`
  - Selected test-file SHA-256:
    `f3c11619b3b12a597bd3d8fdae343e10e93de264d52badefe375eac15d7ae180`
  - Normalized plan digest:
    `sha256:61959eff7a8610db6ba8f302836ccc9051b81aaa3802ca72735caf4a69677493`
  - Result: exactly three mapped failures; lifecycle maturity `red`,
    `failing-first-proven`, with no provenance findings.

## Passing After

- Timestamp: `2026-09-04T21:09:17Z`
- Environment: macOS, Python 3.12.13, pytest 9.1.1
- Result: mapped selectors `3 passed`; complete workflow contract file
  `58 passed`.
- Workflow controls: actionlint passed.
- Strict OpenSpec validation: passed.
- Evidence: the no-existing-target path retains fixed `false`; one or more
  present Python targets record fixed `true` before Code Review; upload remains
  pinned and strict, while failed-review enforcement is unchanged.
- The accepted R07 deletion filter remains unchanged: absent paths are excluded,
  while every present path in a mixed change remains reviewable.
- Full quality, security, and GitHub Requirements results: pending.
