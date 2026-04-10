---
layout: default
title: Agent worktrees and branching
permalink: /contributing/agent-rules/worktrees-and-branching/
description: Branch protection, worktree policy, and conflict-avoidance rules for implementation work.
keywords: [agents, worktrees, git, branching, conflicts]
audience: [team, enterprise]
expertise_level: [advanced]
doc_owner: specfact-cli
tracks:
  - AGENTS.md
  - docs/agent-rules/**
  - scripts/worktree.sh
  - openspec/CHANGE_ORDER.md
last_reviewed: 2026-04-10
exempt: false
exempt_reason: ""
id: agent-rules-worktrees-and-branching
always_load: false
applies_when:
  - implementation
  - branch-management
priority: 30
blocking: true
user_interaction_required: true
stop_conditions:
  - implementation requested from dev or main without override
  - conflicting worktree ownership detected
depends_on:
  - agent-rules-index
  - agent-rules-non-negotiable-checklist
---

# Agent worktrees and branching

## Branch protection

`dev` and `main` are protected. Work on `feature/*`, `bugfix/*`, `hotfix/*`, or `chore/*` branches and submit PRs to `dev`.

## Worktree policy

- The primary checkout remains the canonical `dev` workspace.
- Use `scripts/worktree.sh create <type>/<branch-slug>` to create implementation worktrees (`feature`, `bugfix`, `hotfix`, or `chore` for `<type>`).
- Never create a worktree for `dev` or `main`.
- One branch maps to one worktree path at a time.
- Keep one active OpenSpec change scope per branch where possible.
- Create a dedicated virtual environment inside each worktree.
- Bootstrap Hatch once per new worktree with `hatch env create`.
- Run quick pre-flight checks from the worktree root with `hatch run smart-test-status` and `hatch run contract-test-status`.

## Conflict avoidance

- Check `openspec/CHANGE_ORDER.md` before creating a new worktree.
- Avoid concurrent branches editing the same `openspec/changes/<change-id>/` directory.
- Rebase frequently on `origin/dev`.
- Use `git worktree list` to detect stale or incorrect attachments.
