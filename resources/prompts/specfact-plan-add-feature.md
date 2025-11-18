---
description: "Add a new feature to an existing plan bundle"
---

# SpecFact Add Feature Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact plan add-feature` before any analysis - execute the CLI command before any other operations
2. **NEVER write code**: Do not implement feature addition logic - the CLI handles this
3. **NEVER create YAML/JSON directly**: All plan bundle updates must be CLI-generated
4. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
6. **NEVER manipulate internal code**: Do NOT use Python code to directly modify PlanBundle objects, Feature objects, or any internal data structures. The CLI is THE interface - use it exclusively.
7. **No internal knowledge required**: You should NOT need to know about internal implementation details (PlanBundle model, Feature class, etc.). All operations must be performed via CLI commands.
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

Add a new feature to an existing plan bundle. The feature will be added with the specified key, title, outcomes, and acceptance criteria.

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies plan bundle metadata and content. All updates must be performed by the specfact CLI.

**Command**: `specfact plan add-feature`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag.

## What This Command Does

The `specfact plan add-feature` command:

1. **Loads** the existing plan bundle (default: `.specfact/plans/main.bundle.yaml` or active plan)
2. **Validates** the plan bundle structure
3. **Checks** if the feature key already exists (prevents duplicates)
4. **Creates** a new feature with specified metadata
5. **Adds** the feature to the plan bundle
6. **Validates** the updated plan bundle
7. **Saves** the updated plan bundle

## Execution Steps

### 1. Parse Arguments and Validate Input

**Parse user input** to extract:

- Feature key (required, e.g., `FEATURE-001`)
- Feature title (required)
- Outcomes (optional, comma-separated)
- Acceptance criteria (optional, comma-separated)
- Plan bundle path (optional, defaults to active plan or `.specfact/plans/main.bundle.yaml`)

**WAIT STATE**: If required arguments are missing, ask the user:

```text
"To add a feature, I need:
- Feature key (e.g., FEATURE-001)
- Feature title

Please provide these values:
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

### 2. Check Plan Bundle Existence

**Execute CLI** to check if plan exists:

```bash
# Check if default plan exists
specfact plan select
```

**If plan doesn't exist**:

- Report error: "Default plan not found. Create one with: `specfact plan init --interactive`"
- **WAIT STATE**: Ask user if they want to create a new plan or specify a different path

### 3. Execute Add Feature Command

**Execute CLI command**:

```bash
# Basic usage
specfact plan add-feature --key FEATURE-001 --title "Feature Title" --plan <plan_path>

# With outcomes and acceptance
specfact plan add-feature \
  --key FEATURE-001 \
  --title "Feature Title" \
  --outcomes "Outcome 1, Outcome 2" \
  --acceptance "Criterion 1, Criterion 2" \
  --plan <plan_path>
```

**Capture from CLI**:

- Plan bundle loaded successfully
- Feature key validation (must not already exist)
- Feature created and added
- Plan bundle saved successfully

### 4. Handle Errors

**Common errors**:

- **Feature key already exists**: Report error and suggest using `specfact plan update-feature` instead
- **Plan bundle not found**: Report error and suggest creating plan with `specfact plan init`
- **Invalid plan structure**: Report validation error

### 5. Report Completion

**After successful execution**:

```markdown
✓ Feature added successfully!

**Feature**: FEATURE-001
**Title**: Feature Title
**Outcomes**: Outcome 1, Outcome 2
**Acceptance**: Criterion 1, Criterion 2
**Plan Bundle**: `.specfact/plans/main.bundle.yaml`

**Next Steps**:
- Add stories to this feature: `/specfact-cli/specfact-plan-add-story`
- Update feature metadata: `/specfact-cli/specfact-plan-update-feature`
- Review plan: `/specfact-cli/specfact-plan-review`
```

## Guidelines

### Feature Key Format

- Use consistent format: `FEATURE-001`, `FEATURE-002`, etc.
- Keys must be unique within the plan bundle
- CLI will reject duplicate keys

### Feature Metadata

- **Title**: Clear, concise description of the feature
- **Outcomes**: Expected results or benefits (comma-separated)
- **Acceptance**: Testable acceptance criteria (comma-separated)

### Best Practices

- Add features incrementally as you discover requirements
- Use descriptive titles that explain the feature's purpose
- Include measurable outcomes and testable acceptance criteria
- Keep features focused and single-purpose

## Context

{ARGS}

--- End Command ---
