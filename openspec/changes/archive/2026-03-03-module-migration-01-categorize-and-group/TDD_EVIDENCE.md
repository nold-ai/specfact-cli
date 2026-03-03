# TDD Evidence: module-migration-01-categorize-and-group

## Phase 3 — First-run module selection in `specfact init`

### 5.1 Failing tests (pre-implementation)

Tests were written first in `tests/unit/modules/init/test_first_run_selection.py`. Initial run (before implementation) would fail on:

- Profile resolution and install parsing (no `resolve_profile_bundles`, `resolve_install_bundles`, `is_first_run`, or `install_bundles_for_init`).
- CLI tests would fail due to missing `--profile`/`--install` and missing first_run_selection integration.

(Exact failing run not captured; implementation followed immediately after test creation.)

### 5.3 Passing tests (post-implementation)

**Timestamp:** 2026-02-28  
**Command:** `hatch test -- tests/unit/modules/init/test_first_run_selection.py -v`  
**Result:** 16 passed

**Summary:**

- `test_profile_solo_developer_resolves_to_specfact_codebase_only` — profile preset resolution.
- `test_profile_enterprise_full_stack_resolves_to_all_five_bundles` — enterprise preset.
- `test_profile_nonexistent_raises_with_valid_list` — invalid profile raises with valid list.
- `test_install_backlog_codebase_resolves_to_two_bundles` — `--install` parsing.
- `test_install_all_resolves_to_all_five_bundles` — `--install all`.
- `test_install_unknown_bundle_raises` — unknown bundle raises.
- `test_is_first_run_true_when_no_category_bundle_installed` — first-run detection (no category bundle).
- `test_is_first_run_false_when_category_bundle_installed` — first-run false when bundle present.
- `test_init_profile_solo_developer_calls_installer_with_specfact_codebase` — CLI `--profile solo-developer`.
- `test_init_profile_enterprise_full_stack_calls_installer_with_all_five` — CLI `--profile enterprise-full-stack`.
- `test_init_profile_nonexistent_exits_nonzero_and_lists_valid_profiles` — CLI invalid profile exits non-zero.
- `test_init_install_backlog_codebase_calls_installer_with_two_bundles` — CLI `--install backlog,codebase`.
- `test_init_install_all_calls_installer_with_five_bundles` — CLI `--install all`.
- `test_init_install_widgets_exits_nonzero` — CLI unknown bundle exits non-zero.
- `test_init_second_run_skips_first_run_flow` — second run does not call installer when no `--profile`/`--install`.
- `test_spec_bundle_install_includes_project_dep` — `install_bundles_for_init(["specfact-spec"])` installs project dep.

Implementation: `src/specfact_cli/modules/init/src/first_run_selection.py` and `commands.py` (--profile, --install, first_run_selection integration).

### Phase 3 follow-up (5.2.3, 5.2.7)

**Interactive first-run UI (5.2.3):**
- `_interactive_first_run_bundle_selection()` in commands.py: welcome banner (Panel), questionary.select for profile or "Choose bundles manually", questionary.checkbox for manual bundle selection. When first run and interactive and no --profile/--install, init() calls it and installs selected bundles or shows tip if none.
- `BUNDLE_DISPLAY` and `PROFILE_DISPLAY_ORDER` in first_run_selection.py for UI labels.

**Graceful degradation (5.2.7):**
- In `install_bundles_for_init`, each `install_bundled_module` call wrapped in try/except; on exception log warning "Dependency resolver may be unavailable" and re-raise so errors are surfaced.

**Additional tests:**
- `test_init_first_run_interactive_with_selection_calls_installer`: first run + interactive, mock selection returns ["specfact-codebase"], assert install called.
- `test_init_first_run_interactive_no_selection_shows_tip`: first run + interactive, mock selection returns [], assert no install and "Tip" / "module install" in output.

**Run:** `hatch test -- tests/unit/modules/init/test_first_run_selection.py -v` — 18 passed.

## Section 6 — Integration and E2E

**Timestamp:** 2026-02-28  
**Commands:** `hatch test -- tests/integration/test_category_group_routing.py tests/e2e/test_first_run_init.py -v`  
**Result:** 5 passed (3 integration + 2 e2e).

**Integration:** `test_code_analyze_help_exits_zero`, `test_backlog_help_lists_subcommands`, `test_validate_shim_help_exits_zero`.  
**E2E:** `test_init_profile_solo_developer_completes_in_temp_workspace`, `test_after_solo_developer_init_code_analyze_help_available` (install_bundles_for_init mocked).

## Phase 4 — Regression fixes from review (grouped extension merge + project-scoped first-run)

### 4.1 Failing tests (pre-implementation)

**Timestamp:** 2026-02-28 01:00 UTC  
**Command:** `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py::test_grouped_registration_merges_duplicate_command_extensions tests/unit/modules/init/test_first_run_selection.py::test_is_first_run_false_when_project_scoped_category_bundle_installed -v`  
**Result:** 2 failed.

**Failure summary:**

- `test_grouped_registration_merges_duplicate_command_extensions` failed because grouped registration replaced the earlier `backlog` loader; observed commands were only `('ext_cmd',)` and `base_cmd` was missing.
- `test_is_first_run_false_when_project_scoped_category_bundle_installed` failed because `is_first_run()` ignored modules discovered with source `project`, returning `True` for an already-initialized workspace.

### 4.2 Passing tests (post-implementation)

**Timestamp:** 2026-02-28 01:01 UTC  
**Command:** `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py::test_grouped_registration_merges_duplicate_command_extensions tests/unit/modules/init/test_first_run_selection.py::test_is_first_run_false_when_project_scoped_category_bundle_installed -v`  
**Result:** 2 passed.

**Implementation summary:**

- Updated `register_module_package_commands()` grouped path to merge duplicate command loaders via `_make_extending_loader` for module entries (and core root entries), instead of unconditional overwrite.
- Updated `is_first_run()` source filter to include `project` modules in first-run detection.

## Phase 5 — Regression fix from PR 331 (trust failure should not block unaffected legacy module registration)

### 5.1 Failing test (pre-implementation)

**Timestamp:** 2026-02-28 21:07 local  
**Command:** `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py::test_unaffected_modules_register_when_one_fails_trust -v`  
**Result:** 1 failed.

**Failure summary:**

- In grouped mode, a module without `category` metadata was routed into grouped registration, so `good_cmd` was not mounted as flat top-level despite warning text indicating flat mounting.

### 5.2 Passing tests (post-implementation)

**Timestamp:** 2026-02-28 21:09 local  
**Command:** `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py::test_unaffected_modules_register_when_one_fails_trust tests/unit/specfact_cli/registry/test_module_packages.py::test_grouped_registration_merges_duplicate_command_extensions tests/unit/registry/test_module_grouping.py::test_module_package_yaml_without_category_mounts_ungrouped_warning_logged -v`  
**Result:** 3 passed.

**Implementation summary:**

- Updated `register_module_package_commands()` to use grouped registration only when `category_grouping_enabled` is true and module metadata declares `category`.
- Updated grouped-extension unit fixture metadata to include `category="backlog"` so the test reflects migration-era grouped manifests and remains aligned with category-driven grouping semantics.
