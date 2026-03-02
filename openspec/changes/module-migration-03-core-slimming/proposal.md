# Change: module-migration-03 - Core Package Slimming and Mandatory Profile Selection

## Why

`module-migration-02-bundle-extraction` moved all 17 non-core module sources from `src/specfact_cli/modules/` into independently versioned bundle packages in `specfact-cli-modules/packages/`, published them to the marketplace registry as signed official-tier bundles, and left re-export shims in the core package to preserve backward compatibility.

After module-migration-02, two problems remain:

1. **Core package still ships all 17 modules.** `pyproject.toml` still includes `src/specfact_cli/modules/{project,plan,backlog,...}/` in the package data, so every `specfact-cli` install pulls 17 modules the user may never use. The lean install story cannot be told.
2. **First-run selection is optional.** The `specfact init` interactive bundle selection introduced by module-migration-01 is bypassed when users run `specfact init` without extra arguments — the bundled modules are always available even if no bundle is installed. The user experience of "4 commands on a fresh install" is not yet reality.

This change completes the migration: it removes the 17 non-core module directories from the core package, strips the backward-compat shims that were added in module-migration-01 (one major version has now elapsed), updates `specfact init` to enforce bundle selection before first workspace use, and delivers the lean install experience where `specfact --help` on a fresh install shows only the **4** permanent core commands. Auth **remains in core** for this change; removal of auth (and the move to `specfact backlog auth`) is deferred until after `backlog-auth-01-backlog-auth-commands` is implemented in the modules repo so the same auth behaviour is available there first.

This mirrors the final VS Code model step: the core IDE ships without language extensions, and the first-run experience requires the user to select a language pack.

## What Changes

- **DELETE**: `src/specfact_cli/modules/{project,plan,import_cmd,sync,migrate}/` — extracted to `specfact-project`; entire directory including `__init__.py`, `module-package.yaml`, and the `__getattr__` re-export shim created by migration-02
- **DELETE**: `src/specfact_cli/modules/{backlog,policy_engine}/` — extracted to `specfact-backlog`; entire directory including re-export shim
- **DELETE**: `src/specfact_cli/modules/{analyze,drift,validate,repro}/` — extracted to `specfact-codebase`; entire directory including re-export shim
- **DELETE**: `src/specfact_cli/modules/{contract,spec,sdd,generate}/` — extracted to `specfact-spec`; entire directory including re-export shim
- **DELETE**: `src/specfact_cli/modules/{enforce,patch_mode}/` — extracted to `specfact-govern`; entire directory including re-export shim
- **DELETE**: `src/specfact_cli/modules/auth/` — **Deferred until after backlog-auth-01.** Auth CLI commands will move to the backlog bundle as `specfact backlog auth`; core will then keep only the central auth interface. For this change, auth remains in core (4 core). See "Implementation order" below.
- **REMOVE**: `specfact_cli.modules.*` Python import compatibility shims — the `__getattr__` re-export shims in `src/specfact_cli/modules/*/src/<name>/__init__.py` created by migration-02 are deleted as part of the directory removal. After this change, `from specfact_cli.modules.<name> import X` will raise `ImportError`. Users must switch to direct bundle imports: `from specfact_<bundle>.<name> import X`. See "Backward compatibility" below for the full migration path. This closes the one-version-cycle deprecation window opened by migration-02 (see "Version-cycle definition" below).
- **MODIFY**: `src/specfact_cli/registry/bootstrap.py` — remove bundled bootstrap registrations for the 17 extracted modules; retain only the **4** core module bootstrap registrations (auth remains until 10.6 after backlog-auth-01). Remove the dead shim-registration call sites left over after `module-migration-04-remove-flat-shims` has already deleted `FLAT_TO_GROUP` and `_make_shim_loader()` from `module_packages.py`. (**Prerequisite**: migration-04 must be merged before this bootstrap.py cleanup is implemented, since the registration calls reference machinery that migration-04 deletes.)
- **MODIFY**: `pyproject.toml` — remove the 17 non-core module source paths from `[tool.hatch.build.targets.wheel] packages` and `[tool.hatch.build.targets.wheel] include` entries; only the **4** core module directories remain: `init`, `auth`, `module_registry`, `upgrade` (auth removed in follow-up after backlog-auth-01).
- **MODIFY**: `setup.py` — sync package discovery and data files to match updated `pyproject.toml`; remove `find_packages` matches for deleted module directories
- **MODIFY**: `src/specfact_cli/modules/init/` (`commands.py`) — make bundle selection mandatory on first run: if no bundles are installed after `specfact init` completes, prompt again or require `--profile` or `--install`; add guard that blocks workspace use until at least one bundle is installed (warn-and-exit with actionable message)
- **MODIFY**: `src/specfact_cli/cli.py` — remove category group registrations for categories whose source has been deleted from core; groups are now mounted only when the corresponding bundle is installed and active in the registry

