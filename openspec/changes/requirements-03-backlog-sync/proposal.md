# Change: Requirements ↔ Backlog Bidirectional Sync

## Why

When backlog items change, requirements aren't updated. When requirements change, backlog items aren't updated. The two drift apart silently, creating a traceability gap that grows with every sprint. Teams discover the drift only during audits or after building the wrong thing. A bidirectional sync between backlog items and `.specfact/requirements/` using the sync kernel makes requirements and backlog items a single source of truth — with drift detection as the safety net.

## Ownership Alignment (2026-04-08)

- Repository assignment: `split/rescope`
- Core-owned scope retained here: shared sync contracts, adapter semantics, and spec-kit duplicate-creation safeguards.
- Bundle-owned follow-up required: the user-facing requirements/backlog sync workflow below spans project and backlog bundle behavior and cannot remain a flat `specfact requirements ...` command family in core.
- Target modules-repo follow-up issue: [#166](https://github.com/nold-ai/specfact-cli-modules/issues/166) in `nold-ai/specfact-cli-modules`
- Implementation MUST NOT proceed from this proposal as a single-repo change until the bundle-owned follow-up changes are split out explicitly.

## What Changes

- **NEW**: `specfact requirements sync --from-backlog <adapter> --project <org/repo> --preview` — pull structured requirements from backlog AC text, update `.specfact/requirements/`
- **NEW**: `specfact requirements sync --to-backlog <adapter> --project <org/repo> --preview` — push requirement-derived fields back to backlog items (missing AC, business value gaps, architectural constraints)
- **NEW**: `specfact requirements drift --from-backlog <adapter> --project <org/repo>` — detect divergence between local requirements and backlog items without making changes
- **NEW**: Sync operations use the sync kernel (sync-01) for session management, conflict detection, and patch preview
- **NEW**: Backlog adapter extension: adapters provide `extract_requirements_fields()` and `update_requirements_fields()` methods for bidirectional sync
- **EXTEND**: Requirements module (requirements-02) extended with sync commands
- **DESIGN DECISION**: v1 starts with pull-first (backlog → requirements) as primary direction; push (requirements → backlog) is preview-only and requires explicit `--write` confirmation via patch-mode
- **EXTEND**: Spec-Kit backlog extension awareness — before creating issues during push (requirements → backlog), the sync SHALL query `ToolCapabilities.extension_commands` (from speckit-02) to detect active spec-kit backlog extensions (Jira, ADO, Linear, GitHub Projects, Trello). When a spec-kit backlog extension is active, the sync SHALL scan spec-kit feature `tasks.md` files for existing issue references (e.g., `PROJ-123`, `AB#456`) and import them as pre-existing mappings. Issue creation is skipped for tasks that already have spec-kit extension mappings, preventing duplicate issues. This detection is implemented in `speckit-03-change-proposal-bridge` (specfact-cli-modules) and consumed here via the adapter interface.

## Capabilities

### New Capabilities

- `requirements-backlog-sync`: Bidirectional sync between `.specfact/requirements/` and backlog items (GitHub, ADO, Jira, Linear) via sync kernel. Includes pull (extract from backlog), push (update backlog), and drift detection.

### Modified Capabilities

- `backlog-adapter`: Extended with requirements field extraction and update methods for bidirectional sync; extended with spec-kit backlog extension issue mapping import
- `requirements-module`: Extended with sync and drift commands; extended with spec-kit duplicate issue prevention

---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #244
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/244>
- **Paired Modules Runtime Issue**: nold-ai/specfact-cli-modules#166
- **Paired Modules Scope**: requirements-backlog sync runtime
- **Last Synced Status**: proposed
- **Sanitized**: false
