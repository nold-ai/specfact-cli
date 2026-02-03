# Change: CLI Modular Command Registry (Dynamic Registration and Lazy Load)

## Why

All CLI command groups are hard-wired in `cli.py` via top-level imports and `app.add_typer(...)`. Adding or reordering a command requires editing `cli.py`, which is a merge-conflict hotspot when multiple features touch the same file. Every command module is imported at startup even when the user runs a single command (e.g. `specfact init`), slowing startup. There is no clean extension point for addons or for gating commands by license (community vs enterprise). A registry-based, lazy-load design—mirroring the existing AdapterRegistry pattern—reduces conflicts, improves performance, and prepares for addons and licensing.

## What Changes

- **NEW**: Introduce **CommandRegistry** (and optional **CommandMetadata** model) with `register(name, loader, metadata)`, `get_typer(name)` (lazy load), `list_commands()`, `list_commands_for_help()`.
- **NEW**: Metadata schema: name, help string, tier (community/enterprise), optional addon_id, optional subcommand list.
- **CHANGE**: **cli.py** no longer imports command modules at top level; it builds the Typer tree from the registry (or cached metadata) and adds commands via a lazy callback that loads only the invoked command.
- **NEW**: On **specfact init**, run discovery: write command metadata to `~/.specfact/registry/` (e.g. `commands.json`) so root `-h` / `--help` / `-ha` / `--help-advanced` can render from cache without loading all command modules.
- **EXTEND** (optional in this change or follow-up): Tier and addon_id in metadata; filter list/help and execution by license.

## Capabilities

- **command-registry**: CommandRegistry with register, get_typer (lazy), list_commands, list_commands_for_help; CommandMetadata model; built-in commands registered via registry (no hard-wiring in cli.py).
- **lazy-loading**: Root app adds command groups by name from registry; only the invoked command module is loaded at runtime.
- **help-cache**: Discovery on specfact init writes ~/.specfact/registry/commands.json; root help uses cache when valid; cache invalidation on version change or init.

## Impact

- **Affected specs**: New `openspec/changes/arch-01-cli-modular-command-registry/specs/command-registry/spec.md`, `specs/lazy-loading/spec.md`, `specs/help-cache/spec.md`.
- **Affected code**: New module (e.g. `src/specfact_cli/registry/` or `src/specfact_cli/commands/registry.py`); refactor of `cli.py` (remove direct command imports, use registry); init command extended to run discovery and write cache.
- **Affected documentation** (<https://docs.specfact.io>): docs/ (reference for CLI structure, addons if added); README.md if CLI behavior is documented.
- **Integration points**: Existing AdapterRegistry pattern (mirror); AgentRegistry; all command modules (each registers with CommandRegistry).
- **Backward compatibility**: CLI names, flags, and behavior remain the same; only loading and help source change. No breaking changes to user-facing CLI.

## Source Tracking

- **GitHub Issue**: #193
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/193>
- **Repository**: nold-ai/specfact-cli
- **Parent epic**: [Architecture](https://github.com/nold-ai/specfact-cli/issues/194) (#194)
- **Last Synced Status**: proposed
