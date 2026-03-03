# Change: Modules Repo Quality Parity

## Why

`module-migration-02-bundle-extraction` moved the source for 17 modules from specfact-cli into independently versioned bundle packages in specfact-cli-modules, but explicitly deferred the quality and operational parity work that makes specfact-cli-modules a viable canonical development environment. Sections 18–23 of migration-02's tasks.md capture this deferred scope.

After migration-03 closes, specfact-cli-modules becomes the **canonical and only** home for those 17 modules. Without this change, developers working on bundles in specfact-cli-modules will lack:
- A test suite that runs against bundle code directly (not via specfact-cli shims)
- Contract-first validation (`@icontract` / CrossHair)
- Coverage thresholds
- Pre-commit hooks and a PR orchestrator workflow
- Consistent root-level config (ruff, basedpyright, pylint, pyproject.toml)
- Dependency decoupling (bundle code still imports 85 `specfact_cli.*` paths, some of which are MIGRATE-tier and should live in specfact-cli-modules)
- Docs, LICENSE, and contribution guidance

This is a quality regression against the project's own standard. This change closes that gap.

**Timing constraint:** Sections 18-22 (tests, dependency decoupling/import boundaries, docs baseline, build pipeline, and central config files) of this change **must be completed before or simultaneously with `module-migration-03-core-slimming`**. Once migration-03 closes, specfact-cli-modules is canonical; it must already have equivalent guardrails and decoupling baselines in place.

## What Changes

