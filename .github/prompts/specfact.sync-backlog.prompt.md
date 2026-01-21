# SpecFact Sync Backlog Command

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Sync OpenSpec change proposals to DevOps backlog tools (GitHub Issues, ADO, Linear, Jira) with AI-assisted content sanitization. Supports export-only sync from OpenSpec change proposals to DevOps issues.

**When to use:** Creating backlog issues from OpenSpec change proposals, syncing change status to DevOps tools, managing public vs internal issue content.

**Quick:** `/specfact.sync-backlog --adapter github` or `/specfact.sync-backlog --sanitize --target-repo owner/repo`

## Parameters

### Target/Input

- `--repo PATH` - Path to OpenSpec repository containing change proposals. Default: current directory (.)
- `--code-repo PATH` - Path to source code repository for code change detection (default: same as `--repo`). **Required when OpenSpec repository differs from source code repository.** For example, if OpenSpec proposals are in `specfact-cli-internal` but source code is in `specfact-cli`, use `--repo /path/to/specfact-cli-internal --code-repo /path/to/specfact-cli`.
- `--target-repo OWNER/REPO` - Target repository for issue creation (format: owner/repo). Default: same as code repository

### Behavior/Options

- `--sanitize/--no-sanitize` - Sanitize proposal content for public issues (default: auto-detect based on repo setup)
  - Auto-detection: If code repo != planning repo → sanitize, if same repo → no sanitization
  - `--sanitize`: Force sanitization (removes competitive analysis, internal strategy, implementation details)
  - `--no-sanitize`: Skip sanitization (use full proposal content)
  - **Proposal Filtering**: The sanitization flag also controls which proposals are synced:
    - **Public repos** (`--sanitize`): Only syncs proposals with status `"applied"` (archived/completed changes)
    - **Internal repos** (`--no-sanitize`): Syncs all active proposals (`"proposed"`, `"in-progress"`, `"applied"`, `"deprecated"`, `"discarded"`)
    - Filtering prevents premature exposure of work-in-progress proposals to public repositories
- `--interactive` - Interactive mode for AI-assisted sanitization (requires slash command)
  - Enables interactive change selection
  - Enables per-change sanitization selection
  - Enables LLM review workflow for sanitized proposals
- `--change-ids IDS` - Comma-separated list of change proposal IDs to export (default: all active proposals)
  - Example: `--change-ids add-devops-backlog-tracking,add-change-tracking-datamodel`
  - Only used in non-interactive mode (interactive mode prompts for selection)
- `--export-to-tmp` - Export proposal content to temporary file for LLM review (sanitization workflow)
  - Creates `/tmp/specfact-proposal-<change-id>.md` for each proposal
  - Used internally by slash command for sanitization review
- `--import-from-tmp` - Import sanitized content from temporary file (sanitization workflow)
  - Reads `/tmp/specfact-proposal-<change-id>-sanitized.md` for each proposal
  - Used internally by slash command after LLM review
- `--tmp-file PATH` - Specify temporary file path (used with --export-to-tmp or --import-from-tmp)
  - Default: `/tmp/specfact-proposal-<change-id>.md` or `/tmp/specfact-proposal-<change-id>-sanitized.md`

### Code Change Tracking (Advanced)

- `--track-code-changes/--no-track-code-changes` - Detect code changes (git commits, file modifications) and add progress comments to existing issues (default: False)
  - **Repository Selection**: Uses `--code-repo` if provided, otherwise uses `--repo` for code change detection
  - **Git Commit Detection**: Searches git log for commits mentioning the change proposal ID (e.g., `add-code-change-tracking`)
  - **File Change Tracking**: Extracts files modified in detected commits
  - **Progress Comment Generation**: Formats comment with commit details and file changes
  - **Duplicate Prevention**: Checks against existing comments to avoid duplicates
  - **Source Tracking Update**: Updates `proposal.md` with progress metadata
- `--add-progress-comment/--no-add-progress-comment` - Add manual progress comment to existing issues without code change detection (default: False)
- `--update-existing/--no-update-existing` - Update existing issue bodies when proposal content changes (default: False for safety). Uses content hash to detect changes.

### Advanced/Configuration

- `--adapter TYPE` - DevOps adapter type (github, ado, linear, jira). Default: github

**GitHub Adapter Options:**

- `--repo-owner OWNER` - Repository owner (for GitHub adapter). Optional, can use bridge config
- `--repo-name NAME` - Repository name (for GitHub adapter). Optional, can use bridge config
- `--github-token TOKEN` - GitHub API token (optional, uses GITHUB_TOKEN env var or gh CLI if not provided)
- `--use-gh-cli/--no-gh-cli` - Use GitHub CLI (`gh auth token`) to get token automatically (default: True). Useful in enterprise environments where PAT creation is restricted

