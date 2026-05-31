# TDD Evidence: tester-cli-reliability

## Readiness

- Worktree: `/home/dom/git/nold-ai/specfact-cli-worktrees/feature/tester-command-reliability`
- Branch: `feature/tester-command-reliability`
- Core tracking story: nold-ai/specfact-cli#594
- Paired modules story: nold-ai/specfact-cli-modules#306

## Source Ownership

- `#585` stays core: root unknown-command guidance.
- `#586` is module-owned: `specfact project regenerate` runtime hardening.
- `#587` splits: core module discovery/missing-module guidance, modules canonical `project sync bridge` docs/help.
- `#588` splits: core docs/guidance validation, modules `code import` command contract.
- `#589` stays core: upgrade effective-runner detection.
- `#590` splits: core shared tool/env probing, modules codebase/code-review adoption.
- `#591` is module-owned under the shared CLI error contract.
- `#592` is module-owned backlog delta status contract.
- `#593` stays core: pipx upgrade must validate and repair stale/broken `specfact` launchers after reported success.

## Failing Before

- `hatch run pytest tests/unit/cli/test_error_guidance.py tests/unit/commands/test_update.py::TestInstallationMethodDetection::test_detect_uv_run_before_stale_pipx_inventory tests/unit/utils/test_env_manager.py::TestCheckToolInEnv::test_check_tool_probes_active_uv_environment tests/unit/docs/test_docs_validation_scripts.py::test_code_import_options_after_bundle_are_rejected tests/unit/docs/test_docs_validation_scripts.py::test_core_cli_modes_page_is_not_excluded_from_command_validation -q` -> 3 failed, 2 passed before production edits.
  - `test_check_tool_probes_active_uv_environment` failed because `env_manager` did not actively invoke tools through the detected environment manager.
  - `test_code_import_options_after_bundle_are_rejected` failed because invalid legacy option ordering was still accepted by docs validation.
  - `test_core_cli_modes_page_is_not_excluded_from_command_validation` failed because `docs/core-cli/modes.md` was excluded from validation.
- `hatch run pytest tests/unit/cli/test_error_guidance.py -q` after adding global error-contract tests -> 2 failed, 2 passed before the shared renderer patch.
  - Missing subcommand and nested unknown-command output only showed compact usage, not the command group's full contextual help.

## OpenSpec Validation

- `openspec validate tester-cli-reliability --strict` -> passed.

## Passing After

