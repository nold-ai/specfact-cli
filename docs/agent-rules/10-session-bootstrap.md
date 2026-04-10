---
layout: default
title: Agent session bootstrap
permalink: /contributing/agent-rules/session-bootstrap/
description: Deterministic startup sequence for repository sessions after AGENTS.md is loaded.
keywords: [agents, bootstrap, worktree, cache, instructions]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - docs/agent-rules/**
  - .specfact/backlog/github_hierarchy_cache.md
  - scripts/sync_github_hierarchy_cache.py
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
id: agent-rules-session-bootstrap
always_load: true
applies_when:
  - session-bootstrap
priority: 10
blocking: true
user_interaction_required: true
stop_conditions:
  - unsupported branch or worktree context
  - cache-dependent GitHub work without refreshed hierarchy cache
depends_on:
  - agent-rules-index
  - agent-rules-non-negotiable-checklist
---

# Agent session bootstrap

## Required startup checks

1. Detect repository root, active branch, and whether the session is running in a worktree.
2. If the session is on `dev` or `main`, do not implement until the user explicitly allows it or a worktree is created.
3. Read `AGENTS.md`, then load the rule index and non-negotiable checklist.
4. Determine whether the task is read-only, artifact-only, or implementation work.
5. If GitHub hierarchy data is required, confirm `.specfact/backlog/github_hierarchy_cache.md` is present and fresh enough for the task.
6. If the cache is missing or stale, refresh it with `python scripts/sync_github_hierarchy_cache.py`.
7. Load the additional rule files required by the task signal from the index.

## Stop and continue behavior

- If the session is on the main checkout and the user did not override, stop implementation and create or switch to a worktree.
- If the requested work is tied to stale or ambiguous change metadata, continue only in read-only investigation mode until the user clarifies.
- If GitHub hierarchy metadata is needed and the cache cannot answer after refresh, manual GitHub lookup is allowed.
- If the task is purely explanatory or read-only, full implementation gates do not need to run.

## Why this file exists

This file keeps session bootstrap deterministic after `AGENTS.md` becomes compact. It is small enough to load every time, but specific enough to prevent drift across models and sessions.
