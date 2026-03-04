---
layout: default
title: Azure DevOps Adapter
permalink: /adapters/azuredevops/
---

# Azure DevOps Adapter

The Azure DevOps adapter provides bidirectional synchronization between OpenSpec change proposals and Azure DevOps work items, enabling agile DevOps-driven workflow support for enterprise teams.

## Overview

The Azure DevOps adapter supports:

- **Export**: OpenSpec change proposals → Azure DevOps work items
- **Import**: Azure DevOps work items → OpenSpec change proposals
- **Status Sync**: Bidirectional status synchronization (OpenSpec ↔ ADO state)
- **Work Item Type Derivation**: Automatically detects work item type from process template (Scrum/Kanban/Agile)
- **Markdown Format Support**: Proper markdown rendering in work item descriptions (ADO supports Markdown as of July 2025)
- **HTML to Markdown Conversion**: Converts HTML-formatted work items to markdown when importing
- **Lossless Content Preservation**: Stores raw content for round-trip syncs across adapters
- **Cross-Adapter Sync**: Export stored bundle content to any backlog adapter with 100% fidelity

This adapter follows the same patterns as the GitHub adapter, documented in [Backlog Adapter Patterns](./backlog-adapter-patterns.md).

## Features

### Bidirectional Sync

- **Export**: Create or update Azure DevOps work items from OpenSpec change proposals
- **Import**: Import Azure DevOps work items as OpenSpec change proposals
- **Status Sync**: Keep OpenSpec and ADO status in sync with conflict resolution
- **Lossless Content Preservation**: Original work item content (title, description) stored in `source_tracking.source_metadata` for round-trip syncs

### Supported Artifact Keys

- `change_proposal`: Export change proposal to Azure DevOps work item
- `change_status`: Update Azure DevOps work item state
- `change_proposal_update`: Update Azure DevOps work item description/body
- `change_proposal_comment`: Add status comment to Azure DevOps work item
- `code_change_progress`: Add progress comment based on code changes
- `ado_work_item`: Import Azure DevOps work item as change proposal

### Status Mapping

Azure DevOps work item states are mapped to OpenSpec status:

| ADO State | OpenSpec Status |
|-----------|-----------------|
| `New` | `proposed` |
| `Active`, `In Progress`, `Committed` | `in-progress` |
| `Closed`, `Done`, `Completed`, `Resolved` | `applied` |
| `Removed` | `deprecated` |
| `Rejected` | `discarded` |

### Work Item Type Derivation

The adapter automatically derives work item type from your project's process template:

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

## Configuration

### Bridge Config

```yaml
# bridge_config.yaml
adapter: ado
artifacts:
  - change_proposal
  - change_status
  - change_proposal_update
  - change_proposal_comment
  - code_change_progress
  - ado_work_item
external_base_path: ../openspec-repo  # Optional: cross-repo support
```

**Note**: Organization, project, and API token are **not** stored in bridge config for security. They must be provided via CLI flags or environment variables.

### Field Mapping

The adapter supports flexible field mapping to handle different ADO process templates:

- **Multiple Field Alternatives**: Supports multiple ADO field names mapping to the same canonical field (e.g., both `System.AcceptanceCriteria` and `Microsoft.VSTS.Common.AcceptanceCriteria` map to `acceptance_criteria`)
- **Default Mappings**: Includes default mappings for common ADO fields (Scrum, Agile, SAFe, Kanban)
- **Custom Mappings**: Supports per-project custom field mappings via `.specfact/templates/backlog/field_mappings/ado_custom.yaml`
- **Interactive Mapping**: Use `specfact backlog map-fields` to interactively discover and map ADO fields for your project

**Interactive Field Mapping Command**:

```bash
# Discover and map ADO fields interactively
specfact backlog map-fields --ado-org myorg --ado-project myproject
```

This command:

- Fetches available fields from your ADO project
- Pre-populates default mappings
- Uses arrow-key navigation for field selection
- Saves mappings to `.specfact/templates/backlog/field_mappings/ado_custom.yaml`
- Automatically used by all subsequent backlog operations

See [Custom Field Mapping Guide](../guides/custom-field-mapping.md) for complete documentation.

### Assignee Extraction and Display

The adapter extracts assignee information from ADO work items:

- **Extraction**: Assignees are extracted from `System.AssignedTo` field
- **Display**: Assignees are always displayed in backlog refinement preview output
- **Format**: Shows assignee names or "Unassigned" if no assignee
- **Preservation**: Assignee information is preserved during refinement and sync operations

### Authentication

The adapter supports multiple authentication methods (in order of precedence):

1. **Explicit token**: `api_token` parameter or `--ado-token` CLI flag
2. **Environment variable**: `AZURE_DEVOPS_TOKEN` (also accepts `ADO_TOKEN` or `AZURE_DEVOPS_PAT`)
3. **Stored auth token**: `specfact backlog auth azure-devops` (device code flow or PAT token)

**Token Resolution Priority**:

When using ADO commands, tokens are resolved in this order:

1. Explicit `--ado-token` parameter
2. `AZURE_DEVOPS_TOKEN` environment variable
3. Stored token via `specfact backlog auth azure-devops`
4. Expired stored token (shows warning with options to refresh)

**Token Types**:

- **OAuth Tokens**: Device code flow, expire after ~1 hour, automatically refreshed when possible
- **PAT Tokens**: Personal Access Tokens, can last up to 1 year, recommended for automation

See [Authentication Guide](../reference/authentication.md) for complete documentation.

**Example:**

```python
from specfact_cli.adapters.ado import AdoAdapter

# Explicit token
adapter = AdoAdapter(
    org="your-org",
    project="your-project",
    api_token="your_pat_token",
)

# Or use environment variable
import os
os.environ["AZURE_DEVOPS_TOKEN"] = "your_pat_token"
adapter = AdoAdapter(org="your-org", project="your-project")

# Custom base URL (for Azure DevOps Server)
adapter = AdoAdapter(
    org="your-org",
    project="your-project",
    base_url="https://dev.azure.com",  # Default, or custom for on-prem
    api_token="your_pat_token",
)
```

### Creating a Personal Access Token (PAT)

