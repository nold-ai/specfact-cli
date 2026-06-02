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

## Follow-up Review Fixes

- Addressed PR review findings after commit `5297ea51`:
  - `llms.txt` generation now keeps Jekyll front matter at the top and emits a single H1.
  - `scripts/check-docs-commands.py` preserves flags in parsed command examples so legacy `specfact code import <bundle> --repo ...` ordering is actually rejected.
  - Placeholder examples such as `specfact <command> --help` are ignored as examples, while explicit subcommands such as `specfact code import from-code legacy-api --repo .` remain valid.
  - Core CLI misuse tests strip ANSI locally and cover only core-owned command paths to avoid module-installation flakiness.
  - `src/specfact_cli/utils/structure.py` now emits canonical `specfact code import --repo . <bundle-name>` guidance.
  - `tasks.md` quality/review checklist now matches the recorded evidence.
- Follow-up verification:
  - `hatch run generate-command-overview && hatch run check-command-overview` -> passed.
  - `hatch run pytest tests/unit/docs/test_docs_validation_scripts.py tests/unit/cli/test_error_guidance.py tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_bare_group_shows_full_help_and_missing_subcommand tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_missing_option_value_shows_leaf_help -q` -> 31 passed, 2 warnings.
  - `hatch run python scripts/check-docs-commands.py` -> passed: `check-docs-commands: OK (385 unique command prefix(es) checked)`.
  - `openspec validate tester-cli-reliability --strict` -> passed.
  - `hatch run format && hatch run lint` -> passed.

## Follow-up PR Thread Fixes

- Validated live PR #595 review threads and CI annotations after the previous follow-up.
- Addressed remaining actionable findings:
  - Generated command overview now flattens the mounted code-review app, so the public contract exposes `specfact code review run` instead of `specfact code review review run`; parent subcommand inventories are backfilled from generated child records.
  - Command-contract validation now maps the public `specfact code review` prefix to the code-review app's internal `review` root when invoking mounted help paths.
  - Secondary `specfact-cli-modules` checkouts in touched workflows now pin `actions/checkout` to `34e114876b0b11c390a56381ad16ebd13914f8d5` and disable credential persistence.
  - `specfact.yml` contract validation preserves the real repro exit status and validates/quotes the budget input before invoking the command.
  - Progressive-disclosure bootstrap removes a partially-loaded module from `sys.modules` if import execution fails.
  - Lazy delegated plain `SystemExit` codes are preserved instead of being normalized to success.
  - Public `init` callback was initially wrapped with `@beartype` using Typer's vendored Click context type; this was later replaced after CI proved that private Typer namespace is not available under the declared dependency range.
  - Pipx upgrade validation treats a missing launcher as repairable via `pipx reinstall specfact-cli`, then re-checks the launcher before reporting success.
  - Suggestions and docs were updated away from removed `project plan select` and legacy `code import --repo . <bundle>` forms.
  - `.markdownlint.json` re-enables MD040 fenced-code-language enforcement.
  - OpenSpec change-order tracking includes source bug `#593`.
- Follow-up verification:
  - `hatch run generate-command-overview` -> passed.
  - `hatch run pytest tests/unit/commands/test_update.py tests/unit/utils/test_suggestions.py tests/unit/docs/test_docs_validation_scripts.py tests/unit/cli/test_error_guidance.py tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_bare_group_shows_full_help_and_missing_subcommand tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_missing_option_value_shows_leaf_help tests/unit/workflows/test_trustworthy_green_checks.py -q` -> 89 passed, 2 warnings.
  - `hatch run check-command-contract && hatch run check-command-overview && hatch run python scripts/check-docs-commands.py && hatch run lint-workflows && openspec validate tester-cli-reliability --strict` -> passed.
  - `hatch run format && hatch run lint` -> passed.

## Second Follow-up PR CI Fixes

- Re-checked PR #595 after pushing the paired modules fixes. Fresh CI failures were valid:
  - Docs Review failed in `hatch run check-command-overview` with `ModuleNotFoundError: No module named 'typer._click'` while importing `src/specfact_cli/modules/init/src/commands.py`.
  - Contract Validation failed because `.github/workflows/specfact.yml` ran `specfact code repro` without checking out the paired `specfact-cli-modules` branch, so the installable `code` command group was unavailable.
- Fixed the Typer compatibility regression by removing the private `typer._click` import from the public `init` callback path and using the public `typer.Context` annotation without beartype on that existing framework callback.
- Added `test_init_commands_avoid_private_typer_click_import` to keep the init command source off Typer private namespaces.
- Updated `test_init_commands_avoid_private_typer_click_import` to read the imported commands module source path instead of assuming pytest runs from the repository root.
- Updated `.github/workflows/specfact.yml` to resolve the matching modules branch, fall back to `dev`, check out `nold-ai/specfact-cli-modules` with pinned `actions/checkout`, and export `SPECFACT_MODULES_REPO` before contract validation.
- After rerunning Contract Validation, added `SPECFACT_MODULES_ROOTS=${GITHUB_WORKSPACE}/specfact-cli-modules/packages` because runtime module discovery uses module roots, while `SPECFACT_MODULES_REPO` alone is only repository/path context.
- Corrected the Example 4 integration-showcase docs snippet to use the `example4_precommit` bundle name and remove the undefined `PLAN_FILE`/duplicate health-check lines.
- Updated the Example 4 pre-commit hook walkthrough to pass the explicit `example4_precommit` baseline bundle to `code drift detect` instead of relying on `auto-derived`/legacy `--code-vs-plan` selection.
- Added `test_specfact_contract_workflow_checks_out_matching_modules_branch_when_available`.
- Refreshed core generated command artifacts after the paired modules branch introduced `specfact code review run --enforcement`.
- Follow-up verification:
  - `hatch run pytest tests/unit/modules/init/test_first_run_selection.py tests/unit/docs/test_docs_validation_scripts.py tests/unit/workflows/test_trustworthy_green_checks.py -q` -> 52 passed, 2 warnings.
  - `hatch run check-command-overview` -> passed.
  - `hatch run check-command-contract` -> passed: `check-command-contract: OK (107 generated command path(s) validated)`.
  - `hatch run check-docs-commands` -> passed: `check-docs-commands: OK (380 unique command prefix(es) checked)`.
  - `hatch run lint-workflows` -> passed.
  - `hatch run yaml-lint` -> passed.
  - `hatch run lint` -> passed.
  - `openspec validate tester-cli-reliability --strict` -> passed.

