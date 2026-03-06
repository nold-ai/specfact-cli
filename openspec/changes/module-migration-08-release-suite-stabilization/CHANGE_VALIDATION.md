# Change Validation: module-migration-08-release-suite-stabilization

- Created to own residual red unit/integration/E2E suites after the module migration wave was merged to `dev`.
- Intended implementation boundary: post-migration core runtime regressions plus stale core-side test ownership/command-path expectations.
- Implemented outcome:
  - retained core tests were updated to lean-core semantics,
  - `init` invalid-profile handling now returns CLI-friendly errors instead of contract violations,
  - subprocess CLI smoke tests now run with explicit repo `PYTHONPATH`,
  - migrated bundle suites are skipped centrally in `tests/conftest.py` even when selected directly.
- Validation summary:
  - `tests/unit`: `2050 passed, 1 skipped`
  - `tests/integration`: `143 passed`
  - `tests/e2e`: `41 passed, 1 skipped`
- Follow-up note:
  - module-owned suites remain intentionally excluded from core unless `SPECFACT_INCLUDE_MIGRATED_TESTS=1` is set for migration debugging.