## Capabilities

### New Capabilities

- `core-lean-package`: The installed `specfact-cli` wheel contains only the **4** core modules (`init`, `auth`, `module_registry`, `upgrade`) in this change. After backlog-auth-01 and task 10.6, core will ship 3 modules (auth moves to backlog bundle) and a central auth interface. `specfact --help` on a fresh install shows ≤ 6 top-level commands (4 core + `module` + `upgrade`). All installed category groups appear dynamically when their bundle is present in the registry.
- `profile-presets`: `specfact init` now enforces that at least one bundle is installed before workspace initialisation completes. The four profile presets (solo-developer, backlog-team, api-first-team, enterprise-full-stack) are the canonical first-run paths. Both interactive (Copilot) and non-interactive (CI/CD: `--profile`, `--install`) paths are fully implemented and tested.
- `module-removal-gate`: A pre-deletion verification gate that confirms every module directory targeted for removal has a published, signed, and installable counterpart in the marketplace registry before the source deletion is committed. The gate is implemented as a script (`scripts/verify-bundle-published.py`) and is run as part of the pre-flight checklist for this change and any future module removal.

### Modified Capabilities

- `command-registry`: `bootstrap.py` now registers only the **4** core modules unconditionally in this change (3 core after task 10.6). Category group registration is delegated entirely to the runtime module loader — groups appear only when the installed bundle activates them.
- `lazy-loading`: Registry lazy loading now resolves only installed (marketplace-downloaded) bundles for category groups. The bundled fallback path for non-core modules is removed.

### Removed Capabilities (intentional)

- Backward-compat flat command shims (`specfact plan`, `specfact validate`, `specfact contract`, etc. as top-level commands) — the shim machinery (`FLAT_TO_GROUP`, `_make_shim_loader()`) was removed by `module-migration-04-remove-flat-shims` (prerequisite); this change removes the dead call sites from `bootstrap.py`.
- `specfact_cli.modules.*` Python import compatibility shims — the `__getattr__` re-export shims created by migration-02 are removed when the module directories are deleted. Direct bundle imports (`from specfact_codebase.validate import app`) are the canonical paths. See "Backward compatibility" below.

## Impact

- **Affected code**:
  - `src/specfact_cli/modules/` — 17 module directories deleted
  - `src/specfact_cli/registry/bootstrap.py` — core-only bootstrap, shim removal
  - `src/specfact_cli/modules/init/src/commands.py` — mandatory bundle selection, first-use guard
  - `src/specfact_cli/cli.py` — category group mount conditioned on installed bundles
  - `pyproject.toml` — package includes slimmed to **4** core modules in this change (3 after 10.6)
  - `setup.py` — synced with pyproject.toml
- **Affected specs**: New specs for `core-lean-package`, `profile-presets`, `module-removal-gate`; delta specs on `command-registry` and `lazy-loading`
- **Affected documentation**:
  - `docs/guides/getting-started.md` — complete rewrite of install + first-run section to reflect mandatory profile selection; commands table updated to show **4** core + bundle-installed commands (auth remains; after backlog-auth-01, doc can note `specfact backlog auth`)
  - `docs/guides/installation.md` — update install steps; note that bundles are required for full functionality; add `specfact init --profile <name>` as the canonical post-install step
  - `docs/reference/commands.md` — update command topology; mark removed flat shim commands as deleted in this version
  - `docs/reference/module-categories.md` (created by module-migration-01) — update to note source no longer ships in core; point to marketplace for installation
  - `docs/_layouts/default.html` — verify sidebar navigation reflects current command structure (no stale flat-command references)
  - `README.md` — update "Getting started" section to lead with `specfact init --profile solo` or interactive first-run; update command list to show category groups rather than flat commands