## PR #598 Dev-To-Main Command Contract Fix

- Re-checked PR #598 CI after the runtime smoke fixes. Runtime tests and compatibility checks passed; the remaining failures were duplicate `CLI Command Validation` and `Docs Review` runs.
- Root cause: CI checked out `specfact-cli-modules` at `dev`, and `hatch run check-command-contract` invoked generated legacy alias help paths:
  - `specfact code import from-bridge --help`
  - `specfact code import from-code --help`
- Under the module-owned `code import` Typer shape, the alias token is consumed as the optional `BUNDLE` argument before subcommand resolution, so `--help` is interpreted as the command and exits 2 with `No such command '--help'`.
- Failing-before evidence:
  - `hatch run pytest tests/unit/docs/test_docs_validation_scripts.py::test_command_contract_retries_parent_help_for_code_import_alias -q` -> 1 failed before the production edit because `_check_help` returned immediately on the alias help exit code 2.
- Fix:
  - `scripts/check-command-contract.py` now retries parent `specfact code import --help` for the known ambiguous legacy aliases when direct alias help fails.
- Passing-after evidence:
  - `hatch run pytest tests/unit/docs/test_docs_validation_scripts.py::test_command_contract_retries_parent_help_for_code_import_alias -q` -> 1 passed.
  - `hatch run pytest tests/unit/docs/test_docs_validation_scripts.py -q` -> 15 passed.
  - `SPECFACT_MODULES_REPO=/home/dom/git/nold-ai/specfact-cli-modules hatch run check-command-contract` -> passed: `check-command-contract: OK (107 generated command path(s) validated)`.
  - `SPECFACT_MODULES_REPO=/home/dom/git/nold-ai/specfact-cli-modules hatch run docs-validate` -> passed enforced checks. The warn-only cross-site link step reported DNS resolution failures for `modules.specfact.io` under the local restricted network.
  - `hatch run lint` -> passed.
  - `openspec validate tester-cli-reliability --strict` -> passed.

## PR #598 Stale Artifact And Review Fixes

- Re-checked PR #598 after the prior contract fix. The remaining failures were duplicate `CLI Command Validation` and `Docs Review` runs.
- Root cause: modules `dev` advanced through signing/publish automation to `9b624fb`, while core generated command artifacts still reflected the previous modules command surface.
- Refreshed the generated artifacts with `SPECFACT_MODULES_REPO=/home/dom/git/nold-ai/specfact-cli-modules` after fast-forwarding that checkout to `origin/dev`.
- Validated current PR #598 inline comments:
  - Fixed the valid `src/specfact_cli/cli.py` empty best-effort help fallback comment by replacing the empty `except Exception: pass` with `contextlib.suppress(Exception)` and an explanatory comment.
  - Fixed the valid unused `TyperClickException` compatibility import in `src/specfact_cli/utils/progressive_disclosure.py`.
  - Skipped the `_GENERATED_PREFIX_CACHE` comment in `scripts/check-docs-commands.py` as stale/false-positive: the cache is read before loading and assigned on both generation paths.
  - Fixed the valid namespaced skill export collision in `src/specfact_cli/utils/ide_setup.py`, updated docs, and added regression coverage.
- Passing-after evidence:
  - `hatch run pytest tests/unit/modules/init/test_init_ide_prompt_selection.py tests/unit/utils/test_ide_setup.py tests/unit/cli/test_error_guidance.py tests/unit/cli/test_lean_help_output.py tests/unit/docs/test_docs_validation_scripts.py -q` -> 82 passed, 1 skipped, 2 warnings.
  - `SPECFACT_MODULES_REPO=/home/dom/git/nold-ai/specfact-cli-modules hatch run check-command-overview` -> passed.
  - `SPECFACT_MODULES_REPO=/home/dom/git/nold-ai/specfact-cli-modules hatch run check-command-contract` -> passed: `check-command-contract: OK (107 generated command path(s) validated)`.
  - `SPECFACT_MODULES_REPO=/home/dom/git/nold-ai/specfact-cli-modules hatch run check-docs-commands` -> passed: `check-docs-commands: OK (380 unique command prefix(es) checked)`.
  - `SPECFACT_MODULES_REPO=/home/dom/git/nold-ai/specfact-cli-modules hatch run docs-validate` -> passed enforced checks. The warn-only cross-site link step reported DNS resolution failures for `modules.specfact.io` under the local restricted network.
  - `hatch run format` -> passed, fixed one import-order issue.
  - `hatch run lint` -> passed.
  - `hatch run type-check` -> passed with 0 errors and existing warnings.
  - `openspec validate tester-cli-reliability --strict` -> passed.
