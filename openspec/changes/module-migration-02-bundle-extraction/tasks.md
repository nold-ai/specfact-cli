# Implementation Tasks: module-migration-02-bundle-extraction

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

### 5.2 Create bundle package directories

- [x] 5.2.1 Create `specfact-cli-modules/packages/specfact-project/src/specfact_project/__init__.py`
- [x] 5.2.2 Create `specfact-cli-modules/packages/specfact-backlog/src/specfact_backlog/__init__.py`
- [x] 5.2.3 Create `specfact-cli-modules/packages/specfact-codebase/src/specfact_codebase/__init__.py`
- [x] 5.2.4 Create `specfact-cli-modules/packages/specfact-spec/src/specfact_spec/__init__.py`
- [x] 5.2.5 Create `specfact-cli-modules/packages/specfact-govern/src/specfact_govern/__init__.py`

### 5.3 Create top-level bundle module-package.yaml manifests

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

### 5.4 Move module source into bundle namespaces (one bundle per commit)

For each module move: (a) copy source to bundle, (b) update intra-bundle imports, (c) place re-export shim in core, (d) run tests.

**specfact-project bundle:**

- [x] 5.4.1 Move `src/specfact_cli/modules/project/src/project/` → `specfact-cli-modules/packages/specfact-project/src/specfact_project/project/`; update imports `specfact_cli.modules.project.*` → `specfact_project.project.*`
- [x] 5.4.2 Move `src/specfact_cli/modules/plan/src/plan/` → `specfact_project/plan/`; update imports
- [x] 5.4.3 Move `src/specfact_cli/modules/import_cmd/src/import_cmd/` → `specfact_project/import_cmd/`; update imports
- [x] 5.4.4 Move `src/specfact_cli/modules/sync/src/sync/` → `specfact_project/sync/`; update imports (plan → specfact_project.plan)
- [x] 5.4.5 Move `src/specfact_cli/modules/migrate/src/migrate/` → `specfact_project/migrate/`; update imports
- [x] 5.4.6 Place re-export shims for all 5 project modules in `src/specfact_cli/modules/*/src/*/`
- [x] 5.4.7 `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v` — verify project-related tests pass

**specfact-backlog bundle:**

- [x] 5.4.8 Move `src/specfact_cli/modules/backlog/src/backlog/` → `specfact_backlog/backlog/`; update imports
- [x] 5.4.9 Move `src/specfact_cli/modules/policy_engine/src/policy_engine/` → `specfact_backlog/policy_engine/`; update imports
- [x] 5.4.10 Place re-export shims for backlog and policy_engine
- [x] 5.4.11 `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v`

**specfact-codebase bundle:**

- [x] 5.4.12 Move `src/specfact_cli/modules/analyze/src/analyze/` → `specfact_codebase/analyze/`; update imports
- [x] 5.4.13 Move `src/specfact_cli/modules/drift/src/drift/` → `specfact_codebase/drift/`; update imports
- [x] 5.4.14 Move `src/specfact_cli/modules/validate/src/validate/` → `specfact_codebase/validate/`; update imports
- [x] 5.4.15 Move `src/specfact_cli/modules/repro/src/repro/` → `specfact_codebase/repro/`; update imports
- [x] 5.4.16 Place re-export shims for all 4 codebase modules
- [x] 5.4.17 `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v`

**specfact-spec bundle:**

- [x] 5.4.18 Move `src/specfact_cli/modules/contract/src/contract/` → `specfact_spec/contract/`; update imports
- [x] 5.4.19 Move `src/specfact_cli/modules/spec/src/spec/` → `specfact_spec/spec/`; update imports
- [x] 5.4.20 Move `src/specfact_cli/modules/sdd/src/sdd/` → `specfact_spec/sdd/`; update imports
- [x] 5.4.21 Move `src/specfact_cli/modules/generate/src/generate/` → `specfact_spec/generate/`; update imports (`plan` → `specfact_project.plan` via common interface)
- [x] 5.4.22 Place re-export shims for all 4 spec modules
- [x] 5.4.23 `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v`

**specfact-govern bundle:**

- [x] 5.4.24 Move `src/specfact_cli/modules/enforce/src/enforce/` → `specfact_govern/enforce/`; update imports (`plan` → `specfact_project.plan` via common interface)
- [x] 5.4.25 Move `src/specfact_cli/modules/patch_mode/src/patch_mode/` → `specfact_govern/patch_mode/`; update imports
- [x] 5.4.26 Place re-export shims for enforce and patch_mode
- [x] 5.4.27 `hatch test -- tests/unit/bundles/test_bundle_layout.py tests/unit/ -v`

