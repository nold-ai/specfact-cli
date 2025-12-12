---
description: Import codebase → plan bundle. CLI extracts routes/schemas/relationships. LLM enriches with context.
---

# SpecFact Import Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Import codebase → plan bundle. CLI extracts routes/schemas/relationships/contracts. LLM enriches context/"why"/completeness.

## Parameters

**Target/Input**: `--bundle NAME` (optional, defaults to active plan), `--repo PATH`, `--entry-point PATH`, `--enrichment PATH`  
**Output/Results**: `--report PATH`  
**Behavior/Options**: `--shadow-only`, `--enrich-for-speckit/--no-enrich-for-speckit` (default: enabled, uses PlanEnricher for consistent enrichment)  
**Advanced/Configuration**: `--confidence FLOAT` (0.0-1.0), `--key-format FORMAT` (classname|sequential)

## Workflow

1. **Execute CLI**: `specfact import from-code [<bundle>] --repo <path> [options]`
   - CLI extracts: routes (FastAPI/Flask/Django), schemas (Pydantic), relationships, contracts (OpenAPI scaffolds), source tracking
   - Uses active plan if bundle not specified
   - **Auto-enrichment enabled by default**: Automatically enhances vague acceptance criteria, incomplete requirements, and generic tasks using PlanEnricher (same logic as `plan review --auto-enrich`)
   - Use `--no-enrich-for-speckit` to disable auto-enrichment

2. **LLM Enrichment** (if `--enrichment` provided):
   - Read `.specfact/projects/<bundle>/enrichment_context.md`
   - Enrich: business context, "why" reasoning, missing acceptance criteria
   - Validate: contracts vs code, feature/story alignment
   - Save enrichment report to `.specfact/projects/<bundle-name>/reports/enrichment/` (bundle-specific, Phase 8.5, if created)

3. **Present**: Bundle location, report path, summary (features/stories/contracts/relationships)

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
specfact import from-code [<bundle>] --repo <path> --no-interactive
```

**Capture**:

- CLI-generated artifacts (plan bundles, reports)
- Metadata (timestamps, confidence scores)
- Telemetry (execution time, file counts)

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

**Purpose**: Add semantic understanding to CLI output

**What to do**:

- Read CLI-generated artifacts (use file reading tools for display only)
- Research codebase for additional context
- Identify missing features/stories
- Suggest confidence adjustments
- Extract business context

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` folder directly (always use CLI)
- ❌ Use direct file manipulation tools for writing (use CLI commands)

**Output**: Generate enrichment report (Markdown) saved to `.specfact/projects/<bundle-name>/reports/enrichment/` (bundle-specific, Phase 8.5)

### Phase 3: CLI Artifact Creation (REQUIRED)

```bash
# Use enrichment to update plan via CLI
specfact import from-code [<bundle>] --repo <path> --enrichment <enrichment-report> --no-interactive
```

**Result**: Final artifacts are CLI-generated with validated enrichments

**Note**: If code generation is needed, use the validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code))

## Expected Output

**Success**: Bundle location, report path, summary (features/stories/contracts/relationships)  
**Error**: Missing bundle name or bundle already exists

## Common Patterns

```bash
/specfact.01-import --repo .                    # Uses active plan, auto-enrichment enabled by default
/specfact.01-import --bundle legacy-api --repo . # Auto-enrichment enabled
/specfact.01-import --repo . --no-enrich-for-speckit  # Disable auto-enrichment
/specfact.01-import --repo . --entry-point src/auth/
/specfact.01-import --repo . --enrichment report.md
```

## Context

{ARGS}
