---
description: Select active plan from available plan bundles
---

# SpecFact Plan Select Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact plan select` before any plan selection
2. **NEVER create YAML/JSON directly**: All config updates must be CLI-generated
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

Display a numbered list of available plan bundles and allow the user to select one as the active plan. The active plan is tracked in `.specfact/plans/config.yaml` and will be used as the default for all plan operations.

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies `.specfact/plans/config.yaml` to set the active plan pointer. All updates must be performed by the specfact CLI.

**Command**: `specfact plan select`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag. Mode is detected from:

- Environment variables (`SPECFACT_MODE`)
- CoPilot API availability
- IDE integration (VS Code/Cursor with CoPilot)
- Defaults to CI/CD mode if none detected

## Execution Steps

### 1. Execute CLI Command (REQUIRED)

**ALWAYS execute the specfact CLI** to list and select plans:

```bash
# Interactive mode (no arguments)
specfact plan select

# Select by number
specfact plan select <number>

# Select by plan name
specfact plan select <plan_name>
```

**Note**: Mode is auto-detected by the CLI. No need to specify `--mode` flag.

**The CLI performs**:

- Scans `.specfact/plans/` for all `*.bundle.yaml` files
- Extracts metadata for each plan
- Displays numbered list (if no plan argument provided)
- Updates `.specfact/plans/config.yaml` with selected plan

**Important**: The plan is a **positional argument**, not a `--plan` option. Use:

- `specfact plan select 20` (select by number)
- `specfact plan select main.bundle.yaml` (select by name)
- NOT `specfact plan select --plan 20` (this will fail)

**Capture CLI output**:

- List of available plans with metadata
- Active plan selection result
- Any error messages or warnings

**If CLI execution fails**:

- Report the error to the user
- Do not attempt to update config manually
- Suggest fixes based on error message

### 2. Format and Present Plans (Copilot-Friendly Format)

**⚠️ CRITICAL**: In Copilot mode, you MUST format the plan list as a **Markdown table** for better readability. The CLI's Rich table output is not copilot-friendly.

**Parse the CLI output** and reformat it as a Markdown table:

```markdown
## Available Plans

| # | Status | Plan Name | Features | Stories | Stage | Modified |
|---|--------|-----------|----------|---------|-------|----------|
| 1 | | specfact-cli.2025-11-04T23-35-00.bundle.yaml | 32 | 80 | draft | 2025-11-04T23:35:00 |
| 2 | [ACTIVE] | main.bundle.yaml | 62 | 73 | approved | 2025-11-04T22:17:22 |
| 3 | | api-client-v2.2025-11-04T22-17-22.bundle.yaml | 19 | 45 | draft | 2025-11-04T22:17:22 |

**Selection Options:**
- Enter a **number** (1-3) to select that plan
- Enter **`<number> details`** (e.g., "1 details") to view detailed information about a plan before selecting
- Enter **`q`** or **`quit`** to cancel

**Example:**
- `1` - Select plan #1
- `1 details` - Show details for plan #1, then ask for selection
- `q` - Cancel selection

[WAIT FOR USER RESPONSE - DO NOT CONTINUE]
```

### 3. Handle Plan Details Request (If User Requests Details)

**If user requests details** (e.g., "1 details" or "show 1"):

1. **Load the plan bundle** to extract detailed information:
   - Read the plan bundle YAML file
   - Extract: idea section, product themes, feature list (first 10 features), business context, metadata

2. **Present detailed information**:

```markdown
## Plan Details: specfact-cli.2025-11-04T23-35-00.bundle.yaml

**Overview:**
- Features: 32
- Stories: 80
- Stage: draft
- Modified: 2025-11-04T23:35:00

**Idea:**
- Title: SpecFact CLI
- Narrative: [extract narrative if available]
- Target Users: [extract if available]

**Product Themes:**
- CLI
- Validation
- Contract Enforcement

**Top Features** (showing first 10):
1. Contract First Test Manager (FEATURE-CONTRACTFIRSTTESTMANAGER) - Confidence: 0.9
2. Prompt Validator (FEATURE-PROMPTVALIDATOR) - Confidence: 0.7
3. Smart Coverage Manager (FEATURE-SMARTCOVERAGEMANAGER) - Confidence: 0.7
...

**Business Context:**
- Priority: [extract if available]
- Constraints: [extract if available]

**Would you like to select this plan?** (y/n)
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]
```

1. **After showing details**, ask if user wants to select the plan:
   - If **yes**: Execute `specfact plan select <number>` or `specfact plan select <plan_name>` (use positional argument, NOT `--plan` option)
   - If **no**: Return to the plan list and ask for selection again

### 4. Handle User Selection

**After user provides selection** (number or plan name), execute CLI with the selected plan:

**⚠️ CRITICAL**: The plan is a **positional argument**, not a `--plan` option.

**If user provided a number** (e.g., "20"):

```bash
# Use the number directly as positional argument
specfact plan select 20
```

**If user provided a plan name** (e.g., "main.bundle.yaml"):

```bash
# Use the plan name directly as positional argument
specfact plan select main.bundle.yaml
```

**If you need to resolve a number to a plan name first** (for logging/display purposes):

