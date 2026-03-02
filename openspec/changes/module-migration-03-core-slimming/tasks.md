# Implementation Tasks: module-migration-03-core-slimming

## TDD / SDD Order (Enforced)

Per `openspec/config.yaml`, the following order is mandatory and non-negotiable for every behavior-changing task:

1. **Spec deltas** — already created in `specs/` (core-lean-package, profile-presets, module-removal-gate)
2. **Tests from spec scenarios** — translate each Given/When/Then scenario into test cases; run tests and expect failure (no implementation yet)
3. **Capture failing-test evidence** — record in `openspec/changes/module-migration-03-core-slimming/TDD_EVIDENCE.md`
4. **Code implementation** — implement until tests pass and behavior satisfies spec
5. **Capture passing-test evidence** — update `TDD_EVIDENCE.md` with passing run results
6. **Quality gates** — format, type-check, lint, contract-test, smart-test
7. **Documentation research and review**
8. **Version and changelog**
9. **PR creation**

Do NOT implement production code for any behavior-changing step until failing-test evidence is recorded in TDD_EVIDENCE.md.

---

## 1. Create git worktree branch from dev

- [ ] 1.1 Fetch latest origin and create worktree with feature branch
  - [ ] 1.1.1 `git fetch origin`
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/module-migration-03-core-slimming -b feature/module-migration-03-core-slimming origin/dev`
  - [ ] 1.1.3 `cd ../specfact-cli-worktrees/feature/module-migration-03-core-slimming`
  - [ ] 1.1.4 `git branch --show-current` — verify output is `feature/module-migration-03-core-slimming`
  - [ ] 1.1.5 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.6 `hatch env create`
  - [ ] 1.1.7 `hatch run smart-test-status` and `hatch run contract-test-status` — confirm baseline green

## 2. Create GitHub issue for change tracking

- [ ] 2.1 Create GitHub issue in nold-ai/specfact-cli
  - [ ] 2.1.1 `gh issue create --repo nold-ai/specfact-cli --title "[Change] Core Package Slimming and Mandatory Profile Selection" --label "enhancement,change-proposal" --body "$(cat <<'EOF'`

    ```text
    ## Why

    SpecFact CLI's 21 modules remain bundled in core after module-migration-02 extracted their source to marketplace bundle packages. This change completes the migration: it removes the 17 non-core module directories from pyproject.toml and src/specfact_cli/modules/, strips the backward-compat flat command shims (one major version elapsed), updates specfact init to enforce bundle selection before first use, and delivers the lean install experience where specfact --help shows only 4 core commands on a fresh install.

    ## What Changes

    - Delete src/specfact_cli/modules/ directories for all 17 non-core modules
    - Update pyproject.toml and setup.py to include only 4 core module paths
    - Update bootstrap.py: 4-core-only registration, remove flat command shims
    - Update specfact init: mandatory bundle selection gate (profile/install required in CI/CD)
    - Add scripts/verify-bundle-published.py pre-deletion gate
    - Profile presets fully activate: specfact init --profile solo-developer installs specfact-codebase without manual steps

    *OpenSpec Change Proposal: module-migration-03-core-slimming*
    ```

  - [ ] 2.1.2 Capture issue number and URL from output
  - [ ] 2.1.3 Update `openspec/changes/module-migration-03-core-slimming/proposal.md` Source Tracking section with issue number, URL, and status `open`

## 3. Update CHANGE_ORDER.md

- [ ] 3.1 Open `openspec/CHANGE_ORDER.md`
  - [ ] 3.1.1 Locate the "Module migration" table in the Pending section
  - [ ] 3.1.2 Update the row for `module-migration-03-core-package-slimming` to point to `module-migration-03-core-slimming`, add the GitHub issue number from step 2, and confirm blockers include `module-migration-02`, `module-migration-04`, and migration-05 sections 18-22
  - [ ] 3.1.3 Confirm Wave 4 description includes `module-migration-03-core-slimming` after `module-migration-02-bundle-extraction`
  - [ ] 3.1.4 Commit: `git add openspec/CHANGE_ORDER.md && git commit -m "docs: add module-migration-03-core-slimming to CHANGE_ORDER.md"`

## 4. Implement verify-bundle-published.py gate script (TDD)

### 4.1 Write tests for gate script (expect failure)

