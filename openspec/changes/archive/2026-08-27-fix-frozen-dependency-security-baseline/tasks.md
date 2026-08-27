# Tasks: fix-frozen-dependency-security-baseline

## 1. Branch and governance readiness

- [x] 1.1 Create `bugfix/686-dependency-security-patch-tdd` in the isolated worktree from refreshed `origin/dev@e3a20f20df440dff49f8c6d1f73375451bea1d8c`; retain superseded PR #687 without rewriting its history.
- [x] 1.2 Create and assign issue #686 with bug/security labels after confirming no existing issue owns the finding.
- [x] 1.3 Verify native issue type, project assignment/status, parent applicability, blockers, and blocked-by relationships before dependency implementation.

## 2. Spec and finding validation

- [x] 2.1 Add the dependency-remediation spec delta and patch design before dependency edits.
- [x] 2.2 Capture the original failing Security Audit and independent advisory evidence in `TDD_EVIDENCE.md`.
- [x] 2.3 Complete the accessible Dependabot, code-scanning, and secret-scanning inventory; classify each finding without dismissing alerts.
- [x] 2.4 Strictly validate this change and record dependency/breaking-change analysis in `CHANGE_VALIDATION.md`.
- [x] 2.5 Add and run a focused failing test for the two tooling-only `pip>=26.2` floors and pip-free core runtime; record the exact failure.

## 3. Frozen dependency remediation

- [x] 3.1 Apply only the validated pip floor and compatible pip-tools, Hatchling, Setuptools, and Twine constraint changes.
- [x] 3.2 Regenerate `uv.lock` and `requirements/ci/locked.txt` using the repository refresh command; inspect the full dependency diff.
- [x] 3.3 Run the failing trigger, alternate audit input, and legitimate frozen install/build control; revise only for confirmed compatibility failures.

## 4. Passing evidence and quality gates

- [x] 4.1 Run the reproducible-delivery checker, `uv lock --check`, license audit, security audit, Bandit, Semgrep, and dependency-trust gates.
- [x] 4.2 Run format, type-check, lint, YAML lint, contract tests, smart tests, focused packaging tests, and release/build validation.
- [x] 4.3 Generate a fresh `.specfact/code-review.json`, resolve every finding, and record the passing review evidence.
- [x] 4.4 Run one independent bypass/regression review of the candidate diff and verify any source-backed hypothesis.

## 5. Documentation and patch release metadata

- [x] 5.1 Review README, docs, landing/navigation, contributor, and security documentation impact; correct stale `SECURITY.md` audit semantics and update only required release/security documentation.
- [x] 5.2 Bump all four canonical version sources from 0.55.1 to 0.55.2 and add the dated CHANGELOG Security entry.
- [x] 5.3 Run version-source, PyPI-ahead, build, twine, signature, and final release-readiness checks.

## 6. Delivery

- [x] 6.1 Preserve the signed dependency-only commits in #688, then integrate
  them without rewriting into combined PR #690 after live checks proved the
  #688/#690 gate dependency cycle.
- [ ] 6.2 Observe required CI/review gates, close only fully remediated review threads, and merge only when policy permits.
- [x] 6.3 Archive this completed change with native `openspec archive fix-frozen-dependency-security-baseline` and apply its canonical spec delta.
- [ ] 6.4 Publish and verify the normal patch GitHub/PyPI release if authorized.
- [ ] 6.5 Refresh or rerun PR #685 checks without modifying its branch, report the resulting Security Audit status, and record the exact C14 baseline commit/tag.

## Post-merge cleanup

- [ ] 7.1 Refresh the internal wiki status from the sibling repository root without modifying existing planning PRs, and remove the completed worktree when safe.