- **specfact-cli-modules/pyproject.toml** — add or complete coverage config, hatch envs, pytest options, and test paths aligned with specfact-cli
- **specfact-cli-modules** ruff/basedpyright/pylint config — copy or adapt from specfact-cli root to specfact-cli-modules root; adjust paths for `packages/` and `tests/`
- **specfact-cli-modules/.pre-commit-config.yaml** — align with specfact-cli pre-commit hooks
- **specfact-cli-modules/.github/workflows/** — add PR orchestrator (or consolidated workflow) running format, type-check, lint, test, contract-test, coverage, signature verification
- **specfact-cli-modules branch protection** — configure `main`/`dev` with required status checks
- **specfact-cli-modules/tests/** — create test layout mirroring specfact-cli; migrate unit, integration, and e2e tests from specfact-cli that exercise the 17 migrated modules; update imports from `specfact_cli.modules.*` to bundle namespaces
- **specfact-cli-modules/scripts/check-bundle-imports.py** — import gate that fails if bundle code imports MIGRATE-tier paths; add to CI and pre-commit
- **specfact-cli-modules/ALLOWED_IMPORTS.md** — document which `specfact_cli.*` imports are allowed (CORE only) in bundle code
- **specfact-cli-modules package-boundary policy** — enforce high-level module-group boundaries (no lateral cross-group imports without explicit shared abstraction), so each group can be isolated into independent packages over time without hidden coupling
- **IMPORT_DEPENDENCY_ANALYSIS.md** (migration-02 artifact) — fully populate Category, Target bundle, Notes columns for all 85 imports; execute MIGRATE-tier moves into specfact-cli-modules
- **specfact-cli-modules/docs/** — migrate bundle/module docs from specfact-cli; add Jekyll setup; configure GitHub Pages
- **specfact-cli-modules/LICENSE** — match specfact-cli license (nold-ai official bundles)
- **specfact-cli-modules/CONTRIBUTING.md** — align with specfact-cli contribution guidance; state explicitly that this repo hosts only nold-ai official bundles
- **specfact-cli-modules/AGENTS.md** — add bundle versioning policy (semver semantics, `core_compatibility` field rules, release process)

## Capabilities

### New Capabilities

- `modules-repo-test-suite`: specfact-cli-modules has a full test suite (unit, integration, e2e) mirroring specfact-cli, running against bundle packages directly via correct `PYTHONPATH`. `hatch test` passes in the modules repo.
- `modules-repo-quality-pipeline`: `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, coverage threshold — all available and passing in specfact-cli-modules, matching specfact-cli behavior.
- `modules-repo-ci`: PR orchestrator workflow in specfact-cli-modules runs all quality gates on every PR; branch protection enforces gate passage before merge.
- `modules-repo-import-gate`: `scripts/check-bundle-imports.py` fails CI if any bundle code imports a MIGRATE-tier `specfact_cli.*` path; only CORE-tier imports are allowed after decoupling.
- `bundle-versioning-policy`: Documented semver semantics for independent bundle releases, `core_compatibility` maintenance rules, and release process in `AGENTS.md`.

### Modified Capabilities

- `dependency-decoupling`: Bundle code in specfact-cli-modules no longer imports MIGRATE-tier `specfact_cli.*` subsystems; those subsystems are co-located in specfact-cli-modules or declared CORE (stay in specfact-cli as a pip dependency).
- `modules-repo-docs`: Bundle and module documentation migrated to specfact-cli-modules; specfact-cli docs reference high-level install and link out.

## Impact

- **Affected repos**:
  - **specfact-cli-modules** (primary): pyproject.toml, ruff/pyright/pylint config, .pre-commit-config.yaml, .github/workflows/, tests/, scripts/, docs/, LICENSE, CONTRIBUTING.md, AGENTS.md, all five bundle packages (import updates)
  - **specfact-cli**: tests that solely exercise bundle code may be removed after migration to specfact-cli-modules (deferred to a cleanup pass); docs cross-links updated
- **Backward compatibility**: No CLI-visible changes. Import decoupling is internal to specfact-cli-modules packages. Specfact-cli remains the entry point; bundles continue to be installed via the marketplace registry.
- **Rollback plan**: Quality tooling additions (CI, config files, tests) are purely additive in specfact-cli-modules; rollback is deleting the added files. Dependency decoupling (import moves) is a source-level operation; rollback is reverting the import updates.
- **Blocked by**: `module-migration-02-bundle-extraction` — bundles must be present and canonical source in specfact-cli-modules before tests and tooling can be set up for them.
- **Hard timing constraint**: Sections 18-22 of this change **must land before `module-migration-03-core-slimming` closes**. Once migration-03 deletes the in-repo module source, specfact-cli-modules must already have test parity, decoupling/import boundaries, docs baseline, and quality gates or the project loses its quality standard.
- **Wave**: Wave 4 — parallel with or immediately preceding `module-migration-03-core-slimming`
- **Test migration ownership**: This change is the primary owner for migrating bundle-related tests into `specfact-cli-modules` and establishing parity gates there. It does **not** fully own unrelated legacy test cleanup in `specfact-cli`; residual failures outside bundle-scope migration are tracked as follow-up change(s) from migration-03 phase 20.

---

## Migration checklist (review and validate)

| # | Dimension | Status | Notes |
|---|-----------|--------|-------|
| a | **Tests** in specfact-cli-modules | TBD | Section 18: inventory, migrate, verify — must precede migration-03 closure |
| b | **Quality tooling** (contract-test, smart-test, coverage, yaml-lint) | TBD | Section 18.2 — must precede migration-03 closure |
| c | **Dependency decoupling** (import categorization + MIGRATE moves) | TBD | Section 19; builds on migration-02 IMPORT_DEPENDENCY_ANALYSIS.md — must precede migration-03 closure |
| d | **Docs** migrated to specfact-cli-modules with Jekyll | TBD | Section 20 — minimum docs baseline must precede migration-03 closure |
| e | **Build pipeline** (PR orchestrator, branch protection) | TBD | Section 21 — must precede migration-03 closure |
| f | **Central config files** (pyproject, ruff, basedpyright, pylint, pre-commit) | TBD | Section 22 — must precede migration-03 closure |
| g | **License and contribution** artifacts | TBD | Section 23 |
| h | **Bundle versioning policy** in AGENTS.md | TBD | Section 24 (new) |

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #334
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/334>
- **Repository**: nold-ai/specfact-cli (tasks in this repo) + nold-ai/specfact-cli-modules (all implementation)
- **Last Synced Status**: proposed
- **Sanitized**: false
- **Derived from**: `module-migration-02-bundle-extraction` sections 18–23 (deferred scope) + gap analysis 2026-03-02
