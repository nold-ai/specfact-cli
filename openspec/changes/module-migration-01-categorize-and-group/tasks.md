# Implementation Tasks: module-migration-01-categorize-and-group

## TDD / SDD Order (Enforced)

Per `openspec/config.yaml`, the following order is mandatory and non-negotiable for every behavior-changing task:

1. **Spec deltas** — already created in `specs/` (module-grouping, category-command-groups, first-run-selection)
2. **Tests from spec scenarios** — translate each Given/When/Then scenario into test cases; run tests and expect failure (no implementation yet)
3. **Capture failing-test evidence** — record in `openspec/changes/module-migration-01-categorize-and-group/TDD_EVIDENCE.md`
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
  - [ ] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/module-migration-01-categorize-and-group -b feature/module-migration-01-categorize-and-group origin/dev`
  - [ ] 1.1.3 `cd ../specfact-cli-worktrees/feature/module-migration-01-categorize-and-group`
  - [ ] 1.1.4 `git branch --show-current` — verify output is `feature/module-migration-01-categorize-and-group`
  - [ ] 1.1.5 `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
  - [ ] 1.1.6 `hatch env create`
  - [ ] 1.1.7 `hatch run smart-test-status` and `hatch run contract-test-status` — confirm baseline green

## 2. Create GitHub issue for change tracking

- [ ] 2.1 Create GitHub issue in nold-ai/specfact-cli
  - [ ] 2.1.1 `gh issue create --repo nold-ai/specfact-cli --title "[Change] Module Grouping and Category Command Groups" --label "enhancement,change-proposal" --body "$(cat <<'EOF'`

    ```text
    ## Why

    SpecFact CLI exposes 21 flat top-level commands, overwhelming new users. The marketplace foundation (marketplace-01, marketplace-02) now supports signed packages and bundle-level dependency resolution. This change introduces category grouping metadata, 5 umbrella group commands, and VS Code-style first-run bundle selection.

    ## What Changes

    - Add `category`, `bundle`, `bundle_group_command`, `bundle_sub_command` to all 21 `module-package.yaml` files
    - Create `src/specfact_cli/groups/` with 5 category Typer apps
    - Update `bootstrap.py` to mount category groups with compat shims
    - Add `category_grouping_enabled` config flag (default `true`)
    - Update `specfact init` with `--profile` and `--install` for first-run bundle selection

    *OpenSpec Change Proposal: module-migration-01-categorize-and-group*
    ```

  - [ ] 2.1.2 Capture issue number and URL from output
  - [ ] 2.1.3 Update `openspec/changes/module-migration-01-categorize-and-group/proposal.md` Source Tracking section with issue number, URL, and status `open`

## 3. Phase 1 — Add category metadata to all module-package.yaml files (TDD)

### 3.1 Write tests for manifest validation (expect failure)