### 5.5 Record passing-test evidence (Phase 1)

- [x] 5.5.1 `hatch test -- tests/unit/bundles/ -v` — full bundle layout test suite
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

After all five bundles are extracted and shims are in place, the `module-package.yaml` files in `src/specfact_cli/modules/*/` have changed content (shims replaced source). All signatures must be regenerated.

- [x] 10.1 Run verification (expect failures — manifests changed): `hatch run ./scripts/verify-modules-signature.py --require-signature`
- [x] 10.2 For each affected module: bump patch version in `module-package.yaml`
- [x] 10.3 Re-sign all 21 module-package.yaml files: `hatch run python scripts/sign-modules.py --key-file <private-key.pem> src/specfact_cli/modules/*/module-package.yaml`
- [x] 10.4 Re-run verification: `hatch run ./scripts/verify-modules-signature.py --require-signature` — confirm fully green
- [x] 10.5 Also sign all 5 bundle `module-package.yaml` files in `specfact-cli-modules/packages/*/module-package.yaml`
- [x] 10.6 Confirm all signatures green: `hatch run ./scripts/verify-modules-signature.py --require-signature`

## 11. Phase 7 — Publish bundles to registry

- [x] 11.1 Verify `specfact-cli-modules/registry/index.json` is at `modules: []` (or contains only prior entries — no overlap)
- [x] 11.2 Publish specfact-project: `python scripts/publish-module.py --bundle specfact-project --key-file <private-key.pem>`
- [x] 11.3 Publish specfact-backlog: `python scripts/publish-module.py --bundle specfact-backlog --key-file <private-key.pem>`
- [x] 11.4 Publish specfact-codebase: `python scripts/publish-module.py --bundle specfact-codebase --key-file <private-key.pem>`
- [x] 11.5 Publish specfact-spec: `python scripts/publish-module.py --bundle specfact-spec --key-file <private-key.pem>`
- [x] 11.6 Publish specfact-govern: `python scripts/publish-module.py --bundle specfact-govern --key-file <private-key.pem>`
- [x] 11.7 Inspect `index.json`: confirm 5 entries, each with `tier: official`, `publisher: nold-ai`, valid `checksum_sha256`, and correct `bundle_dependencies`
- [x] 11.8 Re-run offline verification against all 5 entries: `hatch run ./scripts/verify-modules-signature.py --require-signature`

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

## 16. Create PR to dev

- [x] 16.1 Verify TDD_EVIDENCE.md is complete (failing-before and passing-after evidence for all behavior changes: cross-bundle import gate, bundle layout, shim deprecation, official-tier validation, bundle dependency install, publish pipeline)

- [x] 16.2 Prepare commit(s)
  - [x] 16.2.1 Stage all changed files (specfact-cli-modules/packages/, specfact-cli-modules/registry/, src/specfact_cli/modules/ shims, scripts/publish-module.py, tests/, docs/, CHANGELOG.md, pyproject.toml, setup.py, src/specfact_cli/**init**.py, openspec/changes/module-migration-02-bundle-extraction/)
  - [x] 16.2.2 `git commit -m "feat: extract modules to bundle packages and publish to marketplace (#<issue>)"`
  - [x] 16.2.3 (If GPG signing required) provide `git commit -S -m "..."` for user to run locally
  - [x] 16.2.4 `git push -u origin feature/module-migration-02-bundle-extraction`

- [x] 16.3 Create PR via gh CLI
  - [x] 16.3.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/module-migration-02-bundle-extraction --title "feat: Bundle Extraction and Marketplace Publishing (#<issue>)" --body "..."` (body: summary bullets, test plan checklist, OpenSpec change ID, issue reference)
  - [x] 16.3.2 Capture PR URL

- [x] 16.4 Link PR to project board
  - [x] 16.4.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

- [x] 16.5 Verify PR
  - [x] 16.5.1 Confirm base is `dev`, head is `feature/module-migration-02-bundle-extraction`
  - [x] 16.5.2 Confirm CI checks are running (tests.yml, specfact.yml)

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

After this change is created, `openspec/CHANGE_ORDER.md` must reflect:

- Module migration table: `module-migration-02-bundle-extraction` row with GitHub issue link and `Blocked by: module-migration-01`
- Wave 3: confirm `module-migration-02-bundle-extraction` is listed after `module-migration-01-categorize-and-group`
- After merge and archive: move row to Implemented section with archive date; update Wave 3 status if all Wave 3 changes are complete