**Azure DevOps Adapter Options:**

- `--ado-org ORG` - Azure DevOps organization (required for ADO adapter)
- `--ado-project PROJECT` - Azure DevOps project (required for ADO adapter)
- `--ado-base-url URL` - Azure DevOps base URL (optional, defaults to <https://dev.azure.com>). Use for Azure DevOps Server (on-prem)
- `--ado-token TOKEN` - Azure DevOps PAT (optional, uses AZURE_DEVOPS_TOKEN env var if not provided). Requires Work Items (Read & Write) permissions
- `--ado-work-item-type TYPE` - Azure DevOps work item type (optional, derived from process template if not provided). Examples: 'User Story', 'Product Backlog Item', 'Bug'

## Workflow

### Step 1: Parse Arguments

- Extract repository path (default: current directory)
- Extract adapter type (default: github)
- Extract sanitization preference (default: auto-detect)
- Extract target repository (default: same as code repo)

### Step 2: Interactive Change Selection (Slash Command Only)

**When using slash command** (`/specfact.sync-backlog`), provide interactive selection:

1. **List available change proposals**:
   - Read OpenSpec change proposals from `openspec/changes/` (including archived proposals)
   - Display list with: change ID, title, status, existing issue (if any)
   - Format: `[1] add-devops-backlog-tracking (applied) - Issue #17`
   - Format: `[2] add-change-tracking-datamodel (proposed) - No issue`
   - **Note**: When `--sanitize` is used, only proposals with status `"applied"` will be synced to public repos

2. **User selection**:
   - Prompt: "Select changes to export (comma-separated numbers, 'all', or 'none'):"
   - Parse selection (e.g., "1,3" or "all")
   - Validate selection against available proposals

3. **Per-change sanitization selection**:
   - For each selected change, prompt: "Sanitize '[change-title]'? (y/n/auto):"
   - `y`: Force sanitization
   - `n`: Skip sanitization
   - `auto`: Use auto-detection (code repo != planning repo)
   - Store selection: `{change_id: sanitize_choice}`

**When using CLI directly** (non-interactive):

- **Public repos** (`--sanitize`): Only exports proposals with status `"applied"` (archived/completed)
- **Internal repos** (`--no-sanitize`): Exports all active proposals regardless of status
- Use `--sanitize/--no-sanitize` flag to control filtering behavior
- No per-change selection

### Step 3: Execute CLI (Initial Pass)

**For non-sanitized proposals** (direct export):

```bash
# GitHub adapter
specfact sync bridge --adapter github --mode export-only --repo <openspec-path> \
  --no-sanitize --change-ids <id1,id2> \
  [--code-repo <source-code-path>] \
  [--track-code-changes] [--add-progress-comment] \
  [--target-repo <owner/repo>] [--repo-owner <owner>] [--repo-name <name>] \
  [--github-token <token>] [--use-gh-cli]

# Azure DevOps adapter
specfact sync bridge --adapter ado --mode export-only --repo <openspec-path> \
  --no-sanitize --change-ids <id1,id2> \
  [--code-repo <source-code-path>] \
  [--track-code-changes] [--add-progress-comment] \
  --ado-org <org> --ado-project <project> \
  [--ado-token <token>] [--ado-base-url <url>] [--ado-work-item-type <type>]
```

**For sanitized proposals** (requires LLM review):

```bash
# Step 3a: Export to temporary file for LLM review (GitHub)
specfact sync bridge --adapter github --mode export-only --repo <openspec-path> \
  --sanitize --change-ids <id1,id2> \
  [--code-repo <source-code-path>] \
  --export-to-tmp --tmp-file /tmp/specfact-proposal-<change-id>.md \
  [--target-repo <owner/repo>] [--repo-owner <owner>] [--repo-name <name>] \
  [--github-token <token>] [--use-gh-cli]

# Step 3a: Export to temporary file for LLM review (ADO)
specfact sync bridge --adapter ado --mode export-only --repo <openspec-path> \
  --sanitize --change-ids <id1,id2> \
  [--code-repo <source-code-path>] \
  --export-to-tmp --tmp-file /tmp/specfact-proposal-<change-id>.md \
  --ado-org <org> --ado-project <project> \
  [--ado-token <token>] [--ado-base-url <url>]
```

**Note**: When `--code-repo` is provided, code change detection uses that repository. Otherwise, code changes are detected in the OpenSpec repository (`--repo`).

### Step 4: LLM Sanitization Review (Slash Command Only, For Sanitized Proposals)

**Only execute if sanitization is required**:

1. **Read temporary file**:
   - Read `/tmp/specfact-proposal-<change-id>.md` for each sanitized proposal
   - Display original content to user

2. **LLM sanitization**:
   - Review proposal content for:
     - Competitive analysis sections (remove)
     - Market positioning statements (remove)
     - Implementation details (file paths, code structure - remove or generalize)
     - Effort estimates and timelines (remove)
     - Internal strategy sections (remove)
   - Preserve:
     - User-facing value propositions
     - High-level feature descriptions
     - Acceptance criteria (user-facing)
     - External documentation links

3. **Generate sanitized content**:
   - Create sanitized version with removed sections/patterns
   - Write to `/tmp/specfact-proposal-<change-id>-sanitized.md`
   - Display diff (original vs sanitized) for user review

4. **User approval**:
   - Prompt: "Approve sanitized content? (y/n/edit):"
   - `y`: Proceed to Step 5
   - `n`: Skip this proposal
   - `edit`: Allow user to manually edit sanitized file, then proceed

### Step 5: Execute CLI (Final Export)

**For sanitized proposals** (after LLM review):

```bash
# Step 5a: Import sanitized content from temporary file (GitHub)
specfact sync bridge --adapter github --mode export-only --repo <path> \
  --import-from-tmp --tmp-file /tmp/specfact-proposal-<change-id>-sanitized.md \
  --change-ids <id1,id2> \
  [--target-repo <owner/repo>] [--repo-owner <owner>] [--repo-name <name>] \
  [--github-token <token>] [--use-gh-cli]

# Step 5a: Import sanitized content from temporary file (ADO)
specfact sync bridge --adapter ado --mode export-only --repo <path> \
  --import-from-tmp --tmp-file /tmp/specfact-proposal-<change-id>-sanitized.md \
  --change-ids <id1,id2> \
  --ado-org <org> --ado-project <project> \
  [--ado-token <token>] [--ado-base-url <url>]
```

**For non-sanitized proposals** (already exported in Step 3):

- No additional CLI call needed

### Step 6: Present Results

- Display sync results (issues created/updated)
- Show issue URLs and numbers
- Indicate sanitization status (if applied)
- List which proposals were sanitized vs exported directly
- **Show code change tracking results** (if `--track-code-changes` was enabled):
  - Number of commits detected
  - Number of progress comments added
  - Repository used for code change detection (`--code-repo` or `--repo`)
- **Show filtering warnings** (if proposals were filtered out due to status)
  - Example: `⚠ Filtered out 2 proposal(s) with non-applied status (public repos only sync archived/completed proposals)`
- Present any warnings or errors

## CLI Enforcement

**CRITICAL**: Always use SpecFact CLI commands. See [CLI Enforcement Rules](./shared/cli-enforcement.md) for details.

**Rules:**

- Execute CLI first - never create artifacts directly
- Use `--no-interactive` flag in CI/CD environments
- Never modify `.specfact/` or `openspec/` directly
- Use CLI output as grounding for validation
- Code generation requires LLM (only via AI IDE slash prompts, not CLI-only)

## Dual-Stack Workflow (Copilot Mode)

When in copilot mode, follow this workflow:

### Phase 1: Interactive Selection (Slash Command Only)

**Purpose**: Allow user to select which changes to export and sanitization preferences

**What to do**:

1. **List available proposals**:
   - Read `openspec/changes/` directory (including `archive/` subdirectory)
   - Parse `proposal.md` files to extract: change_id, title, status
   - Check for existing issues via `source_tracking` section
   - Display numbered list to user
   - **Note**: When `--sanitize` is used, only proposals with status `"applied"` will be available for public repos

2. **User selection**:
   - Prompt for change selection (comma-separated numbers, 'all', 'none')
   - For each selected change, prompt for sanitization preference (y/n/auto)
   - Store selections: `{change_id: {selected: bool, sanitize: bool|None}}`

**Output**: Dictionary mapping change IDs to selection and sanitization preferences

### Phase 2: CLI Export to Temporary Files (For Sanitized Proposals Only)

**Purpose**: Export proposal content to temporary files for LLM review

**When**: Only for proposals where `sanitize=True`

**What to do**:

```bash
# For each sanitized proposal, export to temp file (GitHub)
specfact sync bridge --adapter github --mode export-only --repo <openspec-path> \
  --change-ids <change-id> --export-to-tmp --tmp-file /tmp/specfact-proposal-<change-id>.md \
  [--code-repo <source-code-path>] \
  [--repo-owner <owner>] [--repo-name <name>] [--github-token <token>] [--use-gh-cli]

# For each sanitized proposal, export to temp file (ADO)
specfact sync bridge --adapter ado --mode export-only --repo <openspec-path> \
  --change-ids <change-id> --export-to-tmp --tmp-file /tmp/specfact-proposal-<change-id>.md \
  [--code-repo <source-code-path>] \
  --ado-org <org> --ado-project <project> [--ado-token <token>] [--ado-base-url <url>]
```

**Capture**:

- Temporary file paths for each proposal
- Original proposal content (for comparison)

**What NOT to do**:

- ❌ Create GitHub issues directly (wait for sanitization review)
- ❌ Skip LLM review for sanitized proposals

### Phase 3: LLM Sanitization Review (For Sanitized Proposals Only)

**Purpose**: Review and sanitize proposal content before creating public issues

**When**: Only for proposals where `sanitize=True`

**What to do**:

1. **Read temporary file**:
   - Read `/tmp/specfact-proposal-<change-id>.md` for each sanitized proposal
   - Display original content to user

2. **LLM sanitization**:
   - Review proposal content section by section
   - Remove:
     - Competitive analysis sections (`## Competitive Analysis`)
     - Market positioning statements (`## Market Positioning`)
     - Implementation details (file paths like `src/specfact_cli/...`, code structure)
     - Effort estimates and timelines
     - Internal strategy sections
   - Preserve:
     - User-facing value propositions
     - High-level feature descriptions (without file paths)
     - Acceptance criteria (user-facing)
     - External documentation links

3. **Generate sanitized content**:
   - Create sanitized version with removed sections/patterns
   - Write to `/tmp/specfact-proposal-<change-id>-sanitized.md`
   - Display diff (original vs sanitized) for user review

4. **User approval**:
   - Prompt: "Approve sanitized content for '[change-title]'? (y/n/edit):"
   - `y`: Proceed to Phase 4
   - `n`: Skip this proposal (don't create issue)
   - `edit`: Allow user to manually edit sanitized file, then proceed

**Output**: Sanitized content files in `/tmp/specfact-proposal-<change-id>-sanitized.md`

**What NOT to do**:

- ❌ Create GitHub issues directly (use CLI in Phase 4)
- ❌ Modify original proposal files
- ❌ Skip user approval step

### Phase 4: CLI Direct Export (For Non-Sanitized Proposals)

**Purpose**: Export proposals that don't require sanitization

**When**: For proposals where `sanitize=False`

**What to do**:

```bash
# Export non-sanitized proposals directly (GitHub)
specfact sync bridge --adapter github --mode export-only --repo <openspec-path> \
  --change-ids <id1,id2> --no-sanitize \
  [--code-repo <source-code-path>] \
  [--track-code-changes] [--add-progress-comment] \
  [--repo-owner <owner>] [--repo-name <name>] [--github-token <token>] [--use-gh-cli]

# Export non-sanitized proposals directly (ADO)
specfact sync bridge --adapter ado --mode export-only --repo <openspec-path> \
  --change-ids <id1,id2> --no-sanitize \
  [--code-repo <source-code-path>] \
  [--track-code-changes] [--add-progress-comment] \
  --ado-org <org> --ado-project <project> [--ado-token <token>] [--ado-base-url <url>]
```

**Result**: Issues created directly without LLM review

### Phase 5: CLI Import Sanitized Content (For Sanitized Proposals Only)

**Purpose**: Create GitHub issues from LLM-reviewed sanitized content

**When**: Only for proposals where `sanitize=True` and user approved

**What to do**:

```bash
# For each approved sanitized proposal, import from temp file and create issue (GitHub)
specfact sync bridge --adapter github --mode export-only --repo <openspec-path> \
  --change-ids <change-id> --import-from-tmp --tmp-file /tmp/specfact-proposal-<change-id>-sanitized.md \
  [--code-repo <source-code-path>] \
  [--track-code-changes] [--add-progress-comment] \
  [--repo-owner <owner>] [--repo-name <name>] [--github-token <token>] [--use-gh-cli]

# For each approved sanitized proposal, import from temp file and create work item (ADO)
specfact sync bridge --adapter ado --mode export-only --repo <openspec-path> \
  --change-ids <change-id> --import-from-tmp --tmp-file /tmp/specfact-proposal-<change-id>-sanitized.md \
  [--code-repo <source-code-path>] \
  [--track-code-changes] [--add-progress-comment] \
  --ado-org <org> --ado-project <project> [--ado-token <token>] [--ado-base-url <url>]
```

**Result**: Issues created with sanitized content

**What NOT to do**:

- ❌ Create GitHub issues directly via API (use CLI command)
- ❌ Skip CLI validation
- ❌ Modify `.specfact/` or `openspec/` folders directly

### Phase 6: Cleanup and Results

**Purpose**: Clean up temporary files and present results

**What to do**:

1. **Cleanup**:
   - Remove temporary files: `/tmp/specfact-proposal-*.md`
   - Remove sanitized files: `/tmp/specfact-proposal-*-sanitized.md`

2. **Present results**:
   - Display sync results (issues created/updated)
   - Show issue URLs and numbers
   - Indicate which proposals were sanitized vs exported directly
   - **Show code change tracking results** (if `--track-code-changes` was enabled):
     - Number of commits detected per proposal
     - Number of progress comments added per issue
     - Repository used for code change detection (`--code-repo` or `--repo`)
     - Example: `✓ Detected 3 commits for 'add-feature-x', added 1 progress comment to issue #123`
   - **Show filtering warnings** (if proposals were filtered out):
     - Public repos: `⚠ Filtered out N proposal(s) with non-applied status (public repos only sync archived/completed proposals)`
     - Internal repos: `⚠ Filtered out N proposal(s) without source tracking entry and inactive status`
   - Present any warnings or errors

**Note**: If code generation is needed, use the validation loop pattern (see [CLI Enforcement Rules](./shared/cli-enforcement.md#standard-validation-loop-pattern-for-llm-generated-code))

## Expected Output

### Success

```text
✓ Successfully synced 3 change proposals

Adapter: github
Repository: nold-ai/specfact-cli-internal
Code Repository: nold-ai/specfact-cli (separate repo)

Issues Created:
  - #14: Add DevOps Backlog Tracking Integration
  - #15: Add Change Tracking Data Model
  - #16: Implement OpenSpec Bridge Adapter

Sanitization: Applied (different repos detected)
Issue IDs saved to OpenSpec proposal files
```

### Success (With Code Change Tracking)

```text
✓ Successfully synced 3 change proposals

Adapter: github
Repository: nold-ai/specfact-cli-internal
Code Repository: nold-ai/specfact-cli (separate repo)

Issues Created:
  - #14: Add DevOps Backlog Tracking Integration
  - #15: Add Change Tracking Data Model
  - #16: Implement OpenSpec Bridge Adapter

Code Change Tracking:
  - Detected 5 commits for 'add-devops-backlog-tracking'
  - Added 1 progress comment to issue #14
  - Detected 3 commits for 'add-change-tracking-datamodel'
  - Added 1 progress comment to issue #15
  - No new commits detected for 'implement-openspec-bridge-adapter'

Sanitization: Applied (different repos detected)
Issue IDs saved to OpenSpec proposal files
```

### Error (Missing Token)

```text
✗ Sync failed: Missing GitHub API token
Provide token via --github-token, GITHUB_TOKEN env var, or --use-gh-cli
```

### Warning (Sanitization Applied)

```text
⚠ Content sanitization applied (code repo != planning repo)
Competitive analysis and internal strategy sections removed
```

### Warning (Proposals Filtered - Public Repo)

```text
✓ Successfully synced 1 change proposals
⚠ Filtered out 2 proposal(s) with non-applied status (public repos only sync archived/completed proposals, regardless of source tracking). Only 1 applied proposal(s) will be synced.
```

### Warning (Proposals Filtered - Internal Repo)

```text
✓ Successfully synced 3 change proposals
⚠ Filtered out 1 proposal(s) without source tracking entry for target repo and inactive status. Only 3 proposal(s) will be synced.
```

## Common Patterns

```bash
# Public repo: only syncs "applied" proposals (archived changes)
/specfact.sync-backlog --adapter github --sanitize --target-repo nold-ai/specfact-cli

# Internal repo: syncs all active proposals (proposed, in-progress, applied, etc.)
/specfact.sync-backlog --adapter github --no-sanitize --target-repo nold-ai/specfact-cli-internal

# Auto-detect sanitization (filters based on repo setup)
/specfact.sync-backlog --adapter github

# Explicit repository configuration (GitHub)
/specfact.sync-backlog --adapter github --repo-owner nold-ai --repo-name specfact-cli-internal

# Azure DevOps adapter (requires org and project)
/specfact.sync-backlog --adapter ado --ado-org my-org --ado-project my-project

# Use GitHub CLI for token (enterprise-friendly)
/specfact.sync-backlog --adapter github --use-gh-cli
```

## Context

{ARGS}
