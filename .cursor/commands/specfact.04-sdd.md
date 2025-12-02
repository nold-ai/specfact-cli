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
- `--sdd PATH` - Output SDD manifest path. Default: .specfact/sdd/<bundle-name>.<format>

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

**Rules:** Execute CLI first, use `--no-interactive` in CI/CD, never modify `.specfact/` directly, use CLI output as grounding.

## Expected Output

### Success

```text
✓ SDD manifest created: .specfact/sdd/legacy-api.yaml

SDD Manifest Summary:
Project Bundle: .specfact/projects/legacy-api/
Bundle Hash: abc123def456...
SDD Path: .specfact/sdd/legacy-api.yaml

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
/specfact.04-sdd --sdd .specfact/sdd/custom.yaml
```

## Context

{ARGS}
