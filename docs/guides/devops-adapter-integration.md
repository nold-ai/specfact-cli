---
layout: default
title: DevOps Adapter Integration Guide
permalink: /guides/devops-adapter-integration/
---

# DevOps Adapter Integration Guide

> **🆕 NEW FEATURE: Integrate SpecFact into Agile DevOps Workflows**  
> Bidirectional synchronization between OpenSpec change proposals and DevOps backlog tools enables seamless integration of specification-driven development into your existing agile workflows.

This guide explains how to integrate SpecFact CLI with DevOps backlog tools (GitHub Issues, Azure DevOps, Linear, Jira) to sync OpenSpec change proposals and track implementation progress through automated comment annotations.

## Policy Readiness in DevOps Flows

You can validate policy readiness (DoR/DoD, Kanban flow gates, SAFe PI hooks) before posting updates back to
your backlog system:

```bash
# Deterministic policy validation with JSON + Markdown output
specfact policy validate --repo . --format both

# AI-assisted suggestions with confidence scores and patch-ready output
specfact policy suggest --repo .
```

Both commands read `.specfact/policy.yaml`. `policy suggest` never writes changes automatically; it emits
recommendations you can review and apply explicitly in your normal workflow.

## Overview

**Why This Matters**: This feature bridges the gap between specification management (OpenSpec) and backlog management (GitHub Issues, ADO, Linear, Jira), allowing you to use SpecFact's specification-driven development approach while working within your existing agile DevOps workflows.

SpecFact CLI supports **bidirectional synchronization** between OpenSpec change proposals and DevOps backlog tools:

- **Issue Creation**: Export OpenSpec change proposals as GitHub Issues (or other DevOps backlog items)
- **Progress Tracking**: Automatically detect code changes and add progress comments to issues
- **Standup Comments**: Use `specfact backlog daily --post` with `--yesterday`, `--today`, `--blockers` to post
  a standup summary as a comment on the linked issue (GitHub/ADO adapters that support comments). Standup
  config: set defaults via env (`SPECFACT_STANDUP_STATE`, `SPECFACT_STANDUP_LIMIT`,
  `SPECFACT_STANDUP_ASSIGNEE`, `SPECFACT_STANDUP_SPRINT_END`) or optional `.specfact/standup.yaml`
  (e.g. `default_state`, `limit`, `sprint`, `show_priority`, `suggest_next`). Iteration/sprint and sprint
  end date support depend on the adapter (ADO supports current iteration and iteration path; see adapter
  docs). Use `--blockers-first` and config `show_priority`/`show_value` for time-critical and value-driven
  standups. **Interactive review** (`--interactive`): step-through stories with arrow-key selection; detail
  view shows the **latest comment** and hints when older comments exist; interactive navigation includes
  **Post standup update** to post yesterday/today/blockers directly on the currently selected story.
  **Comment annotations in exports**:
  add `--comments` (alias `--annotations`) to include descriptions and comment annotations in
  `--copilot-export` and `--summarize`/`--summarize-to` outputs when the adapter supports fetching comments
  (GitHub and ADO). Use optional `--first-comments N` or `--last-comments N` to scope comment volume;
  default is full comment context. Use `--first-issues N` / `--last-issues N` and global filters
  `--search`, `--release`, `--id` for consistent backlog scope across daily/refine commands. **Value score /
  suggested next**: when BacklogItem has `story_points`, `business_value`, and `priority`, use
  `--suggest-next` or config `suggest_next` to show suggested next item (business_value / (story_points ×
  priority)). **Standup summary prompt** (`--summarize` or `--summarize-to PATH`): output a prompt
  (instruction + filter context + standup data) for slash command or Copilot to generate a standup summary.
  **Slash prompt** `specfact.backlog-daily` (or `specfact.daily`): use with IDE/Copilot for interactive
  team walkthrough story-by-story (current focus, issues/open questions, discussion notes as comments);
  prompt file at `resources/prompts/specfact.backlog-daily.md`. **Sprint goal** is stored in your
  board/sprint settings and is not displayed or edited by the CLI.
- **Content Sanitization**: Protect internal information when syncing to public repositories
- **Separate Repository Support**: Handle cases where OpenSpec proposals and source code are in different repositories

## Supported Adapters

Currently supported DevOps adapters:

- **GitHub Issues** (`--adapter github`) - Full support for issue creation and progress comments
- **Azure DevOps** (`--adapter ado`) - ✅ Available - Work item creation, status sync, progress tracking, and interactive field mapping
- **Linear** (`--adapter linear`) - Planned
- **Jira** (`--adapter jira`) - Planned

This guide focuses on GitHub Issues integration. Azure DevOps integration follows similar patterns with ADO-specific configuration.

**Azure DevOps Field Mapping**: Use `specfact backlog map-fields` to interactively discover and map ADO fields for your specific process template. See [Custom Field Mapping Guide](./custom-field-mapping.md) for complete documentation.

**Related**: See [Backlog Refinement Guide](../guides/backlog-refinement.md) 🆕 **NEW FEATURE** for AI-assisted template-driven refinement of backlog items with persona/framework filtering, sprint/iteration support, DoR validation, and preview/write safety.

---

## Quick Start

### 1. Create Change Proposal

Create an OpenSpec change proposal in your OpenSpec repository:

```bash
# Structure: openspec/changes/<change-id>/proposal.md
mkdir -p openspec/changes/add-feature-x
cat > openspec/changes/add-feature-x/proposal.md << 'EOF'
# Add Feature X

## Summary

Add new feature X to improve user experience.

## Status

- status: proposed

## Implementation Plan

1. Design API endpoints
2. Implement backend logic
3. Add frontend components
4. Write tests
EOF
```

### 2. Export to GitHub Issues

Export the change proposal to create a GitHub issue:

```bash
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --repo /path/to/openspec-repo
```

### 3. Track Code Changes

As you implement the feature, track progress automatically:

```bash
# Make commits with change ID in commit message
git commit -m "feat: implement add-feature-x - initial API design"

# Track progress (detects commits and adds comments)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --track-code-changes \
  --repo /path/to/openspec-repo \
  --code-repo /path/to/source-code-repo  # If different from OpenSpec repo
```

