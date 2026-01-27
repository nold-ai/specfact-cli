## 1. Git Workflow Setup

- [x] 1.1 Create git branch `feature/add-ado-backlog-adapter` from `dev` branch
  - [x] 1.1.1 Ensure we're on dev and up to date: `git checkout dev && git pull origin dev`
  - [x] 1.1.2 Create branch with issue link (if issue exists): `gh issue develop <issue-number> --repo nold-ai/specfact-cli --name feature/add-ado-backlog-adapter --checkout`
  - [x] 1.1.3 Or create branch without issue link: `git checkout -b feature/add-ado-backlog-adapter`
  - [x] 1.1.4 Verify branch was created: `git branch --show-current`

## 2. Implement ADO backlog adapter

- [x] 2.1 Add `AdoAdapter` class implementing BridgeAdapter and BacklogAdapterMixin
  - [x] 2.1.1 Create `src/specfact_cli/adapters/ado.py` with constructor and required methods
  - [x] 2.1.2 Implement status mapping (ADO state <-> OpenSpec status) using backlog adapter patterns
  - [x] 2.1.3 Implement change proposal parsing from work item fields (title, description, state)
  - [x] 2.1.4 Implement import/export for `ado_work_item`, `change_proposal`, `change_status` (export-only + bidirectional) with idempotency
  - [x] 2.1.5 Implement work item type derivation from Scrum/Kanban/Agile process templates with override
  - [x] 2.1.6 Store ADO metadata in `source_tracking` (id, url, state, org, project, work item type)
  - [x] 2.1.6.1 Implement `_update_work_item_body()` method for updating work item descriptions
  - [x] 2.1.6.2 Add support for `change_proposal_update` artifact key in `export_artifact()`
  - [x] 2.1.6.3 Set `multilineFieldsFormat` to "Markdown" when creating/updating work items
  - [x] 2.1.6.4 Add `_html_to_markdown()` utility for converting HTML to markdown when importing
  - [x] 2.1.7 Respect `bridge_config.external_base_path` for cross-repo OpenSpec operations
  - [x] 2.1.8 Add `@beartype` and `@icontract` decorators and docstrings
  - [x] 2.1.9 Raise `ValueError` for malformed inputs and `NotImplementedError` for unsupported artifacts

- [x] 2.2 Add ADO bridge config preset and adapter registration
  - [x] 2.2.1 Add `BridgeConfig.preset_ado()` with API artifact mappings for work items
  - [x] 2.2.2 Register ADO adapter in `src/specfact_cli/adapters/__init__.py`
  - [x] 2.2.3 Ensure AdapterRegistry lists "ado" and AdapterType.ADO is used consistently

## 3. CLI and BridgeSync integration

- [x] 3.1 Add ADO configuration inputs to sync command
  - [x] 3.1.1 Add explicit ADO flags (`--ado-org`, `--ado-project`, `--ado-base-url`, `--ado-token`, `--ado-work-item-type`)
  - [x] 3.1.2 Wire org/project/base_url/token/work_item_type and process template defaults into adapter initialization
  - [x] 3.1.3 Update help text to mark ADO as available
  - [x] 3.1.4 Integrate ADO adapter into `specfact sync bridge --mode export-only` workflow (same pattern as GitHub)
  - [x] 3.1.5 Ensure source_tracking correctly stores `work_item_id` and `work_item_url` (not `issue_number`/`issue_url`)

- [x] 3.2 Update BridgeSync DevOps export/import to pass ADO config
  - [x] 3.2.1 Ensure export_change_proposals_to_devops passes ADO-specific kwargs
  - [x] 3.2.2 Ensure bidirectional sync uses `ado_work_item` import path and status sync
  - [x] 3.2.3 Enhance source_tracking matching logic to prevent duplicate work items (three-level matching for ADO)
  - [x] 3.2.3.1 **CRITICAL FIX**: Add ADO GUID matching logic to single dict format (backward compatibility) - ensures duplicate prevention works for both single dict and list formats
  - [x] 3.2.3.2 Verify duplicate prevention triggers when `source_tracking` entry exists but `source_id` is missing (prevents duplicates from corrupted entries)
  - [x] 3.2.4 Add support for `change_proposal_update` artifact key in ADO adapter for work item body updates
  - [x] 3.2.5 Store `source_repo` in hidden comments for single entries to ensure proper matching
  - [x] 3.2.6 Update `target_repo` derivation to use `ado_org/ado_project` for ADO adapter

