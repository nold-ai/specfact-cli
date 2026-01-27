# Change: Fix backlog refine filters, limits, and ADO rendering

## Why

Real-world usage in v0.26.5 shows backlog refinement is error-prone for ADO/GitHub workflows:

- No batch limit or graceful cancel; users must hard-interrupt the flow.
- ADO sprint filtering matches sprint name only and can select the wrong iteration (e.g., "Sprint 01" from 2023).
- ADO status and assignee filters are case-sensitive, leading to mismatched results.
- Assignee identity formats vary between ADO and GitHub and require adapter-specific normalization.
- ADO work item descriptions receive raw Markdown without proper format handling, producing misformatted bodies.

This change aligns refinement behavior with the backlog roadmap (2026-01-18) and makes filters, batching, and writeback safe and deterministic for production use.

## What Changes

- **MODIFY** `specfact backlog refine` to add a `--limit` cap for batch processing and a graceful cancel/skip flow in the refinement prompt (no repeated Ctrl+C/CTRL+Z).
- **MODIFY** ADO sprint filtering to prefer full iteration path matching, detect ambiguous sprint name matches, and avoid defaulting to earliest matching sprint.
- **MODIFY** ADO refinement defaults to the current active iteration when `--sprint` is omitted (resolve via team iterations API), with optional `--ado-team` override and clear error when no current iteration exists.
- **MODIFY** backlog filters to apply case-insensitive matching for state and assignee, with adapter-specific identity normalization (ADO displayName/uniqueName/mail; GitHub login or name with optional `@`, fallback to login).
- **MODIFY** ADO backlog update to render refined Markdown correctly (set `multilineFieldsFormat` to Markdown, fallback to HTML only when required) while preserving raw markdown for round-trip.
- **MODIFY** docs and AI prompt guidance to document limit/cancel behavior and adapter-specific filter formats.

## Impact

- **Affected specs**: `backlog-refinement`, `backlog-adapter`, `format-abstraction`
- **Affected code**:
  - `src/specfact_cli/commands/backlog_commands.py`
  - `src/specfact_cli/backlog/filters.py`
  - `src/specfact_cli/adapters/ado.py`
  - `src/specfact_cli/adapters/github.py`
  - `src/specfact_cli/backlog/formats/` (renderer/format handling)
  - Backlog refinement docs and AI prompt assets
- **Integration points**:
  - BacklogAdapter filtering semantics and identity normalization
  - ADO WIQL query and work item update format
  - CLI prompt flow for refinement

---
*OpenSpec Change Proposal: `fix-backlog-refine-filters-and-markdown`*

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #137
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/137>
- **Last Synced Status**: proposed
- **Sanitized**: true
