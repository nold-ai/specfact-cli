## Context

`specfact-cli` already maintains GitHub planning hierarchy through issue labels, parent-child links, and `openspec/CHANGE_ORDER.md`, but contributors still discover that structure by hitting the GitHub API manually. The new requirement is to make hierarchy lookup deterministic, cheap, and local: a generated markdown file under ignored `.specfact/backlog/` becomes the first source for parent Feature and Epic resolution, and the sync command is rerun only when the hierarchy changed.

This is a cross-cutting governance change because it affects GitHub automation, OpenSpec operating rules, and agent instructions. The same pattern is needed in `specfact-cli-modules`, but each repo should own its own script, state file, and cache output so the result remains self-contained.

## Goals / Non-Goals

**Goals:**
- Generate a deterministic markdown cache of Epic and Feature issues for this repository.
- Include enough metadata for issue-parenting work without another GitHub lookup: issue number, title, short summary, labels, parent/child relationships, and issue URLs.
- Make the sync fast on no-op runs by using a small fingerprint/state check before regenerating markdown.
- Update repo guidance so contributors use the cache first and only rerun sync when needed.

**Non-Goals:**
- Replacing GitHub as the authoritative source of issue hierarchy.
- Caching every issue type or full issue bodies.
- Synchronizing User Story issues into the cache in this first version.
- Introducing a new external dependency beyond the existing `gh` CLI.

## Decisions

### Use `gh api graphql` as the sole upstream source
The script will query GitHub through `gh api graphql` so it can access issue type, labels, relationships, and brief body content in one supported path. This avoids scraping markdown or depending on REST endpoints that do not expose hierarchy fields consistently.

Alternative considered:
- `gh issue list/view` JSON loops: simpler, but requires many calls and awkward relationship reconstruction.

### Split the sync into a lightweight fingerprint pass and a full render pass
The script will first fetch only the Epic and Feature issue identity set plus timestamps/relationship fingerprints, hash that data, and compare it with a local state file. If the fingerprint matches, the script exits successfully without rewriting markdown. If it differs, the script performs a fuller metadata query and regenerates the cache.

Alternative considered:
- Always regenerate markdown: deterministic but wastes GitHub calls and makes local workflows slower.

### Store human-readable cache plus machine-readable state under ignored `.specfact/backlog`
The canonical human-facing output will be `.specfact/backlog/github_hierarchy_cache.md`. A companion state file, `.specfact/backlog/github_hierarchy_cache_state.json`, will hold the last fingerprint and generator metadata. Both files stay local and ignored by Git so the cache can be recreated freely without creating repository drift.

Alternative considered:
- State embedded in markdown comments: workable, but couples machine state to user-facing output and complicates deterministic rendering.

### Render by deterministic section and sort order
The markdown will use fixed sections for Epics and Features, with issues sorted stably by type, then issue number. Relationship lists and labels will also be sorted deterministically so reruns only change the file when source metadata actually changes.

Alternative considered:
- Preserve GitHub API order: easier, but can drift between runs and create noisy diffs.

### Keep instruction updates in repo-local governance files
The change will update `openspec/config.yaml` and `AGENTS.md` in this repo so the workflow explicitly says: consult the cache first, regenerate it when fresh planning metadata is needed, and avoid ad hoc GitHub lookups unless the cache is stale or missing.

Alternative considered:
- Document the behavior only in the script help text: insufficient because agents and OpenSpec flows read governance files first.

## Risks / Trade-offs

- [GitHub schema drift] → Keep GraphQL fields minimal and cover parsing/rendering with tests that pin expected shapes.
- [Cache becomes stale if users forget to rerun sync] → Update `AGENTS.md` and `openspec/config.yaml` to make rerun conditions explicit and keep the script fast enough to run routinely.
- [Relationship data differs between repos or issue states] → Normalize missing parents/children to explicit empty values and show unresolved relationships clearly in markdown.
- [No-op fingerprint misses relevant content changes] → Include type, number, title, updated timestamp, labels, and parent identity in the fingerprint rather than only issue count.

## Migration Plan

1. Add the sync script, state handling, markdown renderer, and tests.
2. Generate the initial cache file under ignored `.specfact/backlog/`.
3. Update `openspec/config.yaml` and `AGENTS.md` to use the cache-first workflow.
4. Run validation and repository tests, then sync the paired change issue metadata.

Rollback is straightforward: remove the script, state file, cache file, and governance references if the workflow proves noisy or unreliable.

## Open Questions

- Whether a later follow-up should also cache User Story issues once the Feature/Epic workflow is stable.
- Whether the fingerprint pass should use a dedicated smaller GraphQL query or reuse one richer query and short-circuit before rendering if unchanged.
