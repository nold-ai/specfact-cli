# Change: Bundle Extraction and Marketplace Publishing

## Why

`module-migration-01-categorize-and-group` introduced the category metadata layer and the `groups/` umbrella commands that aggregate the 21 bundled modules. However, the module source code still lives in `src/specfact_cli/modules/` inside the core package — every `specfact-cli` install still ships all 21 modules unconditionally.

This change completes the extraction step: it moves each category's module source into independently versioned bundle packages in `specfact-cli-modules/packages/`, publishes signed packages to the marketplace registry, and installs the bundle-level dependency graph into the registry index. After this change, the marketplace will carry all five official bundles (`specfact-project`, `specfact-backlog`, `specfact-codebase`, `specfact-spec`, `specfact-govern`) as first-class installable packages with the same trust semantics as any third-party module.

The existing marketplace-01 infrastructure (SHA-256 + Ed25519 signing, `module_installer.py`, `crypto_validator.py`, `module_security.py`) handles all integrity verification — this change wires the bundle extraction and publish pipeline on top of it, using and extending the `scripts/publish-module.py` script introduced by `marketplace-02`.

Without this extraction, the `specfact init --profile <name>` first-run selection flow (introduced by module-migration-01) is cosmetic — it cannot actually restrict what is installed because everything is bundled into core. Extraction makes the profile selection meaningful: only the selected bundles arrive on disk.

## What Changes

- **NEW**: Per-bundle package directories in `specfact-cli-modules/packages/`:
  - `specfact-project/` — consolidates project, plan, import_cmd, sync, migrate module source under `specfact_project` namespace
  - `specfact-backlog/` — consolidates backlog, policy_engine module source under `specfact_backlog` namespace
  - `specfact-codebase/` — consolidates analyze, drift, validate, repro module source under `specfact_codebase` namespace
  - `specfact-spec/` — consolidates contract, spec, sdd, generate module source under `specfact_spec` namespace
  - `specfact-govern/` — consolidates enforce, patch_mode module source under `specfact_govern` namespace
- **MOVE**: Module source code from `src/specfact_cli/modules/<name>/src/` to corresponding bundle package; core `src/specfact_cli/modules/<name>/` retains a re-export shim to preserve `specfact_cli.modules.*` import paths during the migration window
- **REFACTOR**: Shared code used by more than one module factors into `specfact_cli.common` — no cross-bundle private imports are allowed
- **MODIFY**: `specfact-cli-modules/registry/index.json` — populate with five official bundle entries (semantic version, SHA-256, Ed25519 signature URL, tier, dependencies)
- **MODIFY/EXTEND**: `scripts/publish-module.py` (from marketplace-02) — add bundle packaging, per-bundle signing, and index.json update steps
- **MODIFY**: Each bundle's `module-package.yaml` in `src/specfact_cli/modules/*/` — update `integrity_sha256` and `signature_ed25519` fields after source move and re-sign
- **NEW**: Bundle-level dependency declarations in each bundle's top-level `module-package.yaml`:
  - `specfact-spec` depends on `specfact-project` (generate → plan)
  - `specfact-govern` depends on `specfact-project` (enforce → plan)

## Capabilities

### New Capabilities

- `bundle-extraction`: Per-bundle package directories in `specfact-cli-modules/packages/` with correct namespace structure, re-export shims in `src/specfact_cli/modules/*/` preserving `specfact_cli.modules.*` import paths during migration window, and shared-code audit ensuring no cross-bundle private imports
- `marketplace-publishing`: Automated publish pipeline (`scripts/publish-module.py`) that signs each bundle artifact (SHA-256 + Ed25519), generates `module-package.yaml` with integrity checksums, and writes bundle entries into `specfact-cli-modules/registry/index.json`; offline integrity verification via `verify-modules-signature.py` confirms every bundle's signature before the entry is written
- `official-bundle-tier`: `tier: official` publisher tag (`nold-ai`) applied to all five bundles in the registry index; trust semantics verified by `crypto_validator.py` at install time; bundles satisfy the same security policy as third-party signed modules with stricter publisher validation for the `official` tier

### Modified Capabilities

- `module-security`: Extended to define `official` tier trust level; `crypto_validator.py` validates publisher field against `official` allowlist during install
- `module-marketplace-registry`: `index.json` populated with bundle entries including bundle-level dependency graph (`specfact-spec` → `specfact-project`, `specfact-govern` → `specfact-project`)

## Impact

