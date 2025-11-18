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

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly or search bundle files.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact plan promote` before any promotion
2. **NEVER create YAML/JSON directly**: All plan bundle updates must be CLI-generated
3. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata
4. **NEVER search bundle files directly**: Use CLI commands to get plan information (stage, metadata, etc.)
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate it or read files directly

### What Happens If You Don't Follow This

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Out-of-sync information if bundle files are read directly

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

### ⚠️ IMPORTANT: Non-Interactive Mode

The `promote` command does **NOT** have a `--mode` or `--non-interactive` parameter. To avoid interactive confirmation prompts in CI/CD or non-interactive environments, use the `--force` flag:

```bash
# Non-interactive/CI/CD usage (bypasses confirmation prompts)
specfact plan promote --stage review --plan <plan_path> --force

# Interactive usage (may prompt for confirmation)
specfact plan promote --stage review --plan <plan_path>
```

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment for telemetry/routing purposes only. This does **NOT** disable interactive prompts. Mode is detected from:

- Environment variables (`SPECFACT_MODE`)
- CoPilot API availability
- IDE integration (VS Code/Cursor with CoPilot)
- Defaults to CI/CD mode if none detected

**Note**: Mode auto-detection is used for telemetry and routing only. It does **NOT** affect whether the command prompts for confirmation. Use `--force` to bypass interactive confirmations.

## What This Command Does

The `specfact plan promote` command helps move a plan bundle through its lifecycle:

- **draft**: Initial state - can be modified freely
- **review**: Plan is ready for review - should be stable
- **approved**: Plan approved for implementation
- **released**: Plan released and should be immutable

## Execution Steps

### 1. List Available Plans Using CLI (REQUIRED FIRST STEP)

**⚠️ CRITICAL: NEVER search the repository directly or read bundle files. Always use the CLI to get plan information.**

**Execute `specfact plan select` (without arguments) to list all available plans**:

```bash
specfact plan select
```

**⚠️ Note on Interactive Prompt**: This command will display a table and then wait for user input. The copilot should:

1. **Capture the table output** that appears before the prompt
2. **Parse the table** to extract plan information including **current stage** (already included in the table)
3. **Handle the interactive prompt** by either:
   - Using a timeout to cancel after parsing (e.g., `timeout 5 specfact plan select` or similar)
   - Sending an interrupt signal after capturing the output
   - Or in a copilot environment, the output may be available before the prompt blocks

**This command will**:

- Scan `.specfact/plans/` for all `*.bundle.yaml` files
- Extract metadata for each plan (name, features, stories, **stage**, modified date, active status)
- Display a numbered table with all available plans including **current stage** (before the interactive prompt)

**The table includes a "Stage" column** showing the current stage for each plan. Use this information - do NOT read bundle files to get the stage.

**Parse the CLI output** and present it to the user as a Markdown table:

```markdown
## Available Plans

| # | Status | Plan Name | Features | Stories | Stage | Modified |
|---|--------|-----------|----------|---------|-------|----------|
| 1 | | specfact-cli.2025-11-17T08-52-30.bundle.yaml | 32 | 80 | draft | 2025-11-17T08:52:30 |
| 2 | [ACTIVE] | main.bundle.yaml | 62 | 73 | approved | 2025-11-17T00:16:00 |
| 3 | | auto-derived.2025-11-16T23-44-17.bundle.yaml | 19 | 45 | draft | 2025-11-16T23:44:17 |
```

**After showing the list, extract and display detailed information for each plan** so the user can make an informed decision:

```markdown
**Plan Details**:

1. **specfact-cli.2025-11-17T08-52-30.bundle.yaml**
   - Features: 32
   - Stories: 80
   - Stage: draft
   - Modified: 2025-11-17T08:52:30

2. **main.bundle.yaml** [ACTIVE]
   - Features: 62
   - Stories: 73
   - Stage: approved
   - Modified: 2025-11-17T00:16:00

3. **auto-derived.2025-11-16T23-44-17.bundle.yaml**
   - Features: 19
   - Stories: 45
   - Stage: draft
   - Modified: 2025-11-16T23:44:17
