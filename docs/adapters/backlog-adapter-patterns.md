---
layout: default
title: Backlog Adapter Patterns
permalink: /adapters/backlog-adapter-patterns/
---

# Backlog Adapter Patterns

This document describes the extensible patterns for implementing backlog adapters (GitHub, Azure DevOps, Jira, Linear, etc.) that support bidirectional sync between backlog management tools and OpenSpec change proposals.

## Overview

Backlog adapters enable bidirectional synchronization between OpenSpec change proposals and backlog management tools:

- **Export**: OpenSpec change proposals → Backlog items (issues, work items, tickets)
- **Import**: Backlog items → OpenSpec change proposals
- **Status Sync**: Bidirectional status synchronization with conflict resolution
- **Lossless Content Preservation**: Store raw content for round-trip syncs across adapters
- **Cross-Adapter Sync**: Export stored bundle content to any backlog adapter with 100% fidelity

The GitHub adapter is the first implementation. The Azure DevOps (ADO) adapter is now available with full feature parity and follows these patterns. Future backlog adapters (Jira, Linear) should follow the same patterns.

### Key Capability: Lossless Round-Trip Sync

> **🚀 Advanced Feature**: One of SpecFact's most powerful capabilities for DevOps teams.

Backlog adapters support **lossless round-trip synchronization** between different backlog tools (GitHub ↔ ADO ↔ others). This enables:

- **Tool Migration**: Migrate between backlog tools without losing content
- **Multi-Tool Workflows**: Sync proposals across different tools used by different teams
- **Content Fidelity**: Preserve exact formatting, sections, and metadata across adapter boundaries
- **Day-to-Day Developer Experience**: Keep backlogs in sync with feature branches, code changes, and validations

**How it works**: When importing from any backlog adapter, the original raw content (title, body) is stored in `source_tracking.source_metadata` as `raw_title` and `raw_body`. When exporting from stored bundles, this raw content is used to ensure 100% fidelity, even when syncing to a different adapter than the original source.

## Architecture

### BacklogAdapterMixin

All backlog adapters should inherit from `BacklogAdapterMixin` to get common functionality:

```python
from specfact_cli.adapters.backlog_base import BacklogAdapterMixin
from specfact_cli.adapters.base import BridgeAdapter

class MyBacklogAdapter(BridgeAdapter, BacklogAdapterMixin):
    """My backlog adapter implementation."""
    
    # Implement abstract methods from BacklogAdapterMixin
    def map_backlog_status_to_openspec(self, status: str) -> str:
        """Map backlog tool status to OpenSpec status."""
        # Tool-specific mapping logic
        pass
    
    def map_openspec_status_to_backlog(self, status: str) -> list[str]:
        """Map OpenSpec status to backlog tool status."""
        # Tool-specific mapping logic
        pass
    
    def extract_change_proposal_data(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """Extract change proposal data from backlog item."""
        # Tool-specific parsing logic
        pass
```

### Tool-Agnostic Patterns

The mixin provides reusable patterns:

1. **Status Mapping**: Tool-agnostic status mapping interface
2. **Metadata Extraction**: Tool-agnostic metadata extraction interface
3. **Conflict Resolution**: Reusable conflict resolution strategies
4. **Source Tracking**: Common pattern for storing tool-specific metadata

## Implementation Guide

### Step 1: Implement Abstract Methods

Implement the three abstract methods from `BacklogAdapterMixin`:

#### 1.1 Status Mapping (Backlog → OpenSpec)

```python
def map_backlog_status_to_openspec(self, status: str) -> str:
    """
    Map backlog tool status to OpenSpec change status.
    
    Args:
        status: Backlog tool status (e.g., GitHub label, ADO state, Jira status, Linear state)
    
    Returns:
        OpenSpec change status (proposed, in-progress, applied, deprecated, discarded)
    """
    status_lower = status.lower()
    
    # Tool-specific mapping
    if status_lower in ("new", "todo", "backlog"):
        return "proposed"
    elif status_lower in ("in-progress", "active", "in development"):
        return "in-progress"
    elif status_lower in ("done", "completed", "closed"):
        return "applied"
    # ... more mappings
    
    return "proposed"  # Default
```

#### 1.2 Status Mapping (OpenSpec → Backlog)

