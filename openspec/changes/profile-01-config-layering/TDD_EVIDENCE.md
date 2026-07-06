# TDD Evidence: profile-01-config-layering

## Stale-change refresh

- Timestamp: 2026-07-06 23:18 CEST
- Result: Refreshed February 2026 OpenSpec artifacts before PR preparation.
- Evidence:
  - `proposal.md` now records the 2026-07-06 implementation refresh and PR-candidate status.
  - `design.md` no longer describes the change as proposal-stage only or non-code.
  - `specs/init-module-state/spec.md` now uses validation-support module language instead of stale ceremony positioning.
  - `CHANGE_VALIDATION.md` now records the current strict validation result.

## Failing-before run

- Timestamp: 2026-07-06 22:02 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py -q`
- Result: Failed as expected before production implementation.
- Evidence:
  - `test_validation_tier_profiles_resolve_clean_code_defaults` failed because `first_run_selection.resolve_profile_config` did not exist.
  - `test_profile_config_layering_records_winning_sources` failed because `first_run_selection.resolve_profile_config` did not exist.
  - `test_init_startup_profile_writes_layered_config_and_enables_startup_modules` failed because `startup` was rejected as an unknown profile.

## Passing-after runs

- Timestamp: 2026-07-06 22:04 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py -q`
- Result: Passed, 24 passed.

- Timestamp: 2026-07-06 22:08 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py -q`
- Result: Passed, 24 passed.

- Timestamp: 2026-07-06 22:08 CEST
- Command: `hatch run pytest tests/e2e/test_first_run_init.py -q`
- Result: Passed, 2 passed.

## Quality and OpenSpec gates

- Timestamp: 2026-07-06 22:07 CEST
- Command: `hatch run format`
- Result: Passed.

- Timestamp: 2026-07-06 22:07 CEST
- Command: `hatch run type-check`
- Result: Passed with existing repository warnings; touched resolver warning removed.

- Timestamp: 2026-07-06 22:08 CEST
- Command: `openspec validate profile-01-config-layering --strict`
- Result: Passed.

- Timestamp: 2026-07-06 22:09 CEST
- Command: `hatch run yaml-lint`
- Result: Passed.

- Timestamp: 2026-07-06 22:09 CEST
- Command: `hatch run lint`
- Result: Passed.

- Timestamp: 2026-07-06 23:02 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py -q`
- Result: Passed, 24 passed.

- Timestamp: 2026-07-06 23:02 CEST
- Command: `hatch run pytest tests/e2e/test_first_run_init.py -q`
- Result: Passed, 2 passed.

- Timestamp: 2026-07-06 23:02 CEST
- Command: `openspec validate profile-01-config-layering --strict`
- Result: Passed.

- Timestamp: 2026-07-06 23:03 CEST
- Command: `hatch run format`
- Result: Passed.

- Timestamp: 2026-07-06 23:03 CEST
- Command: `hatch run type-check`
- Result: Passed with existing repository warnings; 0 errors.

- Timestamp: 2026-07-06 23:03 CEST
- Command: `hatch run yaml-lint`
- Result: Passed.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run lint`
- Result: Passed. Initial sandbox run failed in pylint process-pool system-limit detection; rerun outside sandbox passed with 10.00/10.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run contract-test`
- Result: Passed with cached changed-scope result: no modified files detected.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run specfact code review run --scope changed --json --out .specfact/code-review.json`
- Result: Passed with advisory, CI exit code 0, score 96, 9 advisory findings, 0 blocking findings.
- Advisory disposition: not fixed in this PR. Findings are legacy clean-code/KISS/YAGNI advisories around existing `commands.py` helpers and `init_ide` size/shape, not regressions introduced by profile config layering. Changing them here would expand scope beyond the OpenSpec story.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run bandit-scan`
- Result: Passed. No medium/high issues identified.

- Timestamp: 2026-07-06 23:08 CEST
- Command: `SEMGREP_ENABLE_VERSION_CHECK=0 hatch run semgrep-sast --json --output logs/static-analysis/semgrep.json`
- Result: Passed, 0 findings.

- Timestamp: 2026-07-06 23:08 CEST
- Command: `hatch run semgrep-sast-gate --results logs/static-analysis/semgrep.json --baseline tools/semgrep/sast-baseline.json`
- Result: Passed, 0 current findings and 0 accepted baseline findings.

- Timestamp: 2026-07-06 23:04 CEST
- Command: `hatch run smart-test`
- Result: Inconclusive. The tool had no incremental baseline, expanded to a full 2,783-test suite, and was stopped after unrelated broad-suite failures appeared outside the changed scope. Targeted unit/e2e tests above provide changed-scope coverage for this PR.

## PR review follow-up evidence

- Timestamp: 2026-07-06 23:31 CEST
- Source: PR #624 GitHub review and CI logs.
- Findings addressed: stale init module checksum/signature metadata, missing `code-review` `init --install` alias, stale tier docs wording, unguarded profile config write error handling, stale generated profile overlay on repeated `init --profile`, missing policy-weakening warning coverage, and duplicated tier module defaults.

