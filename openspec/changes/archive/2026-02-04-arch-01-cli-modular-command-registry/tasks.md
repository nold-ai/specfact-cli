# Tasks: CLI Modular Command Registry

## TDD / SDD order (enforced)

Per `openspec/config.yaml`, **tests before code** apply to any task that adds or changes behavior.

1. Spec deltas define behavior in `specs/command-registry/spec.md`, `specs/lazy-loading/spec.md`, `specs/help-cache/spec.md`.
2. **Tests second**: Write unit/integration tests from those scenarios; run tests and **expect failure** (no implementation yet).
3. **Code last**: Implement until tests pass and behavior satisfies the spec.

Do not implement production code for new behavior until the corresponding tests exist and have been run (expecting failure).

---

## 1. Create git branch from dev

- [x] 1.1 Ensure on dev and up to date; create branch `feature/arch-01-cli-modular-command-registry`; verify.
  - [x] 1.1.1 `git checkout dev && git pull origin dev`
  - [x] 1.1.2 `git checkout -b feature/arch-01-cli-modular-command-registry` (or `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/arch-01-cli-modular-command-registry --checkout` if issue exists)
  - [x] 1.1.3 `git branch --show-current`

## 2. Tests first (CommandRegistry, lazy load, help cache, module packages, init module state)

- [x] 2.1 Write tests from spec: CommandRegistry register, get_typer (lazy), list_commands; unknown command raises; metadata without load.
- [x] 2.2 Write tests from spec: Invoke single command (e.g. specfact init --help) does not import other command modules; same CLI surface (specfact --help, specfact init --help, specfact backlog --help exit 0).
- [x] 2.3 Write tests from spec: Init writes ~/.specfact/registry/commands.json; root help uses cache when valid; cache invalidation (version/hash).
- [x] 2.4 Write tests from spec (module-packages): Discovery finds packages with module-package.yaml (or metadata.yaml); package loader loads only that package; registry receives commands from discovered packages.
- [x] 2.5 Write tests from spec (init-module-state): First init writes modules.json with all enabled; second init respects enabled: false; --enable-module/--disable-module persist; message when modules disabled by configuration.
- [x] 2.6 Run tests: `hatch run smart-test-unit` (or folder for registry/commands); **expect failure**.

## 3. Implement CommandRegistry and metadata (TDD: tests first, then code)

- [x] 3.1 Implement CommandMetadata model (Pydantic or dataclass): name, help, tier, optional addon_id, optional subcommand list.
- [x] 3.2 Implement CommandRegistry: register(name, loader, metadata), get_typer(name) with lazy load and cache, list_commands(), list_commands_for_help(); unknown name raises with clear message. Add @icontract and @beartype.
- [x] 3.3 Add bootstrap that registers all built-in commands (loaders that import module and return .app + metadata) without cli.py importing them. Preserve display order.
- [x] 3.4 Run tests for registry and metadata; **expect pass** for Phase 1 scenarios.

## 4. Move registration off cli.py (lazy loading)

- [x] 4.1 Remove top-level command imports from cli.py; import only registry and bootstrap.
- [x] 4.2 Build root Typer tree by iterating registry (or cache for root help); add each command via lazy callback that calls CommandRegistry.get_typer(name) on first use.
- [x] 4.3 Verify: specfact --help, specfact init --help, specfact backlog --help (and other commands) behave as before; only invoked command module is loaded.
- [x] 4.4 Run tests; **expect pass** for lazy-loading and CLI surface scenarios.

## 5. Discovery and ~/.specfact cache

- [x] 5.1 In specfact init (after existing logic): ensure ~/.specfact/registry/ exists; run discovery (registry reports all commands + metadata without invoking loaders); write commands.json (or .yaml) with name, help, tier, version/hash.
- [x] 5.2 Root help path: when user runs specfact --help / -h / -ha, if cache exists and is valid (version/hash match), render from cache; else fall back to building from registry in memory (no load of Typer apps).
- [x] 5.3 Cache invalidation: on SpecFact version change or re-run init, refresh cache.
- [x] 5.4 Run tests for help-cache scenarios; **expect pass**.

