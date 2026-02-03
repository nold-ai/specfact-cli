# Design: CLI Modular Command Registry

## Overview

This change introduces a **CommandRegistry** (analogous to AdapterRegistry) so command groups are registered by name with a loader and metadata. The root Typer app builds its tree from the registry and loads a command module only when that command is invoked (lazy load). On **specfact init**, discovery writes command metadata to `~/.specfact/registry/` so root `--help` can render from cache without loading any command module. No new external systems; integration is with existing cli.py, commands/, and init.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│  Root Typer (cli.py)                                                    │
│  - No top-level command imports                                         │
│  - Knows: command names + order (from registry or cache)                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  specfact --help / -h / -ha  (root)                                     │
│  → Read ~/.specfact/registry/commands.json if valid                     │
│  → Render from cache (no module loads)                                  │
│                                                                         │
│  specfact <cmd> ...  (e.g. specfact init, specfact backlog --help)      │
│  → CommandRegistry.get_typer("<cmd>")  (lazy: load module on first use) │
│  → add_typer / delegate to returned Typer                               │
│  → Only <cmd> module loaded                                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────▼─────────────────────────┐
                    │  CommandRegistry                         │
                    │  - register(name, loader, metadata)      │
                    │  - get_typer(name) → lazy load           │
                    │  - list_commands() / list_commands_...() │
                    │  - CommandMetadata: name, help, tier, …  │
                    └──────────────────────────────────────────┘
                                     │
                    ┌────────────────▼─────────────────────────┐
                    │  specfact init                           │
                    │  - Ensure ~/.specfact/registry/          │
                    │  - Discovery: registry reports all       │
                    │    commands + metadata                   │
                    │  - Write commands.json (version/hash)    │
                    └──────────────────────────────────────────┘
```

## Integration Points

### cli.py

- **Current**: Imports all command modules; calls `app.add_typer(init.app, ...)`, etc. Order fixed in code.
- **Change**: Import only CommandRegistry and a bootstrap that registers built-in commands (loaders + metadata). Root app iterates registry (or reads cache for help) and adds each command via a lazy callback: on first use of a name, call `CommandRegistry.get_typer(name)` and add the returned Typer (or use Click/Typer pattern for lazy command group). No direct import of `specfact_cli.commands.init`, etc.

### commands/ and Built-in Registration

- **Current**: Each command module defines `app = typer.Typer(...)`; cli.py imports and adds them.
- **Change**: A single "register_builtin_commands()" (or equivalent) runs at startup; it registers each built-in by name with a loader (e.g. lambda or importlib wrapper that imports the module and returns `module.app`) and metadata. Loaders are not invoked until `get_typer(name)` is called. Order can be a fixed list of names (e.g. init, auth, backlog, import, …) so display order is preserved.

### AdapterRegistry Pattern

- **Current**: AdapterRegistry has register(type, class), get_adapter(type), list_adapters(), is_registered(type). Built-ins register in `adapters/__init__.py`.
- **Change**: CommandRegistry mirrors this: register(name, loader, metadata), get_typer(name), list_commands(). Built-ins register in one place (e.g. registry module or `commands/__init__.py`) without cli.py importing each command module.

### specfact init

- **Current**: IDE setup, templates, repo .specfact; may create ~/.specfact for first-run detection.
- **Change**: After existing init logic, run discovery: ask registry for all commands and metadata (without invoking loaders); write ~/.specfact/registry/commands.json (or .yaml) with name, help, tier, version/hash. Create ~/.specfact/registry/ if missing.

### Help Path (progressive_disclosure, -ha)

- **Current**: Typer walks full app tree for --help / --help-advanced.
- **Change**: For root only (no subcommand): if cache exists and is valid, render help from cache (same content as today). For `specfact <cmd> --help`, lazy-load <cmd> and delegate to Typer. Progressive disclosure (advanced options) can remain as today for the loaded command.

## Contract Enforcement

- CommandRegistry: @icontract @require/@ensure on register, get_typer, list_commands; @beartype on public API.
- CommandMetadata: Pydantic model or validated dict; no loader invocation when reading metadata.
- Cache file: Validate schema on read; invalid or missing → fall back to building from registry in memory (no load of Typer apps for root help if cache is used; otherwise minimal path).

## Fallback and Offline

- No network required: discovery and cache are local. Cache invalid → re-run discovery on next init or show help from in-memory registry metadata only (if we store metadata without loading Typer, we can list commands and help without loading any command module).
- Offline-first: unchanged.
