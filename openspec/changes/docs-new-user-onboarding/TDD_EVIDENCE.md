# TDD evidence — docs-new-user-onboarding

## 2026-04-02 (README + wow entrypoint contract)

### Commands run (passing)

- `hatch run pytest tests/unit/docs/test_wow_entrypoint_contract.py tests/e2e/test_wow_entrypoint.py tests/unit/docs/test_first_contact_story.py -v --no-cov`
- `hatch run format`

### Summary

- **README.md**: Rewrote **How do I get started** so the uvx two-command wow path (`init` + `code review run --scope full`) is first; persistent install and deeper workflows follow; **How It Works** updated to lead with review.
- **Tests**: `tests/unit/docs/test_wow_entrypoint_contract.py` locks README ↔ `docs/index.md` canonical command strings and section order; `tests/e2e/test_wow_entrypoint.py` runs `init --profile solo-developer` in a **temp git repo** and asserts registry readiness for the documented second step (mock bundles).

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

## 2026-04-02 (rebase + gate continuation)

### Commands run (passing)

- `git rebase origin/dev` (resolved `tasks.md` conflict; kept 7c.7 + 11.0)
- `hatch run yaml-lint`
- `hatch run contract-test`
- `hatch run pytest tests/unit -n 0 -q --no-cov` (full unit suite)

### Fixes for dev merge

- `docs/index.md`: restored first-contact story strings (`Why does it exist?`, tagline, canonical core CLI story, OpenSpec mention) for `test_first_contact_story` / `test_core_docs_site_contract` / `test_release_docs_parity`.
- `test_first_run_selection.py`: expectations for `solo-developer` + `install all` include `specfact-code-review` / six canonical bundles.
- `test_lean_help_output.py`: accept uvx init hint alongside `<profile>` placeholder.
- `test_commands.py` / `test_module_installer.py`: align with `nold-ai/specfact-backlog` install id and new `core_compatibility` error text.
- `test_multi_module_install_uninstall.py`: autouse fixture re-bootstraps `CommandRegistry` + `rebuild_root_app_from_registry()` after category-group tests mutate global CLI state.