---

## GitHub Issues Integration

### Prerequisites

**For Issue Creation:**

- OpenSpec change proposals in `openspec/changes/<change-id>/proposal.md`
- GitHub token (via `GITHUB_TOKEN` env var, `gh auth token`, or `--github-token`)
- Repository access permissions (read for proposals, write for issues)

**For Code Change Tracking:**

- Issues must already exist (created via previous sync)
- Git repository with commits mentioning the change proposal ID in commit messages
- If OpenSpec and source code are in separate repositories, use `--code-repo` parameter

### Authentication

SpecFact CLI supports multiple authentication methods:

> **Auth Reference**: See [Authentication](../reference/authentication.md) for device code flows, token storage, and adapter token precedence.

**Option 1: Device Code (SSO-friendly)**

```bash
specfact backlog auth github
# or use a custom OAuth app
specfact backlog auth github --client-id YOUR_CLIENT_ID
```

**Note:** The default client ID works only for `https://github.com`. For GitHub Enterprise, provide `--client-id` or set `SPECFACT_GITHUB_CLIENT_ID`.

**Option 2: GitHub CLI (Recommended)**

```bash
# Uses gh auth token automatically
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --use-gh-cli
```

**Option 3: Environment Variable**

```bash
export GITHUB_TOKEN=ghp_your_token_here
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo
```

**Option 4: Command Line Flag**

```bash
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --github-token ghp_your_token_here
```

### Basic Usage

#### Create Issues from Change Proposals

```bash
# Export all active proposals to GitHub Issues
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --repo /path/to/openspec-repo
```

#### Track Code Changes

```bash
# Detect code changes and add progress comments
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --track-code-changes \
  --repo /path/to/openspec-repo
```

#### Sync Specific Proposals

```bash
# Export only specific change proposals
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --change-ids add-feature-x,update-api \
  --repo /path/to/openspec-repo
```

### Project backlog context (.specfact/backlog.yaml)

Store project-level adapter context (org, repo, project per adapter) so you do not have to pass `--repo-owner`, `--repo-name`, `--ado-org`, `--ado-project`, or `--ado-team` on every backlog command after authenticating once.

**Resolution order**: Explicit CLI options override environment variables; environment variables override the config file. **Tokens are never read from the file**—only from CLI or env.

**Config search path**: `SPECFACT_CONFIG_DIR` (if set) or `.specfact/` in the current working directory. File name: `backlog.yaml`.

**File format** (YAML; optional top-level `backlog` key for nesting):

```yaml
# Optional: wrap under top-level key
backlog:
  github:
    repo_owner: your-org
    repo_name: your-repo
  ado:
    org: your-org
    project: YourProject
    team: Your Team
```

Or without the top-level key:

```yaml
github:
  repo_owner: your-org
  repo_name: your-repo
ado:
  org: your-org
  project: YourProject
  team: Your Team
```

**Environment variables** (override file; CLI overrides env):

| Adapter | Env vars |
|--------|----------|
| GitHub | `SPECFACT_GITHUB_REPO_OWNER`, `SPECFACT_GITHUB_REPO_NAME` |
| Azure DevOps | `SPECFACT_ADO_ORG`, `SPECFACT_ADO_PROJECT`, `SPECFACT_ADO_TEAM` |

**Git fallback (auto-detect from clone)**:

- **GitHub**: When repo is not set via CLI, env, or file, SpecFact infers `repo_owner` and `repo_name` from `git remote get-url origin` when run inside a **GitHub** clone (e.g. `https://github.com/owner/repo` or `git@github.com:owner/repo.git`). No `--repo-owner`/`--repo-name` needed when you run from the repo root.
- **Azure DevOps**: When org/project are not set via CLI, env, or file, SpecFact infers `org` and `project` from the remote URL when run inside an **ADO** clone. Supported formats: `https://dev.azure.com/org/project/_git/repo`; SSH with keys: `git@ssh.dev.azure.com:v3/org/project/repo`; SSH without keys (other auth): `user@dev.azure.com:v3/org/project/repo` (no `ssh.` subdomain). No `--ado-org`/`--ado-project` needed when you run from the repo root.

So after authenticating once, **running from the repo root is enough** for both GitHub and ADO—org/repo or org/project are detected automatically from the git remote.

Applies to all backlog commands: `specfact backlog daily`, `specfact backlog refine`, `specfact sync bridge`, etc.

---

## When to Use `--bundle` vs Direct Export

> **⚠️ Important**: Understanding when to use `--bundle` is crucial for successful exports. Using `--bundle` incorrectly will result in "0 backlog items exported" errors.

### Direct Export (No `--bundle`) - Most Common Use Case ✅

**Use this for**: Exporting OpenSpec change proposals directly to GitHub/ADO from your `openspec/changes/` directory.

**How it works**: Reads proposals directly from `openspec/changes/<change-id>/proposal.md` files.

**Example**:

```bash
# ✅ CORRECT: Direct export from OpenSpec to GitHub
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --change-ids add-feature-x \
  --repo /path/to/openspec-repo
```

**When to use**:

- ✅ Exporting OpenSpec change proposals to backlog tools (GitHub, ADO)
- ✅ First-time export of a change proposal
- ✅ Updating existing issues from OpenSpec proposals
- ✅ Most common workflow for OpenSpec → GitHub/ADO sync

**What happens**:

1. Reads `openspec/changes/<change-id>/proposal.md`
2. Creates/updates GitHub issue or ADO work item
3. Updates `source_tracking` in proposal.md with issue/work item ID

### Bundle Export (With `--bundle`) - Cross-Adapter Sync Only 🚀

**Use this for**: Migrating backlog items between different adapters (GitHub → ADO, ADO → GitHub) with lossless content preservation.

**How it works**: Exports from stored bundle content (not from OpenSpec directly). Requires proposals to be imported into bundle first.

**Example**:

```bash
# Step 1: Import GitHub issue into bundle (stores lossless content)
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner your-org --repo-name your-repo \
  --bundle migration-bundle \
  --backlog-ids 123

# Output: "✓ Imported GitHub issue #123 as change proposal: add-feature-x"
# Note the change_id from output

# Step 2: Export from bundle to ADO (uses stored content)
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org --ado-project your-project \
  --bundle migration-bundle \
  --change-ids add-feature-x  # Use change_id from Step 1
```

