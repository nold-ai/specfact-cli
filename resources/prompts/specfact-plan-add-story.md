---
description: "Add a new story to an existing feature in a plan bundle"
---

# SpecFact Add Story Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact plan add-story` before any analysis - execute the CLI command before any other operations
2. **NEVER write code**: Do not implement story addition logic - the CLI handles this
3. **NEVER create YAML/JSON directly**: All plan bundle updates must be CLI-generated
4. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
6. **NEVER manipulate internal code**: Do NOT use Python code to directly modify PlanBundle objects, Story objects, or any internal data structures. The CLI is THE interface - use it exclusively.
7. **No internal knowledge required**: You should NOT need to know about internal implementation details (PlanBundle model, Story class, etc.). All operations must be performed via CLI commands.
8. **NEVER read artifacts directly**: Do NOT read plan bundle files directly to extract information unless for display purposes. Use CLI commands (`specfact plan select`) to get plan information.

### What Happens If You Don't Follow This

- ❌ Artifacts may not match CLI schema versions
- ❌ Missing metadata and telemetry
- ❌ Format inconsistencies
- ❌ Validation failures
- ❌ Works only in Copilot mode, fails in CI/CD
- ❌ Breaks when CLI internals change
- ❌ Requires knowledge of internal code structure

## ⏸️ Wait States: User Input Required

**When user input is required, you MUST wait for the user's response.**

### Wait State Rules

1. **Never assume**: If input is missing, ask and wait
2. **Never continue**: Do not proceed until user responds
3. **Be explicit**: Clearly state what information you need
4. **Provide options**: Give examples or default suggestions

## Goal

Add a new story to an existing feature in a plan bundle. The story will be added with the specified key, title, acceptance criteria, and optional story/value points.

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies plan bundle metadata and content. All updates must be performed by the specfact CLI.

**Command**: `specfact plan add-story`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag.

## What This Command Does

The `specfact plan add-story` command:

1. **Loads** the existing plan bundle (default: `.specfact/plans/main.bundle.yaml` or active plan)
2. **Validates** the plan bundle structure
3. **Finds** the parent feature by key
4. **Checks** if the story key already exists in the feature (prevents duplicates)
5. **Creates** a new story with specified metadata
6. **Adds** the story to the feature
7. **Validates** the updated plan bundle
8. **Saves** the updated plan bundle

## Execution Steps

### 1. Parse Arguments and Validate Input

**Parse user input** to extract:

- Parent feature key (required, e.g., `FEATURE-001`)
- Story key (required, e.g., `STORY-001`)
- Story title (required)
- Acceptance criteria (optional, comma-separated)
- Story points (optional, 0-100)
- Value points (optional, 0-100)
- Draft status (optional, default: false)
- Plan bundle path (optional, defaults to active plan or `.specfact/plans/main.bundle.yaml`)

**WAIT STATE**: If required arguments are missing, ask the user:

```text
"To add a story, I need:
- Parent feature key (e.g., FEATURE-001)
- Story key (e.g., STORY-001)
- Story title

Please provide these values:
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

### 2. Check Plan Bundle and Feature Existence

**Execute CLI** to check if plan exists:

```bash
# Check if default plan exists
specfact plan select
```

**If plan doesn't exist**:

- Report error: "Default plan not found. Create one with: `specfact plan init --interactive`"
- **WAIT STATE**: Ask user if they want to create a new plan or specify a different path

**If feature doesn't exist**:

- CLI will report: "Feature 'FEATURE-001' not found in plan"
- CLI will list available features
- **WAIT STATE**: Ask user to provide a valid feature key or create the feature first

### 3. Execute Add Story Command

**Execute CLI command**:

```bash
# Basic usage
specfact plan add-story \
  --feature FEATURE-001 \
  --key STORY-001 \
  --title "Story Title" \
  --plan <plan_path>

# With acceptance criteria and points
specfact plan add-story \
  --feature FEATURE-001 \
  --key STORY-001 \
  --title "Story Title" \
  --acceptance "Criterion 1, Criterion 2" \
  --story-points 5 \
  --value-points 3 \
  --plan <plan_path>
```

**Capture from CLI**:

- Plan bundle loaded successfully
- Parent feature found
- Story key validation (must not already exist in feature)
- Story created and added to feature
- Plan bundle saved successfully

### 4. Handle Errors

**Common errors**:

- **Feature not found**: Report error and list available features
- **Story key already exists**: Report error and suggest using a different key
- **Plan bundle not found**: Report error and suggest creating plan with `specfact plan init`
- **Invalid plan structure**: Report validation error

### 5. Report Completion

**After successful execution**:

```markdown
✓ Story added successfully!

**Feature**: FEATURE-001
**Story**: STORY-001
**Title**: Story Title
**Acceptance**: Criterion 1, Criterion 2
**Story Points**: 5
**Value Points**: 3
**Plan Bundle**: `.specfact/plans/main.bundle.yaml`

**Next Steps**:
- Add more stories: `/specfact-cli/specfact-plan-add-story`
- Update story metadata: Use `specfact plan update-feature` (stories are updated via feature)
- Review plan: `/specfact-cli/specfact-plan-review`
```

## Guidelines

### Story Key Format

- Use consistent format: `STORY-001`, `STORY-002`, etc.
- Keys must be unique within the feature
- CLI will reject duplicate keys within the same feature

### Story Metadata

- **Title**: Clear, user-focused description (e.g., "As a user, I can...")
- **Acceptance**: Testable acceptance criteria (comma-separated)
- **Story Points**: Complexity estimate (0-100, optional)
- **Value Points**: Business value estimate (0-100, optional)
- **Draft**: Mark as draft if not ready for review (optional)

### Best Practices

- Write stories from the user's perspective
- Include testable acceptance criteria
- Use story points for complexity estimation
- Use value points for business value prioritization
- Keep stories focused and single-purpose

## Context

{ARGS}

--- End Command ---
