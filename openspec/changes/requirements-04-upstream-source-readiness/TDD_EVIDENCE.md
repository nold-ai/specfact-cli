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
- **Result:** 44 passed.
- **Summary:** The pinned v0.12.18 scaffold, incomplete Functional
  Requirements, placeholder Functional Requirements, sources with no user
  story, scenarios outside a user story, invalid native validator results,
  timeouts, and unavailable validators now fail atomically. Enterprise aliases
  and layered policy overrides are covered, while portable imports do not probe
  an ambient executable.

## Quality evidence

- `hatch run format`, `hatch run lint`, `hatch run yaml-lint`, and
  `hatch run contract-test`: passed. `hatch run lint` includes the repository
  basedpyright type-check gate.
- `hatch run smart-test-full`: 2,869 tests passed and 9 skipped; the local
  full-suite line coverage is 64%, above the configured 50% threshold. The
  PR runner independently measures 68.57% for its coverage artifact.
- `hatch run smart-test`: focused-change execution passed; it is not used as
  the full-suite coverage assertion.
- `hatch run semgrep-sast --json --output logs/static-analysis/semgrep.json`,
  `hatch run semgrep-sast-gate --results logs/static-analysis/semgrep.json
  --baseline tools/semgrep/sast-baseline.json`, and `hatch run bandit-scan -f
  json -o logs/static-analysis/bandit.json`: passed with no blocking findings.
- `hatch run python scripts/pre_commit_code_review.py ...`: passed with zero
  findings; report written to `.specfact/code-review.json`.