**When to use**:

- ✅ Cross-adapter sync (GitHub → ADO, ADO → GitHub)
- ✅ Migrating backlog items between tools
- ✅ Preserving lossless content during migrations
- ✅ Multi-tool workflows (public GitHub + internal ADO)

**What happens**:

1. **Step 1 (Import)**: Fetches backlog item, stores raw content in bundle, creates proposal
2. **Step 2 (Export)**: Loads proposal from bundle, uses stored raw content, creates new backlog item

### Common Mistake: Using `--bundle` for Direct Export ❌

**Problem**: Using `--bundle` when exporting directly from OpenSpec:

```bash
# ❌ WRONG: This will show "0 backlog items exported"
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org --repo-name your-repo \
  --bundle some-bundle \
  --change-ids add-feature-x \
  --repo /path/to/openspec-repo
```

**Why it fails**: With `--bundle`, the system looks for proposals in the bundle's `change_tracking.proposals`, not in `openspec/changes/`. If the bundle doesn't have the proposal (because it was never imported), you get "0 backlog items exported".

**Solution**: Remove `--bundle` for direct OpenSpec exports:

```bash
# ✅ CORRECT: Direct export (no --bundle)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org --repo-name your-repo \
  --change-ids add-feature-x \
  --repo /path/to/openspec-repo
```

### Quick Decision Guide

| Scenario | Use `--bundle`? | Command Pattern |
|----------|----------------|-----------------|
| Export OpenSpec proposal → GitHub | ❌ No | `--adapter github --mode export-only --change-ids <id> --repo <openspec-repo>` |
| Export OpenSpec proposal → ADO | ❌ No | `--adapter ado --mode export-only --change-ids <id> --repo <openspec-repo>` |
| Import GitHub issue → Bundle → Export to ADO | ✅ Yes | Step 1: `--bundle <name> --backlog-ids <id>`<br>Step 2: `--bundle <name> --change-ids <id>` |
| Migrate ADO work item → GitHub | ✅ Yes | Step 1: `--bundle <name> --backlog-ids <id>`<br>Step 2: `--bundle <name> --change-ids <id>` |

### Summary

- **Direct Export** (no `--bundle`): OpenSpec → GitHub/ADO - reads from `openspec/changes/` directly
- **Bundle Export** (with `--bundle`): Cross-adapter sync only - exports from stored bundle content
- **Rule of thumb**: Only use `--bundle` when migrating between different backlog adapters

---

## Separate OpenSpec and Source Code Repositories

When your OpenSpec change proposals are in a different repository than your source code:

### Architecture

- **OpenSpec Repository** (`--repo`): Contains change proposals in `openspec/changes/` directory
- **Source Code Repository** (`--code-repo`): Contains actual implementation commits

### Example Setup

```bash
# OpenSpec proposals in specfact-cli-internal
# Source code in specfact-cli

# Step 1: Create issue from proposal
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai \
  --repo-name specfact-cli-internal \
  --repo /path/to/specfact-cli-internal

# Step 2: Track code changes from source code repo
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai \
  --repo-name specfact-cli-internal \
  --track-code-changes \
  --repo /path/to/specfact-cli-internal \
  --code-repo /path/to/specfact-cli
```

### Why Use `--code-repo`?

- **OpenSpec repository** (`--repo`): Contains change proposals and tracks issue metadata
- **Source code repository** (`--code-repo`): Contains actual implementation commits that reference the change proposal ID

If both are in the same repository, you can omit `--code-repo` and it will use `--repo` for both purposes.

---

## Content Sanitization

When exporting to public repositories, use content sanitization to protect internal information:

### What Gets Sanitized

**Removed:**

- Competitive analysis sections
- Market positioning statements
- Implementation details (file-by-file changes)
- Effort estimates and timelines
- Technical architecture details
- Internal strategy sections

**Preserved:**

- High-level feature descriptions
- User-facing value propositions
- Acceptance criteria
- External documentation links
- Use cases and examples

### Usage

```bash
# Public repository: sanitize content
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name public-repo \
  --sanitize \
  --target-repo your-org/public-repo \
  --repo /path/to/openspec-repo

# Internal repository: use full content
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name internal-repo \
  --no-sanitize \
  --target-repo your-org/internal-repo \
  --repo /path/to/openspec-repo
```

### Auto-Detection

SpecFact CLI automatically detects when to sanitize:

- **Different repos** (code repo ≠ planning repo): Sanitization recommended (default: yes)
- **Same repo** (code repo = planning repo): Sanitization optional (default: no)

You can override with `--sanitize` or `--no-sanitize` flags.

---

## Code Change Tracking

### How It Works

When `--track-code-changes` is enabled:

1. **Repository Selection**: Uses `--code-repo` if provided, otherwise uses `--repo`
2. **Git Commit Detection**: Searches git log for commits mentioning the change proposal ID
3. **File Change Tracking**: Extracts files modified in detected commits
4. **Progress Comment Generation**: Formats comment with commit details and file changes
5. **Duplicate Prevention**: Checks against existing comments to avoid duplicates
6. **Source Tracking Update**: Updates `proposal.md` with progress metadata

### Commit Message Format

Include the change proposal ID in your commit messages:

```bash
# Good: Change ID clearly mentioned
git commit -m "feat: implement add-feature-x - initial API design"
git commit -m "fix: add-feature-x - resolve authentication issue"
git commit -m "docs: add-feature-x - update API documentation"

# Also works: Change ID anywhere in message
git commit -m "Implement new feature

- Add API endpoints
- Update database schema
- Related to add-feature-x"
```

### Progress Comment Format

Progress comments include:

- **Commit details**: Hash, message, author, date
- **Files changed**: Up to 10 files listed, then "and X more file(s)"
- **Detection timestamp**: When the change was detected

**Example Comment:**

```
📊 **Code Change Detected**

**Commit**: `364c8cfb` - feat: implement add-feature-x - initial API design
**Author**: @username
**Date**: 2025-12-30
**Files Changed**:
- src/api/endpoints.py
- src/models/feature.py
- tests/test_feature.py
- and 2 more file(s)

*Detected at: 2025-12-30T10:00:00Z*
```

