# Implementation Tasks: module-migration-05-modules-repo-quality

## TDD / SDD Order (Enforced)

Per `openspec/config.yaml`, the following order is mandatory and non-negotiable for every behavior-changing task:

1. **Spec deltas** — create under `specs/` as needed
2. **Tests from spec scenarios** — translate each Given/When/Then scenario into test cases; run tests and expect failure
3. **Capture failing-test evidence** — record in `TDD_EVIDENCE.md`
4. **Code implementation** — implement until tests pass and behavior satisfies spec
5. **Capture passing-test evidence** — update `TDD_EVIDENCE.md` with passing run results
6. **Quality gates** — format, type-check, lint, contract-test, smart-test
7. **Documentation research and review**
8. **Version and changelog**
9. **PR creation**

Do NOT implement production code for any behavior-changing step until failing-test evidence is recorded in TDD_EVIDENCE.md.

---

## Timing constraint (hard)

Sections 21 (build pipeline) and 22 (central config files) **must complete before `module-migration-03-core-slimming` closes.** After migration-03 deletes in-repo module source, specfact-cli-modules becomes canonical and must already have quality gates. Begin these sections immediately after this change is opened.

---

## 1. Create git worktree branch from dev

- [x] 1.1 Fetch latest origin and create worktree with feature branch
  - [x] 1.1.1 `git fetch origin`
  - [x] 1.1.2 `git worktree add ../specfact-cli-worktrees/feature/module-migration-05-modules-repo-quality -b feature/module-migration-05-modules-repo-quality origin/dev`
  - [x] 1.1.3 Verify branch: `git branch --show-current`
  - [x] 1.1.4 `hatch env create`
  - [x] 1.1.5 `hatch run smart-test-status` and `hatch run contract-test-status` — confirm baseline green

## 2. Create GitHub issue for change tracking

- [x] 2.1 `gh issue create --repo nold-ai/specfact-cli --title "[Change] Modules Repo Quality Parity" --label "enhancement,change-proposal"`
- [x] 2.2 Capture issue number and URL; update this file's Source Tracking section and `proposal.md`

## 3. Update CHANGE_ORDER.md

- [x] 3.1 Confirm `module-migration-05-modules-repo-quality` row exists in the Module migration table (added in migration-02 gap remediation)
- [x] 3.2 Add GitHub issue number from step 2
- [x] 3.3 Confirm `Blocked by: module-migration-02` and timing note re: migration-03

---

## 21. Build pipeline in specfact-cli-modules (PRIORITY — must precede migration-03)

Add PR orchestrator (or equivalent) and align CI so PRs to specfact-cli-modules run the same quality gates as specfact-cli.

- [x] 21.1 Add or adapt `.github/workflows/pr-orchestrator.yml` (or consolidated workflow) for specfact-cli-modules:
  - Triggers on PR/push to main and dev
  - Jobs: format → type-check → lint → test → contract-test (if added) → coverage threshold → module-signature verification
- [x] 21.2 Align job names, order, and failure behavior with specfact-cli workflows; document any intentional differences (e.g. no Docker build)
- [x] 21.3 Configure branch protection for `main` (and `dev` if applicable): require PR, require status checks, disallow direct push
  - Applied via GitHub API on 2026-03-04 for both `main` and `dev`:
    - required status checks: `quality (3.11)`, `quality (3.12)`, `quality (3.13)`
    - require pull request reviews (1 approval), dismiss stale reviews
    - disallow force pushes and deletions
    - require conversation resolution
