# Change: Add backlog add (interactive issue creation)

## Why

After implementing backlog adapters and dependency analysis (add-backlog-dependency-analysis-and-commands), teams can analyze and sync backlog items but cannot create new issues from the CLI with proper scoping, hierarchy alignment, and Definition of Ready (DoR) checks. Without a dedicated add flow, users create issues manually in GitHub/ADO and risk orphaned or misaligned items. Adding `specfact backlog add` enables interactive creation with AI copilot assistance: draft → review → enhance → validate (graph, DoR) → create, so new issues fit the existing backlog structure and value chain.

## What Changes

- **NEW**: Add CLI command `specfact backlog add` (or alias `specfact backlog add-issue`) for interactive creation of backlog issues (epic, feature, story, task, bug, spike) with optional parent, title, body, DoR validation, and optional `--sprint` to assign new issue to sprint (when provider supports it).
- **NEW**: Support multiple backlog levels (epic, feature, story, task, bug, spike, custom) with configurable creation hierarchy (allowed parent types per child type) via template or backlog_config; default derived from existing type_mapping and dependency_rules.
- **NEW**: Extend `BacklogAdapterMixin` with abstract method `create_issue(project_id: str, payload: dict) -> dict` returning created item (id, key, url); implement in GitHub and ADO adapters with unified payload shape and provider-specific mapping.
- **NEW**: Add spec delta and implementation for add flow: load graph (BacklogGraphBuilder, fetch_all_issues, fetch_relationships), resolve type and parent from template/hierarchy, validate parent exists and allowed type, optional DoR check (reuse backlog refine DoR; **use Policy Engine #176 for DoR enforcement when available**), map draft to provider payload, call adapter create_issue, output created id/key/url.
- **EXTEND**: **E5**: Provide draft patch preview before create (integrate with patch-mode-preview-apply #177 when available) so user can review proposed issue body/fields before creating.
- **EXTEND**: **E5**: When linking to existing issues (e.g. parent, blocks), support fuzzy match + user confirmation; no silent link (aligns with bundle mapping and future linking).
- **EXTEND**: Template or backlog_config with optional creation_hierarchy (allowed parent types per child type) so Scrum/SAFe/Kanban and custom hierarchies work without code changes.
- **EXTEND**: Documentation (agile-scrum-workflows, backlog-refinement) for backlog add workflow, interactive creation, DoR, and slash-prompt usage.

## Capabilities

- **backlog-add**: Interactive creation of backlog issues with type/parent selection, draft validation (graph and DoR), and create via adapter; multi-level support (epic, feature, story, task, bug, spike, custom) with configurable hierarchy.

## Impact

- **Affected specs**: New `openspec/changes/backlog-02-add-backlog-add-interactive-issue-creation/specs/backlog-add/spec.md` (Given/When/Then for add flow, hierarchy, create via adapter).
- **Affected code**: `src/specfact_cli/adapters/backlog_base.py` (abstract create_issue), `github.py` and `ado.py` (implement create_issue); `src/specfact_cli/commands/backlog_commands.py` or backlog command module (add `specfact backlog add` subcommand); optional creation_hierarchy loader and validation using BacklogGraphBuilder and DependencyAnalyzer (from add-backlog-dependency-analysis-and-commands when available).
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md, backlog-refinement or backlog guide for backlog add, interactive creation, DoR, slash prompt.
- **Integration points**: BacklogGraphBuilder, DependencyAnalyzer, fetch_all_issues, fetch_relationships (add-backlog-dependency-analysis-and-commands); DoR from backlog-refinement; **Policy Engine (#176) for DoR enforcement**; **patch-mode-preview-apply (#177) for draft patch preview before create**; templates and backlog_config.
- **Backward compatibility**: Additive only; new command and adapter method; existing refine/sync/analyze-deps unchanged. Depends on add-backlog-dependency-analysis-and-commands for graph/templates; can be implemented with minimal graph usage (e.g. fetch + validate parent) if that change is not yet merged.

## Source Tracking

- **GitHub Issue**: #173
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/173>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