### Progress Comment Sanitization

When `--sanitize` is enabled, progress comments are sanitized:

- **Commit messages**: Internal keywords removed, long messages truncated
- **File paths**: Replaced with file type counts (e.g., "3 py file(s)")
- **Author emails**: Removed, only username shown
- **Timestamps**: Date only (no time component)

---

## Integration Workflow

### Initial Setup (One-Time)

1. **Create Change Proposal**:

   ```bash
   mkdir -p openspec/changes/add-feature-x
   # Edit openspec/changes/add-feature-x/proposal.md
   ```

2. **Export to GitHub**:

   ```bash
   specfact sync bridge --adapter github --mode export-only \
     --repo-owner your-org \
     --repo-name your-repo \
     --repo /path/to/openspec-repo
   ```

3. **Verify Issue Created**:

   ```bash
   gh issue list --repo your-org/your-repo
   ```

### Development Workflow (Ongoing)

1. **Make Commits** with change ID in commit message:

   ```bash
   git commit -m "feat: implement add-feature-x - initial API design"
   ```

2. **Track Progress**:

   ```bash
   specfact sync bridge --adapter github --mode export-only \
     --repo-owner your-org \
     --repo-name your-repo \
     --track-code-changes \
     --repo /path/to/openspec-repo \
     --code-repo /path/to/source-code-repo
   ```

3. **Verify Comments Added**:

   ```bash
   gh issue view <issue-number> --repo your-org/your-repo --json comments
   ```

### Manual Progress Updates

Add manual progress comments without code change detection:

```bash
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --add-progress-comment \
  --repo /path/to/openspec-repo
```

---

## Advanced Features

### Beyond Export/Update Capabilities

SpecFact supports more than exporting and updating backlog items:

- **Selective backlog import into bundles**: Import only the issues/work items you select (no bulk import by default).
  - Use `--mode bidirectional` with `--backlog-ids` or `--backlog-ids-file` and `--bundle`.
- **Status synchronization**: Keep OpenSpec/bundle proposal status aligned with backlog item state.
- **Validation reporting**: Attach validation outcomes (e.g., contract checks) as backlog comments when enabled.
- **Progress notes**: Add progress updates via `--track-code-changes` or `--add-progress-comment`.
- **Cross-adapter export**: Export stored bundle content 1:1 to another backlog adapter (GitHub ↔ ADO) with `--bundle`.

Example: Import selected GitHub issues into a bundle and keep them in sync:

```bash
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner your-org --repo-name your-repo \
  --bundle main \
  --backlog-ids 111,112
```

### Cross-Adapter Sync: Lossless Round-Trip Migration

> **🚀 Advanced Feature**: One of SpecFact's most powerful capabilities for DevOps teams working with multiple backlog tools.

SpecFact enables **lossless round-trip synchronization** between different backlog adapters (GitHub ↔ Azure DevOps ↔ others), allowing you to:

- **Migrate between backlog tools** without losing content or metadata
- **Sync across teams** using different tools (e.g., GitHub for open source, ADO for enterprise)
- **Maintain consistency** when working with multiple backlog systems
- **Preserve full content fidelity** across adapter boundaries

#### How It Works

The system uses **lossless content preservation** to ensure 100% fidelity during cross-adapter syncs:

1. **Content Storage**: When importing from any backlog adapter, the original raw content (title, body, metadata) is stored in the project bundle's `source_tracking` metadata
2. **Bundle Export**: Export from stored bundles preserves the original content exactly as it was imported
3. **Round-Trip Safety**: Content can be synced GitHub → OpenSpec → ADO → OpenSpec → GitHub with no data loss

#### Example: GitHub → ADO Migration

Migrate a GitHub issue to Azure DevOps while preserving all content:

**Step-by-Step Guide:**

```bash
# Step 1: Import GitHub issue into bundle (stores lossless content)
# This creates a change proposal in the bundle and stores raw content
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner your-org --repo-name your-repo \
  --bundle main \
  --backlog-ids 123

# After Step 1, the CLI will show the change_id that was created
# Example output: "✓ Imported GitHub issue #123 as change proposal: add-feature-x"
# Note the change_id from the output (e.g., "add-feature-x")

# Step 2: Find the change_id (if you missed it in the output)
# Option A: Check the bundle directory
ls .specfact/projects/main/change_tracking/proposals/
# Lists all proposal files - the filename is the change_id

# Option B: Check OpenSpec changes directory (if external_base_path is set)
ls /path/to/openspec-repo/openspec/changes/
# Lists all change directories - the directory name is the change_id

# Step 3: Export from bundle to ADO (uses stored lossless content)
# Replace <change-id> with the actual change_id from Step 1
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org --ado-project your-project \
  --bundle main \
  --change-ids add-feature-x  # Use the actual change_id from Step 1

# Step 4: Verify the export worked
# The CLI will show: "✓ Exported to ADO" with work item ID and URL
# Example: "✓ Work item created: https://dev.azure.com/your-org/your-project/_workitems/edit/456"
```

**What Happens Behind the Scenes:**

1. **Step 1 (Import)**:
   - Fetches GitHub issue #123
   - Creates change proposal in bundle `main`
   - Stores raw content (title, body) in `source_tracking.source_metadata`
   - Creates OpenSpec proposal in `openspec/changes/<change-id>/proposal.md`
   - Returns change_id (e.g., `add-feature-x`)

2. **Step 3 (Export)**:
   - Loads proposal from bundle `main`
   - Uses stored raw content (not reconstructed from sections)
   - Creates ADO work item with exact same content
   - Stores ADO work item ID in `source_tracking` for future updates

**Finding the Change ID:**

The change_id is derived from the GitHub issue:

- **If issue has OpenSpec footer**: Uses the change_id from footer (e.g., `*OpenSpec Change Proposal:`add-feature-x`*`)
- **If no footer**: Uses issue number as change_id (e.g., `123`)

**Verification:**

After export, verify content matches:

```bash
# Check the exported ADO work item
# Visit the work item URL shown in Step 4 output
# Compare content with original GitHub issue
# Both should have identical content (Why, What Changes sections)
```

