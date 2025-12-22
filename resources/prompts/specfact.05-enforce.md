---
description: Validate SDD manifest against project bundle and contracts, check coverage thresholds.
---

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
- `--sdd PATH` - Path to SDD manifest. Default: bundle-specific .specfact/projects/<bundle-name>/sdd.<format> (Phase 8.5), with fallback to legacy .specfact/sdd/<bundle-name>.<format>

### Output/Results

- `--output-format FORMAT` - Output format (yaml, json, markdown). Default: yaml
- `--out PATH` - Output file path. Default: bundle-specific .specfact/projects/<bundle-name>/reports/enforcement/report-<timestamp>.<format> (Phase 8.5)

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
specfact enforce sdd [<bundle-name>] [--sdd <path>] --no-interactive
```

**Capture**:

- CLI-generated validation report
- Deviation counts and severity
- Coverage metrics vs thresholds

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

**Purpose**: Add semantic understanding to validation results

**What to do**:

- Read CLI-generated validation report (use file reading tools for display only)
- Treat the CLI report as the source of truth; scan codebase only to explain deviations or propose fixes
- Research codebase for context on deviations
- Suggest fixes for validation failures

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` folder directly (always use CLI)

**Output**: Generate fix suggestions report (Markdown)

### Phase 3: CLI Artifact Creation (REQUIRED)

```bash
# Apply fixes via CLI commands, then re-validate
specfact plan update-feature [--bundle <name>] [options] --no-interactive
specfact enforce sdd [<bundle-name>] --no-interactive
```

**Result**: Final artifacts are CLI-generated with validated fixes

**Note**: If code generation is needed, use the validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code))

## Expected Output

### Success

```text
✓ SDD validation passed

Validation Summary
Total deviations: 0
  High: 0
  Medium: 0
  Low: 0

Report saved to: .specfact/projects/<bundle-name>/reports/enforcement/report-2025-11-26T10-30-00.yaml
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
