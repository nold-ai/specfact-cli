# Change: Requirements ↔ Backlog Bidirectional Sync

## Why




When backlog items change, requirements aren't updated. When requirements change, backlog items aren't updated. The two drift apart silently, creating a traceability gap that grows with every sprint. Teams discover the drift only during audits or after building the wrong thing. A bidirectional sync between backlog items and `.specfact/requirements/` using the sync kernel makes requirements and backlog items a single source of truth — with drift detection as the safety net.

## What Changes




- **NEW**: `specfact requirements sync --from-backlog <adapter> --project <org/repo> --preview` — pull structured requirements from backlog AC text, update `.specfact/requirements/`
- **NEW**: `specfact requirements sync --to-backlog <adapter> --project <org/repo> --preview` — push requirement-derived fields back to backlog items (missing AC, business value gaps, architectural constraints)
- **NEW**: `specfact requirements drift --from-backlog <adapter> --project <org/repo>` — detect divergence between local requirements and backlog items without making changes
- **NEW**: Sync operations use the sync kernel (sync-01) for session management, conflict detection, and patch preview
- **NEW**: Backlog adapter extension: adapters provide `extract_requirements_fields()` and `update_requirements_fields()` methods for bidirectional sync
- **EXTEND**: Requirements module (requirements-02) extended with sync commands
- **DESIGN DECISION**: v1 starts with pull-first (backlog → requirements) as primary direction; push (requirements → backlog) is preview-only and requires explicit `--write` confirmation via patch-mode

## Capabilities
### New Capabilities

- `requirements-backlog-sync`: Bidirectional sync between `.specfact/requirements/` and backlog items (GitHub, ADO, Jira, Linear) via sync kernel. Includes pull (extract from backlog), push (update backlog), and drift detection.

### Modified Capabilities

- `backlog-adapter`: Extended with requirements field extraction and update methods for bidirectional sync
- `requirements-module`: Extended with sync and drift commands


---

## Source Tracking

<!-- source_repo: nold-ai/specfact-cli -->
- **GitHub Issue**: #244
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/244>
- **Last Synced Status**: proposed
- **Sanitized**: false
<!-- content_hash: 20fe63d460a3ab84 -->