The exported ADO work item will contain the exact same content as the original GitHub issue, including:

- Full markdown formatting
- All sections (Why, What Changes, etc.)
- Metadata and source tracking
- Status and labels (mapped appropriately)

#### Example: Multi-Tool Sync Workflow

Keep proposals in sync across GitHub (public) and ADO (internal):

**Complete Workflow with Change IDs:**

```bash
# Day 1: Create proposal in OpenSpec, export to GitHub (public)
# Assume change_id is "add-feature-x" (from openspec/changes/add-feature-x/proposal.md)
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org --repo-name public-repo \
  --sanitize \
  --repo /path/to/openspec-repo \
  --change-ids add-feature-x

# Output shows: "✓ Exported to GitHub" with issue number (e.g., #123)
# Note the GitHub issue number: 123

# Day 2: Import GitHub issue into bundle (for internal team)
# This stores lossless content in the bundle
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner your-org --repo-name public-repo \
  --bundle internal \
  --backlog-ids 123

# Output shows: "✓ Imported GitHub issue #123 as change proposal: add-feature-x"
# Note the change_id: add-feature-x

# Day 3: Export to ADO for internal tracking (full content, no sanitization)
# Uses the change_id from Day 2
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org --ado-project internal-project \
  --bundle internal \
  --change-ids add-feature-x

# Output shows: "✓ Exported to ADO" with work item ID (e.g., 456)
# Note the ADO work item ID: 456

# Day 4: Update in ADO, sync back to GitHub (status sync)
# Import ADO work item to update bundle with latest status
specfact sync bridge --adapter ado --mode bidirectional \
  --ado-org your-org --ado-project internal-project \
  --bundle internal \
  --backlog-ids 456

# Output shows: "✓ Imported ADO work item #456 as change proposal: add-feature-x"
# Bundle now has latest status from ADO

# Then sync status back to GitHub
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org --repo-name public-repo \
  --update-existing \
  --repo /path/to/openspec-repo \
  --change-ids add-feature-x

# Output shows: "✓ Updated GitHub issue #123"
```

**Key Points:**

- **Change IDs are consistent**: The same change_id (`add-feature-x`) is used across all adapters
- **Bundle preserves content**: The `internal` bundle stores lossless content from GitHub, which is then exported to ADO
- **Status sync**: Bidirectional sync updates the bundle, then export-only syncs status to other adapters
- **No content loss**: Raw content stored in bundle ensures 100% fidelity across all syncs

#### Lossless Content Preservation

SpecFact ensures **zero data loss** during cross-adapter syncs by:

- **Storing raw content**: Original title and body stored in `source_tracking.source_metadata.raw_title` and `raw_body`
- **Preserving formatting**: Markdown formatting, sections, and structure maintained exactly
- **Metadata preservation**: Source tracking, timestamps, and adapter-specific metadata preserved
- **Round-trip validation**: Content can be verified to match original after multiple sync cycles

#### Use Cases

**1. Tool Migration**

- Migrate from GitHub Issues to Azure DevOps without losing any content
- Move from ADO to GitHub for open source projects
- Transition between backlog tools as team needs change

**2. Multi-Tool Workflows**

- Public GitHub issues (sanitized) + Internal ADO work items (full content)
- Open source tracking (GitHub) + Enterprise tracking (ADO)
- Cross-team collaboration with different tool preferences

**3. Feature Branch Integration**

- Sync proposals with feature branches across different backlog tools
- Track code changes in one tool, sync status to another
- Maintain consistency when teams use different tools

**4. Validation & Code Change Tracking**

- Attach validation results to backlog items in any adapter
- Track code changes across multiple backlog systems
- Maintain audit trail across tool boundaries

#### Step-by-Step: Complete Cross-Adapter Sync Workflow

**Scenario**: Migrate a GitHub issue to Azure DevOps with full content preservation.

```bash
# Prerequisites: Set up authentication
export GITHUB_TOKEN='your-github-token'
export AZURE_DEVOPS_TOKEN='your-ado-token'

# Step 1: Import GitHub issue into bundle
# This stores the issue in a bundle with lossless content preservation
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner your-org --repo-name your-repo \
  --bundle migration-bundle \
  --backlog-ids 123

# Expected output:
# ✓ Imported GitHub issue #123 as change proposal: add-feature-x
# Note the change_id: "add-feature-x"

# Step 2: Verify the import (optional but recommended)
# Check that the proposal was created in the bundle
ls .specfact/projects/migration-bundle/change_tracking/proposals/
# Should show: add-feature-x.yaml (or similar)

# Step 3: Export to Azure DevOps
# Use the change_id from Step 1
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org --ado-project your-project \
  --bundle migration-bundle \
  --change-ids add-feature-x

# Expected output:
# ✓ Exported to ADO
# ✓ Work item created: https://dev.azure.com/your-org/your-project/_workitems/edit/456
# Note the work item ID: 456

# Step 4: Verify content preservation
# Visit the ADO work item URL and compare with original GitHub issue
# Content should match exactly (Why, What Changes sections, formatting)

# Step 5: Optional - Round-trip back to GitHub to verify
specfact sync bridge --adapter ado --mode bidirectional \
  --ado-org your-org --ado-project your-project \
  --bundle migration-bundle \
  --backlog-ids 456

# Then export back to GitHub
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org --repo-name your-repo \
  --bundle migration-bundle \
  --change-ids add-feature-x \
  --update-existing

# Verify GitHub issue content matches original
```

#### Complete Round-Trip Example: GitHub → ADO → GitHub

**Scenario**: Full bidirectional sync workflow demonstrating lossless content preservation across GitHub and Azure DevOps.

This example demonstrates the complete cross-adapter sync workflow, showing how to:

1. Import a GitHub issue into a bundle
2. Export to Azure DevOps
3. Import back from Azure DevOps
4. Export back to GitHub
5. Verify content preservation throughout

