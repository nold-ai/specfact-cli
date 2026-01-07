# Adapter Development Guide

This guide explains how to create new bridge adapters for SpecFact CLI using the adapter registry pattern.

## Overview

SpecFact CLI uses a plugin-based adapter architecture that allows external tools (GitHub, Spec-Kit, Linear, Jira, etc.) to integrate seamlessly. All adapters implement the `BridgeAdapter` interface and are registered in the `AdapterRegistry` for automatic discovery and usage.

## Architecture

### Adapter Registry Pattern

The adapter registry provides a centralized way to:

- **Register adapters**: Auto-discover and register adapters at import time
- **Get adapters**: Retrieve adapters by name (e.g., `"speckit"`, `"github"`, `"openspec"`)
- **List adapters**: Enumerate all registered adapters
- **Check registration**: Verify if an adapter is registered

### BridgeAdapter Interface

All adapters must implement the `BridgeAdapter` abstract base class, which defines the following methods:

```python
class BridgeAdapter(ABC):
    @abstractmethod
    def detect(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool:
        """Detect if this adapter applies to the repository."""
    
    @abstractmethod
    def get_capabilities(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> ToolCapabilities:
        """Get tool capabilities for detected repository."""
    
    @abstractmethod
    def import_artifact(self, artifact_key: str, artifact_path: Path | dict[str, Any], project_bundle: Any, bridge_config: BridgeConfig | None = None) -> None:
        """Import artifact from tool format to SpecFact."""
    
    @abstractmethod
    def export_artifact(self, artifact_key: str, artifact_data: Any, bridge_config: BridgeConfig | None = None) -> Path | dict[str, Any]:
        """Export artifact from SpecFact to tool format."""
    
    @abstractmethod
    def generate_bridge_config(self, repo_path: Path) -> BridgeConfig:
        """Generate bridge configuration for this adapter."""
    
    @abstractmethod
    def load_change_tracking(self, bundle_dir: Path, bridge_config: BridgeConfig | None = None) -> ChangeTracking | None:
        """Load change tracking (adapter-specific storage location)."""
    
    @abstractmethod
    def save_change_tracking(self, bundle_dir: Path, change_tracking: ChangeTracking, bridge_config: BridgeConfig | None = None) -> None:
        """Save change tracking (adapter-specific storage location)."""
    
    @abstractmethod
    def load_change_proposal(self, change_id: str, bridge_config: BridgeConfig | None = None) -> ChangeProposal | None:
        """Load change proposal from adapter-specific location."""
    
    @abstractmethod
    def save_change_proposal(self, change_proposal: ChangeProposal, bridge_config: BridgeConfig | None = None) -> None:
        """Save change proposal to adapter-specific location."""
```

## Step-by-Step Guide

### Step 1: Create Adapter Module

Create a new file `src/specfact_cli/adapters/<adapter_name>.py`:

```python
"""
<Adapter Name> bridge adapter for <tool description>.

This adapter implements the BridgeAdapter interface to sync <tool> artifacts
with SpecFact plan bundles and protocols.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from beartype import beartype
from icontract import ensure, require

from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.capabilities import ToolCapabilities
from specfact_cli.models.change import ChangeProposal, ChangeTracking


class MyAdapter(BridgeAdapter):
    """
    <Adapter Name> bridge adapter implementing BridgeAdapter interface.
    
    This adapter provides <sync direction> sync between <tool> artifacts
    and SpecFact plan bundles/protocols.
    """
    
    @beartype
    @ensure(lambda result: result is None, "Must return None")
    def __init__(self) -> None:
        """Initialize <Adapter Name> adapter."""
        pass
    
    # Implement all abstract methods...
```

### Step 2: Implement Required Methods

#### 2.1 Implement `detect()`

Detect if the repository uses your tool:

```python
@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def detect(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool:
    """
    Detect if this is a <tool name> repository.
    
    Args:
        repo_path: Path to repository root
        bridge_config: Optional bridge configuration (for cross-repo detection)
    
    Returns:
        True if <tool> structure detected, False otherwise
    """
    # Check for cross-repo support
    base_path = repo_path
    if bridge_config and bridge_config.external_base_path:
        base_path = bridge_config.external_base_path
    
    # Check for tool-specific structure
    # Example: Check for .tool/ directory or tool-specific files
    tool_dir = base_path / ".tool"
    config_file = base_path / "tool.config"
    
    return (tool_dir.exists() and tool_dir.is_dir()) or config_file.exists()
```

