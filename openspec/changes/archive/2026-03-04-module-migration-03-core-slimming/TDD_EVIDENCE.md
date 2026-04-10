## module-migration-03-core-slimming — TDD Evidence

### Phase: module-removal gate script (verify-bundle-published.py)

- **Failing-before run**
  - Command: `hatch test -- tests/unit/scripts/test_verify_bundle_published.py -v`
  - Timestamp: 2026-03-02
  - Result: **FAILED**
  - Notes: Initial run failed because `scripts/verify-bundle-published.py` did not yet exist. Tests were added first per TDD requirements.

- **Passing-after run**
  - Command: `hatch test -- tests/unit/scripts/test_verify_bundle_published.py -v`
  - Timestamp: 2026-03-02
  - Result: **PASSED**
  - Notes: Implemented `scripts/verify-bundle-published.py` with `verify_bundle_published` orchestrator, contract decorators, and supporting helpers. All gate script unit tests now pass.

### Phase: bootstrap 4-core-only, init mandatory selection, lean help, packaging (tasks 5–8)

- **Failing-before run**
  - Command: `hatch test -- tests/unit/registry/test_core_only_bootstrap.py tests/unit/modules/init/test_mandatory_bundle_selection.py tests/unit/cli/test_lean_help_output.py tests/unit/packaging/test_core_package_includes.py -v`
  - Timestamp: 2026-03-02
  - Result: **3 failed, 13 passed, 4 skipped**
  - Failures:
    - `test_register_builtin_commands_registers_only_four_core_when_discovery_returns_four`: category groups (backlog, code, project, spec, govern) still registered via _register_category_groups_and_shims when only 4 core discovered.
    - `test_bootstrap_does_not_register_extracted_modules_when_only_core_discovered`: same; extracted commands still in list until bootstrap mounts only installed bundles.
    - `test_bootstrap_calls_mount_installed_category_groups`: bootstrap.py does not yet call _mount_installed_category_groups or get_installed_bundles.
  - Skipped (expected until implementation): get_installed_bundles not implemented; category groups conditional on installed bundles; CI/CD gate in init; lean help hint.
  - Notes: Tests added per tasks 5–8. Implementation will: (1) add get_installed_bundles and _mount_installed_category_groups; (2) register only 4 core from builtin and mount category groups only when bundle installed; (3) enforce init CI/CD gate and lean help.

- **Passing-after run**
  - Command: `hatch test -- tests/unit/registry/test_core_only_bootstrap.py tests/unit/modules/init/test_mandatory_bundle_selection.py tests/unit/cli/test_lean_help_output.py tests/unit/packaging/test_core_package_includes.py -v`
  - Timestamp: 2026-03-02
  - Result: **18 passed, 2 skipped**
  - Notes: Implemented `get_installed_bundles(packages, enabled_map)`, `_build_bundle_to_group()`, and `_mount_installed_category_groups(packages, enabled_map)` in `module_packages.py`. Replaced unconditional `_register_category_groups_and_shims()` with `_mount_installed_category_groups()` when category_grouping_enabled. Bootstrap now registers only discovered packages (4 core when discovery returns 4) and mounts category groups (code, backlog, project, spec, govern) only for installed bundles. Skipped tests: init CI/CD gate (task 6), lean help when all modules still in tree (satisfied after Phase 1 deletion).

### Phase: Task 6 — Init CI/CD gate (mandatory bundle selection)

- **Passing-after run**
  - Command: `hatch test -- tests/unit/modules/init/test_mandatory_bundle_selection.py -v`
  - Timestamp: 2026-03-02
  - Result: **4 passed**
  - Notes: Enforced CI/CD gate in `init` command: when `is_first_run()` and `is_non_interactive()` and neither `--profile` nor `--install` is provided, init now exits 1 with message "In CI/CD (non-interactive) mode, first-run init requires --profile or --install to select workflow bundles." All four mandatory-bundle-selection tests pass.