```bash
# Prerequisites: Set up authentication
export GITHUB_TOKEN='your-github-token'
export AZURE_DEVOPS_TOKEN='your-ado-token'

# ============================================================
# STEP 1: Import GitHub Issue → SpecFact Bundle
# ============================================================
# Import GitHub issue #110 into bundle 'cross-sync-test'
# Note: Bundle will be auto-created if it doesn't exist
# This stores lossless content in the bundle
specfact sync bridge --adapter github --mode bidirectional \
  --repo-owner nold-ai --repo-name specfact-cli \
  --bundle cross-sync-test \
  --backlog-ids 110

# Expected output:
# ✓ Imported GitHub issue #110 as change proposal: <change-id>
# Note the change_id from output (e.g., "add-ado-backlog-adapter" or "110")

# Find change_id if you missed it:
# Option A: Check bundle directory
ls .specfact/projects/cross-sync-test/change_tracking/proposals/

# Option B: Check OpenSpec directory (if using external repo)
ls /path/to/openspec-repo/openspec/changes/

# ============================================================
# STEP 2: Export SpecFact Bundle → Azure DevOps
# ============================================================
# Export the proposal to ADO using the change_id from Step 1
# Replace <change-id> with the actual change_id from Step 1
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org --ado-project your-project \
  --bundle cross-sync-test \
  --change-ids <change-id>

# Expected output:
# ✓ Exported to ADO
# ✓ Exported 1 backlog item(s)
# Note the ADO work item ID from the output (e.g., 456)

# ============================================================
# STEP 3: Import Azure DevOps → SpecFact Bundle
# ============================================================
# Import the ADO work item back into the bundle
# This updates the bundle with ADO's version of the content
# Replace <ado-work-item-id> with the ID from Step 2
specfact sync bridge --adapter ado --mode bidirectional \
  --ado-org your-org --ado-project your-project \
  --bundle cross-sync-test \
  --backlog-ids <ado-work-item-id>

# Expected output:
# ✓ Imported ADO work item #<ado-work-item-id> as change proposal: <change-id>
# The change_id should match the one from Step 1

# ============================================================
# STEP 4: Export SpecFact Bundle → GitHub (Round-Trip)
# ============================================================
# Export back to GitHub to complete the round-trip
# This updates the original GitHub issue with any changes from ADO
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai --repo-name specfact-cli \
  --bundle cross-sync-test \
  --change-ids <change-id> \
  --update-existing

# Expected output:
# ✓ Exported to GitHub
# ✓ Updated GitHub issue #110

# ============================================================
# STEP 5: Verification
# ============================================================
# Verify content preservation:
# 1. Visit the original GitHub issue: https://github.com/nold-ai/specfact-cli/issues/110
# 2. Visit the ADO work item URL from Step 2
# 3. Compare content - both should have identical:
#    - Why section
#    - What Changes section
#    - Formatting and structure
#    - Metadata (status, labels mapped appropriately)
```

**What This Demonstrates:**

- **Lossless Content Preservation**: Content is preserved exactly through GitHub → ADO → GitHub round-trip
- **Bundle as Storage**: The bundle stores raw content, ensuring 100% fidelity
- **Bidirectional Sync**: Both adapters can import and export, maintaining consistency
- **Change ID Consistency**: The same change_id is used across all adapters
- **Status Synchronization**: Status changes in one adapter are reflected in others

**Key Points:**

- **Bundle is required**: Without `--bundle`, content may be reconstructed and lose formatting
- **Change IDs are persistent**: The same change_id is used throughout the workflow
- **Content verification**: Always verify content matches after each step
- **Update existing**: Use `--update-existing` when exporting back to GitHub to update the original issue

**Important Notes:**

- **Bundle is required**: Without `--bundle`, content is reconstructed from sections (may lose formatting)
- **Change IDs**: The change_id is shown in the import output, or check the bundle directory
- **Work Item IDs**: ADO work item IDs are shown in export output, or check `source_tracking` in proposal.md
- **Content verification**: Always verify content matches after cross-adapter sync

#### Best Practices

- **Use bundles for cross-adapter sync**: Always use `--bundle` when syncing between adapters to preserve lossless content
- **Verify content preservation**: After cross-adapter sync, verify content matches original
- **Handle sanitization carefully**: Public repos may need sanitization, internal repos can use full content
- **Track source origins**: Use `source_tracking` metadata to understand where content originated
- **Test round-trips**: Validate lossless sync by syncing back to original adapter and comparing content
- **Note change IDs**: Save change IDs from import output for use in export commands
- **Check bundle contents**: Use `ls .specfact/projects/<bundle-name>/change_tracking/proposals/` to list all proposals in a bundle

### Update Existing Issues

When a change proposal already has a linked GitHub issue (via `source_tracking` metadata in the proposal), you can update the issue with the latest proposal content.

#### Prerequisites

The change proposal must have `source_tracking` metadata linking it to the GitHub issue. This is automatically added when:

- You first export a proposal to create an issue
- You import an existing issue as a change proposal (using bidirectional sync)
- You manually add it to the proposal's `proposal.md` file

**Example `source_tracking` in `proposal.md`:**

```markdown
## Source Tracking

- **GitHub Issue**: #105
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/105>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
<!-- content_hash: e628d8468669ebfc -->
```

#### Update a Specific Issue

To update a specific change proposal's linked issue:

```bash
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --change-ids your-change-id \
  --update-existing \
  --repo /path/to/openspec-repo
```

**Example: Update issue #105 for change proposal `implement-adapter-enhancement-recommendations`:**

```bash
cd /path/to/openspec-repo

specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai \
  --repo-name specfact-cli \
  --change-ids implement-adapter-enhancement-recommendations \
  --update-existing \
  --repo .
```

#### Update All Linked Issues

To update all change proposals that have linked GitHub issues:

```bash
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --update-existing \
  --repo /path/to/openspec-repo
```

#### What Gets Updated

When `--update-existing` is used, the GitHub adapter will:

1. **Read `source_tracking` metadata** from the change proposal to find the linked issue number
2. **Compare content hash** to detect if the proposal has changed since last sync
3. **Update issue body** with the latest proposal content (if content changed)
4. **Update issue title** if the proposal title changed
5. **Sync status labels** (OpenSpec status ↔ GitHub labels)
6. **Add/update OpenSpec metadata footer** in the issue body

#### Content Hash Detection

