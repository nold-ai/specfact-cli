# Change: Core Package Slimming and Mandatory Profile Selection

## Why

`module-migration-02-bundle-extraction` moved all 17 non-core module sources from `src/specfact_cli/modules/` into independently versioned bundle packages in `specfact-cli-modules/packages/`, published them to the marketplace registry as signed official-tier bundles, and left re-export shims in the core package to preserve backward compatibility.

After module-migration-02, two problems remain:

1. **Core package still ships all 17 modules.** `pyproject.toml` still includes `src/specfact_cli/modules/{project,plan,backlog,...}/` in the package data, so every `specfact-cli` install pulls 17 modules the user may never use. The lean install story cannot be told.
2. **First-run selection is optional.** The `specfact init` interactive bundle selection introduced by module-migration-01 is bypassed when users run `specfact init` without extra arguments — the bundled modules are always available even if no bundle is installed. The user experience of "4 commands on a fresh install" is not yet reality.

This change completes the migration: it removes the 17 non-core module directories from the core package, strips the backward-compat shims that were added in module-migration-01 (one major version has now elapsed), updates `specfact init` to enforce bundle selection before first workspace use, and delivers the lean install experience where `specfact --help` on a fresh install shows only the 4 permanent core commands.

This mirrors the final VS Code model step: the core IDE ships without language extensions, and the first-run experience requires the user to select a language pack.

## What Changes

- **DELETE**: `src/specfact_cli/modules/{project,plan,import_cmd,sync,migrate}/` — extracted to `specfact-project`
- **DELETE**: `src/specfact_cli/modules/{backlog,policy_engine}/` — extracted to `specfact-backlog`
- **DELETE**: `src/specfact_cli/modules/{analyze,drift,validate,repro}/` — extracted to `specfact-codebase`
- **DELETE**: `src/specfact_cli/modules/{contract,spec,sdd,generate}/` — extracted to `specfact-spec`
- **DELETE**: `src/specfact_cli/modules/{enforce,patch_mode}/` — extracted to `specfact-govern`
- **DELETE**: Backward-compat flat command shims registered by `bootstrap.py` in module-migration-01 (one major version cycle complete; shims are removed)
- **MODIFY**: `pyproject.toml` — remove the 17 non-core module source paths from `[tool.hatch.build.targets.wheel] packages` and `[tool.hatch.build.targets.wheel] include` entries; only the 4 core module directories remain: `init`, `auth`, `module_registry`, `upgrade`
- **MODIFY**: `setup.py` — sync package discovery and data files to match updated `pyproject.toml`; remove `find_packages` matches for deleted module directories
- **MODIFY**: `src/specfact_cli/registry/bootstrap.py` — remove bundled bootstrap registrations for the 17 extracted modules; retain only the 4 core module bootstrap registrations; remove backward-compat shim registration logic introduced by module-migration-01
- **MODIFY**: `src/specfact_cli/modules/init/` (`commands.py`) — make bundle selection mandatory on first run: if no bundles are installed after `specfact init` completes, prompt again or require `--profile` or `--install`; add guard that blocks workspace use until at least one bundle is installed (warn-and-exit with actionable message)
- **MODIFY**: `src/specfact_cli/cli.py` — remove category group registrations for categories whose source has been deleted from core; groups are now mounted only when the corresponding bundle is installed and active in the registry

## Capabilities

### New Capabilities

- `core-lean-package`: The installed `specfact-cli` wheel contains only the 4 core modules (`init`, `auth`, `module_registry`, `upgrade`). `specfact --help` on a fresh install shows ≤ 6 top-level commands (4 core + `module` + `upgrade`). All installed category groups appear dynamically when their bundle is present in the registry.
- `profile-presets`: `specfact init` now enforces that at least one bundle is installed before workspace initialisation completes. The four profile presets (solo-developer, backlog-team, api-first-team, enterprise-full-stack) are the canonical first-run paths. Both interactive (Copilot) and non-interactive (CI/CD: `--profile`, `--install`) paths are fully implemented and tested.
- `module-removal-gate`: A pre-deletion verification gate that confirms every module directory targeted for removal has a published, signed, and installable counterpart in the marketplace registry before the source deletion is committed. The gate is implemented as a script (`scripts/verify-bundle-published.py`) and is run as part of the pre-flight checklist for this change and any future module removal.