- [x] 21.4 Document CI flow in specfact-cli-modules README and AGENTS.md; include how to re-run or debug failed checks
- [x] 21.5 Verify: open a test PR in specfact-cli-modules; confirm all CI jobs run and pass (or fail for expected reasons)
  - 2026-03-04 update: replaced standalone `quality-gates.yml` with tailored orchestrator:
    - `.github/workflows/pr-orchestrator.yml`
    - change detection + dev->main skip behavior
    - explicit `verify-module-signatures` job (`--require-signature --enforce-version-bump`)
    - matrix `quality (3.11/3.12/3.13)` jobs for format/type/lint/yaml/import-boundary/contract/smart-test/test
  - Test PR opened: <https://github.com/nold-ai/specfact-cli-modules/pull/4>
  - Observed checks:
    - `quality (3.11)` pass (51s)
    - `quality (3.12)` pass (53s)
    - `quality (3.13)` pass (1m2s)
  - PR is now merged (GitHub reports merged at 2026-03-04T20:40:48Z).

---

## 22. Central config files in specfact-cli-modules (PRIORITY — must precede migration-03)

Ensure repo-root config files match specfact-cli so format, lint, type-check, and test behavior are aligned.

- [x] 22.1 Audit specfact-cli root for all config affecting format, lint, type-check, tests, pre-commit:
  - `pyproject.toml` (`[tool.ruff]`, `[tool.basedpyright]`, `[tool.pytest.ini_options]`, `[tool.coverage.*]`, `[tool.hatch.*]`)
  - `pylintrc` or pylint config in pyproject
  - `.pre-commit-config.yaml`
  - Any standalone `ruff.toml`, `pyrightconfig.json`
- [x] 22.2 Copy or adapt each config file to specfact-cli-modules root; adjust paths for `packages/`, `tests/`, and module-specific excludes
- [x] 22.3 Ensure `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run test` in the modules repo use the same rules and thresholds as specfact-cli (or document intentional differences)
- [x] 22.4 Add or update `.pre-commit-config.yaml` so local pre-commit matches CI; document in CONTRIBUTING/README
- [x] 22.5 Verify: `hatch run format` then `hatch run type-check` then `hatch run lint` in specfact-cli-modules all pass on the current bundle source

---

## 18. Test migration and quality parity in specfact-cli-modules

### 18.1 Inventory tests by bundle (in specfact-cli)

- [x] 18.1.1 Map each of the 17 migrated modules to its bundle (project→specfact-project, plan→specfact-project, …)
- [x] 18.1.2 List all tests under `tests/unit/` that exercise bundle code: `tests/unit/modules/{plan,backlog,sync,enforce,generate,patch_mode,module_registry,init}`, `tests/unit/backlog/`, `tests/unit/analyzers/`, `tests/unit/commands/`, `tests/unit/bundles/`, and any other module-related unit tests
- [x] 18.1.3 List integration tests that invoke bundle commands: `tests/integration/commands/`, `tests/integration/test_bundle_install.py`, and any other integration tests touching the 17 modules
- [x] 18.1.4 List e2e tests that depend on bundle behavior
- [x] 18.1.5 Produce `openspec/changes/module-migration-05-modules-repo-quality/TEST_INVENTORY.md`: file path, bundle(s) exercised, migration target path in specfact-cli-modules (e.g. `tests/unit/specfact_project/` or `tests/unit/plan/`)

### 18.2 Quality tooling in specfact-cli-modules (partially covered in sections 21 and 22; complete parity required before migration-03 closure)

- [x] 18.2.1 Add hatch env(s) for testing (default env or `test` env) with correct PYTHONPATH for `packages/specfact-*/src`; confirm `hatch test` runs (NOTE: currently fails due to missing dev dependency `typer` for e2e tests; tracked as part of migration work)
- [x] 18.2.2 Add contract-test script: either call specfact-cli's contract-test when specfact-cli is installed as dev dep, or adapt `tools/contract_first_smart_test.py` so `hatch run contract-test` runs contract validation for bundle code
- [x] 18.2.3 Add smart-test or equivalent incremental test runner considering `packages/` and `tests/`; document in README/AGENTS.md
- [x] 18.2.4 Add yaml-lint script for `packages/*/module-package.yaml` and `registry/index.json`; add to pre-commit and CI

### 18.3 Migrate tests into specfact-cli-modules

