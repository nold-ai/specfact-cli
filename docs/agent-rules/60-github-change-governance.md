---
layout: default
title: Agent GitHub change governance
permalink: /contributing/agent-rules/github-change-governance/
description: Cache-first GitHub issue governance for parent lookup, metadata completeness, and concurrency ambiguity checks.
keywords: [agents, github, hierarchy-cache, blockers, labels, project]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - openspec/CHANGE_ORDER.md
  - scripts/sync_github_hierarchy_cache.py
  - .specfact/backlog/github_hierarchy_cache.md
  - docs/agent-rules/**
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
id: agent-rules-github-change-governance
always_load: false
applies_when:
  - github-public-work
  - change-readiness
priority: 60
blocking: true
user_interaction_required: true
stop_conditions:
  - parent or blocker metadata missing
  - labels or project assignment missing
  - linked issue already in progress
depends_on:
  - agent-rules-index
  - agent-rules-session-bootstrap
  - agent-rules-openspec-and-tdd
---

# Agent GitHub change governance

## Hierarchy cache

`.specfact/backlog/github_hierarchy_cache.md` is the local lookup source for current Epic and Feature hierarchy metadata in this repository. It is ephemeral local state and must not be committed.

- Consult the cache first before creating a new change issue, syncing an existing change, or resolving parent or blocker metadata.
- If the cache is missing or stale, rerun `python scripts/sync_github_hierarchy_cache.py`.
- Use manual GitHub lookup only when the cache cannot answer the question after refresh.

### `specfact-cli-modules` (not yet mirrored)

The **`specfact-cli-modules`** repository does **not** yet ship `scripts/sync_github_hierarchy_cache.py` or the same `.specfact/backlog/*.md` / `.specfact/backlog/github_hierarchy_cache_state.json` layout as this repo.

**TODO (modules repo):** Add a compatible `sync_github_hierarchy_cache.py` that produces the **same markdown structure** and **fingerprint/state JSON** (including `github_hierarchy_cache_state.json`) and follows the same **cache-first** rules described here and in `openspec/specs/github-hierarchy-cache/spec.md`, so shared tooling can rely on **identical ordering** and **deterministic rendering**.

## Public-work readiness checks

Before implementation on a publicly tracked change issue:

- When the hierarchy cache file exists, ensure it is **fresh** for live issue-state checks: if `github_hierarchy_cache.md` (or its companion state) is **older than about five minutes** or you cannot tell when it was generated, run `python scripts/sync_github_hierarchy_cache.py` before trusting cached labels or hierarchy for blocking decisions.
- Verify the linked issue exists.
- Verify its parent relationship is correct against current cache-backed GitHub reality.
- Verify required labels are present.
- Verify project assignment is present.
- Verify blockers and blocked-by relationships are complete.

## Concurrency ambiguity

If the linked GitHub issue appears to be `in progress`, **do not** treat that as blocking until you have a **current** view of GitHub state:

1. If `.specfact/backlog/github_hierarchy_cache.md` is missing, or was last updated **more than about five minutes ago** (or freshness is unknown), run `python scripts/sync_github_hierarchy_cache.py` so local metadata is up to date for this repository.
2. Re-read the issue state from GitHub (for example via `gh issue view` or the refreshed cache-backed workflow your session uses) and confirm the issue is **still** `in progress`.
3. Only **after** that verification, if it remains `in progress`, treat it as a blocking ambiguity: pause implementation and ask the user to clarify whether the change is already being worked in another session. Read-only investigation may continue while implementation remains blocked.

## Pull-request review closure ledger

When a pushed commit remedies GitHub pull-request review feedback, re-fetch the
thread-aware review state before finalizing. For every thread whose requested
change is fully implemented and validated, reply in that thread with a concise
ledger entry naming the commit and the relevant tests or gates, then resolve the
thread. Do this even when GitHub has marked the thread outdated: outdated is not
evidence of closure. Leave any unfixed, ambiguous, conflicting, or intentionally
deferred thread unresolved and state why in a concise reply when a response is
appropriate. Re-fetch once more after the writes and report the remaining
unresolved threads.