- **Backward compatibility**:
  - **Breaking — module directories removed**: The 17 module directories are removed from the core package. Any user who installed `specfact-cli` but did not run `specfact init` (or equivalent bundle install) will find that the non-core commands are no longer available. Migration path: run `specfact init --profile <name>` or `specfact module install nold-ai/specfact-<bundle>`.
  - **Breaking — flat CLI shims removed**: Backward-compat flat shims (`specfact plan`, `specfact validate`, etc.) were removed by migration-04 (prerequisite); users must switch to category group commands (`specfact project plan`, `specfact code validate`, etc.) or ensure the relevant bundle is installed.
  - **Breaking — auth commands moved to backlog (after backlog-auth-01)**: In a follow-up after backlog-auth-01, the top-level `specfact auth` command will be removed from core. Auth for DevOps providers will then be provided by the backlog bundle as `specfact backlog auth github` and `specfact backlog auth azure-devops`. For this change, `specfact auth` remains in core.
  - **Breaking — Python import shims removed**: `from specfact_cli.modules.<name> import X` (the `__getattr__` re-export shims added by migration-02) raises `ImportError` after this change. Migration path for import consumers:
    - `from specfact_cli.modules.validate import app` → `from specfact_codebase.validate import app`
    - `from specfact_cli.modules.plan import app` → `from specfact_project.plan import app`
    - `from specfact_cli.modules.backlog import app` → `from specfact_backlog.backlog import app`
    - `from specfact_cli.modules.contract import app` → `from specfact_spec.contract import app`
    - `from specfact_cli.modules.enforce import app` → `from specfact_govern.enforce import app`
    - (full mapping: module → bundle namespace in `specfact-cli-modules/packages/*/src/`)
    - This path must be documented as a migration note in the release changelog and in any tooling that generates or templates CLI code.
  - **Non-breaking for CI/CD**: `specfact init --profile enterprise` or `specfact init --install all` in a pipeline bootstrap step installs all bundles without interaction. All commands remain available post-install. CI/CD pipelines that include an init step are unaffected.
  - **Migration guide**: Included in documentation update. Minimum migration: (1) add `specfact init --profile enterprise` to pipeline bootstrap; (2) update any `specfact_cli.modules.*` imports to direct bundle imports; (3) update tests that tested flat shim commands to use category group command paths.
- **Rollback plan**:
  - Restore deleted module directories from git history (`git checkout HEAD~1 -- src/specfact_cli/modules/{project,plan,...}`)
  - Revert `pyproject.toml` and `setup.py` package include changes
  - Revert `bootstrap.py` to module-migration-02 state (re-register bundled modules + shims)
  - No database or registry state is affected; rollback is a pure source revert
- **Blocked by**:
  - `module-migration-02-bundle-extraction` — all 17 module sources must be confirmed published and available in the marketplace registry with valid signatures before any source deletion is committed. The `module-removal-gate` spec and `scripts/verify-bundle-published.py` gate enforce this.
  - `module-migration-04-remove-flat-shims` — the `FLAT_TO_GROUP` shim machinery and `_make_shim_loader()` must be removed from `module_packages.py` before `bootstrap.py` shim registration call sites are deleted in this change (those sites reference the machinery migration-04 removes).
  - `module-migration-05-modules-repo-quality` (sections 18-22) — tests, dependency decoupling/import boundaries, docs baseline, build pipeline, and central config files in specfact-cli-modules must be in place before this change deletes the in-repo module source, so that the canonical repo has full guardrails at cutover time.
- **Wave**: Wave 4 — after stable bundle release from Wave 3 (`module-migration-01` + `module-migration-02` complete, bundles available in marketplace registry); after migration-04 (flat shim machinery removed); after migration-05 sections 18-22 (modules repo quality and decoupling baseline in place)

**Follow-up change**: `backlog-auth-01-backlog-auth-commands` implements `specfact backlog auth` (azure-devops, github, status, clear) in the specfact-cli-modules backlog bundle, using the central auth interface provided by this change. That change is tracked in `openspec/changes/backlog-auth-01-backlog-auth-commands/`.

**Implementation order — auth stays in core for this change**: The auth module is **not** removed in this change. Task 10.6 (remove auth from core, 3 core only) is **deferred until after** `backlog-auth-01-backlog-auth-commands` is implemented and the backlog bundle ships `specfact backlog auth`. That way the same auth behaviour is available under `specfact backlog auth` before we drop `specfact auth` from core, avoiding a period with no auth or a divergent implementation. This change therefore merges with **4 core** (init, auth, module_registry, upgrade). A follow-up PR (or the same branch after backlog-auth-01 is done) will execute task 10.6 and switch to 3 core.

---

## Version-cycle definition

Migration-02's deprecation notices on the `specfact_cli.modules.*` Python import shims stated "removal in next major version cycle." This change defines and closes that cycle:

- **Deprecation opened**: migration-02 (0.2x series) — shims added with `DeprecationWarning` on first attribute access
- **Deprecation closed**: this change (0.40+ series) — shims removed when module directories are deleted
- **Cycle definition**: The 0.2x → 0.40 version series constitutes one deprecation cycle. Version 0.40 is the first release in a new tens-series (`0.4x`), representing a major UX transition (lean core, mandatory profile selection). Any consumer of `specfact_cli.modules.*` that observed the `DeprecationWarning` in 0.2x has had the full 0.2x series to migrate to direct bundle imports. **Release version**: 0.40.0 is the combined release for all module-migration changes (migration-02, -03, -04, -05); version sync and changelog for this change use 0.40.0, not a separate bump.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #317
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/317>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: in-progress
- **Sanitized**: false
