# TDD Evidence: backlog-core-05-user-modules-bootstrap

## Pre-implementation failing run

- Timestamp: 2026-02-23T11:15:18Z
- Command(s): `hatch test -- tests/unit/registry/test_module_discovery.py tests/unit/registry/test_module_installer.py tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py -q`
- Failure summary:
  - `tests/unit/registry/test_module_discovery.py::test_discover_all_modules_scans_user_root` failed because `USER_MODULES_ROOT` is not defined in `module_discovery`.
  - `tests/unit/registry/test_module_installer.py::test_install_module_defaults_to_user_modules_root` failed because `USER_MODULES_ROOT` is not defined in `module_installer`.
  - `tests/unit/modules/module_registry/test_commands.py::test_module_init_bootstraps_user_modules` failed because the module command group did not yet expose bootstrap behavior.

## Post-implementation passing run

- Timestamp: 2026-02-23T11:20:28Z
- Command(s): `hatch test -- tests/unit/registry/test_module_discovery.py tests/unit/registry/test_module_installer.py tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py tests/unit/utils/test_ide_setup.py -q`
- Result summary: `43 passed` (no failures).

## Follow-up failing run (workspace root boundary hardening)

- Timestamp: 2026-02-23T12:35:44Z
- Command(s): `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py tests/unit/registry/test_module_discovery.py -q`
- Failure summary:
  - `tests/unit/specfact_cli/registry/test_module_packages.py::test_get_modules_roots_includes_workspace_dot_specfact_modules_when_present` failed because `.specfact/modules` was not included as workspace-local discovery root.
  - `tests/unit/specfact_cli/registry/test_module_packages.py::test_get_modules_roots_ignores_workspace_plain_modules_directory` failed because legacy `./modules` was still auto-discovered.
  - `tests/unit/registry/test_module_discovery.py::test_discover_all_modules_scans_builtin_marketplace_and_custom` and `...handles_missing_optional_paths` exposed nondeterministic user-root leakage in tests.

## Follow-up passing run (workspace root boundary hardening)

- Timestamp: 2026-02-23T12:36:32Z
- Command(s): `hatch test -- tests/unit/specfact_cli/registry/test_module_packages.py tests/unit/registry/test_module_discovery.py tests/unit/modules/module_registry/test_commands.py -q`
- Result summary: `66 passed, 1 skipped` (no failures).

## Follow-up failing run (module init scope + startup freshness + precedence)

- Timestamp: 2026-02-23T12:44:17Z
- Command(s): `hatch test -- tests/unit/modules/module_registry/test_commands.py tests/unit/registry/test_module_discovery.py tests/unit/utils/test_startup_checks.py -q`
- Failure summary:
  - `test_module_init_project_scope_defaults_to_cwd_repo` and `test_module_init_project_scope_supports_explicit_repo` failed because `specfact module init` did not yet support `--scope project` / `--repo`.
  - `test_discover_all_modules_project_scope_takes_priority_over_user` failed because discovery still prioritized user modules over project modules.
  - `test_module_freshness_check_runs_on_version_change` and `test_startup_warns_when_project_or_user_modules_are_stale` failed because startup checks did not yet include bundled module freshness logic.

## Follow-up passing run (module init scope + startup freshness + precedence)

- Timestamp: 2026-02-23T12:49:51Z
- Command(s): `hatch test -- tests/unit/modules/module_registry/test_commands.py tests/unit/registry/test_module_discovery.py tests/unit/utils/test_startup_checks.py -q`
- Result summary: `70 passed` (no failures).

## Follow-up failing run (init lifecycle flag removal + bundled availability list)

- Timestamp: 2026-02-23T12:55:52+01:00
- Command(s):
  - `hatch test -- tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py -q`
  - `hatch test -- tests/unit/modules/module_registry/test_commands.py -q`
- Failure summary:
  - `test_init_rejects_deprecated_list_modules_option`, `...enable_module_option`, and `...disable_module_option` failed because `specfact init` still accepted deprecated lifecycle flags.
  - `test_init_bootstrap_only_does_not_run_ide_setup` failed because top-level `specfact init` output did not yet include the module command-group migration notice.
  - `test_list_command_show_bundled_available_separate_section_with_hints` and `...empty_when_all_installed` failed because `specfact module list` did not yet support bundled-not-installed visibility.

## Follow-up passing run (init lifecycle flag removal + bundled availability list)

- Timestamp: 2026-02-23T13:00:49+01:00
- Command(s):
  - `hatch test -- tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py -q`
  - `hatch test -- tests/unit/modules/module_registry/test_commands.py -q`
  - `hatch test -- tests/unit/specfact_cli/registry/test_command_registry.py tests/unit/specfact_cli/registry/test_init_module_state.py tests/e2e/test_init_command.py -q`
