# Tasks: CLI Modular Command Registry

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. Spec deltas define behavior in `specs/command-registry/spec.md`, `specs/lazy-loading/spec.md`, `specs/help-cache/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last**: Implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git branch from dev

- [ ] 1.1 Ensure on dev and up to date; create branch `feature/arch-01-cli-modular-command-registry`; verify.
  - [ ] 1.1.1 `git checkout dev && git pull origin dev`
  - [ ] 1.1.2 `git checkout -b feature/arch-01-cli-modular-command-registry` (or `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/arch-01-cli-modular-command-registry --checkout` if issue exists)
  - [ ] 1.1.3 `git branch --show-current`

## 2. Tests first (CommandRegistry, lazy load, help cache)

- [ ] 2.1 Write tests from spec: CommandRegistry register, get_typer (lazy), list_commands; unknown command raises; metadata without load.
- [ ] 2.2 Write tests from spec: Invoke single command (e.g. specfact init --help) does not import other command modules; same CLI surface (specfact --help, specfact init --help, specfact backlog --help exit 0).
- [ ] 2.3 Write tests from spec: Init writes ~/.specfact/registry/commands.json; root help uses cache when valid; cache invalidation (version/hash).
- [ ] 2.4 Run tests: `hatch run smart-test-unit` (or folder for registry/commands); **expect failure**.

## 3. Implement CommandRegistry and metadata (TDD: tests first, then code)

- [ ] 3.1 Implement CommandMetadata model (Pydantic or dataclass): name, help, tier, optional addon_id, optional subcommand list.
- [ ] 3.2 Implement CommandRegistry: register(name, loader, metadata), get_typer(name) with lazy load and cache, list_commands(), list_commands_for_help(); unknown name raises with clear message. Add @icontract and @beartype.
- [ ] 3.3 Add bootstrap that registers all built-in commands (loaders that import module and return .app + metadata) without cli.py importing them. Preserve display order.
- [ ] 3.4 Run tests for registry and metadata; **expect pass** for Phase 1 scenarios.

## 4. Move registration off cli.py (lazy loading)

- [ ] 4.1 Remove top-level command imports from cli.py; import only registry and bootstrap.
- [ ] 4.2 Build root Typer tree by iterating registry (or cache for root help); add each command via lazy callback that calls CommandRegistry.get_typer(name) on first use.
- [ ] 4.3 Verify: specfact --help, specfact init --help, specfact backlog --help (and other commands) behave as before; only invoked command module is loaded.
- [ ] 4.4 Run tests; **expect pass** for lazy-loading and CLI surface scenarios.

## 5. Discovery and ~/.specfact cache

- [ ] 5.1 In specfact init (after existing logic): ensure ~/.specfact/registry/ exists; run discovery (registry reports all commands + metadata without invoking loaders); write commands.json (or .yaml) with name, help, tier, version/hash.
- [ ] 5.2 Root help path: when user runs specfact --help / -h / -ha, if cache exists and is valid (version/hash match), render from cache; else fall back to building from registry in memory (no load of Typer apps).
- [ ] 5.3 Cache invalidation: on SpecFact version change or re-run init, refresh cache.
- [ ] 5.4 Run tests for help-cache scenarios; **expect pass**.

## 6. Quality gates and documentation

- [ ] 6.1 Run format, type-check, contract-test: `hatch run format`, `hatch run type-check`, `hatch run contract-test`.
- [ ] 6.2 Run full test suite: `hatch run smart-test` (or `hatch test --cover -v`); ensure ≥80% coverage and all tests pass.
- [ ] 6.3 Documentation: Identify affected docs (docs/ reference, README.md if CLI structure documented); update or add content so users understand modular CLI and (if documented) init writing cache. If adding pages, update docs/_layouts/default.html sidebar.
- [ ] 6.4 Version and changelog: Bump minor version (refactor/feature); sync pyproject.toml, setup.py, src/**init**.py, src/specfact_cli/**init**.py; add CHANGELOG.md entry under new [X.Y.Z] - YYYY-MM-DD (Added: CLI modular command registry, lazy load, help cache).

## 7. Create Pull Request to dev

- [ ] 7.1 Prepare changes for commit
  - [ ] 7.1.1 Ensure all changes are committed: `git add .`
  - [ ] 7.1.2 Commit with conventional message: `git commit -m "feat: CLI modular command registry and lazy load (arch-01)"`
  - [ ] 7.1.3 Push to remote: `git push origin feature/arch-01-cli-modular-command-registry`
- [ ] 7.2 Create PR body from template (use `.github/pull_request_template.md`); include OpenSpec change ID `arch-01-cli-modular-command-registry` and summary; if GitHub issue exists use `Fixes nold-ai/specfact-cli#<issue-number>` in body.
- [ ] 7.3 Create PR: `gh pr create --repo nold-ai/specfact-cli --base dev --head feature/arch-01-cli-modular-command-registry --title "feat: CLI modular command registry and lazy load (arch-01)" --body-file <body-file>`
- [ ] 7.4 Link PR to project (if specfact-cli): `gh project item-add 1 --owner nold-ai --url <PR_URL>`; verify Development link on issue; update project status if applicable.
- [ ] 7.5 Verify PR and branch linked to issue (Development section); verify project board.
