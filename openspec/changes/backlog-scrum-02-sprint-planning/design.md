# Design: Sprint planning (capacity and commitment) support

## Capacity config and commitment aggregation

- **Config**: Sprint capacity config schema (e.g. YAML) with sprint identifier → capacity (story points). Store in `.specfact/sprint_capacity.yaml` or similar. Load from project; handle missing/invalid config without crash.
- **Commitment**: Sum BacklogItem.story_points for items where BacklogItem.sprint matches the requested sprint. Commitment is adapter-agnostic (derived from existing BacklogItem data).
- **Integration**: New subcommand under backlog group: `specfact backlog sprint-summary` (optional `--sprint <id>`). Output: sprint id, committed points, capacity (if configured), gap (over/under). No top-level `specfact sprint` command.

## Sequence (sprint summary)

```
User → specfact backlog sprint-summary [--sprint <id>]
  → CLI loads .specfact/sprint_capacity.yaml (if present)
  → CLI fetches backlog items (existing adapter) or uses cached list
  → Filter items by sprint (if --sprint given)
  → Sum story_points per sprint
  → For each sprint: compare sum to capacity (if config present)
  → Output: sprint, committed, capacity, gap (over/under)
```

## Contract enforcement

- Capacity loader and commitment aggregator shall have @icontract and @beartype where they are public APIs.
- Backlog command: additive only; default behavior unchanged.

## Fallback / offline

- Capacity config is read from local project; no network required for config load. Commitment uses backlog item data (from adapter/cache); offline if data already available.
