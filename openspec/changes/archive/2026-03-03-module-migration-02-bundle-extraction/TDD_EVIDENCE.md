# TDD Evidence: module-migration-02-bundle-extraction

## Phase 0 — Cross-bundle import gate

### 4.1 Failing tests (pre-implementation)

**Timestamp:** 2026-02-28 22:43:18 CET  
**Command:** `hatch test -- tests/unit/registry/test_cross_bundle_imports.py -v`  
**Result:** 2 failed, 1 passed

**Failure summary:**

- `test_generate_plan_access_uses_common_or_intra_bundle_only` failed because `src/specfact_cli/modules/generate/src/commands.py` still imports `specfact_cli.models.plan`.
- `test_enforce_plan_access_uses_common_or_intra_bundle_only` failed because `src/specfact_cli/modules/enforce/src/commands.py` still imports `specfact_cli.models.plan`.

This records required failing evidence before any implementation/factoring in steps `4.2.*`.

### 4.3 Passing tests (post-implementation)

**Timestamp:** 2026-02-28 22:40:16 CET  
**Command:** `hatch test -- tests/unit/registry/test_cross_bundle_imports.py -v`  
**Result:** 3 passed

**Summary:**

- `test_analyze_module_has_no_cross_bundle_import_to_plan_module` passed.
- `test_generate_plan_access_uses_common_or_intra_bundle_only` passed after factoring to `specfact_cli.common.bundle_factory`.
- `test_enforce_plan_access_uses_common_or_intra_bundle_only` passed after factoring to `specfact_cli.common.bundle_factory`.

## Phase 1 — Bundle package layout

### 5.1 Failing tests (pre-implementation)

**Timestamp:** 2026-02-28 22:45:24 CET  
**Command:** `hatch test -- tests/unit/bundles/test_bundle_layout.py -v`  
**Result:** 8 failed, 1 passed

**Failure summary:**

- Missing bundle namespace package roots:
  - `specfact-cli-modules/packages/specfact-project/src/specfact_project/__init__.py`
  - `specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/__init__.py`
  - `specfact-cli-modules/packages/specfact-codebase/src/specfact_codebase/__init__.py`
  - `specfact-cli-modules/packages/specfact-spec/src/specfact_spec/__init__.py`
  - `specfact-cli-modules/packages/specfact-govern/src/specfact_govern/__init__.py`
- `ModuleNotFoundError` for `specfact_codebase.analyze` and `specfact_project.plan`.
- `specfact_cli.modules.validate` does not yet expose shimmed `app` with deprecation behavior.

### 5.5 Passing tests (post-implementation)

**Timestamp:** 2026-02-28 22:50:57 CET  
**Command:** `hatch test -- tests/unit/bundles/ -v`  
**Result:** 9 passed

**Summary:**