- [ ] 3.1.1 Create `tests/unit/registry/test_module_grouping.py`
- [ ] 3.1.2 Test: `module-package.yaml` with `category: codebase` passes validation
- [ ] 3.1.3 Test: `module-package.yaml` with `category: unknown` raises `ModuleManifestError`
- [ ] 3.1.4 Test: `module-package.yaml` without `category` field mounts as ungrouped flat command (no error, warning logged)
- [ ] 3.1.5 Test: `bundle_group_command` mismatch vs canonical category raises `ModuleManifestError`
- [ ] 3.1.6 Test: core-category modules have no `bundle` or `bundle_group_command`
- [ ] 3.1.7 Test: `registry.group_modules_by_category()` returns correct grouping dict from a list of module manifests
- [ ] 3.1.8 Run tests: `hatch test -- tests/unit/registry/test_module_grouping.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 3.2 Implement category field validation in registry

- [ ] 3.2.1 Add `category`, `bundle`, `bundle_group_command`, `bundle_sub_command` fields (Optional[str]) to `ModulePackage` Pydantic model in `src/specfact_cli/registry/module_packages.py`
- [ ] 3.2.2 Add validation: if `category` is set and not in `{"core","project","backlog","codebase","spec","govern"}` → raise `ModuleManifestError`
- [ ] 3.2.3 Add validation: if `category` != `"core"` and `bundle_group_command` does not match canonical mapping → raise `ModuleManifestError`
- [ ] 3.2.4 Add `group_modules_by_category()` function with `@require` and `@beartype` decorators
- [ ] 3.2.5 Add warning log when `category` field is absent
- [ ] 3.2.6 `hatch test -- tests/unit/registry/test_module_grouping.py -v` — verify tests pass

### 3.3 Add category metadata to all 21 module-package.yaml files

Apply the canonical category assignments:

**Core (no bundle fields):**

- [ ] 3.3.1 `modules/init/module-package.yaml` → `category: core`, `bundle_sub_command: init`
- [ ] 3.3.2 `modules/auth/module-package.yaml` → `category: core`, `bundle_sub_command: auth`
- [ ] 3.3.3 `modules/module_registry/module-package.yaml` → `category: core`, `bundle_sub_command: module`
- [ ] 3.3.4 `modules/upgrade/module-package.yaml` → `category: core`, `bundle_sub_command: upgrade`

**Project bundle (`specfact-project`, group command `project`):**

- [ ] 3.3.5 `modules/project/module-package.yaml` → `category: project`, `bundle: specfact-project`, `bundle_group_command: project`, `bundle_sub_command: project`
- [ ] 3.3.6 `modules/plan/module-package.yaml` → `category: project`, `bundle: specfact-project`, `bundle_group_command: project`, `bundle_sub_command: plan`
- [ ] 3.3.7 `modules/import_cmd/module-package.yaml` → `category: project`, `bundle: specfact-project`, `bundle_group_command: project`, `bundle_sub_command: import`
- [ ] 3.3.8 `modules/sync/module-package.yaml` → `category: project`, `bundle: specfact-project`, `bundle_group_command: project`, `bundle_sub_command: sync`
- [ ] 3.3.9 `modules/migrate/module-package.yaml` → `category: project`, `bundle: specfact-project`, `bundle_group_command: project`, `bundle_sub_command: migrate`

**Backlog bundle (`specfact-backlog`, group command `backlog`):**

- [ ] 3.3.10 `modules/backlog/module-package.yaml` → `category: backlog`, `bundle: specfact-backlog`, `bundle_group_command: backlog`, `bundle_sub_command: backlog`
- [ ] 3.3.11 `modules/policy_engine/module-package.yaml` → `category: backlog`, `bundle: specfact-backlog`, `bundle_group_command: backlog`, `bundle_sub_command: policy`

**Codebase bundle (`specfact-codebase`, group command `code`):**

- [ ] 3.3.12 `modules/analyze/module-package.yaml` → `category: codebase`, `bundle: specfact-codebase`, `bundle_group_command: code`, `bundle_sub_command: analyze`
- [ ] 3.3.13 `modules/drift/module-package.yaml` → `category: codebase`, `bundle: specfact-codebase`, `bundle_group_command: code`, `bundle_sub_command: drift`
- [ ] 3.3.14 `modules/validate/module-package.yaml` → `category: codebase`, `bundle: specfact-codebase`, `bundle_group_command: code`, `bundle_sub_command: validate`
- [ ] 3.3.15 `modules/repro/module-package.yaml` → `category: codebase`, `bundle: specfact-codebase`, `bundle_group_command: code`, `bundle_sub_command: repro`

**Spec bundle (`specfact-spec`, group command `spec`):**

- [ ] 3.3.16 `modules/contract/module-package.yaml` → `category: spec`, `bundle: specfact-spec`, `bundle_group_command: spec`, `bundle_sub_command: contract`
- [ ] 3.3.17 `modules/spec/module-package.yaml` → `category: spec`, `bundle: specfact-spec`, `bundle_group_command: spec`, `bundle_sub_command: api` (collision avoidance)
- [ ] 3.3.18 `modules/sdd/module-package.yaml` → `category: spec`, `bundle: specfact-spec`, `bundle_group_command: spec`, `bundle_sub_command: sdd`
- [ ] 3.3.19 `modules/generate/module-package.yaml` → `category: spec`, `bundle: specfact-spec`, `bundle_group_command: spec`, `bundle_sub_command: generate`

**Govern bundle (`specfact-govern`, group command `govern`):**

- [ ] 3.3.20 `modules/enforce/module-package.yaml` → `category: govern`, `bundle: specfact-govern`, `bundle_group_command: govern`, `bundle_sub_command: enforce`
- [ ] 3.3.21 `modules/patch_mode/module-package.yaml` → `category: govern`, `bundle: specfact-govern`, `bundle_group_command: govern`, `bundle_sub_command: patch`

### 3.4 Module signing gate (after all module-package.yaml edits)

- [ ] 3.4.1 `hatch run ./scripts/verify-modules-signature.py --require-signature` — expect failures (manifests changed, signatures stale)
- [ ] 3.4.2 Bump version field in each modified module-package.yaml (patch increment per module)
- [ ] 3.4.3 `hatch run python scripts/sign-modules.py --key-file <private-key.pem> src/specfact_cli/modules/*/module-package.yaml`
- [ ] 3.4.4 `hatch run ./scripts/verify-modules-signature.py --require-signature` — confirm fully green

## 4. Phase 2 — Category group commands (TDD)

### 4.1 Write tests for category group bootstrap (expect failure)

- [ ] 4.1.1 Create `tests/unit/registry/test_category_groups.py`
- [ ] 4.1.2 Test: with `category_grouping_enabled=True`, `bootstrap_cli()` registers `code`, `backlog`, `project`, `spec`, `govern` group commands
- [ ] 4.1.3 Test: with `category_grouping_enabled=False`, bootstrap registers flat module commands (no group commands)
- [ ] 4.1.4 Test: `specfact code analyze contracts` routes to the same handler as `specfact analyze contracts`
- [ ] 4.1.5 Test: `specfact govern --help` when govern bundle not installed produces install suggestion
- [ ] 4.1.6 Test: flat shim `specfact validate` emits deprecation warning in Copilot mode
- [ ] 4.1.7 Test: flat shim `specfact validate` is silent in CI/CD mode
- [ ] 4.1.8 Test: `specfact spec api validate` routes correctly (collision avoidance)
- [ ] 4.1.9 Create `tests/unit/groups/test_codebase_group.py` — test group app has expected sub-commands
- [ ] 4.1.10 Run tests: `hatch test -- tests/unit/registry/test_category_groups.py tests/unit/groups/ -v` (expect failures — record in TDD_EVIDENCE.md)

### 4.2 Create `src/specfact_cli/groups/` package

- [ ] 4.2.1 Create `src/specfact_cli/groups/__init__.py`
- [ ] 4.2.2 Create `src/specfact_cli/groups/project_group.py`
  - `app = typer.Typer(name="project", help="Project lifecycle commands.", no_args_is_help=True)`
  - Members: project, plan, import_cmd (as `import`), sync, migrate
  - `@require` and `@beartype` on `_register_members()`
- [ ] 4.2.3 Create `src/specfact_cli/groups/backlog_group.py`
  - Members: backlog, policy_engine (as `policy`)
- [ ] 4.2.4 Create `src/specfact_cli/groups/codebase_group.py`
  - Members: analyze, drift, validate, repro
- [ ] 4.2.5 Create `src/specfact_cli/groups/spec_group.py`
  - Members: contract, spec (as `api`), sdd, generate
- [ ] 4.2.6 Create `src/specfact_cli/groups/govern_group.py`
  - Members: enforce, patch_mode (as `patch`)
- [ ] 4.2.7 All group files must use `@icontract` and `@beartype` on all public functions

### 4.3 Update `bootstrap.py` to mount category groups

- [ ] 4.3.1 Read `category_grouping_enabled` from config (default `True`)
- [ ] 4.3.2 If `True`: import and mount each group app via `app.add_typer()`; skip flat mounting for grouped modules
- [ ] 4.3.3 Always mount core modules (init, auth, module, upgrade) as flat top-level commands
- [ ] 4.3.4 Implement `_register_compat_shims(app)` for all 17 non-core modules:
  - Shim emits deprecation warning in Copilot mode, silent in CI/CD mode
  - Delegates to category group equivalent
- [ ] 4.3.5 Add `@require`, `@ensure`, and `@beartype` to all modified/new bootstrap functions

### 4.4 Update `cli.py` to register category groups

- [ ] 4.4.1 Confirm category group apps are registered via `bootstrap.py` (no direct `cli.py` changes expected; verify and update if needed)

### 4.5 Verify tests pass

- [ ] 4.5.1 `hatch test -- tests/unit/registry/test_category_groups.py tests/unit/groups/ -v`
- [ ] 4.5.2 Record passing-test results in TDD_EVIDENCE.md

## 5. Phase 3 — First-run module selection in `specfact init` (TDD)

### 5.1 Write tests for first-run selection (expect failure)

- [ ] 5.1.1 Create `tests/unit/modules/init/test_first_run_selection.py`
- [ ] 5.1.2 Test: `specfact init --profile solo-developer` installs only `specfact-codebase` (mock installer)
- [ ] 5.1.3 Test: `specfact init --profile enterprise-full-stack` installs all 5 bundles
- [ ] 5.1.4 Test: `specfact init --profile nonexistent` exits non-zero with error listing valid profiles
- [ ] 5.1.5 Test: `specfact init --install backlog,codebase` installs `specfact-backlog` and `specfact-codebase`
- [ ] 5.1.6 Test: `specfact init --install all` installs all 5 bundles
- [ ] 5.1.7 Test: `specfact init --install widgets` exits non-zero with unknown bundle error
- [ ] 5.1.8 Test: second run of init (bundles already installed) skips first-run selection flow
- [ ] 5.1.9 Test: `spec` bundle installation triggers automatic `project` bundle dep install (mock marketplace-02 dep resolver)
- [ ] 5.1.10 Run tests: `hatch test -- tests/unit/modules/init/test_first_run_selection.py -v` (expect failures — record in TDD_EVIDENCE.md)

### 5.2 Implement first-run selection in `specfact init`

- [ ] 5.2.1 Add `--profile` and `--install` parameters to `specfact init` command in `src/specfact_cli/modules/init/src/commands.py`
- [ ] 5.2.2 Implement `is_first_run()` detection (no category bundle installed)
- [ ] 5.2.3 Implement Copilot-mode interactive bundle selection UI using `rich` (multi-select checkboxes)
- [ ] 5.2.4 Implement profile preset resolution: map profile name → bundle list
- [ ] 5.2.5 Implement `--install` flag parsing: comma-separated bundle names + `all` alias
- [ ] 5.2.6 Implement bundle installation by calling `module_installer.install_module()` for each selected bundle
- [ ] 5.2.7 Implement graceful degradation when marketplace-02 dep resolver unavailable (warn, skip dep resolution)
- [ ] 5.2.8 Add `@require`, `@ensure`, `@beartype` on all new public functions
- [ ] 5.2.9 `hatch test -- tests/unit/modules/init/test_first_run_selection.py -v` — verify tests pass

### 5.3 Record passing-test evidence

- [ ] 5.3.1 Update TDD_EVIDENCE.md with passing-test run for first-run selection (timestamp, command, summary)

## 6. Integration and E2E tests

- [ ] 6.1 Create `tests/integration/test_category_group_routing.py`
  - [ ] 6.1.1 Test: `specfact code analyze --help` returns non-zero-error-free output (CLI integration)
  - [ ] 6.1.2 Test: `specfact backlog --help` lists backlog and policy sub-commands
  - [ ] 6.1.3 Test: deprecated flat command `specfact validate --help` still returns help without error
- [ ] 6.2 Create `tests/e2e/test_first_run_init.py`
  - [ ] 6.2.1 Test: `specfact init --profile solo-developer` in a temp workspace completes without error
  - [ ] 6.2.2 Test: after `--profile solo-developer`, `specfact code analyze --help` is available
- [ ] 6.3 Run integration and E2E suites: `hatch test -- tests/integration/test_category_group_routing.py tests/e2e/test_first_run_init.py -v`

## 7. Quality gates

- [ ] 7.1 Format
  - [ ] 7.1.1 `hatch run format`
  - [ ] 7.1.2 Fix any formatting issues

- [ ] 7.2 Type checking
  - [ ] 7.2.1 `hatch run type-check`
  - [ ] 7.2.2 Fix any basedpyright strict errors

- [ ] 7.3 Full lint suite
  - [ ] 7.3.1 `hatch run lint`
  - [ ] 7.3.2 Fix any lint errors

- [ ] 7.4 YAML lint
  - [ ] 7.4.1 `hatch run yaml-lint`
  - [ ] 7.4.2 Fix any YAML formatting issues (includes module-package.yaml files)

- [ ] 7.5 Contract-first testing
  - [ ] 7.5.1 `hatch run contract-test`
  - [ ] 7.5.2 Verify all contracts pass

- [ ] 7.6 Smart test suite
  - [ ] 7.6.1 `hatch run smart-test`
  - [ ] 7.6.2 Verify no regressions

- [ ] 7.7 Module signing gate
  - [ ] 7.7.1 `hatch run ./scripts/verify-modules-signature.py --require-signature`
  - [ ] 7.7.2 If any modules fail (due to field additions in step 3): re-sign with `hatch run python scripts/sign-modules.py --key-file <private-key.pem> <module-package.yaml ...>`
  - [ ] 7.7.3 Re-run verification until fully green

## 8. Documentation research and review

- [ ] 8.1 Identify affected documentation
  - [ ] 8.1.1 Review `docs/guides/getting-started.md` — update install and first-run flow with bundle selection UX
  - [ ] 8.1.2 Review `docs/reference/commands.md` — update command topology with before/after category group layout
  - [ ] 8.1.3 Review `README.md` — update command listing to reflect category group commands and fresh-install view
  - [ ] 8.1.4 Review `docs/index.md` — confirm landing page reflects simplified command surface

- [ ] 8.2 Update `docs/guides/getting-started.md`
  - [ ] 8.2.1 Verify Jekyll front-matter is preserved (title, layout, nav_order, permalink)
  - [ ] 8.2.2 Add "First-run bundle selection" section with interactive UI screenshot/ASCII art
  - [ ] 8.2.3 Add profile preset table with bundle contents
  - [ ] 8.2.4 Add `specfact init --profile <name>` usage for CI/CD

- [ ] 8.3 Create `docs/reference/module-categories.md` (new page)
  - [ ] 8.3.1 Add Jekyll front-matter: `layout: default`, `title: Module Categories`, `nav_order: <appropriate>`, `permalink: /reference/module-categories/`
  - [ ] 8.3.2 Write canonical category assignment table (all 21 modules)
  - [ ] 8.3.3 Write bundle contents section per category
  - [ ] 8.3.4 Write profile presets section
  - [ ] 8.3.5 Write before/after command topology section

- [ ] 8.4 Update `docs/_layouts/default.html`
  - [ ] 8.4.1 Add "Module Categories" link to sidebar navigation under Reference section

- [ ] 8.5 Update `README.md`
  - [ ] 8.5.1 Update command listing: show core commands + category group commands
  - [ ] 8.5.2 Add brief mention of first-run bundle selection

- [ ] 8.6 Verify docs build
  - [ ] 8.6.1 Check all Markdown links resolve
  - [ ] 8.6.2 Check front-matter is valid YAML

## 9. Version and changelog

- [ ] 9.1 Determine version bump: **minor** (new feature: category groups, first-run selection; feature/* branch)
  - [ ] 9.1.1 Confirm current version in `pyproject.toml`
  - [ ] 9.1.2 Confirm bump is minor (e.g., `0.X.Y → 0.(X+1).0`)
  - [ ] 9.1.3 Request explicit confirmation from user before applying bump

- [ ] 9.2 Sync version across all files
  - [ ] 9.2.1 `pyproject.toml`
  - [ ] 9.2.2 `setup.py`
  - [ ] 9.2.3 `src/__init__.py` (if present)
  - [ ] 9.2.4 `src/specfact_cli/__init__.py`
  - [ ] 9.2.5 Verify all four files show the same version

- [ ] 9.3 Update `CHANGELOG.md`
  - [ ] 9.3.1 Add new section `## [X.Y.Z] - 2026-MM-DD`
  - [ ] 9.3.2 Add `### Added` subsection:
    - Category group commands: `specfact project`, `specfact backlog`, `specfact code`, `specfact spec`, `specfact govern`
    - `module-grouping` metadata fields in `module-package.yaml` for all 21 modules
    - First-run interactive bundle selection in `specfact init`
    - `--profile` and `--install` flags for `specfact init`
    - 4 workflow profile presets: solo-developer, backlog-team, api-first-team, enterprise-full-stack
    - `category_grouping_enabled` config flag (default `true`)
  - [ ] 9.3.3 Add `### Changed` subsection:
    - `specfact --help` now shows category group commands when bundles are installed
    - Bootstrap mounts category groups by default
  - [ ] 9.3.4 Add `### Deprecated` subsection:
    - All 17 non-core flat top-level commands are deprecated in favor of category group equivalents (removal in next major version)
  - [ ] 9.3.5 Reference GitHub issue number

## 10. Create PR to dev

- [ ] 10.1 Verify TDD_EVIDENCE.md is complete (failing-before and passing-after evidence for all behavior changes)

- [ ] 10.2 Prepare commit
  - [ ] 10.2.1 `git add src/specfact_cli/groups/ src/specfact_cli/registry/ src/specfact_cli/modules/*/module-package.yaml src/specfact_cli/modules/init/src/ docs/ README.md CHANGELOG.md pyproject.toml setup.py src/specfact_cli/__init__.py openspec/changes/module-migration-01-categorize-and-group/`
  - [ ] 10.2.2 `git commit -m "feat: add category group commands and first-run bundle selection (#<issue>)"`
  - [ ] 10.2.3 (If GPG signing required) provide `git commit -S -m "..."` for user to run locally
  - [ ] 10.2.4 `git push -u origin feature/module-migration-01-categorize-and-group`

- [ ] 10.3 Create PR via gh CLI
  - [ ] 10.3.1 `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/module-migration-01-categorize-and-group --title "feat: Module Grouping and Category Command Groups (#<issue>)" --body "$(cat <<'EOF' ... EOF)"`
    - Body: Summary bullets (3 max), Test plan checklist, OpenSpec change ID, issue reference
  - [ ] 10.3.2 Capture PR URL

- [ ] 10.4 Link PR to project board
  - [ ] 10.4.1 `gh project item-add 1 --owner nold-ai --url <PR_URL>`

- [ ] 10.5 Verify PR
  - [ ] 10.5.1 Confirm base is `dev`, head is `feature/module-migration-01-categorize-and-group`
  - [ ] 10.5.2 Confirm CI checks are running (tests.yml, specfact.yml)

---

## Post-merge worktree cleanup

After PR is merged to `dev`:

```bash
git fetch origin
git worktree remove ../specfact-cli-worktrees/feature/module-migration-01-categorize-and-group
git branch -d feature/module-migration-01-categorize-and-group
git worktree prune
```

If remote branch cleanup is needed:

```bash
git push origin --delete feature/module-migration-01-categorize-and-group
```

---

## CHANGE_ORDER.md update (required)

After this change is created, update `openspec/CHANGE_ORDER.md`:

- Add a new **Module Migration** section (if not already present) with row for `module-migration-01-categorize-and-group`, GitHub issue link (TBD until created), and `Blocked by: marketplace-02 (#215)`
- After merge and archive: move row to Implemented section with archive date
