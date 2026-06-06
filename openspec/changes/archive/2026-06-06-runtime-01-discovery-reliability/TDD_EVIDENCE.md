# TDD Evidence: runtime-01-discovery-reliability

## Scope Decision

- `#552` and `#554` remain in `nold-ai/specfact-cli`: the installed `specfact-codebase` artifact is present, but core runtime loading and diagnostics decide whether `specfact code` is registered and importable.
- `#553` remains in `nold-ai/specfact-cli`: environment-manager detection and `specfact init ide` option handling are core CLI behavior.
- No transfer to `nold-ai/specfact-cli-modules` is required unless implementation proves signed module manifests or payloads must change.

## GitHub Readiness

- Parent feature: `#353 [Feature] Marketplace Module Distribution`.
- Change user story: `#557 [Story] Runtime Discovery Reliability for Installed Modules and Monorepos`.
- Source bug reports: `#552`, `#553`, and `#554`.
- Labels and SpecFact CLI project assignment were present on the reported issues; `#557` was created with `openspec`, `change-proposal`, `marketplace`, `dependencies`, and `module-system` labels and assigned to the SpecFact CLI project with `Todo` status.
- Corrected hierarchy on 2026-05-07: removed direct sub-issue links from bug reports to epic `#285`; linked `#557` under feature `#353`; linked `#557` as blocking `#552`, `#553`, and `#554`; commented source tracking back to all three bug reports.

## Failing Evidence

- `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py::test_installed_group_loader_adds_enabled_dependency_module_src_roots tests/unit/specfact_cli/registry/test_module_packages.py::test_lazy_loader_failure_is_recorded_for_availability_diagnostics tests/unit/utils/test_env_manager.py::TestDetectEnvManager::test_detect_uv_from_path_when_no_project_markers tests/unit/utils/test_env_manager.py::TestDetectEnvManager::test_detect_uv_from_rootless_monorepo_pyproject tests/unit/utils/test_env_manager.py::TestDetectEnvManager::test_detect_uv_from_second_level_monorepo_lock tests/e2e/test_init_command.py::TestInitCommandE2E::test_init_no_warning_with_explicit_uv_env_manager tests/e2e/test_init_command.py::TestInitCommandE2E::test_init_no_warning_with_rootless_monorepo_uv -q`
- Result before production edits: 7 failed. Failures covered installed module dependency `src/` importability, lazy loader failure diagnostics, PATH/monorepo environment detection, and explicit `init ide --env-manager uv`.

## Passing Evidence