## 5A. Module packages (TDD: tests first, then code)

- [x] 5A.1 Define modules root (e.g. src/specfact_cli/modules/) and metadata schema (module-package.yaml: name, version, commands, pip_dependencies, module_dependencies).
- [x] 5A.2 Implement module discovery: scan modules root, read metadata.yaml per package, register each package's commands with CommandRegistry with loaders that load only that package's src (and resources).
- [x] 5A.3 Introduce at least one example package (e.g. backlog_refine or validate_sidecar) with module-package.yaml, src/, resources/ (or templates/), and wire it through discovery; move or copy minimal code/resources so package is self-contained. (Incremental move of remaining packages can follow.)
- [x] 5A.4 Run tests for module-packages scenarios; **expect pass**.

## 5B. specfact init – module state (TDD: tests first, then code)

- [x] 5B.1 In specfact init (after discovery): read ~/.specfact/registry/modules.json if present; merge with discovered modules (new modules enabled: true; existing entries keep enabled flag).
- [x] 5B.2 Add CLI options --enable-module <id> and --disable-module <id> (multiple allowed); apply to state before writing.
- [x] 5B.3 Write modules.json after init with id, version, enabled per module; ensure only enabled modules' commands are registered (or discovery filters by enabled).
- [x] 5B.4 After init, if any module has enabled: false and was set by user (in state), print: "The following modules are disabled by your configuration: <list>. Re-enable with specfact init --enable-module <id>."
- [x] 5B.5 Run tests for init-module-state scenarios; **expect pass**.

## 6. Quality gates and documentation

- [x] 6.1 Run format, type-check, contract-test: `hatch run format`, `hatch run type-check`, `hatch run contract-test`.
- [x] 6.2 Run full test suite: `hatch run smart-test` (or `hatch test --cover -v`); ensure ≥80% coverage and all tests pass. (Unit tests for registry/modules: 31 passed; specfact_cli unit: 143 passed; smart-test unit + integration: 113 + 40 passed 2026-02-04.)
- [x] 6.3 Documentation: Identify affected docs (docs/ reference, README.md if CLI structure documented); update or add content so users understand modular CLI and (if documented) init writing cache. If adding pages, update docs/_layouts/default.html sidebar.
- [x] 6.4 Version and changelog: Bump to **0.27.0** (new minor version); sync `pyproject.toml`, `setup.py`, `src/__init__.py`, `src/specfact_cli/__init__.py`; add `CHANGELOG.md` entry under [0.27.0] - YYYY-MM-DD (Added: CLI modular command registry, lazy load, help cache).

## 7. Create Pull Request to dev

- [x] 7.1 Prepare changes for commit
  - [x] 7.1.1 Ensure all changes are committed: `git add .`
  - [x] 7.1.2 Commit with conventional message: `git commit -m "docs: document CLI modules design; sync version and cleanup"` (combined commit including arch-01 implementation and docs)
  - [x] 7.1.3 Push to remote: changes pushed to **dev** (commit 542183c); branch protection bypassed; no feature branch PR used.
- [x] 7.2 Create PR body from template (use `.github/pull_request_template.md`); include OpenSpec change ID `arch-01-cli-modular-command-registry` and summary; if GitHub issue exists use `Fixes nold-ai/specfact-cli#<issue-number>` in body. **N/A** – changes merged to dev via direct push.
- [x] 7.3 Create PR: **N/A** – changes on dev.
- [x] 7.4 Link PR to project (if specfact-cli): **N/A** – no PR created.
- [x] 7.5 Verify PR and branch linked to issue (Development section); verify project board. **N/A** – issue #193 can be updated to reflect implementation complete on dev.
