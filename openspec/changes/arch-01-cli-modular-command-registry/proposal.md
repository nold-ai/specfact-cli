# Change: CLI Modular Command Registry (Dynamic Registration and Lazy Load)

## Why

All CLI command groups are hard-wired in `cli.py` via top-level imports and `app.add_typer(...)`. Adding or reordering a command requires editing `cli.py`, which is a merge-conflict hotspot when multiple features touch the same file. Every command module is imported at startup even when the user runs a single command (e.g. `specfact init`), slowing startup. There is no clean extension point for addons or for gating commands by license (community vs enterprise). A registry-based, lazy-load design—mirroring the existing AdapterRegistry pattern—reduces conflicts, improves performance, and prepares for addons and licensing. **Logical packaging by feature** (e.g. "backlog refine", "backlog daily", "validate sidecar") with related resources (prompts, templates) in each package prepares for an extensible ecosystem and future selective install without blocking it in this refactor.

## What Changes

- **NEW**: Introduce **CommandRegistry** (and optional **CommandMetadata** model) with `register(name, loader, metadata)`, `get_typer(name)` (lazy load), `list_commands()`, `list_commands_for_help()`.
- **NEW**: Metadata schema: name, help string, tier (community/enterprise), optional addon_id, optional subcommand list.
- **CHANGE**: **cli.py** no longer imports command modules at top level; it builds the Typer tree from the registry (or cached metadata) and adds commands via a lazy callback that loads only the invoked command.
- **NEW**: On **specfact init**, run discovery: write command metadata to `~/.specfact/registry/` (e.g. `commands.json`) so root `-h` / `--help` / `-ha` / `--help-advanced` can render from cache without loading all command modules.
- **NEW**: **Logical module packages**: Group code and resources by feature (not only by command group). Each package has a dedicated folder with `metadata.yaml` (name, version, pip_dependencies, module_dependencies, commands), `src/`, `resources/` (prompts, templates), `tests/`. Core vs package grouping; resources used only by one feature live in that package.
- **NEW**: **Module discovery**: Scan modules root, read package metadata, register packages with registry; loaders load only that package’s src and resources.
- **NEW**: **specfact init** module state: Discover all modules; enable all by default; store `~/.specfact/registry/modules.json` with per-module version and enabled/disabled; support `--enable-module` / `--disable-module`; on next init respect manual deselection and inform user when modules are disabled by configuration.
- **EXTEND** (optional in this change or follow-up): Tier and addon_id in metadata; filter list/help and execution by license. **Out of scope for this phase**: selective install and GitHub delivery with checksums; layout and metadata must not conflict with adding that later.

## Capabilities

- **command-registry**: CommandRegistry with register, get_typer (lazy), list_commands, list_commands_for_help; CommandMetadata model; built-in commands registered via registry (no hard-wiring in cli.py).
- **lazy-loading**: Root app adds command groups by name from registry; only the invoked command module is loaded at runtime.
- **help-cache**: Discovery on specfact init writes ~/.specfact/registry/commands.json; root help uses cache when valid; cache invalidation on version change or init.
- **module-packages**: Logical packages per feature (e.g. backlog-refine, backlog-daily, validate-sidecar) with folder structure (module-package.yaml, src/, resources/, tests/); discovery loads metadata and registers packages; design does not block future selective install.
- **init-module-state**: specfact init discovers modules, enables all by default, writes modules.json (version, enabled); --enable-module/--disable-module; persist overrides and inform user when modules are disabled by configuration.

## Impact

- **Affected specs**: (new) command-registry, lazy-loading, help-cache, module-packages, init-module-state.
- **Affected code**: `cli.py`, `src/specfact_cli/registry/`, `src/specfact_cli/commands/` (or modules/), `specfact init` command, docs.
- **Integration points**: Typer app construction, init flow, future addon/package discovery.
- **Release version**: This change is released as a **new minor version**: **0.27.0** (SemVer minor: new feature/refactor, backward compatible).

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #193
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/193>
- **Last Synced Status**: proposed
<!-- content_hash: 59a4c9bb737b870c -->