- `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py::test_installed_group_loader_adds_enabled_dependency_module_src_roots tests/unit/specfact_cli/registry/test_module_packages.py::test_lazy_loader_failure_is_recorded_for_availability_diagnostics tests/unit/utils/test_env_manager.py::TestDetectEnvManager::test_detect_uv_from_path_when_no_project_markers tests/unit/utils/test_env_manager.py::TestDetectEnvManager::test_detect_uv_from_rootless_monorepo_pyproject tests/unit/utils/test_env_manager.py::TestDetectEnvManager::test_detect_uv_from_second_level_monorepo_lock tests/e2e/test_init_command.py::TestInitCommandE2E::test_init_no_warning_with_explicit_uv_env_manager tests/e2e/test_init_command.py::TestInitCommandE2E::test_init_no_warning_with_rootless_monorepo_uv -q` -> 7 passed.
- `hatch run pytest tests/unit/specfact_cli/registry/test_module_packages.py tests/unit/specfact_cli/registry/test_module_availability.py -q` -> 50 passed.
- `hatch run pytest tests/e2e/test_init_command.py -q` -> 20 passed, 2 warnings.
- `hatch run pytest tests/unit/utils/test_env_manager.py -q` -> 34 passed.
- `hatch run pytest tests/integration/test_bundle_install.py::test_installing_spec_bundle_auto_installs_project_dependency tests/integration/test_bundle_install.py::test_installing_spec_bundle_skips_dependency_when_already_present tests/unit/modules/module_registry/test_commands.py::test_install_command_project_scope_reenable_uses_selected_repo tests/unit/modules/module_registry/test_commands.py::test_install_command_project_scope_installs_to_project_modules_root tests/unit/modules/module_registry/test_official_tier_display.py::test_module_install_reports_verified_official_tier -q` -> 5 passed.
- `hatch run env HOME=/tmp/specfact-test-home-runtime-01 pytest tests/integration/test_core_slimming.py::test_fresh_install_cli_app_registered_commands_only_three_core tests/integration/test_core_slimming.py::test_stale_flat_shim_plan_exits_with_install_instructions tests/unit/cli/test_lean_help_output.py::test_stale_lazy_flat_shim_prints_install_guidance tests/unit/registry/test_category_groups.py::test_bootstrap_with_category_grouping_enabled_registers_group_commands tests/unit/registry/test_category_groups.py::test_bootstrap_with_category_grouping_disabled_still_has_no_flat_shims -q` -> 5 passed.
- Added `scripts/runtime_discovery_smoke.py` and Hatch script `runtime-discovery-smoke` for CI-capable real-world coverage. The script creates an isolated HOME, builds a rootless monorepo fixture from `specfact-cli-demo` when available, adds multiple package-level `pyproject.toml`/lock markers, serves a local file-backed marketplace from `specfact-cli-modules`, installs `nold-ai/specfact-project`, `nold-ai/specfact-codebase`, and `nold-ai/specfact-code-review`, checks upgrade command availability, runs `specfact init ide` with auto and explicit `--env-manager uv`, and verifies installed `specfact code`, `code review run`, and `code import` command loading.
- `.github/workflows/pr-orchestrator.yml` now runs `python scripts/runtime_discovery_smoke.py --launcher direct --launcher pip-editable --launcher uvx` so installer, module discovery, init, and environment-manager regressions fail fast in CI across Hatch/current-interpreter, pip editable, and uvx launch paths.
- `hatch run pytest tests/integration/scripts/test_runtime_discovery_smoke.py -q` -> 1 passed.
- `hatch run runtime-discovery-smoke --modules-repo /home/dom/git/nold-ai/specfact-cli-modules --demo-repo /home/dom/git/nold-ai/specfact-demo-repo --launcher direct` -> passed against a real demo-repo copy and sibling module artifacts.
- `hatch run runtime-discovery-smoke --modules-repo /home/dom/git/nold-ai/specfact-cli-modules --demo-repo /home/dom/git/nold-ai/specfact-demo-repo --launcher pip-editable` -> passed with a temporary editable install and isolated module HOME.
- `hatch run runtime-discovery-smoke --modules-repo /home/dom/git/nold-ai/specfact-cli-modules --demo-repo /home/dom/git/nold-ai/specfact-demo-repo --launcher uvx` -> passed with `uvx --from <repo>` and isolated module HOME.
- `openspec validate runtime-01-discovery-reliability --strict` -> valid.
- `hatch run format` -> all checks passed.
- `hatch run type-check` -> 0 errors, 1572 existing repository-wide warnings.
- Touched-file `ruff format --check`, `ruff check`, and `pylint` -> clean; Pylint rated touched files 10.00/10.
- `hatch run workflows-lint` -> passed.
- `hatch run contract-test` -> no modified files detected; cached results used.
- `hatch run smart-test-auto` attempted a full baseline because no incremental baseline existed; it failed in the local developer HOME due pre-existing installed user modules being discovered by clean-runtime tests. The same failed subset passed with an isolated HOME, and all change-targeted suites passed.
- SpecFact code review: `SPECFACT_MODULES_ROOTS=/home/dom/git/nold-ai/specfact-cli-modules/packages hatch run python -m specfact_cli.cli code review run --json --out .specfact/code-review.runtime-01.changed.json --scope changed` -> 0 blocking findings; 499 warnings remain, dominated by existing repository-wide type-safety warnings. New contract warnings introduced by this change were fixed before the final run.