#### 2.2 Implement `get_capabilities()`

Return tool capabilities:

```python
@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
@ensure(lambda result: isinstance(result, ToolCapabilities), "Must return ToolCapabilities")
def get_capabilities(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> ToolCapabilities:
    """
    Get <tool name> adapter capabilities.
    
    Args:
        repo_path: Path to repository root
        bridge_config: Optional bridge configuration (for cross-repo detection)
    
    Returns:
        ToolCapabilities instance for <tool> adapter
    """
    from specfact_cli.models.capabilities import ToolCapabilities
    
    base_path = repo_path
    if bridge_config and bridge_config.external_base_path:
        base_path = bridge_config.external_base_path
    
    # Determine tool-specific capabilities
    return ToolCapabilities(
        tool="<tool-name>",
        layout="<layout-type>",
        specs_dir="<specs-directory>",
        supported_sync_modes=["<sync-mode-1>", "<sync-mode-2>"],  # e.g., ["bidirectional", "unidirectional"]
        has_custom_hooks=False,  # Set to True if tool has custom hooks/constitution
    )
```

#### 2.3 Implement `generate_bridge_config()`

Generate bridge configuration:

```python
@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
@ensure(lambda result: isinstance(result, BridgeConfig), "Must return BridgeConfig")
def generate_bridge_config(self, repo_path: Path) -> BridgeConfig:
    """
    Generate bridge configuration for <tool name> adapter.
    
    Args:
        repo_path: Path to repository root
    
    Returns:
        BridgeConfig instance for <tool> adapter
    """
    from specfact_cli.models.bridge import AdapterType, ArtifactMapping, BridgeConfig
    
    # Auto-detect layout and create appropriate config
    # Use existing preset methods if available, or create custom config
    return BridgeConfig(
        adapter=AdapterType.<TOOL_NAME>,
        artifacts={
            "specification": ArtifactMapping(
                path_pattern="<path-pattern>",
                format="<format>",
            ),
            # Add other artifact mappings...
        },
    )
```

#### 2.4 Implement `import_artifact()`

Import artifacts from tool format:

```python
@beartype
@require(
    lambda artifact_key: isinstance(artifact_key, str) and len(artifact_key) > 0, "Artifact key must be non-empty"
)
@ensure(lambda result: result is None, "Must return None")
def import_artifact(
    self,
    artifact_key: str,
    artifact_path: Path | dict[str, Any],
    project_bundle: Any,  # ProjectBundle - avoid circular import
    bridge_config: BridgeConfig | None = None,
) -> None:
    """
    Import artifact from <tool name> format to SpecFact.
    
    Args:
        artifact_key: Artifact key (e.g., "specification", "plan", "tasks")
        artifact_path: Path to artifact file or dict for API-based artifacts
        project_bundle: Project bundle to update
        bridge_config: Bridge configuration (may contain adapter-specific settings)
    """
    # Parse tool-specific format and update project_bundle
    # Store tool-specific paths in source_tracking.source_metadata
    pass
```

#### 2.5 Implement `export_artifact()`

Export artifacts to tool format:

```python
@beartype
@require(
    lambda artifact_key: isinstance(artifact_key, str) and len(artifact_key) > 0, "Artifact key must be non-empty"
)
@ensure(lambda result: isinstance(result, (Path, dict)), "Must return Path or dict")
def export_artifact(
    self,
    artifact_key: str,
    artifact_data: Any,  # Feature, ChangeProposal, etc. - avoid circular import
    bridge_config: BridgeConfig | None = None,
) -> Path | dict[str, Any]:
    """
    Export artifact from SpecFact to <tool name> format.
    
    Args:
        artifact_key: Artifact key (e.g., "specification", "plan", "tasks")
        artifact_data: Data to export (Feature, Plan, etc.)
        bridge_config: Bridge configuration (may contain adapter-specific settings)
    
    Returns:
        Path to exported file or dict with API response data
    """
    # Convert SpecFact models to tool-specific format
    # Write to file or send via API
    # Return Path for file-based exports, dict for API-based exports
    pass
```

#### 2.6 Implement Change Tracking Methods

For adapters that support change tracking:

```python
@beartype
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
@require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
@ensure(lambda result: result is None or isinstance(result, ChangeTracking), "Must return ChangeTracking or None")
def load_change_tracking(
    self, bundle_dir: Path, bridge_config: BridgeConfig | None = None
) -> ChangeTracking | None:
    """Load change tracking from tool-specific location."""
    # Return None if tool doesn't support change tracking
    return None

@beartype
@require(lambda bundle_dir: isinstance(bundle_dir, Path), "Bundle directory must be Path")
@require(lambda bundle_dir: bundle_dir.exists(), "Bundle directory must exist")
@ensure(lambda result: result is None, "Must return None")
def save_change_tracking(
    self, bundle_dir: Path, change_tracking: ChangeTracking, bridge_config: BridgeConfig | None = None
) -> None:
    """Save change tracking to tool-specific location."""
    # Raise NotImplementedError if tool doesn't support change tracking
    raise NotImplementedError("Change tracking not supported by this adapter")
```

#### 2.7 Implement Change Proposal Methods

For adapters that support change proposals:

```python
@beartype
@require(lambda change_id: isinstance(change_id, str) and len(change_id) > 0, "Change ID must be non-empty")
@ensure(lambda result: result is None or isinstance(result, ChangeProposal), "Must return ChangeProposal or None")
def load_change_proposal(
    self, change_id: str, bridge_config: BridgeConfig | None = None
) -> ChangeProposal | None:
    """Load change proposal from tool-specific location."""
    # Return None if tool doesn't support change proposals
    return None

@beartype
@require(lambda change_proposal: isinstance(change_proposal, ChangeProposal), "Must provide ChangeProposal")
@ensure(lambda result: result is None, "Must return None")
def save_change_proposal(
    self, change_proposal: ChangeProposal, bridge_config: BridgeConfig | None = None
) -> None:
    """Save change proposal to tool-specific location."""
    # Raise NotImplementedError if tool doesn't support change proposals
    raise NotImplementedError("Change proposals not supported by this adapter")
```

### Step 3: Register Adapter

Register your adapter in `src/specfact_cli/adapters/__init__.py`:

```python
from specfact_cli.adapters.my_adapter import MyAdapter
from specfact_cli.adapters.registry import AdapterRegistry

# Auto-register adapter
AdapterRegistry.register("my-adapter", MyAdapter)

__all__ = [..., "MyAdapter"]
```

**Important**: Use the actual CLI tool name as the registry key (e.g., `"speckit"`, `"github"`, not `"spec-kit"` or `"git-hub"`).

### Step 4: Add Contract Decorators

All methods must have contract decorators:

- `@beartype`: Runtime type checking
- `@require`: Preconditions (input validation)
- `@ensure`: Postconditions (output validation)

Example:

```python
@beartype
@require(lambda repo_path: repo_path.exists(), "Repository path must exist")
@require(lambda repo_path: repo_path.is_dir(), "Repository path must be a directory")
@ensure(lambda result: isinstance(result, bool), "Must return bool")
def detect(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool:
    # Implementation...
```

### Step 5: Add Tests

Create comprehensive tests in `tests/unit/adapters/test_my_adapter.py`:

```python
"""Unit tests for MyAdapter."""

import pytest
from pathlib import Path

from specfact_cli.adapters.my_adapter import MyAdapter
from specfact_cli.adapters.registry import AdapterRegistry
from specfact_cli.models.bridge import BridgeConfig


class TestMyAdapter:
    """Test MyAdapter class."""
    
    def test_detect(self, tmp_path: Path):
        """Test detect() method."""
        adapter = MyAdapter()
        # Create tool-specific structure
        (tmp_path / ".tool").mkdir()
        
        assert adapter.detect(tmp_path) is True
    
    def test_get_capabilities(self, tmp_path: Path):
        """Test get_capabilities() method."""
        adapter = MyAdapter()
        capabilities = adapter.get_capabilities(tmp_path)
        
        assert capabilities.tool == "my-adapter"
        assert "bidirectional" in capabilities.supported_sync_modes
    
    def test_adapter_registry_registration(self):
        """Test adapter is registered in registry."""
        assert AdapterRegistry.is_registered("my-adapter")
        adapter_class = AdapterRegistry.get_adapter("my-adapter")
        assert adapter_class == MyAdapter
```

### Step 6: Update Documentation

1. **Update `docs/reference/architecture.md`**: Add your adapter to the adapters section
2. **Update `README.md`**: Add your adapter to the supported tools list
3. **Update `CHANGELOG.md`**: Document the new adapter addition