The adapter uses a content hash to detect changes. The hash is stored in the proposal's `source_tracking` section:

```markdown
<!-- content_hash: e628d8468669ebfc -->
```

If the proposal content hasn't changed, the issue won't be updated (even with `--update-existing`), preventing unnecessary API calls.

#### Best Practices

- **Use `--change-ids`** to update specific proposals instead of all proposals
- **Use `--update-existing` sparingly** (only when proposal content changes significantly)
- **Verify before updating** by checking the proposal's `source_tracking` metadata
- **Review changes** in the proposal before syncing to ensure accuracy

### Updating Archived Change Proposals

When you improve comment logic or branch detection algorithms, you may want to update existing GitHub issues for archived change proposals with the new improvements.

#### Use Case

- **New comment logic**: When you add new features to status comments (e.g., branch detection improvements)
- **Branch detection improvements**: When you enhance branch detection algorithms
- **Comment format updates**: When you change how comments are formatted

#### How It Works

By default, archived change proposals (in `openspec/changes/archive/`) are excluded from sync. Use `--include-archived` to include them:

```bash
# Update all archived proposals with new comment logic
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --include-archived \
  --update-existing \
  --repo /path/to/openspec-repo

# Update specific archived proposal
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --change-ids add-code-change-tracking \
  --include-archived \
  --update-existing \
  --repo /path/to/openspec-repo
```

#### What Gets Updated

When `--include-archived` is used with `--update-existing`:

1. **Archived proposals are included** in the sync (normally excluded)
2. **Comments are always updated** for applied status (even if content hash hasn't changed)
3. **Branch detection runs** with the latest improvements
4. **Issue state is verified** and updated if needed

#### Example: Updating Issue #107

```bash
# Update issue #107 with improved branch detection
specfact sync bridge --adapter github --mode export-only \
  --repo-owner nold-ai \
  --repo-name specfact-cli \
  --change-ids add-code-change-tracking \
  --include-archived \
  --update-existing \
  --repo /path/to/specfact-cli-internal
```

This will:

- Find the archived proposal `add-code-change-tracking` in `openspec/changes/archive/`
- Detect the implementation branch using the latest branch detection logic
- Add/update a comment on issue #107 with the correct branch information

### Proposal Filtering

Proposals are filtered based on target repository type:

**Public Repositories** (with `--sanitize`):

- Only syncs proposals with status `"applied"` (archived/completed changes)
- Filters out `"proposed"`, `"in-progress"`, `"deprecated"`, or `"discarded"`

**Internal Repositories** (with `--no-sanitize`):

- Syncs all active proposals regardless of status

### Duplicate Prevention

Progress comments are deduplicated using SHA-256 hash:

- First run: Comment added
- Second run: Comment skipped (duplicate detected)
- New commits: New comment added

---

## Verification

### Check Issue Creation

```bash
# List issues
gh issue list --repo your-org/your-repo

# View specific issue
gh issue view <issue-number> --repo your-org/your-repo
```

### Check Progress Comments

```bash
# View latest comment
gh issue view <issue-number> --repo your-org/your-repo --json comments --jq '.comments[-1].body'

# View all comments
gh issue view <issue-number> --repo your-org/your-repo --json comments
```

### Check Source Tracking

Verify `openspec/changes/<change-id>/proposal.md` was updated:

```markdown
## Source Tracking

- **GitHub Issue**: #123
- **Issue URL**: <https://github.com/owner/repo/issues/123>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- last_code_change_detected: 2025-12-30T10:00:00Z -->
```

---

## Troubleshooting

### "0 backlog items exported" Error

**Problem**: Export command shows "✓ Exported 0 backlog item(s) from bundle" even though change proposals exist.

**Common Causes**:

1. **Using `--bundle` for direct OpenSpec export** (most common):

   ```bash
   # ❌ WRONG: Using --bundle when exporting from OpenSpec
   specfact sync bridge --adapter github --mode export-only \
     --repo-owner your-org --repo-name your-repo \
     --bundle some-bundle \
     --change-ids add-feature-x \
     --repo /path/to/openspec-repo
   ```

2. **Bundle doesn't contain the proposal**:
   - Proposal was never imported into the bundle
   - Bundle name is incorrect
   - Proposal was created in OpenSpec but not imported to bundle

**Solutions**:

- **For direct OpenSpec export** (most common): Remove `--bundle` flag:

  ```bash
  # ✅ CORRECT: Direct export from OpenSpec
  specfact sync bridge --adapter github --mode export-only \
    --repo-owner your-org --repo-name your-repo \
    --change-ids add-feature-x \
    --repo /path/to/openspec-repo
  ```

- **For bundle export** (cross-adapter sync): Import proposal into bundle first:

  ```bash
  # Step 1: Import from backlog into bundle
  specfact sync bridge --adapter github --mode bidirectional \
    --repo-owner your-org --repo-name your-repo \
    --bundle your-bundle \
    --backlog-ids 123
  
  # Step 2: Export from bundle (now it will work)
  specfact sync bridge --adapter ado --mode export-only \
    --ado-org your-org --ado-project your-project \
    --bundle your-bundle \
    --change-ids <change-id-from-step-1>
  ```

- **Verify proposal exists**:

  ```bash
  # Check OpenSpec directory
  ls openspec/changes/<change-id>/
  
  # Check bundle directory (if using --bundle)
  ls .specfact/projects/<bundle-name>/change_tracking/proposals/
  ```

**See also**: [When to Use `--bundle` vs Direct Export](#when-to-use---bundle-vs-direct-export) section above.

### No Commits Detected

**Problem**: Code changes not detected even though commits exist.

**Solutions**:

- Ensure commit messages include the change proposal ID (e.g., "add-feature-x")
- Verify `--code-repo` points to the correct source code repository
- Check that `last_code_change_detected` timestamp isn't in the future (reset if needed)

### Wrong Repository

**Problem**: Commits detected from wrong repository.

**Solutions**:

- Verify `--code-repo` parameter points to source code repository
- Check that OpenSpec repository (`--repo`) is correct
- Ensure both repositories are valid Git repositories

### No Comments Added

**Problem**: Progress comments not added to issues.

**Solutions**:

- Verify issues exist (create them first without `--track-code-changes`)
- Check GitHub token has write permissions
- Verify change proposal ID matches commit messages
- Check for duplicate comments (may be skipped)

### Sanitization Issues

**Problem**: Too much or too little content sanitized.

**Solutions**:

- Use `--sanitize` for public repos, `--no-sanitize` for internal repos
- Check auto-detection logic (different repos → sanitize, same repo → no sanitization)
- Review proposal content to ensure sensitive information is properly marked

### Authentication Errors

**Problem**: GitHub authentication fails.

**Solutions**:

- Verify GitHub token is valid: `gh auth status`
- Check token permissions (read/write access)
- Try using `--use-gh-cli` flag
- Verify `GITHUB_TOKEN` environment variable is set correctly

---

## Best Practices

### Commit Messages

- Always include change proposal ID in commit messages
- Use descriptive commit messages that explain what was changed
- Follow conventional commit format: `type: change-id - description`

### Repository Organization

- Keep OpenSpec proposals in a dedicated repository for better organization
- Use `--code-repo` when OpenSpec and source code are separate
- Document repository structure in your team's documentation

### Content Sanitization

- Always sanitize when exporting to public repositories
- Review sanitized content before syncing to ensure nothing sensitive leaks
- Use `--no-sanitize` only for internal repositories

### Progress Tracking

- Run `--track-code-changes` regularly (e.g., after each commit or daily)
- Use manual progress comments for non-code updates (meetings, decisions, etc.)
- Verify comments are added correctly after each sync

### Issue Management

- Create issues first, then track code changes
- Use `--update-existing` sparingly (only when proposal content changes significantly)
- Monitor issue comments to ensure progress tracking is working

---

## See Also

### Related Guides

- [Integrations Overview](integrations-overview.md) - Overview of all SpecFact CLI integrations

- [Command Chains Reference](command-chains.md) - Complete workflows including [External Tool Integration Chain](command-chains.md#3-external-tool-integration-chain)
- [Common Tasks Index](common-tasks.md) - Quick reference for DevOps integration tasks
- [OpenSpec Journey](openspec-journey.md) - OpenSpec integration with DevOps export
- [Agile/Scrum Workflows](agile-scrum-workflows.md) - Persona-based backlog management

### Related Commands

- [Command Reference - Sync Bridge](../reference/commands.md#sync-bridge) - Complete `sync bridge` command documentation
- [Command Reference - DevOps Adapters](../reference/commands.md#sync-bridge) - Adapter configuration

### Related Examples

- [DevOps Integration Examples](../examples/) - Real-world integration examples

### Architecture & Troubleshooting

- [Architecture](../reference/architecture.md) - System architecture and design
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

---

## Azure DevOps Integration

Azure DevOps adapter (`--adapter ado`) is now available and supports:

- **Bidirectional Sync**: Import ADO work items as OpenSpec change proposals AND export proposals as work items
- **Work Item Creation**: Export OpenSpec change proposals as ADO work items
- **Work Item Import**: Import ADO work items as OpenSpec change proposals
- **Status Synchronization**: Bidirectional status sync (OpenSpec ↔ ADO state) with conflict resolution
- **Status Comments**: Automatic status change comments (applied, deprecated, discarded, in-progress)
- **Progress Tracking**: Code change detection and progress comments (same as GitHub)
- **Work Item Type Derivation**: Automatically detects work item type from process template (Scrum/Kanban/Agile)
- **Work Item Updates**: Update existing work items with `--update-existing` flag
- **Markdown Format Support**: Proper markdown rendering in work item descriptions

### Prerequisites

- Azure DevOps organization and project
- Personal Access Token (PAT) with work item read/write permissions **or** device code auth via `specfact backlog auth azure-devops`
- OpenSpec change proposals in `openspec/changes/<change-id>/proposal.md`

### Authentication

```bash
# Option 1: Device Code (SSO-friendly)
specfact backlog auth azure-devops

# Option 2: Environment Variable
export AZURE_DEVOPS_TOKEN=your_pat_token
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --repo /path/to/openspec-repo

# Option 3: Command Line Flag
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --ado-token your_pat_token \
  --repo /path/to/openspec-repo
```

### Basic Usage

```bash
# Bidirectional sync (import work items AND export proposals)
specfact sync bridge --adapter ado --bidirectional \
  --ado-org your-org \
  --ado-project your-project \
  --repo /path/to/openspec-repo

# Export-only (one-way: OpenSpec → ADO)
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --repo /path/to/openspec-repo

# Export with explicit work item type
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --ado-work-item-type "User Story" \
  --repo /path/to/openspec-repo

# Track code changes and add progress comments
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --track-code-changes \
  --repo /path/to/openspec-repo \
  --code-repo /path/to/source-code-repo
```

### Work Item Type Derivation

The ADO adapter automatically derives work item type from your project's process template:

- **Scrum**: `Product Backlog Item`
- **Agile**: `User Story`
- **Kanban**: `User Story` (default)

You can override with `--ado-work-item-type`:

```bash
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --ado-work-item-type "Bug" \
  --repo /path/to/openspec-repo
```

### Status Mapping

ADO states map to OpenSpec status as follows:

| ADO State | OpenSpec Status |
|-----------|----------------|
| `New` | `proposed` |
| `Active` / `In Progress` | `in-progress` |
| `Closed` / `Done` | `applied` |
| `Removed` | `deprecated` |
| `Rejected` | `discarded` |

### Configuration

All ADO-specific configuration can be provided via:

- **CLI flags**: `--ado-org`, `--ado-project`, `--ado-base-url`, `--ado-token`, `--ado-work-item-type`
- **Environment variables**: `AZURE_DEVOPS_TOKEN`, `ADO_BASE_URL` (defaults to `https://dev.azure.com`)

## Future Adapters

Additional DevOps adapters are planned:

- **Linear** (`--adapter linear`) - Issues and progress updates
- **Jira** (`--adapter jira`) - Issues, epics, and sprint tracking

These will follow similar patterns to GitHub Issues and Azure DevOps integration. Check the [Commands Reference](../reference/commands.md) for the latest adapter support.

---

**Need Help?**

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 [hello@noldai.com](mailto:hello@noldai.com)