- [ ] 4.1.1 Create `tests/unit/scripts/test_verify_bundle_published.py`
- [ ] 4.1.2 Test: calling gate with a non-empty module list and a valid index.json containing all 5 bundle entries → exits 0, prints PASS for all rows
- [ ] 4.1.3 Test: calling gate when index.json is missing → exits 1 with "Registry index not found" message
- [ ] 4.1.4 Test: calling gate when a module's bundle has no entry in index.json → exits 1, names the missing bundle
- [ ] 4.1.5 Test: calling gate when bundle signature verification fails → exits 1, prints "SIGNATURE INVALID"
- [ ] 4.1.6 Test: calling gate with empty module list → contract violation, exits 1 with precondition message
- [ ] 4.1.7 Test: gate reads `bundle` field from `module-package.yaml` to resolve bundle name for each module
- [ ] 4.1.8 Test: `--skip-download-check` flag suppresses download URL resolution but still verifies signature
- [ ] 4.1.9 Test: `verify_bundle_published()` function has `@require` and `@beartype` decorators
- [ ] 4.1.10 Test: gate is idempotent (running twice produces same output and exit code)
- [ ] 4.1.11 Run: `hatch test -- tests/unit/scripts/test_verify_bundle_published.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 4.2 Implement scripts/verify-bundle-published.py

- [ ] 4.2.1 Create `scripts/verify-bundle-published.py`
- [ ] 4.2.2 Add CLI: `--modules` (comma-separated), `--registry-index` (default: `../specfact-cli-modules/registry/index.json`), `--skip-download-check`
- [ ] 4.2.3 Implement `load_module_bundle_mapping(module_names: list[str], modules_root: Path) -> dict[str, str]` — reads `bundle` field from each module's `module-package.yaml`
- [ ] 4.2.4 Implement `check_bundle_in_registry(bundle_id: str, index: dict) -> BundleCheckResult` — verifies presence, has required fields, valid signature
- [ ] 4.2.5 Implement `verify_bundle_download_url(download_url: str) -> bool` — HTTP HEAD request, skipped when `--skip-download-check`
- [ ] 4.2.6 Implement `verify_bundle_published(module_names: list[str], index_path: Path, skip_download_check: bool) -> list[BundleCheckResult]` — orchestrator with `@require` and `@beartype`
- [ ] 4.2.7 Add Rich table output: module | bundle | version | signature | download | status
- [ ] 4.2.8 Exit 0 if all PASS, exit 1 if any FAIL
- [ ] 4.2.9 `hatch test -- tests/unit/scripts/test_verify_bundle_published.py -v` — verify tests pass

### 4.3 Add hatch task alias

- [ ] 4.3.1 Add to `pyproject.toml` `[tool.hatch.envs.default.scripts]`:

  ```toml
  verify-removal-gate = [
      "python scripts/verify-bundle-published.py --modules project,plan,import_cmd,sync,migrate,backlog,policy_engine,analyze,drift,validate,repro,contract,spec,sdd,generate,enforce,patch_mode",
      "python scripts/verify-modules-signature.py --require-signature",
  ]
  ```

- [ ] 4.3.2 Verify: `hatch run verify-removal-gate --help` resolves

### 4.4 Record passing-test evidence (Phase: gate script)

- [ ] 4.4.1 `hatch test -- tests/unit/scripts/test_verify_bundle_published.py -v`
- [ ] 4.4.2 Record passing-test run in `TDD_EVIDENCE.md`

## 5. Write tests for bootstrap.py 4-core-only registration (TDD, expect failure)

- [ ] 5.1 Create `tests/unit/registry/test_core_only_bootstrap.py`
- [ ] 5.2 Test: `bootstrap_modules(cli_app)` registers exactly 4 command groups: `init`, `auth`, `module`, `upgrade`
- [ ] 5.3 Test: `bootstrap_modules(cli_app)` does NOT register any of the 17 extracted modules (project, plan, backlog, code, spec, govern, etc.)
- [ ] 5.4 Test: `bootstrap.py` source contains no import statements for the 17 deleted module packages
- [ ] 5.5 Test: flat shim commands (e.g., `specfact plan`) produce an actionable "not found" error after shim removal
- [ ] 5.6 Test: `bootstrap.py` calls `_mount_installed_category_groups(cli_app)` which mounts only installed bundles
- [ ] 5.7 Test: `_mount_installed_category_groups` mounts `backlog` group only when `specfact-backlog` is in `get_installed_bundles()` (mock)
- [ ] 5.8 Test: `_mount_installed_category_groups` does NOT mount `code` group when `specfact-codebase` is NOT in `get_installed_bundles()` (mock)
- [ ] 5.9 Run: `hatch test -- tests/unit/registry/test_core_only_bootstrap.py -v` (expect failures — record in TDD_EVIDENCE.md)

## 6. Write tests for specfact init mandatory bundle selection (TDD, expect failure)

- [ ] 6.1 Create `tests/unit/modules/init/test_mandatory_bundle_selection.py`
- [ ] 6.2 Test: `init_command(profile="solo-developer")` installs `specfact-codebase` and exits 0 (mock installer)
- [ ] 6.3 Test: `init_command(profile="backlog-team")` installs `specfact-project`, `specfact-backlog`, `specfact-codebase` (mock installer, verify call order)
- [ ] 6.4 Test: `init_command(profile="api-first-team")` installs `specfact-spec` + auto-installs `specfact-project` as dep
- [ ] 6.5 Test: `init_command(profile="enterprise-full-stack")` installs all 5 bundles (mock installer)
- [ ] 6.6 Test: `init_command(profile="invalid-name")` exits 1 with error listing valid profile names
- [ ] 6.7 Test: `init_command()` in CI/CD mode (mocked env) with no `profile` or `install` → exits 1, prints CI/CD error message
- [ ] 6.8 Test: `init_command()` in interactive mode with no bundles installed → enters selection loop (mock Rich prompt)
- [ ] 6.9 Test: interactive mode, user selects no bundles and then confirms 'y' → exits 0 with core-only tip
- [ ] 6.10 Test: interactive mode, user selects no bundles and confirms 'n' → loops back to selection UI
- [ ] 6.11 Test: `init_command()` on re-run (bundles already installed) → does NOT show bundle selection gate (mock `get_installed_bundles` returning non-empty)
- [ ] 6.12 Test: `init_command(install="all")` installs all 5 bundles (mock installer)
- [ ] 6.13 Test: `init_command(install="backlog,codebase")` installs `specfact-backlog` and `specfact-codebase`
- [ ] 6.14 Test: `init_command(install="widgets")` exits 1 with unknown bundle error
- [ ] 6.15 Test: core commands (`specfact auth`, `specfact module`) work regardless of bundle installation state
- [ ] 6.16 Test: `init_command` has `@require` and `@beartype` decorators on all new public parameters
- [ ] 6.17 Run: `hatch test -- tests/unit/modules/init/test_mandatory_bundle_selection.py -v` (expect failures — record in TDD_EVIDENCE.md)

## 7. Write tests for lean help output and missing-bundle error (TDD, expect failure)

- [ ] 7.1 Create `tests/unit/cli/test_lean_help_output.py`
- [ ] 7.2 Test: `specfact --help` output (fresh install, no bundles) contains exactly 4 core commands and ≤ 6 total
- [ ] 7.3 Test: `specfact --help` output does NOT contain: project, plan, backlog, code, spec, govern, validate, contract, sdd, generate, enforce, patch, migrate, repro, drift, analyze, policy (any of the 17 extracted)
- [ ] 7.4 Test: `specfact --help` output contains hint: "Run `specfact init` to install workflow bundles"
- [ ] 7.5 Test: `specfact backlog --help` when backlog bundle NOT installed → error "The 'backlog' bundle is not installed" + install command
- [ ] 7.6 Test: `specfact code --help` when codebase bundle IS installed (mock) → shows `analyze`, `drift`, `validate`, `repro` sub-commands
- [ ] 7.7 Test: `specfact --help` with all 5 bundles installed (mock) → shows 9 top-level commands (4 core + 5 category groups)
- [ ] 7.8 Run: `hatch test -- tests/unit/cli/test_lean_help_output.py -v` (expect failures — record in TDD_EVIDENCE.md)

## 8. Write tests for pyproject.toml / setup.py package includes (TDD, expect failure)

- [ ] 8.1 Create `tests/unit/packaging/test_core_package_includes.py`
- [ ] 8.2 Test: parse `pyproject.toml` — `packages` list contains only paths for `init`, `auth`, `module_registry`, `upgrade` core modules
- [ ] 8.3 Test: parse `pyproject.toml` — no path contains any of the 17 deleted module names
- [ ] 8.4 Test: `setup.py` `find_packages()` call with corrected `include` kwarg does not pick up the 17 deleted module directories (mock filesystem)
- [ ] 8.5 Test: version in `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py` are all identical
- [ ] 8.6 Run: `hatch test -- tests/unit/packaging/test_core_package_includes.py -v` (expect failures — record in TDD_EVIDENCE.md)

## 9. Run pre-deletion gate and record evidence

- [x] 9.1 Verify module-migration-02 is complete: `specfact-cli-modules/registry/index.json` contains all 5 bundle entries
- [x] 9.2 Run the module removal gate:

  ```bash
  hatch run verify-removal-gate
  ```

  If the registry index is not found (e.g. when specfact-cli-modules is not a sibling of the checkout), either:
  - Set **SPECFACT_MODULES_REPO** to the modules repo root and run `hatch run verify-removal-gate`, or
  - Run with an explicit path: `python scripts/verify-bundle-published.py --modules ... --registry-index /path/to/specfact-cli-modules/registry/index.json` then `python scripts/verify-modules-signature.py --require-signature`.
  The script supports both formats: (a) SPECFACT_MODULES_REPO for explicit path; (b) fallback sibling search when unset. Use `--branch dev` or `--branch main` to force registry branch; otherwise auto-detects from current git branch.
- [x] 9.3 Record gate output (table with all PASS rows) in `openspec/changes/module-migration-03-core-slimming/TDD_EVIDENCE.md` as pre-deletion evidence (timestamp + command + result)
- [x] 9.4 If any bundle fails: STOP — do not proceed until module-migration-02 is complete and all bundles are verified

## 10. Phase 1 — Delete non-core module directories (one bundle per commit)

**PREREQUISITE: Task 9 gate must have exited 0 before any deletion in this phase.**

### 10.1 Delete specfact-project modules

- [x] 10.1.1 `git rm -r src/specfact_cli/modules/project/ src/specfact_cli/modules/plan/ src/specfact_cli/modules/import_cmd/ src/specfact_cli/modules/sync/ src/specfact_cli/modules/migrate/`
- [x] 10.1.2 Update `pyproject.toml` — remove the 5 project module paths from `packages` and `include`
- [x] 10.1.3 Update `setup.py` — remove corresponding `find_packages` / `package_data` entries
- [x] 10.1.4 `hatch test -- tests/unit/packaging/test_core_package_includes.py -v` — verify project modules absent
- [x] 10.1.5 `git commit -m "feat(core): delete specfact-project module source from core (migration-03)"`

### 10.2 Delete specfact-backlog modules

- [x] 10.2.1 `git rm -r src/specfact_cli/modules/backlog/ src/specfact_cli/modules/policy_engine/`
- [x] 10.2.2 Update `pyproject.toml` and `setup.py` for backlog + policy_engine
- [x] 10.2.3 `hatch test -- tests/unit/packaging/test_core_package_includes.py -v`
- [x] 10.2.4 `git commit -m "feat(core): delete specfact-backlog module source from core (migration-03)"`

### 10.3 Delete specfact-codebase modules

- [x] 10.3.1 `git rm -r src/specfact_cli/modules/analyze/ src/specfact_cli/modules/drift/ src/specfact_cli/modules/validate/ src/specfact_cli/modules/repro/`
- [x] 10.3.2 Update `pyproject.toml` and `setup.py` for codebase modules
- [x] 10.3.3 `hatch test -- tests/unit/packaging/test_core_package_includes.py -v`
- [x] 10.3.4 `git commit -m "feat(core): delete specfact-codebase module source from core (migration-03)"`

### 10.4 Delete specfact-spec modules

- [x] 10.4.1 `git rm -r src/specfact_cli/modules/contract/ src/specfact_cli/modules/spec/ src/specfact_cli/modules/sdd/ src/specfact_cli/modules/generate/`
- [x] 10.4.2 Update `pyproject.toml` and `setup.py` for spec modules
- [x] 10.4.3 `hatch test -- tests/unit/packaging/test_core_package_includes.py -v`
- [x] 10.4.4 `git commit -m "feat(core): delete specfact-spec module source from core (migration-03)"`

### 10.5 Delete specfact-govern modules

- [x] 10.5.1 `git rm -r src/specfact_cli/modules/enforce/ src/specfact_cli/modules/patch_mode/`
- [x] 10.5.2 Update `pyproject.toml` and `setup.py` for govern modules
- [x] 10.5.3 `hatch test -- tests/unit/packaging/test_core_package_includes.py -v` — all 17 modules absent, only 4 core remain
- [x] 10.5.4 `git commit -m "feat(core): delete specfact-govern module source from core (migration-03)"`

### 10.6 Verify all tests pass after all deletions

- [x] 10.6.1 `hatch test -- tests/unit/packaging/test_core_package_includes.py -v` — confirm full suite green
- [x] 10.6.2 Record passing-test result in TDD_EVIDENCE.md (Phase 1: package includes)

## 11. Phase 2 — Update bootstrap.py (shim removal + 4-core-only registration)

- [ ] 11.1 Edit `src/specfact_cli/registry/bootstrap.py`:
  - [ ] 11.1.1 Remove all import statements for the 17 deleted module packages
  - [ ] 11.1.2 Remove all `register_module()` / `add_typer()` calls for the 17 deleted modules
  - [ ] 11.1.3 Remove backward-compat flat command shim registration logic (entire shim block)
  - [ ] 11.1.4 Add `_mount_installed_category_groups(cli_app)` call after the 4 core registrations
  - [ ] 11.1.5 Implement `_mount_installed_category_groups(cli_app: typer.Typer) -> None` using `get_installed_bundles()` and `CATEGORY_GROUP_FACTORIES` mapping
  - [ ] 11.1.6 Add `@beartype` to `bootstrap_modules()` and `_mount_installed_category_groups()`
- [ ] 11.2 `hatch test -- tests/unit/registry/test_core_only_bootstrap.py -v` — verify passes
- [ ] 11.3 Record passing-test result in TDD_EVIDENCE.md (Phase 2: bootstrap)
- [ ] 11.4 `git commit -m "feat(bootstrap): remove flat shims and non-core module registrations (migration-03)"`

## 12. Phase 3 — Update cli.py (conditional category group mounting)

- [ ] 12.1 Edit `src/specfact_cli/cli.py`:
  - [ ] 12.1.1 Remove any unconditional category group registrations for the 17 extracted module categories
  - [ ] 12.1.2 Ensure `bootstrap_modules(cli_app)` is the single registration entry point (it now handles conditional mounting)
  - [ ] 12.1.3 Add actionable error handling for unrecognised commands that match known bundle group names
- [ ] 12.2 `hatch test -- tests/unit/cli/test_lean_help_output.py -v` — verify lean help and missing-bundle errors pass
- [ ] 12.3 Record passing-test result in TDD_EVIDENCE.md (Phase 3: cli.py)
- [ ] 12.4 `git commit -m "feat(cli): conditional category group mount from installed bundles (migration-03)"`

## 13. Phase 4 — Update specfact init for mandatory bundle selection

- [ ] 13.1 Edit `src/specfact_cli/modules/init/src/commands.py` (or equivalent init command file):
  - [ ] 13.1.1 Add `VALID_PROFILES` constant: `frozenset({"solo-developer", "backlog-team", "api-first-team", "enterprise-full-stack"})`
  - [ ] 13.1.2 Add `PROFILE_BUNDLES` mapping: profile name → list of bundle IDs
  - [ ] 13.1.3 Update `init_command()` signature: add `profile: Optional[str]` and `install: Optional[str]` parameters (if not already present from module-migration-01)
  - [ ] 13.1.4 Add CI/CD mode guard: if `_is_cicd_mode()` and profile is None and install is None → exit 1 with error
  - [ ] 13.1.5 Add first-run detection: if `get_installed_bundles()` is empty and not CI/CD → enter interactive selection loop
  - [ ] 13.1.6 Add interactive selection loop with confirmation prompt for core-only selection
  - [ ] 13.1.7 Implement `_install_profile_bundles(profile: str) -> None` — resolves bundle list from `PROFILE_BUNDLES`, calls `module_installer.install_module()` for each
  - [ ] 13.1.8 Implement `_install_bundle_list(install_arg: str) -> None` — parses comma-separated list or "all", validates bundle names, calls installer
  - [ ] 13.1.9 Add `@require(lambda profile: profile is None or profile in VALID_PROFILES)` on `init_command`
  - [ ] 13.1.10 Add `@beartype` on `init_command`, `_install_profile_bundles`, `_install_bundle_list`
- [ ] 13.2 `hatch test -- tests/unit/modules/init/test_mandatory_bundle_selection.py -v` — verify all pass
- [ ] 13.3 Record passing-test result in TDD_EVIDENCE.md (Phase 4: init mandatory selection)
- [ ] 13.4 `git commit -m "feat(init): enforce mandatory bundle selection and profile presets (migration-03)"`

## 14. Module signing gate

- [ ] 14.1 Run verification against the 4 remaining core modules:

  ```bash
  hatch run ./scripts/verify-modules-signature.py --require-signature
  ```

- [ ] 14.2 If any of the 4 core modules fail (signatures may be stale after directory restructuring): bump patch version in their `module-package.yaml` and re-sign

  ```bash
  hatch run python scripts/sign-modules.py --key-file <private-key.pem> src/specfact_cli/modules/init/module-package.yaml src/specfact_cli/modules/auth/module-package.yaml src/specfact_cli/modules/module_registry/module-package.yaml src/specfact_cli/modules/upgrade/module-package.yaml
  ```

- [ ] 14.3 Re-run verification until fully green:

  ```bash
  hatch run ./scripts/verify-modules-signature.py --require-signature
  ```

- [ ] 14.4 Commit updated module-package.yaml files if re-signed

## 15. Integration and E2E tests

- [ ] 15.1 Create `tests/integration/test_core_slimming.py`
  - [ ] 15.1.1 Test: fresh install CLI app — `cli_app.registered_commands` contains only 4 core commands (mock no bundles installed)
  - [ ] 15.1.2 Test: `specfact module install nold-ai/specfact-backlog` (mock) → after install, `specfact backlog --help` resolves
  - [ ] 15.1.3 Test: `specfact init --profile solo-developer` → installs `specfact-codebase`, exits 0, `specfact code --help` resolves
  - [ ] 15.1.4 Test: `specfact init --profile enterprise-full-stack` → all 5 bundles installed, `specfact --help` shows 9 commands
  - [ ] 15.1.5 Test: `specfact init --install all` → all 5 bundles installed (identical to enterprise profile)
  - [ ] 15.1.6 Test: flat shim command `specfact plan` exits with "not found" + install instructions
  - [ ] 15.1.7 Test: flat shim command `specfact validate` exits with "not found" + install instructions
  - [ ] 15.1.8 Test: `specfact init` (CI/CD mode, no --profile/--install) exits 1 with actionable error
- [ ] 15.2 Create `tests/e2e/test_core_slimming_e2e.py`
  - [ ] 15.2.1 Test: end-to-end `specfact init --profile solo-developer` in temp workspace → `specfact code analyze --help` resolves via installed codebase bundle
  - [ ] 15.2.2 Test: end-to-end `specfact init --profile api-first-team` → `specfact-project` auto-installed as dep of `specfact-spec`; `specfact spec contract --help` resolves
  - [ ] 15.2.3 Test: end-to-end `specfact --help` output on fresh install contains ≤ 6 lines of commands
- [ ] 15.3 Run: `hatch test -- tests/integration/test_core_slimming.py tests/e2e/test_core_slimming_e2e.py -v`
- [ ] 15.4 Record passing E2E result in TDD_EVIDENCE.md

## 16. Quality gates

- [ ] 16.1 Format
  - [ ] 16.1.1 `hatch run format`
  - [ ] 16.1.2 Fix any formatting issues

- [ ] 16.2 Type checking
  - [ ] 16.2.1 `hatch run type-check`
  - [ ] 16.2.2 Fix any basedpyright strict errors (especially in `bootstrap.py`, `commands.py`, `verify-bundle-published.py`)

- [ ] 16.3 Full lint suite
  - [ ] 16.3.1 `hatch run lint`
  - [ ] 16.3.2 Fix any lint errors

- [ ] 16.4 YAML lint
  - [ ] 16.4.1 `hatch run yaml-lint`
  - [ ] 16.4.2 Fix any YAML formatting issues in the 4 core `module-package.yaml` files

- [ ] 16.5 Contract-first testing
  - [ ] 16.5.1 `hatch run contract-test`
  - [ ] 16.5.2 Verify all `@icontract` contracts pass for new and modified public APIs (`bootstrap_modules`, `_mount_installed_category_groups`, `init_command`, `verify_bundle_published`)

- [ ] 16.6 Smart test suite
  - [ ] 16.6.1 `hatch run smart-test`
  - [ ] 16.6.2 Verify no regressions in the 4 core commands (init, auth, module, upgrade)

- [ ] 16.7 Module signing gate (final confirmation)
  - [ ] 16.7.1 `hatch run ./scripts/verify-modules-signature.py --require-signature`
  - [ ] 16.7.2 If any core module fails: re-sign as in step 14.2
  - [ ] 16.7.3 Re-run until fully green

## 17. Documentation research and review

- [ ] 17.1 Identify affected documentation
  - [ ] 17.1.1 Review `docs/guides/getting-started.md` — major update required: install + first-run section now requires profile selection
  - [ ] 17.1.2 Review `docs/guides/installation.md` — update install steps; add `specfact init --profile <name>` as mandatory post-install step
  - [ ] 17.1.3 Review `docs/reference/commands.md` — update command topology (4 core + category groups); mark removed flat shim commands as deleted
  - [ ] 17.1.4 Review `docs/reference/module-categories.md` — note modules no longer ship in core; update install instructions to `specfact module install`
  - [ ] 17.1.5 Review `docs/guides/marketplace.md` — update to reflect bundles are now the mandatory install path (not optional add-ons)
  - [ ] 17.1.6 Review `README.md` — update "Getting started" to lead with profile selection; update command list to category groups
  - [ ] 17.1.7 Review `docs/index.md` — confirm landing page reflects lean core model
  - [ ] 17.1.8 Review `docs/_layouts/default.html` — verify sidebar has no stale flat-command references

- [ ] 17.2 Update `docs/guides/getting-started.md`
  - [ ] 17.2.1 Verify Jekyll front-matter is preserved (title, layout, nav_order, permalink)
  - [ ] 17.2.2 Rewrite install + first-run section: after `pip install specfact-cli`, run `specfact init --profile <name>` (with profile table)
  - [ ] 17.2.3 Add "After installation" command table showing category group commands per installed profile
  - [ ] 17.2.4 Add "Upgrading" section: explain post-upgrade bundle reinstall requirement

- [ ] 17.3 Update `docs/guides/installation.md` (create if not existing)
  - [ ] 17.3.1 Add Jekyll front-matter: `layout: default`, `title: Installation`, `nav_order: <appropriate>`, `permalink: /guides/installation/`
  - [ ] 17.3.2 Document the two-step install: `pip install specfact-cli` → `specfact init --profile <name>`
  - [ ] 17.3.3 Document CI/CD bootstrap: `specfact init --profile enterprise` or `specfact init --install all`
  - [ ] 17.3.4 Document upgrade path from pre-slimming versions

- [ ] 17.4 Update `docs/reference/commands.md`
  - [ ] 17.4.1 Replace 21-command flat topology with 4 core + 5 category group topology
  - [ ] 17.4.2 Add "Removed commands" section listing flat shim commands removed in this version and their category group replacements

- [ ] 17.5 Update `README.md`
  - [ ] 17.5.1 Update "Getting started" section to lead with profile selection UX
  - [ ] 17.5.2 Replace flat command list with a category group table
  - [ ] 17.5.3 Ensure first screen is compelling for new users (value + how to get started in ≤ 5 lines)

- [ ] 17.6 Update `docs/_layouts/default.html`
  - [ ] 17.6.1 Add "Installation" and "Upgrade Guide" links to sidebar if installation.md is new
  - [ ] 17.6.2 Remove any sidebar links to individual flat commands that no longer exist

- [ ] 17.7 Verify docs
  - [ ] 17.7.1 Check all Markdown links resolve
  - [ ] 17.7.2 Check front-matter is valid YAML in all modified doc files

## 18. Version and changelog

**Release version:** Use **0.40.0** as the combined release for all module-migration changes (migration-02, -03, -04, -05, etc.). Do not bump to 0.41.0 or 0.40.x for migration-03 alone; sync to 0.40.0 when updating version and changelog.

- [ ] 18.1 Determine version bump: **minor** (feature removal: bundled modules are no longer included; first-run gate is new behavior; feature/* branch → minor increment)
  - [ ] 18.1.1 Confirm current version in `pyproject.toml`
  - [ ] 18.1.2 **Use 0.40.0** for the combined module-migration release (do not apply a separate minor bump for this change only)
  - [ ] 18.1.3 Request explicit confirmation from user before applying bump

- [ ] 18.2 Sync version across all files
  - [ ] 18.2.1 `pyproject.toml`
  - [ ] 18.2.2 `setup.py`
  - [ ] 18.2.3 `src/__init__.py` (if present)
  - [ ] 18.2.4 `src/specfact_cli/__init__.py`
  - [ ] 18.2.5 Verify all four files show the same version

- [ ] 18.3 Update `CHANGELOG.md`
  - [ ] 18.3.1 Add new section `## [0.40.0] - 2026-MM-DD` (combined module-migration release)
  - [ ] 18.3.2 Add `### Added` subsection:
    - `scripts/verify-bundle-published.py` — pre-deletion gate for marketplace bundle verification
    - `hatch run verify-removal-gate` task alias
    - Mandatory bundle selection enforcement in `specfact init` (CI/CD mode requires `--profile` or `--install`)
    - Actionable "bundle not installed" error for category group commands
  - [ ] 18.3.3 Add `### Changed` subsection:
    - `specfact --help` on fresh install now shows ≤ 6 commands (4 core + at most 2 core-adjacent); category groups appear only when bundle is installed
    - `bootstrap.py` now registers 4 core modules only; category groups mounted dynamically from installed bundles
    - `specfact init` first-run experience now enforces bundle selection (interactive: prompt loop; CI/CD: exit 1 if no --profile/--install)
    - Profile presets fully activate marketplace bundle installation
  - [ ] 18.3.4 Add `### Removed` subsection:
    - 17 non-core module directories removed from specfact-cli core package (project, plan, import_cmd, sync, migrate, backlog, policy_engine, analyze, drift, validate, repro, contract, spec, sdd, generate, enforce, patch_mode)
    - Backward-compat flat command shims removed (specfact plan, specfact validate, specfact contract, etc. — use category group commands or install the relevant bundle)
    - Re-export shims `specfact_cli.modules.*` for extracted modules removed
  - [ ] 18.3.5 Add `### Migration` subsection:
    - CI/CD pipelines: add `specfact init --profile enterprise` or `specfact init --install all` as a bootstrap step after install
    - Scripts using flat shim commands: replace `specfact plan` → `specfact project plan`, `specfact validate` → `specfact code validate`, etc.
    - Code importing `specfact_cli.modules.<name>`: update to `specfact_<bundle>.<name>`
  - [ ] 18.3.6 Reference GitHub issue number