- Result summary:
  - `6 passed` (`test_init_module_lifecycle_ux.py`)
  - `34 passed` (`test_commands.py`)
  - `32 passed` (`test_command_registry.py`, `test_init_module_state.py`, `test_init_command.py`)

## Follow-up failing run (scoped install/uninstall consistency)

- Timestamp: 2026-02-23T13:05:00+01:00
- Command(s): `hatch test -- tests/unit/modules/module_registry/test_commands.py -q`
- Failure summary:
  - `test_install_command_project_scope_installs_to_project_modules_root` failed because `module install` did not yet support `--scope project` / `--repo`.
  - `test_install_command_prefers_bundled_source_when_available` failed because `module install` did not resolve bundled modules prior to marketplace fallback.
  - `test_uninstall_command_requires_scope_when_module_exists_in_user_and_project` failed because `module uninstall` did not yet implement scope-aware ambiguity safeguards.

## Follow-up passing run (scoped install/uninstall consistency)

- Timestamp: 2026-02-23T13:05:00+01:00
- Command(s):
  - `hatch test -- tests/unit/modules/module_registry/test_commands.py -q`
  - `hatch test -- tests/unit/registry/test_module_installer.py tests/unit/specfact_cli/registry/test_init_module_lifecycle_ux.py -q`
  - `hatch test -- tests/e2e/test_init_command.py tests/unit/specfact_cli/registry/test_command_registry.py -q`
- Result summary:
  - `37 passed` (`test_commands.py`)
  - `15 passed` (`test_module_installer.py`, `test_init_module_lifecycle_ux.py`)
  - `28 passed` (`test_init_command.py`, `test_command_registry.py`)

## Follow-up failing run (source selection + bundled list visibility UX)

- Timestamp: 2026-02-23T13:13:27+01:00
- Command(s): `hatch test -- tests/unit/modules/module_registry/test_commands.py -q`
- Failure summary:
  - `test_install_command_project_scope_does_not_skip_when_user_scope_module_exists` failed because project-scope install still skipped when a user-scope copy existed.
  - `test_install_command_source_marketplace_skips_bundled_resolution` failed because install did not yet support explicit source selection.
  - `test_list_command_without_flag_shows_hint_when_bundled_available` failed because list output had no discoverability hint for bundled-not-installed modules.

## Follow-up passing run (source selection + bundled list visibility UX)

- Timestamp: 2026-02-23T13:13:27+01:00
- Command(s): `hatch test -- tests/unit/modules/module_registry/test_commands.py -q`
- Result summary: `40 passed` (`test_commands.py`).

## Follow-up failing run (denylist + trust gate + bundled integrity hardening)

- Timestamp: 2026-02-23T12:44:42Z
- Command(s): `hatch run pytest tests/unit/registry/test_module_installer.py tests/unit/modules/module_registry/test_commands.py -q`
- Failure summary:
  - `test_install_module_rejects_denylisted_module` and `test_sync_bundled_modules_rejects_denylisted_module` failed because denylist enforcement hook (`assert_module_allowed`) was not implemented.
  - `test_install_bundled_module_enforces_integrity_verification` failed because bundled installs did not verify integrity before copy.
  - `test_install_command_requires_explicit_trust_for_non_official_in_non_interactive`, `...passes_trust_flag_to_marketplace_installer`, and `test_module_init_passes_trust_flag_and_non_interactive` failed because CLI trust flag and non-interactive trust flow were not wired.

## Follow-up passing run (denylist + trust gate + bundled integrity hardening)

- Timestamp: 2026-02-23T12:50:21Z
- Command(s):
  - `hatch run pytest tests/unit/registry/test_module_security.py tests/unit/registry/test_module_installer.py tests/unit/modules/module_registry/test_commands.py -q`
  - `hatch run pytest tests/unit/specfact_cli/registry/test_signing_artifacts.py tests/unit/registry/test_module_security.py tests/unit/registry/test_module_installer.py tests/unit/modules/module_registry/test_commands.py -q`
  - `hatch run format`
- Result summary:
  - `63 passed` across signing-artifacts, module-security, installer, and module command suites.
  - Formatting checks passed after implementation.

## Follow-up failing run (integrity fallback log-level noise)

- Timestamp: 2026-02-24T21:26:13Z
- Command(s): `python -m pytest tests/unit/registry/test_module_installer.py -k "fallback_does_not_emit_info_in_normal_mode or fallback_emits_debug_in_debug_mode" -q`
- Failure summary:
  - `test_verify_module_artifact_fallback_does_not_emit_info_in_normal_mode` failed because `verify_module_artifact` emitted fallback details via `logger.info(...)` in non-debug mode.
  - `test_verify_module_artifact_fallback_emits_debug_in_debug_mode` failed because fallback diagnostics were not emitted through debug-level logging.

