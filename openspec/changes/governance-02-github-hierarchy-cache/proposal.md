# Governance: GitHub hierarchy cache (specfact-cli)

## Why

OpenSpec and agent workflows still have to query GitHub ad hoc to rediscover Epics, Features, and their parent links before creating or syncing change issues. That is slow, expensive, and error-prone, especially now that planning hierarchy matters in both `specfact-cli` and `specfact-cli-modules`.

## What Changes

- Add a deterministic repo-local hierarchy cache generator for GitHub Epic and Feature issues.
- Persist a repo-local markdown hierarchy cache at `.specfact/backlog/github_hierarchy_cache.md` (ignored; not committed) with issue number, title, brief summary, labels, and hierarchy relationships, plus a companion fingerprint/state file `.specfact/backlog/github_hierarchy_cache_state.json` so the sync can exit quickly when Epic and Feature metadata has not changed.
- Update governance instructions in `openspec/config.yaml` and `AGENTS.md` to consult the cached hierarchy first and rerun `python scripts/sync_github_hierarchy_cache.py` when fresh data is needed.
- Cover the script with tests so cache output and no-change behavior remain stable.

## Capabilities

### New Capabilities

- `github-hierarchy-cache`: Deterministic synchronization of GitHub Epic and Feature hierarchy metadata into a repo-local OpenSpec markdown cache for low-cost parent and planning lookups.

### Modified Capabilities

- `agile-feature-hierarchy`: Local governance workflows must be able to resolve current Epic and Feature planning metadata from the repo-local cache before performing manual GitHub lookups.

## Impact

- Affected code: new script and tests under `scripts/` and `tests/`, plus OpenSpec governance guidance in `openspec/config.yaml` and `AGENTS.md`.
- Affected workflow: OpenSpec change creation, GitHub issue creation/sync, and `CHANGE_ORDER.md` maintenance become cache-first instead of lookup-first.
- Cross-repo impact: a sibling change in `specfact-cli-modules` must implement the same pattern so both repos expose equivalent planning metadata locally.

## Source Tracking

- GitHub Issue: [#491](https://github.com/nold-ai/specfact-cli/issues/491)
- Parent Feature: [#486](https://github.com/nold-ai/specfact-cli/issues/486)
- Related Modules Change: `specfact-cli-modules/governance-03-github-hierarchy-cache`

## Code review note (SpecFact dogfood)

Icontract `@require` preconditions on `fetch_hierarchy_issues`, `render_cache_markdown`, and `sync_cache` intentionally use small, similarly shaped predicates. The code-review module may emit low-severity DRY / duplicate-shape hints for those helpers; that is accepted here because collapsing them would break icontract’s per-parameter argument binding (e.g. `**kwargs` predicates are not supported the same way).