- `hatch run generate-command-overview` -> passed.
- `hatch run check-command-overview` -> passed.
- `hatch run check-command-contract` -> passed: `check-command-contract: OK (108 generated command path(s) validated)`.
- `hatch run check-docs-commands` -> passed: `check-docs-commands: OK (104 unique command prefix(es) checked)`.
- `hatch run pytest tests/unit/cli/test_error_guidance.py tests/unit/commands/test_update.py::TestInstallationMethodDetection::test_detect_uv_run_before_stale_pipx_inventory tests/unit/utils/test_env_manager.py::TestCheckToolInEnv::test_check_tool_probes_active_uv_environment tests/unit/docs/test_docs_validation_scripts.py::test_code_import_options_after_bundle_are_rejected tests/unit/docs/test_docs_validation_scripts.py::test_core_cli_modes_page_is_not_excluded_from_command_validation -q` -> 8 passed, 2 warnings.
- `hatch run pytest tests/unit/commands/test_update.py::test_successful_pipx_upgrade_repairs_stale_launcher tests/unit/commands/test_update.py::test_pipx_upgrade_fails_when_launcher_repair_fails -q` -> 2 failed before the pipx launcher validation patch because no launcher validation or reinstall repair path existed.
- `hatch run pytest tests/unit/commands/test_update.py::TestInstallationMethodDetection::test_detect_uv_run_before_stale_pipx_inventory tests/unit/commands/test_update.py::test_successful_pipx_upgrade_repairs_stale_launcher tests/unit/commands/test_update.py::test_pipx_upgrade_fails_when_launcher_repair_fails -q` -> 3 passed, 2 warnings after adding post-upgrade `specfact --version` validation and `pipx reinstall specfact-cli` repair.
- `hatch run pytest tests/unit/registry/test_module_installer.py::test_install_module_handles_macos_application_support_install_root tests/unit/specfact_cli/registry/test_profile_presets.py::test_install_bundles_for_init_preserves_application_support_root tests/unit/commands/test_update.py::test_install_update_pip_with_application_support_executable_uses_shlex -q` -> 3 passed, 2 warnings. These regressions construct `Library/Application Support` paths under `tmp_path` and verify install roots plus quoted update interpreters stay single path values.
- `hatch run pytest tests/unit/utils/test_ide_setup.py::TestCopyTemplatesToIDE::test_copy_templates_to_codex_creates_grouped_skill tests/unit/utils/test_ide_setup.py::test_expected_ide_prompt_export_paths_groups_skill_targets_by_source tests/unit/modules/init/test_init_ide_prompt_selection.py::test_copy_prompts_by_source_to_codex_exports_grouped_skills tests/unit/modules/init/test_init_ide_prompt_selection.py::test_copy_prompts_by_source_to_codex_prunes_stale_per_prompt_skill_exports tests/unit/docs/test_docs_validation_scripts.py::test_collect_specfact_commands_from_guidance_text_handles_inline_and_yaml tests/unit/docs/test_docs_validation_scripts.py::test_scan_guidance_templates_validates_resource_templates -q` -> initially found one parser gap for YAML/Jinja scalar command values, then passed after adding structured-value extraction.
- `hatch run pytest tests/unit/docs/test_docs_validation_scripts.py::test_scan_guidance_templates_validates_resource_templates -q` -> passed after fixing structured-value extraction.
- Manual and automated misuse matrix against `hatch run specfact ...` covered root typos, nested group typos, missing subcommands, missing required arguments, invalid options, dangling option values, lazy delegate groups, and module-owned direct apps:
  - `specfact modul`
  - `specfact module`
  - `specfact module instal`
  - `specfact module install`
  - `specfact module install --scope`
  - `specfact module show`
  - `specfact module show --bad-option`
  - `specfact module alias`
  - `specfact module alias creat`
  - `specfact module alias create`
  - `specfact init ide --repo`
  - `specfact upgrade --bad-option`
  - `specfact code`
  - `specfact code impor`
  - `specfact code import --repo`
  - `specfact backlog auth`
  - `specfact backlog delta status`
  - `specfact project sync brdge`
  - `specfact project sync bridge --repo`
- The matrix found one additional lazy delegate gap: `specfact module install --scope` rendered wrapper usage instead of `specfact module install` help.
- `hatch run specfact module install --scope` after the fix -> renders `Usage: specfact module install [OPTIONS] MODULE_IDS...` and `Error: Option '--scope' requires an argument.`
- `hatch run pytest tests/unit/cli/test_error_guidance.py tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_missing_option_value_shows_leaf_help tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_forwards_bare_subcommand_without_options tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_bare_group_shows_full_help_and_missing_subcommand -q` -> 26 passed, 2 warnings.
- `hatch run runtime-discovery-smoke --launcher direct` -> passed. The smoke installed marketplace modules, verified `module list`, checked `upgrade --help`, `module upgrade --help`, `module upgrade --all --yes`, ran `init ide` with auto-detected and explicit `uv`, and asserted `code review run`, `code import from-code/from-bridge`, `project export`, and `project import` help surfaces.
- Release hygiene:
  - Core package version bumped across all four canonical artifacts to `0.47.0`: `pyproject.toml`, `setup.py`, `src/__init__.py`, and `src/specfact_cli/__init__.py`.
  - `CHANGELOG.md` gained the `0.47.0` entry for generated command artifacts, runtime package-manager smoke gates, CLI misuse guidance, and legacy command-reference cleanup.
  - Built-in module manifests bumped for changed signed payloads: `init` `0.1.34`, `upgrade` `0.1.20`.
  - `hatch run python scripts/sign-modules.py --allow-unsigned --payload-from-filesystem src/specfact_cli/modules/init/module-package.yaml src/specfact_cli/modules/upgrade/module-package.yaml` -> passed, refreshing payload checksums. No signing key variables were configured in this shell, so this was checksum-only local signing.
  - `hatch run check-version-sources` -> passed.
  - `hatch run verify-modules-signature-pr --version-check-base origin/dev` -> passed.
  - `hatch run python scripts/verify-modules-signature.py --payload-from-filesystem --enforce-version-bump --version-check-base origin/dev` -> passed.
  - `hatch run verify-modules-signature --version-check-base origin/dev` -> failed as expected for strict release signing because `init` and `upgrade` now have checksum-only integrity and no private signing key variables or `.specfact/sign-keys/module-signing-private.pem` key were available locally. Approval-time or release signing must add `integrity.signature` before a `main`-equivalent gate.
  - `hatch run generate-command-overview` -> passed after the version bump.
  - `hatch run check-command-overview` -> passed after regeneration.