### Phase: Task 9 — Pre-deletion gate (verify-removal-gate)

- **Pre-deletion gate run (passing)**
  - Command: `hatch run verify-removal-gate`
  - Timestamp: 2026-03-02
  - Result: **exit 0**
  - Output: Registry branch auto-detected **dev**; all 17 modules PASS (signature OK, download OK). `verify-modules-signature.py --require-signature`: 23 module manifests OK.
  - Notes: Gate uses `scripts/verify-bundle-published.py` with branch auto-detection (and optional `--branch dev|main`). Download URLs resolved via `resolve_download_url` against specfact-cli-modules dev registry. Phase 1 (Task 10) deletions may proceed.

### Phase: Task 10 — Phase 1 deletions (package includes)

- **Passing-after run**
  - Command: `hatch test -- tests/unit/packaging/test_core_package_includes.py -v`
  - Timestamp: 2026-03-02
  - Result: **4 passed**
  - Notes: All 17 non-core module directories deleted in 5 commits (specfact-project, specfact-backlog, specfact-codebase, specfact-spec, specfact-govern). Only 4 core modules remain (init, auth, module_registry, upgrade). Packaging tests confirm pyproject/setup/version sync and no force-include references to deleted modules.

### Phase: Task 11 — Phase 2 (bootstrap)

- **Passing-after run**
  - Command: `hatch test -- tests/unit/registry/test_core_only_bootstrap.py -v`
  - Timestamp: 2026-03-02
  - Result: **7 passed**
  - Notes: Removed _register_category_groups_and_shims (unconditional category/shim registration). CORE_MODULE_ORDER trimmed to 4 core (init, auth, module-registry, upgrade)._mount_installed_category_groups already used when category_grouping_enabled; added @beartype. Bootstrap registers only discovered packages; category groups and flat shims only for installed bundles.

### Phase: Task 12 — Phase 3 (cli.py)

- **Passing-after run**
  - Command: `hatch test -- tests/unit/cli/test_lean_help_output.py -v`
  - Timestamp: 2026-03-02
  - Result: **5 passed**
  - Notes: Root app uses _RootCLIGroup (extends ProgressiveDisclosureGroup). Unrecognised commands that match KNOWN_BUNDLE_GROUP_OR_SHIM_NAMES show actionable error (not installed + specfact init / specfact module install). Main help docstring includes init/module install hint for workflow bundles.

### Phase: Task 13 — Phase 4 (init mandatory selection)

- **Passing-after run**
  - Command: `hatch test -- tests/unit/modules/init/test_mandatory_bundle_selection.py -v`
  - Timestamp: 2026-03-02
  - Result: **4 passed**
  - Notes: VALID_PROFILES and PROFILE_BUNDLES in commands.py. init_command has @require(profile in VALID_PROFILES). _install_profile_bundles(profile) and_install_bundle_list(install_arg) implemented with @beartype; CI/CD gate and interactive first-run flow unchanged and passing.

### Phase: Task 14 — Module signing gate

- **Verification run (passing)**
  - Command: `hatch run ./scripts/verify-modules-signature.py --require-signature`
  - Timestamp: 2026-03-02
  - Result: **exit 0** — 6 manifest(s) verified (4 core: init, auth, module_registry, upgrade; 2 bundled: backlog-core, bundle-mapper).
  - Notes: No re-sign required; 14.2 and 14.4 N/A.

### Phase: Task 15 — Integration and E2E tests (core slimming)

- **Passing run**
  - Command: `hatch test -- tests/integration/test_core_slimming.py tests/e2e/test_core_slimming_e2e.py -v`
  - Timestamp: 2026-03-02
  - Result: **10 passed, 1 skipped**
  - Notes: `tests/integration/test_core_slimming.py` (8 tests): fresh install 4-core, backlog group mounted, init profiles (solo/enterprise/install all), flat shims plan/validate, init CI/CD gate. `tests/e2e/test_core_slimming_e2e.py` (3 tests): init solo-developer then code in registry, init api-first-team (spec/contract skip when stub), fresh install ≤6 commands. Assertions use CommandRegistry.list_commands() after re-bootstrap because root app is built at import time.

