---
layout: default
title: GitHub Adapter
permalink: /adapters/github/
---

# GitHub Adapter

The GitHub adapter provides bidirectional synchronization between OpenSpec change proposals and GitHub Issues, enabling agile DevOps-driven workflow support.

## Overview

The GitHub adapter supports:

- **Export**: OpenSpec change proposals → GitHub Issues
- **Import**: GitHub Issues → OpenSpec change proposals
- **Status Sync**: Bidirectional status synchronization (OpenSpec ↔ GitHub labels)
- **Validation Reporting**: Validation results reported to GitHub Issues
- **Lossless Content Preservation**: Stores raw content for round-trip syncs across adapters
- **Cross-Adapter Sync**: Export stored bundle content to any backlog adapter with 100% fidelity

This is the first backlog adapter implementation. The Azure DevOps (ADO) adapter is now available with full feature parity. Future backlog adapters (Jira, Linear) follow the same patterns documented in [Backlog Adapter Patterns](./backlog-adapter-patterns.md).

## Features

### Bidirectional Sync

- **Export**: Create or update GitHub issues from OpenSpec change proposals
- **Import**: Import GitHub issues as OpenSpec change proposals
- **Status Sync**: Keep OpenSpec and GitHub status in sync with conflict resolution
- **Lossless Content Preservation**: Original issue content (title, body) stored in `source_tracking.source_metadata` for round-trip syncs

### Supported Artifact Keys

- `change_proposal`: Export change proposal to GitHub issue
- `change_status`: Update GitHub issue status
- `change_proposal_update`: Update GitHub issue body
- `code_change_progress`: Add progress comment to GitHub issue
- `github_issue`: Import GitHub issue as change proposal

### Status Mapping

GitHub labels are mapped to OpenSpec status:

| GitHub Label | OpenSpec Status |
|--------------|-----------------|
| `enhancement`, `new`, `todo` | `proposed` |
| `in-progress`, `in progress`, `active` | `in-progress` |
| `done`, `completed`, `closed` | `applied` |
| `deprecated`, `wontfix` | `deprecated` |
| `discarded`, `rejected` | `discarded` |

## Configuration

### Bridge Config

```yaml
# bridge_config.yaml
adapter: github
artifacts:
  - change_proposal
  - change_status
  - change_proposal_update
  - code_change_progress
  - github_issue
repo_owner: your-org
repo_name: your-repo
external_base_path: ../openspec-repo  # Optional: cross-repo support
```

### Authentication

The adapter supports multiple authentication methods (in order of precedence):

1. **Explicit token**: `api_token` parameter
2. **Environment variable**: `GITHUB_TOKEN`
3. **Stored auth token**: `specfact backlog auth github` (device code flow)
4. **GitHub CLI**: `gh auth token` (if `use_gh_cli=True`)

**Note:** The default device-code client ID is only valid for `https://github.com`. For GitHub Enterprise, supply `--client-id` or set `SPECFACT_GITHUB_CLIENT_ID`.

**Example:**

```python
from specfact_cli.adapters.github import GitHubAdapter

# Explicit token
adapter = GitHubAdapter(
    repo_owner="your-org",
    repo_name="your-repo",
    api_token="ghp_...",
)

# Or use environment variable
import os
os.environ["GITHUB_TOKEN"] = "ghp_..."
adapter = GitHubAdapter(repo_owner="your-org", repo_name="your-repo")

# Or use GitHub CLI
adapter = GitHubAdapter(
    repo_owner="your-org",
    repo_name="your-repo",
    use_gh_cli=True,  # Auto-detects gh CLI token
)
```

## Usage Examples

### Export Change Proposal to GitHub

```python
from specfact_cli.adapters.github import GitHubAdapter

adapter = GitHubAdapter(
    repo_owner="your-org",
    repo_name="your-repo",
    api_token="ghp_...",
)

proposal_data = {
    "change_id": "add-feature-x",
    "title": "Add Feature X",
    "description": "Implement feature X",
    "rationale": "Needed for user workflow",
    "status": "proposed",
}

result = adapter.export_artifact(
    artifact_key="change_proposal",
    artifact_data=proposal_data,
)

print(f"Issue created: {result['issue_url']}")
print(f"Issue number: {result['issue_number']}")
```

