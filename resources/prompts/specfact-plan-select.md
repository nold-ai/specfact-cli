---
description: Select active plan from available plan bundles
---

# SpecFact Plan Select Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Display a numbered list of available plan bundles and allow the user to select one as the active plan. The active plan is tracked in `.specfact/plans/config.yaml` and will be used as the default for all plan operations.

## Operating Constraints

**READ-WRITE**: This command modifies `.specfact/plans/config.yaml` to set the active plan pointer.

**Command**: `specfact plan select`

## Execution Steps

### 1. List Available Plans

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

### 2. Display Numbered List

**Present plans in a concise, numbered format**:

```markdown
Available Plans:

  1. [ACTIVE] specfact-cli.2025-11-04T23-35-00.bundle.yaml
     Features: 32 | Stories: 80 | Stage: draft | Modified: 2025-11-04T23:35:00

  2. main.bundle.yaml
     Features: 62 | Stories: 73 | Stage: approved | Modified: 2025-11-04T22:17:22

  3. api-client-v2.2025-11-04T22-17-22.bundle.yaml
     Features: 19 | Stories: 45 | Stage: draft | Modified: 2025-11-04T22:17:22

Select a plan by number (1-3) or 'q' to quit:
```

### 3. Handle User Selection

**If user provides a number**:

- Validate the number is within range
- Get the corresponding plan name
- Set it as the active plan in `.specfact/plans/config.yaml`
- Confirm the selection

**If user provides a plan name directly**:

- Validate the plan exists
- Set it as the active plan
- Confirm the selection

**If user provides 'q' or 'quit'**:

- Exit without changes

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

**Step 2**: If displaying list, present plans in concise format with:

- Plan number (1, 2, 3, ...)
- Active status indicator ([ACTIVE])
- Plan name (filename)
- Quick overview (features, stories, stage, modified date)

**Step 3**: Wait for user input:

- Number selection (e.g., "1", "2", "3")
- Plan name (e.g., "main.bundle.yaml")
- Quit command (e.g., "q", "quit")

**Step 4**: Update config and confirm selection.

## Context

{ARGS}

--- End Command ---
