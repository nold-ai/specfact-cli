# Design: Add backlog add (interactive issue creation)

## Bridge adapter integration

- **Create method**: Extend `BacklogAdapterMixin` with abstract `create_issue(project_id: str, payload: dict) -> dict`. Payload is unified: type (epic|feature|story|task|bug|spike|custom), title, description, optional parent_id, optional sprint, optional custom fields. Adapter maps to provider: GitHub Issues API (POST /repos/{owner}/{repo}/issues) with title, body, labels for type; ADO Create Work Item API with work item type from template type_mapping and parent relation when parent_id present.
- **Adapter capability**: GitHub and ADO adapters implement create_issue; return dict with id, key (or number), url. Read-only or unsupported adapters may raise or return clear "not supported" for future extensibility.

## Sequence (add flow)

```text
User → specfact backlog add --type story --parent FEAT-123 --title "T" [--body "B"] [--check-dor]
  → CLI loads config & template (creation_hierarchy, type_mapping)
  → CLI fetches graph (fetch_all_issues, fetch_relationships) or uses cached graph
  → CLI validates: parent FEAT-123 exists, type Story allowed under parent type
  → Optional: DoR check on draft (reuse backlog refine DoR loader)
  → CLI builds unified payload (type, title, description, parent_id)
  → adapter.create_issue(project_id, payload) → provider API
  → CLI outputs created id, key, url
```

## Contract enforcement

- New public methods: `create_issue` on adapters, add-command entry point and validation helpers shall have @icontract and @beartype.
- Payload schema (unified) can be a Pydantic model for validation before passing to adapter.

## Creation hierarchy

- **Source**: Optional `creation_hierarchy` in template YAML or backlog_config (e.g. under .specfact/spec.yaml). Format: map child type to list of allowed parent types (e.g. story: [feature, epic], task: [story]).
- **Default**: When absent, derive from dependency_rules (PARENT_CHILD) and type_mapping if possible; otherwise allow no parent or any existing type and document behavior.
- **Validation**: Before create, resolve parent_id in graph; check parent's effective type is in allowed list for the new item's type.

## Fallback / offline

- Add command requires network for create. Graph load may use cached baseline if available (from add-backlog-dependency-analysis-and-commands); otherwise fetch. Failure (auth, rate limit) is reported; no silent swallow.

## Alignment with existing backlog commands

- Reuse DoR loading and rules from `specfact backlog refine --check-dor` when --check-dor is set. Reuse BacklogGraphBuilder and DependencyAnalyzer (from add-backlog-dependency-analysis-and-commands) when available for parent validation and cycle avoidance; if that change is not merged, minimal validation (e.g. parent exists via fetch_backlog_item) suffices for v1.