## Examples

### SpecKitAdapter (Bidirectional Sync)

The `SpecKitAdapter` is a complete example of a bidirectional sync adapter:

- **Location**: `src/specfact_cli/adapters/speckit.py`
- **Registry key**: `"speckit"`
- **Features**: Bidirectional sync, classic/modern layout support, constitution management
- **Public helpers**: `discover_features()`, `detect_changes()`, `detect_conflicts()`, `export_bundle()`

### GitHubAdapter (Export-Only)

The `GitHubAdapter` is an example of an export-only adapter:

- **Location**: `src/specfact_cli/adapters/github.py`
- **Registry key**: `"github"`
- **Features**: Export-only (OpenSpec → GitHub Issues), progress tracking, content sanitization

### OpenSpecAdapter (Bidirectional Sync)

The `OpenSpecAdapter` is an example of a bidirectional sync adapter with change tracking:

- **Location**: `src/specfact_cli/adapters/openspec.py`
- **Registry key**: `"openspec"`
- **Features**: Bidirectional sync, change tracking, change proposals

## Best Practices

### 1. Use Adapter Registry Pattern

**✅ DO:**

```python
# In commands/sync.py
adapter = AdapterRegistry.get_adapter(adapter_name)
if adapter:
    adapter_instance = adapter()
    if adapter_instance.detect(repo_path, bridge_config):
        # Use adapter...
```

**❌ DON'T:**

```python
# Hard-coded adapter checks
if adapter_name == "speckit":
    adapter = SpecKitAdapter()
elif adapter_name == "github":
    adapter = GitHubAdapter()
```

### 2. Support Cross-Repo Detection

Always check `bridge_config.external_base_path` for cross-repository support:

```python
base_path = repo_path
if bridge_config and bridge_config.external_base_path:
    base_path = bridge_config.external_base_path

# Use base_path for all file operations
tool_dir = base_path / ".tool"
```

### 3. Store Source Metadata

When importing artifacts, store tool-specific paths in `source_tracking.source_metadata`:

```python
if hasattr(project_bundle, "source_tracking") and project_bundle.source_tracking:
    project_bundle.source_tracking.source_metadata = {
        "tool": "my-adapter",
        "original_path": str(artifact_path),
        "tool_version": "1.0.0",
    }
```

### 4. Handle Missing Artifacts Gracefully

Return appropriate error messages when artifacts are not found:

```python
if not artifact_path.exists():
    raise FileNotFoundError(
        f"Artifact '{artifact_key}' not found at {artifact_path}. "
        f"Expected location: {expected_path}"
    )
```

### 5. Use Contract Decorators

Always add contract decorators for runtime validation:

```python
@beartype
@require(lambda artifact_key: len(artifact_key) > 0, "Artifact key must be non-empty")
@ensure(lambda result: result is not None, "Must return non-None value")
def import_artifact(self, artifact_key: str, ...) -> None:
    # Implementation...
```

## Testing

### Unit Tests

Create comprehensive unit tests covering:

- Detection logic (same-repo and cross-repo)
- Capabilities retrieval
- Artifact import/export for all supported artifact types
- Error handling
- Adapter registry registration

### Integration Tests

Create integration tests covering:

- Full sync workflows
- Bidirectional sync (if supported)
- Cross-repo scenarios
- Error recovery

## Troubleshooting

### Adapter Not Detected

- Check `detect()` method logic
- Verify tool-specific structure exists
- Check `bridge_config.external_base_path` for cross-repo scenarios

### Import/Export Failures

- Verify artifact paths are resolved correctly
- Check `bridge_config.external_base_path` for cross-repo scenarios
- Ensure artifact format matches tool expectations

### Registry Registration Issues

- Verify adapter is imported in `adapters/__init__.py`
- Check registry key matches actual tool name
- Ensure `AdapterRegistry.register()` is called at module import time

## Related Documentation

- **[Architecture Documentation](../reference/architecture.md)**: Adapter architecture overview
- **[Architecture Documentation](../reference/architecture.md)**: Adapter architecture and BridgeConfig/ToolCapabilities models
- **[SpecKitAdapter Example](../../src/specfact_cli/adapters/speckit.py)**: Complete bidirectional sync example
- **[GitHubAdapter Example](../../src/specfact_cli/adapters/github.py)**: Export-only adapter example
