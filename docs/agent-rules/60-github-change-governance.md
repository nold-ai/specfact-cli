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

## Public-work readiness checks

Before implementation on a publicly tracked change issue:

- Verify the linked issue exists.
- Verify its parent relationship is correct against current cache-backed GitHub reality.
- Verify required labels are present.
- Verify project assignment is present.
- Verify blockers and blocked-by relationships are complete.

## Concurrency ambiguity

If the linked GitHub issue is already `in progress`, treat that as a blocking ambiguity. Pause implementation and ask the user to clarify whether the change is already being worked in another session. Read-only investigation may continue while implementation remains blocked.
