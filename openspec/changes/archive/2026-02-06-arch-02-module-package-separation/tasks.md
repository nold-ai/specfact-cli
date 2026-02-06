# Tasks: Module Package Separation for Command Implementations

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. **Spec deltas** define behavior (Given/When/Then) in `openspec/changes/arch-02-module-package-separation/specs/module-package-separation/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last**: Implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git branch from dev

- [x] 1.1 Ensure we're on `dev` and up to date: `git checkout dev && git pull origin dev`
- [x] 1.2 Create branch with Development link to issue (if issue exists): `gh issue develop 199 --repo nold-ai/specfact-cli --name feature/arch-02-module-package-separation --checkout`
- [x] 1.3 Or create branch without issue link: `git checkout -b feature/arch-02-module-package-separation` (if no issue yet)
- [x] 1.4 Verify branch was created: `git branch --show-current`

## 2. Create GitHub issue in nold-ai/specfact-cli (mandatory for public repo)

- [x] 2.1 Create sanitized issue: `gh issue create --repo nold-ai/specfact-cli --title "[Change] Module package separation for command implementations" --body-file <path> --label "enhancement" --label "change-proposal"`
- [x] 2.2 Use proposal content for Why/What Changes and add footer `*OpenSpec Change Proposal: arch-02-module-package-separation*`
- [x] 2.3 Confirm `proposal.md` Source Tracking section references issue `#199`, URL `https://github.com/nold-ai/specfact-cli/issues/199`, repository, and Last Synced Status `proposed`
- [x] 2.4 Optionally link issue to project board: `gh project item-add 1 --owner nold-ai --url <issue-url>`

## 3. Verify spec deltas (SDD: specs first)

- [x] 3.1 Confirm `specs/module-package-separation/spec.md` exists and covers migration behavior, compatibility shims, phased execution, and verification.
- [x] 3.2 Map each scenario to concrete implementation and test tasks before touching command code.

## 4. Tests first (TDD: write tests from spec scenarios; expect failure)

- [x] 4.1 Add/update tests derived from spec scenarios for migrated modules: module-local app wiring, backward-compatible imports from `src/specfact_cli/commands/*`, and module discovery behavior.
- [x] 4.2 Run targeted tests and expect failures before migration code is updated. (Retrospective note: migration already implemented; targeted scenario tests executed and documented in `TEST_SCENARIO_MAPPING.md`.)
- [x] 4.3 Document test-to-scenario mapping for each migrated module wave.

## 5. Build compatibility map before migration waves

- [x] 5.1 Inventory all non-`app` imports from `specfact_cli.commands.*` in `src/` and `tests/` (current baseline: 35 files).
- [x] 5.2 For each imported symbol, decide migration target: temporary shim re-export, move to shared core module, or direct module-local import.
- [x] 5.3 Add regression tests for symbol-level compatibility for migrated modules (not only CLI command `app` entrypoints).

## 6. Implement Tier 1 migration wave (small modules first)

- [x] 6.1 Migrate Tier 1 modules (`drift`, `upgrade`, `validate`, `sdd`) by moving command logic to `src/specfact_cli/modules/<name>/src/commands.py` and adding module-local `src/__init__.py`.
- [x] 6.2 Update `src/specfact_cli/modules/<name>/src/app.py` to import `app` from local `commands`.
- [x] 6.3 Replace legacy files in `src/specfact_cli/commands/` with backward-compatible shims that re-export `app` plus any still-used legacy symbols for that module.
- [x] 6.4 Re-run targeted tests for Tier 1 and fix failures.

## 7. Implement Tier 2 migration wave

- [x] 7.1 Migrate Tier 2 modules (`auth`, `repro`, `enforce`, `migrate`, `spec`, `init`) using the same move/update/shim pattern.
- [x] 7.2 Verify any module-specific test relocations to module package test directories where appropriate.
- [x] 7.3 Re-run targeted tests for Tier 2 and fix failures.

## 8. Implement Tier 3 and Tier 4 migration waves

- [x] 8.1 Migrate Tier 3 modules (`contract`, `project`, `generate`, `sync`, `backlog`, `import_cmd`) with the same pattern.
- [x] 8.2 Migrate Tier 4 module (`plan`) last after validating prior wave stability.
- [x] 8.3 Keep `module_dependencies` in each `module-package.yaml` accurate if any cross-module dependency is introduced.
- [x] 8.4 Re-run targeted tests for Tier 3/4 and fix failures.

## 9. Decouple cross-command dependencies

- [x] 9.1 Extract shared helper symbols currently imported from command modules into stable shared packages (for example under `src/specfact_cli/utils/` or `src/specfact_cli/shared/`).
- [x] 9.2 Update `src/` and `tests/` imports to stop relying on `specfact_cli.commands.*` for non-`app` symbols.
- [x] 9.3 Reduce shim exports module-by-module as dependents are migrated; keep only compatibility exports still needed.
- [x] 9.4 Add/enable boundary checks so new non-`app` imports from `specfact_cli.commands.*` fail CI.

## 10. Quality gates

- [x] 10.1 Run formatting and static checks: `hatch run format`, `hatch run lint`, `hatch run type-check`. (`format` and `type-check` pass; `lint` currently advisory in CI via `.github/workflows/pr-orchestrator.yml`.)
- [x] 10.2 Run contract-first validation: `hatch run contract-test`.
- [x] 10.3 Run full or smart test suite: `hatch run smart-test`.
- [x] 10.4 Verify command UX remains stable by checking representative help paths: `specfact <command> --help` across migrated modules.
- [x] 10.5 Verify non-`app` imports from `specfact_cli.commands.*` are reduced versus baseline and tracked toward zero.

## 11. Documentation research and review

- [x] 11.1 Identify affected docs: `README.md`, `AGENTS.md`, and any docs pages that describe command implementation locations or module architecture.
- [x] 11.2 Update docs to reflect module-local command implementations and compatibility shim policy.
- [x] 11.3 Document deprecation timeline for non-`app` command-module imports and expected replacement import paths.
- [x] 11.4 If docs pages are added or moved, ensure front-matter and sidebar updates in `docs/_layouts/default.html`. (No docs pages were added/moved in this change.)

## 12. Version and changelog (required before PR)

- [x] 12.1 Bump version per semver for this architectural feature and sync versions in `pyproject.toml`, `setup.py`, `src/__init__.py`, and `src/specfact_cli/__init__.py`.
- [x] 12.2 Add `CHANGELOG.md` entry describing module package separation and compatibility behavior.

## 13. Create Pull Request to dev (last)

- [x] 13.1 Commit all changes with conventional commit message(s).
- [x] 13.2 Push branch: `git push origin feature/arch-02-module-package-separation`.
- [x] 13.3 Create PR to `dev` using repository template and include OpenSpec reference plus issue linkage (`Fixes nold-ai/specfact-cli#199`).
- [x] 13.4 Verify issue Development section links branch and PR. (Verified via PR cross-reference on issue #199 with head branch `feature/arch-02-module-package-separation`.)
