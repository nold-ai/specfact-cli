---
layout: default
title: Interface Contracts
permalink: /architecture/interface-contracts/
---

# SpecFact CLI Interface Contracts

## Command Registry contract

`src/specfact_cli/registry/registry.py` exposes a lazy command registry with:

- `register(name, loader, metadata)`
- `get_typer(name)`
- `list_commands()`
- `list_commands_for_help()`
- `get_metadata(name)`

## BridgeAdapter contract

`src/specfact_cli/adapters/base.py` defines required abstract methods:

- `detect(...)`
- `get_capabilities(...)`
- `import_artifact(...)`
- `export_artifact(...)`
- `generate_bridge_config(...)`
- `load_change_tracking(...)`
- `save_change_tracking(...)`
- `load_change_proposal(...)`
- `save_change_proposal(...)`

All public methods are contract-checked (`@icontract`) and runtime type-checked (`@beartype`).

## ToolCapabilities contract

`ToolCapabilities` in `src/specfact_cli/models/capabilities.py` communicates adapter runtime support:

- tool identity and layout
- detected specs path
- available sync modes
- external config/custom hook support flags

Consumers use this metadata to select sync behavior and capability-safe operations.
