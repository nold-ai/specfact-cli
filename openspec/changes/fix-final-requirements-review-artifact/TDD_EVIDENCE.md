# TDD Evidence

## Failing Before

- Timestamp: `2026-09-04T20:13:41Z`
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
  - Run: `33916202294`
  - Artifact: `9953248642` (`requirements-evidence`)
  - Artifact service digest:
    `sha256:5dcc3cf87e2a5aca09b9281d324793c4327a23c484f07becdc608efa650d38eb`
  - Commit: `2d51d176ebee452ef8778a8dc82c923affcad2a7`
  - Tree: `04a0e04c20048f5ee7606083880141475806c042`
  - Merge base: `1d9491595eb4ba0d6cc55823710d9d2e36a21b16`
  - JUnit SHA-256:
    `73003797de79c263aac9c328f2145df290609cc05877ac638ada9f7297f690e9`
  - Selected test-file SHA-256:
    `a9a0e68b21c508e931832f11e69fd09fbc73b64f76a9f5fdbd4012a25610cb33`
  - Normalized plan digest:
    `sha256:61959eff7a8610db6ba8f302836ccc9051b81aaa3802ca72735caf4a69677493`
  - Result: exactly three mapped failures; lifecycle maturity `red`,
    `failing-first-proven`, with no provenance findings.

## Passing After

- Timestamp: `2026-09-04T20:28:26Z`
- Environment: macOS, Python 3.12.13, pytest 9.1.1
- Scope: the three mapped selectors plus the complete
  `test_trustworthy_green_checks.py` workflow contract suite.
- Result: mapped selectors `3 passed`; complete file `58 passed`.
- Workflow controls: actionlint passed; repository YAML validation passed with
  only the already-known unrelated legacy baseline diagnostics.
- Strict OpenSpec validation: passed.
- Evidence: no-target review records fixed `false` before discovery and exits
  before the fixed `true` marker; Python targets record `true` before Code
  Review; upload remains pinned and strict, while failed-review enforcement is
  unchanged.
- GitHub final Requirements and full quality/security results: pending the
  implementation commit.
