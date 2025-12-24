---
description: Manage project bundles - create, add features/stories, and update plan metadata.
---

# SpecFact Plan Management Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Manage project bundles: initialize, add features/stories, update metadata (idea/features/stories).

**When to use:** Creating bundles, adding features/stories, updating metadata.

**Quick:** `/specfact.02-plan init legacy-api` or `/specfact.02-plan add-feature --key FEATURE-001 --title "User Auth"`

## Parameters

### Target/Input

- `--bundle NAME` - Project bundle name (optional, defaults to active plan set via `plan select`)
- `--key KEY` - Feature/story key (e.g., FEATURE-001, STORY-001)
- `--feature KEY` - Parent feature key (for story operations)

### Output/Results

- (No output-specific parameters for plan management)

### Behavior/Options

- `--interactive/--no-interactive` - Interactive mode. Default: True (interactive)
- `--scaffold/--no-scaffold` - Create directory structure. Default: True (scaffold enabled)

### Advanced/Configuration

- `--title TEXT` - Feature/story title
- `--outcomes TEXT` - Expected outcomes (comma-separated)
- `--acceptance TEXT` - Acceptance criteria (comma-separated)
- `--constraints TEXT` - Constraints (comma-separated)
- `--confidence FLOAT` - Confidence score (0.0-1.0)
- `--draft/--no-draft` - Mark as draft

## Workflow

### Step 1: Parse Arguments

- Determine operation: `init`, `add-feature`, `add-story`, `update-idea`, `update-feature`, `update-story`
- Extract parameters (bundle name defaults to active plan if not specified, keys, etc.)

### Step 2: Execute CLI

```bash
specfact plan init <bundle-name> [--interactive/--no-interactive] [--scaffold/--no-scaffold]
specfact plan add-feature [--bundle <name>] --key <key> --title <title> [--outcomes <outcomes>] [--acceptance <acceptance>]
specfact plan add-story [--bundle <name>] --feature <feature-key> --key <story-key> --title <title> [--acceptance <acceptance>]
specfact plan update-idea [--bundle <name>] [--title <title>] [--narrative <narrative>] [--target-users <users>] [--value-hypothesis <hypothesis>] [--constraints <constraints>]
specfact plan update-feature [--bundle <name>] --key <key> [--title <title>] [--outcomes <outcomes>] [--acceptance <acceptance>] [--constraints <constraints>] [--confidence <score>] [--draft/--no-draft]
specfact plan update-story [--bundle <name>] --feature <feature-key> --key <story-key> [--title <title>] [--acceptance <acceptance>] [--story-points <points>] [--value-points <points>] [--confidence <score>] [--draft/--no-draft]
# --bundle defaults to active plan if not specified
```

### Step 3: Present Results

- Display bundle location
- Show created/updated features/stories
- Present summary of changes

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
specfact plan <operation> [--bundle <name>] [options] --no-interactive
```

**Capture**:

- CLI-generated artifacts (plan bundles, features, stories)
- Metadata (timestamps, confidence scores)
- Telemetry (execution time, file counts)

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

**Purpose**: Add semantic understanding to CLI output

**What to do**:

- Read CLI-generated artifacts (use file reading tools for display only)
- Use CLI artifacts as the source of truth for keys/structure/metadata
- Scan codebase only if asked to align the plan with implementation or to add missing features
- When scanning, compare findings against CLI artifacts and propose updates via CLI commands
- Identify missing features/stories
- Suggest confidence adjustments
- Extract business context

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` folder directly (always use CLI)
- ❌ Use direct file manipulation tools for writing (use CLI commands)

**Output**: Generate enrichment report (Markdown) or use `--batch-updates` JSON/YAML file

### Phase 3: CLI Artifact Creation (REQUIRED)

```bash
# Use enrichment to update plan via CLI
specfact plan update-feature [--bundle <name>] --key <key> [options] --no-interactive
# Or use batch updates:
specfact plan update-feature [--bundle <name>] --batch-updates <updates.json> --no-interactive
```

**Result**: Final artifacts are CLI-generated with validated enrichments

**Note**: If code generation is needed, use the validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code))

## Expected Output

## Success (Init)

```text
✓ Project bundle created: .specfact/projects/legacy-api/
✓ Bundle initialized with scaffold structure
```

## Success (Add Feature)

```text
✓ Feature 'FEATURE-001' added successfully
Feature: User Authentication
Outcomes: Secure login, Session management
```

## Error (Missing Bundle)

```text
✗ Project bundle name is required (or set active plan with 'plan select')
Usage: specfact plan <operation> [--bundle <name>] [options]
```

## Common Patterns

```bash
/specfact.02-plan init legacy-api
/specfact.02-plan add-feature --key FEATURE-001 --title "User Auth" --outcomes "Secure login" --acceptance "Users can log in"
/specfact.02-plan add-story --feature FEATURE-001 --key STORY-001 --title "Login API" --acceptance "API returns JWT"
/specfact.02-plan update-feature --key FEATURE-001 --title "Updated Title" --confidence 0.9
/specfact.02-plan update-idea --target-users "Developers, DevOps" --value-hypothesis "Reduce technical debt"
# --bundle defaults to active plan if not specified
```

## Context

{ARGS}
