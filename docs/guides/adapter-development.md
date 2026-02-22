---
layout: default
title: Adapter Development Guide
permalink: /guides/adapter-development/
description: Implement BridgeAdapter integrations for external tools.
---

# Adapter Development Guide

This guide describes how to implement bridge adapters for external tools.

## Core interface

Base contract: `src/specfact_cli/adapters/base.py`

Required methods:

- `detect(repo_path, bridge_config=None) -> bool`
- `get_capabilities(repo_path, bridge_config=None) -> ToolCapabilities`
- `import_artifact(artifact_key, artifact_path, project_bundle, bridge_config=None) -> None`
- `export_artifact(artifact_key, artifact_data, bridge_config=None) -> Path | dict`
- `generate_bridge_config(repo_path) -> BridgeConfig`
- `load_change_tracking(bundle_dir, bridge_config=None) -> ChangeTracking | None`
- `save_change_tracking(bundle_dir, change_tracking, bridge_config=None) -> None`
- `load_change_proposal(bundle_dir, change_name, bridge_config=None) -> ChangeProposal | None`
- `save_change_proposal(bundle_dir, proposal, bridge_config=None) -> None`

All methods should preserve runtime contracts (`@icontract`) and runtime type checks (`@beartype`).

## ToolCapabilities model

`ToolCapabilities` lives in `src/specfact_cli/models/capabilities.py` and communicates runtime support:

- `tool`, `version`, `layout`, `specs_dir`
- `supported_sync_modes`
- `has_external_config`, `has_custom_hooks`

Sync selection and safe behavior depend on this model.

## Minimal adapter skeleton

```python
from pathlib import Path
from typing import Any

from specfact_cli.adapters.base import BridgeAdapter
from specfact_cli.models.bridge import BridgeConfig
from specfact_cli.models.capabilities import ToolCapabilities
from specfact_cli.models.change import ChangeProposal, ChangeTracking


class MyAdapter(BridgeAdapter):
    def detect(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> bool:
        return (repo_path / ".mytool").exists()

    def get_capabilities(self, repo_path: Path, bridge_config: BridgeConfig | None = None) -> ToolCapabilities:
        return ToolCapabilities(tool="mytool", layout="classic", specs_dir="specs", supported_sync_modes=["read-only"])

    def import_artifact(self, artifact_key: str, artifact_path: Path | dict[str, Any], project_bundle: Any, bridge_config: BridgeConfig | None = None) -> None:
        ...

    def export_artifact(self, artifact_key: str, artifact_data: Any, bridge_config: BridgeConfig | None = None) -> Path | dict[str, Any]:
        ...

    def generate_bridge_config(self, repo_path: Path) -> BridgeConfig:
        ...

    def load_change_tracking(self, bundle_dir: Path, bridge_config: BridgeConfig | None = None) -> ChangeTracking | None:
        ...

    def save_change_tracking(self, bundle_dir: Path, change_tracking: ChangeTracking, bridge_config: BridgeConfig | None = None) -> None:
        ...

    def load_change_proposal(self, bundle_dir: Path, change_name: str, bridge_config: BridgeConfig | None = None) -> ChangeProposal | None:
        ...

    def save_change_proposal(self, bundle_dir: Path, proposal: ChangeProposal, bridge_config: BridgeConfig | None = None) -> None:
        ...
```

## Code references

- Base interface: `src/specfact_cli/adapters/base.py`
- Capabilities model: `src/specfact_cli/models/capabilities.py`
- Adapter examples: `src/specfact_cli/adapters/openspec.py`, `src/specfact_cli/adapters/speckit.py`

## Error handling and logging

- Raise explicit exceptions for invalid artifact keys or unsupported operations.
- Use bridge logger patterns in command/service layers for non-fatal adapter issues.
- Keep adapter behavior deterministic and avoid silent data mutation.

## Related docs

- [Architecture Reference](../reference/architecture.md)
- [Bridge Registry](../reference/bridge-registry.md)
- [Creating Custom Bridges](creating-custom-bridges.md)
