## module-migration-07-test-migration-cleanup — TDD Evidence

### Phase: baseline capture and failure bucketing

- **Failing-before run**
  - Command: `hatch run smart-test-full`
  - Timestamp: 2026-03-05 11:07:25
  - Result: **FAILED** (`310 failed`, `19 errors`, `2301 passed`, `23 skipped`)
  - Evidence log: `logs/tests/test_run_20260305_110725.log`
  - Bucketed failures:
    - import-path migration: `ModuleNotFoundError` for removed `specfact_cli.modules.<removed-module>` paths in tests and compatibility shims
    - command topology migration: `No such command 'plan'` and other flat-command assumptions
    - signing/script fixtures: malformed PEM (`MalformedFraming`) in publish/signing tests
  - Excluded as unrelated for this change step:
    - broad legacy e2e/integration behavior failures not directly caused by module-path or topology cleanup work in this change slice

### Phase: focused test-first checks for migration buckets

- **Failing-before run**
  - Command: `hatch test -- tests/unit/migration/test_module_migration_07_cleanup.py -v`
  - Timestamp: 2026-03-05 11:12:00
  - Result: **FAILED** (`3 failed`)
  - Failure summary:
    - legacy removed import paths still present
    - flat command expectation strings still present in migration scope
    - deterministic local PEM fixture missing

### Phase: implementation and focused verification

- **Implementation notes**
  - Migrated removed import paths in tests from `specfact_cli.modules.<removed>.src...` to extracted bundle package imports (`specfact_project`, `specfact_backlog`, `specfact_codebase`, `specfact_spec`, `specfact_govern`)
  - Updated compatibility shim modules in `src/specfact_cli/commands/*.py` to bootstrap bundle source roots and import from extracted package commands
  - Added deterministic test PEM fixture: `tests/fixtures/keys/test_private_key.pem`
  - Updated publish-module tests to use deterministic fixture instead of ad-hoc invalid key content
  - Updated migration-related command topology references in tests/docs fixtures to grouped command forms

- **Passing-after run**
  - Command: `hatch test -- tests/unit/migration/test_module_migration_07_cleanup.py tests/unit/scripts/test_publish_module_bundle.py tests/unit/bundles/test_bundle_layout.py tests/unit/commands/test_policy_module_import.py -v`
  - Timestamp: 2026-03-05 11:16:00
  - Result: **PASSED** (`22 passed`)

### Remaining work

- Optional non-test quality gates (`type-check`, `lint`, `contract-test`) are still pending for both repos if required before PR cut.

### Phase: ownership split verification (core vs modules)

- **Failing-before run**
  - Command: `hatch run smart-test-full`
  - Timestamp: 2026-03-05 11:58:03
  - Result: **FAILED** (`22 failed`, `2073 passed`, `1 skipped`)
  - Evidence log: `logs/tests/test_run_20260305_115803.log`
  - Failure summary:
    - legacy topology assertions expecting removed grouped roots (`code`, `spec`)
    - legacy in-core module path assumptions (`specfact_cli.modules.*`)
    - compatibility/registry tests asserting pre-extraction layout

- **Implementation notes**
  - Added explicit core test ownership gate in `tests/conftest.py` to exclude module-owned suites from core collection, with override via `SPECFACT_INCLUDE_MIGRATED_TESTS=1`
  - Removed obsolete plan-topology tests from core (`tests/integration/test_plan_command.py`, `tests/integration/test_directory_structure.py`, and unit plan command suites)
  - Migrated retained `project plan` integration tests into modules repo and marked them retired via `pytestmark` where no supported runtime surface exists
  - Hardened modules test path resolution to prioritize local package sources and avoid cross-repo import shadowing

- **Passing-after run (core)**
  - Command: `hatch run smart-test-full`
  - Timestamp: 2026-03-05 12:00:56
  - Result: **PASSED** (`2026 passed`, `1 skipped`)
  - Evidence log: `logs/tests/test_run_20260305_120056.log`

- **Passing-after run (modules)**
  - Command: `hatch run test -q`
  - Timestamp: 2026-03-05 12:15:00
  - Result: **PASSED** (`141 passed`, `16 skipped`)
  - Failure mode addressed during run:
    - collection-order shadowing for `specfact_project.sync_runtime` resolved by conftest import-order hardening.