### Import GitHub Issue as Change Proposal

```python
from specfact_cli.adapters.github import GitHubAdapter
from unittest.mock import MagicMock

adapter = GitHubAdapter(
    repo_owner="your-org",
    repo_name="your-repo",
    api_token="ghp_...",
)

# GitHub issue data (from API)
issue_data = {
    "number": 123,
    "title": "Add Feature X",
    "body": "## Why\n\nNeeded\n\n## What Changes\n\nImplement",
    "labels": [{"name": "enhancement"}],
    "state": "open",
    "created_at": "2025-01-01T10:00:00Z",
    "html_url": "https://github.com/your-org/your-repo/issues/123",
}

# Mock project bundle
project_bundle = MagicMock()
project_bundle.change_tracking = ChangeTracking()
project_bundle.bundle_dir = Path("/path/to/repo")

# Import issue
adapter.import_artifact(
    artifact_key="github_issue",
    artifact_path=issue_data,
    project_bundle=project_bundle,
)

# Access imported proposal
proposal = project_bundle.change_tracking.proposals["123"]
print(f"Imported: {proposal.title} - {proposal.status}")
```

### Status Synchronization

```python
# Sync OpenSpec status to GitHub
proposal = {
    "status": "in-progress",
    "source_tracking": {"source_id": "123"},
}

result = adapter.sync_status_to_github(
    proposal=proposal,
    repo_owner="your-org",
    repo_name="your-repo",
)

print(f"Labels updated: {result['new_labels']}")

# Sync GitHub status to OpenSpec
issue_data = {
    "labels": [{"name": "in-progress"}],
}

resolved_status = adapter.sync_status_from_github(
    issue_data=issue_data,
    proposal={"status": "proposed"},
    strategy="prefer_backlog",  # or "prefer_openspec", "merge"
)

print(f"Resolved status: {resolved_status}")
```

## Cross-Repository Support

The adapter supports cross-repository scenarios using `bridge_config.external_base_path`:

```yaml
# bridge_config.yaml
adapter: github
external_base_path: ../openspec-repo  # External OpenSpec repository
```

When `external_base_path` is set:

- OpenSpec repository is loaded from the external path
- All path operations respect the external base path
- Change proposals can reference external repositories

## Issue Body Format

GitHub issues created from change proposals follow this format:

```markdown
## Why

[Rationale from change proposal]

## What Changes

[Description from change proposal]

---

*OpenSpec Change Proposal: `change-id`*
```

When importing GitHub issues, the adapter parses this format to extract:

- **Why section**: Rationale
- **What Changes section**: Description
- **OpenSpec metadata footer**: Change ID

## Status Synchronization

### Conflict Resolution

When OpenSpec and GitHub status differ, the adapter supports three conflict resolution strategies:

1. **`prefer_openspec`** (default): Use OpenSpec status as source of truth
2. **`prefer_backlog`**: Use GitHub status as source of truth
3. **`merge`**: Use most advanced status (applied > in-progress > proposed)

**Example:**

```python
# OpenSpec: "proposed", GitHub: "in-progress"
resolved = adapter.sync_status_from_github(
    issue_data={"labels": [{"name": "in-progress"}]},
    proposal={"status": "proposed"},
    strategy="merge",  # Results in "in-progress" (more advanced)
)
```

## Validation Result Reporting

When validation completes, results are automatically reported to GitHub Issues:

- **Comment**: Added to issue with validation status and results
- **Labels**: Updated based on validation status (`validation-failed` for failures)

**Example GitHub Issue Comment:**

```markdown
## Validation Results

**Status**: FAILED

**Feature Validation**:
- ❌ feature-1
- ✅ feature-2
```

## Limitations

### Current Limitations

- **Single Repository**: Each adapter instance is configured for one repository
- **Label-Based Status**: Status sync relies on GitHub labels (not issue state)
- **Manual Label Creation**: Labels must exist in repository (e.g., `in-progress`, `completed`)

### Future Enhancements