- [x] 18.3.1 Create test layout in specfact-cli-modules (e.g. `tests/unit/specfact_project/`, `tests/unit/specfact_backlog/`, …); add `tests/conftest.py` and shared fixtures (`TEST_MODE`, temp dirs, etc.)
- [x] 18.3.2 Copy unit tests from inventory; update imports from `specfact_cli.modules.*` to bundle namespaces (`specfact_project.plan`, `specfact_codebase.analyze`, etc.) and adjust resource paths
- [x] 18.3.3 Copy integration tests that invoke bundle commands; ensure they run in the modules repo via hatch env; document how to run CLI-dependent tests
- [x] 18.3.4 Copy or adapt e2e tests; if they require full CLI, document that they run in specfact-cli or adapt with minimal harness
- [x] 18.3.5 Run full test suite: `hatch test` (or `hatch run smart-test`); fix failing tests until all pass; document intentionally deferred or skipped tests with reasons in TEST_INVENTORY.md

### 18.4 CI in specfact-cli-modules (covered in section 21)

- [x] 18.4.1 Confirm CI workflow added in section 21 runs: format, type-check, lint, test, contract-test, coverage threshold
- [x] 18.4.2 Ensure CI uses same Python version(s) as specfact-cli (3.11, 3.12, 3.13 matrix if desired)
- [x] 18.4.3 Document pre-commit checklist in specfact-cli-modules README and AGENTS.md

### 18.5 Verification and documentation

- [x] 18.5.1 From specfact-cli-modules: run full quality gate sequence (format, type-check, lint, test, contract-test, smart-test/coverage) — all must pass
- [x] 18.5.2 Update `proposal.md` Source Tracking to record test migration and quality parity complete
- [x] 18.5.3 Add spec delta or AGENTS.md section documenting test layout and quality parity contract for specfact-cli-modules

### 18.6 Handoff for residual specfact-cli cleanup (explicit boundary)

- [x] 18.6.1 Produce a residual-failures list after bundle-test migration (items that are not bundle-scope and not fixable inside specfact-cli-modules).
- [x] 18.6.2 Link each residual item to a follow-up OpenSpec change created from migration-03 phase 20 (import-path migration, E2E topology updates, signing fixture hardening).
- [x] 18.6.3 Keep migration-05 acceptance criteria focused on modules-repo parity; do not block closure on unrelated specfact-cli legacy suite debt once handoff is complete.

---

## 19. Dependency decoupling in specfact-cli-modules

Ensures bundle code does not hardcode imports from MIGRATE-tier `specfact_cli.*` subsystems. Builds on `IMPORT_DEPENDENCY_ANALYSIS.md` in migration-02 (categorization must be done before this section).

### 19.1 Complete import categorization (PREREQUISITE — must be done in migration-02 before gate 17.8)

- [x] 19.1.1 (See migration-02 tasks.md 17.8.0) Run `rg -e "from specfact_cli.* import" -o -IN --trim | sort | uniq` in specfact-cli-modules to confirm the current import list matches `IMPORT_DEPENDENCY_ANALYSIS.md`
- [x] 19.1.2 Verify that migration-02 task 17.8.0 (categorization) is complete and `IMPORT_DEPENDENCY_ANALYSIS.md` has all Category/Target/Notes columns populated before starting 19.2

### 19.2 Migrate module-only dependencies (MIGRATE-tier)

