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

Compare two project bundles (or legacy plan bundles) to detect deviations, mismatches, and missing features. Identifies code vs plan drift.

**When to use:** After import to compare with manual plan, detecting spec/implementation drift, validating completeness.

**Quick:** `/specfact.compare --bundle legacy-api` or `/specfact.compare --code-vs-plan`

## Parameters

### Target/Input

- `--bundle NAME` - Project bundle name. If specified, compares bundles instead of legacy plan files. Default: None
- `--manual PATH` - Manual plan bundle path. Default: active plan in .specfact/plans. Ignored if --bundle specified
- `--auto PATH` - Auto-derived plan bundle path. Default: latest in .specfact/plans/. Ignored if --bundle specified

### Output/Results

- `--output-format FORMAT` - Output format (markdown, json, yaml). Default: markdown
- `--out PATH` - Output file path. Default: bundle-specific .specfact/projects/<bundle-name>/reports/comparison/report-<timestamp>.md (Phase 8.5), or global .specfact/reports/comparison/ if no bundle context

### Behavior/Options

- `--code-vs-plan` - Alias for comparing code-derived plan vs manual plan. Default: False

## Workflow

### Step 1: Parse Arguments

- Extract comparison targets (bundle, manual plan, auto plan)
- Determine comparison mode (bundle vs bundle, or legacy plan files)

### Step 2: Execute CLI

```bash
specfact plan compare [--bundle <bundle-name>] [--manual <path>] [--auto <path>] [--code-vs-plan] [--output-format <format>] [--out <path>]
# --bundle defaults to active plan if not specified
```

### Step 3: Present Results

- Display deviation summary (by type and severity)
- Show missing features in each plan
- Present drift analysis
- Indicate comparison report location

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
specfact plan compare [--bundle <name>] [options] --no-interactive
```

**Capture**:

- CLI-generated comparison report
- Deviation counts and severity
- Missing features analysis

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

**Purpose**: Add semantic understanding to comparison results

**What to do**:

- Read CLI-generated comparison report (use file reading tools for display only)
- Treat the comparison report as the source of truth; scan codebase only to explain or confirm deviations
- Research codebase for context on deviations
- Suggest fixes for missing features or mismatches

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` folder directly (always use CLI)

**Output**: Generate fix suggestions report (Markdown)

### Phase 3: CLI Artifact Creation (REQUIRED)

```bash
# Apply fixes via CLI commands, then re-compare
specfact plan update-feature [--bundle <name>] [options] --no-interactive
specfact plan compare [--bundle <name>] --no-interactive
```

**Result**: Final artifacts are CLI-generated with validated fixes

**Note**: If code generation is needed, use the validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code))

## Expected Output

### Success

```text
✓ Comparison complete

Comparison Report: .specfact/projects/<bundle-name>/reports/comparison/report-2025-11-26T10-30-00.md

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
/specfact.compare --bundle legacy-api
/specfact.compare --code-vs-plan
/specfact.compare --manual <path> --auto <path>
/specfact.compare --code-vs-plan --output-format json
```

## Context

{ARGS}
