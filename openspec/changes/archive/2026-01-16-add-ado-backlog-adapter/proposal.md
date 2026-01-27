# Change: Add Azure DevOps backlog adapter

## Why

Azure DevOps work items are a common enterprise backlog system and the bridge adapter architecture already defines a backlog adapter pattern with GitHub as the first implementation. Without an ADO adapter, OpenSpec change proposals cannot participate in ADO-centered workflows or bidirectional backlog sync. Adding an ADO backlog adapter completes the intended extensibility and allows teams to keep OpenSpec proposals aligned with ADO work items using the same contract-first patterns.

## What Changes

- **NEW**: Implement an Azure DevOps backlog adapter that follows BacklogAdapterMixin patterns for import/export, status mapping, and source_tracking metadata.
- **NEW**: Add an ADO bridge config preset and adapter registration so `specfact sync bridge --adapter ado` can be used.
- **NEW**: Integrate ADO adapter into `specfact sync bridge --mode export-only` workflow for exporting OpenSpec change proposals to ADO work items, matching GitHub adapter integration pattern.
- **EXTEND**: Wire ADO-specific configuration via explicit CLI/env properties (org, project, base URL, PAT, work item type) with secure handling (no secrets in BridgeConfig).
- **EXTEND**: Derive default work item type from Scrum/Kanban/Agile process templates with an explicit override for custom workflows.
- **EXTEND**: Add selective backlog import into project bundles (explicit IDs or interactive selection) with non-interactive input support for AI copilot flows; no automatic bulk import.
- **EXTEND**: Add bundle-targeted backlog sync (CLI selects specific bundle or project context) so imports/exports are scoped to the chosen SpecFact bundle.
- **EXTEND**: Persist lossless backlog content in the selected project bundle (full issue body + metadata) to enable exact round-trip export without truncation or section drift.
- **EXTEND**: Enable cross-adapter exports from a stored bundle (GitHub ↔ ADO ↔ other backlog adapters) with 1:1 content fidelity and no duplicate sections.
- **EXTEND**: Add tests and documentation to mark ADO adapter as available and to codify its usage and mappings.
- **EXTEND**: Support markdown format conversion for ADO work items:
  - Set `multilineFieldsFormat` to &quot;Markdown&quot; when creating/updating work items (ADO supports Markdown as of July 2025)
  - Convert HTML to markdown when importing work items that were created in HTML format
  - Internally use markdown format for all adapter I/O, converting to/from adapter-specific formats as needed
- **EXTEND**: Enhanced source_tracking matching logic to prevent duplicate work items:
  - Three-level matching strategy: exact `source_repo` match → org+type match (for ADO) → org-only match (for ADO)
  - **CRITICAL**: Handles ADO URL GUIDs in both single dict and list formats:
    - ADO URLs contain GUIDs instead of project names (e.g., `dominikusnold/69b5d0c2-2400-470d-b937-b5205503a679`)
    - Matching logic works for both backward-compatible single dict format and multi-repo list format
    - Matches by organization when project names differ or URLs contain GUIDs
    - Prevents duplicate work items even when `source_repo` doesn't match exactly (e.g., GUID vs project name)
  - Stores `source_repo` in hidden comments for single entries to ensure proper matching on subsequent syncs
  - Updates existing entries instead of creating duplicates when org matches (handles project name changes)
  - Supports work item body updates via `change_proposal_update` artifact key for `--update-existing` flag
  - **Duplicate prevention**: If `source_tracking` entry exists for target repo but `source_id` is missing, skip creation and warn user (prevents duplicates from corrupted or partially-saved source_tracking)

## Impact

- **Affected specs**: `devops-sync`, `bridge-adapter`
- **Affected code**: `src/specfact_cli/adapters/ado.py`, `src/specfact_cli/sync/bridge_sync.py`, `src/specfact_cli/commands/sync.py`, `src/specfact_cli/models/bridge.py`
- **Integration points**: Adapter registry (`AdapterRegistry`), backlog adapter import/export flows, bundle-scoped storage for lossless cross-adapter export

---
*OpenSpec Change Proposal: `add-ado-backlog-adapter`*

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issues**: #110, #112
- **Issue URLs**:
  - <https://github.com/nold-ai/specfact-cli/issues/110>
  - <https://github.com/nold-ai/specfact-cli/issues/112>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
