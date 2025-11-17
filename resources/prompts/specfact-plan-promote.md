---
description: Promote a plan bundle through development stages with quality gate validation.
---

# SpecFact Promote Plan Bundle Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact plan promote` before any promotion
2. **NEVER create YAML/JSON directly**: All plan bundle updates must be CLI-generated
3. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata
4. **Use CLI output as grounding**: Parse CLI output, don't regenerate it

### What Happens If You Don't Follow This

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures

## ⏸️ Wait States: User Input Required

**When user input is required, you MUST wait for the user's response.**

### Wait State Rules

1. **Never assume**: If input is missing, ask and wait
2. **Never continue**: Do not proceed until user responds
3. **Be explicit**: Clearly state what information you need
4. **Provide options**: Give examples or default suggestions

## Goal

Help the user promote their plan bundle through development stages (draft → review → approved → released) to track progress and ensure quality gates are met.

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies plan bundle metadata. All updates must be performed by the specfact CLI.

**Command**: `specfact plan promote`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag. Mode is detected from:

- Environment variables (`SPECFACT_MODE`)
- CoPilot API availability
- IDE integration (VS Code/Cursor with CoPilot)
- Defaults to CI/CD mode if none detected

## What This Command Does

The `specfact plan promote` command helps move a plan bundle through its lifecycle:

- **draft**: Initial state - can be modified freely
- **review**: Plan is ready for review - should be stable
- **approved**: Plan approved for implementation
- **released**: Plan released and should be immutable

## Execution Steps

### 1. Parse Arguments and Wait for Missing Input

**Parse user input** to extract:

- Target stage (draft, review, approved, or released) - infer from context if not explicit
- Plan file path - handle special cases like "last imported brownfield plan"
- Validation preference (default: yes)
- Force promotion (default: no)

**Special cases to handle**:

- **"last imported brownfield plan"** or **"last brownfield"**: Find the latest file in `.specfact/plans/` matching pattern `*-<timestamp>.bundle.yaml`
- **"main plan"** or **"default plan"**: Use `.specfact/plans/main.bundle.yaml`
- **Missing target stage**: Infer next logical stage (draft→review→approved→released)

**WAIT STATE**: If information is unclear, ask the user directly and **WAIT for their response**:

```text
"Which plan bundle would you like to promote? 
(Enter path, 'main plan', or 'last brownfield')
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

### 2. Execute CLI Command (REQUIRED)

**ALWAYS execute the specfact CLI** to perform the promotion:

```bash
specfact plan promote --stage <target_stage> --plan <plan_path> [--validate] [--force]
```

**Note**: Mode is auto-detected by the CLI. No need to specify `--mode` flag.

**The CLI performs**:

- Plan bundle loading and validation
- Current stage checking
- Promotion rule validation (cannot promote backward, quality gates)
- **Coverage status validation** (checks for missing critical categories)
- Metadata updates (stage, promoted_at, promoted_by)
- Plan bundle saving with updated metadata

**Capture CLI output**:

- Promotion result (success/failure)
- Validation results (if enabled)
- Updated plan bundle path
- Any error messages or warnings

**If CLI execution fails**:

- Report the error to the user
- Do not attempt to update plan bundles manually
- Suggest fixes based on error message

### 3. Present Results

**Present the CLI promotion results** to the user:

- **Promotion status**: Show if promotion succeeded or failed
- **Current stage**: Show the new stage after promotion
- **Validation results**: Show any validation warnings or errors
- **Next steps**: Suggest next actions based on promotion result

**Example CLI output**:

```markdown
✓ Plan Promotion Successful

**Plan**: `.specfact/plans/auto-derived-2025-11-04T23-00-41.bundle.yaml`
**Stage**: draft → review
**Promoted at**: 2025-11-04T22:02:43.478499+00:00
**Promoted by**: dom

**Validation**: ✓ Passed
- ✓ All features have at least one story (11 features, 22 stories)
- ✓ Plan structure is valid
- ✓ All required fields are present

**Next Steps**:
- Review the plan bundle for completeness
- Ensure all features have acceptance criteria
- When ready, promote to approved: `/specfact-cli/specfact-plan-promote approved`
```

**If there are issues**, present them from CLI output:

```markdown
❌ Plan Promotion Failed

**Plan**: `.specfact/plans/auto-derived-2025-11-04T23-00-41.bundle.yaml`
**Current Stage**: draft
**Target Stage**: review

**Validation Errors** (from CLI):
- FEATURE-001: User Authentication
- FEATURE-002: Payment Processing

**Coverage Validation**:
- ❌ Constraints & Tradeoffs: Missing (blocks promotion)
- ⚠️ Data Model: Partial (warns but allows with confirmation)

**Fix**: 
- Add at least one story to each feature
- Run `specfact plan review` to resolve missing critical categories
**Alternative**: Use `--force` flag to promote anyway (not recommended)
```

## Tips for the User

- **Start at draft**: New plans begin at draft stage automatically
- **Review before approving**: Make sure all features have stories and acceptance criteria before promoting to approved
- **Use validation**: Validation is enabled by default to catch issues early
- **Stage progression**: You can only move forward (draft → review → approved → released), not backward
- **Natural language**: You can say "promote last imported brownfield plan" or "promote main plan to review"

## Context

{ARGS}
