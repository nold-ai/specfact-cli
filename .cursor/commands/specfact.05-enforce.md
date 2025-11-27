# SpecFact SDD Enforcement Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Validate SDD manifest against project bundle and contracts. Checks hash matching, coverage thresholds, frozen sections, and contract density metrics to ensure SDD is synchronized with bundle.

**When to use:**

- After creating or updating SDD manifest
- Before promoting bundle to approved/released stages
- In CI/CD pipelines for quality gates

**Quick Example:**

```bash
/specfact.05-enforce legacy-api
/specfact.05-enforce legacy-api --output-format json --out validation-report.json
```

## Parameters

### Target/Input

- `bundle NAME` (required argument) - Project bundle name (e.g., legacy-api, auth-module)
- `--sdd PATH` - Path to SDD manifest. Default: .specfact/sdd/<bundle-name>.<format>

### Output/Results

- `--output-format FORMAT` - Output format (yaml, json, markdown). Default: yaml
- `--out PATH` - Output file path. Default: .specfact/reports/sdd/validation-<timestamp>.<format>

### Behavior/Options

- `--no-interactive` - Non-interactive mode (for CI/CD). Default: False (interactive mode)

## Workflow

### Step 1: Parse Arguments

- Extract bundle name (required)
- Extract optional parameters (sdd path, output format, etc.)

### Step 2: Execute CLI

```bash
# Validate SDD
specfact enforce sdd <bundle-name> [--sdd <path>] [--output-format <format>] [--out <path>]

# Non-interactive validation
specfact enforce sdd <bundle-name> --no-interactive --output-format json
```

### Step 3: Present Results

- Display validation summary (passed/failed)
- Show deviation counts by severity
- Present coverage metrics vs thresholds
- Indicate hash match status
- Provide fix hints for failures

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

1. **ALWAYS execute CLI first**: Run `specfact enforce sdd` before any analysis
2. **ALWAYS use non-interactive mode for CI/CD**: Use `--no-interactive` flag in Copilot environments
3. **NEVER modify .specfact folder directly**: All operations must go through CLI
4. **NEVER create YAML/JSON directly**: All validation reports must be CLI-generated
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate it

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

   Why this happens:
   The hash changes when you modify:
   - Features (add/remove/update)
   - Stories (add/remove/update)
   - Product, idea, business, or clarifications

   Fix: Run specfact plan harden legacy-api to update the SDD manifest
```

## Common Patterns

```bash
# Validate SDD
/specfact.05-enforce legacy-api

# Validate with JSON output
/specfact.05-enforce legacy-api --output-format json

# Validate with custom report path
/specfact.05-enforce legacy-api --out custom-report.json

# Non-interactive validation
/specfact.05-enforce legacy-api --no-interactive
```

## Context

{ARGS}
