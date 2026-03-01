# Implementation Tasks: module-migration-02-bundle-extraction

## Status and gap (as of review)

**Completed in this worktree (specfact-cli repo only):**

- Phases 0–4, 6–9: Shared-code audit, re-export shims, official-tier trust model, bundle dependency auto-install, publish-module.py bundle mode — all implemented and tested in **specfact-cli**.
- Phase 5.1: Bundle layout tests exist in `tests/unit/bundles/test_bundle_layout.py`; they resolve `specfact-cli-modules` via `SPECFACT_MODULES_REPO` or sibling path and **skip** when the modules repo has no `packages/`.
- Phase 10.1–10.4: Re-signing of **in-repo** module manifests (shims) in `src/specfact_cli/modules/*/module-package.yaml` — done.
- Section 16: PR created (e.g. #332 feature/module-migration-02-bundle-extraction → dev).
- Section 17.1–17.7: **specfact-cli-modules** published and merged (five bundles + registry). CI for specfact-cli now passes — **PR 332 to dev is green.**

**Outstanding before closing:**

- **17.8 Migration-complete gate**: Run `scripts/validate-modules-repo-sync.py --gate`; after confirming content diffs are import/namespace only, pass with `SPECFACT_MIGRATION_CONTENT_VERIFIED=1`. Then merge specfact-cli PR to dev and treat migration-02 as complete (non-reversible).

All other tasks (5.0–5.5, 10.5–10.6, 11.1–11.8) are marked done; 17.8 remains until the gate is passed.

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

- [x] 17.8 **Migration-complete gate (non-reversible)** — Before closing this change, run:
  ```bash
  SPECFACT_MODULES_REPO=/path/to/specfact-cli-modules python scripts/validate-modules-repo-sync.py --gate
  ```
  - If any file is missing in the modules repo, fix by migrating that content to specfact-cli-modules and re-run.
  - If content differs (e.g. import/namespace only), either migrate any missing logic to specfact-cli-modules, or after verification re-run with `SPECFACT_MIGRATION_CONTENT_VERIFIED=1`. Do not close the change until the gate passes. See proposal "Non-reversible gate" and "Migration-complete gate".

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