```python
def map_openspec_status_to_backlog(self, status: str) -> list[str]:
    """
    Map OpenSpec change status to backlog tool status.
    
    Args:
        status: OpenSpec change status
    
    Returns:
        List of backlog tool status indicators (labels, states, etc.)
    """
    status_indicators = ["openspec"]  # Common prefix
    
    if status == "in-progress":
        status_indicators.append("in-progress")
    elif status == "applied":
        status_indicators.append("completed")
    # ... more mappings
    
    return status_indicators
```

#### 1.3 Data Extraction

```python
def extract_change_proposal_data(self, item_data: dict[str, Any]) -> dict[str, Any]:
    """
    Extract change proposal data from backlog item.
    
    Args:
        item_data: Backlog item data (tool-specific format)
    
    Returns:
        Dict with change proposal fields:
        - title: str
        - description: str (What Changes section)
        - rationale: str (Why section)
        - status: str (mapped to OpenSpec status)
        - Other optional fields
    """
    # Parse tool-specific format
    title = item_data.get("title", "")
    body = item_data.get("body", "") or item_data.get("description", "")
    
    # Extract sections (Why, What Changes)
    rationale = extract_section(body, "Why")
    description = extract_section(body, "What Changes")
    
    # Map status
    status = self.map_backlog_status_to_openspec(item_data.get("status", "open"))
    
    return {
        "change_id": item_data.get("id", "unknown"),
        "title": title,
        "description": description,
        "rationale": rationale,
        "status": status,
        "created_at": item_data.get("created_at", ""),
        # ... other fields
    }
```

### Step 2: Implement Import Method

Implement `import_artifact` for your backlog tool:

```python
def import_artifact(
    self,
    artifact_key: str,
    artifact_path: Path | dict[str, Any],
    project_bundle: Any,
    bridge_config: BridgeConfig | None = None,
) -> None:
    """
    Import artifact from backlog tool.
    
    Args:
        artifact_key: Artifact key (e.g., "github_issue", "ado_work_item", "jira_issue")
        artifact_path: Backlog item data (dict from API response)
        project_bundle: Project bundle to update
        bridge_config: Bridge configuration
    """
    # Supported artifact keys for backlog adapters:
    # - "change_proposal": Create new backlog item from change proposal
    # - "change_status": Update backlog item status only
    # - "change_proposal_update": Update backlog item body/content
    # - "change_proposal_comment": Add status comment to backlog item
    # - "code_change_progress": Add progress comment based on code changes
    # - "my_backlog_item": Import backlog item as change proposal (tool-specific)
    
    if artifact_key not in ["change_proposal", "change_status", "change_proposal_update", 
                            "change_proposal_comment", "code_change_progress", "my_backlog_item"]:
        raise NotImplementedError(f"Unsupported artifact key: {artifact_key}")
    
    if not isinstance(artifact_path, dict):
        raise ValueError("Backlog item import requires dict (API response)")
    
    # Use reusable pattern from BacklogAdapterMixin
    proposal = self.import_backlog_item_as_proposal(
        artifact_path, "my_backlog_tool", bridge_config
    )
    
    # Add to project bundle
    if hasattr(project_bundle, "change_tracking"):
        if not project_bundle.change_tracking:
            from specfact_cli.models.change import ChangeTracking
            project_bundle.change_tracking = ChangeTracking()
        project_bundle.change_tracking.proposals[proposal.name] = proposal
```

### Step 3: Implement Status Synchronization

Implement bidirectional status sync methods:

```python
def sync_status_to_backlog(
    self,
    proposal: dict[str, Any] | ChangeProposal,
    repo_owner: str,
    repo_name: str,
    bridge_config: BridgeConfig | None = None,
) -> dict[str, Any]:
    """
    Sync OpenSpec change status to backlog tool.
    
    Updates backlog item status based on OpenSpec change proposal status.
    """
    # Extract status and source_tracking
    # Map OpenSpec status to backlog status
    # Update backlog item via API
    # Return sync result
    pass

def sync_status_from_backlog(
    self,
    item_data: dict[str, Any],
    proposal: dict[str, Any] | ChangeProposal,
    strategy: str = "prefer_openspec",
) -> str:
    """
    Sync backlog tool status to OpenSpec change proposal.
    
    Maps backlog item status to OpenSpec status and resolves conflicts.
    """
    # Extract backlog status
    # Map to OpenSpec status
    # Resolve conflicts using BacklogAdapterMixin.resolve_status_conflict()
    # Return resolved status
    pass
```

## Status Mapping Patterns

### Common Status Mappings

