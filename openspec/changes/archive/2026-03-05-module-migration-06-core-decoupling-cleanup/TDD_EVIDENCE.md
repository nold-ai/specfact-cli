# TDD Evidence: module-migration-06-core-decoupling-cleanup

## Task 2: Spec and tests first (TDD)

### 2.2 Boundary test: core must not import from bundle packages

**Test:** `tests/unit/specfact_cli/test_module_boundary_imports.py::test_core_does_not_import_from_bundle_packages`

#### Pre-implementation (failing) evidence

Temporary violation added to `src/specfact_cli/registry/bootstrap.py`:

```python
from backlog_core.main import backlog_app  # noqa: F401
```

**Command:** `hatch run pytest tests/unit/specfact_cli/test_module_boundary_imports.py::test_core_does_not_import_from_bundle_packages -v`

**Result:** FAILED

```
AssertionError: Core must not import from bundle packages (backlog_core, bundle_mapper).
  - src/specfact_cli/registry/bootstrap.py: from backlog_core.main import
```

**Timestamp:** 2026-03-04

#### Post-implementation (passing) evidence

Temporary violation removed. Core has no imports from `backlog_core` or `bundle_mapper`.

**Command:** `hatch run pytest tests/unit/specfact_cli/test_module_boundary_imports.py -v`

**Result:** 3 passed (including `test_core_does_not_import_from_bundle_packages`)

**Timestamp:** 2026-03-04

### Task 3.4 Post-decoupling (passing) evidence

**Command:** `hatch run pytest tests/unit/specfact_cli/test_module_boundary_imports.py tests/unit/backlog/ tests/unit/validators/test_bundle_dependency_install.py -v`

**Result:** 172 passed (including boundary tests)

**Timestamp:** 2026-03-04

Inventory confirmed no move candidates; core already decoupled. Boundary test prevents future coupling.

### Extended scope (Phase 1) — 2026-03-04

**Removed:** `templates.bridge_templates`, `tests/unit/templates/test_bridge_templates.py` (dead code; only tests used it).

**Added:** `test_core_modules_do_not_import_migrate_tier` — core modules must not import MIGRATE-tier paths.

**Command:** `hatch run pytest tests/unit/sync/ tests/unit/templates/ tests/unit/specfact_cli/test_module_boundary_imports.py -v`

**Result:** 127 passed

### Extended scope continuation (sync-runtime unit test migration) — 2026-03-05

#### Pre-implementation (failing) evidence

Added boundary test: `test_core_repo_does_not_host_sync_runtime_unit_tests`.

**Command:** `hatch run pytest tests/unit/specfact_cli/test_module_boundary_imports.py::test_core_repo_does_not_host_sync_runtime_unit_tests -v`

**Result:** FAILED

```
AssertionError: Sync runtime unit tests must be migrated out of specfact-cli into specfact-cli-modules.
  - tests/unit/sync/test_bridge_probe.py
  - tests/unit/sync/test_bridge_sync.py
  - tests/unit/sync/test_bridge_watch.py
  - tests/unit/sync/test_drift_detector.py
  - tests/unit/sync/test_repository_sync.py
  - tests/unit/sync/test_watcher_enhanced.py
```

**Timestamp:** 2026-03-05 08:21:57Z

#### Post-implementation (passing) evidence

Migrated legacy core sync-runtime unit tests from:

- `specfact-cli/tests/unit/sync/test_*.py`

To modules repo:

- `specfact-cli-modules/tests/unit/specfact_project/sync_runtime/test_*.py`

Then removed migrated tests from `specfact-cli` core.

**Core command:** `hatch run pytest tests/unit/specfact_cli/test_module_boundary_imports.py::test_core_repo_does_not_host_sync_runtime_unit_tests -v`

**Core result:** PASSED (1 passed)

**Modules command:** `hatch run pytest tests/unit/specfact_project/sync_runtime -v`

**Modules result:** PASSED (102 passed)
