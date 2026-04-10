## Why

`AGENTS.md` has become a heavy mixed-purpose instruction surface that front-loads too much repository policy into every new session. That increases token cost, makes cross-model behavior less deterministic, and raises the risk that important workflow gates are forgotten once context is compacted.

## What Changes

- Introduce a deterministic agent-governance rule system with a small bootstrap `AGENTS.md`, a canonical rule index, and focused rule artifacts loaded by applicability.
- Define a machine-readable frontmatter contract for governance rule files so multiple AI models can follow the same loading and stop-condition semantics.
- Require an always-load non-negotiable checklist plus explicit precedence and stop/continue behavior for worktree, change validation, TDD, verification, and finalization gates.
- Make GitHub governance completeness explicit in the deterministic readiness flow, including parent resolution, labels, project assignment, blockers / blocked-by relationships, and live issue-state ambiguity checks.
- Tighten cache-first bootstrap guidance so session startup refreshes the local GitHub hierarchy cache when it is missing or stale.
- Move long-form governance detail out of `AGENTS.md` into dedicated markdown artifacts while preserving `AGENTS.md` as the mandatory small governance layer.

## Capabilities

### New Capabilities
- `agent-governance-loading`: Deterministic bootstrap, rule discovery, rule frontmatter, precedence, and stop-condition behavior for AI instruction surfaces.

### Modified Capabilities
- `github-hierarchy-cache`: Require cache freshness checks as part of the compact governance bootstrap flow.

## Impact

- Affected governance docs and instruction surfaces: `AGENTS.md`, new `docs/agent-rules/` artifacts, and possibly other lightweight instruction aliases that must reference the canonical rule system.
- Affected OpenSpec/runtime guidance: `openspec/config.yaml`, `openspec/CHANGE_ORDER.md`, and related workflow guidance for agents.
- Affected GitHub workflow guidance: cache-backed parent lookup, metadata completeness checks, and concurrency-ambiguity handling for linked change issues.
- Affected validation scope: documentation consistency, frontmatter schema enforcement, and deterministic session-bootstrap behavior across AI models.
