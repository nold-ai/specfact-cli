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
  - Notes: Removed _register_category_groups_and_shims (unconditional category/shim registration). CORE_MODULE_ORDER trimmed to 4 core (init, auth, module-registry, upgrade). _mount_installed_category_groups already used when category_grouping_enabled; added @beartype. Bootstrap registers only discovered packages; category groups and flat shims only for installed bundles.

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
  - Notes: VALID_PROFILES and PROFILE_BUNDLES in commands.py. init_command has @require(profile in VALID_PROFILES). _install_profile_bundles(profile) and _install_bundle_list(install_arg) implemented with @beartype; CI/CD gate and interactive first-run flow unchanged and passing.

### Phase: Task 14 — Module signing gate

- **Verification run (passing)**
  - Command: `hatch run ./scripts/verify-modules-signature.py --require-signature`
  - Timestamp: 2026-03-02
  - Result: **exit 0** — 6 manifest(s) verified (4 core: init, auth, module_registry, upgrade; 2 bundled: backlog-core, bundle-mapper).
  - Notes: No re-sign required; 14.2 and 14.4 N/A.