- [x] 3.3 Add selective backlog import into project bundles
  - [x] 3.3.1 Require explicit backlog item selection (IDs/URLs) or interactive selection; default is no import
  - [x] 3.3.2 Support non-interactive inputs for AI copilot flows (e.g., `--backlog-ids` or input file)
  - [x] 3.3.3 Surface selection summaries in CLI output for auditability
  - [x] 3.3.4 Add bundle selection (explicit bundle name or inferred from project context) to scope import/export
  - [x] 3.3.5 Persist lossless backlog content in the selected project bundle (full issue body + metadata)

- [x] 3.4 Cross-adapter backlog export from stored bundles
  - [x] 3.4.1 Export stored bundle issues 1:1 to any backlog adapter (GitHub ↔ ADO ↔ others)
  - [x] 3.4.2 Ensure no duplicate sections or content drift on round-trip export
  - [x] 3.4.3 Support minimal, few-step CLI workflow (PAT/env configured) without scripts

## 4. Tests

- [x] 4.1 Add unit tests for ADO adapter
  - [x] 4.1.1 Status mapping (ADO state <-> OpenSpec status)
  - [x] 4.1.2 Work item parsing and error handling
  - [x] 4.1.3 Import/export behavior and source_tracking metadata
  - [x] 4.1.4 Work item type derivation from process templates and override handling

- [x] 4.2 Add integration tests for ADO backlog sync
  - [x] 4.2.1 Export change proposals to ADO (mocked API)
  - [x] 4.2.2 Import ADO work items to OpenSpec proposals
  - [x] 4.2.3 Bidirectional status sync and conflict resolution
  - [x] 4.2.4 Export-only mode with default work item type
  - [x] 4.2.5 Work item body updates with `change_proposal_update` artifact key
  - [x] 4.2.6 Source tracking matching logic (three-level matching for ADO)

- [x] 4.3 Add multi-adapter backlog round-trip test (GitHub ↔ OpenSpec ↔ ADO)
  - [x] 4.3.1 Validate lossless content export and no duplicate sections
  - [x] 4.3.2 Cover bundle-scoped export/update flow (`tests/integration/sync/test_multi_adapter_backlog_sync.py`)

## 5. Documentation

- [x] 5.1 Update backlog adapter docs to include ADO usage, mappings, and configuration flags
- [x] 5.2 Update devops adapter integration guide to mark ADO as available and document defaults
- [x] 5.3 Update commands reference and CLI help examples for `--adapter ado`
- [x] 5.4 Add a "Beyond export/update" capabilities section (import, status sync, validation reporting, progress notes) in:
  - `docs/guides/devops-adapter-integration.md`
  - `docs/reference/commands.md`
  - Note: This is an optional enhancement - core functionality is documented
- [x] 5.5 Update CHANGELOG.md

## 6. Code Quality and Contract Validation

- [x] 6.1 Run `hatch run format`
- [x] 6.2 Run `hatch run lint` (0 errors, warnings only - acceptable)
- [x] 6.3 Run `hatch run type-check`
- [x] 6.4 Run `hatch run contract-test` (331 tests passed)

## 7. Testing and Validation

- [x] 7.1 Run `hatch run smart-test`
- [x] 7.2 Run `hatch test --cover -v` (1924+ passed, all ADO tests passing - timeout issues fixed)

## 8. OpenSpec Validation

- [x] 8.1 Run `openspec validate add-ado-backlog-adapter --strict` (Validation passed)

## 9. Pull Request

- [x] 9.1 Create Pull Request from `feature/add-ado-backlog-adapter` to `dev` (specfact-cli)
  - [x] 9.1.1 Ensure all changes are committed: `git add .`
  - [x] 9.1.2 Commit with conventional message: `feat: add ado backlog adapter`
  - [x] 9.1.3 Push to remote: `git push origin feature/add-ado-backlog-adapter`
  - [x] 9.1.4 Create PR (use repository template)
  
**PR Created**: <https://github.com/nold-ai/specfact-cli/pull/113>