| OpenSpec Status | GitHub Labels | ADO State | Jira Status | Linear State |
|----------------|---------------|-----------|-------------|--------------|
| `proposed` | `enhancement`, `new` | `New` | `To Do` | `Backlog` |
| `in-progress` | `in-progress` | `Active`, `In Progress` | `In Progress` | `In Progress` |
| `applied` | `completed` | `Closed`, `Done` | `Done` | `Done` |
| `deprecated` | `deprecated` | `Removed` | `Won't Do` | `Canceled` |
| `discarded` | `wontfix` | `Rejected` | `Rejected` | `Canceled` |

### Conflict Resolution Strategies

The mixin provides three conflict resolution strategies:

1. **`prefer_openspec`** (default): Use OpenSpec status as source of truth
2. **`prefer_backlog`**: Use backlog status as source of truth
3. **`merge`**: Use most advanced status (applied > in-progress > proposed)

```python
# Example usage
resolved_status = self.resolve_status_conflict(
    openspec_status="proposed",
    backlog_status="in-progress",
    strategy="merge"  # Results in "in-progress" (more advanced)
)
```

## Metadata Extraction Patterns

### Common Fields

All backlog adapters should extract:

- **Title**: From backlog item title
- **Description**: From "What Changes" section in body
- **Rationale**: From "Why" section in body
- **Status**: Mapped from backlog status
- **Created At**: From backlog item creation timestamp
- **Owner/Assignees**: From backlog item assignees

### Storing Tool-Specific Metadata

Tool-specific metadata should be stored in `source_tracking.source_metadata`, not in core models:

```python
source_tracking = self.create_source_tracking(item_data, "my_backlog_tool", bridge_config)

# Add tool-specific fields
source_tracking.source_metadata["my_tool_field"] = item_data.get("my_tool_field")
source_tracking.source_metadata["my_tool_id"] = item_data.get("id")
```

### Lossless Content Preservation

**Critical for cross-adapter sync**: Always store raw content when importing backlog items:

```python
def import_artifact(
    self,
    artifact_key: str,
    artifact_path: Path | dict[str, Any],
    project_bundle: Any,
    bridge_config: BridgeConfig | None = None,
) -> None:
    """Import backlog item with lossless content preservation."""
    # ... import logic ...
    
    # CRITICAL: Store raw content for lossless round-trip sync
    if proposal.source_tracking and isinstance(proposal.source_tracking.source_metadata, dict):
        source_metadata = proposal.source_tracking.source_metadata
        raw_title = item_data.get("title") or ""
        raw_body = item_data.get("body") or item_data.get("description") or ""
        source_metadata["raw_title"] = raw_title
        source_metadata["raw_body"] = raw_body
        source_metadata["raw_format"] = "markdown"  # or "html" if applicable
```

**When exporting**, check for raw content first to preserve fidelity:

```python
def export_artifact(
    self,
    artifact_key: str,
    artifact_data: Any,
    bridge_config: BridgeConfig | None = None,
) -> dict[str, Any] | Path:
    """Export with lossless content preservation."""
    # Extract raw content if available
    raw_title, raw_body = self._extract_raw_fields(artifact_data)
    
    # Use raw content if available, otherwise construct from proposal data
    if raw_title:
        title = raw_title
    else:
        title = artifact_data.get("title", "Untitled")
    
    if raw_body:
        body = raw_body
    else:
        # Construct body from proposal sections
        body = self._construct_body_from_proposal(artifact_data)
    
    # ... export logic using title and body ...
```

**Helper method** for extracting raw content:

```python
def _extract_raw_fields(self, proposal_data: dict[str, Any]) -> tuple[str | None, str | None]:
    """Extract lossless title/body content from proposal data."""
    raw_title = proposal_data.get("raw_title")
    raw_body = proposal_data.get("raw_body")
    if raw_title and raw_body:
        return raw_title, raw_body
    
    # Check source_tracking metadata
    source_tracking = proposal_data.get("source_tracking")
    source_metadata = None
    if isinstance(source_tracking, dict):
        source_metadata = source_tracking.get("source_metadata")
    elif hasattr(source_tracking, "source_metadata"):
        source_metadata = getattr(source_tracking, "source_metadata")
    
    if isinstance(source_metadata, dict):
        raw_title = raw_title or source_metadata.get("raw_title")
        raw_body = raw_body or source_metadata.get("raw_body")
    
    return raw_title, raw_body
```