```python
# Example: User selected "1"
# Resolve: plans[0]["name"] → "specfact-cli.2025-11-04T23-35-00.bundle.yaml"
# Then execute: specfact plan select 1  (use the number, not the name)
```

**Note**: The CLI accepts both numbers and plan names as positional arguments. You can use either format directly.

### 5. Present Results

**Present the CLI selection results** to the user:

- **Active plan**: Show which plan is now active
- **Config location**: Show where the config was updated
- **Next steps**: Explain how this affects other commands

## Reference: CLI Behavior

### 1. List Available Plans (Reference - CLI Handles This)

**Load all plan bundles** from `.specfact/plans/` directory:

- Scan for all `*.bundle.yaml` files
- Extract metadata for each plan:
  - Plan name (filename)
  - Number of features
  - Number of stories
  - Stage (draft, review, approved, released)
  - File size
  - Last modified date
  - Active status (if currently selected)

### 2. Display Plans as Markdown Table (Copilot-Friendly)

**⚠️ CRITICAL**: Always format the plan list as a **Markdown table** for Copilot readability. The CLI's Rich table is not copilot-friendly.

**Parse CLI output and reformat as Markdown table**:

```markdown
## Available Plans

| # | Status | Plan Name | Features | Stories | Stage | Modified |
|---|--------|-----------|----------|---------|-------|----------|
| 1 | | specfact-cli.2025-11-04T23-35-00.bundle.yaml | 32 | 80 | draft | 2025-11-04T23:35:00 |
| 2 | [ACTIVE] | main.bundle.yaml | 62 | 73 | approved | 2025-11-04T22:17:22 |
| 3 | | api-client-v2.2025-11-04T22-17-22.bundle.yaml | 19 | 45 | draft | 2025-11-04T22:17:22 |

**Selection Options:**
- Enter a **number** (1-3) to select that plan
- Enter **`<number> details`** (e.g., "1 details") to view detailed information about a plan
- Enter **`q`** or **`quit`** to cancel

**Example commands:**
- `1` - Select plan #1
- `1 details` - Show details for plan #1, then ask for selection
- `q` - Cancel selection
```

**Table Formatting Rules:**

- Use proper Markdown table syntax with pipes (`|`)
- Include all columns: #, Status, Plan Name, Features, Stories, Stage, Modified
- Truncate long plan names if needed (show first 50 chars + "...")
- Highlight active plan with `[ACTIVE]` in Status column
- Sort by modification date (oldest first, newest last) as per CLI behavior

### 3. Handle User Selection

**If user provides a number** (e.g., "1"):

- Validate the number is within range
- Execute: `specfact plan select <number>` (use number as positional argument)
- Confirm the selection

**If user provides a number with "details"** (e.g., "1 details", "show 1"):

- Validate the number is within range
- Load the plan bundle YAML file
- Extract and display detailed information (see "Handle Plan Details Request" section)
- Ask if user wants to select this plan
- If yes: Execute `specfact plan select <number>` (use number as positional argument, NOT `--plan` option)
- If no: Return to plan list and ask for selection again

**If user provides a plan name directly** (e.g., "main.bundle.yaml"):

- Validate the plan exists in the plans list
- Execute: `specfact plan select <plan_name>` (use plan name as positional argument, NOT `--plan` option)
- Confirm the selection

**If user provides 'q' or 'quit'**:

- Exit without changes
- Do not execute any CLI commands

### 4. Update Active Plan Config

**Write to `.specfact/plans/config.yaml`**:

```yaml
active_plan: specfact-cli.2025-11-04T23-35-00.bundle.yaml
```

## Expected Output

**After selection**:

```markdown
✓ Active plan set to: specfact-cli.2025-11-04T23-35-00.bundle.yaml

This plan will now be used as the default for:
  - specfact plan compare
  - specfact plan promote
  - specfact plan add-feature
  - specfact plan add-story
  - specfact sync spec-kit
```

**If no plans found**:

```markdown
⚠ No plan bundles found in .specfact/plans/

Create a plan with:
  - specfact plan init
  - specfact import from-code
```

## Interactive Flow

**Step 1**: Check if `--plan` is provided in user input or arguments.

- **If provided**: Set that plan as active directly (skip list display)
- **If missing**: Display numbered list and ask for selection

**Step 2**: Format plans as a **Markdown table** (copilot-friendly):

- Parse CLI output (Rich table format)
- Convert to Markdown table with columns: #, Status, Plan Name, Features, Stories, Stage, Modified
- Include selection instructions with examples

**Step 3**: Wait for user input:

- Number selection (e.g., "1", "2", "3") - Select plan directly
- Number with "details" (e.g., "1 details", "show 1") - Show plan details first
- Plan name (e.g., "main.bundle.yaml") - Select by name
- Quit command (e.g., "q", "quit") - Cancel

**Step 4**: Handle user input:

- **If details requested**: Load plan bundle, show detailed information, ask for confirmation
- **If selection provided**: Execute `specfact plan select <number>` or `specfact plan select <plan_name>` (positional argument, NOT `--plan` option)
- **If quit**: Exit without changes

**Step 5**: Present results and confirm selection.

## Context

{ARGS}

--- End Command ---