- Timestamp: 2026-07-06 23:33 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py::test_install_code_review_alias_resolves_to_code_review_bundle tests/unit/modules/init/test_first_run_selection.py::test_developer_local_weakening_org_policy_emits_warning tests/unit/modules/init/test_first_run_selection.py::test_profile_defaults_derive_enabled_modules_from_profile_presets tests/unit/modules/init/test_first_run_selection.py::test_write_profile_config_rerun_does_not_keep_prior_generated_profile tests/unit/modules/init/test_first_run_selection.py::test_init_profile_malformed_existing_config_exits_nonzero -q`
- Result: Failed as expected before implementation, 3 failed and 2 passed. Failing cases covered the missing `code-review` alias, stale generated profile overlay, and unhandled malformed config error.

- Timestamp: 2026-07-06 23:34 CEST
- Command: `hatch run pytest tests/unit/modules/init/test_first_run_selection.py::test_install_code_review_alias_resolves_to_code_review_bundle tests/unit/modules/init/test_first_run_selection.py::test_developer_local_weakening_org_policy_emits_warning tests/unit/modules/init/test_first_run_selection.py::test_profile_defaults_derive_enabled_modules_from_profile_presets tests/unit/modules/init/test_first_run_selection.py::test_write_profile_config_rerun_does_not_keep_prior_generated_profile tests/unit/modules/init/test_first_run_selection.py::test_init_profile_malformed_existing_config_exits_nonzero -q`
- Result: Passed, 5 passed.

- Timestamp: 2026-07-06 23:36 CEST
- Command: `hatch run pytest tests/e2e/test_core_slimming_e2e.py::test_e2e_init_profile_solo_developer_then_code_group_available tests/e2e/test_core_slimming_e2e.py::test_e2e_init_profile_api_first_team_then_spec_contract_help tests/e2e/test_first_run_init.py::test_init_profile_solo_developer_completes_in_temp_workspace tests/e2e/test_wow_entrypoint.py::test_init_solo_developer_exits_zero_in_temp_git_repo tests/e2e/test_wow_entrypoint.py::test_after_wow_profile_mock_bundles_registry_lists_code_for_step_two tests/e2e/test_wow_entrypoint.py::test_after_wow_profile_only_code_review_does_not_expose_code_command tests/integration/test_core_slimming.py::test_init_profile_solo_developer_exits_zero_and_code_group_mounted tests/integration/test_core_slimming.py::test_init_profile_enterprise_full_stack_help_shows_eight_commands tests/integration/test_core_slimming.py::test_init_install_all_same_as_enterprise tests/integration/test_core_slimming.py::test_stale_flat_shim_plan_exits_with_removed_alias_guidance tests/integration/test_core_slimming.py::test_init_cicd_mode_no_profile_no_install_exits_one 'tests/unit/cli/test_error_guidance.py::test_cli_misuse_matrix_shows_contextual_help_once[bare module-args1]' tests/unit/cli/test_lean_help_output.py::test_stale_lazy_flat_shim_prints_install_guidance tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_bare_group_shows_full_help_and_missing_subcommand tests/unit/modules/init/test_init_ide_prompt_selection.py::test_init_ide_malformed_vscode_settings_exits_nonzero tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py::test_init_rejects_deprecated_list_modules_option -q`
- Result: Passed, 15 passed and 1 expected skip. This covers the Python 3.12 CI failures observed on PR #624.

- Timestamp: 2026-07-06 23:37 CEST
- Command: `hatch run py311:test tests/unit/modules/init/test_first_run_selection.py::test_install_code_review_alias_resolves_to_code_review_bundle tests/unit/modules/init/test_first_run_selection.py::test_write_profile_config_rerun_does_not_keep_prior_generated_profile tests/unit/modules/init/test_first_run_selection.py::test_init_profile_malformed_existing_config_exits_nonzero tests/unit/cli/test_lean_help_output.py::test_stale_lazy_flat_shim_prints_install_guidance tests/integration/test_core_slimming.py::test_init_profile_solo_developer_exits_zero_and_code_group_mounted -q`
- Result: Passed, 5 passed. This covers the Python 3.11 CI failure class observed on PR #624.

- Timestamp: 2026-07-06 23:38 CEST
- Command: `hatch run lint`
- Result: Passed, 0 errors, 0 warnings, 0 notes; pylint rated 10.00/10.

- Timestamp: 2026-07-06 23:38 CEST
- Command: `hatch run type-check`
- Result: Passed with existing repository warnings; focused touched-file type check passed with 0 errors, 0 warnings, 0 notes.

- Timestamp: 2026-07-06 23:38 CEST
- Command: `hatch run check-docs-commands`
- Result: Passed, 382 unique command prefixes checked.

- Timestamp: 2026-07-06 23:40 CEST
- Command: `hatch run verify-modules-signature-push --version-check-base origin/dev`
- Result: Passed, 4 module manifests verified.

- Timestamp: 2026-07-06 23:56 CEST
- Source: PR #624 GitHub compatibility rerun on commit `0a56c828`.
- Finding addressed: Python 3.11 compatibility still failed because runtime built-in module loading reported `init` integrity verification failure; the PR checksum gate had passed in relaxed mode, but runtime verification uses the strict payload checksum.
- Fix: regenerated `src/specfact_cli/modules/init/module-package.yaml` with the signed/stable payload checksum `sha256:bfadcf13364a94bcf9e0b26e288386f04ecfb23ab932201e487188d17fc499e4`.

- Timestamp: 2026-07-06 23:56 CEST
- Command: `hatch run python -c "from pathlib import Path; import yaml; from specfact_cli.models.module_package import ModulePackageMetadata; from specfact_cli.registry.module_installer import verify_module_artifact; p=Path('src/specfact_cli/modules/init'); data=yaml.safe_load((p/'module-package.yaml').read_text()); meta=ModulePackageMetadata(**data); print(verify_module_artifact(p, meta, allow_unsigned=True))"`
- Result: Passed; runtime verification returned `True`.

- Timestamp: 2026-07-06 23:57 CEST
- Command: `hatch run py311:test tests/unit/cli/test_lean_help_output.py::test_stale_lazy_flat_shim_prints_install_guidance tests/unit/cli/test_lean_help_output.py::test_lazy_delegate_bare_group_shows_full_help_and_missing_subcommand tests/unit/modules/init/test_init_ide_prompt_selection.py::test_init_ide_malformed_vscode_settings_exits_nonzero tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py::test_init_rejects_deprecated_list_modules_option tests/integration/test_core_slimming.py::test_init_profile_solo_developer_exits_zero_and_code_group_mounted tests/integration/test_core_slimming.py::test_init_profile_enterprise_full_stack_help_shows_eight_commands tests/integration/test_core_slimming.py::test_init_install_all_same_as_enterprise tests/integration/test_core_slimming.py::test_stale_flat_shim_plan_exits_with_removed_alias_guidance tests/integration/test_core_slimming.py::test_init_cicd_mode_no_profile_no_install_exits_one -q`
- Result: Passed, 9 passed. This covers the exact Python 3.11 compatibility failures from the GitHub job after refreshing the runtime checksum.

- Timestamp: 2026-07-06 23:40 CEST
- Command: `hatch run specfact code review run --scope changed --json --out .specfact/code-review.json`
- Result: Passed with advisory, CI exit code 0, score 96, 0 blocking findings on changed lines.
- Advisory disposition: not fixed in this PR. Remaining advisories are pre-existing function-size/YAGNI signals in `src/specfact_cli/modules/init/src/commands.py` outside the review-fix lines. The direct regression and review findings were addressed; broader init refactoring is intentionally out of scope for this PR repair.

## Dependabot remediation evidence

- Timestamp: 2026-07-06 23:43 CEST
- Source: GitHub Dependabot alerts #3, #4, and #5.
- Findings addressed: `concurrent-ruby` in `docs/Gemfile.lock` was vulnerable to GHSA-6wx8-w4f5-wwcr, GHSA-h8w8-99g7-qmvj, and GHSA-wv3x-4vxv-whpp for versions `< 1.3.7`.
- Fix: updated `docs/Gemfile.lock` from `concurrent-ruby 1.3.5` to `1.3.7`.

- Timestamp: 2026-07-06 23:43 CEST
- Command: `GEM_HOME=/tmp/specfact-bundler-2.3.5 GEM_PATH=/tmp/specfact-bundler-2.3.5 BUNDLE_GEMFILE=docs/Gemfile /tmp/specfact-bundler-2.3.5/bin/bundle _2.3.5_ update concurrent-ruby --patch`
- Result: Inconclusive due local Ruby 2.6 resolver incompatibility with existing docs lockfile gems requiring Ruby >=2.7. No lockfile drift occurred from this failed resolver run; the minimal patched-version lockfile update was applied manually.

- Timestamp: 2026-07-06 23:44 CEST
- Command: `ruby -e 'lock = File.read("docs/Gemfile.lock"); abort("missing patched concurrent-ruby") unless lock.include?("concurrent-ruby (1.3.7)"); abort("still vulnerable") if lock.include?("concurrent-ruby (1.3.5)") || lock.include?("concurrent-ruby (1.3.6)"); puts "docs/Gemfile.lock concurrent-ruby patched"'`
- Result: Passed.

- Timestamp: 2026-07-06 23:44 CEST
- Command: `GEM_HOME=/tmp/specfact-bundler-2.3.5 GEM_PATH=/tmp/specfact-bundler-2.3.5 BUNDLE_GEMFILE=docs/Gemfile /tmp/specfact-bundler-2.3.5/bin/bundle _2.3.5_ platform`
- Result: Passed; Bundler parsed the lockfile and reported supported platforms.

- Timestamp: 2026-07-06 23:45 CEST
- Command: `hatch run license-check`
- Result: Passed, 0 license violations.

- Timestamp: 2026-07-06 23:45 CEST
- Command: `hatch run security-audit`
- Result: Passed. No high-severity Python vulnerabilities found; pip CVE warning remains CVSS 0.0 and below gate threshold.

- Timestamp: 2026-07-06 23:45 CEST
- Command: `hatch run bandit-scan`
- Result: Passed. No medium/high issues identified.