## Testing Patterns

### Unit Test Structure

```python
class TestMyBacklogAdapter:
    """Test my backlog adapter implementation."""
    
    def test_map_backlog_status_to_openspec(self, adapter):
        """Test status mapping from backlog to OpenSpec."""
        assert adapter.map_backlog_status_to_openspec("new") == "proposed"
        assert adapter.map_backlog_status_to_openspec("in-progress") == "in-progress"
    
    def test_extract_change_proposal_data(self, adapter):
        """Test extracting change proposal data."""
        item_data = {
            "title": "Test Issue",
            "body": "## Why\n\nTest\n\n## What Changes\n\nImplement",
            "status": "new",
        }
        result = adapter.extract_change_proposal_data(item_data)
        assert result["title"] == "Test Issue"
        assert result["status"] == "proposed"
    
    def test_import_artifact(self, adapter, project_bundle):
        """Test importing backlog item."""
        item_data = {...}
        adapter.import_artifact("my_backlog_item", item_data, project_bundle)
        assert "123" in project_bundle.change_tracking.proposals
```

### Integration Test Structure

```python
class TestBidirectionalBacklogSync:
    """Integration tests for bidirectional backlog sync."""
    
    def test_openspec_to_backlog_export(self, adapter):
        """Test OpenSpec → Backlog export."""
        # Test export
        pass
    
    def test_backlog_to_openspec_import(self, adapter):
        """Test Backlog → OpenSpec import."""
        # Test import
        pass
    
    def test_bidirectional_status_sync(self, adapter):
        """Test bidirectional status sync."""
        # Test status sync
        pass
```

## Reference Implementations

### GitHub Adapter

The GitHub adapter (`src/specfact_cli/adapters/github.py`) serves as the reference implementation:

- **Status Mapping**: See `map_backlog_status_to_openspec()` and `map_openspec_status_to_backlog()`
- **Data Extraction**: See `extract_change_proposal_data()`
- **Import**: See `import_artifact()` with `artifact_key="github_issue"`
- **Status Sync**: See `sync_status_to_github()` and `sync_status_from_github()`

### Azure DevOps Adapter

The Azure DevOps adapter (`src/specfact_cli/adapters/ado.py`) demonstrates:

- **Status Mapping**: ADO state mapping (New/Active/Closed ↔ OpenSpec status)
- **Work Item Type Derivation**: Automatic detection from process template (Scrum/Kanban/Agile)
- **Data Extraction**: Parsing ADO work item fields (System.Title, System.Description, System.State)
- **Import**: See `import_artifact()` with `artifact_key="ado_work_item"`
- **Export**: See `export_artifact()` with `artifact_key="change_proposal"`, `"change_status"`, `"change_proposal_update"`, `"change_proposal_comment"`, or `"code_change_progress"`
- **Status Sync**: See `sync_status_to_ado()` and `sync_status_from_ado()` methods
- **Comments**: See `_add_work_item_comment()` and `_add_progress_comment()` methods

## Best Practices

1. **Tool-Agnostic Core Models**: Keep `ChangeProposal` and `FeatureDelta` tool-agnostic
2. **Source Tracking**: Store all tool-specific metadata in `source_tracking.source_metadata`
3. **Error Handling**: Raise `ValueError` for invalid inputs, `NotImplementedError` for unsupported operations
4. **Contract Decorators**: Add `@beartype` and `@icontract` decorators to all public methods
5. **Comprehensive Tests**: Test status mapping, data extraction, import, export, and status sync
6. **Documentation**: Document tool-specific patterns and limitations

## Future Adapters

When implementing new backlog adapters:

1. Follow the GitHub adapter pattern
2. Implement the three abstract methods from `BacklogAdapterMixin`
3. Use reusable utilities from the mixin
4. Store tool-specific metadata in `source_tracking` only
5. Add comprehensive unit and integration tests
6. Document tool-specific patterns and limitations

## Related Documentation

- **[GitHub Adapter Documentation](./github.md)** - GitHub adapter reference
- **[Azure DevOps Adapter Documentation](./azuredevops.md)** - Azure DevOps adapter reference
- **[DevOps Adapter Integration Guide](../guides/devops-adapter-integration.md)** - Complete integration guide for GitHub and ADO
- **[Validation Integration](../validation-integration.md)** - Validation with change proposals
- **[Bridge Adapter Interface](../bridge-adapter-interface.md)** - Base adapter interface
