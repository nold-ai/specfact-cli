# SpecFact Sync Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Synchronize artifacts from external tools (e.g., Spec-Kit, Linear, Jira) with SpecFact project bundles using configurable bridge mappings. Supports bidirectional sync for team collaboration.

**When to use:**

- Syncing with Spec-Kit projects
- Integrating with external planning tools
- Maintaining consistency across tool ecosystems

**Quick Example:**

```bash
/specfact.06-sync --adapter speckit --repo . --bidirectional
/specfact.06-sync --adapter speckit --bundle legacy-api --watch
```

## Parameters

### Target/Input

- `--repo PATH` - Path to repository. Default: current directory (.)
- `--bundle NAME` - Project bundle name for SpecFact → tool conversion. Default: auto-detect

### Behavior/Options

- `--bidirectional` - Enable bidirectional sync (tool ↔ SpecFact). Default: False
- `--overwrite` - Overwrite existing tool artifacts. Default: False
- `--watch` - Watch mode for continuous sync. Default: False
- `--ensure-compliance` - Validate and auto-enrich for tool compliance. Default: False

### Advanced/Configuration

- `--adapter TYPE` - Adapter type (speckit, generic-markdown). Default: auto-detect
- `--interval SECONDS` - Watch interval in seconds. Default: 5 (range: 1+)

## Workflow

### Step 1: Parse Arguments

- Extract repository path (default: current directory)
- Extract adapter type (default: auto-detect)
- Extract sync options (bidirectional, overwrite, watch, etc.)

### Step 2: Execute CLI

```bash
# Bidirectional sync
specfact sync bridge --adapter <adapter> --repo <path> --bidirectional [--bundle <name>] [--overwrite] [--watch]

# One-way sync (Spec-Kit → SpecFact)
specfact sync bridge --adapter speckit --repo <path> [--bundle <name>]

# Watch mode
specfact sync bridge --adapter speckit --repo <path> --watch --interval 5
```

### Step 3: Present Results

- Display sync direction and adapter used
- Show artifacts synchronized
- Present conflict resolution (if any)
- Indicate watch status (if enabled)

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

1. **ALWAYS execute CLI first**: Run `specfact sync bridge` before any sync operation
2. **ALWAYS use non-interactive mode for CI/CD**: Use appropriate flags in Copilot environments
3. **NEVER modify .specfact or .specify folders directly**: All operations must go through CLI
4. **NEVER create YAML/JSON directly**: All sync operations must be CLI-generated
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate it

## Expected Output

### Success

```text
✓ Sync complete: Spec-Kit ↔ SpecFact (bidirectional)

Adapter: speckit
Repository: /path/to/repo

Artifacts Synchronized:
  - Spec-Kit → SpecFact: 12 features, 45 stories
  - SpecFact → Spec-Kit: 3 new features, 8 updated stories

Conflicts Resolved: 2
```

### Error (Missing Adapter)

```text
✗ Unsupported adapter: invalid-adapter
Supported adapters: speckit, generic-markdown
```

## Common Patterns

```bash
# Bidirectional sync with Spec-Kit
/specfact.06-sync --adapter speckit --repo . --bidirectional

# One-way sync (Spec-Kit → SpecFact)
/specfact.06-sync --adapter speckit --repo . --bundle legacy-api

# Watch mode for continuous sync
/specfact.06-sync --adapter speckit --repo . --watch --interval 5

# Sync with overwrite
/specfact.06-sync --adapter speckit --repo . --bidirectional --overwrite

# Auto-detect adapter
/specfact.06-sync --repo . --bidirectional
```

## Context

{ARGS}
