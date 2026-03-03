# Change: module-migration-02 - Bundle Extraction and Marketplace Publishing

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
- **NEW (gap)**: Migrate tests for the 17 migrated modules from specfact-cli to specfact-cli-modules; align specfact-cli-modules with specfact-cli quality standards and test scripts (contract-test, smart-test, coverage, format, type-check, lint, CI).
- **NEW (gap)**: Decouple bundle code from hardcoded `specfact_cli` imports — categorize each import (core/keep vs module-only/migrate), migrate module-only dependencies into specfact-cli-modules, and update bundle imports for correct decoupling from core CLI.
- **NEW (gap)**: Migrate docs to specfact-cli-modules (with Jekyll setup) so module/bundle doc updates do not require changes in the CLI core repo.
- **NEW (gap)**: Build pipeline and repo parity — pr-orchestrator (or equivalent) for modules repo; central config files at repo root to match specfact-cli; license and contribution artifacts aligned with specfact-cli for nold-ai official modules (third-party modules are not hosted in this repo).

## Migration checklist (review and validate)

The following dimensions SHALL be reviewed and validated before the migration is complete:

| # | Dimension | Status | Notes |
|---|-----------|--------|-------|
| a | **Source** of modules logic | Done (structure) | Bundle packages and re-export shims in place. Import dependencies (19.1 categorization) required before gate 17.8. |
| a2 | **Import dependency categorization** | Required before gate | 85 `specfact_cli.*` imports must be categorized CORE/MIGRATE/SHARED (tasks.md 17.8.0). Blocks gate 17.8. |
| b | **Tests** | Done (baseline parity in migration-02) | Section 18 completed in this change: inventory, migrated baseline unit/integration/e2e suites, and passing gates in specfact-cli-modules. |
| c | **Docs** | Deferred → migration-05 | Section 20 in module-migration-05-modules-repo-quality. |
| d | **Build pipeline** | Deferred → migration-05 (⚠️ before migration-03) | Section 21 in module-migration-05. Must precede migration-03. |
| e | **Central config** at repo root | Deferred → migration-05 (⚠️ before migration-03) | Section 22 in module-migration-05. Must precede migration-03. |
| f | **License & contribution** | Deferred → migration-05 | Section 23 in module-migration-05-modules-repo-quality. |
| g | **Proposal consistency** (migration-03/04 overlap) | Required before migration-03 starts | Tasks.md 17.9 — reconcile flat-shim and Python import shim removal claims. |

**Scope (both repos):** The specfact-cli (core) repo does not host third-party module source; it contains only the core CLI and re-export shims. The specfact-cli-modules repo hosts only nold-ai official bundle source; third-party modules are not hosted there—they are developed and published from their own repositories and registered in the marketplace/registry.

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

## Gap analysis (2026-03-02)

A structured review of the completed migration scope identified 8 gaps (3 critical, 2 important, 3 minor). The full findings are in **`GAP_ANALYSIS.md`** in this change folder. Key remediation actions taken:

- **Gap 1 (critical)**: Import categorization added as a mandatory pre-gate step (tasks.md 17.8.0) — all 85 `specfact_cli.*` imports must be categorized CORE/MIGRATE/SHARED before gate 17.8 runs.
- **Gap 2 (critical)**: Tasks.md 17.9.2 requires migration-03's proposal to explicitly declare Python import shim removal and provide a version-cycle justification.
- **Gap 3 (critical)**: Tasks.md 17.9.1 requires reconciling the flat-shim removal overlap between migration-03 and migration-04 proposals.
- **Gap 4 (important)**: Sections 19–23 deferred to new change `module-migration-05-modules-repo-quality` (stub created). Section 18 was pulled back into migration-02 and completed here.
- **Gap 5 (important)**: Migration-05 sections 21 (build pipeline) and 22 (central config) carry a hard timing constraint: must land before or simultaneously with migration-03.
- **Gap 6 (minor)**: Behavioral smoke test added to gate 17.8 checklist (tasks.md 17.8.2).
- **Gap 7 (minor)**: Residual core decoupling cleanup assigned to `module-migration-06-core-decoupling-cleanup` (post migration-03/05) — see `GAP_ANALYSIS.md`.
- **Gap 8 (minor)**: Bundle versioning policy added to migration-05 tasks.md section 24.

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