- **Multi-Repository Support**: Support for multiple repositories in one adapter instance
- **Automatic Label Creation**: Auto-create required labels if missing
- **Issue State Sync**: Sync issue open/closed state in addition to labels
- **Assignee Sync**: Sync assignees between OpenSpec and GitHub

## Troubleshooting

### Common Issues

**Issue: "GitHub API token required"**

- Ensure `GITHUB_TOKEN` environment variable is set, or
- Provide `api_token` parameter, or
- Use GitHub CLI: `gh auth login` and set `use_gh_cli=True`

**Issue: "GitHub repository owner and name required"**

- Provide `repo_owner` and `repo_name` parameters, or
- Set them in `bridge_config.yaml`

**Issue: "Issue number not found in source_tracking"**

- Issue must be created first (export change proposal)
- Check that `source_tracking` contains `source_id` for the repository

**Issue: Status sync doesn't update labels**

- Verify labels exist in repository
- Check API token has write permissions
- Ensure issue number is correct in `source_tracking`

## CLI Usage

### Export OpenSpec change to GitHub (create issue + Source Tracking)

To create a GitHub issue from an OpenSpec change and have the issue number/URL written back into `proposal.md` (Source Tracking section), run from the repository that contains `openspec/changes/`:

```bash
# Export one or more changes; creates issues and updates proposal.md Source Tracking
specfact sync bridge --adapter github --mode export-only \
  --repo . \
  --repo-owner nold-ai \
  --repo-name specfact-cli \
  --change-ids <change-id>

# Example: export backlog-scrum-05-summarize-markdown-output
specfact sync bridge --adapter github --mode export-only \
  --repo . \
  --repo-owner nold-ai \
  --repo-name specfact-cli \
  --change-ids backlog-scrum-05-summarize-markdown-output
```

- **`--repo .`**: Path to the repo with `openspec/changes/` (default is current directory).
- **`--repo-owner` / `--repo-name`**: Target GitHub repo for new issues.
- **`--change-ids`**: Comma-separated change IDs to export (omit to export all active proposals).

After a successful run, each change’s `openspec/changes/<change-id>/proposal.md` will contain a **Source Tracking** block with the new issue number and URL. Use that section to link the PR and keep backlog in sync.

For public repos, add `--sanitize` when exporting so content is sanitized before creating issues. See [DevOps Adapter Integration](../guides/devops-adapter-integration.md) and the [sync bridge command reference](../reference/commands.md#sync-bridge).

### Updating Archived Change Proposals

When you improve comment logic or branch detection, use `--include-archived` to update existing GitHub issues for archived proposals:

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

This ensures archived issues get updated with:

- Improved branch detection algorithms
- Enhanced comment formatting
- Latest status information

See [DevOps Adapter Integration Guide](../guides/devops-adapter-integration.md#updating-archived-change-proposals) for complete documentation.

## Lossless Content Preservation

The GitHub adapter stores raw content when importing issues to enable lossless round-trip syncs:

```python
# When importing, raw content is automatically stored
proposal = adapter.import_backlog_item_as_proposal(issue_data, "github", bridge_config)

# Raw content stored in source_tracking.source_metadata
raw_title = proposal.source_tracking.source_metadata.get("raw_title")
raw_body = proposal.source_tracking.source_metadata.get("raw_body")
raw_format = proposal.source_tracking.source_metadata.get("raw_format")  # "markdown"
```

When exporting from stored bundles, the adapter uses raw content if available to preserve 100% fidelity, even when syncing to a different adapter (e.g., GitHub → ADO).

**See**: [Cross-Adapter Sync Guide](../guides/devops-adapter-integration.md#cross-adapter-sync-lossless-round-trip-migration) for complete documentation.

## Related Documentation

- **[Backlog Adapter Patterns](./backlog-adapter-patterns.md)** - Patterns for backlog adapters
- **[Azure DevOps Adapter](./azuredevops.md)** - Azure DevOps adapter documentation
- **[Validation Integration](../validation-integration.md)** - Validation with change proposals
- **[DevOps Adapter Integration](../guides/devops-adapter-integration.md)** - DevOps workflow integration
