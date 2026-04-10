# Change: Implement backlog refine --import-from-tmp

## Why

The `specfact backlog refine` command supports `--export-to-tmp` to export items to a markdown file for copilot processing and documents `--import-from-tmp` / `--tmp-file` to re-import refined content. When users run with `--import-from-tmp`, the CLI only checks that the file exists and then prints "Import functionality pending implementation" and exits. This leaves the export/import workflow unusable and contradicts the documented behavior. Implementing the import path completes the round-trip: export → edit with copilot → import with --write, so teams can refine backlog items in bulk via their IDE without interactive prompts.

## What Changes

- **NEW**: Parser for the refined export markdown format (same structure as export: `## Item N:`, **ID**, **Body** in ```markdown ...```, **Acceptance Criteria**, optional title/metrics). Parser returns a list of parsed blocks keyed by item ID for matching against fetched items.
- **NEW**: Import branch in `specfact backlog refine`: when `--import-from-tmp` is set and the file exists, read and parse the file, match parsed blocks to currently fetched items by ID, update each matched `BacklogItem`'s `body_markdown` and `acceptance_criteria` (and optionally title/metrics), then call `adapter.update_backlog_item(item, update_fields=[...])` when `--write` is set. Without `--write`, show a preview (e.g. "Would update N items") and do not call the adapter.
- **EXTEND**: Reuse existing refine flow: same adapter/fetch as export so `items` is in scope; reuse `_build_adapter_kwargs` and `adapter_registry.get_adapter` for write-back; reuse the same `update_fields` logic as interactive refine (title, body_markdown, acceptance_criteria, story_points, business_value, priority).
- **NOTE**: Default import path remains `...-refined.md`; users are expected to pass `--tmp-file` to point to the file they edited (same path as export or a copy). No change to export path or naming.

## Capabilities

- **backlog-refinement**: ADDED requirement for import-from-tmp (parse refined export format, match by ID, update items via adapter with --write).

## Impact

- **Affected specs**: backlog-refinement (ADDED scenario for import-from-tmp).
- **Affected code**: `src/specfact_cli/commands/backlog_commands.py` (import branch implementation); optionally `src/specfact_cli/backlog/refine_export_parser.py` (parser helper).
- **Integration points**: BacklogAdapter.update_backlog_item (existing); _fetch_backlog_items,_build_adapter_kwargs (existing).

## Source Tracking

- **GitHub Issue**: #155
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/155>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: implemented
