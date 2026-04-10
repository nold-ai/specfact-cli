# Change: Implement Adapter Enhancement Recommendations

## Why

The architecture verification of the adapter bridge enhancement plan identified three critical gaps that need to be addressed to fully enable agile DevOps-driven workflow support:

1. **Bidirectional Backlog Sync**: Currently, GitHubAdapter only supports export (OpenSpec → GitHub Issues). Import capability (GitHub Issues → OpenSpec) is needed for complete bidirectional sync, enabling teams to manage backlogs in GitHub while keeping OpenSpec change proposals in sync. **Note**: GitHub is the first backlog adapter implementation; the architecture must support future backlog adapters (Azure DevOps/ADO, Jira, Linear, etc.) following the same patterns.

2. **Validation Integration Details**: The plan mentions SpecFact validation against change proposals but doesn't detail the integration mechanism. This needs to be documented and implemented to enable automatic validation status updates in change proposals.

3. **Integration Test Coverage**: While unit tests exist for adapters, integration tests for complete SDD workflows, cross-adapter sync scenarios, and backlog sync are missing. These are critical for ensuring the adapter architecture works end-to-end.

These enhancements will complete the adapter bridge architecture, enabling full agile DevOps-driven workflow support with proper backlog handling and validation integration.

## What Changes

- **NEW**: Add backlog adapter import capability (GitHub as first implementation)
  - Implement `import_artifact("github_issue", issue_data, project_bundle, bridge_config)` method in GitHubAdapter
  - Parse backlog item body/markdown to extract change proposal data (GitHub issues, future: ADO work items, Jira issues, Linear issues)
  - Map backlog item status/labels → OpenSpec change status (tool-agnostic mapping pattern)
  - Store backlog item metadata in `source_tracking` (tool-agnostic pattern)
  - **Design for extensibility**: Create reusable patterns that future backlog adapters (ADO, Jira, Linear) can follow

- **NEW**: Add validation integration documentation and implementation
  - Document how `specfact validate` command integrates with change proposals
  - Implement change proposal loading from OpenSpec during validation
  - Implement spec merging (current Spec-Kit specs + proposed OpenSpec changes)
  - Implement validation status updates in `FeatureDelta` models
  - Implement validation result reporting to backlog (GitHub Issues)

- **EXTEND**: Add integration test suite for adapter workflows
  - Add integration tests for complete SDD workflow (OpenSpec → Spec-Kit → SpecFact → GitHub)
  - Add integration tests for cross-adapter sync scenarios (OpenSpec ↔ Spec-Kit)
  - Add integration tests for bidirectional backlog sync (GitHub Issues ↔ OpenSpec)
  - Add integration tests for validation integration with change proposals

- **MODIFY**: Update GitHubAdapter to support status sync (pattern for future backlog adapters)
  - Add status synchronization (OpenSpec status ↔ GitHub issue labels)
  - Implement bidirectional status updates
  - **Design for extensibility**: Create status mapping patterns that future backlog adapters can reuse

## Impact

- **Affected specs**: `bridge-adapter` (adapter interface and backlog adapter implementations)
- **Affected code**:
  - `src/specfact_cli/adapters/github.py` (add import capability and status sync - first backlog adapter)
  - `src/specfact_cli/adapters/` (create reusable backlog adapter patterns for future: ADO, Jira, Linear)
  - `src/specfact_cli/commands/validate.py` (add change proposal integration)
  - `tests/integration/adapters/` (new integration test suite)
  - `docs/` (validation integration documentation, backlog adapter patterns)
- **Integration points**:
  - OpenSpec adapter (change proposal loading)
  - Spec-Kit adapter (spec merging)
  - SpecFact validation (contract enforcement)
  - Backlog adapters (GitHub first, future: ADO, Jira, Linear) - bidirectional sync

---

## Source Tracking

- **GitHub Issue**: #105
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/105>
- **Last Synced Status**: proposed
- **Sanitized**: true
<!-- content_hash: e628d8468669ebfc -->