## Test migration and quality parity (gap) — status update

Section 18 is completed in this change.

Delivered in `specfact-cli-modules`:

- Test inventory in `openspec/changes/module-migration-02-bundle-extraction/TEST_INVENTORY.md` with module-to-bundle mapping, migrated tests, and deferred high-coupling suites.
- Quality tooling parity baseline in `pyproject.toml`: `format`, `type-check`, `lint`, `yaml-lint`, `contract-test`, `smart-test`, `test`, with coverage config and thresholds.
- Migrated baseline suites:
  - unit: module IO contract tests across bundle namespaces
  - integration: command app availability tests
  - e2e: Typer `--help` smoke tests for bundle command apps
- CI parity workflow: `.github/workflows/quality-gates.yml` running the gate sequence on Python 3.11/3.12/3.13.

Result: **working on bundle code in specfact-cli-modules now has a passing quality-gate baseline equivalent to specfact-cli, scoped for the dedicated modules repo.**

---

## Dependency decoupling (gap)

Migration-02 moved module **source** to specfact-cli-modules but bundle code still imports from `specfact_cli.*` (adapters, agents, analyzers, backlog, comparators, enrichers, generators, importers, integrations, merge, migrations, models, parsers, sync, templates, utils, validators, etc.). These hardcoded imports tightly couple bundles to the core CLI and prevent true decoupling.

**Required to close the gap:**

1. **Categorize** — For each import: (a) **CORE** — must stay in specfact-cli; bundles depend on `specfact-cli` as a package (e.g. `common`, `contracts.module_interface`, `cli`, `registry`, `modes`, `runtime`, `telemetry`, `versioning`); (b) **MIGRATE** — used only by bundle code; move to appropriate bundle or shared package in specfact-cli-modules; (c) **SHARED** — used by both; consider extracting to shared package or keep in core.
2. **Migrate module-only dependencies** — For each MIGRATE item: copy dependency (and transitive deps) into target bundle or shared package in specfact-cli-modules; update bundle imports to local paths.
3. **Document allowed imports** — After migration, document which `specfact_cli` imports are allowed (CORE) and add a lint/gate to fail on new hardcoded imports of MIGRATE-tier code.
4. **Update bundle deps** — Ensure each bundle declares only `specfact-cli` (and optionally other bundles) as dependency; no hidden imports of non-core specfact_cli submodules.

See **`IMPORT_DEPENDENCY_ANALYSIS.md`** for the full categorized import list and migration targets.

---

## Docs migration (gap)

Module and bundle documentation currently lives in specfact-cli (e.g. `docs/` with Jekyll). When a module changes, docs are updated in the core repo, which forces every doc change to touch the CLI repo. To avoid that, bundle-related docs SHALL be migrated to specfact-cli-modules so that doc updates for modules are made in the modules repo only.

**Required:**

1. **Identify** — List all docs in specfact-cli that describe the 17 migrated modules or the five bundles (guides, reference, getting-started sections that are bundle-specific).
2. **Migrate** — Copy or move those docs into specfact-cli-modules under a `docs/` layout; adjust internal links and navigation.
3. **Jekyll setup** — Add Jekyll page setup in specfact-cli-modules similar to specfact-cli (e.g. `docs/_config.yml`, `docs/_layouts/`, front-matter, GitHub Pages or equivalent) so that module docs can be built and published from the modules repo.
4. **Cross-links** — specfact-cli docs may link to "module docs" via a stable URL (e.g. docs.specfact.io/modules/ or a separate site); document the URL strategy.
5. **Ownership** — After migration, bundle/module doc changes are made in specfact-cli-modules; specfact-cli docs reference high-level "install bundles" and link out to modules docs where appropriate.