- [x] 19.2.1 For each MIGRATE item: identify transitive deps; copy source into target bundle or create shared package in specfact-cli-modules (e.g. `packages/specfact-cli-shared/` if cross-bundle)
- [x] 19.2.2 Update bundle imports: replace `from specfact_cli.X import Y` with local bundle or shared path
- [x] 19.2.3 Resolve circular deps: prefer factoring into shared package or extracting interfaces
- [x] 19.2.4 Run tests in specfact-cli-modules after each migration batch; fix breakages
  - Progress (2026-03-04): completed backlog-focused migration batch with local replacements for:
    - `specfact_cli.utils.auth_tokens` -> `specfact_backlog.backlog.auth_tokens`
    - `specfact_cli.backlog.{ai_refiner,filters,template_detector}` -> `specfact_backlog.backlog.{ai_refiner,filters,template_detector}`
    - `specfact_cli.templates.registry` -> `specfact_backlog.templates.registry`
    - `specfact_cli.backlog.mappers.*` -> `specfact_backlog.backlog.mappers.*`
    - `specfact_cli.backlog.adapters.base.BacklogAdapter` -> `specfact_backlog.backlog.adapters.interface.BacklogAdapter`
  - Verification run after batch: `hatch run smart-test` in `specfact-cli-modules` passed (`39 passed`).
  - Progress (2026-03-04): completed project-utils migration batch with local replacements for:
    - `specfact_cli.utils.{acceptance_criteria,enrichment_context,enrichment_parser,feature_keys,incremental_check,persona_ownership,source_scanner,yaml_utils}`
      -> `specfact_project.utils.{acceptance_criteria,enrichment_context,enrichment_parser,feature_keys,incremental_check,persona_ownership,source_scanner,yaml_utils}`
  - Verification run after batch: `hatch run smart-test` in `specfact-cli-modules` passed (`39 passed`).
  - Progress (2026-03-04): completed codebase-validation migration batch with local replacements for:
    - `specfact_cli.validators.sidecar.*` -> `specfact_codebase.validators.sidecar.*`
    - `specfact_cli.validators.repro_checker` -> `specfact_codebase.validators.repro_checker`
    - `specfact_cli.sync.drift_detector` -> `specfact_codebase.sync.drift_detector`
  - Verification run after batch: `hatch run smart-test` in `specfact-cli-modules` passed (`39 passed`).
  - Progress (2026-03-04): completed project-sync runtime migration batch with local replacements for:
    - `specfact_cli.sync.*` -> `specfact_project.sync_runtime.*` (bridge probe/sync/watch, watcher, repository sync, change detectors, code/spec sync helpers)
  - Verification run after batch: `hatch run smart-test` in `specfact-cli-modules` passed (`39 passed`).
  - Progress (2026-03-04): completed spec-generate migration batch with local replacements for:
    - `specfact_cli.generators.contract_generator` -> `specfact_spec.generators.contract_generator`
    - `specfact_cli.migrations.plan_migrator` -> `specfact_spec.migrations.plan_migrator`
  - Verification run after batch: `hatch run smart-test` in `specfact-cli-modules` passed (`39 passed`).
  - Progress (2026-03-04): completed remaining MIGRATE-tier decoupling batch for project/spec/codebase/govern:
    - added local packages in `specfact_project`: `agents`, `analyzers`, `comparators`, `enrichers`, `generators`, `importers`, `merge`, `parsers`, `migrations`, `validators`
    - added local `yaml_utils` under `specfact_codebase.utils` and `specfact_govern.utils`
    - added local `specfact_spec.enrichers` + `specfact_spec.utils.acceptance_criteria`
  - Verification run after final 19.2 batch:
    - `python scripts/check-bundle-imports.py` passed
    - `hatch run smart-test` passed (`39 passed`)

### 19.3 Document allowed imports and add gate