### Phase: module-removal gate hardening + loader/signature follow-up (2026-03-03)

- **Failing-before run**
  - Command: `hatch test -- tests/unit/scripts/test_verify_bundle_published.py tests/unit/specfact_cli/registry/test_module_packages.py::test_unaffected_modules_register_when_one_fails_trust tests/unit/specfact_cli/registry/test_module_packages.py::test_integrity_failure_shows_user_friendly_risk_warning -v`
  - Timestamp: 2026-03-03
  - Result: **8 failed, 7 passed**
  - Failure summary:
    - Gate script lacked `check_bundle_in_registry` and still relied on permissive `signature_ok` metadata.
    - Beartype return checks surfaced instability in repeated script loading during tests.
    - Pre-existing registry tests depended on global `SPECFACT_ALLOW_UNSIGNED=1` test env default and did not force strict mode.

- **Passing-after run**
  - Command: `hatch test -- tests/unit/scripts/test_verify_bundle_published.py tests/unit/specfact_cli/registry/test_module_packages.py::test_unaffected_modules_register_when_one_fails_trust tests/unit/specfact_cli/registry/test_module_packages.py::test_integrity_failure_shows_user_friendly_risk_warning -v`
  - Timestamp: 2026-03-03
  - Result: **15 passed**
  - Notes:
    - Added explicit `check_bundle_in_registry(...)` validation path for required registry fields.
    - Added artifact-based `verify_bundle_signature(...)` flow in gate script (checksum + extracted manifest verification via installer verifier, requiring signature when verification can be executed).
    - Updated the two pre-existing `module_packages` tests to call `register_module_package_commands(allow_unsigned=False)` so trust/integrity assertions are deterministic and independent of global test env defaults.

### Phase: docs alignment + quality gate refresh (2026-03-03)

- **Quality gate runs**
  - `hatch run format` -> **PASSED**
  - `hatch run type-check` -> **PASSED** (warnings-only baseline remains)
  - `hatch run yaml-lint` -> **PASSED**
  - `hatch run contract-test` -> **PASSED** (cached, no modified files path)
  - `hatch run smart-test` -> **FAILED** due stale cached coverage path (`0.0% coverage`); no new test regression signal from this run.

- **Docs parity verification**
  - Command: `hatch test -- tests/unit/docs/test_release_docs_parity.py -v`
  - Result: **3 passed**
  - Notes: Updated `docs/reference/commands.md` to retain legacy patch apply strings required by release-doc parity checks while documenting new grouped command topology.

### Phase: installed-bundle group mounting and namespaced loader regression (2026-03-03)

- **Failing-before run**
  - Command:
    - `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py::test_make_package_loader_supports_namespaced_nested_command_app tests/unit/registry/test_core_only_bootstrap.py::test_mount_installed_category_groups_does_not_mount_code_when_codebase_not_installed -v`
    - `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py::test_get_installed_bundles_infers_bundle_from_namespaced_module_name -v`
  - Result: **FAILED**
  - Failure summary:
    - `_make_package_loader` could not load namespaced command app entrypoints (`src/<pkg>/<command>/app.py`) when root `src/app.py` was absent.
    - `_mount_installed_category_groups` registered category groups even when no bundle was installed (e.g. `code` appeared in core-only state).
    - `get_installed_bundles` missed installed namespaced bundles when manifest omitted `bundle` field (`nold-ai/specfact-backlog`).

