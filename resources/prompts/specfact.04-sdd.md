---
description: Create or update SDD manifest (hard spec) from project bundle with WHY/WHAT/HOW extraction.
---

# SpecFact SDD Creation Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Create/update SDD manifest from project bundle. Captures WHY (intent/constraints), WHAT (capabilities/acceptance), HOW (architecture/invariants/contracts).

**When to use:** After plan review, before promotion, when plan changes.

**Quick:** `/specfact.04-sdd` (uses active plan) or `/specfact.04-sdd legacy-api`

## Parameters

### Target/Input

- `bundle NAME` (optional argument) - Project bundle name (e.g., legacy-api, auth-module). Default: active plan (set via `plan select`)
- `--sdd PATH` - Output SDD manifest path. Default: bundle-specific .specfact/projects/<bundle-name>/sdd.<format> (Phase 8.5)

### Output/Results

- `--output-format FORMAT` - SDD manifest format (yaml or json). Default: global --output-format (yaml)

### Behavior/Options

- `--interactive/--no-interactive` - Interactive mode with prompts. Default: True (interactive, auto-detect)

## Workflow

### Step 1: Parse Arguments

- Extract bundle name (defaults to active plan if not specified)
- Extract optional parameters (sdd path, output format, etc.)

### Step 2: Execute CLI

```bash
specfact plan harden [<bundle-name>] [--sdd <path>] [--output-format <format>]
# Uses active plan if bundle not specified
```

### Step 3: Present Results

- Display SDD location, WHY/WHAT/HOW summary, coverage metrics
- Hash excludes clarifications (stable across review sessions)

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

- Execute CLI first - never create artifacts directly
- Use `--no-interactive` flag in CI/CD environments
- Never modify `.specfact/` directly
- Use CLI output as grounding for validation
- Code generation requires LLM (only via AI IDE slash prompts, not CLI-only)

## Dual-Stack Workflow (Copilot Mode)

When in copilot mode, follow this three-phase workflow:

### Phase 1: CLI Grounding (REQUIRED)

```bash
# Execute CLI to get structured output
specfact plan harden [<bundle-name>] [--sdd <path>] --no-interactive
```

**Capture**:

- CLI-generated SDD manifest
- Metadata (hash, coverage metrics)
- Telemetry (execution time, file counts)

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

**Purpose**: Add semantic understanding to SDD content

**What to do**:

- Read CLI-generated SDD (use file reading tools for display only)
- Treat CLI SDD as the source of truth; scan codebase only to enrich WHY/WHAT/HOW context
- Research codebase for additional context
- Suggest improvements to WHY/WHAT/HOW sections

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` folder directly (always use CLI)

**Output**: Generate enrichment report (Markdown) with suggestions

### Phase 3: CLI Artifact Creation (REQUIRED)

```bash
# Use enrichment to update plan via CLI, then regenerate SDD
specfact plan update-idea [--bundle <name>] [options] --no-interactive
specfact plan harden [<bundle-name>] --no-interactive
```

**Result**: Final SDD is CLI-generated with validated enrichments

**Note**: If code generation is needed, use the validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code))

## Expected Output

### Success

```text
✓ SDD manifest created: .specfact/projects/legacy-api/sdd.yaml

SDD Manifest Summary:
Project Bundle: .specfact/projects/legacy-api/
Bundle Hash: abc123def456...
SDD Path: .specfact/projects/legacy-api/sdd.yaml

WHY (Intent):
  Build secure authentication system
Constraints: 2

WHAT (Capabilities): 12

HOW (Architecture):
  Microservices architecture with JWT tokens...
Invariants: 8
Contracts: 15
```

### Error (Missing Bundle)

```text
✗ Project bundle 'legacy-api' not found
Create one with: specfact plan init legacy-api
```

## Common Patterns

```bash
/specfact.04-sdd                              # Uses active plan
/specfact.04-sdd legacy-api                   # Specific bundle
/specfact.04-sdd --output-format json         # JSON format
/specfact.04-sdd --sdd .specfact/projects/custom-bundle/sdd.yaml
```

## Context

{ARGS}
