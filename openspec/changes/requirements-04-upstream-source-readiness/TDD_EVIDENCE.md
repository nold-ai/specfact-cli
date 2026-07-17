# TDD Evidence: requirements-04-upstream-source-readiness

## Failing-before

- **Date:** 2026-07-17 (Europe/Berlin)
- **Command:** `hatch run test -- tests/unit/requirements/test_upstream_evidence_imports.py`
- **Result:** 6 failed, 22 passed.
- **Expected failures:** the pristine v0.12.18 Spec Kit scaffold emitted six
  placeholder records; incomplete Spec Kit sources returned the prior
  compatibility result or partial records; and native-validation tests could
  not exercise a policy-gated subprocess because that behavior did not exist.
- **Non-blocking environment warnings:** pytest could not write its cache in
  the sandboxed feature worktree.

## Passing-after

- **Date:** 2026-07-17 (Europe/Berlin)
- **Command:** `hatch run test -- tests/unit/requirements/test_upstream_evidence_imports.py`
- **Result:** 41 passed.
- **Summary:** The pinned v0.12.18 scaffold, incomplete Functional
  Requirements, user stories without Given/When/Then scenarios, invalid native
  validator results, timeouts, and unavailable validators now fail atomically.
  Enterprise aliases and layered policy overrides are covered, while portable
  imports do not probe an ambient executable.

## Quality evidence

- `hatch run format`, `hatch run lint`, `hatch run yaml-lint`, and
  `hatch run contract-test`: passed.
- `hatch run smart-test`: 2,856 tests passed, 64% coverage (50% threshold).
- `hatch run semgrep-sast --json --output logs/static-analysis/semgrep.json`,
  `hatch run semgrep-sast-gate --results logs/static-analysis/semgrep.json
  --baseline tools/semgrep/sast-baseline.json`, and `hatch run bandit-scan -f
  json -o logs/static-analysis/bandit.json`: passed with no blocking findings.
- `hatch run python scripts/pre_commit_code_review.py ...`: passed with zero
  findings; report written to `.specfact/code-review.json`.
