---
description: "Update an existing feature's metadata in a plan bundle"
---

# SpecFact Update Feature Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## ⚠️ CRITICAL: CLI Usage Enforcement

**YOU MUST ALWAYS USE THE SPECFACT CLI**. Never create artifacts directly.

### Rules

1. **ALWAYS execute CLI first**: Run `specfact plan update-feature` before any analysis - execute the CLI command before any other operations
2. **NEVER write code**: Do not implement feature update logic - the CLI handles this
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

Update an existing feature's metadata in a plan bundle. This command allows updating feature properties (title, outcomes, acceptance criteria, constraints, confidence, draft status) in non-interactive environments (CI/CD, Copilot).

**Note**: All parameters except `--key` are optional - you only need to provide the fields you want to update.

## Operating Constraints

**STRICTLY READ-WRITE**: This command modifies plan bundle metadata and content. All updates must be performed by the specfact CLI.

**Command**: `specfact plan update-feature`

**Mode Auto-Detection**: The CLI automatically detects operational mode (CI/CD or CoPilot) based on environment. No need to specify `--mode` flag.

## What This Command Does

The `specfact plan update-feature` command:

1. **Loads** the existing plan bundle (default: `.specfact/plans/main.bundle.yaml` or active plan)
2. **Validates** the plan bundle structure
3. **Finds** the feature by key
4. **Updates** only the specified fields (all parameters except key are optional)
5. **Validates** the updated plan bundle
6. **Saves** the updated plan bundle

## Execution Steps

### 1. Parse Arguments and Validate Input

**Parse user input** to extract:

- Feature key (required, e.g., `FEATURE-001`)
- Title (optional)
- Outcomes (optional, comma-separated)
- Acceptance criteria (optional, comma-separated)
- Constraints (optional, comma-separated)
- Confidence (optional, 0.0-1.0)
- Draft status (optional, true/false)
- Plan bundle path (optional, defaults to active plan or `.specfact/plans/main.bundle.yaml`)

**WAIT STATE**: If feature key is missing, ask the user:

```text
"Which feature would you like to update? Please provide the feature key (e.g., FEATURE-001):
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

**WAIT STATE**: If no update fields are specified, ask:

```text
"Which fields would you like to update?
- Title
- Outcomes
- Acceptance criteria
- Constraints
- Confidence
- Draft status

Please specify the fields and values:
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
- **WAIT STATE**: Ask user to provide a valid feature key

### 3. Execute Update Feature Command

**Execute CLI command**:

```bash
# Update title and outcomes
specfact plan update-feature \
  --key FEATURE-001 \
  --title "Updated Title" \
  --outcomes "Outcome 1, Outcome 2" \
  --plan <plan_path>

# Update acceptance criteria and confidence
specfact plan update-feature \
  --key FEATURE-001 \
  --acceptance "Criterion 1, Criterion 2" \
  --confidence 0.9 \
  --plan <plan_path>

# Update constraints
specfact plan update-feature \
  --key FEATURE-001 \
  --constraints "Python 3.11+, Test coverage >= 80%" \
  --plan <plan_path>

# Mark as draft
specfact plan update-feature \
  --key FEATURE-001 \
  --draft true \
  --plan <plan_path>
```

**Capture from CLI**:

- Plan bundle loaded successfully
- Feature found by key
- Fields updated (only specified fields)
- Plan bundle saved successfully

### 4. Handle Errors

**Common errors**:

- **Feature not found**: Report error and list available features
- **No updates specified**: Report warning and list available update options
- **Invalid confidence**: Report error if confidence is not 0.0-1.0
- **Plan bundle not found**: Report error and suggest creating plan with `specfact plan init`
- **Invalid plan structure**: Report validation error

### 5. Report Completion

**After successful execution**:

```markdown
✓ Feature updated successfully!

**Feature**: FEATURE-001
**Updated Fields**: title, outcomes, acceptance, confidence
**Plan Bundle**: `.specfact/plans/main.bundle.yaml`

**Updated Metadata**:
- Title: Updated Title
- Outcomes: Outcome 1, Outcome 2
- Acceptance: Criterion 1, Criterion 2
- Confidence: 0.9

**Next Steps**:
- Add stories: `/specfact-cli/specfact-plan-add-story`
- Review plan: `/specfact-cli/specfact-plan-review`
- Promote plan: `/specfact-cli/specfact-plan-promote`
```

## Guidelines

### Update Strategy

- **Partial updates**: Only specified fields are updated, others remain unchanged
- **Comma-separated lists**: Outcomes, acceptance, and constraints use comma-separated strings
- **Confidence range**: Must be between 0.0 and 1.0
- **Draft status**: Use `true` or `false` (boolean)

### Field Guidelines

- **Title**: Clear, concise description of the feature
- **Outcomes**: Expected results or benefits (comma-separated)
- **Acceptance**: Testable acceptance criteria (comma-separated)
- **Constraints**: Technical or business constraints (comma-separated)
- **Confidence**: Confidence score (0.0-1.0) based on requirements clarity
- **Draft**: Mark as draft if not ready for review

### Best Practices

- Update features incrementally as requirements evolve
- Keep acceptance criteria testable and measurable
- Update confidence scores as requirements become clearer
- Use draft status to mark work-in-progress features

## Context

{ARGS}

--- End Command ---
