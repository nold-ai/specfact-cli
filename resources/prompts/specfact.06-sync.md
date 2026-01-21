---
description: Sync changes between external tool artifacts and SpecFact using bridge architecture.
---

# SpecFact Sync Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Synchronize artifacts from external tools (Spec-Kit, Linear, Jira) with SpecFact project bundles using bridge mappings. Supports bidirectional sync.

**When to use:** Syncing with Spec-Kit, integrating external tools, maintaining consistency.

**Quick:** `/specfact.06-sync --adapter speckit --repo . --bidirectional` or `/specfact.06-sync --bundle legacy-api --watch`

## Parameters

### Target/Input

- `--repo PATH` - Path to repository. Default: current directory (.)
- `--bundle NAME` - Project bundle name for SpecFact → tool conversion. Default: auto-detect

### Behavior/Options

- `--bidirectional` - Enable bidirectional sync (tool ↔ SpecFact). Default: False
- `--overwrite` - Overwrite existing tool artifacts. Default: False
- `--watch` - Watch mode for continuous sync. Default: False
- `--ensure-compliance` - Validate and auto-enrich for tool compliance. Default: False

### Advanced/Configuration

- `--adapter TYPE` - Adapter type (speckit, generic-markdown, openspec, github, ado). Default: auto-detect
- `--interval SECONDS` - Watch interval in seconds. Default: 5 (range: 1+)

**GitHub Adapter Options (for backlog sync):**

- `--repo-owner OWNER` - GitHub repository owner (required for GitHub backlog sync)
- `--repo-name NAME` - GitHub repository name (required for GitHub backlog sync)
- `--github-token TOKEN` - GitHub API token (optional, uses GITHUB_TOKEN env var or gh CLI if not provided)
- `--use-gh-cli/--no-gh-cli` - Use GitHub CLI (`gh auth token`) to get token automatically (default: True)

**Azure DevOps Adapter Options (for backlog sync):**

- `--ado-org ORG` - Azure DevOps organization (required for ADO backlog sync)
- `--ado-project PROJECT` - Azure DevOps project (required for ADO backlog sync)
- `--ado-base-url URL` - Azure DevOps base URL (optional, defaults to <https://dev.azure.com>). Use for Azure DevOps Server (on-prem)
- `--ado-token TOKEN` - Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var if not provided)
- `--ado-work-item-type TYPE` - Azure DevOps work item type (optional, derived from process template if not provided)

## Workflow

### Step 1: Parse Arguments

- Extract repository path (default: current directory)
- Extract adapter type (default: auto-detect)
- Extract sync options (bidirectional, overwrite, watch, etc.)

### Step 2: Execute CLI

```bash
# Spec-Kit adapter (default)
specfact sync bridge --adapter speckit --repo <path> [--bidirectional] [--bundle <name>] [--overwrite] [--watch] [--interval <seconds>]

# GitHub adapter (for backlog sync)
specfact sync bridge --adapter github --repo <path> --repo-owner <owner> --repo-name <name> [--bidirectional] [--bundle <name>] [--github-token <token>] [--use-gh-cli]

# Azure DevOps adapter (for backlog sync)
specfact sync bridge --adapter ado --repo <path> --ado-org <org> --ado-project <project> [--bidirectional] [--bundle <name>] [--ado-token <token>] [--ado-base-url <url>]

# --bundle defaults to active plan if not specified
```

### Step 3: Present Results

- Display sync direction and adapter used
- Show artifacts synchronized
- Present conflict resolution (if any)
- Indicate watch status (if enabled)

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

- Execute CLI first - never create artifacts directly
- Use `--no-interactive` flag in CI/CD environments
- Never modify `.specfact/` or `.specify/` directly
- Use CLI output as grounding for validation
- Code generation requires LLM (only via AI IDE slash prompts, not CLI-only)

## Dual-Stack Workflow (Copilot Mode)

When in copilot mode, follow this three-phase workflow:

### Phase 1: CLI Grounding (REQUIRED)

```bash
# Execute CLI to get structured output
specfact sync bridge --adapter <adapter> --repo <path> [options] --no-interactive
```

**Capture**:

- CLI-generated sync results
- Artifacts synchronized
- Conflict resolution status

### Phase 2: LLM Enrichment (OPTIONAL, Copilot Only)

**Purpose**: Add semantic understanding to sync results

**What to do**:

- Read CLI-generated sync results (use file reading tools for display only)
- Treat CLI sync output as the source of truth; scan codebase only to explain conflicts
- Research codebase for context on conflicts
- Suggest resolution strategies

**What NOT to do**:

- ❌ Create YAML/JSON artifacts directly
- ❌ Modify CLI artifacts directly (use CLI commands to update)
- ❌ Bypass CLI validation
- ❌ Write to `.specfact/` or `.specify/` folders directly (always use CLI)

**Output**: Generate conflict resolution suggestions (Markdown)

### Phase 3: CLI Artifact Creation (REQUIRED)

```bash
# Apply resolutions via CLI commands, then re-sync
specfact plan update-feature [--bundle <name>] [options] --no-interactive
specfact sync bridge --adapter <adapter> --repo <path> --no-interactive
```

**Result**: Final artifacts are CLI-generated with validated resolutions

**Note**: If code generation is needed, use the validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code))

## Expected Output

### Success

```text
✓ Sync complete: Spec-Kit ↔ SpecFact (bidirectional)

Adapter: speckit
Repository: /path/to/repo

Artifacts Synchronized:
  - Spec-Kit → SpecFact: 12 features, 45 stories
  - SpecFact → Spec-Kit: 3 new features, 8 updated stories

Conflicts Resolved: 2
```

### Error (Missing Adapter)

```text
✗ Unsupported adapter: invalid-adapter
Supported adapters: speckit, generic-markdown, openspec, github, ado
```

### Error (Missing Required Parameters)

```text
✗ GitHub adapter requires both --repo-owner and --repo-name options
Example: specfact sync bridge --adapter github --repo-owner 'nold-ai' --repo-name 'specfact-cli' --bidirectional
```

```text
✗ Azure DevOps adapter requires both --ado-org and --ado-project options
Example: specfact sync bridge --adapter ado --ado-org 'my-org' --ado-project 'my-project' --bidirectional
```

## Common Patterns

```bash
# Spec-Kit adapter
/specfact.06-sync --adapter speckit --repo . --bidirectional
/specfact.06-sync --adapter speckit --repo . --bundle legacy-api
/specfact.06-sync --adapter speckit --repo . --watch --interval 5
/specfact.06-sync --repo . --bidirectional  # Auto-detect adapter

# GitHub adapter (backlog sync)
/specfact.06-sync --adapter github --repo . --repo-owner nold-ai --repo-name specfact-cli --bidirectional

# Azure DevOps adapter (backlog sync)
/specfact.06-sync --adapter ado --repo . --ado-org my-org --ado-project my-project --bidirectional
```

## Context

{ARGS}
