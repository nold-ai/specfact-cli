# Design: Fix backlog refine filters and ADO markdown rendering

## Goals

- Provide deterministic filtering for ADO/GitHub (case-insensitive state/assignee, sprint path support).
- Allow users to cap batch size and exit refinement cleanly.
- Preserve Markdown fidelity when writing to ADO.

## Decisions

1. **Filter normalization**
   - Normalize state/assignee inputs via a shared helper (lowercase, trim, collapse whitespace).
   - GitHub assignee: strip leading `@`, match against login and display name (case-insensitive), fallback to login only.
   - ADO assignee: match against displayName, uniqueName, and mail (case-insensitive).

2. **Sprint/iteration matching (ADO)**
   - If `--sprint` contains `\` or `/`, treat it as a full iteration path and match against `item.iteration`.
   - If `--sprint` is name-only, match against `item.sprint` but detect duplicate iteration paths.
   - When duplicates exist, surface a clear error listing candidate iteration paths and require an explicit path.
   - If `--sprint` is omitted, resolve the current active iteration via the team iterations API (`$timeframe=current`).
   - Use `--ado-team` when provided; otherwise default to the project team name for iteration lookup.

3. **Batch control & cancellation**
   - Expose `--limit` on `specfact backlog refine` and pass it through to `_fetch_backlog_items`.
   - Add prompt sentinels:
     - `:skip` skips the current item.
     - `:quit` / `:abort` cancels the full run with a summary and no additional items processed.
   - Ensure writeback only happens when explicitly accepted.

4. **ADO description rendering**
   - When updating backlog items, set `/multilineFieldsFormat/System.Description` to `Markdown` (ADO supports Markdown in work item descriptions).
   - Fallback to Markdown → HTML conversion only if the API rejects Markdown (e.g., older on-premise servers).
   - Store format metadata in `provider_fields` (e.g., `description_format`, `description_markdown`) for round-trip safety.

## Non-Goals

- Changing core template detection logic or OpenSpec bundle generation.
- Introducing new backlog providers.