- **Affected code**:
  - `specfact-cli-modules/packages/specfact-project/` (new)
  - `specfact-cli-modules/packages/specfact-backlog/` (new)
  - `specfact-cli-modules/packages/specfact-codebase/` (new)
  - `specfact-cli-modules/packages/specfact-spec/` (new)
  - `specfact-cli-modules/packages/specfact-govern/` (new)
  - `specfact-cli-modules/registry/index.json` (populated with 5 bundle entries)
  - `specfact-cli-modules/registry/signatures/` (5 bundle signature files)
  - `src/specfact_cli/modules/*/module-package.yaml` (updated checksums + signatures, bundle-level deps for spec and govern)
  - `src/specfact_cli/modules/*/src/` (re-export shims replacing moved source)
  - `src/specfact_cli/common/` (any shared logic factored out of modules)
  - `scripts/publish-module.py` (bundle packaging + index update extension)
- **Affected specs**: New specs for `bundle-extraction`, `marketplace-publishing`, `official-bundle-tier`; deltas on `module-security` (official tier), `module-marketplace-registry` (populated entries)
- **Affected documentation**:
  - `docs/guides/getting-started.md` — update to reflect that bundles are now installable from the marketplace (not only from core)
  - `docs/reference/module-categories.md` — update bundle contents section with package directory layout and namespace information
  - `docs/guides/marketplace.md` — new or updated section on official bundles, trust tiers, and `specfact module install <bundle-id>`
  - `README.md` — update to note that bundles are marketplace-distributed
- **Backward compatibility**: `specfact_cli.modules.*` import paths are preserved as re-export shims for one major version cycle. All 21 existing commands continue to function via the `groups/` category layer introduced in module-migration-01. No CLI-visible behavior changes. Bundle extraction is invisible to end users until module-migration-03 removes the bundled source from core.
- **Rollback plan**: Delete the `specfact-cli-modules/packages/` directories, revert `index.json` to its empty state (`modules: []`), restore original module source from git history, and revert `scripts/publish-module.py` changes. The re-export shims in `src/specfact_cli/modules/*/src/` would also be reverted to the original implementation. No runtime behavior visible to end users changes — rollback is a source-level operation.
- **Blocked by**: `module-migration-01-categorize-and-group` — category metadata in `module-package.yaml` (category, bundle, bundle_group_command, bundle_sub_command) and the `groups/` layer must be in place before extraction can target the correct bundle namespaces and command group assignments

---

## Non-reversible gate

**Closing this change is a one-way gate.** After migration-02 is closed:

- **Canonical source** for the 17 migrated modules (project, plan, import_cmd, sync, migrate, backlog, policy_engine, analyze, drift, validate, repro, contract, spec, sdd, generate, enforce, patch_mode) lives in **specfact-cli-modules** only. New work and fixes for those modules are done in that repo.
- **specfact-cli** keeps only re-export shims under `src/specfact_cli/modules/*/` that delegate to the bundle packages; it no longer owns or maintains the implementation of those modules.
- Reverting "who owns the code" would require a separate, explicit reverse-migration change (not in scope here).

**Before closing this change**, the migration-complete gate must pass (see below). Do not close until all migrated module source is present and verified in specfact-cli-modules.

See **`openspec/changes/module-migration-02-bundle-extraction/MIGRATION_GATE.md`** for expected gate output, why content differs, and the exact command to pass the gate when closing.

---

## Migration-complete gate

Before marking migration-02 complete or merging the change:

1. **Run the gate script** from the specfact-cli worktree (with `SPECFACT_MODULES_REPO` pointing at the specfact-cli-modules clone, on the branch that will be merged):
   ```bash
   SPECFACT_MODULES_REPO=/path/to/specfact-cli-modules python scripts/validate-modules-repo-sync.py --gate
   ```
2. **Gate criteria:**
   - All 17 migrated modules have every source file **present** in specfact-cli-modules at the correct bundle path (script fails if any file is missing).
   - **Content:** If any file’s content differs between worktree and modules repo, the script exits non-zero and lists differing files. Resolve by either (a) migrating missing logic into specfact-cli-modules and re-running, or (b) confirming that differences are only import/namespace and re-running with `SPECFACT_MIGRATION_CONTENT_VERIFIED=1`.
3. **specfact-cli-modules** bundles and registry are merged to the target branch (e.g. `main`) so CI and installers use the canonical bundles.

Only then should this change be closed and future work on those modules continue in specfact-cli-modules only.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #316
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/316>
- **Repository**: nold-ai/specfact-cli
- **PR**: #332 (feature/module-migration-02-bundle-extraction → dev)
- **Last Synced Status**: in progress — specfact-cli-modules published and merged; specfact-cli PR 332 CI is green. Pending: migration-complete gate (17.8) and merge of PR 332 to dev.
- **Sanitized**: false
