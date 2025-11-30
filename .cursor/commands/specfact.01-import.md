# SpecFact Import Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Import an existing codebase into a SpecFact plan bundle. Analyzes code structure using AI-first semantic understanding or AST-based fallback to generate a plan bundle representing the current system.

**When to use:**

- Starting SpecFact on an existing project (brownfield)
- Converting legacy code to contract-driven format
- Creating initial plan from codebase structure

**Quick Example:**

```bash
/specfact.01-import --bundle legacy-api --repo .
```

## Parameters

### Target/Input

- `--bundle NAME` (required argument) - Project bundle name (e.g., legacy-api, auth-module)
- `--repo PATH` - Repository path. Default: current directory (.)
- `--entry-point PATH` - Subdirectory for partial analysis. Default: None (analyze entire repo)
- `--enrichment PATH` - Path to LLM enrichment report. Default: None

### Output/Results

- `--report PATH` - Analysis report path. Default: .specfact/reports/brownfield/analysis-<timestamp>.md

### Behavior/Options

- `--shadow-only` - Observe without enforcing. Default: False
- `--enrich-for-speckit` - Auto-enrich for Spec-Kit compliance. Default: False

### Advanced/Configuration

- `--confidence FLOAT` - Minimum confidence score (0.0-1.0). Default: 0.5
- `--key-format FORMAT` - Feature key format: 'classname' or 'sequential'. Default: classname

## Workflow

### Step 1: Parse Arguments

- Extract `--bundle` (required)
- Extract `--repo` (default: current directory)
- Extract optional parameters (confidence, enrichment, etc.)

### Step 2: Execute CLI

```bash
specfact import from-code <bundle-name> --repo <path> [options]
```

### Step 3: Present Results

- Display generated plan bundle location
- Show analysis report path
- Present summary of features/stories detected

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

1. **ALWAYS execute CLI first**: Run `specfact import from-code` before any analysis
2. **ALWAYS use non-interactive mode for CI/CD**: Use `--no-interactive` flag in Copilot environments
3. **NEVER modify .specfact folder directly**: All operations must go through CLI
4. **NEVER create YAML/JSON directly**: All artifacts must be CLI-generated
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate it

## Expected Output

## Success

```text
✓ Project bundle created: .specfact/projects/legacy-api/
✓ Analysis report: .specfact/reports/brownfield/analysis-2025-11-26T10-30-00.md
✓ Features detected: 12
✓ Stories detected: 45
```

## Error (Missing Bundle)

```text
✗ Project bundle name is required
Usage: specfact import from-code <bundle-name> [options]
```

## Common Patterns

```bash
# Basic import
/specfact.01-import --bundle legacy-api --repo .

# Import with confidence threshold
/specfact.01-import --bundle legacy-api --repo . --confidence 0.7

# Import with enrichment report
/specfact.01-import --bundle legacy-api --repo . --enrichment enrichment-report.md

# Partial analysis (subdirectory only)
/specfact.01-import --bundle auth-module --repo . --entry-point src/auth/

# Spec-Kit compliance mode
/specfact.01-import --bundle legacy-api --repo . --enrich-for-speckit
```

## Context

{ARGS}