## 19. Create PR to dev

- [ ] 19.1 Verify TDD_EVIDENCE.md is complete with:
  - Pre-deletion gate output (gate script PASS for all 17 modules)
  - Failing-before and passing-after evidence for: gate script, bootstrap 4-core-only, init mandatory selection, lean help output, package includes
  - Passing E2E results

- [ ] 19.2 Prepare commit(s)
  - [ ] 19.2.1 Stage all changed files (see deletion commits in phase 10; `scripts/verify-bundle-published.py`, `src/specfact_cli/registry/bootstrap.py`, `src/specfact_cli/cli.py`, `src/specfact_cli/modules/init/`, `pyproject.toml`, `setup.py`, `src/specfact_cli/__init__.py`, `tests/`, `docs/`, `CHANGELOG.md`, `openspec/changes/module-migration-03-core-slimming/`)
  - [ ] 19.2.2 `git commit -m "feat: slim core package, mandatory profile selection, remove non-core modules (#<issue>)"`
  - [ ] 19.2.3 (If GPG signing required) provide `git commit -S -m "..."` for user to run locally
  - [ ] 19.2.4 `git push -u origin feature/module-migration-03-core-slimming`

- [ ] 19.3 Create PR via gh CLI
  - [ ] 19.3.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/module-migration-03-core-slimming --title "feat: Core Package Slimming — Lean Install and Mandatory Profile Selection (#<issue>)" --body "..."` (body: summary bullets, breaking changes, migration guide, test plan checklist, OpenSpec change ID, issue reference)
  - [ ] 19.3.2 Capture PR URL

- [ ] 19.4 Link PR to project board
  - [ ] 19.4.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

- [ ] 19.5 Verify PR
  - [ ] 19.5.1 Confirm base is `dev`, head is `feature/module-migration-03-core-slimming`
  - [ ] 19.5.2 Confirm CI checks are running (tests.yml, specfact.yml)

---

## Post-merge worktree cleanup

After PR is merged to `dev`:

```bash
git fetch origin
git worktree remove ../specfact-cli-worktrees/feature/module-migration-03-core-slimming
git branch -d feature/module-migration-03-core-slimming
git worktree prune
```

If remote branch cleanup is needed:

```bash
git push origin --delete feature/module-migration-03-core-slimming
```

---

## CHANGE_ORDER.md update (required — also covered in task 3 above)

After this change is created, `openspec/CHANGE_ORDER.md` must reflect:

- Module migration table: `module-migration-03-core-slimming` row with GitHub issue link and `Blocked by: module-migration-02`
- Wave 4: confirm `module-migration-03-core-slimming` is listed after `module-migration-02-bundle-extraction`
- After merge and archive: move row to Implemented section with archive date; update Wave 4 status if all Wave 4 changes are complete
