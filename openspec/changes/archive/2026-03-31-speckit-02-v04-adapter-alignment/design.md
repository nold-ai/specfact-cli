## Context

The `SpecKitAdapter` (in `src/specfact_cli/adapters/speckit.py`) was built when spec-kit had a simple layout: `specs/` or `.specify/specs/` directories containing `spec.md`, `plan.md`, `tasks.md`, and an optional `.specify/memory/constitution.md`. The adapter detects these directories, delegates parsing to `SpecKitScanner`, conversion to `SpecKitConverter`, and exposes `ToolCapabilities` with `version=None` and two sync modes.

Spec-Kit v0.4.3 now has:

- 7+ slash commands (was 4)
- 46 community extensions with their own commands, loaded from `extensions/catalog.community.json`
- A pluggable preset system in `presets/` with catalog resolution (v0.3.0+)
- Hook events (before/after task completion) wired into templates
- `specify status --json` and `specify doctor` for version/health reporting
- Auto-registered AI skills with native fallback
- `.extensionignore` for extension exclusion

The adapter, scanner, capabilities model, and bridge config presets all need updates to model this expanded surface area.

## Goals / Non-Goals

**Goals:**

- Detect and model spec-kit extensions installed in a target repository
- Parse extension catalogs to expose extension-provided commands to SpecFact sync
- Detect spec-kit version via CLI probe or directory heuristics
- Detect active preset configuration and adjust artifact mappings
- Expand `ToolCapabilities` with extension, preset, and hook metadata
- Expand `BridgeConfig` command mappings for all 7 spec-kit slash commands
- Maintain backward compatibility with repos using older spec-kit versions (pre-0.3.0)

**Non-Goals:**

- Executing spec-kit extensions from SpecFact (we detect and model, not invoke)
- Managing spec-kit presets (read-only detection)
- Replacing spec-kit's own sync/reconcile extensions (we coordinate, not compete)
- Adding spec-kit CLI as a hard dependency

## Decisions

### D1: Extension catalog detection via filesystem only

Parse `extensions/catalog.community.json` and `extensions/catalog.core.json` as JSON files from the repo. Do not invoke `specify` CLI commands to list extensions.

**Rationale**: Offline-first constraint. The CLI may not be installed. Extension catalogs are static JSON files committed to the repo. This also avoids subprocess overhead during detection.

**Alternative considered**: Invoking `specify status --json` to get active extensions. Rejected because it requires the CLI to be installed and doesn't work for cross-repo detection where only the filesystem is available.

### D2: Version detection with graceful degradation

Three-tier version detection strategy:

1. **CLI probe** (best): Run `specify --version` if CLI is on PATH — returns exact version
2. **Directory heuristics** (good): `presets/` dir → `>=0.3.0`; `extensions/` dir → `>=0.2.0`; `.specify/` dir only → `>=0.1.0`
3. **Unknown** (fallback): `version=None` — same as today, no features gated

**Rationale**: CLI probe is most accurate but optional. Heuristics cover cross-repo and offline scenarios. The fallback preserves backward compatibility.

**Alternative considered**: Parsing a version file inside `.specify/`. Rejected because spec-kit does not write a version marker file.

### D3: ToolCapabilities extension via optional typed fields

Add optional fields to the existing `ToolCapabilities` dataclass rather than creating a subclass:

```python
@dataclass
class ToolCapabilities:
    tool: str
    version: str | None = None
    layout: str = "classic"
    specs_dir: str = "specs"
    has_external_config: bool = False
    has_custom_hooks: bool = False
    supported_sync_modes: list[str] | None = None
    # New fields (v0.4.x alignment)
    extensions: list[str] | None = None          # Detected extension names
    extension_commands: dict[str, list[str]] | None = None  # Extension → commands mapping
    presets: list[str] | None = None             # Active preset names
    hook_events: list[str] | None = None         # Detected hook event types
    detected_version_source: str | None = None   # "cli", "heuristic", or None
```

**Rationale**: Single dataclass keeps the adapter interface simple. Optional fields with `None` defaults mean no breaking changes for other adapters. The `detected_version_source` field lets downstream code know how reliable the version info is.

**Alternative considered**: SpecKit-specific subclass `SpecKitCapabilities(ToolCapabilities)`. Rejected because it forces adapter-specific type checks in generic sync code.

### D4: BridgeConfig presets expanded incrementally

Add the 5 missing command mappings to all 3 existing presets (`classic`, `specify`, `modern`). Each preset gets the same command set; only artifact paths differ.

```python
commands = {
    "specify": CommandMapping(trigger="/speckit.specify", input_ref="specification"),
    "plan": CommandMapping(trigger="/speckit.plan", input_ref="specification", output_ref="plan"),
    "tasks": CommandMapping(trigger="/speckit.tasks", input_ref="plan", output_ref="tasks"),
    "implement": CommandMapping(trigger="/speckit.implement", input_ref="tasks"),
    "constitution": CommandMapping(trigger="/speckit.constitution", output_ref="constitution"),
    "clarify": CommandMapping(trigger="/speckit.clarify", input_ref="specification"),
    "analyze": CommandMapping(trigger="/speckit.analyze", input_ref="specification"),
}
```

**Rationale**: All presets share the same slash commands; only directory layouts differ. Adding commands to existing presets is additive and non-breaking.

### D5: Extension-provided commands stored separately from core commands

Extension commands (e.g., `/speckit.reconcile.run`, `/speckit.sync.detect`) are stored in `ToolCapabilities.extension_commands` rather than mixed into `BridgeConfig.commands`. This separation lets sync code distinguish between spec-kit core commands and extension commands.

**Rationale**: Extension commands are optional and vary per installation. Mixing them into BridgeConfig presets would require dynamic preset generation. Keeping them in capabilities allows the sync kernel to query "does this repo have the reconcile extension?" without modifying bridge config.

### D6: Scanner detects new directories without requiring spec-kit CLI

`SpecKitScanner` adds detection for:

- `extensions/` directory → extension catalog files
- `presets/` directory → preset catalog files
- `.extensionignore` → extension exclusion rules

All detection is filesystem-based. The scanner returns structured metadata that `SpecKitAdapter.get_capabilities()` consumes.

## Risks / Trade-offs

- **[Spec-kit schema instability]** Extension catalog JSON format may change between spec-kit versions → **Mitigation**: Parse defensively with fallback to empty list. Log warnings for unrecognized fields. Pin to known schema keys (`name`, `commands`, `version`).
- **[CLI probe latency]** Running `specify --version` adds subprocess overhead to detection → **Mitigation**: CLI probe is opt-in, triggered only when `ToolCapabilities.version` is explicitly requested or when version-gated features are needed. Cached per session.
- **[Cross-repo extension detection]** Extensions may be installed in a different location than specs → **Mitigation**: Always look for `extensions/` relative to the same base path as `.specify/`. Cross-repo configs pass `external_base_path` which is used consistently.
- **[Backward compatibility]** Repos with old spec-kit (pre-0.2.0) have no `extensions/` or `presets/` → **Mitigation**: All new fields default to `None`. Detection logic is additive — old repos work exactly as before.

## Open Questions

- Should we cache extension catalog parsing results across multiple adapter calls in the same CLI session? (Likely yes, but deferred to implementation.)
- Should `ToolCapabilities.extensions` include disabled extensions (from `.extensionignore`)? (Proposed: no — only report active extensions.)
