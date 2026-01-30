# Change: Daily standup and progress support

## Why

Bridge comments and sync already support exporting/updating change proposals and issues. For daily standup there is no structured "standup" view that aggregates my items, recent activity, and blockers; progress/standup notes are not first-class (e.g. yesterday/today/blockers format) that could be pushed to issue comments. Teams duplicate standup info in tools; SpecFact can surface progress from OpenSpec/bridge and optionally publish to GitHub/ADO so standup updates are visible where the team works.

## What Changes

- **NEW**: Add a lightweight standup/progress view under the backlog command group: list my change proposals or backlog items (by assignee or filter), with last-updated and status; optional one-line summary for yesterday/today/blockers from proposal or linked issue body. Expose as `specfact backlog daily` (no top-level `specfact standup`).
- **NEW**: Optional mode to post standup summary as a comment on linked issues via `specfact backlog daily` (e.g. `--post`) or reuse of `specfact sync bridge --add-progress-comment` with standup format (e.g. GitHub issue comment).
- **EXTEND**: Bridge/adapters: support posting comment to linked issue when adapter supports it (e.g. GitHub).
- **EXTEND**: Documentation (agile-scrum-workflows, devops-adapter-integration) for daily standup with SpecFact.

## Capabilities

- **daily-standup**: Standup view (list my/filtered items with status and last activity; optional standup summary lines) and optional post standup comment to linked issue via adapter.

## Impact

- **Affected specs**: New `openspec/changes/daily-standup-progress-support/specs/daily-standup/spec.md` (Given/When/Then for standup view and comment).
- **Affected code**: `src/specfact_cli/commands/` (extend backlog command group with `backlog daily` subcommand for standup view and optional comment post); bridge/adapters extended to post comment when supported (e.g. GitHub).
- **Affected documentation** (<https://docs.specfact.io>): docs/guides/agile-scrum-workflows.md, docs/guides/devops-adapter-integration.md for daily standup workflow.
- **Integration points**: Existing `specfact sync bridge`, GitHub/ADO adapters; OpenSpec change proposals and backlog items.
- **Backward compatibility**: Additive only; existing sync/bridge behavior unchanged unless user opts into standup view or comment post.

## Source Tracking

- **GitHub Issue**: #168
- **Issue URL**: <https://github.com/nold-ai/specfact-cli/issues/168>
- **Repository**: nold-ai/specfact-cli
- **Last Synced Status**: proposed