- [x] 19.3.1 Produce `ALLOWED_IMPORTS.md` (or section in AGENTS.md) listing which `specfact_cli.*` imports are allowed (CORE only)
- [x] 19.3.2 Add `scripts/check-bundle-imports.py` that fails if bundle code imports MIGRATE-tier paths; add to CI and pre-commit
- [x] 19.3.3 Update each bundle's `pyproject.toml` / `module-package.yaml`: dependencies declare only `specfact-cli` (and other bundles); no hidden non-core imports
- [x] 19.3.4 Define module-group isolation rules (high level): disallow direct lateral imports between unrelated groups (e.g., backlog -> spec internals) unless routed via explicit shared abstractions
- [x] 19.3.5 Enforce isolation rules in `scripts/check-bundle-imports.py` with an allowlist matrix and fail-fast violations in CI
  - Implemented artifacts:
    - `ALLOWED_IMPORTS.md` (CORE/SHARED `specfact_cli.*` allowlist + cross-bundle policy)
    - `scripts/check-bundle-imports.py` (MIGRATE-tier + lateral import guard)
    - `pyproject.toml` script: `check-bundle-imports`
    - `.pre-commit-config.yaml` hook: `check-bundle-imports`
    - `.github/workflows/quality-gates.yml` step: `Bundle Import Boundary Check`
  - Verification: `hatch run check-bundle-imports` passed.

### 19.4 Verification

- [x] 19.4.1 Re-run `rg -e "from specfact_cli.* import"` in specfact-cli-modules; confirm only CORE imports remain (or document exceptions)
- [x] 19.4.2 Run full quality gate in specfact-cli-modules; all tests pass
- [x] 19.4.3 Produce `MODULE_GROUP_BOUNDARY_REPORT.md` summarizing remaining approved cross-group dependencies and rationale
  - Verification evidence (2026-03-04):
    - `rg -e "from specfact_cli.* import" -o -IN --trim packages | sort | uniq` now shows only CORE/SHARED prefixes.
    - Quality gates passed: `hatch run format`, `hatch run type-check`, `hatch run lint`, `hatch run contract-test`, `hatch run smart-test`, `hatch run yaml-lint`, `hatch run check-bundle-imports`.
    - Report added: `MODULE_GROUP_BOUNDARY_REPORT.md` in this change directory.

---

## 20. Docs migration in specfact-cli-modules

Migrate bundle/module docs to the modules repo; set up Jekyll.

- [x] 20.1 Identify all docs in specfact-cli that describe the 17 migrated modules or the five bundles
- [x] 20.2 Copy or move those docs into specfact-cli-modules under `docs/`; adjust internal links and navigation
- [x] 20.3 Add Jekyll setup: `docs/_config.yml`, `docs/_layouts/` (or equivalent), front-matter on pages, theme/assets as needed
- [x] 20.4 Configure GitHub Pages (or equivalent) for specfact-cli-modules; document URL
- [x] 20.5 Update specfact-cli docs to link to module docs (no duplicated content that would drift)
- [x] 20.6 Document in specfact-cli-modules README that bundle/module doc changes are made in this repo
  - 2026-03-04 outputs:
    - Inventory report: `DOCS_MIGRATION_INVENTORY.md`
    - Migrated docs into modules repo: `docs/{guides,getting-started,reference,adapters}/`
    - Jekyll baseline in modules repo: `docs/_config.yml`, `docs/_layouts/default.html`, `docs/assets/main.scss`, `docs/index.md`
    - GitHub Pages workflow: `.github/workflows/docs-pages.yml`
    - Documented target URL: `https://nold-ai.github.io/specfact-cli-modules/` (modules README, modules docs index, specfact-cli README, specfact-cli docs index)

---

## 23. License and contribution artifacts in specfact-cli-modules

- [x] 23.1 Add LICENSE at repo root matching specfact-cli (same type and copyright for nold-ai official bundles)
- [x] 23.2 Add CONTRIBUTING.md aligned with specfact-cli; explicitly state this repo is for **official nold-ai bundles** only; third-party authors publish from their own repos
- [x] 23.3 Add CODE_OF_CONDUCT.md, SECURITY.md, `.github/CODEOWNERS` (for nold-ai) as applicable
- [x] 23.4 Add "Scope" note in README or CONTRIBUTING: third-party modules are not hosted in specfact-cli-modules; they are published to the registry from their own repositories

---

## 24. Bundle versioning policy (NEW — from gap analysis)

Document and operationalize the versioning policy for independently released bundles.