```

### 2. Parse Arguments and Determine Current Stage

**Parse user input** to extract:

- Target stage (draft, review, approved, or released) - infer from context if not explicit
- Plan selection - can be:
  - Plan number from the list (e.g., "1", "2", "3")
  - Plan name (e.g., "main.bundle.yaml", "specfact-cli.2025-11-17T08-52-30.bundle.yaml")
  - Special cases: "main plan", "active plan", "last brownfield"
- Validation preference (default: yes)
- Force promotion (default: no)

#### Get Current Stage from CLI Only

**⚠️ CRITICAL: NEVER search bundle files directly**. The `specfact plan select` command already includes the stage in its table output. Use one of these methods:

1. **Parse stage from the table** (already displayed in step 1) - The stage column shows the current stage for each plan
2. **Get stage for specific plan** - If you need to verify the current stage for a specific plan, use:

```bash
specfact plan select <plan_number>
```

This command will output the plan details including the stage, for example:

```text
Active plan set to: specfact-import-test-v2.2025-11-17T13-53-31.bundle.yaml
  Features: 44
  Stories: 101
  Stage: review
```

**Special cases to handle**:

- **"main plan"** or **"default plan"**: Use `.specfact/plans/main.bundle.yaml`
- **"active plan"**: Use the plan marked as `[ACTIVE]` in the list
- **"last brownfield"** or **"last imported"**: Find the latest file by modification date from the CLI table
- **Missing target stage**: Infer next logical stage (draft→review→approved→released) based on current stage from CLI output

**WAIT STATE**: If plan selection is unclear, show the plan list again and ask the user directly:

```text
"Which plan bundle would you like to promote? 
(Enter number from the list above, plan name, 'main plan', 'active plan', or 'last brownfield')
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

**If target stage is missing**, infer from context using the current stage from the CLI table output:

- If current stage is **draft** → next stage is **review**
- If current stage is **review** → next stage is **approved**
- If current stage is **approved** → next stage is **released**
- If current stage is **released** → cannot promote further

If the current stage is not clear from the table, use `specfact plan select <plan_number>` to get the current stage, then infer the next stage.

If still unclear, ask:

```text
"Which stage would you like to promote to? 
(Current stage: draft → Next: review)
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

### 3. Resolve Plan Path and Current Stage

**⚠️ CRITICAL: Use CLI to resolve plan path and get current stage. NEVER search bundle files directly.**

**Resolve the plan selection to an actual file path**:

- **If user selected a number**: Use the plan name from the CLI table (e.g., plan #1 → `specfact-cli.2025-11-17T08-52-30.bundle.yaml`)
- **If user selected a plan name**: Use it directly (may need to add `.bundle.yaml` suffix if missing)
- **If user selected "main plan"**: Use `.specfact/plans/main.bundle.yaml`
- **If user selected "active plan"**: Use the plan marked as `[ACTIVE]` from the CLI table
- **If user selected "last brownfield"**: Use the plan with the latest modification date from the CLI table

**Get current stage from CLI**:

If the current stage is not clear from the table output, use the CLI to get it:

```bash
# Get plan details including current stage
specfact plan select <plan_number>
```

The CLI output will show:

- Plan name
- Features count
- Stories count
- **Stage** (current stage)

**Verify the plan path exists** by attempting to use it with the CLI. If the CLI reports the plan doesn't exist, show an error and ask the user to select again.

### 4. Execute CLI Command (REQUIRED)

**ALWAYS execute the specfact CLI** to perform the promotion:

```bash
# For non-interactive/CI/CD use (bypasses confirmation prompts)
specfact plan promote --stage <target_stage> --plan <plan_path> [--validate] --force

# For interactive use (may prompt for confirmation)
specfact plan promote --stage <target_stage> --plan <plan_path> [--validate]
```

**⚠️ Critical Notes**:

- **No `--mode` or `--non-interactive` flag**: The `promote` command does NOT have these parameters
- **Use `--force` for non-interactive**: The `--force` flag bypasses interactive confirmation prompts when there are partial/missing important categories
- **Mode auto-detection**: Only affects telemetry/routing, NOT interactive prompts
- **When `--force` is used**: The command will skip the `prompt_confirm()` call and proceed automatically

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

### 5. Present Results

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
**Alternative**: Use `--force` flag to promote anyway (bypasses interactive confirmation, suitable for CI/CD/non-interactive use)
```

## Tips for the User

- **Start at draft**: New plans begin at draft stage automatically
- **Review before approving**: Make sure all features have stories and acceptance criteria before promoting to approved
- **Use validation**: Validation is enabled by default to catch issues early
- **Stage progression**: You can only move forward (draft → review → approved → released), not backward
- **Natural language**: You can say "promote plan 1 to review" or "promote main plan to review" or "promote active plan to approved"
- **List plans first**: The command will automatically list all available plans using `specfact plan select` so you can see what's available
- **Non-interactive use**: Use `--force` flag to bypass interactive confirmation prompts (required for CI/CD automation)
- **Interactive prompts**: Without `--force`, the command may prompt for confirmation when there are partial/missing important categories

## Context

{ARGS}