- The generated command overview is now source-derived and expanded across paired modules when available:
  - `docs/reference/commands.generated.json`
  - `docs/reference/commands.generated.md`
  - `llms.txt`
- `scripts/pre-commit-quality-checks.sh` regenerates and stages the generated command artifacts before checking overview freshness, command behavior, and docs command references.
- PR validation now checks command overview freshness, source-backed command behavior, docs command references, and real-world runtime discovery across the configured package-manager launchers.
- `openspec validate tester-cli-reliability --strict` -> passed after the misuse-matrix expansion.
- CI duplicate full-suite hardening:
  - Core PR orchestrator now has one full-suite owner: `python tools/smart_test_coverage.py run --level full`.
  - The contract-first PR job now runs only scoped checks: `hatch run contract-test-contracts` and `hatch run contract-test-exploration-fast`.
  - Core pre-commit fallback now runs `hatch run contract-test-contracts` instead of the broad `hatch run contract-test` auto runner.
  - PR template now points the full-suite checklist at `hatch run smart-test-full`, not `hatch run contract-test-full`.
  - `hatch run pytest tests/unit/workflows/test_trustworthy_green_checks.py::test_pr_orchestrator_contract_first_job_uses_hatch_contract_test tests/unit/workflows/test_trustworthy_green_checks.py::test_pr_orchestrator_has_single_full_suite_owner tests/unit/specfact_cli/registry/test_signing_artifacts.py::test_pr_orchestrator_pins_virtualenv_below_21_for_hatch_jobs tests/unit/migration/test_module_migration_07_cleanup.py::test_no_flat_topology_command_expectations -q` -> 4 passed.
  - The runtime smoke integration test now resolves the matching modules worktree before the stale sibling checkout when running from a core worktree.
  - `hatch run pytest tests/integration/scripts/test_runtime_discovery_smoke.py::test_runtime_discovery_smoke_direct_launcher -q` -> 1 passed after the matching-worktree resolver fix.
- Package-manager smoke harness hardening:
  - `hatch run runtime-discovery-smoke --launcher direct --launcher hatch-source --launcher pip-editable --launcher pipx --launcher uv-run --launcher uvx` initially failed in `hatch-source` because isolated `HOME` hid a user-installed Hatch package from the Hatch launcher.
  - `scripts/runtime_discovery_smoke.py` now bootstraps a user-site Hatch launcher with its original Python package path, then resets `PYTHONPATH` before the child `specfact` process starts.
  - `hatch run runtime-discovery-smoke --launcher pipx --launcher uv-run --launcher uvx` -> passed after forcing pipx to use the active Python 3.11+ interpreter.
  - `hatch run runtime-discovery-smoke --launcher uv-run` -> passed after changing the uv launcher to `uv run --no-project --with <repo>` with an isolated uv cache, so uv is exercised without creating or updating a project `uv.lock`.
- Quality gates after CI duplicate hardening:
  - `hatch run format` -> passed.
  - `hatch run type-check` -> passed with existing warnings and 0 errors.
  - `hatch run lint` -> passed.
  - `hatch run yaml-lint` -> passed.
  - `openspec validate tester-cli-reliability --strict` -> passed.
- SpecFact code review bug-hunt:
  - Initial `specfact code review run --scope changed --bug-hunt --include-tests --json --out .specfact/code-review.changed.json` found 3 blocking issues in this slice: runtime smoke launcher complexity, a 12-parameter test fixture helper, and a `Path | None` append in `scripts/check-command-contract.py`.
  - Fixed the blocking findings by splitting runtime smoke assertions into smaller helpers, replacing the wide fixture signature with typed overrides, and narrowing the paired modules repo path before appending it.
  - Rerun with paired modules source wired through `SPECFACT_MODULES_ROOTS`/`PYTHONPATH` -> `Review completed with 856 findings (0 blocking)`. The command still returned nonzero because advisory findings remain, but no blocking bug-hunt findings remain in core.

## Deferred / Not Covered In This Slice

- Full `smart-test` was attempted and failed on existing full-suite issues unrelated to the duplicate-run workflow patch: runtime smoke used stale sibling modules before resolver fix, migration fixture false positive, local project module discovery pollution, `ProjectBundle` timeout, and a stale virtualenv pin assertion. Focused regressions for the touched workflow/runtime areas now pass.
