# SpecFact Plan Management Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Manage project bundles: initialize new bundles, add features and stories, and update plan metadata. This unified command replaces multiple granular commands for better LLM workflow integration.

**When to use:**

- Creating a new project bundle (greenfield)
- Adding features/stories to existing bundles
- Updating plan metadata (idea, features, stories)

**Quick Example:**

```bash
/specfact.02-plan init legacy-api
/specfact.02-plan add-feature --bundle legacy-api --key FEATURE-001 --title "User Auth"
```

## Parameters

### Target/Input

- `--bundle NAME` - Project bundle name (required for most operations)
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
- Extract required parameters (bundle name, keys, etc.)

### Step 2: Execute CLI

```bash
# Initialize bundle
specfact plan init <bundle-name> [--interactive/--no-interactive] [--scaffold/--no-scaffold]

# Add feature
specfact plan add-feature --bundle <name> --key <key> --title <title> [--outcomes <outcomes>] [--acceptance <acceptance>]

# Add story
specfact plan add-story --bundle <name> --feature <feature-key> --key <story-key> --title <title> [--acceptance <acceptance>]

# Update idea
specfact plan update-idea --bundle <name> [--title <title>] [--narrative <narrative>] [--target-users <users>] [--value-hypothesis <hypothesis>] [--constraints <constraints>]

# Update feature
specfact plan update-feature --bundle <name> --key <key> [--title <title>] [--outcomes <outcomes>] [--acceptance <acceptance>] [--constraints <constraints>] [--confidence <score>] [--draft/--no-draft]

# Update story
specfact plan update-story --bundle <name> --feature <feature-key> --key <story-key> [--title <title>] [--acceptance <acceptance>] [--story-points <points>] [--value-points <points>] [--confidence <score>] [--draft/--no-draft]
```

### Step 3: Present Results

- Display bundle location
- Show created/updated features/stories
- Present summary of changes

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

1. **ALWAYS execute CLI first**: Run appropriate `specfact plan` command before any analysis
2. **ALWAYS use non-interactive mode for CI/CD**: Use `--no-interactive` flag in Copilot environments
3. **NEVER modify .specfact folder directly**: All operations must go through CLI
4. **NEVER create YAML/JSON directly**: All artifacts must be CLI-generated
5. **Use CLI output as grounding**: Parse CLI output, don't regenerate it

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
✗ Project bundle name is required
Usage: specfact plan <operation> --bundle <name> [options]
```

## Common Patterns

```bash
# Initialize new bundle
/specfact.02-plan init legacy-api
/specfact.02-plan init auth-module --no-interactive

# Add feature with full metadata
/specfact.02-plan add-feature --bundle legacy-api --key FEATURE-001 --title "User Auth" --outcomes "Secure login, Session management" --acceptance "Users can log in, Sessions persist"

# Add story to feature
/specfact.02-plan add-story --bundle legacy-api --feature FEATURE-001 --key STORY-001 --title "Login API" --acceptance "API returns JWT token" --story-points 5

# Update feature metadata
/specfact.02-plan update-feature --bundle legacy-api --key FEATURE-001 --title "Updated Title" --confidence 0.9

# Update idea section
/specfact.02-plan update-idea --bundle legacy-api --target-users "Developers, DevOps" --value-hypothesis "Reduce technical debt"
```

## Context

{ARGS}
