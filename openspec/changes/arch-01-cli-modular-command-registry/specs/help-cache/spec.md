# Help Cache (~/.specfact/registry)

## ADDED Requirements

### Requirement: Discovery on specfact init Writes Command Metadata to ~/.specfact

When the user runs **specfact init**, the CLI SHALL run a discovery step that collects all registered commands' metadata (name, help, tier, optional subcommands) and SHALL write this metadata under `~/.specfact/registry/` (e.g. `commands.json` or `commands.yaml`), including a version or hash for cache invalidation.

**Rationale**: Enables fast root help without loading any command module.

#### Scenario: Init Writes Cache

**Given**: User has not run specfact init before (or cache is missing/invalid)

**When**: User runs `specfact init` (with or without subcommand, e.g. `specfact init` or `specfact init cursor`)

**Then**: After init logic runs, discovery runs: registry reports all commands and metadata; result is written to `~/.specfact/registry/commands.json` (or equivalent) with version/hash (e.g. SpecFact version)

**Acceptance Criteria**:

- `~/.specfact` and `~/.specfact/registry/` are created if missing
- File format is deterministic and readable (JSON or YAML)
- Cache includes at least: command names, help strings, optional tier; and a version or hash field for invalidation

#### Scenario: Root Help Uses Cache When Valid

**Given**: Cache exists at `~/.specfact/registry/commands.json` and is valid (e.g. version matches current SpecFact version or hash matches)

**When**: User runs `specfact --help` or `specfact -h` or `specfact --help-advanced` (root level, no subcommand)

**Then**: Root help is rendered from cached metadata without loading any command module; output is consistent with previous behavior (same commands and help strings)

**Acceptance Criteria**:

- If cache exists and is valid, no command module is loaded for root help
- If cache is missing or invalid, fall back to current behavior (e.g. build from registry in memory, which may load metadata only or lazy-load; or show help by iterating registry without loading Typer apps)
- Subcommand help (e.g. `specfact backlog --help`) may still lazy-load that command and use Typer's help

#### Scenario: Cache Invalidation

**Given**: Cache was written by an older SpecFact version or after init

**When**: SpecFact version changes (e.g. upgrade) or user runs `specfact init` again

**Then**: Cache is refreshed (discovery re-run, file overwritten) so root help reflects current commands and version

**Acceptance Criteria**:

- Version or hash in cache file allows comparison with current runtime; if mismatch, treat cache as invalid and refresh on next init or root help
- Running `specfact init` always refreshes cache for current version
