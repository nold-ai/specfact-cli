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
2. **ALWAYS use non-interactive mode for CI/CD**: When executing CLI commands, use appropriate flags to avoid interactive prompts that can cause timeouts in Copilot environments
3. **ALWAYS use tools for read/write**: Use file reading tools (e.g., `read_file`) to read artifacts for display purposes only. Use CLI commands for all write operations. Never use direct file manipulation.
4. **NEVER modify .specfact folder directly**: Do NOT create, modify, or delete any files in `.specfact/` folder directly. All operations must go through the CLI.
5. **NEVER write code**: Do not implement feature addition logic - the CLI handles this
6. **NEVER create YAML/JSON directly**: All plan bundle updates must be CLI-generated
7. **NEVER bypass CLI validation**: CLI ensures schema compliance and metadata - use it, don't bypass its validation
8. **Use CLI output as grounding**: Parse CLI output, don't regenerate or recreate it - use the CLI output as the source of truth
9. **NEVER manipulate internal code**: Do NOT use Python code to directly modify PlanBundle objects, Feature objects, or any internal data structures. The CLI is THE interface - use it exclusively.
10. **No internal knowledge required**: You should NOT need to know about internal implementation details (PlanBundle model, Feature class, etc.). All operations must be performed via CLI commands.
11. **NEVER read artifacts directly for updates**: Do NOT read plan bundle files directly to extract information for updates. Use CLI commands (`specfact plan select`) to get plan information.

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

1. **Loads** the existing project bundle from `.specfact/projects/<bundle-name>/`
2. **Validates** the project bundle structure
3. **Checks** if the feature key already exists (prevents duplicates)
4. **Creates** a new feature with specified metadata
5. **Adds** the feature to the project bundle (saves to `features/FEATURE-XXX.yaml`)
6. **Validates** the updated project bundle
7. **Saves** the updated project bundle

## Execution Steps

### 1. Parse Arguments and Validate Input

**Parse user input** to extract:

- `--bundle <bundle-name>` - Project bundle name (required, e.g., `legacy-api`)
- Feature key (required, e.g., `FEATURE-001`)
- Feature title (required)
- Outcomes (optional, comma-separated)
- Acceptance criteria (optional, comma-separated)

**WAIT STATE**: If required arguments are missing, ask the user:

```text
"To add a feature, I need:
- Feature key (e.g., FEATURE-001)
- Feature title

Please provide these values:
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

### 2. Check Plan Bundle Existence

**WAIT STATE**: If `--bundle` is missing, ask user for bundle name and **WAIT**:

```text
"Which project bundle should I use? (e.g., 'legacy-api', 'auth-module')
[WAIT FOR USER RESPONSE - DO NOT CONTINUE]"
```

**If bundle doesn't exist**:

- Report error: "Project bundle not found. Create one with: `specfact plan init <bundle-name>`"
- **WAIT STATE**: Ask user if they want to create a new bundle or specify a different bundle name

### 3. Execute Add Feature Command

**Execute CLI command**:

```bash
# Basic usage
specfact plan add-feature --bundle <bundle-name> --key FEATURE-001 --title "Feature Title"

# With outcomes and acceptance
specfact plan add-feature \
  --bundle <bundle-name> \
  --key FEATURE-001 \
  --title "Feature Title" \
  --outcomes "Outcome 1, Outcome 2" \
  --acceptance "Criterion 1, Criterion 2"
```

**Capture from CLI**:

- Plan bundle loaded successfully
- Feature key validation (must not already exist)
- Feature created and added
- Plan bundle saved successfully

### 4. Handle Errors

**Common errors**:

- **Feature key already exists**: Report error and suggest using `specfact plan update-feature` instead
- **Project bundle not found**: Report error and suggest creating bundle with `specfact plan init <bundle-name>`
- **Invalid plan structure**: Report validation error

### 5. Report Completion

**After successful execution**:

```markdown
✓ Feature added successfully!

**Feature**: FEATURE-001
**Title**: Feature Title
**Outcomes**: Outcome 1, Outcome 2
**Acceptance**: Criterion 1, Criterion 2
**Project Bundle**: `.specfact/projects/<bundle-name>/`

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
