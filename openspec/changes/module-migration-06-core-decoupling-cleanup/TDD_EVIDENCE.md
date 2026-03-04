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