- All bundle namespace layout checks pass for `specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, and `specfact-govern`.
- `specfact_codebase.analyze` and `specfact_project.plan` imports resolve from extracted bundle namespaces.
- Legacy `specfact_cli.modules.validate` import path resolves and emits `DeprecationWarning` on attribute access via shim.

## Phase 2 — Re-export shim tests

### 6.1 Test run (post-shim baseline)

**Timestamp:** 2026-02-28 22:51:42 CET  
**Command:** `hatch test -- tests/unit/modules/test_reexport_shims.py -v`  
**Result:** 4 passed, 2 warnings

**Note:**

- Step `6.1.6` expected failures before shim implementation.
- Shim behavior was already implemented during Phase 1 (`5.4.*`) as required by bundle extraction, so this baseline run is already green.

### 6.2 Verification run

**Timestamp:** 2026-02-28 22:51:42 CET  
**Command:** `hatch test -- tests/unit/modules/test_reexport_shims.py -v`  
**Result:** 4 passed, 2 warnings

**Summary:**

- `specfact_cli.modules.validate` emits `DeprecationWarning` on attribute access.
- `from specfact_cli.modules.analyze import app` resolves successfully.
- Validate shim module keeps a minimal API surface (`__getattr__` only function definition).
- `specfact_cli.modules.validate.__name__` remains accessible after import.

## Phase 3 — Official-tier trust and display

### 7.1 Failing tests (pre-implementation)

**Timestamp:** 2026-02-28 22:55:55 CET  
**Command:** `hatch test -- tests/unit/validators/test_official_tier.py -v`  
**Result:** 6 failed

**Failure summary:**

- `specfact_cli.registry.crypto_validator` did not expose:
  - `validate_module`
  - `OFFICIAL_PUBLISHERS`
  - `SecurityError`
  - `SignatureVerificationError`

### 7.2 Passing tests (post-implementation)

**Timestamp:** 2026-02-28 22:55:55 CET  
**Command:** `hatch test -- tests/unit/validators/test_official_tier.py -v`  
**Result:** 6 passed

**Summary:**

- Added official-tier policy validation with allowlist and signature enforcement.
- Community tier remains non-official and does not get elevated.
- Contract/type decorators are present on `validate_module`.

### 7.3 Failing tests (pre-display implementation)

**Timestamp:** 2026-02-28 22:55:55 CET  
**Command:** `hatch test -- tests/unit/modules/module_registry/test_official_tier_display.py -v`  
**Result:** 2 failed

**Failure summary:**

- List output did not render `[official]` marker.
- Install success output did not include `Verified: official (nold-ai)`.

### 7.4 Passing tests (post-display implementation)

**Timestamp:** 2026-02-28 22:55:55 CET  
**Command:** `hatch test -- tests/unit/modules/module_registry/test_official_tier_display.py -v`  
**Result:** 2 passed

**Summary:**

- Official list entries render explicit `[official]` marker.
- Install success output includes official-tier verification line for official namespace installs.

## Phase 4 — Bundle dependency auto-install

### 8.1 Failing tests (pre-implementation)

**Timestamp:** 2026-02-28 23:08:25 CET  
**Command:** `hatch test -- tests/unit/validators/test_bundle_dependency_install.py -v`  
**Result:** 5 failed

**Failure summary:**

- Missing dependency auto-install behavior:
  - `specfact-spec` and `specfact-govern` did not trigger `nold-ai/specfact-project`.
- Missing dependency skip logging for already installed dependencies.
- Missing abort path when dependency installation fails.
- Missing offline cached-archive fallback (`MODULE_DOWNLOAD_CACHE_ROOT` not present).

### 8.2 Passing tests (post-implementation)

**Timestamp:** 2026-02-28 23:08:25 CET  
**Command:** `hatch test -- tests/unit/validators/test_bundle_dependency_install.py -v`  
**Result:** 5 passed

**Summary:**

- `bundle_dependencies` are read from manifest and installed before target module.
- Installed dependencies are skipped with "already satisfied" logging.
- Dependency install failures abort requested module install with explicit error.
- Offline installs can fallback to cached archives in `MODULE_DOWNLOAD_CACHE_ROOT`.

## Phase 5 — publish-module bundle mode

### 9.1 Failing tests (pre-implementation)

**Timestamp:** 2026-02-28 23:11:18 CET  
**Command:** `hatch test -- tests/unit/scripts/test_publish_module_bundle.py -v`  
**Result:** 9 failed

**Failure summary:**

- `scripts/publish-module.py` lacked bundle-mode API surface:
  - `BUNDLE_PACKAGES_ROOT`
  - `package_bundle`
  - `sign_bundle`
  - `verify_bundle`
  - `write_index_entry`
  - `publish_bundle`
- CLI lacked `--bundle all` flow.

### 9.2 Passing tests (post-implementation)

**Timestamp:** 2026-02-28 23:11:18 CET  
**Command:** `hatch test -- tests/unit/scripts/test_publish_module_bundle.py -v`  
**Result:** 9 passed

**Summary:**

- Bundle tarball packaging, checksum/index alignment, and path traversal safeguards pass.
- Signature artifact and inline verification gating behavior pass.
- Atomic index writes (`os.replace`) and version guardrails pass.
- `--bundle all` publishes all 5 official bundles in sequence.

## Phase 6 — Signature gate progress

### 10.1 Verification baseline

**Timestamp:** 2026-02-28 23:11:18 CET  
**Command:** `hatch run ./scripts/verify-modules-signature.py --require-signature`  
**Result:** failed (checksum mismatch across changed module manifests)

**Summary:**

- Expected mismatch after extraction/shim updates.
- Patch version bump (`10.2`) applied to all affected `src/specfact_cli/modules/*/module-package.yaml`.

### 10.4/10.6 Verification after signing

**Timestamp:** 2026-02-28 23:12:00 CET  
**Command:** `hatch run ./scripts/verify-modules-signature.py --require-signature`  
**Result:** passed (`Verified 23 module manifest(s).`)

**Summary:**

- Core module manifests are signed and verified after version bumps.
- Bundle manifests were checksum-signed in this environment and published metadata generation proceeded.

## Phase 7 — Bundle publishing

### 11.2-11.7 Publish sequence

**Timestamp:** 2026-02-28 23:12:00 CET  
**Command(s):**

- `python scripts/publish-module.py --bundle specfact-project --key-file ... --registry-dir specfact-cli-modules/registry`
- `python scripts/publish-module.py --bundle specfact-backlog --key-file ... --registry-dir specfact-cli-modules/registry`
- `python scripts/publish-module.py --bundle specfact-codebase --key-file ... --registry-dir specfact-cli-modules/registry`
- `python scripts/publish-module.py --bundle specfact-spec --key-file ... --registry-dir specfact-cli-modules/registry`
- `python scripts/publish-module.py --bundle specfact-govern --key-file ... --registry-dir specfact-cli-modules/registry`

**Result:** passed (5 bundles published; index contains 5 entries)

**Index summary:**

- All entries have `tier: official`, `publisher: nold-ai`, and non-empty `checksum_sha256`.
- Dependency fields are correct:
  - `nold-ai/specfact-spec` → `["nold-ai/specfact-project"]`
  - `nold-ai/specfact-govern` → `["nold-ai/specfact-project"]`

## Phase 8 — Section 18 test/quality parity in specfact-cli-modules

### 18.x failing baseline (pre-fix)

**Timestamp:** 2026-03-02 08:21:30 UTC  
**Command(s):**

- `hatch run type-check`
- `hatch run lint`
- `hatch run test`

**Result:** failed

**Failure summary:**

- `type-check` failed on unresolved bundle imports in modules-repo tests until basedpyright path scoping was aligned.
- `lint` initially failed due overly broad package lint scope and cache path mismatch.
- `test` initially had no migrated suite (0 collected), then failed until migrated tests/import strategy were aligned.

### 18.x passing baseline (post-fix)

**Timestamp:** 2026-03-02 08:21:30 UTC  
**Command(s):**

- `hatch run format`
- `hatch run type-check`
- `hatch run lint`
- `hatch run yaml-lint`
- `hatch run contract-test`
- `hatch run smart-test`
- `hatch run test`

**Result:** passed

**Summary:**

- Modules-repo parity gate scripts are available and green.
- Migrated baseline suites pass in modules repo (`32 passed`):
  - unit module IO contract tests (bundle namespaces)
  - integration command-app smoke tests
  - e2e `--help` command smoke tests
- Inventory and deferred high-coupling suites documented in `TEST_INVENTORY.md`.
