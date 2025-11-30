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

Create or update SDD (Software Design Document) manifest from project bundle. Generates canonical SDD that captures WHY (intent, constraints), WHAT (capabilities, acceptance), and HOW (architecture, invariants, contracts) with promotion status.

**When to use:**

- After plan bundle is complete and reviewed
- Before promoting to review/approved stages
- When SDD needs to be updated after plan changes

**Quick Example:**

```bash
/specfact.04-sdd legacy-api
/specfact.04-sdd legacy-api --no-interactive --output-format json
```

## Parameters

### Target/Input

- `bundle NAME` (required argument) - Project bundle name (e.g., legacy-api, auth-module)
- `--sdd PATH` - Output SDD manifest path. Default: .specfact/sdd/<bundle-name>.<format>

### Output/Results

- `--output-format FORMAT` - SDD manifest format (yaml or json). Default: global --output-format (yaml)

### Behavior/Options

- `--interactive/--no-interactive` - Interactive mode with prompts. Default: True (interactive, auto-detect)

## Workflow

### Step 1: Parse Arguments

- Extract bundle name (required)
- Extract optional parameters (sdd path, output format, etc.)

### Step 2: Execute CLI

```bash
# Interactive SDD creation
specfact plan harden <bundle-name> [--sdd <path>] [--output-format <format>]

# Non-interactive SDD creation
specfact plan harden <bundle-name> --no-interactive [--output-format <format>]
```

### Step 3: Present Results

- Display SDD manifest location
- Show WHY/WHAT/HOW summary
- Present coverage metrics (invariants, contracts)
- Indicate hash linking to bundle

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

1. **ALWAYS execute CLI first**: Run `specfact plan harden` before any analysis
2. **ALWAYS use non-interactive mode for CI/CD**: Use `--no-interactive` flag in Copilot environments
3. **NEVER modify .specfact folder directly**: All operations must go through CLI
4. **NEVER create YAML/JSON directly**: All SDD manifests must be CLI-generated
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate it

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
# Create SDD interactively
/specfact.04-sdd legacy-api

# Create SDD non-interactively
/specfact.04-sdd legacy-api --no-interactive

# Create SDD in JSON format
/specfact.04-sdd legacy-api --output-format json

# Create SDD at custom path
/specfact.04-sdd legacy-api --sdd .specfact/sdd/custom-sdd.yaml
```

## Context

{ARGS}