## Follow-up passing run (integrity fallback log-level noise)

- Timestamp: 2026-02-24T21:26:13Z
- Command(s):
  - `python -m pytest tests/unit/registry/test_module_installer.py -k "fallback_does_not_emit_info_in_normal_mode or fallback_emits_debug_in_debug_mode" -q`
  - `python -m pytest tests/unit/registry/test_module_installer.py -q`
- Result summary:
  - Targeted fallback-log tests: `2 passed`.
  - Full installer test file: `20 passed`.

## Follow-up failing run (GitHub map-fields missing issue-type IDs)

- Timestamp: 2026-02-24T21:42:09Z
- Command(s): `python -m pytest tests/unit/commands/test_backlog_commands.py -k "map_fields_github_provider_persists_backlog_config or map_fields_github_provider_fails_when_issue_types_unavailable" -q`
- Failure summary:
  - `test_map_fields_github_provider_fails_when_issue_types_unavailable` failed because `backlog map-fields` returned success even when repository issue types were empty/unavailable.
  - This left `github_issue_types.type_ids` unconfigured and allowed `backlog add` to keep warning despite setup attempts.

## Follow-up passing run (GitHub map-fields missing issue-type IDs)

- Timestamp: 2026-02-24T21:42:09Z
- Command(s):
  - `python -m pytest tests/unit/commands/test_backlog_commands.py -k "map_fields_github_provider_persists_backlog_config or map_fields_github_provider_fails_when_issue_types_unavailable" -q`
  - `python -m pytest modules/backlog-core/tests/unit/test_add_command.py -k "warns_when_github_issue_type_mapping_missing" -q`
- Result summary:
  - GitHub map-fields targeted tests: `2 passed`.
  - Backlog add warning path regression check: `1 passed`.

## Follow-up failing run (startup integrity warning noise)

- Timestamp: 2026-02-24T22:54:14+01:00
- Command(s): `hatch run specfact module list`
- Failure summary:
  - Startup emitted raw logger warning with checksum internals:
    - `Module backlog: Integrity check failed: Checksum mismatch: ...`
  - Warning was noisy and not user-guided, and exposed technical checksum detail in normal mode.

## Follow-up passing run (startup integrity warning UX + debug separation)

- Timestamp: 2026-02-24T22:57:56+01:00
- Command(s):
  - `python -m pytest tests/unit/registry/test_module_installer.py -k "checksum_mismatch_hides_raw_details_without_debug or checksum_mismatch_logs_raw_details_in_debug" -q`
  - `python -m pytest tests/unit/specfact_cli/registry/test_module_packages.py -k "integrity_failure_shows_user_friendly_risk_warning" -q`
  - `PYTHONPATH=src python -m specfact_cli.cli module list`
  - `PYTHONPATH=src python -m specfact_cli.cli --debug module list`
- Result summary:
  - New debug-gating tests: `3 passed`.
  - User-warning UX test: `1 passed`.
  - CLI startup now shows a concise risk warning with mitigation guidance (`specfact module init`) instead of raw checksum mismatch internals in normal mode.
  - With `--debug`, raw checksum mismatch diagnostics are shown for troubleshooting.

## Follow-up failing run (changed-module release automation)

- Timestamp: 2026-02-24T23:05:56+01:00
- Command(s): `python -m pytest tests/unit/specfact_cli/registry/test_signing_artifacts.py -k "changed_module_automation or changed_only_auto_bump" -q`
- Failure summary:
  - `test_sign_modules_py_help_mentions_changed_module_automation` failed because signer help did not expose changed-module automation flags.
  - `test_sign_modules_py_changed_only_auto_bump_and_sign` failed because `sign-modules.py` did not accept `--changed-only`, `--base-ref`, or `--bump-version`.

## Follow-up passing run (changed-module release automation)

- Timestamp: 2026-02-24T23:08:05+01:00
- Command(s):
  - `python -m pytest tests/unit/specfact_cli/registry/test_signing_artifacts.py -k "changed_module_automation or changed_only_auto_bump" -q`
  - `python -m pytest tests/unit/specfact_cli/registry/test_signing_artifacts.py -q`
  - `python scripts/sign-modules.py --allow-unsigned --changed-only --base-ref HEAD --bump-version patch`
  - `python -m pytest tests/unit/registry/test_module_installer.py tests/unit/specfact_cli/registry/test_module_packages.py tests/unit/commands/test_backlog_commands.py -q`
- Result summary:
  - New changed-module automation tests: `2 passed`.
  - Full signing-artifacts suite: `15 passed`.
  - Changed-only automation bumped and re-signed changed bundled manifest (`backlog`), restoring runtime integrity sync.
  - Regression safety suites after module re-sign: `95 passed, 1 skipped`.
