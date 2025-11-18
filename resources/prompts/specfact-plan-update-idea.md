---
description: "Update idea section metadata in a plan bundle (optional business context)"
---

# SpecFact Update Idea Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact plan update-idea` before any analysis - execute the CLI command before any other operations
2. **NEVER write code**: Do not implement idea update logic - the CLI handles this
3. **NEVER create YAML/JSON directly**: All plan bundle updates must be CLI-generated
4. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
6. **NEVER manipulate internal code**: Do NOT use Python code to directly modify PlanBundle objects, Idea objects, or any internal data structures. The CLI is THE interface - use it exclusively.
7. **No internal knowledge required**: You should NOT need to know about internal implementation details (PlanBundle model, Idea class, etc.). All operations must be performed via CLI commands.
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

Update idea section metadata in a plan bundle. The idea section is OPTIONAL and provides business context and metadata, not technical implementation details.

**Note**: All parameters are optional - you only need to provide the fields you want to update.

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies plan bundle metadata and content. All updates must be performed by the specfact CLI.

**Command**: `specfact plan update-idea`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag.

## What This Command Does

The `specfact plan update-idea` command:

1. **Loads** the existing plan bundle (default: active plan or latest in `.specfact/plans/`)
2. **Validates** the plan bundle structure
3. **Creates** idea section if it doesn't exist
4. **Updates** only the specified fields (all parameters are optional)
5. **Validates** the updated plan bundle
6. **Saves** the updated plan bundle

## Execution Steps

### 1. Parse Arguments and Validate Input

**Parse user input** to extract:

- Title (optional)
- Narrative (optional, brief description)
- Target users (optional, comma-separated personas)
- Value hypothesis (optional, value statement)
- Constraints (optional, comma-separated)
- Plan bundle path (optional, defaults to active plan or latest)

**Note**: All parameters are optional. If no parameters are provided, the command will report a warning.

**WAIT STATE**: If user wants to update but hasn't specified what, ask:

```text
"Which idea fields would you like to update?
- Title
- Narrative
- Target users
- Value hypothesis
- Constraints

Please specify the fields and values:
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

### 2. Check Plan Bundle Existence

**Execute CLI** to check if plan exists:

```bash
# Check active plan
specfact plan select
```

**If plan doesn't exist**:

- CLI will report: "No plan bundles found"
- **WAIT STATE**: Ask user if they want to create a new plan with `specfact plan init`

### 3. Execute Update Idea Command

**Execute CLI command**:

```bash
# Update target users and value hypothesis
specfact plan update-idea \
  --target-users "Developers, DevOps" \
  --value-hypothesis "Reduce technical debt" \
  --plan <plan_path>

# Update constraints
specfact plan update-idea \
  --constraints "Python 3.11+, Maintain backward compatibility" \
  --plan <plan_path>

# Update multiple fields
specfact plan update-idea \
  --title "Project Title" \
  --narrative "Brief project description" \
  --target-users "Developers, QA Engineers" \
  --value-hypothesis "Improve code quality" \
  --constraints "Python 3.11+, Test coverage >= 80%" \
  --plan <plan_path>
```

**Capture from CLI**:

- Plan bundle loaded successfully
- Idea section created if it doesn't exist
- Fields updated (only specified fields)
- Plan bundle saved successfully

### 4. Handle Errors

**Common errors**:

- **No plan bundles found**: Report error and suggest creating plan with `specfact plan init`
- **Plan bundle not found**: Report error if specified path doesn't exist
- **Invalid plan structure**: Report validation error

### 5. Report Completion

**After successful execution**:

```markdown
✓ Idea section updated successfully!

**Updated Fields**: title, target_users, value_hypothesis
**Plan Bundle**: `.specfact/plans/main.bundle.yaml`

**Idea Metadata**:
- Title: Project Title
- Target Users: Developers, QA Engineers
- Value Hypothesis: Improve code quality
- Constraints: Python 3.11+, Test coverage >= 80%

**Next Steps**:
- Review plan: `/specfact-cli/specfact-plan-review`
- Update features: `/specfact-cli/specfact-plan-update-feature`
- Promote plan: `/specfact-cli/specfact-plan-promote`
```

## Guidelines

### Idea Section Purpose

The idea section is **OPTIONAL** and provides:

- **Business context**: Who the plan is for and why it exists
- **Metadata**: High-level constraints and value proposition
- **Not technical implementation**: Technical details belong in features/stories

### Field Guidelines

- **Title**: Brief, descriptive project title
- **Narrative**: Short description of the project's purpose
- **Target Users**: Comma-separated list of user personas (e.g., "Developers, DevOps, QA Engineers")
- **Value Hypothesis**: Statement of expected value or benefit
- **Constraints**: Comma-separated technical or business constraints

### Best Practices

- Keep idea section high-level and business-focused
- Use target users to clarify who benefits from the plan
- State value hypothesis clearly to guide decision-making
- List constraints that affect all features (language, platform, etc.)

## Context

{ARGS}

--- End Command ---
