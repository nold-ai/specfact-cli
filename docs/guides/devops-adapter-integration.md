# DevOps Adapter Integration Guide

This guide explains how to integrate SpecFact CLI with DevOps backlog tools (GitHub Issues, Azure DevOps, Linear, Jira) to sync OpenSpec change proposals and track implementation progress through automated comment annotations.

## Overview

SpecFact CLI supports exporting OpenSpec change proposals to DevOps tools and tracking implementation progress:

- **Issue Creation**: Export OpenSpec change proposals as GitHub Issues (or other DevOps backlog items)
- **Progress Tracking**: Automatically detect code changes and add progress comments to issues
- **Content Sanitization**: Protect internal information when syncing to public repositories
- **Separate Repository Support**: Handle cases where OpenSpec proposals and source code are in different repositories

## Supported Adapters

Currently supported DevOps adapters:

- **GitHub Issues** (`--adapter github`) - Full support for issue creation and progress comments
- **Azure DevOps** (`--adapter ado`) - Planned
- **Linear** (`--adapter linear`) - Planned
- **Jira** (`--adapter jira`) - Planned

This guide focuses on GitHub Issues integration. Other adapters will follow similar patterns.

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

**Option 1: GitHub CLI (Recommended)**

```bash
# Uses gh auth token automatically
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --use-gh-cli
```

**Option 2: Environment Variable**

```bash
export GITHUB_TOKEN=ghp_your_token_here
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo
```

**Option 3: Command Line Flag**

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

### Update Existing Issues

Update issue bodies when proposal content changes:

```bash
specfact sync bridge --adapter github --mode export-only \
  --repo-owner your-org \
  --repo-name your-repo \
  --update-existing \
  --repo /path/to/openspec-repo
```

**Note**: Uses content hash to detect changes. Default: `False` for safety.

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

## Future Adapters

Additional DevOps adapters are planned:

- **Azure DevOps** (`--adapter ado`) - Work items and progress tracking
- **Linear** (`--adapter linear`) - Issues and progress updates
- **Jira** (`--adapter jira`) - Issues, epics, and sprint tracking

These will follow similar patterns to GitHub Issues integration. Check the [Commands Reference](../reference/commands.md) for the latest adapter support.

---

**Need Help?**

- 💬 [GitHub Discussions](https://github.com/nold-ai/specfact-cli/discussions)
- 🐛 [GitHub Issues](https://github.com/nold-ai/specfact-cli/issues)
- 📧 [hello@noldai.com](mailto:hello@noldai.com)
