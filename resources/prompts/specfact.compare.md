---
description: Compare manual and auto-derived plans to detect code vs plan drift and deviations.
---

# SpecFact Compare Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Compare two project bundles (or legacy plan bundles) to detect deviations, mismatches, and missing features. Identifies gaps between planned features and actual implementation (code vs plan drift).

**When to use:**

- After importing codebase to compare with manual plan
- Detecting drift between specification and implementation
- Validating plan completeness

**Quick Example:**

```bash
/specfact.compare --bundle legacy-api
/specfact.compare --code-vs-plan
```

## Parameters

### Target/Input

- `--bundle NAME` - Project bundle name. If specified, compares bundles instead of legacy plan files. Default: None
- `--manual PATH` - Manual plan bundle path. Default: active plan in .specfact/plans. Ignored if --bundle specified
- `--auto PATH` - Auto-derived plan bundle path. Default: latest in .specfact/plans/. Ignored if --bundle specified

### Output/Results

- `--output-format FORMAT` - Output format (markdown, json, yaml). Default: markdown
- `--out PATH` - Output file path. Default: .specfact/reports/comparison/deviations-<timestamp>.md

### Behavior/Options

- `--code-vs-plan` - Alias for comparing code-derived plan vs manual plan. Default: False

## Workflow

### Step 1: Parse Arguments

- Extract comparison targets (bundle, manual plan, auto plan)
- Determine comparison mode (bundle vs bundle, or legacy plan files)

### Step 2: Execute CLI

```bash
# Compare bundles
specfact plan compare --bundle <bundle-name>

# Compare legacy plans
specfact plan compare --manual <manual-plan> --auto <auto-plan>

# Convenience alias for code vs plan
specfact plan compare --code-vs-plan
```

### Step 3: Present Results

- Display deviation summary (by type and severity)
- Show missing features in each plan
- Present drift analysis
- Indicate comparison report location

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

1. **ALWAYS execute CLI first**: Run `specfact plan compare` before any analysis
2. **ALWAYS use non-interactive mode for CI/CD**: Use appropriate flags in Copilot environments
3. **NEVER modify .specfact folder directly**: All operations must go through CLI
4. **NEVER create YAML/JSON directly**: All comparison reports must be CLI-generated
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate it

## Expected Output

### Success

```text
✓ Comparison complete

Comparison Report: .specfact/reports/comparison/deviations-2025-11-26T10-30-00.md

Deviations Summary:
  Total: 5
  High: 1 (Missing Feature)
  Medium: 3 (Feature Mismatch)
  Low: 1 (Story Difference)

Missing in Manual Plan: 2 features
Missing in Auto Plan: 1 feature
```

### Error (Missing Plans)

```text
✗ Default manual plan not found: .specfact/plans/main.bundle.yaml
Create one with: specfact plan init --interactive
```

## Common Patterns

```bash
# Compare bundles
/specfact.compare --bundle legacy-api

# Compare code vs plan (convenience)
/specfact.compare --code-vs-plan

# Compare specific plans
/specfact.compare --manual .specfact/plans/main.bundle.yaml --auto .specfact/plans/auto-derived-2025-11-26.bundle.yaml

# Compare with JSON output
/specfact.compare --code-vs-plan --output-format json
```

## Context

{ARGS}
