## Context

- ADO backlog adapter builds on the GitHub adapter and BacklogAdapterMixin patterns.
- The adapter must implement BridgeAdapter, integrate with AdapterRegistry, and use BridgeSync devops export/import flows.
- ADO REST API integration and PAT-based authentication are required.

## Goals / Non-Goals

- Goals:
  - Provide bidirectional and export-only sync between OpenSpec change proposals and ADO work items.
  - Follow BacklogAdapterMixin patterns for status mapping, metadata extraction, and conflict resolution.
  - Provide configuration for organization, project, base URL, PAT, and work item type.
  - Support selective backlog import into project bundles (explicit IDs or interactive selection), including non-interactive inputs for AI copilot flows.
  - Preserve source_tracking metadata and idempotency.
- Non-Goals:
  - Advanced ADO features (area/iteration path planning, custom templates).
  - Non-REST clients or bespoke SDKs.
  - Changing existing GitHub adapter behavior.

## Decisions

- Adapter key is "ado" with artifact key `ado_work_item`.
- Authentication uses PAT from env/CLI; no secrets stored in BridgeConfig.
- Work item mapping uses `System.Title`, `System.Description`, and `System.State` as primary fields.
- Default work item type is derived from ADO process templates (Scrum/Kanban/Agile) following ADO docs, with explicit override when configured.
- Configuration uses explicit ADO CLI/env properties (`--ado-org`, `--ado-project`, `--ado-base-url`, `--ado-token`, `--ado-work-item-type`).
- Backlog import defaults to no-op unless specific items are selected; support explicit IDs and interactive selection, plus non-interactive inputs for AI copilot flows.
- Idempotency relies on source_tracking metadata (work item id, URL, content hash).
- Scope: Azure DevOps Services (cloud) only; Azure DevOps Server (on-prem) is out of scope.

## Risks / Trade-offs

- ADO state names vary by process template; mapping may require overrides.
- ADO cloud vs server base URLs differ; adapter must allow custom base URL.

## Migration Plan

- Add ADO adapter and config presets alongside existing adapters.
- Update docs and tests; no breaking changes to existing CLI defaults.

## Open Questions

- None.
