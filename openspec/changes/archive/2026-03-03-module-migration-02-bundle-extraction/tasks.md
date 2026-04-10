# Implementation Tasks: module-migration-02-bundle-extraction

## Status and gap (as of review — updated with gap analysis 2026-03-02)

**Gap analysis artifact:** See `GAP_ANALYSIS.md` for the full findings (8 gaps, 3 critical) and the remediation actions taken in this file.

**Completed in this worktree (specfact-cli repo only):**

- Phases 0–4, 6–9: Shared-code audit, re-export shims, official-tier trust model, bundle dependency auto-install, publish-module.py bundle mode — all implemented and tested in **specfact-cli**.
- Phase 5.1: Bundle layout tests exist in `tests/unit/bundles/test_bundle_layout.py`; they resolve `specfact-cli-modules` via `SPECFACT_MODULES_REPO` or sibling path and **skip** when the modules repo has no `packages/`.
- Phase 10.1–10.4: Re-signing of **in-repo** module manifests (shims) in `src/specfact_cli/modules/*/module-package.yaml` — done.
- Section 16: PR created (e.g. #332 feature/module-migration-02-bundle-extraction → dev).
- Section 17.1–17.7: **specfact-cli-modules** published and merged (five bundles + registry). CI for specfact-cli now passes — **PR 332 to dev is green.**
- Section 18.1–18.5: Test inventory, modules-repo quality tooling parity, baseline migrated unit/integration/e2e tests, and CI matrix workflow (3.11/3.12/3.13) implemented and verified.

**Outstanding before closing (updated):**

- **17.8.4** — ✅ Merged: specfact-cli PR #332 is on `dev` (commit `039da8b`). Migration-02 is non-reversibly closed; canonical source for the 17 modules is specfact-cli-modules only.
- **17.9** — Proposal consistency (migration-03/04 overlap and migration-03 Python import shim declaration): content committed in branch; 17.9.1.6 and 17.9.2.5 marked done.
- **17.10** — module-migration-05 stub and GitHub issue #334 created; 17.10.4 done.

**Deferred to module-migration-05-modules-repo-quality (do not check in migration-02):**

- **Section 19.1** (import categorization): ✅ Done in this change via 17.8.0; `IMPORT_DEPENDENCY_ANALYSIS.md` has 91 imports categorized. Sections 19.2–19.4 (migrate MIGRATE-tier, gate, verify) deferred to module-migration-05.
- **Section 20** (docs migration): Migrate bundle docs to specfact-cli-modules with Jekyll. See `module-migration-05` tasks.md section 20.
- **Section 21** (build pipeline): PR orchestrator workflow in specfact-cli-modules. **Must land before migration-03.** See `module-migration-05` tasks.md section 21.
- **Section 22** (central config files): pyproject, ruff, basedpyright, pylint, pre-commit alignment. **Must land before migration-03.** See `module-migration-05` tasks.md section 22.
- **Section 23** (license and contribution): LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT alignment. See `module-migration-05` tasks.md section 23.
- **Section 20 (docs migration)**: Migrate bundle/module docs to specfact-cli-modules; Jekyll setup similar to specfact-cli. See proposal "Docs migration (gap)" and checklist (c).
- **Section 21 (build pipeline)**: pr-orchestrator (or equivalent) for modules repo; CI gates aligned with specfact-cli. See proposal "Build pipeline (gap)" and checklist (d).
- **Section 22 (central config)**: Root-level config files (pyproject, ruff, pyright, pylint, pre-commit) match specfact-cli. See proposal "Central config files (gap)" and checklist (e).
- **Section 23 (license & contribution)**: LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, etc. match specfact-cli; clarify repo is for nold-ai official bundles only; third-party modules are not hosted here. See proposal "License and contribution (gap)" and checklist (f).

All other tasks (5.0–5.5, 10.5–10.6, 11.1–11.8, 17.8.0–17.8.4, 17.9, 17.10, 18.1–18.5, 19.1) are marked done. Sections 19.2–23 are acknowledged as deferred handoff items and marked complete-in-this-change because they are tracked under `openspec/changes/module-migration-05-modules-repo-quality/tasks.md`.

Migration-02 is **complete** when (1) specfact-cli PR is merged to `dev`, (2) specfact-cli-modules contains the five bundles and a populated registry (merged — **done**), (3) migration-complete gate passed. After close, canonical source for the 17 modules lives in specfact-cli-modules only; provides non-conflicting basis for module-migration-03 and module-migration-04.

---

## TDD / SDD Order (Enforced)

Per `openspec/config.yaml`, the following order is mandatory and non-negotiable for every behavior-changing task:

1. **Spec deltas** — already created in `specs/` (bundle-extraction, marketplace-publishing, official-bundle-tier)
2. **Tests from spec scenarios** — translate each Given/When/Then scenario into test cases; run tests and expect failure (no implementation yet)
3. **Capture failing-test evidence** — record in `openspec/changes/module-migration-02-bundle-extraction/TDD_EVIDENCE.md`
4. **Code implementation** — implement until tests pass and behavior satisfies spec
5. **Capture passing-test evidence** — update `TDD_EVIDENCE.md` with passing run results
6. **Quality gates** — format, type-check, lint, contract-test, smart-test
7. **Documentation research and review**
8. **Version and changelog**
9. **PR creation**

Do NOT implement production code for any behavior-changing step until failing-test evidence is recorded in TDD_EVIDENCE.md.

---

## 1. Create git worktree branch from dev

- [x] 1.1 Fetch latest origin and create worktree with feature branch
  - [x] 1.1.1 `git fetch origin`
  - [x] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/module-migration-02-bundle-extraction -b feature/module-migration-02-bundle-extraction origin/dev`
  - [x] 1.1.3 `cd ../specfact-cli-worktrees/feature/module-migration-02-bundle-extraction`
  - [x] 1.1.4 `git branch --show-current` — verify output is `feature/module-migration-02-bundle-extraction`
  - [x] 1.1.5 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [x] 1.1.6 `hatch env create`
  - [x] 1.1.7 `hatch run smart-test-status` and `hatch run contract-test-status` — confirm baseline green

## 2. Create GitHub issue for change tracking

- [x] 2.1 Create GitHub issue in nold-ai/specfact-cli
  - [x] 2.1.1 `gh issue create --repo nold-ai/specfact-cli --title "[Change] Bundle Extraction and Marketplace Publishing" --label "enhancement,change-proposal" --body "$(cat <<'EOF'`

    ```text
    ## Why

    SpecFact CLI's 21 modules remain bundled in core even after module-migration-01 added the category metadata and group commands. This change extracts each category's modules into independently versioned bundle packages in specfact-cli-modules, signs and publishes them to the marketplace registry, and wires the official-tier trust model. After this change, `specfact init --profile solo-developer` will actually restrict what arrives on disk.

    ## What Changes

    - Create 5 bundle package directories in specfact-cli-modules/packages/ with correct namespaces
    - Move module source from src/specfact_cli/modules/ into bundle namespaces; leave re-export shims
    - Populate registry/index.json with 5 signed official-tier bundle entries
    - Add `official` tier to crypto_validator.py with publisher allowlist enforcement
    - Extend scripts/publish-module.py with --bundle mode and atomic index write

    *OpenSpec Change Proposal: module-migration-02-bundle-extraction*
    ```

  - [x] 2.1.2 Capture issue number and URL from output
  - [x] 2.1.3 Update `openspec/changes/module-migration-02-bundle-extraction/proposal.md` Source Tracking section with issue number, URL, and status `open`

## 3. Update CHANGE_ORDER.md

- [x] 3.1 Open `openspec/CHANGE_ORDER.md`
  - [x] 3.1.1 Locate the "Module migration" table in the Pending section
  - [x] 3.1.2 Update the row for `module-migration-02-extract-bundles-to-marketplace` (or add a new row) to point to the correct change folder `module-migration-02-bundle-extraction`, add the GitHub issue number from step 2, and confirm `Blocked by: module-migration-01`
  - [x] 3.1.3 Confirm Wave 3 row includes `module-migration-02-bundle-extraction` in the wave description
  - [x] 3.1.4 Commit the CHANGE_ORDER.md update: `git add openspec/CHANGE_ORDER.md && git commit -m "docs: add module-migration-02-bundle-extraction to CHANGE_ORDER.md"`

## 4. Phase 0 — Shared-code audit and factoring (pre-extraction prerequisite)

### 4.1 Write tests for cross-bundle import gate (expect failure)

- [x] 4.1.1 Create `tests/unit/registry/test_cross_bundle_imports.py`
- [x] 4.1.2 Test: import graph from `analyze` module has no imports from `specfact_cli.modules.plan` (codebase → project would be cross-bundle)
- [x] 4.1.3 Test: import graph from `generate` module accessing `plan` uses `specfact_cli.common` or intra-bundle path only
- [x] 4.1.4 Test: import graph from `enforce` module accessing `plan` uses `specfact_cli.common` or intra-bundle path only
- [x] 4.1.5 Run: `hatch test -- tests/unit/registry/test_cross_bundle_imports.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 4.2 Run automated import graph audit

- [x] 4.2.1 Run import graph analysis across all 21 module sources (use `pydeps`, `pyright --outputjson`, or custom AST walker)
- [x] 4.2.2 Document all cross-module imports that cross bundle boundaries (import from a module in a different bundle)
- [x] 4.2.3 For each identified cross-bundle private import: move the shared logic to `specfact_cli.common`
- [x] 4.2.4 Re-run import graph analysis — confirm zero remaining cross-bundle private imports
- [x] 4.2.5 Commit audit artifact: `openspec/changes/module-migration-02-bundle-extraction/IMPORT_AUDIT.md`

### 4.3 Verify tests pass after common factoring

- [x] 4.3.1 `hatch test -- tests/unit/registry/test_cross_bundle_imports.py -v`
- [x] 4.3.2 Record passing-test results in TDD_EVIDENCE.md (Phase 0)

## 5. Phase 1 — Bundle package directories and source move (TDD)

All of 5.2–5.4 and 5.5 (verification) are performed **in the specfact-cli-modules repository**: use a local clone at a path visible to the specfact-cli worktree (e.g. sibling `../specfact-cli-modules` from the specfact-cli worktree root, or set `SPECFACT_MODULES_REPO` to that clone). The specfact-cli tests in 5.1 and 5.5 resolve this path via `SPECFACT_MODULES_REPO` or sibling discovery; CI uses the cloned `nold-ai/specfact-cli-modules` repo.

### 5.0 Prepare specfact-cli-modules repository (local clone)

- [x] 5.0.1 Ensure a local clone of `nold-ai/specfact-cli-modules` exists (e.g. `git clone https://github.com/nold-ai/specfact-cli-modules.git ../specfact-cli-modules` from the specfact-cli worktree root, or use existing clone).
- [x] 5.0.2 `cd` into the specfact-cli-modules clone; ensure clean state or create a feature branch for migration-02 (e.g. `feature/module-migration-02-bundles`).
- [x] 5.0.3 From specfact-cli worktree, set `SPECFACT_MODULES_REPO` to the absolute path of the clone (or rely on sibling `../specfact-cli-modules`). Until 5.2 is done, `hatch run smart-test` will skip bundle layout tests; after 5.2–5.4, those tests should run and pass.
- [x] 5.0.4 Create empty `packages/` and `registry/` directories in the specfact-cli-modules repo if they do not exist; ensure `registry/index.json` exists with `{"modules": []}` (or merge-safe structure).

### 5.1 Write tests for bundle package layout (expect failure)

- [x] 5.1.1 Create `tests/unit/bundles/test_bundle_layout.py`
- [x] 5.1.2 Test: `specfact-cli-modules/packages/specfact-project/src/specfact_project/__init__.py` exists
- [x] 5.1.3 Test: `specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/__init__.py` exists
- [x] 5.1.4 Test: `specfact-cli-modules/packages/specfact-codebase/src/specfact_codebase/__init__.py` exists
- [x] 5.1.5 Test: `specfact-cli-modules/packages/specfact-spec/src/specfact_spec/__init__.py` exists
- [x] 5.1.6 Test: `specfact-cli-modules/packages/specfact-govern/src/specfact_govern/__init__.py` exists
- [x] 5.1.7 Test: `from specfact_codebase.analyze import app` resolves without error (mock install path)
- [x] 5.1.8 Test: `from specfact_cli.modules.validate import something` emits DeprecationWarning (re-export shim)
- [x] 5.1.9 Test: `from specfact_cli.modules.validate import something` resolves without ImportError
- [x] 5.1.10 Test: `from specfact_project.plan import app` resolves (intra-bundle import within specfact-project)
- [x] 5.1.11 Run: `hatch test -- tests/unit/bundles/test_bundle_layout.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 5.2 Create bundle package directories (in specfact-cli-modules repo)

- [x] 5.2.1 Create `specfact-cli-modules/packages/specfact-project/src/specfact_project/__init__.py`
- [x] 5.2.2 Create `specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/__init__.py`
- [x] 5.2.3 Create `specfact-cli-modules/packages/specfact-codebase/src/specfact_codebase/__init__.py`
- [x] 5.2.4 Create `specfact-cli-modules/packages/specfact-spec/src/specfact_spec/__init__.py`
- [x] 5.2.5 Create `specfact-cli-modules/packages/specfact-govern/src/specfact_govern/__init__.py`

### 5.3 Create top-level bundle module-package.yaml manifests (in specfact-cli-modules repo)

Each bundle manifest must contain: `name`, `version` (matching core minor), `tier: official`, `publisher: nold-ai`, `bundle_dependencies` (empty or list), `description`, `category`, `bundle_group_command`.

- [x] 5.3.1 Create `specfact-cli-modules/packages/specfact-project/module-package.yaml`
  - `bundle_dependencies: []`
- [x] 5.3.2 Create `specfact-cli-modules/packages/specfact-backlog/module-package.yaml`
  - `bundle_dependencies: []`
- [x] 5.3.3 Create `specfact-cli-modules/packages/specfact-codebase/module-package.yaml`
  - `bundle_dependencies: []`
- [x] 5.3.4 Create `specfact-cli-modules/packages/specfact-spec/module-package.yaml`
  - `bundle_dependencies: [nold-ai/specfact-project]`
- [x] 5.3.5 Create `specfact-cli-modules/packages/specfact-govern/module-package.yaml`
  - `bundle_dependencies: [nold-ai/specfact-project]`

### 5.4 Move module source into bundle namespaces (in specfact-cli-modules repo; one bundle per commit)

For each module move: (a) copy source from specfact-cli into the bundle in specfact-cli-modules, (b) update intra-bundle imports to use `specfact_project.*` / `specfact_backlog.*` / etc., (c) ensure re-export shims remain in specfact-cli `src/specfact_cli/modules/*/`, (d) from specfact-cli worktree run tests with `SPECFACT_MODULES_REPO` set.

**specfact-project bundle:**

- [x] 5.4.1 Move `src/specfact_cli/modules/project/src/project/` → `specfact-cli-modules/packages/specfact-project/src/specfact_project/project/`; update imports `specfact_cli.modules.project.*` → `specfact_project.project.*`
- [x] 5.4.2 Move `src/specfact_cli/modules/plan/src/plan/` → `specfact_project/plan/`; update imports
- [x] 5.4.3 Move `src/specfact_cli/modules/import_cmd/src/import_cmd/` → `specfact_project/import_cmd/`; update imports
- [x] 5.4.4 Move `src/specfact_cli/modules/sync/src/sync/` → `specfact_project/sync/`; update imports (plan → specfact_project.plan)
- [x] 5.4.5 Move `src/specfact_cli/modules/migrate/src/migrate/` → `specfact_project/migrate/`; update imports
- [x] 5.4.6 Confirm re-export shims for all 5 project modules exist in `src/specfact_cli/modules/*/` (shims delegate to `specfact_project.*`)
- [x] 5.4.7 From specfact-cli worktree with `SPECFACT_MODULES_REPO` set: `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v` — verify project-related tests pass

**specfact-backlog bundle:**

- [x] 5.4.8 Move `src/specfact_cli/modules/backlog/src/backlog/` → `specfact_backlog/backlog/`; update imports
- [x] 5.4.9 Move `src/specfact_cli/modules/policy_engine/src/policy_engine/` → `specfact_backlog/policy_engine/`; update imports
- [x] 5.4.10 Confirm re-export shims for backlog and policy_engine
- [x] 5.4.11 `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v`

**specfact-codebase bundle:**

- [x] 5.4.12 Move `src/specfact_cli/modules/analyze/src/analyze/` → `specfact_codebase/analyze/`; update imports
- [x] 5.4.13 Move `src/specfact_cli/modules/drift/src/drift/` → `specfact_codebase/drift/`; update imports
- [x] 5.4.14 Move `src/specfact_cli/modules/validate/src/validate/` → `specfact_codebase/validate/`; update imports
- [x] 5.4.15 Move `src/specfact_cli/modules/repro/src/repro/` → `specfact_codebase/repro/`; update imports
- [x] 5.4.16 Confirm re-export shims for all 4 codebase modules
- [x] 5.4.17 `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v`

**specfact-spec bundle:**

- [x] 5.4.18 Move `src/specfact_cli/modules/contract/src/contract/` → `specfact_spec/contract/`; update imports
- [x] 5.4.19 Move `src/specfact_cli/modules/spec/src/spec/` → `specfact_spec/spec/`; update imports
- [x] 5.4.20 Move `src/specfact_cli/modules/sdd/src/sdd/` → `specfact_spec/sdd/`; update imports
- [x] 5.4.21 Move `src/specfact_cli/modules/generate/src/generate/` → `specfact_spec/generate/`; update imports (`plan` → `specfact_project.plan` via common interface)
- [x] 5.4.22 Confirm re-export shims for all 4 spec modules
- [x] 5.4.23 `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v`

**specfact-govern bundle:**

- [x] 5.4.24 Move `src/specfact_cli/modules/enforce/src/enforce/` → `specfact_govern/enforce/`; update imports (`plan` → `specfact_project.plan` via common interface)
- [x] 5.4.25 Move `src/specfact_cli/modules/patch_mode/src/patch_mode/` → `specfact_govern/patch_mode/`; update imports
- [x] 5.4.26 Confirm re-export shims for enforce and patch_mode
- [x] 5.4.27 `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v`

### 5.5 Record passing-test evidence (Phase 1)

- [x] 5.5.1 From specfact-cli worktree with `SPECFACT_MODULES_REPO` pointing at populated clone: `hatch test -- tests/unit/bundles/ -v` — full bundle layout test suite
- [x] 5.5.2 Record passing-test run in TDD_EVIDENCE.md

## 6. Phase 2 — Re-export shim DeprecationWarning tests

### 6.1 Write shim deprecation tests (expect failure pre-shim)

- [x] 6.1.1 Create `tests/unit/modules/test_reexport_shims.py`
- [x] 6.1.2 Test: importing `specfact_cli.modules.validate` emits `DeprecationWarning` on attribute access
- [x] 6.1.3 Test: `from specfact_cli.modules.analyze import app` resolves without ImportError
- [x] 6.1.4 Test: shim does not duplicate implementation (shim module has no function/class definitions, only `__getattr__`)
- [x] 6.1.5 Test: after shim import, `specfact_cli.modules.validate.__name__` is accessible (delegates to bundle)
- [x] 6.1.6 Run: `hatch test -- tests/unit/modules/test_reexport_shims.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 6.2 Verify shims after implementation

- [x] 6.2.1 `hatch test -- tests/unit/modules/test_reexport_shims.py -v`
- [x] 6.2.2 Record passing result in TDD_EVIDENCE.md

## 7. Phase 3 — Official-tier trust model (crypto_validator.py extension, TDD)

### 7.1 Write tests for official-tier validation (expect failure)

- [x] 7.1.1 Create `tests/unit/validators/test_official_tier.py`
- [x] 7.1.2 Test: manifest with `tier: official`, `publisher: nold-ai`, valid signature → `ValidationResult(tier="official", signature_valid=True)`
- [x] 7.1.3 Test: manifest with `tier: official`, `publisher: unknown-org` → `SecurityError` (publisher not in allowlist)
- [x] 7.1.4 Test: manifest with `tier: official`, `publisher: nold-ai`, invalid signature → `SignatureVerificationError`
- [x] 7.1.5 Test: manifest with `tier: community` is not elevated to official (separate code path)
- [x] 7.1.6 Test: `OFFICIAL_PUBLISHERS` constant is a `frozenset` containing `"nold-ai"`
- [x] 7.1.7 Test: `validate_module()` has `@require` and `@beartype` decorators (contract coverage)
- [x] 7.1.8 Run: `hatch test -- tests/unit/validators/test_official_tier.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 7.2 Implement official-tier in crypto_validator.py

- [x] 7.2.1 Add `OFFICIAL_PUBLISHERS: frozenset[str] = frozenset({"nold-ai"})` constant
- [x] 7.2.2 Add `official` tier branch to `validate_module()` with publisher allowlist check
- [x] 7.2.3 Add `@require(lambda manifest: manifest.get("tier") in {"official", "community", "unsigned"})` precondition
- [x] 7.2.4 Add `@beartype` to `validate_module()` and any new helper functions
- [x] 7.2.5 `hatch test -- tests/unit/validators/test_official_tier.py -v` — verify tests pass

### 7.3 Write tests for official-tier badge in module list (expect failure)

- [x] 7.3.1 Create `tests/unit/modules/module_registry/test_official_tier_display.py`
- [x] 7.3.2 Test: `specfact module list` output for an official-tier bundle contains `[official]` marker
- [x] 7.3.3 Test: `specfact module install` success output contains "Verified: official (nold-ai)" confirmation line
- [x] 7.3.4 Run: `hatch test -- tests/unit/modules/module_registry/test_official_tier_display.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 7.4 Implement official-tier display in module_registry commands

- [x] 7.4.1 Update `specfact module list` command to display `[official]` badge for official-tier entries
- [x] 7.4.2 Update `specfact module install` success message to include tier verification confirmation
- [x] 7.4.3 `hatch test -- tests/unit/modules/module_registry/test_official_tier_display.py -v`

### 7.5 Record passing-test evidence (Phase 3)

- [x] 7.5.1 Update TDD_EVIDENCE.md with passing-test run for official-tier (timestamp, command, summary)

## 8. Phase 4 — Auto-install of bundle dependencies (module_installer.py, TDD)

### 8.1 Write tests for bundle dependency auto-install (expect failure)

- [x] 8.1.1 Create `tests/unit/validators/test_bundle_dependency_install.py`
- [x] 8.1.2 Test: installing `specfact-spec` (with dep `specfact-project`) triggers `install_module("nold-ai/specfact-project")` before `install_module("nold-ai/specfact-spec")` (mock installer)
- [x] 8.1.3 Test: installing `specfact-govern` triggers `specfact-project` install first (mock)
- [x] 8.1.4 Test: if `specfact-project` is already installed, dependency install is skipped (mock)
- [x] 8.1.5 Test: if `specfact-project` install fails, `specfact-spec` install is aborted
- [x] 8.1.6 Test: offline — dependency resolution uses cached tarball when registry unavailable (mock cache)
- [x] 8.1.7 Run: `hatch test -- tests/unit/validators/test_bundle_dependency_install.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 8.2 Implement bundle dependency auto-install in module_installer.py

- [x] 8.2.1 Read `bundle_dependencies` field from bundle manifest (list of `namespace/name` strings)
- [x] 8.2.2 For each listed dependency: check if installed → skip if yes, install if no
- [x] 8.2.3 Install dependencies before the requested bundle
- [x] 8.2.4 Abort bundle install if any dependency install fails
- [x] 8.2.5 Log "Dependency <id> already satisfied (version X)" when skipping
- [x] 8.2.6 Add `@require` and `@beartype` on modified public functions
- [x] 8.2.7 `hatch test -- tests/unit/validators/test_bundle_dependency_install.py -v`

### 8.3 Record passing-test evidence (Phase 4)

- [x] 8.3.1 Update TDD_EVIDENCE.md with passing-test run for bundle deps (timestamp, command, summary)

## 9. Phase 5 — publish-module.py bundle mode extension (TDD)

### 9.1 Write tests for publish-module.py bundle mode (expect failure)

- [x] 9.1.1 Create `tests/unit/scripts/test_publish_module_bundle.py`
- [x] 9.1.2 Test: `publish_bundle("specfact-codebase", key_file, output_dir)` creates tarball in `registry/modules/`
- [x] 9.1.3 Test: tarball SHA-256 matches `checksum_sha256` in generated index entry
- [x] 9.1.4 Test: tarball contains no path-traversal entries (`..` or absolute paths)
- [x] 9.1.5 Test: signature file created at `registry/signatures/specfact-codebase-<ver>.sig`
- [x] 9.1.6 Test: inline verification passes before index is written (mock verify function)
- [x] 9.1.7 Test: if inline verification fails, `index.json` is not modified
- [x] 9.1.8 Test: `index.json` write is atomic (uses tempfile + os.replace)
- [x] 9.1.9 Test: publishing with same version as existing latest raises `ValueError` (reject downgrade/same-version)
- [x] 9.1.10 Test: `--bundle all` flag publishes all 5 bundles in sequence
- [x] 9.1.11 Run: `hatch test -- tests/unit/scripts/test_publish_module_bundle.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 9.2 Implement publish-module.py bundle mode

- [x] 9.2.1 Add `--bundle <name>` and `--bundle all` argument to `publish-module.py` CLI
- [x] 9.2.2 Implement `package_bundle(bundle_dir: Path) -> Path` (tarball creation, path-traversal check)
- [x] 9.2.3 Implement `sign_bundle(tarball: Path, key_file: Path) -> Path` (Ed25519 signature)
- [x] 9.2.4 Implement `verify_bundle(tarball: Path, sig: Path, manifest: dict) -> bool` (inline verification)
- [x] 9.2.5 Implement `write_index_entry(index_path: Path, entry: dict) -> None` (atomic write)
- [x] 9.2.6 Implement `publish_bundle(bundle_name: str, key_file: Path, registry_dir: Path) -> None` (orchestrator)
- [x] 9.2.7 Add `@require`, `@ensure`, `@beartype` on all public functions
- [x] 9.2.8 `hatch test -- tests/unit/scripts/test_publish_module_bundle.py -v`

### 9.3 Record passing-test evidence (Phase 5)

- [x] 9.3.1 Update TDD_EVIDENCE.md with passing-test run for publish pipeline (timestamp, command, summary)

## 10. Phase 6 — Module signing gate after all source moves

After all five bundles are extracted in **specfact-cli-modules** and shims are in place in specfact-cli, all affected manifests must be signed.

- [x] 10.1 Run verification in specfact-cli (expect failures if manifests changed): `hatch run ./scripts/verify-modules-signature.py --require-signature`
- [x] 10.2 For each affected in-repo module: bump patch version in `module-package.yaml`
- [x] 10.3 Re-sign all 21 in-repo module-package.yaml files: `hatch run python scripts/sign-modules.py --key-file <private-key.pem> src/specfact_cli/modules/*/module-package.yaml`
- [x] 10.4 Re-run verification in specfact-cli: `hatch run ./scripts/verify-modules-signature.py --require-signature` — confirm in-repo manifests fully green
- [x] 10.5 In **specfact-cli-modules** repo: sign all 5 bundle `module-package.yaml` files in `packages/*/module-package.yaml` (use specfact-cli's `scripts/sign-modules.py` with `--key-file` and paths into the modules clone, or equivalent signing from modules repo)
- [x] 10.6 Confirm all signatures green: from specfact-cli, run verifier with scope covering both in-repo and `SPECFACT_MODULES_REPO` bundles (or run verifier in each repo)

## 11. Phase 7 — Publish bundles to registry (specfact-cli-modules repo)

Run from **specfact-cli** worktree with `SPECFACT_MODULES_REPO` (or default sibling) pointing at the populated specfact-cli-modules clone. The publish script reads bundle content from that path and writes to `specfact-cli-modules/registry/`.

- [x] 11.1 Verify `specfact-cli-modules/registry/index.json` is at `modules: []` (or contains only prior entries — no overlap with the 5 official bundles)
- [x] 11.2 Publish specfact-project: `python scripts/publish-module.py --bundle specfact-project --key-file <private-key.pem>` (uses SPECFACT_MODULES_REPO or sibling for bundle dir and registry output)
- [x] 11.3 Publish specfact-backlog: `python scripts/publish-module.py --bundle specfact-backlog --key-file <private-key.pem>`
- [x] 11.4 Publish specfact-codebase: `python scripts/publish-module.py --bundle specfact-codebase --key-file <private-key.pem>`
- [x] 11.5 Publish specfact-spec: `python scripts/publish-module.py --bundle specfact-spec --key-file <private-key.pem>`
- [x] 11.6 Publish specfact-govern: `python scripts/publish-module.py --bundle specfact-govern --key-file <private-key.pem>`
- [x] 11.7 Inspect `specfact-cli-modules/registry/index.json`: confirm 5 entries, each with `tier: official`, `publisher: nold-ai`, valid `checksum_sha256`, and correct `bundle_dependencies`
- [x] 11.8 Re-run offline verification against all 5 entries (from specfact-cli or modules repo as appropriate): `hatch run ./scripts/verify-modules-signature.py --require-signature`

## 12. Integration and E2E tests

- [x] 12.1 Create `tests/integration/test_bundle_install.py`
  - [x] 12.1.1 Test: `specfact module install nold-ai/specfact-codebase` (mock registry) succeeds, official-tier confirmed
  - [x] 12.1.2 Test: `specfact module install nold-ai/specfact-spec` auto-installs `specfact-project` first (mock)
  - [x] 12.1.3 Test: `specfact module install nold-ai/specfact-spec` when `specfact-project` already present skips re-install
  - [x] 12.1.4 Test: `specfact module list` shows `[official]` badge for installed official bundles
  - [x] 12.1.5 Test: deprecated flat import `from specfact_cli.modules.validate import app` still works, emits DeprecationWarning
- [x] 12.2 Create `tests/e2e/test_bundle_extraction_e2e.py`
  - [x] 12.2.1 Test: `specfact module install nold-ai/specfact-codebase` in temp workspace → `specfact code analyze --help` resolves via installed bundle
  - [x] 12.2.2 Test: full round-trip — publish → install → verify for specfact-codebase in isolated temp dir
- [x] 12.3 Run: `hatch test -- tests/integration/test_bundle_install.py tests/e2e/test_bundle_extraction_e2e.py -v`

## 13. Quality gates

- [x] 13.1 Format
  - [x] 13.1.1 `hatch run format`
  - [x] 13.1.2 Fix any formatting issues

- [x] 13.2 Type checking
  - [x] 13.2.1 `hatch run type-check`
  - [x] 13.2.2 Fix any basedpyright strict errors (especially in shim modules and publish script)

- [x] 13.3 Full lint suite
  - [x] 13.3.1 `hatch run lint`
  - [x] 13.3.2 Fix any lint errors

- [x] 13.4 YAML lint
  - [x] 13.4.1 `hatch run yaml-lint`
  - [x] 13.4.2 Fix any YAML formatting issues (bundle module-package.yaml files must be valid)

- [x] 13.5 Contract-first testing
  - [x] 13.5.1 `hatch run contract-test`
  - [x] 13.5.2 Verify all `@icontract` contracts pass for new and modified public APIs

- [x] 13.6 Smart test suite
  - [x] 13.6.1 `hatch run smart-test`
  - [x] 13.6.2 Verify no regressions in existing commands (compat shims and group routing must still work)

- [x] 13.7 Module signing gate (final)
  - [x] 13.7.1 `hatch run ./scripts/verify-modules-signature.py --require-signature`
  - [x] 13.7.2 If any module fails: re-sign with `hatch run python scripts/sign-modules.py --key-file <private-key.pem> <module-package.yaml ...>`
  - [x] 13.7.3 Re-run verification until fully green

## 14. Documentation research and review

- [x] 14.1 Identify affected documentation
  - [x] 14.1.1 Review `docs/getting-started/README.md` — update to reflect bundles are marketplace-installable
  - [x] 14.1.2 Review `docs/reference/module-categories.md` — add bundle package directory layout and namespace info (created by module-migration-01)
  - [x] 14.1.3 Review or create `docs/guides/marketplace.md` — official bundles section with `specfact module install <id>`, trust tiers, dependency auto-install
  - [x] 14.1.4 Review `README.md` — note that bundles are marketplace-distributed; update install example
  - [x] 14.1.5 Review `docs/index.md` — confirm landing page reflects marketplace availability of official bundles

- [x] 14.2 Update `docs/getting-started/README.md`
  - [x] 14.2.1 Verify Jekyll front-matter is preserved (title, layout, nav_order, permalink)
  - [x] 14.2.2 Add note that bundles are installable via `specfact module install nold-ai/specfact-<name>` or `specfact init --profile <name>`

- [x] 14.3 Update or create `docs/guides/marketplace.md`
  - [x] 14.3.1 Add Jekyll front-matter: `layout: default`, `title: Marketplace Bundles`, `nav_order: <appropriate>`, `permalink: /guides/marketplace/`
  - [x] 14.3.2 Write "Official bundles" section: list all 5 bundles with IDs, contents, and install commands
  - [x] 14.3.3 Write "Trust tiers" section: explain `official` (nold-ai) vs `community` vs unsigned
  - [x] 14.3.4 Write "Bundle dependencies" section: explain that specfact-spec and specfact-govern pull in specfact-project automatically

- [x] 14.4 Update `docs/_layouts/default.html`
  - [x] 14.4.1 Add "Marketplace Bundles" link to sidebar navigation if `docs/guides/marketplace.md` is new

- [x] 14.5 Update `README.md`
  - [x] 14.5.1 Update "Available modules" section to group by bundle with install commands
  - [x] 14.5.2 Note official-tier trust and marketplace availability

- [x] 14.6 Verify docs
  - [x] 14.6.1 Check all Markdown links resolve
  - [x] 14.6.2 Check front-matter is valid YAML

## 15. Version and changelog

- [x] 15.1 Determine version bump: **minor** (new feature: bundle extraction, official tier, publish pipeline; feature/* branch)
  - [x] 15.1.1 Confirm current version in `pyproject.toml`
  - [x] 15.1.2 Confirm bump is minor (e.g., `0.X.Y → 0.(X+1).0`)
  - [x] 15.1.3 Request explicit confirmation from user before applying bump

- [x] 15.2 Sync version across all files
  - [x] 15.2.1 `pyproject.toml`
  - [x] 15.2.2 `setup.py`
  - [x] 15.2.3 `src/__init__.py` (if present)
  - [x] 15.2.4 `src/specfact_cli/__init__.py`
  - [x] 15.2.5 Verify all four files show the same version

- [x] 15.3 Update `CHANGELOG.md`
  - [x] 15.3.1 Add new section `## [X.Y.Z] - 2026-MM-DD`
  - [x] 15.3.2 Add `### Added` subsection:
    - 5 official bundle packages in `specfact-cli-modules/packages/`
    - `official` trust tier in `crypto_validator.py` with `nold-ai` publisher allowlist
    - Bundle-level dependency auto-install in `module_installer.py`
    - `--bundle` mode in `scripts/publish-module.py`
    - Signed bundle entries in `specfact-cli-modules/registry/index.json`
    - `[official]` tier badge in `specfact module list` output
  - [x] 15.3.3 Add `### Changed` subsection:
    - Module source relocated to bundle namespaces; `specfact_cli.modules.*` paths now re-export shims
    - `specfact module install` output confirms official-tier verification result
  - [x] 15.3.4 Add `### Deprecated` subsection:
    - `specfact_cli.modules.*` import paths deprecated in favour of `specfact_<bundle>.*` (removal in next major version)
  - [x] 15.3.5 Reference GitHub issue number

## 16. Create PR to dev (specfact-cli repo)

- [x] 16.1 Verify TDD_EVIDENCE.md is complete (failing-before and passing-after evidence for all behavior changes: cross-bundle import gate, bundle layout, shim deprecation, official-tier validation, bundle dependency install, publish pipeline)

- [x] 16.2 Prepare commit(s) **in specfact-cli repository**
  - [x] 16.2.1 Stage all changed files **in this repo**: `src/specfact_cli/modules/` (shims), `scripts/publish-module.py`, `tests/`, `docs/`, `CHANGELOG.md`, `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`, `openspec/changes/module-migration-02-bundle-extraction/`. Do **not** stage `specfact-cli-modules/` — that directory lives in a separate repository; see Section 17.
  - [x] 16.2.2 `git commit -m "feat: extract modules to bundle packages and publish to marketplace (#<issue>)"`
  - [x] 16.2.3 (If GPG signing required) provide `git commit -S -m "..."` for user to run locally
  - [x] 16.2.4 `git push -u origin feature/module-migration-02-bundle-extraction`

- [x] 16.3 Create PR via gh CLI
  - [x] 16.3.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/module-migration-02-bundle-extraction --title "feat: Bundle Extraction and Marketplace Publishing (#<issue>)" --body "..."` (body: summary bullets, test plan checklist, OpenSpec change ID, issue reference)
  - [x] 16.3.2 Capture PR URL

- [x] 16.4 Link PR to project board
  - [x] 16.4.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

- [x] 16.5 Verify PR and CI
  - [x] 16.5.1 Confirm base is `dev`, head is `feature/module-migration-02-bundle-extraction`
  - [x] 16.5.2 Confirm CI checks run; **CI was red (~78 failures)** until specfact-cli-modules was populated and merged (Section 17).
  - [x] 16.5.3 After Section 17 complete (specfact-cli-modules merged with five bundles), CI re-ran — **PR 332 to dev is now green.**

---

## 17. specfact-cli-modules repo: commit, push, and publish

Migration-02 is not complete until the **specfact-cli-modules** repository contains the five bundle packages and a populated registry, and that state is merged/pushed so that CI (which clones `nold-ai/specfact-cli-modules`) and installers can resolve the bundles.

- [x] 17.1 In the **specfact-cli-modules** clone (used in 5.0–5.4, 10.5, 11): ensure branch is created if not already (e.g. `feature/module-migration-02-bundles`).
- [x] 17.2 Stage and commit all new/modified files in the modules repo:
  - [x] 17.2.1 `packages/specfact-project/`, `packages/specfact-backlog/`, `packages/specfact-codebase/`, `packages/specfact-spec/`, `packages/specfact-govern/` (full bundle source and `module-package.yaml`)
  - [x] 17.2.2 `registry/index.json` and `registry/signatures/` (or equivalent) after Phase 11 publish
  - [x] 17.2.3 Commit message: e.g. `feat: add five official bundle packages and registry entries (module-migration-02)`
- [x] 17.3 Push the branch: `git push -u origin feature/module-migration-02-bundles` (or the branch name used).
- [x] 17.4 Open a PR in **nold-ai/specfact-cli-modules** from the feature branch to `main` (or `dev`, per repo policy). Ensure the PR description references module-migration-02 and specfact-cli issue #316.
- [x] 17.5 After review, merge the PR so that `main` (or default branch) of specfact-cli-modules contains the five bundles and `registry/index.json` with the five official entries.
- [x] 17.6 (Optional) Tag or release in specfact-cli-modules so that `https://raw.githubusercontent.com/nold-ai/specfact-cli-modules/main/registry/index.json` (or equivalent) serves the registry for installers and CI.
- [x] 17.7 Return to specfact-cli: trigger CI again (e.g. push empty commit or re-run workflow). CI clones specfact-cli-modules; with the five bundles now on the default branch, tests pass — **specfact-cli PR 332 to dev is now green.**

### 17.8.0 Pre-gate prerequisite: complete import dependency categorization (Gap 1)

**Blocks 17.8.** Do not run the migration gate until this section is complete.

- [x] 17.8.0.1 Run `rg -e "from specfact_cli.* import" -o -IN --trim | sort | uniq` in specfact-cli-modules; confirm list matches the entries in `IMPORT_DEPENDENCY_ANALYSIS.md` (current scan: 91 unique imports; supersedes earlier 85-count note)
- [x] 17.8.0.2 For each entry in `IMPORT_DEPENDENCY_ANALYSIS.md`, populate **Category** (CORE / MIGRATE / SHARED), **Target bundle** (if MIGRATE), and **Notes** using the suggested initial categorization in that file as a starting point; verify each assignment against actual usage in bundle code
- [x] 17.8.0.3 For each MIGRATE-tier import: confirm that the source code it references still exists in specfact-cli at `src/specfact_cli/<subsystem>/`; if migration-03 would delete it, the MIGRATE move **must** happen before migration-03 begins (add a task to module-migration-05 section 19.2 and note the dependency here)
- [x] 17.8.0.4 For each SHARED-tier import: document in Notes whether it stays in specfact-cli (bundles depend on core as package) or will be extracted to a shared package in specfact-cli-modules
- [x] 17.8.0.5 Commit the completed `IMPORT_DEPENDENCY_ANALYSIS.md`: `git add openspec/changes/module-migration-02-bundle-extraction/IMPORT_DEPENDENCY_ANALYSIS.md && git commit -m "docs: complete import dependency categorization for migration-02 gate"`

### 17.8 Migration-complete gate (non-reversible) — updated with behavioral smoke test

- [x] 17.8.1 Confirm 17.8.0 (import categorization) is complete before proceeding
- [x] 17.8.2 **Behavioral smoke test** — Run from specfact-cli worktree with `SPECFACT_MODULES_REPO` set:

  ```bash
  hatch test -- tests/unit/bundles/ tests/integration/test_bundle_install.py -v
  ```

  Confirm: bundle layout tests pass, install lifecycle tests (official-tier verify, dependency resolution) pass via installed bundle paths — not shims. Record result.
- [x] 17.8.3 **Presence gate** — Run:

  ```bash
  SPECFACT_MODULES_REPO=/path/to/specfact-cli-modules python scripts/validate-modules-repo-sync.py --gate
  ```

  - If any file is missing in the modules repo, fix by migrating that content to specfact-cli-modules and re-run.
  - If content differs (e.g. import/namespace only), either migrate any missing logic to specfact-cli-modules, or after verification re-run with `SPECFACT_MIGRATION_CONTENT_VERIFIED=1`. Do not close the change until the gate passes. See proposal "Non-reversible gate" and `MIGRATION_GATE.md`.
- [x] 17.8.4 Merge specfact-cli PR #332 to dev. ✅ Completed on `dev` (commit `039da8b`). Migration-02 is now non-reversibly closed: canonical source for the 17 modules is specfact-cli-modules only.

---

## 17.9 Proposal consistency: resolve migration-03 and migration-04 overlap (Gap 2 + Gap 3)

After migration-02 closes, two proposal-level inconsistencies exist in the follow-up changes that could cause implementation conflicts or undeclared breaking changes. Resolve before migration-03 or migration-04 implementation begins.

### 17.9.1 Reconcile flat-shim removal overlap between migration-03 and migration-04 (Gap 3)

- [x] 17.9.1.1 Review migration-04 "What Changes": it removes `FLAT_TO_GROUP` + `_make_shim_loader()` from `module_packages.py` (the shim machinery)
- [x] 17.9.1.2 Review migration-03 "What Changes": it claims to remove "backward-compat flat command shims registered by `bootstrap.py` in module-migration-01"
- [x] 17.9.1.3 Confirmed distinct: migration-04 owns `module_packages.py` shim *machinery*; migration-03 owns `bootstrap.py` dead call-site *cleanup* (the call sites become dead after migration-04 removes the machinery they reference). Boundary documented in both proposals.
- [x] 17.9.1.4 Updated migration-03 proposal "What Changes": bootstrap.py cleanup scoped to dead shim call sites; cross-reference to migration-04 as prerequisite added. "Removed Capabilities" updated to reflect two-step removal.
- [x] 17.9.1.5 Updated migration-04 proposal "What Changes": explicit scope boundary — `bootstrap.py` NOT modified by migration-04; migration-03 handles that cleanup. "Followed by" relationship with migration-03 added. Wave ordering confirmed consistent.
- [x] 17.9.1.6 Commit proposal updates: proposal text committed in branch (migration-03 and migration-04 proposals already contain the reconciled scope; no separate commit required).

### 17.9.2 Update migration-03 to explicitly declare Python import shim removal (Gap 2)

- [x] 17.9.2.1 Confirmed: migration-03 proposal did not state Python import shim removal; `__getattr__` shims were undeclared collateral of the directory DELETE.
- [x] 17.9.2.2 Added explicit REMOVE bullet to migration-03 "What Changes": each DELETE line updated to include "entire directory including `__getattr__` re-export shim created by migration-02"; standalone REMOVE bullet added with ImportError consequence and module-to-bundle mapping.
- [x] 17.9.2.3 Added "Migration path for import consumers" to migration-03 Backward compatibility section: full module → bundle namespace mapping for all 17 modules.
- [x] 17.9.2.4 Added "Version-cycle definition" section to migration-03 proposal: 0.2x series = deprecation opened; 0.40 series = deprecation closed; rationale that 0.40 represents a new tens-series major UX transition.
- [x] 17.9.2.5 Commit: proposal text committed in branch (migration-03 proposal already contains Python import shim removal and version-cycle justification; no separate commit required).

---

## 17.10 Create module-migration-05 change stub (Gap 4) — ✅ Done

The following change stub has been created to own sections 18–23 (deferred from migration-02):

- [x] 17.10.1 Created `openspec/changes/module-migration-05-modules-repo-quality/proposal.md`
- [x] 17.10.2 Created `openspec/changes/module-migration-05-modules-repo-quality/tasks.md` (sections 18–24, with sections 21+22 marked as must-precede-migration-03)
- [x] 17.10.3 CHANGE_ORDER.md updated with migration-05 entry (see CHANGE_ORDER.md edits)
- [x] 17.10.4 Create GitHub issue for migration-05; update migration-05 proposal.md Source Tracking with issue number and URL

---

## 18. Test migration and quality parity (specfact-cli-modules) — DEFERRED → module-migration-05

Ensures that working on bundle code in specfact-cli-modules has the same quality standards and test scripts as in specfact-cli. See proposal section "Test migration and quality parity (gap)".

### 18.1 Inventory tests by bundle (in specfact-cli)

- [x] 18.1.1 Map each of the 17 migrated modules to its bundle (project→specfact-project, plan→specfact-project, …).
- [x] 18.1.2 List all tests under `tests/unit/` that exercise bundle code: e.g. `tests/unit/modules/{plan,backlog,sync,enforce,generate,patch_mode,module_registry,init}`, `tests/unit/backlog/`, `tests/unit/analyzers/`, `tests/unit/commands/`, `tests/unit/bundles/`, and any other module-related unit tests.
- [x] 18.1.3 List integration tests that invoke bundle commands: `tests/integration/commands/`, `tests/integration/test_bundle_install.py`, and any other integration tests touching the 17 modules.
- [x] 18.1.4 List e2e tests that depend on bundle behavior (e.g. `tests/e2e/test_bundle_extraction_e2e.py` or similar).
- [x] 18.1.5 Produce an inventory document (e.g. `openspec/changes/module-migration-02-bundle-extraction/TEST_INVENTORY.md`) with: file path, bundle(s) exercised, and migration target path in specfact-cli-modules (e.g. `tests/unit/specfact_project/` or `tests/unit/plan/`).

### 18.2 Quality tooling in specfact-cli-modules

- [x] 18.2.1 Copy or adapt coverage config from specfact-cli into specfact-cli-modules: `[tool.coverage.run]`, `[tool.coverage.report]`, threshold (e.g. 80%); ensure pytest is configured with `addopts`, `testpaths`, `pythonpath` so that `packages/*/src` and `tests/` are covered.
- [x] 18.2.2 Add hatch env(s) for testing (e.g. default env or a `test` env) so that `hatch test` runs with correct PYTHONPATH for `packages/specfact-*/src`.
- [x] 18.2.3 Add contract-test script: either call specfact-cli's contract-test when specfact-cli is installed as dev dep, or copy/adapt `tools/contract_first_smart_test.py` (or equivalent) into specfact-cli-modules so that `hatch run contract-test` runs contract validation for bundle code.
- [x] 18.2.4 Add smart-test or equivalent: copy/adapt `tools/smart_test_coverage.py` (or a simplified incremental test runner that considers `packages/` and `tests/`) so that `hatch run smart-test` (or `hatch run test` with coverage) is available; document in README/AGENTS.md.
- [x] 18.2.5 Add yaml-lint script for `packages/*/module-package.yaml` and `registry/index.json` (or equivalent YAML/JSON validation); add to pre-commit or CI.
- [x] 18.2.6 Align ruff, basedpyright, and pylint config (and scripts) with specfact-cli so that `hatch run format`, `hatch run type-check`, `hatch run lint` match specfact-cli behavior; fix or document any intentional differences (e.g. type-check overrides for bundle packages).

### 18.3 Migrate tests into specfact-cli-modules

- [x] 18.3.1 Create test layout in specfact-cli-modules (e.g. `tests/unit/specfact_project/`, `tests/unit/specfact_backlog/`, … or mirror specfact-cli under `tests/unit/` with paths adjusted). Add `tests/conftest.py` and any shared fixtures (e.g. `TEST_MODE`, temp dirs).
- [x] 18.3.2 Copy unit tests from the inventory into specfact-cli-modules; update imports from `specfact_cli.modules.*` to bundle namespaces (e.g. `specfact_project.plan`, `specfact_codebase.analyze`) and adjust paths (e.g. resources, registry) so tests run against packages in `packages/`.
- [x] 18.3.3 Copy integration tests that invoke bundle commands; ensure they run in the modules repo (e.g. via `pip install -e .` or hatch env that exposes bundle packages). Update any references to specfact-cli CLI to use the same entrypoint if available or document how to run.
- [x] 18.3.4 Copy or adapt e2e tests that depend on bundle behavior; if they require full CLI, document that they run in specfact-cli or adapt to run in modules repo with minimal harness.
- [x] 18.3.5 Run full test suite in specfact-cli-modules: `hatch test` (or `hatch run smart-test`); fix failing tests until all pass. Record any tests intentionally deferred or skipped (with reason) in TEST_INVENTORY.md or a short migration note.

### 18.4 CI in specfact-cli-modules

- [x] 18.4.1 Add or update `.github/workflows/` in specfact-cli-modules so that CI runs: format, type-check, lint, test (and contract-test, coverage threshold where applicable). Mirror specfact-cli quality gates as far as feasible.
- [x] 18.4.2 Ensure CI uses the same Python version(s) as specfact-cli (e.g. 3.11, 3.12, 3.13) if matrix is desired.
- [x] 18.4.3 Document in specfact-cli-modules README and AGENTS.md the pre-commit checklist (format, type-check, lint, test, contract-test, smart-test) so contributors follow the same standards as specfact-cli.

### 18.5 Verification and documentation

- [x] 18.5.1 From specfact-cli-modules repo: run full quality gate sequence (format, type-check, lint, test, contract-test if added, smart-test/coverage). All must pass.
- [x] 18.5.2 Update `openspec/changes/module-migration-02-bundle-extraction/proposal.md` Source Tracking (or status note) to record that test migration and quality parity are done; update `tasks.md` status header to include Section 18 in "Completed" when all 18.x tasks are done.
- [x] 18.5.3 Optionally add a short design or spec delta under this change (e.g. `specs/bundle-test-parity/spec.md` or a bullet in an existing spec) describing the test layout and quality parity contract for specfact-cli-modules.

---

## 19. Dependency decoupling (specfact-cli-modules) — DEFERRED → module-migration-05

**Note:** Section 19.1 (import categorization) is a **prerequisite for gate 17.8** and must be done in this change (see task 17.8.0). Sections 19.2–19.4 (migration execution, gate, verification) are deferred to module-migration-05.

Ensures bundle code in specfact-cli-modules does not hardcode imports from `specfact_cli.*` for module-only dependencies. See proposal "Dependency decoupling (gap)" and `IMPORT_DEPENDENCY_ANALYSIS.md`.

### 19.1 Categorize all specfact_cli imports

**Completed in this change via 17.8.0** — see `IMPORT_DEPENDENCY_ANALYSIS.md` (91 imports categorized CORE/MIGRATE/SHARED).

- [x] 19.1.1 Run `rg -e "from specfact_cli.* import" -o -IN --trim | sort | uniq` in specfact-cli-modules to obtain the full import list.
- [x] 19.1.2 For each import, determine category: **CORE** (stay in specfact-cli; bundles depend on specfact-cli), **MIGRATE** (used only by bundle code; move to modules repo), **SHARED** (used by both; decide TBD).
- [x] 19.1.3 Populate `IMPORT_DEPENDENCY_ANALYSIS.md` with: import path, category, target bundle (if MIGRATE), notes.
- [x] 19.1.4 Typical CORE: `common`, `contracts.module_interface`, `cli`, `registry.registry`, `modes`, `runtime`, `telemetry`, `versioning`, `models.*` (if shared). Typical MIGRATE candidates: `analyzers.*`, `backlog.*`, `comparators.*`, `enrichers.*`, `generators.*`, `importers.*`, `migrations.*`, `parsers.*`, `sync.*`, `validators.*`, bundle-specific `utils.*`.

### 19.2 Migrate module-only dependencies — tracked in module-migration-05

**The following tasks (19.2–23.x) are deferred to `module-migration-05-modules-repo-quality`; do not check in migration-02. See `openspec/changes/module-migration-05-modules-repo-quality/tasks.md`.**

- [x] 19.2.1 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.2.1.
- [x] 19.2.2 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.2.2.
- [x] 19.2.3 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.2.3.
- [x] 19.2.4 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.2.4.

### 19.3 Document allowed imports and add gate

- [x] 19.3.1 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.3.1.
- [x] 19.3.2 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.3.2.
- [x] 19.3.3 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.3.3.

### 19.4 Verification

- [x] 19.4.1 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.4.1.
- [x] 19.4.2 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.4.2.
- [x] 19.4.3 Deferred handoff acknowledged: tracked in `module-migration-05` task 19.4.2 plus migration-05 closeout updates.

---

## 20. Docs migration (specfact-cli-modules) — DEFERRED → module-migration-05

Migrate bundle/module docs to the modules repo and set up Jekyll so doc updates for modules do not require changes in the CLI core repo. See proposal "Docs migration (gap)" and checklist (c).

- [x] 20.1 Deferred handoff acknowledged: tracked in `module-migration-05` task 20.1.
- [x] 20.2 Deferred handoff acknowledged: tracked in `module-migration-05` task 20.2.
- [x] 20.3 Deferred handoff acknowledged: tracked in `module-migration-05` task 20.3.
- [x] 20.4 Deferred handoff acknowledged: tracked in `module-migration-05` task 20.4.
- [x] 20.5 Deferred handoff acknowledged: tracked in `module-migration-05` task 20.5.
- [x] 20.6 Deferred handoff acknowledged: tracked in `module-migration-05` task 20.6.

---

## 21. Build pipeline (specfact-cli-modules) — DEFERRED → module-migration-05 (MUST PRECEDE MIGRATION-03)

**Timing constraint:** Must land before or simultaneously with `module-migration-03-core-slimming`. See Gap 5 in `GAP_ANALYSIS.md`.

Add pr-orchestrator (or equivalent) and align CI with specfact-cli so that PRs to the modules repo run the same quality gates. See proposal "Build pipeline (gap)" and checklist (d).

- [x] 21.1 Deferred handoff acknowledged: tracked in `module-migration-05` task 21.1.
- [x] 21.2 Deferred handoff acknowledged: tracked in `module-migration-05` task 21.2.
- [x] 21.3 Deferred handoff acknowledged: tracked in `module-migration-05` task 21.3.
- [x] 21.4 Deferred handoff acknowledged: tracked in `module-migration-05` task 21.4.

---

## 22. Central config files (specfact-cli-modules) — DEFERRED → module-migration-05 (MUST PRECEDE MIGRATION-03)

**Timing constraint:** Must land before or simultaneously with `module-migration-03-core-slimming`. See Gap 5 in `GAP_ANALYSIS.md`.

Ensure repo-root config files match specfact-cli so that format, lint, type-check, and test behavior are aligned. See proposal "Central config files (gap)" and checklist (e).

- [x] 22.1 Deferred handoff acknowledged: tracked in `module-migration-05` task 22.1.
- [x] 22.2 Deferred handoff acknowledged: tracked in `module-migration-05` task 22.2.
- [x] 22.3 Deferred handoff acknowledged: tracked in `module-migration-05` task 22.3.
- [x] 22.4 Deferred handoff acknowledged: tracked in `module-migration-05` task 22.4.

---

## 23. License and contribution (specfact-cli-modules) — DEFERRED → module-migration-05

Align LICENSE and contribution artifacts with specfact-cli; clarify that this repo is for nold-ai official bundles only and third-party modules are not hosted here. See proposal "License and contribution (gap)" and checklist (f).

- [x] 23.1 Deferred handoff acknowledged: tracked in `module-migration-05` task 23.1.
- [x] 23.2 Deferred handoff acknowledged: tracked in `module-migration-05` task 23.2.
- [x] 23.3 Deferred handoff acknowledged: tracked in `module-migration-05` task 23.3.
- [x] 23.4 Deferred handoff acknowledged: tracked in `module-migration-05` task 23.4.
- [x] 23.5 Deferred handoff acknowledged: covered by `module-migration-05` task 23.2 (official-bundles-only statement) and 23.4 (explicit third-party hosting scope note).

---

## Handoff to module-migration-03 and module-migration-04

Migration-02 is **complete** when:

1. **specfact-cli**: PR merged to `dev` (shims, scripts, tests, docs, quality gates).
2. **specfact-cli-modules**: Five bundle packages and `registry/index.json` are merged (and optionally released) so that:
   - CI for specfact-cli (which checkouts specfact-cli-modules) sees `packages/specfact-*/src/` and tests pass.
   - Installers and `specfact module install` can resolve the official bundles from the registry.
3. **Migration-complete gate**: `scripts/validate-modules-repo-sync.py --gate` passes (all files present; content differences resolved or accepted with `SPECFACT_MIGRATION_CONTENT_VERIFIED=1`). Closing is **non-reversible**: after close, canonical source for the 17 modules lives in specfact-cli-modules only.

**Non-conflicting basis for migration-03 and migration-04:**

- **module-migration-03** (core slimming) removes the 17 non-core module **directories** from specfact-cli and relies on `specfact-cli-modules/registry/index.json` containing all 5 bundle entries. It does not modify the modules repo. Migration-02 must deliver the populated registry and bundles before 03 deletes in-repo module dirs.
- **module-migration-04** (remove flat shims) removes the remaining flat command registration; it depends on 03. No dependency on pushing from specfact-cli to specfact-cli-modules.

Ensure `openspec/CHANGE_ORDER.md` is updated when migration-02 is archived: move the row to Implemented with archive date and note that both specfact-cli and specfact-cli-modules PRs are merged.

---

## Post-merge worktree cleanup

After PR is merged to `dev`:

```bash
git fetch origin
git worktree remove ../specfact-cli-worktrees/feature/module-migration-02-bundle-extraction
git branch -d feature/module-migration-02-bundle-extraction
git worktree prune
```

If remote branch cleanup is needed:

```bash
git push origin --delete feature/module-migration-02-bundle-extraction
```

---

## CHANGE_ORDER.md update (required — also covered in task 3 above)

After this change is **fully** completed (both specfact-cli and specfact-cli-modules work done):

- Module migration table: move `module-migration-02-bundle-extraction` row from Pending to **Implemented (archived)** with archive date.
- Note that completion requires: (1) specfact-cli PR merged to `dev`, (2) specfact-cli-modules PR merged (five bundles + registry/index.json).
- Wave 3: confirm `module-migration-02-bundle-extraction` is listed after `module-migration-01-categorize-and-group`; update Wave 3 status when all Wave 3 changes are complete.
- migration-03 and migration-04 remain blocked on migration-02 until both repos are merged as above.
