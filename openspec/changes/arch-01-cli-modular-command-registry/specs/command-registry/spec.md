# Command Registry

## ADDED Requirements

### Requirement: CommandRegistry with Lazy Load

The CLI SHALL provide a **CommandRegistry** that registers command groups by name with a loader and metadata, and resolves the Typer app only when requested (lazy load).

**Rationale**: Enables modular command registration without importing all command modules at startup; mirrors AdapterRegistry pattern.

#### Scenario: Register and Resolve Command

**Given**: CommandRegistry is initialized and a command "init" is registered with a loader (callable returning typer.Typer) and metadata (name, help, tier)

**When**: Code calls `CommandRegistry.get_typer("init")`

**Then**: The loader is invoked (if not already cached), the Typer app for "init" is returned, and subsequent calls for "init" return the same instance (or same Typer) without re-importing

**Acceptance Criteria**:

- `register(name, loader, metadata)` stores entry without invoking loader
- `get_typer(name)` invokes loader on first use and returns typer.Typer
- `list_commands()` returns all registered command names in registration order (or configured order)
- `list_commands_for_help()` returns names (and optional metadata) for help display; MAY be filtered by tier/license when implemented

#### Scenario: Unknown Command

**Given**: CommandRegistry has no entry for "unknown-cmd"

**When**: Code calls `CommandRegistry.get_typer("unknown-cmd")`

**Then**: A clear error is raised (e.g. ValueError or KeyError) with message listing registered commands or suggesting typo

**Acceptance Criteria**:

- No silent failure; caller can distinguish "not registered" from "load failed"

---

### Requirement: CommandMetadata Model

The CLI SHALL support a **CommandMetadata** model (or equivalent dict schema) with at least: name, help string, tier (e.g. community | enterprise), optional addon_id, optional subcommand list.

**Rationale**: Enables discovery, cached help, and future licensing without loading modules.

#### Scenario: Metadata Available Without Loading Module

**Given**: A command "backlog" is registered with metadata (help="Backlog refinement and template management", tier="community")

**When**: Code calls `CommandRegistry.get_metadata("backlog")` or equivalent (or metadata is returned by list_commands_for_help)

**Then**: Metadata is returned without invoking the command's loader

**Acceptance Criteria**:

- Metadata is stored at registration time
- Accessing metadata does not trigger module load