1. Go to Azure DevOps: `https://dev.azure.com/{your-org}/_usersSettings/tokens`
2. Create a new token with **Work Items (Read & Write)** permissions
3. Copy the token (it's only shown once)
4. Set as environment variable: `export AZURE_DEVOPS_TOKEN='your-token'`

### Error diagnostics (PATCH failures)

When a work item PATCH fails (e.g. HTTP 400 during backlog refine or status update), the CLI shows the ADO error message and a hint in the console. With `--debug`, the log includes the ADO response snippet and the JSON Patch paths attempted so you can identify the failing field. See [Debug Logging – Examining ADO API Errors](../reference/debug-logging.md#examining-ado-api-errors) and [Troubleshooting – Backlog refine or work item PATCH fails (400/422)](../guides/troubleshooting.md#backlog-refine-or-work-item-patch-fails-400422).

## Usage Examples

### Export Change Proposal to Azure DevOps

```python
from specfact_cli.adapters.ado import AdoAdapter

adapter = AdoAdapter(
    org="your-org",
    project="your-project",
    api_token="your_pat_token",
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

print(f"Work item created: {result['work_item_url']}")
print(f"Work item ID: {result['work_item_id']}")
```

### Import Azure DevOps Work Item as Change Proposal

```python
from specfact_cli.adapters.ado import AdoAdapter
from unittest.mock import MagicMock

adapter = AdoAdapter(
    org="your-org",
    project="your-project",
    api_token="your_pat_token",
)

# Azure DevOps work item data (from API)
work_item_data = {
    "id": 123,
    "fields": {
        "System.Title": "Add Feature X",
        "System.Description": "## Why\n\nNeeded\n\n## What Changes\n\nImplement",
        "System.State": "New",
        "System.WorkItemType": "User Story",
        "System.CreatedDate": "2025-01-01T10:00:00Z",
    },
    "_links": {
        "html": {"href": "https://dev.azure.com/your-org/your-project/_workitems/edit/123"}
    },
}

# Mock project bundle
project_bundle = MagicMock()
project_bundle.change_tracking = ChangeTracking()
project_bundle.bundle_dir = Path("/path/to/repo")

# Import work item
adapter.import_artifact(
    artifact_key="ado_work_item",
    artifact_path=work_item_data,
    project_bundle=project_bundle,
)

# Access imported proposal
proposal = project_bundle.change_tracking.proposals["123"]
print(f"Imported: {proposal.title} - {proposal.status}")
```

### Status Synchronization

```python
# Sync OpenSpec status to Azure DevOps
proposal = {
    "status": "in-progress",
    "source_tracking": {"source_id": "123"},
}

result = adapter.sync_status_to_ado(
    proposal=proposal,
    org="your-org",
    project="your-project",
)

print(f"State updated: {result['state']}")

# Sync Azure DevOps status to OpenSpec
work_item_data = {
    "fields": {"System.State": "Active"},
}

resolved_status = adapter.sync_status_from_ado(
    work_item_data=work_item_data,
    proposal={"status": "proposed"},
    strategy="prefer_backlog",  # or "prefer_openspec", "merge"
)

print(f"Resolved status: {resolved_status}")
```

### Update Work Item Body

```python
# Update existing work item description
proposal_data = {
    "change_id": "add-feature-x",
    "title": "Add Feature X (Updated)",
    "description": "Updated implementation details",
    "rationale": "Updated rationale",
    "status": "in-progress",
    "source_tracking": {
        "source_id": "123",  # Work item ID
        "source_repo": "your-org/your-project",
    },
}

result = adapter.export_artifact(
    artifact_key="change_proposal_update",
    artifact_data=proposal_data,
)

print(f"Work item updated: {result['work_item_url']}")
```

## Cross-Repository Support

The adapter supports cross-repository scenarios using `bridge_config.external_base_path`:

```yaml
# bridge_config.yaml
adapter: ado
external_base_path: ../openspec-repo  # External OpenSpec repository
```

When `external_base_path` is set:

- OpenSpec repository is loaded from the external path
- All path operations respect the external base path
- Change proposals can reference external repositories

## Work Item Description Format

Azure DevOps work items created from change proposals follow this format:

```markdown
# [Title]

## Why

[Rationale from change proposal]

## What Changes

[Description from change proposal]

---

*OpenSpec Change Proposal: `change-id`*
```

When importing Azure DevOps work items, the adapter parses this format to extract:

- **Why section**: Rationale
- **What Changes section**: Description
- **OpenSpec metadata footer**: Change ID

### Markdown Format Support

The adapter sets `multilineFieldsFormat` to `"Markdown"` when creating/updating work items (ADO supports Markdown as of July 2025). This ensures proper rendering of:

- Headers (`#`, `##`, etc.)
- Lists (ordered and unordered)
- Code blocks
- Links
- Bold/italic text

### HTML to Markdown Conversion

When importing work items that were created in HTML format, the adapter automatically converts HTML to markdown:

- HTML tags are converted to markdown equivalents
- Preserves formatting and structure
- Handles nested elements correctly

## Status Synchronization

### Conflict Resolution

When OpenSpec and Azure DevOps status differ, the adapter supports three conflict resolution strategies:

1. **`prefer_openspec`** (default): Use OpenSpec status as source of truth
2. **`prefer_backlog`**: Use Azure DevOps status as source of truth
3. **`merge`**: Use most advanced status (applied > in-progress > proposed)

**Example:**

```python
# OpenSpec: "proposed", ADO: "Active"
resolved = adapter.sync_status_from_ado(
    work_item_data={"fields": {"System.State": "Active"}},
    proposal={"status": "proposed"},
    strategy="merge",  # Results in "in-progress" (more advanced)
)
```

## Lossless Content Preservation

The Azure DevOps adapter stores raw content when importing work items to enable lossless round-trip syncs:

```python
# When importing, raw content is automatically stored
proposal = adapter.import_backlog_item_as_proposal(work_item_data, "ado", bridge_config)

# Raw content stored in source_tracking.source_metadata
raw_title = proposal.source_tracking.source_metadata.get("raw_title")
raw_body = proposal.source_tracking.source_metadata.get("raw_body")
raw_format = proposal.source_tracking.source_metadata.get("raw_format")  # "markdown"
```

When exporting from stored bundles, the adapter uses raw content if available to preserve 100% fidelity, even when syncing to a different adapter (e.g., ADO → GitHub).

**See**: [Cross-Adapter Sync Guide](../guides/devops-adapter-integration.md#cross-adapter-sync-lossless-round-trip-migration) for complete documentation.

## Source Tracking Matching

The adapter uses a three-level matching strategy to prevent duplicate work items:

1. **Exact match**: Match by exact `source_repo` (e.g., `org/project`)
2. **Org + type match**: For ADO, match by organization and work item type when project names differ or URLs contain GUIDs
3. **Org-only match**: For ADO, match by organization only when project names differ

This handles cases where:

- ADO URLs contain GUIDs instead of project names (e.g., `dominikusnold/69b5d0c2-2400-470d-b937-b5205503a679`)
- Project names change but organization stays the same
- Work items are synced across different projects in the same organization

## CLI Usage

### Basic Export

```bash
# Export OpenSpec change proposals to Azure DevOps work items
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --repo /path/to/openspec-repo
```

### Bidirectional Sync

```bash
# Import work items AND export proposals
specfact sync bridge --adapter ado --bidirectional \
  --ado-org your-org \
  --ado-project your-project \
  --repo /path/to/openspec-repo
```

### Selective Import

```bash
# Import specific work items into bundle
specfact sync bridge --adapter ado --mode bidirectional \
  --ado-org your-org \
  --ado-project your-project \
  --bundle main \
  --backlog-ids 123,456 \
  --repo /path/to/openspec-repo
```

### Update Existing Work Items

```bash
# Update existing work item with latest proposal content
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --change-ids add-feature-x \
  --update-existing \
  --repo /path/to/openspec-repo
```

### Track Code Changes

```bash
# Detect code changes and add progress comments
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --track-code-changes \
  --repo /path/to/openspec-repo \
  --code-repo /path/to/source-code-repo
```

### Cross-Adapter Export

```bash
# Export from bundle to ADO (uses stored lossless content)
specfact sync bridge --adapter ado --mode export-only \
  --ado-org your-org \
  --ado-project your-project \
  --bundle main \
  --change-ids <change-id> \
  --repo /path/to/openspec-repo
```

## Limitations

### Current Limitations

- **Single Organization/Project**: Each adapter instance is configured for one organization and project
- **State-Based Status**: Status sync relies on Azure DevOps work item state (not tags/labels)
- **Process Template Dependency**: Work item type derivation requires process template access
- **Azure DevOps Services Only**: Azure DevOps Server (on-prem) support is limited (requires custom base URL)

### Future Enhancements

- **Multi-Project Support**: Support for multiple projects in one adapter instance
- **Automatic Work Item Type Detection**: Enhanced detection for custom process templates
- **Area/Iteration Path Support**: Sync area and iteration path fields
- **Custom Field Mapping**: Support for custom work item fields
- **Assignee Sync**: Sync assignees between OpenSpec and Azure DevOps

## Troubleshooting

### Common Issues

**Issue: "Azure DevOps API token required"**

- Ensure `AZURE_DEVOPS_TOKEN` environment variable is set, or
- Provide `--ado-token` CLI flag, or
- Verify token has **Work Items (Read & Write)** permissions

**Issue: "Azure DevOps organization and project required"**

- Provide `--ado-org` and `--ado-project` CLI flags, or
- Verify organization and project names are correct

**Issue: "Work item ID not found in source_tracking"**

- Work item must be created first (export change proposal)
- Check that `source_tracking` contains `source_id` for the repository
- Verify three-level matching logic is working correctly

**Issue: Status sync doesn't update work item state**

- Verify API token has write permissions
- Check that work item state name matches process template (e.g., "Active" vs "In Progress")
- Ensure work item ID is correct in `source_tracking`

**Issue: Work item type not found**

- Verify process template is accessible (Scrum, Agile, or Kanban)
- Check that work item type exists in the project
- Use `--ado-work-item-type` to override automatic detection

**Issue: HTML content not converted to markdown**

- Check that `_normalize_description()` is being called during import
- Verify HTML content is in `System.Description` field
- Check that `raw_format` is set to "markdown" in source_metadata

## Related Documentation

- **[Backlog Adapter Patterns](./backlog-adapter-patterns.md)** - Patterns for backlog adapters
- **[GitHub Adapter](./github.md)** - GitHub adapter documentation
- **[Validation Integration](../validation-integration.md)** - Validation with change proposals
- **[DevOps Adapter Integration](../guides/devops-adapter-integration.md)** - DevOps workflow integration
