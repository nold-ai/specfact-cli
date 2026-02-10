# Change: Backlog Core — Interactive Issue Creation

## Why


After implementing backlog adapters and dependency analysis (backlog-core-01), teams can analyze and sync backlog items but cannot create new issues from the CLI with proper scoping, hierarchy alignment, and Definition of Ready (DoR) checks. Without a dedicated add flow, users create issues manually in GitHub/ADO and risk orphaned or misaligned items. Adding `specfact backlog add` enables interactive creation with AI copilot assistance: draft → review → enhance → validate (graph, DoR) → create, so new issues fit the existing backlog structure and value chain.

This change extends the **`backlog-core` module** (backlog-core-01) with the `backlog add` command.

## Module Package Structure

This change adds to the existing `modules/backlog-core/` module:

```
modules/backlog-core/
  module-package.yaml          # updated: add 'backlog add' to commands list
  src/backlog_core/
    commands/
      add.py                   # specfact backlog add (interactive issue creation)
    adapters/
      backlog_protocol.py      # extended: add create_issue() to BacklogGraphProtocol
```

**`module-package.yaml` update:** Add `backlog add` to commands list. No new module; this is a capability increment to backlog-core.

## Module Package Structure

This change adds to the existing `modules/backlog-core/` module:

```
modules/backlog-core/
  module-package.yaml          # updated: add 'backlog add' to commands list
  src/backlog_core/
    commands/
      add.py                   # specfact backlog add (interactive issue creation)
    adapters/
      backlog_protocol.py      # extended: add create_issue() to BacklogGraphProtocol
```

**`module-package.yaml` update:** Add `backlog add` to commands list. No new module; this is a capability increment to backlog-core.

## What Changes


- **NEW**: Add CLI command `specfact backlog add` in `modules/backlog-core/src/backlog_core/commands/add.py` for interactive creation of backlog issues (epic, feature, story, task, bug, spike) with optional parent, title, body, DoR validation, and optional `--sprint` to assign new issue to sprint (when provider supports it).
- **NEW**: Support multiple backlog levels (epic, feature, story, task, bug, spike, custom) with configurable creation hierarchy (allowed parent types per child type) via template or backlog_config; default derived from existing type_mapping and dependency_rules in `ado_scrum.yaml` / `github_projects.yaml` templates.
- **EXTEND** (arch-05 bridge registry): Extend `BacklogGraphProtocol` in `modules/backlog-core/src/backlog_core/adapters/backlog_protocol.py` with `create_issue(project_id: str, payload: dict) -> dict` returning created item (id, key, url). Adapter modules (github-adapter, ado-adapter) implement this method and register updated protocol conformance via bridge registry.
- **NEW**: Add flow: load graph (BacklogGraphBuilder, fetch_all_issues, fetch_relationships from backlog-core-01), resolve type and parent from template/hierarchy, validate parent exists and allowed type, optional DoR check (**use policy-engine-01 when available**), map draft to provider payload, call adapter `create_issue`, output created id/key/url.
- **EXTEND** (E5): Provide draft patch preview before create (integrate with patch-mode-01 when available) so user can review proposed issue body/fields before creating.
- **EXTEND** (E5): When linking to existing issues (e.g. parent, blocks), support fuzzy match + user confirmation; no silent link (aligns with bundle-mapper-01).
- **EXTEND**: Template or backlog_config with optional `creation_hierarchy` (allowed parent types per child type) so Scrum/SAFe/Kanban and custom hierarchies work without code changes.

## Capabilities
- **backlog-core** (extended): `backlog add` — interactive creation of backlog issues with type/parent selection, draft validation (graph and DoR), and create via adapter protocol; multi-level support with configurable hierarchy.

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #173
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/173>
- **Last Synced Status**: proposed
- **Sanitized**: false
