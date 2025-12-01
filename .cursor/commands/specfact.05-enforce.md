# SpecFact SDD Enforcement Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Validate SDD manifest against project bundle and contracts. Checks hash matching, coverage thresholds, and contract density.

**When to use:** After creating/updating SDD, before promotion, in CI/CD pipelines.

**Quick:** `/specfact.05-enforce` (uses active plan) or `/specfact.05-enforce legacy-api`

## Parameters

### Target/Input

- `bundle NAME` (optional argument) - Project bundle name (e.g., legacy-api, auth-module). Default: active plan (set via `plan select`)
- `--sdd PATH` - Path to SDD manifest. Default: .specfact/sdd/<bundle-name>.<format>

### Output/Results

- `--output-format FORMAT` - Output format (yaml, json, markdown). Default: yaml
- `--out PATH` - Output file path. Default: .specfact/reports/sdd/validation-<timestamp>.<format>

### Behavior/Options

- `--no-interactive` - Non-interactive mode (for CI/CD). Default: False (interactive mode)

## Workflow

### Step 1: Parse Arguments

- Extract bundle name (defaults to active plan if not specified)
- Extract optional parameters (sdd path, output format, etc.)

### Step 2: Execute CLI

```bash
specfact enforce sdd [<bundle-name>] [--sdd <path>] [--output-format <format>] [--out <path>]
# Uses active plan if bundle not specified
```

### Step 3: Present Results

- Display validation summary (passed/failed)
- Show deviation counts by severity
- Present coverage metrics vs thresholds
- Indicate hash match status
- Provide fix hints for failures

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:** Execute CLI first, use `--no-interactive` in CI/CD, never modify `.specfact/` directly, use CLI output as grounding.

## Expected Output

### Success

```text
✓ SDD validation passed

Validation Summary
Total deviations: 0
  High: 0
  Medium: 0
  Low: 0

Report saved to: .specfact/reports/sdd/validation-2025-11-26T10-30-00.yaml
```

### Failure (Hash Mismatch)

```text
✗ SDD validation failed

Issues Found:

1. Hash Mismatch (HIGH)
   The project bundle has been modified since the SDD manifest was created.
   SDD hash: abc123def456...
   Bundle hash: xyz789ghi012...

   Hash changes when modifying features, stories, or product/idea/business sections.
   Note: Clarifications don't affect hash (review metadata). Hash stable across review sessions.
   Fix: Run `specfact plan harden <bundle-name>` to update SDD manifest.
```

## Common Patterns

```bash
/specfact.05-enforce                    # Uses active plan
/specfact.05-enforce legacy-api         # Specific bundle
/specfact.05-enforce --output-format json --out report.json
/specfact.05-enforce --no-interactive   # CI/CD mode
```

## Context

{ARGS}