---

## Build pipeline (gap)

specfact-cli uses a pr-orchestrator and multiple workflows for quality gates. The modules repo SHALL have a build pipeline that mirrors this so that PRs to specfact-cli-modules run the same discipline (format, type-check, lint, test, contract-test, coverage, optional signing verification).

**Required:**

1. **pr-orchestrator (or equivalent)** — Add or adapt a PR orchestration workflow for the specfact-cli-modules repo (e.g. `.github/workflows/pr-orchestrator.yml` or a single workflow that runs all gates) so that each PR runs format, type-check, lint, test, and any module-specific checks.
2. **Workflow alignment** — Ensure workflow names, job structure, and gate order are consistent with specfact-cli where it makes sense; document differences (e.g. no Docker build if not needed).
3. **Branch protection** — Align with specfact-cli (e.g. `dev`/`main` protection, required status checks).

---

## Central config files (gap)

specfact-cli has central config at repo root: `pyproject.toml`, `ruff.toml` or config in pyproject, `pyrightconfig.json` or basedpyright in pyproject, `pylintrc` or equivalent, `.pre-commit-config.yaml`, etc. specfact-cli-modules SHALL have equivalent config at repo root so that the same tooling and standards apply.

**Required:**

1. **Audit** — List all root-level config files in specfact-cli that affect format, lint, type-check, tests, and pre-commit.
2. **Copy or adapt** — Add corresponding config to specfact-cli-modules root; adjust paths if needed (e.g. `packages/`, `tests/`).
3. **Single source of truth** — Developers and CI use the same config; no divergence in line length, rule sets, or test options unless explicitly documented.

---

## License and contribution (gap)

specfact-cli-modules hosts **nold-ai official bundles only**. Third-party modules are not foreseen in this repo: they are developed and published from their own repositories and registered in the marketplace/registry; the specfact-cli-modules repo is not used to host third-party module source. License and contribution artifacts SHALL match specfact-cli at repo root so that nold-ai modules have the same legal and contribution expectations as the core CLI.

**Required:**

1. **License** — LICENSE file at repo root SHALL match specfact-cli (e.g. same license type and copyright for nold-ai). All official bundle code in this repo is under that license.
2. **Contribution** — CONTRIBUTING.md (or equivalent) SHALL align with specfact-cli: how to contribute, branch policy, PR process, code standards. Clarify that contributions to this repo are for **official nold-ai bundles**; third-party authors publish modules from their own repos.
3. **Other root artifacts** — Add any other root-level artifacts that specfact-cli has and that apply to the modules repo (e.g. CODE_OF_CONDUCT, SECURITY, .github/CODEOWNERS for nold-ai).
4. **Explicit scope** — In README or CONTRIBUTING, state: "This repository contains the source and docs for the official SpecFact CLI bundles (nold-ai). Third-party modules are not hosted here; they are published to the registry from their own repositories."

**Clarification:** Yes — third-party modules are **not** hosted in the specfact-cli-modules repo. This repo is for nold-ai official bundles only. Third-party module authors maintain their own repos and publish to the marketplace/registry; specfact-cli (core) and the registry index reference those external modules.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #316
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/316>
- **Repository**: nold-ai/specfact-cli
- **PR**: #332 (feature/module-migration-02-bundle-extraction → dev)
- **Last Synced Status**: complete in specfact-cli scope — specfact-cli-modules published and merged; Section 18 test/quality parity completed in migration-02 and verified with passing local gates; 17.8.2 behavioral smoke and 17.8.3 presence gate executed successfully (presence gate passed with `SPECFACT_MIGRATION_CONTENT_VERIFIED=1`); PR #332 merged to `dev` (commit `039da8b`). Deferred follow-up scope (19.2-23.5) is tracked in `module-migration-05-modules-repo-quality`.
- **Sanitized**: false
