# TDD evidence — docs-new-user-onboarding

## 2026-04-02 (implementation session)

### Commands run (passing)

- `hatch test tests/unit/specfact_cli/registry/test_profile_presets.py tests/unit/specfact_cli/modules/test_multi_module_install_uninstall.py tests/unit/specfact_cli/modules/test_module_upgrade_improvements.py tests/unit/specfact_cli/test_module_not_found_error.py tests/unit/specfact_cli/registry/test_dependency_resolver_pip_free.py tests/unit/specfact_cli/registry/test_versioned_bundle_deps.py -q`
- `hatch run format`
- `hatch run type-check` (0 errors; existing baseline warnings)

### Summary

- Profile `solo-developer` includes `specfact-code-review`; init installs marketplace bundle via `install_bundles_for_init`.
- `dependency_resolver` skips pip validation when pip is unavailable (uvx).
- `module_installer`: versioned `bundle_dependencies` dict entries; actionable `core_compatibility` error.
- `module` CLI: multi-install, multi-uninstall, upgrade with latest-skip, major-bump gate, `--yes`.
- Root CLI: module-not-found message includes `uvx specfact-cli init --profile solo-developer`.
- Init: prints `Installed: …` after profile/`--install` bundle install.
- Docs: `docs/index.md`, `docs/getting-started/installation.md`, `docs/getting-started/quickstart.md` updated for vibe-coder entry path.

### Deferred / follow-up

- **`specfact code review run --path .` without `--scope full`**: UX lives primarily in the **specfact-code-review** module (`nold-ai/specfact-cli-modules`); not changed in this repo.
- **`openspec sync --change …`**: local OpenSpec CLI has no `sync` subcommand in this environment; run the project’s documented sync workflow when available before archive.
- **7d full dependency-resolution wiring**: `_extract_bundle_dependencies` + message improvements landed; interactive dep resolution / `--dry-run` / graph (7d.11–7d.16) remain for a follow-up change if not bundled here.
