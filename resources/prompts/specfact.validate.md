---
description: Run full validation suite for reproducibility and contract compliance.
---

# SpecFact Validate Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Run full validation suite for reproducibility and contract compliance. Executes linting, type checking, contract exploration, and tests.

**When to use:** Before committing, in CI/CD pipelines, validating contract compliance.

**Quick:** `/specfact.validate --repo .` or `/specfact.validate --verbose --budget 120`

## Parameters

### Target/Input

- `--repo PATH` - Path to repository. Default: current directory (.)

### Output/Results

- `--out PATH` - Output report path. Default: .specfact/reports/enforcement/report-<timestamp>.yaml

### Behavior/Options

- `--verbose` - Verbose output. Default: False
- `--fail-fast` - Stop on first failure. Default: False
- `--fix` - Apply auto-fixes where available. Default: False

### Advanced/Configuration

- `--budget SECONDS` - Time budget in seconds. Default: 120 (must be > 0)

## Workflow

### Step 1: Parse Arguments

- Extract repository path (default: current directory)
- Extract validation options (verbose, fail-fast, fix, budget)

### Step 2: Execute CLI

```bash
specfact repro --repo <path> [--verbose] [--fail-fast] [--fix] [--budget <seconds>] [--out <path>]
```

### Step 3: Present Results

- Display validation summary table
- Show check results (pass/fail/timeout)
- Present report location
- Indicate exit code

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**
- Execute CLI first - never create artifacts directly
- Never modify `.specfact/` directly
- Use CLI output as grounding for validation results

## Expected Output

### Success

```text
✓ All validations passed!

Check Summary:
  Lint (ruff)          ✓ Passed
  Async Patterns       ✓ Passed
  Type Checking         ✓ Passed
  Contract Exploration ✓ Passed
  Property Tests        ✓ Passed
  Smoke Tests           ✓ Passed

Report saved to: .specfact/reports/enforcement/report-2025-11-26T10-30-00.yaml
```

### Failure

```text
✗ Some validations failed

Check Summary:
  Lint (ruff)          ✓ Passed
  Async Patterns       ✗ Failed (2 issues)
  Type Checking         ✓ Passed
  ...
```

## Common Patterns

```bash
/specfact.validate --repo .
/specfact.validate --verbose
/specfact.validate --fix
/specfact.validate --fail-fast
/specfact.validate --budget 300
```

## Context

{ARGS}