### Modified Capabilities

- `command-registry`: `bootstrap.py` now registers only the 4 core modules unconditionally. Category group registration is delegated entirely to the runtime module loader — groups appear only when the installed bundle activates them.
- `lazy-loading`: Registry lazy loading now resolves only installed (marketplace-downloaded) bundles for category groups. The bundled fallback path for non-core modules is removed.

### Removed Capabilities (intentional)

- Backward-compat flat command shims (`specfact plan`, `specfact validate`, `specfact contract`, etc. as top-level commands) — removed after one major version cycle. Users must have migrated to category group commands (`specfact project plan`, `specfact code validate`, etc.) or have the appropriate bundle installed.

## Impact

- **Affected code**:
  - `src/specfact_cli/modules/` — 17 module directories deleted
  - `src/specfact_cli/registry/bootstrap.py` — core-only bootstrap, shim removal
  - `src/specfact_cli/modules/init/src/commands.py` — mandatory bundle selection, first-use guard
  - `src/specfact_cli/cli.py` — category group mount conditioned on installed bundles
  - `pyproject.toml` — package includes slimmed to 4 core modules
  - `setup.py` — synced with pyproject.toml
- **Affected specs**: New specs for `core-lean-package`, `profile-presets`, `module-removal-gate`; delta specs on `command-registry` and `lazy-loading`
- **Affected documentation**:
  - `docs/guides/getting-started.md` — complete rewrite of install + first-run section to reflect mandatory profile selection; commands table updated to show 4 core + bundle-installed commands
  - `docs/guides/installation.md` — update install steps; note that bundles are required for full functionality; add `specfact init --profile <name>` as the canonical post-install step
  - `docs/reference/commands.md` — update command topology; mark removed flat shim commands as deleted in this version
  - `docs/reference/module-categories.md` (created by module-migration-01) — update to note source no longer ships in core; point to marketplace for installation
  - `docs/_layouts/default.html` — verify sidebar navigation reflects current command structure (no stale flat-command references)
  - `README.md` — update "Getting started" section to lead with `specfact init --profile solo` or interactive first-run; update command list to show category groups rather than flat commands
- **Backward compatibility**:
  - **Breaking**: The 17 module directories are removed from the core package. Any user who installed `specfact-cli` but did not run `specfact init` (or equivalent bundle install) will find that the non-core commands are no longer available. Migration path: run `specfact init --profile <name>` or `specfact module install nold-ai/specfact-<bundle>`.
  - **Breaking**: Backward-compat flat shims (`specfact plan`, `specfact validate`, etc.) are removed. Users relying on these must switch to category group commands or ensure the relevant bundle is installed.
  - **Non-breaking for CI/CD**: `specfact init --profile enterprise` or `specfact init --install all` in a pipeline bootstrap step installs all bundles without interaction. All commands remain available post-install. CI/CD pipelines that include an init step are unaffected.
  - **Migration guide**: Included in documentation update. Minimum migration: add `specfact init --profile enterprise` to pipeline bootstrap. Existing tests that test flat shim commands must be updated to use category group command paths.
- **Rollback plan**:
  - Restore deleted module directories from git history (`git checkout HEAD~1 -- src/specfact_cli/modules/{project,plan,...}`)
  - Revert `pyproject.toml` and `setup.py` package include changes
  - Revert `bootstrap.py` to module-migration-02 state (re-register bundled modules + shims)
  - No database or registry state is affected; rollback is a pure source revert
- **Blocked by**: `module-migration-02-bundle-extraction` — all 17 module sources must be confirmed published and available in the marketplace registry with valid signatures before any source deletion is committed. The `module-removal-gate` spec and `scripts/verify-bundle-published.py` gate enforce this.
- **Wave**: Wave 4 — after stable bundle release from Wave 3 (`module-migration-01` + `module-migration-02` complete, bundles available in marketplace registry)

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #317
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/317>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
