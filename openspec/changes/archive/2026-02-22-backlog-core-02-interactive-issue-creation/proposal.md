# Change: Backlog Core — Interactive Issue Creation

## Why

After backlog-core-01, teams can analyze dependencies but still create new work items manually in GitHub/ADO. That causes hierarchy drift (wrong parent types), missing readiness fields, and inconsistent sprint/iteration assignment.

This change adds `specfact backlog add` as a guided creation workflow in the `backlog` command group, with provider-aware interactive UX and contract-safe adapter writes.

## What Changes

- **NEW**: `specfact backlog add` in `modules/backlog-core/src/backlog_core/commands/add.py` for interactive and non-interactive issue/work-item creation.
- **EXTEND**: Backlog adapter protocol with `create_issue(project_id: str, payload: dict) -> dict` and concrete implementations in GitHub and ADO adapters.
- **EXTEND**: GitHub parent assignment uses native issue relationship metadata (sidebar parent/sub-issue) via GraphQL sub-issue linking, not only body text conventions.
- **NEW**: Configurable creation hierarchy (`creation_hierarchy`) from template/config for parent-type validation (for example epic -> feature -> story -> task).
- **NEW**: Interactive creation UX for required fields including type/title/body, parent selection, sprint/iteration selection, and immediate create-progress feedback.
- **NEW**: Multiline body entry with non-markdown sentinel (default `::END::`) and configurable marker.
- **NEW**: Provider-agnostic draft fields for story-quality capture where applicable: acceptance criteria, priority, story points.
- **NEW**: Description format selection (`markdown` or `classic`) with provider mapping (`ADO multiline format` handling).
- **EXTEND**: GitHub custom mapping parity with ADO behavior: when `.specfact/templates/backlog/field_mappings/github_custom.yaml` exists and `--custom-config` is omitted, `backlog add` auto-loads it; otherwise it falls back to default mappings.
- **EXTEND**: Parent selection behavior:
  - ADO: hierarchy-aware parent candidates filtered by allowed parent types.
  - GitHub: select from available issues and normalized type mapping (including custom/epic labels when configured).
- **EXTEND**: `specfact backlog map-fields` to support a multi-provider field mapping workflow (ADO + GitHub), including auth checks, provider field discovery, mapping verification, and config persistence in `.specfact/backlog-config.yaml`. For GitHub, issue-type source-of-truth is repository issue types (`repository.issueTypes`), while ProjectV2 Type option mapping is optional enrichment when a suitable Type-like single-select field exists.

## Capabilities

- **backlog-core** (extended): `backlog add` interactive creation flow with hierarchy validation, readiness checks, and adapter-backed create operations.
- **backlog** (extended): Provider-aware `backlog init-config` scaffolding and `backlog map-fields` setup for mapping backlog fields across supported adapters.
- **backlog** (extended): Minimal default backlog-config scaffolding (without empty GitHub ProjectV2 placeholders); persist ProjectV2 mapping only when explicitly configured/discovered.

## Impact

- **Affected specs**: `openspec/changes/backlog-core-02-interactive-issue-creation/specs/backlog-add/spec.md`
- **Affected code**:
  - `modules/backlog-core/src/backlog_core/commands/add.py`
  - `modules/backlog-core/src/backlog_core/adapters/backlog_protocol.py`
  - `modules/backlog-core/src/backlog_core/graph/config_schema.py`
  - `modules/backlog-core/src/backlog_core/graph/builder.py`
  - `src/specfact_cli/adapters/backlog_base.py`
  - `src/specfact_cli/adapters/github.py`
  - `src/specfact_cli/adapters/ado.py`
  - `src/specfact_cli/modules/backlog/src/commands.py`
- **Affected tests**:
  - `modules/backlog-core/tests/unit/test_add_command.py`
  - `modules/backlog-core/tests/unit/test_adapter_create_issue.py`
  - `modules/backlog-core/tests/unit/test_backlog_protocol.py`
- **Documentation impact**:
  - `docs/guides/agile-scrum-workflows.md`
  - `docs/reference/commands.md`

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #173
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/173>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
- **Sanitized**: false
