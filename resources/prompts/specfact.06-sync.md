---
description: Sync changes between external tool artifacts and SpecFact using bridge architecture.
---

# SpecFact Sync Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Synchronize artifacts from external tools (Spec-Kit, Linear, Jira) with SpecFact project bundles using bridge mappings. Supports bidirectional sync.

**When to use:** Syncing with Spec-Kit, integrating external tools, maintaining consistency.

**Quick:** `/specfact.06-sync --adapter speckit --repo . --bidirectional` or `/specfact.06-sync --bundle legacy-api --watch`

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
specfact sync bridge --adapter <adapter> --repo <path> [--bidirectional] [--bundle <name>] [--overwrite] [--watch] [--interval <seconds>]
# --bundle defaults to active plan if not specified
```

### Step 3: Present Results

- Display sync direction and adapter used
- Show artifacts synchronized
- Present conflict resolution (if any)
- Indicate watch status (if enabled)

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:** Execute CLI first, use appropriate flags in CI/CD, never modify `.specfact/` or `.specify/` directly, use CLI output as grounding.

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
/specfact.06-sync --adapter speckit --repo . --bidirectional
/specfact.06-sync --adapter speckit --repo . --bundle legacy-api
/specfact.06-sync --adapter speckit --repo . --watch --interval 5
/specfact.06-sync --repo . --bidirectional  # Auto-detect adapter
```

## Context

{ARGS}