- **Passing-after run**
  - Command:
    - `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py tests/unit/registry/test_core_only_bootstrap.py -v`
    - `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py::test_make_package_loader_supports_namespaced_nested_command_app tests/unit/specfact_cli/registry/test_module_packages.py::test_get_installed_bundles_infers_bundle_from_namespaced_module_name tests/unit/registry/test_core_only_bootstrap.py::test_mount_installed_category_groups_does_not_mount_code_when_codebase_not_installed -q`
  - Result: **PASSED** (`46 passed` in full targeted files; focused rerun `3 passed`)
  - Notes:
    - Category groups now mount only for installed bundles.
    - Namespaced loader resolves command-specific entrypoints for marketplace bundles.
    - Bundle detection infers `specfact-*` bundle IDs from namespaced module names when `bundle` is absent.
    - Manual CLI verification:
      - `specfact -h` shows core + `backlog` only when backlog bundle is installed.
      - `specfact backlog -h` resolves real backlog commands (no placeholder-only `install` fallback).

### Phase: quality-gate rerun for migration-03 closeout (2026-03-03)

- **Lint rerun**
  - Command: `hatch run lint`
  - Timestamp: 2026-03-03
  - Result: **FAILED** in restricted sandbox environment
  - Failure summary:
    - One run reached lint tooling and surfaced pre-existing baseline issues in unrelated large modules.
    - Re-run with writable cache env failed earlier during Hatch dependency sync because `pip-tools` could not be downloaded (`Name or service not known`).

- **Smart-test rerun**
  - Command: `hatch run smart-test`
  - Timestamp: 2026-03-03
  - Result: **FAILED** in restricted sandbox environment
  - Failure summary:
    - Hatch dependency sync failed before tests executed because `pip-tools` could not be downloaded (`Name or service not known`).

### Phase: change-to-github export wrapper (2026-03-03)

- **Failing-before run**
  - Command: `hatch test -- tests/unit/scripts/test_export_change_to_github.py -v`
  - Timestamp: 2026-03-03
  - Result: **FAILED** (`4 failed`)
  - Failure summary:
    - Wrapper script `scripts/export-change-to-github.py` did not exist.
    - Tests failed with `FileNotFoundError` while loading script module.

- **Passing-after run**
  - Command: `hatch test -- tests/unit/scripts/test_export_change_to_github.py -v`
  - Timestamp: 2026-03-03
  - Result: **PASSED** (`4 passed`)
  - Notes:
    - Added `scripts/export-change-to-github.py` wrapper for `specfact sync bridge --adapter github --mode export-only`.
    - Added `--inplace-update` option that maps to `--update-existing`.
    - Added hatch alias `hatch run export-change-github -- ...`.

### Phase: task 10.6 auth removal from core (2026-03-04)

- **Failing-before run**
  - Command: `hatch test -- tests/unit/packaging/test_core_package_includes.py tests/unit/registry/test_core_only_bootstrap.py tests/unit/cli/test_lean_help_output.py -v`
  - Timestamp: 2026-03-04
  - Result: **FAILED** (`1 failed, 14 passed, 1 skipped`)
  - Failure summary:
    - `tests/unit/cli/test_lean_help_output.py::test_specfact_help_fresh_install_contains_core_commands` failed because top-level `auth` still appears in `specfact --help`, proving auth is still registered as a core command before task 10.6 production changes.

- **Passing-after run**
  - Command: `hatch test -- tests/unit/packaging/test_core_package_includes.py tests/unit/registry/test_core_only_bootstrap.py tests/unit/cli/test_lean_help_output.py tests/unit/commands/test_auth_commands.py tests/integration/commands/test_auth_commands_integration.py -v`
  - Timestamp: 2026-03-04
  - Result: **PASSED** (`17 passed, 1 skipped`)
  - Notes:
    - Removed core auth module and shim from `specfact-cli`.
    - Core registry now exposes only `init`, `module`, `upgrade`.
    - Top-level `specfact auth` is no longer available; auth guidance now points to `specfact backlog auth`.