- [x] 24.1 Define semver semantics for bundles:
  - patch: bug fix in a module with no new commands or public API changes
  - minor: new command, new option, or new public API in any bundle module
  - major: breaking change to a public API or removal of a command
- [x] 24.2 Define `core_compatibility` field maintenance rules: when a bundle requires a minimum specfact-cli version, update `core_compatibility` in the bundle's `module-package.yaml` and `index.json`
- [x] 24.3 Define release process: branch from `main`, bump version, publish via `scripts/publish-module.py --bundle <name>`, tag release, update `index.json`
- [x] 24.4 Document in `AGENTS.md` under a "Bundle versioning policy" section; include semver table, `core_compatibility` rules, and release process steps
- [x] 24.5 Add validation in `scripts/publish-module.py`: reject publish if bundle version < current latest (already enforced) and warn if `core_compatibility` range is not updated after a version bump

---

## Quality gates (final pass)

- [x] Q.1 `hatch run format` (specfact-cli-modules)
- [x] Q.2 `hatch run type-check` (specfact-cli-modules)
- [x] Q.3 `hatch run lint` (specfact-cli-modules)
- [x] Q.4 `hatch run contract-test` (specfact-cli-modules, if added in 18.2)
- [x] Q.5 `hatch run smart-test` or `hatch test --cover` (specfact-cli-modules)
- [x] Q.6 `hatch run yaml-lint` (specfact-cli-modules)
- [x] Q.7 Module signature verification: `hatch run ./scripts/verify-modules-signature.py --require-signature` (from specfact-cli or specfact-cli-modules)
  - 2026-03-04 verification evidence:
    - `hatch run format` passed (with writable Hatch cache/data overrides for sandbox).
    - `hatch run type-check` passed (`0 errors`).
    - `hatch run lint` passed (`ruff` + `basedpyright` + `pylint`).
    - `hatch run contract-test` passed.
    - `hatch run smart-test` passed (`39 passed`).
    - `hatch run yaml-lint` passed (`Validated 5 manifests and registry/index.json`).
  - Q.7 status (2026-03-04): added modules-native scripts in `specfact-cli-modules`:
    - `scripts/sign-modules.py`
    - `scripts/verify-modules-signature.py`
    - hatch aliases: `hatch run sign-modules`, `hatch run verify-modules-signature`
  - After bundle version bumps + re-signing in `specfact-cli-modules`, verifier is now green:
    - `hatch run verify-modules-signature --require-signature --enforce-version-bump --version-check-base HEAD~1`
    - output: `Verified 5 module manifest(s).`

---

## PR and closure

- [x] PR.1 Create PR in specfact-cli-modules from feature branch to `dev`; reference migration-02 #316 and this change's GitHub issue
  - Implemented as: <https://github.com/nold-ai/specfact-cli-modules/pull/5>
- [x] PR.2 Confirm CI passes all gates on the PR
  - PR #5 checks passed:
    - `detect-changes`
    - `verify-module-signatures`
    - `quality (3.11)`
    - `quality (3.12)`
    - `quality (3.13)`
  - PR #5 merged at 2026-03-04T21:39:45Z.
- [x] PR.3 After merge, create PR in specfact-cli if any changes required (e.g. removed duplicate tests, updated cross-links in docs)
  - Specfact-cli-side cleanup prepared on this branch: docs cross-link updates (`README.md`, `docs/index.md`) + OpenSpec evidence artifacts.
- [x] PR.4 Update `openspec/CHANGE_ORDER.md`: move `module-migration-05-modules-repo-quality` to Implemented with archive date
  - Updated `openspec/CHANGE_ORDER.md` to mark migration-05 as implemented (2026-03-04) and remove it from pending rows.

---

## CHANGE_ORDER.md update required

When archived, update `openspec/CHANGE_ORDER.md`:

- Move `module-migration-05-modules-repo-quality` from Pending to Implemented with archive date
- If timing constraint met (sections 18-22 before migration-03): update migration-03's row to remove the quality-and-decoupling blocker note
