# Tasks: Module Lifecycle Management for Dependencies, Compatibility, and Safe Disable

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. **Spec deltas** define behavior (Given/When/Then) in `openspec/changes/arch-03-module-lifecycle-management/specs/module-lifecycle-management/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last**: Implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git branch from dev

- [x] 1.1 Ensure `dev` is checked out and up to date: `git checkout dev && git pull origin dev`
- [x] 1.2 Create branch linked to issue when available: `gh issue develop 203 --repo nold-ai/specfact-cli --name feature/arch-03-module-lifecycle-management --checkout`
- [x] 1.3 Fallback branch creation when no issue exists: `git checkout -b feature/arch-03-module-lifecycle-management` (not needed; issue-linked branch created)
- [x] 1.4 Verify current branch: `git branch --show-current`

## 2. Create GitHub issue in target repository

- [x] 2.1 Create sanitized issue in `nold-ai/specfact-cli` with labels `enhancement` and `change-proposal`
- [x] 2.2 Use title format `[Change] Module lifecycle management for dependency validation and safe disable`
- [x] 2.3 Update `proposal.md` Source Tracking with issue number, URL, repository, and status `proposed`

## 3. Finalize spec delta (SDD)

- [x] 3.1 Confirm `specs/module-lifecycle-management/spec.md` covers dependency validation, compatibility checks, safe-disable behavior, and boundary guard expectations
- [x] 3.2 Map each scenario to test tasks before implementation tasks

## 4. Tests first for lifecycle behavior (TDD)

- [x] 4.1 Add/update registry tests for dependency validation and safe-disable reverse dependency logic (expect failure before implementation)
- [x] 4.2 Add/update version compatibility tests for `core_compatibility` parsing and boundary ranges (expect failure before implementation)
- [x] 4.3 Add/update tests for extracted bundle converter helpers and constitution minimality utility (expect failure before implementation)
- [x] 4.4 Add/update boundary guard tests preventing cross-module non-`app` imports from `src.commands` (expect failure before implementation)

## 5. Implement shared helper extraction

- [x] 5.1 Create `src/specfact_cli/utils/bundle_converters.py` with conversion and constitution helpers plus contracts
- [x] 5.2 Redirect imports in sync/generate/enforce to core utility helpers
- [x] 5.3 Replace plan/sdd helper implementations with compatibility delegates where needed
- [x] 5.4 Re-run targeted tests for helper extraction changes

## 6. Implement manifest and registry lifecycle validation

- [x] 6.1 Extend module manifest model and parsing with optional `core_compatibility`
- [x] 6.2 Add `core_compatibility` to all module manifests and reconcile `module_dependencies` updates
- [x] 6.3 Add registry checks for compatibility and dependency validation before command registration
- [x] 6.4 Ensure skipped modules are debug-logged with clear reasons

## 7. Implement safe-disable behavior in init

- [x] 7.1 Add reverse dependency utility and disable validation helper
- [x] 7.2 Add init command guard that blocks unsafe disable with actionable message
- [x] 7.3 Add `--force` override support and verify behavior parity

## 8. Quality gates

- [x] 8.1 Run formatting and linting checks: `hatch run format` and `hatch run lint`
- [x] 8.2 Run strict type checks: `hatch run type-check`
- [x] 8.3 Run contract-first validation: `hatch run contract-test`
- [x] 8.4 Run scenario-relevant tests and full suite as required: `hatch run smart-test` and/or `hatch test --cover -v`
- [x] 8.5 Verify all module command helps resolve after changes

## 9. Documentation research and review

- [x] 9.1 Identify affected docs in `docs/`, `docs/index.md`, and `README.md` for module lifecycle behavior
- [x] 9.2 Update/add user-facing docs for manifest `core_compatibility`, dependency enforcement, and safe-disable semantics
- [x] 9.3 If pages are added/moved, update front-matter and `docs/_layouts/default.html` sidebar links (N/A: no pages added or moved)

## 10. Version and changelog

- [x] 10.1 Bump version according to semver impact and sync in `pyproject.toml`, `setup.py`, `src/__init__.py`, and `src/specfact_cli/__init__.py`
- [x] 10.2 Add `CHANGELOG.md` entry for lifecycle validation and safe-disable behavior

## 11. Create Pull Request to dev (last)

- [ ] 11.1 Commit with conventional commit message
- [ ] 11.2 Push branch: `git push origin feature/arch-03-module-lifecycle-management`
- [ ] 11.3 Create PR to `dev` using repository template and include `Fixes nold-ai/specfact-cli#<issue-number>`
- [ ] 11.4 Verify issue Development links include branch and PR

## 12. Extend module lifecycle UX for listing and interactive selection

- [x] 12.1 Add tests first for `specfact init --list-modules` effective enabled/disabled output
- [x] 12.2 Add tests first for interactive up/down selection flow for enable/disable when ids are not passed
- [x] 12.3 Add tests first for non-interactive validation requiring explicit module ids
- [x] 12.4 Implement `--list-modules` in init command with effective merged state output
- [x] 12.5 Implement interactive module selection using questionary for enable/disable requests without explicit ids
- [x] 12.6 Implement non-interactive guardrail error messaging for id-less enable/disable requests
- [x] 12.7 Run focused tests for new module UX behavior

## 13. Split init bootstrap from IDE setup

- [x] 13.1 Add `init ide` command for prompt/template copy and IDE settings update behavior
- [x] 13.2 Keep top-level `init` bootstrap/module-management only (no template copy side effects)
- [x] 13.3 Add prompt status audit messaging in bootstrap init with guidance to run `specfact init ide`
- [x] 13.4 Add interactive IDE selection (questionary up/down) when `init ide` runs without `--ide`
- [x] 13.5 Update tests to target `init ide` for template copy behavior and keep bootstrap-init regression coverage

## 14. Force-mode dependency cascade

- [x] 14.1 In `--force` disable flows, cascade-disable enabled dependents transitively
- [x] 14.2 In `--force` enable flows, cascade-enable required dependencies transitively
- [x] 14.3 Add regression tests for both force-mode cascades in registry/init lifecycle tests
